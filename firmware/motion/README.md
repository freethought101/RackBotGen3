# RBG3-MOTION firmware (ESP32-S3)

Implements `docs/spec/03-software.md` §3 (serial protocol) and §8 (motion firmware) on the
ESP32-S3-DevKitC-1 plugged into the motion board (`pcb/motion-board`, pin map 02 §3.1).

```
pio run -e esp32s3                # build
pio run -e esp32s3 -t upload      # flash (DevKit's native "USB" port, the one the Pi uses)
pio device monitor                # talk to it by hand: type "1 PING"
pio test -e native                # unit tests of the core on the Mac/PC
make -C sim                       # host simulator (used by rackbot/tests/test_firmware_link.py)
```

## Structure

| Path | Content |
|---|---|
| `lib/rbg3core/` | Hardware-independent core: protocol parser, `Controller` (commands, interlocks, homing, E-stop and driver re-configuration, VEL watchdog, telemetry), `Settings` (`CFG` keys) |
| `src/main.cpp`, `src/pins.h` | ESP32 HAL: FastAccelStepper, TMCStepper (single-wire UART, addr 0-3), ESP32Servo, INA226, WS2812, ADC dividers |
| `sim/` | `FakeHal` (stepper physics with real home switches) and `fwsim`, the core on a pseudo-terminal |
| `test/test_core/` | Unity tests (20) run on the host |

## Behaviour

- **Safety first in every loop pass**: VMOT_SENSE < 9 V → all axes halted, drivers disabled, homed flags
  cleared, the running command answers `FAIL E_ESTOP`, `EVT ESTOP`. When VMOT is back (> 10.5 V for 200 ms)
  every TMC2209 register is re-sent and verified via IFCNT; only then `EVT ESTOP_CLEAR` and `ENABLE 1` is
  accepted. GSTAT.reset is also polled every 500 ms (`EVT DRIVER_RESET`, same recovery).
- **Homing** (`HOME Y`, then `HOME Z`): seek at 10 mm/s, back off 3 mm, re-seek at 2 mm/s, set Y = 0 /
  Z = `z_home` (100). NC switches: open = pressed, so a broken wire reads "at home"; if the switch is still
  "pressed" after backing off, homing fails `E_LIMIT` instead of driving into the end stop.
  A home switch hit during a normal move halts the axis (`FAIL E_LIMIT`, `EVT LIMIT Z_HOME`).
- **Interlocks** (all enforced here, not only on the Pi): Z needs Y ≤ 2; Y > 2 needs NOSE unless `CFG bench 1`;
  FINGER needs Y ≤ 2 or Y at Y_PULL/Y_PUSH (±0.5); DRIVE/TURN/DOCK/VEL need Y ≤ 2 and Z ≤ 220 and both homed.
- **DOCK** drives forward until NOSE closes (`DONE`) or `max_mm` is travelled (`FAIL E_NODOCK`).
- **VEL** stops the wheels if no new VEL arrives within 300 ms. Motion commands answer `E_BUSY` meanwhile.
- **STOP** decelerates everything; the cancelled command answers `FAIL E_STOPPED`.
- Status LED: blue idle, green docked (DOCK_V > 20 V), amber moving, red last command failed, red blink E-stop
  (with a short buzzer chirp every 10 s).

`CFG` keys: `bench`, `lcur rcur zcur ycur` (mA), `v_drive a_drive v_turn v_z a_z v_y a_y v_dock`,
`home_fast home_slow`, `track`, `z_home y_pull y_push y_max`, `fa_park fa_engage fb_park fb_engage` (servo °).
Settings are RAM only; the Pi sends its calibration after connecting.

## Bring-up checklist (first power-on)

1. Before inserting the StepSticks: set every VREF pot low (≈ 0.5 V); after a VMOT reset the drivers run on
   VREF until re-configured.
2. Flash, open the monitor, `1 PING` → `1 OK RBG3-FW 0.1.0`. With VMOT on you should see `EVT ESTOP_CLEAR`;
   if not, the UART bus is not answering (check the 1 k on TX, PDN_UART pin 4, addresses 0-3).
3. Switches: watch `sw=` in TEL while pressing each one (bit0 Z_HOME, bit1 Y_HOME, bit2 NOSE, bit3 SLOT_A,
   bit4 SLOT_B). Unplug a home switch: its bit must read 1.
4. Directions: `2 ENABLE 1`, `3 CFG bench 1`, `4 HOME Y` with a hand on the E-stop. If an axis runs away from
   its switch, flip it in `DIR_HIGH_COUNTS_UP` (`src/pins.h`). Wheels: `DRIVE 100` must go forward.
5. Fingers: find the servo angles with `CFG fa_engage <deg>` + `FINGER A ENGAGE`, then copy them into
   `settings.h` (or have the Pi send them at startup).
6. E-stop: press it during a Z move → `FAIL E_ESTOP`, `EVT ESTOP`; release → `EVT ESTOP_CLEAR` within ~1 s.
7. INA226: `vbat` in TEL matches a multimeter; `ibat` is positive while driving (else swap the shunt leads).
