// CORVIN technical film (150 s @ 30 fps, cuts on 120 BPM bars = 60 frames): scene table, the robot script and
// the derived per-frame state. Same conventions as anim.ts: (cx, cy) axle centre in world CAD mm, th heading about
// +z (0 = facing the rack, forward = (-sin th, cos th)).
import {AXLE_Y, BAY_PITCH, H_BAY, H_SPARE, SPARE_D, SPARE_X, TURN_R, Y_PULL, Z_TRAVEL} from '../constants';
import {Ch, inOut, linear, outCubic, Script, Track} from '../engine';
import {V3} from '../geom';

export const T_FPS = 30;
export const T_TOTAL = 4500;

export const TS = {
  intro: [0, 240],
  system: [240, 600],
  anatomy: [600, 840],
  drive: [840, 1200],
  lift: [1200, 1620],
  extract: [1620, 2040],
  vision: [2040, 2400],
  power: [2400, 2940],
  safety: [2940, 3240],
  swap: [3240, 4140],
  make: [4140, 4320],
  close: [4320, 4500],
} as const;
export type SceneId = keyof typeof TS;

/** Scenes shot in the studio (robot alone at the origin); the rest play on the rack / base-station floor. */
export const STUDIO: SceneId[] = ['intro', 'anatomy', 'drive', 'lift', 'power', 'make'];
export const sceneAt = (f: number): SceneId => (Object.keys(TS) as SceneId[]).find((k) => f >= TS[k][0] && f < TS[k][1]) ?? 'close';
export const inStudio = (f: number) => STUDIO.includes(sceneAt(f));

export type CaddyId = 'spare' | 'failed';
export type CaddyMode = {mode: 'rack'; bay: number} | {mode: 'spare'; slot: number} | {mode: 'robot'; slot: 'A' | 'B'};
export type BayState = 'ok' | 'failed' | 'empty' | 'new';
export type Light = 'green' | 'amber' | 'red';
export type Tone = 'info' | 'ok' | 'warn';

type Event =
  | {f: number; kind: 'caddy'; id: CaddyId; to: CaddyMode}
  | {f: number; kind: 'step'; step: number}
  | {f: number; kind: 'bay'; bay: number; state: BayState}
  | {f: number; kind: 'light'; light: Light}
  | {f: number; kind: 'toast'; text: string; tone: Tone}
  | {f: number; kind: 'tag'; id: number; on: boolean}
  | {f: number; kind: 'charge'; on: boolean}
  | {f: number; kind: 'sfx'; id: string};

export const HERO_TH = -0.55; // studio heading: front three-quarter from the default camera side
const RACK_AXLE = AXLE_Y;
const BASE_AXLE = -SPARE_D - AXLE_Y;
const UNDOCK = 150;
const APPROACH = SPARE_D - 2 * -AXLE_Y - UNDOCK - 2 * TURN_R; // 800 mm
const ARC = (TURN_R * Math.PI) / 2;
export const zFor = (slot: 'A' | 'B', h: number) => h - 1 - (slot === 'A' ? BAY_PITCH : 0);

export const STEPS = [
  'Fault: bay 2 SMART failure',
  'Pick spare at base → slot A',
  'Drive to rack · dock',
  'Extract failed drive → slot B',
  'Insert spare into bay 2',
  'Drive back to base station',
  'Failed drive → RMA slot',
  'Dock · charge · job closed',
];

const HOME = {spare: {mode: 'spare', slot: 0}, failed: {mode: 'rack', bay: 1}} as const;

