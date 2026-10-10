"""All-best-pose CPU validation, stable episode keys, and deterministic ranking."""

from __future__ import annotations

from collections import Counter
import math
import statistics

import numpy as np

from ..geometry import validate_pose
from .config import Campaign, digest


def episode_key(program_hash: str, bank_hash: str, initial_id: str, replicate: str, profile_hash: str) -> str:
    return digest({"program": program_hash, "bank": bank_hash, "initial_id": initial_id,
                   "replicate": replicate, "profile": profile_hash})


def result_row(campaign: Campaign, state: np.void, best: np.ndarray, current: np.ndarray,
               *, program_hash: str, bank_hash: str, initial_id: str, replicate: str,
               validations: tuple[dict, dict] | None = None, profile_hash: str | None = None) -> dict:
    """One episode's record. `validations` may carry the (best, current) results of `validate_poses` for
    this episode, which equal `validate_pose`; `profile_hash` may carry digest(campaign.profile())."""
    from .gpu import OUTCOMES, TERMINATIONS, defined_fields
    if validations is None:
        validations = (validate_pose(best, float(state["best_side"]), 1e-9),
                       validate_pose(current, float(state["result"]["side"]), 1e-9))
    best_validation, current_validation = validations
    profile_hash = profile_hash or digest(campaign.profile())
    termination = TERMINATIONS[int(state["termination"])]
    eligible = (int(state["termination"]) in (1, 2, 3)
                and int(state["best_feasible"]) == 1
                and best_validation["status"] == "NUMERICALLY_VALIDATED")
    values = {}
    for name, array in defined_fields(np.asarray([state], dtype=state.dtype)).items():
        scalar = array[0]
        values[name] = str(int(scalar)) if scalar.dtype == np.dtype("uint64") else scalar.item()
    reserved = 2 * (2 * campaign.n + campaign.n * (campaign.n - 1) // 2) + campaign.n
    return {"episode_key": episode_key(program_hash, bank_hash, initial_id, replicate, profile_hash),
            "program_hash": program_hash, "bank_hash": bank_hash, "profile_hash": profile_hash,
            "initial_id": initial_id, "replicate": replicate, "best_L": float(state["best_side"]),
            "current_L": float(state["result"]["side"]), "termination": termination,
            "operation_outcome": OUTCOMES[int(state["last_outcome"])], "gpu_feasible": bool(state["best_feasible"]),
            "validation": best_validation, "current_validation": current_validation,
            "eligible": eligible, "charged_work": int(state["work"]) + reserved,
            "body_work": int(state["work"]), "reserved_finalization_work": reserved, "defined_fields": values}


def score(rows: list[dict], *, expected_count: int, instruction_count: int, program_hash: str,
          thresholds: list[float]) -> dict:
    ordered = sorted(rows, key=lambda row: (int(row["initial_id"]), int(row["replicate"]), row["episode_key"]))
    unique = {row["episode_key"] for row in ordered}
    complete = len(ordered) == expected_count and len(unique) == expected_count and all(row["termination"] != "CANCELLED" for row in ordered)
    eligible = complete and all(row["eligible"] for row in ordered)
    values = [row["best_L"] for row in ordered]
    work = [row["charged_work"] for row in ordered]
    mean = math.fsum(values) / len(values) if values else None
    median = statistics.median(values) if values else None
    mean_work = math.fsum(work) / len(work) if work else None
    quantiles = {str(q): float(np.quantile(np.asarray(values, dtype=np.float64), q)) for q in (0.1, 0.25, 0.75, 0.9)} if values else {}
    return {"complete": complete, "eligible": eligible, "completed_episodes": len(ordered),
            "expected_episodes": expected_count, "mean_best_L": mean, "median_best_L": median,
            "best_L": min(values) if values else None, "worst_L": max(values) if values else None,
            "stddev_best_L": statistics.pstdev(values) if values else None,
            "quantiles": quantiles, "mean_charged_work": mean_work, "total_charged_work": sum(work),
            "validation_counts": dict(Counter(row["validation"]["status"] for row in ordered)),
            "termination_counts": dict(Counter(row["termination"] for row in ordered)),
            "threshold_hits": {str(threshold): sum(value <= threshold for value in values) for threshold in thresholds},
            "instruction_count": instruction_count, "program_hash": program_hash,
            "ranking_tuple": [mean, median, mean_work, instruction_count, program_hash] if eligible else None,
            "aggregation": "math.fsum/float64 in initial-ID, replicate, episode-key order; population standard deviation"}


def best_eligible(candidates: list[dict]) -> dict | None:
    valid = [candidate for candidate in candidates if candidate.get("score", {}).get("eligible")]
    return min(valid, key=lambda candidate: tuple(candidate["score"]["ranking_tuple"])) if valid else None


def paired_comparison(left: list[dict], right: list[dict]) -> dict:
    by_identity = {(row["initial_id"], row["replicate"]): row for row in right}
    differences = []
    for row in sorted(left, key=lambda item: (int(item["initial_id"]), int(item["replicate"]))):
        other = by_identity.get((row["initial_id"], row["replicate"]))
        if other and (row["bank_hash"], row["profile_hash"]) == (other["bank_hash"], other["profile_hash"]):
            differences.append({"initial_id": row["initial_id"], "replicate": row["replicate"],
                                "difference_L": row["best_L"] - other["best_L"],
                                "both_valid": row["eligible"] and other["eligible"],
                                "left_episode": row["episode_key"], "right_episode": other["episode_key"]})
    return {"pairs": differences, "mean_difference_L": math.fsum(x["difference_L"] for x in differences) / len(differences) if differences else None,
            "scope": "Matched common initial worlds and profile; left best L minus right best L"}
