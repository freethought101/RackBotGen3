"""Robot checks against docs/spec: self-interference, docking/extraction at every bay and spare slot,
caddy carrying, camera sight lines, mass/CG/tip-over, packing and print-bed fit.

Run from cad/:  PYTHONPATH=src python checks/robot_check.py
"""

import math
from itertools import combinations

from cadgen import build123d as bd
from cadgen.geometry import closest_points, overlap_volume

from caddy import caddy
from lib.dims import CADDY_H, H_BAY, H_SPARE, NOTCH_DEPTH, NOTCH_FROM_FRONT, NOTCH_L, TAG_APPROACH_Z, TAG_FACE_Y
from lib.robot_build import EXTRUSIONS, base_parts, extractor_parts, lift_parts
from lib.robot_dims import (AXLE_Y, CAM_DZ, CAM_LENS, CASTER_REAR, FINGER_DZ, FINGER_LEN, FINGER_X, SLOT_A_DZ,
                            WHEEL_X, Y_MAX, Y_NOTCH_HOME, Z_MAX, Z_MIN)
from rack import rack
from spare_station import spare_station

failures = []
EXPECTED_CONTACT = {frozenset(p) for p in [("kp08", "leadscrew_tr8x2"), ("nema17:z", "coupler")]}
PRINTED_DENSITY = 1.27e-3 * 0.5          # PETG, ~50 % effective fill
EXTRUSION_G_PER_MM = {"2020": 0.5, "2040": 0.9}
VENDOR_G = {"nema17": 280, "mg90s": 14, "wheel": 60, "caster": 35, "kp08": 40, "leadscrew": 130, "coupler": 15,
            "motion_board": 130, "raspberry_pi_3": 45, "battery_4s1p": 220, "estop_box": 45, "estop_button": 15,
            "buck": 25, "camera_module_3_wide": 5}
CADDY_G = 750.0
BAG = sorted((560.0, 360.0, 230.0))


def expect(name, ok, detail):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    if not ok:
        failures.append(name)


def flatten(shapes, prefix=""):
    out = []
    for s in shapes:
        label = f"{prefix}{s.label}" if s.label else prefix.rstrip("/")
        kids = list(getattr(s, "children", ()) or ())
        moved = kids and s.location is not None and (s.location.position.length > 1e-9 or
                                                     s.location.orientation.length > 1e-9)
        if moved:      # build123d: a moved compound's children are not placed; use its placed solids
            for solid in s.solids():
                out.append((label, solid, solid.bounding_box(optimal=False)))
        elif kids:
            out += flatten(kids, label + "/")
        else:
            for solid in s.solids():
                out.append((label, solid, solid.bounding_box(optimal=False)))
    return out


def bb_hit(a, b, pad=0.0):
    return not (a.max.X + pad < b.min.X or b.max.X + pad < a.min.X or a.max.Y + pad < b.min.Y
                or b.max.Y + pad < a.min.Y or a.max.Z + pad < b.min.Z or b.max.Z + pad < a.min.Z)


def clashes(group_a, group_b, limit=0.05, skip=lambda la, lb: False):
    hits = []
    for la, a, ba in group_a:
        for lb, b, bb in group_b:
            if skip(la, lb) or not bb_hit(ba, bb):
                continue
            v = overlap_volume(a, b)
            if v > limit:
                hits.append((la, lb, round(v, 1)))
    return hits


def self_clashes(group):
    hits = []
    for (la, a, ba), (lb, b, bb) in combinations(group, 2):
        if la.split("/")[0] == lb.split("/")[0] and "motion_board" in la:
            continue
        key = frozenset((la.split("/")[0], lb.split("/")[0]))
        if key in EXPECTED_CONTACT or not bb_hit(ba, bb):
            continue
        v = overlap_volume(a, b)
        if v > 0.05:
            hits.append((la, lb, round(v, 1)))
    return hits


def caddy_at(y_offset, z, label):
    c = bd.Pos(0, y_offset, z) * caddy()
    c.label = label
    return flatten([c])


# Caddy positions: seated in a bay at floor height h -> Pos(0, 0, h); on the tray (home) -> Pos(0, -175, Z [+45]).
TRAY_HOME_DY = Y_NOTCH_HOME - (-20.0 + NOTCH_FROM_FRONT)      # -175


