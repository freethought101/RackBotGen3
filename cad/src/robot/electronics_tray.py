"""Electronics tray (PETG): standoffs for the 100 x 100 motion board (M3 at 93 x 93) on the deck."""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M3_CLEAR, M3_INSERT_D
from lib.prims import box, cyl_z
from lib.robot_dims import DECK_Z, PCB_XY, PCB_Z

T = 3.0
MARGIN = 4.0
HOLE_INSET = 3.5


@step(out="../../STEP/robot/electronics_tray.step")
@stl(out="../../STL/robot/electronics_tray.stl")
def electronics_tray():
    x, y = PCB_XY
    z0 = DECK_Z[1]
    part = box(x - MARGIN, x + 100 + MARGIN, y - MARGIN, y + 100 + MARGIN, z0, z0 + T)
    part -= box(x + 15, x + 85, y + 15, y + 85, z0 - 0.1, z0 + T + 0.1)          # wiring window
    for hx in (x + HOLE_INSET, x + 100 - HOLE_INSET):
        for hy in (y + HOLE_INSET, y + 100 - HOLE_INSET):
            part += cyl_z(9.0, hx, hy, z0, PCB_Z)           # 2.5 mm wall around the insert
            part -= cyl_z(M3_INSERT_D, hx, hy, PCB_Z - 5.0, PCB_Z + 0.1)
    for hx in (x - MARGIN + 6, x + 100 + MARGIN - 6):
        part -= cyl_z(M3_CLEAR, hx, y + 50, z0 - 0.1, z0 + T + 0.1)               # to the deck
    part.label = "electronics_tray"
    return part


if __name__ == "__main__":
    electronics_tray()
