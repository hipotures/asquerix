"""Resumable Warp interpreter; geometry is owned by the existing contact engine."""

from __future__ import annotations

from dataclasses import asdict
from time import perf_counter

import numpy as np
import warp as wp

from ..gpu import Config, Parameters, Result, correct_pair, correct_wall, mix64, parameters, random_value, residuals, support
from .config import Campaign
from .strategy import Compiled, verify

wp.set_module_options({"fast_math": False, "enable_backward": False, "block_dim": 32})

TERMINATIONS = {0: "RUNNING", 1: "STOPPED", 2: "INSTRUCTION_LIMIT", 3: "GLOBAL_WORK_LIMIT",
                4: "NUMERICAL_FAILURE", 5: "INVALID_PROGRAM", 6: "CANCELLED"}
OUTCOMES = {0: "NONE", 1: "TARGET_REACHED", 2: "PARTIAL_PROGRESS", 3: "NO_PROGRESS",
            4: "REJECTED", 5: "NO_TARGET", 6: "ALREADY_FEASIBLE", 7: "LIMIT_REACHED",
            8: "UNCHANGED", 9: "RESTORED", 10: "EXPANDED"}
# Trace flags: proposal, repair, commit, reject, rollback, best, restore, final, invoke.
PROPOSAL, REPAIR, COMMIT, REJECT, ROLLBACK, BEST, RESTORE, FINAL, INVOKE = (1, 2, 4, 8, 16, 32, 64, 128, 256)


@wp.struct
class Instruction:
    op: int
    i0: int
    i1: int
    i2: int
    a: float
    b: float
    c: float
    d: float


@wp.struct
class Limits:
    dispatches: int
    attempts: int
    sweeps: int
    visits: wp.uint64
    maximum_side: float


@wp.struct
class VM:
    result: Result
    pc: int
    phase: int
    termination: int
    finalized: int
    dispatches: int
    op_attempt: int
    op_sweep: int
    stagnant: int
    stalled: int
    last_outcome: int
    last_improved: int
    op_improved: int
    entry_side: float
    target_side: float
    trial_side: float
    effective_floor: float
    best_side: float
    best_pc: int
    best_attempt: int
    best_sweep: int
    best_gap: float
    best_wall: float
    best_feasible: int
    rng: wp.uint64
    rng_draws: wp.uint64
    work: wp.uint64
    checks: int
    proposal_count: int
    mask: wp.uint32
    sequence: wp.uint64


@wp.struct
class Frame:
    side: float
    best_side: float
    pc: int
    phase: int
    flags: int
    attempt: int
    sweep: int
    sweep_total: int
    outcome: int
    mask: wp.uint32
    work: wp.uint64
    sequence: wp.uint64
    rng_draws: wp.uint64


@wp.struct
class Capture:
    used: int
    observed: int
    stride: int
    events: int


@wp.func
def _record(source: wp.array2d(dtype=wp.vec3), world: int, n: int, vm: VM,
            side: float, phase: int, flags: int, keep_geometry: int,
            poses: wp.array2d(dtype=wp.vec3), frames: wp.array(dtype=Frame),
            events: wp.array(dtype=Frame), capture: wp.array(dtype=Capture), cap: int):
    if world == 0:
        c = capture[0]
        f = Frame()
        f.side = side
        f.best_side = vm.best_side
        f.pc = vm.pc
        f.phase = phase
        f.flags = flags
        f.attempt = vm.op_attempt
        f.sweep = vm.op_sweep
        f.sweep_total = vm.result.sweeps
        f.outcome = vm.last_outcome
        f.mask = vm.mask
        f.work = vm.work
        f.sequence = vm.sequence
        f.rng_draws = vm.rng_draws
        # Sweeps are geometric samples; semantic boundaries are retained separately.
        if flags != 2 and c.events < 1024:
            events[c.events] = f
            c.events += 1
        if keep_geometry == 1:
            c.observed += 1
            endpoint = int((flags & 128) != 0 or phase == 0 or flags == 32)
            if endpoint == 1 or c.observed % c.stride == 0:
                if c.used >= cap - 2 and endpoint == 0:
                    target = int(1)
                    for old in range(2, c.used, 2):
                        frames[target] = frames[old]
                        for square in range(n):
                            poses[target, square] = poses[old, square]
                        target += 1
                    c.used = target
                    c.stride *= 2
                if c.used < cap:
                    frames[c.used] = f
                    for square in range(n):
                        poses[c.used, square] = source[square, world]
                    c.used += 1
        capture[0] = c


