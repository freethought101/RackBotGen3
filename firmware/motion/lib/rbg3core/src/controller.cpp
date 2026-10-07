#include "controller.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace rbg3 {

namespace {
constexpr float kPi = 3.14159265f;
constexpr float kDockedV = 20.0f;

uint32_t secondsMs(float s) { return static_cast<uint32_t>(s * 1000.0f); }
}  // namespace

// --- helpers ---------------------------------------------------------------------------------------

float Controller::mm(Axis a) { return hal_.position(a) / settings.steps_mm[a]; }

int32_t Controller::steps(Axis a, float mm) const { return static_cast<int32_t>(lroundf(mm * settings.steps_mm[a])); }

uint32_t Controller::hz(Axis a, float mm_s) const {
  float v = fabsf(mm_s) * settings.steps_mm[a];
  return v < 1.0f ? 1u : static_cast<uint32_t>(v);
}

void Controller::reply(uint16_t seq, const char* kind, const char* a, const char* b) {
  char out[kMaxLine + 32];
  if (a && b) {
    snprintf(out, sizeof out, "%u %s %s %s", seq, kind, a, b);
  } else if (a) {
    snprintf(out, sizeof out, "%u %s %s", seq, kind, a);
  } else {
    snprintf(out, sizeof out, "%u %s", seq, kind);
  }
  hal_.writeLine(out);
}

void Controller::event(const char* name, const char* data) {
  char out[64];
  if (data) {
    snprintf(out, sizeof out, "EVT %s %s", name, data);
  } else {
    snprintf(out, sizeof out, "EVT %s", name);
  }
  hal_.writeLine(out);
}

// --- lifecycle -------------------------------------------------------------------------------------

void Controller::begin() {
  hal_.enableDrivers(false);
  for (int i = 0; i < 2; i++) hal_.servo(i, settings.finger_park[i]);
  in_ = hal_.inputs();
  in_valid_ = true;
  char data[24];
  snprintf(data, sizeof data, "RBG3-FW %s", FW_VERSION);
  event("BOOT", data);
  if (hal_.vmot() < settings.vmot_min) event("ESTOP");  // VMOT off at boot: report it like an E-stop
}

void Controller::feed(char c) {
  if (rx_.feed(c)) handleLine(rx_.line());
}

void Controller::update() {
  uint32_t now = hal_.millis();
  updateSafety(now);
  updateInputs();
  if (job_ != Job::NONE) updateJob(now);
  if (vel_active_ && now - vel_last_ > settings.vel_timeout_ms) {  // VEL watchdog
    hal_.stop(AX_L);
    hal_.stop(AX_R);
    vel_active_ = false;
  }
  updateLed();
  if (now - last_tel_ >= settings.tel_period_ms) {
    last_tel_ = now;
    telemetry();
  }
}

// --- command dispatch ------------------------------------------------------------------------------

void Controller::handleLine(char* line) {
  Request r;
  if (!parseRequest(line, r)) {
    event("BADLINE");
    return;
  }
  const char* c = r.cmd;
  if (!strcmp(c, "PING")) return cmdPing(r);
  if (!strcmp(c, "ENABLE")) return cmdEnable(r);
  if (!strcmp(c, "HOME")) return cmdHome(r);
  if (!strcmp(c, "Z")) return cmdLinear(r, AX_Z);
  if (!strcmp(c, "Y")) return cmdLinear(r, AX_Y);
  if (!strcmp(c, "FINGER")) return cmdFinger(r);
  if (!strcmp(c, "DRIVE")) return cmdDrive(r, false);
  if (!strcmp(c, "TURN")) return cmdDrive(r, true);
  if (!strcmp(c, "DOCK")) return cmdDock(r);
  if (!strcmp(c, "VEL")) return cmdVel(r);
  if (!strcmp(c, "STOP")) return cmdStop(r);
  if (!strcmp(c, "STATUS")) return cmdStatus(r);
  if (!strcmp(c, "CFG")) return cmdCfg(r);
  reply(r.seq, "ERR", "E_ARG", "unknown command");
}