function build() {
  const s = new Script<Event>({cx: 0, cy: 0, th: -2.6, Z: Z_TRAVEL, Y: 0, fA: 0, fB: 0});
  const studio = (th = HERO_TH) => s.cut({cx: 0, cy: 0, th, Z: Z_TRAVEL, Y: 0, fA: 0, fB: 0});
  const caddiesHome = () => {
    s.ev({kind: 'caddy', id: 'spare', to: HOME.spare}).ev({kind: 'caddy', id: 'failed', to: HOME.failed});
    s.ev({kind: 'bay', bay: 1, state: 'ok'}).ev({kind: 'light', light: 'green'});
  };

  // intro: slow turntable reveal
  s.goto(TS.intro[0]);
  s.to(TS.intro[1], {th: HERO_TH}, outCubic);

  // system: robot waits docked and charging at its base, down the aisle from the rack
  s.goto(TS.system[0]).cut({cx: SPARE_X, cy: BASE_AXLE, th: -Math.PI});
  s.ev({kind: 'charge', on: true});

  // anatomy: back in the studio (exploded by the explode track below)
  s.goto(TS.anatomy[0]);
  studio();
  s.ev({kind: 'charge', on: false});

  // drive: forward, spin in place (differential), spin back, reverse
  s.goto(TS.drive[0] + 40);
  s.ev({kind: 'sfx', id: 'drive'});
  s.path(55, [{d: 170}]);
  s.wait(14);
  s.to(54, {th: HERO_TH + Math.PI / 2});
  s.wait(12);
  s.to(54, {th: HERO_TH});
  s.wait(8);
  s.path(55, [{d: -170}]);

  // lift: both caddies on the tray (slot B low, slot A 45 mm above), full Z sweep
  s.goto(TS.lift[0]);
  studio();
  s.cut({fA: 1, fB: 1});
  s.ev({kind: 'caddy', id: 'spare', to: {mode: 'robot', slot: 'A'}}).ev({kind: 'caddy', id: 'failed', to: {mode: 'robot', slot: 'B'}});
  s.goto(TS.lift[0] + 50).to(70, {Z: 295}).wait(24).to(80, {Z: 102}).wait(20).to(56, {Z: Z_TRAVEL});

  // extract: docked at the rack, pull the bay 2 caddy into slot B and push it back
  s.goto(TS.extract[0]);
  s.cut({cx: 0, cy: RACK_AXLE, th: 0, Z: zFor('B', H_BAY[1]), Y: 0, fA: 0, fB: 0});
  caddiesHome();
  s.goto(TS.extract[0] + 50);
  s.to(36, {Y: Y_PULL}).to(12, {fB: 1});
  s.ev({kind: 'caddy', id: 'failed', to: {mode: 'robot', slot: 'B'}});
  s.to(38, {Y: 0}).wait(26);
  s.to(38, {Y: Y_PULL});
  s.ev({kind: 'caddy', id: 'failed', to: {mode: 'rack', bay: 1}});
  s.to(12, {fB: 0}).to(32, {Y: 0}).wait(16);
  // one visit: the lift puts slot A level with the same bay
  s.to(44, {Z: zFor('A', H_BAY[1])}).wait(30).to(40, {Z: zFor('B', H_BAY[1])});

  // vision: back off 700 mm, then the tag-guided approach into the funnel
  s.goto(TS.vision[0]);
  s.cut({cx: 0, cy: RACK_AXLE - 700, th: 0, Z: Z_TRAVEL, Y: 0, fA: 0, fB: 0});
  s.ev({kind: 'tag', id: 0, on: true}, 30);
  s.goto(TS.vision[0] + 50);
  s.ev({kind: 'sfx', id: 'drive'});
  s.path(200, [{d: 700}], (t) => outCubic(t));
  s.ev({kind: 'tag', id: 0, on: false}).ev({kind: 'sfx', id: 'dock'});

  // power: studio, robot still
  s.goto(TS.power[0]);
  studio(HERO_TH);

  // safety: robot docked at the rack; the rack E-stop is pressed and released
  s.goto(TS.safety[0]);
  s.cut({cx: 0, cy: RACK_AXLE, th: 0, Z: Z_TRAVEL, Y: 0, fA: 0, fB: 0});
  s.ev({kind: 'light', light: 'green'});
  s.ev({kind: 'light', light: 'red'}, 150).ev({kind: 'sfx', id: 'estop'}, 150);
  s.ev({kind: 'light', light: 'green'}, 236);

  // swap: the full mission, starting docked and charging at the base
  const f0 = TS.swap[0];
  s.goto(f0).cut({cx: SPARE_X, cy: BASE_AXLE, th: -Math.PI, Z: Z_TRAVEL, Y: 0, fA: 0, fB: 0});
  caddiesHome();
  s.ev({kind: 'charge', on: true});
  s.ev({kind: 'step', step: 0}).ev({kind: 'bay', bay: 1, state: 'failed'}).ev({kind: 'light', light: 'red'});
  s.ev({kind: 'toast', text: 'Bay 2 · SMART fault → swap job queued', tone: 'warn'}, 8);
  s.wait(54);
  const drive = (dockTag: number) => {
    const PI = Math.PI;
    s.ev({kind: 'sfx', id: 'drive'});
    s.path(40, [{d: -UNDOCK}, {d: -ARC, dth: -PI / 2}]);
    s.ev({kind: 'toast', text: dockTag === 10 ? 'Route: aisle → L turn → base station' : 'Route: aisle → L turn → rack', tone: 'info'});
    s.ev({kind: 'tag', id: dockTag, on: true}, 92);
    s.path(124, [{d: SPARE_X}, {d: ARC, dth: -PI / 2}, {d: APPROACH}]);
    s.ev({kind: 'tag', id: dockTag, on: false}).ev({kind: 'toast', text: 'Funnel docked · dock switch ✓', tone: 'ok'}).ev({kind: 'sfx', id: 'dock'});
    s.wait(6);
  };
  s.ev({kind: 'step', step: 1});
  s.to(20, {Z: zFor('A', H_SPARE[0])});
  s.to(26, {Y: Y_PULL}).to(10, {fA: 1});
  s.ev({kind: 'caddy', id: 'spare', to: {mode: 'robot', slot: 'A'}});
  s.to(26, {Y: 0}).wait(4);
  s.ev({kind: 'step', step: 2}).ev({kind: 'charge', on: false});
  s.to(16, {Z: Z_TRAVEL});
  s.goto(s.t - 16);
  drive(0);
  s.cut({th: 0});
  s.ev({kind: 'step', step: 3});
  s.to(18, {Z: zFor('B', H_BAY[1])}).to(8, {fA: 0});
  s.ev({kind: 'toast', text: 'Camera: caddy tag ID matches job ✓', tone: 'ok'}).ev({kind: 'sfx', id: 'lock'});
  s.to(24, {Y: Y_PULL}).to(10, {fB: 1});
  s.ev({kind: 'caddy', id: 'failed', to: {mode: 'robot', slot: 'B'}});
  s.to(24, {Y: 0}).to(8, {fA: 1});
  s.ev({kind: 'bay', bay: 1, state: 'empty'}).ev({kind: 'light', light: 'amber'});
  s.ev({kind: 'toast', text: 'Rack controller · Modbus: bay 2 empty', tone: 'info'});
  s.wait(4);
  s.ev({kind: 'step', step: 4});
  s.to(16, {Z: zFor('A', H_BAY[1])}).to(8, {fB: 0});
  s.to(24, {Y: Y_PULL});
  s.ev({kind: 'caddy', id: 'spare', to: {mode: 'rack', bay: 1}});
  s.to(10, {fA: 0});
  s.ev({kind: 'bay', bay: 1, state: 'new'}).ev({kind: 'light', light: 'green'});
  s.ev({kind: 'toast', text: 'Modbus: bay 2 occupied · new ID logged', tone: 'ok'});
  s.to(22, {Y: 0}).to(8, {fB: 1}).wait(6);
  s.ev({kind: 'step', step: 5});
  s.to(16, {Z: Z_TRAVEL});
  s.goto(s.t - 16);
  drive(10);
  s.ev({kind: 'step', step: 6});
  s.to(18, {Z: zFor('B', H_SPARE[1])});
  s.to(24, {Y: Y_PULL});
  s.ev({kind: 'caddy', id: 'failed', to: {mode: 'spare', slot: 1}});
  s.to(10, {fB: 0});
  s.to(22, {Y: 0});
  s.ev({kind: 'step', step: 7});
  s.to(16, {Z: Z_TRAVEL});
  s.ev({kind: 'charge', on: true}).ev({kind: 'toast', text: 'Docked at base · charging', tone: 'ok'}).ev({kind: 'sfx', id: 'charge'});
  s.ev({kind: 'toast', text: 'Job closed · cycle time + Wh logged', tone: 'ok'}, 24).ev({kind: 'sfx', id: 'done'}, 24);
  const missionEnd = s.t;

  // make: studio, exploded flat-pack
  s.goto(TS.make[0]);
  studio(HERO_TH);
  s.ev({kind: 'charge', on: false});
  caddiesHome();
  s.ev({kind: 'caddy', id: 'spare', to: {mode: 'spare', slot: 0}});

  // close: docked and charging at the base, both drives where the mission left them
  s.goto(TS.close[0]).cut({cx: SPARE_X, cy: BASE_AXLE, th: -Math.PI});
  s.ev({kind: 'charge', on: true});
  s.ev({kind: 'caddy', id: 'spare', to: {mode: 'rack', bay: 1}}).ev({kind: 'caddy', id: 'failed', to: {mode: 'spare', slot: 1}});
  s.ev({kind: 'bay', bay: 1, state: 'ok'});
  return {s, missionEnd};
}

