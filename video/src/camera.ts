// Camera path: a pure function of the frame. Positions are world CAD mm; S4 shots are written in the robot's
// model frame and mapped through the (fixed) studio pose so they stay locked to the part they explain.
import {HERO_TH, inOut, stateAt, stepStart, TRIPS} from './anim';
import {SCENES, SPARE_D, SPARE_X} from './constants';
import {clamp01, lerp, lerp3, robotToWorld, V3} from './geom';

export type Cam = {pos: V3; target: V3; fov: number};
type Key = {f: number; cam: Cam; follow?: boolean}; // follow: pos/target are offsets from the robot

const DIST = 1.0;

/** Truck the camera sideways by k mm (k > 0 moves the subject to the right of frame, clearing room for text). */
function pan(c: Cam, k: number): Cam {
  const dx = c.target[0] - c.pos[0];
  const dy = c.target[1] - c.pos[1];
  const n = Math.hypot(dx, dy) || 1;
  const r: V3 = [dy / n, -dx / n, 0]; // screen-right in the ground plane
  const off = (p: V3): V3 => [p[0] - r[0] * k, p[1] - r[1] * k, p[2]];
  return {pos: off(c.pos), target: off(c.target), fov: c.fov};
}
const HERO = {cx: 0, cy: 0, th: HERO_TH};
const rob = (pos: V3, target: V3, fov = 30, k = 0): Cam =>
  pan({pos: robotToWorld(pos, HERO), target: robotToWorld(target, HERO), fov}, k);

// S4 feature shots (robot model frame): drive, lift, extractor, fingers, vision, electronics.
export const HOW_SHOTS: Cam[] = [
  rob([650, 150, 200], [90, -150, 80], 32, 140),
  rob([800, 450, 560], [0, -190, 260], 30, 200),
  rob([850, -40, 420], [70, -130, 235], 28, 150),
  rob([300, 330, 560], [60, -190, 245], 26, 110),
  rob([-700, 450, 420], [-40, -60, 200], 32, -180),
  rob([450, -1050, 850], [-10, -330, 90], 30, 150),
];
export const HOW_LEN = 100;

