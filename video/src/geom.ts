// Frame helpers: CAD (mm, z up) <-> three.js (m, y up), robot model -> world.
import * as THREE from 'three';
import {AXLE_Y, SPARE_D, SPARE_X} from './constants';
import type {WorldState} from './anim';

export type V3 = [number, number, number];

/** CAD mm (x, y, z) -> three m. */
export const c3 = (x: number, y: number, z: number): V3 => [x / 1000, z / 1000, -y / 1000];

/** Robot model point (CAD mm, docked frame) -> world CAD mm, for a robot pose. */
export function robotToWorld(m: V3, s: Pick<WorldState, 'cx' | 'cy' | 'th'>): V3 {
  const dx = m[0];
  const dy = m[1] - AXLE_Y;
  const c = Math.cos(s.th);
  const sn = Math.sin(s.th);
  return [s.cx + c * dx - sn * dy, s.cy + sn * dx + c * dy, m[2]];
}

/** Spare-station local point (CAD mm) -> world CAD mm (station turned 180°, face at (SPARE_X, -SPARE_D)). */
export const spareToWorld = (m: V3): V3 => [SPARE_X - m[0], -SPARE_D - m[1], m[2]];

export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export const lerp3 = (a: V3, b: V3, t: number): V3 => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
export const clamp01 = (t: number) => Math.min(1, Math.max(0, t));

const tmpCam = new THREE.PerspectiveCamera();
/** Project a world CAD point (mm) to screen pixels for the given camera. */
export function project(p: V3, cam: {pos: V3; target: V3; fov: number}, w: number, h: number) {
  tmpCam.fov = cam.fov;
  tmpCam.aspect = w / h;
  tmpCam.near = 0.01;
  tmpCam.far = 50;
  tmpCam.position.set(...c3(...cam.pos));
  tmpCam.lookAt(new THREE.Vector3(...c3(...cam.target)));
  tmpCam.updateMatrixWorld();
  tmpCam.updateProjectionMatrix();
  const v = new THREE.Vector3(...c3(...p)).project(tmpCam);
  return {x: ((v.x + 1) / 2) * w, y: ((1 - v.y) / 2) * h, visible: v.z < 1};
}
