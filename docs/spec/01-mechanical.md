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
- Printed parts must fit a **400 × 400 mm** bed. Structural parts in **PETG** (≥ 4 walls, ≥ 20 % gyroid or cubic infill; the print service's 5 walls + 20 % is fine), fixtures and dummy shells in **PLA**, tires in **TPU 95A**.
- Hole clearances are already in the CAD (M3 bolt 3.4, M5 bolt 5.3, drive screws 3.7, shaft bores +0.3, sockets on extrusions +0.3 per side).
  **Print at 100 % scale with no hole compensation**: heat-set insert pilots (M3 4.0, M5 6.4) must stay tight.
  Check a new printer or service with the hole coupon first (`docs/fit-test-01.md`).
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
| Drive retention | 4 screws through **3.7 mm slots** in the floor into the drive's bottom holes: standard **6-32 UNC** HDD screws for a real drive, M3 for the dummy's inserts |
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
| Footprint / height | 220 W (base feet) × ≈ 335 D (dock mouth y = −85 to rear electronics y ≈ 250) × 360 H, plus the status lamp box |
| Frame | 2020 V-slot: **2 base cross members × 220** (y 10–30 and 125–145, on the table), **4 uprights × 320** (centres x ±80, y 20 / 135), **2 top cross members × 180**. Inside corner brackets. **2.08 m total**. The shelves brace the frame front-to-back |
| Bay shelves (×4, identical part, also used ×2 on the spare station) | Printed: 4 mm floor, side channel walls (116 clear), front lead-in 45° × 6, back stop at y = 150, top of floor at `H_BAY[n]`. Bolted to uprights (2 × M5 each side) |
| Bay switch | Lever microswitch (KW11-3Z) at back stop. Pressed by the caddy rear in the last 3 mm of travel. Wired to PLC (see 02) |
| Approach tag | **tag36h11 ID 0, 50 × 50**, on a printed fin (`tag_fin`) on the outer face of the **front-right** upright, centre x ≈ 125, z = 230. On the right so it does not clash with the bay-tag strip on the left |
| Bay tags | **IDs 1–4, 16 × 16**, on a printed strip (`tag_strip_rack`) on the front face of the front-left upright, at bay floor + 15. Used for Z fine-alignment |
| Dock block (printed, `dock_block`) | Bolted (2 × M5) to the front face of the front base cross member. V-funnel 0–40 high: mouth 282 wide at y = −85, then a **10 mm parallel throat 202 wide** (nose 200 + 2) ending at the stop. Holds the nose to **±1 mm in X**. Funnel is shorter than the 60 mm nose so the robot body never enters it |
| Dock stop & switch | Stop face at **y = −30**, 220 wide, **90 high** (stays below the tray at the lowest Z). The switch bracket and slot (z 70–85) are printed, but **no switch is fitted at the rack**: the PLC dock input (X4) belongs to the charging dock at the spare station, and the robot's NOSE switch confirms docking here |
| Dock contacts | None since v0.1.22: the recesses are printed (same part as the spare station) but left empty. The robot charges at the spare station (§5) |
| Rear | DIN rail 35 mm (≈ 250) between rear uprights: Delta PSU, Delta PLC, terminal blocks, ESP32 rack controller (P40) if no PLC. Mushroom E-stop and the 3-lamp status box on top |
| Flat-pack | Uprights unbolt from base/top (8 × M5 + brackets). Shelves stay on uprights in pairs. Max piece ≤ 400 long |
| Mass | ≈ 1.7 kg (frame 1.04, shelves 0.25, dock 0.25, tags, fasteners), ≈ 1.0 kg electronics |

## 5. Spare station

- **Home and charging dock.** Same dock block as the rack, fitted with the **KW11-3Z dock-detect switch** (to PLC X4)
  and the **dock contacts**: 2 × spring contacts (brass leaf or 10 mm pogo, CAD), 80 apart, center height 60, on the
  dock stop face. **+24 V on the right, GND on the left** (viewed from the robot). The robot waits here between jobs.
- Dock power comes from the dock relay on the rack's DIN rail (PLC Y0) over a 2-core lead; the S1, S2 and dock
  switches share a 4-core cable to the PLC (02 §4).
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
  The deck screws into **M3 × 4 heat-set inserts in the web tops** at x ±105 (clear of the motor). Tractive force
  ≈ 6 N per wheel at the 1.0 A run current (≈ 0.25 N·m of the 0.41 N·m rated at 1.7 A). The motor allows 28 N radial
  load at 20 mm from the flange; the wheel centre is ≈ 18 mm out and carries ≈ 21 N with two loaded caddies. To keep
  the load that close, the hub's blind bore clears the full 24 ± 1 mm shaft (the shaft end does not locate the hub):
  **fit each hub with a 2 mm shim against the bracket plate** before tightening the set screw (gap ≤ 2 mm). If a
  shaft shows play after testing, add an outboard bearing. Resolution 3200 µsteps / (π·80) ≈ **12.7 µsteps/mm**.
- Wheels Ø80 × 24 at x ±(125…149), **printed**: PETG hub on the 5 mm D-shaft (M3 set screw into a heat-set insert,
  onto the flat) + TPU 95A tire stretched over the rim. Wheel fronts at y −95 stay 10 mm short of the dock funnel mouth.
- Casters: 2 ball casters under the rear cross member (±65, −380); an **anti-tip ball caster under the nose** with a
  **6.5 mm** gap (3.5 mm above the dock floor plate when docked).
- **Nose/bumper** (printed, 200 W × 60 L, **z 30–90** so it stays under the tray): tip on the stop at y = −30, tray front
  overhangs 5 mm. 2 copper pad recesses 30 × 20 at x ±40, z 60 (dock contacts); dock-detect KW11 lever at x = 20.

### 6.3 Z lift

- Mast: **2040 V-slot × 420** at x ±20, y −250…−230, z 62–482, through the deck **standing on the mast cross member**.
  Printed **mast collar**: 28 mm deep socket (0.3 mm per side on the 2040, as printed pockets come out undersize), a +x flange with 2 × M5 into the cross member's top slot,
  2 × M5 into the mast side slots, and a **rear gusset** (4 × M5 into the mast's back slots up to z 160, rib to the
  deck). The mast unit lifts out for packing.
- **Z carriage** plate x −70…62, y −228…−222, on **4 mini V-wheels in the mast's side grooves** (axles along y at
  x ±26, z Z+14 and Z+92; eccentric spacers on the +x pair, in 7.3 mm holes).
