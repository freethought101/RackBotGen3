// Simulated drive health, ported from rackbot/health.py (03 §7): synthetic SMART values per caddy that drift
// slowly; an injected fault ramps reallocated sectors to WARN then FAILED within FAULT_RAMP_S.
import {FAIL_REALLOC, FAULT_RAMP_S, WARN_REALLOC} from './spec.ts';

export type DriveStatus = 'OK' | 'WARN' | 'FAILED';
export type Smart = {id: number; temp: number; realloc: number; poh: number; status: DriveStatus; ramp: boolean; acc: number};

export class Health {
  drives = new Map<number, Smart>();
  private rng: () => number;

  constructor(rng: () => number) {
    this.rng = rng;
  }

  get(id: number): Smart {
    let d = this.drives.get(id);
    if (!d) {
      d = {id, temp: 31 + this.rng() * 7, realloc: Math.floor(this.rng() * 3), poh: 4000 + this.rng() * 26000, status: 'OK', ramp: false, acc: 0};
      this.drives.set(id, d);
    }
    return d;
  }

  /** A brand-new spare: zero hours, zero reallocated sectors. */
  fresh(id: number) {
    this.drives.set(id, {id, temp: 34, realloc: 0, poh: 0, status: 'OK', ramp: false, acc: 0});
  }

  inject(id: number) {
    this.get(id).ramp = true;
  }

  /** Advance by dt; `spinning` = drives seated in a rack bay. Returns drives whose status changed. */
  tick(dt: number, spinning: Set<number>): Smart[] {
    const changed: Smart[] = [];
    const rate = FAIL_REALLOC / FAULT_RAMP_S;
    for (const d of this.drives.values()) {
      if (spinning.has(d.id)) {
        d.poh += (dt / 3600) * 60; // time-lapse so the dashboard visibly ticks (as health.py)
        const target = 36 + (d.ramp ? 6 : 0);
        d.temp += (target - d.temp) * Math.min(1, dt / 30) + (this.rng() - 0.5) * 0.1 * Math.min(1, dt * 10);
      } else {
        d.temp += (26 - d.temp) * Math.min(1, dt / 60);
      }
      if (d.ramp && d.realloc < FAIL_REALLOC) {
        d.acc += rate * dt;
        const whole = Math.floor(d.acc);
        d.acc -= whole;
        d.realloc = Math.min(FAIL_REALLOC, d.realloc + whole);
      }
      const st: DriveStatus = d.realloc >= FAIL_REALLOC ? 'FAILED' : d.realloc >= WARN_REALLOC ? 'WARN' : 'OK';
      if (st !== d.status) {
        d.status = st;
        changed.push(d);
      }
    }
    return changed;
  }
}
