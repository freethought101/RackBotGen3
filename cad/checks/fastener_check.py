"""Fastener checks: every screw, nut, T-nut and insert of the robot (lib/robot_fasteners.py) against the parts.

- holes: a fastener that overlaps a part it does not thread into (or pass through as a bought part modeled without
  holes) is a clash, so a missing, misplaced or blocked hole shows up here;
- seating: the head touches what it clamps, a nut touches the part it bears on;
- thread: engagement in the nut / T-nut / insert / pilot / tapped hole, and no bottoming out;
- motion: fasteners on the lift, extractor and fingers keep >= 1 mm from parts that move relative to them.

Run from cad/:  PYTHONPATH=src python checks/fastener_check.py
"""

from collections import Counter

from cadgen.geometry import closest_points, overlap_volume

from lib.robot_build import base_parts, extractor_parts, lift_parts
from lib.robot_dims import Y_MAX, Y_PULL, Z_MAX, Z_MIN
from lib.robot_fasteners import all_joints, engagement, fastener_parts

GAP = 1.0
failures = []


def expect(name, ok, detail):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    if not ok:
        failures.append(name)


def flat(shapes, group):
    out = []
    for s in shapes:
        for solid in s.solids():
            out.append((s.label, group, solid, solid.bounding_box(optimal=False)))
    return out


def bb_hit(a, b, pad=0.0):
    return not (a.max.X + pad < b.min.X or b.max.X + pad < a.min.X or a.max.Y + pad < b.min.Y
                or b.max.Y + pad < a.min.Y or a.max.Z + pad < b.min.Z or b.max.Z + pad < a.min.Z)


def robot(Z, Y, fingers):
    parts = flat(base_parts(), "base") + flat(lift_parts(Z), "lift")
    ext = flat(extractor_parts(Z, Y, fingers), "ext")
    for label, g, s, b in ext:          # fingers move relative to the carriage
        parts.append((label, f"finger:{label.split(':')[1]}" if label.startswith("finger:") else g, s, b))
    fx = []
    for j, kind, shape in fastener_parts(Z, Y, fingers, JOINTS):
        for solid in shape.solids():
            fx.append((j, kind, solid, solid.bounding_box(optimal=False)))
    return parts, fx


def allowed(j, kind, label):
    if j.target and label.startswith(j.target):
        return True                     # threads into it, insert seated in it, T-nut in its slot
    return any(label.startswith(t) for t in j.through)


JOINTS = all_joints()


# ---- 1. Reference pose: holes, seating, engagement ------------------------------------------------------------------
Z0, Y0 = 210.0, 0.0
parts, fx = robot(Z0, Y0, {})
joints = JOINTS
print(f"{len(joints)} joints, {len(fx)} fastener solids, {len(parts)} part solids")

clash = []
for j, kind, s, b in fx:
    for label, g, p, pb in parts:
        if not bb_hit(b, pb) or allowed(j, kind, label):
            continue
        v = overlap_volume(s, p)
        if v > 0.05:
            clash.append((j.name, kind, label, round(v, 1)))
for (j1, k1, s1, b1), (j2, k2, s2, b2) in ((a, c) for i, a in enumerate(fx) for c in fx[i + 1:]):
    if j1.name == j2.name or not bb_hit(b1, b2):
        continue
    v = overlap_volume(s1, s2)
    if v > 0.05:
        clash.append((j1.name, k1, f"fx:{j2.name}/{k2}", round(v, 1)))
expect("holes: no fastener hits a part it does not thread into", not clash, f"{len(clash)} clashes")
for c in clash:
    print("       ", c)

loose = []
for j in joints:
    if not j.seat:
        continue
    screw = [s for jj, k, s, _ in fx if jj is j and k == "screw"]
    seat = [p for label, g, p, _ in parts if label.startswith(j.seat)]
    if not seat:
        loose.append((j.name, f"seat {j.seat!r} not in the model"))
        continue
    d = min(closest_points(a, b).distance for a in screw for b in seat)
    if d > 0.3:
        loose.append((j.name, f"head {d:.1f} mm off {j.seat}"))
    nut = [s for jj, k, s, _ in fx if jj is j and k == "nut"]
    if nut and j.end in ("nut", "nylock"):
        others = [p for label, g, p, pb in parts if bb_hit(nut[0].bounding_box(), pb, 0.5)]
        dn = min((closest_points(nut[0], p).distance for p in others), default=99.0)
        if dn > 0.3:
            loose.append((j.name, f"nut {dn:.1f} mm from any part"))
expect("seating: heads and nuts sit on their parts", not loose, f"{len(loose)} loose")
for c in loose:
    print("       ", c)

bad_thread = []
for j in joints:
    ok, txt = engagement(j)
    if not ok:
        bad_thread.append((j.name, j.spec, txt))
expect("thread: engagement and no bottoming out", not bad_thread, f"{len(bad_thread)} joints")
for c in bad_thread:
    print("       ", c)

# ---- 2. Motion: moving fasteners vs parts that move relative to them ------------------------------------------------
poses = [(z, y, {}) for z in (Z_MIN, 200.0, Z_MAX) for y in (0.0, 60.0, 120.0, Y_PULL, Y_MAX)]
poses += [(z, y, {"A": "engaged", "B": "engaged"}) for z in (Z_MIN, Z_MAX) for y in (0.0, Y_PULL)]
near = []
for z, y, f in poses:
    parts, fx = robot(z, y, f)
    for j, kind, s, b in fx:
        for label, g, p, pb in parts:
            if g == j.group or not bb_hit(b, pb, GAP) or allowed(j, kind, label):
                continue
            dist = closest_points(s, p).distance
            if dist < GAP - 1e-6:
                near.append(((z, y, tuple(f.items())), j.name, kind, label, round(dist, 2)))
expect(f"motion: moving fasteners >= {GAP} mm from other moving groups over {len(poses)} poses", not near,
       f"{len(near)} cases")
seen = set()
for c in near:
    if (c[1], c[3]) not in seen:
        seen.add((c[1], c[3]))
        print("       ", c)

# ---- 3. Bill of fasteners ------------------------------------------------------------------------------------------
count = Counter(j.spec for j in joints)
nuts = Counter((j.end, j.d) for j in joints if j.end in ("nut", "nylock", "tnut", "insert"))
print("\nFasteners modeled:")
for k, n in sorted(count.items()):
    print(f"  {n:3d} x {k}")
for (e, d), n in sorted(nuts.items()):
    print(f"  {n:3d} x M{d:g} {dict(nut='hex nut', nylock='nylon lock nut', tnut='T-nut (slot 6)', insert='heat-set insert')[e]}")

if failures:
    raise SystemExit(f"\n{len(failures)} check(s) failed: {failures}")
print("\nAll fastener checks passed.")
