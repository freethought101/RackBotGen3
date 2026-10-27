"""Robot assembly factory: robot_parts(Z, Y, fingers) -> list of labeled, placed shapes.

Pose: Z = slot B floor height (lift), Y = extractor travel (0 = home, 175 = finger at a seated
caddy's notch), fingers = {"A": "parked"|"engaged", "B": ...}. Frame as in lib/robot_dims.py.
"""

import os

from cadgen import build123d as bd
from cadgen import read_step, srgb

from lib import vendor
from lib.dims import DOCK_STOP_Y, KW11, KW11_PRESS
from lib.extrusion import vslot
from lib.prims import box, cyl_z
from lib.robot_dims import (AXLE_Y, AXLE_Z, BASE_FRONT_Y, BASE_REAR_Y, BATTERY, BUCK_SIZE, BUCKS, CAM_BOARD, CAM_DZ,
                            CAM_LENS, CASTER, CASTER_FRONT, CASTER_FRONT_GAP, CASTER_REAR, COUPLER_Z, CROSS_Y, DECK_Z,
                            DRIVE_MOTOR_X, ESTOP_XY, FINGER_DZ, FINGER_X, KFL08, MAST_X,
                            NUT_BLOCK, NUT_BLOCK_DZ, MAST_Y, MAST_Z, NOSE_Z,
                            PCB_XY, PCB_Z, PI_XY, RAIL_X, RAIL_Z, SCREW_XY, SCREW_Z, SERVO, SERVO_FACE_DY, VWHEEL,
                            Y_NOTCH_HOME, YRAIL_DZ, YRAIL_X, YRAIL_Y, YWHEEL_DY,
                            YWHEEL_DZ, YWHEEL_SEAT_X, ZMOTOR_Z, ZWHEEL_DZ, ZWHEEL_SEAT_Y, ZWHEEL_X,
                            BELT_DZ, BELT_STRAND_X, BELT_X, IDLER_Y, PULLEY_CORE_D, PULLEY_FLANGE_D, PULLEY_Y,
                            YMOTOR_DZ, ECC_OFFSET, WHEEL_STACK, NOSE_SWITCH_X, SLOT_A_DZ, YCARRIAGE_DY, YFRAME_DZ, Z_HOME)
from robot.battery_box import battery_box
from robot.belt_clamp import belt_clamp
from robot.caster_spacer import caster_spacer_front, caster_spacer_rear
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
NUT_STEP = os.path.join(HERE, "..", "..", "..", "docs", "3d-models", "P05_anti-backlash-nut-block_openbuilds.step")
MODELS = os.path.join(HERE, "..", "..", "..", "docs", "3d-models")
WHEEL_STEPS = {"wheel": "P04_mini-v-wheel_delrin-assembly_openbuilds.step", "ecc": "P04_mini-eccentric-spacer-6mm_openbuilds.step",
               "spacer": "P04_spacer-6mm_openbuilds.step", "shim": "P04_precision-shim-8x5x1_openbuilds.step"}
PCB_STEP = os.path.join(HERE, "..", "..", "..", "pcb", "motion-board", "fab", "rbg3-motion.step")
PI_STEP = os.path.join(HERE, "..", "..", "..", "docs", "3d-models", "P12_raspberry-pi-3b.step")
PRINTED = srgb("#E8E4DA")
ACCENT = srgb("#E07A1F")

# Extrusion cut list (mm), used by the mass/packing checks.
M5_BORE = 5.0
EXTRUSIONS = {"2020": [300.0, 300.0, 110.0, 110.0, 110.0, YRAIL_Y[1] - YRAIL_Y[0]], "2040": [MAST_Z[1] - MAST_Z[0]]}


