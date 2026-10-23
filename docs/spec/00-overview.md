# RackBotGen3 — System Overview

Delta Cup 2026 · Automation track · Regional Final, Thailand, 14 Nov 2026
Status: **Draft v0.1.27 (23 Oct 2026)** — single owner for all subsystems; peers review and give feedback.

| Doc | Content |
|---|---|
| [00-overview.md](00-overview.md) | Goals, constraints, demo workflow, architecture, weight & packing budget |
| [01-mechanical.md](01-mechanical.md) | Caddy, dummy drive, rack, spare station, robot base, Z lift, Y extractor, tray |
| [02-electrical.md](02-electrical.md) | Power tree, motion board, pin map, rack/PLC I/O, networking |
| [03-software.md](03-software.md) | Software architecture, serial protocol, Modbus map, mission state machine, vision, dashboard |
| [04-plan-budget-risk.md](04-plan-budget-risk.md) | BOM & budget, schedule, test protocol, risks, airline packing checklist |

---

## 1. Goal

A proof-of-concept **autonomous hot-swap robot for data-center drive maintenance**. When the monitoring
dashboard reports a failing drive, a small mobile robot fetches a spare caddy from a spare station,
drives to the rack, pulls the failed 3.5" caddy, inserts the spare, verifies it, and returns the failed
drive to an RMA slot. It waits and charges at the spare station, its home base, so every job starts with the
spare already in reach.

Pitch angle (judging: Innovation, Technical Viability, Impact & Sustainability, Communication):
- **Lights-out data centers**: no technician walk or truck roll per failed drive, shorter degraded-RAID window.
- **Delta inside**: a Delta PLC does rack I/O and safety, and a Delta PSU powers the rack and the charging dock.
- **Energy-aware**: measured Wh per swap, the robot sleeps on the dock, and the dashboard reports energy.

## 2. Constraints

| # | Constraint | Design response |
|---|---|---|
| C1 | Built and tested by **10 Nov 2026** (about 5 weeks) | Off-the-shelf modules, 4 steppers with a single driver type, Python on the Pi, mechanical docking instead of precision navigation |
| C2 | **≤ 500 USD** | Est. ≈ 548 USD, **over** (see 04 §1.5). Delta PLC loan unlikely; ESP32 rack controller counted (P40) |
| C3 | Manufacturable with a 400×400 mm FDM printer, grinder and drill press | 2020/2040 V-slot cut to length, printed plates/brackets; no machining beyond cutting and drilling |
| C4 | **Carry-on, 7 kg per bag, 4 members** | Flat-pack rack, removable mast; ≈ 14 kg of hardware over 4 bags (≈ 50 % margin) |
| C5 | Airline safety | Li-ion pack **≈ 50 Wh (< 100 Wh)**, in cabin, terminals protected; universal-input Delta PSU (Thailand 220 V / 50 Hz) |
| C6 | Must include **machine vision, IIoT dashboard, Delta hardware** | AprilTag docking and caddy ID, FastAPI web dashboard, Delta DVP-12SE PLC and Delta 24 V PSU |
| C7 | 3.5" HDD payload | Printed caddy plus ballasted dummy drive (≈ 750 g together); design load 1.0 kg per caddy |

## 3. Key design decisions

