"""Robot dimensions (mm). Robot frame = station frame when docked at the rack:
x = 0 on the centerline, +y toward the rack (robot nose tip on the dock stop at y = -30),
z = 0 on the table. Pose variables: Z = slot B floor height (lift), Y = extractor travel.
Source: docs/spec/01-mechanical.md §6; values added here are recorded back into the spec.
"""

from lib.dims import BAY_PITCH, CADDY_H, DOCK_STOP_Y, NOSE_W, TRAY_FRONT_DOCKED_Y

# ---- Lift / extractor ranges ------------------------------------------------------------------
Z_MIN, Z_MAX = 102.0, 295.0          # soft limits (slot B floor height)
Y_MAX = 175.0                        # finger at the notch of a seated caddy
Y_NOTCH_HOME = -185.0                # finger (notch centre) y with the caddy fully on the tray

# ---- Base ------------------------------------------------------------------------------------
BASE_FRONT_Y = DOCK_STOP_Y - 60.0    # -90: nose is 60 long
BASE_REAR_Y = BASE_FRONT_Y - 300.0   # -390
RAIL_X = (55.0, 75.0)                # |x| span of the two 2020 side rails
RAIL_Z = (42.0, 62.0)                # rails sit above the drive motors
DECK_Z = (62.0, 67.0)                # printed deck plate
DECK_HALF_W = 123.0
CROSS_Y = {"front": (BASE_FRONT_Y - 20.0, BASE_FRONT_Y),
           "mast": (-260.0, -240.0),
           "rear": (BASE_REAR_Y, BASE_REAR_Y + 20.0)}

NOSE_HALF_W = NOSE_W / 2
NOSE_Z = (30.0, 90.0)                # top stays below the tray underside (>= Z_MIN - 4)
CONTACT_X = 40.0                     # charging pads at x = +/-40, z = 60 (match the dock)
CONTACT_Z = 60.0
NOSE_SWITCH_X = 20.0                 # robot dock-detect lever (clear of the dock's own switch slot)

WHEEL_D, WHEEL_W = 80.0, 24.0
AXLE_Y, AXLE_Z = -135.0, 40.0        # direct drive; wheel front (y -95) stays 10 mm short of the dock funnel mouth
WHEEL_X = (125.0, 149.0)             # |x|
DRIVE_MOTOR_X = (79.0, 119.0)        # |x| body span, shaft face at 119
DRIVE_PLATE_X = (119.0, 123.0)       # |x| printed bracket plate between motor face and wheel
CASTER_REAR = [(-65.0, -380.0), (65.0, -380.0)]   # under the rear cross member
CASTER_FRONT = (0.0, -60.0)          # anti-tip caster under the nose, 3 mm off the table
CASTER_FRONT_GAP = 3.0

# ---- Mast / Z ---------------------------------------------------------------------------------
MAST_X = (-20.0, 20.0)               # 2040, 40 along x
MAST_Y = (-250.0, -230.0)
MAST_Z = (DECK_Z[1], DECK_Z[1] + 420.0)
SCREW_XY = (-51.0, -265.0)           # Tr8x2 lead screw axis (Z motor clears the mast collar)
SCREW_Z = (130.0, 480.0)
ZMOTOR_Z = (DECK_Z[1], DECK_Z[1] + 40.0)
ZPLATE_Y = (-228.0, -222.0)          # carriage plate in front of the mast
ZPLATE_X = (-70.0, 70.0)             # right edge clear of the extractor arm at Y = 0
ZPLATE_TAB = (70.0, 82.0, -10.0, 0.0)   # x0, x1, dz0, dz1: rail bracket bolts here, below the arm
ZPLATE_DZ = (-10.0, 100.0)           # relative to Z
TRAY_BOLTS = [(x, z) for x in (-50.0, 0.0, 50.0) for z in (-5.0, 37.0, 75.0)]   # tray -> Z plate (M5 along y)

# ---- Tray stack -------------------------------------------------------------------------------
TRAY_FRONT_Y = TRAY_FRONT_DOCKED_Y   # -25
TRAY_REAR_Y = -222.0                 # back plate bolts to the carriage plate
TRAY_STOP_Y = -200.0                 # caddy handle front rests 5 mm short of this
SLOT_A_DZ = BAY_PITCH
TRAY_FLOOR_T = 4.0
TRAY_CHANNEL_W = 116.0
TRAY_WALL_T = 3.0
TRAY_RIGHT_LIP_H = 6.0               # right side open above the lip for the finger
TRAY_TOP_DZ = SLOT_A_DZ + CADDY_H + 5.0   # 80

# ---- Y extractor ------------------------------------------------------------------------------
YRAIL_X = (82.0, 102.0)
YRAIL_DZ = (15.0, 35.0)              # relative to Z
YRAIL_Y = (-320.0, -35.0)
YBRACKET_Y = (-366.0, -228.0)        # rail is held only at its rear end (behind the carriage travel)
YBRACKET_X = (76.0, 82.0)
YBRACKET_DZ = (15.0, 33.0)
ARM_X = (74.5, 80.5)
YCARRIAGE_DY = (-92.0, -42.0)        # carriage y span relative to the finger pivot
ARM_DY = (-42.0, -8.0)               # arm y span relative to the finger pivot
# Fingers swing in the x-z plane about an axis along y (servo output shaft points +y):
# parked = pointing up (+z), engaged = pointing -x into the caddy's side notch.
FINGER_X = 68.0                      # pivot x (servo output axis)
FINGER_DZ = {"B": 15.0, "A": SLOT_A_DZ + 15.0}   # pivot heights relative to Z (caddy mid-height)
FINGER_LEN = 18.0                    # pivot to tip (tip at x = 50, inside the notch)
FINGER_W, FINGER_T = 6.0, 5.0        # width (in the swing plane), thickness (along y)
SERVO = {"len": 22.8, "wid": 12.2, "h": 28.5, "shaft_from_end": 5.9, "tab": 4.85}  # MG90S
SERVO_FACE_DY = -4.5                 # output face y relative to the pivot (horn + half finger)

# ---- Camera -----------------------------------------------------------------------------------
CAM_LENS = (-78.0, -115.0)           # x, y of the lens (looking +y)
CAM_DZ = 15.0                        # lens height relative to Z (slot B level)

# ---- Electronics / power ----------------------------------------------------------------------
PCB_XY = (19.0, -362.0)              # motion board lower-left corner (100 x 100)
PCB_Z = DECK_Z[1] + 10.0
PI_XY = (-123.0, -346.0)             # Pi 3 corner (85 along x, 56 along y)
BATTERY = (-118.0, -38.0, -387.5, -352.0, DECK_Z[1], DECK_Z[1] + 50.0)
ESTOP_XY = (-22.0, -255.0)           # on the mast top plate: highest, easiest point to hit
BUCKS = [(-50.0, -205.0), (7.0, -205.0)]      # 43 x 20 modules (x0, y0) on the deck under the tray
YMOTOR_X = (82.5, 124.8)             # behind the rail end, keeps the mast unit <= 230 wide
YMOTOR_Y = (-362.0, -320.0)
