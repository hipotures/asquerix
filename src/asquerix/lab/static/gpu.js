/* Header GPU telemetry: shown while the laboratory computes, frozen afterwards until dismissed. */
const root = document.getElementById('gpu-monitor');
const headers = {'Content-Type': 'application/json', 'X-Asquerix-Client': 'lab-v1'};
try { const csrf = sessionStorage.getItem('asquerix-csrf'); if (csrf) headers['X-CSRF-Token'] = csrf; } catch {}
let dismissed = null, session = null, openLimit = null, timer = null;
try { dismissed = Number(sessionStorage.getItem('asquerix-gpu-dismissed')) || null; } catch {}

const short = name => name.replace(/^NVIDIA\s+/, '').replace(/^GeForce\s+/, '');
const value = (number, unit, digits = 0) => number === null || number === undefined ? '—' : `${number.toFixed(digits)}${unit}`;
const level = (number, warn, hot) => number === null ? '' : number >= hot ? 'hot' : number >= warn ? 'warm' : 'ok';
const el = (tag, className, text) => { const node = document.createElement(tag); if (className) node.className = className; if (text !== undefined) node.textContent = text; return node; };

function sparkline(canvas, values) {
  const ratio = devicePixelRatio || 1, width = canvas.clientWidth * ratio, height = canvas.clientHeight * ratio;
  canvas.width = width; canvas.height = height;
  const context = canvas.getContext('2d'), slots = 60, bar = width / slots;
  context.clearRect(0, 0, width, height);
  context.fillStyle = 'rgba(255,255,255,.08)'; context.fillRect(0, height - ratio, width, ratio);
  context.fillStyle = '#3fb6c8';
  values.slice(-slots).forEach((item, index, list) => {
    if (item === null) return;
    const h = Math.max(ratio, item / 100 * height);
    context.fillRect((slots - list.length + index) * bar, height - h, Math.max(1, bar - ratio), h);
  });
}

function limitPanel(gpu, control) {
  const panel = el('form', 'gpu-limit-panel');
  panel.append(el('strong', undefined, `Power limit · GPU ${gpu.index}`));
  const input = el('input'); input.type = 'number'; input.min = gpu.power_min_w; input.max = gpu.power_max_w; input.step = '5';
  input.value = Math.round(gpu.power_limit_w); input.setAttribute('aria-label', 'Power limit in watts');
  const row = el('div', 'gpu-limit-row'); row.append(input, el('span', undefined, `W (${gpu.power_min_w}–${gpu.power_max_w}, default ${gpu.power_default_w})`));
  const apply = el('button', 'gpu-apply', 'Apply'); apply.type = 'submit';
  const message = el('p', 'gpu-limit-message');
  panel.append(row, apply, message);
  if (!control?.available) {
    input.disabled = apply.disabled = true;
    message.textContent = control?.reason || 'Power control is unavailable.';
    if (control?.sudoers) message.append(el('code', undefined, control.sudoers));
  } else message.textContent = 'Affects measured speed, not numerical results. Recorded in the running campaign history.';
  panel.addEventListener('submit', async event => {
    event.preventDefault(); apply.disabled = true; message.textContent = 'Applying…';
    try {
      const response = await fetch(`/api/v1/gpus/${gpu.index}/power-limit`, {method: 'POST', headers: {...headers, 'Idempotency-Key': crypto.randomUUID()}, body: JSON.stringify({watts: Number(input.value)})});
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Request rejected');
      message.textContent = `Set to ${data.requested_w} W (was ${data.previous_w} W).`;
    } catch (error) { message.textContent = error.message; }
    apply.disabled = false;
  });
  return panel;
}