| Decision | Choice | Why |
|---|---|---|
| Robot type | Differential-drive mobile base + Z lift + Y extractor | Proposal commitment; shows mobility |
| Rack | 1 column × 4 bays + separate 2-slot spare station | Simplest geometry that still shows a full swap workflow |
| Tray | **2 slots stacked vertically at bay pitch (45 mm)**, slot selected by the Z lift | Pulls the failed caddy and inserts the spare in one visit, with no extra actuator (replaces the lateral shuttle in the plan) |
| Gripping | Fingers swing down (servo axis along the travel direction) into a side notch in the caddy handle block; one finger both pulls and pushes, and holds the caddy during driving | One mechanism, no clamping force; nothing passes the rack face |
| Docking | Vision approach (AprilTag) + **mechanical V-funnel** + dock switch | Funnel gives ±2 mm repeatability without precise odometry |
| Caddy | 3D-printed, own design, real 3.5" drive envelope | No latch to work, tags built in, no shipping risk |
| Compute | Raspberry Pi 3B/3B+ (owned) + ESP32-S3 motion controller | Pi does vision, logic and web; ESP32 does real-time step generation |
| Actuators | 4× NEMA17 on TMC2209 (2 direct-drive wheels, Z, Y) + 2 micro servos | One driver type, open-loop steps are repeatable, quiet; no belts on the drive |
| Rack controller | Delta DVP-12SE PLC over Modbus TCP | Delta hardware; industrial pattern (PLC = I/O and safety, PC = planning) |

## 4. Coordinate system & naming

Viewed from in front of the rack:
- **X**: left/right along the rack face (robot drives / turns on the floor)
- **Y**: in/out of the bay (extractor stroke, + toward the rack)
- **Z**: up/down (lift), measured from the floor/table surface
- Bays numbered **1 (bottom) → 4 (top)**. Spare station slots: **S1 = GOOD** (bottom), **S2 = RMA** (top).
- Tray slots: **B = lower**, **A = upper** (A = B + 45 mm).

## 5. Demo arena

Fits a table of at least **1.2 m × 0.6 m** (a floor works too). The rack and spare station face each other, about 700 mm apart.

```
  +---------------------------------------------------------------+
  |                                                               |
  |  [SPARE STATION]  <-------- ~700 mm --------->  [RACK 1x4]    |
  |   S2 RMA / S1 GOOD        robot path           bays 1-4       |
  |   tag 10, dock +      [ROBOT] (turns 180°)     tag 0, dock    |
  |   charging (home)                              Delta PLC+PSU  |
  +---------------------------------------------------------------+
               table / mat >= 1200 x 600 mm
```

## 6. Swap workflow (happy path)

The robot waits docked and charging at the spare station (home).

1. The dashboard marks **bay N = FAILED** (simulated SMART fault, or operator button). A swap job is queued.
2. The PLC turns dock power off. **Pick spare**: the robot aligns slot A with S1, extends Y, engages finger A, retracts. The spare is now in slot A, held by the finger.
3. **Undocks** (reverses 250 mm), turns 180°, approaches the rack using tag 0 and funnel-docks (robot NOSE switch).
4. **Extract**: aligns slot B with bay N and reads the caddy tag (checks the ID matches the job). Extends, engages finger B, retracts. The PLC sees bay N empty.
5. **Insert**: lowers Z by 45 mm so slot A (the upper slot) is level with bay N, extends (pushing the spare in), releases finger A, retracts. The PLC sees bay N occupied, and the dashboard shows bay N OK with the new caddy ID.
6. **Return RMA**: drives back to the spare station and docks (the PLC confirms its dock switch), aligns slot B with S2, pushes the failed caddy in, releases and retracts.
7. **Charge**: still docked at home, the PLC enables dock power and the robot charges. The job is closed with cycle time and Wh used.

Two drives per job (spare → rack → spare). Until v0.1.21 the robot lived at the rack and drove four
(rack → spare → rack → spare → rack); in the simulator the cycle drops from about 163 s to 107 s.

Target: **≤ 3 min per full swap cycle**, **≥ 95 % success over 50 cycles** (see 04 test protocol).

## 7. System architecture

