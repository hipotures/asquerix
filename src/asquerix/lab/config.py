"""Immutable campaign specifications, explicit generation laws, and preflight."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

from .strategy import Op, Selector, compile_program, control_program

SCHEMA = "asquerix-lab-campaign-v1"
RNG_VERSION = "splitmix64-operator-world-v1"
SCORING_VERSION = "eligible-f64-mean-median-work-size-hash-v1"


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, allow_nan=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def uint64(value: str) -> str:
    if type(value) is not str or not value.isascii() or not value.isdecimal() or not 0 <= int(value) < 2**64:
        raise ValueError("identity must be an unsigned uint64 decimal string")
    if str(int(value)) != value:
        raise ValueError("identity must use canonical decimal spelling")
    return value


PositiveInt = Annotated[StrictInt, Field(ge=1)]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, allow_inf_nan=False)


class Bank(Model):
    first_id: str
    valid_count: Annotated[StrictInt, Field(ge=1, le=4096)] = 64
    _id = field_validator("first_id")(uint64)

    @model_validator(mode="after")
    def bounded_replacements(self):
        if int(self.first_id) + 4 * self.valid_count > 2**64:
            raise ValueError("bank including bounded replacement IDs exceeds uint64")
        return self


class Datasets(Model):
    initializer_seed: str = "20261008"
    training: Bank = Bank(first_id="100000")
    holdout: Bank = Bank(first_id="200000")
    _seed = field_validator("initializer_seed")(uint64)

    @model_validator(mode="after")
    def disjoint(self):
        left = int(self.training.first_id)
        right = int(self.holdout.first_id)
        if max(left, right) < min(left + 4 * self.training.valid_count, right + 4 * self.holdout.valid_count):
            raise ValueError("training and holdout replacement ranges must be disjoint")
        return self


class Search(Model):
    methods: list[Literal["random_program_search", "one_plus_lambda"]] = ["random_program_search", "one_plus_lambda"]
    seed: str = "8001"
    candidate_budget_per_method: Annotated[StrictInt, Field(ge=1, le=1024)] = 32
    initial_pool: Annotated[StrictInt, Field(ge=1, le=128)] = 8
    lambda_: Annotated[StrictInt, Field(ge=1, le=128)] = Field(default=8, alias="lambda")
    shared_initial_pool: Literal[True] = True
    _seed = field_validator("seed")(uint64)

    @model_validator(mode="after")
    def valid_pool(self):
        if len(set(self.methods)) != len(self.methods):
            raise ValueError("search methods must be unique")
        if self.initial_pool > self.candidate_budget_per_method:
            raise ValueError("initial_pool must not exceed candidate budget")
        return self


class Interval(Model):
    minimum: float
    maximum: float

    @model_validator(mode="after")
    def order(self):
        if not 0 < self.minimum <= self.maximum:
            raise ValueError("parameter interval must be finite, positive, and ordered")
        return self


class Generation(Model):
    version: Literal["bounded-grammar-v1"] = "bounded-grammar-v1"
    min_nodes: Annotated[StrictInt, Field(ge=1, le=32)] = 4
    max_nodes: Annotated[StrictInt, Field(ge=1, le=32)] = 16
    weights: dict[str, Annotated[StrictInt, Field(ge=0, le=1000)]] = {
        "COMPRESS": 40, "EXPAND": 20, "ROTATE": 20, "MOVE": 15, "RESTORE_BEST": 5, "RELAX": 0}
    selectors: list[Literal["ALL", "RANDOM_K", "WALL_K"]] = ["ALL", "RANDOM_K", "WALL_K"]
    compress_fraction: Interval = Interval(minimum=0.01, maximum=0.10)
    expand_fraction: Interval = Interval(minimum=0.005, maximum=0.10)
    move_distance: Interval = Interval(minimum=0.005, maximum=0.20)
    rotate_angle_rad: Interval = Interval(minimum=0.01, maximum=0.30)
    attempt_min: Annotated[StrictInt, Field(ge=1, le=128)] = 4
    attempt_max: Annotated[StrictInt, Field(ge=1, le=128)] = 32
    sweep_min: Annotated[StrictInt, Field(ge=1, le=480)] = 120
    sweep_max: Annotated[StrictInt, Field(ge=1, le=480)] = 480
    k_min: Annotated[StrictInt, Field(ge=0, le=32)] = 1
    k_max: Annotated[StrictInt, Field(ge=0, le=32)] = 6
    repeat_probability: Annotated[float, Field(ge=0, le=1)] = 0.08
    condition_probability: Annotated[float, Field(ge=0, le=1)] = 0.05
    repeat_min: Annotated[StrictInt, Field(ge=1, le=8)] = 1
    repeat_max: Annotated[StrictInt, Field(ge=1, le=8)] = 4
    legacy_target_probability: Annotated[float, Field(ge=0, le=1)] = 0.25
    proposal_retries: Annotated[StrictInt, Field(ge=1, le=1000)] = 64
    mutation_weights: dict[str, Annotated[StrictInt, Field(ge=0, le=1000)]] = {
        "parameter": 30, "selector": 15, "insert": 15, "delete": 10,
        "replace": 15, "repeat": 10, "condition": 5}

    @model_validator(mode="after")
    def law(self):
        allowed = {op.name for op in Op if op.value <= 6}
        if not self.weights or set(self.weights) - allowed or sum(self.weights.values()) == 0:
            raise ValueError("operator weights must name allowed operators and have a positive sum")
        mutations = {"parameter", "selector", "insert", "delete", "replace", "repeat", "condition"}
        if set(self.mutation_weights) != mutations or not sum(self.mutation_weights.values()):
            raise ValueError("declare all seven mutation weights with a positive sum")
        if not self.selectors or len(set(self.selectors)) != len(self.selectors):
            raise ValueError("declare a nonempty unique selector allowlist")
        for low, high in ((self.min_nodes, self.max_nodes), (self.attempt_min, self.attempt_max),
                          (self.sweep_min, self.sweep_max), (self.k_min, self.k_max), (self.repeat_min, self.repeat_max)):
            if low > high:
                raise ValueError("minimum must not exceed maximum")
        for interval, cap in ((self.compress_fraction, 0.999), (self.expand_fraction, 0.25),
                              (self.move_distance, 0.5), (self.rotate_angle_rad, math.pi / 4)):
            if interval.maximum > cap:
                raise ValueError("generation parameter exceeds hard operator cap")
        return self


class WorkLimits(Model):
    dispatches: Annotated[StrictInt, Field(ge=1, le=256)] = 256
    compression_attempts: Annotated[StrictInt, Field(ge=1, le=128)] = 128
    contact_sweeps: Annotated[StrictInt, Field(ge=1, le=61440)] = 61440
    constraint_visits: Annotated[StrictInt, Field(ge=1, le=2**31 - 1)] | None = None

    def resolved(self, n: int) -> dict:
        visits = self.constraint_visits
        if visits is None:
            visits = self.contact_sweeps * (6 * n + n * (n - 1)) + self.dispatches * (8 * n + n * n + 1) + self.compression_attempts * (3 * n + 1)
        return {**self.model_dump(), "constraint_visits": visits}


class Recording(Model):
    automatic: bool = True
    mode: Literal["accepted", "sweeps"] = "accepted"
    max_traces: Annotated[StrictInt, Field(ge=0, le=8)] = 8
    max_frames_per_trace: Annotated[StrictInt, Field(ge=4, le=256)] = 256
    every: Annotated[StrictInt, Field(ge=1, le=1024)] = 16
    max_trace_mib: Annotated[float, Field(gt=0, le=10)] = 10.0


class Limits(Model):
    max_seconds: Annotated[float, Field(gt=0, le=86400)] = 600.0
    max_artifact_mib: Annotated[float, Field(gt=0, le=256)] = 256.0


class Publication(Model):
    enabled: bool = True


class Campaign(Model):
    schema_name: Literal["asquerix-lab-campaign-v1"] = Field(default=SCHEMA, alias="schema")
    name: Annotated[str, Field(min_length=1, max_length=160)]
    description: Annotated[str, Field(max_length=2000)] = ""
    n: Annotated[StrictInt, Field(ge=1, le=32)] = 11
    initial_side: Annotated[float, Field(gt=math.sqrt(2) + 0.00004, le=100)] = 10.0
    device: Annotated[str, Field(pattern=r"^cuda:[0-9]{1,2}$")] = "cuda:0"
    batch_capacity: Annotated[StrictInt, Field(ge=1, le=65536)] = 4096
    slice_sweeps: Annotated[StrictInt, Field(ge=1, le=128)] = 16
    slice_dispatches: Annotated[StrictInt, Field(ge=1, le=256)] = 32
    datasets: Datasets = Datasets()
    operator_seed: str = "20261009"
    operator_replicates: Annotated[StrictInt, Field(ge=1, le=16)] = 1
    evaluation_profile: Literal["rigid-square-lab-v1"] = "rigid-square-lab-v1"
    controls: list[Literal["legacy_compress", "pulse_rotate"]] = ["legacy_compress", "pulse_rotate"]
    search: Search = Search()
    generation: Generation = Generation()
    work_limits: WorkLimits = WorkLimits()
    recording: Recording = Recording()
    limits: Limits = Limits()
    publication: Publication = Publication()
    fixed_programs: Annotated[list[dict], Field(max_length=8)] = []
    thresholds: Annotated[list[float], Field(max_length=16)] = []
    _seed = field_validator("operator_seed")(uint64)

    @model_validator(mode="after")
    def semantic_validation(self):
        if len(set(self.controls)) != len(self.controls):
            raise ValueError("controls must be unique")
        if not self.search.methods and not self.fixed_programs and not self.controls:
            raise ValueError("select a search method, a control, or provide fixed programs")
        for program in self.fixed_programs:
            compile_program(program)
        if any(not 0 < threshold <= self.initial_side for threshold in self.thresholds):
            raise ValueError("thresholds must be finite, positive, and no larger than initial side")
        if self.plan()["estimated_native_bytes"] > self.limits.max_artifact_mib * 1024**2:
            raise ValueError("estimated native evidence exceeds artifact quota; reduce the declared campaign")
        return self

    def document(self) -> dict:
        return self.model_dump(by_alias=True)

    def profile(self) -> dict:
        return {"name": self.evaluation_profile, "n": self.n, "initial_side": self.initial_side,
                "precision": "FP32", "fast_math": False, "operator_version": "rigid-operators-v1",
                "solver": {"step": 0.2, "step_floor": 0.0001, "step_reduction": 0.5,
                           "guard": 0.00002, "acceptance_tolerance": 0.000002,
                           "motion_tolerance": 0.0000001, "rotation_mobility": 0.3,
                           "relaxation": 0.8, "max_translation": 0.1, "max_rotation": 0.08,
                           "stagnation_sweeps": 4, "proposals_per_square": 2000},
                "work_limits": self.work_limits.resolved(self.n),
                "maximum_side": min(100.0, 2 * self.initial_side),
                "cpu_validation_tolerance": 1e-9, "scoring_version": SCORING_VERSION,
                "rng_version": RNG_VERSION,
                "work_policy": "Prepaid conservative constraint visits, copies, selectors and dispatches; actual sweeps recorded separately; no refunds."}

    def plan(self) -> dict:
        candidates = len(self.search.methods) * self.search.candidate_budget_per_method
        fixed = len(self.controls) + len(self.fixed_programs)
        training = (candidates + fixed) * self.datasets.training.valid_count * self.operator_replicates
        holdout = (len(self.search.methods) + fixed) * self.datasets.holdout.valid_count * self.operator_replicates
        native = (training + holdout) * (24 * self.n + 2048) + (self.datasets.training.valid_count + self.datasets.holdout.valid_count) * (12 * self.n + 16)
        return {"candidate_evaluations": candidates, "training_episodes": training,
                "holdout_episodes_before_deduplication": holdout,
                "estimated_native_bytes": native,
                "estimated_device_bytes": self.batch_capacity * (52 * self.n + 512) + 128 * 32 * max(1, self.search.initial_pool, self.search.lambda_) + self.recording.max_frames_per_trace * (12 * self.n + 96) + 1024 * 96,
                "maximum_seconds": self.limits.max_seconds,
                "automatic_replay_cap": self.recording.max_traces if self.recording.automatic else 0,
                "timing_forecast": None}


def capabilities() -> dict:
    return {"campaign_schema": SCHEMA, "program_schema": "asquerix-strategy-v1",
            "operators": [op.name for op in Op if op.value <= 7],
            "selectors": [selector.name for selector in Selector],
            "methods": ["random_program_search", "one_plus_lambda"],
            "profiles": ["rigid-square-lab-v1"], "square_count": [1, 32],
            "defaults": Campaign(name="New campaign").document(),
            "controls": {name: control_program(name) for name in ("legacy_compress", "pulse_rotate")},
            "help": {"fraction": "Fractions multiply the side measured at operation entry; centers do not scale.",
                     "WALL_K": "Nearest squares to any wall, with ID tie breaks; exact contact is not required.",
                     "RELAX": "A feasible instruction boundary returns ALREADY_FEASIBLE without geometric changes.",
                     "cost": "Charged work is a declared conservative budget, not CUDA instruction count."}}
