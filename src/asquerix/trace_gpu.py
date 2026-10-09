"""CUDA-only, bounded trajectory replay for one selected production trial.

The production kernel in :mod:`asquerix.gpu` intentionally remains untouched.
This module contains a diagnostic kernel with the same initialization and
solver arithmetic, plus device-side frame capture for a single world.
"""

from __future__ import annotations

import os
from dataclasses import asdict
from numbers import Integral
from time import perf_counter
from typing import Any

import numpy as np
import warp as wp

from .gpu import (
    Config,
    Parameters,
    Result,
    correct_pair,
    correct_wall,
    mix64,
    parameters,
    random_value,
    residuals,
)


# Keep this module's cache location aligned with the production module without
# changing the production module's source or module options.
wp.config.kernel_cache_dir = os.environ.get("ASQUERIX_WARP_CACHE", "/tmp/asquerix-warp-cache")

TRACE_SCHEMA_VERSION = 1
MODE_ACCEPTED = "accepted"
MODE_SWEEPS = "sweeps"

PHASE_INITIAL = 0
PHASE_TRIAL = 1
PHASE_RELAXING = 2
PHASE_ACCEPTED = 3
PHASE_REJECTED = 4
PHASE_ROLLBACK = 5
PHASE_FINAL = 6

ROLE_INITIAL = 1
ROLE_FINAL = 2

_MODE_ACCEPTED = 0
_MODE_SWEEPS = 1
_MIN_FRAMES = 2
_MAX_FRAMES = 4096


@wp.func
def _copy_trace_frame(
    trace_poses: wp.array2d(dtype=wp.vec3),
    source: int,
    target: int,
    n: int,
    trace_side: wp.array(dtype=float),
    trace_sequence: wp.array(dtype=wp.int64),
    trace_attempt: wp.array(dtype=int),
    trace_sweep: wp.array(dtype=int),
    trace_sweep_total: wp.array(dtype=int),
    trace_phase: wp.array(dtype=wp.uint8),
    trace_roles: wp.array(dtype=wp.uint8),
):
    for square in range(n):
        trace_poses[square, target] = trace_poses[square, source]
    trace_side[target] = trace_side[source]
    trace_sequence[target] = trace_sequence[source]
    trace_attempt[target] = trace_attempt[source]
    trace_sweep[target] = trace_sweep[source]
    trace_sweep_total[target] = trace_sweep_total[source]
    trace_phase[target] = trace_phase[source]
    trace_roles[target] = trace_roles[source]


@wp.func
def _record_trace_frame(
    accepted_pose: wp.array2d(dtype=wp.vec3),
    world: int,
    source_pose: wp.array2d(dtype=wp.vec3),
    source_side: float,
    frame_capacity: int,
    frame_count: wp.array(dtype=int),
    event_count: wp.array(dtype=wp.int64),
    suppressed_count: wp.array(dtype=wp.int64),
    compaction_count: wp.array(dtype=int),
    effective_stride: wp.array(dtype=wp.int64),
    sequence_value: wp.int64,
    attempt_value: int,
    sweep_value: int,
    sweep_total_value: int,
    phase_value: int,
    role_value: int,
    trace_poses: wp.array2d(dtype=wp.vec3),
    trace_side: wp.array(dtype=float),
    trace_sequence: wp.array(dtype=wp.int64),
    trace_attempt: wp.array(dtype=int),
    trace_sweep: wp.array(dtype=int),
    trace_sweep_total: wp.array(dtype=int),
    trace_phase: wp.array(dtype=wp.uint8),
    trace_roles: wp.array(dtype=wp.uint8),
    n: int,
):
    """Append one bounded event, compacting old representatives in-place."""

    event_count[0] += wp.int64(1)
    # Only endpoints bypass the sampling stride.  Accepted/rejection and
    # sweep states are retained while capacity permits, then sampled by the
    # same deterministic stride so long replays cannot repeatedly compact.
    force = int(phase_value == PHASE_INITIAL or phase_value == PHASE_FINAL)
    record = int(1)
    if force == 0 and effective_stride[0] > wp.int64(1):
        if sequence_value % effective_stride[0] != wp.int64(0):
            record = 0
            suppressed_count[0] += wp.int64(1)
    if record == 1:
        count = frame_count[0]
        if count >= frame_capacity:
            # Keep a deterministic, evenly spaced representative set including
            # both endpoints.  The source is copied to a lower slot, so each
            # destination is safe to write in ascending order.  Future
            # non-boundary events are then skipped until the doubled stride.
            retained = (frame_capacity + 1) // 2
            for destination in range(retained):
                source = 0
                if retained > 1:
                    source = (destination * (count - 1)) // (retained - 1)
                _copy_trace_frame(
                    trace_poses,
                    source,
                    destination,
                    n,
                    trace_side,
                    trace_sequence,
                    trace_attempt,
                    trace_sweep,
                    trace_sweep_total,
                    trace_phase,
                    trace_roles,
                )
            suppressed_count[0] += wp.int64(count - retained)
            compaction_count[0] += 1
            effective_stride[0] *= wp.int64(2)
            count = retained

        for square in range(n):
            trace_poses[square, count] = source_pose[square, world]
        trace_side[count] = source_side
        trace_sequence[count] = sequence_value
        trace_attempt[count] = attempt_value
        trace_sweep[count] = sweep_value
        trace_sweep_total[count] = sweep_total_value
        trace_phase[count] = wp.uint8(phase_value)
        trace_roles[count] = wp.uint8(role_value)
        frame_count[0] = count + 1


