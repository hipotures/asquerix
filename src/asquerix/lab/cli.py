"""Rich clients and a local server for the shared laboratory service."""

from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import stat
import sys
import time
import urllib.error
import urllib.request
from uuid import uuid4
import zipfile

from ..persistence import read_json, write_json
from .config import Campaign


def request(url, path, *, method="GET", body=None, binary=False):
    headers = {"X-Asquerix-Client": "lab-v1", "Content-Type": "application/json"}
    if method == "POST":
        headers["Idempotency-Key"] = uuid4().hex
    token = os.environ.get("ASQUERIX_LAB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url.rstrip("/") + "/api/v1" + path,
          data=json.dumps(body or {}).encode() if method == "POST" else None, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = response.read(256 * 1024**2 + 1)
            if len(data) > 256 * 1024**2:
                raise ValueError("Server response exceeded bounded export size")
            return data if binary else json.loads(data)
    except urllib.error.HTTPError as error:
        payload = json.loads(error.read(1024 * 1024))
        raise ValueError(payload.get("detail", f"HTTP {error.code}")) from None


def duration(seconds) -> str:
    seconds = round(seconds or 0)
    if seconds < 60:
        return f"{seconds} s"
    if seconds < 3600:
        return f"{seconds // 60} min {seconds % 60:02d} s"
    return f"{seconds // 3600} h {seconds % 3600 // 60:02d} min"


def display(result, *, plain=False):
    if plain:
        print(f"Campaign {result['id']}: {result.get('state', 'QUEUED')}")
        return
    from ..cli import _console
    from rich.table import Table
    summary = result.get("summary", {})
    table = Table(title=f"Asquerix laboratory · {result['id']}", show_header=False)
    for label, value in (("State / worker phase", f"{result['state']} / {summary.get('phase', 'queued')}"),
                         ("Method / generation", f"{summary.get('arm', 'fixed / preparation')} / {summary.get('generation', '—')}"),
                         ("Completed candidates", summary.get("completed_candidates", 0)),
                         ("Scientific episode executions", summary.get("completed_episode_executions", 0)),
                         ("Training incumbent mean L", summary.get("training_incumbent", {}).get("mean_best_L", "—")),
                         ("GPU execution time", duration(summary.get("elapsed_execution_seconds", 0))),
                         ("Diagnostic replays", summary.get("replay_executions", 0)),
                         ("Publication", result.get("publication", {}).get("status", "PENDING"))):
        table.add_row(label, str(value))
    _console().print(table)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Single-host rigid-square experiment laboratory")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="Start the owned HTTP/coordinator/CUDA-worker lifecycle")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--root", type=Path, default=Path("runs/lab"))
    for name in ("submit", "watch", "status", "pause", "resume", "stop", "report", "export"):
        command = commands.add_parser(name)
        command.add_argument("--url", default="http://127.0.0.1:8765")
        command.add_argument("--json", action="store_true", help="Save structured output to disk and print concise paths")
        if name == "submit":
            command.add_argument("--config", type=Path, required=True)
        else:
            command.add_argument("campaign_id")
        if name == "export":
            command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "serve":
            import uvicorn
            from .api import create_app
            print(f"Laboratory: http://{args.host}:{args.port} | catalog: {args.root.resolve()}", flush=True)
            print("Press Ctrl+C to stop the server. A running campaign is stopped and finalized as PARTIAL; "
                  "use Pause in the browser first to resume it later.", flush=True)
            app = create_app(args.root, host=args.host, port=args.port)

            class Server(uvicorn.Server):
                first_signal = None

                def handle_exit(self, sig, frame):
                    # `uv run` forwards the terminal's Ctrl+C a second time; only a later repeat forces exit.
                    now = time.monotonic()
                    if self.first_signal is not None and now - self.first_signal < 1.0:
                        return
                    self.first_signal = self.first_signal or now
                    app.state.closing.set()  # end open browser progress streams before waiting for connections
                    super().handle_exit(sig, frame)

            Server(uvicorn.Config(app, host=args.host, port=args.port, access_log=False, log_level="info")).run()
            return 0
        if args.command == "submit":
            spec = Campaign.model_validate(read_json(args.config))
            result = request(args.url, "/campaigns", method="POST", body=spec.document())
        elif args.command in ("pause", "resume", "stop"):
            result = request(args.url, f"/campaigns/{args.campaign_id}/{args.command}", method="POST")
        elif args.command == "export":
            payload = request(args.url, f"/campaigns/{args.campaign_id}/export", binary=True)
            if args.output.exists() and any(args.output.iterdir()):
                raise ValueError("Export destination must be empty; existing evidence is never overwritten")
            args.output.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                total = 0
                for item in archive.infolist():
                    relative = Path(item.filename)
                    total += item.file_size
                    if total > 256 * 1024**2 or relative.is_absolute() or any(part.startswith(".") for part in relative.parts) or stat.S_ISLNK(item.external_attr >> 16):
                        raise ValueError("Unsafe export archive entry")
                    target = args.output / relative
                    if not target.resolve().is_relative_to(args.output.resolve()):
                        raise ValueError("Unsafe export archive path")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(item))
            print(f"Export: {args.output.resolve()}")
            print(f"Offline report: {(args.output / 'report.html').resolve()}")
            return 0
        else:
            result = request(args.url, f"/campaigns/{args.campaign_id}")
        if args.command == "watch":
            while result["state"] not in ("COMPLETED", "PARTIAL", "FAILED", "INTERRUPTED", "PAUSED"):
                display(result, plain=args.json)
                time.sleep(1)
                result = request(args.url, f"/campaigns/{args.campaign_id}")
        display(result, plain=args.json)
        output = write_json(Path("runs/lab-cli") / (args.command + "-" + result["id"] + ".json.gz"), result)
        print(f"Saved: {output}")
        if args.command == "report":
            artifact = result.get("summary", {}).get("report_artifact_id")
            if not artifact:
                raise ValueError("Campaign report is not finalized yet")
            print(f"Report: {args.url}/api/v1/artifacts/{artifact}")
        return 0
    except KeyboardInterrupt:
        if args.command == "serve":
            print("Laboratory server stopped.")
            return 0
        print("Client closed; the service continues its owned computation.")
        return 130
    except (OSError, ValueError, urllib.error.URLError) as error:
        print(f"Laboratory error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
