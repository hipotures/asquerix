"""Generate a self-contained offline HTML viewer for one trajectory.

The viewer is intentionally plain JavaScript and Canvas.  The embedded
numeric arrays are decoded from little-endian base64 bytes in the browser;
there is no network access, server, package loader, or CUDA dependency.
"""

from __future__ import annotations

import base64
import json
from collections.abc import Mapping
from typing import Any

import numpy as np

from .trajectory_format import ARRAY_DTYPES, SCHEMA, validate_arrays, validate_metadata


def _json_for_script(value: Any) -> str:
    """Serialize JSON while preventing data from terminating its script tag."""

    try:
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("viewer metadata must be strict JSON serializable") from exc
    # JSON permits these escapes and browsers decode them before JSON.parse;
    # escaping '<' is the relevant XSS boundary for an application/json script.
    return (
        encoded.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _array_payload(arrays: Mapping[str, np.ndarray]) -> dict[str, Any]:
    encoded: dict[str, Any] = {}
    for name, dtype in ARRAY_DTYPES.items():
        array = arrays[name]
        # The format validator requires C order and a fixed little-endian dtype.
        encoded[name] = {
            "dtype": dtype.str,
            "shape": list(array.shape),
            "base64": base64.b64encode(array.tobytes(order="C")).decode("ascii"),
        }
    return encoded


def _payload(arrays: Mapping[str, np.ndarray], metadata: Mapping[str, Any]) -> str:
    return _json_for_script({"schema": SCHEMA, "arrays": _array_payload(arrays), "metadata": dict(metadata)})


_HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Asquerix trajectory</title>
<style>
:root {
  color-scheme: dark;
  --ink: #e7e5df;
  --muted: #a5aaa7;
  --line: #334147;
  --panel: #151c20;
  --panel-2: #1c262b;
  --accent: #e2b35c;
  --accent-2: #78d6c3;
  --danger: #e88475;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  min-width: 880px;
  background: #0d1215;
  color: var(--ink);
}
main { max-width: 1500px; margin: 0 auto; padding: 28px 30px 40px; }
.eyebrow { color: var(--accent); font-size: 11px; letter-spacing: .18em; text-transform: uppercase; }
h1 { margin: 7px 0 5px; font: 700 31px/1.05 Georgia, "Times New Roman", serif; letter-spacing: -.03em; }
.subhead { margin: 0; color: var(--muted); font-size: 12px; }
.status-strip {
  display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 1px;
  margin: 23px 0 16px; border: 1px solid var(--line); background: var(--line);
}
.status-card { min-height: 60px; padding: 10px 13px; background: var(--panel); }
.status-card .label { color: var(--muted); font-size: 10px; text-transform: uppercase; letter-spacing: .08em; }
.status-card .value { margin-top: 6px; color: var(--accent-2); font-size: 13px; overflow-wrap: anywhere; }
.warning { display: none; border-left: 3px solid var(--accent); padding: 10px 13px; margin: 10px 0 15px; background: #211f19; color: #e9d7a8; font-size: 12px; line-height: 1.5; }
.warning.visible { display: block; }
.panels { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.panel { min-width: 0; border: 1px solid var(--line); background: var(--panel); }
.panel-head { display: flex; align-items: baseline; justify-content: space-between; border-bottom: 1px solid var(--line); padding: 10px 13px 9px; }
.panel-head h2 { margin: 0; font: 600 14px/1.2 Georgia, "Times New Roman", serif; }
.panel-head span { color: var(--muted); font-size: 10px; }
.canvas-wrap { aspect-ratio: 1.45; min-height: 300px; padding: 13px; background: #10171a; }
canvas { display: block; width: 100%; height: 100%; background: #0b1012; border: 1px solid #2a373c; }
.controls { margin-top: 14px; padding: 13px; border: 1px solid var(--line); background: var(--panel); }
.button-row { display: flex; flex-wrap: wrap; align-items: center; gap: 7px; }
button, select { border: 1px solid #526168; background: var(--panel-2); color: var(--ink); padding: 7px 10px; font: inherit; font-size: 11px; cursor: pointer; }
button:hover, select:hover { border-color: var(--accent); }
button:focus-visible, select:focus-visible, input:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
button.primary { border-color: var(--accent); color: var(--accent); }
input[type="range"] { flex: 1 1 230px; min-width: 180px; accent-color: var(--accent); }
.frame-line { display: flex; align-items: center; gap: 10px; margin-top: 11px; color: var(--muted); font-size: 11px; }
.frame-line output { color: var(--ink); white-space: nowrap; }
.options { display: flex; flex-wrap: wrap; gap: 15px; margin-top: 12px; color: var(--muted); font-size: 11px; }
label { cursor: pointer; }
label input { accent-color: var(--accent-2); vertical-align: -1px; }
.details { display: grid; grid-template-columns: 1.2fr 1fr; gap: 13px; margin-top: 14px; }
.detail-box { border: 1px solid var(--line); padding: 12px 13px; background: var(--panel); }
.detail-box h3 { margin: 0 0 9px; color: var(--accent); font-size: 10px; letter-spacing: .12em; text-transform: uppercase; }
.detail-box p { margin: 5px 0; color: var(--muted); font-size: 11px; line-height: 1.45; }
.detail-box strong { color: var(--ink); font-weight: 500; }
.provisional { color: var(--danger) !important; }
@media (max-width: 980px) { body { min-width: 0; } main { padding: 20px 15px 30px; } .panels, .details { grid-template-columns: 1fr; } .status-strip { grid-template-columns: repeat(2, 1fr); } }
</style>
</head>
<body>
<main>
  <div class="eyebrow">Asquerix / diagnostic playback</div>
  <h1>Selected trajectory</h1>
  <p class="subhead" id="trial-line">A bounded CUDA replay of one accepted compression run.</p>

  <section class="status-strip" aria-label="Replay status">
    <div class="status-card"><div class="label">Replay comparison</div><div class="value" id="comparison-status">—</div></div>
    <div class="status-card"><div class="label">Termination</div><div class="value" id="termination-status">—</div></div>
    <div class="status-card"><div class="label">Current frame</div><div class="value" id="frame-status">—</div></div>
    <div class="status-card"><div class="label">Current validation</div><div class="value" id="validation-status">—</div></div>
  </section>
  <div class="warning" id="provisional-warning">Intermediate states marked provisional may contain overlaps or leave the current container. They are diagnostic replay states, not accepted packings.</div>

  <section class="panels" aria-label="Trajectory panels">
    <article class="panel">
      <div class="panel-head"><h2>Initial arrangement</h2><span>frame 1 / fixed reference</span></div>
      <div class="canvas-wrap"><canvas id="initial-canvas" aria-label="Initial arrangement"></canvas></div>
    </article>
    <article class="panel">
      <div class="panel-head"><h2>Current recorded frame</h2><span id="current-caption">paused at start</span></div>
      <div class="canvas-wrap"><canvas id="current-canvas" aria-label="Current recorded frame"></canvas></div>
    </article>
  </section>

  <section class="controls" aria-label="Playback controls">
    <div class="button-row">
      <button type="button" id="first-frame" title="First frame">|&lt;</button>
      <button type="button" id="previous-frame" title="Previous frame">&lt;</button>
      <button type="button" id="play-pause" class="primary">Play</button>
      <button type="button" id="next-frame" title="Next frame">&gt;</button>
      <button type="button" id="last-frame" title="Last frame">&gt;|</button>
      <select id="speed" aria-label="Playback speed">
        <option value="1">1 fps</option><option value="2">2 fps</option><option value="4" selected>4 fps</option><option value="8">8 fps</option><option value="16">16 fps</option>
      </select>
      <button type="button" id="export-svg">Export current SVG</button>
    </div>
    <div class="frame-line"><input id="frame-slider" type="range" min="0" value="0" step="1" aria-label="Recorded frame"><output id="frame-output">Frame 1 / 1</output></div>
    <div class="options">
      <label><input id="show-ids" type="checkbox" checked> show square IDs</label>
      <label><input id="show-orientation" type="checkbox" checked> show orientation marks</label>
      <span>Playback visits saved frames only; no interpolation.</span>
    </div>
  </section>

  <section class="details">
    <div class="detail-box"><h3>Recorded state</h3><p id="algorithm-line">—</p><p id="side-line">—</p><p id="validation-detail">—</p></div>
    <div class="detail-box"><h3>Evidence and sampling</h3><p id="comparison-detail">—</p><p id="sampling-detail">—</p><p id="provenance-detail">—</p></div>
  </section>
</main>

<script id="trajectory-data" type="application/json">__PAYLOAD__</script>
<script>
(() => {
  "use strict";
  const DATA = JSON.parse(document.getElementById("trajectory-data").textContent);
  const A = {};
  const PHASES = ["INITIAL", "TRIAL", "RELAXING", "ACCEPTED", "REJECTED", "ROLLBACK", "FINAL"];
  const COLORS = ["#e2b35c", "#78d6c3", "#d88978", "#a5c66f", "#b49be5", "#e1a1c9", "#77b5de", "#e5d08a"];
  const endpoint = DATA.metadata.comparison || {};
  const sampling = DATA.metadata.sampling || {};
  const provenance = DATA.metadata.provenance || {};
  const originalProvenance = provenance.original || {};
  const replayProvenance = provenance.replay || {};
  const validationRecords = Array.isArray(DATA.metadata.validations) ? DATA.metadata.validations : [];

  function decodeBase64(spec) {
    const text = atob(spec.base64);
    const bytes = new Uint8Array(text.length);
    for (let i = 0; i < text.length; i += 1) bytes[i] = text.charCodeAt(i);
    const count = spec.shape.reduce((a, b) => a * b, 1);
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const out = spec.dtype === "<f4" ? new Float32Array(count)
      : spec.dtype === "<i4" ? new Int32Array(count)
      : spec.dtype === "<i8" ? new Array(count)
      : new Uint8Array(count);
    for (let i = 0; i < count; i += 1) {
      if (spec.dtype === "<f4") out[i] = view.getFloat32(i * 4, true);
      else if (spec.dtype === "<i4") out[i] = view.getInt32(i * 4, true);
      else if (spec.dtype === "<i8") out[i] = view.getBigInt64(i * 8, true);
      else out[i] = view.getUint8(i);
    }
    return out;
  }
  for (const [name, spec] of Object.entries(DATA.arrays)) A[name] = decodeBase64(spec);
  const F = DATA.arrays.poses.shape[0];
  const N = DATA.arrays.poses.shape[1];
  let frame = 0;
  let playing = false;
  let lastTick = 0;
  let speed = 4;
  let showIds = true;
  let showOrientation = true;
  const initialSideValue = Number(A.side[0]);
  const initialSide = Number.isFinite(initialSideValue) && initialSideValue > 0 ? initialSideValue : 1;
  const retainedCount = sampling.retained ?? sampling.retained_frames ?? F;
  const observedCount = sampling.observed ?? sampling.events_seen ?? F;
  const suppressedCount = sampling.suppressed ?? sampling.suppressed_frames ?? 0;
  const effectiveStride = sampling.effective_stride ?? 1;
  const frameCap = sampling.max_frames ?? F;
  const initialCanvas = document.getElementById("initial-canvas");
  const currentCanvas = document.getElementById("current-canvas");
  const slider = document.getElementById("frame-slider");
  slider.max = String(Math.max(0, F - 1));
  document.getElementById("trial-line").textContent = `Trial ${String(DATA.metadata.trial_id)} · ${N} unit squares · seed ${String(DATA.metadata.seed)}`;
  document.getElementById("comparison-status").textContent = String(endpoint.status || "REFERENCE_INCOMPLETE");
  document.getElementById("termination-status").textContent = String(DATA.metadata.termination_reason || "UNKNOWN");
  document.getElementById("sampling-detail").textContent = `Sampling: ${String(retainedCount)} retained / ${String(observedCount)} observed; ${String(suppressedCount)} suppressed; effective stride ${String(effectiveStride)}; cap ${String(frameCap)}.`;
  document.getElementById("comparison-detail").textContent = `This is a newly recorded replay. Endpoint/result comparison scope: ${String(endpoint.scope || "defined saved endpoint fields")} — intermediate states are not proven identical.`;
  const replayRevision = replayProvenance.source_revision || replayProvenance.revision || provenance.replay_revision || provenance.source_revision || "unrecorded";
  const replayDevice = replayProvenance.device_uuid || replayProvenance.device_name || replayProvenance.gpu_uuid || replayProvenance.gpu_model || provenance.replay_gpu_uuid || "unrecorded";
  const provenanceStatus = provenance.status || endpoint.provenance_status || "unrecorded";
  document.getElementById("provenance-detail").textContent = `Provenance: ${String(provenanceStatus)} · replay revision ${String(replayRevision)} · replay device ${String(replayDevice)} · original revision ${String(originalProvenance.source_revision || originalProvenance.revision || "unrecorded")}.`;
  if (suppressedCount || effectiveStride > 1 || observedCount > retainedCount) document.getElementById("provisional-warning").classList.add("visible");

  function dimensions(canvas) {
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(160, Math.floor(rect.width || 500));
    const height = Math.max(160, Math.floor(rect.height || 350));
    const dpr = Math.max(1, window.devicePixelRatio || 1);
    if (canvas.width !== width * dpr || canvas.height !== height * dpr) { canvas.width = width * dpr; canvas.height = height * dpr; }
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, width, height };
  }
  function mapPoint(x, y, width, height, scale) { return [width / 2 + x * scale, height / 2 - y * scale]; }
  function poseAt(index, square) {
    const offset = (index * N + square) * 3;
    return [Number(A.poses[offset]), Number(A.poses[offset + 1]), Number(A.poses[offset + 2])];
  }
  function drawPanel(canvas, index, isInitial, sharedScale) {
    const {ctx, width, height} = dimensions(canvas);
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#0b1012"; ctx.fillRect(0, 0, width, height);
    const side = Number(A.side[index]);
    const validSide = Number.isFinite(side) && side > 0;
    if (validSide) {
      const [left, top] = mapPoint(-side / 2, side / 2, width, height, sharedScale);
      ctx.strokeStyle = "#62727a"; ctx.lineWidth = 1.4; ctx.strokeRect(left, top, side * sharedScale, side * sharedScale);
    }
    let omittedSquares = 0;
    for (let square = 0; square < N; square += 1) {
      const [x, y, theta] = poseAt(index, square);
      if (![x, y, theta].every(Number.isFinite)) { omittedSquares += 1; continue; }
      const ux = Math.cos(theta), uy = Math.sin(theta), vx = -uy, vy = ux;
      const corners = [[1, 1], [-1, 1], [-1, -1], [1, -1]].map(([sx, sy]) => {
        return mapPoint(x + 0.5 * (sx * ux + sy * vx), y + 0.5 * (sx * uy + sy * vy), width, height, sharedScale);
      });
      ctx.beginPath(); ctx.moveTo(corners[0][0], corners[0][1]);
      for (let k = 1; k < corners.length; k += 1) ctx.lineTo(corners[k][0], corners[k][1]);
      ctx.closePath(); ctx.fillStyle = COLORS[square % COLORS.length] + "99"; ctx.fill();
      ctx.strokeStyle = COLORS[square % COLORS.length]; ctx.lineWidth = 1.15; ctx.stroke();
      const center = mapPoint(x, y, width, height, sharedScale);
      if (showOrientation) { ctx.beginPath(); ctx.moveTo(center[0], center[1]); ctx.lineTo(center[0] + 0.35 * sharedScale * ux, center[1] - 0.35 * sharedScale * uy); ctx.strokeStyle = "#f2eee4"; ctx.lineWidth = 1; ctx.stroke(); }
      if (showIds) { ctx.fillStyle = "#f2eee4"; ctx.font = "11px ui-monospace, monospace"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(String(A.square_ids[square]), center[0], center[1]); }
    }
    ctx.fillStyle = "#a5aaa7"; ctx.font = "10px ui-monospace, monospace"; ctx.textAlign = "left"; ctx.textBaseline = "top";
    ctx.fillText(`L = ${validSide ? side.toPrecision(7) : "invalid diagnostic side; boundary omitted"}${isInitial ? " · fixed reference" : ""}`, 9, 8);
    if (omittedSquares) {
      ctx.fillStyle = "#e88475";
      ctx.fillText(`non-finite poses: ${omittedSquares} square(s) omitted`, 9, 23);
    }
  }
  function validationFor(index) {
    return validationRecords.find((item) => {
      const candidate = item.frame ?? item.frame_index;
      const numeric = typeof candidate === "string" && /^\d+$/.test(candidate) ? Number(candidate) : candidate;
      return Number.isInteger(numeric) && numeric === index;
    }) || null;
  }
  function render() {
    const first = dimensions(initialCanvas);
    const current = dimensions(currentCanvas);
    const scale = Math.max(1, Math.min((first.width - 28) / initialSide, (first.height - 28) / initialSide, (current.width - 28) / initialSide, (current.height - 28) / initialSide));
    drawPanel(initialCanvas, 0, true, scale);
    drawPanel(currentCanvas, frame, false, scale);
    const phase = Number(A.phase[frame]);
    const validation = validationFor(frame);
    const isProvisional = phase === 1 || phase === 2 || phase === 4;
    const isRestoredAccepted = phase === 5;
    const phaseLabel = PHASES[phase] || "UNKNOWN";
    const sequence = A.sequence[frame];
    const sequenceText = typeof sequence === "bigint" ? sequence.toString() : String(sequence);
    document.getElementById("frame-status").textContent = `${frame + 1} / ${F} · ${phaseLabel}`;
    document.getElementById("frame-output").textContent = `Frame ${frame + 1} / ${F}`;
    document.getElementById("current-caption").textContent = `${phaseLabel.toLowerCase()} · ${playing ? "playing" : "paused"}`;
    document.getElementById("algorithm-line").textContent = `Algorithm sequence ${sequenceText} · attempt ${String(A.attempt[frame])} · sweep ${String(A.sweep[frame])} within attempt · cumulative sweeps ${String(A.sweep_total[frame])} · phase ${phaseLabel}.`;
    const side = Number(A.side[frame]);
    document.getElementById("side-line").textContent = `Container side L = ${Number.isFinite(side) ? side.toPrecision(9) : "non-finite diagnostic value"}.`;
    const validationValue = validation && validation.validation;
    const validationStatus = validationValue && typeof validationValue === "object" ? validationValue.status : validationValue || (validation && validation.status) || "CHECKED";
    document.getElementById("validation-status").textContent = isProvisional ? "PROVISIONAL · measured diagnostics" : isRestoredAccepted ? "RESTORED ACCEPTED" : (validation ? String(validationStatus) : "NOT CHECKED");
    document.getElementById("validation-detail").textContent = validation ? `${isProvisional ? "Provisional measured diagnostics" : isRestoredAccepted ? "Restored accepted state" : "Validation record"}: ${JSON.stringify(validationValue || validation)}${isProvisional ? " · no accepted/CPU badge is inherited" : ""}` : (isProvisional ? "No accepted/CPU validation badge is inherited by this provisional state." : isRestoredAccepted ? "Rollback restored the previously accepted pose; no new CPU validation record was retained for this frame." : "No per-frame validation record was retained.");
    document.getElementById("validation-status").classList.toggle("provisional", isProvisional);
    if (isProvisional) document.getElementById("provisional-warning").classList.add("visible");
  }
  function setFrame(value) { frame = Math.max(0, Math.min(F - 1, Number(value) || 0)); slider.value = String(frame); render(); }
  function setPlaying(value) { playing = Boolean(value); document.getElementById("play-pause").textContent = playing ? "Pause" : "Play"; if (playing) { lastTick = 0; requestAnimationFrame(tick); } else render(); }
  function tick(now) { if (!playing) return; if (!lastTick) lastTick = now; if (now - lastTick >= 1000 / speed) { lastTick = now; if (frame >= F - 1) { setPlaying(false); return; } setFrame(frame + 1); } requestAnimationFrame(tick); }
  document.getElementById("first-frame").addEventListener("click", () => setFrame(0));
  document.getElementById("previous-frame").addEventListener("click", () => setFrame(frame - 1));
  document.getElementById("next-frame").addEventListener("click", () => setFrame(frame + 1));
  document.getElementById("last-frame").addEventListener("click", () => setFrame(F - 1));
  document.getElementById("play-pause").addEventListener("click", () => setPlaying(!playing));
  slider.addEventListener("input", (event) => setFrame(event.target.value));
  document.getElementById("speed").addEventListener("change", (event) => { speed = Number(event.target.value) || 4; });
  document.getElementById("show-ids").addEventListener("change", (event) => { showIds = event.target.checked; render(); });
  document.getElementById("show-orientation").addEventListener("change", (event) => { showOrientation = event.target.checked; render(); });
  window.addEventListener("resize", render);

  function xml(value) { return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
  function exportCurrentSvg() {
    const width = 900, height = 700, margin = 70, scale = Math.min((width - 2 * margin) / initialSide, (height - 2 * margin) / initialSide);
    const side = Number(A.side[frame]);
    const validSide = Number.isFinite(side) && side > 0;
    const map = (x, y) => [width / 2 + x * scale, height / 2 - y * scale];
    const parts = [`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><title>Asquerix trajectory frame ${frame + 1}</title>`, `<rect width="${width}" height="${height}" fill="#0b1012"/>`];
    if (validSide) parts.push(`<rect x="${width / 2 - side * scale / 2}" y="${height / 2 - side * scale / 2}" width="${side * scale}" height="${side * scale}" fill="none" stroke="#62727a"/>`);
    let omittedSquares = 0;
    for (let square = 0; square < N; square += 1) { const [x, y, theta] = poseAt(frame, square); if (![x, y, theta].every(Number.isFinite)) { omittedSquares += 1; continue; } const ux = Math.cos(theta), uy = Math.sin(theta), vx = -uy, vy = ux; const points = [[1,1],[-1,1],[-1,-1],[1,-1]].map(([sx, sy]) => map(x + .5 * (sx * ux + sy * vx), y + .5 * (sx * uy + sy * vy))).map(([px, py]) => `${px},${py}`).join(" "); parts.push(`<polygon points="${points}" fill="${COLORS[square % COLORS.length]}99" stroke="${COLORS[square % COLORS.length]}"/><text x="${map(x, y)[0]}" y="${map(x, y)[1]}" text-anchor="middle" dominant-baseline="middle" fill="#f2eee4" font-family="monospace" font-size="11">${xml(A.square_ids[square])}</text>`); }
    if (!validSide) parts.push(`<text x="${margin}" y="${height - 48}" fill="#e88475" font-family="monospace" font-size="12">invalid diagnostic side; boundary omitted</text>`);
    if (omittedSquares) parts.push(`<text x="${margin}" y="${height - 30}" fill="#e88475" font-family="monospace" font-size="12">non-finite poses: ${omittedSquares} square(s) omitted</text>`);
    parts.push(`<text x="${margin}" y="30" fill="#e7e5df" font-family="monospace" font-size="14">trial ${xml(DATA.metadata.trial_id)} · frame ${frame + 1}/${F} · ${xml(PHASES[Number(A.phase[frame])] || "UNKNOWN")}</text></svg>`);
    const blob = new Blob([parts.join("")], {type: "image/svg+xml;charset=utf-8"}); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = `trial-${String(DATA.metadata.trial_id)}-frame-${frame + 1}.svg`; link.click(); setTimeout(() => URL.revokeObjectURL(link.href), 0);
  }
  document.getElementById("export-svg").addEventListener("click", exportCurrentSvg);
  render();
})();
</script>
</body>
</html>
"""


def render_html(arrays: Mapping[str, np.ndarray], metadata: Mapping[str, Any]) -> bytes:
    """Return a self-contained HTML viewer for validated trajectory arrays."""

    checked = validate_arrays(arrays, metadata)
    validate_metadata(metadata, frame_count=checked["poses"].shape[0], square_count=checked["poses"].shape[1])
    html = _HTML_TEMPLATE.replace("__PAYLOAD__", _payload(checked, metadata))
    return html.encode("utf-8")


__all__ = ["render_html"]