@wp.func
def _record_trace_accepted_pose(
    accepted_pose: wp.array2d(dtype=wp.vec3),
    world: int,
    source_side: float,
    frame_capacity: int,
    frame_count: wp.array(dtype=int),
    event_count: wp.array(dtype=wp.int64),
    suppressed_count: wp.array(dtype=wp.int64),
    compaction_count: wp.array(dtype=int),
    effective_stride: wp.array(dtype=wp.int64),
    sequence_value: wp.int64,
    attempt_value: int,
    sweep_value: int,
    sweep_total_value: int,
    phase_value: int,
    role_value: int,
    trace_poses: wp.array2d(dtype=wp.vec3),
    trace_side: wp.array(dtype=float),
    trace_sequence: wp.array(dtype=wp.int64),
    trace_attempt: wp.array(dtype=int),
    trace_sweep: wp.array(dtype=int),
    trace_sweep_total: wp.array(dtype=int),
    trace_phase: wp.array(dtype=wp.uint8),
    trace_roles: wp.array(dtype=wp.uint8),
    n: int,
):
    """Append the accepted pose by using accepted storage as the source."""

    _record_trace_frame(
        accepted_pose,
        world,
        accepted_pose,
        source_side,
        frame_capacity,
        frame_count,
        event_count,
        suppressed_count,
        compaction_count,
        effective_stride,
        sequence_value,
        attempt_value,
        sweep_value,
        sweep_total_value,
        phase_value,
        role_value,
        trace_poses,
        trace_side,
        trace_sequence,
        trace_attempt,
        trace_sweep,
        trace_sweep_total,
        trace_phase,
        trace_roles,
        n,
    )


