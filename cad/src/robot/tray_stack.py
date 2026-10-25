"""Tray stack (PETG, one print 122 x 197 x 90), modeled at Z = 0. Print it standing on the back plate
(slot floors vertical) so neither floor needs support.

Two caddy slots stacked at the bay pitch: slot B floor at z = Z, slot A floor at z = Z + 45.
Left wall full height; right side open above a 6 mm lip so the extractor fingers can reach the
caddy notch. Rear stops hold the caddy handle 5 mm short of the back plate; KW11-3Z slot-presence
switches lie flat in pockets behind the stops, open to the back face: drop each in from behind, fix it with
2 x M2 self-tapping screws driven through the access holes in the bottom face (slot B) or top face (slot A), and
run the wires down the groove in the back face; the Z carriage plate closes the pockets. The camera mount is on the
left wall. The back plate takes M5 heat-set inserts for the screws that come through the Z carriage plate from
behind, and has pockets for the lower Z-wheel axle nuts.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import CADDY_H, KW11, M2_PILOT_D, M5_INSERT_D
from lib.prims import box, cyl_z, prism_yz
from lib.robot_dims import (CAM_BOARD, CAM_DZ, CAM_LENS, SLOT_A_DZ, TRAY_CHANNEL_W, TRAY_FLOOR_T, TRAY_FRONT_Y,
                            TRAY_REAR_Y, TRAY_RIGHT_LIP_H, TRAY_STOP_Y, TRAY_TOP_DZ, TRAY_WALL_T, TRAY_BOLTS, ZPLATE_DZ,
                            ZWHEEL_DZ, ZWHEEL_X)

CH = TRAY_CHANNEL_W / 2              # 58
OUT = CH + TRAY_WALL_T               # 61
BACK_Y = (TRAY_REAR_Y, TRAY_STOP_Y - 5.0)     # back plate -222 .. -205
RIGHT_WALL_Y = (TRAY_REAR_Y, -207.0)          # right wall only behind the finger travel
LEAD_IN = 2.0
# KW11-3Z slot switch (P10 drawing: 19.7 x 10.6 x 6.6, M2 holes 9.5 apart): lies flat (thickness along z), long
# side along x, lever edge toward +y. Kept in the middle of the stop, clear of the caddy's tag (left) and QR (right).
SW_X = -6.0                                   # body centre x
SW_DZ = 15.0                                  # body mid-plane above the slot floor (caddy handle mid-height)
SW_FRONT_Y = TRAY_STOP_Y - 0.5               # lever edge of the body: the free lever (7.1 high) reaches 6.6 past the
                                              # stop face, 2.6 past a pulled caddy's handle at y -196 (spec: >= 4)
SW_BODY = (KW11["l"], KW11["h"], KW11["t"])
SW_FIT = 0.3                                  # per side
SW_HOLE_DX, SW_HOLE_UP = KW11["hole_dx"], KW11["hole_up"]
SW_HOLE_ADJ = 1.0                             # +/- slot in y for the hole position
SW_HEAD_D = 5.5                               # access hole for an M2 pan head (Ø3.8) + driver
WIRE_GROOVE = (4.0, 9.0, 4.0)                 # x0, x1, depth into the back face
AXLE_NUT_POCKET = (12.0, 9.0)                 # Ø, depth: M5 nylock + ~8 mm of M5 x 30 axle past the Z plate
CAM_BLOCK = (-93.5, -61.0, -128.0, -100.0)    # x0, x1, y0, y1
CAM_PCB_Y = CAM_LENS[1] - 1.0                 # front face of the camera PCB
CAM_FIT = 0.4                                 # per side around the PCB (slots print ~0.2-0.4 small, fit test 1)
CAM_LEDGE = 1.5                               # PCB edge strips that hold it front and back
CAM_WINDOW = (-98.0, -38.0, 8.0, 26.0)        # y0, y1, z0, z1 in the left wall (slot B level)
M5_INSERT_DEPTH = 12.0                        # heat-set insert pilot depth, from the back face


def _z_slot(d, x, y, z0, z1):
    """Vertical hole of diameter d, slotted +/- SW_HOLE_ADJ along y."""
    return (box(x - d / 2, x + d / 2, y - SW_HOLE_ADJ, y + SW_HOLE_ADJ, z0, z1)
            + cyl_z(d, x, y - SW_HOLE_ADJ, z0, z1) + cyl_z(d, x, y + SW_HOLE_ADJ, z0, z1))


def _y_hole(d, x, z, y0, y1):
    return bd.Pos(x, y0, z) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        d / 2, y1 - y0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


@step(out="../../STEP/robot/tray_stack.step")
@stl(out="../../STL/robot/tray_stack.stl")
def tray_stack():
    yf = TRAY_FRONT_Y
    part = box(-OUT, OUT, TRAY_REAR_Y, yf, -TRAY_FLOOR_T, 0.0)                       # slot B floor
    part += box(-OUT, OUT, TRAY_REAR_Y, yf, SLOT_A_DZ - TRAY_FLOOR_T, SLOT_A_DZ)     # slot A floor
    part += box(-OUT, -CH, TRAY_REAR_Y, yf, -TRAY_FLOOR_T, TRAY_TOP_DZ)              # left wall
    for z0 in (0.0, SLOT_A_DZ):
        part += box(CH, OUT, TRAY_REAR_Y, yf, z0, z0 + TRAY_RIGHT_LIP_H)             # right lips
    part += box(CH, OUT, *RIGHT_WALL_Y, -TRAY_FLOOR_T, TRAY_TOP_DZ)                  # right wall (rear)
    part += box(-OUT, OUT, *BACK_Y, ZPLATE_DZ[0], TRAY_TOP_DZ)                       # back plate
    for z0 in (0.0, SLOT_A_DZ):
        part += box(-CH, CH - 18.0, BACK_Y[1], TRAY_STOP_Y, z0, z0 + CADDY_H)        # handle stops
    # Lead-ins at the front: floor top edges and the left wall.
    for z in (0.0, SLOT_A_DZ):
        part -= prism_yz([(yf + 0.1, z + 0.1), (yf - 3.0, z + 0.1), (yf + 0.1, z - 3.0)], -OUT - 1, OUT + 1)
    part -= prism_xy_wedge(yf)
    # Slot-presence switch pockets (body in the back plate, lever through the stop).
    sl, sd, st = SW_BODY
    hx = sl / 2 + SW_FIT
    hy = SW_FRONT_Y - sd + SW_HOLE_UP                                   # screw axis y
    for z0, access_up in ((0.0, False), (SLOT_A_DZ, True)):
        zc = z0 + SW_DZ
        zl, zh = zc - st / 2 - SW_FIT, zc + st / 2 + SW_FIT
        part -= box(SW_X - hx, SW_X + hx, BACK_Y[0] - 0.1, SW_FRONT_Y, zl, zh)            # pocket, open at the back
        part -= box(SW_X - hx, SW_X + hx, SW_FRONT_Y - 0.1, TRAY_STOP_Y + 0.1, zc - 3.0, zc + 3.0)   # lever slot
        for dx in (-SW_HOLE_DX, SW_HOLE_DX):
            x = SW_X + dx
            if access_up:   # head from the top face, pilot below the pocket
                part -= _z_slot(SW_HEAD_D, x, hy, zh - 0.1, TRAY_TOP_DZ + 0.1)
                part -= _z_slot(M2_PILOT_D, x, hy, zl - 6.0, zl + 0.1)
            else:           # head from the bottom face, pilot above the pocket
                part -= _z_slot(SW_HEAD_D, x, hy, ZPLATE_DZ[0] - 0.1, zl + 0.1)
                part -= _z_slot(M2_PILOT_D, x, hy, zh - 0.1, zh + 6.0)
    gx0, gx1, gd = WIRE_GROOVE
    part -= box(gx0, gx1, BACK_Y[0] - 0.1, BACK_Y[0] + gd, ZPLATE_DZ[0] - 0.1,
                SLOT_A_DZ + SW_DZ + st / 2 + SW_FIT)                                   # wires down to the bottom edge
    # Lower Z-wheel axles end past the Z plate's front face: pockets for the nut and the bolt tail.
    nd, ndep = AXLE_NUT_POCKET
    for s in (-1, 1):
        part -= _y_hole(nd, s * ZWHEEL_X, ZWHEEL_DZ[0], BACK_Y[0] - 0.1, BACK_Y[0] + ndep)
    # Inserts for the Z carriage plate screws (pattern matches z_carriage.py).
    for x, z in TRAY_BOLTS:
        part -= _y_hole(M5_INSERT_D, x, z, BACK_Y[0] - 0.1, BACK_Y[0] + M5_INSERT_DEPTH)
    # Camera mount on the left wall, lens looking +y at slot B level.
    cx0, cx1, cy0, cy1 = CAM_BLOCK
    lx, ly = CAM_LENS
    # The PCB drops in from the top and rests on the slot floor, which puts the lens at CAM_DZ; edge strips hold it
    # front and back, the holder and lens look out through a front window, the connector sits in a rear pocket.
    cb = CAM_BOARD
    hw = cb["w"] / 2 + CAM_FIT                                   # slot half width
    zb = CAM_DZ - cb["lens_up"] - CAM_FIT                        # slot floor
    ztop = CAM_DZ + 15.1
    pf, pb = CAM_PCB_Y + CAM_FIT, CAM_PCB_Y - cb["t"] - CAM_FIT    # PCB slot front / back
    part += box(cx0, cx1, cy0, cy1, zb - 2.5, CAM_DZ + 15.0)
    part -= box(lx - hw, lx + hw, pb, pf, zb, ztop)                                          # PCB slot
    win = hw - CAM_LEDGE
    part -= box(lx - win, lx + win, pf - 0.1, CAM_PCB_Y + cb["holder_l"] + 0.8, zb, ztop)    # front window
    part -= box(lx - 8.0, cx1 + 0.1, pf - 0.1, cy1 + 0.1, CAM_DZ - 6.0, CAM_DZ + 6.0)        # lens fan (0..+50 deg)
    part -= box(lx - win, lx + win, pb - cb["back"] - 0.6, pb + 0.1, zb, ztop)              # connector pocket
    part -= box(lx - 9.0, lx + 9.0, cy0 - 0.1, pb - cb["back"] - 0.5, zb, ztop)             # ribbon exit (16 mm FFC)
    wy0, wy1, wz0, wz1 = CAM_WINDOW
    part -= box(-OUT - 0.1, -CH + 0.1, wy0, wy1, wz0, wz1)       # sight line to the caddy tag
    part.label = "tray_stack"
    return part


def prism_xy_wedge(yf):
    """45-degree lead-in on the inner front edge of the left wall (2 mm)."""
    from lib.prims import prism_xy
    return prism_xy([(-CH, yf - LEAD_IN), (-CH - LEAD_IN, yf + 0.1), (-CH, yf + 0.1)], -TRAY_FLOOR_T - 0.1,
                    TRAY_TOP_DZ + 0.1)


if __name__ == "__main__":
    tray_stack()
