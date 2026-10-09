"""Owned spawned worker; CUDA starts only after selecting an immutable campaign."""

from __future__ import annotations

import json
import os
from pathlib import Path
import queue
import signal as os_signal
import time
import traceback

import numpy as np

from ..persistence import open_jsonl_writer, read_json, read_jsonl, write_json
from .config import Campaign, digest
from .evaluation import result_row, score
from .search import Controller, initial_pool
from .storage import check_quota, environment, executable_identity, load_banks, load_npz, prepare_banks, sha256, write_npz
from .strategy import compile_program, control_program


def process_start(pid: int) -> str | None:
    try:
        # The command field can contain spaces or parentheses.
        content = Path(f"/proc/{pid}/stat").read_text()
        fields = content[content.rfind(")") + 2:].split()
        if fields[0] == "Z":
            return None
        return fields[19]
    except (OSError, IndexError):
        return None


def alive(pid: int, start: str) -> bool:
    return process_start(pid) == start


class CampaignWorker:
    def __init__(self, job: dict, *, emit, signal, signal_since):
        self.identifier = job["id"]
        self.campaign = Campaign.model_validate(job["spec"])
        self.directory = Path(job["directory"])
        self.checkpoint_path = Path(job["checkpoint"])
        self.directory.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        self.emit, self.signal, self.signal_since = emit, signal, signal_since
        self.started = time.time()
        self.execution_start = time.monotonic()
        self.state = {"schema": "asquerix-lab-checkpoint-v1", "phase": "PREPARING", "controllers": {},
                      "candidates": [], "chunks": [], "replays": [], "shared_pool": None, "frozen_winners": [],
                      "submitted_episode_attempts": 0, "completed_episode_executions": 0, "replay_executions": 0,
                      "group_attempts": {}, "elapsed_execution_seconds": 0.0, "timings": {}, "pause_drains": [], "arm_start_elapsed": {}}
        if self.checkpoint_path.exists():
            self.state = read_json(self.checkpoint_path)
            if self.state["manifest_hash"] != digest(self.campaign.document()):
                raise ValueError("Checkpoint immutable manifest mismatch")
            if self.state["executable_hash"] != digest(executable_identity()):
                raise ValueError("Numerical source/dependency identity changed; this campaign cannot mix executables")
        self.state["manifest_hash"] = digest(self.campaign.document())
        self.state["executable_hash"] = digest(executable_identity())
        self.elapsed_before = self.state["elapsed_execution_seconds"]
        self.last_activity = 0.0
        self.deadline_reached = False

    def elapsed(self):
        return self.elapsed_before + time.monotonic() - self.execution_start

    def stopped(self):
        if self.elapsed() >= self.campaign.limits.max_seconds:
            self.deadline_reached = True
        return self.signal.value >= 2 or self.deadline_reached

    def event(self, kind: str, payload: dict):
        self.emit({"type": "event", "campaign_id": self.identifier, "kind": kind, "payload": payload})

    def checkpoint(self):
        self.state["elapsed_execution_seconds"] = self.elapsed()
        write_json(self.checkpoint_path, self.state)
        self.emit({"type": "checkpoint", "campaign_id": self.identifier, "path": str(self.checkpoint_path)})

    def activity(self, *, phase=None, **values):
        now = time.monotonic()
        if phase is not None or now - self.last_activity > 2:
            self.last_activity = now
            self.emit({"type": "progress", "campaign_id": self.identifier,
                       "summary": {"phase": phase or self.state["phase"], "elapsed_execution_seconds": self.elapsed(),
                                   "submitted_episode_attempts": self.state["submitted_episode_attempts"],
                                   "completed_episode_executions": self.state["completed_episode_executions"],
                                   "replay_executions": self.state["replay_executions"], **values}})

    def safe_boundary(self) -> str | None:
        self.checkpoint()
        if self.stopped():
            return "PARTIAL"
        if self.signal.value == 1:
            drain = max(0, time.time() - self.signal_since.value)
            self.state["pause_drains"].append(drain)
            self.event("PAUSED_AT_GROUP_BOUNDARY", {"drain_seconds": drain, "phase": self.state["phase"]})
            self.checkpoint()
            return "PAUSED"
        if digest(executable_identity()) != self.state["executable_hash"]:
            self.event("EXECUTABLE_CHANGED", {"phase": self.state["phase"]})
            return "INTERRUPTED"
        return None

    def fixed_candidates(self):
        result = []
        authored = [("controls", control_program(name)) for name in self.campaign.controls]
        authored += [("fixed", program) for program in self.campaign.fixed_programs]
        for position, (arm, program) in enumerate(authored):
            result.append({"id": f"{self.identifier}:{arm}:{position}", "arm": arm,
                           "position": position, "generation": 0, "program": compile_program(program).document(),
                           "parent_id": None, "parent_hash": None, "mutation": None,
                           "origin": "fixed_control" if arm == "controls" else "authored_fixed_program",
                           "state": "PENDING", "score": {}})
        return result

    def evaluate(self, candidates: list[dict], bank_name: str) -> list[dict]:
        from .gpu import StrategyBatch, defined_fields
        bank = self.banks[bank_name]
        episodes_per_candidate = len(bank["ids"]) * self.campaign.operator_replicates
        total = len(candidates) * episodes_per_candidate
        group_hash = digest({"candidates": [candidate["id"] for candidate in candidates], "bank": bank_name})[:16]
        programs = [compile_program(candidate["program"]["authored"]) for candidate in candidates]
        records_by_candidate = {candidate["id"]: [] for candidate in candidates}
        chunk_size = min(self.campaign.batch_capacity, 4096)
        for first in range(0, total, chunk_size):
            count = min(chunk_size, total - first)
            stem = f"part-{group_hash}-{first // chunk_size:04d}"
            numeric_relative = f"evaluations/{stem}.npz"
            json_relative = f"evaluations/{stem}.jsonl.gz"
            receipt_path = self.directory / "evaluations" / (stem + ".done.json.gz")
            if receipt_path.exists():
                receipt = read_json(receipt_path)
                if sha256(self.directory / numeric_relative) != receipt["numeric_sha256"] or sha256(self.directory / json_relative) != receipt["records_sha256"]:
                    raise ValueError("Finalized result chunk checksum mismatch during reconciliation")
                rows = list(read_jsonl(self.directory / json_relative))
                self.emit({"type": "chunk", "campaign_id": self.identifier, "records": json_relative})
            else:
                if self.stopped():
                    break
                if digest(executable_identity()) != self.state["executable_hash"]:
                    raise InterruptedError("Executable changed before task admission")
                check_quota(self.campaign, self.directory, reserve=count * (24 * self.campaign.n + 2048))
                indices = np.arange(first, first + count, dtype=np.int64)
                pids = (indices // episodes_per_candidate).astype(np.int32)
                local = indices % episodes_per_candidate
                initial_slots = (local // self.campaign.operator_replicates).astype(np.int32)
                replicates = (local % self.campaign.operator_replicates).astype(np.uint64)
                attempt = self.state["group_attempts"].get(stem, 0) + 1
                self.state["group_attempts"][stem] = attempt
                self.state["submitted_episode_attempts"] += count
                self.event("TASK_GROUP_STARTED", {"group": stem, "bank": bank_name, "episodes": count, "attempt": attempt,
                                                  "candidate_ids": [candidate["id"] for candidate in candidates]})
                self.checkpoint()
                self.activity(phase=bank_name.upper(), arm=candidates[0]["arm"], generation=candidates[0]["generation"], active_episodes=count)
                batch = StrategyBatch(self.campaign, programs, bank["poses"][initial_slots],
                                      bank["initial_results"][initial_slots], bank["ids"][initial_slots], replicates, pids)
                while not batch.advance(cancel=self.stopped()):
                    self.activity(active_episodes=count)
                states, best, current = batch.collect()
                validation_start = time.monotonic()
                rows = []
                for index in range(count):
                    candidate = candidates[int(pids[index])]
                    row = result_row(self.campaign, states[index], best[index], current[index],
                                     program_hash=candidate["program"]["hash"], bank_hash=bank["hash"],
                                     initial_id=str(int(bank["ids"][initial_slots[index]])), replicate=str(int(replicates[index])))
                    row.update({"candidate_id": candidate["id"], "bank": bank_name, "arm": candidate["arm"],
                                "task_id": digest({"campaign": self.identifier, "candidate": candidate["id"], "episode": row["episode_key"]}),
                                "execution_attempt": attempt, "numeric_path": numeric_relative, "numeric_index": index,
                                "timing_scope": "Shared strategy batch; GPU time is not an isolated per-program measurement"})
                    rows.append(row)
                validation_seconds = time.monotonic() - validation_start
                arrays = {"best_poses": best, "current_poses": current,
                          "initial_ids": bank["ids"][initial_slots], "replicates": replicates,
                          "program_indices": pids}
                arrays.update({"state_" + name: array for name, array in defined_fields(states).items()})
                persist_start = time.monotonic()
                numeric = write_npz(self.directory / numeric_relative, arrays)
                with open_jsonl_writer(self.directory / json_relative) as stream:
                    for row in rows:
                        stream.write(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n")
                timing = {**batch.timings, "validation_seconds": validation_seconds,
                          "persistence_seconds": time.monotonic() - persist_start}
                receipt = {"schema": "asquerix-lab-result-chunk-v1", "group": stem, "count": count,
                           "numeric_path": numeric_relative, "records_path": json_relative,
                           "numeric_sha256": sha256(numeric), "records_sha256": sha256(self.directory / json_relative),
                           "timings": timing, "attempt": attempt, "completed_at": time.time(),
                           "execution_elapsed_seconds": self.elapsed(),
                           "completed_episode_executions": sum(row["termination"] != "CANCELLED" for row in rows)}
                write_json(receipt_path, receipt)
                self.state["completed_episode_executions"] += receipt["completed_episode_executions"]
                self.emit({"type": "chunk", "campaign_id": self.identifier, "records": json_relative})
                self.event("TASK_GROUP_COMPLETED", receipt)
            if receipt not in self.state["chunks"]:
                self.state["chunks"].append(receipt)
            for row in rows:
                records_by_candidate[row["candidate_id"]].append(row)
            self.checkpoint()
            if self.stopped():
                break
        evaluated = []
        for candidate in candidates:
            rows = records_by_candidate[candidate["id"]]
            started = time.monotonic()
            summary = score(rows, expected_count=episodes_per_candidate,
                            instruction_count=candidate["program"]["instruction_count"],
                            program_hash=candidate["program"]["hash"], thresholds=self.campaign.thresholds)
            summary["scoring_seconds"] = time.monotonic() - started
            result = {**candidate, "state": "EVALUATED" if summary["complete"] else "INCOMPLETE",
                      "score" if bank_name == "training" else "holdout_score": summary,
                      "completed_at": time.time(), "execution_elapsed_seconds": self.elapsed()}
            result["arm_execution_elapsed_seconds"] = self.elapsed() - self.state["arm_start_elapsed"].get(candidate["arm"], 0.0)
            evaluated.append(result)
            self.emit({"type": "candidate", "campaign_id": self.identifier, "candidate": result})
            self.event("CANDIDATE_RESULT" if bank_name == "training" else "HOLDOUT_RESULT",
                       {"candidate_id": result["id"], "arm": result["arm"], "bank": bank_name, "score": summary,
                        "program_hash": candidate["program"]["hash"], "execution_elapsed_seconds": self.elapsed()})
        return evaluated

    def all_rows(self) -> list[dict]:
        rows = []
        for chunk in self.state["chunks"]:
            rows.extend(read_jsonl(self.directory / chunk["records_path"]))
        return rows

    def automatic_replays(self):
        if not self.campaign.recording.automatic:
            return
        from .trace import replay
        rows = self.all_rows()
        initial_id = str(int(self.banks["training"]["ids"][0]))
        selected = [candidate for candidate in self.state["candidates"] if candidate["arm"] in ("controls", "fixed")]
        selected += self.state["frozen_winners"]
        selections = []
        for method, state in self.state["controllers"].items():
            by_id = {candidate["id"]: candidate for candidate in state["candidates"]}
            replacement = next((candidate for candidate in reversed(state["candidates"])
                                if candidate["parent_id"] and candidate.get("score", {}).get("eligible")
                                and candidate["parent_id"] in by_id
                                and tuple(candidate["score"]["ranking_tuple"]) < tuple(by_id[candidate["parent_id"]]["score"]["ranking_tuple"])), None)
            if replacement:
                selections.extend((replacement, by_id[replacement["parent_id"]]))
        selected += selections[:2]
        seen = {item["episode_key"] for item in self.state["replays"]}
        collection_bytes = sum(artifact["size_bytes"] for item in self.state["replays"] for artifact in item["artifacts"])
        omissions = []
        for candidate in selected:
            row = next((item for item in rows if item["candidate_id"] == candidate["id"] and item["bank"] == "training"
                        and item["initial_id"] == initial_id and item["replicate"] == "0"), None)
            if not row or row["episode_key"] in seen:
                continue
            if len(seen) >= self.campaign.recording.max_traces:
                omissions.append({"candidate_id": candidate["id"], "reason": "trace count cap"})
                continue
            if self.stopped():
                omissions.append({"candidate_id": candidate["id"], "reason": "stop/deadline; available on demand"})
                continue
            # Reserve a conservative complete native/HTML trace before starting CUDA.
            estimated = 100000 + self.campaign.recording.max_frames_per_trace * (64 * self.campaign.n + 2048)
            if collection_bytes + estimated > self.campaign.recording.max_trace_mib * 1024**2:
                omissions.append({"candidate_id": candidate["id"], "reason": "trace collection storage cap"})
                continue
            self.activity(phase="REPLAYS", candidate_id=candidate["id"])
            reference = load_npz(self.directory / row["numeric_path"])
            result = replay(self.campaign, self.directory, candidate=candidate, row=row,
                            bank=self.banks["training"], reference_arrays=reference,
                            reference_index=row["numeric_index"], provenance=self.provenance, cancelled=self.stopped)
            self.state["replay_executions"] += 1
            actual_bytes = sum(artifact["size_bytes"] for artifact in result["artifacts"])
            if collection_bytes + actual_bytes > self.campaign.recording.max_trace_mib * 1024**2:
                raise OSError("Trace collection exceeded its preflight quota")
            collection_bytes += actual_bytes
            self.state["replays"].append(result)
            seen.add(row["episode_key"])
            self.emit({"type": "replay", "campaign_id": self.identifier, "replay": result})
            self.event("REPLAY_COMPLETED", {"episode_key": result["episode_key"], "status": result["status"], "frames": result["frames"]})
            self.checkpoint()
        self.state["replay_omissions"] = omissions

    def run(self) -> dict:
        if self.stopped():
            if (self.directory / "datasets.json.gz").exists():
                self.metadata, self.banks = load_banks(self.directory)
            if not (self.directory / "campaign.json.gz").exists():
                write_json(self.directory / "campaign.json.gz", {"id": self.identifier, "spec": self.campaign.document(), "plan": self.campaign.plan(), "profile": self.campaign.profile()})
                write_json(self.directory / "environment.json.gz", environment())
            return self.finish("PARTIAL")
        import warp as wp
        wp.init()
        device = wp.get_device(self.campaign.device)
        if not device.is_cuda:
            raise ValueError("The selected worker device is not CUDA")
        self.provenance = environment(device)
        if self.state["executable_hash"] != self.provenance["executable_hash"]:
            raise ValueError("Worker launch identity changed during preparation")
        self.emit({"type": "device", "campaign_id": self.identifier, "uuid": device.uuid,
                   "identity": self.provenance["executable_hash"]})
        write_json(self.directory / "campaign.json.gz", {"id": self.identifier, "spec": self.campaign.document(),
                                                        "plan": self.campaign.plan(), "profile": self.campaign.profile()})
        if not (self.directory / "environment.json.gz").exists():
            write_json(self.directory / "environment.json.gz", self.provenance)
        if not (self.directory / "datasets.json.gz").exists():
            self.activity(phase="PREPARING")
            metadata, timing = prepare_banks(self.campaign, self.directory, stop=self.stopped,
                                           progress=lambda value: self.activity(phase="PREPARING", **{key: val for key, val in value.items() if key != "phase"}))
            self.state["timings"].update(timing)
        self.metadata, self.banks = load_banks(self.directory)
        for candidate in self.state["candidates"]:
            self.emit({"type": "candidate", "campaign_id": self.identifier, "candidate": candidate})
        if self.state["phase"] in ("PREPARING", "CONTROLS"):
            self.state["phase"] = "CONTROLS"
            controls = self.fixed_candidates()
            for candidate in controls:
                self.emit({"type": "candidate", "campaign_id": self.identifier, "candidate": candidate})
                self.event("CANDIDATE_GENERATED", candidate)
            self.state["candidates"] = self.evaluate(controls, "training") if controls else []
            self.state["phase"] = "SEARCH"
            boundary = self.safe_boundary()
            if boundary:
                return self.finish(boundary)
        if self.state["phase"] == "SEARCH":
            if self.campaign.search.methods and self.state["shared_pool"] is None:
                self.state["shared_pool"] = initial_pool(self.campaign, event=self.event)
                self.checkpoint()
            for method in self.campaign.search.methods:
                self.state["arm_start_elapsed"].setdefault(method, self.elapsed())
                controller = Controller(self.campaign, method, self.state["shared_pool"], self.identifier,
                                        state=self.state["controllers"].get(method), event=self.event)
                while True:
                    if self.stopped():
                        return self.finish("PARTIAL")
                    group = controller.ask()
                    if not group:
                        break
                    self.state["controllers"][method] = controller.checkpoint()
                    self.checkpoint()
                    evaluated = self.evaluate(group, "training")
                    controller.tell(evaluated)
                    self.state["controllers"][method] = controller.checkpoint()
                    by_id = {candidate["id"]: candidate for candidate in self.state["candidates"]}
                    by_id.update({candidate["id"]: candidate for candidate in controller.candidates})
                    self.state["candidates"] = list(by_id.values())
                    self.activity(phase="SEARCH", arm=method, generation=controller.generation,
                                  completed_candidates=sum(state["completed"] for state in self.state["controllers"].values()),
                                  training_incumbent=controller.winner()["score"] if controller.winner() else None)
                    boundary = self.safe_boundary()
                    if boundary:
                        return self.finish(boundary)
                if controller.winner():
                    winner = controller.winner()
                    self.state["frozen_winners"] = [candidate for candidate in self.state["frozen_winners"] if candidate["arm"] != method] + [winner]
                    self.event("TRAINING_WINNER_FROZEN", {"arm": method, "candidate_id": winner["id"], "program_hash": winner["program"]["hash"], "score": winner["score"]})
                self.state["controllers"][method] = controller.checkpoint()
                self.checkpoint()
            self.state["phase"] = "HOLDOUT"
        if self.state["phase"] == "HOLDOUT":
            if self.stopped():
                return self.finish("PARTIAL")
            selected = [candidate for candidate in self.state["candidates"] if candidate["arm"] in ("controls", "fixed")]
            selected += self.state["frozen_winners"]
            evaluated = self.evaluate(selected, "holdout") if selected else []
            by_id = {candidate["id"]: candidate for candidate in self.state["candidates"]}
            by_id.update({candidate["id"]: candidate for candidate in evaluated})
            self.state["candidates"] = list(by_id.values())
            self.state["phase"] = "REPLAYS"
            boundary = self.safe_boundary()
            if boundary:
                return self.finish(boundary)
        if self.state["phase"] == "REPLAYS":
            self.automatic_replays()
            self.state["phase"] = "REPORT"
            self.checkpoint()
        return self.finish("PARTIAL" if self.stopped() else "COMPLETED")

    def finish(self, status: str) -> dict:
        self.checkpoint()
        if status == "PAUSED" or status == "INTERRUPTED":
            return {"state": status, "elapsed_execution_seconds": self.elapsed()}
        for name, values in (("programs", self.state["candidates"]), ("genealogy", [
                {key: candidate.get(key) for key in ("id", "arm", "parent_id", "parent_hash", "mutation", "origin", "program")}
                for candidate in self.state["candidates"]])):
            with open_jsonl_writer(self.directory / (name + ".jsonl.gz")) as stream:
                for value in values:
                    stream.write(json.dumps(value, allow_nan=False, separators=(",", ":")) + "\n")
        summary = {"schema": "asquerix-lab-summary-v1", "id": self.identifier, "state": status,
                   "stop_reason": "EXECUTION_DEADLINE" if self.deadline_reached else "USER_STOP" if self.signal.value >= 2 else None,
                   "elapsed_execution_seconds": self.elapsed(), "datasets": getattr(self, "metadata", {}),
                   "profile_hash": digest(self.campaign.profile()), "executable_hash": self.state["executable_hash"],
                   "completed_candidates": sum(state["completed"] for state in self.state["controllers"].values()),
                   "logical_candidate_budget": self.campaign.plan()["candidate_evaluations"],
                   "submitted_episode_attempts": self.state["submitted_episode_attempts"],
                   "completed_episode_executions": self.state["completed_episode_executions"],
                   "replay_executions": self.state["replay_executions"],
                   "cache_hits": sum(state["cache_hits"] for state in self.state["controllers"].values()),
                   "controllers": {method: {key: state[key] for key in ("completed", "generation", "outcome", "cache_hits", "parent_id")}
                                   for method, state in self.state["controllers"].items()},
                   "frozen_winners": [{"candidate_id": candidate["id"], "arm": candidate["arm"], "program_hash": candidate["program"]["hash"], "score": candidate["score"]}
                                      for candidate in self.state["frozen_winners"]],
                   "replays": self.state["replays"], "replay_omissions": self.state.get("replay_omissions", []),
                   "chunks": self.state["chunks"], "timings": self.state["timings"], "pause_drains": self.state["pause_drains"],
                   "stop_drain_seconds": max(0, time.time() - self.signal_since.value) if self.signal.value >= 2 else None,
                   "scientific_caveat": "Functional pilot; no claim of optimality or statistically established method superiority."}
        write_json(self.directory / "summaries.json.gz", summary)
        self.event("COMPUTATION_FINALIZED", {"state": status, "completed_candidates": summary["completed_candidates"],
                                              "completed_episode_executions": summary["completed_episode_executions"]})
        return summary


def worker_main(tasks, replies, signal, signal_since, token: str, parent_pid: int, parent_start: str):
    # Ctrl+C in the terminal reaches the whole process group. The owning service
    # stops this worker through `signal` and the task queue, never mid-launch.
    os_signal.signal(os_signal.SIGINT, os_signal.SIG_IGN)
    launch_identity = digest(executable_identity())
    def emit(message):
        while True:
            if not alive(parent_pid, parent_start):
                signal.value = 2
                return
            try:
                replies.put(message, timeout=1)
                return
            except queue.Full:
                continue

    emit({"type": "ready", "token": token, "pid": os.getpid(), "process_start": process_start(os.getpid())})
    while alive(parent_pid, parent_start):
        try:
            job = tasks.get(timeout=1)
        except queue.Empty:
            continue
        if job is None:
            return
        try:
            if digest(executable_identity()) != launch_identity:
                raise InterruptedError("Owned worker source changed since spawn; restart before new task admission")
            if job.get("kind") == "replay":
                from .trace import replay
                campaign = Campaign.model_validate(job["spec"])
                options = campaign.document()
                options["recording"].update({"mode": job["options"]["mode"], "max_frames_per_trace": job["options"]["max_frames"],
                                             "max_trace_mib": job["options"]["max_mib"]})
                campaign = Campaign.model_validate(options)
                root = Path(job["directory"])
                metadata, banks = load_banks(root)
                reference = load_npz(root / job["row"]["numeric_path"])
                destination = root / "collections" / job["replay_id"]
                destination.mkdir(parents=True, exist_ok=True)
                result = replay(campaign, destination, candidate=job["candidate"], row=job["row"],
                                bank=banks[job["row"]["bank"]], reference_arrays=reference,
                                reference_index=job["row"]["numeric_index"], provenance=read_json(root / "environment.json.gz"),
                                cancelled=lambda: signal.value >= 2)
                if sum(item["size_bytes"] for item in result["artifacts"]) > job["options"]["max_mib"] * 1024**2:
                    raise OSError("On-demand trace collection exceeded its declared size cap")
                write_json(destination / "collection.json.gz", result)
                for artifact in result["artifacts"]:
                    artifact["path"] = str(Path("collections") / job["replay_id"] / artifact["path"])
                emit({"type": "replay_finished", "campaign_id": job["id"], "replay_id": job["replay_id"], "replay": result})
                continue
            campaign = CampaignWorker(job, emit=emit, signal=signal, signal_since=signal_since)
            result = campaign.run()
            emit({"type": "finished", "campaign_id": job["id"], "summary": result})
        except BaseException as error:
            emit({"type": "failed", "campaign_id": job["id"], "error": str(error),
                  "traceback": traceback.format_exc(limit=12)})