const BUILT = build();
const SCRIPT = BUILT.s;
export const MISSION_END = BUILT.missionEnd;
export const EVENTS = SCRIPT.events;
export const stepStart = (i: number) => SCRIPT.events.find((e) => e.kind === 'step' && e.step === i)!.f;
export const ROUTES = SCRIPT.routes.filter((r) => r.f0 >= TS.swap[0]).filter((_, i) => i % 2 === 1);
export const TRIPS = SCRIPT.routes.filter((r) => r.f0 >= TS.swap[0]).map((r) => r.f0).filter((_, i) => i % 2 === 0);

// Exploded-view offsets in the robot model frame (CAD mm), scaled by the explode track.
// The chassis stays on the floor; everything else lifts away from it in layers.
export const EXPLODE: Record<string, V3> = {
  chassis: [0, 0, 0], nose: [0, 130, 0],
  wheel_left: [-150, 0, 0], wheel_right: [150, 0, 0],
  drive_motor_left: [-80, 0, 70], drive_motor_right: [80, 0, 70],
  power: [-140, -100, 100], electronics: [140, -130, 100],
  mast: [0, -20, 180], zdrive: [-120, -70, 190],
  zcarriage: [0, 30, 280], tray: [0, 120, 310], camera: [-150, 110, 320], yrail: [140, 40, 350],
  ycarriage: [180, 50, 400], servo_a: [225, 50, 410], servo_b: [225, 50, 410], finger: [225, 50, 410],
};

