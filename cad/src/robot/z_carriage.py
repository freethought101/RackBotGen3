"""Z carriage plate (PETG), modeled at Z = 0 (the assembly moves it to the lift height).

Rides the 2040 mast on four mini V-wheels in the mast's side grooves (axles along y through the plate,
eccentric spacers on the +x pair). Carries the Tr8x2 anti-backlash nut on a side block (raised so it clears
the coupler at the bottom of the lift), and the tray stack on its front face: M5 screws go in from behind
into heat-set inserts in the tray back plate; the x = 50 column also clamps the Y-rail bracket.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import KW11, KW11_PRESS, M2_PILOT_D, M3_SELF_TAP_D, M5_CLEAR
from lib.prims import box, cyl_x, cyl_z
from lib.robot_dims import (ECC_HOLE_D, NUT_BLOCK_DZ, SCREW_XY, TRAY_BOLTS, WHEEL_SEAT_D, ZPLATE_DZ, ZPLATE_X,
                            ZPLATE_Y, ZWHEEL_DZ, ZWHEEL_SEAT_Y, ZWHEEL_X, Z_HOME)

NUT_FLANGE_D, NUT_BODY_D = 22.8, 10.8      # +0.3-0.8 for the print shrink (fit test 1)
# Common T8 nut flange (brass and POM anti-backlash): Ø22, 4 x Ø3.5 on a 16 mm circle. Not measured yet: check the
# bought nut. The flange sits in a recess UNDER the block (body up, so a long nut can't reach the coupler) and pushes
# up on the recess ceiling when lifting, so the 4 M3 self-tapping screws (from below) only locate it.
NUT_FLANGE_T = 4.0
NUT_HOLE_ANGLES = (45.0, 135.0, 225.0, 315.0)   # diagonals: most material around each pilot
NUT_HOLE_R = 8.0
NUT_PILOT_DEPTH = 12.0
NUT_BLOCK_HALF = 15.0                     # 30 x 30 block: >= 3.6 mm walls around the flange recess
# Two gussets under the block, beside the coupler (|x - screw| >= 11), brace the 50 mm overhang to the plate. They
# stay above the Z-motor mount (top z 112) at the hard stop.
GUSSET_T = 4.0
GUSSET_FOOT_DZ = 16.0                     # gusset bottom at the plate face
GUSSET_TIP_Y = -262.0                     # gusset meets the block underside here
# Z home switch (KW11-3Z): on a hanger below the nut block's -x side, lever pointing down onto the Z-motor mount plate
# (top at z 112, y -286.7..-246.4). It triggers at Z_HOME (lever pressed KW11_PRESS); slotted +/-1.5 in z to adjust.
ZSW_MOUNT_TOP = 112.0                     # z_motor_mount plate top (ZMOTOR_Z[1] + ZMOUNT_T)
ZSW_Y = (-266.0, -246.3)                  # body span along y; lever pivot at the -246.3 end, free end over the plate
ZSW_HANGER_T = 3.0
ZSW_ADJ = 1.5


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
            part += _y_hole(WHEEL_SEAT_D, s * ZWHEEL_X, z, ZWHEEL_SEAT_Y, y0 + 0.1)  # spacer seat pad
    for s in (-1, 1):
        for z in ZWHEEL_DZ:
            d = ECC_HOLE_D if s > 0 else M5_CLEAR                                   # eccentric spacers on +x
            part -= _y_hole(d, s * ZWHEEL_X, z, ZWHEEL_SEAT_Y - 0.1, y1 + 0.1)        # V-wheel axles
    sx, sy = SCREW_XY
    bh, (bz0, bz1) = NUT_BLOCK_HALF, NUT_BLOCK_DZ
    part += box(sx - bh, sx + bh, sy - bh, y0, bz0, bz1)
    for gx in (sx - bh, sx + bh - GUSSET_T):
        tri = bd.Polygon((y0 + 0.5, GUSSET_FOOT_DZ), (y0 + 0.5, bz0 + 0.5), (GUSSET_TIP_Y, bz0 + 0.5), align=None)
        part += bd.extrude(bd.Plane.YZ.offset(gx) * tri, amount=GUSSET_T)
    part -= cyl_z(NUT_BODY_D, sx, sy, bz0 - 0.1, bz1 + 0.1)
    part -= cyl_z(NUT_FLANGE_D, sx, sy, bz0 - 0.1, bz0 + NUT_FLANGE_T)
    for a in NUT_HOLE_ANGLES:
        hx, hy = bd.Vector(NUT_HOLE_R, 0, 0).rotate(bd.Axis.Z, a).to_tuple()[:2]
        part -= cyl_z(M3_SELF_TAP_D, sx + hx, sy + hy, bz0, bz0 + NUT_FLANGE_T + NUT_PILOT_DEPTH)
    for x, z in TRAY_BOLTS:
        part -= _y_hole(M5_CLEAR, x, z, y0 - 0.1, y1 + 0.1)
    # Z home switch hanger: plate on the nut block's -x face, switch on its -x face (screws from -x).
    kx = sx - bh                                                     # nut block -x face
    lever_edge = ZSW_MOUNT_TOP - KW11_PRESS + KW11["lever"] - Z_HOME  # body's lever edge, relative to Z
    pin_edge = lever_edge + KW11["h"]
    hx0 = kx - ZSW_HANGER_T                                          # switch body sits at hx0 - t .. hx0
    part += box(hx0, kx + 0.5, *ZSW_Y, lever_edge - 3.0, NUT_BLOCK_DZ[1])   # overlaps the block's side face
    yc, zh = (ZSW_Y[0] + ZSW_Y[1]) / 2, pin_edge - KW11["hole_up"]
    for dy in (-KW11["hole_dx"], KW11["hole_dx"]):
        part -= box(hx0 - 0.1, kx + 0.6, yc + dy - M2_PILOT_D / 2, yc + dy + M2_PILOT_D / 2,
                    zh - ZSW_ADJ, zh + ZSW_ADJ)
        for dz in (-ZSW_ADJ, ZSW_ADJ):
            part -= cyl_x(M2_PILOT_D, hx0 - 0.1, kx + 0.6, yc + dy, zh + dz)
    part.label = "z_carriage"
    return part


if __name__ == "__main__":
    z_carriage()