def wheel_stack(axle, d, p, seat, eccentric, label):
    """Mini V-wheel on its axle (OpenBuilds STEPs): 6 mm spacer (eccentric or plain) on the plate seat, 1 mm shim, wheel.
    axle: a point on the axle; d: unit vector plate -> wheel along the axle; p: unit vector square to the preload direction
    (the eccentric's offset); seat: plate seat coordinate along the axle."""
    d, p = bd.Vector(*d), bd.Vector(*p)
    a = bd.Vector(*axle)
    k = [abs(c) for c in d.to_tuple()].index(1.0)                       # axle axis index
    s = bd.Vector(*[seat if i == k else c for i, c in enumerate(a.to_tuple())])   # axle point on the seat face
    x = d.cross(p)
    if eccentric:                                                        # STEP: axis +y (hex toward +y), flange face y -1,
        frame = bd.Plane(origin=s + d * 1.0 - p * ECC_OFFSET, x_dir=x, z_dir=p)   # bore 0.7 toward +z of the boss
        sp = bd.Location(frame) * read_step(os.path.join(MODELS, WHEEL_STEPS["ecc"]))
    else:                                                                # STEP: axis +z, z 0..6
        sp = bd.Location(bd.Plane(origin=s, x_dir=p, z_dir=d)) * read_step(os.path.join(MODELS, WHEEL_STEPS["spacer"]))
    shim = bd.Location(bd.Plane(origin=s + d * 6.0, x_dir=x, z_dir=p)) * read_step(os.path.join(MODELS, WHEEL_STEPS["shim"]))
    w = VWHEEL["w"]
    wheel = bd.Location(bd.Plane(origin=s + d * (WHEEL_STACK + w / 2), x_dir=d, z_dir=p)) * \
        read_step(os.path.join(MODELS, WHEEL_STEPS["wheel"]))
    tag = label.split(":")[1]
    return [_p(wheel, label, vendor.STEEL), _p(sp, f"spacer:{tag}", vendor.STEEL), _p(shim, f"shim:{tag}", vendor.STEEL)]


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
    rear_spacer = caster_spacer_rear()
    for i, (x, y) in enumerate(CASTER_REAR):
        parts.append(vendor.ball_caster(x, y, 0.0, CASTER["h"], f"caster:rear_{i}"))   # long side along the rail
        parts.append(_p(bd.Pos(x - CASTER_REAR[1][0], 0, 0) * rear_spacer, f"caster_spacer_rear:{i}"))
    cx, cy = CASTER_FRONT
    parts.append(vendor.ball_caster(cx, cy, CASTER_FRONT_GAP, CASTER["h"], "caster:front_antitip", long_axis="x"))
    parts.append(_p(caster_spacer_front(), "caster_spacer_front"))
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
    # STEP: board x -42.5..42.5 (USB/Ethernet at +x), z -24.5..31.5 (HDMI edge +z, GPIO -z), bottom face y 0, parts +y
    pi = bd.Pos(PI_XY[0] + 42.5, PI_XY[1] + 31.5, PCB_Z) * bd.Rot(90, 0, 0) * read_step(PI_STEP)
    parts.append(_p(pi, "raspberry_pi_3", vendor.GREEN))
    parts.append(_p(battery_box(), "battery_box"))
    bx0, bx1, by0, by1, bz0, bz1 = BATTERY
    parts.append(vendor.board(bx0 + 1, by0 + 1, bz0 + 3, bx1 - bx0 - 2, by1 - by0 - 2, 42.0, "battery_4s1p",
                              srgb("#3B82F6")))
    ex, ey = ESTOP_XY
    zt = MAST_Z[1] + 6.0                         # on the mast top plate
    parts.append(vendor.board(ex - 20, ey - 20, zt, 40.0, 40.0, 40.0, "estop_box", srgb("#FACC15")))
    parts.append(_p(cyl_z(40.0, ex, ey, zt + 40.0, zt + 60.0), "estop_button", srgb("#DC2626")))
    for name, (x, y) in BUCKS.items():
        bw, bl, bh = BUCK_SIZE[name]
        parts.append(vendor.board(x, y, DECK_Z[1], bw, bl, bh, f"buck:{name}", srgb("#7C3AED")))
    for label, hole, T, L, H, lifts in switch_frames():
        if not lifts:
            parts.append(kw11_part(label, hole, T, L, H))
    return parts


KW11_STEP = os.path.join(MODELS, "P10_kw11-3z-hinge-lever.step")
# KW11-3Z STEP frame: x = thickness, y = length (lever hinge at -y, free end at +y), z = pin edge (-z) -> lever (+z);
# the two M2 holes are centred at y -5.1, z -0.1 (0.4 from the body centre toward the hinge, 2.8 above the pin edge).
KW11_STEP_HOLES = (0.0, -5.1, -0.1)


def switch_frames():
    """KW11-3Z switches where the printed mounts hold them: (label, hole centre, T, L, H, moves_with_lift) with
    T = thickness axis, L = hinge -> free lever end, H = pin edge -> lever edge (T x L = H)."""
    from robot import nose, rail_bracket, tray_stack, z_carriage
    l, h, t, up = KW11["l"], KW11["h"], KW11["t"], KW11["hole_up"]
    out = []
    bx = NOSE_SWITCH_X + nose.SWITCH_SLOT[0] / 2                       # nose: body on the bracket's -x face, lever +y
    lever_y = DOCK_STOP_Y + nose.SWITCH_REACH - KW11["lever"]
    out.append(("kw11:nose", (bx - t / 2, lever_y - h + up, nose.SWITCH_Z), (1, 0, 0), (0, 0, -1), (0, 1, 0), False))
    sx, sy = SCREW_XY                                                  # Z home: on the hanger, lever down, hinge at +y
    hx0 = sx - z_carriage.FIN_GAP - z_carriage.FIN_T - z_carriage.ZSW_HANGER_T
    lever_z = z_carriage.ZSW_MOUNT_TOP - KW11_PRESS + KW11["lever"] - Z_HOME
    out.append(("kw11:z_home", (hx0 - t / 2, sum(z_carriage.ZSW_Y) / 2, lever_z + h - up), (1, 0, 0), (0, -1, 0),
                (0, 0, -1), True))
    hy = tray_stack.SW_FRONT_Y - h + up                                # tray slot presence: flat, lever +y
    for slot, dz in (("B", 0.0), ("A", SLOT_A_DZ)):
        out.append((f"kw11:slot_{slot}", (tray_stack.SW_X, hy, dz + tray_stack.SW_DZ), (0, 0, 1), (1, 0, 0), (0, 1, 0),
                    True))
    front = Y_NOTCH_HOME + YCARRIAGE_DY[0] + KW11_PRESS - KW11["lever"]   # Y home: flat on the post, free end +x
    out.append(("kw11:y_home", (rail_bracket.YSW_X1 - l / 2, front - h + up, YFRAME_DZ[1] - t / 2), (0, 0, 1),
                (1, 0, 0), (0, 1, 0), True))
    return out