```mermaid
flowchart LR
  subgraph RACK["Rack (static)"]
    PSU["Delta 24 V DIN PSU"] --> PLC["Delta DVP-12SE PLC"]
    PSU --> RLY["Dock power relay\n(PLC Y0)"]
    SW["Bay switches 1-4, E-stop"] --> PLC
    PLC --> LAMP["Status lamps R/Y/G"]
    PLC <-. Wi-Fi .-> RTR["Pi access point\n(on the robot)"]
  end
  subgraph SPARE["Spare station (home)"]
    DOCK["Dock contacts"]
    SSW["S1/S2 switches\nDock switch"]
  end
  RLY -- "2-core power lead" --> DOCK
  SSW -- "4-core signal cable" --> PLC
  subgraph ROBOT["Robot (mobile)"]
    BAT["4S Li-ion ~50 Wh\n+ BMS + INA226"] --> MB["Motion board\nESP32-S3 + 4x TMC2209"]
    BAT --> PI["Raspberry Pi 3\n+ IMX708 120° camera"]
    PI <-- USB serial --> MB
    MB --> MOT["Drive L/R, Z lift, Y extractor\n(NEMA17)"]
    MB --> SRV["Finger servos A/B"]
    CHG["4S CC/CV charger"] --> BAT
  end
  DOCK -. spring contacts .-> CHG
  PI <-- Wi-Fi: Modbus TCP --> RTR
  LAPTOP["Laptop / phone\n(dashboard)"] <-- Wi-Fi: HTTP/WebSocket --> RTR
  RTR <-- Wi-Fi --> PI
```

## 8. Weight & packing budget

Per-person carry-on limit is 7 kg (bag size ≈ 56 × 36 × 23 cm). The hardware budget below leaves room for personal items.

| Item | Mass (kg, est.) | Packs as |
|---|---|---|
| Robot base (frame, plates, 2 drive motors, wheels, casters, bumper) | 2.3 | 1 piece, ≈ 300 × 300 × 130 mm |
| Mast + Z lift + Y extractor + tray + camera (removable unit) | 1.6 | 1 piece, ≈ 450 × 200 × 120 mm |
| Robot electronics (motion board, Pi, wiring) | 0.4 | Mounted on base |
| Battery pack 4S ≈ 50 Wh (**cabin, own pouch**) | 0.35 | LiPo bag |
| Rack frame (flat-packed) + printed shelves + dock block | 1.7 | Uprights 320 mm |
| Rack electronics (Delta PSU, ESP32 rack controller or PLC, DIN rail, status lamps, E-stop) | 1.0 | Padded box |
| Spare station (2020 frame + 2 shelves + dock block) | 1.3 | Uprights 215 mm |
| Caddies + dummy drives × 6 (≈ 0.75 each) | 4.5 | 1–2 per bag |
| Table mat, tools (carry-on legal), spares, cables | 2.0 | Split |
| **Total** | **≈ 15.2** | vs 28 kg allowance → ≈ 45 % margin |

Suggested split: Bag 1 robot base + electronics + battery (≈ 3.1 kg) · Bag 2 mast unit + 2 caddies (≈ 3.1 kg) ·
Bag 3 rack frame + rack electronics + 1 caddy (≈ 3.5 kg) · Bag 4 spare station + 3 caddies + mat/tools (≈ 5.6 kg; move tools to bag 1 if personal items need room).
Weigh every bag in week 5 (see 04).

## 9. Open questions

1. ~~Subsystem owners~~ — resolved: one owner for all subsystems; peers act as reviewers.
2. Can Delta Thailand lend a DVP-12SE (or similar SE/SS2 with Ethernet)? Ask this week. If not, use the ESP32 rack fallback.
3. Do we have broken 3.5" HDDs (IT department, repair shop, e-waste)? Use 1–2 for the show, dummies for the rest.
4. Team-owned parts to reuse (Pi 3, steppers, filament, router, fasteners) — this frees budget.
5. Will the final demo be on a table or the floor? This affects the mat and edge safety.

## 10. Revision history

