"""Drive motor bracket, right side (PETG; print one as modeled and one mirrored for the left).

The NEMA17 bolts to the outer plate (shaft through it to the wheel hub, direct drive); two webs
reach inward to the side rail's outer face (M5 + T-nut; the head goes in through the bore from the plate
side before the wheel is fitted). The deck screws down into M3 x 4 heat-set inserts in the web tops, beside
the motor.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M3_CLEAR, M3_INSERT_D, M5_CLEAR
from lib.prims import box, cyl_x, cyl_z
from lib.robot_dims import AXLE_Y, AXLE_Z, DRIVE_INSERT_X, DRIVE_INSERT_Y, DRIVE_PLATE_X, RAIL_X, RAIL_Z

Y_SPAN = (AXLE_Y - 32.0, AXLE_Y + 32.0)      # webs sit just beyond the 42.3 motor (0.85 mm)
WEB_T = 10.0
INSERT_DEPTH = 4.5                           # M3 x 4 insert; 0.5 mm above the head-access bore
PLATE_Z0 = 14.0
NEMA_PITCH = 31.0
BOSS_D = 23.0


@step(out="../../STEP/robot/drive_bracket.step")
@stl(out="../../STL/robot/drive_bracket.stl")
def drive_bracket():
    x0, x1 = DRIVE_PLATE_X
    ytop = RAIL_Z[1]
    part = box(x0, x1, *Y_SPAN, PLATE_Z0, ytop)
    for y0, y1 in ((Y_SPAN[0], Y_SPAN[0] + WEB_T), (Y_SPAN[1] - WEB_T, Y_SPAN[1])):
        part += box(RAIL_X[1], x0, y0, y1, RAIL_Z[0], ytop)                      # webs to the rail
        part -= cyl_x(M5_CLEAR, RAIL_X[1] - 0.1, RAIL_X[1] + 4.0, (y0 + y1) / 2, (RAIL_Z[0] + RAIL_Z[1]) / 2)
        part -= cyl_x(10.5, RAIL_X[1] + 4.0, x1 + 0.1, (y0 + y1) / 2, (RAIL_Z[0] + RAIL_Z[1]) / 2)  # head access
    part -= cyl_x(BOSS_D, x0 - 0.1, x1 + 0.1, AXLE_Y, AXLE_Z)
    for dy in (-NEMA_PITCH / 2, NEMA_PITCH / 2):
        for dz in (-NEMA_PITCH / 2, NEMA_PITCH / 2):
            part -= cyl_x(M3_CLEAR, x0 - 0.1, x1 + 0.1, AXLE_Y + dy, AXLE_Z + dz)
    for y in DRIVE_INSERT_Y:
        part -= cyl_z(M3_INSERT_D, DRIVE_INSERT_X, y, ytop - INSERT_DEPTH, ytop + 0.1)
    part.label = "drive_bracket"
    return part


if __name__ == "__main__":
    drive_bracket()