@wp.kernel
def trace_simulate(
    cfg: Parameters,
    offset: wp.uint64,
    accepted_pose: wp.array2d(dtype=wp.vec3),
    work: wp.array2d(dtype=wp.vec3),
    results: wp.array(dtype=Result),
    mode: int,
    every: int,
    frame_capacity: int,
    frame_count: wp.array(dtype=int),
    event_count: wp.array(dtype=wp.int64),
    suppressed_count: wp.array(dtype=wp.int64),
    compaction_count: wp.array(dtype=int),
    effective_stride: wp.array(dtype=wp.int64),
    sequence_counter: wp.array(dtype=wp.int64),
    last_attempt: wp.array(dtype=int),
    last_sweep: wp.array(dtype=int),
    trace_poses: wp.array2d(dtype=wp.vec3),
    trace_side: wp.array(dtype=float),
    trace_sequence: wp.array(dtype=wp.int64),
    trace_attempt: wp.array(dtype=int),
    trace_sweep: wp.array(dtype=int),
    trace_sweep_total: wp.array(dtype=int),
    trace_phase: wp.array(dtype=wp.uint8),
    trace_roles: wp.array(dtype=wp.uint8),
    stage: int,
    chunk_attempts: int,
):
    """Production control flow with bounded diagnostic recording added."""

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
                candidate = wp.vec3(
                    (2.0 * rx - 1.0) * room,
                    (2.0 * ry - 1.0) * room,
                    rt * 1.5707963267948966,
                )
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
            # INITIAL is recorded only after every square was written.
            _record_trace_accepted_pose(
                accepted_pose,
                world,
                result.side,
                frame_capacity,
                frame_count,
                event_count,
                suppressed_count,
                compaction_count,
                effective_stride,
                wp.int64(0),
                -1,
                -1,
                0,
                PHASE_INITIAL,
                ROLE_INITIAL,
                trace_poses,
                trace_side,
                trace_sequence,
                trace_attempt,
                trace_sweep,
                trace_sweep_total,
                trace_phase,
                trace_roles,
                cfg.n,
            )
            sequence_counter[0] = wp.int64(1)
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

            sequence_counter[0] += wp.int64(1)
            if mode == _MODE_SWEEPS:
                _record_trace_accepted_pose(
                    work,
                    world,
                    proposed_side,
                    frame_capacity,
                    frame_count,
                    event_count,
                    suppressed_count,
                    compaction_count,
                    effective_stride,
                    sequence_counter[0],
                    attempt,
                    0,
                    result.sweeps,
                    PHASE_TRIAL,
                    0,
                    trace_poses,
                    trace_side,
                    trace_sequence,
                    trace_attempt,
                    trace_sweep,
                    trace_sweep_total,
                    trace_phase,
                    trace_roles,
                    cfg.n,
                )

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
                completed_sweep = sweep + 1
                gap, wall, finite = residuals(work, world, cfg.n, proposed_side)
                sequence_counter[0] += wp.int64(1)
                if mode == _MODE_SWEEPS and completed_sweep % every == 0:
                    _record_trace_frame(
                        work,
                        world,
                        work,
                        proposed_side,
                        frame_capacity,
                        frame_count,
                        event_count,
                        suppressed_count,
                        compaction_count,
                        effective_stride,
                        sequence_counter[0],
                        attempt,
                        completed_sweep,
                        result.sweeps,
                        PHASE_RELAXING,
                        0,
                        trace_poses,
                        trace_side,
                        trace_sequence,
                        trace_attempt,
                        trace_sweep,
                        trace_sweep_total,
                        trace_phase,
                        trace_roles,
                        cfg.n,
                    )
                elif mode == _MODE_SWEEPS:
                    # Count sweep states skipped by the requested interval so
                    # metadata can state the observed/suppressed event totals.
                    event_count[0] += wp.int64(1)
                    suppressed_count[0] += wp.int64(1)
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

            last_attempt[0] = attempt
            last_sweep[0] = completed_sweep

            # The configured floor is an admissible step, not an untried
            # stopping threshold. Remember whether THIS attempt used it.
            floor_failed = int(success == 0 and result.final_step <= cfg.step_floor)
            if success == 1:
                result.side = proposed_side
                result.accepted += 1
                for i in range(cfg.n):
                    accepted_pose[i, world] = work[i, world]
                sequence_counter[0] += wp.int64(1)
                if mode == _MODE_SWEEPS:
                    _record_trace_accepted_pose(
                        accepted_pose,
                        world,
                        result.side,
                        frame_capacity,
                        frame_count,
                        event_count,
                        suppressed_count,
                        compaction_count,
                        effective_stride,
                        sequence_counter[0],
                        attempt,
                        completed_sweep,
                        result.sweeps,
                        PHASE_ACCEPTED,
                        0,
                        trace_poses,
                        trace_side,
                        trace_sequence,
                        trace_attempt,
                        trace_sweep,
                        trace_sweep_total,
                        trace_phase,
                        trace_roles,
                        cfg.n,
                    )
                else:
                    _record_trace_accepted_pose(
                        accepted_pose,
                        world,
                        result.side,
                        frame_capacity,
                        frame_count,
                        event_count,
                        suppressed_count,
                        compaction_count,
                        effective_stride,
                        sequence_counter[0],
                        attempt,
                        completed_sweep,
                        result.sweeps,
                        PHASE_ACCEPTED,
                        0,
                        trace_poses,
                        trace_side,
                        trace_sequence,
                        trace_attempt,
                        trace_sweep,
                        trace_sweep_total,
                        trace_phase,
                        trace_roles,
                        cfg.n,
                    )
            else:
                if mode == _MODE_SWEEPS:
                    sequence_counter[0] += wp.int64(1)
                    _record_trace_frame(
                        work,
                        world,
                        work,
                        proposed_side,
                        frame_capacity,
                        frame_count,
                        event_count,
                        suppressed_count,
                        compaction_count,
                        effective_stride,
                        sequence_counter[0],
                        attempt,
                        completed_sweep,
                        result.sweeps,
                        PHASE_REJECTED,
                        0,
                        trace_poses,
                        trace_side,
                        trace_sequence,
                        trace_attempt,
                        trace_sweep,
                        trace_sweep_total,
                        trace_phase,
                        trace_roles,
                        cfg.n,
                    )
                result.rejected += 1
                for i in range(cfg.n):
                    work[i, world] = accepted_pose[i, world]
                result.final_step = wp.max(cfg.step_floor, result.final_step * cfg.step_reduction)
                if mode == _MODE_SWEEPS:
                    sequence_counter[0] += wp.int64(1)
                    _record_trace_accepted_pose(
                        accepted_pose,
                        world,
                        result.side,
                        frame_capacity,
                        frame_count,
                        event_count,
                        suppressed_count,
                        compaction_count,
                        effective_stride,
                        sequence_counter[0],
                        attempt,
                        completed_sweep,
                        result.sweeps,
                        PHASE_ROLLBACK,
                        0,
                        trace_poses,
                        trace_side,
                        trace_sequence,
                        trace_attempt,
                        trace_sweep,
                        trace_sweep_total,
                        trace_phase,
                        trace_roles,
                        cfg.n,
                    )
            if result.termination == 4:
                break
            if floor_failed == 1:
                result.termination = 1
                if stalled == 1:
                    result.termination = 2
                break
        gap, wall, finite = residuals(accepted_pose, world, cfg.n, result.side)
        result.min_gap = gap
        result.min_wall = wall
        result.max_penetration = wp.max(0.0, -wp.min(gap, wall))
        result.feasible = int(finite == 1 and wp.min(gap, wall) >= cfg.guard - cfg.acceptance_tolerance)
    results[world] = result


