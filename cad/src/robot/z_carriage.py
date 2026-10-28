"""Z carriage plate (PETG), modeled at Z = 0 (the assembly moves it to the lift height).

Rides the 2040 mast on four mini V-wheels in the mast's side grooves (axles along y through the plate,
eccentric spacers on the +x pair). Carries the Tr8x2 anti-backlash nut block beside the mast: a vertical fin and a
shelf behind the plate hold it (raised so it clears the coupler at the bottom of the lift), and the tray stack on its front face: M5 screws go in from behind
into heat-set inserts in the tray back plate; the x = 50 column also clamps the Y-rail bracket.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import KW11, KW11_PRESS, M2_PILOT_D, M5_CLEAR
from lib.prims import box, cyl_x, cyl_z
from lib.robot_dims import (ECC_HOLE_D, ECC_OFFSET, NUT_BLOCK, NUT_BLOCK_DZ, SCREW_XY, TRAY_BOLTS, WHEEL_SEAT_D, ZPLATE_DZ, ZPLATE_X,
                            ZPLATE_Y, ZWHEEL_DZ, ZWHEEL_SEAT_Y, ZWHEEL_X, Z_HOME)

# Nut block mount: the block's face sits on a fin's +x face (fin in the y-z plane, so the lift load runs in its
# plane), 2 x M5 through the fin into nylon-insert nuts in the block's hex pockets. The block's body end bears on a
# shelf above it: the carriage hangs on the nut through the shelf, not through the screws. The shelf has an access
# hole for the preload screw (fit the block with that screw on the +y side, toward the plate).
FIN_GAP = NUT_BLOCK["t"] / 2               # screw axis -> fin face
FIN_T = 6.0
FIN_Z0 = 43.0                             # above the coupler (top z 40 at Z_MIN, 41.4 at the hard stop)
FIN_LOW_Y = -247.0                        # in front of this the fin runs down to the switch hanger (clear of the coupler)
SHELF_T = 6.0
SHELF_X1 = -41.0                          # clear of the x -38 tray bolt heads (z <= 79.3, under the shelf)
SHELF_HOLE_D = 10.0                       # Tr8 screw + 1 mm
PRELOAD_ACCESS_D = 5.5                    # hex key to the M5 preload screw
BLOCK_MARGIN = 2.0                        # fin/shelf beyond the block's 34 width
MOUNT_Z = NUT_BLOCK_DZ[1] - NUT_BLOCK["hole_down"]
MOUNT_SLOT = 0.5                          # +/- in z, so the block can be pushed up against the shelf
# Z home switch (KW11-3Z): on a hanger below the fin's -x side, lever pointing down onto the Z-motor mount plate
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
            if s > 0:                                                               # eccentric spacer boss, 0.7 under the axle
                part -= _y_hole(ECC_HOLE_D, s * ZWHEEL_X, z - ECC_OFFSET, ZWHEEL_SEAT_Y - 0.1, y1 + 0.1)
            else:
                part -= _y_hole(M5_CLEAR, s * ZWHEEL_X, z, ZWHEEL_SEAT_Y - 0.1, y1 + 0.1)  # V-wheel axles
    sx, sy = SCREW_XY
    fx1 = sx - FIN_GAP
    fx0 = fx1 - FIN_T
    yb = sy - NUT_BLOCK["h"] / 2 - BLOCK_MARGIN                      # back edge
    part += box(fx0, fx1, yb, y0, FIN_Z0, NUT_BLOCK_DZ[1] + SHELF_T)                        # fin
    part += box(fx0, fx1, FIN_LOW_Y, y0, ZPLATE_DZ[0] + 23.0, FIN_Z0 + 0.1)                 # fin root, down to z 13
    part += box(fx0, SHELF_X1, yb, y0, NUT_BLOCK_DZ[1], NUT_BLOCK_DZ[1] + SHELF_T)          # shelf over the block
    part -= cyl_z(SHELF_HOLE_D, sx, sy, NUT_BLOCK_DZ[1] - 0.1, NUT_BLOCK_DZ[1] + SHELF_T + 0.1)
    part -= cyl_z(PRELOAD_ACCESS_D, sx, sy + NUT_BLOCK["preload_dy"], NUT_BLOCK_DZ[1] - 0.1,
                  NUT_BLOCK_DZ[1] + SHELF_T + 0.1)
    p = NUT_BLOCK["pitch"] / 2
    for y in (sy - p, sy + p):
        part -= box(fx0 - 0.1, fx1 + 0.1, y - M5_CLEAR / 2, y + M5_CLEAR / 2, MOUNT_Z - MOUNT_SLOT, MOUNT_Z + MOUNT_SLOT)
        for dz in (-MOUNT_SLOT, MOUNT_SLOT):
            part -= cyl_x(M5_CLEAR, fx0 - 0.1, fx1 + 0.1, y, MOUNT_Z + dz)
    for x, z in TRAY_BOLTS:
        part -= _y_hole(M5_CLEAR, x, z, y0 - 0.1, y1 + 0.1)
    # Z home switch hanger: plate on the nut block's -x face, switch on its -x face (screws from -x).
    kx = fx0                                                         # fin -x face
    lever_edge = ZSW_MOUNT_TOP - KW11_PRESS + KW11["lever"] - Z_HOME  # body's lever edge, relative to Z
    pin_edge = lever_edge + KW11["h"]
    hx0 = kx - ZSW_HANGER_T                                          # switch body sits at hx0 - t .. hx0
    part += box(hx0, kx + 0.5, *ZSW_Y, lever_edge, FIN_Z0 + 8.0)             # overlaps the fin's side face; no lower:
    # below the switch body it would land on the Z-motor screw heads at the hard stop
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
