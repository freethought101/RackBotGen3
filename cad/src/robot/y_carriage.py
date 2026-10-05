"""Y carriage with finger arm (PETG, one print), modeled at Z = 0 with the finger pivot at y = 0.

Rides the 2020 Y rail on its top and outer faces (mini V-wheels; no inner skirt so the arm and the
rear rail bracket stay clear). The arm hangs inside the rail and carries two MG90S servos whose
output shafts point +y; their mounting tabs screw into ledges on the arm.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M3_CLEAR
from lib.prims import box, cyl_z
from lib.robot_dims import (ARM_DY, ARM_X, FINGER_DZ, FINGER_X, SERVO, SERVO_FACE_DY, YCARRIAGE_DY,
                            YRAIL_DZ, YRAIL_X)

TOP_T = 6.0
SKIRT_T = 4.0
LEDGE_X0 = 61.5
LEDGE_DEPTH = 5.0           # along +y, in front of the servo tabs
LEDGE_H = 4.5


def ledge_spans(f):
    """z spans of the tab ledges below and above a servo whose pivot is at height f."""
    off, ln, tab = SERVO["shaft_from_end"], SERVO["len"], SERVO["tab"]
    lo, hi = f - off, f - off + ln
    return [(lo - tab, lo), (hi, hi + tab)]


@step(out="../../STEP/robot/y_carriage.step")
@stl(out="../../STL/robot/y_carriage.stl")
def y_carriage():
    rail_top = YRAIL_DZ[1]
    part = box(ARM_X[0], YRAIL_X[1] + 1.0 + SKIRT_T, *YCARRIAGE_DY, rail_top, rail_top + TOP_T)   # top plate
    part += box(YRAIL_X[1] + 1.0, YRAIL_X[1] + 1.0 + SKIRT_T, *YCARRIAGE_DY, YRAIL_DZ[0], rail_top + TOP_T)
    z_lo = min(z0 for f in FINGER_DZ.values() for z0, _ in ledge_spans(f))
    z_hi = max(z1 for f in FINGER_DZ.values() for _, z1 in ledge_spans(f))
    part += box(*ARM_X, ARM_DY[0], ARM_DY[1], z_lo, max(z_hi, rail_top + TOP_T))   # arm
    tab_y = SERVO_FACE_DY - 9.5                                                   # front face of the tabs
    for f in FINGER_DZ.values():
        for z0, z1 in ledge_spans(f):
            part += box(LEDGE_X0, ARM_X[0], tab_y, tab_y + LEDGE_DEPTH, z0, z1)
            part -= bd.Pos(FINGER_X, tab_y - 0.1, (z0 + z1) / 2) * bd.Rot(-90, 0, 0) * bd.Cylinder(
                1.0, LEDGE_DEPTH + 0.2, align=(bd.Align.CENTER,) * 2 + (bd.Align.MIN,))   # M2 pilot
    # V-wheel axle holes: two on the top plate (riding the rail top groove), two on the skirt.
    yc = [YCARRIAGE_DY[0] + 10.0, YCARRIAGE_DY[1] - 10.0]
    for y in yc:
        part -= cyl_z(M3_CLEAR + 1.6, (YRAIL_X[0] + YRAIL_X[1]) / 2, y, rail_top - 0.1, rail_top + TOP_T + 0.1)
    part.label = "y_carriage"
    return part


if __name__ == "__main__":
    y_carriage()