@wp.kernel
def trace_finalize(
    cfg: Parameters,
    accepted_pose: wp.array2d(dtype=wp.vec3),
    results: wp.array(dtype=Result),
    frame_count: wp.array(dtype=int),
    sequence_counter: wp.array(dtype=wp.int64),
    last_attempt: wp.array(dtype=int),
    last_sweep: wp.array(dtype=int),
    frame_capacity: int,
    event_count: wp.array(dtype=wp.int64),
    suppressed_count: wp.array(dtype=wp.int64),
    compaction_count: wp.array(dtype=int),
    effective_stride: wp.array(dtype=wp.int64),
    trace_poses: wp.array2d(dtype=wp.vec3),
    trace_side: wp.array(dtype=float),
    trace_sequence: wp.array(dtype=wp.int64),
    trace_attempt: wp.array(dtype=int),
    trace_sweep: wp.array(dtype=int),
    trace_sweep_total: wp.array(dtype=int),
    trace_phase: wp.array(dtype=wp.uint8),
    trace_roles: wp.array(dtype=wp.uint8),
):
    """Mark or append the final accepted endpoint after all stages finish."""

    world = wp.tid()
    result = results[world]
    if result.termination != 3 and frame_count[0] > 0:
        last = frame_count[0] - 1
        same = int(trace_side[last] == result.side)
        for square in range(cfg.n):
            p = trace_poses[square, last]
            q = accepted_pose[square, world]
            if p[0] != q[0] or p[1] != q[1] or p[2] != q[2]:
                same = 0
        # Preserve an already captured endpoint in place.  The role bit
        # carries the final endpoint even for a rollback frame; changing its
        # phase would erase the rejection/rollback boundary from playback.
        if same == 1:
            # Copy from accepted storage even when equality treated signed
            # zeros as equal.  The endpoint must retain the exact accepted
            # FP32 bits rather than those of a provisional frame.
            for square in range(cfg.n):
                trace_poses[square, last] = accepted_pose[square, world]
            trace_side[last] = result.side
            if (trace_phase[last] != wp.uint8(PHASE_INITIAL)
                    and trace_phase[last] != wp.uint8(PHASE_ROLLBACK)):
                trace_phase[last] = wp.uint8(PHASE_FINAL)
            trace_roles[last] = wp.uint8(trace_roles[last] | wp.uint8(ROLE_FINAL))
        else:
            sequence_counter[0] += wp.int64(1)
            _record_trace_accepted_pose(
                accepted_pose,
                world,
                result.side,
                frame_capacity,
                frame_count,
                event_count,
                suppressed_count,
                compaction_count,
                effective_stride,
                sequence_counter[0],
                last_attempt[0],
                last_sweep[0],
                result.sweeps,
                PHASE_FINAL,
                ROLE_FINAL,
                trace_poses,
                trace_side,
                trace_sequence,
                trace_attempt,
                trace_sweep,
                trace_sweep_total,
                trace_phase,
                trace_roles,
                cfg.n,
            )
    results[world] = result