bool Controller::argFloat(const Request& r, int i, float& out, float fallback, bool required) {
  if (i >= r.argc) {
    if (required) {
      reply(r.seq, "ERR", "E_ARG", "missing argument");
      return false;
    }
    out = fallback;
    return true;
  }
  if (!parseNumber(r.argv[i], out)) {
    reply(r.seq, "ERR", "E_ARG", "bad number");
    return false;
  }
  return true;
}

bool Controller::checkEnabled(uint16_t seq, bool allow_vel) {
  if (estop_ || !drivers_ok_) {
    reply(seq, "ERR", "E_ESTOP");
    return false;
  }
  if (!en_) {
    reply(seq, "ERR", "E_INTERLOCK", "drivers disabled");
    return false;
  }
  if (job_ != Job::NONE || (vel_active_ && !allow_vel)) {
    reply(seq, "ERR", "E_BUSY");
    return false;
  }
  return true;
}

bool Controller::checkTravelPose(uint16_t seq) {
  if (!homed_[AX_Y] || !homed_[AX_Z]) {
    reply(seq, "ERR", "E_NOT_HOMED");
    return false;
  }
  if (mm(AX_Y) > settings.y_safe || mm(AX_Z) > settings.z_drive_max) {
    reply(seq, "ERR", "E_INTERLOCK", "Y or Z not in travel pose");
    return false;
  }
  return true;
}

void Controller::cmdPing(const Request& r) {
  char data[24];
  snprintf(data, sizeof data, "RBG3-FW %s", FW_VERSION);
  reply(r.seq, "OK", data);
}

void Controller::cmdEnable(const Request& r) {
  float on;
  if (!argFloat(r, 0, on, 0, true)) return;
  if (on != 0) {
    if (estop_ || !drivers_ok_) return reply(r.seq, "ERR", "E_ESTOP", "drivers not configured");
    en_ = true;
    hal_.enableDrivers(true);
  } else {
    stopAll("E_STOPPED");
    en_ = false;
    hal_.enableDrivers(false);
    homed_[AX_Y] = homed_[AX_Z] = false;  // axes can be moved by hand while unpowered
  }
  reply(r.seq, "OK");
}

void Controller::cmdHome(const Request& r) {
  if (r.argc != 1 || (strcmp(r.argv[0], "Y") && strcmp(r.argv[0], "Z")))
    return reply(r.seq, "ERR", "E_ARG");
  if (!checkEnabled(r.seq)) return;
  Axis a = r.argv[0][0] == 'Y' ? AX_Y : AX_Z;
  if (a == AX_Z) {
    if (!homed_[AX_Y]) return reply(r.seq, "ERR", "E_NOT_HOMED", "home Y first");
    if (mm(AX_Y) > settings.y_safe) return reply(r.seq, "ERR", "E_INTERLOCK", "Y > 2");
  }
  homed_[a] = false;
  home_axis_ = a;
  phase_ = START;
  float travel = a == AX_Z ? settings.z_travel : settings.y_travel;
  startJob(Job::HOME, r.seq, secondsMs(travel / settings.home_fast + 30.0f));
}

void Controller::cmdLinear(const Request& r, Axis a) {
  float target, speed;
  float vmax = a == AX_Z ? settings.v_z : settings.v_y;
  if (!argFloat(r, 0, target, 0, true) || !argFloat(r, 1, speed, vmax, false)) return;
  if (speed <= 0) return reply(r.seq, "ERR", "E_ARG", "speed");
  speed = fminf(speed, vmax);
  if (!checkEnabled(r.seq)) return;
  if (!homed_[a]) return reply(r.seq, "ERR", "E_NOT_HOMED");
  if (a == AX_Z) {
    if (mm(AX_Y) > settings.y_safe) return reply(r.seq, "ERR", "E_INTERLOCK", "Y > 2");
    if (target < settings.z_min || target > settings.z_max) return reply(r.seq, "ERR", "E_LIMIT");
  } else {
    if (target < 0 || target > settings.y_max) return reply(r.seq, "ERR", "E_LIMIT");
    if (target > settings.y_safe && !in_.nose && !settings.bench)
      return reply(r.seq, "ERR", "E_INTERLOCK", "not docked");
  }
  float dist = fabsf(target - mm(a));
  float accel = a == AX_Z ? settings.a_z : settings.a_y;
  startJob(a == AX_Z ? Job::Z : Job::Y, r.seq, secondsMs(dist / speed * 1.5f + speed / accel + 3.0f));
  hal_.moveTo(a, steps(a, target), hz(a, speed), hz(a, accel));
}