// ---- extra tracks: explode amount and the per-scene focus ---------------------------------------------------
function keys(k: [number, number][], e = inOut) {
  const t = new Track();
  t.push(k[0][0], k[0][1], linear);
  for (const [f, v] of k.slice(1)) t.push(f, v, e);
  return t;
}
const a = TS.anatomy[0];
const m = TS.make[0];
const EXPLODE_TRACK = keys([
  [0, 0], [a + 24, 0], [a + 70, 1], [a + 196, 1], [a + 236, 0],
  [m + 6, 0], [m + 50, 1.35], [m + 140, 1.35], [m + 176, 0],
]);
export const explodeAt = (f: number) => EXPLODE_TRACK.at(f);

/** Subsystem groups emphasised in each scene (the rest of the robot is ghosted). */
export const FOCUS: Partial<Record<SceneId, string[]>> = {
  drive: ['wheel_left', 'wheel_right', 'drive_motor_left', 'drive_motor_right', 'chassis'],
  lift: ['mast', 'zdrive', 'zcarriage', 'tray', 'caddy'],
  extract: ['yrail', 'ycarriage', 'servo_a', 'servo_b', 'finger', 'tray', 'caddy'],
  vision: ['camera', 'nose'],
  power: ['power', 'electronics'],
};
/** 0..1 focus strength at frame f (eases in after a scene starts, out before it ends). */
export function focusAt(f: number): {groups: string[]; k: number} {
  const id = sceneAt(f);
  const groups = FOCUS[id];
  if (!groups) return {groups: [], k: 0};
  const [s0, s1] = TS[id];
  const k = Math.min(1, Math.max(0, Math.min((f - s0 - 20) / 24, (s1 - 8 - f) / 16)));
  return {groups, k: inOut(k)};
}