@wp.func
def _pay(vm: VM, cost: int, limits: Limits):
    result = vm
    if result.work + wp.uint64(cost) > limits.visits:
        result.termination = 3
    else:
        result.work += wp.uint64(cost)
    return result


@wp.func
def _complete(vm: VM, outcome: int):
    result = vm
    result.last_outcome = outcome
    result.last_improved = result.op_improved
    result.phase = 0
    result.pc += 1
    return result


@wp.func
def _valid(ins: Instruction, pc: int, length: int):
    valid = int(wp.isfinite(ins.a) and ins.b == 0.0 and ins.c == 0.0 and ins.d == 0.0)
    if ins.op == 1:
        valid = valid * int(ins.i0 >= 1 and ins.i0 <= 128 and ins.i1 >= 1 and ins.i1 <= 480 and ins.i2 >= 0 and ins.i2 <= 1)
        if ins.i2 == 0:
            valid = valid * int(ins.a == 0.0)
        else:
            valid = valid * int(ins.a > 0.0 and ins.a < 1.0)
    elif ins.op == 2:
        valid = valid * int(ins.i0 == 0 and ins.i1 == 0 and ins.i2 == 0 and ins.a > 0.0 and ins.a <= 0.25)
    elif ins.op == 3 or ins.op == 4:
        cap = float(0.5)
        if ins.op == 4:
            cap = 0.7853981633974483
        valid = valid * int(ins.i0 >= 0 and ins.i0 <= 2 and ins.i1 >= 0 and ins.i1 <= 32 and ins.i2 >= 1 and ins.i2 <= 480 and ins.a > 0.0 and ins.a <= cap)
        if ins.i0 == 0 and ins.i1 != 0:
            valid = 0
    elif ins.op >= 5 and ins.op <= 7:
        valid = valid * int(ins.i0 == 0 and ins.i1 == 0 and ins.i2 == 0 and ins.a == 0.0)
    elif ins.op == 8 or ins.op == 9:
        valid = valid * int(ins.i1 > pc and ins.i1 < length and ins.i2 == 0 and ins.a == 0.0)
        if ins.op == 8:
            valid = valid * int(ins.i0 >= 1 and ins.i0 <= 3)
        else:
            valid = valid * int(ins.i0 == 0)
    else:
        valid = 0
    return valid


@wp.kernel
def initialize(cfg: Parameters, operator_seed: wp.uint64, inputs: wp.array2d(dtype=wp.vec3),
               initial_results: wp.array(dtype=Result), ids: wp.array(dtype=wp.uint64),
               replicates: wp.array(dtype=wp.uint64), program_ids: wp.array(dtype=int),
               code: wp.array2d(dtype=Instruction), lengths: wp.array(dtype=int),
               current: wp.array2d(dtype=wp.vec3), trial: wp.array2d(dtype=wp.vec3),
               best: wp.array2d(dtype=wp.vec3), states: wp.array(dtype=VM), recording: int,
               trace_poses: wp.array2d(dtype=wp.vec3), frames: wp.array(dtype=Frame),
               events: wp.array(dtype=Frame), capture: wp.array(dtype=Capture), frame_cap: int):
    world = wp.tid()
    vm = VM()
    vm.result = initial_results[world]
    vm.entry_side = vm.result.side
    vm.trial_side = vm.result.side
    vm.best_side = vm.result.side
    vm.best_pc = -1
    vm.best_attempt = -1
    vm.best_sweep = -1
    vm.rng = operator_seed ^ mix64(ids[world]) ^ mix64(replicates[world] + wp.uint64(1609587929392839161))
    for square in range(cfg.n):
        current[square, world] = inputs[square, world]
        trial[square, world] = inputs[square, world]
        best[square, world] = inputs[square, world]
    pid = program_ids[world]
    if pid < 0 or pid >= lengths.shape[0]:
        vm.termination = 5
    else:
        length = lengths[pid]
        if length < 1 or length > 128 or code.shape[1] < length:
            vm.termination = 5
        else:
            for pc in range(length):
                if _valid(code[pid, pc], pc, length) == 0:
                    vm.termination = 5
            if code[pid, length - 1].op != 7:
                vm.termination = 5
    gap, wall, finite = residuals(current, world, cfg.n, vm.result.side)
    vm.checks = 1
    vm.best_gap = gap
    vm.best_wall = wall
    vm.best_feasible = int(finite == 1 and wp.isfinite(vm.result.side) and vm.result.side > 0.0 and wp.min(gap, wall) >= cfg.guard - cfg.acceptance_tolerance)
    if vm.result.termination == 3 or vm.best_feasible == 0:
        vm.termination = 4
    if recording != 0 and world == 0:
        c = Capture()
        c.stride = 1
        capture[0] = c
        _record(current, world, cfg.n, vm, vm.result.side, 0, 0, 1, trace_poses, frames, events, capture, frame_cap)
    states[world] = vm