- **V-wheel axle stack** (both carriages): plate → 6 mm spacer (mini eccentric, 8 mm hex, or plain) → 1 mm shim
  5 × 8 on the bearing's inner ring → wheel → nylock nut. The plates have a 0.6 mm pad (Z) or 0.4 mm recess (Y)
  around each axle so this 7 mm stack puts every wheel on its groove centre (`WHEEL_STACK` in `robot_dims.py`).
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
  x, eccentric spacers on the lower pair in 7.3 mm holes), a frame over the top wheels (z Z+50…56) and the **arm on the rail's inner
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
| Wheel hub + tire | 2 + 2 | PETG + TPU 95A | Ø80 × 24 assembled; tire printed slowly on a direct-drive extruder (or a local print service) |
| Caster spacers | 3 | PETG | rear to 42 mm total, front to 27 mm; size after measuring the bought casters |
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

IDs refer to [`docs/parts.csv`](../parts.csv) (supplier, cost and order status are kept there).

| ID | Part | Qty | Spec | Used for |
|---|---|---|---|---|
| P01 | NEMA17 stepper | 4 | 42 × 42 × 40, ≥ 0.4 N·m holding, 1.5–1.7 A, 5 mm D-shaft ≥ 22 mm (chosen: JK42HS40-1704) | Drive L/R (wheel hub direct on the shaft), Z lift, Y extractor |
| P02 | 2020 V-slot | 6 × 1 m | 4.96 m of cuts + ≈ 3 mm kerf per cut. Rack 2 × 220, 4 × 320, 2 × 180; spare station 2 × 220, 4 × 215, 2 × 180; robot 2 × 300 (side rails), 3 × 110 (cross members), 1 × 285 (Y rail) | Rack and spare-station frames, robot chassis, Y rail |
| P03 | 2040 V-slot | 1 × 420 | | Z mast |
| P04 | Mini V-wheel kit | 8 | Mini V-wheel (105zz) for 20xx V-slot; 4 mini eccentric spacers (8 mm hex, 6 mm) + 4 plain 6 mm spacers + 10 shims 5 × 8 × 1 | Z carriage (4, in the mast's side grooves), Y carriage (4, on the Y rail) |
| P05 | Tr8×2 lead-screw set | 1 | Tr8×2 (2 mm lead) × 350, anti-backlash nut, 5→8 flexible coupler, **KFL08** 2-bolt flange bearing | Z lift (1600 µsteps/mm) |
| P06 | GT2 belt set | 1 | GT2 6 mm belt (≈ 0.8 m used, buy ≥ 1 m), 20T pulley 5 mm bore, toothless idler 5 mm bore | Y extractor (80 µsteps/mm) |
| P08 | Ball caster | 3 | Metal ball caster, raised with printed spacers to 42 mm (rear) / 27 mm (front) | 2 rear supports, 1 anti-tip under the nose |
| P09 | MG90S servo | 2 (+1 spare) | 22.8 × 12.2 × 28.5, metal gear, run at 5.8 V | Extractor fingers A/B |
| P10 | KW11-3Z lever microswitch | 15 (12 + 3 spare) | 20 × 10 × 6.4, SPDT, lever | 4 bays, 2 spare slots, spare-station dock, robot nose, tray slots A/B, Z and Y home |
| P11 | Fastener kit | kit | M5 T-nuts (~120), M5 button heads 8/10/12, M5 × 16 (7) + M5 × 25 (3) for the Z carriage to the tray, 2020 inside corner brackets (~48), M3 screws + nuts, M3 heat-set inserts (~60), M5 heat-set inserts (~15, tray back plate) | Everything |
| P30 | Dock contacts | small | Brass strip / 0.5 mm sheet or 10 mm pogo pins; copper sheet for the robot pads | Charging contacts (dock stop face and nose) |

## 9. Part reference

One row per printed part: what it does, what it fastens to and how it prints. Function and position are described
by subsystem in §2–6; quantities and materials match §7. Sizes are the CAD bounding box (x × y × z in the part's
own frame). Volumes are the solid CAD volume; `robot_check.py` estimates printed mass as volume × 0.64 g/cm³
(PETG at ~50 % effective fill). Parts with more walls (caddy handle block) come out heavier than that, which is
why §2 gives 130–150 g for the caddy.

### 9.1 Robot (`cad/src/robot/`)

| Part (script) | Qty · material · print | Size · vol. | What it does | Mounts to / fasteners |
|---|---|---|---|---|
| Nose / bumper (`nose.py`) | 1 · PETG (+ TPU strip, not modeled) | 200 × 60 × 60 · 161 cm³ | Fits the 202 mm dock throat (±1 mm in X), its tip stops at y = −30. Carries the 2 copper charging pads (x ±40, z 60) and the dock-detect KW11 (lever at x = 20). z 30–90, so it stays under the tray | Front 2020 cross member (y −110…−90) |
| Deck (`deck.py`) | 1 · PETG · flat | 246 × 300 × 5 · 355 cm³ | Main plate. Carries the mast collar, Z-motor mount, electronics/Pi trays and battery box, and caps the drive brackets. Has a cut-out for the mast. Laser-cut option (undecided): `deck_dxf.py` → `cad/DXF/robot/deck.dxf`, same outline and holes, for 5 mm acrylic | Sits on the 2020 side rails at z 62–67; M3 into the inserts in the drive-bracket webs; trays and battery box M3 + nut through the deck (6 holes) |
| Drive bracket (`drive_bracket.py`) | 2 (one mirrored) · PETG | 48 × 64 × 48 · 21 cm³ | Holds a drive NEMA17 under the deck, shaft out to the wheel | Motor on the outer plate; 2 webs to the side rail's outer face (M5 + T-nut, head inserted through the bore before the wheel goes on); M3 × 4 inserts in the web tops for the deck |
| Drive hub (`drive_wheel.py`) | 2 · PETG · outboard face down | Ø75 × 24 · 27 cm³ | Wheel hub direct on the 5 mm D-shaft (axle y −135, z 40), bore Ø5.3 (the set screw takes up the play). The blind bore clears the 24 ± 1 mm shaft, so the hub is located by a 2 mm shim against the bracket plate (wheel centre 18 mm from the flange, under the motor's 28 N radial rating at 20 mm) | M3 set screw onto the shaft flat, in a radial M3 × 4 insert; Ø8 rim window for the iron and hex key |
| Drive tire (`drive_wheel.py`) | 2 · TPU 95A · print slowly, direct drive | Ø80 × 21 · 21 cm³ | Traction, Ø80 × 24 wheel assembled | 0.5 mm undersize on the rim seat, held between two 1.5 mm lips; Ø4 hole lined up with the set-screw window |
| Mast collar (`mast_collar.py`) | 1 · PETG | 78 × 57 × 93 · 39 cm³ | Locates and braces the foot of the 2040 mast (28 mm deep socket, 0.3 mm per side). The rear gusset takes the forward tilt of the loaded mast in tension | Flange 2 × M5 through the deck into the mast cross member's top slot; 2 × M5 into the mast side slots; gusset 4 × M5 into the mast's back slots (to z 160) with a rib to the deck. Undo these to lift the mast unit out for packing |
| Mast top plate (`mast_top_plate.py`) | 1 · PETG | 92 × 65 × 36 · 40 cm³ | Caps the mast. Holds the KFL08 bearing (hanging below) for the top of the lead screw, and the robot E-stop box on top | Front tab 2 × M5 + T-nuts into both front slots (no tapping); 2 × M3 inserts for the E-stop box |
| Z-motor mount (`z_motor_mount.py`) | 1 · PETG | 65 × 40 × 45 · 18 cm³ | Fixes the Z NEMA17 at (−51, −265) in x, y and yaw and stops it lifting; the body rests on the deck | 4 × M3 into the motor face; M3 + nuts through the deck at the wall feet |
| Z carriage (`z_carriage.py`) | 1 · PETG | 132 × 56 × 110 · 108 cm³ | Lift plate riding the mast on 4 mini V-wheels (eccentric spacers on the +x pair, 7.3 mm holes; 0.6 mm spacer pads). Carries the anti-backlash nut on a raised side block (Z+44…64, clears the coupler at Z min) | V-wheel axles along y through the plate; 10 × M5 from behind into the tray's back-plate inserts (the x = 50 column also clamps the rail bracket) |
| Tray stack (`tray_stack.py`) | 1 · PETG · standing on its back plate, no support | 153 × 197 × 90 incl. camera mount (tray body 122 wide) · 438 cm³ | Two caddy slots at 45 pitch (B at Z, A at Z + 45). Left wall full height with the camera mount and window; right side open above a 6 mm lip for the fingers. Handle stops at y = −200 with KW11 slot-presence switches behind | 10 × M5 heat-set inserts in the back plate, screws from the Z carriage |
| Rail bracket (`rail_bracket.py`) | 1 · PETG | 92 × 140 × 90 · 84 cm³ | Hangs the Y rail and Y motor off the lift, so the pull/push loads go into the tray/Z-plate sandwich. Carries the Y NEMA17 (shaft down) behind the rail end | Back plate clamped by the 3 × M5 tray screws at x = 50; strip 2 × M5 into the rail's inner slot |
| Y idler bracket (`y_idler_bracket.py`) | 1 · PETG | 24 × 15 × 22 · 3 cm³ | Fork holding the GT2 idler at (117, −44) in the belt plane; also the carriage's hard stop at Y ≈ 187 | M5 + T-nut on the rail's outer face, slotted ±3 mm for belt tension; idler on an M5 bolt |
| Y carriage (`y_carriage.py`) | 1 · PETG | 51 × 84 × 82 · 34 cm³ | Gantry carriage on the Y rail (4 mini V-wheels above and below, captured in z, x and yaw). The arm on the rail's inner side carries both MG90S; the belt clamp grips the inner strand | V-wheel axles along x (eccentric on the lower pair, 7.3 mm holes; 0.4 mm spacer recesses); servo tabs screw to ledges on the arm |
| Finger (`finger.py`) | 2 · PETG or nylon | 10 × 10 × 25 · 2 cm³ | Swings down into the caddy's 12 mm side notch (10 thick → ±1 mm play) to pull, push and hold the caddy on the tray. Pivots at Z + 15 (slot B) and Z + 60 (slot A) | Screws to the MG90S horn |
| Electronics tray (`electronics_tray.py`) | 1 · PETG | 108 × 108 × 10 · 22 cm³ | Standoffs for the 100 × 100 motion board, rear right (x 19–119, y −362…−262) | Board M3 at 93 × 93 into Ø9 standoffs with inserts; tray on the deck |
| Pi tray (`pi_tray.py`) | 1 · PETG | 91 × 57 × 10 · 11 cm³ | Standoffs for the Raspberry Pi 3, rear left | Pi on the 58 × 49 hole pattern; tray on the deck |
| Battery box (`battery_box.py`) | 1 · PETG | 85 × 44 × 50 · 35 cm³ | Holds the 4 × 18650 pack + BMS low at the far rear left (counterweight). Open top with a strap slot so the pack lifts out for the airport | On the deck; pack held by a strap |

### 9.2 Rack, spare station and caddies (`cad/src/`)

| Part (script) | Qty · material · print | Size · vol. | What it does | Mounts to / fasteners |
|---|---|---|---|---|
| Caddy (`caddy.py`) | 6 · PETG · floor down, no supports | 114 × 170 × 30 · 137 cm³ | Carries a 3.5" drive or the dummy. Side rails run in the bay channel; the hook notch takes the finger; the front face has the AprilTag (ID 101–106) and QR. The rear presses the bay switch (§2) | Drive with 4 × 6-32 UNC (real drive) or M3 (dummy) through 3.7 mm floor slots; dummy press-fit |
| Dummy drive shell (`dummy_drive_shell.py`) | 6 · PLA · floor down | 102 × 147 × 26 · 80 cm³ | 3.5" drive stand-in, filled with steel ballast in epoxy to 600 ± 30 g total (§3) | M3 heat-set inserts at the 3.5" bottom-hole positions for the caddy screws |
| Dummy drive lid (`dummy_drive_lid.py`) | 6 · PLA · flat | 95 × 141 × 2 · 24 cm³ | Closes the ballast pocket; label recess on top | 4 × M3 into the shell |
| Bay shelf (`bay_shelf.py`) | 6 (4 rack + 2 spare) · PETG · floor down | 140 × 168 × 24 · 87 cm³ | Bay floor with 116 clear channel, 45° × 6 lead-in, back stop at y = 150, KW11 bay-switch bracket. Also braces the frame front-to-back | 2 × M5 button heads + T-nuts per side into the uprights; heads in counterbores reached through the channel |
| Dock block (`dock_block.py`) | 2 (rack + spare) · PETG · floor down | 298 × 95 × 90 · 354 cm³ | V-funnel (282 mouth) + 10 mm throat (202) that centres the nose to ±1 mm; stop face at y = −30; recesses for the charging contacts and the dock-detect switch bracket (both fitted on the spare-station copy only) | 2 × M5 into the front face of the front base cross member |
| Approach-tag fin (`tag_fin.py`) | 2 · PLA | 70 × 23 × 70 · 20 cm³ | Holds the 50 mm approach tag (ID 0 rack, ID 10 spare) for station approach | Outer face of the front-right upright |
| Tag strip, rack (`tag_strip_rack.py`) | 1 · PLA | 20 × 3 × 167 · 9 cm³ | Bay tags IDs 1–4 (16 mm) at bay floor + 15, for Z fine-alignment | Front face of the front-left upright |
| Tag strip, spare (`tag_strip_spare.py`) | 1 · PLA | 20 × 3 × 89 · 5 cm³ | Slot tags IDs 11–12 | Front face of the front-left upright |

Test prints and check assemblies (not part of the build): `fit_coupons.py` (fit test 1, see
[`docs/fit-test-01.md`](../fit-test-01.md)), `bay_fit.py`, `rack.py`, `spare_station.py`, `robot_assembly.py`,
`robot_docked.py`.

### 9.3 Listed but not modeled yet

- **Caster spacers** (×3, PETG, §7): the assembly models each caster at its total height; the spacers are sized after measuring the bought casters (rear to 42 mm total, front to 27 mm).
- **Nose TPU strip** (§7): bumper strip on the nose.
- **Robot E-stop box**: a bought part on the mast top plate; the assembly shows only a 40 mm box stand-in (`lib/robot_build.py`).
