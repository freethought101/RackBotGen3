"""Raspberry Pi 3 tray (PETG): standoffs on the 58 x 49 mm hole pattern, board long side along x.

Orientation (the real board, docs/3d-models/P12_raspberry-pi-3b.step): USB/Ethernet end at +x, SD card end at -x,
GPIO header edge facing +y (Z motor), micro-USB / HDMI / audio edge facing -y against the battery box. A Pi 3 can't
have that edge at +y with USB at +x (it would be a mirror image), and turned round its plugs would hit the Z motor. So
the micro-USB is not used: the Pi is powered through GPIO pins 2/4 (5 V) and 6 (GND) from the 5 V buck; the HDMI and
audio jacks sit in a relief in the battery box wall.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M25_PILOT_D, M3_CLEAR
from lib.prims import box, cyl_z
from lib.robot_dims import DECK_Z, PI_DECK_HOLES, PI_XY, PCB_Z

PI_W, PI_L = 85.0, 56.0          # board along x, y
HOLES_X, HOLES_Y = 58.0, 49.0
T = 3.0
M25_PILOT = M25_PILOT_D


@step(out="../../STEP/robot/pi_tray.step")
@stl(out="../../STL/robot/pi_tray.stl")
def pi_tray():
    x, y = PI_XY
    z0 = DECK_Z[1]
    part = box(x - 3, x + PI_W + 3, y - 0.5, y + PI_L + 0.5, z0, z0 + T)     # tight in y: battery box behind, Z motor ahead
    part -= box(x + 12, x + PI_W - 20, y + 10, y + PI_L - 10, z0 - 0.1, z0 + T + 0.1)
    for hx in (x + 3.5, x + 3.5 + HOLES_X):
        for hy in (y + 3.5, y + 3.5 + HOLES_Y):
            part += cyl_z(6.0, hx, hy, z0, PCB_Z)
            part -= cyl_z(M25_PILOT, hx, hy, PCB_Z - 6.0, PCB_Z + 0.1)
    for hx, hy in PI_DECK_HOLES:
        part -= cyl_z(M3_CLEAR, hx, hy, z0 - 0.1, z0 + T + 0.1)                   # to the deck
    part.label = "pi_tray"
    return part


if __name__ == "__main__":
    pi_tray()