def finger_in_notch(finger_group, caddy_group):
    """Finger clear of the caddy and its tip inside the notch void (x 47..55)."""
    f = [s for l, s, _ in finger_group]
    c = [s for l, s, _ in caddy_group]
    ov = sum(overlap_volume(a, b) for a in f for b in c)
    d = min(closest_points(a, b).distance for a in f for b in c)
    tip_x = min(s.bounding_box().min.X for s in f)
    return ov < 0.05 and d < 3.5 and tip_x < 55.0 - 0.5, f"overlap {ov:.2f} mm3, gap {d:.2f} mm, tip x {tip_x:.1f}"


# ------------------------------------------------------------------------------------------------
base = flatten(base_parts())
print(f"robot base: {len(base)} solids")

# 1. Self-interference over poses.
poses = [(z, y, f) for z in (Z_MIN, 200.0, Z_MAX) for y in (0.0, Y_MAX)
         for f in ({}, {"B": "engaged"}, {"A": "engaged"})]
bad = []
for z, y, f in poses:
    moving = flatten(lift_parts(z) + extractor_parts(z, y, f))
    hits = self_clashes(moving) + clashes(moving, base)
    if hits:
        bad.append(((z, y, tuple(f.items())), hits[:4]))
static = self_clashes(base)
expect("robot base self-interference", not static, static[:6] or "none")
expect(f"robot moving parts over {len(poses)} poses", not bad, bad[:3] or "none")

