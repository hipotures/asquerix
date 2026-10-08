import json
from pathlib import Path
import signal
import subprocess
from time import perf_counter, sleep

command = [".venv/bin/python", "-m", "asquerix.cli", "run", "--n", "12", "--trials", "64",
           "--batch-size", "8", "--max-seconds", "60", "--keep-best", "3", "--max-images", "2",
           "--output", "artifacts/pilot/stop-sigint"]
with Path("artifacts/pilot/stop-sigint.log").open("w") as log:
    child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
    sleep(2)
    requested = perf_counter()
    child.send_signal(signal.SIGINT)
    returncode = child.wait(timeout=15)
value = {"command": command, "returncode": returncode, "signal": "SIGINT",
         "signal_sent_to_process_exit_seconds": perf_counter()-requested,
         "note": "External request-to-exit includes in-flight drain, audit, persistence and reporting."}
Path("artifacts/pilot/stop-controller.json").write_text(json.dumps(value, indent=2)+"\n")
assert returncode == 0
metadata = json.loads(Path("artifacts/pilot/stop-sigint/environment.json").read_text())
assert metadata["stop_reason"] == "SIGINT"
assert metadata["completed_trials"] < 64
print(value)
print(metadata["stop_reason"], metadata["completed_trials"], metadata["stop_observed_to_batch_completion_seconds"])
