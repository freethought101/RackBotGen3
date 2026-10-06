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
from lib.robot_dims import (AXLE_Y, CAM_DZ, CAM_LENS, CASTER_REAR, FINGER_DZ, FINGER_LEN, FINGER_T, FINGER_X,
                            SLOT_A_DZ, TRAY_FRONT_Y, WHEEL_X, Y_HARD, Y_MAX, Y_NOTCH_HOME, Y_PULL, Y_PUSH, Y_SEAT,
                            Z_MAX, Z_MIN)
from rack import rack
from spare_station import spare_station

failures = []
# Designed contacts (label prefixes): shafts in hubs, V-wheel rims in their grooves, the belt in its clamp.
EXPECTED = [("kfl08", "leadscrew_tr8x2"), ("nema17:z", "coupler"), ("nema17:y", "gt2_pulley_20t"),
            ("vwheel:z", "mast_2040"), ("vwheel:y", "y_rail_2020"), ("y_carriage", "gt2_belt:inner"),
            ("leadscrew_tr8x2", "mast_top_plate"), ("coupler", "leadscrew_tr8x2")]
PRINTED_DENSITY = 1.27e-3 * 0.5          # PETG, ~50 % effective fill
EXTRUSION_G_PER_MM = {"2020": 0.5, "2040": 0.9}
VENDOR_G = {"nema17": 280, "mg90s": 14, "wheel": 60, "caster": 35, "kfl08": 45, "vwheel": 12, "leadscrew": 130,
            "coupler": 15, "motion_board": 130, "raspberry_pi_3": 45, "battery_4s1p": 220, "estop_box": 45,
            "estop_button": 15, "buck": 25, "camera_module_3_wide": 5, "gt2_pulley": 10, "gt2_idler": 8, "gt2_belt": 5}
CADDY_G = 750.0
BAG = sorted((560.0, 360.0, 230.0))
GAP = 1.0                                # minimum running clearance between parts that move relative to each other


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


def expected(la, lb):
    return any((la.startswith(a) and lb.startswith(b)) or (la.startswith(b) and lb.startswith(a)) for a, b in EXPECTED)


def clashes(group_a, group_b, limit=0.05, skip=lambda la, lb: False):
    hits = []
    for la, a, ba in group_a:
        for lb, b, bb in group_b:
            if skip(la, lb) or expected(la, lb) or not bb_hit(ba, bb):
                continue
            v = overlap_volume(a, b)
            if v > limit:
                hits.append((la, lb, round(v, 1)))
    return hits


def tight(group_a, group_b, need=GAP, skip=lambda la, lb: False):
    """Pairs closer than `need` (mm) that are not designed contacts: the running-clearance test."""
    hits = []
    for la, a, ba in group_a:
        for lb, b, bb in group_b:
            if skip(la, lb) or expected(la, lb) or not bb_hit(ba, bb, need):
                continue
            d = closest_points(a, b).distance
            if d < need - 1e-6:
                hits.append((la, lb, round(d, 2)))
    return hits


def self_clashes(group):
    hits = []
    for (la, a, ba), (lb, b, bb) in combinations(group, 2):
        if la.split("/")[0] == lb.split("/")[0]:
            continue
        if expected(la, lb) or not bb_hit(ba, bb):
            continue
        v = overlap_volume(a, b)
        if v > 0.05:
            hits.append((la, lb, round(v, 1)))
    return hits


def caddy_at(y_offset, z, label):
    c = bd.Pos(0, y_offset, z) * caddy()
    c.label = label
    return flatten([c])


# Caddy y offsets (Pos(0, dy, h)): seated in a bay -> 0 (notch centre at y = -10). With the finger in the
# notch, the notch centre sits +PLAY ahead of the pivot when pulling and -PLAY behind it when pushing.
PLAY = (NOTCH_L - FINGER_T) / 2
SEATED_NOTCH_Y = -20.0 + NOTCH_FROM_FRONT


def pulled_dy(Y):
    return min(0.0, Y_NOTCH_HOME + Y + PLAY - SEATED_NOTCH_Y)


def pushed_dy(Y):
    return max(pulled_dy(0.0), Y_NOTCH_HOME + Y - PLAY - SEATED_NOTCH_Y)


TRAY_DY = pulled_dy(0.0)                 # a caddy resting on the tray after a pull


