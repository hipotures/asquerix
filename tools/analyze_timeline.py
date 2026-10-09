"""Analyze the installed Nsight Systems SQLite schema without copying snapshots."""
import argparse
import csv
from pathlib import Path
import sqlite3

from asquerix.persistence import read_json, write_json


def union_seconds(intervals):
    total = 0
    end = None
    for start, finish in sorted(intervals):
        if end is None or start >= end:
            total += finish - start
            end = finish
        elif finish > end:
            total += finish - end
            end = finish
    return total / 1e9


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    connection = sqlite3.connect(f"file:{args.sqlite.resolve()}?mode=ro", uri=True)
    manifest = read_json(args.manifest)
    anchor = connection.execute("SELECT systemClockNs FROM TARGET_INFO_SESSION_START_TIME").fetchone()[0]
    # deviceId in CUPTI is process-local here: both UUID-isolated workers use
    # ordinal zero. Map (pid, local ordinal) through Nsight's recorded UUIDs.
    mapping = {(pid, ordinal): "GPU-" + uuid for ordinal, pid, uuid in connection.execute(
        "SELECT cudaId,pid,uuid FROM TARGET_INFO_CUDA_DEVICE")}
    kernels = []
    for start, end, ordinal, global_pid, grid, name in connection.execute(
            "SELECT k.start,k.end,k.deviceId,k.globalPid,k.gridX,s.value "
            "FROM CUPTI_ACTIVITY_KIND_KERNEL k JOIN StringIds s ON s.id=k.shortName ORDER BY k.start"):
        pid = (global_pid & ((1 << 48) - 1)) >> 24
        kernels.append(dict(start=start + anchor, end=end + anchor, uuid=mapping[pid, ordinal],
                            pid=pid, local_device=ordinal, grid=grid, name=name))
    summaries = []
    rows = []
    for measurement in manifest["measurements"]:
        release, finish = measurement["release_ns"], measurement["end_ns"]
        selected = [k for k in kernels if release <= k["start"] and k["end"] <= finish
                    and "simulate" in k["name"] and k["grid"] == manifest["batch_size"] // 32]
        per_device = []
        for device in manifest["devices"]:
            own = [k for k in selected if k["uuid"] == device["uuid"]]
            gaps = [(own[i]["start"] - own[i-1]["end"]) / 1e9 for i in range(8, len(own), 8)]
            per_device.append(dict(uuid=device["uuid"], production_kernel_count=len(own),
                                   kernel_seconds=union_seconds([(k["start"], k["end"]) for k in own]),
                                   inter_batch_submission_gaps_seconds=gaps,
                                   gap_scope="Last simulation kernel through first simulation kernel of next batch; includes host processing and small pose/scalar transfers."))
        busy = union_seconds([(k["start"], k["end"]) for k in selected])
        simultaneous = sum(d["kernel_seconds"] for d in per_device) - busy
        sync = connection.execute(
            "SELECT sum(end-start)/1e9,count(*) FROM CUPTI_ACTIVITY_KIND_RUNTIME r "
            "JOIN StringIds s ON s.id=r.nameId WHERE s.value='cuCtxSynchronize' AND start>=? AND end<=?",
            (release - anchor, finish - anchor)).fetchone()
        # Native leaf samples are attributed by thread, and the API ranges
        # independently identify which samples occurred while synchronizing.
        native = list(connection.execute(
            "SELECT e.globalTid,m.value,count(*) FROM COMPOSITE_EVENTS e "
            "JOIN SAMPLING_CALLCHAINS c ON c.id=e.id AND c.stackDepth=0 "
            "JOIN StringIds m ON m.id=c.module WHERE e.start>=? AND e.start<=? "
            "GROUP BY e.globalTid,c.module ORDER BY count(*) DESC LIMIT 30",
            (release - anchor, finish - anchor)))
        summaries.append(dict(mode=measurement["mode"], measurement=measurement["measurement"],
                              common_wall_seconds=measurement["common_execution_seconds"], devices=per_device,
                              kernel_union_seconds=busy, simultaneous_kernel_seconds=simultaneous,
                              synchronization_api_seconds=sync[0], synchronization_api_calls=sync[1],
                              native_leaf_samples=[dict(global_tid=tid, pid=(tid & ((1 << 48)-1)) >> 24,
                                                   tid=tid & ((1 << 24)-1), module=module, samples=count)
                                                   for tid, module, count in native]))
        for kernel in selected:
            rows.append(dict(mode=measurement["mode"], uuid=kernel["uuid"], pid=kernel["pid"],
                             start_seconds=(kernel["start"] - release) / 1e9,
                             end_seconds=(kernel["end"] - release) / 1e9, grid=kernel["grid"]))
    with (args.output / "kernel-intervals.csv").open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=("mode", "uuid", "pid", "start_seconds", "end_seconds", "grid"))
        writer.writeheader()
        writer.writerows(rows)
    write_json(args.output / "analysis.json", dict(source=str(args.sqlite), mappings=[dict(pid=pid, local_ordinal=ordinal, uuid=uuid)
               for (pid, ordinal), uuid in mapping.items()], measurements=summaries,
               warning="Profiled diagnostic only. API durations across concurrent threads overlap and are not additive wall time."))
    connection.close()
    print(f"Timeline analysis saved: {args.output}")


if __name__ == "__main__":
    main()
