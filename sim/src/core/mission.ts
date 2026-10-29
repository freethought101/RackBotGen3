// Mission state machine, ported from rackbot/mission.py (03 §5): job preconditions, the seven job states,
// pull/push with the one-working-finger rule, goto with the tag approach (§6.2) and its back-off retries,
// FAULT -> operator resume. Every state transition is timestamped for the cycle-time breakdown.
import {AP, CAM_FPS, TURN_ERROR_DEG, Y_PULL, Y_PUSH, Y_SAFE, Z_APPROACH, Z_DRIVE, zFor, type Slot} from './spec.ts';
import {dockPose, fwd, undockPose, wrap, type Station} from './layout.ts';
import {Fault, all, type Proc, type Wait} from './task.ts';
import {approachStep, findTag} from './vision.ts';
import type {Sim} from './sim.ts';

export const JOB_STATES = ['PICK_GOOD', 'TO_RACK', 'EXTRACT_FAILED', 'INSERT_GOOD', 'TO_SPARE_RMA', 'PLACE_RMA', 'RETURN'] as const;
export type JobState = (typeof JOB_STATES)[number];
export const STATE_LABEL: Record<JobState, string> = {
  PICK_GOOD: 'Pick spare from S1 → slot A',
  TO_RACK: 'Drive to rack · tag approach · dock',
  EXTRACT_FAILED: 'Read caddy tag · extract failed → slot B',
  INSERT_GOOD: 'Insert spare into the bay',
  TO_SPARE_RMA: 'Drive home · tag approach · dock',
  PLACE_RMA: 'Failed drive → RMA slot S2',
  RETURN: 'Dock power on · charging',
};

export type Job = {
  id: number;
  rack: string;
  bay: number; // 0-based
  failed: number | null; // caddy ID expected in the bay
  fresh: number | null; // caddy ID of the spare that goes in
  status: 'queued' | 'waiting' | 'running' | 'done' | 'rejected';
  reason: string;
  created: number;
  faultAt: number; // when the drive went FAILED (degraded window start)
  start: number | null;
  end: number | null;
  insertAt: number | null;
  wh0: number;
  wh: number;
  faults: number;
  timeline: {state: JobState; t0: number; t1: number | null}[];
};

export class Mission {
  sim: Sim;
  state: string = 'IDLE_DOCKED';
  step = 'docked at home, charging';
  location: string | null = 'home'; // station the robot is docked at
  job: Job | null = null;
  fault: Fault | null = null;
  resumeReq = false;
  route: [number, number][] = []; // planned floor path of the current drive (world mm)

  constructor(sim: Sim) {
    this.sim = sim;
  }

  private get r() {
    return this.sim.robot;
  }

  private sleep(s: number): Wait {
    const t = this.sim.mt + s;
    return () => this.sim.mt >= t - 1e-9;
  }

  private *do(label: string, w: Wait): Proc {
    this.step = label;
    yield w;
  }

  // --- main loop -----------------------------------------------------------------------------------------------
  *run(): Proc {
    for (;;) {
      const job = this.sim.nextJob();
      if (!job) {
        yield this.sleep(0.25);
        continue;
      }
      yield* this.runJob(job);
    }
  }

  private *runJob(job: Job): Proc {
    const sim = this.sim;
    this.job = job;
    job.status = 'running';
    job.start = sim.t;
    job.wh0 = sim.battery.whUsed;
    sim.plc.M0 = false; // dock power off before moving
    sim.plc.M1 = true;
    sim.log('info', 'mission', `job #${job.id} started: ${job.rack} bay ${job.bay + 1}, caddy ${job.failed} out`);
    for (const st of JOB_STATES) {
      const prev = job.timeline[job.timeline.length - 1];
      if (prev) prev.t1 = sim.t;
      job.timeline.push({state: st, t0: sim.t, t1: null});
      this.state = st;
      yield* this.guarded(() => this.jobState(st, job));
    }
    job.timeline[job.timeline.length - 1].t1 = sim.t;
    job.status = 'done';
    job.end = sim.t;
    job.wh = sim.battery.whUsed - job.wh0;
    sim.plc.M1 = false;
    this.job = null;
    this.state = 'IDLE_DOCKED';
    this.step = 'docked at home, charging';
    sim.log('ok', 'mission', `job #${job.id} closed: cycle ${(job.end - job.start!).toFixed(1)} s, ${job.wh.toFixed(2)} Wh`);
    sim.onJobDone(job);
  }

  /** Run a state; on a Fault wait in FAULT for the operator's resume, then re-run it (each state is re-entrant). */
  private *guarded(fn: () => Proc): Proc {
    for (;;) {
      try {
        yield* fn();
        return;
      } catch (e) {
        if (!(e instanceof Fault)) throw e;
        const st = this.state;
        this.fault = e;
        if (this.job) this.job.faults++;
        this.r.vel(0, 0);
        this.sim.plc.M2 = true;
        this.state = `FAULT(${e.code})`;
        this.step = 'waiting for the operator: fix the cause, then Resume';
        this.sim.log('err', 'mission', `FAULT ${e.code}: ${e.message}`);
        this.resumeReq = false;
        yield () => this.resumeReq;
        this.resumeReq = false;
        this.fault = null;
        this.sim.plc.M2 = false;
        this.state = st;
        this.sim.log('info', 'mission', `resumed ${st}`);
      }
    }
  }