@wp.kernel
def execute(cfg: Parameters, limits: Limits, code: wp.array2d(dtype=Instruction),
            lengths: wp.array(dtype=int), program_ids: wp.array(dtype=int),
            current: wp.array2d(dtype=wp.vec3), trial: wp.array2d(dtype=wp.vec3),
            best: wp.array2d(dtype=wp.vec3), selected_ids: wp.array2d(dtype=int),
            states: wp.array(dtype=VM), slice_sweeps: int, slice_dispatches: int,
            cancel: int, recording: int, every: int, trace_poses: wp.array2d(dtype=wp.vec3),
            frames: wp.array(dtype=Frame), events: wp.array(dtype=Frame),
            capture: wp.array(dtype=Capture), frame_cap: int):
    world = wp.tid()
    vm = states[world]
    sweeps_used = int(0)
    dispatches_used = int(0)
    scan_cost = 2 * cfg.n + cfg.n * (cfg.n - 1) // 2
    if cancel == 1 and vm.termination == 0:
        vm.termination = 6
    for microstep in range(2 * slice_sweeps + slice_dispatches + 1):
        if vm.termination != 0:
            break
        pid = program_ids[world]
        if pid < 0 or pid >= lengths.shape[0] or pid >= code.shape[0]:
            vm.termination = 5
            break
        length = lengths[pid]
        if length < 1 or length > 128 or length > code.shape[1] or vm.pc < 0 or vm.pc >= length:
            vm.termination = 5
            break
        ins = code[pid, vm.pc]
        if _valid(ins, vm.pc, lengths[pid]) == 0:
            vm.termination = 5
            break
        if vm.phase == 0:
            if dispatches_used >= slice_dispatches:
                break
            if vm.dispatches >= limits.dispatches:
                vm.termination = 2
                break
            vm = _pay(vm, 1, limits)
            if vm.termination != 0:
                break
            vm.dispatches += 1
            dispatches_used += 1
            vm.sequence += wp.uint64(1)
            vm.entry_side = vm.result.side
            vm.op_attempt = 0
            vm.op_sweep = 0
            vm.op_improved = 0
            vm.mask = wp.uint32(0)
            if recording != 0:
                _record(current, world, cfg.n, vm, vm.result.side, 3, 256, 0, trace_poses, frames, events, capture, frame_cap)
            if ins.op == 7:
                vm.termination = 1
                break
            elif ins.op == 8:
                condition = int(0)
                if ins.i0 == 1:
                    condition = int(vm.last_outcome == 3)
                elif ins.i0 == 2:
                    condition = int(vm.last_outcome == 4)
                elif ins.i0 == 3:
                    condition = vm.last_improved
                vm.pc += 1
                if condition == 0:
                    vm.pc = ins.i1
                continue
            elif ins.op == 9:
                vm.pc = ins.i1
                continue
            elif ins.op == 1:
                vm.result.final_step = cfg.step
                vm.result.termination = 0
                vm.target_side = float(0.0)
                if ins.i2 == 1:
                    vm.target_side = vm.entry_side * (1.0 - ins.a)
                    if vm.target_side >= vm.entry_side:
                        vm = _complete(vm, 3)
                        continue
                vm.phase = 1
            elif ins.op == 2:
                vm = _pay(vm, scan_cost, limits)
                if vm.termination != 0:
                    break
                proposed = vm.result.side * (1.0 + ins.a)
                outcome = int(4)
                if wp.isfinite(proposed) and proposed <= limits.maximum_side and proposed > vm.result.side:
                    gap, wall, finite = residuals(current, world, cfg.n, proposed)
                    vm.checks += 1
                    if finite == 1 and wp.min(gap, wall) >= cfg.guard - cfg.acceptance_tolerance:
                        vm.result.side = proposed
                        outcome = 10
                vm.last_outcome = outcome
                if recording != 0:
                    _record(current, world, cfg.n, vm, vm.result.side, 3, 4, 1, trace_poses, frames, events, capture, frame_cap)
                vm = _complete(vm, outcome)
            elif ins.op == 5:
                vm = _pay(vm, scan_cost, limits)
                if vm.termination != 0:
                    break
                gap, wall, finite = residuals(current, world, cfg.n, vm.result.side)
                vm.checks += 1
                if finite == 0 or wp.min(gap, wall) < cfg.guard - cfg.acceptance_tolerance:
                    vm.termination = 4
                    break
                vm = _complete(vm, 6)
            elif ins.op == 6:
                vm = _pay(vm, cfg.n + scan_cost, limits)
                if vm.termination != 0:
                    break
                changed = int(vm.result.side != vm.best_side)
                for square in range(cfg.n):
                    p = current[square, world]
                    q = best[square, world]
                    if p[0] != q[0] or p[1] != q[1] or p[2] != q[2]:
                        changed = 1
                    current[square, world] = q
                    trial[square, world] = q
                vm.result.side = vm.best_side
                vm.trial_side = vm.best_side
                outcome = int(8)
                if changed == 1:
                    outcome = 9
                vm.last_outcome = outcome
                if recording != 0:
                    _record(current, world, cfg.n, vm, vm.result.side, 5, 64, 1, trace_poses, frames, events, capture, frame_cap)
                vm = _complete(vm, outcome)
            else:
                vm = _pay(vm, 8 * cfg.n + cfg.n * cfg.n, limits)
                if vm.termination != 0:
                    break
                count = wp.min(ins.i1, cfg.n)
                if ins.i0 == 0:
                    count = cfg.n
                    for square in range(cfg.n):
                        vm.mask = vm.mask | (wp.uint32(1) << wp.uint32(square))
                elif ins.i0 == 1:
                    for square in range(cfg.n):
                        selected_ids[square, world] = square
                    for pick in range(count):
                        next_rng, draw = random_value(vm.rng)
                        vm.rng = next_rng
                        vm.rng_draws += wp.uint64(1)
                        chosen = pick + wp.min(cfg.n - pick - 1, int(draw * float(cfg.n - pick)))
                        square = selected_ids[chosen, world]
                        selected_ids[chosen, world] = selected_ids[pick, world]
                        selected_ids[pick, world] = square
                        vm.mask = vm.mask | (wp.uint32(1) << wp.uint32(square))
                else:
                    for square in range(cfg.n):
                        p = current[square, world]
                        clearance = wp.min(0.5 * vm.result.side - wp.abs(p[0]) - support(p[2], wp.vec2(1.0, 0.0)),
                                           0.5 * vm.result.side - wp.abs(p[1]) - support(p[2], wp.vec2(0.0, 1.0)))
                        rank = int(0)
                        for other in range(cfg.n):
                            q = current[other, world]
                            other_clearance = wp.min(0.5 * vm.result.side - wp.abs(q[0]) - support(q[2], wp.vec2(1.0, 0.0)),
                                                     0.5 * vm.result.side - wp.abs(q[1]) - support(q[2], wp.vec2(0.0, 1.0)))
                            if other_clearance < clearance or (other_clearance == clearance and other < square):
                                rank += 1
                        if rank < count:
                            vm.mask = vm.mask | (wp.uint32(1) << wp.uint32(square))
                if count == 0:
                    vm = _complete(vm, 5)
                    continue
                for square in range(cfg.n):
                    p = current[square, world]
                    if (vm.mask & (wp.uint32(1) << wp.uint32(square))) != wp.uint32(0):
                        next_rng, draw = random_value(vm.rng)
                        vm.rng = next_rng
                        vm.rng_draws += wp.uint64(1)
                        if ins.op == 3:
                            next_rng, angle = random_value(vm.rng)
                            vm.rng = next_rng
                            vm.rng_draws += wp.uint64(1)
                            radius = ins.a * wp.sqrt(draw)
                            p = p + wp.vec3(radius * wp.cos(6.283185307179586 * angle), radius * wp.sin(6.283185307179586 * angle), 0.0)
                        else:
                            p = p + wp.vec3(0.0, 0.0, (2.0 * draw - 1.0) * ins.a)
                        vm.proposal_count += 1
                    trial[square, world] = p
                vm.trial_side = vm.result.side
                vm.stagnant = 0
                vm.stalled = 0
                vm.phase = 2
                if recording != 0:
                    _record(trial, world, cfg.n, vm, vm.trial_side, 1, 1, int(recording == 2), trace_poses, frames, events, capture, frame_cap)
        elif vm.phase == 1:
            if sweeps_used >= slice_sweeps:
                break
            if ins.i2 == 1 and vm.result.side <= vm.target_side:
                vm = _complete(vm, 1)
                continue
            if vm.op_attempt >= ins.i0:
                outcome = int(7)
                if vm.result.side < vm.entry_side:
                    outcome = 2
                vm = _complete(vm, outcome)
                continue
            if vm.result.attempts >= limits.attempts:
                vm.termination = 3
                break
            step = vm.result.final_step
            vm.effective_floor = cfg.step_floor
            if ins.i2 == 1:
                remaining = vm.result.side - vm.target_side
                if remaining <= 0.0:
                    vm = _complete(vm, 1)
                    continue
                step = wp.min(step, remaining)
                vm.effective_floor = wp.min(cfg.step_floor, remaining)
            vm.trial_side = vm.result.side - step
            if vm.trial_side == vm.result.side or not wp.isfinite(vm.trial_side):
                vm = _complete(vm, 3)
                continue
            vm.result.final_step = step
            vm = _pay(vm, 3 * cfg.n + 1, limits)
            if vm.termination != 0:
                break
            vm.result.attempts += 1
            vm.op_attempt += 1
            vm.op_sweep = 0
            vm.stagnant = 0
            vm.stalled = 0
            vm.sequence += wp.uint64(1)
            for square in range(cfg.n):
                trial[square, world] = current[square, world]
            vm.phase = 2
            if recording != 0:
                _record(trial, world, cfg.n, vm, vm.trial_side, 1, 1, int(recording == 2), trace_poses, frames, events, capture, frame_cap)
        else:
            if sweeps_used >= slice_sweeps:
                break
            if vm.result.sweeps >= limits.sweeps:
                vm.termination = 3
                break
            vm = _pay(vm, 6 * cfg.n + cfg.n * (cfg.n - 1), limits)
            if vm.termination != 0:
                break
            motion = float(0.0)
            for square in range(cfg.n):
                p = trial[square, world]
                for wall_index in range(4):
                    normal = wp.vec2(1.0, 0.0)
                    if wall_index == 1:
                        normal = wp.vec2(-1.0, 0.0)
                    elif wall_index == 2:
                        normal = wp.vec2(0.0, 1.0)
                    elif wall_index == 3:
                        normal = wp.vec2(0.0, -1.0)
                    p, moved = correct_wall(p, vm.trial_side, normal, cfg)
                    motion = wp.max(motion, moved)
                trial[square, world] = p
            for square in range(cfg.n):
                for other in range(square + 1, cfg.n):
                    p, q, moved = correct_pair(trial[square, world], trial[other, world], cfg)
                    trial[square, world] = p
                    trial[other, world] = q
                    motion = wp.max(motion, moved)
            vm.result.sweeps += 1
            vm.op_sweep += 1
            sweeps_used += 1
            vm.sequence += wp.uint64(1)
            gap, wall, finite = residuals(trial, world, cfg.n, vm.trial_side)
            vm.checks += 1
            success = int(wp.min(gap, wall) >= cfg.guard - cfg.acceptance_tolerance)
            if finite == 0:
                success = 0
                vm.termination = 4
                vm.result.termination = 4
            if recording == 2 and vm.op_sweep % every == 0:
                _record(trial, world, cfg.n, vm, vm.trial_side, 2, 2, 1, trace_poses, frames, events, capture, frame_cap)
            if motion <= cfg.motion_tolerance:
                vm.stagnant += 1
            else:
                vm.stagnant = 0
            if vm.stagnant >= cfg.stagnation_sweeps:
                vm.stalled = 1
            sweep_limit = ins.i2
            if ins.op == 1:
                sweep_limit = ins.i1
            if success == 1 or vm.stalled == 1 or vm.op_sweep >= sweep_limit or vm.termination != 0:
                if success == 1:
                    vm.result.side = vm.trial_side
                    if ins.op == 1:
                        vm.result.accepted += 1
                    for square in range(cfg.n):
                        current[square, world] = trial[square, world]
                    flags = int(4)
                    if vm.result.side < vm.best_side:
                        vm.best_side = vm.result.side
                        vm.best_pc = vm.pc
                        vm.best_attempt = vm.op_attempt
                        vm.best_sweep = vm.op_sweep
                        vm.op_improved = 1
                        flags = flags | 32
                        for square in range(cfg.n):
                            best[square, world] = current[square, world]
                    vm.last_outcome = 2
                    if recording != 0:
                        _record(current, world, cfg.n, vm, vm.result.side, 3, flags, 1, trace_poses, frames, events, capture, frame_cap)
                    if ins.op == 1:
                        vm.phase = 1
                    else:
                        vm = _complete(vm, 2)
                else:
                    if ins.op == 1:
                        vm.result.rejected += 1
                    vm.last_outcome = 4
                    if recording != 0:
                        _record(trial, world, cfg.n, vm, vm.trial_side, 4, 8, int(recording == 2), trace_poses, frames, events, capture, frame_cap)
                    for square in range(cfg.n):
                        trial[square, world] = current[square, world]
                    if recording != 0:
                        _record(current, world, cfg.n, vm, vm.result.side, 5, 16, 1, trace_poses, frames, events, capture, frame_cap)
                    if ins.op == 1:
                        floor_failed = int(vm.result.final_step <= vm.effective_floor)
                        vm.result.final_step = wp.max(vm.effective_floor, vm.result.final_step * cfg.step_reduction)
                        vm.phase = 1
                        if floor_failed == 1 and vm.termination == 0:
                            vm.result.termination = 1
                            if vm.stalled == 1:
                                vm.result.termination = 2
                            vm = _complete(vm, 3)
                    elif vm.termination == 0:
                        vm = _complete(vm, 4)
    if vm.termination != 0 and vm.finalized == 0:
        # Reserved final checks never modify geometry or override a failure.
        for square in range(cfg.n):
            trial[square, world] = current[square, world]
        vm.trial_side = vm.result.side
        gap, wall, finite = residuals(current, world, cfg.n, vm.result.side)
        vm.result.min_gap = gap
        vm.result.min_wall = wall
        vm.result.max_penetration = wp.max(0.0, -wp.min(gap, wall))
        vm.result.feasible = int(finite == 1 and wp.min(gap, wall) >= cfg.guard - cfg.acceptance_tolerance)
        gap, wall, finite = residuals(best, world, cfg.n, vm.best_side)
        vm.best_gap = gap
        vm.best_wall = wall
        vm.best_feasible = int(finite == 1 and wp.min(gap, wall) >= cfg.guard - cfg.acceptance_tolerance)
        vm.checks += 2
        vm.finalized = 1
        if recording != 0:
            final_pc = vm.pc
            vm.pc = vm.best_pc
            _record(best, world, cfg.n, vm, vm.best_side, 3, 32, 1, trace_poses, frames, events, capture, frame_cap)
            vm.pc = final_pc
            _record(current, world, cfg.n, vm, vm.result.side, 6, 128, 1, trace_poses, frames, events, capture, frame_cap)
    states[world] = vm