void Controller::cmdFinger(const Request& r) {
  if (r.argc != 2) return reply(r.seq, "ERR", "E_ARG");
  bool a = !strcmp(r.argv[0], "A"), b = !strcmp(r.argv[0], "B"), both = !strcmp(r.argv[0], "both");
  bool engage = !strcmp(r.argv[1], "ENGAGE"), park = !strcmp(r.argv[1], "PARK");
  if (!(a || b || both) || !(engage || park)) return reply(r.seq, "ERR", "E_ARG");
  if (!checkEnabled(r.seq)) return;
  if (!homed_[AX_Y]) return reply(r.seq, "ERR", "E_NOT_HOMED");
  float y = mm(AX_Y);
  bool at_rest = y <= settings.y_safe || fabsf(y - settings.y_pull) <= settings.y_at_tol ||
                 fabsf(y - settings.y_push) <= settings.y_at_tol;
  if (!at_rest) return reply(r.seq, "ERR", "E_INTERLOCK", "Y mid-stroke");
  startJob(Job::FINGER, r.seq, settings.finger_ms + 1000);
  for (int i = 0; i < 2; i++) {
    if (both || (i == 0 && a) || (i == 1 && b)) {
      finger_engaged_[i] = engage;
      hal_.servo(i, engage ? settings.finger_engage[i] : settings.finger_park[i]);
    }
  }
}

void Controller::cmdDrive(const Request& r, bool turn) {
  float amount, speed;
  float vmax = turn ? settings.v_turn : settings.v_drive;
  if (!argFloat(r, 0, amount, 0, true) || !argFloat(r, 1, speed, vmax, false)) return;
  if (speed <= 0) return reply(r.seq, "ERR", "E_ARG", "speed");
  speed = fminf(speed, vmax);
  if (!checkEnabled(r.seq) || !checkTravelPose(r.seq)) return;
  // TURN: + = counter-clockwise, so the right wheel goes forward
  float arc_per_unit = settings.track_mm / 2.0f * kPi / 180.0f;
  float dl = turn ? -amount * arc_per_unit : amount;
  float dr = turn ? amount * arc_per_unit : amount;
  float wheel_speed = turn ? speed * arc_per_unit : speed;
  float dist = fabsf(dl);
  startJob(turn ? Job::TURN : Job::DRIVE, r.seq,
           secondsMs(dist / wheel_speed * 1.5f + wheel_speed / settings.a_drive + 3.0f));
  hal_.moveTo(AX_L, hal_.position(AX_L) + steps(AX_L, dl), hz(AX_L, wheel_speed), hz(AX_L, settings.a_drive));
  hal_.moveTo(AX_R, hal_.position(AX_R) + steps(AX_R, dr), hz(AX_R, wheel_speed), hz(AX_R, settings.a_drive));
}

void Controller::cmdDock(const Request& r) {
  float max_mm, speed;
  if (!argFloat(r, 0, max_mm, 0, true) || !argFloat(r, 1, speed, settings.v_dock, false)) return;
  if (max_mm <= 0 || speed <= 0) return reply(r.seq, "ERR", "E_ARG");
  speed = fminf(speed, settings.v_dock);
  if (!checkEnabled(r.seq) || !checkTravelPose(r.seq)) return;
  if (in_.nose) {  // already docked
    reply(r.seq, "OK");
    return reply(r.seq, "DONE");
  }
  dock_start_mm_ = (mm(AX_L) + mm(AX_R)) / 2.0f;
  dock_max_mm_ = max_mm;
  phase_ = START;
  startJob(Job::DOCK, r.seq, secondsMs(max_mm / speed * 1.5f + 3.0f));
  hal_.runAt(AX_L, static_cast<int32_t>(hz(AX_L, speed)), hz(AX_L, settings.a_drive));
  hal_.runAt(AX_R, static_cast<int32_t>(hz(AX_R, speed)), hz(AX_R, settings.a_drive));
}

