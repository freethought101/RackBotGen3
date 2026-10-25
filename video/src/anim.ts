// Keyframe engine + the mission script. Everything is a pure function of the frame number, so stills,
// overlays and the 3D scene always agree.
import {AXLE_Y, BAY_PITCH, H_BAY, H_SPARE, SCENES, SPARE_D, Y_PULL, Z_TRAVEL} from './constants';

export type Ease = (t: number) => number;
export const linear: Ease = (t) => t;
export const inOut: Ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
export const outCubic: Ease = (t) => 1 - Math.pow(1 - t, 3);
export const smooth: Ease = (t) => t * t * (3 - 2 * t);

type Key = {f: number; v: number; e: Ease};

class Track {
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

const CHANNELS = ['cx', 'cy', 'th', 'Z', 'Y', 'fA', 'fB'] as const;
type Ch = (typeof CHANNELS)[number];

export type CaddyMode =
  | {mode: 'rack'; bay: number}
  | {mode: 'spare'; slot: number}
  | {mode: 'robot'; slot: 'A' | 'B'};

type Event =
  | {f: number; kind: 'caddy'; id: CaddyId; to: CaddyMode}
  | {f: number; kind: 'step'; step: number}
  | {f: number; kind: 'bay'; bay: number; state: BayState}
  | {f: number; kind: 'light'; light: Light}
  | {f: number; kind: 'toast'; text: string; tone: Tone}
  | {f: number; kind: 'tag'; id: number; on: boolean}
  | {f: number; kind: 'charge'; on: boolean};

export type CaddyId = 'spare' | 'failed';
export type BayState = 'ok' | 'failed' | 'empty' | 'new';
export type Light = 'green' | 'amber' | 'red';
export type Tone = 'info' | 'ok' | 'warn';

type DistributiveOmit<T, K extends keyof T> = T extends unknown ? Omit<T, K> : never;

class Script {
  t = 0;
  tracks: Record<Ch, Track>;
  events: Event[] = [];
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
    this.events.push({...e, f: this.t + dt} as Event);
    return this;
  }
  get(c: Ch) {
    return this.tracks[c].at(this.t);
  }
}

// Robot pose: (cx, cy) = axle centre (mm, rack frame), th = heading about +z (0 = facing the rack).
const RACK_AXLE = AXLE_Y; // docked at the rack
const SPARE_AXLE = -SPARE_D - AXLE_Y; // docked at the spare station (turned 180°)
const UNDOCK = 250;
export const HERO_TH = -0.75; // robot heading in the S3/S4 studio shots

// z_for(slot, h): slot B floor = Z, slot A floor = Z + 45; extract/insert 1 mm below the shelf floor.
const zFor = (slot: 'A' | 'B', h: number) => h - 1 - (slot === 'A' ? BAY_PITCH : 0);

export const STEPS = [
  'Fault: bay 2 SMART failure',
  'Drive to spare station',
  'Pick spare → slot A',
  'Drive to rack · dock',
  'Extract failed drive → slot B',
  'Insert spare into bay 2',
  'Return failed drive to RMA',
  'Dock · charge · job closed',
];

