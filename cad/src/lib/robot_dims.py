"""Robot dimensions (mm). Robot frame = station frame when docked at the rack:
x = 0 on the centerline, +y toward the rack (robot nose tip on the dock stop at y = -30),
z = 0 on the table. Pose variables: Z = slot B floor height (lift), Y = extractor travel.
Source: docs/spec/01-mechanical.md §6; values added here are recorded back into the spec.
"""

from lib.dims import BAY_PITCH, CADDY_H, DOCK_STOP_Y, NOSE_W, TRAY_FRONT_DOCKED_Y

# ---- Lift / extractor ranges ------------------------------------------------------------------
Z_MIN, Z_MAX = 102.0, 295.0          # soft limits (slot B floor height)
Z_HOME = 101.0                       # Z home switch triggers here (firmware z_home); the hard stop is ~100.6
Y_NOTCH_HOME = -187.0                # finger pivot y at Y = 0 (notch centre of a caddy resting on the tray)
Y_PULL = 177.0                       # finger centred in the notch of a seated caddy (handle front at y -20)
Y_SEAT = 178.0                       # pushing: finger front face on the notch wall with the caddy seated
Y_PUSH = Y_SEAT + 0.5                # push target (0.5 mm preload against the bay back stop)
Y_MAX = 180.0                        # soft limit; the carriage meets the idler bracket at Y = Y_HARD
Y_HARD = 187.0

