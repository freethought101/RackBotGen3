// Camera for the technical film: one composed shot per scene (hard cut on the scene's first bar), a slow drift
// inside it. Studio shots are written in the robot's model frame (studio pose at the origin) so they stay locked
// to the subsystem they explain; floor shots are in world CAD mm.
import {SPARE_D, SPARE_X} from '../constants';
import {inOut} from '../engine';
import {clamp01, lerp, lerp3, robotToWorld, V3} from '../geom';
import {HERO_TH, stateAt, stepStart, TRIPS, TS} from './timeline';

export type Cam = {pos: V3; target: V3; fov: number};
type Key = {f: number; cam: Cam; follow?: boolean};

const HERO = {cx: 0, cy: 0, th: HERO_TH};
/** Truck sideways by k mm (k > 0 moves the subject right in frame, clearing room for text on the left). */
function pan(c: Cam, k: number): Cam {
  const dx = c.target[0] - c.pos[0];
  const dy = c.target[1] - c.pos[1];
  const n = Math.hypot(dx, dy) || 1;
  const r: V3 = [dy / n, -dx / n, 0];
  const off = (p: V3): V3 => [p[0] - r[0] * k, p[1] - r[1] * k, p[2]];
  return {pos: off(c.pos), target: off(c.target), fov: c.fov};
}
const rob = (pos: V3, target: V3, fov = 30, k = 0): Cam => pan({pos: robotToWorld(pos, HERO), target: robotToWorld(target, HERO), fov}, k);
const world = (pos: V3, target: V3, fov = 30, k = 0): Cam => pan({pos, target, fov}, k);
const atBase = (p: V3): V3 => [SPARE_X - p[0], -SPARE_D - p[1], p[2]];

/** Studio shot anchors, exported so overlays can project 3D callout anchors with the same camera. */
export const SHOT = {
  introA: rob([780, 520, 300], [0, -210, 250], 26, 200),
  introB: rob([1050, 760, 420], [0, -210, 240], 26, 230),
  anatomyA: rob([1650, 1150, 1000], [0, -220, 470], 32, 150),
  anatomyB: rob([1500, 1350, 950], [0, -220, 470], 32, 150),
  driveA: rob([1650, -60, 620], [0, -120, 170], 30, 40),
  driveB: rob([1600, -380, 650], [0, -120, 170], 30, 40),
  liftA: rob([900, 520, 420], [0, -230, 240], 30, 230),
  liftB: rob([860, 420, 620], [0, -230, 250], 30, 230),
  powerA: rob([-760, -1150, 980], [0, -280, 120], 30, 330),
  powerB: rob([-560, -1250, 920], [0, -280, 120], 30, 330),
  makeA: rob([1850, 1000, 1450], [0, -220, 330], 32, 380),
  makeB: rob([1700, 1250, 1350], [0, -220, 330], 32, 380),
};

