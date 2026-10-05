"""Robot deck plate (PETG, 246 x 300 x 5, one print). Sits on the 2020 side rails; carries the
mast collar, electronics trays, battery box and E-stop, and caps the drive brackets.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M3_CLEAR, M5_CLEAR
from lib.prims import box, cyl_z
from lib.robot_dims import (AXLE_Y, BASE_FRONT_Y, BASE_REAR_Y, CROSS_Y, DECK_HALF_W, DECK_Z,
                            DRIVE_PLATE_X, MAST_X, RAIL_X)

RAIL_HOLE_Y = (-375.0, -250.0, -100.0)
CABLE_SLOTS = [(-10.0, 10.0, -330.0, -300.0), (-100.0, -85.0, -220.0, -180.0), (85.0, 100.0, -220.0, -180.0)]


@step(out="../../STEP/robot/deck.step")
@stl(out="../../STL/robot/deck.stl")
def deck():
    z0, z1 = DECK_Z
    part = box(-DECK_HALF_W, DECK_HALF_W, BASE_REAR_Y, BASE_FRONT_Y, z0, z1)
    xr = (RAIL_X[0] + RAIL_X[1]) / 2
    for s in (-1, 1):
        for y in RAIL_HOLE_Y:
            part -= cyl_z(M5_CLEAR, s * xr, y, z0 - 0.1, z1 + 0.1)              # into rail top slots
        xp = s * (DRIVE_PLATE_X[0] + DRIVE_PLATE_X[1]) / 2
        for y in (AXLE_Y - 25.0, AXLE_Y + 25.0):
            part -= cyl_z(M3_CLEAR, xp, y, z0 - 0.1, z1 + 0.1)                  # drive bracket inserts
    ym = (CROSS_Y["mast"][0] + CROSS_Y["mast"][1]) / 2
    for x in (MAST_X[0] - 3.0, MAST_X[1] + 3.0):
        part -= cyl_z(M5_CLEAR, x, ym - 3.0, z0 - 0.1, z1 + 0.1)                # mast collar -> cross member
        part -= cyl_z(M5_CLEAR, x, -227.0, z0 - 0.1, z1 + 0.1)
    for x0, x1, y0, y1 in CABLE_SLOTS:
        part -= box(x0, x1, y0, y1, z0 - 0.1, z1 + 0.1)
    part.label = "deck"
    return part


if __name__ == "__main__":
    deck()
