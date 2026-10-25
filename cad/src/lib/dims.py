"""Shared interface dimensions (mm). Source of truth: docs/spec/01-mechanical.md §1.

Frame used by every bay-side part: x = across the bay (0 = bay centerline),
y = into the bay (0 = rack face / shelf front edge), z = up (0 = shelf floor top).
"""

# Rack / bay
BAY_PITCH = 45.0
H_BAY = (150.0, 195.0, 240.0, 285.0)
H_SPARE = (150.0, 195.0)
BAY_CHANNEL_W = 116.0          # clear width between shelf guide walls
BAY_DEPTH = 150.0              # shelf front edge to back stop
LEAD_IN = 6.0                  # 45 deg lead-in at the bay mouth

# Caddy
CADDY_BODY_L = 150.0           # inside the bay
CADDY_HANDLE_L = 20.0          # protrudes out of the rack face
CADDY_W = 110.0
CADDY_H = 30.0
CADDY_RAIL_W = 2.0             # rib protrusion per side -> 114 over rails
CADDY_RAIL_H = 4.0

# Hook notch on the right (+x) side of the handle block
NOTCH_L = 12.0                 # along y
NOTCH_DEPTH = 8.0              # into x
NOTCH_FROM_FRONT = 10.0        # notch center from handle front face

# 3.5" drive (SFF-8301 envelope)
HDD_L = 147.0
HDD_W = 101.6
HDD_H = 26.1
HDD_HOLE_SPAN_X = 95.25        # bottom hole spacing across the width
HDD_HOLE_Y = (41.28, 85.73)    # bottom hole positions from drive front (verify on a real drive)

# 2020 upright position used by the shelf mounting flanges
UPRIGHT_INNER_X = 70.0         # |x| of the upright inner face
UPRIGHT_Y = (20.0, 135.0)      # upright centers along y
# Hole sizes are modeled oversize: fit test 1 (25 Oct, hole coupon, PETG) printed small holes 0.2-0.65 mm under.
# Design -> printed: 2.5 -> 2.11, 3.4 -> 3.19, 4.0 -> 3.58, 5.3 -> 5.08, 6.4 -> 5.75. See docs/fit-test-01.md.
M5_CLEAR = 5.5
M3_CLEAR = 3.6
M3_INSERT_D = 4.4              # M3 heat-set insert pilot (OD 4.5): prints ~4.0
M5_INSERT_D = 7.0              # M5 heat-set insert pilot (OD ~7): prints ~6.4
M3_SELF_TAP_D = 2.85           # prints ~2.5
M2_PILOT_D = 1.95              # M2 self-tapping pilot, prints ~1.6 (not measured, by extrapolation)
HDD_SCREW_CLEAR = 3.7          # drive bottom screws: real HDDs are 6-32 UNC (3.5 mm), the dummy takes M3

# Docking (station frame: z = 0 on the table)
NOSE_W = 200.0                 # robot nose width
DOCK_STOP_Y = -30.0            # stop face; robot nose tip lands here
TRAY_FRONT_DOCKED_Y = -25.0    # tray overhangs the nose by 5 mm

# Tags (tag36h11)
TAG_APPROACH = 50.0            # IDs 0 (rack) and 10 (spare station)
TAG_BAY = 16.0                 # IDs 1-4 (rack bays), 11-12 (spare slots)
TAG_APPROACH_Z = 230.0         # approach tag centre height above the table
TAG_FACE_Y = 7.0               # front face of tag strips and fins

# Station frames (2020): base cross members on the table, uprights on top, top cross members.
EXT = 20.0
BASE_HALF_L = 110.0            # base cross members span x -110..110 (feet)
TOP_HALF_L = 90.0              # top cross members span the uprights
RACK_TOP_Z = 360.0
SPARE_TOP_Z = 255.0
