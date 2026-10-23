# RackBotGen3 — Backlog

Open checks and to-dos collected from the spec, the CAD and PCB work, and review notes.
**Live version: Notion "RackBotGen3 Backlog" database** (inside the Delta Cup 2026 hub page). This file is a snapshot.

## Now (this week)

- [ ] Ask Delta Thailand for a DVP-12SE (or SE/SS2 with Ethernet) PLC loan; decide on the ESP32 rack fallback otherwise.
- [ ] Order all parts by **8 Oct** (motors, extrusion, fasteners locally if AliExpress quotes > 10 days). Re-check prices against the budget (≈ 478 USD, 04 §1).
- [ ] Team decisions: broken 3.5" HDDs available? Team-owned parts to reuse (Pi 3, steppers, filament, router)? Demo on a table or the floor?

## Before ordering the motion PCB (deadline 14 Oct)

- [ ] **DevKit header row spacing**: measure the ESP32-S3-DevKitC-1 (22.86 or 25.4 mm). The board has both; note which row to populate.
- [ ] **DevKit pinout**: compare `pcb/motion-board/lib/rbg3.kicad_sym` (J1 pins 1–22, J3 pins 23–44, pin 1 at the antenna end) with Espressif's pin layout for the board revision you bought.
- [ ] **TMC2209 module pinout**: check the module silkscreen against the Pololu layout used (EN, MS1, MS2, PDN_UART, PDN_UART2, CLK, STEP, DIR / VM, GND, 2B, 2A, 1A, 1B, VDD, GND), especially UART on pin 4 vs 5.
- [ ] **XT30 polarity**: pad 2 = +, pad 1 = −; confirm against the connector you bought and the battery lead. The silkscreen now marks + and − above J1's pads (23 Oct). Use ready-made XT30/XT60 pigtails (P21) and wire red = +, black = −. Check the finished battery lead with a multimeter before the first plug-in, and power the board first from a current-limited bench supply (≈ 0.2 A).
- [ ] DevKit onboard RGB LED pin (GPIO38 or 48 depending on revision): confirm it does not conflict with AUX_IN (GPIO38) / BUZZER (GPIO48).
- [ ] StepStick pin 6 (CLK, tied to GND on the board) on the bought modules — some modules wire pins 5/6 differently.
- [ ] Optional: tidy the 16 silkscreen-only DRC items in the KiCad PCB editor.
- [x] Schematic review (v0.1.25): servo-rail 220 µF + 100 nF, +5V/+3V3 10 µF + 100 nF, R25 buzzer pull-down, test pads TP1–TP7, E-stop NO contact to J13 (firmware: `sw` bit5, immediate E-stop).
- [x] JLCPCB: C15850 (Samsung CL21A106KAYNNNE, 10 µF 25 V X5R 0805, C20/C22) is a basic part, in stock (checked 22 Oct; re-check in the BOM upload).
- [ ] **EE review** of the motion board and robot power path before the JLCPCB order: send `docs/review/electrical-review.md` (questions 1–12). Optional ~30 min ME review: `docs/review/mechanical-review.md`. 22 Oct: a human EE gave an overall hardware OK. His only warning was that the firmware must not set any input pin as an output or the other way round; checked, and `pins.h` and `main.cpp` match the netlist and spec 02 §3.1. Questions 1–12 are still unanswered. Of those, only the TVS margin and copper widths would change the PCB.
- [ ] Upload `fab/rbg3-motion-gerbers.zip` to JLCPCB and check their viewer (2 layers, 1.6 mm, 1 oz).

## Before printing the full set

- [ ] **Test T1** (checklist: `docs/fit-test-01.md`): print the fit coupons, then 1 caddy + 1 bay shelf; caddy slides in/out by hand with ≤ 5 N, no binding. Adjust `BAY_CHANNEL_W` / caddy rails in `cad/src/lib/dims.py` if the 1 mm/side clearance is wrong for your printer.
- [ ] **3.5" HDD bottom screw holes** (`HDD_HOLE_Y`, slotted ±3 mm in the caddy): check against a real drive.
- [ ] **KW11-3Z switch**: hole pitch (9.5 mm assumed) and lever actuation point vs the bracket slots (±2 mm) on the shelf, dock block, nose and tray.
- [ ] Dummy drive mass 600 ± 30 g with ballast (test T2).
- [ ] Reprint caddies from the current model (AprilTag recess moved to the **left** of the handle face).

