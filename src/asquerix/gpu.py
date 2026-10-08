"""One CUDA thread per independent world; all search decisions are device-side."""
import math
import os
from dataclasses import asdict, dataclass
from time import perf_counter

import numpy as np
import warp as wp

wp.config.kernel_cache_dir = os.environ.get("ASQUERIX_WARP_CACHE", "/tmp/asquerix-warp-cache")
wp.set_module_options({"fast_math": False, "enable_backward": False, "block_dim": 32})

TERMINATIONS = {0: "BUDGET_EXHAUSTED", 1: "STEP_FLOOR_REACHED", 2: "STAGNATED",
                3: "INIT_FAILED", 4: "NUMERICAL_FAILURE"}


@dataclass(frozen=True)
class Config:
    n: int = 12
    initial_side: float = 10.0
    seed: int = 20261008
    step: float = 0.2
    step_floor: float = 0.0001
    step_reduction: float = 0.5
    guard: float = 0.00002
    acceptance_tolerance: float = 0.000002
    motion_tolerance: float = 0.0000001
    rotation_mobility: float = 0.3
    relaxation: float = 0.8
    max_translation: float = 0.1
    max_rotation: float = 0.08
    max_attempts: int = 128
    max_sweeps: int = 120
    stagnation_sweeps: int = 4
    proposals_per_square: int = 2000

    def validate(self):
        for key in ("n", "seed", "max_attempts", "max_sweeps", "stagnation_sweeps", "proposals_per_square"):
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
                raise ValueError(f"{key} must be an integer")
        if not 1 <= self.n <= 32:
            raise ValueError("n must be an integer from 1 through 32")
        if not 0 <= self.seed < 2**64:
            raise ValueError("seed must fit unsigned 64 bits")
        for key in ("initial_side", "step", "step_floor", "guard", "acceptance_tolerance",
                    "motion_tolerance", "rotation_mobility", "relaxation", "max_translation", "max_rotation"):
            value = getattr(self, key)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{key} must be positive and finite")
        if self.initial_side <= math.sqrt(2) + 2 * self.guard:
            raise ValueError("initial_side must exceed sqrt(2) + 2*guard for the circle initializer")
        if self.initial_side > 100 or self.guard >= 0.1:
            raise ValueError("FP32 baseline requires initial_side <= 100 and guard < 0.1")
        if self.guard <= self.acceptance_tolerance or self.step_floor > self.step:
            raise ValueError("guard must exceed acceptance_tolerance; step_floor must not exceed step")
        if not 0 < self.step_reduction < 1 or not 0 < self.relaxation <= 1:
            raise ValueError("step_reduction must be in (0,1); relaxation must be in (0,1]")
        if not 0 <= self.max_attempts <= 2048 or not 1 <= self.max_sweeps <= 2000:
            raise ValueError("attempt/sweep budgets exceed the bounded baseline limits")
        if not 1 <= self.proposals_per_square <= 100000 or not 1 <= self.stagnation_sweeps <= 100:
            raise ValueError("proposal/stagnation budgets are outside their supported limits")


@wp.struct
class Parameters:
    n: int
    initial_side: float
    seed: wp.uint64
    step: float
    step_floor: float
    step_reduction: float
    guard: float
    acceptance_tolerance: float
    motion_tolerance: float
    rotation_mobility: float
    relaxation: float
    max_translation: float
    max_rotation: float
    max_attempts: int
    max_sweeps: int
    stagnation_sweeps: int
    proposals_per_square: int


@wp.struct
class Result:
    side: float
    min_gap: float
    min_wall: float
    max_penetration: float
    termination: int
    feasible: int
    attempts: int
    sweeps: int
    accepted: int
    rejected: int
    proposals: int
    final_step: float

@wp.func
def mix64(value: wp.uint64):
    z = value
    z = (z ^ (z >> wp.uint64(30))) * wp.uint64(13787848793156543929)
    z = (z ^ (z >> wp.uint64(27))) * wp.uint64(10723151780598845931)
    return z ^ (z >> wp.uint64(31))


