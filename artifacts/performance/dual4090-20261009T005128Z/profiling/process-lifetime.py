"""Measure an existing benchmark process lifetime from Linux start ticks."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import time
from asquerix.persistence import write_json

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pid',type=int,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
path=Path(f'/proc/{args.pid}/stat')
fields=path.read_text().rsplit(')',1)[1].split()
start_ticks=int(fields[19]); hz=os.sysconf('SC_CLK_TCK')
command=Path(f'/proc/{args.pid}/cmdline').read_bytes().replace(b'\0',b' ').decode()
if 'dual_gpu_benchmark.py run ' not in command:
    parser.error('target must be the benchmark CLI process')
while path.exists():
    try:
        if path.read_text().rsplit(')',1)[1].split()[0]=='Z':break
    except FileNotFoundError:
        break
    time.sleep(.1)
observed=time.clock_gettime(time.CLOCK_BOOTTIME)
write_json(args.output,dict(pid=args.pid,command=command,clock_ticks_per_second=hz,
           process_start_ticks=start_ticks,exit_observed_boottime_seconds=observed,
           full_python_cli_process_seconds=observed-start_ticks/hz,
           finished_utc=datetime.now(timezone.utc).isoformat(),
           uncertainty_seconds=.1+1/hz,
           scope='Linux process creation through observed exit/zombie; includes Python imports, argument parsing, entire harness, final JSON serialization and terminal output. Excludes uv launcher startup and this observer file. Birth quantization and exit polling uncertainty are reported; not pure CUDA time.'))
