"""Battery box (PETG): holds the 4S1P 18650 pack + BMS low at the rear (counterweight).
Open top with a strap slot; the pack lifts out for the airport (carry-on, <100 Wh)."""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M3_CLEAR
from lib.prims import box, cyl_z
from lib.robot_dims import BATTERY

WALL = 2.5


@step(out="../../STEP/robot/battery_box.step")
@stl(out="../../STL/robot/battery_box.stl")
def battery_box():
    x0, x1, y0, y1, z0, z1 = BATTERY
    part = box(x0 - WALL, x1 + WALL, y0 - WALL, y1 + WALL, z0, z1)
    part -= box(x0, x1, y0, y1, z0 + WALL, z1 + 0.1)
    part -= box(x0 + 10, x1 - 10, y0 - WALL - 0.1, y1 + WALL + 0.1, z1 - 12, z1 - 4)   # strap slot
    part -= box(x1 - 0.1, x1 + WALL + 0.1, y0 + 12, y0 + 28, z0 + WALL, z0 + 20)       # XT60 lead exit
    for x in (x0 + 10, x1 - 10):
        part -= cyl_z(M3_CLEAR, x, (y0 + y1) / 2, z0 - 0.1, z0 + WALL + 0.1)
    part.label = "battery_box"
    return part


if __name__ == "__main__":
    battery_box()
