// Host-side HAL with simple stepper physics. Used by the unit tests and the host simulator.
// Each axis has a physical position (home switch at physical 0) and a step counter offset,
// so homing really has to find the switch.
#pragma once

#include <math.h>
#include <stdint.h>

#include <string>
#include <vector>

#include "hal.h"

namespace rbg3 {

class FakeHal : public Hal {
 public:
  struct AxisSim {
    double phys = 0;  // steps from the home switch
    int32_t offset = 0;
    enum Mode { IDLE, MOVE, RUN } mode = IDLE;
    double target = 0, speed = 0, vel = 0;
  };

  uint32_t now = 0;
  AxisSim ax[AX_COUNT];
  float steps_mm[AX_COUNT] = {12.732f, 12.732f, 1600.0f, 80.0f};
  float vmot_v = 15.0f, dock_v = 0.0f, vbat_v = 15.2f, ibat_a = 0.3f;
  bool en = false;
  bool driver_ok = true;  // configureDrivers() succeeds
  bool reset_flag = false;
  int configure_calls = 0;
  bool slot_a = false, slot_b = false;
  bool nose_fixed = false;       // NOSE input when no dock distance is set
  double nose_at_mm = -1;        // NOSE closes when the wheels have moved this far forward (< 0: off)
  bool home_wire_broken = false; // NC switch with a broken wire reads "pressed"
  float servo_deg[2] = {};
  std::vector<std::string> out;

  FakeHal() {
    ax[AX_Z].phys = 30 * steps_mm[AX_Z];  // lift 30 mm above its home switch
    ax[AX_Y].phys = 5 * steps_mm[AX_Y];
  }

  void tick(uint32_t ms) {
    now += ms;
    double dt = ms / 1000.0;
    for (auto& a : ax) {
      if (a.mode == AxisSim::MOVE) {
        double step = a.speed * dt;
        double d = a.target - (a.phys + a.offset);
        if (fabs(d) <= step) {
          a.phys = a.target - a.offset;
          a.mode = AxisSim::IDLE;
        } else {
          a.phys += d > 0 ? step : -step;
        }
      } else if (a.mode == AxisSim::RUN) {
        a.phys += a.vel * dt;
      }
    }
  }

  double physMm(Axis a) const { return ax[a].phys / steps_mm[a]; }

  // Hal
  uint32_t millis() override { return now; }
  void moveTo(Axis a, int32_t pos, uint32_t speed_hz, uint32_t) override {
    ax[a].target = pos;
    ax[a].speed = speed_hz;
    ax[a].mode = AxisSim::MOVE;
  }
  void runAt(Axis a, int32_t speed_hz, uint32_t) override {
    ax[a].vel = speed_hz;
    ax[a].mode = speed_hz ? AxisSim::RUN : AxisSim::IDLE;
  }
  void stop(Axis a) override { ax[a].mode = AxisSim::IDLE; }
  void halt(Axis a) override { ax[a].mode = AxisSim::IDLE; }
  bool running(Axis a) override { return ax[a].mode != AxisSim::IDLE; }
  int32_t position(Axis a) override { return static_cast<int32_t>(lround(ax[a].phys)) + ax[a].offset; }
  void setPosition(Axis a, int32_t pos) override { ax[a].offset = pos - static_cast<int32_t>(lround(ax[a].phys)); }
  void enableDrivers(bool on) override { en = on; }
  bool configureDrivers(const DriverSettings&) override {
    configure_calls++;
    return driver_ok;
  }
  bool driversWereReset() override {
    bool r = reset_flag;
    reset_flag = false;
    return r;
  }
  Inputs inputs() override {
    Inputs in;
    in.z_home = home_wire_broken || ax[AX_Z].phys <= 0;
    in.y_home = home_wire_broken || ax[AX_Y].phys <= 0;
    double wheels = (physMm(AX_L) + physMm(AX_R)) / 2;
    in.nose = nose_at_mm >= 0 ? wheels >= nose_at_mm : nose_fixed;
    in.slot_a = slot_a;
    in.slot_b = slot_b;
    return in;
  }
  float vmot() override { return vmot_v; }
  float dockV() override { return dock_v; }
  float vbat() override { return vbat_v; }
  float ibat() override { return ibat_a; }
  void servo(uint8_t i, float deg) override { servo_deg[i] = deg; }
  void led(Led) override {}
  void writeLine(const char* line) override { out.emplace_back(line); }
};

}  // namespace rbg3
