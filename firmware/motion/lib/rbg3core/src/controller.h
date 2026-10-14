// Motion controller core: command handling, interlocks, homing, E-stop recovery, telemetry.
// Hardware-independent (see hal.h) so it runs in unit tests and in the host simulator.
#pragma once

#include <stdint.h>

#include "hal.h"
#include "protocol.h"
#include "settings.h"

namespace rbg3 {

class Controller {
 public:
  explicit Controller(Hal& hal) : hal_(hal) {}

  void begin();
  void handleLine(char* line);
  void feed(char c);  // byte-wise input (serial), dispatches complete lines
  void update();      // call as often as possible from the main loop

  Settings settings;

  // state for tests / diagnostics
  bool enabled() const { return en_; }
  bool estop() const { return estop_; }
  bool driversOk() const { return drivers_ok_; }
  bool homed(Axis a) const { return homed_[a]; }
  bool busy() const { return job_ != Job::NONE || vel_active_; }
  float mm(Axis a);

 private:
  enum class Job : uint8_t { NONE, HOME, Z, Y, FINGER, DRIVE, TURN, DOCK };
  enum Phase : uint8_t { START, BACKOFF1, SEEK_FAST, BACKOFF2, SEEK_SLOW, STOPPING };

  // commands
  void cmdPing(const Request& r);
  void cmdEnable(const Request& r);
  void cmdHome(const Request& r);
  void cmdLinear(const Request& r, Axis a);
  void cmdFinger(const Request& r);
  void cmdDrive(const Request& r, bool turn);
  void cmdDock(const Request& r);
  void cmdVel(const Request& r);
  void cmdStop(const Request& r);
  void cmdStatus(const Request& r);
  void cmdCfg(const Request& r);

  // checks; each sends ERR and returns false on failure
  bool checkEnabled(uint16_t seq, bool allow_vel = false);
  bool checkTravelPose(uint16_t seq);
  bool argFloat(const Request& r, int i, float& out, float fallback, bool required);

  // jobs
  void startJob(Job j, uint16_t seq, uint32_t timeout_ms);
  void finishJob(bool ok, const char* code = nullptr);
  void updateJob(uint32_t now);
  void updateHome(uint32_t now);
  void stopAll(const char* fail_code);
  void haltAll();

  // safety
  void updateSafety(uint32_t now);
  void enterEstop(const char* event);
  void updateInputs();

  // output
  void reply(uint16_t seq, const char* kind, const char* a = nullptr, const char* b = nullptr);
  void event(const char* name, const char* data = nullptr);
  void telemetry();
  void updateLed();

  int32_t steps(Axis a, float mm) const;
  uint32_t hz(Axis a, float mm_s) const;
  bool homeSwitch(Axis a) const { return a == AX_Z ? in_.z_home : in_.y_home; }

  Hal& hal_;
  LineBuffer rx_;
  Inputs in_;
  bool in_valid_ = false;

  bool en_ = false;
  bool estop_ = true;  // until the drivers are configured after boot
  bool drivers_ok_ = false;
  bool fault_ = false;
  bool homed_[AX_COUNT] = {};
  bool finger_engaged_[2] = {};
  uint32_t vmot_ok_since_ = 0;
  uint32_t last_config_try_ = 0;
  uint32_t last_reset_poll_ = 0;

  Job job_ = Job::NONE;
  uint16_t job_seq_ = 0;
  uint32_t job_t0_ = 0, job_deadline_ = 0;
  Axis home_axis_ = AX_Y;
  Phase phase_ = START;
  int32_t seek_start_ = 0;
  float dock_start_mm_ = 0, dock_max_mm_ = 0;

  bool vel_active_ = false;
  uint32_t vel_last_ = 0;
  uint32_t last_tel_ = 0;
};

}  // namespace rbg3
