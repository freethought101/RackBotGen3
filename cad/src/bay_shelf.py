"""Bay shelf (PETG, x6: 4 rack bays + 2 spare-station slots). Spec: docs/spec/01-mechanical.md §4.

Frame: x = 0 on the bay centerline, y = 0 at the shelf front edge (rack face),
z = 0 on the shelf floor top. Bolts to two 2020 uprights per side (inner face at
|x| = 70, centers at y = 20 and 135) with M5 button heads + T-nuts; the heads sit in
counterbores reached with a hex key through the channel.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import BAY_CHANNEL_W, BAY_DEPTH, LEAD_IN, M5_CLEAR, UPRIGHT_INNER_X, UPRIGHT_Y
from lib.prims import box, cyl_x, prism_xy, prism_yz

FLOOR_T = 4.0
WALL_T = 3.0
WALL_H = 20.0
RUNNER_INNER_X = 44.0      # runners support the caddy's side walls and rails (|x| 51.5..57)
BACKSTOP_T = 4.0
BOLT_Z = 8.0
CBORE_D = 10.0
FLANGE_T = 4.0             # material between the counterbore and the upright face
FRONT_BLOCK = (0.0, 32.0)  # y span of the front flange block (also carries the lead-in)
REAR_BLOCK = (123.0, BAY_DEPTH + BACKSTOP_T)
FLOOR_CHAMFER = 3.0

# KW11-3Z bay switch: body in the y-z plane on a bracket behind the back stop,
# lever reaching through a slot to meet the caddy rear in its last ~3 mm.
SWITCH_SLOT_W = 8.0
SWITCH_SLOT_Z = (4.0, 18.0)
BRACKET_X = (4.0, 7.0)
BRACKET_Y_END = BAY_DEPTH + BACKSTOP_T + 14.0
SWITCH_HOLE_D = 1.7        # M2 self-tapping pilot
SWITCH_HOLE_Z = (3.25, 12.75)  # 9.5 mm pitch (verify against the purchased switch)
SWITCH_HOLE_Y = 161.0
SWITCH_ADJUST = 2.0        # +/- slot in y to tune the actuation point

CH = BAY_CHANNEL_W / 2
OUT = UPRIGHT_INNER_X


@step(out="../STEP/bay_shelf.step")
@stl(out="../STL/bay_shelf.stl")
def bay_shelf():
    back = BAY_DEPTH + BACKSTOP_T
    shelf = (
        box(-CH, CH, 0, 10, -FLOOR_T, 0)                                  # front cross bar
        + box(-CH, CH, 70, 80, -FLOOR_T, 0)                               # middle cross bar
        + box(-CH - WALL_T, CH + WALL_T, BAY_DEPTH, back, -FLOOR_T, WALL_H)  # back stop
    )
    for s in (-1, 1):
        def xs(a, b):
            return sorted((s * a, s * b))

        shelf += box(*xs(RUNNER_INNER_X, OUT), 0, back, -FLOOR_T, 0)      # runner
        shelf += box(*xs(CH, CH + WALL_T), 0, BAY_DEPTH, 0, WALL_H)       # guide wall
        for y0, y1 in (FRONT_BLOCK, REAR_BLOCK):
            shelf += box(*xs(CH, OUT), y0, y1, -FLOOR_T, WALL_H)          # flange block

    # Switch bracket behind the back stop.
    shelf += box(*BRACKET_X, back, BRACKET_Y_END, -FLOOR_T, WALL_H)

    cuts = []
    for s in (-1, 1):
        def xs(a, b):
            return sorted((s * a, s * b))

        for y in UPRIGHT_Y:
            cuts.append(cyl_x(M5_CLEAR, *xs(OUT - FLANGE_T - 0.1, OUT + 0.1), y, BOLT_Z))
            cuts.append(cyl_x(CBORE_D, *xs(CH - 0.1, OUT - FLANGE_T), y, BOLT_Z))
        # 45 deg lead-in at the bay mouth.
        cuts.append(prism_xy([(s * CH, LEAD_IN), (s * (CH + LEAD_IN), -0.1), (s * CH, -0.1)],
                             -0.01, WALL_H + 0.1))
    # Front top edge of the floor chamfered so a slightly low caddy ramps up.
    cuts.append(prism_yz([(-0.1, 0.1), (FLOOR_CHAMFER, 0.1), (-0.1, -FLOOR_CHAMFER)], -OUT - 1, OUT + 1))
    # Switch lever slot through the back stop.
    cuts.append(box(-SWITCH_SLOT_W / 2, SWITCH_SLOT_W / 2, BAY_DEPTH - 0.1, back + 0.1, *SWITCH_SLOT_Z))
    # Switch mounting slots through the bracket.
    for z in SWITCH_HOLE_Z:
        y0, y1 = SWITCH_HOLE_Y - SWITCH_ADJUST, SWITCH_HOLE_Y + SWITCH_ADJUST
        cuts.append(cyl_x(SWITCH_HOLE_D, BRACKET_X[0] - 0.1, BRACKET_X[1] + 0.1, y0, z))
        cuts.append(cyl_x(SWITCH_HOLE_D, BRACKET_X[0] - 0.1, BRACKET_X[1] + 0.1, y1, z))
        cuts.append(box(BRACKET_X[0] - 0.1, BRACKET_X[1] + 0.1, y0, y1,
                        z - SWITCH_HOLE_D / 2, z + SWITCH_HOLE_D / 2))

    for c in cuts:
        shelf -= c
    shelf.label = "bay_shelf"
    return shelf


if __name__ == "__main__":
    bay_shelf()
