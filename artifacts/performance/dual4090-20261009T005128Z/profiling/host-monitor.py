"""Read-only aggregate/per-core CPU telemetry; no attribution of useful work."""
import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
import signal
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--seconds', type=float, default=1800)
args = parser.parse_args()
if args.seconds <= 0 or args.seconds > 3600:
    parser.error('seconds must be in (0,3600]')
stopped = False

def stop(*_):
    global stopped
    stopped = True

signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)

def sample():
    rows = {}
    for line in Path('/proc/stat').read_text().splitlines():
        if line.startswith('cpu'):
            name, *values = line.split()
            rows[name] = [int(x) for x in values[:8]]
    return rows

previous = sample()
deadline = time.monotonic() + args.seconds
with args.output.open('x', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=['utc','monotonic_ns','logical_cpus',
                            'aggregate_cpu_percent','maximum_core_cpu_percent','iowait_percent'])
    writer.writeheader()
    while not stopped and time.monotonic() < deadline:
        time.sleep(1)
        current = sample()
        rates, waits = {}, {}
        for name, values in current.items():
            delta = [a-b for a,b in zip(values,previous[name])]
            total = sum(delta)
            rates[name] = 100*(total-delta[3]-delta[4])/total if total else 0
            waits[name] = 100*delta[4]/total if total else 0
        writer.writerow(dict(utc=datetime.now(timezone.utc).isoformat(),monotonic_ns=time.perf_counter_ns(),
                             logical_cpus=len(rates)-1,aggregate_cpu_percent=rates['cpu'],
                             maximum_core_cpu_percent=max(v for k,v in rates.items() if k!='cpu'),
                             iowait_percent=waits['cpu']))
        stream.flush()
        previous = current
