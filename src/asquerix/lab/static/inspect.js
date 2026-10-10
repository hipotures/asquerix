/* Shared real-data inspection controls for the local app and offline report. */
const element = (tag, text, className = "") => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  node.className = className;
  return node;
};
const number = value => typeof value === "number" ? value.toPrecision(7) : "—";
const describe = instruction => {
  const [, a, b, c, magnitude] = instruction.words;
  if (instruction.op === "COMPRESS") return `${c ? `${number(magnitude * 100)}% reduction at entry` : "legacy adaptive compression"}; ${a} attempts, ${b} sweeps per attempt`;
  if (instruction.op === "EXPAND") return `${number(magnitude * 100)}% larger container; centers stay fixed`;
  if (["MOVE", "ROTATE"].includes(instruction.op)) return `${["ALL", "RANDOM_K", "WALL_K"][a]}${a ? `(${b})` : ""}; maximum ${number(magnitude)} ${instruction.op === "MOVE" ? "unit lengths" : "radians"}; ${c} joint repair sweeps`;
  if (instruction.op === "IF_FALSE") return `${["", "LAST_NO_PROGRESS", "LAST_REJECTED", "LAST_IMPROVED_BEST"][a]}; false branch → ${b}`;
  if (instruction.op === "JUMP") return `forward to instruction ${b}`;
  if (instruction.op === "RELAX") return "Already feasible: no geometric change";
  if (instruction.op === "RESTORE_BEST") return "Restore protected best; RNG and work are preserved";
  return "Return protected best; finalization does not compress";
};

// Authored (source) form: the tree that mutations edit, with REPEAT and IF as blocks.
const describeSource = node => {
  if (node.op === "COMPRESS") return `${node.target_reduction === null ? "legacy adaptive compression" : `${number(node.target_reduction * 100)}% reduction at entry`}; ${node.attempt_limit} attempts, ${node.sweep_limit} sweeps per attempt`;
  if (node.op === "EXPAND") return `${number(node.fraction * 100)}% larger container; centers stay fixed`;
  if (["MOVE", "ROTATE"].includes(node.op)) return `${node.selector.kind}${node.selector.kind === "ALL" ? "" : `(${node.selector.k})`}; maximum ${number(node.op === "MOVE" ? node.max_distance : node.max_angle_rad)} ${node.op === "MOVE" ? "unit lengths" : "radians"}; ${node.repair_sweeps} joint repair sweeps`;
  if (node.op === "RELAX") return "Already feasible: no geometric change";
  if (node.op === "RESTORE_BEST") return "Restore protected best; RNG and work are preserved";
  if (node.op === "STOP") return "Return protected best; finalization does not compress";
  return "";
};
let programMode = "compiled";
try { programMode = localStorage.getItem("asquerix-program-view") || "compiled"; } catch {}

function sourceList(items, path, mutated, mutationType) {
  const list = element("ol", undefined, "source-list");
  items.forEach((node, index) => {
    const nodePath = `${path}[${index}]`, row = element("li");
    if (nodePath === mutated) row.classList.add("mutated");
    const head = element("div", undefined, "source-node");
    if (node.op === "REPEAT") head.append(element("strong", `${index}  REPEAT ${node.count}×`));
    else if (node.op === "IF") head.append(element("strong", `${index}  IF ${node.predicate}`));
    else head.append(element("strong", `${index}  ${node.op}`), element("span", describeSource(node)));
    if (nodePath === mutated) { head.title = "Node changed by this candidate's mutation"; head.append(element("em", `mutation: ${mutationType}`, "mutation-tag")); }
    row.append(head);
    if (node.op === "REPEAT") row.append(sourceList(node.body, `${nodePath}.body`, mutated, mutationType));
    if (node.op === "IF") {
      row.append(sourceList(node.then, `${nodePath}.then`, mutated, mutationType));
      if (node.else?.length) { row.append(element("div", "ELSE", "source-else")); row.append(sourceList(node.else, `${nodePath}.else`, mutated, mutationType)); }
    }
    list.append(row);
  });
  return list;
}

