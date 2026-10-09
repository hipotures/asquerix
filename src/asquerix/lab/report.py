"""Self-contained campaign inspection and playable exports; no API dependency."""

from __future__ import annotations

import html
import json
from pathlib import Path
from time import perf_counter

from ..persistence import open_jsonl_writer, read_json, read_jsonl, write_json
from ..trajectory_format import atomic_write_bytes
from ..trajectory_viewer import _json_for_script
from .evaluation import paired_comparison
from .storage import check_quota, sha256, storage_bytes

STATIC = Path(__file__).parent / "static"

SCRIPT = r"""
(() => {
const DATA = JSON.parse(document.getElementById('report-data').textContent);
const {element,number,programView,curve,historyView,replayComparison} = LabInspect;
const candidates = DATA.programs;
const table = document.getElementById('candidate-table');
for (const candidate of candidates) {
  const row=element('tr');
  for (const value of [candidate.arm,candidate.position,number(candidate.score?.mean_best_L),number(candidate.holdout_score?.mean_best_L),number(candidate.score?.best_L),candidate.score?.eligible ? 'Eligible' : 'Ineligible / incomplete']) row.append(element('td',String(value)));
  const cell=element('td'), button=element('button','Inspect program'); button.addEventListener('click',()=>programView(document.getElementById('program'),candidate,candidates)); cell.append(button); row.append(cell); table.append(row);
}
if (candidates.length) programView(document.getElementById('program'),candidates[0],candidates);
historyView(document.getElementById('history'),DATA.events,candidates,candidate=>programView(document.getElementById('program'),candidate,candidates));
function drawCurve() {
  const key=document.getElementById('curve-axis').value;
  const points=[]; const counts={}; const work={}; const incumbents={};
  for (const candidate of candidates.filter(item=>!['controls','fixed'].includes(item.arm)).sort((a,b)=>a.completed_at-b.completed_at)) {
    counts[candidate.arm]=(counts[candidate.arm]||0)+(candidate.score?.complete ? 1 : 0);
    work[candidate.arm]=(work[candidate.arm]||0)+(candidate.score?.total_charged_work||0);
    if (candidate.score?.eligible) {
      incumbents[candidate.arm]=Math.min(incumbents[candidate.arm]??Infinity,candidate.score.mean_best_L);
      points.push({arm:candidate.arm,candidate_id:candidate.id,x:key==='evaluations'?counts[candidate.arm]:key==='work'?work[candidate.arm]:candidate.arm_execution_elapsed_seconds??candidate.execution_elapsed_seconds,y:incumbents[candidate.arm]});
    }
  }
  curve(document.getElementById('curve'),points,{xLabel:key==='evaluations'?'Completed candidate evaluations':key==='work'?'Charged work':'Arm execution seconds',onSelect:point=>programView(document.getElementById('program'),candidates.find(item=>item.id===point.candidate_id),candidates)});
}
document.getElementById('curve-axis').addEventListener('change',drawCurve); drawCurve();
replayComparison(document.getElementById('replays'),DATA.replays,replay=>replay.html);
document.getElementById('paired-data').textContent=JSON.stringify(DATA.paired,null,2);
})();
"""


def generate(directory: Path, events: list[dict], *, campaign=None) -> dict:
    started = perf_counter()
    manifest = read_json(directory / "campaign.json.gz")
    summary = read_json(directory / "summaries.json.gz")
    programs = list(read_jsonl(directory / "programs.jsonl.gz"))
    with open_jsonl_writer(directory / "events.jsonl.gz") as stream:
        for event in events:
            stream.write(json.dumps(event, allow_nan=False, separators=(",", ":")) + "\n")
    rows = []
    for chunk in summary["chunks"]:
        rows.extend(read_jsonl(directory / chunk["records_path"]))
    paired = {}
    leaders = [candidate for candidate in programs if candidate["arm"] in ("controls", "fixed") or candidate["id"] in {winner["candidate_id"] for winner in summary["frozen_winners"]}]
    for left_index, left in enumerate(leaders):
        for right in leaders[left_index + 1:]:
            for bank in ("training", "holdout"):
                paired[f"{bank}: {left['id']} vs {right['id']}"] = paired_comparison(
                    [row for row in rows if row["candidate_id"] == left["id"] and row["bank"] == bank],
                    [row for row in rows if row["candidate_id"] == right["id"] and row["bank"] == bank])
    write_json(directory / "comparisons.json.gz", paired)
    replays = []
    for replay in summary["replays"]:
        item = dict(replay)
        item["html"] = (directory / next(artifact["path"] for artifact in replay["artifacts"] if artifact["path"].endswith(".html"))).read_text()
        replays.append(item)
    data = {"campaign": manifest, "summary": summary, "programs": programs, "events": events, "replays": replays, "paired": paired}
    name = html.escape(manifest["spec"]["name"])
    payload = _json_for_script(data)
    document = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{name} — Asquerix</title><style>{(STATIC / "style.css").read_text()}</style></head><body>
