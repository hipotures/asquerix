"""Measure complete subprocess wall time, excluding observer persistence."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import time
from asquerix.persistence import write_json

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--log',type=Path,required=True)
parser.add_argument('command',nargs=argparse.REMAINDER)
args=parser.parse_args()
command=args.command[1:] if args.command[:1]==['--'] else args.command
if not command:parser.error('a subprocess command is required')
with args.log.open('x') as stream:
    started_utc=datetime.now(timezone.utc).isoformat()
    begin=time.perf_counter_ns()
    result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
    finish=time.perf_counter_ns()
write_json(args.output,dict(command=command,started_utc=started_utc,
           finished_utc=datetime.now(timezone.utc).isoformat(),start_ns=begin,end_ns=finish,
           full_subprocess_seconds=(finish-begin)/1e9,exit_code=result.returncode,
           scope='Immediately before subprocess launch through subprocess exit; includes uv launcher, imports, all harness operations, final gzip manifest and terminal output. Excludes this observer serialization. Publication is disabled in benchmark.'))
raise SystemExit(result.returncode)
