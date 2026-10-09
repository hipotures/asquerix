"""Exercise the real laboratory UI with headless Chromium and retain evidence.

The check submits a small two-method campaign through the browser form, then
inspects the finished campaign through the same UI: mutation diffs, paired
replays, strategy overlays, durable history, the offline report with the
network disabled, and backward compatibility of historical trajectory files.
"""

from __future__ import annotations

import argparse
import base64
import json
import math
from pathlib import Path
import tempfile
import time
import urllib.request

from trajectory_browser_smoke import CDPError, CDPWebSocket, _free_port, _start_chromium, _wait_for_page, _write_report, run_smoke

FLAG_LABELS = {16: "rollback", 64: "discontinuous restore", 32: "best snapshot", 128: "finalization"}


def wait(cdp, expression, timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = cdp.evaluate(expression)
        if result:
            return result
        time.sleep(.2)
    raise TimeoutError(expression)


def screenshot(cdp, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(cdp.command("Page.captureScreenshot", {"format": "png"})["data"]))
    return str(path)


def fetch(url, binary=False):
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read()
    return data if binary else json.loads(data)


def frame_contexts(cdp):
    """Default JavaScript contexts of the current child frames, in document order."""
    tree = cdp.command("Page.getFrameTree")["frameTree"]
    children = [child["frame"]["id"] for child in tree.get("childFrames", [])]
    contexts = {}
    for event in cdp.events:
        if event["method"] == "Runtime.executionContextCreated":
            context = event["params"]["context"]
            if context.get("auxData", {}).get("isDefault"):
                contexts[context["auxData"]["frameId"]] = context["id"]
        elif event["method"] == "Runtime.executionContextDestroyed":
            contexts = {frame: identifier for frame, identifier in contexts.items()
                        if identifier != event["params"]["executionContextId"]}
    missing = [frame for frame in children if frame not in contexts]
    if missing:
        raise AssertionError(f"No JavaScript context for frames {missing}; sandboxed frames may be out of process")
    return [contexts[frame] for frame in children]


def frame_evaluate(cdp, context, expression):
    result = cdp.command("Runtime.evaluate", {"expression": expression, "contextId": context, "returnByValue": True})
    if "exceptionDetails" in result:
        raise AssertionError(result["exceptionDetails"])
    return result["result"].get("value")


def wait_frames(cdp, count, ready="window.asquerixTrajectory", timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        cdp.evaluate("0")  # drain context events
        try:
            contexts = frame_contexts(cdp)
            if len(contexts) >= count and all(frame_evaluate(cdp, context, "!!" + ready) for context in contexts[:count]):
                return contexts[:count]
        except (AssertionError, CDPError):
            pass
        time.sleep(.25)
    raise TimeoutError(f"{count} replay frames did not load")


def frames_evaluate(cdp, count, expression, timeout=30):
    """Evaluate in each replay frame, re-acquiring contexts after an iframe reload."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            return [frame_evaluate(cdp, context, expression) for context in wait_frames(cdp, count)]
        except CDPError:
            if time.monotonic() > deadline:
                raise
            time.sleep(.25)


def check_strategy_overlay(cdp, evidence):
    """Every recorded frame highlights its saved instruction; markers and two sides are explicit."""
    frames = cdp.evaluate("JSON.parse(document.getElementById('trajectory-data').textContent).metadata.strategy.frames")
    instructions = cdp.evaluate("JSON.parse(document.getElementById('trajectory-data').textContent).metadata.strategy.program.instructions.map(item=>item.op)")
    for index, saved in enumerate(frames):
        shown = cdp.evaluate(f"""(()=>{{window.asquerixTrajectory.seekFrame({index});
            const rows=[...document.querySelectorAll('#strategy-code li')];
            return {{current:rows.findIndex(row=>row.getAttribute('aria-current')==='true'),
                     position:document.getElementById('strategy-position').textContent,
                     state:document.getElementById('strategy-state').textContent}};}})()""")
        expected_pc = saved["pc"] if 0 <= saved["pc"] < len(instructions) else -1
        if shown["current"] != expected_pc:
            raise AssertionError(f"Frame {index}: highlighted instruction {shown['current']} != saved pc {saved['pc']}")
        if expected_pc >= 0 and not shown["position"].startswith(instructions[expected_pc]):
            raise AssertionError(f"Frame {index}: position label {shown['position']!r} does not name {instructions[expected_pc]}")
        for flag, label in FLAG_LABELS.items():
            if saved["flags"] & flag and label not in shown["state"]:
                raise AssertionError(f"Frame {index}: flag {label} is not displayed")
    evidence["overlay_frames_checked"] = len(frames)
    markers = {label: [index for index, saved in enumerate(frames) if saved["flags"] & flag] for flag, label in FLAG_LABELS.items()}
    evidence["markers"] = {label: len(indexes) for label, indexes in markers.items()}
    differing = [index for index, saved in enumerate(frames) if saved["side"] != saved["best_side"]]
    evidence["current_differs_from_best"] = len(differing)
    if differing:
        evidence["current_best_example"] = cdp.evaluate(
            f"window.asquerixTrajectory.seekFrame({differing[0]}); document.getElementById('strategy-state').textContent")
    cdp.evaluate("document.getElementById('go-best').click()")
    if cdp.evaluate("window.asquerixTrajectory.getFrame()") != cdp.evaluate("JSON.parse(document.getElementById('trajectory-data').textContent).metadata.strategy.best_frame"):
        raise AssertionError("Go to best state did not seek to the protected best frame")
    cdp.evaluate("document.getElementById('go-final-current').click()")
    if cdp.evaluate("window.asquerixTrajectory.getFrame()") != len(frames) - 1:
        raise AssertionError("Go to final current did not seek to the final frame")


def run(url, output, screenshots, old_trajectory, old_npz):
    evidence = {"status": "FAIL", "url": url, "actions": [], "screenshots": []}
    work = Path(tempfile.mkdtemp(prefix="asquerix-lab-browser-work-"))  # bulky intermediate HTML stays out of evidence
    log = evidence["actions"].append
    with tempfile.TemporaryDirectory(prefix="asquerix-lab-browser-", dir="/tmp", ignore_cleanup_errors=True) as profile:
        port = _free_port()
        # Keep sandboxed replay iframes in process so CDP can drive their players.
        browser = _start_chromium(Path(profile), port, ("--disable-features=IsolateSandboxedIframes",))
        try:
            version, page = _wait_for_page(port, 20)
            evidence["browser"] = version["Browser"]
            with CDPWebSocket(page["webSocketDebuggerUrl"], timeout=30) as cdp:
                for command in ("Runtime.enable", "Page.enable", "Network.enable", "Log.enable"):
                    cdp.command(command)
                cdp.command("Emulation.setDeviceMetricsOverride", {"width": 1500, "height": 1000, "deviceScaleFactor": 1, "mobile": False})

                # 1. Create and submit a small campaign through forms.
                cdp.command("Page.navigate", {"url": url})
                wait(cdp, "document.querySelector('[name=device]')?.options.length")
                cdp.evaluate("document.getElementById('new-campaign').click()")
                settings = {"name": "Browser search smoke", "candidate_budget": 4, "initial_pool": 2, "lambda": 2,
                            "training_count": 2, "holdout_count": 2, "max_seconds": 120, "attempts": 128,
                            "sweeps": 30000, "min_nodes": 4, "max_nodes": 6, "attempt_min": 4,
                            "attempt_max": 8, "sweep_min": 120, "sweep_max": 120, "max_frames": 96}
                cdp.evaluate("""(() => { const f=document.getElementById('campaign-form');
                    for (const [name,value] of Object.entries(""" + json.dumps(settings) + """)) f.elements.namedItem(name).value=String(value);
                    f.elements.namedItem('method').value='both';
                    f.elements.namedItem('publication').checked=false;
                    f.elements.namedItem('legacy_control').checked=true;
                    f.elements.namedItem('pulse_control').checked=true;
                    document.getElementById('review-plan').click(); })()""")
                evidence["plan_summary"] = cdp.evaluate("document.getElementById('plan-summary').textContent")
                evidence["screenshots"].append(screenshot(cdp, screenshots / "create.png"))
                cdp.evaluate("document.getElementById('campaign-form').requestSubmit()")
                identifier = wait(cdp, "location.hash.slice(1)")
                evidence["campaign_id"] = identifier
                log("Submitted a finite two-method search with both fixed controls through the campaign form")

                # 2. Close/reopen the page and see the same campaign continue.
                cdp.command("Page.navigate", {"url": "about:blank"})
                time.sleep(1)
                cdp.command("Page.navigate", {"url": url + "#" + identifier})
                wait(cdp, "['COMPLETED','PARTIAL','FAILED'].includes(document.getElementById('campaign-state')?.dataset.state)", 300)
                wait(cdp, "!document.getElementById('open-report').hidden", 120)
                state = cdp.evaluate("document.getElementById('campaign-state').dataset.state")
                evidence["state"] = state
                if state != "COMPLETED":
                    raise AssertionError(cdp.evaluate("document.getElementById('campaign-provenance').textContent"))
                evidence["phase_line"] = cdp.evaluate("document.getElementById('campaign-activity').textContent")
                log("Closed and reopened the page; the same CUDA campaign completed in the background")
                evidence["screenshots"].append(screenshot(cdp, screenshots / "campaign.png"))
                campaign = fetch(f"{url}/api/v1/campaigns/{identifier}")
                evidence["summary"] = {key: campaign["summary"].get(key) for key in
                                       ("completed_candidates", "completed_episode_executions", "replay_executions", "report_status")}

                # 3. Inspect a program and its mutation diff.
                programs = fetch(f"{url}/api/v1/campaigns/{identifier}/programs?limit=50")["items"]
                mutated = next((item for item in programs if item.get("mutation")), None)
                if mutated is None:
                    raise AssertionError("The (1 + lambda) arm produced no mutated candidate")
                label = mutated["id"]
                clicked = cdp.evaluate(f"""(()=>{{const row=[...document.querySelectorAll('#program-table tr')]
                    .find(row=>row.dataset.candidateId==={json.dumps(label)}); if(!row) return false;
                    row.querySelector('button').click(); return true;}})()""")
                if not clicked:
                    raise AssertionError(f"Program table has no row {label}")
                heading = wait(cdp, "document.querySelector('#program-inspector .diff') && document.querySelector('#program-inspector h4')?.textContent")
                if mutated["mutation"]["type"] not in heading:
                    raise AssertionError(f"Mutation heading {heading!r} does not name {mutated['mutation']['type']}")
                evidence["mutation"] = {"candidate": mutated["id"], "heading": heading,
                                        "instructions": cdp.evaluate("document.querySelectorAll('#program-inspector .program-list li').length")}
                cdp.evaluate("document.getElementById('program-inspector').scrollIntoView()")
                evidence["screenshots"].append(screenshot(cdp, screenshots / "program-diff.png"))
                log(f"Inspected mutated program {mutated['id']} with its before/after diff")

                # 7. Compare two programs on the same start.
                replays = [record["document"] for record in campaign["replays"] if record["state"] == "REPLAY_MATCHED"]
                evidence["replays"] = [{"candidate_id": item["candidate_id"], "frames": item["frames"]} for item in replays]
                if len({item["candidate_id"] for item in replays}) < 2:
                    raise AssertionError("Fewer than two matched replays of different programs")
                cdp.evaluate("document.querySelector('[data-tab=replays]').click()")
                wait(cdp, "document.querySelectorAll('#live-replays iframe').length===2")
                cdp.evaluate("""(()=>{const s=document.querySelectorAll('#live-replays select');s[0].value='0';s[1].value='1';
                    s[2].value='frame';s[1].dispatchEvent(new Event('change'));})()""")
                warning = cdp.evaluate("document.querySelector('#live-replays p').textContent")
                if not warning.startswith("Same initial-world identity"):
                    raise AssertionError(f"Paired replay warning: {warning}")
                time.sleep(1)
                wait_frames(cdp, 2)
                cdp.evaluate("""(()=>{const r=document.querySelector('#live-replays input[type=range]');r.value='500';r.dispatchEvent(new Event('input'));})()""")
                time.sleep(.5)
                positions = frames_evaluate(cdp, 2, "window.asquerixTrajectory.getFrame()")
                expected = [math.floor(.5 * (item["frames"] - 1) + .5) for item in replays[:2]]  # JavaScript Math.round
                if positions != expected:
                    raise AssertionError(f"Synchronized frames {positions} != {expected}")
                evidence["paired_positions"] = positions
                cdp.evaluate("document.getElementById('live-replays').scrollIntoView()")
                evidence["screenshots"].append(screenshot(cdp, screenshots / "paired-replay.png"))
                log("Compared two programs on the same initial world with synchronized frame seeking")

                # 8. Replay campaign history and see the corresponding incumbent/program state.
                cdp.evaluate("document.querySelector('[data-tab=history]').click()")
                total = int(wait(cdp, "document.querySelector('#live-history input[type=range]')?.max")) + 1
                checked = []
                for index in sorted({0, total // 3, 2 * total // 3, total - 1}):
                    cdp.evaluate(f"""(()=>{{const r=document.querySelector('#live-history input[type=range]');r.value='{index}';r.dispatchEvent(new Event('input'));}})()""")
                    expected = fetch(f"{url}/api/v1/campaigns/{identifier}/history-state?index={index}")
                    text = wait(cdp, f"(t=>t.startsWith('Event {expected['event']['id']} ')&&t)(document.querySelector('#live-history p')?.textContent||'')")
                    known = cdp.evaluate("document.querySelector('#live-history div').textContent")
                    if f"{expected['completed_candidates']} candidate evaluations" not in known:
                        raise AssertionError(f"History event {index} does not show the incumbent state")
                    if expected.get("candidate") and expected["candidate"]["program"]["hash"] not in known:
                        raise AssertionError(f"History event {index} does not show its program")
                    checked.append(text)
                evidence["history_events"] = {"total": total, "checked": checked}
                evidence["screenshots"].append(screenshot(cdp, screenshots / "history.png"))
                log(f"Scrubbed {len(checked)} of {total} durable history events with program state")

                # 4-6. Open real recorded geometry: overlay, markers, and current/best sides.
                evidence["overlays"] = []
                for record in campaign["replays"]:
                    if record["state"] != "REPLAY_MATCHED":
                        continue
                    html = next(item for item in record["document"]["artifacts"] if item["path"].endswith(".html"))
                    cdp.command("Page.navigate", {"url": f"{url}/api/v1/artifacts/{html['id']}"})
                    wait(cdp, "window.asquerixTrajectory")
                    overlay = {"candidate_id": record["document"]["candidate_id"], "artifact": html["id"]}
                    check_strategy_overlay(cdp, overlay)
                    evidence["overlays"].append(overlay)
                if not any(item["markers"]["rollback"] + item["markers"]["discontinuous restore"] for item in evidence["overlays"]):
                    raise AssertionError("No selected replay contains rollback or restore markers")
                if not any(item["current_differs_from_best"] for item in evidence["overlays"]):
                    raise AssertionError("No selected replay shows current L different from protected best L")
                chosen = max(evidence["overlays"], key=lambda item: (item["markers"]["rollback"] > 0, item["current_differs_from_best"]))
                cdp.command("Page.navigate", {"url": f"{url}/api/v1/artifacts/{chosen['artifact']}"})
                wait(cdp, "window.asquerixTrajectory")
                cdp.evaluate("""(()=>{const f=JSON.parse(document.getElementById('trajectory-data').textContent).metadata.strategy.frames;
                    const i=f.findIndex(x=>x.flags&16); window.asquerixTrajectory.seekFrame(i>=0?i:Math.floor(f.length/2));})()""")
                evidence["screenshots"].append(screenshot(cdp, screenshots / "strategy-replay.png"))
                log(f"Verified the highlighted instruction and markers on every frame of {len(evidence['overlays'])} replays")
                local_html = work / "replay-viewer.html"
                local_html.write_bytes(fetch(f"{url}/api/v1/artifacts/{chosen['artifact']}", binary=True))

                # 9. Open the exported report with the network disabled and play its trajectories.
                report_html = work / "report.html"
                report_html.write_bytes(fetch(f"{url}/api/v1/artifacts/{campaign['summary']['report_artifact_id']}", binary=True))
                cdp.command("Page.navigate", {"url": "about:blank"})
                time.sleep(.3)
                cdp.command("Network.emulateNetworkConditions", {"offline": True, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1})
                cdp.events.clear()
                cdp.command("Page.navigate", {"url": report_html.resolve().as_uri()})
                wait(cdp, "document.querySelectorAll('#candidate-table tr').length > 0")
                cdp.evaluate("document.getElementById('replays').scrollIntoView()")  # animation frames run only when visible
                time.sleep(1)
                before = frames_evaluate(cdp, 2, "window.asquerixTrajectory.getFrame()")[0]
                frames_evaluate(cdp, 2, "window.asquerixTrajectory.setPlaying(true)")
                time.sleep(1.0)
                after = frames_evaluate(cdp, 2, "(()=>{const f=window.asquerixTrajectory.getFrame();window.asquerixTrajectory.setPlaying(false);return f;})()")[0]
                if after <= before:
                    raise AssertionError(f"Offline report replay did not advance: {before} -> {after}")
                requests = [event["params"]["request"]["url"] for event in cdp.events if event["method"] == "Network.requestWillBeSent"
                            and not event["params"]["request"]["url"].startswith(("file:", "data:", "about:", "blob:"))]
                if requests:
                    raise AssertionError(f"Offline report requested network resources: {requests}")
                evidence["offline_report"] = {"bytes": report_html.stat().st_size, "playback": [before, after],
                                              "candidates": cdp.evaluate("document.querySelectorAll('#candidate-table tr').length")}
                evidence["screenshots"].append(screenshot(cdp, screenshots / "offline-report.png"))
                cdp.command("Network.emulateNetworkConditions", {"offline": False, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1})
                log("Opened the exported report offline and played an embedded trajectory")

                evidence["page_errors"] = [event for event in cdp.events if event["method"] == "Runtime.exceptionThrown"]
                evidence["console_errors"] = [event for event in cdp.events if event["method"] == "Log.entryAdded"
                                              and event["params"]["entry"]["level"] == "error"]
                if evidence["page_errors"] or evidence["console_errors"]:
                    raise AssertionError(evidence["page_errors"] or evidence["console_errors"])
        except BaseException as error:
            evidence["error"] = f"{type(error).__name__}: {error}"
            raise
        finally:
            browser.terminate()
            browser.wait(timeout=10)
            _write_report(output, evidence)

    # 4. Full geometric controls on the laboratory replay; 10. historical files remain usable,
    # both as saved before the laboratory and re-rendered by the current viewer.
    from asquerix.trajectory_format import load_trajectory
    from asquerix.trajectory_viewer import render_html
    rerendered = work / "historical-rerendered.html"
    rerendered.write_bytes(render_html(*load_trajectory(old_npz)))
    for name, path in (("lab_replay_viewer", local_html), ("historical_trajectory", old_trajectory),
                       ("historical_rerendered", rerendered)):
        result = run_smoke(path, output.parent / f"{name}.json.gz", screenshots / name, 30.0)
        evidence[name] = {"html": str(path), "status": result["status"], "screenshot": result.get("screenshot")}
        if result["status"] != "PASS":
            _write_report(output, evidence)
            raise AssertionError(f"{name} viewer check failed: {result.get('error')}")
        log(f"Exercised play/pause/scrub/zoom/pan/square selection/trails on {name}")
    evidence["status"] = "PASS"
    _write_report(output, evidence)
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8766")
    parser.add_argument("--output", type=Path, default=Path("artifacts/lab/browser/report.json.gz"))
    parser.add_argument("--screenshots", type=Path, default=Path("artifacts/lab/browser/screens"))
    parser.add_argument("--old-trajectory", type=Path,
                        default=Path("artifacts/trajectories/viewer-center-trails/historical/trial-4124.html"),
                        help="Historical viewer HTML saved before the laboratory")
    parser.add_argument("--old-npz", type=Path,
                        default=Path("artifacts/trajectories/demo-historical-4124/trajectories/trial-4124.npz"),
                        help="Historical trajectory re-rendered with the current viewer")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = run(args.url, args.output, args.screenshots, args.old_trajectory, args.old_npz)
    print(f"Browser {result['status']}: {args.output}; campaign {result['campaign_id']}")


if __name__ == "__main__":
    main()
