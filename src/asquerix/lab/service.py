"""Owned service lifecycle, bounded IPC, and serialized durable result admission."""

from __future__ import annotations

import csv
import fcntl
import json
import multiprocessing
import os
from pathlib import Path
import queue
import subprocess
from threading import Event, Thread
import time
from uuid import uuid4

from ..persistence import read_json, read_jsonl, write_json
from .catalog import Catalog, Conflict
from .config import Campaign, digest
from .report import generate
from .storage import executable_identity, sha256, storage_bytes
from .worker import alive, process_start, worker_main


def devices() -> list[dict]:
    """Driver inventory without importing Warp or creating a CUDA context."""
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=index,name,uuid,memory.used,memory.total,utilization.gpu,driver_version", "--format=csv,noheader,nounits"],
                                capture_output=True, text=True, timeout=3, check=True)
    except (OSError, subprocess.SubprocessError):
        return []
    rows = []
    for values in csv.reader(result.stdout.splitlines()):
        if len(values) != 7:
            continue
        index, name, uuid, used, total, utilization, driver = (value.strip() for value in values)
        rows.append({"device": "cuda:" + index, "physical_index": int(index), "name": name, "uuid": uuid,
                     "memory_used_mib": int(used), "memory_total_mib": int(total),
                     "utilization_percent": int(utilization), "driver_version": driver,
                     "display_attached": True, "warning": "Display and other processes may share this GPU; slices provide bounded work, not hard preemption."})
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible is not None:
        by_index = {str(row["physical_index"]): row for row in rows}
        by_uuid = {row["uuid"]: row for row in rows}
        selected = []
        for ordinal, identity in enumerate(visible.split(",")):
            row = by_index.get(identity.strip()) or by_uuid.get(identity.strip())
            if row:
                selected.append({**row, "device": f"cuda:{ordinal}"})
        rows = selected
    return rows


