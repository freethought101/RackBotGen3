"""Dock block (PETG, x2: rack + spare station). Spec: docs/spec/01-mechanical.md §4-5.

Both copies are identical; only the spare-station copy (the robot's home) gets the charging contacts and
the dock-detect switch.

Bolts to the front face of the station's front base cross member (2020, y = 10..30).
The robot nose (200 W, z 30..100) is centred by a short V-funnel and stops against
the stop face at y = DOCK_STOP_Y; the robot tray then overhangs the nose to y = -25.

Frame: station frame — x = 0 on the bay centerline, y = 0 at the rack face, z = 0 on the table.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import DOCK_STOP_Y, M2_PILOT_D, M3_CLEAR, M5_CLEAR, NOSE_W
from lib.prims import box, cyl_x, prism_xy

THROAT = NOSE_W + 2.0          # 202
CAPTURE = 40.0                 # lateral capture per side at the funnel mouth
FUNNEL_L = 55.0                # shorter than the 60 mm nose so the robot body never enters
THROAT_L = 10.0                # parallel section before the stop: holds the nose to +/-1 mm
WALL_T = 8.0
WALL_H = 40.0
FLOOR_T = 3.0
HALF_W = 145.0
STOP_T = 10.0
STOP_H = 90.0                  # below the tray (tray underside >= 100 at the lowest Z)
STOP_HALF_W = 110.0
FRAME_FACE_Y = 10.0            # front face of the base cross member
FLANGE_T = 8.0
FLANGE_H = 20.0
BOLT_X = (-40.0, 40.0)
BOLT_Z = 10.0
RIB_X = (-100.0, -60.0, 60.0, 100.0)
RIB_T = 6.0
RIB_H = 40.0

# Charging contacts (spare station only): brass leaf springs screwed into recesses on the stop face.
CONTACT_X = (-40.0, 40.0)      # GND left, +24 V right (seen from the robot)
CONTACT_Z = 60.0
CONTACT_RECESS = (12.0, 30.0, 3.0)   # width, height, depth
CONTACT_SCREW_DZ = 8.0

# Dock-detect KW11-3Z: same mounting scheme as the bay shelf.
SWITCH_SLOT = (-4.0, 4.0, 70.0, 85.0)  # x0, x1, z0, z1
BRACKET_X = (4.0, 7.0)
SWITCH_HOLE_D = M2_PILOT_D
SWITCH_HOLE_Z = (69.75, 79.25)
SWITCH_ADJUST = 2.0


@step(out="../STEP/dock_block.step")
@stl(out="../STL/dock_block.stl")
def dock_block():
    y_stop = DOCK_STOP_Y
    y_mouth = y_stop - FUNNEL_L
    y_back = y_stop + STOP_T
    flange_y0 = FRAME_FACE_Y - FLANGE_T

    part = box(-HALF_W, HALF_W, y_mouth, FRAME_FACE_Y, 0, FLOOR_T)
    part += box(-STOP_HALF_W, STOP_HALF_W, y_stop, y_back, 0, STOP_H)
    part += box(-STOP_HALF_W, STOP_HALF_W, flange_y0, FRAME_FACE_Y, 0, FLANGE_H)
    for x in RIB_X:
        part += box(x - RIB_T / 2, x + RIB_T / 2, y_back, flange_y0, 0, RIB_H)
    for s in (-1, 1):
        t, m = THROAT / 2, THROAT / 2 + CAPTURE
        yt = y_stop - THROAT_L
        part += prism_xy([(s * t, y_stop), (s * t, yt), (s * m, y_mouth), (s * (m + WALL_T), y_mouth),
                          (s * (t + WALL_T), yt), (s * (t + WALL_T), y_stop)], 0, WALL_H)
    part += box(*BRACKET_X, y_back, y_back + 14.0, 55.0, STOP_H)

    cuts = []
    for x in BOLT_X:
        cuts.append(bd.Pos(x, flange_y0 - 0.1, BOLT_Z) * bd.Rot(-90, 0, 0) *
                    bd.Cylinder(M5_CLEAR / 2, FLANGE_T + 0.2, align=(bd.Align.CENTER,) * 2 + (bd.Align.MIN,)))
    w, h, d = CONTACT_RECESS
    for x in CONTACT_X:
        cuts.append(box(x - w / 2, x + w / 2, y_stop - 0.1, y_stop + d, CONTACT_Z - h / 2, CONTACT_Z + h / 2))
        for dz in (-CONTACT_SCREW_DZ, CONTACT_SCREW_DZ):
            cuts.append(bd.Pos(x, y_stop - 0.1, CONTACT_Z + dz) * bd.Rot(-90, 0, 0) *
                        bd.Cylinder(M3_CLEAR / 2, STOP_T + 0.2, align=(bd.Align.CENTER,) * 2 + (bd.Align.MIN,)))
    sx0, sx1, sz0, sz1 = SWITCH_SLOT
    cuts.append(box(sx0, sx1, y_stop - 0.1, y_back + 0.1, sz0, sz1))
    hole_y = y_back + 7.0
    for z in SWITCH_HOLE_Z:
        for y in (hole_y - SWITCH_ADJUST, hole_y + SWITCH_ADJUST):
            cuts.append(cyl_x(SWITCH_HOLE_D, BRACKET_X[0] - 0.1, BRACKET_X[1] + 0.1, y, z))
        cuts.append(box(BRACKET_X[0] - 0.1, BRACKET_X[1] + 0.1, hole_y - SWITCH_ADJUST, hole_y + SWITCH_ADJUST,
                        z - SWITCH_HOLE_D / 2, z + SWITCH_HOLE_D / 2))
    for c in cuts:
        part -= c
    part.label = "dock_block"
    return part


if __name__ == "__main__":
    dock_block()