@wp.func
def random_value(state: wp.uint64):
    nxt = state + wp.uint64(11400714819323198485)
    return nxt, float(mix64(nxt) >> wp.uint64(40)) * (1.0 / 16777216.0)


@wp.func
def sign_symmetric(x: float):
    s = float(0.0)
    if x > 0.000001:
        s = 1.0
    elif x < -0.000001:
        s = -1.0
    return s


@wp.func
def axes(theta: float):
    return wp.vec2(wp.cos(theta), wp.sin(theta)), wp.vec2(-wp.sin(theta), wp.cos(theta))


@wp.func
def support(theta: float, normal: wp.vec2):
    u, v = axes(theta)
    return 0.5 * (wp.abs(wp.dot(u, normal)) + wp.abs(wp.dot(v, normal)))


@wp.func
def support_derivative(theta: float, normal: wp.vec2):
    u, v = axes(theta)
    return 0.5 * (sign_symmetric(wp.dot(u, normal)) * wp.dot(v, normal)
                  - sign_symmetric(wp.dot(v, normal)) * wp.dot(u, normal))


@wp.func
def pair_constraint(p: wp.vec3, q: wp.vec3):
    # Differentiate the moving SAT axis as well as the support functions.
    # Tied owner axes are averaged: aligned face contacts then use their midpoint.
    d = wp.vec2(q[0] - p[0], q[1] - p[1])
    up, vp = axes(p[2])
    uq, vq = axes(q[2])
    best = float(-1.0e20)
    center_gradient = wp.vec2(0.0, 0.0)
    gp = float(0.0)
    gq = float(0.0)
    count = int(0)
    for k in range(4):
        a = up
        if k == 1:
            a = vp
        elif k == 2:
            a = uq
        elif k == 3:
            a = vq
        dot = wp.dot(d, a)
        direction = float(1.0)
        if dot < 0.0:
            direction = -1.0
        pu = wp.dot(up, a)
        pv = wp.dot(vp, a)
        qu = wp.dot(uq, a)
        qv = wp.dot(vq, a)
        hp = 0.5 * (wp.abs(pu) + wp.abs(pv))
        hq = 0.5 * (wp.abs(qu) + wp.abs(qv))
        dhp = 0.5 * (sign_symmetric(pu) * pv - sign_symmetric(pv) * pu)
        dhq = 0.5 * (sign_symmetric(qu) * qv - sign_symmetric(qv) * qu)
        gap = wp.abs(dot) - hp - hq
        dp = -dhp
        dq = -dhq
        da = direction * wp.dot(d, wp.vec2(-a[1], a[0]))
        if k < 2:
            dp = da + dhq
        else:
            dq = da + dhp
        if gap > best + 0.000001:
            best = gap
            center_gradient = direction * a
            gp = dp
            gq = dq
            count = 1
        elif wp.abs(gap - best) <= 0.000001:
            best = wp.max(best, gap)
            center_gradient += direction * a
            gp += dp
            gq += dq
            count += 1
    return best, center_gradient / float(count), gp / float(count), gq / float(count)


@wp.func
def pair_gap(p: wp.vec3, q: wp.vec3):
    up, vp = axes(p[2])
    uq, vq = axes(q[2])
    d = wp.vec2(q[0] - p[0], q[1] - p[1])
    best = float(-1.0e20)
    for k in range(4):
        a = up
        if k == 1:
            a = vp
        elif k == 2:
            a = uq
        elif k == 3:
            a = vq
        hp = 0.5 * (wp.abs(wp.dot(up, a)) + wp.abs(wp.dot(vp, a)))
        hq = 0.5 * (wp.abs(wp.dot(uq, a)) + wp.abs(wp.dot(vq, a)))
        best = wp.max(best, wp.abs(wp.dot(d, a)) - hp - hq)
    return best


@wp.func
def bounded_scale(lam: float, linear_norm: float, angular: float, cfg: Parameters):
    scale = lam * cfg.relaxation
    if linear_norm > 0.0:
        scale = wp.min(scale, cfg.max_translation / linear_norm)
    if angular > 0.0:
        scale = wp.min(scale, cfg.max_rotation / angular)
    return scale


