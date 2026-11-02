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
M3_INSERT_D = 4.4              # M3 heat-set insert pilot (3Din M3, OD 4.2): prints ~4.0, 0.2 interference
M5_INSERT_D = 7.0              # M5 heat-set insert pilot (3Din M5, OD 7.0): prints ~6.35
M3_SELF_TAP_D = 2.85           # prints ~2.5
M2_PILOT_D = 1.95              # M2 self-tapping pilot, prints ~1.6 (not measured, by extrapolation)
M25_PILOT_D = 2.4              # M2.5 self-tapping pilot (Pi standoffs), prints ~2.05
M3_HEAD_CBORE = 6.9            # M3 button head (Ø5.7) counterbore: prints ~6.25 (6.4 would print ~5.75, no clearance)
M5_HEAD_CBORE = 10.4           # M5 button head (Ø9.5) counterbore / access: prints ~9.75
M3_NUT_AF = 6.3                # M3 nut pocket across flats (nut 5.5): prints ~5.7-6.0
SHAFT5_BORE = 5.3              # bore on a 5 mm motor shaft (drive hub): printed 5.08 in fit test 1, a snug slide

# KW11-3Z lever microswitch (P10 drawing): body length, height (pin edge to lever edge), thickness; free lever height
# above the lever edge; mounting holes +/- hole_dx from the body centre, ~hole_up in from the pin edge (estimated).
KW11 = {"l": 19.7, "h": 10.6, "t": 6.6, "lever": 7.1, "hole_dx": 4.75, "hole_up": 2.8, "hole_dl": 0.4}   # hole_up, hole_dl
# (holes 0.4 off the body centre, toward the lever hinge)   # hole_up from the P10 STEP
# (docs/3d-models/P10_kw11-3z-hinge-lever.step); its short lever rises only 4.3 above the body, not 7.1: measure the
# bought switches, the trigger points (nose, Z/Y home) are designed for 7.1
KW11_PRESS = 2.0               # lever travel at which a switch counts as triggered (design value)
HDD_SCREW_CLEAR = 4.0          # drive bottom screws: real HDDs are 6-32 UNC (3.5 mm), the dummy takes M3; prints ~3.6-3.8

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
