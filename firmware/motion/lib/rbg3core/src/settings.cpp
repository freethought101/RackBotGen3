#include "settings.h"

#include <string.h>

namespace rbg3 {

namespace {
struct FloatKey {
  const char* name;
  float Settings::*field;
};

const FloatKey kFloatKeys[] = {
    {"v_drive", &Settings::v_drive}, {"a_drive", &Settings::a_drive}, {"v_turn", &Settings::v_turn},
    {"v_z", &Settings::v_z},         {"a_z", &Settings::a_z},         {"v_y", &Settings::v_y},
    {"a_y", &Settings::a_y},         {"v_dock", &Settings::v_dock},   {"track", &Settings::track_mm},
    {"z_home", &Settings::z_home},   {"y_pull", &Settings::y_pull},   {"y_push", &Settings::y_push},
    {"y_max", &Settings::y_max},     {"home_fast", &Settings::home_fast},
    {"home_slow", &Settings::home_slow},
};
}  // namespace

bool Settings::set(const char* key, float value) {
  for (const auto& k : kFloatKeys) {
    if (strcmp(key, k.name) == 0) {
      if (value <= 0) return false;
      this->*k.field = value;
      return true;
    }
  }
  if (strcmp(key, "bench") == 0) {
    bench = value != 0;
    return true;
  }
  // currents in mA: lcur, rcur, zcur, ycur (03 §3: "CFG ycur" limits the Y jam force)
  const char* cur[AX_COUNT] = {"lcur", "rcur", "zcur", "ycur"};
  for (int i = 0; i < AX_COUNT; i++) {
    if (strcmp(key, cur[i]) == 0) {
      if (value < 100 || value > 1500) return false;
      run_ma[i] = static_cast<uint16_t>(value);
      return true;
    }
  }
  if (strcmp(key, "fa_park") == 0) return finger_park[0] = value, true;
  if (strcmp(key, "fa_engage") == 0) return finger_engage[0] = value, true;
  if (strcmp(key, "fb_park") == 0) return finger_park[1] = value, true;
  if (strcmp(key, "fb_engage") == 0) return finger_engage[1] = value, true;
  return false;
}

DriverSettings Settings::drivers() const {
  DriverSettings d{};
  for (int i = 0; i < AX_COUNT; i++) d.run_ma[i] = run_ma[i];
  d.hold_ma_z = hold_ma_z;
  d.microsteps = microsteps;
  return d;
}

}  // namespace rbg3