## Verify against purchased hardware (then update the CAD stand-ins)

- [x] Y axis belt drive modeled (motor shaft-down behind the rail end, 20T pulley, idler fork, carriage clamp); robot checks pass.
- [ ] Y belt parts vs real hardware: 20T pulley (5 mm bore, flange Ø ≈ 16), GT2 idler on an M5 axle, belt length (≈ 0.65 m open belt), clamp slot fits the belt (real GT2 6 mm ≈ 1.38 mm thick; CAD 1.1); tension range of the idler slot (±3 mm).
- [ ] Mast unit packs at 228 mm deep **with the Y motor removed** (230 with it fitted) vs the 230 mm bag limit: check with the real bag.
- [ ] NEMA17 (42 × 42 × 40, 5 mm shaft, 31 mm hole pitch) and the direct-drive wheel hub fit (wheel x 125–149 on a 22 mm shaft).
- [ ] MG90S dimensions (22.8 × 12.2 × 28.5, shaft 5.9 mm from the end, tab size) vs the y_carriage ledges.
- [ ] Mini V-wheels / eccentric spacers (modeled Ø15.2 × 8.8, rim 1.6 mm in the groove, spacer Ø10): measure the real wheel and spacer; adjust `ZWHEEL_X` / `YWHEEL_DZ`, and `VWHEEL["w"]` / `WHEEL_STACK` if the wheel width or the spacer + shim height differ (v0.1.23).
- [ ] Ball caster heights: rear 42 mm (table to rail bottom), front anti-tip 23.5 mm (6.5 mm gap, clears the dock floor plate).
- [ ] KFL08 (48 × 27, 37 mm pitch), Tr8×2 nut (flange Ø22) and 5→8 coupler (Ø19 × 25) vs `KFL08`, `NUT_BLOCK_DZ`, `COUPLER_Z`.
- [ ] **Tr8 nut flange hole pattern**: count the flange holes (CAD assumes 3 × M3 on a 16 mm circle; many Tr8 nuts have 4) and measure the circle Ø and the hole Ø. Then update the nut block in `cad/src/robot/z_carriage.py`, possibly with M3 heat-set inserts instead of nuts underneath.
- [ ] E-stop box base: the hole spacing (CAD assumes 2 × M3, 26 mm apart, into inserts in the mast top plate).
- [ ] VMOT relay (P38): find a place for it on the electronics tray or deck; check that it pulls in at 12 V (empty battery) and stays cool at 16.8 V; check that the E-stop drops VMOT within 50 ms. Release the E-stop 20 times with VMOT loaded: the BMS must not trip on the 120–220 A capacitor inrush (if it does, add an NTC or pre-charge resistor) and the relay contact must not weld. Check that a press shows at once as `sw` bit5 / `EVT ESTOP`.
- [ ] DevKit plugged-in height (~8.5 mm sockets) clears the RC parts underneath; Y motor clears the motion board components.
- [ ] Camera Module 3 Wide: works on Pi 3 with libcamera/Picamera2; CSI cable length (≈ 500 mm) and routing on the moving carriage.
- [ ] Rack electronics placeholders (Delta PSU, DVP-12SE, relay, router, tower light, E-stop) vs real sizes on the DIN rail.
- [x] Delta 24 V DIN PSU: picked DRL-24V120W1EN (LYTE II, 120 W, universal input) — v0.1.19.
- [ ] Detail bolt patterns on the robot printed parts once the hardware is in hand (current parts are v0 for fit).
- [ ] Cable routing: drag chain or spiral for the Z carriage (Y motor, servos, switches, camera).

## From the datasheet cross-check (v0.1.15, `docs/datasheets/CROSSCHECK.md`)

