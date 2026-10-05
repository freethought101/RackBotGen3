"""Y-rail bracket (PETG), modeled at Z = 0.

Holds the 2020 Y rail by its rear end only (the carriage travels over the rest) beside the rail's
inner face, bolts to the Z carriage plate's rear face, and carries the Y stepper behind the rail.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M3_CLEAR, M5_CLEAR
from lib.prims import box, cyl_x
from lib.robot_dims import (YBRACKET_DZ, YBRACKET_X, YBRACKET_Y, YMOTOR_X, YMOTOR_Y, YRAIL_DZ, YRAIL_X,
                            YRAIL_Y, ZPLATE_TAB, ZPLATE_Y)

MOTOR_PLATE_T = 4.0
NEMA_PITCH = 31.0


@step(out="../../STEP/robot/rail_bracket.step")
@stl(out="../../STL/robot/rail_bracket.stl")
def rail_bracket():
    part = box(*YBRACKET_X, *YBRACKET_Y, *YBRACKET_DZ)                             # strip beside the rail
    zc = (YRAIL_DZ[0] + YRAIL_DZ[1]) / 2
    for y in (YRAIL_Y[0] + 12.0, YRAIL_Y[0] + 45.0):
        part -= cyl_x(M5_CLEAR, YBRACKET_X[0] - 0.1, YBRACKET_X[1] + 0.1, y, zc)    # into the rail inner slot
    # Motor plate behind the rail end, motor shaft along +y (belt drive along the rail).
    py0 = YMOTOR_Y[0] - MOTOR_PLATE_T
    part += box(YBRACKET_X[0], YMOTOR_X[1], py0, YMOTOR_Y[0], YRAIL_DZ[0] - 11.0, YRAIL_DZ[1] + 11.0)
    mx, mz = (YMOTOR_X[0] + YMOTOR_X[1]) / 2, zc
    part -= bd.Pos(mx, py0 - 0.1, mz) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        11.5, MOTOR_PLATE_T + 0.2, align=(bd.Align.CENTER,) * 2 + (bd.Align.MIN,))
    for dx in (-NEMA_PITCH / 2, NEMA_PITCH / 2):
        for dz in (-NEMA_PITCH / 2, NEMA_PITCH / 2):
            part -= bd.Pos(mx + dx, py0 - 0.1, mz + dz) * bd.Rot(-90, 0, 0) * bd.Cylinder(
                M3_CLEAR / 2, MOTOR_PLATE_T + 0.2, align=(bd.Align.CENTER,) * 2 + (bd.Align.MIN,))
    # Front end drops below the extractor arm and bolts (M3) to the Z carriage plate's tab.
    part += box(*YBRACKET_X, ZPLATE_Y[0] - 12.0, ZPLATE_Y[0], ZPLATE_TAB[2], YBRACKET_DZ[1])
    part -= bd.Pos((ZPLATE_TAB[0] + ZPLATE_TAB[1]) / 2 + 3.0, ZPLATE_Y[0] - 12.1, (ZPLATE_TAB[2] + ZPLATE_TAB[3]) / 2) * \
        bd.Rot(-90, 0, 0) * bd.Cylinder(M3_CLEAR / 2, 12.2, align=(bd.Align.CENTER,) * 2 + (bd.Align.MIN,))
    part.label = "rail_bracket"
    return part


if __name__ == "__main__":
    rail_bracket()