// ---- state -----------------------------------------------------------------------------------------------
const lastEvent = <K extends Event['kind']>(f: number, kind: K, pred: (e: Extract<Event, {kind: K}>) => boolean = () => true) => {
  let out: Extract<Event, {kind: K}> | undefined;
  for (const e of SCRIPT.events) if (e.kind === kind && e.f <= f && pred(e as Extract<Event, {kind: K}>)) out = e as Extract<Event, {kind: K}>;
  return out;
};

export type TechState = {
  cx: number; cy: number; th: number; Z: number; Y: number; fA: number; fB: number;
  caddies: Record<CaddyId, CaddyMode>;
  bays: BayState[];
  light: Light;
  step: number;
  tag: number | null;
  charging: boolean;
  wheelL: number;
  wheelR: number;
};

// Wheel angles: integrate the axle motion frame by frame (skipping cuts), 80 mm wheels at x = ±137 mm.
const WHEEL_R = 40;
const HALF_TRACK = 137;
const WHEELS: [number, number][] = (() => {
  const v = (c: Ch, f: number) => SCRIPT.tracks[c].at(f);
  const out: [number, number][] = [[0, 0]];
  let [l, r] = [0, 0];
  for (let f = 1; f <= T_TOTAL; f++) {
    const dx = v('cx', f) - v('cx', f - 1);
    const dy = v('cy', f) - v('cy', f - 1);
    let dth = v('th', f) - v('th', f - 1);
    const th = v('th', f);
    if (Math.hypot(dx, dy) < 60 && Math.abs(dth) < 0.2) {
      const ds = dx * -Math.sin(th) + dy * Math.cos(th);
      l += (ds - dth * HALF_TRACK) / WHEEL_R;
      r += (ds + dth * HALF_TRACK) / WHEEL_R;
    } else dth = 0;
    out.push([l, r]);
  }
  return out;
})();

export function stateAt(f: number): TechState {
  const v = (c: Ch) => SCRIPT.tracks[c].at(f);
  const caddy = (id: CaddyId) => lastEvent(f, 'caddy', (e) => e.id === id)?.to ?? HOME[id];
  const bays: BayState[] = [0, 1, 2, 3].map((b) => lastEvent(f, 'bay', (e) => e.bay === b)?.state ?? 'ok');
  const tagEv = lastEvent(f, 'tag');
  const fi = Math.max(0, Math.min(T_TOTAL, Math.floor(f)));
  return {
    cx: v('cx'), cy: v('cy'), th: v('th'), Z: v('Z'), Y: v('Y'), fA: v('fA'), fB: v('fB'),
    caddies: {spare: caddy('spare'), failed: caddy('failed')},
    bays,
    light: lastEvent(f, 'light')?.light ?? 'green',
    step: f >= TS.swap[0] && f < TS.swap[1] ? lastEvent(f, 'step')?.step ?? -1 : -1,
    tag: tagEv && tagEv.on ? tagEv.id : null,
    charging: lastEvent(f, 'charge')?.on ?? false,
    wheelL: WHEELS[fi][0],
    wheelR: WHEELS[fi][1],
  };
}

export const toasts = (f: number) =>
  SCRIPT.events.filter((e): e is Extract<Event, {kind: 'toast'}> => e.kind === 'toast' && e.f <= f && f - e.f < 75 && f < TS.swap[1]);

/** Raw channel value at frame f (for deriving sound cues from motion). */
export const sampleChannel = (c: Ch, f: number) => SCRIPT.tracks[c].at(f);
