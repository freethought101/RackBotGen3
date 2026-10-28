"""Caster spacers (PETG). The bought ball casters are 20 mm tall (48 x 32 base, 2 x Ø4 holes 40 apart); these make
up the design heights. Hole pitch slotted +/-2 mm, so a caster with holes 38-42 mm apart also fits.

- caster_spacer_rear (x2): 22 mm block under each side rail's rear end (caster long side along the rail). Two M5 +
  T-nuts into the rail's bottom slot (heads in counterbores from below, fitted before the caster); the caster's two M3
  screws go up into M3 nuts slid into side pockets.
- caster_spacer_front (x1): 3.5 mm plate between the anti-tip caster and the nose floor; M3 screws through the caster,
  plate and floor into nuts inside the nose.
"""

from cadgen import step, stl

from lib.dims import M3_CLEAR, M3_NUT_AF, M5_CLEAR, M5_HEAD_CBORE
from lib.prims import box, cyl_z
from lib.robot_dims import CASTER, CASTER_FRONT, CASTER_FRONT_GAP, CASTER_REAR, NOSE_Z, RAIL_Z

MARGIN = 2.0                  # spacer outline beyond the caster base, per side
M5_FLANGE = 6.0               # material under the rail between the counterbore and the top face
NUT_AF, NUT_T = M3_NUT_AF, 3.0   # M3 nut pocket (5.5 AF x 2.4 nut + print clearance)
NUT_Z = 5.0                   # nut pocket floor above the spacer bottom


def _slot_z(d, x0, x1, y0, y1, z0, z1):
    """Vertical hole of diameter d whose centre may lie anywhere on the segment (x0, y0)-(x1, y1) (axis-aligned)."""
    return (box(min(x0, x1) - (d / 2 if y0 != y1 else 0), max(x0, x1) + (d / 2 if y0 != y1 else 0),
                min(y0, y1) - (d / 2 if x0 != x1 else 0), max(y0, y1) + (d / 2 if x0 != x1 else 0), z0, z1)
            + cyl_z(d, x0, y0, z0, z1) + cyl_z(d, x1, y1, z0, z1))


@step(out="../../STEP/robot/caster_spacer_rear.step")
@stl(out="../../STL/robot/caster_spacer_rear.stl")
def caster_spacer_rear():
    cx, cy = CASTER_REAR[1]                                   # right one; the left is the same part turned 180°
    bl, bw = CASTER["base"]                                   # long side along y (the rail)
    z0, z1 = CASTER["h"], RAIL_Z[0]                         # caster top .. rail bottom (22 mm)
    hl, hw = bl / 2 + MARGIN, bw / 2 + MARGIN
    part = box(cx - hw, cx + hw, cy - hl, cy + hl, z0, z1)
    for dy in (-8.0, 8.0):                                    # M5 into the rail's bottom slot
        part -= cyl_z(M5_CLEAR, cx, cy + dy, z1 - M5_FLANGE - 0.1, z1 + 0.1)
        part -= cyl_z(M5_HEAD_CBORE, cx, cy + dy, z0 - 0.1, z1 - M5_FLANGE)
    p, a = CASTER["pitch"] / 2, CASTER["pitch_adj"]
    for s in (-1, 1):
        ya, yb = cy + s * (p - a), cy + s * (p + a)
        part -= _slot_z(M3_CLEAR, cx, cx, ya, yb, z0 - 0.1, z0 + NUT_Z + NUT_T + 4.0)
        part -= box(cx - NUT_AF / 2, cx + hw + 0.1, min(ya, yb) - NUT_AF / 2, max(ya, yb) + NUT_AF / 2,
                    z0 + NUT_Z, z0 + NUT_Z + NUT_T)               # nut slides in from the +x side
    part.label = "caster_spacer_rear"
    return part


@step(out="../../STEP/robot/caster_spacer_front.step")
@stl(out="../../STL/robot/caster_spacer_front.stl")
def caster_spacer_front():
    cx, cy = CASTER_FRONT
    bl, bw = CASTER["base"]                                   # long side along x (across the nose)
    z1 = NOSE_Z[0]
    z0 = CASTER_FRONT_GAP + CASTER["h"]
    hl, hw = bl / 2 + MARGIN, bw / 2 + MARGIN
    part = box(cx - hl, cx + hl, cy - hw, cy + hw, z0, z1)
    p, a = CASTER["pitch"] / 2, CASTER["pitch_adj"]
    for s in (-1, 1):
        part -= _slot_z(M3_CLEAR, cx + s * (p - a), cx + s * (p + a), cy, cy, z0 - 0.1, z1 + 0.1)
    part.label = "caster_spacer_front"
    return part


if __name__ == "__main__":
    caster_spacer_rear()
    caster_spacer_front()
