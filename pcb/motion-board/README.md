# RBG3-MOTION v1 — robot motion board

2-layer, 100 × 100 mm module carrier: ESP32-S3-DevKitC-1 + 4 × TMC2209 StepStick drivers,
switch inputs, servo/LED/buzzer/I2C outputs, VMOT and dock voltage sensing.
Spec: [`docs/spec/02-electrical.md`](../../docs/spec/02-electrical.md) §3.

| File | What |
|---|---|
| `rbg3-motion.kicad_sch` / `.kicad_pcb` / `.kicad_pro` | KiCad 10 project (schematic ERC clean, DRC: 0 errors, 0 unconnected, 0 parity) |
| `lib/rbg3.kicad_sym`, `lib/rbg3.pretty/` | Custom symbols (`ESP32-S3-DevKitC-1`, `StepStick_TMC2209`) and the DevKit socket footprint |
| `scripts/build.sh` | Rebuilds the layout from scratch: text fix-ups → placement → silkscreen (`silk.py`) → GND pour → Freerouting → stitching vias → pours → DRC |
| `fab/rbg3-motion-gerbers.zip` | Gerbers + Excellon drill (separate PTH / NPTH files) for JLCPCB (2 layers, 1.6 mm, 1 oz, HASL is fine) |
| `fab/rbg3-motion-bom.csv`, `fab/rbg3-motion-pos.csv` | BOM and placement file (hand assembly expected: 0805 / SOT-23 / SOD-123 / SMB + through-hole) |
| `fab/rbg3-motion-schematic.pdf`, `fab/rbg3-motion.step` | Schematic print and 3D board for the robot CAD |

Rebuild: `scripts/build.sh` (needs KiCad 10 at `/Applications/KiCad`, Java 21+, Freerouting jar at
`~/.kicad-mcp/freerouting.jar` or `$FREEROUTING_JAR`). Then `scripts/export_fab.sh` regenerates `fab/`.

## Board summary

- **Power in**: J1 XT30 **VMOT** after the robot E-stop (**pad 2 = +, pad 1 = −**, matches the XT30 silkscreen), bottom-left
  corner, mating face 1.7 mm past the board edge so the plug goes in from outside,
  J2 **5 V** from the off-board 5 V/5 A buck, J3 **6 V servo** from the off-board 6 V/3 A buck.
  Bulk 470 µF + **SMBJ18A** unidirectional TVS right at J1 (cathode on VMOT: clamps ringing, and a reversed harness
  conducts and blows the 10 A fuse); 100 µF + 100 nF at every driver.
- **ESP32**: powered over USB from the Pi; its 5V pin is **not** connected. 3V3 from the DevKit feeds logic.
  Use a **90° USB-C plug** whose cable exits away from the board: the area under the USB end (y 179.5–191) is kept
  free of connectors (J12/J13 sit left of it), but J10/J11 on the bottom edge are ≈ 13 mm from the port.
- **Drivers**: UART addresses hard-wired with MS1/MS2: U2 drive-L = 0, U3 drive-R = 1, U4 Z = 2, U5 Y = 3.
  Single-wire UART on StepStick pin 4 (PDN_UART): ESP TX (GPIO9) via 1 k, RX (GPIO10) direct. CLK tied to GND.
  **JP1–JP4** (open solder jumpers between the socket rows, labelled `JPn UART P5`) join pin 5 to the bus. Bridge one
  only if that module brings PDN_UART out on pin 5; this has to be done with the module unplugged.
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
  ANTENNA END / USB END. The reference designators of J8–J15 and JP1–JP4 are on F.Fab; the function labels name those parts.

## Check before ordering (things drawn from memory, not datasheets)

1. **DevKit header row spacing.** The right-hand row is drilled at **both 22.86 mm and 25.4 mm** from the left row.
   Measure your ESP32-S3-DevKitC-1 and solder the female header into the matching row only.
2. **DevKit pinout.** Compare `lib/rbg3.kicad_sym` (J1 = pins 1–22, J3 = pins 23–44, pin 1 at the antenna end)
   against Espressif's ESP32-S3-DevKitC-1 pin layout for your board revision.
3. **StepStick pinout.** Left column EN, MS1, MS2, PDN_UART, PDN_UART2, CLK, STEP, DIR; right column VM, GND,
   2B, 2A, 1A, 1B, VDD, GND (Pololu layout). Check your TMC2209 module's silkscreen, especially pin 4 vs 5 for UART.
   If the module has UART on pin 5, bridge that socket's JP. Insert each module so its EN pin matches the `EN` mark.
4. **Motor connector order** is 2B, 2A, 1A, 1B. If a motor runs backwards or stutters, swap one coil pair in the cable.
5. **Mounting holes**: M3 at 93 × 93 mm pitch (3.5 mm from each edge).

## Known cosmetic items

DRC reports 15 silkscreen-only items (reference designators touching each other or the C9 outline, and the J1 outline clipped by the
board edge). JLCPCB clips silkscreen over pads automatically; tidy them in the KiCad PCB editor if wanted. It also reports 4
`lib_footprint_mismatch` warnings for JP1–JP4, whose courtyards are removed on purpose (`scripts/fix_text.py`).
