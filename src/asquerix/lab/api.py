"""Versioned single-user HTTP/SSE interface; requests never execute GPU work."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import hmac
import io
import json
import os
from pathlib import Path
import secrets
import threading
import time
from typing import Annotated, Literal
from urllib.parse import urlsplit
import zipfile

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .catalog import Conflict
from .config import Campaign, Model, capabilities
from .gpumon import power_control, query as gpu_query, set_power_limit
from .service import Service
from .storage import sha256
from .strategy import ProgramError, compile_program

STATIC = Path(__file__).parent / "static"
BEST_KNOWN = Path(__file__).parent / "data" / "best-known-upper-bounds.json"


def load_best_known(path: Path = BEST_KNOWN) -> dict:
    """Published best known upper bounds on s(n), for display beside results; never used by a search."""
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema") != "asquerix-best-known-upper-bounds-v1":
        raise ValueError(f"{path.name}: unsupported best-known schema")
    numbers = [entry["n"] for entry in document["entries"]]
    if len(numbers) != len(set(numbers)) or not all(isinstance(entry["upper_bound"], float) and entry["upper_bound"] >= 1.0
                                                    for entry in document["entries"]):
        raise ValueError(f"{path.name}: entries must have unique n and an upper bound of at least 1")
    return document
Key = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)]
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0, le=1000000)]


class ProgramRequest(Model):
    program: dict


class Created(Model):
    id: str
    state: str
    plan: dict


class ReplayRequest(Model):
    candidate_id: Annotated[str, Field(min_length=1, max_length=128)]
    episode_key: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    mode: Literal["accepted", "sweeps"] = "accepted"
    max_frames: Annotated[int, Field(ge=4, le=256)] = 256
    max_mib: Annotated[float, Field(gt=0, le=10)] = 10.0


class PowerLimit(Model):
    watts: Annotated[float, Field(gt=0, le=2000)]


class ContinueRequest(Model):
    additional_candidates_per_method: Annotated[int, Field(ge=1, le=1_000_000)]
    time_budget_seconds: Annotated[float, Field(gt=0, le=86400)] | None = None
    name: Annotated[str, Field(min_length=1, max_length=160)] | None = None
    description: Annotated[str, Field(max_length=2000)] | None = None
    device: Annotated[str, Field(pattern=r"^cuda:[0-9]{1,2}$")] | None = None
    batch_capacity: Annotated[int, Field(ge=1, le=262144)] | None = None
    slice_sweeps: Annotated[int, Field(ge=1, le=128)] | None = None
    slice_dispatches: Annotated[int, Field(ge=1, le=256)] | None = None
    max_seconds: Annotated[float, Field(gt=0, le=86400)] | None = None
    max_artifact_mib: Annotated[float, Field(gt=0, le=256)] | None = None
    automatic_replays: bool | None = None
    publication: bool | None = None


class Login(Model):
    token: Annotated[str, Field(min_length=16, max_length=512)]


def create_app(root: Path = Path("runs/lab"), *, host="127.0.0.1", port=8765,
               token: str | None = None, worker_enabled=True) -> FastAPI:
    remote = host not in ("127.0.0.1", "localhost", "::1")
    token = token or os.environ.get("ASQUERIX_LAB_TOKEN")
    if remote and (not token or len(token) < 16):
        raise ValueError("LAN binding requires ASQUERIX_LAB_TOKEN with at least 16 characters and explicit Host configuration")
    best_known = load_best_known()  # loaded and checked once when the web server starts
    service = Service(root, worker_enabled=worker_enabled)
    sessions = {}

    @asynccontextmanager
    async def lifespan(app):
        service.start()
        yield
        await asyncio.to_thread(service.stop)

    app = FastAPI(title="Asquerix Experiment Laboratory", version="1.0", lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url="/api/v1/openapi.json")
    app.state.service = service
    app.state.closing = threading.Event()
    hosts = ["127.0.0.1", "localhost", "[::1]"]
    if remote:
        hosts += [host] + [value.strip() for value in os.environ.get("ASQUERIX_LAB_HOSTS", "").split(",") if value.strip()]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            origin = request.headers.get("origin")
            expected = request.headers.get("host", "")
            if origin and (urlsplit(origin).netloc != expected or urlsplit(origin).scheme not in ("http", "https")):
                return JSONResponse({"detail": "Mutation Origin must match the laboratory Host"}, status_code=403)
            if request.headers.get("x-asquerix-client") != "lab-v1":
                return JSONResponse({"detail": "Missing same-origin laboratory client header"}, status_code=403)
            body = bytearray()
            async for part in request.stream():
                if len(body) + len(part) > 1024 * 1024:
                    return JSONResponse({"detail": "Request body exceeds 1 MiB"}, status_code=413)
                body.extend(part)
            request._body = bytes(body)
        if token and request.url.path.startswith("/api/") and request.url.path != "/api/v1/session":
            bearer = request.headers.get("authorization", "")
            via_bearer = bearer.startswith("Bearer ") and hmac.compare_digest(bearer[7:], token)
            cookie = request.cookies.get("asquerix_session")
            via_cookie = cookie in sessions
            if not via_bearer and not via_cookie:
                return JSONResponse({"detail": "Laboratory authentication required"}, status_code=401)
            if via_cookie and not via_bearer and request.method == "POST" and not hmac.compare_digest(request.headers.get("x-csrf-token", ""), sessions[cookie]):
                return JSONResponse({"detail": "Missing valid session CSRF token"}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.url.path == "/" or request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache"  # revalidate so an updated laboratory is picked up
        if "content-security-policy" not in response.headers:
            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; frame-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'"
        return response

    @app.exception_handler(ProgramError)
    async def bad_program(request, error):
        return JSONResponse({"detail": error.message, "node_path": error.path}, status_code=422)

    @app.exception_handler(Conflict)
    async def conflict(request, error):
        return JSONResponse({"detail": str(error)}, status_code=409)

    @app.exception_handler(KeyError)
    async def missing(request, error):
        return JSONResponse({"detail": str(error)}, status_code=404)

    @app.exception_handler(ValueError)
    async def invalid(request, error):
        return JSONResponse({"detail": str(error)}, status_code=422)

    @app.post("/api/v1/session")
    def session(login: Login, response: Response):
        if not token or not hmac.compare_digest(login.token, token):
            raise HTTPException(401, "Invalid laboratory token")
        identity, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        if len(sessions) >= 32:
            sessions.pop(next(iter(sessions)))
        sessions[identity] = csrf
        response.set_cookie("asquerix_session", identity, httponly=True, samesite="strict", secure=remote, max_age=86400)
        return {"csrf_token": csrf}

    @app.get("/api/v1/capabilities")
    def caps():
        return capabilities()

    @app.get("/api/v1/devices")
    def inventory():
        return {"items": service.inventory(), "active_campaign": service.active}

    @app.get("/api/v1/references/best-known")
    def references():
        return best_known

    power = {"checked": 0.0, "status": None}

    @app.get("/api/v1/gpu-monitor")
    def gpu_monitor():
        if time.monotonic() - power["checked"] > 30:
            power.update(checked=time.monotonic(), status=power_control())
        snapshot = service.gpu_monitor.snapshot()
        active = service.catalog.get(snapshot["campaign_id"]) if snapshot["campaign_id"] else None
        return {**snapshot, "campaign_device_uuid": active and active.get("device_uuid"), "power_control": power["status"]}

    @app.post("/api/v1/gpus/{index}/power-limit")
    def power_limit(index: int, request: PowerLimit):
        try:
            change = set_power_limit(index, request.watts, gpu_query())
        except PermissionError as error:
            raise HTTPException(403, f"Power limit not changed: {error}") from None
        if service.active:  # timing evidence of a running campaign must explain the change
            service.catalog.event(service.active, "GPU_POWER_LIMIT", change)
        power["checked"] = 0.0
        return change

    @app.get("/api/v1/debug")
    def debug(campaign_id: Annotated[str | None, Query(pattern=r"^[0-9a-f]{32}$")] = None):
        """One document describing the server and, optionally, a campaign, for diagnosing a problem."""
        import platform, subprocess
        from .storage import executable_identity, digest as identity_digest
        root = Path(__file__).resolve().parents[3]
        try:
            revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, timeout=3).stdout.strip()
            dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root, capture_output=True, text=True, timeout=3).stdout.split("\n")
        except (OSError, subprocess.SubprocessError):
            revision, dirty = None, []
        monitor = service.gpu_monitor.snapshot()
        report = {"generated_at": time.time(), "generated_at_text": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                  "server": {"source_revision": revision, "modified_files": [line[3:] for line in dirty if line.strip()],
                             "executable_hash_now": identity_digest(executable_identity()), "python": platform.python_version(),
                             "worker_alive": bool(service.process and service.process.is_alive()), "worker_ready": service.ready,
                             "active_campaign": service.active, "catalog": str(service.catalog.path)},
                  "gpus": monitor["gpus"] or [{key: device[key] for key in ("device", "name", "uuid", "memory_used_mib", "memory_total_mib", "utilization_percent")}
                                              for device in service.inventory()],
                  "gpu_monitor": {key: monitor[key] for key in ("session", "live", "campaign_id", "started", "finished", "error")},
                  "recent_campaigns": [{"id": item["id"], "name": item["spec"]["name"], "n": item["spec"]["n"], "state": item["state"],
                                        "error": item["summary"].get("error"), "updated": item["updated"]}
                                       for item in service.catalog.campaigns(limit=8)["items"]]}
        if campaign_id:
            campaign = service.catalog.get(campaign_id)
            directory = service.directory(campaign_id)
            checkpoint_path = service.root / "checkpoints" / (campaign_id + ".json.gz")
            checkpoint = None
            if checkpoint_path.is_file():
                from ..persistence import read_json
                state = read_json(checkpoint_path)
                checkpoint = {"phase": state.get("phase"), "executable_hash": state.get("executable_hash"),
                              "executable_matches_now": state.get("executable_hash") == report["server"]["executable_hash_now"],
                              "completed_episode_executions": state.get("completed_episode_executions"),
                              "elapsed_execution_seconds": state.get("elapsed_execution_seconds"),
                              "controllers": {method: {key: value.get(key) for key in ("outcome", "count", "completed", "generation", "parent_id")}
                                              for method, value in state.get("controllers", {}).items()},
                              "pending_groups": {method: len(value.get("pending", [])) for method, value in state.get("controllers", {}).items()},
                              "chunks": len(state.get("chunks", [])), "retained_programs": len(state.get("candidates", []))}
            error = None
            if (directory / "error.json.gz").is_file():
                from ..persistence import read_json
                error = read_json(directory / "error.json.gz")
            report["campaign"] = {"id": campaign_id, "state": campaign["state"], "created": campaign["created"], "updated": campaign["updated"],
                                  "device_uuid": campaign["device_uuid"], "spec": campaign["spec"], "summary": campaign["summary"],
                                  "publication": campaign["publication"], "error_file": error, "checkpoint": checkpoint,
                                  "recent_events": service.catalog.recent_events(campaign_id)}
        return report

    @app.post("/api/v1/debug")
    def debug_file(campaign_id: Annotated[str | None, Query(pattern=r"^[0-9a-f]{32}$")] = None, page: dict | None = None):
        """Write the diagnostic document to /tmp and return its path, which is short enough to paste."""
        report = debug(campaign_id)
        if page:
            report["page"] = page
        path = Path("/tmp") / f"asquerix-debug-{time.strftime('%Y%m%d-%H%M%S')}{'-' + campaign_id[:8] if campaign_id else ''}.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
        return {"path": str(path), "bytes": path.stat().st_size}

    @app.post("/api/v1/programs/validate")
    def validate(program: ProgramRequest):
        return compile_program(program.program).document()

    @app.post("/api/v1/campaigns", status_code=202, response_model=Created)
    def submit(campaign: Campaign, idempotency_key: Key):
        return service.submit(campaign, idempotency_key)

    @app.get("/api/v1/campaigns")
    def campaigns(limit: Limit = 30, offset: Offset = 0, state: str | None = None, query: str = ""):
        return service.catalog.campaigns(limit=limit, offset=offset, state=state, query=query[:160])

    @app.get("/api/v1/campaigns/{identifier}")
    def campaign(identifier: str):
        service.directory(identifier)
        result = service.catalog.get(identifier)
        result["replays"] = service.catalog.replays(identifier)
        return result

    @app.post("/api/v1/campaigns/{identifier}/replays", status_code=202)
    def queue_replay(identifier: str, replay: ReplayRequest, idempotency_key: Key):
        return service.queue_replay(identifier, replay.model_dump(), idempotency_key)

    @app.post("/api/v1/campaigns/{identifier}/continue", status_code=202, response_model=Created)
    def continue_campaign(identifier: str, request: ContinueRequest, idempotency_key: Key):
        values = request.model_dump(exclude_none=True)
        additional = values.pop("additional_candidates_per_method")
        overrides = {key: values.pop(key) for key in ("name", "description", "device", "batch_capacity",
                                                      "slice_sweeps", "slice_dispatches", "time_budget_seconds") if key in values}
        limits = {key: values.pop(key) for key in ("max_seconds", "max_artifact_mib") if key in values}
        if limits:
            overrides["limits"] = limits
        if "automatic_replays" in values:
            overrides["recording"] = {"automatic": values.pop("automatic_replays")}
        if "publication" in values:
            overrides["publication"] = {"enabled": values.pop("publication")}
        service.directory(identifier)
        return service.continue_campaign(identifier, additional, overrides, idempotency_key)

    @app.post("/api/v1/campaigns/{identifier}/{command}")
    def command(identifier: str, command: str, idempotency_key: Key):
        service.directory(identifier)
        if command == "clone":
            spec = service.catalog.get(identifier)["spec"]
            spec["name"] = spec["name"][:150] + " (clone)"
            return service.catalog.submit(Campaign.model_validate(spec), idempotency_key, state="DRAFT")
        if command not in ("pause", "resume", "stop"):
            raise HTTPException(404, "Unknown lifecycle command")
        return service.command(identifier, command, idempotency_key)

    @app.get("/api/v1/campaigns/{identifier}/history")
    def history(identifier: str, after: Annotated[str, Query(pattern=r"^[0-9]{1,19}$")] = "0", limit: Limit = 100):
        if int(after) > 2**63 - 1:
            raise HTTPException(422, "Event cursor exceeds signed int64")
        return service.catalog.history(identifier, after=int(after), limit=limit)

    @app.get("/api/v1/campaigns/{identifier}/history-state")
    def history_state(identifier: str, index: Annotated[int, Query(ge=0, le=1000000)]):
        return service.catalog.history_state(identifier, index)

    @app.get("/api/v1/campaigns/{identifier}/comparison")
    def comparison(identifier: str):
        return service.catalog.comparison(identifier)

    @app.get("/api/v1/campaigns/{identifier}/candidate/{candidate_id}")
    def candidate(identifier: str, candidate_id: str):
        return service.catalog.get_candidate(identifier, candidate_id)

    @app.get("/api/v1/campaigns/{identifier}/events")
    async def events(identifier: str, request: Request):
        service.catalog.get(identifier)
        raw = request.headers.get("last-event-id", "0")
        if not raw.isdecimal() or not 0 <= int(raw) <= 2**63 - 1:
            raise HTTPException(422, "Invalid Last-Event-ID")
        cursor = int(raw)

        async def stream():
            nonlocal cursor
            # Server shutdown ends open progress streams so Ctrl+C does not wait on browser tabs.
            while not app.state.closing.is_set() and not await request.is_disconnected():
                page = service.catalog.history(identifier, after=cursor, limit=100)
                if page["cursor_reset"]:
                    cursor = 0
                    yield "event: reset\ndata: " + json.dumps({"snapshot": f"/api/v1/campaigns/{identifier}", "history_cursor": "0"}) + "\n\n"
                for event in page["items"]:
                    cursor = int(event["id"])
                    yield f"id: {event['id']}\nevent: progress\ndata: {json.dumps(event, separators=(',', ':'))}\n\n"
                if not page["items"]:
                    yield ": heartbeat\n\n"
                    for _ in range(10):
                        if app.state.closing.is_set():
                            break
                        await asyncio.sleep(0.1)

        return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.get("/api/v1/campaigns/{identifier}/programs")
    def programs(identifier: str, limit: Limit = 50, offset: Offset = 0, arm: str | None = None,
                 sort: Literal["rank", "best", "order"] = "order"):
        return service.catalog.candidates(identifier, limit=limit, offset=offset, arm=arm, sort=sort)

    @app.get("/api/v1/programs/{program_hash}")
    def program(program_hash: str):
        return service.catalog.program(program_hash)

    @app.get("/api/v1/campaigns/{identifier}/episodes")
    def episodes(identifier: str, limit: Limit = 50, offset: Offset = 0, candidate_id: str | None = None, bank: str | None = None):
        return service.catalog.episodes(identifier, limit=limit, offset=offset, candidate_id=candidate_id, bank=bank)

    @app.get("/api/v1/replays/{identifier}")
    def replay(identifier: str):
        return service.catalog.get_replay(identifier)

    @app.get("/api/v1/artifacts/{identifier}")
    def artifact(identifier: str):
        item = service.catalog.get_artifact(identifier)
        root = service.directory(item["campaign_id"]).resolve()
        path = root / item["path"]
        if path.is_symlink() or not path.resolve().is_relative_to(root) or any(parent.is_symlink() for parent in path.parents if parent.is_relative_to(root)):
            raise HTTPException(403, "Artifact path is not allowlisted")
        if not path.is_file() or sha256(path) != item["sha256"]:
            raise HTTPException(409, "Artifact is missing or changed after finalization")
        headers = {}
        if path.suffix == ".html":
            headers["Content-Security-Policy"] = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; frame-src 'self' data: blob: about:; img-src data: blob:; sandbox allow-scripts allow-downloads"
        return FileResponse(path, headers=headers, filename=path.name, content_disposition_type="inline")

    @app.get("/api/v1/campaigns/{identifier}/export")
    def export(identifier: str):
        campaign = service.catalog.get(identifier)
        if campaign["summary"].get("report_status") != "READY":
            raise HTTPException(409, "Finalize the campaign report before export")
        root = service.directory(identifier)
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w", compression=zipfile.ZIP_STORED) as archive:
            for item in campaign["summary"]["artifacts"]:
                path = root / item["path"]
                if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink() or sha256(path) != item["sha256"]:
                    raise HTTPException(409, "Finalized export artifact changed")
                archive.write(path, arcname=item["path"])
        return Response(data.getvalue(), media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="asquerix-{identifier}.zip"'})

    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon():
        return FileResponse(STATIC / "favicon.svg", media_type="image/svg+xml")

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    return app