function keys(): Key[] {
  const k: Key[] = [];
  const add = (f: number, c: Cam) => k.push({f, cam: c});
  const cut = (f: number, c: Cam) => add(f + 0.01, c);
  const follow = (f: number, pos: V3, target: V3, fov = 30) => k.push({f, cam: {pos, target, fov}, follow: true});

  add(TS.intro[0], SHOT.introA);
  add(TS.intro[1], SHOT.introB);
  // system: the whole floor, then settle
  const mid: V3 = [SPARE_X / 2, -SPARE_D / 2, 80];
  cut(TS.system[0], world([1000, -5600, 2500], [1300, -800, 520], 27, 0));
  add(TS.system[1], world([1350, -5300, 2250], [1300, -800, 520], 27, 0));
  cut(TS.anatomy[0], SHOT.anatomyA);
  add(TS.anatomy[1], SHOT.anatomyB);
  cut(TS.drive[0], SHOT.driveA);
  add(TS.drive[1], SHOT.driveB);
  cut(TS.lift[0], SHOT.liftA);
  add(TS.lift[1], SHOT.liftB);
  // extract: docked at the rack, from the finger side
  cut(TS.extract[0], world([1050, -620, 480], [40, -110, 210], 30, 150));
  add(TS.extract[1], world([980, -520, 520], [40, -110, 215], 30, 150));
  // vision: from behind and above the robot as it closes in on the funnel
  cut(TS.vision[0], world([620, -1500, 620], [0, -150, 200], 30, 220));
  add(TS.vision[1], world([480, -1050, 520], [0, -60, 210], 30, 220));
  cut(TS.power[0], SHOT.powerA);
  add(TS.power[1], SHOT.powerB);
  // safety: behind the rack (DIN rail), up toward the lamp box
  cut(TS.safety[0], world([-1000, 1300, 520], [-20, 150, 170], 30, 260));
  add(TS.safety[1], world([-650, 1450, 800], [10, 140, 230], 30, 260));

  // swap: same grammar as the pitch film (cuts on the robot's motion, slow drifts in between)
  const s = (i: number) => stepStart(i);
  const T = TRIPS;
  const c = (f: number) => f - 0.01;
  type Shot = [V3, V3, number, number];
  const wideA: Shot = [[-1500, -3300, 2400], mid, 34, 250];
  const wideB: Shot = [[4700, -200, 2300], mid, 34, 250];
  const rackClose: Shot = [[780, -380, 420], [30, -90, 215], 30, 150];
  const baseClose: Shot = [atBase([750, -340, 420]), atBase([30, -120, 180]), 30, 150];
  const drift = ([p, t, fov, kp]: Shot, d: V3): Shot => [[p[0] + d[0], p[1] + d[1], p[2] + d[2]], t, fov, kp];
  const w = ([p, t, fov, kp]: Shot) => world(p, t, fov, kp);
  const chaseA: [V3, V3, number] = [[700, -1250, 650], [-250, 0, 150], 30];
  const chaseB: [V3, V3, number] = [[-900, 1400, 1300], [-100, -100, 100], 32];
  cut(TS.swap[0], world([-760, 160, 330], [0, 70, 215], 28, 80));
  add(s(1) - 2, world([-680, 60, 310], [0, 70, 215], 28, 80));
  cut(s(1), w(baseClose));
  add(c(T[0] + 14), w(baseClose));
  add(T[0] + 14, w(wideA));
  add(c(T[0] + 84), w(drift(wideA, [450, 250, -150])));
  follow(T[0] + 84, ...chaseA);
  follow(c(T[0] + 148), ...chaseA);
  add(T[0] + 148, w(rackClose));
  add(s(5), world([740, -360, 420], [30, -90, 215], 30, 260));
  add(c(T[1] + 14), world([740, -360, 420], [30, -90, 215], 30, 260));
  add(T[1] + 14, w(wideB));
  add(c(T[1] + 84), w(drift(wideB, [-250, -450, -150])));
  follow(T[1] + 84, ...chaseB);
  follow(c(T[1] + 148), ...chaseB);
  add(T[1] + 148, w(baseClose));
  add(s(7), w(baseClose));
  add(TS.swap[1], world(atBase([1050, -700, 620]), atBase([30, -140, 170]), 30, 200));

  cut(TS.make[0], SHOT.makeA);
  add(TS.make[1], SHOT.makeB);
  // close: a high, slow orbit over the robot charging at its base
  cut(TS.close[0], world(atBase([1700, 500, 1300]), atBase([0, -380, 140]), 30, 0));
  add(TS.close[1], world(atBase([1100, -1500, 1450]), atBase([0, -380, 140]), 30, 0));
  return k.sort((x, y) => x.f - y.f);
}

const KEYS = keys();

function camOf(k: Key, f: number): Cam {
  if (!k.follow) return k.cam;
  const st = stateAt(f);
  const o = (p: V3): V3 => [p[0] + st.cx, p[1] + st.cy, p[2]];
  return {pos: o(k.cam.pos), target: o(k.cam.target), fov: k.cam.fov};
}

export function techCameraAt(f: number): Cam {
  if (f <= KEYS[0].f) return camOf(KEYS[0], f);
  for (let i = 1; i < KEYS.length; i++) {
    if (f < KEYS[i].f) {
      const a = camOf(KEYS[i - 1], f);
      const b = camOf(KEYS[i], f);
      const span = KEYS[i].f - KEYS[i - 1].f;
      const t = span < 0.1 ? 1 : inOut(clamp01((f - KEYS[i - 1].f) / span));
      return {pos: lerp3(a.pos, b.pos, t), target: lerp3(a.target, b.target, t), fov: lerp(a.fov, b.fov, t)};
    }
  }
  return camOf(KEYS[KEYS.length - 1], f);
}