@wp.func
def correct_pair(p: wp.vec3, q: wp.vec3, cfg: Parameters):
    gap, normal, gp, gq = pair_constraint(p, q)
    motion = float(0.0)
    if gap < cfg.guard:
        denominator = 2.0 * wp.dot(normal, normal) + cfg.rotation_mobility * (gp * gp + gq * gq)
        if denominator > 0.00000001:
            angular = cfg.rotation_mobility * wp.max(wp.abs(gp), wp.abs(gq))
            scale = bounded_scale((cfg.guard - gap) / denominator, wp.length(normal), angular, cfg)
            delta = scale * normal
            dp = scale * cfg.rotation_mobility * gp
            dq = scale * cfg.rotation_mobility * gq
            p = p + wp.vec3(-delta[0], -delta[1], dp)
            q = q + wp.vec3(delta[0], delta[1], dq)
            motion = wp.max(wp.length(delta), wp.max(wp.abs(dp), wp.abs(dq)))
    return p, q, motion


@wp.func
def correct_wall(p: wp.vec3, side: float, normal: wp.vec2, cfg: Parameters):
    gap = 0.5 * side - wp.dot(wp.vec2(p[0], p[1]), normal) - support(p[2], normal)
    motion = float(0.0)
    if gap < cfg.guard:
        angular_gradient = -support_derivative(p[2], normal)
        denominator = 1.0 + cfg.rotation_mobility * angular_gradient * angular_gradient
        scale = bounded_scale((cfg.guard - gap) / denominator, 1.0,
                              cfg.rotation_mobility * wp.abs(angular_gradient), cfg)
        dp = scale * cfg.rotation_mobility * angular_gradient
        p = p + wp.vec3(-scale * normal[0], -scale * normal[1], dp)
        motion = wp.max(scale, wp.abs(dp))
    return p, motion


@wp.func
def residuals(poses: wp.array2d(dtype=wp.vec3), world: int, n: int, side: float):
    gap = float(1.0e20)
    wall = float(1.0e20)
    finite = int(1)
    for i in range(n):
        p = poses[i, world]
        if not wp.isfinite(p[0]) or not wp.isfinite(p[1]) or not wp.isfinite(p[2]):
            finite = 0
        wall = wp.min(wall, 0.5 * side - wp.abs(p[0]) - support(p[2], wp.vec2(1.0, 0.0)))
        wall = wp.min(wall, 0.5 * side - wp.abs(p[1]) - support(p[2], wp.vec2(0.0, 1.0)))
        for j in range(i + 1, n):
            gap = wp.min(gap, pair_gap(p, poses[j, world]))
    return gap, wall, finite


