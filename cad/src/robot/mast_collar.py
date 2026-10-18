"""Mast collar (PETG): locates and braces the foot of the 2040 mast.

The mast passes through a cut-out in the deck and stands on the mast cross member (directly below it).
The collar is a 28 mm deep, close-fitting socket (deck cut-out + 23 mm collar) with:
- a flange on the +x side with two M5 down through the deck into the cross member's top slot (T-nuts); the
  -x side is left free for the Z motor,
- two M5 into the mast's side slots (below the Z wheels' lowest position),
- a rear gusset: a plate on the mast's back face (4 x M5 into its two back slots, up to z 160) with a rib
  down to the deck, so a forward tilt of the loaded mast puts the gusset in tension.
The mast unit lifts out for packing by undoing the flange, side and gusset bolts.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M5_CLEAR
from lib.prims import box, cyl_x, cyl_z, prism_yz
from lib.robot_dims import CROSS_Y, DECK_Z, MAST_X, MAST_Y

WALL = 6.0
HEIGHT = 23.0          # top at z = 90, below the Z carriage plate (92) and wheels (92.4) at their lowest
FIT = 0.3              # per side on the 2040: the printed pocket comes out undersize
FLANGE_X = (20.0, 52.0)       # +x side only; bolts at x = 32 and 46 into the cross member's top slot
FLANGE_T = 6.0
FLANGE_Y = (-245.5, -234.5)
GUSSET_X = 16.0        # |x| of the back plate (bolts at |x| = 10, the back slots)
GUSSET_TOP = 160.0
GUSSET_T = 6.0
RIB_T = 6.0
RIB_LEN = 25.0         # rib foot length behind the back plate


def _y_hole(d, x, z, y0, y1):
    return bd.Pos(x, y0, z) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        d / 2, y1 - y0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


@step(out="../../STEP/robot/mast_collar.step")
@stl(out="../../STL/robot/mast_collar.stl")
def mast_collar():
    z0 = DECK_Z[1]
    x0, x1 = MAST_X[0] - WALL, MAST_X[1] + WALL
    y0, y1 = MAST_Y[0] - WALL, MAST_Y[1] + WALL
    part = box(x0, x1, y0, y1, z0, z0 + HEIGHT)
    part += box(*FLANGE_X, *FLANGE_Y, z0, z0 + FLANGE_T)
    yb = MAST_Y[0]                                                                 # mast back face
    part += box(-GUSSET_X, GUSSET_X, yb - GUSSET_T, yb, z0, GUSSET_TOP)
    part += prism_yz([(yb - GUSSET_T, z0), (yb - GUSSET_T - RIB_LEN, z0), (yb - GUSSET_T, GUSSET_TOP)],
                     -RIB_T / 2, RIB_T / 2)
    part -= box(MAST_X[0] - FIT, MAST_X[1] + FIT, MAST_Y[0] - FIT, MAST_Y[1] + FIT, z0 - 0.1, GUSSET_TOP + 0.1)
    yc = (MAST_Y[0] + MAST_Y[1]) / 2
    part -= cyl_x(M5_CLEAR, x0 - 0.1, x1 + 0.1, yc, z0 + HEIGHT / 2)              # into the mast side slots
    ym = (CROSS_Y["mast"][0] + CROSS_Y["mast"][1]) / 2
    for x in (32.0, 46.0):
        part -= cyl_z(M5_CLEAR, x, ym, z0 - 0.1, z0 + FLANGE_T + 0.1)              # -> cross member top slot
    for x in (-10.0, 10.0):
        for z in (110.0, 150.0):
            part -= _y_hole(M5_CLEAR, x, z, yb - GUSSET_T - 0.1, yb + 0.1)        # -> mast back slots
    part.label = "mast_collar"
    return part


if __name__ == "__main__":
    mast_collar()
