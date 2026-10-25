// Motion constants (01-mechanical §1/§6, 02-electrical §2, 03-software §3/§8).
// Everything here can be changed at runtime with `CFG <key> <value>` (see settings.cpp).
#pragma once

#include <stdint.h>

#include "hal.h"

namespace rbg3 {

constexpr const char* FW_VERSION = "0.1.0";

struct Settings {
  // steps per mm (16 microsteps): drive 3200 / (pi * 80), Z Tr8x2 lead screw, Y GT2 20T
  float steps_mm[AX_COUNT] = {12.732f, 12.732f, 1600.0f, 80.0f};
  float track_mm = 274.0f;  // wheel centre distance (wheels at x = ±137)

  // speeds (mm/s, deg/s) and accelerations (mm/s²)
  float v_drive = 150, a_drive = 300;
  float v_turn = 60;
  float v_z = 15, a_z = 50;
  float v_y = 60, a_y = 200;
  float v_dock = 50;
  float home_fast = 10, home_slow = 2, home_backoff = 3;

  // geometry (mm)
  float z_home = 101;  // Z where the home switch triggers (CAD Z_HOME; hard stop ~100.6): confirm on the robot
  float z_min = 102, z_max = 295, z_drive_max = 220;
  float y_max = 180, y_safe = 2, y_pull = 177, y_push = 178.5f, y_at_tol = 0.5f;
  float z_travel = 220, y_travel = 200;  // homing search distance before E_LIMIT

  // fingers (servo degrees, calibrate per robot)
  float finger_park[2] = {0, 0};
  float finger_engage[2] = {90, 90};
  uint32_t finger_ms = 300;

  // drivers: L, R, Z, Y run current (mA rms), Z hold
  uint16_t run_ma[AX_COUNT] = {1000, 1000, 900, 600};
  uint16_t hold_ma_z = 500;
  uint16_t microsteps = 16;

  // safety and timing
  float vmot_min = 9.0f;   // below = E-stop / VMOT off
  float vmot_ok = 10.5f;   // above (for vmot_settle_ms) = VMOT back
  uint32_t vmot_settle_ms = 200;
  uint32_t vel_timeout_ms = 300;
  uint32_t tel_period_ms = 100;
  uint32_t reset_poll_ms = 500;
  bool bench = false;  // lifts the docked interlock for Y

  bool set(const char* key, float value);  // CFG handler; false = unknown key
  DriverSettings drivers() const;
};

}  // namespace rbg3
