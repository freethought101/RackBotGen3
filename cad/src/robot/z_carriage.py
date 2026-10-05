"""Z carriage plate (PETG), modeled at Z = 0 (the assembly moves it to the lift height).

Rides the 2040 mast on four V-wheels (eccentric spacers on the side arms), carries the Tr8x2
anti-backlash nut on a side block, the tray stack on its front face and the Y-rail bracket.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M3_CLEAR, M5_CLEAR
from lib.prims import box, cyl_x, cyl_z
from lib.robot_dims import MAST_X, MAST_Y, SCREW_XY, TRAY_BOLTS, ZPLATE_DZ, ZPLATE_TAB, ZPLATE_X, ZPLATE_Y

ARM_W = 8.0
ARM_GAP = 1.0                 # to the mast side faces (V-wheels make the contact)
ARM_DZ = [(-10.0, 10.0), (80.0, 100.0)]
NUT_BLOCK_DZ = (30.0, 50.0)
NUT_FLANGE_D, NUT_BODY_D = 22.0, 10.5
WHEEL_AXLE_D = M5_CLEAR


@step(out="../../STEP/robot/z_carriage.step")
@stl(out="../../STL/robot/z_carriage.stl")
def z_carriage():
    part = box(*ZPLATE_X, *ZPLATE_Y, *ZPLATE_DZ)
    tx0, tx1, tz0, tz1 = ZPLATE_TAB
    part += box(tx0, tx1, *ZPLATE_Y, tz0, tz1)                                   # rail bracket tab
    part -= bd.Pos((tx0 + tx1) / 2 + 3.0, ZPLATE_Y[0] - 0.1, (tz0 + tz1) / 2) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        M3_CLEAR / 2, ZPLATE_Y[1] - ZPLATE_Y[0] + 0.2, align=(bd.Align.CENTER,) * 2 + (bd.Align.MIN,))
    for s in (-1, 1):
        xa0, xa1 = sorted((s * (MAST_X[1] + ARM_GAP), s * (MAST_X[1] + ARM_GAP + ARM_W)))
        for z0, z1 in ARM_DZ:
            part += box(xa0, xa1, MAST_Y[0] - 2.0, ZPLATE_Y[0], z0, z1)
            part -= cyl_x(WHEEL_AXLE_D, xa0 - 0.1, xa1 + 0.1, (MAST_Y[0] + MAST_Y[1]) / 2, (z0 + z1) / 2)
    sx, sy = SCREW_XY
    part += box(sx - 13.0, sx + 13.0, sy - 13.0, ZPLATE_Y[0], *NUT_BLOCK_DZ)
    part -= cyl_z(NUT_BODY_D, sx, sy, NUT_BLOCK_DZ[0] - 0.1, NUT_BLOCK_DZ[1] + 0.1)
    part -= cyl_z(NUT_FLANGE_D, sx, sy, NUT_BLOCK_DZ[1] - 4.0, NUT_BLOCK_DZ[1] + 0.1)
    for a in (0.0, 120.0, 240.0):
        part -= bd.Pos(sx, sy, NUT_BLOCK_DZ[0]) * bd.Rot(0, 0, a) * bd.Pos(8.0, 0, 0) * bd.Cylinder(
            M3_CLEAR / 2, NUT_BLOCK_DZ[1] - NUT_BLOCK_DZ[0] + 0.2, align=(bd.Align.CENTER,) * 2 + (bd.Align.MIN,))
    # Tray stack and rail bracket bolt pattern (M5 through the plate, along y).
    for x, z in TRAY_BOLTS:
        part -= bd.Pos(x, ZPLATE_Y[0] - 0.1, z) * bd.Rot(-90, 0, 0) * bd.Cylinder(
            M5_CLEAR / 2, ZPLATE_Y[1] - ZPLATE_Y[0] + 0.2, align=(bd.Align.CENTER,) * 2 + (bd.Align.MIN,))
    part.label = "z_carriage"
    return part


if __name__ == "__main__":
    z_carriage()