  private *jobState(st: JobState, job: Job): Proc {
    const sim = this.sim;
    const rack = sim.world.station(job.rack);
    const home = sim.world.home;
    switch (st) {
      case 'PICK_GOOD':
        if (sim.world.tray('A') === null) job.fresh = yield* this.pull('A', home, 0, null);
        return;
      case 'TO_RACK':
        return yield* this.goto(rack);
      case 'EXTRACT_FAILED':
        if (sim.world.tray('B') === null) yield* this.pull('B', rack, job.bay, job.failed);
        return;
      case 'INSERT_GOOD':
        if (sim.world.tray('A') !== null) {
          yield* this.push('A', rack, job.bay);
          job.insertAt = sim.t;
          sim.onInserted(job);
        }
        return;
      case 'TO_SPARE_RMA':
        return yield* this.goto(home);
      case 'PLACE_RMA':
        if (sim.world.tray('B') !== null) yield* this.push('B', home, 1);
        return;
      case 'RETURN':
        return yield* this.startCharging();
    }
  }

  // --- primitives (mission.py _pull/_push) ------------------------------------------------------------------------
  private *ensureYHome(): Proc {
    if (this.r.Y > Y_SAFE) yield* this.do('Y 0', this.r.moveY(0));
  }

  private *secureFingers(): Proc {
    const w = this.sim.world;
    yield* this.do('secure fingers', all(this.r.finger('A', w.tray('A') !== null), this.r.finger('B', w.tray('B') !== null)));
  }

  private *fineAlign(st: Station, i: number): Proc {
    const id = st.kind === 'rack' ? i + 1 : 11 + i;
    yield* this.do(`fine-align on shelf tag ${id}`, this.sleep(1 / CAM_FPS));
  }

  private *pull(slot: Slot, st: Station, i: number, expected: number | null): Proc<number | null> {
    const sim = this.sim;
    const other: Slot = slot === 'A' ? 'B' : 'A';
    const where = st.kind === 'rack' ? `${st.id} bay ${i + 1}` : `S${i + 1}`;
    yield* this.ensureYHome();
    const z = zFor(slot, st.shelves[i], 'extract');
    yield* this.do(`Z ${z.toFixed(0)} (slot ${slot} level with ${where})`, this.r.moveZ(z));
    yield* this.fineAlign(st, i);
    let caddy: number | null = sim.world.at(st.id, i);
    if (sim.world.tray('B') === null) {
      // the camera sees the shelf through the empty slot B window
      yield* this.do('read caddy tag', this.sleep(1 / CAM_FPS));
      const seen = sim.camBlocked ? null : caddy;
      if (seen === null) sim.log('warn', 'vision', `${where}: caddy tag not read`);
      else if (expected !== null && seen !== expected) throw new Fault('E_CADDY_ID', `${where}: expected caddy ${expected}, saw ${seen}`);
      else sim.log('ok', 'vision', `${where}: caddy tag ${seen}${expected !== null ? ' matches the job' : ' → new caddy for this job'}`);
    }
    if (caddy === null) throw new Fault('E_VERIFY', `${where} is empty`);
    yield* this.do('fingers park', all(this.r.finger('A', false), this.r.finger('B', false)));
    yield* this.do('Y pull', this.r.moveY(Y_PULL));
    yield* this.do(`finger ${slot} engage`, this.r.finger(slot, true));
    sim.world.loc.set(caddy, {at: 'tray', slot});
    yield* this.do('Y 0', this.r.moveY(0));
    if (sim.world.tray(other) !== null) yield* this.do(`finger ${other} engage`, this.r.finger(other, true));
    sim.log('info', 'mission', `pulled caddy ${caddy} from ${where} into slot ${slot}`);
    return caddy;
  }

  private *push(slot: Slot, st: Station, i: number): Proc {
    const sim = this.sim;
    const other: Slot = slot === 'A' ? 'B' : 'A';
    const where = st.kind === 'rack' ? `${st.id} bay ${i + 1}` : `S${i + 1}`;
    const caddy = sim.world.tray(slot);
    yield* this.ensureYHome();
    const z = zFor(slot, st.shelves[i], 'insert');
    yield* this.do(`Z ${z.toFixed(0)} (slot ${slot} level with ${where})`, this.r.moveZ(z));
    yield* this.fineAlign(st, i);
    yield* this.do(`finger ${slot} engage, ${other} park`, all(this.r.finger(slot, true), this.r.finger(other, false)));
    yield* this.do('Y push', this.r.moveY(Y_PUSH));
    yield* this.do(`finger ${slot} park`, this.r.finger(slot, false));
    if (caddy !== null) sim.world.loc.set(caddy, {at: 'shelf', st: st.id, i});
    yield* this.do('Y 0', this.r.moveY(0));
    if (sim.world.tray(other) !== null) yield* this.do(`finger ${other} engage`, this.r.finger(other, true));
    sim.log('info', 'mission', `pushed caddy ${caddy} from slot ${slot} into ${where}`);
  }

