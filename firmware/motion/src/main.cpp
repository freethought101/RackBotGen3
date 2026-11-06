// RBG3-MOTION firmware: ESP32-S3 implementation of the rbg3::Hal and the main loop.
// All protocol, interlock and safety logic lives in lib/rbg3core (host-tested).
#include <Adafruit_NeoPixel.h>
#include <Arduino.h>
#include <ESP32Servo.h>
#include <FastAccelStepper.h>
#include <INA226.h>
#include <TMCStepper.h>
#include <Wire.h>

#include "controller.h"
#include "pins.h"

using namespace rbg3;

namespace {

constexpr int kStepPins[AX_COUNT] = {pins::L_STEP, pins::R_STEP, pins::Z_STEP, pins::Y_STEP};
constexpr int kDirPins[AX_COUNT] = {pins::L_DIR, pins::R_DIR, pins::Z_DIR, pins::Y_DIR};
constexpr uint8_t kTmcAddr[AX_COUNT] = {0, 1, 2, 3};  // MS1/MS2 straps per socket (02 §2)
#ifdef RBG3_RIG
// Table rig: only the Z (U4) and Y (U5) sockets are fitted. An empty socket never answers over UART, so
// configureDrivers() would always fail and the board would never leave E-stop.
constexpr bool kDriverFitted[AX_COUNT] = {false, false, true, true};
#else
constexpr bool kDriverFitted[AX_COUNT] = {true, true, true, true};
#endif

class EspHal : public Hal {
 public:
  void begin() {
    pinMode(pins::STEPPER_EN_N, OUTPUT);
    digitalWrite(pins::STEPPER_EN_N, HIGH);  // disabled
    for (int p : {pins::Z_HOME, pins::Y_HOME, pins::NOSE, pins::SLOT_A, pins::SLOT_B, pins::AUX_IN})
      pinMode(p, INPUT_PULLUP);
    pinMode(pins::BUZZER, OUTPUT);
    digitalWrite(pins::BUZZER, LOW);
    analogReadResolution(12);

    engine_.init();
    for (int i = 0; i < AX_COUNT; i++) {
      steppers_[i] = engine_.stepperConnectToPin(kStepPins[i]);
      if (steppers_[i]) steppers_[i]->setDirectionPin(kDirPins[i], DIR_HIGH_COUNTS_UP[i]);
    }

    Serial1.begin(115200, SERIAL_8N1, pins::TMC_RX, pins::TMC_TX);
    for (int i = 0; i < AX_COUNT; i++) drivers_[i] = new TMC2209Stepper(&Serial1, TMC_R_SENSE, kTmcAddr[i]);

    Wire.begin(pins::I2C_SDA, pins::I2C_SCL);
    ina_ok_ = ina_.begin() && ina_.setMaxCurrentShunt(INA_MAX_A, INA_SHUNT_OHM) == INA226_ERR_NONE;
    ina_.setAverage(INA226_16_SAMPLES);

    ESP32PWM::allocateTimer(0);
    for (int i = 0; i < 2; i++) {
      servos_[i].setPeriodHertz(50);
      servos_[i].attach(i == 0 ? pins::SERVO_A : pins::SERVO_B, 500, 2400);
    }

    pixel_.begin();
    pixel_.setBrightness(40);
  }

  uint32_t millis() override { return ::millis(); }

  void moveTo(Axis a, int32_t pos, uint32_t speed_hz, uint32_t accel) override {
    auto* s = steppers_[a];
    if (!s) return;
    s->setSpeedInHz(speed_hz);
    s->setAcceleration(accel);
    s->moveTo(pos);
  }

  void runAt(Axis a, int32_t speed_hz, uint32_t accel) override {
    auto* s = steppers_[a];
    if (!s) return;
    if (speed_hz == 0) return s->stopMove();
    s->setSpeedInHz(static_cast<uint32_t>(abs(speed_hz)));
    s->setAcceleration(accel);
    if (s->isRunning()) s->applySpeedAcceleration();
    if (speed_hz > 0) {
      s->runForward();
    } else {
      s->runBackward();
    }
  }

  void stop(Axis a) override {
    if (steppers_[a]) steppers_[a]->stopMove();
  }
  void halt(Axis a) override {
    if (steppers_[a]) steppers_[a]->forceStop();
  }
  bool running(Axis a) override { return steppers_[a] && steppers_[a]->isRunning(); }
  int32_t position(Axis a) override { return steppers_[a] ? steppers_[a]->getCurrentPosition() : 0; }
  void setPosition(Axis a, int32_t pos) override {
    if (steppers_[a]) steppers_[a]->setCurrentPosition(pos);
  }

  void enableDrivers(bool on) override { digitalWrite(pins::STEPPER_EN_N, on ? LOW : HIGH); }