def _validate_replay_arguments(config: Config, trial_id: int, mode: str, max_frames: int, every: int) -> None:
    config.validate()
    if isinstance(trial_id, bool) or not isinstance(trial_id, Integral) or not 0 <= trial_id < 2**64:
        raise ValueError("trial_id must fit unsigned 64 bits")
    if mode not in (MODE_ACCEPTED, MODE_SWEEPS):
        raise ValueError("mode must be 'accepted' or 'sweeps'")
    if isinstance(max_frames, bool) or not isinstance(max_frames, Integral) or not _MIN_FRAMES <= max_frames <= _MAX_FRAMES:
        raise ValueError(f"max_frames must be an integer in [{_MIN_FRAMES},{_MAX_FRAMES}]")
    if isinstance(every, bool) or not isinstance(every, Integral) or not 1 <= every <= 2**31 - 1:
        raise ValueError("every must be an integer in [1,2147483647]")


def _device_description(device: Any) -> dict[str, Any]:
    return {
        "selector": getattr(device, "alias", None) or getattr(device, "name", None),
        "name": getattr(device, "name", None),
        "uuid": getattr(device, "uuid", None),
    }


def replay(
    config: Config,
    trial_id: int,
    *,
    device: str = "cuda:0",
    mode: str = MODE_ACCEPTED,
    max_frames: int = 256,
    every: int = 16,
) -> dict[str, Any]:
    """Replay one global trial on CUDA and return bounded numeric trajectory data.

    The returned ``poses`` array has shape ``[frames, n, 3]`` and dtype
    ``float32``.  Device work and all trajectory writes complete before any
    frame data is copied to the host.
    """

    _validate_replay_arguments(config, trial_id, mode, max_frames, every)
    wp.init()
    selected_device = wp.get_device(device)
    if not selected_device.is_cuda:
        raise ValueError("trajectory replay requires an explicit CUDA device; CPU fallback is forbidden")

    frame_capacity = int(max_frames)
    params = parameters(config)
    start = perf_counter()
    wp.load_module(module=__name__, device=selected_device, block_dim=32)
    wp.synchronize_device(selected_device)
    compile_seconds = perf_counter() - start

    accepted_pose = wp.empty((config.n, 1), dtype=wp.vec3, device=selected_device)
    work = wp.empty_like(accepted_pose)
    results = wp.empty(1, dtype=Result, device=selected_device)
    frame_count = wp.zeros(1, dtype=int, device=selected_device)
    event_count = wp.zeros(1, dtype=wp.int64, device=selected_device)
    suppressed_count = wp.zeros(1, dtype=wp.int64, device=selected_device)
    compaction_count = wp.zeros(1, dtype=int, device=selected_device)
    effective_stride = wp.ones(1, dtype=wp.int64, device=selected_device)
    sequence_counter = wp.zeros(1, dtype=wp.int64, device=selected_device)
    last_attempt = wp.full(1, -1, dtype=int, device=selected_device)
    last_sweep = wp.full(1, -1, dtype=int, device=selected_device)
    trace_poses = wp.empty((config.n, frame_capacity), dtype=wp.vec3, device=selected_device)
    trace_side = wp.empty(frame_capacity, dtype=float, device=selected_device)
    trace_sequence = wp.empty(frame_capacity, dtype=wp.int64, device=selected_device)
    trace_attempt = wp.empty(frame_capacity, dtype=int, device=selected_device)
    trace_sweep = wp.empty(frame_capacity, dtype=int, device=selected_device)
    trace_sweep_total = wp.empty(frame_capacity, dtype=int, device=selected_device)
    trace_phase = wp.empty(frame_capacity, dtype=wp.uint8, device=selected_device)
    trace_roles = wp.empty(frame_capacity, dtype=wp.uint8, device=selected_device)

    stage_count = max(1, (config.max_attempts + 15) // 16)
    start_event = wp.Event(device=selected_device, enable_timing=True)
    end_event = wp.Event(device=selected_device, enable_timing=True)
    simulation_start = perf_counter()
    with wp.ScopedDevice(selected_device):
        wp.record_event(start_event)
        for stage in range(stage_count):
            wp.launch(
                trace_simulate,
                dim=1,
                inputs=[
                    params,
                    wp.uint64(int(trial_id)),
                    accepted_pose,
                    work,
                    results,
                    _MODE_ACCEPTED if mode == MODE_ACCEPTED else _MODE_SWEEPS,
                    int(every),
                    frame_capacity,
                    frame_count,
                    event_count,
                    suppressed_count,
                    compaction_count,
                    effective_stride,
                    sequence_counter,
                    last_attempt,
                    last_sweep,
                    trace_poses,
                    trace_side,
                    trace_sequence,
                    trace_attempt,
                    trace_sweep,
                    trace_sweep_total,
                    trace_phase,
                    trace_roles,
                    stage,
                    16,
                ],
                device=selected_device,
                block_dim=32,
            )
        wp.launch(
            trace_finalize,
            dim=1,
            inputs=[
                params,
                accepted_pose,
                results,
                frame_count,
                sequence_counter,
                last_attempt,
                last_sweep,
                frame_capacity,
                event_count,
                suppressed_count,
                compaction_count,
                effective_stride,
                trace_poses,
                trace_side,
                trace_sequence,
                trace_attempt,
                trace_sweep,
                trace_sweep_total,
                trace_phase,
                trace_roles,
            ],
            device=selected_device,
            block_dim=32,
        )
        wp.record_event(end_event)
    wp.synchronize_device(selected_device)
    simulation_seconds = perf_counter() - simulation_start
    device_seconds = wp.get_event_elapsed_time(start_event, end_event) / 1000.0

    transfer_start = perf_counter()
    result_values = results.numpy().copy()
    count = int(frame_count.numpy()[0])
    event_total = int(event_count.numpy()[0])
    suppressed_total = int(suppressed_count.numpy()[0])
    compactions = int(compaction_count.numpy()[0])
    stride = int(effective_stride.numpy()[0])
    if count:
        raw_poses = trace_poses.numpy()
        poses = np.asarray(raw_poses[:, :count, :], dtype=np.float32).transpose(1, 0, 2).copy()
        side = trace_side.numpy()[:count].copy()
        sequence = trace_sequence.numpy()[:count].copy()
        attempt = trace_attempt.numpy()[:count].copy()
        sweep = trace_sweep.numpy()[:count].copy()
        sweep_total = trace_sweep_total.numpy()[:count].copy()
        phase = trace_phase.numpy()[:count].copy()
        roles = trace_roles.numpy()[:count].copy()
    else:
        poses = np.empty((0, config.n, 3), dtype=np.float32)
        side = np.empty((0,), dtype=np.float32)
        sequence = np.empty((0,), dtype=np.int64)
        attempt = np.empty((0,), dtype=np.int32)
        sweep = np.empty((0,), dtype=np.int32)
        sweep_total = np.empty((0,), dtype=np.int32)
        phase = np.empty((0,), dtype=np.uint8)
        roles = np.empty((0,), dtype=np.uint8)
    transfer_seconds = perf_counter() - transfer_start
    total_seconds = perf_counter() - start

    arrays = {
        "poses": poses,
        "side": side,
        "sequence": sequence,
        "attempt": attempt,
        "sweep": sweep,
        "sweep_total": sweep_total,
        "phase": phase,
        "roles": roles,
        "square_ids": np.arange(config.n, dtype=np.int32),
    }
    return {
        "schema_version": TRACE_SCHEMA_VERSION,
        "trial_id": int(trial_id),
        "n": int(config.n),
        "result": result_values[0],
        "results": result_values,
        "arrays": arrays,
        "scalars": result_values,
        **arrays,
        "mode": mode,
        "every": int(every),
        "max_frames": frame_capacity,
        "sampling": {
            "observed": event_total,
            "events_seen": event_total,
            "retained_frames": count,
            "retained": count,
            "suppressed_frames": suppressed_total,
            "suppressed": suppressed_total,
            "compactions": compactions,
            "effective_stride": stride,
            "max_frames": frame_capacity,
        },
        "timings": {
            "compile_seconds": compile_seconds,
            "simulation_seconds": simulation_seconds,
            "device_seconds": device_seconds,
            "transfer_seconds": transfer_seconds,
            "total_seconds": total_seconds,
        },
        "device": _device_description(selected_device),
        "config": asdict(config),
    }


__all__ = [
    "MODE_ACCEPTED",
    "MODE_SWEEPS",
    "PHASE_ACCEPTED",
    "PHASE_FINAL",
    "PHASE_INITIAL",
    "PHASE_RELAXING",
    "PHASE_REJECTED",
    "PHASE_ROLLBACK",
    "PHASE_TRIAL",
    "ROLE_FINAL",
    "ROLE_INITIAL",
    "TRACE_SCHEMA_VERSION",
    "replay",
    "trace_finalize",
    "trace_simulate",
]
