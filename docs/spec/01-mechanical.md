# RackBotGen3 — Mechanical Specification

Status: Draft v0.1 · Coordinates and naming as in [00-overview §4](00-overview.md#4-coordinate-system--naming).
All dimensions in mm. Values marked **(CAD)** must be confirmed while modeling.

**Viewing the CAD.** STEP files are build outputs (gitignored), so build them first. From `cad/`:
`PYTHONPATH=src uvx --no-config --managed-python --python 3.13 --from cadgen==0.7.14 python src/robot_docked.py`
(and `src/robot_assembly.py`, `src/rack.py`, `src/spare_station.py`). Then open them in the text-to-cad CAD Viewer
(it must be running on this machine; the links refresh automatically after a rebuild):
- Robot docked at the rack, extracting from bay 2: <http://127.0.0.1:3245/?file=/Users/salehalatas/Documents/Projects/RackBotGen3/cad/STEP/robot_docked.step>
- Robot alone, travel pose: <http://127.0.0.1:3245/?file=/Users/salehalatas/Documents/Projects/RackBotGen3/cad/STEP/robot_assembly.step>

The same files open in any STEP viewer (FreeCAD, Fusion, Onshape import, or an online STEP viewer) for teammates
who don't have the CAD Viewer. Model catalog: [`cad/src/README.md`](../../cad/src/README.md).

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
| `Y` (extractor coordinate) | finger travel from home | 0 = home (caddy fully on tray), **177 = finger centred in a seated caddy's notch (pull)**, 178.5 = push target, soft max 180 |
| Rack face plane | y = 0 | Front edge of shelves |
| Dock stop face | y = −30 | Robot nose tip lands here, in front of the rack (the 200 mm nose cannot pass between the uprights) |
| Tray front when docked | y = −25 | Tray overhangs the nose by 5 mm; 5 mm clearance to protruding handle blocks (y = −20) |
| Caddy envelope | 170 L × 110 W × 30 H | 150 body + 20 handle block |
| Bay channel | 116 W × 41 H clear, 150 deep | 45° × 6 lead-in at mouth |

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
| Front face labels | Left: **AprilTag tag36h11, 24 × 24, IDs 101–106** (caddy ID, in the robot camera's view). Right: QR code 22 × 22 (caddy serial, e.g. `RBG3-C01`). Printed on matte paper/vinyl, recessed 0.5 mm |
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

Modeled in `cad/src/robot/` (parts) and `cad/src/lib/robot_build.py` (assembly, posed by Z / Y / finger
state). Frame = rack frame with the robot docked: nose tip on the stop at y = −30, robot toward −y.
All numbers live in `cad/src/lib/robot_dims.py`. `cad/checks/robot_check.py` verifies every item below.

### 6.1 Overall (as modeled, v0.1.6)

| Item | Value |
|---|---|
| Footprint | 300 W (wheels) × 360 L (incl. 60 mm nose); height ≈ 545 to the E-stop on the mast top |
| Mass | **4.45 kg** without caddies (printed 0.88, purchased 2.22, extrusions + hardware 1.35) — target ≤ 4.7 |
| CG | empty (2, −235, 152); with 2 caddies at Z max (1, −204, 198) mm |
| Tip-over | CG ≥ 69 mm behind the drive axle (needs > 6 mm at 0.3 m/s² braking), ≥ 145 mm ahead of the rear casters, ≥ 63 mm sideways |
| Packing | base unit 363 × 298 × 160; mast unit 486 × 343 × 228 **with the Y motor packed separately** (4 × M3; 230 with it fitted) → both fit a 56 × 36 × 23 cm carry-on |
| Speeds | Drive 150 mm/s cruise, 50 mm/s final approach. Z 15 mm/s. Y 60 mm/s |

### 6.2 Base & drive (X / turning)

- Chassis: 2020 side rails at x ±(55…75), z 42–62, y −390…−90; three 110 mm cross members (front, **directly under the
  mast** at y −250…−230, rear). Printed **deck** 246 × 300 × 5 at z 62–67 (one print) with a cut-out for the mast.
- **Differential drive, direct drive**: wheel hub on each NEMA17 shaft. Axle at **y = −135, z = 40**; motor bodies
  x ±(79…119) under the deck, held by a printed **drive bracket**: plate between motor face and wheel + two 10 mm
  webs bolted to the rail (M5; the head goes in through the bore from the plate side before the wheel is fitted).
  The deck screws into **M3 × 4 heat-set inserts in the web tops** at x ±105 (clear of the motor). Torque ≈ 10 N
  per wheel. Resolution 3200 µsteps / (π·80) ≈ **12.7 µsteps/mm**.
- Wheels Ø80 × 24 at x ±(125…149), 5 mm bore hubs. Wheel fronts at y −95 stay 10 mm short of the dock funnel mouth.
- Casters: 2 ball casters under the rear cross member (±65, −380); an **anti-tip ball caster under the nose** with a
  **6.5 mm** gap (3.5 mm above the dock floor plate when docked).
- **Nose/bumper** (printed, 200 W × 60 L, **z 30–90** so it stays under the tray): tip on the stop at y = −30, tray front
  overhangs 5 mm. 2 copper pad recesses 30 × 20 at x ±40, z 60 (dock contacts); dock-detect KW11 lever at x = 20.

### 6.3 Z lift

- Mast: **2040 V-slot × 420** at x ±20, y −250…−230, z 62–482, through the deck **standing on the mast cross member**.
  Printed **mast collar**: 28 mm deep close-fit socket, a +x flange with 2 × M5 into the cross member's top slot,
  2 × M5 into the mast side slots, and a **rear gusset** (4 × M5 into the mast's back slots up to z 160, rib to the
  deck). The mast unit lifts out for packing.
- **Z carriage** plate x −70…62, y −228…−222, on **4 mini V-wheels in the mast's side grooves** (axles along y at
  x ±26, z Z+14 and Z+92; eccentric spacers on the +x pair).
- Drive: NEMA17 on the deck at **(−51, −265)** in a printed **Z-motor mount** (plate on the shaft face + two walls,
  M3 + nuts through the deck) + 5→8 coupler z 117–142 + **Tr8×2 × 350 lead screw** z 131–481, anti-backlash nut in a
  side block at Z+44…64 (clears the coupler at Z min), **KFL08 flange bearing** hanging under the printed
  **mast top plate**. 1600 µsteps/mm, 15 mm/s.
- Lift range (slot B floor) **Z 102–295** (soft limits). Home switch at the bottom.

### 6.4 Tray stack (2 slots, vertical)

- One print, **122 × 197 × 90, printed standing on its back plate** (both floors vertical, no support): channels 116
  wide, slot B floor at Z, slot A floor at Z + 45; left wall full height, **right side open above a 6 mm lip** for the
  fingers. Fixed to the Z plate by **10 × M5 from behind into M5 heat-set inserts** in the back plate (columns x ±38,
  ±50 clear of the mast, Z wheels and nut block; the x = 50 column also clamps the Y-rail bracket).
- Handle stops at y = −200 (a pulled caddy's handle front rests at −196); KW11 slot-presence switches in pockets
  behind the stops (lever must reach ≥ 4 mm past the stop face).
- **Camera mount** on the left wall (lens at (−78, −115), Z + 15) and a **window in the left wall** (y −98…−38,
  z 8–26 above slot B) so the camera sees the caddy tag.

### 6.5 Y extractor

- 2020 Y rail x 84–104, y −320…−35, z Z+15…Z+35. Printed **rail bracket**: a 16 × 20 strip on the rail's inner face
  (2 × M5 into the rail's inner slot) from a **back plate clamped behind the Z plate by the 3 × M5 tray screws at
  x = 50** (80 mm apart), back to a horizontal plate behind the rail end that carries the Y motor.
- **Belt drive**: GT2 6 mm belt loop in a horizontal plane beside the rail's outer face (z Z+19…Z+25, strands at
  x ≈ 110 and 124). **20T pulley** at (117, −345) on the Y NEMA17 (**shaft pointing down**, body above the belt).
  **Idler** at (117, −44) in a printed **fork bracket** on the rail's outer face (slotted ±3 mm for tension). A
  **clamp on the carriage's outer plate** grips the inner strand. 200 × 16 / (20 × 2) = 80 µsteps/mm.
- **Y carriage** (gantry style): outer plate x 105–109 with **4 mini V-wheels above and below the rail** (axles along
  x, eccentric spacers on one of each pair), a frame over the top wheels (z Z+50…56) and the **arm on the rail's inner
  side** (x 76.5–82, 2 mm from the rail). Captured in z, x and yaw.
- **Fingers swing about an axis along y**: each MG90S (x 63.4…75.6, 2.4 mm from the tray lip) has its output shaft
  pointing +y and sits *behind* its finger, so nothing passes the rack face. Parked = finger up; engaged = finger
  pointing −x, tip at x = 50 inside the caddy notch. **Finger 10 mm thick in the 12 mm notch → ±1 mm play.**
  Pivot heights Z + 15 (slot B) and Z + 60 (slot A).
- Stroke (pivot y = −187 + Y): **Y_PULL = 177** (finger centred in a seated caddy's notch), **Y_SEAT = 178** (pushed
  caddy just seated), **Y_PUSH = 178.5** (0.5 mm preload), soft max **180**; the carriage meets the idler bracket at
  Y ≈ 187 (hard stop). A pulled caddy rests with its rear at y −26, 1 mm inside the tray front.
- **Only the working finger is engaged during a Y stroke** (both fingers ride the same carriage): the idle finger
  parks before the stroke and re-engages after Y = 0 (03 §5.1). **Pull** = extend parked → engage → retract.
  **Push** = (engaged) extend to Y_PUSH → park → retract. Engaged fingers hold the caddies while driving.

### 6.6 Camera (verified sight lines)

- IMX708 120° camera board (Camera Module 3 Wide class, ~102° × 67°), lens at (−78, −115, Z + 15), looking +y.
  Third-party board: check its outline, hole pattern and lens height against the tray mount and window on arrival.
- Bay tag strip (x −80): straight ahead (−0.9° H) at every bay. **Caddy tag (now on the left of the handle front)**:
  23° H through the tray window, slot B empty. Approach tag (right fin): 28.6° at 250 mm, 13.9° at 700 mm back-off
  with Z approach = 215.

### 6.7 Electronics mounting

- Motion board on the **electronics tray** at x 19–119, y −362…−262 (rear right; Ø9 standoffs with M3 inserts);
  **Pi 3** on its tray rear left (85 along x, y −343.5…−287.5); **battery box** far rear left, inside 80 × 38.5 × 47.5
  (4 × 18650 in 2 × 2 along x + BMS on top); **3 module spaces 56 × 27 × 20** (charger, 5 V buck, 6 V buck) on the
  deck under the tray.
- **Robot E-stop on the mast top plate** (highest, most reachable point); Y motor sits above the motion board.

### 6.8 What `robot_check.py` verifies (v0.1.6)

- Overlap **and ≥ 1 mm running clearance** between every pair of parts that move relative to each other (designed
  contacts excepted: V-wheels in grooves, shafts in hubs, belt in its clamp) over 42 poses, including intermediate
  Y positions, Y_PULL, Y_PUSH, the soft limit and just short of the hard stop; the hard stop itself.
- Docked lift sweep carrying two caddies at their real on-tray position (finger play included): no contact, ≥ 1 mm
  from the rack and its caddies.
- Full pull and push strokes at every bay and spare slot, through intermediate positions, with the caddy (and dummy)
  moving with the finger (step down/up at the shelf edge), the idle finger parked and the other caddy on the tray.
- Push seats the caddy at Y_SEAT; pull starts centred in the notch; the pulled caddy stays inside the tray.
- Camera sight lines, mass/CG/tip-over, packing, print bed.

## 7. Print list (first pass)

| Part | Qty | Material | Notes |
|---|---|---|---|
| Caddy | 6 | PETG | 4 rack + 1 spare + 1 extra |
| Dummy drive shell + lid | 6 | PLA | + ballast |
| Bay shelf | 6 | PETG | 4 rack + 2 spare station |
| Dock block (funnel + stop + contacts + switch bracket) | 1 + 1 | PETG | Rack + spare station, 298 × 95 × 90, ≈ 250 g |
| Tag fin, tag strip (rack 4 tags / spare 2 tags) | 2 + 1 + 1 | PLA | |
| Robot deck | 1 | PETG | 246 × 300 × 5 |
| Nose/bumper | 1 | PETG | + TPU strip |
| Drive bracket | 2 | PETG | one mirrored |
| Mast collar (socket + flange + rear gusset), mast top plate (tab: 2 × M5 into both front slots; 2 × M3 inserts for the E-stop box) | 1 + 1 | PETG | |
| Z-motor mount | 1 | PETG | |
| Z carriage (plate + nut block; V-wheels on axles through the plate) | 1 | PETG | |
| Tray stack (incl. camera mount) | 1 | PETG | 122 × 197 × 90, print standing on the back plate; 10 × M5 heat-set inserts |
| Rail bracket (back plate + strip + horizontal Y motor plate) | 1 | PETG | |
| Y idler bracket (fork) | 1 | PETG | |
| Y carriage (outer wheel plate + frame + finger arm + belt clamp) | 1 | PETG | |
| Fingers (10 mm thick) | 2 | PETG/nylon | |
| Electronics tray, Pi tray, battery box | 1 + 1 + 1 | PETG | |

Estimated filament: PETG ≈ 2.0 kg, PLA ≈ 0.8 kg, TPU ≈ 0.15 kg.

## 8. Purchased mechanical parts

| Part | Qty |
|---|---|
| NEMA17 stepper 42×40, ≥ 0.4 N·m, 1.5–1.7 A | 4 |
| 2020 V-slot (4.96 m of cuts + ≈ 3 mm kerf per cut → buy 6 × 1 m: rack 2.08, spare station 1.66, robot chassis 2 × 300 + 3 × 110, Y rail 285) | 6 × 1 m |
| 2040 V-slot × 420 | 1 |
| Mini V-wheel kit (wheel + bearing + eccentric spacer) | 8 |
| Tr8×2 lead screw 350 + anti-backlash nut + 5→8 coupler + **KFL08** 2-bolt flange bearing | 1 set |
| GT2 6 mm belt (≈ 0.8 m), 20T pulley 5 mm bore × 1, GT2 idler × 1 (Y axis only) | set |
| Wheels Ø80 with 5 mm bore hubs (direct drive) | 2 |
| Ball casters (2 rear, 1 front anti-tip) | 3 |
| MG90S servos | 2 (+1 spare) |
| Lever microswitches KW11-3Z (13 used + 2 spare) | 15 |
| M5 T-nuts (~120)/screws/inside corner brackets (~48), M3 screws + nuts + heat-set inserts | kit |
| Brass strip or pogo pins, copper tape/sheet | small |