def finger_in_notch(finger_group, caddy_group):
    """Finger clear of the caddy and its tip inside the notch void (x 47..55)."""
    f = [s for l, s, _ in finger_group]
    c = [s for l, s, _ in caddy_group]
    ov = sum(overlap_volume(a, b) for a in f for b in c)
    d = min(closest_points(a, b).distance for a in f for b in c)
    tip_x = min(s.bounding_box().min.X for s in f)
    return ov < 0.05 and d < 3.5 and tip_x < 55.0 - 0.5, f"overlap {ov:.2f} mm3, gap {d:.2f} mm, tip x {tip_x:.1f}"


def robot_at(z, y, fingers):
    lift = flatten(lift_parts(z))
    ext = flatten(extractor_parts(z, y, fingers))
    return lift, ext


# ------------------------------------------------------------------------------------------------
base = flatten(base_parts())
print(f"robot base: {len(base)} solids")
print(f"geometry: Y pull {Y_PULL}, seat {Y_SEAT}, push {Y_PUSH}, soft max {Y_MAX}, hard {Y_HARD}; "
      f"finger play +/-{PLAY} mm; caddy on the tray at dy {TRAY_DY:.0f} (rear at y {TRAY_DY + 150:.0f}, "
      f"tray front {TRAY_FRONT_Y:.0f})")

# 1. Self-interference and running clearance over poses (lift vs base, extractor vs lift and base).
ys = [0.0, 30.0, 60.0, 90.0, 120.0, 150.0, Y_PULL, Y_PUSH, Y_MAX, Y_HARD - 1.5]
poses = [(z, y, {}) for z in (Z_MIN, 200.0, Z_MAX) for y in ys]
poses += [(z, y, f) for z in (Z_MIN, Z_MAX) for y in (0.0, Y_PULL)
          for f in ({"B": "engaged"}, {"A": "engaged"}, {"A": "engaged", "B": "engaged"})]
bad, near = [], []
for z, y, f in poses:
    lift, ext = robot_at(z, y, f)
    hits = self_clashes(lift + ext) + clashes(lift + ext, base)
    if hits:
        bad.append(((z, y, tuple(f.items())), hits[:4]))
    t = tight(lift, base) + tight(ext, base) + tight(ext, lift)
    if t:
        near.append(((z, y, tuple(f.items())), t[:4]))
static = self_clashes(base)
expect("robot base self-interference", not static, static[:6] or "none")
expect(f"robot moving parts, no overlap over {len(poses)} poses", not bad, bad[:3] or "none")
expect(f"robot moving parts, >= {GAP} mm running clearance over {len(poses)} poses", not near, near[:3] or "none")
lift, ext = robot_at(Z_MIN, Y_HARD + 0.5, {})
stop = clashes(ext, lift)
expect(f"Y hard stop: the carriage meets the idler bracket at Y = {Y_HARD}",
       any("y_idler_bracket" in a + b for a, b, _ in stop), stop[:2] or "no contact at Y_HARD + 0.5")

