// Kinematic robot: diff-drive base, Z lift, Y extractor and fingers A/B at the spec speeds (spec.ts), like the
// firmware's command set (03 §3): Z, Y, FINGER, DRIVE, TURN, VEL, DOCK, STOP. While the E-stop is pressed nothing
// moves (VMOT is cut) but logic stays alive.
import {AP, FINGER_S, POWER_W, SPEED, Z_HOME, type Slot} from './spec.ts';
import {fwd, wrap, rad, type Pose} from './layout.ts';
import type {Wait} from './task.ts';

type Anim = {update(dt: number): boolean; axis: 'drive' | 'z' | 'y' | 'finger'};

const approach = (cur: number, target: number, rate: number, dt: number) => {
  const d = target - cur;
  const s = rate * dt;
  return Math.abs(d) <= s ? target : cur + Math.sign(d) * s;
};

export class Robot {
  pose: Pose = {x: 0, y: 0, th: 0};
  Z = Z_HOME;
  Y = 0;
  fA = 0; // 0 = parked, 1 = engaged
  fB = 0;
  nose = false; // NOSE switch: pressed when funnel-docked
  estop = false;
  private ch: {base: Anim | null; z: Anim | null; y: Anim | null; A: Anim | null; B: Anim | null} = {base: null, z: null, y: null, A: null, B: null};
  private seq = {base: 0, z: 0, y: 0, A: 0, B: 0};
  /** Turn error source (wheel slip), deterministic per seed. */
  rng: () => number;
  odo = 0; // mm driven

  constructor(rng: () => number) {
    this.rng = rng;
  }

  private run(c: keyof Robot['ch'], a: Anim): Wait {
    this.ch[c] = a;
    const n = ++this.seq[c];
    return () => this.seq[c] !== n || this.ch[c] === null;
  }

  update(dt: number) {
    if (this.estop) return;
    for (const c of ['base', 'z', 'y', 'A', 'B'] as const) {
      const a = this.ch[c];
      if (a && a.update(dt)) this.ch[c] = null;
    }
  }

  /** Axes moving right now (for the power model and the dashboard's busy letters). */
  busy() {
    const b = new Set<string>();
    if (this.estop) return b;
    for (const a of Object.values(this.ch)) if (a) b.add(a.axis);
    return b;
  }

  powerW() {
    const b = this.busy();
    return POWER_W.idle + (b.has('drive') ? POWER_W.drive : 0) + (b.has('z') ? POWER_W.z : 0) + (b.has('y') ? POWER_W.y : 0) + (b.has('finger') ? POWER_W.finger : 0);
  }

  moveZ(target: number): Wait {
    return this.run('z', {axis: 'z', update: (dt) => (this.Z = approach(this.Z, target, SPEED.z, dt)) === target});
  }

  moveY(target: number): Wait {
    return this.run('y', {axis: 'y', update: (dt) => (this.Y = approach(this.Y, target, SPEED.y, dt)) === target});
  }

  finger(slot: Slot, engage: boolean): Wait {
    const key = slot === 'A' ? 'fA' : 'fB';
    const t = engage ? 1 : 0;
    if (this[key] === t) return () => true;
    return this.run(slot, {axis: 'finger', update: (dt) => (this[key] = approach(this[key], t, 1 / FINGER_S, dt)) === t});
  }

  /** Straight move along the heading (mm, < 0 = reverse). */
  drive(d: number, v = SPEED.drive): Wait {
    this.nose = false;
    let left = Math.abs(d);
    const sg = Math.sign(d);
    return this.run('base', {
      axis: 'drive',
      update: (dt) => {
        const s = Math.min(left, v * dt);
        this.advance(sg * s);
        left -= s;
        return left <= 1e-6;
      },
    });
  }

  /** In-place turn (rad, + = CCW). `slip` adds the sim's wheel-slip error (TURN overshoot). */
  turn(a: number, slip = 0): Wait {
    this.nose = false;
    const total = a + Math.sign(a) * slip;
    let left = Math.abs(total);
    const sg = Math.sign(total);
    return this.run('base', {
      axis: 'drive',
      update: (dt) => {
        const s = Math.min(left, rad(SPEED.turn) * dt);
        this.pose.th = wrap(this.pose.th + sg * s);
        left -= s;
        return left <= 1e-9;
      },
    });
  }

  /** Velocity mode (VEL v w): mm/s, deg/s (+ = CCW), until the next base command. */
  vel(v: number, wDeg: number) {
    this.nose = false;
    if (v === 0 && wDeg === 0) {
      this.ch.base = null;
      return;
    }
    this.ch.base = {
      axis: 'drive',
      update: (dt) => {
        this.pose.th = wrap(this.pose.th + rad(wDeg) * dt);
        this.advance(v * dt);
        return false;
      },
    };
  }

  stop() {
    this.ch.base = null;
  }

  /**
   * DOCK max speed: blind forward until the NOSE switch closes. The V-funnel takes out up to ±20 mm lateral and a few
   * degrees of heading, so when the dock pose is within reach the robot is guided onto it exactly.
   */
  dock(target: Pose | null, max = AP.dock_max_mm, v = AP.dock_speed): Wait {
    const p0 = {...this.pose};
    const [fx, fy] = fwd(p0.th);
    const along = target ? (target.x - p0.x) * fx + (target.y - p0.y) * fy : Infinity;
    const lateral = target ? (target.x - p0.x) * fy - (target.y - p0.y) * fx : Infinity;
    const herr = target ? Math.abs(wrap(target.th - p0.th)) : Infinity;
    const ok = target !== null && along > 0 && along <= max && Math.abs(lateral) <= 20 && herr <= rad(8);
    const dist = ok ? along : max;
    let s = 0;
    this.nose = false;
    return this.run('base', {
      axis: 'drive',
      update: (dt) => {
        s = Math.min(dist, s + v * dt);
        const k = s / dist;
        if (ok) {
          // straight run in, with the funnel pulling the residual offset out over the last third
          const g = Math.min(1, Math.max(0, (k - 0.66) / 0.34));
          const bx = p0.x + fx * s;
          const by = p0.y + fy * s;
          const tx = target!.x - fx * (dist - s);
          const ty = target!.y - fy * (dist - s);
          this.pose.x = bx + (tx - bx) * g;
          this.pose.y = by + (ty - by) * g;
          this.pose.th = wrap(p0.th + wrap(target!.th - p0.th) * g);
        } else {
          this.pose.x = p0.x + fx * s;
          this.pose.y = p0.y + fy * s;
        }
        if (s >= dist) {
          this.nose = ok;
          return true;
        }
        return false;
      },
    });
  }

  private advance(d: number) {
    const [fx, fy] = fwd(this.pose.th);
    this.pose.x += fx * d;
    this.pose.y += fy * d;
    this.odo += Math.abs(d);
  }

  /** TURN overshoot for this turn (rad). */
  slip(maxDeg: number) {
    return rad(maxDeg * (0.4 + 0.6 * this.rng()));
  }
}