- [x] JP1–JP4 for the MKS TMC2209 V2.0 (UART on pin 5): bridged by default on the board since v0.1.19 (cut to open). Still check whether R8 is fitted.
- [x] Replace `docs/datasheets/P18_xl4015.pdf` (was the XL7015 sheet); XL4015E1 8–36 V in, 5 A: fits 24 V → 16.8 V / 1.5 A. The CC limit is set by the module, so check it on the board.
- [x] Servo buck set point: **5.8 V** (MG90S 4.8–6.0 V). Set it with a meter before connecting the servos.
- [ ] Drive shafts: ≈ 21 N static per wheel vs the 28 N radial limit at 20 mm. Fit each hub with a 2 mm shim against the bracket plate (v0.1.19) and check for shaft play after testing.
- [x] Fuse vs cells: main fuse is 7.5 A (35E max discharge 8 A) — v0.1.19.
- [ ] Airline label: use the bought cell's Wh (35E 4S = 49.7 Wh, MJ1 4S = 50.9 Wh).
- [ ] XT30PW-M pad polarity: the datasheet doesn't number the pads; check the footprint (pad 1 = GND) against the real part.

## From the independent review (v0.1.6)

Fixed in the design: see 00 revision history v0.1.6. Still to verify on hardware or by test:

- [ ] Charger module: measure IN− ↔ OUT− (low-side shunt?) before wiring; dock − only to the charger IN−; charge current ≤ 1.5 A on the INA226; glue the trim pots.
- [ ] INA226 module has the 10 mΩ (R010) shunt.
- [ ] Robot E-stop DC rating ≥ 5 A at 24 V.
- [ ] Dock sense (J18) wired to the pad side, before the SS54; firmware: docked = NOSE and DOCK_V > 20 V.
- [ ] Home switches wired NC (COM → GND, NC → SIG).
- [ ] 90° USB-C cable with the cable exiting away from the board (J10/J11 are ≈ 13 mm from the port).
- [ ] WS2812 works with 3.3 V data (else SK6812 / WS2812B-V5).
- [ ] Finger/servo pull test: Y current set so a jam stalls at ≈ 15 N; 20 jammed pulls without the horn slipping (else add a carriage back-stop).
- [ ] Tray floor deflection with 1 kg at the front-right of each slot ≤ 0.5 mm.
- [x] NEMA17 radial load rating vs ≈ 20 N per wheel (direct drive): 28 N at 20 mm per the datasheet; hub bore fixed in v0.1.19.
- [ ] Rack and spare station don't slide when docking (≈ 17 N push); add a yaw criterion to T6.
- [ ] Battery pack + BMS fit the 80 × 38.5 × 47.5 box (2 × 2 cells along x).
- [ ] Buck/charger modules fit 56 × 27 × 20.
- [ ] Tray slot switch lever triggers within ≥ 4 mm past the stop face.

## Rack / PLC bring-up

- [ ] DVP-SE Modbus addresses (M0 = 0x0800, D0 = 0x1000) against the DVP-SE manual (03 §4).
- [ ] DVP-SE input wiring (sink/source naming for S/S) before wiring the switches (02 §4.2).
- [ ] PLC watchdog trips in 2 ± 0.5 s; dock power only with the spare-station dock switch + E-stop OK (test T9).
- [ ] Charging dock at the spare station (v0.1.22): fit the contacts and the dock switch on the spare-station dock block (none on the rack's); run the 2-core dock power lead from the rack relay and wire the dock switch to X4 in the 4-core spare-station cable.

## Test protocol (04 §3)

- [ ] T1 caddy fit · [ ] T2 dummy mass · [ ] T3 Z homing/holding · [ ] T4 Y pull/push on bench · [ ] T5 drive accuracy
- [ ] T6 docking 20/20 · [ ] T7 bay alignment ≤ 1 mm · [ ] T8 vision ≥ 8 fps on Pi 3 · [ ] T9 PLC/rack · [ ] T10 E-stop
- [ ] T11 50-cycle swap ≥ 48/50 · [ ] T12 battery 1 h + dock charging · [ ] T13 dashboard · [ ] T14 pack test (every bag ≤ 7 kg)

## Travel (04 §5)

- [ ] Check each member's airline carry-on rules (7 kg, 56 × 36 × 23 cm), battery (50.4 Wh, cabin only, labeled), tools.
- [ ] Device description + Delta invitation letter printed; national flag packed.

## Later (before the pitch)

- [ ] **3D digital-twin view** in the dashboard: three.js, driven by the `/ws` state (pose, Z, Y, fingers, slots, bays) so it mirrors both `--sim` and the real robot; GLB meshes from the CAD (`robot_build` poses). ~1 day. Demo asset, not a test tool (the sim has no physics). Interim option for approach debugging: 2D top-down path plot.
