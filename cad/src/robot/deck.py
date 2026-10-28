"""Robot deck plate (PETG, 246 x 300 x 5, one print). Sits on the 2020 side rails; carries the
mast collar, Z-motor mount, electronics trays and battery box, and caps the drive brackets. The mast
passes through a cut-out and stands on the mast cross member.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M3_CLEAR, M5_CLEAR
from lib.prims import box, cyl_z
from lib.robot_dims import (BASE_FRONT_Y, BASE_REAR_Y, BATTERY_DECK_HOLES, CROSS_Y, DECK_HALF_W, DECK_Z,
                            DRIVE_INSERT_X, DRIVE_INSERT_Y, MAST_X, MAST_Y, PCB_DECK_HOLES, PI_DECK_HOLES, RAIL_X,
                            SCREW_XY)

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
        for y in DRIVE_INSERT_Y:
            part -= cyl_z(M3_CLEAR, s * DRIVE_INSERT_X, y, z0 - 0.1, z1 + 0.1)  # drive bracket inserts
    part -= box(MAST_X[0] - 0.3, MAST_X[1] + 0.3, MAST_Y[0] - 0.3, MAST_Y[1] + 0.3, z0 - 0.1, z1 + 0.1)   # mast
    ym = (CROSS_Y["mast"][0] + CROSS_Y["mast"][1]) / 2
    for x in (32.0, 46.0):
        part -= cyl_z(M5_CLEAR, x, ym, z0 - 0.1, z1 + 0.1)                      # mast collar -> cross member
    sx, sy = SCREW_XY
    for x in (sx - 21.65 - 3.0 - 4.0, sx + 21.65 + 3.0 + 4.0):
        part -= cyl_z(M3_CLEAR, x, sy - 16.0, z0 - 0.1, z1 + 0.1)                 # Z-motor mount feet
    for x, y in PCB_DECK_HOLES + PI_DECK_HOLES + BATTERY_DECK_HOLES:
        part -= cyl_z(M3_CLEAR, x, y, z0 - 0.1, z1 + 0.1)                       # trays, battery box (M3 + nut)
    for x0, x1, y0, y1 in CABLE_SLOTS:
        part -= box(x0, x1, y0, y1, z0 - 0.1, z1 + 0.1)
    part.label = "deck"
    return part


if __name__ == "__main__":
    deck()