@wp.kernel
def simulate(cfg: Parameters, offset: wp.uint64,
             accepted_pose: wp.array2d(dtype=wp.vec3), work: wp.array2d(dtype=wp.vec3),
             results: wp.array(dtype=Result), trace: wp.array2d(dtype=float), debug: int, stage: int, chunk_attempts: int):
    world = wp.tid()
    if stage == 0:
        result = Result()
        result.termination = 0
        result.side = cfg.initial_side
        result.final_step = cfg.step
        state = cfg.seed ^ mix64(offset + wp.uint64(world))
        room = 0.5 * cfg.initial_side - 0.7071067811865476 - cfg.guard
        initialized = int(1)
        for i in range(cfg.n):
            placed = int(0)
            for proposal in range(cfg.proposals_per_square):
                state, rx = random_value(state)
                state, ry = random_value(state)
                state, rt = random_value(state)
                candidate = wp.vec3((2.0 * rx - 1.0) * room, (2.0 * ry - 1.0) * room, rt * 1.5707963267948966)
                result.proposals += 1
                clear = int(1)
                for j in range(i):
                    p = accepted_pose[j, world]
                    dx = p[0] - candidate[0]
                    dy = p[1] - candidate[1]
                    if dx * dx + dy * dy < 2.0 + 4.0 * cfg.guard:
                        clear = 0
                if clear == 1:
                    accepted_pose[i, world] = candidate
                    placed = 1
                    break
            if placed == 0:
                initialized = 0
                break
        if initialized == 0:
            result.termination = 3
            result.side = 0.0
    else:
        result = results[world]
    initialized = int(result.termination == 0 and result.attempts < cfg.max_attempts)
    if stage == 0 and cfg.max_attempts == 0 and result.termination == 0:
        initialized = 1
    if initialized == 1:
        gap, wall, finite = residuals(accepted_pose, world, cfg.n, result.side)
        result.feasible = 1
        for local_attempt in range(chunk_attempts):
            if result.attempts >= cfg.max_attempts:
                break
            attempt = result.attempts
            result.attempts += 1
            proposed_side = result.side - result.final_step
            success = int(0)
            stagnant = int(0)
            stalled = int(0)
            for i in range(cfg.n):
                work[i, world] = accepted_pose[i, world]
            for sweep in range(cfg.max_sweeps):
                motion = float(0.0)
                for i in range(cfg.n):
                    p = work[i, world]
                    for k in range(4):
                        normal = wp.vec2(1.0, 0.0)
                        if k == 1:
                            normal = wp.vec2(-1.0, 0.0)
                        elif k == 2:
                            normal = wp.vec2(0.0, 1.0)
                        elif k == 3:
                            normal = wp.vec2(0.0, -1.0)
                        p, m = correct_wall(p, proposed_side, normal, cfg)
                        motion = wp.max(motion, m)
                    work[i, world] = p
                for i in range(cfg.n):
                    for j in range(i + 1, cfg.n):
                        p, q, m = correct_pair(work[i, world], work[j, world], cfg)
                        work[i, world] = p
                        work[j, world] = q
                        motion = wp.max(motion, m)
                result.sweeps += 1
                gap, wall, finite = residuals(work, world, cfg.n, proposed_side)
                if finite == 0:
                    result.termination = 4
                    break
                if wp.min(gap, wall) >= cfg.guard - cfg.acceptance_tolerance:
                    success = 1
                    break
                if motion <= cfg.motion_tolerance:
                    stagnant += 1
                else:
                    stagnant = 0
                if stagnant >= cfg.stagnation_sweeps:
                    stalled = 1
                    break
            if success == 1:
                result.side = proposed_side
                result.accepted += 1
                for i in range(cfg.n):
                    accepted_pose[i, world] = work[i, world]
            else:
                result.rejected += 1
                for i in range(cfg.n):
                    work[i, world] = accepted_pose[i, world]
                result.final_step *= cfg.step_reduction
            if debug == 1:
                trace[attempt, world] = result.side
            if result.termination == 4:
                break
            if result.final_step < cfg.step_floor:
                result.termination = 1
                if stalled == 1:
                    result.termination = 2
                break
        gap, wall, finite = residuals(accepted_pose, world, cfg.n, result.side)
        result.min_gap = gap
        result.min_wall = wall
        result.max_penetration = wp.max(0.0, -gap)
        result.feasible = int(finite == 1 and wp.min(gap, wall) >= cfg.guard - cfg.acceptance_tolerance)
    results[world] = result


@wp.kernel
def gather(poses: wp.array2d(dtype=wp.vec3), indices: wp.array(dtype=int), output: wp.array2d(dtype=wp.vec3), n: int):
    square, selected = wp.tid()
    if square < n:
        output[selected, square] = poses[square, indices[selected]]


@wp.kernel
def contact_diagnostic(p: wp.array(dtype=wp.vec3), q: wp.array(dtype=wp.vec3),
                       cfg: Parameters, side: float, wall_mode: int, values: wp.array2d(dtype=float)):
    i = wp.tid()
    if wall_mode == 1:
        updated, motion = correct_wall(p[i], side, wp.vec2(1.0, 0.0), cfg)
        p[i] = updated
    else:
        gap, normal, gp, gq = pair_constraint(p[i], q[i])
        values[i, 0] = gap
        values[i, 1] = -normal[0]
        values[i, 2] = -normal[1]
        values[i, 3] = gp
        values[i, 4] = normal[0]
        values[i, 5] = normal[1]
        values[i, 6] = gq
        updated_p, updated_q, motion = correct_pair(p[i], q[i], cfg)
        p[i] = updated_p
        q[i] = updated_q


