"""Battery box (PETG): holds the 4S1P 18650 pack + BMS low at the rear (counterweight).
Open top with a strap slot; the pack lifts out for the airport (carry-on, <100 Wh)."""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M3_CLEAR
from lib.prims import box, cyl_z
from lib.robot_dims import BATTERY, BATTERY_DECK_HOLES

WALL = 2.5
TAB = (10.0, (-368.0, -345.0), 4.0)    # +x screw tab: width, y span, thickness
# The Pi's HDMI and audio jacks overhang its board 2 mm toward the box: front wall thinned to 1 mm there (0.5 mm gap).
PI_RELIEF = (-99.0, -64.0, 1.5, 22.0)    # x0, x1, depth into the wall, height above the deck


@step(out="../../STEP/robot/battery_box.step")
@stl(out="../../STL/robot/battery_box.stl")
def battery_box():
    x0, x1, y0, y1, z0, z1 = BATTERY
    part = box(x0 - WALL, x1 + WALL, y0 - WALL, y1 + WALL, z0, z1)
    part -= box(x0, x1, y0, y1, z0 + WALL, z1 + 0.1)
    part -= box(x0 + 10, x1 - 10, y0 - WALL - 0.1, y1 + WALL + 0.1, z1 - 12, z1 - 4)   # strap slot
    part -= box(x1 - 0.1, x1 + WALL + 0.1, y0 + 12, y0 + 28, z0 + WALL, z0 + 20)       # XT60 lead exit
    part += box(x1 + WALL - 0.1, x1 + WALL + TAB[0], *TAB[1], z0, z0 + TAB[2])
    rx0, rx1, rd, rh = PI_RELIEF
    part -= box(rx0, rx1, y1 + WALL - rd, y1 + WALL + 0.1, z0 - 0.1, z0 + rh)
    for x, y in BATTERY_DECK_HOLES:
        part -= cyl_z(M3_CLEAR, x, y, z0 - 0.1, z0 + TAB[2] + 0.1)               # to the deck (M3 + nut)
    part.label = "battery_box"
    return part


if __name__ == "__main__":
    battery_box()
