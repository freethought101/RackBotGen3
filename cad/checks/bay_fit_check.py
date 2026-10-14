"""Checks for the caddy / dummy drive / bay shelf set against docs/spec/01-mechanical.md §1.

Run from cad/:  PYTHONPATH=src python checks/bay_fit_check.py
"""

from itertools import combinations

from cadgen import build123d as bd
from cadgen import read_scene, read_step
from cadgen.geometry import closest_points, overlap_volume

PETG = 1.27e-3   # g/mm^3
PLA = 1.24e-3
INFILL_FACTOR = 0.55  # rough solid-fraction for 4 walls + 30-40 % infill

failures = []


def expect(name, ok, detail):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    if not ok:
        failures.append(name)


def size(shape):
    bb = shape.bounding_box()
    return tuple(round(v, 2) for v in (bb.size.X, bb.size.Y, bb.size.Z)), bb


# --- Individual parts -------------------------------------------------------
parts = {}
for name, density in (("caddy", PETG), ("dummy_drive_shell", PLA), ("dummy_drive_lid", PLA), ("bay_shelf", PETG)):
    shape = read_step(f"STEP/{name}.step")
    solids = shape.solids()
    parts[name] = shape
    dims, _ = size(shape)
    vol = sum(s.volume for s in solids)
    expect(f"{name} single valid solid", len(solids) == 1 and shape.is_valid and vol > 0,
           f"{len(solids)} solid(s), valid={shape.is_valid}, volume={vol / 1000:.1f} cm3")
    print(f"       envelope {dims} mm, est. print mass {vol * density * INFILL_FACTOR:.0f} g "
          f"(solid {vol * density:.0f} g)")

expect("caddy envelope 114 x 170 x 30", size(parts["caddy"])[0] == (114.0, 170.0, 30.0), size(parts["caddy"])[0])
expect("dummy shell envelope 101.6 x 147 x 26.1", size(parts["dummy_drive_shell"])[0] == (101.6, 147.0, 26.1),
       size(parts["dummy_drive_shell"])[0])

# Ballast space and achievable mass
shell_lid_g = sum(s.volume for p in ("dummy_drive_shell", "dummy_drive_lid") for s in parts[p].solids()) * PLA * INFILL_FACTOR
ballast_target = 600 - shell_lid_g
cavity_mm3 = 139.0 * 93.6 * 22.1  # inner pocket (gross, ignoring bosses)
steel_mm3 = ballast_target / 7.85e-3
expect("ballast fits (steel, <= 60 % of cavity incl. epoxy/packing)", steel_mm3 <= 0.6 * cavity_mm3,
       f"shell+lid ~{shell_lid_g:.0f} g -> steel {ballast_target:.0f} g = {steel_mm3 / 1000:.0f} cm3 "
       f"of {cavity_mm3 / 1000:.0f} cm3 cavity")

# --- Fit assembly -----------------------------------------------------------
scene = read_scene("STEP/bay_fit.step")
bodies = {}
for entity in scene.resolve("#bay_fit").entities("shape"):
    for solid in entity.shape().solids():
        bodies[entity.ref] = solid
print(f"\nbay_fit bodies: {len(bodies)}")


def find(label):
    hits = [e.shape().solids()[0] for e in scene.resolve(f"#{label}").entities("shape")]
    if len(hits) != 1:
        raise SystemExit(f"expected one body labeled {label!r}, got {len(hits)}")
    return hits[0]


# Interference: everything pairwise, except the shell/lid rebate contact (zero overlap expected anyway).
overlaps = []
for (ra, a), (rb, b) in combinations(bodies.items(), 2):
    v = overlap_volume(a, b)
    if v > 0.01:
        overlaps.append((ra, rb, round(v, 2)))
expect("no interference in bay_fit", not overlaps, overlaps or "0 overlapping pairs")

caddy = find("caddy")
shelf_lo = find("bay_shelf:lower")
shelf_hi = find("bay_shelf:upper")
shell = find("dummy_drive_shell")

d = closest_points(caddy, shelf_hi).distance
expect("caddy to shelf above >= 10 mm", d >= 10.0, f"{d:.2f} mm")
d = closest_points(caddy, shelf_lo).distance
expect("caddy rests on lower shelf (contact)", d < 0.01, f"{d:.3f} mm")
d = closest_points(shell, caddy).distance
expect("dummy drive sits on caddy floor (contact)", d < 0.01, f"{d:.3f} mm")

cb = caddy.bounding_box()
sb = shell.bounding_box()
expect("drive top below caddy top", sb.max.Z <= cb.max.Z, f"drive top z={sb.max.Z:.2f}, caddy top z={cb.max.Z:.2f}")
expect("handle block protrudes 20 mm from rack face", abs(cb.min.Y + 20.0) < 1e-6, f"caddy min y={cb.min.Y:.2f}")
expect("caddy rear at back stop (y=150)", abs(cb.max.Y - 150.0) < 1e-6, f"caddy max y={cb.max.Y:.2f}")

# Lateral clearance, measured: lift the caddy 3 mm off the floor and back it 3 mm off the stop, so the
# nearest shelf feature is a guide wall (as long as that clearance is under 3 mm).
lifted = caddy.moved(bd.Location((0.0, -3.0, 3.0)))
lat = closest_points(lifted, shelf_lo).distance
expect("lateral clearance per side 0.8-1.5 mm (measured)", 0.8 <= lat <= 1.5, f"{lat:.2f} mm")

if failures:
    raise SystemExit(f"\n{len(failures)} check(s) failed: {failures}")
print("\nAll checks passed.")
