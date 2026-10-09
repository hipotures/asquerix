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

function programView(target, candidate, candidates = []) {
  target.replaceChildren();
  const program = candidate.program;
  target.append(element("h3", program.authored.name || "World strategy"));
  target.append(element("p", `${candidate.origin || "Immutable program"} · ${candidate.state || "COMPILED"} · ${candidate.score?.eligible ? "Eligible" : "Unvalidated / ineligible"}`, "muted"));
  const hash = element("p", program.hash, "hash"); target.append(hash);
  const list = element("ol", undefined, "program-list");
  for (const instruction of program.instructions) {
    const row = element("li");
    row.append(element("strong", `${instruction.pc}  ${instruction.op}`), element("span", describe(instruction)), element("small", instruction.source_node, "muted"));
    row.title = `Exact FP32 bits: ${instruction.fp32_bits.join(" ")}`;
    list.append(row);
  }
  target.append(list);
  if (candidate.mutation) {
    target.append(element("h4", `${candidate.mutation.type} at ${candidate.mutation.node_path}`));
    const diff = element("div", undefined, "diff");
    diff.append(element("pre", JSON.stringify(candidate.mutation.before, null, 2), "before"),
                element("pre", JSON.stringify(candidate.mutation.after, null, 2), "after"));
    target.append(diff);
    const parent = candidates.find(item => item.id === candidate.parent_id);
    target.append(element("p", `Parent: ${candidate.parent_id || candidate.parent_hash}. Child tuple: ${JSON.stringify(candidate.score?.ranking_tuple || null)}. Parent tuple: ${JSON.stringify(parent?.score?.ranking_tuple || null)}.`, "muted"));
  } else target.append(element("p", candidate.parent_id ? `Parent: ${candidate.parent_id}` : "Independently generated or fixed; no parent.", "muted"));
}

function curve(target, points, {xKey = "x", yKey = "y", xLabel = "Completed candidate evaluations", onSelect = () => {}} = {}) {
  target.replaceChildren();
  if (!points.length) { target.append(element("p", "No completed independently valid observations yet.", "muted")); return; }
  const ns = "http://www.w3.org/2000/svg", svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", "0 0 680 220"); svg.setAttribute("role", "img"); svg.setAttribute("aria-label", `Best training mean side against ${xLabel}`);
  const xMax = Math.max(1, ...points.map(point => point[xKey]));
  const yMin = Math.min(...points.map(point => point[yKey])), yMax = Math.max(...points.map(point => point[yKey]));
  const x = value => 50 + value / xMax * 600, y = value => 175 - (value - yMin) / Math.max(0.001, yMax - yMin) * 145;
  const colors = ["#2764ad", "#7464ab", "#147d8b", "#b05c37"];
  const arms = [...new Set(points.map(point => point.arm))];
  for (const [index, arm] of arms.entries()) {
    const group = points.filter(point => point.arm === arm).sort((a,b) => a[xKey] - b[xKey]);
    const path = document.createElementNS(ns, "path");
    path.setAttribute("d", group.map((point,i) => `${i ? "L" : "M"}${x(point[xKey])},${y(point[yKey])}`).join(" "));
    path.setAttribute("fill", "none"); path.setAttribute("stroke", colors[index % colors.length]); path.setAttribute("stroke-width", "2"); svg.append(path);
    for (const point of group) {
      const dot = document.createElementNS(ns, "circle"); dot.setAttribute("cx", x(point[xKey])); dot.setAttribute("cy", y(point[yKey])); dot.setAttribute("r", "4"); dot.setAttribute("fill", colors[index % colors.length]);
      dot.setAttribute("tabindex", "0"); dot.setAttribute("role", "button");
      const title = document.createElementNS(ns, "title"); title.textContent = `${arm}: ${xLabel} ${point[xKey]}, mean L ${point[yKey]}; program ${point.candidate_id}`; dot.append(title);
      dot.addEventListener("click", () => onSelect(point)); dot.addEventListener("keydown", event => { if (event.key === "Enter") onSelect(point); }); svg.append(dot);
    }
  }
  for (const [text, tx, ty] of [[`Mean side L ${number(yMin)}–${number(yMax)}`,50,16],[`${xLabel} (0–${number(xMax)})`,50,207]]) {
    const label = document.createElementNS(ns, "text"); label.setAttribute("x",tx); label.setAttribute("y",ty); label.setAttribute("fill","#496174"); label.setAttribute("font-size","11"); label.textContent = text; svg.append(label);
  }
  target.append(svg, element("p", arms.join(" · "), "muted"));
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