function keys(): Key[] {
  const k: Key[] = [];
  // DIST pulls every shot back along its view line (one knob for overall framing).
  const add = (f: number, pos: V3, target: V3, fov = 30, kp = 0) =>
    k.push({f, cam: pan({pos: lerp3(target, pos, DIST), target, fov}, kp)});
  const follow = (f: number, pos: V3, target: V3, fov = 30) => k.push({f, cam: {pos, target, fov}, follow: true});
  const [h0, h1] = SCENES.hook;
  add(h0, [-1100, -900, 330], [-300, 40, 230], 30);
  add(h0 + 60, [-1000, -820, 310], [-250, 40, 225], 30);
  add(h1, [-260, -420, 260], [0, 40, 215], 28);
  add(h1 + 0.01, [900, -1000, 520], [0, 50, 200], 30);
  add(SCENES.problem[1], [700, -850, 430], [0, 50, 200], 30);
  // S3 turntable (robot spins, camera dollies in a little)
  const r0 = SCENES.reveal[0];
  add(r0 + 0.01, [1250, 1050, 540], [0, -60, 210], 28, 260);
  add(SCENES.reveal[1], [1100, 920, 460], [0, -60, 200], 28, 260);
  // S4 feature shots: hold, then a 30-frame move to the next
  HOW_SHOTS.forEach((c, i) => {
    const f = SCENES.how[0] + i * HOW_LEN;
    add(i === 0 ? f + 0.01 : f, c.pos, c.target, c.fov);
    add(f + HOW_LEN - 30, c.pos, c.target, c.fov);
  });
  add(SCENES.how[1], HOW_SHOTS[5].pos, HOW_SHOTS[5].target, HOW_SHOTS[5].fov);
  // S5 the swap: the robot lives at its base (the spare station) ~3.2 m down the aisle from the rack. Wide
  // shots show the whole floor; tracking shots ride along. Trip i = TRIPS[i]: 40 f reverse swing, 124 f aisle +
  // L turn + approach.
  const mid: V3 = [SPARE_X / 2, -SPARE_D / 2, 80];
  // a rack-frame point mirrored into the base's frame (the station faces the rack side, turned 180°)
  const atBase = (p: V3): V3 => [SPARE_X - p[0], -SPARE_D - p[1], p[2]];
  const wideA: [V3, V3, number, number] = [[-1500, -3300, 2400], mid, 34, 250];
  const wideB: [V3, V3, number, number] = [[4700, -200, 2300], mid, 34, 250];
  const rackClose: [V3, V3, number, number] = [[780, -380, 420], [30, -90, 215], 30, 150];
  const baseClose: [V3, V3, number, number] = [atBase([750, -340, 420]), atBase([30, -120, 180]), 30, 150];
  const s = (i: number) => stepStart(i);
  const T = TRIPS;
  // fault on the rack, then over to the robot waiting at its base
  add(s(0) + 0.01, [-760, 160, 330], [0, 70, 215], 28, 80);
  add(s(1) - 2, [-680, 60, 310], [0, 70, 215], 28, 80);
  add(s(1) + 0.01, ...baseClose);
  add(T[0] + 4, ...baseClose);
  // trip 1 → rack: establish the floor and the route, then track the robot through the L turn into the dock
  add(T[0] + 34, ...wideA);
  add(T[0] + 84, ...wideA);
  follow(T[0] + 120, [700, -1250, 650], [-250, 0, 150], 30);
  follow(T[0] + 150, [700, -1250, 650], [-250, 0, 150], 30);
  add(s(3) + 4, ...rackClose);
  add(s(5), [740, -360, 420], [30, -90, 215], 30, 260);
  // trip 2 → base: the other wide angle, then a high chase into the base dock
  add(T[1] + 34, ...wideB);
  add(T[1] + 80, ...wideB);
  follow(T[1] + 118, [-900, 1400, 1300], [-100, -100, 100], 32);
  follow(T[1] + 150, [-900, 1400, 1300], [-100, -100, 100], 32);
  add(s(6) + 6, ...baseClose);
  add(s(7), ...baseClose);
  add(SCENES.swap[1], atBase([-900, -380, 520]), atBase([0, -160, 160]), 30, 260);
  // S6 Delta inside: behind the rack (PSU, PLC, router on the DIN rail), then up to the tower light
  const d0 = SCENES.delta[0];
  add(d0 + 0.01, [-800, 1000, 360], [-40, 170, 110], 30, 140);
  add(d0 + 170, [-550, 900, 450], [-30, 160, 150], 30, 150);
  add(SCENES.delta[1], [500, 1050, 800], [20, 100, 280], 32, 170);
  // S7 close: a high orbit over the robot charging at its base
  const c0 = SCENES.close[0];
  add(c0 + 0.01, atBase([1800, 450, 1400]), atBase([0, -380, 120]), 30, 650);
  add(SCENES.close[1], atBase([1000, -1900, 1500]), atBase([0, -380, 120]), 30, 650);
  return k.sort((a, b) => a.f - b.f);
}

const KEYS = keys();

/** A key's camera at frame f (follow keys ride along with the robot's current position). */
function camOf(k: Key, f: number): Cam {
  if (!k.follow) return k.cam;
  const st = stateAt(f);
  const o = (p: V3): V3 => [p[0] + st.cx, p[1] + st.cy, p[2]];
  return {pos: o(k.cam.pos), target: o(k.cam.target), fov: k.cam.fov};
}

export function cameraAt(f: number): Cam {
  if (f <= KEYS[0].f) return camOf(KEYS[0], f);
  for (let i = 1; i < KEYS.length; i++) {
    const b0 = KEYS[i];
    if (f < b0.f) {
      const a = {...KEYS[i - 1], cam: camOf(KEYS[i - 1], f)};
      const b = {...b0, cam: camOf(b0, f)};
      const t = b.f - a.f < 0.1 ? 1 : inOut(clamp01((f - a.f) / (b.f - a.f)));
      return {pos: lerp3(a.cam.pos, b.cam.pos, t), target: lerp3(a.cam.target, b.cam.target, t), fov: lerp(a.cam.fov, b.cam.fov, t)};
    }
  }
  return camOf(KEYS[KEYS.length - 1], f);
}

export {stateAt};
