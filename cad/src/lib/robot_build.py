"""Robot assembly factory: robot_parts(Z, Y, fingers) -> list of labeled, placed shapes.

Pose: Z = slot B floor height (lift), Y = extractor travel (0 = home, 175 = finger at a seated
caddy's notch), fingers = {"A": "parked"|"engaged", "B": ...}. Frame as in lib/robot_dims.py.
"""

import os

from cadgen import build123d as bd
from cadgen import read_step, srgb

from lib import vendor
from lib.extrusion import vslot
from lib.prims import box, cyl_z
from lib.robot_dims import (AXLE_Y, AXLE_Z, BASE_FRONT_Y, BASE_REAR_Y, BATTERY, BUCK_SIZE, BUCKS, CAM_DZ,
                            CAM_LENS, CASTER_FRONT, CASTER_FRONT_GAP, CASTER_REAR, COUPLER_Z, CROSS_Y, DECK_Z,
                            DRIVE_MOTOR_X, ESTOP_XY, FINGER_DZ, FINGER_X, KFL08, MAST_X, MAST_Y, MAST_Z, NOSE_Z,
                            PCB_XY, PCB_Z, PI_XY, RAIL_X, RAIL_Z, SCREW_XY, SCREW_Z, SERVO, SERVO_FACE_DY, VWHEEL,
                            Y_NOTCH_HOME, YPLATE_X, YRAIL_DZ, YRAIL_X, YRAIL_Y, YWHEEL_DY,
                            YWHEEL_DZ, ZMOTOR_Z, ZPLATE_Y, ZWHEEL_DZ, ZWHEEL_X,
                            BELT_DZ, BELT_STRAND_X, BELT_X, IDLER_Y, PULLEY_CORE_D, PULLEY_FLANGE_D, PULLEY_Y,
                            YMOTOR_DZ)
from robot.battery_box import battery_box
from robot.deck import deck
from robot.drive_bracket import drive_bracket
from robot.drive_wheel import drive_hub, drive_tire
from robot.electronics_tray import electronics_tray
from robot.finger import finger
from robot.mast_collar import mast_collar
from robot.mast_top_plate import mast_top_plate
from robot.nose import nose
from robot.pi_tray import pi_tray
from robot.rail_bracket import rail_bracket
from robot.tray_stack import tray_stack
from robot.y_carriage import y_carriage
from robot.y_idler_bracket import y_idler_bracket
from robot.z_carriage import z_carriage
from robot.z_motor_mount import z_motor_mount

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_STEP = os.path.join(HERE, "..", "..", "..", "pcb", "motion-board", "fab", "rbg3-motion.step")
PRINTED = srgb("#E8E4DA")
ACCENT = srgb("#E07A1F")

# Extrusion cut list (mm), used by the mass/packing checks.
M5_BORE = 5.0
EXTRUSIONS = {"2020": [300.0, 300.0, 110.0, 110.0, 110.0, YRAIL_Y[1] - YRAIL_Y[0]], "2040": [MAST_Z[1] - MAST_Z[0]]}


def _p(shape, label, color=PRINTED):
    shape.label = label
    shape.color = color
    return shape


def base_parts():
    parts = []
    xr0, xr1 = RAIL_X
    for s, side in ((-1, "left"), (1, "right")):
        x0, x1 = sorted((s * xr0, s * xr1))
        parts.append(vslot(x0, x1, BASE_REAR_Y, BASE_FRONT_Y, *RAIL_Z, f"rail_2020:{side}"))
    for name, (y0, y1) in CROSS_Y.items():
        parts.append(vslot(-xr0, xr0, y0, y1, *RAIL_Z, f"cross_2020:{name}"))
    parts.append(_p(deck(), "deck"))
    parts.append(_p(nose(), "nose", ACCENT))
    right = drive_bracket()
    parts.append(_p(right, "drive_bracket:right"))
    parts.append(_p(right.mirror(bd.Plane.YZ), "drive_bracket:left"))
    hub, tire = drive_hub(), drive_tire()
    parts.append(_p(hub, "drive_hub:right"))
    parts.append(_p(hub.mirror(bd.Plane.YZ), "drive_hub:left"))
    parts.append(_p(tire, "drive_tire:right", vendor.RUBBER))
    parts.append(_p(tire.mirror(bd.Plane.YZ), "drive_tire:left", vendor.RUBBER))
    for s, side in ((-1, "left"), (1, "right")):
        parts.append(vendor.nema17_x(s * DRIVE_MOTOR_X[1], AXLE_Y, AXLE_Z, s, f"nema17:drive_{side}"))
    for i, (x, y) in enumerate(CASTER_REAR):
        parts.append(vendor.ball_caster(x, y, 0.0, RAIL_Z[0], f"caster:rear_{i}"))
    cx, cy = CASTER_FRONT
    parts.append(vendor.ball_caster(cx, cy, CASTER_FRONT_GAP, NOSE_Z[0] - CASTER_FRONT_GAP, "caster:front_antitip"))
    # Mast, Z drive.
    parts.append(vslot(*MAST_X, *MAST_Y, *MAST_Z, "mast_2040"))
    parts.append(_p(mast_collar(), "mast_collar"))
    parts.append(_p(mast_top_plate(), "mast_top_plate"))
    sx, sy = SCREW_XY
    parts.append(vendor.nema17_z(sx, sy, ZMOTOR_Z[0], "nema17:z"))
    parts.append(_p(z_motor_mount(), "z_motor_mount"))
    parts.append(vendor.rod_z(19.0, sx, sy, *COUPLER_Z, "coupler"))
    parts.append(vendor.rod_z(8.0, sx, sy, SCREW_Z[0], SCREW_Z[1], "leadscrew_tr8x2"))
    parts.append(vendor.kfl08_z(sx, sy, MAST_Z[1], KFL08))
    # Electronics and power.
    parts.append(_p(electronics_tray(), "electronics_tray"))
    pcb = read_step(PCB_STEP)
    pcb = bd.Pos(PCB_XY[0] - 100.0, PCB_XY[1] + 200.0, PCB_Z) * pcb   # STEP: board x 100..200, y -200..-100, bottom face at z 0
    parts.append(_p(pcb, "motion_board", vendor.GREEN))
    parts.append(_p(pi_tray(), "pi_tray"))
    parts.append(vendor.board(PI_XY[0], PI_XY[1], PCB_Z, 85.0, 56.0, 17.0, "raspberry_pi_3"))
    parts.append(_p(battery_box(), "battery_box"))
    bx0, bx1, by0, by1, bz0, bz1 = BATTERY
    parts.append(vendor.board(bx0 + 1, by0 + 1, bz0 + 3, bx1 - bx0 - 2, by1 - by0 - 2, 42.0, "battery_4s1p",
                              srgb("#3B82F6")))
    ex, ey = ESTOP_XY
    zt = MAST_Z[1] + 6.0                         # on the mast top plate
    parts.append(vendor.board(ex - 20, ey - 20, zt, 40.0, 40.0, 40.0, "estop_box", srgb("#FACC15")))
    parts.append(_p(cyl_z(40.0, ex, ey, zt + 40.0, zt + 60.0), "estop_button", srgb("#DC2626")))
    bw, bl, bh = BUCK_SIZE
    for name, (x, y) in BUCKS.items():
        parts.append(vendor.board(x, y, DECK_Z[1], bw, bl, bh, f"buck:{name}", srgb("#7C3AED")))
    return parts