void Controller::cmdVel(const Request& r) {
  float v, w;
  if (!argFloat(r, 0, v, 0, true) || !argFloat(r, 1, w, 0, true)) return;
  if (!checkEnabled(r.seq, true) || !checkTravelPose(r.seq)) return;
  v = fmaxf(-settings.v_drive, fminf(v, settings.v_drive));
  float dv = w * kPi / 180.0f * settings.track_mm / 2.0f;
  float vl = v - dv, vr = v + dv;
  if (v == 0 && w == 0) {
    hal_.stop(AX_L);
    hal_.stop(AX_R);
    vel_active_ = false;
  } else {
    int32_t sl = static_cast<int32_t>(vl * settings.steps_mm[AX_L]);
    int32_t sr = static_cast<int32_t>(vr * settings.steps_mm[AX_R]);
    hal_.runAt(AX_L, sl, hz(AX_L, settings.a_drive));
    hal_.runAt(AX_R, sr, hz(AX_R, settings.a_drive));
    vel_active_ = true;
    vel_last_ = hal_.millis();
  }
  reply(r.seq, "OK");
}

void Controller::cmdStop(const Request& r) {
  stopAll("E_STOPPED");
  reply(r.seq, "OK");
}

void Controller::cmdStatus(const Request& r) {
  reply(r.seq, "OK");
  telemetry();
}

void Controller::cmdCfg(const Request& r) {
  float value;
  if (r.argc != 2 || !parseNumber(r.argv[1], value) || !settings.set(r.argv[0], value))
    return reply(r.seq, "ERR", "E_ARG");
  if (strstr(r.argv[0], "cur") && drivers_ok_ && !hal_.configureDrivers(settings.drivers()))
    return reply(r.seq, "ERR", "E_TIMEOUT", "driver UART");
  reply(r.seq, "OK");
}

// --- jobs ------------------------------------------------------------------------------------------

void Controller::startJob(Job j, uint16_t seq, uint32_t timeout_ms) {
  job_ = j;
  job_seq_ = seq;
  job_t0_ = hal_.millis();
  job_deadline_ = job_t0_ + timeout_ms;
  fault_ = false;
  reply(seq, "OK");
}

void Controller::finishJob(bool ok, const char* code) {
  if (job_ == Job::NONE) return;
  job_ = Job::NONE;
  if (ok) {
    reply(job_seq_, "DONE");
  } else {
    fault_ = true;
    reply(job_seq_, "FAIL", code);
  }
}

void Controller::stopAll(const char* fail_code) {
  for (int a = 0; a < AX_COUNT; a++) hal_.stop(static_cast<Axis>(a));
  vel_active_ = false;
  if (job_ == Job::HOME) homed_[home_axis_] = false;
  if (job_ != Job::NONE) finishJob(false, fail_code);
}

void Controller::haltAll() {
  for (int a = 0; a < AX_COUNT; a++) hal_.halt(static_cast<Axis>(a));
  vel_active_ = false;
}

