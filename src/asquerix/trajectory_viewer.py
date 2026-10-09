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
.panels { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.panel { min-width: 0; border: 1px solid var(--line); background: var(--panel); }
.panel-head { display: flex; flex-wrap: wrap; gap: 6px; align-items: baseline; justify-content: space-between; border-bottom: 1px solid var(--line); padding: 10px 13px 9px; }
.panel-head h2 { margin: 0; font: 600 14px/1.2 Georgia, "Times New Roman", serif; }
.panel-head span { color: var(--muted); font-size: 10px; }
.panel-view-controls { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; min-height: 54px; padding: 6px 12px; border-bottom: 1px solid var(--line); color: var(--muted); font-size: 10px; }
.panel-view-controls button { padding: 4px 7px; }
.panel-view-controls input { width: 72px; }
.canvas-wrap { aspect-ratio: 1.45; min-height: 300px; padding: 13px; background: #10171a; }
canvas { display: block; width: 100%; height: 100%; background: #0b1012; border: 1px solid #2a373c; }
#current-canvas { touch-action: none; cursor: grab; }
#current-canvas.dragging { cursor: grabbing; }
.controls { margin-top: 14px; padding: 13px; border: 1px solid var(--line); background: var(--panel); }
.button-row { display: flex; flex-wrap: wrap; align-items: center; gap: 7px; }
button, select { border: 1px solid #526168; background: var(--panel-2); color: var(--ink); padding: 7px 10px; font: inherit; font-size: 11px; cursor: pointer; }
button:hover, select:hover { border-color: var(--accent); }
button:focus-visible, select:focus-visible, input:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
button.primary { border-color: var(--accent); color: var(--accent); }
input[type="number"] { border: 1px solid #526168; background: var(--panel-2); color: var(--ink); padding: 4px 5px; font: inherit; }
input[type="range"] { width: 100%; margin: 0; accent-color: var(--accent); }
.frame-slider-area { flex: 1 1 230px; min-width: 180px; }
.marker-track { position: relative; height: 24px; margin: 0 8px 4px; }
.marker-band { position: absolute; top: 11px; height: 4px; background: var(--accent-2); opacity: .5; }
.range-marker { position: absolute; top: 0; transform: translateX(-50%); padding: 2px 4px; color: var(--accent-2); border-color: var(--accent-2); font-size: 10px; touch-action: none; cursor: ew-resize; }
.range-controls { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 9px; color: var(--muted); font-size: 11px; }
.range-controls input { width: 65px; }
.range-controls button, .range-controls select { padding: 5px 8px; }
.frame-line { display: flex; align-items: center; gap: 10px; margin-top: 11px; color: var(--muted); font-size: 11px; }
.frame-line output { color: var(--ink); white-space: nowrap; }
.options { display: flex; flex-wrap: wrap; align-items: center; gap: 15px; margin-top: 12px; color: var(--muted); font-size: 11px; }
.legend-title { margin: 14px 0 7px; color: var(--muted); font-size: 11px; }
.square-legend { display: flex; flex-wrap: wrap; gap: 6px; }
.legend-key { display: inline-flex; align-items: center; gap: 6px; padding: 4px 7px; }
.legend-key[aria-pressed="true"] { border-color: var(--square-color); color: var(--square-color); }
.legend-swatch { display: inline-block; width: 10px; height: 10px; background: var(--square-color); }
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

  <section class="panels" aria-label="Trajectory panels">
    <article class="panel">
      <div class="panel-head"><h2>Initial arrangement</h2><span id="initial-caption">frame 1 / fixed reference</span></div>
      <div class="panel-view-controls">Fixed initial scale · current panel zooms independently</div>
      <div class="canvas-wrap"><canvas id="initial-canvas" aria-label="Initial arrangement"></canvas></div>
    </article>
    <article class="panel">
      <div class="panel-head"><h2>Current recorded frame</h2><span id="current-caption">paused at start</span></div>
      <div class="panel-view-controls">
        <button type="button" id="zoom-out" aria-label="Zoom current panel out">−</button>
        <label>Zoom × <input id="current-zoom" type="number" min="0.25" max="65536" step="any" value="1" aria-label="Current panel zoom"></label>
        <button type="button" id="zoom-in" aria-label="Zoom current panel in">+</button>
        <button type="button" id="fit-current">Fit container</button>
        <button type="button" id="fit-trajectory">Fit full trajectory</button>
        <button type="button" id="focus-trail">Focus selected ID</button>
        <button type="button" id="reset-view">Reset view</button>
        <span>Wheel to zoom · drag to pan</span>
      </div>
      <div class="canvas-wrap"><canvas id="current-canvas" aria-label="Current recorded frame" title="Wheel to zoom at the pointer; drag to pan. Enter a zoom up to ×65536 to inspect micromovements."></canvas></div>
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
    <div class="frame-line"><div class="frame-slider-area"><div class="marker-track" id="marker-track"><div id="marker-band" class="marker-band"></div><button id="start-marker" class="range-marker" type="button" aria-label="Drag start marker A">A</button><button id="end-marker" class="range-marker" type="button" aria-label="Drag end marker B">B</button></div><input id="frame-slider" type="range" min="0" value="0" step="1" aria-label="Recorded frame"></div><output id="frame-output">Frame 1 / 1</output></div>
    <div class="range-controls">
      <label>A: <input id="range-start" type="number" min="0" step="1" value="0" aria-label="Start frame index"></label>
      <button type="button" id="set-range-start">Set A here</button>
      <label>B: <input id="range-end" type="number" min="0" step="1" value="0" aria-label="End frame index"></label>
      <button type="button" id="set-range-end">Set B here</button>
      <select id="playback-mode" aria-label="Playback mode"><option value="once">Play range once</option><option value="loop">Loop range</option></select>
      <button type="button" id="reset-range">Full range</button>
      <span>Drag A/B markers or set them here · frame indices start at 0</span>
    </div>
    <div class="options">
      <label><input id="show-squares" type="checkbox" checked> show squares</label>
      <label><input id="show-container" type="checkbox" checked> show container boundary</label>
      <label><input id="show-ids" type="checkbox" checked> show square IDs</label>
      <label><input id="show-orientation" type="checkbox" checked> show orientation marks</label>
      <label><input id="show-trails" type="checkbox" checked> show center trails</label>
      <select id="trail-square" aria-label="Center trail square"><option value="all">all square trails</option></select>
      <label><input id="only-selected-trail" type="checkbox"> only selected trail</label>
      <label>Trail frames <input id="trail-history" type="number" min="0" max="4096" step="1" value="0" aria-label="Center trail history length" style="width:65px"> (0 = full history)</label>
      <span>Playback visits saved frames only; no interpolation.</span>
    </div>
    <p class="legend-title">Square colors · click an ID to inspect its center trail</p>
    <div id="square-legend" class="square-legend" aria-label="Square color legend"></div>
  </section>

  <section class="details">
    <div class="detail-box"><h3>Recorded state</h3><p id="algorithm-line">—</p><p id="side-line">—</p><p id="trail-detail">Center trails connect recorded centers up to the current frame. Dots mark saved positions; connecting lines do not reconstruct skipped states or intermediate motion.</p><p id="validation-detail">—</p></div>
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
  const COLORS = ["#e2b35c", "#78d6c3", "#d88978", "#a5c66f", "#b49be5", "#e1a1c9", "#77b5de", "#e5d08a", "#eb8650", "#58c9e2", "#e66fad", "#78a9ef", "#d6e761", "#bf9472", "#95d4ef", "#c6a8d2", "#6eb894", "#efb8a2", "#99a7cc", "#d4cbbc", "#e6cc58", "#9ee0d8", "#df776d", "#96b768", "#d28eed", "#efaddb", "#5c9ac2", "#cebf75", "#c887a0", "#a4c8ad", "#8fbcea", "#c5d094"];
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
  const strategy = DATA.metadata.strategy || null;
  let strategyPanel = null;
  let strategyRows = [];
  if (strategy) {
    strategyPanel = document.createElement("section");
    strategyPanel.className = "panel";
    strategyPanel.style.margin = "16px 0";
    strategyPanel.innerHTML = '<div class="panel-head"><h2>World strategy</h2><span id="strategy-position"></span></div><div style="display:grid;grid-template-columns:minmax(220px,1fr) 2fr;gap:16px;padding:14px"><ol id="strategy-code" style="max-height:190px;overflow:auto;margin:0;padding-left:32px"></ol><div><canvas id="strategy-graph" style="width:100%;height:105px" aria-label="Current and protected best side against consumed work"></canvas><p id="strategy-state"></p><p id="strategy-selection"></p><button id="go-best" type="button">Go to best state</button> <button id="go-final-current" type="button">Go to final current</button></div></div>';
    document.querySelector(".panels").before(strategyPanel);
    strategyRows = strategy.program.instructions.map(instruction => {
      const row = document.createElement("li");
      row.textContent = `${instruction.pc}: ${instruction.op} · ${instruction.source_node}`;
      row.title = `Operands: ${JSON.stringify(instruction.words.slice(1))}. Exact FP32 words: ${instruction.fp32_bits.join(" ")}`;
      row.style.padding = "4px";
      document.getElementById("strategy-code").append(row);
      return row;
    });
  }
  let frame = 0;
  let playing = false;
  let lastTick = 0;
  let speed = 4;
  let showSquares = true;
  let showContainer = true;
  let showIds = true;
  let showOrientation = true;
  let showTrails = true;
  let trailSquare = "all";
  let onlySelectedTrail = false;
  let trailHistory = 0;
  let currentZoom = 1;
  let currentCenter = [0, 0];
  let baseScale = 1;
  let rangeStart = 0;
  let rangeEnd = F - 1;
  let loopRange = false;
  let playbackGeneration = 0;
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
  const trailSelect = document.getElementById("trail-square");
  const legend = document.getElementById("square-legend");
  const legendKeys = [];
  for (let square = 0; square < N; square += 1) {
    const option = document.createElement("option");
    option.value = String(square); option.textContent = `focus square ${String(A.square_ids[square])}`;
    trailSelect.appendChild(option);
    const key = document.createElement("button"), swatch = document.createElement("span"), label = document.createElement("span");
    key.type = "button"; key.className = "legend-key"; key.dataset.squareIndex = String(square);
    key.style.setProperty("--square-color", COLORS[square]);
    key.setAttribute("aria-label", `Show center trail for square ${String(A.square_ids[square])}`);
    swatch.className = "legend-swatch"; swatch.setAttribute("aria-hidden", "true"); label.textContent = String(A.square_ids[square]);
    key.append(swatch, label); legend.appendChild(key); legendKeys.push(key);
    key.addEventListener("click", () => selectSquare(square));
  }
  slider.max = String(Math.max(0, F - 1));
  document.getElementById("range-start").max = String(F - 1);
  document.getElementById("range-end").max = String(F - 1);
  document.getElementById("trial-line").textContent = `Trial ${String(DATA.metadata.trial_id)} · ${N} unit squares · seed ${String(DATA.metadata.seed)}`;
  document.getElementById("initial-caption").textContent = `L = ${Number.isFinite(initialSideValue) && initialSideValue > 0 ? initialSideValue.toPrecision(7) : "invalid diagnostic value"} · frame 1 / fixed reference`;
  document.getElementById("comparison-status").textContent = String(endpoint.status || "REFERENCE_INCOMPLETE");
  document.getElementById("termination-status").textContent = String(DATA.metadata.termination_reason || "UNKNOWN");
  document.getElementById("sampling-detail").textContent = `Sampling: ${String(retainedCount)} retained / ${String(observedCount)} observed; ${String(suppressedCount)} suppressed; effective stride ${String(effectiveStride)}; cap ${String(frameCap)}.`;
  document.getElementById("comparison-detail").textContent = `This is a newly recorded replay. Endpoint/result comparison scope: ${String(endpoint.scope || "defined saved endpoint fields")} — intermediate states are not proven identical.`;
  const replayRevision = replayProvenance.source_revision || replayProvenance.revision || provenance.replay_revision || provenance.source_revision || "unrecorded";
  const replayDevice = replayProvenance.device_uuid || replayProvenance.device_name || replayProvenance.gpu_uuid || replayProvenance.gpu_model || provenance.replay_gpu_uuid || "unrecorded";
  const provenanceStatus = provenance.status || endpoint.provenance_status || "unrecorded";
  document.getElementById("provenance-detail").textContent = `Provenance: ${String(provenanceStatus)} · replay revision ${String(replayRevision)} · replay device ${String(replayDevice)} · original revision ${String(originalProvenance.source_revision || originalProvenance.revision || "unrecorded")}.`;

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
  function mapPoint(x, y, width, height, scale, center = [0, 0]) { return [width / 2 + (x - center[0]) * scale, height / 2 - (y - center[1]) * scale]; }
  function poseAt(index, square) {
    const offset = (index * N + square) * 3;
    return [Number(A.poses[offset]), Number(A.poses[offset + 1]), Number(A.poses[offset + 2])];
  }
  function trailSegments(index, square) {
    const segments = []; let segment = [];
    for (let saved = trailStart(index); saved <= index; saved += 1) {
      const [x, y] = poseAt(saved, square);
      if (Number.isFinite(x) && Number.isFinite(y)) segment.push([x, y]);
      else if (segment.length) { segments.push(segment); segment = []; }
    }
    if (segment.length) segments.push(segment);
    return segments;
  }
  function trailStart(index) { return trailHistory > 0 ? Math.max(0, index - trailHistory + 1) : 0; }
  function trailSquares() {
    return onlySelectedTrail && trailSquare !== "all" ? [Number(trailSquare)] : Array.from({length: N}, (_, square) => square);
  }
  function trailStyle(square) { return trailSquare === "all" ? [0.65, 1.25] : trailSquare === String(square) ? [0.95, 2] : [0.12, 1]; }
  function selectSquare(square) {
    trailSquare = square === null ? "all" : String(square); trailSelect.value = trailSquare;
    showTrails = true; document.getElementById("show-trails").checked = true; trailSelect.disabled = false; render();
  }
  function drawTrails(ctx, index, width, height, scale, center) {
    ctx.save(); ctx.lineJoin = "round";
    for (const square of trailSquares()) {
      [ctx.globalAlpha, ctx.lineWidth] = trailStyle(square);
      ctx.strokeStyle = COLORS[square % COLORS.length]; ctx.fillStyle = ctx.strokeStyle;
      for (const segment of trailSegments(index, square)) {
        const points = segment.map(([x, y]) => mapPoint(x, y, width, height, scale, center));
        ctx.beginPath(); ctx.moveTo(points[0][0], points[0][1]);
        for (let saved = 1; saved < points.length; saved += 1) ctx.lineTo(points[saved][0], points[saved][1]);
        ctx.stroke();
        for (const [x, y] of points) { ctx.beginPath(); ctx.arc(x, y, 1.5, 0, 2 * Math.PI); ctx.fill(); }
      }
      const [startX, startY] = poseAt(trailStart(index), square);
      if (Number.isFinite(startX) && Number.isFinite(startY)) {
        const [x, y] = mapPoint(startX, startY, width, height, scale, center);
        ctx.beginPath(); ctx.arc(x, y, 3.5, 0, 2 * Math.PI); ctx.stroke();
      }
    }
    ctx.restore();
  }
  function labelLayout(ctx, square) {
    const text = String(A.square_ids[square]);
    ctx.font = "11px ui-monospace, monospace";
    return {text, halfWidth: ctx.measureText(text).width / 2 + 3, halfHeight: 8};
  }
  function orientationPoints(center, theta, scale, label) {
    const dx = Math.cos(theta), dy = -Math.sin(theta);
    const clearance = showIds ? Math.min(label.halfWidth / Math.max(Math.abs(dx), 1e-12), label.halfHeight / Math.max(Math.abs(dy), 1e-12)) + 3 : 0;
    const start = Math.max(0.28 * scale, clearance), end = 0.44 * scale;
    if (start >= end) return null;
    return [[center[0] + start * dx, center[1] + start * dy], [center[0] + end * dx, center[1] + end * dy]];
  }
  function drawPanel(canvas, index, isInitial, sharedScale, viewCenter = [0, 0]) {
    const {ctx, width, height} = dimensions(canvas);
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#0b1012"; ctx.fillRect(0, 0, width, height);
    const side = Number(A.side[index]);
    const validSide = Number.isFinite(side) && side > 0;
    if (showContainer && validSide) {
      const [left, top] = mapPoint(-side / 2, side / 2, width, height, sharedScale, viewCenter);
      ctx.strokeStyle = "#62727a"; ctx.lineWidth = 1.4; ctx.strokeRect(left, top, side * sharedScale, side * sharedScale);
    }
    let omittedSquares = 0;
    for (let square = 0; square < N; square += 1) {
      const [x, y, theta] = poseAt(index, square);
      if (![x, y, theta].every(Number.isFinite)) { omittedSquares += 1; continue; }
      if (!showSquares) continue;
      const ux = Math.cos(theta), uy = Math.sin(theta), vx = -uy, vy = ux;
      const corners = [[1, 1], [-1, 1], [-1, -1], [1, -1]].map(([sx, sy]) => {
        return mapPoint(x + 0.5 * (sx * ux + sy * vx), y + 0.5 * (sx * uy + sy * vy), width, height, sharedScale, viewCenter);
      });
      ctx.beginPath(); ctx.moveTo(corners[0][0], corners[0][1]);
      for (let k = 1; k < corners.length; k += 1) ctx.lineTo(corners[k][0], corners[k][1]);
      ctx.closePath(); ctx.fillStyle = COLORS[square % COLORS.length] + "99"; ctx.fill();
      const selected = strategy && !isInitial && (BigInt(strategy.frames[index].mask) & (1n << BigInt(square))) !== 0n;
      ctx.strokeStyle = selected ? "#ffffff" : COLORS[square % COLORS.length]; ctx.lineWidth = selected ? 2.8 : 1.15; ctx.stroke();
    }
    if (showTrails && !isInitial) drawTrails(ctx, index, width, height, sharedScale, viewCenter);
    for (let square = 0; square < N; square += 1) {
      const [x, y, theta] = poseAt(index, square);
      if (![x, y, theta].every(Number.isFinite)) continue;
      const center = mapPoint(x, y, width, height, sharedScale, viewCenter);
      const label = labelLayout(ctx, square);
      const marker = orientationPoints(center, theta, sharedScale, label);
      if (showOrientation && marker) { ctx.beginPath(); ctx.moveTo(...marker[0]); ctx.lineTo(...marker[1]); ctx.strokeStyle = "#f2eee4"; ctx.lineWidth = 1.5; ctx.stroke(); }
      if (showIds) {
        ctx.fillStyle = "#0b1012"; ctx.fillRect(center[0] - label.halfWidth, center[1] - label.halfHeight, 2 * label.halfWidth, 2 * label.halfHeight);
        ctx.fillStyle = "#f2eee4"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(label.text, center[0], center[1]);
      }
    }
    ctx.fillStyle = "#a5aaa7"; ctx.font = "10px ui-monospace, monospace"; ctx.textAlign = "left"; ctx.textBaseline = "top";
    if (omittedSquares) {
      ctx.fillStyle = "#e88475";
      ctx.fillText(`non-finite poses: ${omittedSquares} square(s) omitted`, 9, 8);
    }
  }
  function validationFor(index) {
    return validationRecords.find((item) => {
      const candidate = item.frame ?? item.frame_index;
      const numeric = typeof candidate === "string" && /^\d+$/.test(candidate) ? Number(candidate) : candidate;
      return Number.isInteger(numeric) && numeric === index;
    }) || null;
  }
  function validationDetails(record, provisional, restored) {
    const values = record.validation && typeof record.validation === "object" ? record.validation : record;
    const outcomes = {NUMERICALLY_VALIDATED: "constraints passed", INVALID: "constraint violation detected", INDETERMINATE: "result indeterminate within numerical tolerance"};
    const parts = [provisional ? "Provisional geometry measurements" : `${restored ? "Restored accepted state" : "Independent numerical check"}: ${outcomes[values.status || record.status] || "checked"}`];
    for (const [field, label] of [["max_penetration", "Maximum overlap depth"], ["min_pair_separation", "Minimum square separation"], ["min_wall_clearance", "Minimum wall clearance"], ["tolerance", "Check tolerance"]]) {
      const value = values[field];
      if (typeof value === "number" && Number.isFinite(value)) parts.push(`${label}: ${value === 0 ? "0" : value.toPrecision(5)} unit lengths`);
    }
    if (values.nonfinite) parts.push("Non-finite coordinates detected");
    if (provisional) parts.push("These measurements do not mark the state as accepted");
    return parts.join(" · ") + ".";
  }
  function render() {
    const first = dimensions(initialCanvas);
    const current = dimensions(currentCanvas);
    const scale = Math.max(1, Math.min((first.width - 28) / initialSide, (first.height - 28) / initialSide, (current.width - 28) / initialSide, (current.height - 28) / initialSide));
    baseScale = scale;
    drawPanel(initialCanvas, 0, true, scale);
    drawPanel(currentCanvas, frame, false, scale * currentZoom, currentCenter);
    document.getElementById("current-zoom").value = String(Number(currentZoom.toPrecision(7)));
    document.getElementById("only-selected-trail").disabled = trailSquare === "all";
    document.getElementById("trail-detail").textContent = `Center trails: ${trailHistory ? `last ${trailHistory} saved frames` : "full history"}, from index ${trailStart(frame)} through ${frame}. Dots mark recorded centers, not physical speed; connecting lines do not reconstruct skipped motion.`;
    updateMarkers();
    const phase = Number(A.phase[frame]);
    const validation = validationFor(frame);
    const isProvisional = phase === 1 || phase === 2 || phase === 4;
    const isRestoredAccepted = phase === 5;
    const phaseLabel = PHASES[phase] || "UNKNOWN";
    const sequence = A.sequence[frame];
    const sequenceText = typeof sequence === "bigint" ? sequence.toString() : String(sequence);
    document.getElementById("frame-status").textContent = `${frame + 1} / ${F} · ${phaseLabel}`;
    document.getElementById("frame-output").textContent = `Frame ${frame + 1} / ${F}`;
    document.getElementById("algorithm-line").textContent = `Algorithm sequence ${sequenceText} · attempt ${String(A.attempt[frame])} · sweep ${String(A.sweep[frame])} within attempt · cumulative sweeps ${String(A.sweep_total[frame])} · phase ${phaseLabel}.`;
    const side = Number(A.side[frame]);
    document.getElementById("current-caption").textContent = `L = ${Number.isFinite(side) && side > 0 ? side.toPrecision(7) : "invalid diagnostic value"} · ${phaseLabel.toLowerCase()} · ${playing ? "playing" : "paused"}`;
    legendKeys.forEach((key, square) => key.setAttribute("aria-pressed", String(showTrails && trailSquare === String(square))));
    document.getElementById("side-line").textContent = `Container side L = ${Number.isFinite(side) ? side.toPrecision(9) : "non-finite diagnostic value"}.`;
    const validationValue = validation && validation.validation;
    const validationStatus = validationValue && typeof validationValue === "object" ? validationValue.status : validationValue || (validation && validation.status) || "CHECKED";
    const validationLabels = {NUMERICALLY_VALIDATED: "Numerically validated", INVALID: "Constraint violation", INDETERMINATE: "Numerically indeterminate", CHECKED: "Checked"};
    document.getElementById("validation-status").textContent = isProvisional ? "PROVISIONAL · measured diagnostics" : isRestoredAccepted ? "RESTORED ACCEPTED" : (validation ? validationLabels[validationStatus] || "Check available" : "NOT CHECKED");
    document.getElementById("validation-detail").textContent = validation ? validationDetails(validation, isProvisional, isRestoredAccepted) : (isProvisional ? "No accepted/CPU validation badge is inherited by this provisional state." : isRestoredAccepted ? "Rollback restored the previously accepted pose; no new CPU validation record was retained for this frame." : "No per-frame validation record was retained.");
    document.getElementById("validation-status").classList.toggle("provisional", isProvisional);
    if (strategy) renderStrategy();
  }
  function renderStrategy() {
    const item = strategy.frames[frame];
    const instruction = strategy.program.instructions[item.pc];
    strategyRows.forEach((row, pc) => {
      row.style.background = pc === item.pc ? "#30454d" : "transparent";
      row.setAttribute("aria-current", String(pc === item.pc));
    });
    document.getElementById("strategy-position").textContent = instruction ? `${instruction.op} · ${instruction.source_node}` : "Initial protected state";
    const labels = [[1,"proposal"],[2,"repair"],[4,"commit"],[8,"rejection"],[16,"rollback"],[32,"best snapshot"],[64,"discontinuous restore"],[128,"finalization"],[256,"invocation"]];
    const markers = labels.filter(([flag]) => item.flags & flag).map(([,label]) => label).join(" · ");
    document.getElementById("strategy-state").textContent = `Current L ${Number(item.side).toPrecision(8)} · protected best L ${Number(item.best_side).toPrecision(8)} · body work ${item.work} · ${item.outcome_name} · ${markers}`;
    const ids = Array.from({length:N}, (_,square) => square).filter(square => (BigInt(item.mask) & (1n << BigInt(square))) !== 0n);
    document.getElementById("strategy-selection").textContent = `Selected square IDs: ${ids.length ? ids.join(", ") : "none"}. Attempt ${item.attempt}, sweep ${item.sweep}; operator RNG draws ${item.rng_draws}. Fractions multiply the side at operation entry; squares retain unit side.`;
    const graph = document.getElementById("strategy-graph"), ctx = graph.getContext("2d");
    graph.width = Math.max(300, graph.clientWidth * devicePixelRatio); graph.height = 105 * devicePixelRatio;
    const width = graph.width, height = graph.height, margin = 14 * devicePixelRatio;
    const maxWork = Math.max(1, ...strategy.frames.map(value => Number(value.work)));
    const minSide = Math.min(...strategy.frames.flatMap(value => [value.side, value.best_side]));
    const maxSide = Math.max(...strategy.frames.flatMap(value => [value.side, value.best_side]));
    const x = value => margin + Number(value.work) / maxWork * (width - 2 * margin);
    const y = value => margin + (maxSide - value) / Math.max(1e-8, maxSide - minSide) * (height - 2 * margin);
    ctx.clearRect(0, 0, width, height);
    for (const [key, color] of [["side","#e2b35c"],["best_side","#78d6c3"]]) {
      ctx.beginPath(); ctx.strokeStyle = color; ctx.lineWidth = 1.5 * devicePixelRatio;
      strategy.frames.forEach((value, index) => {
        if (index === 0 || (key === "side" && value.flags & (16 | 64))) ctx.moveTo(x(value), y(value[key]));
        else ctx.lineTo(x(value), y(value[key]));
      });
      ctx.stroke();
    }
    ctx.strokeStyle = "#ffffff"; ctx.beginPath(); ctx.moveTo(x(item), margin); ctx.lineTo(x(item), height - margin); ctx.stroke();
    graph.title = `Current L ${item.side}; best L ${item.best_side}; body work ${item.work}. Amber: current; teal: protected best. Click to seek by work.`;
  }
  function setFrame(value) { frame = Math.max(0, Math.min(F - 1, Number(value) || 0)); slider.value = String(frame); render(); }
  function seekFrame(value) { if (playing) setPlaying(false); setFrame(value); }
  function setPlaying(value) {
    playing = Boolean(value); playbackGeneration += 1;
    document.getElementById("play-pause").textContent = playing ? "Pause" : "Play";
    if (playing) { if (frame < rangeStart || frame >= rangeEnd) setFrame(rangeStart); lastTick = 0; const generation = playbackGeneration; requestAnimationFrame(now => tick(now, generation)); }
    render();
  }
  function tick(now, generation) {
    if (!playing || generation !== playbackGeneration) return;
    if (!lastTick) lastTick = now;
    if (now - lastTick >= 1000 / speed) {
      lastTick = now;
      if (frame >= rangeEnd) { if (loopRange) setFrame(rangeStart); else { setPlaying(false); return; } }
      else setFrame(frame + 1);
    }
    requestAnimationFrame(next => tick(next, generation));
  }
  function updateMarkers() {
    document.getElementById("range-start").value = String(rangeStart); document.getElementById("range-end").value = String(rangeEnd);
    const start = 100 * rangeStart / Math.max(1, F - 1), end = 100 * rangeEnd / Math.max(1, F - 1);
    document.getElementById("start-marker").style.left = `${start}%`; document.getElementById("end-marker").style.left = `${end}%`;
    document.getElementById("marker-band").style.left = `${start}%`; document.getElementById("marker-band").style.width = `${end - start}%`;
  }
  function setMarker(which, value) {
    if (playing) setPlaying(false);
    const index = Math.max(0, Math.min(F - 1, Math.round(Number(value) || 0)));
    if (which === "start") { rangeStart = index; if (rangeEnd < index) rangeEnd = index; }
    else { rangeEnd = index; if (rangeStart > index) rangeStart = index; }
    updateMarkers();
  }
  function clampZoom(value) { return Math.max(0.25, Math.min(65536, Number(value) || 1)); }
  function zoomTo(value, point = null) {
    const {width, height} = dimensions(currentCanvas), next = clampZoom(value);
    if (point) {
      const dx = point[0] - width / 2, dy = point[1] - height / 2;
      currentCenter = [currentCenter[0] + dx / (baseScale * currentZoom) - dx / (baseScale * next), currentCenter[1] - dy / (baseScale * currentZoom) + dy / (baseScale * next)];
    }
    currentZoom = next; render();
  }
  function fitTrajectory() {
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    const include = (x, y) => { if (Number.isFinite(x) && Number.isFinite(y)) { minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y); } };
    for (let saved = 0; saved < F; saved += 1) {
      const side = Number(A.side[saved]);
      if (showContainer && Number.isFinite(side) && side > 0) { include(-side / 2, -side / 2); include(side / 2, side / 2); }
      for (const square of (showSquares ? Array.from({length: N}, (_, index) => index) : trailSquares())) {
        const [x, y, theta] = poseAt(saved, square); include(x, y);
        if (showSquares && Number.isFinite(theta)) {
          const extent = 0.5 * (Math.abs(Math.cos(theta)) + Math.abs(Math.sin(theta)));
          include(x - extent, y - extent); include(x + extent, y + extent);
        }
      }
    }
    if (!Number.isFinite(minX)) return;
    const {width, height} = dimensions(currentCanvas);
    currentCenter = [minX + (maxX - minX) / 2, minY + (maxY - minY) / 2];
    zoomTo(Math.min((width - 28) / Math.max(1e-6, maxX - minX), (height - 28) / Math.max(1e-6, maxY - minY)) / baseScale);
  }
  function selectAt(point) {
    const {width, height} = dimensions(currentCanvas), scale = baseScale * currentZoom;
    const worldX = currentCenter[0] + (point[0] - width / 2) / scale, worldY = currentCenter[1] - (point[1] - height / 2) / scale;
    for (let square = N - 1; square >= 0; square -= 1) {
      const [x, y, theta] = poseAt(frame, square); if (![x, y, theta].every(Number.isFinite)) continue;
      const dx = worldX - x, dy = worldY - y;
      if (showSquares ? Math.abs(dx * Math.cos(theta) + dy * Math.sin(theta)) <= 0.5 && Math.abs(-dx * Math.sin(theta) + dy * Math.cos(theta)) <= 0.5 : showIds && Math.hypot(dx, dy) * scale <= 12) { selectSquare(square); return; }
    }
    selectSquare(null);
  }
  document.getElementById("zoom-in").addEventListener("click", () => zoomTo(currentZoom * 2));
  document.getElementById("zoom-out").addEventListener("click", () => zoomTo(currentZoom / 2));
  document.getElementById("current-zoom").addEventListener("change", event => zoomTo(event.target.value));
  document.getElementById("reset-view").addEventListener("click", () => { currentCenter = [0, 0]; zoomTo(1); });
  document.getElementById("fit-current").addEventListener("click", () => { const side = Number(A.side[frame]); if (Number.isFinite(side) && side > 0) { currentCenter = [0, 0]; zoomTo(initialSide / side); } });
  document.getElementById("fit-trajectory").addEventListener("click", fitTrajectory);
  document.getElementById("focus-trail").addEventListener("click", () => { if (trailSquare !== "all") { const [x, y] = poseAt(frame, Number(trailSquare)); if (Number.isFinite(x) && Number.isFinite(y)) { currentCenter = [x, y]; render(); } } });
  currentCanvas.addEventListener("wheel", event => { event.preventDefault(); const rect = currentCanvas.getBoundingClientRect(); zoomTo(currentZoom * Math.exp(-event.deltaY * 0.002), [event.clientX - rect.left, event.clientY - rect.top]); }, {passive: false});
  let sceneDrag = null;
  currentCanvas.addEventListener("pointerdown", event => { if (event.button !== 0) return; sceneDrag = {x: event.clientX, y: event.clientY, center: [...currentCenter], moved: false}; currentCanvas.setPointerCapture(event.pointerId); });
  currentCanvas.addEventListener("pointermove", event => {
    if (!sceneDrag) return;
    const dx = event.clientX - sceneDrag.x, dy = event.clientY - sceneDrag.y;
    if (Math.hypot(dx, dy) > 3) sceneDrag.moved = true;
    if (sceneDrag.moved) { const scale = baseScale * currentZoom; currentCenter = [sceneDrag.center[0] - dx / scale, sceneDrag.center[1] + dy / scale]; currentCanvas.classList.add("dragging"); render(); }
  });
  currentCanvas.addEventListener("pointerup", event => { if (sceneDrag && !sceneDrag.moved) { const rect = currentCanvas.getBoundingClientRect(); selectAt([event.clientX - rect.left, event.clientY - rect.top]); } sceneDrag = null; currentCanvas.classList.remove("dragging"); });
  currentCanvas.addEventListener("pointercancel", () => { sceneDrag = null; currentCanvas.classList.remove("dragging"); });
  for (const which of ["start", "end"]) {
    document.getElementById(`range-${which}`).addEventListener("change", event => setMarker(which, event.target.value));
    document.getElementById(`set-range-${which}`).addEventListener("click", () => setMarker(which, frame));
    const marker = document.getElementById(`${which}-marker`); let dragging = false;
    marker.addEventListener("pointerdown", event => { if (event.button !== 0) return; dragging = true; event.preventDefault(); marker.setPointerCapture(event.pointerId); });
    marker.addEventListener("pointermove", event => { if (!dragging) return; const rect = document.getElementById("marker-track").getBoundingClientRect(); setMarker(which, (event.clientX - rect.left) / rect.width * (F - 1)); });
    marker.addEventListener("pointerup", () => { dragging = false; }); marker.addEventListener("pointercancel", () => { dragging = false; });
  }
  document.getElementById("playback-mode").addEventListener("change", event => { loopRange = event.target.value === "loop"; });
  document.getElementById("reset-range").addEventListener("click", () => { if (playing) setPlaying(false); rangeStart = 0; rangeEnd = F - 1; updateMarkers(); });
  document.getElementById("first-frame").addEventListener("click", () => seekFrame(0));
  document.getElementById("previous-frame").addEventListener("click", () => seekFrame(frame - 1));
  document.getElementById("next-frame").addEventListener("click", () => seekFrame(frame + 1));
  document.getElementById("last-frame").addEventListener("click", () => seekFrame(F - 1));
  document.getElementById("play-pause").addEventListener("click", () => setPlaying(!playing));
  slider.addEventListener("input", (event) => seekFrame(event.target.value));
  document.getElementById("speed").addEventListener("change", (event) => { speed = Number(event.target.value) || 4; });
  document.getElementById("show-squares").addEventListener("change", (event) => { showSquares = event.target.checked; render(); });
  document.getElementById("show-container").addEventListener("change", (event) => { showContainer = event.target.checked; render(); });
  document.getElementById("show-ids").addEventListener("change", (event) => { showIds = event.target.checked; render(); });
  document.getElementById("show-orientation").addEventListener("change", (event) => { showOrientation = event.target.checked; render(); });
  document.getElementById("show-trails").addEventListener("change", (event) => { showTrails = event.target.checked; trailSelect.disabled = !showTrails; render(); });
  trailSelect.addEventListener("change", (event) => { trailSquare = event.target.value; render(); });
  document.getElementById("only-selected-trail").addEventListener("change", event => { onlySelectedTrail = event.target.checked; render(); });
  document.getElementById("trail-history").addEventListener("change", event => { trailHistory = Math.max(0, Math.min(4096, Math.round(Number(event.target.value) || 0))); event.target.value = String(trailHistory); render(); });
  window.addEventListener("resize", render);

  function xml(value) { return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
  function exportCurrentSvg() {
    const width = 900, height = 700, margin = 70, scale = Math.min((width - 2 * margin) / initialSide, (height - 2 * margin) / initialSide) * currentZoom;
    const side = Number(A.side[frame]);
    const validSide = Number.isFinite(side) && side > 0;
    const map = (x, y) => mapPoint(x, y, width, height, scale, currentCenter);
    const parts = [`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" data-zoom="${currentZoom}" data-view-x="${currentCenter[0]}" data-view-y="${currentCenter[1]}" data-trail-start="${trailStart(frame)}"><title>Asquerix trajectory frame ${frame + 1}</title>`, `<rect width="${width}" height="${height}" fill="#0b1012"/>`];
    if (showContainer && validSide) { const [left, top] = map(-side / 2, side / 2); parts.push(`<rect data-container-boundary="true" x="${left}" y="${top}" width="${side * scale}" height="${side * scale}" fill="none" stroke="#62727a"/>`); }
    let omittedSquares = 0;
    for (let square = 0; square < N; square += 1) { const [x, y, theta] = poseAt(frame, square); if (![x, y, theta].every(Number.isFinite)) { omittedSquares += 1; continue; } if (!showSquares) continue; const ux = Math.cos(theta), uy = Math.sin(theta), vx = -uy, vy = ux; const points = [[1,1],[-1,1],[-1,-1],[1,-1]].map(([sx, sy]) => map(x + .5 * (sx * ux + sy * vx), y + .5 * (sx * uy + sy * vy))).map(([px, py]) => `${px},${py}`).join(" "); parts.push(`<polygon points="${points}" fill="${COLORS[square % COLORS.length]}99" stroke="${COLORS[square % COLORS.length]}"/>`); }
    if (showTrails) {
      for (const square of trailSquares()) {
        const color = COLORS[square % COLORS.length];
        const [opacity, lineWidth] = trailStyle(square);
        parts.push(`<g data-center-trail="${xml(A.square_ids[square])}" fill="${color}" stroke="${color}" opacity="${opacity}" stroke-width="${lineWidth}">`);
        for (const segment of trailSegments(frame, square)) {
          const points = segment.map(([x, y]) => map(x, y));
          parts.push(`<polyline points="${points.map(([x, y]) => `${x},${y}`).join(" ")}" fill="none" stroke-linejoin="round"/>`);
          for (const [x, y] of points) parts.push(`<circle cx="${x}" cy="${y}" r="1.5" stroke="none"/>`);
        }
        const [startX, startY] = poseAt(trailStart(frame), square);
        if (Number.isFinite(startX) && Number.isFinite(startY)) { const [x, y] = map(startX, startY); parts.push(`<circle cx="${x}" cy="${y}" r="3.5" fill="none"/>`); }
        parts.push("</g>");
      }
    }
    const measureContext = currentCanvas.getContext("2d");
    for (let square = 0; square < N; square += 1) {
      const [x, y, theta] = poseAt(frame, square);
      if (![x, y, theta].every(Number.isFinite)) continue;
      const center = map(x, y), label = labelLayout(measureContext, square);
      const marker = orientationPoints(center, theta, scale, label);
      if (showOrientation && marker) parts.push(`<line data-orientation="${xml(A.square_ids[square])}" x1="${marker[0][0]}" y1="${marker[0][1]}" x2="${marker[1][0]}" y2="${marker[1][1]}" stroke="#f2eee4" stroke-width="1.5"/>`);
      if (showIds) parts.push(`<rect data-label="${xml(A.square_ids[square])}" x="${center[0] - label.halfWidth}" y="${center[1] - label.halfHeight}" width="${2 * label.halfWidth}" height="${2 * label.halfHeight}" fill="#0b1012"/><text x="${center[0]}" y="${center[1]}" text-anchor="middle" dominant-baseline="middle" fill="#f2eee4" font-family="ui-monospace, monospace" font-size="11">${xml(label.text)}</text>`);
    }
    if (showTrails) parts.push(`<text x="${margin}" y="${height - 12}" fill="#a5aaa7" font-family="monospace" font-size="11">Center trails connect saved positions through frame ${frame + 1}; skipped motion is not reconstructed.</text>`);
    if (!validSide) parts.push(`<text x="${margin}" y="${height - 48}" fill="#e88475" font-family="monospace" font-size="12">invalid diagnostic side; boundary omitted</text>`);
    if (omittedSquares) parts.push(`<text x="${margin}" y="${height - 30}" fill="#e88475" font-family="monospace" font-size="12">non-finite poses: ${omittedSquares} square(s) omitted</text>`);
    parts.push(`<text x="${margin}" y="30" fill="#e7e5df" font-family="monospace" font-size="14">trial ${xml(DATA.metadata.trial_id)} · frame ${frame + 1}/${F} · ${xml(PHASES[Number(A.phase[frame])] || "UNKNOWN")}</text></svg>`);
    const blob = new Blob([parts.join("")], {type: "image/svg+xml;charset=utf-8"}); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = `trial-${String(DATA.metadata.trial_id)}-frame-${frame + 1}.svg`; link.click(); setTimeout(() => URL.revokeObjectURL(link.href), 0);
  }
  document.getElementById("export-svg").addEventListener("click", exportCurrentSvg);
  if (strategy) {
    document.getElementById("go-best").addEventListener("click", () => seekFrame(strategy.best_frame));
    document.getElementById("go-final-current").addEventListener("click", () => seekFrame(F - 1));
    document.getElementById("strategy-graph").addEventListener("click", event => {
      const box = event.currentTarget.getBoundingClientRect();
      const fraction = Math.max(0, Math.min(1, (event.clientX - box.left) / box.width));
      seekNormalizedWork(fraction);
    });
  }
  function seekNormalizedWork(fraction) {
    if (!strategy) { seekFrame(Math.round(fraction * (F - 1))); return; }
    const work = fraction * Number(strategy.frames[F - 1].work);
    let nearest = 0;
    strategy.frames.forEach((item, index) => { if (Math.abs(Number(item.work) - work) < Math.abs(Number(strategy.frames[nearest].work) - work)) nearest = index; });
    seekFrame(nearest);
  }
  window.asquerixTrajectory = {seekFrame, seekNormalizedWork, setPlaying, getFrame: () => frame, frameCount: F,
    initialIdentity: DATA.metadata.initial_identity || null, frameMetadata: index => strategy ? strategy.frames[index] : null};
  window.addEventListener("message", event => {
    if (event.source !== window.parent || !event.data || event.data.type !== "asquerix-seek") return;
    if (event.data.mode === "work") seekNormalizedWork(Number(event.data.value));
    else if (event.data.mode === "frame") seekFrame(Number(event.data.value));
  });
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
