"""Extractor finger (PETG or nylon, x2), modeled at its pivot: parked pose pointing +z.

Screws to the MG90S horn. Engaged = rotated -90 deg about +y so the tip points -x into the
caddy's side notch; one finger both pulls and pushes the caddy and holds it on the tray.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.prims import box
from lib.robot_dims import FINGER_LEN, FINGER_T, FINGER_W

HUB_D = 10.0
HORN_SCREW_D = 2.2


@step(out="../../STEP/robot/finger.step")
@stl(out="../../STL/robot/finger.stl")
def finger():
    t = FINGER_T / 2
    hub = bd.Pos(0, -t, 0) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        HUB_D / 2, FINGER_T, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    tip_c = FINGER_LEN - FINGER_W / 2            # rounded tip ends exactly FINGER_LEN from the pivot
    bar = box(-FINGER_W / 2, FINGER_W / 2, -t, t, 0.0, tip_c)
    tip = bd.Pos(0, 0, tip_c) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        FINGER_W / 2, FINGER_T, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER))
    part = hub + bar + tip
    part -= bd.Pos(0, -t - 0.1, 0) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        HORN_SCREW_D / 2, FINGER_T + 0.2, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    part = part.solids()[0] if len(part.solids()) == 1 else part
    part.label = "finger"
    return part


if __name__ == "__main__":
    finger()
