# RBG3-MOTION v1 — robot motion board

2-layer, 100 × 100 mm module carrier: ESP32-S3-DevKitC-1 + 4 × TMC2209 StepStick drivers,
switch inputs, servo/LED/buzzer/I2C outputs, VMOT and dock voltage sensing.
Spec: [`docs/spec/02-electrical.md`](../../docs/spec/02-electrical.md) §3.

| File | What |
|---|---|
| `rbg3-motion.kicad_sch` / `.kicad_pcb` / `.kicad_pro` | KiCad 10 project (schematic ERC clean, DRC: 0 errors, 0 unconnected, 0 parity) |
| `lib/rbg3.kicad_sym`, `lib/rbg3.pretty/` | Custom symbols (`ESP32-S3-DevKitC-1`, `StepStick_TMC2209`) and the DevKit socket footprint |
| `scripts/build.sh` | Rebuilds the layout from scratch: text fix-ups → placement → silkscreen (`silk.py`) → antenna keep-out → Freerouting (GND routed as tracks too, so traces cannot cut a pour pocket loose) → stitching vias → pours → DRC; fails on unrouted nets or any error-level DRC item |
| `fab/rbg3-motion-gerbers.zip` | Gerbers + Excellon drill (separate PTH / NPTH files) for JLCPCB (2 layers, 1.6 mm, 1 oz, HASL is fine) |
| `fab/rbg3-motion-bom.csv`, `fab/rbg3-motion-pos.csv` | BOM and placement file (hand assembly expected: 0805 / SOT-23 / SOD-123 / SMB + through-hole) |
| `fab/rbg3-motion-jlc-bom.csv`, `fab/rbg3-motion-jlc-cpl.csv` | JLCPCB **Economic** assembly of the 45 SMD parts on 2 of the 5 boards (the plan since spec v0.1.20) (LCSC numbers in `scripts/jlc_pcba.py`; all basic or preferred, so no extended-part fees). Check Q1, D1 and D2 orientation in the placement preview |
| `fab/rbg3-motion-schematic.pdf`, `fab/rbg3-motion.step` | Schematic print and 3D board for the robot CAD |

Rebuild: `scripts/build.sh` (needs KiCad 10 at `/Applications/KiCad`, Java 21+, Freerouting jar at
`~/.kicad-mcp/freerouting.jar` or `$FREEROUTING_JAR`). Then `scripts/export_fab.sh` regenerates `fab/`.

## Board summary

- **Power in**: J1 XT30 **VMOT** after the robot E-stop (**pad 2 = +, pad 1 = −**, matches the XT30 silkscreen), bottom-left
  corner, mating face 1.7 mm past the board edge so the plug goes in from outside,
  J2 **5 V** from the off-board 5 V/5 A buck, J3 **6 V servo** from the off-board 6 V/3 A buck.
  Bulk 470 µF + **SMBJ18A** unidirectional TVS right at J1 (cathode on VMOT: clamps ringing, and a reversed harness
  conducts and blows the 7.5 A fuse); 100 µF + 100 nF at every driver. 220 µF + 100 nF on the servo rail
  (C18/C19), 10 µF + 100 nF on +5V (C20/C21) and on +3V3 (C22/C23).
- **Test pads** TP1–TP7 (SMD, Ø 2 mm): VM, 5V, 6V, 3V3 between the drive L/R sockets; UART, EN, GND by R5/R6.
- **J13 (AUX)** takes the robot E-stop's NO contact (pressed = low): the firmware reports the press at once.
- **ESP32**: powered over USB from the Pi; its 5V pin is **not** connected. 3V3 from the DevKit feeds logic.
  Use a **90° USB-C plug** whose cable exits away from the board: the area under the USB end (y 179.5–191) is kept
  free of connectors (J12/J13 sit left of it), but J10/J11 on the bottom edge are ≈ 13 mm from the port.
- **Drivers**: UART addresses hard-wired with MS1/MS2: U2 drive-L = 0, U3 drive-R = 1, U4 Z = 2, U5 Y = 3.
  Single-wire UART on StepStick pin 4 (PDN_UART): ESP TX (GPIO9) via 1 k, RX (GPIO10) direct. CLK tied to GND.
  **JP1–JP4** (normally bridged solder jumpers between the socket rows, labelled `JPn P5 CUT`) join pin 5 to the bus,
  as the MKS TMC2209 V2.0 needs. Cut the copper strip only for a module with another signal on pin 5 (module unplugged).
- **Inputs** (J8–J13, JST-XH GND/SIG/3V3): Z_HOME, Y_HOME, NOSE, SLOT_A, SLOT_B, AUX — 10 k pull-up, 1 k series, 100 nF.
- **Outputs**: servos J14/J15 (GND, 6V, SIG, 330 Ω), WS2812 J17, buzzer J19 (low-side NPN), I2C J16 (INA226).
- **Sense**: VMOT 100 k/18 k → GPIO1 (16.8 V → 2.56 V), dock 100 k/10 k → GPIO2 (J18 pin 1; wire it to the dock + pad
  **before** the SS54, so the charger cannot backfeed it). J18 pin 2 is **not connected**: never wire dock − to the
  robot, because it goes only to the charger IN−. Home switches (J8/J9) are wired NC for fail-safe homing.
- Net classes: VMOT, GND and +6V_SERVO 1.0 mm; motor 0.6 mm; +5V/+3V3 0.5 mm; signals 0.25 mm.
- GND stitching vias on a 5 mm grid, plus one next to every through-hole GND pad that has none nearby.
  Copper keep-out under the DevKit antenna (top-right corner).
