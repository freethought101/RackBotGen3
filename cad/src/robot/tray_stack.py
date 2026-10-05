"""Tray stack (PETG, one print ~122 x 197 x 104), modeled at Z = 0.

Two caddy slots stacked at the bay pitch: slot B floor at z = Z, slot A floor at z = Z + 45.
Left wall full height; right side open above a 6 mm lip so the extractor fingers can reach the
caddy notch. Rear stops hold the caddy handle 5 mm short of the back plate; KW11-3Z slot-presence
switches sit in pockets behind the stops. The camera mount is on the left wall.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import CADDY_H, M5_CLEAR
from lib.prims import box, prism_yz
from lib.robot_dims import (CAM_DZ, CAM_LENS, SLOT_A_DZ, TRAY_CHANNEL_W, TRAY_FLOOR_T, TRAY_FRONT_Y,
                            TRAY_REAR_Y, TRAY_RIGHT_LIP_H, TRAY_STOP_Y, TRAY_TOP_DZ, TRAY_WALL_T, TRAY_BOLTS, ZPLATE_DZ)

CH = TRAY_CHANNEL_W / 2              # 58
OUT = CH + TRAY_WALL_T               # 61
BACK_Y = (TRAY_REAR_Y, TRAY_STOP_Y - 5.0)     # back plate -222 .. -205
RIGHT_WALL_Y = (TRAY_REAR_Y, -207.0)          # right wall only behind the finger travel
LEAD_IN = 2.0
SWITCH_POCKET = (-12.0, 2.0)                  # x span of the KW11 pocket in the back plate
SWITCH_SLOT = (-10.0, -2.0)
CAM_BLOCK = (-92.0, -61.0, -128.0, -100.0)    # x0, x1, y0, y1
CAM_WINDOW = (-98.0, -38.0, 8.0, 26.0)        # y0, y1, z0, z1 in the left wall (slot B level)


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
    for z0 in (0.0, SLOT_A_DZ):
        part -= box(*SWITCH_POCKET, BACK_Y[0] + 3.0, BACK_Y[1] + 0.1, z0 + 2.0, z0 + 28.0)
        part -= box(*SWITCH_SLOT, BACK_Y[1] - 0.1, TRAY_STOP_Y + 0.1, z0 + 8.0, z0 + 22.0)
    # Bolts to the Z carriage plate (pattern matches z_carriage.py).
    for x, z in TRAY_BOLTS:
        part -= _y_hole(M5_CLEAR, x, z, BACK_Y[0] - 0.1, BACK_Y[1] + 0.1)
    # Camera mount on the left wall, lens looking +y at slot B level.
    cx0, cx1, cy0, cy1 = CAM_BLOCK
    lx, ly = CAM_LENS
    part += box(cx0, cx1, cy0, cy1, CAM_DZ - 15.0, CAM_DZ + 15.0)
    part -= box(lx - 12.5, lx + 12.5, ly - 4.0, ly - 1.0, CAM_DZ - 12.0, CAM_DZ + 13.0)    # board slot
    part -= box(lx - 12.5, lx + 12.5, ly - 4.0, ly - 1.0, CAM_DZ + 12.0, CAM_DZ + 15.1)    # insert from top
    part -= box(lx - 8.0, cx1 + 0.1, ly - 1.1, cy1 + 0.1, CAM_DZ - 6.0, CAM_DZ + 6.0)        # lens fan (0..+50 deg)
    part -= box(lx - 6.0, lx + 6.0, cy0 - 0.1, ly - 4.0, CAM_DZ - 3.0, CAM_DZ + 3.0)        # ribbon exit
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
