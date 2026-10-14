// RackBotGen3 dashboard: renders the /ws state push (5 Hz). No build step.
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmtTime = (ts) => new Date(ts * 1000).toLocaleTimeString();
const num = (v, d = 1) => (v === null || v === undefined ? "—" : Number(v).toFixed(d));
let last = null;

async function api(method, path, body) {
  const res = await fetch(path, {
    method, headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    flash(err.detail || res.statusText);
  }
  return res;
}

function flash(msg) {
  const bar = $("faultbar");
  bar.hidden = false;
  bar.textContent = msg;
  setTimeout(() => { if (last) renderFault(last.robot.mission); }, 3000);
}

function renderFault(m) {
  const bar = $("faultbar");
  if (m.fault) {
    bar.hidden = false;
    bar.textContent = `FAULT in ${m.fault.state}: ${m.fault.code} ${m.fault.msg || ""}` +
      (m.estop ? " — release the E-stop, then Resume" : " — fix it, then Resume or Abort");
  } else {
    bar.hidden = true;
  }
}

function renderRack(rack) {
  $("bays").innerHTML = rack.bays.map((b) => {
    const h = b.health;
    const cls = b.caddy == null ? "empty" : h.status;
    return `<div class="bay ${cls}">
      <h3>Bay ${b.bay} <span class="status">${b.caddy == null ? "EMPTY" : h.status}</span></h3>
      ${b.caddy == null ? `<div class="muted">no caddy</div>` : `
        <div>${esc(b.serial)} <span class="muted">(tag ${b.caddy})</span></div>
        <div class="muted small">${num(h.temp_c)} °C · ${h.realloc} realloc · ${h.poh} h</div>`}
      <div class="muted small">PLC presence: ${b.present ? "seated" : "empty"}</div>
      <div class="actions">
        <button class="small" data-fault="${b.bay}" ${b.caddy == null ? "disabled" : ""}>Inject fault</button>
        <button class="small" data-swap="${b.bay}" ${b.caddy == null ? "disabled" : ""}>Swap</button>
      </div></div>`;
  }).join("");
  const sp = (s) => (s.present ? `caddy ${s.caddy ?? "?"}` : "empty");
  $("s1").textContent = sp(rack.spare.S1);
  $("s2").textContent = sp(rack.spare.S2);
  $("plc").textContent = rack.plc.online ? `${rack.plc.plc_state} (hb ${rack.plc.plc_heartbeat})` : "offline";
  $("lamp").className = `lamp ${rack.plc.lamp}`;
  if (document.activeElement !== $("auto")) $("auto").checked = rack.auto_mode;
}

function renderRobot(r) {
  const m = r.mission, t = r.telemetry;
  const st = $("mstate");
  st.textContent = m.paused ? `${m.state} (paused)` : m.state;
  st.className = "pill " + (m.state === "FAULT" ? "fault" : m.job ? "busy" : "");
  $("mstep").textContent = m.job ? `job ${m.job.id} · bay ${m.job.bay} · ${m.step} · ${num(m.job.elapsed_s)} s` : m.step;
  renderFault(m);
  const rows = [
    ["Location", m.location ?? "between stations"],
    ["Docked", r.docked ? "yes" : "no"],
    ["Z / Y", `${num(t.z)} / ${num(t.y)} mm`],
    ["Fingers A / B", `${t.fa === "E" ? "engaged" : "parked"} / ${t.fb === "E" ? "engaged" : "parked"}`],
    ["Tray A / B", `${r.tray.A ?? "—"} / ${r.tray.B ?? "—"}`],
    ["Battery", `${r.battery_pct} % · ${num(t.vbat, 2)} V · ${num(t.ibat, 2)} A`],
    ["Charging", r.charging ? `yes (${num(t.dock)} V dock)` : "no"],
    ["Drivers", `${t.en ? "enabled" : "disabled"} · homed ${t.homed || "—"}`],
    ["E-stop", r.estop ? "PRESSED" : "ok"],
    ["Queue", m.queue.length ? m.queue.join(", ") : "empty"],
  ];
  $("robot").innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("");
  $("simcard").hidden = !r.sim;
  $("estop").textContent = r.estop ? "Release robot E-stop" : "Press robot E-stop";
  $("camtext").textContent = r.sim ? "no camera in simulation" : "no camera stream";
}

function renderEnergy(e) {
  const rows = [
    ["Power now", `${num(e.power_w, 1)} W`],
    ["Wh per swap", e.wh_per_swap == null ? "—" : `${num(e.wh_per_swap, 3)} Wh (${e.swaps} swaps)`],
    ["Robot used", `${num(e.wh_used, 3)} Wh`],
    ["Active / idle", `${num(e.wh_active, 3)} / ${num(e.wh_idle, 3)} Wh`],
    ["Dock charge", `${num(e.wh_charged, 3)} Wh`],
  ];
  $("energy").innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("");
}

function renderJobs(jobs) {
  $("jobs").innerHTML = jobs.map((j) => `<tr>
    <td>${j.id}</td><td>${j.bay}</td><td>${esc(j.source)}</td><td>${j.caddy_out ?? "—"}</td><td>${j.caddy_in ?? "—"}</td>
    <td class="res-${esc(j.result)}">${esc(j.result)}</td><td>${j.cycle_s == null ? "—" : num(j.cycle_s) + " s"}</td>
    <td>${j.wh == null ? "—" : num(j.wh, 3)}</td><td class="muted">${esc(j.detail ?? "")}</td></tr>`).join("");
}

function renderEvents(events) {
  $("events").innerHTML = events.slice().reverse().map((e) =>
    `<li class="${esc(e.level)}"><span class="t">${fmtTime(e.ts)}</span>[${esc(e.source)}] ${esc(e.msg)}</li>`).join("");
}

function render(s) {
  last = s;
  renderRack(s.rack);
  renderRobot(s.robot);
  renderEnergy(s.energy);
  renderJobs(s.jobs);
  renderEvents(s.events);
}

function connect() {
  const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
  ws.onopen = () => { $("conn").textContent = "live"; $("conn").className = "pill on"; };
  ws.onmessage = (ev) => render(JSON.parse(ev.data));
  ws.onclose = () => { $("conn").textContent = "offline"; $("conn").className = "pill off"; setTimeout(connect, 1000); };
}

document.addEventListener("click", (ev) => {
  const b = ev.target.closest("button");
  if (!b) return;
  if (b.dataset.act) api("POST", `/api/robot/${b.dataset.act}`);
  else if (b.dataset.fault) api("POST", `/api/bays/${b.dataset.fault}/fault`);
  else if (b.dataset.swap) api("POST", "/api/jobs", { bay: Number(b.dataset.swap) });
  else if (b.id === "estop") api("POST", "/api/sim/estop", { pressed: !(last && last.robot.estop) });
  else if (b.id === "restock") api("POST", "/api/sim/restock", {});
});
$("auto").addEventListener("change", (ev) => api("POST", "/api/auto", { on: ev.target.checked }));
connect();
