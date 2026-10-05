"""Rack / spare station checks: interference, docking envelope, tray and caddy sweep clearances.

Run from cad/:  PYTHONPATH=src python checks/station_check.py
Probe boxes stand in for the robot (not modeled yet); dimensions from docs/spec/01-mechanical.md.
"""

from itertools import combinations

from cadgen import read_scene
from cadgen.geometry import closest_points, overlap_volume

from lib.dims import (BAY_PITCH, CADDY_H, DOCK_STOP_Y, H_BAY, H_SPARE, NOSE_W, TRAY_FRONT_DOCKED_Y)
from lib.prims import box

failures = []


def expect(name, ok, detail):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    if not ok:
        failures.append(name)


def bodies_of(path):
    """(label, solid) for every leaf occurrence."""
    return [(leaf.label or leaf.ref, s) for leaf in read_scene(path).leaves() for s in leaf.shape().solids()]


def overlaps_with(probe, bodies, limit=0.01):
    probe = probe.solids()[0]
    hits = []
    for ref, s in bodies:
        bb_p, bb_s = probe.bounding_box(), s.bounding_box()
        if (bb_p.max.X < bb_s.min.X or bb_s.max.X < bb_p.min.X or bb_p.max.Y < bb_s.min.Y
                or bb_s.max.Y < bb_p.min.Y or bb_p.max.Z < bb_s.min.Z or bb_s.max.Z < bb_p.min.Z):
            continue
        v = overlap_volume(probe, s)
        if v > limit:
            hits.append((ref, round(v, 1)))
    return hits


# Robot probes (robot frame placed docked against the stop).
TRAY_HALF_W = 65.0
TRAY_DEPTH = 180.0
TRAY_BELOW = 4.0          # tray floor thickness below slot B floor (Z)
TRAY_ABOVE = BAY_PITCH + CADDY_H + 5.0   # top of slot A walls above Z
NOSE_L, NOSE_Z = 60.0, (30.0, 100.0)
BASE_HALF_W, BASE_L, BASE_Z = 150.0, 300.0, (10.0, 100.0)

for path, root, heights in (("STEP/rack.step", "rack", H_BAY), ("STEP/spare_station.step", "spare_station", H_SPARE)):
    print(f"\n== {root}")
    bodies = bodies_of(path)
    bad = []
    for (ra, a), (rb, b) in combinations(bodies, 2):
        if overlaps_with(a, [(rb, b)]):
            bad.append((ra, rb))
    expect(f"{root}: no interference between {len(bodies)} bodies", not bad, bad or "0 pairs")

    nose = box(-NOSE_W / 2, NOSE_W / 2, DOCK_STOP_Y - NOSE_L, DOCK_STOP_Y, *NOSE_Z)
    expect(f"{root}: docked nose clear of station", not overlaps_with(nose, bodies), "nose box 200 W, z 30-100")
    d = min(closest_points(nose.solids()[0], s).distance for _, s in bodies)
    expect(f"{root}: nose touches the dock stop", d < 0.01, f"min distance {d:.3f} mm")
    shifted = box(-NOSE_W / 2 + 1.5, NOSE_W / 2 + 1.5, DOCK_STOP_Y - NOSE_L, DOCK_STOP_Y - 1, *NOSE_Z)
    expect(f"{root}: funnel throat constrains nose to <= 1.5 mm", bool(overlaps_with(shifted, bodies)),
           "nose shifted 1.5 mm in x collides with the funnel")

    base = box(-BASE_HALF_W, BASE_HALF_W, DOCK_STOP_Y - NOSE_L - BASE_L, DOCK_STOP_Y - NOSE_L, *BASE_Z)
    expect(f"{root}: robot base body clear of funnel", not overlaps_with(base, bodies), "base 300 x 300 behind the nose")

    # Tray stack sweep over the full lift range while docked.
    tray_hits = []
    for z in range(100, 301, 5):
        tray = box(-TRAY_HALF_W, TRAY_HALF_W, TRAY_FRONT_DOCKED_Y - TRAY_DEPTH, TRAY_FRONT_DOCKED_Y,
                   z - TRAY_BELOW, z + TRAY_ABOVE)
        if overlaps_with(tray, bodies):
            tray_hits.append(z)
    expect(f"{root}: tray stack clear over Z 100-300 mm", not tray_hits, tray_hits or "no collisions")

    # Caddy extraction sweep: from seated to fully on the tray, per shelf.
    sweep_hits = []
    for h in heights:
        sweep = box(-57.0, 57.0, TRAY_FRONT_DOCKED_Y - TRAY_DEPTH, 149.0, h + 0.2, h + CADDY_H)
        hits = [r for r, _ in overlaps_with(sweep, [(r, s) for r, s in bodies if "caddy" not in r
                                                    and "dummy" not in r])]
        if hits:
            sweep_hits.append((h, hits))
    expect(f"{root}: caddy extraction path clear", not sweep_hits, sweep_hits or "all shelves")

if failures:
    raise SystemExit(f"\n{len(failures)} check(s) failed: {failures}")
print("\nAll station checks passed.")