<header><div class="brand"><span class="mark"><i></i><i></i><i></i><i></i></span><div><strong>ASQUERIX / EXPERIMENT LAB</strong><small>Offline campaign evidence · rigid unit squares</small></div></div><span class="badge">{html.escape(summary["state"])}</span></header>
<main><h1>{name}</h1><p class="muted">n = {manifest["spec"]["n"]} · profile {html.escape(summary["profile_hash"])} · {summary["completed_episode_executions"]} completed scientific episode executions · {summary["replay_executions"]} diagnostic replays</p><p class="notice">{html.escape(summary["scientific_caveat"])} All ranking best poses were independently checked. GPU acceptance, validation, and errors remain separate in the native records. Training winners were frozen before holdout.</p>
<section class="card"><h2>Quality, reliability and cost</h2><label>Curve coordinate<select id="curve-axis"><option value="evaluations">Completed candidate evaluations</option><option value="work">Charged work</option><option value="time">Arm execution time</option></select></label><div id="curve"></div><p class="muted">Mixed strategy batch timing is not isolated per-program timing. Native chunks retain measured timing scopes. Equal candidate budgets do not imply equal work.</p><div class="table-wrap"><table><thead><tr><th>Arm</th><th>Candidate</th><th>Training mean L</th><th>Holdout mean L</th><th>Best individual L</th><th>Eligibility</th><th>Program</th></tr></thead><tbody id="candidate-table"></tbody></table></div></section>
<section class="split"><div class="card"><h2>Search history</h2><div id="history"></div></div><div class="card"><h2>Program explorer</h2><div id="program"></div></div></section>
<section class="card"><h2>Geometric replay and paired programs</h2><div id="replays"></div></section><details class="card"><summary>Paired per-start differences</summary><pre id="paired-data"></pre></details>
<details class="card"><summary>Configuration and provenance</summary><pre>{html.escape(json.dumps({"campaign": manifest, "summary": summary}, indent=2))}</pre></details></main><script id="report-data" type="application/json">{payload}</script><script>{(STATIC / "inspect.js").read_text()}\n{SCRIPT}</script></body></html>'''
    if campaign:
        check_quota(campaign, directory, reserve=len(document.encode()))
    atomic_write_bytes(directory / "report.html", document.encode())
    lines = [f"# {manifest['spec']['name']}", "", f"State: **{summary['state']}**. Square count: {manifest['spec']['n']}.", "",
             f"Completed candidate evaluations: {summary['completed_candidates']}/{summary['logical_candidate_budget']}.",
             f"Scientific episode executions: {summary['completed_episode_executions']}. Submitted attempts: {summary['submitted_episode_attempts']}.",
             f"Diagnostic replays: {summary['replay_executions']}; cached-parent reuse: {summary['cache_hits']}.", "",
             "Every ranked best pose is independently CPU validated. Native NPZ chunks preserve exact FP32 best/current geometry and defined VM/result fields.",
             "Training winners are frozen before untouched holdout. A valid construction supports an upper bound; this functional pilot makes no optimality or method-superiority claim.", "",
             "| Program | Arm | Training mean L | Holdout mean L | Valid/total |", "|---|---|---|---|---|"]
    for candidate in leaders:
        training, holdout = candidate.get("score", {}), candidate.get("holdout_score", {})
        lines.append(f"| {candidate['program']['authored'].get('name', candidate['id'])} | {candidate['arm']} | {training.get('mean_best_L')} | {holdout.get('mean_best_L')} | {training.get('validation_counts', {}).get('NUMERICALLY_VALIDATED', 0)}/{training.get('expected_episodes', 0)} |")
    lines += ["", "Open `report.html` with the network disabled for programs, durable history, actual curves and embedded selected trajectories.",
              "Native replay comparison checks best/current endpoints, defined fields, RNG and work; it does not certify unrecorded intermediate states.", ""]
    atomic_write_bytes(directory / "report.md", "\n".join(lines).encode())
    artifacts = [{"path": str(path.relative_to(directory)), "size_bytes": path.stat().st_size, "sha256": sha256(path)}
                 for path in sorted(directory.rglob("*")) if path.is_file() and path.name not in ("manifest.json.gz", "publication.json.gz")]
    report = {"schema": "asquerix-lab-manifest-v1", "campaign_id": summary["id"], "state": summary["state"],
              "source_revision": read_json(directory / "environment.json.gz")["source_revision"],
              "executable_hash": summary["executable_hash"], "artifacts": artifacts,
              "total_artifact_bytes": sum(item["size_bytes"] for item in artifacts), "report_seconds": perf_counter() - started}
    write_json(directory / "manifest.json.gz", report)
    return report
