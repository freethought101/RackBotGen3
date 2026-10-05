"""Mast top plate (PETG): caps the 2040 mast and carries the KP08 bearing for the top of the
Tr8x2 lead screw. A front tab bolts into the mast's front slot (no tapping of the extrusion ends).
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M5_CLEAR
from lib.prims import box, cyl_z
from lib.robot_dims import MAST_X, MAST_Y, MAST_Z, SCREW_XY

T = 6.0
TAB = (MAST_Y[1], MAST_Y[1] + 4.0)          # in front of the mast face
TAB_DROP = 30.0
KP08_HOLE_PITCH = 29.0


def _y_hole(d, x, z, y0, y1):
    return bd.Pos(x, y0, z) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        d / 2, y1 - y0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


@step(out="../../STEP/robot/mast_top_plate.step")
@stl(out="../../STL/robot/mast_top_plate.stl")
def mast_top_plate():
    ztop = MAST_Z[1]
    sx, sy = SCREW_XY
    x0, x1 = sx - 17.0, MAST_X[1] + 4.0
    # (the E-stop housing screws onto the plate top: 2 x M3 at the ESTOP_XY footprint)
    y0, y1 = sy - 19.0, TAB[1]
    part = box(x0, x1, y0, y1, ztop, ztop + T)
    part += box(MAST_X[0], MAST_X[1], *TAB, ztop - TAB_DROP, ztop)
    part -= _y_hole(M5_CLEAR, 0.0, ztop - TAB_DROP / 2, TAB[0] - 0.1, TAB[1] + 0.1)
    part -= cyl_z(10.0, sx, sy, ztop - 0.1, ztop + T + 0.1)                       # screw clearance
    for dy in (-KP08_HOLE_PITCH / 2, KP08_HOLE_PITCH / 2):
        part -= cyl_z(M5_CLEAR, sx, sy + dy, ztop - 0.1, ztop + T + 0.1)          # KP08 hangs below
    part.label = "mast_top_plate"
    return part


if __name__ == "__main__":
    mast_top_plate()
