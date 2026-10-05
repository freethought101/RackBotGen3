"""Lid for the dummy 3.5" drive shell (PLA, x6). Same frame as the shell, in its closed position."""

from cadgen import build123d as bd
from cadgen import step, stl

from dummy_drive_shell import HALF_W, LID_SCREWS, LID_STEP, LID_T, WALL
from lib.dims import HDD_H, HDD_L, M3_CLEAR
from lib.prims import box, cyl_z

FIT_GAP = 0.2              # per side, lid to rebate
CBORE_D = 6.0
CBORE_DEPTH = 1.0
LABEL_RECESS = 0.4


@step(out="../STEP/dummy_drive_lid.step")
@stl(out="../STL/dummy_drive_lid.stl")
def dummy_drive_lid():
    x = HALF_W - WALL + LID_STEP - FIT_GAP
    y0, y1 = WALL - LID_STEP + FIT_GAP, HDD_L - WALL + LID_STEP - FIT_GAP
    z0 = HDD_H - LID_T
    lid = box(-x, x, y0, y1, z0, HDD_H)
    for sx, sy in LID_SCREWS:
        lid -= cyl_z(M3_CLEAR, sx, sy, z0 - 0.1, HDD_H + 0.1)
        lid -= cyl_z(CBORE_D, sx, sy, HDD_H - CBORE_DEPTH, HDD_H + 0.1)
    # Recess for a printed "dummy drive" label.
    lid -= box(-35, 35, 25, HDD_L - 25, HDD_H - LABEL_RECESS, HDD_H + 0.1)
    lid.label = "dummy_drive_lid"
    return lid


if __name__ == "__main__":
    dummy_drive_lid()
