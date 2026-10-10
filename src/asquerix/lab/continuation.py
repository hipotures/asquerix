"""Continue a finished search as a new campaign on the same frozen datasets and profile.

The parent stays immutable. The child copies the parent's banks, result chunks
and selected trajectories, takes over its controller checkpoints (including
RNG state and incumbents) and adds candidates. Only settings that do not change
what an episode computes may differ from the parent.
"""

from __future__ import annotations

import copy
from pathlib import Path
import shutil

from ..persistence import read_json
from .config import Campaign, digest
from .storage import executable_identity

# Sources that determine episode results, rankings and the proposed programs; they must match.
KERNEL_FILES = ("gpu.py", "geometry.py", "lab/gpu.py", "lab/strategy.py", "lab/evaluation.py", "lab/search.py")
EDITABLE = ("name", "description", "device", "batch_capacity", "slice_sweeps", "slice_dispatches",
            "recording", "limits", "publication", "time_budget_seconds")
INHERITED_PATHS = ("initial-bank.npz", "datasets.json.gz", "evaluations", "trajectories", "candidates.jsonl.gz")


def continuation_spec(parent: dict, additional: int, overrides: dict) -> Campaign:
    unknown = set(overrides) - set(EDITABLE)
    if unknown:
        raise ValueError(f"A continuation cannot change {', '.join(sorted(unknown))}; clone the campaign instead")
    spec = copy.deepcopy(parent["spec"])
    if not spec["search"]["methods"]:
        raise ValueError("This campaign has no search method to continue")
    if not 1 <= additional <= 1_000_000:
        raise ValueError("Additional candidates per method must be between 1 and 1,000,000")
    time_budget = overrides.pop("time_budget_seconds", None)
    for key, value in overrides.items():
        spec[key] = {**spec[key], **value} if isinstance(spec.get(key), dict) else value
    spec["search"]["candidate_budget_per_method"] = min(1_000_000, spec["search"]["candidate_budget_per_method"] + additional)
    # A stopping rule, not a comparability setting: the continuation may search for a time instead.
    spec["search"]["time_budget_seconds"] = time_budget
    if time_budget:
        spec["limits"]["max_seconds"] = max(spec["limits"]["max_seconds"], time_budget + 600)
    spec["continuation_of"] = parent["id"]
    return Campaign.model_validate(spec)


def compatibility(parent_directory: Path, campaign: Campaign) -> dict:
    """Check that a continuation can take over the parent's search.

    Numerical code that changed since the parent ran is recorded in the provenance, not refused.
    """
    environment = read_json(parent_directory / "environment.json.gz")
    summary = read_json(parent_directory / "summaries.json.gz")
    old, now = environment["executable_identity"], executable_identity()
    changed = [name for name in KERNEL_FILES if old["sources"].get(name) != now["sources"].get(name)]
    if old["dependencies"] != now["dependencies"] or old["python"] != now["python"]:
        changed.append("dependencies/python")
    if summary.get("profile_hash") != digest(campaign.profile()):
        raise ValueError("Evaluation profile differs from the parent campaign")
    if summary.get("state") not in ("COMPLETED", "PARTIAL"):
        raise ValueError("Only finished (completed or partial) campaigns can be continued")
    return {"parent_executable_hash": environment["executable_hash"], "changed_numerical_files": changed,
            "differing_orchestration_files": sorted(name for name in set(old["sources"]) | set(now["sources"])
                                                    if name not in KERNEL_FILES and old["sources"].get(name) != now["sources"].get(name))}


def inherit(campaign: Campaign, directory: Path, parent_directory: Path, parent_checkpoint: Path) -> dict:
    """Copy parent evidence into the child directory and return the child's starting checkpoint state."""
    provenance = compatibility(parent_directory, campaign)
    for name in INHERITED_PATHS:
        source = parent_directory / name
        if source.is_dir():
            shutil.copytree(source, directory / name, dirs_exist_ok=True)
        elif source.is_file():
            shutil.copy2(source, directory / name)
    state = read_json(parent_checkpoint)
    for controller in state["controllers"].values():
        if controller["outcome"] in ("CANDIDATE_BUDGET_REACHED", "TIME_BUDGET_REACHED"):  # a new budget lets the same search go on
            controller["outcome"] = "RUNNING"
    prior = dict(state.get("arm_elapsed", {}))
    state.pop("arm_clock", None)  # a time budget counts the continuation's own search time
    state["continuation"] = {"parent_id": campaign.continuation_of, **provenance,
                             "inherited_candidates": sum(item["completed"] for item in state["controllers"].values()),
                             "inherited_episode_executions": state["completed_episode_executions"],
                             "parent_execution_seconds": state["elapsed_execution_seconds"], "catalog_synced": False}
    state.update(phase="SEARCH", arm_start_elapsed={}, arm_prior_elapsed=prior, elapsed_execution_seconds=0.0, pause_drains=[])
    for key in ("manifest_hash", "executable_hash"):
        state.pop(key, None)
    return state
