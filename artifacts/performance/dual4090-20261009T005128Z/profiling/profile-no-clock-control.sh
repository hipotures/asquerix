#!/usr/bin/env bash
set -euo pipefail
AX_PROFILE_ROOT=artifacts/performance/dual4090-20261009T005128Z/profiling/no-clock-control
AX_REFERENCE=artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py
AX_METRICS=sm__warps_active.avg.pct_of_peak_sustained_active,smsp__warps_active.avg.per_cycle_active,smsp__warps_eligible.avg.per_cycle_active,smsp__issue_active.avg.pct_of_peak_sustained_active,smsp__average_warps_issue_stalled_wait_per_issue_active.ratio,smsp__average_warps_issue_stalled_long_scoreboard_per_issue_active.ratio,smsp__average_warps_issue_stalled_math_pipe_throttle_per_issue_active.ratio,smsp__average_warps_issue_stalled_not_selected_per_issue_active.ratio,smsp__sass_average_branch_targets_threads_uniform.pct,l1tex__t_sectors_pipe_lsu_mem_local_op_ld.sum,l1tex__t_sectors_pipe_lsu_mem_local_op_st.sum,l1tex__t_sectors_pipe_lsu_mem_global_op_ld.sum,l1tex__t_sectors_pipe_lsu_mem_global_op_st.sum,dram__bytes.sum
mkdir "$AX_PROFILE_ROOT"
for AX_CASE in early-n12:12:0 dense-n12:12:3 dense-n16:16:3; do
  IFS=: read -r AX_NAME AX_N AX_SKIP <<< "$AX_CASE"
  CUDA_VISIBLE_DEVICES=GPU-81ac6e96-0bfe-390d-beb1-241466569d6b ASQUERIX_WARP_CACHE=runs/dual4090-no-clock-profiles/cache \
    timeout 300s uv run --locked ncu --clock-control none --kernel-name regex:simulate --launch-skip "$AX_SKIP" --launch-count 1 \
    --metrics "$AX_METRICS" --export "$AX_PROFILE_ROOT/$AX_NAME" \
    python tools/kernel_profile.py --source "$AX_REFERENCE" --device cuda:0 --n "$AX_N" --count 131072 \
    --output "$AX_PROFILE_ROOT/$AX_NAME.json" > "$AX_PROFILE_ROOT/$AX_NAME.log" 2>&1
  ncu --import "$AX_PROFILE_ROOT/$AX_NAME.ncu-repz" --page raw --csv > "$AX_PROFILE_ROOT/$AX_NAME.csv"
  ncu --import "$AX_PROFILE_ROOT/$AX_NAME.ncu-repz" --page session > "$AX_PROFILE_ROOT/$AX_NAME-session.txt"
done