function programView(target, candidate, candidates = []) {
  target.replaceChildren();
  const program = candidate.program;
  target.append(element("h3", program.authored.name || "World strategy"));
  target.append(element("p", `${candidate.origin || "Immutable program"} · ${candidate.state || "COMPILED"} · ${candidate.score?.eligible ? "Eligible" : "Unvalidated / ineligible"}`, "muted"));
  const hash = element("p", program.hash, "hash"); target.append(hash);
  const toggle = element("div", undefined, "view-toggle"), holder = element("div");
  const show = mode => {
    programMode = mode;
    try { localStorage.setItem("asquerix-program-view", mode); } catch {}
    for (const button of toggle.children) button.setAttribute("aria-pressed", String(button.dataset.mode === mode));
    holder.replaceChildren();
    if (mode === "source") {
      const tree = sourceList(program.authored.body, "body", candidate.mutation?.node_path, candidate.mutation?.type);
      tree.classList.add("source-root"); holder.append(tree); return;
    }
    const list = element("ol", undefined, "program-list");
    for (const instruction of program.instructions) {
      const row = element("li");
      row.append(element("strong", `${instruction.pc}  ${instruction.op}`), element("span", describe(instruction)), element("small", instruction.source_node, "muted"));
      row.title = `Exact FP32 bits: ${instruction.fp32_bits.join(" ")}`;
      list.append(row);
    }
    holder.append(list);
  };
  for (const [mode, label, title] of [["compiled", "Compiled", "Instructions as the GPU executes them: REPEAT unrolled, IF as jumps"], ["source", "Source", "The authored program tree that mutations edit"]]) {
    const button = element("button", label); button.type = "button"; button.dataset.mode = mode; button.title = title;
    button.addEventListener("click", () => show(mode)); toggle.append(button);
  }
  target.append(toggle, holder);
  show(programMode);
  if (candidate.mutation) {
    // Same colour as the highlighted node in the source view; before/after use the same tree form.
    const section = element("div", undefined, "mutation-section");
    section.append(element("h4", `Mutation: ${candidate.mutation.type} at ${candidate.mutation.node_path}`));
    const side = (value, label, className) => {
      const box = element("div", undefined, `mutation-side ${className}`);
      box.append(element("small", label));
      const nodes = Array.isArray(value) ? value : value && typeof value === "object" && value.op ? [value] : null;
      if (nodes) box.append(sourceList(nodes, "", null, null));
      else box.append(element("pre", value === null || value === undefined ? "(nothing)" : JSON.stringify(value, null, 2)));
      return box;
    };
    const diff = element("div", undefined, "diff");
    diff.append(side(candidate.mutation.before, "Parent", "before"), side(candidate.mutation.after, "This candidate", "after"));
    section.append(diff);
    target.append(section);
    const parent = candidates.find(item => item.id === candidate.parent_id);
    target.append(element("p", `Parent: ${candidate.parent_id || candidate.parent_hash}. Child tuple: ${JSON.stringify(candidate.score?.ranking_tuple || null)}. Parent tuple: ${JSON.stringify(parent?.score?.ranking_tuple || null)}.`, "muted"));
  } else target.append(element("p", candidate.parent_id ? `Parent: ${candidate.parent_id}` : "Independently generated or fixed; no parent.", "muted"));
}

// Validated pairs for the light and dark surfaces (theme tokens in style.css); color follows the method.
const SERIES_COLORS = {random_program_search: "var(--series-random)", one_plus_lambda: "var(--series-mutation)"};
const FALLBACK_COLORS = ["var(--series-3)", "var(--series-4)"];
const ARM_LABELS = {random_program_search: "random search", one_plus_lambda: "(1 + λ) mutation"};
const armLabel = arm => ARM_LABELS[arm] || arm.replaceAll("_", " ");
const svgNode = (tag, attributes = {}, text) => {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  return node;
};
const compact = value => Math.abs(value) >= 1e6 ? `${+(value / 1e6).toFixed(1)}M` : Math.abs(value) >= 1e3 ? `${+(value / 1e3).toFixed(1)}K` : `${+value.toFixed(2)}`;
function niceTicks(low, high, count) {
  const span = Math.max(high - low, 1e-9), raw = span / count, power = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map(f => f * power).find(f => f >= raw);
  const ticks = [];
  for (let value = Math.ceil(low / step) * step; value <= high + step * 1e-9; value += step) ticks.push(+value.toFixed(10));
  return ticks;
}

