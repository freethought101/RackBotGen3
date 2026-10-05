"""Mast collar (PETG): clamps the bottom of the 2040 mast to the deck and the mast cross member.
Two M5 bolts into the mast side slots, four M5 down through the deck. The mast unit lifts out
for packing by undoing the four vertical bolts.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M5_CLEAR
from lib.prims import box, cyl_x, cyl_z
from lib.robot_dims import CROSS_Y, DECK_Z, MAST_X, MAST_Y

WALL = 6.0
HEIGHT = 23.0          # top at z = 90, below the Z carriage plate at its lowest (z = 92)
FIT = 0.2


@step(out="../../STEP/robot/mast_collar.step")
@stl(out="../../STL/robot/mast_collar.stl")
def mast_collar():
    z0 = DECK_Z[1]
    x0, x1 = MAST_X[0] - WALL, MAST_X[1] + WALL
    y0, y1 = MAST_Y[0] - WALL, MAST_Y[1] + WALL
    part = box(x0, x1, y0, y1, z0, z0 + HEIGHT)
    part -= box(MAST_X[0] - FIT, MAST_X[1] + FIT, MAST_Y[0] - FIT, MAST_Y[1] + FIT, z0 - 0.1, z0 + HEIGHT + 0.1)
    yc = (MAST_Y[0] + MAST_Y[1]) / 2
    part -= cyl_x(M5_CLEAR, x0 - 0.1, x1 + 0.1, yc, z0 + HEIGHT / 2)             # into the mast side slots
    ym = (CROSS_Y["mast"][0] + CROSS_Y["mast"][1]) / 2
    for x in (MAST_X[0] - 3.0, MAST_X[1] + 3.0):
        for y in (ym - 3.0, -227.0):
            part -= cyl_z(M5_CLEAR, x, y, z0 - 0.1, z0 + HEIGHT + 0.1)
    part.label = "mast_collar"
    return part


if __name__ == "__main__":
    mast_collar()
