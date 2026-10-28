"""Y carriage with finger arm (PETG, one print), modeled at Z = 0 with the finger pivot at y = 0.

Gantry-style: a plate on the rail's outer face carries four mini V-wheels on axles along x, two above and
two below the rail (one of each pair on an eccentric spacer), so the carriage is captured in z, x and yaw.
A frame over the top wheels joins the plate to the arm on the rail's inner side. The arm carries the two
MG90S servos (output shafts along +y; their tabs screw into ledges on the arm). The belt's two ends are clamped to a
pad on the plate's outer face by a separate jaw (belt_clamp.py, 2 x M3 into inserts in the plate).
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M2_PILOT_D, M3_INSERT_D, M5_CLEAR
from lib.prims import box, cyl_x
from lib.robot_dims import (ARM_DY, ARM_X, BELT_DZ, BELT_STRAND_X, ECC_HOLE_D, ECC_OFFSET, FINGER_DZ, FINGER_X, SERVO,
                            SERVO_FACE_DY, WHEEL_SEAT_D, YCARRIAGE_DY, YFRAME_DZ, YPLATE_X, YWHEEL_DY, YWHEEL_DZ,
                            YWHEEL_SEAT_X)

LEDGE_X0 = FINGER_X - SERVO["wid"] / 2      # flush with the servo's side, 2.4 mm from the tray lip
LEDGE_DEPTH = 5.0           # along +y, in front of the servo tabs
SERVO_SHIM = 1.0            # nominal washer stack between tab and ledge: 0-2 mm tunes the servo stack +/-1 mm
CLAMP_DY = (-80.0, -62.0)   # belt clamp y span relative to the finger pivot (between the wheel axle bolts)
CLAMP_SCREW_DZ = (BELT_DZ[0] - 3.0, BELT_DZ[1] + 3.0)   # M3 inserts below and above the belt band
M2_PILOT = M2_PILOT_D       # self-tapping M2 into PETG


def ledge_spans(f):
    """z spans of the tab ledges below and above a servo whose pivot is at height f."""
    off, ln, tab = SERVO["shaft_from_end"], SERVO["len"], SERVO["tab"]
    lo, hi = f - off, f - off + ln
    return [(lo - tab, lo), (hi, hi + tab)]


@step(out="../../STEP/robot/y_carriage.step")
@stl(out="../../STL/robot/y_carriage.stl")
def y_carriage():
    px0, px1 = YPLATE_X
    fz0, fz1 = YFRAME_DZ
    part = box(px0, px1, *YCARRIAGE_DY, 0.0, fz1)                                   # outer wheel plate
    part += box(ARM_X[0], px1, YCARRIAGE_DY[0], ARM_DY[0], fz0, fz1)                # frame over the top wheels
    z_lo = min(z0 for f in FINGER_DZ.values() for z0, _ in ledge_spans(f))
    z_hi = max(z1 for f in FINGER_DZ.values() for _, z1 in ledge_spans(f))
    part += box(*ARM_X, ARM_DY[0], ARM_DY[1], z_lo, max(z_hi, fz1))                 # arm
    tab_y = SERVO_FACE_DY - SERVO["tab_drop"] + SERVO_SHIM                          # ledge face: tab face + 1 mm shim
    for f in FINGER_DZ.values():
        for z0, z1 in ledge_spans(f):
            part += box(LEDGE_X0, ARM_X[0], tab_y, tab_y + LEDGE_DEPTH, z0, z1)
            part -= bd.Pos(FINGER_X, tab_y - 0.1, (z0 + z1) / 2) * bd.Rot(-90, 0, 0) * bd.Cylinder(
                M2_PILOT / 2, LEDGE_DEPTH + 0.2, align=(bd.Align.CENTER,) * 2 + (bd.Align.MIN,))
    # V-wheel axles through the outer plate, above and below the rail; eccentric spacers on the lower pair.
    # Each spacer sits in a shallow recess so the wheel runs on the groove centre.
    for y in YWHEEL_DY:
        for z in YWHEEL_DZ:
            part -= cyl_x(WHEEL_SEAT_D, px0 - 0.1, YWHEEL_SEAT_X, y, z)
            if z == YWHEEL_DZ[0]:                                                   # eccentric boss, 0.7 behind the axle
                part -= cyl_x(ECC_HOLE_D, px0 - 0.1, px1 + 0.1, y - ECC_OFFSET, z)
            else:
                part -= cyl_x(M5_CLEAR, px0 - 0.1, px1 + 0.1, y, z)
    # Belt clamp pad: brings the plate face out to the inner strand's back; the jaw (belt_clamp.py) presses the belt
    # ends onto it with 2 x M3 into heat-set inserts through the plate (above and below the belt).
    sx0, sx1 = BELT_STRAND_X[0]
    part += box(px1 - 0.1, sx0, *CLAMP_DY, BELT_DZ[0] - 1.0, BELT_DZ[1] + 1.0)
    for z in CLAMP_SCREW_DZ:
        part -= cyl_x(M3_INSERT_D, px0 - 0.1, px1 + 0.1, sum(CLAMP_DY) / 2, z)
    part.label = "y_carriage"
    return part


if __name__ == "__main__":
    y_carriage()