def lift_parts(Z):
    at = bd.Pos(0, 0, Z)
    parts = [_p(at * z_carriage(), "z_carriage"), _p(at * tray_stack(), "tray_stack", ACCENT),
             _p(at * rail_bracket(), "rail_bracket")]
    yc = (MAST_Y[0] + MAST_Y[1]) / 2                         # mast side groove centre
    for s in (-1, 1):
        for dz in ZWHEEL_DZ:
            parts.append(vendor.vwheel((s * ZWHEEL_X, yc, Z + dz), "y", VWHEEL, spacer_to=ZPLATE_Y[0],
                                       label=f"vwheel:z{'LR'[s > 0]}{dz:.0f}"))
    parts.append(vslot(*YRAIL_X, *YRAIL_Y, Z + YRAIL_DZ[0], Z + YRAIL_DZ[1], "y_rail_2020"))
    # Y belt drive: motor (shaft down) + 20T pulley behind the rail end, idler on the front bracket, belt loop.
    parts.append(vendor.nema17_z(BELT_X, PULLEY_Y, Z + YMOTOR_DZ[0], "nema17:y", shaft_up=False))
    parts.append(vendor.gt2_wheel(BELT_X, PULLEY_Y, Z + BELT_DZ[0], Z + BELT_DZ[1], PULLEY_CORE_D,
                                  PULLEY_FLANGE_D, "gt2_pulley_20t"))
    parts.append(vendor.gt2_wheel(BELT_X, IDLER_Y, Z + BELT_DZ[0], Z + BELT_DZ[1], PULLEY_CORE_D,
                                  PULLEY_FLANGE_D, "gt2_idler", bore=M5_BORE))
    parts.append(_p(at * y_idler_bracket(), "y_idler_bracket"))
    for (x0, x1), side in zip(BELT_STRAND_X, ("inner", "outer")):
        parts.append(_p(box(x0, x1, PULLEY_Y, IDLER_Y, Z + BELT_DZ[0], Z + BELT_DZ[1]), f"gt2_belt:{side}",
                        vendor.RUBBER))
    lx, ly = CAM_LENS
    cam = box(lx - 12.5, lx + 12.5, ly - 3.5, ly - 1.5, Z + CAM_DZ - 11.5, Z + CAM_DZ + 12.5)
    cam += bd.Pos(lx, ly - 1.5, Z + CAM_DZ) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        4.0, 1.4, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    parts.append(_p(cam, "camera_module_3_wide", vendor.GREEN))
    return parts


def extractor_parts(Z, Y, fingers):
    pivot_y = Y_NOTCH_HOME + Y
    parts = [_p(bd.Pos(0, pivot_y, Z) * y_carriage(), "y_carriage")]
    xc = (YRAIL_X[0] + YRAIL_X[1]) / 2                       # rail top/bottom groove centre
    for dy in YWHEEL_DY:
        for dz in YWHEEL_DZ:
            parts.append(vendor.vwheel((xc, pivot_y + dy, Z + dz), "x", VWHEEL, spacer_to=YPLATE_X[0],
                                       label=f"vwheel:y{dy:.0f}{dz:.0f}"))
    for slot, dz in FINGER_DZ.items():
        pz = Z + dz
        parts.append(vendor.mg90s_y(FINGER_X, pivot_y + SERVO_FACE_DY, pz, f"mg90s:{slot}", SERVO))
        angle = -90.0 if fingers.get(slot, "parked") == "engaged" else 0.0
        f = bd.Pos(FINGER_X, pivot_y, pz) * bd.Rot(0, angle, 0) * finger()
        parts.append(_p(f, f"finger:{slot}", ACCENT))
    return parts


def robot_parts(Z, Y=0.0, fingers=None):
    fingers = fingers or {}
    return base_parts() + lift_parts(Z) + extractor_parts(Z, Y, fingers)
