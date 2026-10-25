"""Dummy 3.5" drive shell (PLA, x6), filled with ~520 g steel ballast in epoxy.

Spec: docs/spec/01-mechanical.md §3. Frame: drive front at y = 0, centered in x,
bottom at z = 0. Outer envelope is the 3.5" form factor (147 x 101.6 x 26.1).
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import HDD_H, HDD_HOLE_SPAN_X, HDD_HOLE_Y, HDD_L, HDD_W, M3_INSERT_D, M3_SELF_TAP_D
from lib.prims import box, cyl_z

WALL = 4.0
FLOOR = 2.0
LID_T = 2.0
LID_STEP = 1.0             # rebate the lid drops into, so the top stays flush
BOSS_D = 8.0
INSERT_DEPTH = 5.0

HALF_W = HDD_W / 2
LID_SCREWS = [(sx * (HALF_W - WALL - 3.0), y) for sx in (-1, 1) for y in (WALL + 6.0, HDD_L - WALL - 6.0)]


@step(out="../STEP/dummy_drive_shell.step")
@stl(out="../STL/dummy_drive_shell.stl")
def dummy_drive_shell():
    inner_x = HALF_W - WALL
    top_z = HDD_H - LID_T
    shell = box(-HALF_W, HALF_W, 0, HDD_L, 0, HDD_H)
    shell -= box(-inner_x, inner_x, WALL, HDD_L - WALL, FLOOR, HDD_H + 0.1)
    shell -= box(-inner_x - LID_STEP, inner_x + LID_STEP, WALL - LID_STEP, HDD_L - WALL + LID_STEP,
                 top_z, HDD_H + 0.1)

    # Lid screw bosses in the corners (heat-set inserts from the top).
    for x, y in LID_SCREWS:
        shell += cyl_z(BOSS_D, x, y, FLOOR, top_z)
        shell -= cyl_z(M3_INSERT_D, x, y, top_z - INSERT_DEPTH, top_z + 0.1)

    # Bottom mounting holes in the side walls: the standard hole line is only 3.2 mm from the outer face, too
    # close for a heat-set insert, so these are pilots for M3 self-tapping screws (1.9 mm wall).
    for x in (-HDD_HOLE_SPAN_X / 2, HDD_HOLE_SPAN_X / 2):
        for y in HDD_HOLE_Y:
            shell += cyl_z(BOSS_D, x, y, 0, INSERT_DEPTH + 3.0)
            shell -= cyl_z(M3_SELF_TAP_D, x, y, -0.1, INSERT_DEPTH + 1.0)

    # Bosses near the walls can poke outside the envelope: trim back to it.
    shell &= box(-HALF_W, HALF_W, 0, HDD_L, 0, HDD_H)
    shell.label = "dummy_drive_shell"
    return shell


if __name__ == "__main__":
    dummy_drive_shell()
