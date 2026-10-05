# RackBotGen3 — Mechanical Specification

Status: Draft v0.1 · Coordinates and naming as in [00-overview §4](00-overview.md#4-coordinate-system--naming).
All dimensions in mm. Values marked **(CAD)** must be confirmed while modeling.

Manufacturing rules (all parts):
- Printed parts must fit a **400 × 400 mm** bed. Structural parts in **PETG** (4 walls, 30–40 % gyroid), fixtures and dummy shells in **PLA**, tires in **TPU 95A**.
- Fasteners: **M5** with T-nuts on 2020/2040 V-slot, **M3** with heat-set inserts in printed parts.
- Extrusions are cut with an angle grinder (cut-off disc) and squared and deburred. Holes go on the drill press.
  **No tapping, no lathe**: all extrusion joints use inside corner brackets or printed gussets.

---

## 1. Key interface dimensions (single source of truth)

Software config (`03-software.md` §6) and CAD must use these numbers.

| Symbol | Value | Meaning |
|---|---|---|
| `BAY_PITCH` | 45 | Vertical pitch of rack bays, spare slots and tray slots |
| `H_BAY[1..4]` | 150, 195, 240, 285 | Bay shelf floor height above table, bays 1–4 |
| `H_SPARE[S1,S2]` | 150, 195 | Spare station GOOD (S1) / RMA (S2) shelf floor heights |
| `SLOT_A_OFFSET` | +45 | Slot A floor = slot B floor + 45 |
| `Z` (lift coordinate) | slot B floor height above table | Range **100 … 300**, soft limits 102 … 295 |
| `Z_INSERT_OFFSET` | +1 | Tray floor 1 above shelf floor when pushing a caddy in |
| `Z_EXTRACT_OFFSET` | −1 | Tray floor 1 below shelf floor when pulling a caddy out |
| `Y` (extractor coordinate) | finger travel from home | 0 = home (caddy fully on tray), **175 = finger at notch of a seated caddy**, max 185 |
| Rack face plane | y = 0 | Front edge of shelves |
| Dock stop face | y = −30 | Robot nose tip lands here, in front of the rack (the 200 mm nose cannot pass between the uprights) |
| Tray front when docked | y = −25 | Tray overhangs the nose by 5 mm; 5 mm clearance to protruding handle blocks (y = −20) |
| Caddy envelope | 170 L × 110 W × 30 H | 150 body + 20 handle block |
| Bay channel | 116 W × 34 H clear, 150 deep | 45° × 6 lead-in at mouth |

---

## 2. Caddy (printed, ×6)

```
   TOP VIEW (handle toward robot = −y)

   y=−20        y=0                                   y=150
     +----------+-------------------------------------+
     | HANDLE   |                                     |
     | BLOCK  [N]  <- side notch (right side, x=+55)  |   110 W
     | (20)     |   drive pocket 148 x 103 x 27.6     |
     +----------+-------------------------------------+
       front face: [QR 22] text [AprilTag 24]
```

| Feature | Spec |
|---|---|
| Body | 150 L × 110 W × 30 H, open top, floor 2.5, side walls 3.5 |
| Drive pocket | 148 × 103 × 27.6 deep: fits a standard 3.5" drive (147 × 101.6 × 26.1) or the dummy |
| Side rails | 2 × 4 ribs along both bottom edges (width over rails 114), 1 mm chamfer at the rear end |
| Handle block | Front 20 mm, full width and height, solid (≥ 6 walls) |
| **Hook notch** | Right side face of handle block: **12 (y) × 8 deep (x) × full 30 height**, centered 10 from the handle front face. Edges 0.5 mm chamfered |
| Front face labels | Left: QR code 22 × 22 (caddy serial, e.g. `RBG3-C01`). Right: **AprilTag tag36h11, 24 × 24, IDs 101–106** (caddy ID). Printed on matte paper/vinyl, recessed 0.5 mm |
| Drive retention | 4 × M3 screws through the floor into the drive's bottom holes (real HDD, 6-32 also fits by hand), or press-fit for the dummy |
| Rear | Flat, for actuating the bay switch |
| Mass | ≈ 130–150 g (PETG). **Design load with drive: 1.0 kg** |

Print orientation: floor down, no supports. ≈ 6 h each.

## 3. Dummy 3.5" drive (printed + ballast, ×6, or a real broken HDD)

- Outer **147 × 101.6 × 26.1** (3.5" form factor), PLA, 2 parts (shell + screwed lid, 4 × M3).
- Internal pocket ≈ 130 × 85 × 18 (≈ 199 cm³), filled with **steel washers/nuts/BB shot set in epoxy** to reach
  **600 ± 30 g total** (real 3.5" drives weigh 450–720 g). Weigh it on a kitchen scale.
- A printed label on top makes it look like a drive ("RackBot dummy 4 TB").
- 2–3 bottom M3 heat-set inserts in the standard 3.5" bottom hole positions (CAD), so caddy screws work for dummies and real drives alike.

## 4. Rack (1 column × 4 bays)

| Item | Spec |
|---|---|
| Footprint / height | 220 W (base feet) × ≈ 335 D (dock mouth y = −85 to rear electronics y ≈ 250) × 360 H, plus tower light |
| Frame | 2020 V-slot: **2 base cross members × 220** (y 10–30 and 125–145, on the table), **4 uprights × 320** (centres x ±80, y 20 / 135), **2 top cross members × 180**. Inside corner brackets. **2.08 m total**. The shelves brace the frame front-to-back |
| Bay shelves (×4, identical part, also used ×2 on the spare station) | Printed: 4 mm floor, side channel walls (116 clear), front lead-in 45° × 6, back stop at y = 150, top of floor at `H_BAY[n]`. Bolted to uprights (2 × M5 each side) |
| Bay switch | Lever microswitch (KW11-3Z) at back stop. Pressed by the caddy rear in the last 3 mm of travel. Wired to PLC (see 02) |
| Approach tag | **tag36h11 ID 0, 50 × 50**, on a printed fin (`tag_fin`) on the outer face of the **front-right** upright, centre x ≈ 125, z = 230. On the right so it does not clash with the bay-tag strip on the left |
| Bay tags | **IDs 1–4, 16 × 16**, on a printed strip (`tag_strip_rack`) on the front face of the front-left upright, at bay floor + 15. Used for Z fine-alignment |
| Dock block (printed, `dock_block`) | Bolted (2 × M5) to the front face of the front base cross member. V-funnel 0–40 high: mouth 282 wide at y = −85, then a **10 mm parallel throat 202 wide** (nose 200 + 2) ending at the stop. Holds the nose to **±1 mm in X**. Funnel is shorter than the 60 mm nose so the robot body never enters it |
| Dock stop & switch | Stop face at **y = −30**, 220 wide, **90 high** (stays below the tray at the lowest Z). KW11-3Z dock-detect switch behind a slot at z 70–85 |
| Dock contacts | 2 × spring contacts (brass leaf or 10 mm pogo, CAD), 80 apart, center height 60, on the dock stop face. **+24 V on the right, GND on the left** (viewed from the robot) |
| Rear | DIN rail 35 mm (≈ 250) between rear uprights: Delta PSU, Delta PLC, terminal blocks, 24→5 V buck for the router. Mushroom E-stop and mini 3-color tower light on top |
| Flat-pack | Uprights unbolt from base/top (8 × M5 + brackets). Shelves stay on uprights in pairs. Max piece ≤ 400 long |
| Mass | ≈ 1.7 kg (frame 1.04, shelves 0.25, dock 0.25, tags, fasteners), ≈ 1.0 kg electronics |

## 5. Spare station

- Same dock funnel, stop and switch as the rack, but **no dock contacts**.
- Two shelves (same printed part as the rack): **S1 GOOD** at 150, **S2 RMA** at 195, each with a lever switch (to PLC, see 02; fallback is vision-only).
- Approach tag **ID 10** (50 mm) on the left fin. Slot tags **IDs 11 (S1), 12 (S2)** at 16 mm on the left strip.
- Same 2020 frame layout as the rack but **uprights × 215** (top at 255): 2 × 220 + 4 × 215 + 2 × 180 = 1.66 m. Mass ≈ 1.3 kg.
- Approach tag fin and tag strip (`tag_strip_spare`, IDs 11–12) in the same places as on the rack, so the robot uses the same approach pose.

## 6. Robot

### 6.1 Overall

| Item | Spec |
|---|---|
| Base footprint | 300 W × 300 L, plus the nose (200 W × 60 L) at the front |
| Height | ≈ 480 at the mast top. The mast unit detaches for packing |
| Mass target | **≤ 4.7 kg** without caddies (budget in 00 §8) |
| Speeds | Drive 150 mm/s cruise, 50 mm/s final approach. Z 15 mm/s. Y 60 mm/s |
| Stability | Tip-over check in CAD with 2 caddies (1.5 kg) at the highest Z, 0.3 m/s² decel. The mast and battery sit low and at the rear as counterweight |

### 6.2 Base & drive (X / turning)

- Chassis: 2020 rectangle 300 × 260 + 5 mm printed deck plates (2–4 pieces, PETG). Deck top ≈ 90.
- **Differential drive**: 2 × NEMA17 (≥ 0.4 N·m), **GT2 belt 20T → 60T (3 : 1)**, 8 mm steel shafts in 2 × KFL08 flange bearings per wheel.
- Wheels Ø80: printed PETG hub + **TPU tire**, or bought rubber 80 mm wheels with an 8 mm bore. Track width ≈ 260 (CAD).
- Wheel axle ≈ 100 behind the nose, under the tray load. **2 casters** (≈ 25 mm ball or swivel) at the rear corners.
- Resolution: 200 × 16 µsteps × 3 / (π·80) ≈ **38 µsteps/mm**.
- **Nose/bumper** (printed, 200 W × 60 L × 30–100 H): fits the dock funnel throat, tip lands on the stop at y = −30 with the tray front overhanging it by 5 mm, carries **2 copper pads 30 × 20** matching the dock contacts (80 apart, center height 60) and a front sacrificial TPU strip.

### 6.3 Z lift

- Mast: **2040 V-slot × 450**, vertical, at the rear center, bolted to the base with 2 printed brackets and 4 × M5 thumb screws (removable).
- Carriage: printed plate with 4 × V-wheels (eccentric spacers) on the 2040.
- Drive: NEMA17 at the bottom + **Tr8×2 lead screw (lead 2 mm, self-locking)** 400 long, anti-backlash nut, flexible coupler, KP08 top bearing.
  - Resolution 200 × 16 / 2 = **1600 µsteps/mm**. Speed 15 mm/s ≈ 450 rpm.
- Home switch at the bottom (Z = 100). Optional top switch.
- Load: tray stack + extractor (≈ 0.6 kg) + 2 caddies (≤ 2.0 kg design) cantilevered ≈ 150 from the mast.
- Cable chain or loose spiral for the moving cables (Y motor, servos, slot switches, Y home, **camera CSI cable 500 mm**).

### 6.4 Tray stack (2 slots, vertical)

```
  SIDE VIEW (robot left side, rack to the right)

             camera (left side, slot B level, 100 behind tray front)
                 |
   mast  carriage+-----------------------+  <- slot A (floor = Z + 45)
    ||  =========|      slot A 180 deep   |-- y = −25 (tray front)
    ||           +-----------------------+
    ||           |      slot B           |  <- slot B (floor = Z)
    ||           +-----------------------+
    ||   extractor rail along right side, finger arm reaches to y = −10
```

- One printed part (or 2 halves) ≈ 130 W × 180 D × 110 H: **2 channels 116 wide**, floors at Z and Z + 45, 45° × 6 lead-in at the front (rack side), rear stops at the caddy-home position.
- **Slot presence switch** in each floor (lever microswitch, flush), pressed when the caddy is fully home.
- Right side open for the extractor finger. Left side has the camera mount.

### 6.5 Y extractor

- 2020 rail ≈ 300 long along the **right side** of the tray stack, on the Z carriage.
- Mini V-wheel plate, **GT2 belt + 20T pulley**, NEMA17 at the rear end, idler at the front. Resolution 200 × 16 / 40 = **80 µsteps/mm**.
- **Finger arm**: printed vertical plate with **2 fingers** (heights of the slot A and slot B notches). Each finger is a 6 thick × 8 reach PETG tab on an **MG90S micro servo** that rotates 90° about a vertical axis: *parked* (parallel to the arm, outside the 114 caddy width) or *engaged* (into the notch).
- Stroke: Y = 0 (finger at notch of a caddy fully on tray, y ≈ −185) → **Y = 175** (notch of a seated caddy, y = −10). Rail allows 185.
- Y home switch at Y = 0.
- **Pull** = extend with finger parked → engage → retract. **Push** = (finger already engaged) extend → release → retract.
  The engaged finger holds the caddy on the tray while driving.
- Force: pulling ≈ 3–5 N (friction + switch). Belt and servo hold this with large margin.

### 6.6 Camera

- **Raspberry Pi Camera Module 3 Wide** (≈ 102° H) on the Z carriage, left of the tray stack, lens at **slot B level (≈ Z + 15)**, ≈ 100 behind the tray front, looking straight ahead (+y).
- Sight lines to check in CAD:
  1. Rack tag 0 / spare tag 10 visible from 700 mm down to ≈ 250 mm at the approach Z pose.
  2. Bay tags 1–4 visible at docked distance (≈ 100 mm) when slot B is aligned with that bay.
  3. Caddy tag (front-right of handle block) visible when slot B is aligned and **slot B is empty** (pick-from-spare and pre-extract verification).
- Seated-confirmation after insert uses the PLC bay switch, not the camera (the line of sight may be blocked by the caddy in slot B).

### 6.7 Electronics mounting

- Motion board, Pi 3 and buck converters on a printed electronics tray on the deck, behind the drive axle.
- Battery box low at the rear (counterweight), with an XT60 and quick access for removal at the airport.
- Robot E-stop mushroom on top at the rear, reachable from above. Main power switch and fuse beside it.

## 7. Print list (first pass)

| Part | Qty | Material | Notes |
|---|---|---|---|
| Caddy | 6 | PETG | 4 rack + 1 spare + 1 extra |
| Dummy drive shell + lid | 6 | PLA | + ballast |
| Bay shelf | 6 | PETG | 4 rack + 2 spare station |
| Dock block (funnel + stop + contacts + switch bracket) | 1 + 1 | PETG | Rack + spare station, 298 × 95 × 90, ≈ 250 g |
| Tag fin, tag strip (rack 4 tags / spare 2 tags) | 2 + 1 + 1 | PLA | |
| Robot deck plates | 2–4 | PETG | |
| Nose/bumper | 1 | PETG + TPU strip | |
| Wheel hubs + tires | 2 + 2 | PETG + TPU | (if not bought) |
| Drive motor mounts / belt tensioners | 2 | PETG | |
| Mast brackets | 2 | PETG | |
| Z carriage plate, lead nut holder | 1 | PETG | |
| Tray stack | 1 (or 2) | PETG | Largest part, ≈ 130 × 180 × 110 |
| Y carriage, finger arm, fingers | 1 + 1 + 2 | PETG | |
| Camera mount, electronics tray, battery box | 1 + 1 + 1 | PETG | |

Estimated filament: PETG ≈ 2.0 kg, PLA ≈ 0.8 kg, TPU ≈ 0.15 kg.

## 8. Purchased mechanical parts

| Part | Qty |
|---|---|
| NEMA17 stepper 42×40, ≥ 0.4 N·m, 1.5–1.7 A | 4 |
| 2020 V-slot (≈ 5.2 m total: rack 2.08, spare station 1.66, robot chassis 1.12, Y rail 0.3) | — |
| 2040 V-slot × 450 | 1 |
| Mini V-wheel kit (wheel + bearing + eccentric spacer) | 8 |
| Tr8×2 lead screw 400 + anti-backlash nut + 5→8 coupler + KP08 | 1 set |
| GT2 6 mm belt (≈ 2 m closed/open), 20T pulley 5 mm bore × 3 (2 drive motors + Y motor), 60T pulley 8 mm bore × 2 (wheel shafts), GT2 idler × 1 | set |
| 8 mm steel shaft × 100, KFL08 × 4 | 2 / 4 |
| Casters | 2 |
| MG90S servos | 2 (+1 spare) |
| Lever microswitches KW11-3Z | 12 |
| M5 T-nuts/screws/inside corner brackets, M3 screws + heat-set inserts | kit |
| Brass strip or pogo pins, copper tape/sheet | small |
