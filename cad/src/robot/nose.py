"""Robot nose / bumper (PETG). Fits the dock funnel throat (200 wide), carries the two copper
charging pads (x = +/-40, z = 60) and the robot's dock-detect switch (lever at x = 20).
Bolts to the front 2020 cross member (y -110..-90). Robot frame, docked pose (see lib/robot_dims.py).
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import DOCK_STOP_Y, KW11, M2_PILOT_D, M3_CLEAR, M5_CLEAR
from lib.prims import box, cyl_x, cyl_z
from lib.robot_dims import (BASE_FRONT_Y, CASTER, CASTER_FRONT, CONTACT_X, CONTACT_Z, NOSE_HALF_W,
                            NOSE_SWITCH_X, NOSE_Z, RAIL_Z)

WALL = 4.0
PAD = (30.0, 20.0, 1.0)            # copper pad recess: width, height, depth
SWITCH_SLOT = (8.0, 22.0)          # lever slot width, height (centre z = 52): covers the whole lever
SWITCH_Z = 52.0
SWITCH_REACH = 3.0                 # free lever tip past the nose tip: pressed 3 mm when docked (triggers at 2)
SWITCH_ADJUST = 2.0                # +/- slot in y to tune the actuation point


def _y_hole(d, x, z, y0, y1):
    return bd.Pos(x, y0, z) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        d / 2, y1 - y0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


@step(out="../../STEP/robot/nose.step")
@stl(out="../../STL/robot/nose.stl")
def nose():
    y0, y1 = BASE_FRONT_Y, DOCK_STOP_Y
    z0, z1 = NOSE_Z
    part = box(-NOSE_HALF_W, NOSE_HALF_W, y0, y1, z0, z1)
    part -= box(-NOSE_HALF_W + WALL, NOSE_HALF_W - WALL, y0 + WALL, y1 - WALL, z0 + WALL, z1 + 0.1)  # open top
    # Front corners rounded off as a lead-in for the funnel.
    for s in (-1, 1):
        part -= bd.Pos(s * NOSE_HALF_W, y1, (z0 + z1) / 2) * bd.Rot(0, 0, 45) * bd.Box(8, 8, z1 - z0 + 1)
    w, h, d = PAD
    for x in (-CONTACT_X, CONTACT_X):
        part -= box(x - w / 2, x + w / 2, y1 - d, y1 + 0.1, CONTACT_Z - h / 2, CONTACT_Z + h / 2)
        part -= _y_hole(M3_CLEAR, x, CONTACT_Z, y1 - WALL - 0.1, y1 + 0.1)        # pad screw / wire
    sw, sh = SWITCH_SLOT
    part -= box(NOSE_SWITCH_X - sw / 2, NOSE_SWITCH_X + sw / 2, y1 - WALL - 0.1, y1 + 0.1,
                SWITCH_Z - sh / 2, SWITCH_Z + sh / 2)
    # Switch bracket inside, beside the slot (M2 self-tapping, slotted +/-2 mm in y).
    bx = NOSE_SWITCH_X + sw / 2
    part += box(bx, bx + 3.0, y1 - 22.0, y1 - WALL, z0 + WALL, z0 + 45.0)
    # Body (thickness along x) against the bracket's -x face, long side along z centred on the slot, lever edge
    # toward +y; M2 self-tapping screws from -x through the switch into the bracket.
    hy = y1 + SWITCH_REACH - KW11["lever"] - KW11["h"] + KW11["hole_up"]
    for dz in (-KW11["hole_dx"], KW11["hole_dx"]):
        z = SWITCH_Z + dz
        y0s, y1s = hy - SWITCH_ADJUST, hy + SWITCH_ADJUST
        part -= cyl_x(M2_PILOT_D, bx - 0.1, bx + 3.1, y0s, z) + cyl_x(M2_PILOT_D, bx - 0.1, bx + 3.1, y1s, z)
        part -= box(bx - 0.1, bx + 3.1, y0s, y1s, z - M2_PILOT_D / 2, z + M2_PILOT_D / 2)
    # Rear wall bolts to the front cross member (M5 + T-nut), centre of the 2020 at z = 52.
    zc = (RAIL_Z[0] + RAIL_Z[1]) / 2
    for x in (-40.0, 40.0):
        part -= _y_hole(M5_CLEAR, x, zc, y0 - 0.1, y0 + WALL + 0.1)
    # Anti-tip caster: the bought caster (40 mm hole pitch, slotted +/-2) hangs under the floor on caster_spacer_front;
    # M3 nuts inside the nose. The boss keeps the 19 mm pattern of the original small caster as a fallback.
    cx, cy = CASTER_FRONT
    part += cyl_z(30.0, cx, cy, z0, z0 + 6.0)
    for dx in (-9.5, 9.5):
        part -= cyl_z(M3_CLEAR, cx + dx, cy, z0 - 0.1, z0 + 6.1)
    p, a = CASTER["pitch"] / 2, CASTER["pitch_adj"]
    for s in (-1, 1):
        x0, x1 = sorted((cx + s * (p - a), cx + s * (p + a)))
        part -= box(x0, x1, cy - M3_CLEAR / 2, cy + M3_CLEAR / 2, z0 - 0.1, z0 + WALL + 0.1)
        part -= cyl_z(M3_CLEAR, x0, cy, z0 - 0.1, z0 + WALL + 0.1) + cyl_z(M3_CLEAR, x1, cy, z0 - 0.1, z0 + WALL + 0.1)
    part.label = "nose"
    return part


if __name__ == "__main__":
    nose()