void Controller::updateJob(uint32_t now) {
  if (static_cast<int32_t>(now - job_deadline_) > 0) {
    haltAll();
    if (job_ == Job::HOME) homed_[home_axis_] = false;
    return finishJob(false, "E_TIMEOUT");
  }
  switch (job_) {
    case Job::HOME:
      return updateHome(now);
    case Job::Z:
    case Job::Y: {
      Axis a = job_ == Job::Z ? AX_Z : AX_Y;
      if (!hal_.running(a)) return finishJob(true);
      // A home switch hit outside homing means the position is wrong: stop before the end stop.
      if (homeSwitch(a)) {
        hal_.halt(a);
        homed_[a] = false;
        event("LIMIT", a == AX_Z ? "Z_HOME" : "Y_HOME");
        return finishJob(false, "E_LIMIT");
      }
      return;
    }
    case Job::FINGER:
      if (now - job_t0_ >= settings.finger_ms) finishJob(true);
      return;
    case Job::DRIVE:
    case Job::TURN:
      if (!hal_.running(AX_L) && !hal_.running(AX_R)) finishJob(true);
      return;
    case Job::DOCK: {
      if (phase_ == STOPPING) {
        if (!hal_.running(AX_L) && !hal_.running(AX_R)) finishJob(false, "E_NODOCK");
        return;
      }
      if (in_.nose) {
        hal_.halt(AX_L);
        hal_.halt(AX_R);
        return finishJob(true);
      }
      float travelled = (mm(AX_L) + mm(AX_R)) / 2.0f - dock_start_mm_;
      if (travelled >= dock_max_mm_) {
        hal_.stop(AX_L);
        hal_.stop(AX_R);
        phase_ = STOPPING;
      }
      return;
    }
    case Job::NONE:
      return;
  }
}

void Controller::updateHome(uint32_t now) {
  (void)now;
  Axis a = home_axis_;
  bool pressed = homeSwitch(a);
  float accel = a == AX_Z ? settings.a_z : settings.a_y;
  int32_t fast = -static_cast<int32_t>(hz(a, settings.home_fast));
  int32_t slow = -static_cast<int32_t>(hz(a, settings.home_slow));
  int32_t backoff = steps(a, settings.home_backoff);
  float travel = a == AX_Z ? settings.z_travel : settings.y_travel;
  switch (phase_) {
    case START:
      if (pressed) {  // already on the switch: move off it first
        hal_.moveTo(a, hal_.position(a) + backoff, hz(a, settings.home_fast), hz(a, accel));
        phase_ = BACKOFF1;
      } else {
        seek_start_ = hal_.position(a);
        hal_.runAt(a, fast, hz(a, accel));
        phase_ = SEEK_FAST;
      }
      return;
    case BACKOFF1:
      if (hal_.running(a)) return;
      if (pressed) {
        homed_[a] = false;
        return finishJob(false, "E_LIMIT");  // switch stuck closed or wire broken (NC: open = pressed)
      }
      seek_start_ = hal_.position(a);
      hal_.runAt(a, fast, hz(a, accel));
      phase_ = SEEK_FAST;
      return;
    case SEEK_FAST:
      if (pressed) {
        hal_.halt(a);
        hal_.moveTo(a, hal_.position(a) + backoff, hz(a, settings.home_fast), hz(a, accel));
        phase_ = BACKOFF2;
      } else if (abs(hal_.position(a) - seek_start_) > steps(a, travel)) {
        hal_.halt(a);
        finishJob(false, "E_LIMIT");  // switch never closed
      }
      return;
    case BACKOFF2:
      if (hal_.running(a)) return;
      if (pressed) {
        finishJob(false, "E_LIMIT");
        return;
      }
      seek_start_ = hal_.position(a);
      hal_.runAt(a, slow, hz(a, accel));
      phase_ = SEEK_SLOW;
      return;
    case SEEK_SLOW:
      if (pressed) {
        hal_.halt(a);
        hal_.setPosition(a, a == AX_Z ? steps(AX_Z, settings.z_home) : 0);
        homed_[a] = true;
        finishJob(true);
      } else if (abs(hal_.position(a) - seek_start_) > steps(a, settings.home_backoff + 5.0f)) {
        hal_.halt(a);
        finishJob(false, "E_LIMIT");
      }
      return;
    case STOPPING:
      return;
  }
}

// --- safety ----------------------------------------------------------------------------------------

void Controller::enterEstop(const char* evt) {
  haltAll();
  hal_.enableDrivers(false);
  en_ = false;
  estop_ = true;
  drivers_ok_ = false;
  homed_[AX_Y] = homed_[AX_Z] = false;
  vmot_ok_since_ = 0;
  if (job_ != Job::NONE) finishJob(false, "E_ESTOP");
  event(evt);
}