class StrategyBatch:
    """Batched device execution with scalar progress only at bounded slice boundaries."""

    def __init__(self, campaign: Campaign, programs: list[Compiled], poses: np.ndarray,
                 initial_results: np.ndarray, ids: np.ndarray, replicates: np.ndarray,
                 program_ids: np.ndarray, *, recording: bool = False):
        if not programs or any(verify(program.code) != program.code for program in programs):
            raise ValueError("Invalid program table")
        count = len(ids)
        if not 1 <= count <= campaign.batch_capacity or poses.shape != (count, campaign.n, 3):
            raise ValueError("Invalid task geometry dimensions")
        if poses.dtype != np.dtype("float32") or ids.dtype != np.dtype("uint64") or replicates.dtype != np.dtype("uint64"):
            raise ValueError("Task geometry and identity dtypes must be exact FP32/uint64")
        if len(initial_results) != count or replicates.shape != ids.shape or program_ids.shape != ids.shape:
            raise ValueError("Invalid task table dimensions")
        if program_ids.dtype != np.dtype("int32") or np.any(program_ids < 0) or np.any(program_ids >= len(programs)):
            raise ValueError("Invalid program table indices")
        if recording and count != 1:
            raise ValueError("Selected replay requires exactly one episode")
        wp.init()
        self.device = wp.get_device(campaign.device)
        if not self.device.is_cuda:
            raise ValueError("Strategy execution requires the explicitly selected CUDA device")
        self.campaign, self.count = campaign, count
        config = Config(n=campaign.n, initial_side=campaign.initial_side,
                        seed=int(campaign.datasets.initializer_seed), max_attempts=128, max_sweeps=480,
                        **campaign.profile()["solver"])
        self.cfg = parameters(config)
        self.limits = Limits()
        caps = campaign.work_limits.resolved(campaign.n)
        for name, value in {"dispatches": caps["dispatches"], "attempts": caps["compression_attempts"],
                            "sweeps": caps["contact_sweeps"], "visits": caps["constraint_visits"],
                            "maximum_side": campaign.profile()["maximum_side"]}.items():
            setattr(self.limits, name, value)
        load_start = perf_counter()
        wp.load_module(module=__name__, device=self.device, block_dim=32)
        wp.synchronize_device(self.device)
        self.module_seconds = perf_counter() - load_start
        self.start_event = wp.Event(device=self.device, enable_timing=True)
        self.end_event = wp.Event(device=self.device, enable_timing=True)
        self.timings = {"jit_seconds": self.module_seconds, "device_seconds": 0.0,
                        "simulation_seconds": 0.0, "transfer_seconds": 0.0, "slice_count": 0,
                        "max_slice_seconds": 0.0}
        upload_start = perf_counter()
        words = np.zeros((len(programs), 128), dtype=Instruction.numpy_dtype())
        for pid, program in enumerate(programs):
            for pc, instruction in enumerate(program.code):
                for name, value in zip(words.dtype.names, instruction.words(), strict=True):
                    words[pid, pc][name] = value
        self.code = wp.array(words, dtype=Instruction, device=self.device)
        self.lengths = wp.array(np.asarray([len(p.code) for p in programs], dtype=np.int32), dtype=int, device=self.device)
        self.program_ids = wp.array(program_ids, dtype=int, device=self.device)
        self.inputs = wp.array(np.transpose(poses, (1, 0, 2)).copy(), dtype=wp.vec3, device=self.device)
        self.initial_results = wp.array(initial_results, dtype=Result, device=self.device)
        self.ids = wp.array(ids, dtype=wp.uint64, device=self.device)
        self.replicates = wp.array(replicates, dtype=wp.uint64, device=self.device)
        self.current = wp.zeros((campaign.n, count), dtype=wp.vec3, device=self.device)
        self.trial = wp.zeros_like(self.current)
        self.best = wp.zeros_like(self.current)
        self.selected_ids = wp.zeros((campaign.n, count), dtype=int, device=self.device)
        self.states = wp.zeros(count, dtype=VM, device=self.device)
        self.frame_cap = campaign.recording.max_frames_per_trace if recording else 4
        self.recording = (1 if campaign.recording.mode == "accepted" else 2) if recording else 0
        self.trace_poses = wp.zeros((self.frame_cap, campaign.n), dtype=wp.vec3, device=self.device)
        self.frames = wp.zeros(self.frame_cap, dtype=Frame, device=self.device)
        self.events = wp.zeros(1024 if recording else 1, dtype=Frame, device=self.device)
        self.capture = wp.zeros(1, dtype=Capture, device=self.device)
        wp.launch(initialize, dim=count, inputs=[self.cfg, wp.uint64(int(campaign.operator_seed)),
                  self.inputs, self.initial_results, self.ids, self.replicates, self.program_ids,
                  self.code, self.lengths, self.current, self.trial, self.best, self.states,
                  self.recording, self.trace_poses, self.frames, self.events, self.capture, self.frame_cap],
                  device=self.device, block_dim=32)
        wp.synchronize_device(self.device)
        self.timings["upload_initialize_seconds"] = perf_counter() - upload_start
        self.latest = None

    def advance(self, *, cancel: bool = False) -> bool:
        start = perf_counter()
        wp.record_event(self.start_event)
        wp.launch(execute, dim=self.count, inputs=[self.cfg, self.limits, self.code, self.lengths,
                  self.program_ids, self.current, self.trial, self.best, self.selected_ids, self.states,
                  self.campaign.slice_sweeps, self.campaign.slice_dispatches, int(cancel), self.recording,
                  self.campaign.recording.every, self.trace_poses, self.frames, self.events,
                  self.capture, self.frame_cap], device=self.device, block_dim=32)
        wp.record_event(self.end_event)
        wp.synchronize_device(self.device)
        elapsed = perf_counter() - start
        self.timings["simulation_seconds"] += elapsed
        self.timings["device_seconds"] += wp.get_event_elapsed_time(self.start_event, self.end_event) / 1000
        self.timings["max_slice_seconds"] = max(self.timings["max_slice_seconds"], elapsed)
        self.timings["slice_count"] += 1
        start = perf_counter()
        self.latest = self.states.numpy().copy()
        self.timings["transfer_seconds"] += perf_counter() - start
        return bool(np.all(self.latest["termination"] != 0))

    def collect(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if self.latest is None or np.any(self.latest["termination"] == 0):
            raise ValueError("Cannot collect unfinished episodes")
        start = perf_counter()
        best = np.transpose(self.best.numpy(), (1, 0, 2)).copy()
        current = np.transpose(self.current.numpy(), (1, 0, 2)).copy()
        self.timings["transfer_seconds"] += perf_counter() - start
        return self.latest.copy(), best, current

    def trace(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
        if not self.recording or self.latest is None or np.any(self.latest["termination"] == 0):
            raise ValueError("No completed selected trace")
        captured = self.capture.numpy()[0]
        count, event_count = int(captured["used"]), int(captured["events"])
        return (self.trace_poses.numpy()[:count].copy(), self.frames.numpy()[:count].copy(),
                self.events.numpy()[:event_count].copy(),
                {name: int(captured[name]) for name in captured.dtype.names})


def defined_fields(states: np.ndarray) -> dict[str, np.ndarray]:
    """Flatten named fields for byte comparison, excluding implementation padding."""
    fields = {}
    for name in states.dtype.names:
        if name == "result":
            fields.update({"result." + key: states[name][key].copy() for key in states[name].dtype.names})
        else:
            fields[name] = states[name].copy()
    return fields
