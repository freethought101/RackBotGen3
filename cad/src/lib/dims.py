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
M5_CLEAR = 5.3
M3_CLEAR = 3.4
M3_INSERT_D = 4.0              # heat-set insert pilot
