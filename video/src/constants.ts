// Film format and scene boundaries (frames @ 30 fps, cuts on 120 BPM bar lines = 60 frames).
export const FPS = 30;
export const W = 1920;
export const H = 1080;

export const SCENES = {
  hook: [0, 240],
  problem: [240, 480],
  reveal: [480, 660],
  how: [660, 1260],
  swap: [1260, 2160],
  delta: [2160, 2460],
  close: [2460, 2700],
} as const;
export const TOTAL = 2700;

// CAD numbers (mm, docked-at-rack frame: x across the bay, y into the bay, z up). Source: cad/src/lib/*.py.
export const H_BAY = [150, 195, 240, 285];
export const H_SPARE = [150, 195];
export const BAY_PITCH = 45;
export const Y_PULL = 177;
export const Y_NOTCH_HOME = -187;
export const FINGER_X = 69.5;
export const FINGER_DZ = {B: 15, A: 60};
export const AXLE_Y = -135;
export const Z_TRAVEL = 210;
// Spare station = the robot's base (charging dock) down the aisle: face at (SPARE_X, -SPARE_D), facing the rack side (+y), ~3.2 m from the rack.
// The robot reaches it with a reverse swing out of the dock, one aisle run and a single 90° L turn (anim.ts).
export const SPARE_X = 2600;
export const SPARE_D = 1820;
export const TURN_R = 300; // axle-centre radius of the swing and the L turn
export const CAM_LENS = {x: -78, y: -115, dz: 15};
export const TAG_APPROACH = {x: 125, y: 7, z: 230}; // tag centre on the fin plate (lib/tags.py)
export const RACK_TOP_Z = 360;
export const TOWER = {x: 60, y: 135, z0: 360, z1: 480, r: 20};

export const COLORS = {
  bg: '#0B0D10',
  ink: '#F4F1EA',
  dim: '#8A929C',
  accent: '#E07A1F',
  green: '#3DDC84',
  red: '#FF4D4D',
  amber: '#FFB020',
  blue: '#5AA9FF',
};
