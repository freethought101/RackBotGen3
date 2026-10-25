"""Mast top plate (PETG): caps the 2040 mast and carries the KFL08 2-bolt flange bearing (hanging below the
plate, bore vertical) for the top of the Tr8x2 lead screw. A front tab bolts into both of the mast's front slots
(2 x M5 + T-nuts at x = +/-10; no tapping of the extrusion ends). The E-stop box screws onto the plate top with
2 x M3 into heat-set inserts.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M3_INSERT_D, M5_CLEAR
from lib.prims import box, cyl_z
from lib.robot_dims import ESTOP_XY, KFL08, MAST_X, MAST_Y, MAST_Z, SCREW_XY

T = 6.0
TAB = (MAST_Y[1], MAST_Y[1] + 4.0)          # in front of the mast face
TAB_DROP = 30.0
SLOT_X = (-10.0, 10.0)                      # 2040 front face slots
ESTOP_HOLE_DX = 13.0                        # +/- from the E-stop centre (verify against the purchased box)
INSERT_DEPTH = 5.0


def _y_hole(d, x, z, y0, y1):
    return bd.Pos(x, y0, z) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        d / 2, y1 - y0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


@step(out="../../STEP/robot/mast_top_plate.step")
@stl(out="../../STL/robot/mast_top_plate.stl")
def mast_top_plate():
    ztop = MAST_Z[1]
    sx, sy = SCREW_XY
    x0, x1 = sx - 17.0, MAST_X[1] + 4.0
    y0, y1 = sy - KFL08["l"] / 2 - 2.0, TAB[1]
    part = box(x0, x1, y0, y1, ztop, ztop + T)
    part += box(MAST_X[0], MAST_X[1], *TAB, ztop - TAB_DROP, ztop)
    for x in SLOT_X:
        part -= _y_hole(M5_CLEAR, x, ztop - TAB_DROP / 2, TAB[0] - 0.1, TAB[1] + 0.1)     # -> front slots
    part -= cyl_z(10.0, sx, sy, ztop - 0.1, ztop + T + 0.1)                       # screw clearance
    for dy in (-KFL08["pitch"] / 2, KFL08["pitch"] / 2):
        part -= cyl_z(M5_CLEAR, sx, sy + dy, ztop - 0.1, ztop + T + 0.1)          # KFL08 hangs below (M4 + nut)
    ex, ey = ESTOP_XY
    for dx in (-ESTOP_HOLE_DX, ESTOP_HOLE_DX):
        part -= cyl_z(M3_INSERT_D, ex + dx, ey, ztop + T - INSERT_DEPTH, ztop + T + 0.1)  # E-stop box
    part.label = "mast_top_plate"
    return part


if __name__ == "__main__":
    mast_top_plate()
