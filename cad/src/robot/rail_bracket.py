"""Y-rail bracket (PETG), modeled at Z = 0.

A back plate behind the Z carriage plate is clamped by the x = 50 column of tray screws (3 x M5, 80 mm
apart), so the extractor's weight and the pull/push loads go straight into the tray/Z-plate sandwich.
A 16 x 20 strip runs back along the rail's inner face (2 x M5 into the rail's inner slot) to a horizontal
plate behind the rail end that carries the Y stepper (shaft down). Everything sits behind y = -228.5, out
of the carriage arm's travel; above z_step the back plate stops short of the carriage frame.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M3_CLEAR, M5_CLEAR
from lib.prims import box, cyl_x, cyl_z
from lib.robot_dims import (BELT_X, PULLEY_Y, RAIL_BRACKET_BOLT_X, TRAY_BOLTS, YBRACKET_DZ, YBRACKET_PLATE,
                            YBRACKET_PLATE_Y, YBRACKET_X, YBRACKET_Y, YMOTOR_PLATE_DZ, YRAIL_DZ, YRAIL_Y)

NEMA_PITCH = 31.0


def _y_hole(d, x, z, y0, y1):
    return bd.Pos(x, y0, z) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        d / 2, y1 - y0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


@step(out="../../STEP/robot/rail_bracket.step")
@stl(out="../../STL/robot/rail_bracket.stl")
def rail_bracket():
    part = box(*YBRACKET_X, *YBRACKET_Y, *YBRACKET_DZ)                             # strip beside the rail
    zc = (YRAIL_DZ[0] + YRAIL_DZ[1]) / 2
    for y in (YRAIL_Y[0] + 12.0, YRAIL_Y[0] + 45.0):
        part -= cyl_x(M5_CLEAR, YBRACKET_X[0] - 0.1, YBRACKET_X[1] + 0.1, y, zc)    # into the rail inner slot
    # Back plate (L-shaped: full width below z_step, narrower above it).
    bx0, bx1_hi, bx1_lo, z_step, bz0, bz1 = YBRACKET_PLATE
    py0, py1 = YBRACKET_PLATE_Y
    part += box(bx0, bx1_lo, py0, py1, bz0, z_step)
    part += box(bx0, bx1_hi, py0, py1, z_step, bz1)
    for x, z in TRAY_BOLTS:
        if x == RAIL_BRACKET_BOLT_X:
            part -= _y_hole(M5_CLEAR, x, z, py0 - 0.1, py1 + 0.1)
    # Horizontal Y-motor plate behind the rail end: motor body on top, shaft down through the plate to the
    # 20T pulley in the belt plane.
    pz0, pz1 = YMOTOR_PLATE_DZ
    part += box(YBRACKET_X[0], BELT_X + 19.0, YBRACKET_Y[0], PULLEY_Y + 23.0, pz0, pz1)   # motor overhangs 2 mm
    part += box(*YBRACKET_X, YBRACKET_Y[0], PULLEY_Y + 23.0, YBRACKET_DZ[0], pz1)          # web to the strip
    part -= cyl_z(22.5, BELT_X, PULLEY_Y, pz0 - 0.1, pz1 + 0.1)                             # motor boss / shaft
    for dx in (-NEMA_PITCH / 2, NEMA_PITCH / 2):
        for dy in (-NEMA_PITCH / 2, NEMA_PITCH / 2):
            part -= cyl_z(M3_CLEAR, BELT_X + dx, PULLEY_Y + dy, pz0 - 0.1, pz1 + 0.1)
    part.label = "rail_bracket"
    return part


if __name__ == "__main__":
    rail_bracket()
