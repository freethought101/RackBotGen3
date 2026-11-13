// Every number the simulator uses, with its source. Geometry: CAD mm (x across the bay, y into the bay, z up),
// in the docked-at-rack frame of video/src/constants.ts. Behaviour: rackbot/config.yaml and 03-software.md.

// --- geometry (cad/src/lib/dims.py, video/src/constants.ts) ---------------------------------------------------
export const H_BAY = [150, 195, 240, 285];
export const H_SPARE = [150, 195]; // S1 GOOD, S2 RMA
export const BAY_PITCH = 45;
export const Y_PULL = 177;
export const Y_PUSH = 178.5;
export const Y_SAFE = 2;
export const Y_NOTCH_HOME = -187;
export const FINGER_X = 69.5;
export const FINGER_DZ = {A: 60, B: 15};
export const AXLE_Y = -135; // robot axle centre when docked (nose at the dock stop)
export const NOSE_Y = -30;
export const Z_DRIVE = 110;
export const Z_APPROACH = 200; // camera level with the approach tag (calibrated on the real robot)
export const Z_HOME = 102;
export const CAM_LENS = {x: -78, y: -115, dz: 15}; // tray camera, dz above the lift Z
export const CAM_HFOV = 102; // IMX708 wide, horizontal
export const CAM_W = 640;
export const CAM_H = 480;
export const TAG_FACE_Y = 7;
export const TAG_APPROACH = {x: 125, z: 230, size: 50};
export const TAG_BAY = {x: -80, dz: 15, size: 16};
export const TAG_CADDY = {x: -38, y: -20.5, dz: 15, size: 24};
export const RACK_TOP_Z = 360;
export const SPARE_TOP_Z = 255;
export const TOWER = {x: 60, y: 135, z0: 360, z1: 480, r: 20};

/** z_for(slot, h, op) of 03 §5.1: slot B floor height that puts `slot` level with a shelf. */
export const zFor = (slot: Slot, h: number, op: 'insert' | 'extract') => h + (op === 'insert' ? 1 : -1) - (slot === 'A' ? BAY_PITCH : 0);

export type Slot = 'A' | 'B';

// --- motion (config.yaml motion.speeds; firmware Y 60 mm/s since v0.1.26) --------------------------------------
export const SPEED = {z: 15, y: 60, drive: 150, turn: 60}; // mm/s, deg/s
export const FINGER_S = 0.35; // MG90S swing, s

// --- approach (config.yaml approach, 03 §6.2) -------------------------------------------------------------------
export const AP = {
  k_theta: 1.5, k_psi: 0.8, k_d: 0.5, d_target: 250, v_min: 30, v_max: 150,
  handoff_d: 260, handoff_x: 10, handoff_psi: 3, abort_d: 200, lost_s: 0.5,
  backoff_mm: 100, max_retries: 3, dock_max_mm: 300, dock_speed: 50, undock_mm: 250,
};
export const CAM_FPS = 10; // vision.fps
export const TURN_ERROR_DEG = 3; // sim.turn_error_deg: TURN overshoot so the approach has work to do

// --- health (config.yaml health) ---------------------------------------------------------------------------------
export const WARN_REALLOC = 10;
export const FAIL_REALLOC = 50;
export const FAULT_RAMP_S = 10;

// --- power (02-electrical §1) -------------------------------------------------------------------------------------
export const BATTERY_WH = 50.4; // 4S1P 18650, 3.5 Ah
export const V_EMPTY = 12.0;
export const V_FULL = 16.8;
export const CHARGE_A = 1.5; // CC/CV buck 16.8 V / 1.5 A
export const CHARGE_TAPER_A = 0.2;
// idle ≈ 4 W (Pi + logic), moving ≈ 12–20 W; split per active axis
export const POWER_W = {idle: 4, drive: 12, z: 8, y: 6, finger: 2};

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
