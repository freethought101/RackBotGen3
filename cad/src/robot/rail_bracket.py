"""Y-rail bracket (PETG), modeled at Z = 0.

Holds the 2020 Y rail by its rear end only (the carriage travels over the rest) beside the rail's
inner face, bolts to the Z carriage plate's rear face, and carries the Y stepper (shaft down) on a horizontal plate behind the rail end.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M3_CLEAR, M5_CLEAR
from lib.prims import box, cyl_x, cyl_z
from lib.robot_dims import (BELT_X, PULLEY_Y, YBRACKET_DZ, YBRACKET_X, YBRACKET_Y, YMOTOR_PLATE_DZ, YRAIL_DZ,
                            YRAIL_Y, ZPLATE_TAB, ZPLATE_Y)

NEMA_PITCH = 31.0


@step(out="../../STEP/robot/rail_bracket.step")
@stl(out="../../STL/robot/rail_bracket.stl")
def rail_bracket():
    part = box(*YBRACKET_X, *YBRACKET_Y, *YBRACKET_DZ)                             # strip beside the rail
    zc = (YRAIL_DZ[0] + YRAIL_DZ[1]) / 2
    for y in (YRAIL_Y[0] + 12.0, YRAIL_Y[0] + 45.0):
        part -= cyl_x(M5_CLEAR, YBRACKET_X[0] - 0.1, YBRACKET_X[1] + 0.1, y, zc)    # into the rail inner slot
    # Horizontal Y-motor plate behind the rail end: motor body on top, shaft down through the plate to the
    # 20T pulley in the belt plane.
    pz0, pz1 = YMOTOR_PLATE_DZ
    part += box(YBRACKET_X[0], BELT_X + 22.0, YBRACKET_Y[0], PULLEY_Y + 23.0, pz0, pz1)
    part += box(*YBRACKET_X, YBRACKET_Y[0], PULLEY_Y + 23.0, YBRACKET_DZ[0], pz1)          # web to the strip
    part -= cyl_z(22.5, BELT_X, PULLEY_Y, pz0 - 0.1, pz1 + 0.1)                             # motor boss / shaft
    for dx in (-NEMA_PITCH / 2, NEMA_PITCH / 2):
        for dy in (-NEMA_PITCH / 2, NEMA_PITCH / 2):
            part -= cyl_z(M3_CLEAR, BELT_X + dx, PULLEY_Y + dy, pz0 - 0.1, pz1 + 0.1)
    # Front end drops below the extractor arm and bolts (M3) to the Z carriage plate's tab.
    part += box(*YBRACKET_X, ZPLATE_Y[0] - 12.0, ZPLATE_Y[0], ZPLATE_TAB[2], YBRACKET_DZ[1])
    part -= bd.Pos((ZPLATE_TAB[0] + ZPLATE_TAB[1]) / 2 + 3.0, ZPLATE_Y[0] - 12.1, (ZPLATE_TAB[2] + ZPLATE_TAB[3]) / 2) * \
        bd.Rot(-90, 0, 0) * bd.Cylinder(M3_CLEAR / 2, 12.2, align=(bd.Align.CENTER,) * 2 + (bd.Align.MIN,))
    part.label = "rail_bracket"
    return part


if __name__ == "__main__":
    rail_bracket()