  bool configureDrivers(const DriverSettings& cfg) override {
    bool ok = true;
    for (int i = 0; i < AX_COUNT; i++) {
      if (!kDriverFitted[i]) continue;
      TMC2209Stepper& d = *drivers_[i];
      uint8_t before = d.IFCNT();
      d.begin();
      d.toff(4);
      d.blank_time(24);
      d.I_scale_analog(false);  // current from UART, not the VREF pot
      d.internal_Rsense(false);
      d.pdn_disable(true);       // PDN_UART pin is used for UART
      d.mstep_reg_select(true);  // microsteps from MRES, not the MS1/MS2 address straps
      d.microsteps(cfg.microsteps);
      d.intpol(true);
      float hold = i == AX_Z ? static_cast<float>(cfg.hold_ma_z) / cfg.run_ma[i] : 0.5f;
      d.rms_current(cfg.run_ma[i], hold);
      d.en_spreadCycle(false);  // StealthChop
      d.pwm_autoscale(true);
      d.GSTAT(0b111);  // clear reset / drv_err / uv_cp flags
      uint8_t after = d.IFCNT();
      // Every successful write increments IFCNT; no change means the driver did not hear us.
      if (after == before || d.microsteps() != cfg.microsteps) ok = false;
    }
    return ok;
  }

  bool driversWereReset() override {
    bool reset = false;
    for (int i = 0; i < AX_COUNT; i++)
      if (kDriverFitted[i]) reset |= (drivers_[i]->GSTAT() & 0x01) != 0;
    return reset;
  }

  Inputs inputs() override {
    Inputs in;
    in.z_home = digitalRead(pins::Z_HOME) == HIGH;
    in.y_home = digitalRead(pins::Y_HOME) == HIGH;
    in.nose = digitalRead(pins::NOSE) == LOW;
    in.slot_a = digitalRead(pins::SLOT_A) == LOW;
    in.slot_b = digitalRead(pins::SLOT_B) == LOW;
    in.estop = digitalRead(pins::AUX_IN) == LOW;
    return in;
  }

  float vmot() override { return analogReadMilliVolts(pins::VMOT_SENSE) / 1000.0f * VMOT_DIVIDER; }
  float dockV() override { return analogReadMilliVolts(pins::DOCK_SENSE) / 1000.0f * DOCK_DIVIDER; }

  // The INA226 is read at 10 Hz (cached): I2C on every loop pass would slow down the control loop.
  float vbat() override {
    refreshIna();
    return vbat_;
  }
  float ibat() override {
    refreshIna();
    return ibat_;
  }

  void servo(uint8_t i, float deg) override {
    if (i < 2) servos_[i].write(static_cast<int>(deg));
  }

  void led(Led state) override {
    uint32_t c = 0;
    bool blink = (::millis() / 250) % 2;
    switch (state) {
      case Led::OFF: c = 0; break;
      case Led::IDLE: c = pixel_.Color(0, 0, 255); break;
      case Led::DOCKED: c = pixel_.Color(0, 255, 0); break;
      case Led::MOVING: c = pixel_.Color(255, 160, 0); break;
      case Led::FAULT: c = pixel_.Color(255, 0, 0); break;
      case Led::ESTOP: c = blink ? pixel_.Color(255, 0, 0) : 0; break;
    }
    if (c != last_color_) {
      last_color_ = c;
      pixel_.setPixelColor(0, c);
      pixel_.show();
    }
    bool beep = state == Led::ESTOP && blink && (::millis() / 2000) % 5 == 0;  // short chirp every 10 s
    digitalWrite(pins::BUZZER, beep ? HIGH : LOW);
  }

  void writeLine(const char* line) override {
    Serial.print(line);
    Serial.print('\n');
  }

 private:
  void refreshIna() {
    if (!ina_ok_ || ::millis() - ina_t_ < 100) return;
    ina_t_ = ::millis();
    vbat_ = ina_.getBusVoltage();
    ibat_ = ina_.getCurrent();
  }

  FastAccelStepperEngine engine_;
  FastAccelStepper* steppers_[AX_COUNT] = {};
  TMC2209Stepper* drivers_[AX_COUNT] = {};
  INA226 ina_{INA_ADDR};
  bool ina_ok_ = false;
  uint32_t ina_t_ = 0;
  float vbat_ = 0, ibat_ = 0;
  Servo servos_[2];
  Adafruit_NeoPixel pixel_{1, pins::STATUS_LED, NEO_GRB + NEO_KHZ800};
  uint32_t last_color_ = 1;
};

EspHal hal;
Controller controller(hal);

}  // namespace

void setup() {
  Serial.begin(115200);
  Serial.setTxTimeoutMs(0);  // never block the control loop when the Pi is not reading
  hal.begin();
  controller.begin();
}

void loop() {
  while (Serial.available() > 0) controller.feed(static_cast<char>(Serial.read()));
  controller.update();
}