def parameters(config):
    config.validate()
    p = Parameters()
    for key, value in asdict(config).items():
        setattr(p, key, value)
    return p


class Batch:
    """Reusable GPU storage. Readbacks happen only at completed batch boundaries."""
    def __init__(self, config, capacity, device="cuda:0", debug=False):
        config.validate()
        if not 1 <= capacity <= 65536:
            raise ValueError("batch_size must be in [1,65536]")
        wp.init()
        self.device = wp.get_device(device)
        if not self.device.is_cuda:
            raise ValueError("GPU runs require an explicit CUDA device; CPU fallback is forbidden")
        self.config, self.capacity, self.debug = config, capacity, debug
        self.params = parameters(config)
        start = perf_counter()
        wp.load_module(module=__name__, device=self.device, block_dim=32)
        self.kernel_properties = wp.get_cuda_kernel_properties(simulate, device=self.device, block_dim=32)
        wp.synchronize_device(self.device)
        self.module_load_seconds = perf_counter() - start
        self.poses = wp.empty((config.n, capacity), dtype=wp.vec3, device=self.device)
        self.work = wp.empty_like(self.poses)
        self.results = wp.empty(capacity, dtype=Result, device=self.device)
        self.trace = wp.zeros((max(1, config.max_attempts) if debug else 1, capacity), dtype=float, device=self.device)
        self.indices = wp.empty(capacity, dtype=int, device=self.device)
        self.selected = wp.empty((capacity, config.n), dtype=wp.vec3, device=self.device)
        self.start_event = wp.Event(device=self.device, enable_timing=True)
        self.end_event = wp.Event(device=self.device, enable_timing=True)
        self.stage_count = max(1, (config.max_attempts + 15) // 16)
        self.stage_events = [wp.Event(device=self.device, enable_timing=True) for _ in range(self.stage_count + 1)]

    def run(self, count, offset):
        if not 1 <= count <= self.capacity or not 0 <= offset <= 2**64 - count:
            raise ValueError("batch count or global unsigned-64 trial range is invalid")
        wp.synchronize_device(self.device)
        begin = perf_counter()
        # A fixed submission contains at most 16 attempts per kernel. The CPU
        # does not inspect state or decide on compression between these stages.
        with wp.ScopedDevice(self.device):
            wp.record_event(self.start_event)
            wp.record_event(self.stage_events[0])
            for stage in range(self.stage_count):
                wp.launch(simulate, dim=count, inputs=[self.params, wp.uint64(offset), self.poses, self.work,
                    self.results, self.trace, int(self.debug), stage, 16], device=self.device, block_dim=32)
                wp.record_event(self.stage_events[stage + 1])
            wp.record_event(self.end_event)
        wp.synchronize_device(self.device)
        synchronized = perf_counter() - begin
        device_seconds = wp.get_event_elapsed_time(self.start_event, self.end_event) / 1000.0
        max_stage = max(wp.get_event_elapsed_time(self.stage_events[i], self.stage_events[i + 1])
                        for i in range(self.stage_count)) / 1000.0
        begin = perf_counter()
        scalars = self.results[:count].numpy().copy()
        transfer = perf_counter() - begin
        return scalars, {"simulation_seconds": synchronized, "device_seconds": device_seconds,
                         "transfer_seconds": transfer, "max_stage_seconds": max_stage}

    def get_poses(self, indices):
        if not len(indices):
            return np.empty((0, self.config.n, 3)), 0.0
        begin = perf_counter()
        idx = np.asarray(indices, dtype=np.int32)
        wp.copy(self.indices, wp.array(idx, dtype=int, device="cpu"), count=len(idx))
        wp.launch(gather, dim=(self.config.n, len(idx)), inputs=[self.poses, self.indices, self.selected,
                                                              self.config.n], device=self.device)
        selected = self.selected[:len(idx)].numpy().copy()
        wp.synchronize_device(self.device)
        return selected, perf_counter() - begin