function render(data) {
  const visible = data.session > 0 && data.gpus.length && (data.live || dismissed !== data.started);
  root.hidden = !visible;
  if (!visible) { layout(); return; }
  if (session !== data.session) { session = data.session; openLimit = null; }
  root.classList.toggle('frozen', !data.live);
  root.dataset.count = String(data.gpus.length + (data.cpu ? 1 : 0));
  root.replaceChildren();
  // Host CPU next to the GPUs: validation and bookkeeping run on the CPU while the GPU waits.
  if (data.cpu) {
    const cpu = data.cpu, tile = el('div', 'gpu-tile cpu-tile'), head = el('div', 'gpu-head'), stats = el('div', 'gpu-stats');
    head.append(el('span', 'gpu-name', 'CPU'), el('span', 'gpu-tag', `${cpu.cores} threads`));
    const app = el('span', undefined, `app ${cpu.app_cores.toFixed(1)} cores`);
    app.title = `This server, its CUDA worker and validation processes (${cpu.app_processes} processes) used ${cpu.app_cores.toFixed(2)} cores of CPU time per second`;
    const busy = el('span', undefined, `busy ${cpu.busy_threads}/${cpu.cores}`);
    busy.title = 'Threads of this application that ran for more than half of the last second';
    stats.append(el('span', undefined, `load ${value(cpu.load_percent, '%')}`), app, busy);
    const spark = el('canvas', 'gpu-spark'); spark.setAttribute('aria-label', 'Host CPU load history');
    tile.append(head, stats, spark); root.append(tile);
    sparkline(spark, data.samples.map(sample => sample.cpu ? sample.cpu[0] : null));
  }
  data.gpus.forEach((gpu, position) => {
    const history = data.samples.map(sample => sample.gpus[position] || [null, null, null, null, null]);
    const tile = el('div', 'gpu-tile');
    const head = el('div', 'gpu-head');
    head.append(el('span', 'gpu-name', short(gpu.name)), el('span', 'gpu-tag', `GPU ${gpu.index}${gpu.uuid === data.campaign_device_uuid ? ' · campaign' : ''}`));
    const stats = el('div', 'gpu-stats');
    stats.append(el('span', `gpu-temp ${level(gpu.temperature_c, 70, 83)}`, value(gpu.temperature_c, '°C')),
                 el('span', undefined, `fan ${value(gpu.fan_percent, '%')}`),
                 el('span', undefined, `gpu ${value(gpu.utilization_percent, '%')}`),
                 el('span', undefined, `mem ${value(gpu.memory_percent, '%')}`));
    const power = el('button', 'gpu-power', `pwr ${value(gpu.power_w, '')}/${value(gpu.power_limit_w, ' W')}`);
    power.type = 'button'; power.title = 'Power draw / limit. Click to change the power limit.';
    power.setAttribute('aria-expanded', String(openLimit === gpu.index));
    power.addEventListener('click', () => { openLimit = openLimit === gpu.index ? null : gpu.index; render(data); });
    stats.append(power);
    const spark = el('canvas', 'gpu-spark'); spark.setAttribute('aria-label', 'GPU utilization history');
    tile.append(head, stats, spark);
    if (openLimit === gpu.index) tile.append(limitPanel(gpu, data.power_control));
    root.append(tile);
    sparkline(spark, history.map(item => item[3]));
  });
  layout();
  if (!data.live) {
    const close = el('button', 'gpu-close');  // the cross is drawn in CSS so it stays centred close.type = 'button';
    close.title = `Computation finished at ${new Date(data.finished * 1000).toLocaleTimeString()}; values are frozen. Hide until the next computation.`;
    close.setAttribute('aria-label', 'Hide GPU telemetry');
    close.addEventListener('click', () => { dismissed = data.started;  // session numbers restart with the server; start times do not
      try { sessionStorage.setItem('asquerix-gpu-dismissed', String(dismissed)); } catch {} root.hidden = true; layout(); });
    root.append(close);
  }
}

// Keep the tiles centred on the page: in the first header row when they fit there, otherwise on a row of their own.
function layout() {
  const header = root.closest('header');
  header.classList.remove('stacked');
  if (root.hidden) return;
  const style = getComputedStyle(header), gap = parseFloat(style.columnGap) || 0;
  const inner = header.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
  const side = Math.max(header.querySelector('.brand').offsetWidth, header.querySelector('.header-actions').offsetWidth);
  if (2 * side + root.offsetWidth + 2 * 28 + 2 * gap > inner) header.classList.add('stacked');
}
addEventListener('resize', layout);

async function poll() {
  let live = false;
  try {
    // An open power-limit form is not re-rendered, so typed values are kept.
    const response = await fetch('/api/v1/gpu-monitor', {credentials: 'same-origin', headers});
    if (response.ok) { const data = await response.json(); live = data.live; if (openLimit === null) render(data); }
  } catch {}
  timer = setTimeout(poll, document.hidden ? 5000 : live ? 1000 : 3000);
}
document.addEventListener('visibilitychange', () => { if (!document.hidden) { clearTimeout(timer); poll(); } });
poll();