void Controller::updateSafety(uint32_t now) {
  float v = hal_.vmot();
  if (!estop_ && v < settings.vmot_min) return enterEstop("ESTOP");
  if (estop_) {
    if (v < settings.vmot_ok) {
      vmot_ok_since_ = 0;
      return;
    }
    if (vmot_ok_since_ == 0) vmot_ok_since_ = now ? now : 1;
    // VMOT is back: the TMC2209s reset with it (wrong microsteps, VREF current) -> reconfigure first
    if (now - vmot_ok_since_ >= settings.vmot_settle_ms &&
        (last_config_try_ == 0 || now - last_config_try_ >= settings.reset_poll_ms)) {
      last_config_try_ = now ? now : 1;
      if (hal_.configureDrivers(settings.drivers())) {
        hal_.driversWereReset();  // clear GSTAT.reset left from the power cycle
        drivers_ok_ = true;
        estop_ = false;
        last_config_try_ = 0;
        last_reset_poll_ = now;
        event("ESTOP_CLEAR");
      }
    }
    return;
  }
  if (now - last_reset_poll_ >= settings.reset_poll_ms) {
    last_reset_poll_ = now;
    if (hal_.driversWereReset()) enterEstop("DRIVER_RESET");  // VS brown-out we did not see on VMOT_SENSE
  }
}

void Controller::updateInputs() {
  Inputs n = hal_.inputs();
  if (in_valid_) {
    if (n.nose != in_.nose) event("NOSE", n.nose ? "1" : "0");
    if (n.slot_a != in_.slot_a) event("SLOT_A", n.slot_a ? "1" : "0");
    if (n.slot_b != in_.slot_b) event("SLOT_B", n.slot_b ? "1" : "0");
  }
  in_ = n;
  in_valid_ = true;
}

// --- output ----------------------------------------------------------------------------------------

void Controller::telemetry() {
  char busy[6] = {};
  int n = 0;
  if (hal_.running(AX_Z)) busy[n++] = 'Z';
  if (hal_.running(AX_Y)) busy[n++] = 'Y';
  if (hal_.running(AX_L) || hal_.running(AX_R)) busy[n++] = 'D';
  if (job_ == Job::FINGER) busy[n++] = 'F';
  if (vel_active_) busy[n++] = 'V';
  uint8_t sw = (in_.z_home ? 1 : 0) | (in_.y_home ? 2 : 0) | (in_.nose ? 4 : 0) | (in_.slot_a ? 8 : 0) |
               (in_.slot_b ? 16 : 0);
  char homed[3] = {};
  int h = 0;
  if (homed_[AX_Z]) homed[h++] = 'Z';
  if (homed_[AX_Y]) homed[h++] = 'Y';
  char out[200];
  snprintf(out, sizeof out,
           "TEL t=%lu z=%.2f y=%.2f l=%.1f r=%.1f en=%d busy=%s sw=%02x vbat=%.2f ibat=%.3f vmot=%.1f dock=%.1f "
           "fa=%c fb=%c homed=%s",
           static_cast<unsigned long>(hal_.millis()), mm(AX_Z), mm(AX_Y), mm(AX_L), mm(AX_R), en_ ? 1 : 0, busy,
           sw, hal_.vbat(), hal_.ibat(), hal_.vmot(), hal_.dockV(), finger_engaged_[0] ? 'E' : 'P',
           finger_engaged_[1] ? 'E' : 'P', homed);
  hal_.writeLine(out);
}

void Controller::updateLed() {
  Led s = Led::IDLE;
  if (estop_) {
    s = Led::ESTOP;
  } else if (fault_) {
    s = Led::FAULT;
  } else if (busy()) {
    s = Led::MOVING;
  } else if (hal_.dockV() > kDockedV) {
    s = Led::DOCKED;
  }
  hal_.led(s);
}

}  // namespace rbg3