def kw11_part(label, hole, T, L, H, dz=0.0):
    T, L, H = bd.Vector(*T), bd.Vector(*L), bd.Vector(*H)
    hx, hy, hz = KW11_STEP_HOLES
    origin = bd.Vector(*hole) + bd.Vector(0, 0, dz) - T * hx - L * hy - H * hz
    return _p(bd.Location(bd.Plane(origin=origin, x_dir=T, z_dir=H)) * read_step(KW11_STEP), label, vendor.BLACK)


def lift_parts(Z):
    at = bd.Pos(0, 0, Z)
    parts = [_p(at * z_carriage(), "z_carriage"), _p(at * tray_stack(), "tray_stack", ACCENT),
             _p(at * rail_bracket(), "rail_bracket")]
    sx, sy = SCREW_XY                                          # anti-backlash nut block (P05) on the carriage fin
    zc = Z + (NUT_BLOCK_DZ[0] + NUT_BLOCK_DZ[1]) / 2           # STEP: x across (preload hole +x), y along the screw
    # (body end -y, mounting holes at y -6.5, slit and lip toward +y), z -12..0. Turned 180° about its x so the body
    # end is up against the shelf and the preload screw stays on +y.
    nut = bd.Location(bd.Plane(origin=(sx - NUT_BLOCK["t"] / 2, sy, zc), x_dir=(0, 1, 0), z_dir=(1, 0, 0))) * \
        bd.Rot(180, 0, 0) * read_step(NUT_STEP)
    parts.append(_p(nut, "nut_block_tr8", srgb("#1F2937")))
    yc = (MAST_Y[0] + MAST_Y[1]) / 2                         # mast side groove centre
    for s in (-1, 1):
        for dz in ZWHEEL_DZ:
            parts += wheel_stack((s * ZWHEEL_X, yc, Z + dz), (0, -1, 0), (0, 0, 1), ZWHEEL_SEAT_Y, s > 0,
                                 f"vwheel:z{'LR'[s > 0]}{dz:.0f}")             # eccentric spacers on the +x pair
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
    cb, py, zc = CAM_BOARD, ly - 1.0, Z + CAM_DZ                 # PCB front face as in tray_stack.CAM_PCB_Y
    zb = zc - cb["lens_up"]
    cam = box(lx - cb["w"] / 2, lx + cb["w"] / 2, py - cb["t"], py, zb, zb + cb["h"])
    hh = cb["holder"] / 2
    cam += box(lx - hh, lx + hh, py, py + cb["holder_l"], zc - hh, zc + hh)
    cam += bd.Pos(lx, py, zc) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        cb["barrel_d"] / 2, cb["lens_l"], align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    cam += box(lx - 10.5, lx + 10.5, py - cb["t"] - cb["back"], py - cb["t"], zb, zb + 6.0)   # connector
    parts.append(_p(cam, "camera_module_3_wide", vendor.GREEN))
    for label, hole, T, L, H, lifts in switch_frames():
        if lifts:
            parts.append(kw11_part(label, hole, T, L, H, Z))
    return parts


def extractor_parts(Z, Y, fingers):
    pivot_y = Y_NOTCH_HOME + Y
    parts = [_p(bd.Pos(0, pivot_y, Z) * y_carriage(), "y_carriage"), _p(bd.Pos(0, pivot_y, Z) * belt_clamp(), "belt_clamp")]
    xc = (YRAIL_X[0] + YRAIL_X[1]) / 2                       # rail top/bottom groove centre
    for dy in YWHEEL_DY:
        for dz in YWHEEL_DZ:
            parts += wheel_stack((xc, pivot_y + dy, Z + dz), (-1, 0, 0), (0, 1, 0), YWHEEL_SEAT_X, dz == YWHEEL_DZ[0],
                                 f"vwheel:y{dy:.0f}{dz:.0f}")                   # eccentric spacers on the lower pair
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
