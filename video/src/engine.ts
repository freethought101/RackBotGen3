// Keyframe engine shared by the films: channels animated by keys, plus a timed event list. Everything is a pure
// function of the frame number, so stills, overlays and the 3D scene always agree.

export type Ease = (t: number) => number;
export const linear: Ease = (t) => t;
export const inOut: Ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
export const outCubic: Ease = (t) => 1 - Math.pow(1 - t, 3);
export const smooth: Ease = (t) => t * t * (3 - 2 * t);

type Key = {f: number; v: number; e: Ease};

export class Track {
  keys: Key[] = [];
  push(f: number, v: number, e: Ease) {
    this.keys.push({f, v, e});
  }
  last() {
    return this.keys[this.keys.length - 1];
  }
  at(f: number): number {
    const k = this.keys;
    if (f <= k[0].f) return k[0].v;
    for (let i = 1; i < k.length; i++) {
      if (f < k[i].f) {
        const a = k[i - 1];
        const b = k[i];
        const t = (f - a.f) / (b.f - a.f);
        return a.v + (b.v - a.v) * b.e(t);
      }
    }
    return k[k.length - 1].v;
  }
}

export const CHANNELS = ['cx', 'cy', 'th', 'Z', 'Y', 'fA', 'fB'] as const;
export type Ch = (typeof CHANNELS)[number];

/** A path segment: signed length along the heading (mm, < 0 = reverse) and the heading change over it. */
export type Seg = {d: number; dth?: number};
export type Route = {f0: number; f1: number; pts: [number, number][]};

export type DistributiveOmit<T, K extends keyof T> = T extends unknown ? Omit<T, K> : never;

export class Script<Event extends {f: number}> {
  t = 0;
  tracks: Record<Ch, Track>;
  events: Event[] = [];
  routes: Route[] = [];
  constructor(init: Record<Ch, number>) {
    this.tracks = Object.fromEntries(CHANNELS.map((c) => [c, new Track()])) as Record<Ch, Track>;
    for (const c of CHANNELS) this.tracks[c].push(0, init[c], linear);
  }
  hold(c: Ch) {
    const tr = this.tracks[c];
    if (tr.last().f < this.t) tr.push(this.t, tr.last().v, linear);
  }
  /** Animate the given channels over dur frames, starting at the cursor. */
  to(dur: number, vals: Partial<Record<Ch, number>>, e: Ease = inOut) {
    for (const [c, v] of Object.entries(vals) as [Ch, number][]) {
      this.hold(c);
      this.tracks[c].push(this.t + dur, v, e);
    }
    this.t += dur;
    return this;
  }
  /** Jump channels instantly (scene cuts). */
  cut(vals: Partial<Record<Ch, number>>) {
    for (const [c, v] of Object.entries(vals) as [Ch, number][]) {
      this.hold(c);
      this.tracks[c].push(this.t + 0.001, v, linear);
    }
    return this;
  }
  wait(dur: number) {
    this.t += dur;
    return this;
  }
  goto(f: number) {
    this.t = f;
    return this;
  }
  ev(e: DistributiveOmit<Event, 'f'>, dt = 0) {
    this.events.push({...e, f: this.t + dt} as unknown as Event);
    return this;
  }
  get(c: Ch) {
    return this.tracks[c].at(this.t);
  }
  /** Drive a chain of straights and arcs with one speed profile; keys every frame keep the arcs round. */
  path(dur: number, segs: Seg[], e: Ease = smooth) {
    const x0 = this.get('cx');
    const y0 = this.get('cy');
    const th0 = this.get('th');
    const total = segs.reduce((a, g) => a + Math.abs(g.d), 0);
    const pose = (sd: number) => {
      let [x, y, th] = [x0, y0, th0];
      for (const g of segs) {
        const len = Math.abs(g.d);
        const u = Math.min(len, Math.max(0, sd));
        const sg = Math.sign(g.d);
        const k = (g.dth ?? 0) / len;
        if (Math.abs(k) < 1e-9) {
          x += -Math.sin(th) * sg * u;
          y += Math.cos(th) * sg * u;
        } else {
          const th1 = th + k * u;
          x += (sg * (Math.cos(th1) - Math.cos(th))) / k;
          y += (sg * (Math.sin(th1) - Math.sin(th))) / k;
          th = th1;
        }
        sd -= len;
        if (sd <= 0) break;
      }
      return [x, y, th] as const;
    };
    for (const c of ['cx', 'cy', 'th'] as const) this.hold(c);
    for (let i = 1; i <= dur; i++) {
      const [x, y, th] = pose(e(i / dur) * total);
      this.tracks.cx.push(this.t + i, x, linear);
      this.tracks.cy.push(this.t + i, y, linear);
      this.tracks.th.push(this.t + i, th, linear);
    }
    const pts = Array.from({length: 61}, (_, i) => pose((i / 60) * total)).map(([x, y]) => [x, y] as [number, number]);
    this.routes.push({f0: this.t, f1: this.t + dur, pts});
    this.t += dur;
    return this;
  }
}
