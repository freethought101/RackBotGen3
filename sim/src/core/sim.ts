// The whole simulated system in one object, three.js-free so it also runs headless (scripts/check.ts):
// world + robot + mission + PLC + health + battery, the job queue, RAID state per rack, KPIs and the event log.
import {PRESETS, dockPose, robotToWorld, toWorld, type Preset} from './layout.ts';
import {Robot} from './robot.ts';
import {World} from './world.ts';
import {Plc} from './plc.ts';
import {Health, type Smart} from './health.ts';
import {Battery} from './energy.ts';
import {Mission, type Job} from './mission.ts';
import {Task} from './task.ts';
import type {TagPose} from './vision.ts';
import {BAY_PITCH, Y_PULL, Z_DRIVE} from './spec.ts';

export type Level = 'info' | 'ok' | 'warn' | 'err';
export type LogLine = {t: number; level: Level; src: string; msg: string};
export type Raid = {state: 'OPTIMAL' | 'DEGRADED' | 'REBUILDING' | 'AT RISK'; progress: number; degradedS: number};

export const REBUILD_S = 60; // RAID rebuild, time-lapsed (a real multi-TB rebuild takes hours)
const TECH_DELAY_S = 30; // simulated technician visit after the spare station runs out
const SUBSTEP = 0.02;