// Best-so-far training mean L per search method as step lines, with fixed controls as reference lines.
function curve(target, points, {xKey = "x", yKey = "y", xLabel = "Completed candidate evaluations", onSelect = () => {}, references = [], marker = null, xMax: xLimit = 0} = {}) {
  target.replaceChildren();
  target.classList.add("progress-chart");
  if (!points.length) { target.append(element("p", "No completed, independently validated candidates yet. The curve appears after the first finished group.", "muted empty-chart")); return; }
  const arms = [...new Set(points.map(point => point.arm))];
  const seriesLabel = group => armLabel(group.arm) + (group.measure === "single" ? " best single" : "");
  const color = (arm, index) => SERIES_COLORS[arm] || FALLBACK_COLORS[index % FALLBACK_COLORS.length];
  const width = Math.max(560, target.clientWidth || 900), height = 340, margin = {left: 62, right: 64, top: 18, bottom: 44};
  const plotW = width - margin.left - margin.right, plotH = height - margin.top - margin.bottom;
  const ys = [...points.map(point => point[yKey]), ...references.map(item => item.value)];
  let yMin = Math.min(...ys), yMax = Math.max(...ys);
  // Early poor incumbents would flatten the interesting region: the scale tops out at the controls or at the
  // best first value of any method, and higher values are clipped to the top edge with a marker.
  const firsts = arms.map(arm => points.filter(point => point.arm === arm).sort((a, b) => a[xKey] - b[xKey])[0][yKey]);
  const focus = Math.max(...references.filter(item => item.kind !== "best-known").map(item => item.value), Math.min(...firsts));
  if (yMax > focus + (focus - yMin) * 1.5) yMax = focus + (focus - yMin) * 0.25;
  const pad = Math.max((yMax - yMin) * 0.08, 0.002); yMin -= pad; yMax += pad;
  const top = yMax;
  const xMax = Math.max(1, xLimit, ...points.map(point => point[xKey]));
  const x = value => margin.left + value / xMax * plotW, y = value => margin.top + (top - Math.min(value, top)) / (top - yMin) * plotH;
  const clipped = value => value > top;
  const svg = svgNode("svg", {viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": `Best training mean and best single-episode side L so far for ${arms.join(" and ")} against ${xLabel}; lower is better`});
  for (const tick of niceTicks(yMin, yMax, 5)) {
    svg.append(svgNode("line", {x1: margin.left, x2: margin.left + plotW, y1: y(tick), y2: y(tick), class: "grid"}));
    svg.append(svgNode("text", {x: margin.left - 8, y: y(tick) + 4, "text-anchor": "end", class: "tick"}, tick.toFixed(3)));
  }
  for (const tick of niceTicks(0, xMax, 8)) svg.append(svgNode("text", {x: x(tick), y: margin.top + plotH + 18, "text-anchor": "middle", class: "tick"}, compact(tick)));
  svg.append(svgNode("line", {x1: margin.left, x2: margin.left + plotW, y1: margin.top + plotH, y2: margin.top + plotH, class: "axis"}));
  svg.append(svgNode("text", {x: margin.left + plotW / 2, y: height - 6, "text-anchor": "middle", class: "axis-label"}, xLabel));
  svg.append(svgNode("text", {x: 14, y: margin.top + plotH / 2, transform: `rotate(-90 14 ${margin.top + plotH / 2})`, "text-anchor": "middle", class: "axis-label"}, "Best L (lower is better)"));
  if (marker && marker.x > 0 && marker.x < xMax) {
    svg.append(svgNode("line", {x1: x(marker.x), x2: x(marker.x), y1: margin.top, y2: margin.top + plotH, class: "reference"}));
    svg.append(svgNode("text", {x: x(marker.x) + 6, y: margin.top + 12, class: "tick"}, marker.label));
  }
  const labels = [];
  for (const item of references) {
    const best = item.kind === "best-known";
    svg.append(svgNode("line", {x1: margin.left, x2: margin.left + plotW, y1: y(item.value), y2: y(item.value), class: best ? "best-known" : "reference"}));
    labels.push({y: y(item.value), text: item.value.toFixed(4), kind: best ? "best-known" : "reference"});
  }
  // The best-single line shares its method's colour and is drawn dashed.
  const groups = arms.flatMap((arm, index) => ["mean", "single"].map(measure => ({arm, measure, color: color(arm, index),
    points: points.filter(point => point.arm === arm && (point.measure || "mean") === measure).sort((a, b) => a[xKey] - b[xKey])}))).filter(group => group.points.length);
  for (const group of groups) {
    const path = group.points.map((point, i) => i ? `H${x(point[xKey])}V${y(point[yKey])}` : `M${x(point[xKey])},${y(point[yKey])}`).join("");
    const line = svgNode("path", {d: path + `H${margin.left + plotW}`, fill: "none", "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round"});
    if (group.measure === "single") line.setAttribute("stroke-dasharray", "7 4");
    line.style.stroke = group.color; svg.append(line);
    group.points.forEach((point, i) => {
      if (i && point[yKey] >= group.points[i - 1][yKey]) return;  // markers only where the incumbent improved
      const cx = x(point[xKey]), cy = y(point[yKey]);
      const dot = clipped(point[yKey])
        ? svgNode("path", {d: `M${cx - 5},${cy + 6}L${cx},${cy - 2}L${cx + 5},${cy + 6}Z`, class: "chart-point", tabindex: "0", role: "button"})
        : svgNode("circle", {cx, cy, r: 4.5, class: "chart-point", tabindex: "0", role: "button"});
      dot.style.fill = group.color;
      dot.append(svgNode("title", {}, `${seriesLabel(group)} ${i ? "improved to" : "started at"} ${point[yKey].toFixed(6)}${clipped(point[yKey]) ? " (above the shown range)" : ""} at ${compact(point[xKey])}; open program ${point.candidate_id}`));
      dot.addEventListener("click", () => onSelect(point));
      dot.addEventListener("keydown", event => { if (event.key === "Enter") onSelect(point); });
      svg.append(dot);
    });
    const last = group.points.at(-1);
    labels.push({y: y(last[yKey]), text: last[yKey].toFixed(4), color: group.color});
  }
  labels.sort((a, b) => a.y - b.y);  // keep end labels from overlapping
  labels.forEach((label, i) => { if (i && label.y - labels[i - 1].y < 15) label.y = labels[i - 1].y + 15; });
  // Only the end values; the legend above the chart names the lines.
  for (const label of labels) {
    svg.append(svgNode("text", {x: margin.left + plotW + 6, y: label.y + 4, class: label.color || label.kind === "best-known" ? "end-label" : "tick"}, label.text));
  }
  // Crosshair and tooltip: values of every method at the hovered x.
  const cross = svgNode("line", {y1: margin.top, y2: margin.top + plotH, class: "crosshair", visibility: "hidden"});
  const hit = svgNode("rect", {x: margin.left, y: margin.top, width: plotW, height: plotH, fill: "transparent"});
  svg.append(cross); svg.insertBefore(hit, svg.querySelector(".chart-point"));
  const tooltip = element("div", undefined, "chart-tooltip"); tooltip.hidden = true;
  hit.addEventListener("mousemove", event => {
    const box = svg.getBoundingClientRect(), scale = width / box.width, px = (event.clientX - box.left) * scale;
    const at = Math.max(0, Math.min(xMax, (px - margin.left) / plotW * xMax));
    cross.setAttribute("x1", x(at)); cross.setAttribute("x2", x(at)); cross.setAttribute("visibility", "visible");
    tooltip.replaceChildren(element("strong", `${xLabel}: ${compact(at)}`));
    for (const group of groups) {
      const current = group.points.filter(point => point[xKey] <= at).at(-1);
      const row = element("div"), key = element("i"); key.style.background = group.color;
      row.append(key, element("span", `${seriesLabel(group)}: ${current ? current[yKey].toFixed(6) : "—"}`));
      tooltip.append(row);
    }
    for (const item of references) tooltip.append(element("div", `${item.label}: ${item.value.toFixed(6)}`, "muted"));
    tooltip.hidden = false;
    tooltip.style.left = `${Math.min(event.clientX - target.getBoundingClientRect().left + 14, target.clientWidth - 240)}px`;
    tooltip.style.top = `${event.clientY - target.getBoundingClientRect().top + 14}px`;
  });
  hit.addEventListener("mouseleave", () => { tooltip.hidden = true; cross.setAttribute("visibility", "hidden"); });
  const legend = element("div", undefined, "legend");
  for (const group of groups) {
    const item = element("span", group.measure === "single" ? `${armLabel(group.arm)} best single episode` : `${armLabel(group.arm)} best mean`), swatch = element("i", undefined, group.measure === "single" ? "dashed-series" : undefined);
    if (group.measure === "single") swatch.style.borderTopColor = group.color; else swatch.style.background = group.color;
    item.prepend(swatch); legend.append(item);
  }
  if (references.some(item => item.kind !== "best-known")) { const item = element("span", "fixed controls"), swatch = element("i", undefined, "dashed"); item.prepend(swatch); legend.append(item); }
  if (references.some(item => item.kind === "best-known")) { const item = element("span", "best known upper bound"), swatch = element("i", undefined, "best-known"); item.prepend(swatch); legend.append(item); }
  if (points.some(point => clipped(point[yKey]))) legend.append(element("span", `▲ above ${top.toFixed(3)}: off scale, hover for the value`, "muted"));
  target.append(legend, svg, tooltip);
}

function historyView(target, events, candidates, onSelect) {
  target.replaceChildren();
  if (!events.length) { target.append(element("p", "No durable semantic events yet.", "muted")); return; }
  const slider = element("input"); slider.type = "range"; slider.min = "0"; slider.max = String(events.length - 1); slider.value = "0"; slider.setAttribute("aria-label", "Campaign history event");
  const label = element("p"), detail = element("pre");
  const show = () => {
    const event = events[Number(slider.value)];
    label.textContent = `Event ${event.id} · ${event.kind} · ${new Date(event.created * 1000).toLocaleString()}`;
    detail.textContent = JSON.stringify(event.payload, null, 2);
    const candidateId = event.payload.candidate_id || event.payload.parent_id || (event.kind === "CANDIDATE_GENERATED" ? event.payload.id : null);
    const candidate = candidates.find(item => item.id === candidateId);
    if (candidate) onSelect(candidate);
  };
  slider.addEventListener("input", show); target.append(slider, label, detail); show();
}

function replayComparison(target, replays, resolveHtml) {
  target.replaceChildren();
  if (!replays.length) { target.append(element("p", "Selected geometric replays become available after evaluation.", "muted")); return; }
  const controls = element("div", undefined, "toolbar"), left = element("select"), right = element("select"), mode = element("select");
  for (const select of [left, right]) for (const [index, replay] of replays.entries()) {
    const option = element("option", `${replay.candidate_id} · ${replay.status}`); option.value = String(index); select.append(option);
  }
  right.value = String(Math.min(1, replays.length - 1));
  for (const [value, label] of [["frame", "Recorded frame"],["work", "Normalized consumed work"],["independent", "Independent stepping"]]) {
    const option = element("option",label); option.value=value; mode.append(option);
  }
  const range = element("input"); range.type="range"; range.min="0"; range.max="1000"; range.value="0"; range.setAttribute("aria-label", "Two-program synchronized progress");
  const warning = element("p", undefined, "muted"), panes = element("div", undefined, "replay-pair");
  const frames = [element("iframe"), element("iframe")];
  frames.forEach(frame => { frame.title="Recorded strategy geometry"; frame.setAttribute("sandbox","allow-scripts allow-downloads"); panes.append(frame); });
  controls.append(left,right,mode); target.append(controls,warning,range,panes);
  const load = () => {
    const selected = [replays[Number(left.value)],replays[Number(right.value)]];
    const same = JSON.stringify(selected[0].initial_identity) === JSON.stringify(selected[1].initial_identity);
    warning.textContent = same ? "Same initial-world identity. Equal frame indices do not imply equal work. Each pane also supports independent playback and zoom." : "Different initial-world identities: synchronized comparison is disabled.";
    range.disabled = !same || mode.value === "independent";
    selected.forEach((replay,index) => {
      const html = resolveHtml(replay);
      if (html.startsWith("<!") || html.startsWith("<html")) frames[index].srcdoc = html;
      else frames[index].src = html;
    });
  };
  [left,right,mode].forEach(select => select.addEventListener("change",load));
  range.addEventListener("input", () => {
    const fraction = Number(range.value) / 1000;
    const selected = [replays[Number(left.value)],replays[Number(right.value)]];
    frames.forEach((frame,index) => frame.contentWindow.postMessage({type:"asquerix-seek",mode:mode.value,value:mode.value === "work" ? fraction : Math.round(fraction*(selected[index].frames-1))},"*"));
  });
  load();
}

globalThis.LabInspect = {element, number, describe, programView, curve, historyView, replayComparison};
