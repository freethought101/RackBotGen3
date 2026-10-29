// The IIoT dashboard (03 §7 views: rack, robot, jobs, energy, alarms/log, controls), built once per sim and
// refreshed at 5 Hz. Nothing interactive is re-created on refresh, so clicks and focus survive.
import {JOB_STATES, STATE_LABEL} from '../core/mission.ts';
import type {LogLine, Sim} from '../core/sim.ts';
import {COLORS} from '../core/spec.ts';

const $ = <T extends HTMLElement = HTMLElement>(id: string) => document.getElementById(id) as T;

export const hms = (t: number) => {
  const s = Math.floor(t);
  return [s / 3600, (s % 3600) / 60, s % 60].map((v) => String(Math.floor(v)).padStart(2, '0')).join(':');
};
const mmss = (t: number) => `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, '0')}`;
const esc = (s: string) => s.replace(/[&<>]/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;'})[c]!);

type Cell = {btn: HTMLButtonElement; rack: string; i: number};

export class Dashboard {
  sim!: Sim;
  private cells: Cell[] = [];
  private rackHeads = new Map<string, {small: HTMLElement; bar: HTMLElement; col: HTMLElement}>();
  private logEl = $('log');

  bind(sim: Sim) {
    this.sim = sim;
    this.buildRacks();
    this.logEl.innerHTML = '';
    for (const l of sim.logs) this.addLog(l);
    sim.onLog = (l) => this.addLog(l);
    $('kpis').innerHTML = '';
    this.update();
  }

  private buildRacks() {
    const sim = this.sim;
    const host = $('racks');
    host.innerHTML = '';
    this.cells = [];
    this.rackHeads.clear();
    const cols = [...sim.world.racks, sim.world.home];
    host.style.setProperty('--cols', String(cols.length));
    for (const st of cols) {
      const col = document.createElement('div');
      col.className = 'rack-col';
      const head = document.createElement('div');
      head.className = 'rack-h';
      head.innerHTML = `<span>${st.kind === 'rack' ? st.id : 'Home'}</span><small></small><div class="bar"><i style="width:0"></i></div>`;
      col.append(head);
      this.rackHeads.set(st.id, {small: head.querySelector('small')!, bar: head.querySelector('i')!, col: head});
      // top shelf first, like looking at the rack
      for (let i = st.shelves.length - 1; i >= 0; i--) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'drive';
        btn.id = `drive-${st.id}-${i}`;
        if (st.kind === 'rack') btn.addEventListener('click', () => sim.injectFault(st.id, i));
        else btn.disabled = true;
        col.append(btn);
        this.cells.push({btn, rack: st.id, i});
      }
      host.append(col);
    }
  }

  private addLog(l: LogLine) {
    const li = document.createElement('li');
    li.className = l.level;
    li.innerHTML = `<span class="ts">${hms(l.t)}</span><span class="src">${esc(l.src)}</span><span class="msg">${esc(l.msg)}</span>`;
    const atTop = this.logEl.scrollTop < 8;
    this.logEl.prepend(li);
    while (this.logEl.children.length > 200) this.logEl.lastElementChild!.remove();
    if (atTop) this.logEl.scrollTop = 0;
  }

  update() {
    const sim = this.sim;
    $('simClock').textContent = hms(sim.t);
    this.updateMission();
    this.updateRacks();
    this.updateKpis();
    this.updateRobot();
    this.updatePlc();
    this.updateJobs();
    const fault = !!sim.mission.fault || sim.needResumeAfterEstop;
    $<HTMLButtonElement>('resume').disabled = !fault || sim.estop;
    const es = $<HTMLButtonElement>('estop');
    es.textContent = sim.estop ? 'RELEASE E-STOP' : 'E-STOP';
    es.setAttribute('aria-pressed', String(sim.estop));
  }

  private updateMission() {
    const sim = this.sim;
    const m = sim.mission;
    const state = sim.missionState;
    const pill = $('missionPill');
    pill.textContent = state.replace(/_/g, ' ');
    pill.className = `pill ${state.startsWith('FAULT') || state.startsWith('E-STOP') ? 'tone-bad' : m.job ? 'tone-accent' : 'tone-ok'}`;
    const job = m.job;
    const waiting = sim.jobs.find((j) => j.status === 'waiting');
    $('jobLine').textContent = job
      ? `Job #${job.id} · ${job.rack} bay ${job.bay + 1} · caddy ${job.failed} out${job.fresh ? `, ${job.fresh} in` : ''}`
      : waiting
        ? `Job #${waiting.id} waiting: ${waiting.reason}`
        : 'Docked at home, charging. Click a drive to fail it.';
    $('stepLine').textContent = sim.estop ? 'E-stop pressed: motors unpowered' : job ? m.step : '';
    // stepper: the running job, else the last finished one (its cycle-time breakdown)
    const shown = job ?? [...sim.jobs].reverse().find((j) => j.status === 'done');
    const ol = $('stepper');
    if (ol.children.length !== JOB_STATES.length) ol.innerHTML = JOB_STATES.map(() => '<li><span></span><span class="t"></span></li>').join('');
    JOB_STATES.forEach((s, i) => {
      const li = ol.children[i] as HTMLElement;
      const seg = shown?.timeline.find((x) => x.state === s);
      const now = !!job && m.state.endsWith(s) || (!!job && m.state.startsWith('FAULT') && job.timeline[job.timeline.length - 1]?.state === s);
      li.className = !seg ? '' : seg.t1 === null ? (m.fault || sim.paused ? 'fault' : 'now') : 'done';
      if (now && !seg?.t1) li.className = m.fault || sim.paused ? 'fault' : 'now';
      (li.children[0] as HTMLElement).textContent = STATE_LABEL[s];
      const dur = seg ? (seg.t1 ?? sim.t) - seg.t0 : null;
      (li.children[1] as HTMLElement).textContent = dur === null ? '' : `${dur.toFixed(1)} s`;
    });
  }

  private updateRacks() {
    const sim = this.sim;
    for (const [id, h] of this.rackHeads) {
      if (id === 'home') {
        const s1 = sim.world.at('home', 0) !== null;
        const s2 = sim.world.at('home', 1) !== null;
        h.small.textContent = s1 && !s2 ? 'READY' : 'RESTOCK';
        h.col.className = `rack-h ${s1 && !s2 ? 'tone-ok' : 'tone-warn'}`;
        h.bar.style.width = s1 && !s2 ? '100%' : '0';
        continue;
      }
      const r = sim.raid.get(id)!;
      const tone = r.state === 'OPTIMAL' ? 'tone-ok' : r.state === 'REBUILDING' ? 'tone-info' : r.state === 'DEGRADED' ? 'tone-warn' : 'tone-bad';
      h.col.className = `rack-h ${tone}`;
      h.small.textContent = r.state === 'REBUILDING' ? `REBUILD ${(r.progress * 100).toFixed(0)}%` : r.state;
      h.bar.style.width = `${(r.state === 'OPTIMAL' ? 1 : r.state === 'REBUILDING' ? r.progress : 0) * 100}%`;
      h.bar.parentElement!.style.color = r.state === 'REBUILDING' ? COLORS.blue : COLORS.green;
    }
    for (const c of this.cells) {
      const id = sim.world.at(c.rack, c.i);
      const label = c.rack === 'home' ? `S${c.i + 1}${c.i === 0 ? ' good' : ' RMA'}` : `bay ${c.i + 1}`;
      let cls = 'drive';
      let html: string;
      if (id === null) {
        cls += ' empty';
        const inTray = sim.mission.job && sim.mission.job.rack === c.rack && sim.mission.job.bay === c.i;
        html = `<span class="bay">${label}</span><span></span><span class="s">${inTray ? 'swap in progress' : 'empty'}</span>`;
      } else {
        const d = sim.health.get(id);
        if (d.status === 'FAILED') cls += ' failed';
        else if (d.status === 'WARN') cls += ' warn';
        else if (d.poh < 2 && c.rack !== 'home') cls += ' fresh';
        const s = c.rack === 'home' ? (c.i === 0 ? 'new spare' : 'to RMA') : d.realloc >= 5 ? `${d.realloc} bad sect.` : `${d.temp.toFixed(1)} °C`;
        html = `<b>${id}</b><span class="bay">${label}</span><span class="s">${s}</span>`;
      }
      if (c.btn.className !== cls) c.btn.className = cls;
      if (c.btn.innerHTML !== html) c.btn.innerHTML = html;
      c.btn.title = c.rack === 'home' ? '' : id === null ? 'Empty bay' : `Fail caddy ${id} (inject a SMART fault)`;
    }
  }

  private updateKpis() {
    const sim = this.sim;
    const k = sim.kpis();
    const host = $('kpis');
    const items: [string, string, string][] = [
      ['Swaps done', String(k.swaps), k.queued ? `${k.queued} queued` : ''],
      ['Mean cycle', k.cycle === null ? '—' : k.cycle.toFixed(0), k.cycle === null ? '' : 's'],
      ['Fault → new drive', k.window === null ? '—' : mmss(k.window), k.window === null ? '' : 'min'],
      ['Energy / swap', k.wh === null ? '—' : k.wh.toFixed(2), k.wh === null ? '' : 'Wh'],
      ['No-touch jobs', k.clean === null ? '—' : (k.clean * 100).toFixed(0), k.clean === null ? '' : '%'],
      ['RAID degraded', mmss(k.degraded), 'min total'],
      ['Driven', k.odoM.toFixed(1), 'm'],
      ['Failed drives out', String(k.swaps), sim.rmaShipped ? `${sim.rmaShipped} shipped` : ''],
    ];
    if (!host.children.length) {
      host.innerHTML =
        items.map(() => '<div class="kpi"><div class="v"></div><div class="k"></div></div>').join('') +
        '<div class="spark"><span>Battery</span><canvas id="socSpark" width="400" height="68"></canvas><b id="socNow"></b></div>';
    }
    items.forEach(([key, v, unit], i) => {
      const el = host.children[i] as HTMLElement;
      const html = `${v}<small>${unit}</small>`;
      const vv = el.children[0] as HTMLElement;
      if (vv.innerHTML !== html) vv.innerHTML = html;
      (el.children[1] as HTMLElement).textContent = key;
    });
    $('socNow').textContent = `${(sim.battery.soc * 100).toFixed(1)} %`;
    this.drawSpark();
  }

  private drawSpark() {
    const cv = document.getElementById('socSpark') as HTMLCanvasElement | null;
    if (!cv) return;
    const g = cv.getContext('2d')!;
    const {width: w, height: h} = cv;
    g.clearRect(0, 0, w, h);
    const hist = this.sim.battery.history;
    if (hist.length < 2) return;
    const t0 = hist[0].t;
    const t1 = Math.max(hist[hist.length - 1].t, t0 + 60);
    const lo = 0.5;
    const X = (t: number) => ((t - t0) / (t1 - t0)) * (w - 6) + 3;
    const Y = (s: number) => h - 4 - ((Math.max(lo, s) - lo) / (1 - lo)) * (h - 8);
    g.strokeStyle = 'rgba(138,146,156,0.25)';
    g.lineWidth = 1;
    for (const s of [0.5, 0.75, 1]) {
      g.beginPath();
      g.moveTo(0, Y(s));
      g.lineTo(w, Y(s));
      g.stroke();
    }
    g.beginPath();
    hist.forEach((p, i) => (i ? g.lineTo(X(p.t), Y(p.soc)) : g.moveTo(X(p.t), Y(p.soc))));
    g.lineTo(X(hist[hist.length - 1].t), h);
    g.lineTo(X(t0), h);
    g.closePath();
    g.fillStyle = 'rgba(61,220,132,0.14)';
    g.fill();
    g.beginPath();
    hist.forEach((p, i) => (i ? g.lineTo(X(p.t), Y(p.soc)) : g.moveTo(X(p.t), Y(p.soc))));
    g.strokeStyle = COLORS.green;
    g.lineWidth = 2;
    g.stroke();
    const e = hist[hist.length - 1];
    g.fillStyle = COLORS.green;
    g.beginPath();
    g.arc(X(e.t), Y(e.soc), 3.5, 0, Math.PI * 2);
    g.fill();
  }

  private updateRobot() {
    const sim = this.sim;
    const r = sim.robot;
    const b = sim.battery;
    const busy = [...r.busy()].join(' ').toUpperCase() || 'idle';
    const loc = sim.mission.location ? (sim.mission.location === 'home' ? 'docked · home' : `docked · ${sim.mission.location}`) : 'on the move';
    const tray = (s: 'A' | 'B') => sim.world.tray(s) ?? '—';
    const finger = (f: number) => (f > 0.99 ? 'ENG' : f < 0.01 ? 'park' : '…');
    const rows: [string, string][] = [
      ['Where', loc],
      ['Busy', r.estop ? 'E-STOP' : busy],
      ['Lift Z', `${r.Z.toFixed(1)} mm`],
      ['Extract Y', `${r.Y.toFixed(1)} mm`],
      ['Slot A', `${tray('A')} · ${finger(r.fA)}`],
      ['Slot B', `${tray('B')} · ${finger(r.fB)}`],
      ['Battery', `${(b.soc * 100).toFixed(1)} % · ${b.vbat.toFixed(2)} V`],
      ['Current', `${b.ibat >= 0 ? '+' : ''}${b.ibat.toFixed(2)} A ${b.charging ? '(charging)' : ''}`],
      ['Load', `${b.powerW.toFixed(1)} W`],
      ['Wh used', `${b.whUsed.toFixed(2)} · in ${b.whCharged.toFixed(2)}`],
    ];
    const html = `<dl class="rows">${rows.map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join('')}</dl>`;
    const el = $('robotTel');
    if (el.innerHTML !== html) el.innerHTML = html;
  }

  private updatePlc() {
    const sim = this.sim;
    const p = sim.plc;
    const served = sim.mission.job?.rack ?? sim.world.racks[0].id;
    $('plcRack').textContent = `serving ${served}`;
    const led = (on: boolean, cls = '') => `<span class="led ${on ? 'on' : ''} ${cls}"></span>`;
    const x = p.x;
    const ins: [string, string, boolean][] = [
      ...x.bays.map((b, i) => [`X${i}`, `bay ${i + 1} present`, b] as [string, string, boolean]),
      ['X4', 'robot docked (home)', x.dock],
      ['X5', 'rack E-stop OK', x.estopOk],
      ['X6', 'S1 spare present', x.s1],
      ['X7', 'S2 RMA present', x.s2],
    ];
    const lamp = p.lamp;
    const outs: [string, string, boolean, string][] = [
      ['Y0', 'dock power', p.Y0, ''],
      ['Y1', 'lamp green', lamp === 'green', ''],
      ['Y2', 'lamp yellow', lamp === 'amber', 'amber'],
      ['Y3', 'lamp red', lamp === 'red', 'red'],
    ];
    const html =
      `<div class="io">${ins.map(([a, n, on]) => `${led(on)}<code>${a}</code><span>${n}</span>`).join('')}<div class="io-sep"></div>` +
      `${outs.map(([a, n, on, c]) => `${led(on, c)}<code>${a}</code><span>${n}</span>`).join('')}</div>` +
      `<div class="regs">D0=0x${p.D0.toString(16).padStart(2, '0')} D1=0x${p.D1.toString(16)} D3=${p.D3} M0=${+p.M0} M1=${+p.M1} M2=${+p.M2}<br>D2 heartbeat ${p.D2}</div>`;
    const el = $('plcIo');
    if (el.innerHTML !== html) el.innerHTML = html;
  }

  private updateJobs() {
    const sim = this.sim;
    const rows = [...sim.jobs].reverse().slice(0, 8);
    const tone = (s: string) => (s === 'done' ? 'tone-ok' : s === 'running' ? 'tone-accent' : s === 'waiting' ? 'tone-warn' : s === 'rejected' ? 'tone-bad' : 'tone-dim');
    const html =
      '<thead><tr><th>#</th><th>Bay</th><th>Out → in</th><th>Status</th><th class="num">Cycle</th><th class="num">Wh</th></tr></thead><tbody>' +
      (rows.length
        ? rows
            .map(
              (j) =>
                `<tr><td>${j.id}</td><td>${j.rack}·${j.bay + 1}</td><td>${j.failed ?? '—'} → ${j.fresh ?? '…'}</td>` +
                `<td class="${tone(j.status)}">${j.status}${j.faults ? ` (${j.faults} fault)` : ''}</td>` +
                `<td class="num">${j.end !== null && j.start !== null ? `${(j.end - j.start).toFixed(0)} s` : j.start !== null ? `${(sim.t - j.start).toFixed(0)} s` : ''}</td>` +
                `<td class="num">${j.status === 'done' ? j.wh.toFixed(2) : ''}</td></tr>`,
            )
            .join('')
        : '<tr><td colspan="6" class="tone-dim">No jobs yet. Fail a drive above, or turn on random failures.</td></tr>') +
      '</tbody>';
    const el = $('jobs');
    if (el.innerHTML !== html) el.innerHTML = html;
  }
}