# 2. Docked at the rack: full lift sweep (extractor home), all four bays filled.
rack_bodies = flatten([rack()]) + caddy_at(0, H_BAY[2], "caddy:bay3")
sweep_hits = []
for z in [Z_MIN + 10 * i for i in range(int((Z_MAX - Z_MIN) // 10) + 1)] + [Z_MAX]:
    moving = flatten(lift_parts(z) + extractor_parts(z, 0.0, {}))
    h = clashes(moving, rack_bodies)
    if h:
        sweep_hits.append((z, h[:3]))
static_dock = clashes(base, rack_bodies)
expect("rack: robot base docked, no contact except the stop", not static_dock, static_dock[:4] or "none")
expect("rack: lift sweep Z 102-295 at Y=0", not sweep_hits, sweep_hits[:3] or "none")

# 3. Extract (slot B) and insert (slot A) at every rack bay, extractor fully out.
for n, h in enumerate(H_BAY, start=1):
    zb = h - 1.0
    moving = flatten(lift_parts(zb) + extractor_parts(zb, Y_MAX, {"B": "engaged"}))
    target = [b for b in rack_bodies if b[0].endswith(f"caddy:bay{n}")]
    others = [b for b in rack_bodies if b not in target]
    h1 = clashes(moving, others)
    fingers = [m for m in moving if m[0] == "finger:B"]
    ok, detail = finger_in_notch(fingers, target)
    expect(f"rack bay {n}: extract pose clear", not h1, h1[:3] or "no contact")
    expect(f"rack bay {n}: finger B in the notch", ok, detail)

    za = h + 1.0 - SLOT_A_DZ
    moving = flatten(lift_parts(za) + extractor_parts(za, Y_MAX, {"A": "engaged"}))
    failed = caddy_at(TRAY_HOME_DY, za, "caddy:failed_in_slotB")
    h2 = clashes(moving, others) + clashes(failed, others) + clashes(failed, moving, skip=lambda a, b: False)
    fingers = [m for m in moving if m[0] == "finger:A"]
    ok, detail = finger_in_notch(fingers, target)
    expect(f"rack bay {n}: insert pose clear (failed caddy in slot B)", not h2, h2[:3] or "no contact")
    expect(f"rack bay {n}: finger A in the notch", ok, detail)

# 4. Spare station: pick from S1 into slot A, place the failed caddy into S2 from slot B.
spare_bodies = flatten([spare_station()]) + caddy_at(0, H_SPARE[1], "caddy:s2")
for name, h, slot, z in (("S1 pick", H_SPARE[0], "A", H_SPARE[0] - 1.0 - SLOT_A_DZ),
                         ("S2 place", H_SPARE[1], "B", H_SPARE[1] + 1.0)):
    moving = flatten(lift_parts(z) + extractor_parts(z, Y_MAX, {slot: "engaged"}))
    target_label = "caddy:s1" if slot == "A" else "caddy:s2"
    target = [b for b in spare_bodies if b[0].endswith(target_label)]
    others = [b for b in spare_bodies if b not in target]
    hh = clashes(moving, others)
    expect(f"spare {name}: pose clear", not hh, hh[:3] or "no contact")
    ok, detail = finger_in_notch([m for m in moving if m[0] == f"finger:{slot}"], target)
    expect(f"spare {name}: finger {slot} in the notch", ok, detail)

# 5. Carrying two caddies (both fingers engaged, extractor home), at the top of the lift.
z = Z_MAX
moving = flatten(lift_parts(z) + extractor_parts(z, 0.0, {"A": "engaged", "B": "engaged"}))
cb = caddy_at(TRAY_HOME_DY, z, "caddy:slotB")
ca = caddy_at(TRAY_HOME_DY, z + SLOT_A_DZ, "caddy:slotA")
hh = clashes(cb + ca, moving + base)
expect("carry: two caddies on the tray, no contact", not hh, hh[:3] or "none")
for slot, cg in (("B", cb), ("A", ca)):
    ok, detail = finger_in_notch([m for m in moving if m[0] == f"finger:{slot}"], cg)
    expect(f"carry: finger {slot} holds its caddy", ok, detail)

# 6. Camera sight lines (Camera Module 3 Wide ~102 x 67 deg; keep 3 deg margin).
H_FOV, V_FOV = 102.0 / 2 - 3.0, 67.0 / 2 - 3.0


def sight(lens, target, bodies, ignore=()):
    dx, dy, dz = (target[i] - lens[i] for i in range(3))
    hang = math.degrees(math.atan2(dx, dy))
    vang = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
    steps = int(math.dist(lens, target) // 2)
    blocked = None
    for i in range(2, steps - 1):
        p = bd.Vector(*(lens[k] + (target[k] - lens[k]) * i / steps for k in range(3)))
        for label, s, bb in bodies:
            if any(t in label for t in ignore):
                continue
            if bb.min.X <= p.X <= bb.max.X and bb.min.Y <= p.Y <= bb.max.Y and bb.min.Z <= p.Z <= bb.max.Z \
                    and s.is_inside(p):
                blocked = label
                break
        if blocked:
            break
    return hang, vang, blocked


lx, ly = CAM_LENS
for n, h in ((1, H_BAY[0]), (4, H_BAY[3])):
    z = h - 1.0
    scene = flatten(lift_parts(z) + extractor_parts(z, 0.0, {})) + base + rack_bodies
    lens = (lx, ly + 0.5, z + CAM_DZ)
    for what, tgt, ign in (("bay tag", (-80.0, TAG_FACE_Y - 0.2, h + 15.0), ("tag_strip", "camera")),
                           ("caddy tag", (-55.0 + 5 + 12.0, -20.2, h + 15.0), (f"caddy:bay{n}", "camera"))):
        ha, va, blk = sight(lens, tgt, scene, ign)
        ok = blk is None and abs(ha) <= H_FOV and abs(va) <= V_FOV
        expect(f"camera -> bay {n} {what}", ok, f"h {ha:.1f} deg, v {va:.1f} deg, blocked by {blk}")
z_app = TAG_APPROACH_Z - CAM_DZ
for d in (250.0, 450.0, 700.0):
    lens = (lx, ly - d, z_app + CAM_DZ)
    ha, va, _ = sight(lens, (125.0, TAG_FACE_Y, TAG_APPROACH_Z), [], ())
    expect(f"camera -> approach tag at {d:.0f} mm back-off", abs(ha) <= H_FOV and abs(va) <= V_FOV,
           f"h {ha:.1f} deg, v {va:.1f} deg (Z approach = {z_app:.0f})")

# 7. Mass, CG and tip-over (worst case: two caddies at the top of the lift).
def mass_of(label, solid):
    key = label.split("/")[0].split(":")[0]
    if key in ("rail_2020", "cross_2020", "y_rail_2020", "mast_2040"):
        return None
    for k, g in VENDOR_G.items():
        if key.startswith(k):
            return ("vendor", g)
    return ("printed", solid.volume * PRINTED_DENSITY)


def mass_props(group):
    total, mx, my, mz, printed, per_label = 0.0, 0.0, 0.0, 0.0, 0.0, {}
    seen_vendor = set()
    for label, s, bb in group:
        r = mass_of(label, s)
        if r is None:
            continue
        kind, g = r
        top = label.split("/")[0]
        if kind == "vendor":
            if top in seen_vendor:
                continue
            seen_vendor.add(top)
            c = bb.center()
        else:
            c = s.center(bd.CenterOf.MASS)
            printed += g
        total += g
        mx, my, mz = mx + g * c.X, my + g * c.Y, mz + g * c.Z
        per_label[top] = per_label.get(top, 0.0) + g
    return total, (mx, my, mz), printed


z = Z_MAX
robot = base + flatten(lift_parts(z) + extractor_parts(z, 0.0, {}))
g_parts, mom, g_printed = mass_props(robot)
g_ext = sum(L * EXTRUSION_G_PER_MM[k] for k, Ls in EXTRUSIONS.items() for L in Ls) + 330.0 * EXTRUSION_G_PER_MM["2020"] + 450.0
# (+ 3 x 110 mm cross members already in EXTRUSIONS; +450 g fasteners, wiring, belts, V-wheels)
ext_cg = (0.0, -240.0, 120.0)
g_robot = g_parts + g_ext
cg = [(mom[i] + g_ext * ext_cg[i]) / g_robot for i in range(3)]
expect("robot mass <= 4.7 kg (spec target)", g_robot <= 4700, f"{g_robot / 1000:.2f} kg "
       f"(printed {g_printed / 1000:.2f} kg, purchased {(g_parts - g_printed) / 1000:.2f} kg, "
       f"extrusions+hardware {g_ext / 1000:.2f} kg)")
loads = [(CADDY_G, (0.0, TRAY_HOME_DY + 65.0, z + 15.0)), (CADDY_G, (0.0, TRAY_HOME_DY + 65.0, z + SLOT_A_DZ + 15.0))]
g_tot = g_robot + sum(m for m, _ in loads)
cg_l = [(cg[i] * g_robot + sum(m * p[i] for m, p in loads)) / g_tot for i in range(3)]
print(f"       CG empty (x, y, z) = ({cg[0]:.0f}, {cg[1]:.0f}, {cg[2]:.0f}) mm; "
      f"with 2 caddies at Z max = ({cg_l[0]:.0f}, {cg_l[1]:.0f}, {cg_l[2]:.0f}) mm")
decel = 0.3 / 9.81
for name, c in (("empty", cg), ("2 caddies, Z max", cg_l)):
    fwd = AXLE_Y - c[1]                              # CG must stay behind the wheel axle line
    rear = c[1] - CASTER_REAR[0][1]
    need = c[2] * decel
    expect(f"tip-over margin forward ({name})", fwd > need,
           f"{fwd:.0f} mm behind the axle; needs > {need:.0f} mm for 0.3 m/s^2 braking")
    expect(f"tip-over margin rearward ({name})", rear > need, f"{rear:.0f} mm ahead of the rear casters")
    side = min(WHEEL_X[0] + 12, abs(CASTER_REAR[0][0])) - abs(c[0])
    expect(f"tip-over margin sideways ({name})", side > need, f"{side:.0f} mm")

# 8. Packing (carry-on 56 x 36 x 23 cm): base unit vs removable mast unit (mast, carriage, tray, Y axis).
mast_keys = ("mast_2040", "mast_top_plate", "leadscrew", "kp08", "z_carriage", "tray_stack", "rail_bracket",
             "y_rail", "nema17:y", "camera", "y_carriage", "mg90s", "finger", "estop")
z = Z_MIN
everything = base + flatten(lift_parts(z) + extractor_parts(z, 0.0, {}))
for unit, members in (("base unit", [b for b in everything if not b[0].startswith(mast_keys)]),
                      ("mast unit", [b for b in everything if b[0].startswith(mast_keys)])):
    bb = members[0][2]
    for _, _, b in members[1:]:
        bb = bb.add(b)
    dims = sorted((bb.size.X, bb.size.Y, bb.size.Z))
    expect(f"packing: {unit} fits a 56 x 36 x 23 cm bag", all(d <= b for d, b in zip(dims, BAG)),
           f"{dims[2]:.0f} x {dims[1]:.0f} x {dims[0]:.0f} mm")

# 9. Print bed 400 x 400 (x 400 high) for every printed part.
printed_parts = {l.split("/")[0]: s for l, s, _ in base + flatten(lift_parts(Z_MIN) + extractor_parts(Z_MIN, 0, {}))
                 if mass_of(l, s) and mass_of(l, s)[0] == "printed"}
too_big = []
for label, s in printed_parts.items():
    d = sorted(s.bounding_box().size.to_tuple())
    if d[2] > 400 or d[1] > 400:
        too_big.append((label, [round(v) for v in d]))
expect(f"print bed: {len(printed_parts)} printed parts fit 400 x 400", not too_big, too_big or "all fit")

if failures:
    raise SystemExit(f"\n{len(failures)} check(s) failed: {failures}")
print("\nAll robot checks passed.")