# ---- Base ------------------------------------------------------------------------------------
BASE_FRONT_Y = DOCK_STOP_Y - 60.0    # -90: nose is 60 long
BASE_REAR_Y = BASE_FRONT_Y - 300.0   # -390
RAIL_X = (55.0, 75.0)                # |x| span of the two 2020 side rails
RAIL_Z = (42.0, 62.0)                # rails sit above the drive motors
DECK_Z = (62.0, 67.0)                # printed deck plate
DECK_HALF_W = 123.0
CROSS_Y = {"front": (BASE_FRONT_Y - 20.0, BASE_FRONT_Y),
           "mast": (-250.0, -230.0),       # directly under the mast (the mast stands on it)
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
DRIVE_INSERT_X = 105.0               # |x| deck -> drive bracket M3 (inserts in the web tops, clear of the motor)
DRIVE_INSERT_Y = (AXLE_Y - 27.0, AXLE_Y + 27.0)
CASTER_REAR = [(-65.0, -380.0), (65.0, -380.0)]   # under the rear cross member
CASTER_FRONT = (0.0, -60.0)          # anti-tip caster under the nose, 23.5 mm tall (nose floor z 30 - gap)
CASTER_FRONT_GAP = 6.5               # 3.5 mm above the dock floor plate (3 mm) when docked

# ---- Mast / Z ---------------------------------------------------------------------------------
MAST_X = (-20.0, 20.0)               # 2040, 40 along x
MAST_Y = (-250.0, -230.0)
MAST_Z = (RAIL_Z[1], RAIL_Z[1] + 420.0)   # through a deck cut-out, standing on the mast cross member
SCREW_XY = (-51.0, -265.0)           # Tr8x2 lead screw axis (Z motor clears the mast collar)
ZMOTOR_Z = (DECK_Z[1], DECK_Z[1] + 40.0)
ZMOUNT_T = 5.0                       # printed Z-motor mount plate on the motor's shaft face
COUPLER_Z = (ZMOTOR_Z[1] + ZMOUNT_T + 5.0, ZMOTOR_Z[1] + ZMOUNT_T + 30.0)   # 5->8 coupler, 25 long
SCREW_Z = (COUPLER_Z[1] - 11.0, COUPLER_Z[1] - 11.0 + 350.0)   # 350 mm screw, 11 mm in the coupler
KFL08 = {"l": 48.0, "w": 27.0, "pitch": 37.0, "flange_t": 5.0, "h": 13.0, "boss_d": 22.0}
ZPLATE_Y = (-228.0, -222.0)          # carriage plate in front of the mast
ZPLATE_X = (-70.0, 62.0)             # right edge 1.4 mm clear of the servos at Y = 0
ZPLATE_DZ = (-10.0, 100.0)           # relative to Z
ZWHEEL_X = 26.0                      # |x| V-wheel centres in the mast side grooves (axles along y)
ZWHEEL_DZ = (14.0, 92.0)            # lower pair rolls 1.4 mm above the Z motor at Z_MIN (78 mm wheelbase)
NUT_BLOCK_DZ = (44.0, 64.0)          # anti-backlash nut block; bottom clears the coupler top at Z_MIN
# Tray -> Z plate: M5 from behind the plate into M5 heat-set inserts in the tray back plate. Columns clear the
# mast (|x| <= 20), the Z wheels and the nut block (x -64..-38, z 44..64); the x = 50 column also clamps the
# Y-rail bracket's back plate.
TRAY_BOLTS = [(-50.0, -5.0), (-50.0, 75.0), (-38.0, -5.0), (-38.0, 75.0),
              (38.0, -5.0), (38.0, 37.0), (38.0, 75.0), (50.0, -5.0), (50.0, 37.0), (50.0, 75.0)]
RAIL_BRACKET_BOLT_X = 50.0

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
YRAIL_X = (84.0, 104.0)
YRAIL_DZ = (15.0, 35.0)              # relative to Z
YRAIL_Y = (-320.0, -35.0)
YBRACKET_Y = (-368.0, -228.5)        # rail is held at its rear end (behind the carriage travel)
YBRACKET_X = (68.0, 84.0)            # strip on the rail's inner face, 16 x 20
YBRACKET_DZ = (13.0, 33.0)           # top stays 2.5 mm under the carriage frame
YBRACKET_PLATE = (44.0, 75.0, 84.0, 33.0, -10.0, 80.0)   # back plate: x0, x1 above z_step, x1 below, z_step, z0, z1
YBRACKET_PLATE_Y = (-240.0, -228.5)  # behind the Z plate; clamped by the x = 50 tray bolts
ARM_X = (76.5, 82.0)                 # arm on the rail's inner side, 2 mm from the rail face
YCARRIAGE_DY = (-92.0, -50.0)        # carriage y span relative to the finger pivot
ARM_DY = (-40.0, -8.0)               # arm y span relative to the finger pivot
YPLATE_X = (YRAIL_X[1] + 1.0, YRAIL_X[1] + 5.0)   # outer wheel plate
YFRAME_DZ = (50.0, 56.0)             # frame over the top wheels joining the arm to the outer plate
YWHEEL_DY = (-84.0, -58.0)           # V-wheel pairs (above and below the rail), axles along x
YWHEEL_DZ = (YRAIL_DZ[0] - 6.0, YRAIL_DZ[1] + 6.0)
VWHEEL = {"d": 15.2, "w": 8.8, "sink": 1.6, "spacer_d": 10.0}   # mini V-wheel; rim sits 1.6 mm in the groove
# Axle stack plate -> wheel: 6 mm mini spacer (eccentric 8 mm hex, or plain) + 1 mm 5 x 8 shim on the bearing's
# inner ring. The plates get a pad or recess around each axle so the wheel sits on its groove centre.
WHEEL_STACK = 7.0
ECC_HOLE_D = 7.9                     # eccentric boss Ø7.11 (OpenBuilds STEP); ~7 mm holes print ~0.65 under (fit test 1) -> ~7.25
WHEEL_SEAT_D = 12.0                  # pad / recess diameter around an axle (spacer hex is 9.2 across corners)
ZWHEEL_SEAT_Y = (MAST_Y[0] + MAST_Y[1]) / 2 + VWHEEL["w"] / 2 + WHEEL_STACK   # -228.6: 0.6 pad on the Z plate
YWHEEL_SEAT_X = (YRAIL_X[0] + YRAIL_X[1]) / 2 + VWHEEL["w"] / 2 + WHEEL_STACK  # 105.4: 0.4 recess in the Y plate
# Fingers swing in the x-z plane about an axis along y (servo output shaft points +y):
# parked = pointing up (+z), engaged = pointing -x into the caddy's side notch.
FINGER_X = 69.5                      # pivot x (servo output axis); servo 63.4..75.6, 2.4 mm from the tray lip
FINGER_DZ = {"B": 15.0, "A": SLOT_A_DZ + 15.0}   # pivot heights relative to Z (caddy mid-height)
FINGER_LEN = 19.5                    # pivot to tip (tip at x = 50, inside the notch)
FINGER_W, FINGER_T = 6.0, 10.0       # width (in the swing plane), thickness (along y): +/-1 mm play in the 12 mm notch
# MG90S from the P09 STEP (docs/3d-models/P09_mg90s.step): case 23 x 12.4, output face 27.4 above the bottom, shaft
# 6.2 from the case end, 2.5 mm tabs (33 over the tabs) whose upper face is 7.9 below the output face; the single-arm
# horn is 5.0 tall (Ø7 hub 3.5 + arm plate 1.5, Ø1 holes every 2 mm at 4-14 from the axis, tip at 16.5).
SERVO = {"len": 23.0, "wid": 12.4, "h": 27.4, "shaft_from_end": 6.2, "tab": 5.0, "tab_drop": 7.9, "horn": 5.0}
SERVO_FACE_DY = -(SERVO["horn"] + FINGER_T / 2)   # -10: output face y relative to the pivot (horn 5 + half finger 5)

# ---- Camera -----------------------------------------------------------------------------------
CAM_LENS = (-78.0, -115.0)           # x, y of the lens (looking +y)
CAM_DZ = 15.0                        # lens height relative to Z (slot B level)
# Waveshare IMX708-120 (wirogix listing) = Camera Module 3 Wide board (P13 mechanical drawing): 25 x 23.862 x 1.12 PCB,
# lens centred across the width and 14.4 above the bottom edge; 10.8 square holder 4.23 deep + Ø6.95 barrel to 8.3 in
# front of the PCB; connector 2.75 deep on the back.
CAM_BOARD = {"w": 25.0, "h": 23.862, "t": 1.12, "lens_up": 14.4, "holder": 10.8, "holder_l": 4.23,
             "barrel_d": 6.95, "lens_l": 8.3, "back": 2.75}

# ---- Electronics / power ----------------------------------------------------------------------
PCB_XY = (19.0, -362.0)              # motion board lower-left corner (100 x 100)
PCB_Z = DECK_Z[1] + 10.0
PI_XY = (-123.0, -343.5)             # Pi 3 corner (85 along x, 56 along y), between the battery box and the Z motor
BATTERY = (-118.0, -38.0, -387.5, -349.0, DECK_Z[1], DECK_Z[1] + 50.0)   # inside: 4 x 18650 2 x 2 along x + BMS on top
# M3 + nut through the deck for the trays and the battery box (nuts clear the side rails and the rear cross member)
PCB_DECK_HOLES = ((PCB_XY[0] + 2.0, PCB_XY[1] + 50.0), (PCB_XY[0] + 98.0, PCB_XY[1] + 50.0))
PI_DECK_HOLES = ((PI_XY[0] + 6.0, PI_XY[1] + 28.0), (PI_XY[0] + 77.0, PI_XY[1] + 28.0))   # outside the tray window
BATTERY_DECK_HOLES = ((BATTERY[0] + 10.0, BATTERY[3] - 8.0), (BATTERY[1] - 10.0, BATTERY[3] - 8.0))
ESTOP_XY = (-22.0, -255.0)           # on the mast top plate: highest, easiest point to hit
BUCKS = {"charger": (-60.0, -205.0), "5v": (4.0, -205.0), "6v": (-28.0, -172.0)}   # (x0, y0) under the tray
# (x, y, z) envelope per module (P18), from the Tokopedia listings we order from; measure on arrival.
# charger: XL4015 CC/CV (CNC Store Bandung) gives no size; other sellers list 52-55 x 25-27 x 14-15.
# 5v: XY-3606 (EasyWare) lists 63 x 27 x 10; 13 high for the DC jack and capacitors.
# 6v: a second XL4015, set to 5.8 V (v0.1.29; the MP2482/SY8205 module is fixed at 5 V).
BUCK_SIZE = {"charger": (55.0, 27.0, 15.0), "5v": (63.0, 27.0, 13.0), "6v": (55.0, 27.0, 15.0)}
# Y drive: GT2 6 mm belt loop in a horizontal plane beside the rail's outer face. 20T pulley behind the
# rail end on the Y motor (shaft pointing down, body above the belt), idler on a fork bracket at the rail's
# front end, carriage clamps the inner strand. 200 x 16 / (20 x 2 mm) = 80 usteps/mm.
BELT_X = 117.0                       # pulley / idler axis x
PULLEY_Y, IDLER_Y = -345.0, -44.0
BELT_DZ = (19.0, 25.0)               # belt width band relative to Z
PULLEY_CORE_D, PULLEY_FLANGE_D = 12.0, 16.0
BELT_T = 1.1
BELT_STRAND_X = [(BELT_X - PULLEY_CORE_D / 2 - BELT_T, BELT_X - PULLEY_CORE_D / 2),
                 (BELT_X + PULLEY_CORE_D / 2, BELT_X + PULLEY_CORE_D / 2 + BELT_T)]   # inner, outer strand
YMOTOR_PLATE_DZ = (28.0, 32.0)       # horizontal motor plate; motor body sits on top
YMOTOR_DZ = (YMOTOR_PLATE_DZ[1], YMOTOR_PLATE_DZ[1] + 40.0)
IDLER_BRACKET_Y = (-50.0, -35.0)     # fork on the rail's outer face; the carriage plate meets it at Y_HARD
