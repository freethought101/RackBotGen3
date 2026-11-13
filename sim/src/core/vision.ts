// Vision (03 §6): which AprilTags the tray camera can decode, the station tag pose for the approach controller,
// and approach_step() ported from rackbot/vision.py.
//
// A tag counts as detected when all four corners land in the 640×480 frame, it faces the camera within 60° and
// its side is at least MIN_PX pixels. The pose handed to the controller is relative to the station centre line,
// as SimVision does (the real code gets there from the tag pose plus the known tag offset).
import {AP, CAM_H, CAM_HFOV, CAM_LENS, CAM_W, TAG_APPROACH, TAG_BAY, TAG_CADDY, TAG_FACE_Y} from './spec.ts';
import {deg, fwd, robotToWorld, toWorld, wrap, type Pose, type Station} from './layout.ts';
import type {World} from './world.ts';

export type TagPose = {id: number; d: number; x: number; theta: number; psi: number};
export type ApproachCmd = {v: number; w: number; handoff: boolean; tooClose: boolean};
export type TagKind = 'approach' | 'shelf' | 'caddy';
export type Tag = {id: number; kind: TagKind; size: number; c: [number, number, number]; st: Station};
export type Detection = {id: number; kind: TagKind; px: [number, number][]; dist: number; center: [number, number, number]};

const MIN_PX = 8;
const F = CAM_W / 2 / Math.tan(((CAM_HFOV / 2) * Math.PI) / 180);
export const CAM_VFOV = (2 * Math.atan(CAM_H / 2 / F) * 180) / Math.PI;

export function approachStep(p: TagPose): ApproachCmd {
  if (p.d < AP.handoff_d && Math.abs(p.x) < AP.handoff_x && Math.abs(p.psi) < AP.handoff_psi) return {v: 0, w: 0, handoff: true, tooClose: false};
  if (p.d < AP.abort_d) return {v: 0, w: 0, handoff: false, tooClose: true};
  const w = -AP.k_theta * p.theta - AP.k_psi * p.psi;
  const v = Math.min(Math.max(AP.k_d * (p.d - AP.d_target), AP.v_min), AP.v_max);
  return {v, w, handoff: false, tooClose: false};
}

/** Every tag in the scene: approach fins, shelf strips and the caddy faces on the shelves (station-local centres). */
export function allTags(world: World): Tag[] {
  const out: Tag[] = [];
  for (const st of world.stations) {
    out.push({id: st.tag, kind: 'approach', size: TAG_APPROACH.size, c: [TAG_APPROACH.x, TAG_FACE_Y - 0.3, TAG_APPROACH.z], st});
    st.shelves.forEach((h, i) => {
      out.push({id: st.kind === 'rack' ? i + 1 : 11 + i, kind: 'shelf', size: TAG_BAY.size, c: [TAG_BAY.x, TAG_FACE_Y - 0.3, h + TAG_BAY.dz], st});
      const cid = world.at(st.id, i);
      if (cid !== null) out.push({id: cid, kind: 'caddy', size: TAG_CADDY.size, c: [TAG_CADDY.x, TAG_CADDY.y, h + TAG_CADDY.dz], st});
    });
  }
  return out;
}

export class Camera {
  lens: [number, number, number] = [0, 0, 0];
  f: [number, number] = [0, 1];
  r: [number, number] = [1, 0];

  constructor(pose: Pose, Z: number) {
    const [x, y] = robotToWorld(pose, CAM_LENS.x, CAM_LENS.y);
    this.lens = [x, y, Z + CAM_LENS.dz];
    this.f = fwd(pose.th);
    this.r = [this.f[1], -this.f[0]];
  }

  project(p: [number, number, number]): [number, number] | null {
    const v = [p[0] - this.lens[0], p[1] - this.lens[1], p[2] - this.lens[2]];
    const zc = v[0] * this.f[0] + v[1] * this.f[1];
    if (zc < 10) return null;
    const xc = v[0] * this.r[0] + v[1] * this.r[1];
    return [CAM_W / 2 + (F * xc) / zc, CAM_H / 2 - (F * v[2]) / zc];
  }

  detect(tag: Tag): Detection | null {
    const {st, size, c} = tag;
    const h = size / 2;
    const corners: [number, number, number][] = [[-h, h], [h, h], [h, -h], [-h, -h]].map(([dx, dz]) => {
      const [x, y] = toWorld(st, c[0] + dx, c[1]);
      return [x, y, c[2] + dz];
    });
    // tag normal points out of the station (local -y)
    const [cx, cy] = toWorld(st, c[0], c[1]);
    const nx = Math.sin(st.phi);
    const ny = -Math.cos(st.phi);
    const tx = this.lens[0] - cx;
    const ty = this.lens[1] - cy;
    const tz = this.lens[2] - c[2];
    const dist = Math.hypot(tx, ty, tz);
    if ((nx * tx + ny * ty) / dist < Math.cos((60 * Math.PI) / 180)) return null;
    const px: [number, number][] = [];
    for (const k of corners) {
      const q = this.project(k);
      if (!q || q[0] < 0 || q[0] > CAM_W || q[1] < 0 || q[1] > CAM_H) return null;
      px.push(q);
    }
    const side = Math.min(...px.map((a, i) => Math.hypot(a[0] - px[(i + 1) % 4][0], a[1] - px[(i + 1) % 4][1])));
    if (side < MIN_PX) return null;
    return {id: tag.id, kind: tag.kind, px, dist, center: [cx, cy, c[2]]};
  }
}

export function detections(world: World, pose: Pose, Z: number, blocked: boolean): Detection[] {
  if (blocked) return [];
  const cam = new Camera(pose, Z);
  const out: Detection[] = [];
  for (const t of allTags(world)) {
    const d = cam.detect(t);
    if (d) out.push(d);
  }
  return out;
}

/** Station approach-tag pose for the controller, or null when the camera cannot decode it. */
export function findTag(world: World, st: Station, pose: Pose, Z: number, blocked: boolean): TagPose | null {
  if (blocked) return null;
  const tag = allTags(world).find((t) => t.kind === 'approach' && t.st === st)!;
  if (!new Camera(pose, Z).detect(tag)) return null;
  const [px, py] = robotToWorld(pose, 0, CAM_LENS.y);
  const [tx, ty] = toWorld(st, 0, TAG_FACE_Y);
  const f = fwd(pose.th);
  const vx = tx - px;
  const vy = ty - py;
  const d = vx * f[0] + vy * f[1];
  const x = vx * f[1] - vy * f[0];
  return {id: st.tag, d, x, theta: deg(Math.atan2(x, d)), psi: deg(wrap(pose.th - st.phi))};
}
