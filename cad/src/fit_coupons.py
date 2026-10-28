"""Fit-test coupons (print first, < 1 h each, before the full caddies/shelves). See docs/fit-test-01.md.

- shelf_slice: the front 40 mm of the bay shelf (lead-in, guide walls, front flange block with the M5 bolts).
- caddy_slice: the rear 40 mm of the caddy, cut at z = 12 (rails, side walls, floor, rear chamfer/ramp).
  Slides into shelf_slice: tests the 1 mm/side channel clearance on your printer.
- hole_coupon: one of each hole size used on the printed parts, small to large from the chamfered corner.
"""

from cadgen import step, stl

from bay_shelf import bay_shelf
from caddy import caddy
from lib.dims import (BAY_CHANNEL_W, CADDY_BODY_L, M2_PILOT_D, M3_CLEAR, M3_INSERT_D, M3_SELF_TAP_D, M5_CLEAR,
                      M5_INSERT_D)
from lib.prims import box, cyl_z, prism_xy

SLICE_L = 40.0
CADDY_SLICE_H = 12.0

# (diameter, blind depth or None = through): M2 pilot, M3 self-tap, M3 clear, M3 insert, M5 clear, M5 insert
HOLES = [(M2_PILOT_D, None), (M3_SELF_TAP_D, None), (M3_CLEAR, None), (M3_INSERT_D, None), (M5_CLEAR, None),
         (M5_INSERT_D, 12.0)]
COUPON_T = 14.0
PITCH = 15.0


@step(out="../STEP/fit/shelf_slice.step")
@stl(out="../STL/fit/shelf_slice.stl")
def shelf_slice():
    part = bay_shelf() & box(-100, 100, 0, SLICE_L, -10, 30)
    part.label = "shelf_slice"
    return part


@step(out="../STEP/fit/caddy_slice.step")
@stl(out="../STL/fit/caddy_slice.stl")
def caddy_slice():
    w = BAY_CHANNEL_W
    part = caddy() & box(-w, w, CADDY_BODY_L - SLICE_L, CADDY_BODY_L + 1, -1, CADDY_SLICE_H)
    part.label = "caddy_slice"
    return part


@step(out="../STEP/fit/hole_coupon.step")
@stl(out="../STL/fit/hole_coupon.stl")
def hole_coupon():
    length = PITCH * (len(HOLES) + 1)
    part = box(0, length, 0, 18, 0, COUPON_T)
    part -= prism_xy([(-0.1, -0.1), (5, -0.1), (-0.1, 5)], -0.1, COUPON_T + 0.1)   # marks the small end
    for i, (d, depth) in enumerate(HOLES):
        z0 = -0.1 if depth is None else COUPON_T - depth
        part -= cyl_z(d, PITCH * (i + 1), 9.0, z0, COUPON_T + 0.1)
    part.label = "hole_coupon"
    return part


if __name__ == "__main__":
    shelf_slice()
    caddy_slice()
    hole_coupon()