- **Silkscreen** (`scripts/silk.py`): the board name, plus function and pin order at every connector. Each StepStick socket
  has its module pin names at the corners (EN/VM at the top, DIR/GND at the bottom), and the DevKit socket is marked
  ANTENNA END / USB END, and the XT30 (J1) has + / − marks above its pads. The reference designators of J8–J15 and JP1–JP4 are on F.Fab; the function labels name those parts.

## Check before ordering (things drawn from memory, not datasheets)

1. **DevKit header row spacing.** The right-hand row is drilled at **both 22.86 mm and 25.4 mm** from the left row.
   Measure your ESP32-S3-DevKitC-1 and solder the female header into the matching row only.
2. **DevKit pinout.** Compare `lib/rbg3.kicad_sym` (J1 = pins 1–22, J3 = pins 23–44, pin 1 at the antenna end)
   against Espressif's ESP32-S3-DevKitC-1 pin layout for your board revision.
3. **StepStick pinout.** Left column EN, MS1, MS2, PDN_UART, PDN_UART2, CLK, STEP, DIR; right column VM, GND,
   2B, 2A, 1A, 1B, VDD, GND (Pololu layout). Check your TMC2209 module's silkscreen, especially pin 4 vs 5 for UART.
   JP1–JP4 come bridged (UART on pin 4 and 5); cut one only if that module uses pin 5 for something else. Insert each module so its EN pin matches the `EN` mark.
4. **Motor connector order** is 2B, 2A, 1A, 1B. If a motor runs backwards or stutters, swap one coil pair in the cable.
5. **Mounting holes**: M3 at 93 × 93 mm pitch (3.5 mm from each edge).

## Assembly and bring-up checklist

JLCPCB fits the 45 SMD parts on 2 of the 5 boards (Economic PCBA); the through-hole parts and the 3 bare
spares are hand-soldered. Tools: fine-tip iron, flux, 0.5–0.8 mm solder, tweezers,
multimeter, current-limited bench supply.

**Solder, low parts first so the board sits flat**

*JLCPCB-assembled boards: the first two items are already done; check them by eye and start at JP1–JP4.
Only the 3 bare spares need them.*

- [ ] 0805 resistors and capacitors (values in `fab/rbg3-motion-bom.csv`).
- [ ] Q1 MMBT3904 (SOT-23), D2 1N4148W (SOD-123, band as on the silkscreen), D1 SMBJ18A (SMB, **band toward VMOT**).
- [ ] JP1–JP4: check with a meter that each joins pin 5 to the UART bus (bridged on the board; nothing to solder for the MKS TMC2209 V2.0).
      Easiest before the sockets go on; always with the module unplugged.
- [ ] Through-hole, low to tall: J14/J15 servo headers → JST-XH (J4–J13, J16–J19) → StepStick sockets (8 rows) →
      DevKit female headers (**matching row only**, 22.86 or 25.4 mm) → J2/J3 terminals → J1 XT30 →
      electrolytics C1/C3/C5/C7/C9/C18 last (**long leg to the + pad**; C18 is the 220 µF / 25 V servo-rail cap).
- [ ] Clean the flux and look for bridges, especially at Q1, the socket rows and the DevKit rows.

**Harness polarity, before the first plug-in** (nothing on the board blocks a reversed lead, spec 02 §3)

- [ ] Use ready-made XT30/XT60 pigtails (leads soldered at the factory) and wire by colour only: red = +, black = −.
- [ ] Meter every finished lead on its mating pins: + must land on J1 pad 2 (the `+` mark next to J1). Check the
      battery pack's XT60 from the shop the same way.
- [ ] The first power-up is always the bench supply below, never the battery.

**Bring-up, stop at the first failure**

- [ ] Nothing plugged in: no short from VMOT, +5V, +6V_SERVO or +3V3 to GND.
- [ ] Bench supply 16.8 V, limit 0.2 A, into J1 (pad 2 = +): idle current near zero, VMOT on all four VM pins,
      nothing warm. Don't test reverse polarity (by design it blows the 7.5 A fuse through D1).
- [ ] Set and check the 5.0 V and 5.8 V (servo, "6V" rail) bucks off-board before wiring them to J2/J3. Check the
      polarity of both leads with a meter before tightening the terminals (J2/J3 are not reverse-protected), then
      read 5.0 V and 5.8 V at TP2 and TP3.
- [ ] ESP32 in, powered over USB (its 5V pin is not used): GPIO1 reads ≈ 2.56 V at 16.8 V; each input J8–J13 toggles
      (home switches are NC, so they read active until pressed). Press the E-stop: TEL `sw` bit5 sets at once.
- [ ] **VMOT off**, then fit the TMC2209s (EN pin at the `EN` mark) and connect the motors. Never plug or unplug a
      driver or a motor with VMOT on. Power up; the firmware sets motor current over UART. Check that addresses 0–3
      answer, then jog each axis slowly (motor wrong way or stuttering: swap one coil pair in its cable).

## Known cosmetic items

DRC reports 16 silkscreen-only items (reference designators touching each other or the C9 outline, the "DOCK+ V+ NC" label
touching a C20 pad, and the J1 outline clipped by the board edge). JLCPCB clips silkscreen over pads automatically; tidy them in the KiCad PCB editor if wanted. It also reports 4
`lib_footprint_mismatch` warnings for JP1–JP4, whose courtyards are removed on purpose (`scripts/fix_text.py`).
