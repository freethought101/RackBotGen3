"""Z carriage plate (PETG), modeled at Z = 0 (the assembly moves it to the lift height).

Rides the 2040 mast on four mini V-wheels in the mast's side grooves (axles along y through the plate,
eccentric spacers on the +x pair). Carries the Tr8x2 anti-backlash nut on a side block (raised so it clears
the coupler at the bottom of the lift), and the tray stack on its front face: M5 screws go in from behind
into heat-set inserts in the tray back plate; the x = 50 column also clamps the Y-rail bracket.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M3_CLEAR, M5_CLEAR
from lib.prims import box, cyl_z
from lib.robot_dims import (NUT_BLOCK_DZ, SCREW_XY, TRAY_BOLTS, ZPLATE_DZ, ZPLATE_X, ZPLATE_Y, ZWHEEL_DZ,
                            ZWHEEL_X)

NUT_FLANGE_D, NUT_BODY_D = 22.0, 10.5


def _y_hole(d, x, z, y0, y1):
    return bd.Pos(x, y0, z) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        d / 2, y1 - y0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


@step(out="../../STEP/robot/z_carriage.step")
@stl(out="../../STL/robot/z_carriage.stl")
def z_carriage():
    y0, y1 = ZPLATE_Y
    part = box(*ZPLATE_X, y0, y1, *ZPLATE_DZ)
    for s in (-1, 1):
        for z in ZWHEEL_DZ:
            part -= _y_hole(M5_CLEAR, s * ZWHEEL_X, z, y0 - 0.1, y1 + 0.1)          # V-wheel axles
    sx, sy = SCREW_XY
    part += box(sx - 13.0, sx + 13.0, sy - 13.0, y0, *NUT_BLOCK_DZ)
    part -= cyl_z(NUT_BODY_D, sx, sy, NUT_BLOCK_DZ[0] - 0.1, NUT_BLOCK_DZ[1] + 0.1)
    part -= cyl_z(NUT_FLANGE_D, sx, sy, NUT_BLOCK_DZ[1] - 4.0, NUT_BLOCK_DZ[1] + 0.1)
    for a in (0.0, 120.0, 240.0):
        part -= bd.Pos(sx, sy, NUT_BLOCK_DZ[0]) * bd.Rot(0, 0, a) * bd.Pos(8.0, 0, 0) * bd.Cylinder(
            M3_CLEAR / 2, NUT_BLOCK_DZ[1] - NUT_BLOCK_DZ[0] + 0.2, align=(bd.Align.CENTER,) * 2 + (bd.Align.MIN,))
    for x, z in TRAY_BOLTS:
        part -= _y_hole(M5_CLEAR, x, z, y0 - 0.1, y1 + 0.1)
    part.label = "z_carriage"
    return part


if __name__ == "__main__":
    z_carriage()