  // --- driving (mission.py _goto/_approach) ------------------------------------------------------------------------
  private *goto(st: Station): Proc {
    const sim = this.sim;
    const r = this.r;
    if (this.location === st.id && r.nose) return;
    yield* this.ensureYHome();
    yield* this.secureFingers();
    if (this.location === 'home') sim.plc.M0 = false;
    yield* this.do('Z approach', r.moveZ(Z_APPROACH));
    if (r.nose && this.location) {
      const from = sim.world.station(this.location);
      const lane = sim.preset.laneY;
      const u = undockPose(from, lane);
      const d = dockPose(st);
      this.route = this.plan(from, st);
      this.location = null;
      yield* this.do('undock', r.drive(-Math.hypot(u.x - r.pose.x, u.y - r.pose.y)));
      if (lane !== null && Math.abs(d.x - r.pose.x) > 1) {
        const dir = Math.sign(d.x - r.pose.x);
        yield* this.do('turn to the aisle', r.turn(wrap(-dir * (Math.PI / 2) - r.pose.th)));
        yield* this.do(`drive the aisle → ${st.label}`, r.drive(Math.abs(d.x - r.pose.x)));
        yield* this.do('turn to the station', r.turn(wrap(st.phi - r.pose.th), r.slip(TURN_ERROR_DEG)));
      } else {
        yield* this.do('turn 180', r.turn(Math.PI, r.slip(TURN_ERROR_DEG)));
      }
    }
    yield* this.approach(st);
    yield* this.do('dock', r.dock(dockPose(st)));
    if (!r.nose) throw new Fault('E_NODOCK', 'NOSE not pressed after DOCK');
    this.route = [];
    this.location = st.id;
    sim.log('ok', 'robot', `funnel-docked at ${st.label}${st.kind === 'spare' ? ' (PLC dock switch X4 ✓)' : ' (NOSE ✓)'}`);
    yield* this.do('Z drive', r.moveZ(Z_DRIVE));
  }

  private *approach(st: Station): Proc {
    const sim = this.sim;
    let retries = 0;
    let lostSince: number | null = null;
    const label = `approach tag ${st.tag}`;
    this.step = label;
    for (;;) {
      yield this.sleep(1 / CAM_FPS);
      const pose = findTag(sim.world, st, this.r.pose, this.r.Z, sim.camBlocked);
      sim.lastTagPose = pose;
      const now = sim.mt;
      let backoff: string | null = null;
      if (!pose) {
        lostSince ??= now;
        if (now - lostSince > AP.lost_s) backoff = `tag ${st.tag} lost`;
      } else {
        lostSince = null;
        const cmd = approachStep(pose);
        if (cmd.handoff) {
          this.r.vel(0, 0);
          sim.log('info', 'vision', `hand-off to DOCK at d=${pose.d.toFixed(0)} mm, x=${pose.x.toFixed(1)} mm, ψ=${pose.psi.toFixed(1)}°`);
          return;
        }
        if (cmd.tooClose) backoff = `too close without alignment (x=${pose.x.toFixed(0)} mm, ψ=${pose.psi.toFixed(1)}°)`;
        else this.r.vel(cmd.v, cmd.w);
      }
      if (backoff) {
        retries++;
        if (retries > AP.max_retries) throw new Fault('E_TAG_LOST', backoff);
        sim.log('warn', 'vision', `approach: ${backoff}, backing off (${retries}/${AP.max_retries})`);
        this.r.stop();
        yield* this.do('back off', this.r.drive(-AP.backoff_mm));
        this.step = label;
        lostSince = null;
      }
    }
  }

  private *startCharging(): Proc {
    const sim = this.sim;
    sim.plc.M0 = true;
    for (let i = 0; i < 20; i++) {
      if (this.r.nose && sim.plc.Y0 && (sim.battery.charging || sim.battery.soc >= 0.999)) {
        sim.log('ok', 'robot', 'docked at the spare station, charging');
        return;
      }
      yield* this.do('dock power on, waiting for charge current', this.sleep(0.25));
    }
    throw new Fault('E_NOCHARGE', 'dock power on but no charging current');
  }

  /** The nominal floor path for the route line. */
  private plan(from: Station, to: Station): [number, number][] {
    const u = undockPose(from, this.sim.preset.laneY);
    const d = dockPose(to);
    const pts: [number, number][] = [[this.r.pose.x, this.r.pose.y], [u.x, u.y]];
    if (this.sim.preset.laneY !== null) pts.push([d.x, u.y]);
    const [fx, fy] = fwd(d.th);
    pts.push([d.x - fx * 2, d.y - fy * 2]);
    return pts;
  }
}
