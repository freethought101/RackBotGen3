// Hardware abstraction for the motion controller core.
// src/main.cpp implements it on the ESP32-S3; tests and the host simulator use fakes.
#pragma once

#include <stdint.h>

namespace rbg3 {

enum Axis : uint8_t { AX_L = 0, AX_R, AX_Z, AX_Y, AX_COUNT };

// Switch states, already converted to "pressed" (NC home switches: input high = pressed).
struct Inputs {
  bool z_home = false;
  bool y_home = false;
  bool nose = false;
  bool slot_a = false;
  bool slot_b = false;
  bool estop = false;  // robot E-stop NO contact on AUX_IN (J13): input low = pressed
};

struct DriverSettings {
  uint16_t run_ma[AX_COUNT];  // rms run current per driver
  uint16_t hold_ma_z;         // Z hold current
  uint16_t microsteps;
};

enum class Led : uint8_t { OFF, IDLE, DOCKED, MOVING, FAULT, ESTOP };

class Hal {
 public:
  virtual ~Hal() = default;
  virtual uint32_t millis() = 0;

  // Steppers, positions in steps. Positive = forward (wheels), up (Z), out (Y).
  virtual void moveTo(Axis a, int32_t pos, uint32_t speed_hz, uint32_t accel) = 0;
  virtual void runAt(Axis a, int32_t speed_hz, uint32_t accel) = 0;  // signed; continuous
  virtual void stop(Axis a) = 0;  // decelerate to standstill
  virtual void halt(Axis a) = 0;  // stop immediately
  virtual bool running(Axis a) = 0;
  virtual int32_t position(Axis a) = 0;
  virtual void setPosition(Axis a, int32_t pos) = 0;

  // TMC2209 drivers
  virtual void enableDrivers(bool on) = 0;
  // Write every register to all drivers and verify (IFCNT). False if a driver did not answer.
  virtual bool configureDrivers(const DriverSettings& s) = 0;
  // True if a driver reports GSTAT.reset (it lost VS since the last configure).
  virtual bool driversWereReset() = 0;

  virtual Inputs inputs() = 0;
  virtual float vmot() = 0;   // V
  virtual float dockV() = 0;  // V
  virtual float vbat() = 0;   // V (INA226 bus)
  virtual float ibat() = 0;   // A, + = discharge
  virtual void servo(uint8_t index, float deg) = 0;  // 0 = finger A, 1 = finger B
  virtual void led(Led state) = 0;
  virtual void writeLine(const char* line) = 0;  // without the trailing newline
};

}  // namespace rbg3
