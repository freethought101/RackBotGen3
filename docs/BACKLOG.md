# RackBotGen3 — Backlog

Open checks and to-dos collected from the spec, the CAD and PCB work, and review notes.
Tick items off as they are done; add the result (measured value, part number) inline.

## Now (this week)

- [ ] Ask Delta Thailand for a DVP-12SE (or SE/SS2 with Ethernet) PLC loan; decide on the ESP32 rack fallback otherwise.
- [ ] Order all parts by **8 Oct** (motors, extrusion, fasteners locally if AliExpress quotes > 10 days). Re-check prices against the budget (≈ 478 USD, 04 §1).
- [ ] Team decisions: broken 3.5" HDDs available? Team-owned parts to reuse (Pi 3, steppers, filament, router)? Demo on a table or the floor?

## Before ordering the motion PCB (deadline 14 Oct)

- [ ] **DevKit header row spacing**: measure the ESP32-S3-DevKitC-1 (22.86 or 25.4 mm). The board has both; note which row to populate.
- [ ] **DevKit pinout**: compare `pcb/motion-board/lib/rbg3.kicad_sym` (J1 pins 1–22, J3 pins 23–44, pin 1 at the antenna end) with Espressif's pin layout for the board revision you bought.
- [ ] **TMC2209 module pinout**: check the module silkscreen against the Pololu layout used (EN, MS1, MS2, PDN_UART, PDN_UART2, CLK, STEP, DIR / VM, GND, 2B, 2A, 1A, 1B, VDD, GND), especially UART on pin 4 vs 5.
- [ ] **XT30 polarity**: pad 2 = +, pad 1 = −; confirm against the connector you bought and the battery lead.
- [ ] DevKit onboard RGB LED pin (GPIO38 or 48 depending on revision): confirm it does not conflict with AUX_IN (GPIO38) / BUZZER (GPIO48).
- [ ] Optional: tidy the 13 silkscreen-only DRC items in the KiCad PCB editor.
- [ ] Upload `fab/rbg3-motion-gerbers.zip` to JLCPCB and check their viewer (2 layers, 1.6 mm, 1 oz).

## Before printing the full set

- [ ] **Test T1**: print 1 caddy + 1 bay shelf; caddy slides in/out by hand with ≤ 5 N, no binding. Adjust `BAY_CHANNEL_W` / caddy rails in `cad/src/lib/dims.py` if the 1 mm/side clearance is wrong for your printer.
- [ ] **3.5" HDD bottom screw holes** (`HDD_HOLE_Y`, slotted ±3 mm in the caddy): check against a real drive.
- [ ] **KW11-3Z switch**: hole pitch (9.5 mm assumed) and lever actuation point vs the bracket slots (±2 mm) on the shelf, dock block, nose and tray.
- [ ] Dummy drive mass 600 ± 30 g with ballast (test T2).
- [ ] Reprint caddies from the current model (AprilTag recess moved to the **left** of the handle face).

## Verify against purchased hardware (then update the CAD stand-ins)

- [x] Y axis belt drive modeled (motor shaft-down behind the rail end, 20T pulley, idler fork, carriage clamp); robot checks pass.
- [ ] Y belt parts vs real hardware: 20T pulley (5 mm bore, flange Ø ≈ 16), GT2 idler on an M5 axle, belt length (≈ 0.65 m open belt), clamp slot fits the belt; tension range of the idler slot (±3 mm).
- [ ] Mast unit packs at 229 mm deep vs the 230 mm bag limit (1 mm margin): check with the real bag, or pack the Y motor separately.
- [ ] NEMA17 (42 × 42 × 40, 5 mm shaft, 31 mm hole pitch) and the direct-drive wheel hub fit (wheel x 125–149 on a 22 mm shaft).
- [ ] MG90S dimensions (22.8 × 12.2 × 28.5, shaft 5.9 mm from the end, tab size) vs the y_carriage ledges.
- [ ] V-wheels / eccentric spacers on the 2040 mast and the 2020 Y rail (not modeled; carriage arms have 1 mm gaps).
- [ ] Ball caster heights: rear 42 mm (table to rail bottom), front anti-tip 27 mm (3 mm gap).
- [ ] KP08, Tr8×2 nut and coupler dimensions vs the mast top plate and nut block.
- [ ] DevKit plugged-in height (~8.5 mm sockets) clears the RC parts underneath; Y motor ≥ 14 mm above the motion board components.
- [ ] Camera Module 3 Wide: works on Pi 3 with libcamera/Picamera2; CSI cable length (≈ 500 mm) and routing on the moving carriage.
- [ ] Rack electronics placeholders (Delta PSU, DVP-12SE, relay, router, tower light, E-stop) vs real sizes on the DIN rail.
- [ ] Delta 24 V DIN PSU: pick the exact part number from distributor stock (75–100 W, universal input).
- [ ] Detail bolt patterns on the robot printed parts once the hardware is in hand (current parts are v0 for fit).
- [ ] Cable routing: drag chain or spiral for the Z carriage (Y motor, servos, switches, camera).

## Rack / PLC bring-up

- [ ] DVP-SE Modbus addresses (M0 = 0x0800, D0 = 0x1000) against the DVP-SE manual (03 §4).
- [ ] DVP-SE input wiring (sink/source naming for S/S) before wiring the switches (02 §4.2).
- [ ] PLC watchdog trips in 2 ± 0.5 s; dock power only with dock switch + E-stop OK (test T9).

## Test protocol (04 §3)

- [ ] T1 caddy fit · [ ] T2 dummy mass · [ ] T3 Z homing/holding · [ ] T4 Y pull/push on bench · [ ] T5 drive accuracy
- [ ] T6 docking 20/20 · [ ] T7 bay alignment ≤ 1 mm · [ ] T8 vision ≥ 8 fps on Pi 3 · [ ] T9 PLC/rack · [ ] T10 E-stop
- [ ] T11 50-cycle swap ≥ 48/50 · [ ] T12 battery 1 h + dock charging · [ ] T13 dashboard · [ ] T14 pack test (every bag ≤ 7 kg)

## Travel (04 §5)

- [ ] Check each member's airline carry-on rules (7 kg, 56 × 36 × 23 cm), battery (50.4 Wh, cabin only, labeled), tools.
- [ ] Device description + Delta invitation letter printed; national flag packed.
