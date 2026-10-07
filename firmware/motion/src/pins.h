// ESP32-S3 pin map of RBG3-MOTION v1 (docs/spec/02-electrical.md §3.1).
#pragma once

#include <stdint.h>

namespace pins {
constexpr int L_STEP = 4, L_DIR = 5;
constexpr int R_STEP = 6, R_DIR = 7;
constexpr int Z_STEP = 15, Z_DIR = 16;
constexpr int Y_STEP = 17, Y_DIR = 18;
constexpr int STEPPER_EN_N = 8;  // shared, active low, external pull-up (disabled at boot)
constexpr int TMC_TX = 9, TMC_RX = 10;  // single-wire PDN_UART bus (TX through 1 k)
constexpr int VMOT_SENSE = 1;  // 100 k / 18 k
constexpr int DOCK_SENSE = 2;  // 100 k / 10 k
constexpr int Z_HOME = 11, Y_HOME = 12;  // NC to GND: high = pressed (or broken wire)
constexpr int NOSE = 13, SLOT_A = 14, SLOT_B = 21;  // NO to GND: low = pressed
constexpr int SERVO_A = 39, SERVO_B = 40;
constexpr int I2C_SDA = 41, I2C_SCL = 42;
constexpr int STATUS_LED = 47;
constexpr int BUZZER = 48;
constexpr int AUX_IN = 38;
}  // namespace pins

// Wiring constants
constexpr float VMOT_DIVIDER = (100.0f + 18.0f) / 18.0f;
constexpr float DOCK_DIVIDER = (100.0f + 10.0f) / 10.0f;
constexpr float TMC_R_SENSE = 0.11f;  // BTT TMC2209 v1.3 StepStick
constexpr float INA_SHUNT_OHM = 0.010f;  // R010 (many modules ship with R100: check, BACKLOG)
constexpr float INA_MAX_A = 8.0f;
constexpr uint8_t INA_ADDR = 0x40;
// Direction of each motor: flip if an axis runs the wrong way (wheels are mirrored left/right).
constexpr bool DIR_HIGH_COUNTS_UP[4] = {true, false, true, true};  // L, R, Z, Y
