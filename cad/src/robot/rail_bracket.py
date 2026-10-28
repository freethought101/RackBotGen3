"""Y-rail bracket (PETG), modeled at Z = 0.

A back plate behind the Z carriage plate is clamped by the x = 50 column of tray screws (3 x M5, 80 mm
apart), so the extractor's weight and the pull/push loads go straight into the tray/Z-plate sandwich.
A 16 x 20 strip runs back along the rail's inner face (2 x M5 into the rail's inner slot) to a horizontal
plate behind the rail end that carries the Y stepper (shaft down). Everything sits behind y = -228.5, out
of the carriage arm's travel; above z_step the back plate stops short of the carriage frame.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import KW11, KW11_PRESS, M2_PILOT_D, M3_CLEAR, M5_CLEAR, M5_HEAD_CBORE
from lib.prims import box, cyl_x, cyl_z
from lib.robot_dims import (BELT_X, PULLEY_Y, RAIL_BRACKET_BOLT_X, TRAY_BOLTS, YBRACKET_DZ, YBRACKET_PLATE,
                            YBRACKET_PLATE_Y, YBRACKET_X, YBRACKET_Y, YCARRIAGE_DY, YFRAME_DZ, YMOTOR_PLATE_DZ,
                            Y_NOTCH_HOME, YRAIL_DZ, YRAIL_Y)

NEMA_PITCH, BOSS_D = 31.0, 23.0   # boss Ø22: same 0.5 mm clearance as the drive bracket and Z-motor mount
# Y home switch (KW11-3Z) lies flat on a post on the strip behind the carriage, lever pointing +y. The carriage frame's
# rear face (y = Y_NOTCH_HOME + YCARRIAGE_DY[0] + Y, z YFRAME_DZ) presses it; it triggers at Y = 0. Screws from the
# top; the holes are slotted +/-1.5 in y to set the trigger point.
YSW_X1 = YBRACKET_X[1]                    # body's +x end (lever free end, under the frame)
YSW_ADJ = 1.5
YSW_POST_MARGIN = 1.5                     # post overhangs the switch body's -x end (the body is longer than the strip)
MOTOR_PLATE_X1 = BELT_X + 19.0            # motor overhangs 2 mm: wider breaks the 230 mm bag limit (mast unit)
STRIP_CBORE = (M5_HEAD_CBORE, 6.0)                 # M5 head counterbore from the strip's inner face: 10 mm left for M5 x 16 + T-nut


def _y_hole(d, x, z, y0, y1):
    return bd.Pos(x, y0, z) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        d / 2, y1 - y0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


@step(out="../../STEP/robot/rail_bracket.step")
@stl(out="../../STL/robot/rail_bracket.stl")
def rail_bracket():
    part = box(*YBRACKET_X, *YBRACKET_Y, *YBRACKET_DZ)                             # strip beside the rail
    zc = (YRAIL_DZ[0] + YRAIL_DZ[1]) / 2
    for y in (YRAIL_Y[0] + 12.0, YRAIL_Y[0] + 45.0):
        part -= cyl_x(M5_CLEAR, YBRACKET_X[0] - 0.1, YBRACKET_X[1] + 0.1, y, zc)    # into the rail inner slot
        part -= cyl_x(STRIP_CBORE[0], YBRACKET_X[0] - 0.1, YBRACKET_X[0] + STRIP_CBORE[1], y, zc)
    # Back plate (L-shaped: full width below z_step, narrower above it).
    bx0, bx1_hi, bx1_lo, z_step, bz0, bz1 = YBRACKET_PLATE
    py0, py1 = YBRACKET_PLATE_Y
    part += box(bx0, bx1_lo, py0, py1, bz0, z_step)
    part += box(bx0, bx1_hi, py0, py1, z_step, bz1)
    for x, z in TRAY_BOLTS:
        if x == RAIL_BRACKET_BOLT_X:
            part -= _y_hole(M5_CLEAR, x, z, py0 - 0.1, py1 + 0.1)
    # Horizontal Y-motor plate behind the rail end: motor body on top, shaft down through the plate to the
    # 20T pulley in the belt plane.
    pz0, pz1 = YMOTOR_PLATE_DZ
    part += box(YBRACKET_X[0], MOTOR_PLATE_X1, YBRACKET_Y[0], PULLEY_Y + 23.0, pz0, pz1)
    part += box(*YBRACKET_X, YBRACKET_Y[0], PULLEY_Y + 23.0, YBRACKET_DZ[0], pz1)          # web to the strip
    part -= cyl_z(BOSS_D, BELT_X, PULLEY_Y, pz0 - 0.1, pz1 + 0.1)                             # motor boss / shaft
    for dx in (-NEMA_PITCH / 2, NEMA_PITCH / 2):
        for dy in (-NEMA_PITCH / 2, NEMA_PITCH / 2):
            part -= cyl_z(M3_CLEAR, BELT_X + dx, PULLEY_Y + dy, pz0 - 0.1, pz1 + 0.1)
    # Y home switch post.
    st, sh = KW11["t"], KW11["h"]
    frame_rear = Y_NOTCH_HOME + YCARRIAGE_DY[0]                     # at Y = 0
    front = frame_rear + KW11_PRESS - KW11["lever"]                  # body's lever edge
    back = front - sh
    zt = YFRAME_DZ[1]                                                # body top flush with the frame top
    zb = zt - st
    xb0 = YSW_X1 - KW11["l"]
    part += box(xb0 - YSW_POST_MARGIN, YBRACKET_X[1], back, front, YBRACKET_DZ[1] - 0.1, zb)
    xc, yh = (xb0 + YSW_X1) / 2, back + KW11["hole_up"]
    for dx in (-KW11["hole_dx"], KW11["hole_dx"]):
        part -= box(xc + dx - M2_PILOT_D / 2, xc + dx + M2_PILOT_D / 2, yh - YSW_ADJ, yh + YSW_ADJ, zb - 8.0, zb + 0.1)
        for dy in (-YSW_ADJ, YSW_ADJ):
            part -= cyl_z(M2_PILOT_D, xc + dx, yh + dy, zb - 8.0, zb + 0.1)
    part.label = "rail_bracket"
    return part


if __name__ == "__main__":
    rail_bracket()
