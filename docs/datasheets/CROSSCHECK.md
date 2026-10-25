# Datasheet cross-check (spec v0.1.15, 10 Oct 2026; motor, KFL08, KW11-3Z, MG90S, camera and casters added 25 Oct)

Spec, CAD and firmware values checked against the files in this folder. Page numbers are PDF pages.
✓ match · ✗ mismatch (fixed in the spec unless noted) · ⚠ open: no source, or a judgment call

## Robot motion

| Value (where) | Datasheet | Status |
|---|---|---|
| JK42HS40-1704: 1.7 A, 40 mm, ≥ 0.4 N·m (parts.csv P01) | 1.7 A, 1.5 Ω, 2.3 mH, 4.2 kg·cm = 0.41 N·m, 0.28 kg (P01 catalog p. 32) | ✓ (0.41 is only just ≥ 0.4) |
| 5 mm D-shaft ≥ 22 mm, 31 mm hole pitch, Ø22 boss (`drive_bracket.py`, `z_motor_mount.py`, `rail_bracket.py`) | Ø5 × 24 ± 1, 31 ± 0.2, boss Ø22 × 2, M3 depth 4.5 (p. 32) | ✓ |
| Motor mass 280 g (`vendor.py` MASS_G) | 0.28 kg (p. 32) | ✓ |
| **Bought motor is the 17HS4401S** (Lajarus, cart 24 Oct), not the JK42HS40-1704 | P01_17hs4401s_handsontec: 1.7 A, 1.5 Ω, 2.8 mH, **0.43 N·m**, 280 g, body 40 max, □42 max, 31 ± 0.1 pitch, M3 4.5 deep, boss Ø22 × 2, **shaft Ø5 × 23 ± 0.5**, flat 4.5 ± 0.1 across (p. 2) | ✓ (25 Oct) everything the CAD uses matches: the shaft ends 1 mm shorter than the JK's 24 ± 1, inside the hub bore's range, and the flat sits 2.0 from the axis as modeled (`FLAT_R` 2.2 with print shrink). Radial and axial load limits are not given, so the JK values (28 N at 20 mm, 10 N axial) remain the working estimate |
| KFL08: 48 × 27, 37 pitch, 5 flange, 13 tall, Ø22 boss (`robot_dims.KFL08`); fixed with M5 (`mast_top_plate.py`, P11) | Handsontec table: H 48, L 27, J 37, A0 12.5, **N Ø4.8, bolt M4** (P05_kfl08_handsontec p. 2; p. 1 says M5, contradicting the table). STEP model: 46.5 × 27 × 11.35 (`docs/3d-models/P05_kfl08.step`) | ⚠ envelope ✓ (CAD slightly larger). **Bolt size**: an M5 won't pass a 4.8 hole; use 2 × M4 + nuts unless the bought one has ≥ 5.3 mm holes (measure). The plate's 5.5 holes take either. M4 × 16 + nuts added to P11 (25 Oct) |
| "Torque ≈ 10 N per wheel" (01 §6.2) | 0.41 N·m at the rated 1.7 A; the run current is 1.0 A → ≈ 0.25 N·m → ≈ 6 N at r = 40 mm (p. 32, p. 33 curve) | ✗ → ≈ 6 N (still ≈ 4× the need) |
| Direct-drive wheel on the motor shaft (01 §6.2) | Max radial force **28 N at 20 mm from the flange** (p. 32). Static load ≈ 21 N per wheel with 2 loaded caddies (≈ 6 kg, 72 % on the axle), wheel centre ≈ 18 mm from the flange | ⚠ 75 % of the limit before bumps. v0.1.19: hub bore no longer bottoms on the 24 ± 1 mm shaft (it was sized for 22 mm and would have pushed the wheel 1–3 mm out); hub fitted with a 2 mm shim |
| Z 15 mm/s on Tr8×2 = 450 rpm at 12 V (empty pack) | 12 V / 1.6 A-peak curve ≈ 0.2 N·m at 450 rpm; Z needs ≈ 0.05 N·m (p. 33) | ✓ |
| TMC2209 VS limit "29 V" (02 §3.3, TVS note) | Operating 5.5–29 V; absolute max 32 V (P17_tmc2209 §20.1, §19) | ✗ wording → 29 V operating / 32 V abs max |
| Run currents 1.0 / 1.0 / 0.9 / 0.6 A rms (02 §2, `settings.h`) | 1.4 A rms design guideline per coil (§20.1) | ✓ |
| R_sense 0.11 Ω (`pins.h`) | MKS V2.0 schematic: R0805 0R11 | ✓ |
| UART address = MS1 (bit 0), MS2 (bit 1) | §"UART": SLAVEADDR from MS1 bit 0, MS2 bit 1 | ✓ |
| CLK tied to GND = internal clock | "Tie to GND using short wire for internal clock" | ✓ |
| Cutting VMOT resets the registers (02 §1, 03 §8) | §17: cycling VS resets the chip | ✓ |
| VIO from ESP32 3V3 | VCC_IO 3.00–5.25 V | ✓ |
| UART on StepStick pin 4; JP1–JP4 open (02 §3.3) | **MKS TMC2209 V2.0 (P17): PDN/UART on pin 5**; pin 4 only if the optional R8 is fitted (P17 size-pin drawing) | ✗ → JP1–JP4 are now bridged by default (v0.1.19) |
| MG90S supply (02 §3.3, P18) | Operating 4.8–6.0 V (P09 p. 1) | ✓ buck set to 5.8 V (v0.1.18) |
| MG90S 22.8 × 12.2 × 28.5, 14 g (`robot_dims.py` SERVO) | 22.5 × 12 × 35.5 (height probably includes the output spline), 13.4 g (P09 p. 1) | ⚠ measure (already in the backlog) |
| MG90S tabs 4.85 per side (`SERVO["tab"]`) | 32.5 over the tabs − 22.5 body = 5.0 per side; tabs ≈ 21 above the bottom; 35.5 to the top of the horn (P09 p. 1 drawing). The cart listing (CNC Store) gives 22 × 12 × 29 | ✓ tab span. ⚠ tab height vs the output face isn't readable on the drawing; measure on arrival (`y_carriage` ledges depend on it) |
| KW11-3Z body 20 × 10 × 6.4, M2 holes 9.5 apart (`bay_shelf`, `dock_block`, tray, nose) | Generic drawing: 19.7 × 10.6 × 6.6, mounting holes **9.5** apart (P10_kw11-3z_dimensions.png) | ✓ pitch confirmed (25 Oct). The tray pockets were closed (the switch couldn't be fitted, independent review 25 Oct): now open to the back face with M2 screws and a wire groove, sized from this drawing (hole position 3 mm from the pin edge is estimated, slotted ±1) |
| MG90S stall current vs the 3 A servo buck | Not given | ⚠ no source |

## Robot compute and I/O

| Value (where) | Datasheet | Status |
|---|---|---|
| Strapping pins 0, 3, 45, 46 (02 §3.1) | Same (P16 datasheet, pin table notes) | ✓ |
| "35–37 (PSRAM)" avoided (02 §3.1) | Octal flash/PSRAM uses **GPIO33–37** | ✗ → 33–37 (33/34 are unused anyway) |
| GPIO47/48 at 1.8 V on R8V/R16V | Same (pin table note 4) | ✓ |
| VMOT_SENSE on GPIO1, DOCK_V on GPIO2 | ADC1_CH0 / ADC1_CH1 (not ADC2, so Wi-Fi safe) | ✓ |
| VMOT divider "readable to ≈ 20 V" | Calibrated ADC range at 12 dB is 0–2.9 V → 2.9 × 118/18 = **19.0 V** (Table 5-6) | ✗ → ≈ 19 V (16.8 V reads 2.56 V ✓) |
| DOCK_V 24 V → 2.18 V | Within 0–2.9 V; readable to ≈ 32 V | ✓ |
| Onboard RGB on GPIO48/38 | DevKitC-1 schematic: RGB_CTRL on GPIO38 (v1.1) / GPIO48 (v1.0) | ✓ |
| DevKit header row spacing 22.86 / 25.4 | Not in the schematic | ⚠ measure (already in parts.csv P16) |
| Pi 3B+ 85 × 56, holes 58 × 49 at 3.5 (`pi_tray.py`) | Same (P12 mechanical drawing) | ✓ |
| Pi 5 V input, buck 5.15 V / 5 A | 5 V / 2.5 A (P12 brief) | ✓ |
| Camera ~120° diag, 102° H, focus ~150 mm, 25 × 24 (P13, 01 §6) | CM3 Wide: 120° diag, 102° H, focus 5 cm–∞, 25 × 24 × 12.4 mm (P13 brief pp. 4–5) | ✓ for the genuine Wide; ⚠ the third-party IMX708 board must be measured |
| Tray camera slot: board 25 wide in a 25.0 × 3 slot, lens centre assumed 12 above the board's bottom edge (`tray_stack.py` lines 64–66) | CM3 Wide drawing: board **25 × 23.862**, **lens 14.4 above the bottom edge** (9.46 below the top), PCB 1.12 thick, connector 2.75 deep behind the top 5.71 mm, Ø2.2 holes 21 × 12.5 apart (P13_camera-module-3-wide_mechanical-drawing; STEP in `docs/3d-models/`) | ✓ fixed 25 Oct: wirogix sent the Waveshare IMX708-120 spec, same board as the CM3 Wide. Slot now 25.8 wide with 0.4 mm per side, floor 14.8 below the lens, front window for the holder, 3.35 mm rear connector pocket, 18 mm ribbon slot (`CAM_BOARD` in `robot_dims.py`) |
| INA226 @ 0x40, ±8 A with R010, bus ≤ 16.8 V | A1 = A0 = GND → 0x40; ±81.92 mV / 10 mΩ = ±8.19 A; bus 0–36 V (P19 §5.5, Table 6-2) | ✓ |
| WS2812 VIH = 0.7 × VDD (02 §3.3) | 0.7 VDD (PCB_ws2812b) | ✓ |

## Robot power

| Value (where) | Datasheet | Status |
|---|---|---|
| 35E 3.5 Ah, 4.2 V, 50.4 Wh (02 §1, P20) | 3.6 V nominal, 3450 mAh typ / 3350 min, 4.20 V, cutoff 2.50 V → 4S = **49.7 Wh** (P20 Samsung p. 2) | ✓ < 100 Wh; put the bought cell's Wh on the airline label |
| MJ1 3.5 Ah | 3500 mAh, 3.635 V → 4S = **50.9 Wh** (P20 LG p. 3) | ✓ same note |
| Charge 1.5 A (02 §1) | 35E max charge 1.5 A (exactly at the limit); MJ1 standard 1.7 A, max 3.4 A | ✓ |
| 10 A fuse, BMS ≥ 15 A | 35E max discharge **8 A**; MJ1 10 A. Normal draw < 2 A | ✗ → 7.5 A fuse (v0.1.19) |
| Pack cutoff 12.0 V | 3.0 V/cell, above the 2.5 V minimum | ✓ (conservative) |
| Servo buck MP2482 / SY8205 on VMOT ≤ 16.8 V, 3 A | MP2482 4.5–30 V, 5 A; SY8205 4.5–30 V, 5 A (P18) | ✓ |
| Charger XL4015 CC/CV 16.8 V / 1.5 A from 24 V | XL4015E1: Vin 8–36 V (abs max 40 V), Vout 1.25–32 V, 5 A, dropout 0.3 V, 7 A switch limit (P18_xl4015 pp. 1, 4–5) | ✓ for 24 V → 16.8 V at 1.5 A. The chip has no CC loop: the 1.5 A limit comes from the module's own shunt + op-amp, so it can only be checked on the bought board (backlog: measure IN− ↔ OUT−) |
| XY-3606 5 V / 5 A (P18, P29 input ≥ 30 V) | No datasheet exists | ⚠ check the listing / board on arrival |
| SS54 in the dock path | 40 V, 5 A (PCB_ss54_mdd) vs 24 V / 1.5 A | ✓ |
| SMBJ18A: standoff 18, breakdown 20–22, clamp 29.2 V; SMBJ17A 27.6 V | VWM 18, VBR 20.0–22.1, VC 29.2 V (Vishay, Littelfuse) | ✓ |
| VMOT relay coil 0.1–0.2 A, pulls in at 12 V, OK at 16.8 V (P38) | The Bosch file is a family overview with no coil data | ⚠ no source (already in the backlog) |
| 1N4007 flyback | 1 A, 1000 V | ✓ |

## Motion board connectors and parts

| Value (where) | Datasheet | Status |
|---|---|---|
| XT30PW-M on VMOT | 15 A rated, 30 A for 1 min (PCB_xt30pw-m) | ✓ |
| XT30PW-M pad 1 = GND, pad 2 = VMOT | Pad numbering not shown in the sheet | ⚠ check the footprint vs the real part's polarity marks |
| JST-XH for motors (1.0 A) | 3 A with AWG 22 (PCB_jst-xh) | ✓ |
| MKDS 5.08 for 5 V / 5 A | 10 A, 300 V (PCB_mkds) | ✓ |
| MMBT3904 buzzer driver | 200 mA, 40 V | ✓ |

## Rack

| Value (where) | Datasheet | Status |
|---|---|---|
| PSU 75–100 W (02 §4.1) | The saved example DRP024V060W1AZ is **60 W** (P24 p. 1) | ✓ chosen DRL-24V120W1EN is 120 W (P24_delta-drl-24v120w1en); spec now ≥ 75 W (v0.1.19) |
| PLC ≈ 5 W in the power budget | DVP-12SE11T 1.5 W (P25 instruction sheet) | ✓ (budget conservative) |
| Inputs: +24 V to Xn, S/S to 0 V ("verify sink/source") | S/S supports both SINK and SOURCE wiring; on at > 15 V, 5 mA | ✓ (resolved) |
| Outputs Y0–Y3 NPN sinking | Transistor outputs need **UP = +24 V and ZP = 0 V** wired; 0.5 A/point, lamp ≤ 2.5 W/point | ✗ UP/ZP missing from 02 §4.2 → added |
| Modbus M0 = 0x0800, D0 = 0x1000 (03 §4) | Not in the instruction sheet or catalogue (needs the DVP programming manual) | ⚠ no source (verify during PLC bring-up) |
| 12SE size | 37.4 W × 90 H × 60 D, 35 mm DIN rail | ✓ |

## No datasheet at all (verify on purchased hardware; mostly already in `docs/BACKLOG.md`)
Shop questions sent 25 Oct (Tokopedia chat) for the battery pack, V-wheel/eccentric spacer/pulley, camera, E-stops,
relay, buck modules, KW11-3Z and TMC2209. Ball caster (bustan listing): **20 mm tall**, 48 × 32 base, holes 40 apart,
Ø15 ball: ✗ the CAD needs 42 (rear) and 23.5 (front), so spacers or taller casters are needed.
OpenBuilds STEP models (25 Oct, `docs/3d-models/`): mini eccentric spacer boss **Ø7.11** (✓ `ECC_HOLE_D` assumes 7.12,
now 7.9 for print shrink, ≈ 7.25 printed; 7.6 would have printed ≈ 7.0), 6 mm tall + 3.7 mm boss, hex ≈ 8.5 across flats / 10 across corners (fits the Ø12
`WHEEL_SEAT_D` pads); mini V-wheel Ø15.23 × 8.8 (✓ `VWHEEL`); GT2 20T Ø15 flange, Ø12.2 teeth, 14 wide (✓ CAD 12 / 16).
These are the OpenBuilds originals; the bought Rajawali3D clones should match but check on arrival.
V-wheels, Tr8×2 nut, coupler (seller spec Ø20 × 25 matches), GT2 pulley/idler, ball casters, 4S BMS, both E-stops,
24 V relay module, 3 A polyfuse, tower light current, dock contacts, travel router, third-party IMX708 board,
CSI cable (only a 200 mm drawing exists). Estimates with no source: robot power 4 / 12–20 W, rack budget, MASS_G masses.

## Open decisions (not changed in the spec)
1. ~~**Servo supply**~~: decided in v0.1.18, buck set to 5.8 V.
2. ~~**Drive shaft radial load**~~: decided in v0.1.19, wheel kept tight to the bracket plate (2 mm shim, bore clears the full shaft); outboard bearing only if the shafts show play.
3. ~~**Fuse vs cell rating**~~: decided in v0.1.19, 7.5 A main fuse (works with 35E and MJ1).
