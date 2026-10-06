"""Z-motor mount (PETG): a plate on the NEMA17's shaft face (4 x M3 into the motor) on two side walls
that stand on the deck (M3 + nut through the deck at the feet). The motor body rests on the deck; the
plate fixes it in x, y and yaw and stops it lifting. The coupler starts 5 mm above the plate.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M3_CLEAR
from lib.prims import box, cyl_z
from lib.robot_dims import DECK_Z, SCREW_XY, ZMOTOR_Z, ZMOUNT_T

NEMA_HALF, NEMA_PITCH, BOSS_D = 21.15, 31.0, 23.0
WALL_T = 3.0                   # +x wall stays 0.35 mm off the mast collar socket
PLATE_DY = (-21.65, 18.6)     # relative to the screw axis; front edge 2 mm behind the Z wheels at the lowest lift
WALL_DY = (-21.65, 18.0)
FOOT = (8.0, (-20.0, -12.0), 4.0)   # foot length (outward in x), y span relative to the axis, thickness


@step(out="../../STEP/robot/z_motor_mount.step")
@stl(out="../../STL/robot/z_motor_mount.stl")
def z_motor_mount():
    sx, sy = SCREW_XY
    z0, zp = DECK_Z[1], ZMOTOR_Z[1]
    xl, xr = sx - NEMA_HALF - 0.5, sx + NEMA_HALF + 0.5          # motor sides + 0.5 clearance
    part = box(xl - WALL_T, xr + WALL_T, sy + PLATE_DY[0], sy + PLATE_DY[1], zp, zp + ZMOUNT_T)
    fy0, fy1 = sy + FOOT[1][0], sy + FOOT[1][1]
    for wx0, wx1, fx0, fx1 in ((xl - WALL_T, xl, xl - WALL_T - FOOT[0], xl - WALL_T),
                               (xr, xr + WALL_T, xr + WALL_T, xr + WALL_T + FOOT[0])):
        part += box(wx0, wx1, sy + WALL_DY[0], sy + WALL_DY[1], z0, zp)
        part += box(fx0, fx1, fy0, fy1, z0, z0 + FOOT[2])
        part -= cyl_z(M3_CLEAR, (fx0 + fx1) / 2, (fy0 + fy1) / 2, z0 - 0.1, z0 + FOOT[2] + 0.1)
    part -= cyl_z(BOSS_D, sx, sy, zp - 0.1, zp + ZMOUNT_T + 0.1)
    for dx in (-NEMA_PITCH / 2, NEMA_PITCH / 2):
        for dy in (-NEMA_PITCH / 2, NEMA_PITCH / 2):
            part -= cyl_z(M3_CLEAR, sx + dx, sy + dy, zp - 0.1, zp + ZMOUNT_T + 0.1)
    part.label = "z_motor_mount"
    return part


if __name__ == "__main__":
    z_motor_mount()