/** Small deterministic PRNG (mulberry32). */
export function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export class Sim {
  preset: Preset;
  t = 0; // simulated seconds
  mt = 0; // mission clock: stops while the robot is E-stopped or waiting for resume
  rand: () => number;
  world: World;
  robot: Robot;
  plc = new Plc();
  health: Health;
  battery = new Battery(0.9);
  mission: Mission;
  task: Task;
  jobs: Job[] = [];
  logs: LogLine[] = [];
  raid = new Map<string, Raid>();
  lastTagPose: TagPose | null = null;
  // settings / operator inputs
  auto = true;
  randomFaults = false;
  autoRestock = true;
  camBlocked = false;
  estop = false;
  needResumeAfterEstop = false;
  private nextRandom = Infinity;
  private techAt: number | null = null;
  private jobSeq = 1;
  rmaShipped = 0;
  onLog: ((l: LogLine) => void) | null = null;

  constructor(presetId: keyof typeof PRESETS = 'hall', seed = 7) {
    this.preset = PRESETS[presetId];
    this.rand = rng(seed);
    this.world = new World(this.preset.stations);
    this.robot = new Robot(this.rand);
    this.health = new Health(this.rand);
    for (const id of this.world.loc.keys()) this.health.get(id);
    this.health.fresh(this.world.at('home', 0)!);
    const home = dockPose(this.world.home);
    this.robot.pose = {...home};
    this.robot.Z = Z_DRIVE;
    this.robot.nose = true;
    this.plc.M0 = true;
    for (const r of this.world.racks) this.raid.set(r.id, {state: 'OPTIMAL', progress: 1, degradedS: 0});
    this.mission = new Mission(this);
    this.task = new Task(this.mission.run());
    this.log('info', 'system', `${this.preset.title}: robot docked at home, ${this.world.racks.length * 4} drives online`);
  }

  log(level: Level, src: string, msg: string) {
    const l = {t: this.t, level, src, msg};
    this.logs.push(l);
    if (this.logs.length > 400) this.logs.shift();
    this.onLog?.(l);
  }

  // --- operator / judge actions -----------------------------------------------------------------------------------
  injectFault(rack: string, bay: number) {
    const id = this.world.at(rack, bay);
    if (id === null) return;
    const d = this.health.get(id);
    if (d.ramp || d.status !== 'OK') return;
    this.health.inject(id);
    this.log('warn', 'health', `${rack} bay ${bay + 1}: caddy ${id} reallocated sectors rising (fault injected)`);
  }

  queueJob(rack: string, bay: number, faultAt = this.t): Job | null {
    if (this.jobs.some((j) => j.rack === rack && j.bay === bay && (j.status === 'queued' || j.status === 'waiting' || j.status === 'running'))) return null;
    const job: Job = {
      id: this.jobSeq++, rack, bay, failed: this.world.at(rack, bay), fresh: null, status: 'queued', reason: '',
      created: this.t, faultAt, start: null, end: null, insertAt: null, wh0: 0, wh: 0, faults: 0, timeline: [],
    };
    this.jobs.push(job);
    this.log('info', 'jobs', `job #${job.id} queued: ${rack} bay ${bay + 1}`);
    return job;
  }

  pressEstop() {
    if (this.estop) return;
    this.estop = true;
    this.robot.estop = true;
    this.robot.stop();
    this.plc.M2 = true;
    this.log('err', 'robot', 'E-STOP pressed: VMOT cut, all axes stopped (logic stays alive)');
  }

  releaseEstop() {
    if (!this.estop) return;
    this.estop = false;
    this.robot.estop = false;
    this.needResumeAfterEstop = true;
    this.log('info', 'robot', 'E-stop released: drivers re-configured (TMC2209 UART), ENABLE 1 — press Resume');
  }

  resume() {
    if (this.estop) return;
    if (this.needResumeAfterEstop) {
      this.needResumeAfterEstop = false;
      if (!this.mission.fault) this.plc.M2 = false;
      this.log('info', 'mission', 'operator: resume after E-stop');
    }
    if (this.mission.fault) this.mission.resumeReq = true;
  }

  restock() {
    const {removed, added} = this.world.restock();
    if (removed !== null) this.rmaShipped++;
    if (added !== null) this.health.fresh(added);
    this.techAt = null;
    if (removed !== null || added !== null)
      this.log('ok', 'technician', `spare station restocked${added !== null ? `: new spare ${added} in S1` : ''}${removed !== null ? `, RMA caddy ${removed} taken out of S2` : ''}`);
  }

  get paused() {
    return this.estop || this.needResumeAfterEstop;
  }

  get missionState() {
    if (this.estop) return 'FAULT(E_ESTOP)';
    if (this.needResumeAfterEstop) return 'E-STOP RELEASED · press Resume';
    return this.mission.state;
  }

  // --- job scheduling (mission.py job preconditions) --------------------------------------------------------------
  nextJob(): Job | null {
    for (const j of this.jobs) {
      if (j.status !== 'queued' && j.status !== 'waiting') continue;
      if (this.world.at(j.rack, j.bay) === null) {
        j.status = 'rejected';
        j.reason = 'bay is empty';
        this.log('warn', 'jobs', `job #${j.id} rejected: ${j.rack} bay ${j.bay + 1} is empty`);
        continue;
      }
      const why =
        this.mission.location !== 'home' || !this.robot.nose ? 'robot not docked at home'
        : this.world.at('home', 0) === null ? 'no spare in S1 — waiting for restock'
        : this.world.at('home', 1) !== null ? 'RMA slot S2 full — waiting for restock'
        : this.world.tray('A') !== null || this.world.tray('B') !== null ? 'tray not empty'
        : '';
      if (why) {
        if (j.status !== 'waiting' || j.reason !== why) this.log('warn', 'jobs', `job #${j.id} waiting: ${why}`);
        j.status = 'waiting';
        j.reason = why;
        return null; // FIFO: the head of the queue blocks
      }
      j.reason = '';
      return j;
    }
    return null;
  }

  onInserted(job: Job) {
    const r = this.raid.get(job.rack)!;
    r.state = 'REBUILDING';
    r.progress = 0;
    this.log('ok', 'raid', `${job.rack}: new drive ${job.fresh} seated in bay ${job.bay + 1} (PLC bit ✓), RAID rebuild started`);
  }

  onJobDone(_job: Job) {
    if (this.world.at('home', 0) === null || this.world.at('home', 1) !== null) this.scheduleTech();
  }

  private scheduleTech() {
    if (!this.autoRestock || this.techAt !== null) return;
    this.techAt = this.t + TECH_DELAY_S;
    this.log('info', 'technician', `spare station needs restocking: technician visit in ${TECH_DELAY_S} s (simulated)`);
  }

  setRandomFaults(on: boolean) {
    this.randomFaults = on;
    this.nextRandom = on ? this.t + this.expo(this.preset.randomFaultMeanS * 0.3) : Infinity;
    this.log('info', 'system', on ? 'random drive failures ON' : 'random drive failures OFF');
  }

  private expo(mean: number) {
    return -Math.log(1 - this.rand()) * mean;
  }

  // --- time ------------------------------------------------------------------------------------------------------------
  advance(dt: number) {
    let left = dt;
    while (left > 1e-9) {
      const h = Math.min(SUBSTEP, left);
      this.substep(h);
      left -= h;
    }
  }

  private substep(dt: number) {
    this.t += dt;
    if (!this.paused && !this.mission.fault) this.mt += dt;
    if (!this.paused) {
      this.robot.update(dt);
      this.task.step();
    }
    const w = this.world;
    // the Y carriage carries a tray caddy only while its finger is in the notch; released, it stays put
    for (const id of w.trayY.keys()) if (w.where(id)?.at !== 'tray') w.trayY.delete(id);
    for (const slot of ['A', 'B'] as const) {
      const id = w.tray(slot);
      if (id === null) continue;
      if ((slot === 'A' ? this.robot.fA : this.robot.fB) > 0.5 || !w.trayY.has(id)) w.trayY.set(id, this.robot.Y - Y_PULL);
    }
    // health of the drives seated in racks
    const spinning = new Set<number>();
    for (const r of w.racks) r.shelves.forEach((_, i) => {
      const id = w.at(r.id, i);
      if (id !== null) spinning.add(id);
    });
    for (const d of this.health.tick(dt, spinning)) this.onHealth(d);
    // RAID per rack
    for (const r of w.racks) {
      const raid = this.raid.get(r.id)!;
      let bad = 0;
      r.shelves.forEach((_, i) => {
        const id = w.at(r.id, i);
        if (id === null || this.health.get(id).status === 'FAILED') bad++;
      });
      if (bad >= 2) raid.state = 'AT RISK';
      else if (bad === 1) raid.state = 'DEGRADED';
      else if (raid.state === 'REBUILDING') {
        raid.progress = Math.min(1, raid.progress + dt / REBUILD_S);
        if (raid.progress >= 1) {
          raid.state = 'OPTIMAL';
          this.log('ok', 'raid', `${r.id}: rebuild complete, RAID optimal`);
        }
      } else if (raid.state !== 'OPTIMAL') raid.state = 'REBUILDING';
      if (bad > 0) raid.degradedS += dt;
    }
    // PLC inputs: the rack being served (or R1) + the spare station
    const served = this.mission.job?.rack ?? w.racks[0].id;
    const docked = this.robot.nose && this.mission.location === 'home';
    this.plc.scan(dt, {
      bays: w.station(served).shelves.map((_, i) => w.at(served, i) !== null),
      dock: docked, estopOk: true, s1: w.at('home', 0) !== null, s2: w.at('home', 1) !== null,
    });
    // idle housekeeping: stop charging when full, top up below 15.6 V (config mission.charge_restart_v)
    if (!this.mission.job && docked) {
      if (this.battery.soc >= 1 && this.plc.M0) this.plc.M0 = false;
      if (this.battery.vbat < 15.6 && !this.plc.M0) this.plc.M0 = true;
    }
    this.battery.tick(dt, this.robot.powerW(), this.plc.Y0 && docked, this.mission.job !== null, this.t);
    // random failures and the technician
    if (this.randomFaults && this.t >= this.nextRandom) {
      this.nextRandom = this.t + this.expo(this.preset.randomFaultMeanS);
      const ok = [...spinning].filter((id) => {
        const d = this.health.get(id);
        return d.status === 'OK' && !d.ramp;
      });
      if (ok.length) {
        const id = ok[Math.floor(this.rand() * ok.length)];
        const l = w.where(id)!;
        if (l.at === 'shelf') this.injectFault(l.st, l.i);
      }
    }
    if (this.techAt !== null && this.t >= this.techAt && !this.mission.job) this.restock();
    if (this.techAt === null && this.autoRestock && !this.mission.job && this.jobs.some((j) => j.status === 'waiting' && j.reason.includes('restock'))) this.scheduleTech();
  }

  private onHealth(d: Smart) {
    const l = this.world.where(d.id);
    const where = this.world.name(l);
    if (d.status === 'WARN') this.log('warn', 'health', `${where}: caddy ${d.id} SMART WARN (${d.realloc} reallocated sectors)`);
    if (d.status === 'FAILED') {
      this.log('err', 'health', `${where}: caddy ${d.id} FAILED — RAID degraded`);
      if (this.auto && l?.at === 'shelf') this.queueJob(l.st, l.i, this.t);
    }
  }

  /** Where a caddy physically is (world mm, shelf-floor z), or null once it has gone to RMA. */
  caddyPos(id: number): [number, number, number] | null {
    const l = this.world.where(id);
    if (!l || l.at === 'gone') return null;
    if (l.at === 'shelf') {
      const st = this.world.station(l.st);
      const [x, y] = toWorld(st, 0, 0);
      return [x, y, st.shelves[l.i]];
    }
    const [x, y] = robotToWorld(this.robot.pose, 0, this.world.trayY.get(id) ?? -Y_PULL);
    return [x, y, this.robot.Z + 1 + (l.slot === 'A' ? BAY_PITCH : 0)];
  }

  // --- KPIs ------------------------------------------------------------------------------------------------------------
  kpis() {
    const done = this.jobs.filter((j) => j.status === 'done');
    const mean = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null);
    return {
      swaps: done.length,
      queued: this.jobs.filter((j) => j.status === 'queued' || j.status === 'waiting').length,
      cycle: mean(done.map((j) => j.end! - j.start!)),
      window: mean(done.map((j) => j.insertAt! - j.faultAt)),
      wh: mean(done.map((j) => j.wh)),
      clean: done.length ? done.filter((j) => j.faults === 0).length / done.length : null,
      degraded: [...this.raid.values()].reduce((a, r) => a + r.degradedS, 0),
      odoM: this.robot.odo / 1000,
    };
  }
}