# 2. Docked at the rack: full lift sweep (extractor home), bay 3 filled; once empty, once carrying
#    two caddies at their real on-tray position (rear 1 mm inside the tray front).
rack_bodies = flatten([rack()]) + caddy_at(0, H_BAY[2], "caddy:bay3")
rack_frame = [b for b in rack_bodies if not b[0].startswith("caddy")]
sweep_hits, sweep_near, carry_near = [], [], []
for z in [Z_MIN + 10 * i for i in range(int((Z_MAX - Z_MIN) // 10) + 1)] + [Z_MAX]:
    lift, ext = robot_at(z, 0.0, {"A": "engaged", "B": "engaged"})
    carried = caddy_at(TRAY_DY, z, "caddy:slotB") + caddy_at(TRAY_DY, z + SLOT_A_DZ, "caddy:slotA")
    h = clashes(lift + ext + carried, rack_bodies)
    if h:
        sweep_hits.append((z, h[:3]))
    t = tight(lift + ext, rack_bodies)
    if t:
        sweep_near.append((z, t[:3]))
    t = tight(carried, rack_bodies)
    if t:
        carry_near.append((z, t[:3]))
static_dock = clashes(base, rack_bodies)
expect("rack: robot base docked, no contact except the stop", not static_dock, static_dock[:4] or "none")
expect("rack: lift sweep Z 102-295 carrying two caddies, no contact", not sweep_hits, sweep_hits[:3] or "none")
expect(f"rack: lift sweep, robot >= {GAP} mm from the rack", not sweep_near, sweep_near[:3] or "none")
expect(f"rack: lift sweep, carried caddies >= {GAP} mm from the rack and its caddies", not carry_near,
       carry_near[:3] or "none")


def moved(group, dy, dz, tag):
    out = []
    for label, sol, _ in group:
        m = sol.moved(bd.Location((0.0, dy, dz)))
        out.append((f"{tag}/{label}", m, m.bounding_box(optimal=False)))
    return out


def stroke(z, bodies, item, slot, mode, other_caddy):
    """One Y stroke at a shelf (rack bay or spare slot). `item` = the caddy (+ dummy drive) seated on that
    shelf. mode 'pull': extend parked, engage at Y_PULL, retract with the caddy (it stays at shelf height until
    its rear leaves the shelf, then drops 1 mm onto the tray). mode 'push': the shelf is empty; the caddy starts
    on the tray (1 mm above the shelf), is pushed until seated at Y_SEAT, then the finger parks and retracts.
    The other finger stays parked; `other_caddy` (label or None) rests on the tray in the other slot."""
    other = "A" if slot == "B" else "B"
    rest = [b for b in bodies if b not in item]
    rest_caddies = [b for b in rest if b[0].split("/")[-1].startswith(("caddy", "dummy"))]
    problems = []
    if mode == "pull":
        seq = [(y, {}, None) for y in (0.0, 60.0, 120.0, Y_PULL)]
        seq += [(y, {slot: "engaged"}, pulled_dy(y)) for y in (Y_PULL, 150.0, 100.0, 50.0, 0.0)]
        dz_of = lambda dy: 0.0 if dy > -150.0 else -1.0
    else:
        seq = [(y, {slot: "engaged"}, pushed_dy(y)) for y in (0.0, 50.0, 100.0, 150.0, Y_SEAT)]
        seq += [(y, {}, None) for y in (Y_SEAT, 120.0, 0.0)]
        dz_of = lambda dy: 1.0 if dy < -5.0 else 0.0
    for y, f, dy in seq:
        lift, ext = robot_at(z, y, f)
        robot = lift + ext
        if dy is None:      # finger parked: the caddy is seated on the shelf (before a pull / after a push)
            cad = item
        else:
            cad = moved(item, dy, dz_of(dy), "moving")
        resting = []
        if other_caddy:
            zo = z + (SLOT_A_DZ if other == "A" else 0.0)
            resting = caddy_at(TRAY_DY, zo, other_caddy)
        h = clashes(robot + resting, rest) + clashes(cad, rest + resting)
        h += clashes(cad, robot, skip=lambda a, b: b.startswith(("tray_stack", "finger")))
        h += clashes(resting, robot, skip=lambda a, b: b.startswith("tray_stack"))
        h += clashes(robot, cad, skip=lambda a, b: a.startswith(("tray_stack", "finger")))
        t = tight(robot, rest) + tight(resting, rest + cad) + tight(ext, resting) + tight(cad, rest_caddies)
        t += tight(ext, cad, skip=lambda a, b: a.startswith(f"finger:{slot}"))
        if h or t:
            problems.append((y, tuple(f.items()), (h + t)[:3]))
        if y in (Y_PULL, Y_SEAT) and f:
            ok, detail = finger_in_notch([m for m in ext if m[0] == f"finger:{slot}"],
                                         [c for c in cad if c[0].endswith(tuple(f"caddy:{k}" for k in ("bay1", "bay2", "bay3", "bay4", "s1", "s2")))])
            if not ok:
                problems.append((y, "finger", detail))
    return problems


def shelf_item(bodies, key):
    return [b for b in bodies if b[0].split("/")[-1] in (f"caddy:{key}", f"dummy_drive:{key}", f"dummy_lid:{key}")]


# 3. Extract (pull into slot B, spare waiting in A) and insert (push from slot A, failed caddy in B) at every
#    rack bay, through the intermediate stroke positions. Bay 3 is empty in the rack model: a bare caddy is used.
for n, h in enumerate(H_BAY, start=1):
    bodies = flatten([rack()]) + (caddy_at(0, h, f"caddy:bay{n}") if n == 3 else [])
    item = shelf_item(bodies, f"bay{n}")
    p = stroke(h - 1.0, bodies, item, "B", "pull", "caddy:spare_in_A")
    expect(f"rack bay {n}: extract into slot B (spare waiting in A)", not p, p[:3] or "clear, finger in the notch")
    p = stroke(h + 1.0 - SLOT_A_DZ, bodies, item, "A", "push", "caddy:failed_in_B")
    expect(f"rack bay {n}: insert from slot A (failed caddy in B)", not p, p[:3] or "clear, finger in the notch")

# The push seats the caddy: at Y_SEAT the pushed caddy is at dy 0 (rear on the bay back stop), and at
# Y_PULL the finger is centred in a seated caddy's notch.
expect("push seats the caddy at Y_SEAT", abs(pushed_dy(Y_SEAT)) < 1e-6, f"caddy dy {pushed_dy(Y_SEAT):.2f} mm")
expect("pull starts centred in the notch", abs(Y_NOTCH_HOME + Y_PULL - SEATED_NOTCH_Y) < 1e-6,
       f"pivot y {Y_NOTCH_HOME + Y_PULL:.1f} vs notch {SEATED_NOTCH_Y:.1f}")
expect("caddy on the tray stays inside the tray front", TRAY_DY + 150.0 <= TRAY_FRONT_Y - 0.5,
       f"rear at y {TRAY_DY + 150.0:.1f}, tray front {TRAY_FRONT_Y:.1f}")

# 4. Spare station: pick from S1 into slot A, place the failed caddy into S2 from slot B.
for name, h, slot, z, mode, key in (("S1 pick", H_SPARE[0], "A", H_SPARE[0] - 1.0 - SLOT_A_DZ, "pull", "s1"),
                                    ("S2 place", H_SPARE[1], "B", H_SPARE[1] + 1.0, "push", "s2")):
    bodies = flatten([spare_station()]) + (caddy_at(0, h, "caddy:s2") if key == "s2" else [])
    p = stroke(z, bodies, shelf_item(bodies, key), slot, mode, None)
    expect(f"spare {name}: stroke clear, finger {slot} in the notch", not p, p[:3] or "clear")

# 5. Carrying two caddies (both fingers engaged, extractor home), at the top of the lift.
z = Z_MAX
lift, ext = robot_at(z, 0.0, {"A": "engaged", "B": "engaged"})
moving = lift + ext
cb = caddy_at(TRAY_DY, z, "caddy:slotB")
ca = caddy_at(TRAY_DY, z + SLOT_A_DZ, "caddy:slotA")
hh = clashes(cb + ca, moving + base, skip=lambda a, b: b.startswith("tray_stack"))
hh += clashes(cb + ca, [m for m in moving if not m[0].startswith(("tray_stack", "finger"))])
expect("carry: two caddies on the tray, no contact", not hh, hh[:3] or "none")
for slot, cg in (("B", cb), ("A", ca)):
    ok, detail = finger_in_notch([m for m in ext if m[0] == f"finger:{slot}"], cg)
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
g_ext = sum(L * EXTRUSION_G_PER_MM[k] for k, Ls in EXTRUSIONS.items() for L in Ls) + 360.0
# (+360 g fasteners, wiring, belts; V-wheels and bearings are modeled)
ext_cg = (0.0, -240.0, 120.0)
g_robot = g_parts + g_ext
cg = [(mom[i] + g_ext * ext_cg[i]) / g_robot for i in range(3)]
expect("robot mass <= 4.7 kg (spec target)", g_robot <= 4700, f"{g_robot / 1000:.2f} kg "
       f"(printed {g_printed / 1000:.2f} kg, purchased {(g_parts - g_printed) / 1000:.2f} kg, "
       f"extrusions+hardware {g_ext / 1000:.2f} kg)")
loads = [(CADDY_G, (0.0, TRAY_DY + 65.0, z + 15.0)), (CADDY_G, (0.0, TRAY_DY + 65.0, z + SLOT_A_DZ + 15.0))]
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
mast_keys = ("mast_2040", "mast_top_plate", "leadscrew", "kfl08", "vwheel", "z_carriage", "tray_stack", "rail_bracket",
             "y_rail", "nema17:y", "camera", "y_carriage", "mg90s", "finger", "estop", "gt2", "y_idler")
z = Z_MIN
everything = [b for b in base + flatten(lift_parts(z) + extractor_parts(z, 0.0, {}))
              if not b[0].startswith("nema17:y")]      # the Y motor (4 x M3) is packed separately
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
