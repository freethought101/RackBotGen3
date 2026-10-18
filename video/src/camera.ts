// Camera path: a pure function of the frame. Positions are world CAD mm; S4 shots are written in the robot's
// model frame and mapped through the (fixed) studio pose so they stay locked to the part they explain.
import {HERO_TH, inOut, stateAt, stepStart} from './anim';
import {SCENES} from './constants';
import {clamp01, lerp, lerp3, robotToWorld, V3} from './geom';

export type Cam = {pos: V3; target: V3; fov: number};
type Key = {f: number; cam: Cam};

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
  // S5 the swap
  const wide: [V3, V3, number, number] = [[1700, -400, 1100], [0, -400, 150], 30, 300];
  const rackClose: [V3, V3, number, number] = [[780, -380, 420], [30, -90, 215], 30, 150];
  const spareClose: [V3, V3, number, number] = [[-750, -420, 420], [-30, -640, 180], 30, 150];
  const s = (i: number) => stepStart(i);
  add(s(0) + 0.01, [-760, 160, 330], [0, 70, 215], 28, 80);
  add(s(1) - 2, [-680, 60, 310], [0, 70, 215], 28, 80);
  add(s(1) + 20, ...wide);
  add(s(2) - 16, ...wide);
  add(s(2) + 6, ...spareClose);
  add(s(3), ...spareClose);
  add(s(3) + 24, ...wide);
  add(s(4) - 14, ...wide);
  add(s(4) + 8, ...rackClose);
  add(s(6), [740, -360, 420], [30, -90, 215], 30, 260);
  add(s(6) + 26, [1700, -350, 1100], [0, -420, 150], 30, 260);
  add(s(7) - 10, [-1650, -460, 1050], [0, -420, 150], 30, 260);
  add(s(7) + 40, [-1500, -300, 900], [0, -330, 150], 30, 260);
  add(SCENES.swap[1], [-900, -380, 520], [0, -160, 160], 30, 260);
  // S6 Delta inside: behind the rack (PSU, PLC, router on the DIN rail), then up to the tower light
  const d0 = SCENES.delta[0];
  add(d0 + 0.01, [-800, 1000, 360], [-40, 170, 110], 30, 140);
  add(d0 + 170, [-550, 900, 450], [-30, 160, 150], 30, 150);
  add(SCENES.delta[1], [500, 1050, 800], [20, 100, 280], 32, 170);
  // S7 close: a high orbit over the whole arena
  const c0 = SCENES.close[0];
  add(c0 + 0.01, [1800, 450, 1400], [0, -380, 120], 30, 650);
  add(SCENES.close[1], [1000, -1900, 1500], [0, -380, 120], 30, 650);
  return k.sort((a, b) => a.f - b.f);
}

const KEYS = keys();

export function cameraAt(f: number): Cam {
  if (f <= KEYS[0].f) return KEYS[0].cam;
  for (let i = 1; i < KEYS.length; i++) {
    const b = KEYS[i];
    if (f < b.f) {
      const a = KEYS[i - 1];
      const t = b.f - a.f < 0.1 ? 1 : inOut(clamp01((f - a.f) / (b.f - a.f)));
      return {pos: lerp3(a.cam.pos, b.cam.pos, t), target: lerp3(a.cam.target, b.cam.target, t), fov: lerp(a.cam.fov, b.cam.fov, t)};
    }
  }
  return KEYS[KEYS.length - 1].cam;
}

export {stateAt};