class Service:
    def __init__(self, root: Path, *, worker_enabled=True):
        self.root = root.resolve()
        self.catalog = Catalog(self.root)
        self.worker_enabled = worker_enabled
        self.shutdown = Event()
        self.thread = None
        self.process = None
        self.token = None
        self.worker_start = None
        self.active = None
        self.active_replay = None
        self.ready = False
        self.ctx = multiprocessing.get_context("spawn")
        self.tasks = self.ctx.Queue(maxsize=1)
        self.replies = self.ctx.Queue(maxsize=32)
        self.signal = self.ctx.Value("i", 0)
        self.signal_since = self.ctx.Value("d", 0.0)
        self.launch_identity = None
        self.lock_stream = None

    def directory(self, identifier: str) -> Path:
        if len(identifier) != 32 or any(char not in "0123456789abcdef" for char in identifier):
            raise KeyError("Invalid campaign identity")
        return self.root / "campaigns" / identifier

    def start(self):
        self.lock_stream = (self.root / ".service.lock").open("a")
        try:
            fcntl.flock(self.lock_stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Conflict("Another laboratory service owns this catalog") from None
        for campaign in self.catalog.campaigns(limit=10000)["items"]:
            if campaign["state"] in ("PREPARING", "RUNNING", "PAUSE_REQUESTED", "FINALIZING"):
                self.catalog.set_state(campaign["id"], "INTERRUPTED", summary={"recovery": "Service restarted; finalized chunks will be reconciled before missing work is retried."})
                self.reconcile(campaign["id"])
        self.thread = Thread(target=self._coordinate, name="asquerix-lab-coordinator", daemon=True)
        self.thread.start()

    def stop(self):
        self.shutdown.set()
        if self.active:
            self.signal_since.value = time.time()
            self.signal.value = 2
        if self.thread:
            self.thread.join(timeout=10)
        if self.process and self.process.is_alive():
            try:
                self.tasks.put_nowait(None)
            except queue.Full:
                pass
            self.process.join(timeout=5)
        # Never kill an owned in-flight CUDA launch. Its parent identity check drains it.
        if self.lock_stream:
            fcntl.flock(self.lock_stream, fcntl.LOCK_UN)
            self.lock_stream.close()

    def submit(self, campaign: Campaign, key: str) -> dict:
        selected = next((item for item in devices() if item["device"] == campaign.device), None)
        if self.worker_enabled and selected is None:
            raise Conflict("Selected CUDA GPU is not detected; a GPU run cannot fall back to CPU")
        if selected and campaign.plan()["estimated_device_bytes"] > (selected["memory_total_mib"] - selected["memory_used_mib"]) * 1024**2:
            raise Conflict("Declared batch and recording buffers exceed currently available device memory")
        return self.catalog.submit(campaign, key)

    def command(self, identifier: str, command: str, key: str):
        result = self.catalog.command(identifier, command, key)
        if identifier == self.active and command in ("pause", "stop"):
            self.signal_since.value = time.time()
            self.signal.value = 1 if command == "pause" else 2
        return result

    def queue_replay(self, identifier: str, options: dict, key: str):
        campaign = self.catalog.get(identifier)
        candidate = self.catalog.get_candidate(identifier, options["candidate_id"])
        with self.catalog.lock:
            found = self.catalog.db.execute("SELECT document FROM episodes WHERE campaign_id=? AND candidate_id=? AND episode_key=?",
                (identifier, options["candidate_id"], options["episode_key"])).fetchone()
        if found is None:
            raise KeyError("Episode has no finalized best/current reference")
        row = json.loads(found[0])
        replay_id = digest({"campaign": identifier, "episode": options["episode_key"]})[:32]
        try:
            existing = self.catalog.get_replay(replay_id)
            if existing["state"] != "FAILED":
                return {"id": replay_id, "state": existing["state"]}
        except KeyError:
            pass
        estimated = 100000 + options["max_frames"] * (64 * campaign["spec"]["n"] + 2048)
        if estimated > options["max_mib"] * 1024**2 or storage_bytes(self.directory(identifier)) + estimated > campaign["spec"]["limits"]["max_artifact_mib"] * 1024**2:
            raise Conflict("Selected replay exceeds its explicit trace/campaign storage quota")
        document = {"candidate": candidate, "row": row, "options": options, "collection_id": replay_id}

        def action(db):
            db.execute("INSERT INTO replays VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET state=excluded.state,document=excluded.document",
                       (replay_id, identifier, row["episode_key"], "QUEUED", json.dumps(document, allow_nan=False)))
            self.catalog._event(db, identifier, "REPLAY_QUEUED", {"id": replay_id, "episode_key": row["episode_key"], "quota_mib": options["max_mib"]})
            return {"id": replay_id, "state": "QUEUED"}
        return self.catalog.idempotent(key, "replay:" + identifier, options, action)

    def reconcile(self, identifier):
        directory = self.directory(identifier)
        for path in sorted((directory / "evaluations").glob("*.done.json.gz")):
            receipt = read_json(path)
            if sha256(directory / receipt["records_path"]) != receipt["records_sha256"] or sha256(directory / receipt["numeric_path"]) != receipt["numeric_sha256"]:
                raise ValueError("Finalized chunk changed during recovery")
            self.catalog.admit_episodes(identifier, list(read_jsonl(directory / receipt["records_path"])))

    def inventory(self):
        owned = self.catalog.workers()
        return [{**device, "owned_jobs": [worker for worker in owned if worker["device_uuid"] == device["uuid"] and alive(worker["pid"], worker["process_start"])]}
                for device in devices()]

    def _ensure_worker(self):
        identity = digest(executable_identity())
        if self.process and self.process.is_alive() and identity == self.launch_identity:
            return
        if self.process and self.process.is_alive():
            self.tasks.put(None)
            self.process.join(timeout=5)
            if self.process.is_alive():
                raise Conflict("Old owned worker is still draining after an executable change")
        self.token = uuid4().hex
        self.launch_identity = identity
        self.ready = False
        self.process = self.ctx.Process(target=worker_main,
            args=(self.tasks, self.replies, self.signal, self.signal_since, self.token, os.getpid(), process_start(os.getpid())),
            name="asquerix-cuda-worker", daemon=False)
        self.process.start()

    def _register_artifacts(self, identifier):
        directory = self.directory(identifier)
        artifacts = []
        for path in sorted(directory.rglob("*")):
            if path.is_file() and not path.is_symlink() and not any(part.startswith(".") for part in path.relative_to(directory).parts):
                item = {"path": str(path.relative_to(directory)), "sha256": sha256(path), "size_bytes": path.stat().st_size}
                item["id"] = self.catalog.artifact(identifier, item)
                artifacts.append(item)
        return artifacts

    def _finalize(self, identifier, summary):
        self.catalog.set_state(identifier, "FINALIZING", summary={**summary, "phase": "FINALIZING", "scientific_status": summary["state"], "report_status": "BUILDING"})
        directory = self.directory(identifier)
        events = []
        cursor = 0
        while True:
            page = self.catalog.history(identifier, after=cursor, limit=500)
            if not page["items"]:
                break
            events.extend(page["items"])
            cursor = int(page["items"][-1]["id"])
        spec = Campaign.model_validate(self.catalog.get(identifier)["spec"])
        report = generate(directory, events, campaign=spec)
        publication = {"status": "LOCAL_ONLY"}
        if spec.publication.enabled:
            from ..publication import publish
            publication = publish(directory, push=True)
        artifacts = self._register_artifacts(identifier)
        report_artifact = next(item["id"] for item in artifacts if item["path"] == "report.html")
        self.catalog.set_state(identifier, summary["state"], summary={"phase": summary["state"], "report_status": "READY", "report_artifact_id": report_artifact,
            "artifacts": artifacts, "report_seconds": report["report_seconds"]}, publication=publication)

    def _message(self, message):
        kind = message["type"]
        if kind == "ready":
            if message["token"] != self.token:
                return
            self.ready = True
            self.worker_start = message["process_start"]
            self.catalog.worker(self.token, message["pid"], self.worker_start)
            return
        identifier = message["campaign_id"]
        if kind == "event":
            self.catalog.event(identifier, message["kind"], message["payload"])
        elif kind == "checkpoint":
            with self.catalog.transaction() as db:
                db.execute("INSERT INTO checkpoints VALUES(?,?) ON CONFLICT(campaign_id) DO UPDATE SET document=excluded.document",
                           (identifier, json.dumps({"path": message["path"], "updated": time.time()})))
        elif kind == "candidate":
            self.catalog.candidate(identifier, message["candidate"])
        elif kind == "chunk":
            path = self.directory(identifier) / message["records"]
            self.catalog.admit_episodes(identifier, list(read_jsonl(path)))
        elif kind == "replay":
            result = dict(message["replay"])
            for artifact in result["artifacts"]:
                artifact["id"] = self.catalog.artifact(identifier, artifact)
            self.catalog.replay(identifier, result["episode_key"], result, state=result["status"])
        elif kind == "device":
            self.catalog.set_state(identifier, "PREPARING", token=self.token, uuid=message["uuid"], summary={"executable_hash": message["identity"]})
            self.catalog.worker(self.token, self.process.pid, self.worker_start, campaign_id=identifier, device_uuid=message["uuid"], state="RUNNING")
        elif kind == "progress":
            campaign = self.catalog.get(identifier)
            state = campaign["state"]
            if state not in ("PAUSE_REQUESTED", "STOP_REQUESTED"):
                state = "PREPARING" if message["summary"]["phase"] == "PREPARING" else "RUNNING"
            self.catalog.set_state(identifier, state, summary=message["summary"])
            self.catalog.worker(self.token, self.process.pid, self.worker_start, campaign_id=identifier, device_uuid=campaign["device_uuid"], state="RUNNING")
        elif kind == "finished":
            summary = message["summary"]
            if summary["state"] in ("PAUSED", "INTERRUPTED"):
                self.catalog.set_state(identifier, summary["state"], summary=summary)
            else:
                self._finalize(identifier, summary)
            self.catalog.worker(self.token, self.process.pid, self.worker_start, state="IDLE")
            self.active = None
        elif kind == "replay_finished":
            result = message["replay"]
            for artifact in result["artifacts"]:
                artifact["id"] = self.catalog.artifact(identifier, artifact)
            self.catalog.replay(identifier, result["episode_key"], result, state=result["status"])
            self.catalog.event(identifier, "ON_DEMAND_REPLAY_COMPLETED", {"id": message["replay_id"], "status": result["status"]})
            self.catalog.worker(self.token, self.process.pid, self.worker_start, state="IDLE")
            self.active = self.active_replay = None
        elif kind == "failed":
            if self.active_replay:
                item = self.catalog.get_replay(self.active_replay)
                self.catalog.replay(identifier, item["episode_key"], {"error": message["error"]}, state="FAILED")
                self.active = self.active_replay = None
                return
            write_json(self.directory(identifier) / "error.json.gz", {"error": message["error"], "traceback": message["traceback"]})
            self.catalog.set_state(identifier, "FAILED", summary={"error": message["error"], "report_status": "FAILED"})
            self.catalog.worker(self.token, self.process.pid, self.worker_start, state="IDLE")
            self.active = None

    def _coordinate(self):
        while not self.shutdown.is_set() or self.active:
            try:
                message = self.replies.get(timeout=0.2)
                self._message(message)
            except queue.Empty:
                pass
            except BaseException as error:
                if self.active:
                    self.catalog.set_state(self.active, "FAILED", summary={"error": str(error), "report_status": "FAILED"})
                    self.active = None
            if self.active and self.process and not self.process.is_alive():
                self.catalog.set_state(self.active, "INTERRUPTED", summary={"error": "Owned worker exited; resume reconciles finalized chunks and retries missing work."})
                self.active = None
                self.ready = False
            if self.shutdown.is_set() or self.active or not self.worker_enabled:
                continue
            orphans = [worker for worker in self.catalog.workers() if worker["token"] != self.token and alive(worker["pid"], worker["process_start"])]
            if orphans:
                continue
            queued = self.catalog.campaigns(limit=100, state="QUEUED")["items"]
            queued += self.catalog.campaigns(limit=100, state="STOP_REQUESTED")["items"]
            pending_replays = self.catalog.pending_replays() if not queued else []
            if not queued and not pending_replays:
                continue
            campaign = min(queued, key=lambda item: item["created"]) if queued else self.catalog.get(pending_replays[0]["campaign_id"])
            try:
                self._ensure_worker()
                if not self.ready:
                    continue
                self.active = campaign["id"]
                if pending_replays:
                    pending = pending_replays[0]
                    self.active_replay = pending["id"]
                    self.signal.value = 0
                    self.signal_since.value = 0.0
                    self.catalog.replay(self.active, pending["episode_key"], pending["document"], state="RUNNING")
                    self.tasks.put({"kind": "replay", "id": self.active, "spec": campaign["spec"],
                                    "directory": str(self.directory(self.active)), "replay_id": pending["id"], **pending["document"]})
                    continue
                self.signal.value = 2 if campaign["state"] == "STOP_REQUESTED" else 0
                self.signal_since.value = time.time() if self.signal.value else 0.0
                self.catalog.set_state(self.active, "PREPARING", token=self.token)
                self.tasks.put({"id": self.active, "spec": campaign["spec"],
                                "directory": str(self.directory(self.active)),
                                "checkpoint": str(self.root / "checkpoints" / (self.active + ".json.gz"))})
            except BaseException as error:
                self.catalog.set_state(campaign["id"], "FAILED", summary={"error": str(error)})
                self.active = None