function build() {
  const s = new Script({cx: 0, cy: RACK_AXLE, th: 0, Z: Z_TRAVEL, Y: 0, fA: 0, fB: 0});

  // --- S3 reveal + S4 how-it-works: robot alone in the studio, centred at the origin of its own frame.
  s.goto(SCENES.reveal[0]).cut({cx: 0, cy: 0, th: -2.4});
  s.to(SCENES.reveal[1] - SCENES.reveal[0], {th: HERO_TH}, outCubic);
  // S4 a) drive: a short forward/back shuffle (heading stays fixed so the cameras can be robot-relative)
  s.goto(SCENES.how[0] + 20).to(30, {cy: 40}).to(34, {cy: 0});
  // b) Z lift sweep
  s.goto(SCENES.how[0] + 120).to(30, {Z: 295}).to(30, {Z: 120}).to(26, {Z: Z_TRAVEL});
  // c) Y extractor stroke
  s.goto(SCENES.how[0] + 220).to(34, {Y: Y_PULL}).wait(16).to(34, {Y: 0});
  // d) fingers
  s.goto(SCENES.how[0] + 320).to(12, {fB: 1}).wait(6).to(12, {fA: 1}).wait(18).to(12, {fB: 0}).wait(6).to(12, {fA: 0});

  // --- S5 the swap. Robot starts docked at the rack.
  const f0 = SCENES.swap[0];
  s.goto(f0).cut({cx: 0, cy: RACK_AXLE, th: 0, Z: Z_TRAVEL, Y: 0, fA: 0, fB: 0});
  s.ev({kind: 'step', step: 0}).ev({kind: 'bay', bay: 1, state: 'failed'}).ev({kind: 'light', light: 'red'});
  s.ev({kind: 'toast', text: 'Bay 2 · SMART fault → swap job queued', tone: 'warn'}, 8);
  s.wait(42);

  const drive = (fromAxle: number, toAxle: number, thFrom: number, thTo: number, dockTag: number) => {
    // undock (reverse 250), turn 180° in place, approach on the tag, funnel-dock
    const back = fromAxle + (thFrom === 0 ? -UNDOCK : UNDOCK);
    s.to(26, {cy: back});
    s.to(32, {th: thTo});
    s.ev({kind: 'tag', id: dockTag, on: true});
    s.to(30, {cy: toAxle}, inOut);
    s.ev({kind: 'tag', id: dockTag, on: false}).ev({kind: 'toast', text: 'Funnel docked · dock switch ✓', tone: 'ok'});
    s.wait(6);
  };
  const PI = Math.PI;

  // 1) to the spare station
  s.ev({kind: 'step', step: 1});
  drive(RACK_AXLE, SPARE_AXLE, 0, PI, 10);
  // 2) pick spare S1 into slot A (pull)
  s.ev({kind: 'step', step: 2});
  s.to(20, {Z: zFor('A', H_SPARE[0])});
  s.to(26, {Y: Y_PULL}).to(10, {fA: 1});
  s.ev({kind: 'caddy', id: 'spare', to: {mode: 'robot', slot: 'A'}});
  s.to(26, {Y: 0}).wait(4);
  // 3) back to the rack
  s.ev({kind: 'step', step: 3});
  s.to(16, {Z: Z_TRAVEL});
  s.goto(s.t - 16);
  drive(SPARE_AXLE, RACK_AXLE, PI, 2 * PI, 0);
  s.cut({th: 0});
  // 4) extract bay 2 into slot B: park A, pull with B, re-engage A
  s.ev({kind: 'step', step: 4});
  s.to(18, {Z: zFor('B', H_BAY[1])}).to(8, {fA: 0});
  s.ev({kind: 'toast', text: 'Camera: caddy tag ID matches job ✓', tone: 'ok'});
  s.to(24, {Y: Y_PULL}).to(10, {fB: 1});
  s.ev({kind: 'caddy', id: 'failed', to: {mode: 'robot', slot: 'B'}});
  s.to(24, {Y: 0}).to(8, {fA: 1});
  s.ev({kind: 'bay', bay: 1, state: 'empty'}).ev({kind: 'light', light: 'amber'});
  s.ev({kind: 'toast', text: 'PLC · Modbus: bay 2 empty', tone: 'info'});
  s.wait(4);
  // 5) insert the spare: slot A level with bay 2, park B, push with A, park A, re-engage B
  s.ev({kind: 'step', step: 5});
  s.to(16, {Z: zFor('A', H_BAY[1])}).to(8, {fB: 0});
  s.to(24, {Y: Y_PULL}).to(10, {fA: 0});
  s.ev({kind: 'caddy', id: 'spare', to: {mode: 'rack', bay: 1}});
  s.ev({kind: 'bay', bay: 1, state: 'new'}).ev({kind: 'light', light: 'green'});
  s.ev({kind: 'toast', text: 'PLC · Modbus: bay 2 occupied · new ID logged', tone: 'ok'});
  s.to(22, {Y: 0}).to(8, {fB: 1}).wait(6);
  // 6) return the failed drive to RMA (S2) with slot B
  s.ev({kind: 'step', step: 6});
  s.to(16, {Z: Z_TRAVEL});
  s.goto(s.t - 16);
  drive(RACK_AXLE, SPARE_AXLE, 0, PI, 10);
  s.to(18, {Z: zFor('B', H_SPARE[1])});
  s.to(24, {Y: Y_PULL}).to(10, {fB: 0});
  s.ev({kind: 'caddy', id: 'failed', to: {mode: 'spare', slot: 1}});
  s.to(22, {Y: 0});
  // 7) home and charge
  s.ev({kind: 'step', step: 7});
  s.to(16, {Z: Z_TRAVEL});
  s.goto(s.t - 16);
  drive(SPARE_AXLE, RACK_AXLE, PI, 2 * PI, 0);
  s.cut({th: 0});
  s.ev({kind: 'charge', on: true}).ev({kind: 'toast', text: 'PLC Y0: dock power on · charging', tone: 'ok'});
  s.ev({kind: 'toast', text: 'Job closed · cycle time + Wh logged', tone: 'ok'}, 24);
  return s;
}

const SCRIPT = build();
export const stepStart = (i: number) => SCRIPT.events.find((e) => e.kind === 'step' && e.step === i)!.f;
export const MISSION_END = SCRIPT.t;

const lastEvent = <K extends Event['kind']>(f: number, kind: K, pred: (e: Extract<Event, {kind: K}>) => boolean = () => true) => {
  let out: Extract<Event, {kind: K}> | undefined;
  for (const e of SCRIPT.events) if (e.kind === kind && e.f <= f && pred(e as Extract<Event, {kind: K}>)) out = e as Extract<Event, {kind: K}>;
  return out;
};

export type WorldState = {
  cx: number; cy: number; th: number; Z: number; Y: number; fA: number; fB: number;
  caddies: Record<CaddyId, CaddyMode>;
  bays: BayState[];
  light: Light;
  step: number;
  tag: number | null;
  charging: boolean;
};

export function stateAt(f: number): WorldState {
  const v = (c: Ch) => SCRIPT.tracks[c].at(f);
  const caddy = (id: CaddyId, init: CaddyMode) => lastEvent(f, 'caddy', (e) => e.id === id)?.to ?? init;
  const bays: BayState[] = [0, 1, 2, 3].map((b) => lastEvent(f, 'bay', (e) => e.bay === b)?.state ?? 'ok');
  const tagEv = lastEvent(f, 'tag');
  return {
    cx: v('cx'), cy: v('cy'), th: v('th'), Z: v('Z'), Y: v('Y'), fA: v('fA'), fB: v('fB'),
    caddies: {spare: caddy('spare', {mode: 'spare', slot: 0}), failed: caddy('failed', {mode: 'rack', bay: 1})},
    bays,
    light: lastEvent(f, 'light')?.light ?? (f < SCENES.swap[0] && f < SCENES.reveal[0] ? 'red' : 'green'),
    step: lastEvent(f, 'step')?.step ?? -1,
    tag: tagEv && tagEv.on ? tagEv.id : null,
    charging: lastEvent(f, 'charge')?.on ?? false,
  };
}

export const toasts = (f: number) =>
  SCRIPT.events.filter((e): e is Extract<Event, {kind: 'toast'}> => e.kind === 'toast' && e.f <= f && f - e.f < 75);
