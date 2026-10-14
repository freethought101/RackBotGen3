"""Y-belt idler bracket (PETG), modeled at Z = 0.

A fork bolted (M5 + T-nut) to the front end of the Y rail's outer face; the GT2 idler spins on an M5
bolt between the two arms, in the belt plane. Sits ahead of the carriage at full stroke (carriage front
y = -52 at Y = 175). Slotted bolt hole (+/-3 mm in y) tensions the belt.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M5_CLEAR
from lib.prims import box, cyl_x, cyl_z
from lib.robot_dims import BELT_DZ, BELT_X, IDLER_BRACKET_Y, IDLER_Y, PULLEY_FLANGE_D, YRAIL_DZ, YRAIL_X

PLATE_T = 3.0
ARM_T = 3.0
GAP = 1.5                    # flange to arm
TENSION_SLOT = 3.0


@step(out="../../STEP/robot/y_idler_bracket.step")
@stl(out="../../STL/robot/y_idler_bracket.stl")
def y_idler_bracket():
    y0, y1 = IDLER_BRACKET_Y
    x0 = YRAIL_X[1]                                          # rail outer face
    z_lo = BELT_DZ[0] - 1.0 - GAP - ARM_T                    # below the lower flange
    z_hi = BELT_DZ[1] + 1.0 + GAP + ARM_T
    x1 = BELT_X + PULLEY_FLANGE_D / 2 + 3.0
    part = box(x0, x0 + PLATE_T, y0, y1, min(z_lo, YRAIL_DZ[0]), max(z_hi, YRAIL_DZ[1]))
    part += box(x0, x1, y0, y1, z_lo, z_lo + ARM_T)
    part += box(x0, x1, y0, y1, z_hi - ARM_T, z_hi)
    part -= cyl_z(M5_CLEAR, BELT_X, IDLER_Y, z_lo - 0.1, z_hi + 0.1)                   # idler axle
    zc = (YRAIL_DZ[0] + YRAIL_DZ[1]) / 2
    yc = (y0 + y1) / 2
    for dy in (-TENSION_SLOT, TENSION_SLOT):
        part -= cyl_x(M5_CLEAR, x0 - 0.1, x0 + PLATE_T + 0.1, yc + dy, zc)
    part -= box(x0 - 0.1, x0 + PLATE_T + 0.1, yc - TENSION_SLOT, yc + TENSION_SLOT, zc - M5_CLEAR / 2, zc + M5_CLEAR / 2)
    part.label = "y_idler_bracket"
    return part


if __name__ == "__main__":
    y_idler_bracket()
