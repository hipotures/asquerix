"""Owned spawned worker; CUDA starts only after selecting an immutable campaign."""

from __future__ import annotations

from concurrent.futures import Future, ProcessPoolExecutor
import gzip
import json
import os
from pathlib import Path
import queue
import signal as os_signal
import time
import traceback

import numpy as np

from ..persistence import open_jsonl_writer, read_json, read_jsonl, write_json
from .config import RETAINED_PER_METHOD, Campaign, digest
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


# Validation dominates group time on the CPU while the GPU waits; leave two cores for the service and display.
VALIDATION_PROCESSES = max(1, min(16, (os.cpu_count() or 2) - 2))
PARALLEL_VALIDATION_MINIMUM = 128


def _result_row(campaign: Campaign, item: tuple) -> dict:
    state, best, current, program_hash, bank_hash, initial_id, replicate = item
    return result_row(campaign, state, best, current, program_hash=program_hash, bank_hash=bank_hash,
                      initial_id=initial_id, replicate=replicate)


def _result_chunk(campaign: Campaign, items: list[tuple]) -> list[dict]:
    return [_result_row(campaign, item) for item in items]


def _validate_chunk(campaign: Campaign, chunk: dict) -> list[dict]:
    """Validate a chunk of episodes and finish their rows, in a pool process; arrays travel as whole blocks."""
    rows = []
    for index in range(len(chunk["states"])):
        row = result_row(campaign, chunk["states"][index], chunk["best"][index], chunk["current"][index],
                         program_hash=chunk["program_hashes"][index], bank_hash=chunk["bank_hash"],
                         initial_id=chunk["initial_ids"][index], replicate=chunk["replicates"][index])
        candidate_id = chunk["candidate_ids"][index]
        row.update({"candidate_id": candidate_id, "bank": chunk["bank"], "arm": chunk["arms"][index],
                    "task_id": digest({"campaign": chunk["identifier"], "candidate": candidate_id, "episode": row["episode_key"]}),
                    "execution_attempt": chunk["attempt"],
                    "timing_scope": "Shared strategy batch; GPU time is not an isolated per-program measurement"})
        rows.append(row)
    return rows


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
            # Code may change between pauses; each identity used by the campaign is recorded.
            if self.state["executable_hash"] != digest(executable_identity()):
                self.state.setdefault("executable_history", [self.state["executable_hash"]])
        elif self.campaign.continuation_of:
            from .continuation import inherit
            parent = self.campaign.continuation_of
            self.state = inherit(self.campaign, self.directory, self.directory.parent / parent,
                                 self.checkpoint_path.parent / (parent + ".json.gz"))
        self.state["manifest_hash"] = digest(self.campaign.document())
        self.state["executable_hash"] = digest(executable_identity())
        if "executable_history" in self.state and self.state["executable_history"][-1] != self.state["executable_hash"]:
            self.state["executable_history"].append(self.state["executable_hash"])
        self.elapsed_before = self.state["elapsed_execution_seconds"]
        self.last_activity = 0.0
        self.deadline_reached = False
        self.time_cut = None  # execution-elapsed second at which a method's time budget ends, during its groups
        self.pool = None

    def elapsed(self):
        return self.elapsed_before + time.monotonic() - self.execution_start

    def cut(self):
        return self.time_cut is not None and self.elapsed() >= self.time_cut

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
        """Report progress; a new phase or stage (what the worker is doing now, e.g. GPU or CPU work) is sent at once."""
        now = time.monotonic()
        stage = values.get("stage")
        changed = stage is not None and stage != getattr(self, "last_stage", None)
        if changed:
            self.last_stage, self.stage_since = stage, time.time()
        if stage is not None:  # cleared fields replace the previous stage's values in the merged summary
            values.update({"stage_done": values.get("stage_done"), "stage_total": values.get("stage_total"), "stage_since": self.stage_since})
        if phase is not None or changed or now - self.last_activity > 2:
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

    def retained(self, candidates: list[dict], scores: dict, bank_name: str) -> set[str]:
        """Programs whose exact poses and episode rows are kept permanently in the group's files.

        With "important" evidence these are controls, fixed programs and every program that improved its
        method's best mean or best single episode; the current top programs of each method are kept separately in a replaceable file.
        """
        if self.campaign.pose_evidence == "all" or bank_name != "training":
            return {candidate["id"] for candidate in candidates}
        keep, best, single = set(), self.state.setdefault("arm_best", {}), self.state.setdefault("arm_best_single", {})
        for candidate in candidates:
            score = scores[candidate["id"]]
            if candidate["arm"] in ("controls", "fixed"):
                keep.add(candidate["id"])
            elif score.get("eligible") and (candidate["arm"] not in best or tuple(score["ranking_tuple"]) < tuple(best[candidate["arm"]])):
                best[candidate["arm"]] = score["ranking_tuple"]
                keep.add(candidate["id"])
            if score.get("eligible") and score.get("best_L") is not None and (candidate["arm"] not in single or score["best_L"] < single[candidate["arm"]]):
                single[candidate["arm"]] = score["best_L"]
                keep.add(candidate["id"])
        return keep

    def update_top(self, candidates: list[dict], scores: dict, rows: list[dict], arrays: dict):
        """Rewrite each method's top-RETAINED_PER_METHOD evidence when the group changes it.

        The files on disk are the source of truth, so a resumed campaign continues from what was written.
        """
        if self.campaign.pose_evidence != "important":
            return
        for arm in {candidate["arm"] for candidate in candidates} - {"controls", "fixed"}:
            stem = self.directory / "evaluations" / f"top-{arm}"
            current_rows = list(read_jsonl(stem.with_suffix(".jsonl.gz"))) if stem.with_suffix(".jsonl.gz").exists() else []
            current = load_npz(stem.with_suffix(".npz")) if current_rows else None
            entries = {}
            for index, row in enumerate(current_rows):
                entries.setdefault(row["candidate_id"], {"rank": tuple(row["ranking_tuple"]), "rows": [], "indices": [], "source": "old"})
                entries[row["candidate_id"]]["rows"].append(row)
                entries[row["candidate_id"]]["indices"].append(index)
            # Only this group's best RETAINED_PER_METHOD programs can enter the top list; skip the others' rows.
            contenders = set(sorted((identifier for identifier, score in scores.items()
                                     if score.get("eligible") and identifier.split(":")[-2] == arm),
                                    key=lambda identifier: tuple(scores[identifier]["ranking_tuple"]))[:RETAINED_PER_METHOD])
            for index, row in enumerate(rows):
                if row["candidate_id"] not in contenders:
                    continue
                score = scores.get(row["candidate_id"])
                if row["arm"] != arm or not score or not score.get("eligible") or row["candidate_id"] in entries and entries[row["candidate_id"]]["source"] == "old":
                    continue
                entries.setdefault(row["candidate_id"], {"rank": tuple(score["ranking_tuple"]), "rows": [], "indices": [], "source": "new"})
                entries[row["candidate_id"]]["rows"].append({**row, "ranking_tuple": score["ranking_tuple"]})
                entries[row["candidate_id"]]["indices"].append(index)
            chosen = sorted(entries.items(), key=lambda item: item[1]["rank"])[:RETAINED_PER_METHOD]
            if [identifier for identifier, _ in chosen] == list(dict.fromkeys(row["candidate_id"] for row in current_rows)):
                continue
            names = list(arrays) if arrays else list(current)
            kept = {name: np.concatenate([(current if entry["source"] == "old" else arrays)[name][entry["indices"]] for _, entry in chosen])
                    for name in names}
            kept_rows = []
            for _, entry in chosen:
                for row in entry["rows"]:
                    kept_rows.append({**row, "numeric_path": f"evaluations/top-{arm}.npz", "numeric_index": len(kept_rows)})
            check_quota(self.campaign, self.directory, reserve=len(kept_rows) * (24 * self.campaign.n + 2048))
            numeric = write_npz(stem.with_suffix(".npz"), kept)
            with open_jsonl_writer(stem.with_suffix(".jsonl.gz")) as stream:
                for row in kept_rows:
                    stream.write(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n")
            write_json(stem.with_suffix(".done.json.gz"), {"schema": "asquerix-lab-top-evidence-v1", "arm": arm,
                       "numeric_path": f"evaluations/top-{arm}.npz", "records_path": f"evaluations/top-{arm}.jsonl.gz",
                       "numeric_sha256": sha256(numeric), "records_sha256": sha256(stem.with_suffix(".jsonl.gz")),
                       "programs": [identifier for identifier, _ in chosen], "count": len(kept_rows)})

    def evaluate(self, candidates: list[dict], bank_name: str) -> list[dict]:
        """Evaluate one group on the GPU, validate every episode and keep evidence by the campaign policy.

        A group's results are admitted atomically: its first part's receipt, written last, records every
        program's score, so a resumed campaign never evaluates a finished group again.
        """
        from .gpu import StreamingBatch, defined_fields
        bank = self.banks[bank_name]
        episodes_per_candidate = len(bank["ids"]) * self.campaign.operator_replicates
        total = len(candidates) * episodes_per_candidate
        group_hash = digest({"candidates": [candidate["id"] for candidate in candidates], "bank": bank_name})[:16]
        head = self.directory / "evaluations" / f"part-{group_hash}-0000.done.json.gz"
        if head.exists():
            receipt = read_json(head)
            parts = [receipt] + [read_json(self.directory / "evaluations" / f"part-{group_hash}-{index:04d}.done.json.gz")
                                 for index in range(1, receipt.get("group_parts", 1))]
            for part in parts:
                if sha256(self.directory / part["numeric_path"]) != part["numeric_sha256"] or sha256(self.directory / part["records_path"]) != part["records_sha256"]:
                    raise ValueError("Finalized result chunk checksum mismatch during reconciliation")
            keep = set(receipt.get("retained_candidates", [candidate["id"] for candidate in candidates]))
            scores = receipt.get("candidate_scores")
            if scores is None:  # receipts that keep every episode carry no separate scores
                rows = [row for part in parts for row in read_jsonl(self.directory / part["records_path"])]
                scores = self.scores(candidates, rows, episodes_per_candidate)
            for part in parts:
                self.emit({"type": "chunk", "campaign_id": self.identifier, "records": part["records_path"]})
                self.remember_chunk(part)
        else:
            if self.stopped():  # a stop before the group starts: nothing to record, the group stays pending
                return [{**candidate, "score": {"complete": False}} for candidate in candidates]
            rows, arrays = [], []
            programs = [compile_program(candidate["program"]["authored"]) for candidate in candidates]
            attempt = self.state["group_attempts"].get(group_hash, 0) + 1
            self.state["group_attempts"][group_hash] = attempt
            timing = {"validation_seconds": 0.0, "simulation_seconds": 0.0, "device_seconds": 0.0, "transfer_seconds": 0.0}
            self.event("TASK_GROUP_STARTED", {"group": group_hash, "bank": bank_name, "episodes": total, "attempt": attempt,
                                              "candidate_ids": [candidate["id"] for candidate in candidates]})
            self.activity(phase=bank_name.upper(), arm=candidates[0]["arm"], generation=candidates[0]["generation"], active_episodes=total,
                          stage="CPU: preparing group (compiling programs, uploading worlds)", stage_total=len(candidates))
            if not self.stopped():
                setup_start = time.monotonic()
                indices = np.arange(total, dtype=np.int64)
                pids = (indices // episodes_per_candidate).astype(np.int32)
                local = indices % episodes_per_candidate
                initial_slots = (local // self.campaign.operator_replicates).astype(np.int32)
                replicates = (local % self.campaign.operator_replicates).astype(np.uint64)
                self.state["submitted_episode_attempts"] += total
                # GPU slots are refilled as episodes finish, so long programs do not leave the GPU idle.
                batch = StreamingBatch(self.campaign, programs, bank["poses"][initial_slots],
                                       bank["initial_results"][initial_slots], bank["ids"][initial_slots], replicates, pids)
                setup_seconds = time.monotonic() - setup_start
                # An exhausted time budget or a stop cancels the group in flight. Finished episodes are validated
                # by the process pool while the GPU keeps simulating; validation is a pure function of each episode.
                cancelled, waiting, futures = False, [], []
                hashes = [candidate["program"]["hash"] for candidate in candidates]
                identities = [candidate["id"] for candidate in candidates]
                arm_names = [candidate["arm"] for candidate in candidates]
                stream_pids, stream_slots, stream_replicates = pids, initial_slots, replicates  # stream positions, never remapped

                def submit(indices):
                    indices = np.asarray(indices, dtype=np.int64)
                    owners = stream_pids[indices]
                    return self.validate_async({
                        "states": batch.states[indices], "best": batch.best[indices], "current": batch.current[indices],
                        "program_hashes": [hashes[owner] for owner in owners], "candidate_ids": [identities[owner] for owner in owners],
                        "arms": [arm_names[owner] for owner in owners], "initial_ids": [str(int(value)) for value in bank["ids"][stream_slots[indices]]],
                        "replicates": [str(int(value)) for value in stream_replicates[indices]],
                        "identifier": self.identifier, "bank": bank_name, "bank_hash": bank["hash"], "attempt": attempt})

                chunk = max(512, min(8192, total // (VALIDATION_PROCESSES * 4)))
                while True:
                    cancel = self.stopped() or self.cut()
                    cancelled = cancelled or cancel
                    done = batch.advance(cancel=cancel)
                    if not cancelled:
                        waiting.extend(batch.newly.tolist())
                        while len(waiting) >= chunk:
                            indices, waiting = waiting[:chunk], waiting[chunk:]
                            futures.append((indices, submit(indices)))
                    if done:
                        break
                    self.activity(active_episodes=total, stage="GPU: simulating episodes", stage_done=int(batch.collected.sum()), stage_total=total)
                for key in ("simulation_seconds", "device_seconds", "transfer_seconds"):
                    timing[key] += batch.timings.get(key, 0.0)
                timing["setup_seconds"] = setup_seconds
                order = np.arange(total)
                if cancelled and not self.stopped():
                    # Time budget cut: programs whose every episode finished are admitted as a smaller group;
                    # the rest are dropped unevaluated.
                    finished = batch.collected & (batch.states["termination"] != 6)
                    complete = finished.reshape(len(candidates), episodes_per_candidate).all(axis=1)
                    self.event("TASK_GROUP_TRUNCATED", {"group": group_hash, "complete_candidates": int(complete.sum()),
                                                        "dropped_candidates": int((~complete).sum())})
                    if complete.any():
                        selected = np.repeat(complete, episodes_per_candidate)
                        order = np.flatnonzero(selected)  # stream positions of the admitted episodes
                        candidates = [candidate for candidate, flag in zip(candidates, complete) if flag]
                        total = len(candidates) * episodes_per_candidate
                        initial_slots, replicates = initial_slots[selected], replicates[selected]
                        pids = (np.arange(total) // episodes_per_candidate).astype(np.int32)
                        group_hash = digest({"candidates": [candidate["id"] for candidate in candidates], "bank": bank_name})[:16]
                        cancelled = False
                    else:
                        candidates = []
                if not cancelled and not self.stopped():
                    validation_start = time.monotonic()
                    self.activity(stage="CPU: validating poses", stage_total=total)
                    states, best, current = batch.states[order], batch.best[order], batch.current[order]
                    # Episodes not yet sent (the stream's tail, or a truncated group's) are validated now; rows
                    # already validated during the simulation are reused.
                    submitted = {index for indices, _ in futures for index in indices}
                    rest = [int(index) for index in order if int(index) not in submitted]
                    if rest:
                        futures.append((rest, submit(rest)))
                    by_index = {}
                    for indices, future in futures:
                        by_index.update(zip(indices, future.result()))
                    validated = [by_index[int(index)] for index in order]
                    timing["validation_seconds"] += time.monotonic() - validation_start
                    rows.extend(validated)
                    arrays.append({"best_poses": best, "current_poses": current, "initial_ids": bank["ids"][initial_slots],
                                   "replicates": replicates, "program_indices": pids,
                                   **{"state_" + name: array for name, array in defined_fields(states).items()}})
            executed = sum(row["termination"] != "CANCELLED" for row in rows)
            self.state["completed_episode_executions"] += executed
            self.activity(stage="CPU: scoring programs", stage_total=len(candidates))
            scoring_start = time.monotonic()
            scores = self.scores(candidates, rows, episodes_per_candidate)
            timing["scoring_seconds"] = time.monotonic() - scoring_start
            # Program generation for this group happened before it started; it is reported with the group.
            timing["generation_seconds"] = self.state.pop("generation_seconds", 0.0)
            keep = set()
            if len(rows) == total and executed == total:  # a group cut short by a stop is not admitted; a resume repeats it
                keep = self.retained(candidates, scores, bank_name)
                persist_start = time.monotonic()
                self.activity(stage="Disk: writing evidence", stage_total=len(keep))
                merged = {name: np.concatenate([part[name] for part in arrays]) for name in arrays[0]}
                mask = np.asarray([row["candidate_id"] in keep for row in rows])
                kept_rows = [row for row, flag in zip(rows, mask) if flag]
                kept = {name: array[mask] for name, array in merged.items()}
                part_size = 16384
                count_parts = max(1, -(-len(kept_rows) // part_size))
                receipts = []
                for index in reversed(range(count_parts)):  # the head part, written last, admits the group
                    stem = f"part-{group_hash}-{index:04d}"
                    numeric_relative, json_relative = f"evaluations/{stem}.npz", f"evaluations/{stem}.jsonl.gz"
                    window = slice(index * part_size, (index + 1) * part_size)
                    part_rows = kept_rows[window]
                    for offset, row in enumerate(part_rows):
                        row.update({"numeric_path": numeric_relative, "numeric_index": offset})
                    check_quota(self.campaign, self.directory, reserve=len(part_rows) * (24 * self.campaign.n + 2048))
                    numeric = write_npz(self.directory / numeric_relative, {name: array[window] for name, array in kept.items()})
                    with open_jsonl_writer(self.directory / json_relative) as stream:
                        for row in part_rows:
                            stream.write(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n")
                    receipt = {"schema": "asquerix-lab-result-chunk-v1", "group": stem, "count": len(part_rows),
                               "numeric_path": numeric_relative, "records_path": json_relative,
                               "numeric_sha256": sha256(numeric), "records_sha256": sha256(self.directory / json_relative),
                               "attempt": attempt, "completed_at": time.time(), "execution_elapsed_seconds": self.elapsed(),
                               "completed_episode_executions": sum(row["termination"] != "CANCELLED" for row in part_rows)}
                    if index == 0:
                        timing["persistence_seconds"] = time.monotonic() - persist_start
                        receipt.update({"group_parts": count_parts, "group_episode_executions": executed, "timings": timing,
                                        "retained_candidates": sorted(keep), "candidate_scores": scores})
                    write_json(self.directory / "evaluations" / (stem + ".done.json.gz"), receipt)
                    receipts.append(receipt)
                for receipt in reversed(receipts):
                    self.emit({"type": "chunk", "campaign_id": self.identifier, "records": receipt["records_path"]})
                    self.remember_chunk(receipt)
                if bank_name == "training":
                    self.activity(stage="Disk: updating top programs")
                    top_start = time.monotonic()
                    self.update_top(candidates, scores, rows, merged)
                    timing["top_seconds"] = time.monotonic() - top_start
                self.event("TASK_GROUP_COMPLETED", {"group": group_hash, "bank": bank_name, "episodes": total,
                                                    "retained_programs": len(keep), "timings": timing})
        evaluated, outgoing = [], []
        recording_start = time.monotonic()
        self.activity(stage="CPU: recording program results", stage_total=len(candidates))
        for candidate in candidates:
            result = {**candidate, "state": "EVALUATED" if scores[candidate["id"]]["complete"] else "INCOMPLETE",
                      "score" if bank_name == "training" else "holdout_score": scores[candidate["id"]],
                      "completed_at": time.time(), "execution_elapsed_seconds": self.elapsed()}
            result["arm_execution_elapsed_seconds"] = self.elapsed() - self.state["arm_start_elapsed"].get(candidate["arm"], 0.0)
            self.state.setdefault("arm_elapsed", {})[candidate["arm"]] = result["arm_execution_elapsed_seconds"]
            evaluated.append(result)
            summary = result.get("score") or result.get("holdout_score")
            outgoing.append({"type": "candidate", "campaign_id": self.identifier, "candidate": result})
            outgoing.append({"type": "event", "campaign_id": self.identifier, "kind": "CANDIDATE_RESULT" if bank_name == "training" else "HOLDOUT_RESULT",
                             "payload": {"candidate_id": result["id"], "arm": result["arm"], "bank": bank_name,
                                         "score": {key: summary.get(key) for key in ("complete", "eligible", "mean_best_L", "best_L", "ranking_tuple")},
                                         "program_hash": candidate["program"]["hash"], "execution_elapsed_seconds": self.elapsed()}})
        # Program results reach the service in a few large messages instead of two per program.
        for start in range(0, len(outgoing), 1024):
            self.emit({"type": "batch", "campaign_id": self.identifier, "messages": outgoing[start:start + 1024]})
        recording_seconds = time.monotonic() - recording_start
        self.activity(stage="Disk: candidate log and checkpoint")
        log_start = time.monotonic()
        self.remember(evaluated, keep)
        self.checkpoint()
        self.event("TASK_GROUP_RECORDED", {"bank": bank_name, "candidates": len(evaluated), "recording_seconds": recording_seconds,
                                           "log_checkpoint_seconds": time.monotonic() - log_start})
        return evaluated

    def scores(self, candidates: list[dict], rows: list[dict], episodes_per_candidate: int) -> dict:
        by_candidate = {candidate["id"]: [] for candidate in candidates}
        for row in rows:
            by_candidate[row["candidate_id"]].append(row)
        result = {}
        for candidate in candidates:
            started = time.monotonic()
            summary = score(by_candidate[candidate["id"]], expected_count=episodes_per_candidate,
                            instruction_count=candidate["program"]["instruction_count"],
                            program_hash=candidate["program"]["hash"], thresholds=self.campaign.thresholds)
            summary["scoring_seconds"] = time.monotonic() - started
            result[candidate["id"]] = summary
        return result

    def remember_chunk(self, receipt: dict):
        """Keep a small chunk index in the checkpoint; program scores stay in the receipt on disk."""
        entry = {key: value for key, value in receipt.items() if key not in ("candidate_scores", "retained_candidates")}
        if entry not in self.state["chunks"]:
            self.state["chunks"].append(entry)

    def remember(self, evaluated: list[dict], keep: set[str]):
        """Keep full records of programs with retained evidence; log every evaluated program."""
        log = self.directory / "candidates.jsonl.gz"
        with gzip.open(log, "at", encoding="utf-8") as stream:  # append-only; readers keep the last record per id
            for candidate in evaluated:
                stream.write(json.dumps(candidate, allow_nan=False, separators=(",", ":")) + "\n")
        permanent = self.state.setdefault("retained_ids", [])
        permanent.extend(sorted(keep - set(permanent)))
        wanted = set(permanent) | self.top_programs() | {candidate["id"] for candidate in self.state["frozen_winners"]}
        known = {candidate["id"]: candidate for candidate in self.state["candidates"]}
        for candidate in evaluated:
            if candidate["id"] in wanted:
                known[candidate["id"]] = {**known.get(candidate["id"], {}), **candidate}
        # Records stay for programs with evidence: permanent ones, the current best per method and winners.
        self.state["candidates"] = [candidate for identifier, candidate in known.items() if identifier in wanted]

    def result_rows(self, items: list[tuple]) -> list[dict]:
        """Independent CPU validation of every returned pose, spread over a process pool.

        Each row is the same pure `result_row` computation as a serial loop; only where it runs differs.
        """
        if len(items) < PARALLEL_VALIDATION_MINIMUM or VALIDATION_PROCESSES < 2:
            return [_result_row(self.campaign, item) for item in items]
        if self.pool is None:
            import multiprocessing
            self.pool = ProcessPoolExecutor(VALIDATION_PROCESSES, mp_context=multiprocessing.get_context("spawn"))
        # The campaign is sent once per chunk, not once per episode: pickling it per row kept the parent busy.
        size = max(1, -(-len(items) // (VALIDATION_PROCESSES * 4)))
        chunks = [items[start:start + size] for start in range(0, len(items), size)]
        return [row for rows in self.pool.map(_result_chunk, [self.campaign] * len(chunks), chunks) for row in rows]

    def validate_async(self, chunk: dict):
        """Start validating a chunk of episodes in the process pool; the rows keep the chunk's order."""
        if VALIDATION_PROCESSES < 2:
            future = Future()
            future.set_result(_validate_chunk(self.campaign, chunk))
            return future
        if self.pool is None:
            import multiprocessing
            self.pool = ProcessPoolExecutor(VALIDATION_PROCESSES, mp_context=multiprocessing.get_context("spawn"))
        return self.pool.submit(_validate_chunk, self.campaign, chunk)

    def close(self):
        if self.pool is not None:
            self.pool.shutdown()
            self.pool = None

    def top_files(self) -> list[dict]:
        return [read_json(path) for path in sorted((self.directory / "evaluations").glob("top-*.done.json.gz"))]

    def top_programs(self) -> set[str]:
        return {identifier for receipt in self.top_files() for identifier in receipt["programs"]}

    def all_rows(self) -> list[dict]:
        rows, seen = [], set()
        for chunk in self.state["chunks"] + self.top_files():
            for row in read_jsonl(self.directory / chunk["records_path"]):
                if (row["candidate_id"], row["episode_key"]) not in seen:
                    seen.add((row["candidate_id"], row["episode_key"]))
                    rows.append(row)
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
        for method in self.state["controllers"]:
            arm = [candidate for candidate in self.state["candidates"] if candidate["arm"] == method]
            by_id = {candidate["id"]: candidate for candidate in arm}
            replacement = next((candidate for candidate in reversed(arm)
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
            self.activity(phase="REPLAYS", candidate_id=candidate["id"], stage="GPU: recording replay of a selected episode")
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
        try:
            return self._run()
        finally:
            self.close()

    def _run(self) -> dict:
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
        self.emit({"type": "device", "campaign_id": self.identifier, "uuid": device.uuid,
                   "identity": self.provenance["executable_hash"]})
        write_json(self.directory / "campaign.json.gz", {"id": self.identifier, "spec": self.campaign.document(),
                                                        "plan": self.campaign.plan(), "profile": self.campaign.profile()})
        if not (self.directory / "environment.json.gz").exists():
            write_json(self.directory / "environment.json.gz", self.provenance)
        if not (self.directory / "datasets.json.gz").exists():
            self.activity(phase="PREPARING", stage="GPU: preparing starting worlds")
            metadata, timing = prepare_banks(self.campaign, self.directory, stop=self.stopped,
                                           progress=lambda value: self.activity(phase="PREPARING", **{key: val for key, val in value.items() if key != "phase"}))
            self.state["timings"].update(timing)
        self.metadata, self.banks = load_banks(self.directory)
        for candidate in self.state["candidates"]:
            self.emit({"type": "candidate", "campaign_id": self.identifier, "candidate": candidate})
        continuation = self.state.get("continuation")
        if continuation and not continuation["catalog_synced"]:  # make inherited episodes and replays browsable
            for chunk in self.state["chunks"]:
                self.emit({"type": "chunk", "campaign_id": self.identifier, "records": chunk["records_path"], "inherited": True})
            for replay in self.state["replays"]:
                self.emit({"type": "replay", "campaign_id": self.identifier, "replay": replay})
            self.event("CONTINUATION_STARTED", continuation)
            continuation["catalog_synced"] = True
            self.checkpoint()
        if self.state["phase"] in ("PREPARING", "CONTROLS"):
            self.state["phase"] = "CONTROLS"
            controls = self.fixed_candidates()
            for candidate in controls:
                self.emit({"type": "candidate", "campaign_id": self.identifier, "candidate": candidate})
                self.event("CANDIDATE_GENERATED", candidate)
            if controls:
                evaluated = self.evaluate(controls, "training")
                if not all(candidate["score"]["complete"] for candidate in evaluated):
                    return self.finish("PARTIAL")
            self.state["phase"] = "SEARCH"
            boundary = self.safe_boundary()
            if boundary:
                return self.finish(boundary)
        if self.state["phase"] == "SEARCH":
            if self.campaign.search.methods and self.state["shared_pool"] is None:
                self.state["shared_pool"] = initial_pool(self.campaign, event=self.event)
                self.checkpoint()
            budget = self.campaign.search.time_budget_seconds
            share = budget / len(self.campaign.search.methods) if budget and self.campaign.search.methods else None
            for method in self.campaign.search.methods:
                # A continuation resumes each method's clock where the parent left it.
                self.state["arm_start_elapsed"].setdefault(method, self.elapsed() - self.state.get("arm_prior_elapsed", {}).get(method, 0.0))
                # The time budget counts only this campaign's own search time for the method.
                clock = self.state.setdefault("arm_clock", {}).setdefault(method, self.elapsed())
                controller = Controller(self.campaign, method, self.state["shared_pool"], self.identifier,
                                        state=self.state["controllers"].get(method), event=self.event)
                # A continuation or resumed campaign shows its inherited counts before its first group finishes.
                self.activity(phase="SEARCH", arm=method, generation=controller.generation,
                              completed_candidates=sum(state["completed"] for state in self.state["controllers"].values()),
                              training_incumbent=controller.winner()["score"] if controller.winner() else None)
                while True:
                    if self.stopped():
                        return self.finish("PARTIAL")
                    if share is not None and not controller.pending and self.elapsed() - clock >= share:
                        controller.outcome = "TIME_BUDGET_REACHED"
                        self.event("TIME_BUDGET_REACHED", {"arm": method, "seconds": self.elapsed() - clock,
                                                           "completed_candidates": controller.completed})
                        break
                    self.activity(stage="CPU: generating programs")
                    generation_start = time.monotonic()
                    group = controller.ask()
                    self.state["generation_seconds"] = time.monotonic() - generation_start
                    if not group:
                        break
                    self.state["controllers"][method] = controller.checkpoint()
                    self.checkpoint()
                    self.time_cut = clock + share if share is not None else None
                    evaluated = self.evaluate(group, "training")
                    self.time_cut = None
                    if self.stopped() and not all(candidate["score"]["complete"] for candidate in evaluated):
                        return self.finish("PARTIAL")  # the interrupted group stays pending and is repeated later
                    if len(evaluated) < len(group):  # cut by the time budget: only fully finished programs were admitted
                        if evaluated:
                            controller.pending = [candidate for candidate in controller.pending if candidate["id"] in {item["id"] for item in evaluated}]
                            controller.tell(evaluated)
                        else:
                            controller.pending = []
                        controller.outcome = "TIME_BUDGET_REACHED"
                        self.state["controllers"][method] = controller.checkpoint()
                        self.event("TIME_BUDGET_REACHED", {"arm": method, "seconds": self.elapsed() - clock, "completed_candidates": controller.completed,
                                                           "dropped_group_candidates": len(group) - len(evaluated)})
                        break
                    controller.tell(evaluated)
                    self.state["controllers"][method] = controller.checkpoint()
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
            # Frozen winners are copies taken before holdout; an inherited winner's holdout result is in its latest record.
            latest = {candidate["id"]: candidate for candidate in self.state["candidates"]}
            selected = [latest.get(candidate["id"], candidate) for candidate in selected]
            selected = [candidate for candidate in selected if not candidate.get("holdout_score")]
            if selected:
                self.evaluate(selected, "holdout")
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
        self.activity(stage="Disk: writing summaries and checkpoint")
        self.checkpoint()
        if status == "PAUSED" or status == "INTERRUPTED":
            return {"state": status, "elapsed_execution_seconds": self.elapsed()}
        for name, values in (("programs", self.state["candidates"]), ("genealogy", [
                {key: candidate.get(key) for key in ("id", "arm", "parent_id", "parent_hash", "mutation", "origin", "program")}
                for candidate in self.state["candidates"]])):
            with open_jsonl_writer(self.directory / (name + ".jsonl.gz")) as stream:
                for value in values:
                    stream.write(json.dumps(value, allow_nan=False, separators=(",", ":")) + "\n")
        tops = self.top_files()
        for receipt in tops:  # final top programs become browsable; earlier versions were replaced on disk
            self.emit({"type": "chunk", "campaign_id": self.identifier, "records": receipt["records_path"]})
        summary = {"schema": "asquerix-lab-summary-v1", "id": self.identifier, "state": status,
                   "top_evidence": tops,
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
                   "continuation": self.state.get("continuation"),
                   "pose_evidence": self.campaign.pose_evidence, "time_budget_seconds": self.campaign.search.time_budget_seconds,
                   "evaluated_programs": sum(state["count"] for state in self.state["controllers"].values()),
                   "retained_programs": len(self.state["candidates"]),
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
