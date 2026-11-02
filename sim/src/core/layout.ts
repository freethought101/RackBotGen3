// Scene presets: where the racks and the spare station (home, charging dock) stand, and how the robot drives
// between them. World frame = CAD mm, z up. A station's local frame is the docked-at-rack frame of spec.ts
// (rack face at y = 0, robot on the -y side), rotated by `phi` and moved to (x, y).
import {AXLE_Y, AP, H_BAY, H_SPARE} from './spec.ts';

export type StationKind = 'rack' | 'spare';
export type Station = {
  id: string; // "R1".."R4" | "home"
  kind: StationKind;
  label: string;
  x: number;
  y: number;
  phi: number; // rad; also the robot heading when docked here
  tag: number; // approach tag ID
  shelves: number[]; // shelf floor heights
};

export type Preset = {
  id: 'hall' | 'arena';
  title: string;
  note: string;
  stations: Station[];
  /** Hall routing: robot backs out to this lane (world y) and drives along it. null = arena (undock + TURN 180). */
  laneY: number | null;
  randomFaultMeanS: number; // mean time between random drive failures (simulated)
};

const rack = (i: number, x: number, tag: number): Station => ({
  id: `R${i + 1}`, kind: 'rack', label: `Rack ${i + 1}`, x, y: 0, phi: 0, tag, shelves: H_BAY,
});
const home = (x: number, d: number): Station => ({
  id: 'home', kind: 'spare', label: 'Spare station', x, y: -d, phi: Math.PI, tag: 10, shelves: H_SPARE,
});

/** The competition table (00-overview §5): one 1×4 rack and the spare station facing it ~700 mm away. */
const ARENA: Preset = {
  id: 'arena',
  title: 'Competition arena',
  note: 'The real demo setup: 1 rack × 4 bays, spare station 700 mm across (00-overview §5)',
  stations: [rack(0, 0, 0), home(0, 700)],
  laneY: null,
  randomFaultMeanS: 240,
};

/** Scaled concept of a data hall: a row of 4 racks and the home station across a 1.4 m aisle. */
const HALL: Preset = {
  id: 'hall',
  title: 'Data hall (scaled concept)',
  note: 'Concept at scale: 4 racks × 4 bays (RAID groups), one robot, one spare station across the aisle',
  stations: [rack(0, 0, 0), rack(1, 500, 20), rack(2, 1000, 30), rack(3, 1500, 40), home(750, 1400)],
  laneY: -700,
  randomFaultMeanS: 150,
};

export const PRESETS = {hall: HALL, arena: ARENA};

export type Pose = {x: number; y: number; th: number};

/** Station-local point -> world. */
export function toWorld(st: Station, lx: number, ly: number): [number, number] {
  const c = Math.cos(st.phi);
  const s = Math.sin(st.phi);
  return [st.x + c * lx - s * ly, st.y + s * lx + c * ly];
}

/** Robot pose (axle centre, heading) when docked at a station. */
export function dockPose(st: Station): Pose {
  const [x, y] = toWorld(st, 0, AXLE_Y);
  return {x, y, th: st.phi};
}

/** Robot-model point (docked frame, mm) -> world, for a pose. */
export function robotToWorld(p: Pose, mx: number, my: number): [number, number] {
  const dx = mx;
  const dy = my - AXLE_Y;
  const c = Math.cos(p.th);
  const s = Math.sin(p.th);
  return [p.x + c * dx - s * dy, p.y + s * dx + c * dy];
}

export const fwd = (th: number): [number, number] => [-Math.sin(th), Math.cos(th)];
export const wrap = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));
export const deg = (r: number) => (r * 180) / Math.PI;
export const rad = (d: number) => (d * Math.PI) / 180;

/** Where the robot ends up after the blind undock from a station. */
export function undockPose(st: Station, laneY: number | null): Pose {
  const d = dockPose(st);
  const dist = laneY === null ? AP.undock_mm : Math.abs(laneY - d.y);
  const [fx, fy] = fwd(d.th);
  return {x: d.x - fx * dist, y: d.y - fy * dist, th: d.th};
}