| Version | Date | Change |
|---|---|---|
| v0.1 | 2026-10-05 | Initial spec: concept, mechanical, electrical, software, plan/budget/risk |
| v0.1.1 | 2026-10-06 | Ownership recorded (single owner, peer review); CAD started for caddy, dummy drive, bay shelf |
| v0.1.2 | 2026-10-06 | Rack + spare station CAD: dock stop moved in front of the rack (y = −30), approach tag on the right upright, real frame lengths and masses |
| v0.1.3 | 2026-10-06 | Motion board v1 in KiCad (`pcb/motion-board`): buck modules off-board, hard-wired driver addresses, XT30 polarity, AUX input on GPIO38 |
| v0.1.5 | 2026-10-06 | Y belt drive modeled: motor shaft-down behind the rail end, 20T pulley, idler fork, carriage belt clamp; robot 4.52 kg |
| v0.1.6 | 2026-10-06 | Independent review fixes. **Mech:** idle finger parked during Y strokes; 10 mm fingers (±1 mm play), Y pull/seat/push 177/178/178.5, hard stop 187; gantry V-wheel carriages (Z in mast side grooves, Y above/below the rail); rail bracket clamped by 3 tray screws; tray screws from behind into inserts; mast on its cross member + collar socket/gusset; KFL08 (not KP08); Z-motor mount; battery box 2 × 2 cells; 3 module spaces; caster gap 6.5; stricter checks (≥ 1 mm running clearance, full strokes). **Elec:** XT30 J1 turned to the board edge, SMBJ18A TVS at J1, J12/J13 out of the USB plug path, R2 18 k, +6 V trace 1.0 mm, separate PTH/NPTH drill files, dock sense before SS54, fuse first, charger IN−-only grounding, NC home switches, TMC re-init after E-stop. **Parts:** 6 m of 2020, KFL08, fastener counts, 90° USB-C cable (P37), INA226 R010; budget ≈ 491 USD; robot 4.45 kg |
| v0.1.7 | 2026-10-06 | Mast top plate tab bolts into both front slots of the 2040 (2 × M5 at x = ±10; the single bolt at x = 0 missed the slots), E-stop box on 2 × M3 inserts. Parts: M5 heat-set inserts (~15) and M5×16/×25 tray bolts added to P11 (25 → 28 USD); budget ≈ 494 USD. Fit-test coupons (`docs/fit-test-01.md`) |
| v0.1.8 | 2026-10-06 | Robot E-stop drives a 12 V automotive relay (coil through the NC button, contact cuts VMOT) instead of breaking motor current in the button; fail-safe on a broken wire. New P38 (3 USD); budget ≈ 497 USD |
| v0.1.9 | 2026-10-07 | Software started: Pi application (`rackbot/`, sim mode) and motion firmware (`firmware/motion/`). 03 §3 completed from the implementation: `E_STOPPED`, `STATUS` reply, `busy` letters, extra events (`BOOT`, `DRIVER_RESET`, `SLOT_A/B`, `BADLINE`), `CFG` keys, busy/homed rules; §8 homing, E-stop recovery timing, LED. No parts change |
| v0.1.10 | 2026-10-07 | Motion board review fixes (02 §3): full silkscreen (connector functions, pin order, polarity, StepStick EN/VM/DIR/GND corner marks, DevKit orientation); open solder jumpers JP1–JP4 for StepStick modules with PDN_UART on pin 5; J18 pin 2 not connected (no GND next to the dock sense); TVS clamp and reverse-polarity wording corrected. No parts change |
| v0.1.11 | 2026-10-10 | Sourcing for Indonesia: P13 camera → IMX708 120° board (Camera Module 3 Wide class) from Tokopedia, 37 USD (genuine Module 3 Wide ≈ 46 USD landed from AliExpress after import tax, ≈ 76 USD locally); budget ≈ 499 USD. Backup cost-cutting options and local sources in `docs/sourcing-options.md` |
| v0.1.12 | 2026-10-10 | Local suppliers to avoid Indonesian import tax: NEMA17 ×4 (P01, 36 → 42), TMC2209 ×4 (P17, 16 → 12), ESP32-S3-DevKitC-1 (P16, 10 → 6), MG90S ×3 (P09, 8 → 4) from Tokopedia; budget ≈ 493 USD |
| v0.1.13 | 2026-10-10 | All remaining parts except the motion PCB (JLCPCB) moved to Tokopedia: P04–P06, P08, P10, P15, P18, P19, P21, P23, P27–P29, P37, P38. Drive wheels (P07) are now a printed PETG hub + TPU 95A tire (P07 not needed). Local INA226 modules carry R100, so P19 adds a 2512 R010 shunt swap. Casters set to height with printed spacers. Budget ≈ 440 USD |
| v0.1.14 | 2026-10-10 | Motion board components (P23) itemised on Tokopedia (12 → 5 USD); drive hub web cut into 5 spokes and rim thinned to 3 mm (hub 39 → 27 cm³). Budget ≈ 433 USD |
| v0.1.15 | 2026-10-10 | Datasheet cross-check (`docs/datasheets/CROSSCHECK.md`): MKS TMC2209 V2.0 has UART on pin 5, so close JP1–JP4 (P17); ESP32-S3 octal flash/PSRAM pins are 33–37; VMOT sense readable to ≈ 19 V; TMC2209 29 V operating / 32 V abs max; drive tractive force ≈ 6 N per wheel at 1.0 A (was ≈ 10 N) + shaft radial-load note; DVP-12SE11T outputs need UP/ZP wired. No cost change |
| v0.1.16 | 2026-10-10 | Orders consolidated into fewer Tokopedia shops (`docs/shopping-list.md`): extrusion, lead screw, belt and idler from Lajarus Teknik; V-wheels, spacers and pulley from Rajawali3D; ESP32, casters and switches with the motors at Rajacell; robot E-stop at CNC Store Bandung; headers and 470 µF at Putra Niaga. Travel router (P31) is not owned: GL.iNet GL-MT300N-V2 bought (38 USD). Backup prices for the Pi 3 (P12) and the Delta PLC (P25) recorded. Budget ≈ 462 USD |
| v0.1.17 | 2026-10-10 | Last generic parts sourced: 4S 30 A BMS (Rajacell), nickel strip, rocker switch, DIN rail and UK5N terminal blocks (CNC Store Bandung), silicone wire (alladinshop), brass sheet, microSD brand. Datasheets added for the Delta DRL-24V120W1EN PSU, the Songle SRD relay and the Amass XT60H. No local polyfuse ≥ 30 V found: proposed UK5-HESI fuse terminal + 3.15 A fuse (pending). Budget ≈ 460 USD |
| v0.1.18 | 2026-10-11 | Servo buck (P18) set to 5.8 V instead of 6 V: the MG90S is rated 4.8–6.0 V. The rail keeps its "6V" name; no PCB or cost change |
| v0.1.19 | 2026-10-12 | Cross-check open items closed: main fuse **7.5 A** (35E cells max 8 A); motion board JP1–JP4 now **normally bridged** (MKS TMC2209 V2.0 has UART on pin 5; cut to open), fab files regenerated; drive hub bore deepened for the 24 ± 1 mm shaft and hub fitted with a 2 mm shim against the bracket plate (keeps the radial load at ≈ 18 mm from the flange); PSU spec ≥ 75 W, chosen DRL-24V120W1EN (120 W), P24 35 → 39 USD (Rp622k). Budget ≈ 464 USD |
| v0.1.20 | 2026-10-14 | Motion PCB: JLCPCB **Economic assembly** of the 39 SMD parts on 2 of the 5 boards (`fab/rbg3-motion-jlc-bom.csv` + `-jlc-cpl.csv`); through-hole parts still hand-soldered. P22 25 → 40 USD; P23 keeps only the through-hole parts (SMD parts only for a bare spare). Budget ≈ 479 USD |
| v0.1.21 | 2026-10-18 | Print-service tolerances: caddy drive-screw slots 3.4 → **3.7 mm** (real HDDs use 6-32 UNC); mast collar socket 0.1 → **0.3 mm** per side on the 2040; drive hub bore 5.15 → **5.3 mm**. Print rule: ≥ 4 walls + ≥ 20 % gyroid/cubic (service runs 5 walls + 20 %), 100 % scale, no hole compensation (insert pilots stay tight). No parts or cost change |
| v0.1.22 | 2026-10-18 | **Charging dock moved to the spare station**, which becomes the robot's home: a job starts with the pick from S1 and ends after placing the RMA caddy in S2, so each swap drives spare → rack → spare (2 drives instead of 4; simulated cycle 163 → 107 s). Dock contacts and the dock switch (PLC X4) are fitted on the spare-station dock block only; the dock relay stays on the rack's DIN rail, so the rack E-stop still cuts dock power. Pi app: `HOME = "spare"`. Parts: P30 adds a 2-core dock power lead (8 → 9 USD), P10 now 12 + 3 spare; budget ≈ 480 USD |
| v0.1.23 | 2026-10-22 | V-wheel axles: the eccentric spacers had only 5.3 mm holes (their 7.12 mm boss could not turn), and the CAD's 7.6 / 6.6 mm wheel-to-plate gaps would have put the wheels 1.6 / 0.6 mm off the groove centre with 6 mm spacers. Now 7.3 mm eccentric holes (Z +x pair, Y lower pair) and a fixed 7 mm stack (6 mm spacer + 1 mm 5 × 8 shim) set by a pad (Z) or recess (Y) at each axle. Mini eccentric spacer is 8 mm hex. P04 adds 4 plain spacers + 10 shims (8 → 10 USD); budget ≈ 482 USD |
| v0.1.25 | 2026-10-22 | Motion PCB, from the schematic review: servo rail 220 µF / 25 V + 100 nF (C18/C19), +5V and +3V3 10 µF + 100 nF each (C20–C23), 10 k pull-down on the buzzer transistor base (R25), 7 SMD test pads (TP1–TP7), notes on the schematic sheet. The robot E-stop's NO contact goes to J13 (AUX_IN): the firmware reports a press at once (`sw` bit5) instead of waiting up to ≈ 370 ms for VMOT to decay. Layout build now routes GND as tracks too (a reroute had cut GND pour pockets loose) and fails on any DRC error. JLCPCB assembly 39 → 45 SMD parts (all basic); P23 adds the 220 µF. No cost change |
| v0.1.27 | 2026-10-23 | **Budget ≈ 482 → ≈ 548 USD (≈ 48 over)**: the Raspberry Pi 3 is not team-owned after all, so a 3B+ is bought (P12, +70), and one month of Claude Pro is added (new P39, Rp360k ≈ 23). Deck: 6 M3 holes for the electronics tray, Pi tray and battery box (positions now shared in `robot_dims.py`; the Pi tray holes had sat in its own window and over the side rail, the battery box holes over the rear cross member), and an optional laser-cut file `deck_dxf.py` → `cad/DXF/robot/deck.dxf`. Sourcing links for P03, P12, P14, P20 and the last P23 lines. PLC access looks unlikely, so the **ESP32 rack controller (new P40, 18 USD) is counted** as a contingency. **Travel router dropped** (P29, P31 not needed, −40): the Pi is the Wi-Fi access point (02 §4.3). Tower light → 3 × 22 mm 24 V panel lamps (P27 8 → 3). Budget ≈ 548 USD (≈ 530 with a PLC loan) |
| v0.1.4 | 2026-10-06 | Robot CAD v0 + checks: direct drive (axle y −135), nose z 30–90, swing-down fingers, tray camera window, caddy tag moved left, E-stop on the mast top; mass 4.49 kg; budget ≈ 478 USD |
