"""Robot fasteners and heat-set inserts, placed at their holes. Screws, nuts and T-nuts are step.parts models
(cad/vendor/fasteners); heat-set inserts are plain sleeves at the seller's size. M2 self-tapping screws are shown as
M2 socket heads (the pan head is lower).

Each Joint says what the head bears on, how far it is to the nut / thread (grip) and what the screw threads into, so
checks/fastener_check.py can test the holes (a screw that hits a printed part it is not threaded into is a clash),
the seating and the thread engagement. Coordinates as in lib/robot_dims.py: base joints in the robot frame, lift
joints at Z = 0, extractor joints at Z = 0 with the finger pivot at y = 0, finger joints in the finger's own frame.
"""

import os
from dataclasses import dataclass

from cadgen import build123d as bd
from cadgen import read_step, srgb

from lib.dims import KW11, KW11_PRESS
from lib.robot_dims import (AXLE_Y, AXLE_Z, BATTERY, BATTERY_DECK_HOLES, BELT_DZ, BELT_STRAND_X, BELT_X, CASTER, CASTER_FRONT,
                            CASTER_FRONT_GAP, CASTER_REAR, CROSS_Y, DECK_Z, DRIVE_INSERT_X, DRIVE_INSERT_Y,
                            DRIVE_PLATE_X, ESTOP_XY, FINGER_DZ, FINGER_T, FINGER_X, IDLER_BRACKET_Y, IDLER_Y,
                            KFL08, MAST_Y, MAST_Z, NOSE_SWITCH_X, NUT_BLOCK, NUT_BLOCK_DZ, PCB_DECK_HOLES, PCB_XY,
                            PCB_Z, PI_DECK_HOLES, PI_XY, PULLEY_Y, RAIL_X, RAIL_Z, SCREW_XY, SERVO, SERVO_FACE_DY,
                            SLOT_A_DZ, TRAY_BOLTS, VWHEEL, WHEEL_STACK, Y_NOTCH_HOME, YBRACKET_PLATE_Y,
                            YBRACKET_X, YCARRIAGE_DY, YFRAME_DZ, YMOTOR_PLATE_DZ, YPLATE_X, YRAIL_DZ, YRAIL_X,
                            YRAIL_Y, YWHEEL_DY, YWHEEL_DZ, ZMOTOR_Z, ZMOUNT_T, ZPLATE_Y, ZWHEEL_DZ, ZWHEEL_SEAT_Y,
                            ZWHEEL_X, Z_HOME, DOCK_STOP_Y, BASE_FRONT_Y, NOSE_Z, RAIL_BRACKET_BOLT_X)

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "..", "vendor", "fasteners")
STEEL = srgb("#C3C8CE")
BRASS = srgb("#C9A227")

SLOT_LIP = 1.8        # V-slot face -> T-nut (the slot lip)
SLOT_DEPTH = 6.0      # V-slot face -> core: a screw tip past this bottoms out in the slot
NUT_H = {("hex", 3): 2.4, ("hex", 4): 3.2, ("hex", 5): 4.0, ("nylock", 3): 2.4, ("nylock", 5): 4.0, ("tnut", 5): 4.0}
NUT_ID = {("hex", 3): "iso4032_hex_nut_m3", ("hex", 4): "iso4032_hex_nut_m4", ("hex", 5): "iso4032_hex_nut_m5",
          ("nylock", 3): "nylon_locknut_m3_simple", ("nylock", 5): "nylon_locknut_m5_simple",
          ("tnut", 5): "extrusion_slot6_drop_in_tnut_m5_simple"}
INSERT = {3: (4.2, 4.0), 5: (7.0, 8.0)}       # heat-set insert OD, length: 3Din M3 x 4, M5 x 8 (P11)


@dataclass
class Joint:
    name: str
    group: str            # "base", "lift", "ext" or "finger:A" / "finger:B"
    head: str             # "bh" ISO 7380 button, "cs" countersunk (`at` = head top, flush), "sh" ISO 4762 socket head
    #                       (also stands in for the M2 / M2.5 self-tapping pan heads)
    d: float
    L: float
    at: tuple             # head bearing face centre
    axis: tuple           # unit vector, head -> tip
    seat: str             # label prefix of what the head bears on ("" = not modeled)
    grip: float           # head face -> nut face / face of the part it threads into
    end: str              # "nut", "nylock", "tnut", "insert", "tap" (self-tapping into a printed pilot), "thread"
    target: str = ""      # label prefix threaded into (the extrusion for a T-nut)
    depth: float = None   # usable depth past the entry face (pilot / tapped hole); None = through
    through: tuple = ()   # bought parts the screw passes that are modeled without their holes
    nut_at: float = None  # nut in a pocket: head face -> nut near face (default: at the grip)

    @property
    def spec(self):
        size = {2.5: "M2.5"}.get(self.d, f"M{self.d:g}")
        return f"{size} x {self.L:g} {dict(bh='button', cs='countersunk', sh='socket/self-tap')[self.head]}"


def _screw_id(j):
    if j.head == "bh":
        return f"button_head_screw_m5_l{int(j.L):04d}_simple"
    if j.head == "cs":
        return f"countersunk_socket_screw_m5_l{int(j.L):04d}_simple"
    ds = {2.5: "2p5"}.get(j.d, f"{j.d:g}")
    return f"iso4762_socket_head_cap_screw_m{ds}x{j.L:g}"


_cache = {}


def _model(model_id):
    if model_id not in _cache:
        _cache[model_id] = read_step(os.path.join(LIB, model_id + ".step"))
    return _cache[model_id]


def _frame(origin, z_dir):
    z = bd.Vector(*z_dir)
    x = bd.Vector(1, 0, 0) if abs(z.X) < 0.9 else bd.Vector(0, 1, 0)
    return bd.Location(bd.Plane(origin=origin, x_dir=x - z * x.dot(z), z_dir=z))


def _tag(shape, label, color):
    shape.label = label
    shape.color = color
    return shape


def pieces(j):
    """Shapes of one joint in its group frame: [(kind, shape)]: the screw, and its nut / T-nut / insert."""
    a = bd.Vector(*j.axis)
    p = bd.Vector(*j.at)
    out = [("screw", _tag(_frame(p, -a) * _model(_screw_id(j)), f"fx:{j.name}/screw", STEEL))]
    if j.end in ("nut", "nylock", "tnut"):
        kind = "hex" if j.end == "nut" else j.end
        off = j.grip + (SLOT_LIP if j.end == "tnut" else 0.0) if j.nut_at is None else j.nut_at
        out.append(("nut", _tag(_frame(p + a * off, a) * _model(NUT_ID[(kind, int(j.d))]), f"fx:{j.name}/nut", STEEL)))
    elif j.end == "insert":
        od, ln = INSERT[int(j.d)]
        sleeve = bd.Cylinder(od / 2, ln, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
        sleeve -= bd.Cylinder(j.d / 2, ln, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
        out.append(("insert", _tag(_frame(p + a * j.grip, a) * sleeve, f"fx:{j.name}/insert", BRASS)))
    return out


def engagement(j):
    """(ok, text): thread engagement and bottoming from the joint's numbers."""
    tip = j.L
    if j.end in ("nut", "nylock"):
        far = (j.grip if j.nut_at is None else j.nut_at) + NUT_H[("hex" if j.end == "nut" else j.end, int(j.d))]
        return tip >= far - 0.3, f"tip {tip - far:+.1f} mm past the nut"
    if j.end == "tnut":
        face = j.grip + SLOT_LIP
        eng = min(tip, face + NUT_H[("tnut", 5)]) - face
        ok = eng >= 3.0 and tip <= j.grip + SLOT_DEPTH
        return ok, f"{eng:.1f} mm in the T-nut, tip {j.grip + SLOT_DEPTH - tip:+.1f} mm short of the slot core"
    od, ln = INSERT.get(int(j.d), (0, 0))
    eng = tip - j.grip
    if j.end == "insert":
        ok = eng >= 0.6 * ln and (j.depth is None or eng <= j.depth)
        return ok, f"{min(eng, ln):.1f} of {ln:g} mm insert, pilot {j.depth}: tip {eng:.1f} deep"
    need = 1.5 * j.d if j.end == "tap" else 1.0 * j.d
    ok = eng >= need and (j.depth is None or eng <= j.depth + 0.05)
    room = "through" if j.depth is None else f"of {j.depth:g}"
    return ok, f"{eng:.1f} mm thread ({room}; needs >= {need:.1f})"


# ---- Joint tables -------------------------------------------------------------------------------------------------
X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
NX, NY, NZ = (-1, 0, 0), (0, -1, 0), (0, 0, -1)


def base_joints():
    from robot import battery_box, caster_spacer, deck, drive_bracket, mast_collar, mast_top_plate, nose, z_motor_mount
    J = []
    z_deck = DECK_Z[1]
    deck_t = DECK_Z[1] - DECK_Z[0]
    xr = (RAIL_X[0] + RAIL_X[1]) / 2
    for s, side in ((-1, "left"), (1, "right")):
        for i, y in enumerate(deck.RAIL_HOLE_Y[s]):
            J.append(Joint(f"deck_rail_{side}{i}", "base", "bh", 5, 10, (s * xr, y, z_deck), NZ, "deck", deck_t,
                           "tnut", f"rail_2020:{side}"))
        for i, y in enumerate(DRIVE_INSERT_Y):
            J.append(Joint(f"deck_drive_{side}{i}", "base", "sh", 3, 8, (s * DRIVE_INSERT_X, y, z_deck), NZ, "deck",
                           deck_t, "insert", f"drive_bracket:{side}", drive_bracket.INSERT_DEPTH))
        y0, y1 = drive_bracket.Y_SPAN
        for i, y in enumerate((y0 + drive_bracket.WEB_T / 2, y1 - drive_bracket.WEB_T / 2)):
            J.append(Joint(f"drive_rail_{side}{i}", "base", "bh", 5, 10, (s * (RAIL_X[1] + 4.0), y, sum(RAIL_Z) / 2),
                           (-s, 0, 0), f"drive_bracket:{side}", 4.0, "tnut", f"rail_2020:{side}"))
        px = DRIVE_PLATE_X[1]
        for i, (dy, dz) in enumerate(((-15.5, -15.5), (-15.5, 15.5), (15.5, -15.5), (15.5, 15.5))):
            J.append(Joint(f"drive_motor_{side}{i}", "base", "sh", 3, 8, (s * px, AXLE_Y + dy, AXLE_Z + dz),
                           (-s, 0, 0), f"drive_bracket:{side}", DRIVE_PLATE_X[1] - DRIVE_PLATE_X[0], "thread",
                           f"nema17:drive_{side}", 4.5))
    # Mast collar: flange -> mast cross member, side bolts and rear gusset -> mast slots.
    ym = sum(CROSS_Y["mast"]) / 2
    for i, x in enumerate((32.0, 46.0)):
        J.append(Joint(f"collar_cross{i}", "base", "bh", 5, 16, (x, ym, z_deck + mast_collar.FLANGE_T), NZ,
                       "mast_collar", mast_collar.FLANGE_T + deck_t, "tnut", "cross_2020:mast"))
    w = mast_collar.WALL
    for s in (-1, 1):
        J.append(Joint(f"collar_side{'LR'[s > 0]}", "base", "bh", 5, 12,
                       (s * (20.0 + w), sum(MAST_Y) / 2, z_deck + mast_collar.HEIGHT / 2), (-s, 0, 0),
                       "mast_collar", w, "tnut", "mast_2040"))
    for x in (-10.0, 10.0):
        for z in (110.0, 150.0):
            J.append(Joint(f"collar_gusset{x:+.0f}_{z:.0f}", "base", "bh", 5, 12,
                           (x, MAST_Y[0] - mast_collar.GUSSET_T, z), Y, "mast_collar", mast_collar.GUSSET_T,
                           "tnut", "mast_2040"))
    # Mast top plate: tab -> mast front slots, KFL08 (M4 + nut), E-stop box (inserts).
    ztop = MAST_Z[1]
    tab = mast_top_plate.TAB
    for x in mast_top_plate.SLOT_X:
        J.append(Joint(f"top_tab{x:+.0f}", "base", "bh", 5, 10, (x, tab[1], ztop - mast_top_plate.TAB_DROP / 2), NY,
                       "mast_top_plate", tab[1] - tab[0], "tnut", "mast_2040"))
    sx, sy = SCREW_XY
    for i, dy in enumerate((-KFL08["pitch"] / 2, KFL08["pitch"] / 2)):
        J.append(Joint(f"kfl08_{i}", "base", "sh", 4, 16, (sx, sy + dy, ztop + mast_top_plate.T), NZ,
                       "mast_top_plate", mast_top_plate.T + KFL08["flange_t"], "nut", through=("kfl08",)))
    ex, ey = ESTOP_XY
    for i, dx in enumerate((-mast_top_plate.ESTOP_HOLE_DX, mast_top_plate.ESTOP_HOLE_DX)):
        floor = 2.0                                                                  # box floor (assumed)
        J.append(Joint(f"estop_{i}", "base", "sh", 3, 6, (ex + dx, ey, ztop + mast_top_plate.T + floor), NZ,
                       "estop_box", floor, "insert", "mast_top_plate", mast_top_plate.INSERT_DEPTH,
                       through=("estop_box",)))
    # Z motor: mount plate -> motor, feet -> deck.
    zp = ZMOTOR_Z[1] + ZMOUNT_T
    for i, (dx, dy) in enumerate(((-15.5, -15.5), (-15.5, 15.5), (15.5, -15.5), (15.5, 15.5))):
        J.append(Joint(f"zmotor_{i}", "base", "sh", 3, 8, (sx + dx, sy + dy, zp), NZ, "z_motor_mount", ZMOUNT_T,
                       "thread", "nema17:z", 4.5))
    xl = sx - z_motor_mount.NEMA_HALF - 0.5 - z_motor_mount.WALL_T - z_motor_mount.FOOT[0] / 2
    xr_ = sx + z_motor_mount.NEMA_HALF + 0.5 + z_motor_mount.WALL_T + z_motor_mount.FOOT[0] / 2
    fy = sy + sum(z_motor_mount.FOOT[1]) / 2
    for i, x in enumerate((xl, xr_)):
        J.append(Joint(f"zmount_deck{i}", "base", "sh", 3, 12, (x, fy, z_deck + z_motor_mount.FOOT[2]), NZ,
                       "z_motor_mount", z_motor_mount.FOOT[2] + deck_t, "nut"))
    # Trays and battery box -> deck (M3 + nut under the deck).
    for name, holes, t in (("pcb_tray", PCB_DECK_HOLES, 3.0), ("pi_tray", PI_DECK_HOLES, 3.0),
                           ("battery_box", BATTERY_DECK_HOLES, battery_box.TAB[2])):
        part = {"pcb_tray": "electronics_tray"}.get(name, name)
        for i, (x, y) in enumerate(holes):
            J.append(Joint(f"{name}_deck{i}", "base", "sh", 3, 12, (x, y, z_deck + t), NZ,
                           part, t + deck_t, "nut"))
    # Motion board (inserts in the tray standoffs) and Pi (M2.5 self-tapping into the tray pilots).
    x, y = PCB_XY
    for i, (hx, hy) in enumerate(((x + 3.5, y + 3.5), (x + 96.5, y + 3.5), (x + 3.5, y + 96.5), (x + 96.5, y + 96.5))):
        J.append(Joint(f"pcb_{i}", "base", "sh", 3, 6, (hx, hy, PCB_Z + 1.6), NZ, "motion_board", 1.6, "insert",
                       "electronics_tray", 5.0, through=("motion_board",)))
    x, y = PI_XY
    for i, (hx, hy) in enumerate(((x + 3.5, y + 3.5), (x + 61.5, y + 3.5), (x + 3.5, y + 52.5), (x + 61.5, y + 52.5))):
        J.append(Joint(f"pi_{i}", "base", "sh", 2.5, 6, (hx, hy, PCB_Z + 1.4), NZ, "raspberry_pi_3", 1.4, "tap",
                       "pi_tray", 6.0, through=("raspberry_pi_3",)))
    # Nose: rear wall -> front cross member; dock switch (M2 self-tapping from -x into the bracket).
    for x in (-40.0, 40.0):
        J.append(Joint(f"nose_cross{x:+.0f}", "base", "bh", 5, 10, (x, BASE_FRONT_Y + nose.WALL, sum(RAIL_Z) / 2), NY,
                       "nose", nose.WALL, "tnut", "cross_2020:front"))
    bx = NOSE_SWITCH_X + nose.SWITCH_SLOT[0] / 2
    hy = DOCK_STOP_Y + nose.SWITCH_REACH - KW11["lever"] - KW11["h"] + KW11["hole_up"]
    for dz in (-KW11["hole_dx"], KW11["hole_dx"]):
        J.append(Joint(f"nose_switch{dz:+.0f}", "base", "sh", 2, 10, (bx - KW11["t"], hy, nose.SWITCH_Z + dz), X,
                       "kw11:nose", KW11["t"], "tap", "nose", None, through=("kw11:nose",)))
    # Casters: front under the nose (M3 through caster, spacer and floor, nuts inside the nose); rear spacers
    # (M5 up into the rail's bottom slot, caster M3 into nuts in the spacer's side pockets).
    cx, cy = CASTER_FRONT
    top = CASTER_FRONT_GAP + CASTER["h"]
    stack = 3.0 + (NOSE_Z[0] - top) + nose.WALL
    for s in (-1, 1):
        J.append(Joint(f"caster_front{'LR'[s > 0]}", "base", "sh", 3, 16, (cx + s * CASTER["pitch"] / 2, cy, top - 3.0),
                       Z, "caster:front", stack, "nut"))
    for i, (x, y) in enumerate(CASTER_REAR):
        side = ("left", "right")[x > 0]
        z1 = RAIL_Z[0]
        for dy in (-8.0, 8.0):
            J.append(Joint(f"caster_rear{i}_rail{dy:+.0f}", "base", "bh", 5, 12, (x, y + dy, z1 - caster_spacer.M5_FLANGE),
                           Z, f"caster_spacer_rear:{i}", caster_spacer.M5_FLANGE, "tnut", f"rail_2020:{side}"))
        for s in (-1, 1):
            J.append(Joint(f"caster_rear{i}_caster{'FR'[s > 0]}", "base", "sh", 3, 12,
                           (x, y + s * CASTER["pitch"] / 2, CASTER["h"] - 3.0), Z, f"caster:rear_{i}", 3.0, "nut",
                           nut_at=3.0 + caster_spacer.NUT_Z))
    return J


def lift_joints():
    from robot import rail_bracket, tray_stack, y_idler_bracket, z_carriage
    J = []
    yb, yf = ZPLATE_Y
    for x, z in TRAY_BOLTS:
        if x == RAIL_BRACKET_BOLT_X:
            y0 = YBRACKET_PLATE_Y[0]
            J.append(Joint(f"tray_bolt{x:+.0f}_{z:+.0f}", "lift", "bh", 5, 25, (x, y0, z), Y, "rail_bracket", yf - y0,
                           "insert", "tray_stack", tray_stack.M5_INSERT_DEPTH))
        else:
            J.append(Joint(f"tray_bolt{x:+.0f}_{z:+.0f}", "lift", "bh", 5, 16, (x, yb, z), Y, "z_carriage", yf - yb,
                           "insert", "tray_stack", tray_stack.M5_INSERT_DEPTH))
    head_y = ZWHEEL_SEAT_Y - WHEEL_STACK - VWHEEL["w"]
    for s in (-1, 1):
        for dz in ZWHEEL_DZ:
            wheel = f"vwheel:z{'LR'[s > 0]}{dz:.0f}"
            J.append(Joint(f"zwheel_{'LR'[s > 0]}{dz:.0f}", "lift", "bh", 5, 30, (s * ZWHEEL_X, head_y, dz), Y, wheel,
                           yf - head_y, "nylock", through=(wheel,)))
    sx, sy = SCREW_XY
    fx0 = sx - z_carriage.FIN_GAP - z_carriage.FIN_T
    for dy in (-NUT_BLOCK["pitch"] / 2, NUT_BLOCK["pitch"] / 2):
        J.append(Joint(f"nut_block{dy:+.0f}", "lift", "bh", 5, 20, (fx0, sy + dy, z_carriage.MOUNT_Z), X, "z_carriage",
                       z_carriage.FIN_T, "nylock", through=("nut_block_tr8",),
                       nut_at=z_carriage.FIN_T + NUT_BLOCK["t"] - 5.0))         # nut at the hex pocket floor (5 deep)
    hx0 = fx0 - z_carriage.ZSW_HANGER_T
    lever_z = z_carriage.ZSW_MOUNT_TOP - KW11_PRESS + KW11["lever"] - Z_HOME
    yc = sum(z_carriage.ZSW_Y) / 2
    for dy in (-KW11["hole_dx"], KW11["hole_dx"]):
        J.append(Joint(f"z_switch{dy:+.0f}", "lift", "sh", 2, 10, (hx0 - KW11["t"], yc + dy, lever_z + KW11["h"] -
                       KW11["hole_up"]), X, "kw11:z_home", KW11["t"], "tap", "z_carriage", z_carriage.ZSW_HANGER_T + 0.6,
                       through=("kw11:z_home",)))
    hy = tray_stack.SW_FRONT_Y - KW11["h"] + KW11["hole_up"]
    for slot, dz, ax in (("B", 0.0, Z), ("A", SLOT_A_DZ, NZ)):
        zc = dz + tray_stack.SW_DZ
        face = zc - ax[2] * KW11["t"] / 2
        for dx in (-KW11["hole_dx"], KW11["hole_dx"]):
            J.append(Joint(f"slot{slot}_switch{dx:+.0f}", "lift", "sh", 2, 10, (tray_stack.SW_X + dx, hy, face), ax,
                           f"kw11:slot_{slot}", KW11["t"] + tray_stack.SW_FIT, "tap", "tray_stack", 6.0,
                           through=(f"kw11:slot_{slot}",)))
    zc = sum(YRAIL_DZ) / 2
    for y in (YRAIL_Y[0] + 12.0, YRAIL_Y[0] + 45.0):
        cb = rail_bracket.STRIP_CBORE[1]
        J.append(Joint(f"rail_bracket_rail{y:.0f}", "lift", "bh", 5, 16, (YBRACKET_X[0] + cb, y, zc), X, "rail_bracket",
                       YBRACKET_X[1] - YBRACKET_X[0] - cb, "tnut", "y_rail_2020"))
    pz0, pz1 = YMOTOR_PLATE_DZ
    for i, (dx, dy) in enumerate(((-15.5, -15.5), (-15.5, 15.5), (15.5, -15.5), (15.5, 15.5))):
        J.append(Joint(f"ymotor_{i}", "lift", "sh", 3, 8, (BELT_X + dx, PULLEY_Y + dy, pz0), Z, "rail_bracket",
                       pz1 - pz0, "thread", "nema17:y", 4.5))
    xb1 = rail_bracket.YSW_X1
    front = Y_NOTCH_HOME + YCARRIAGE_DY[0] + KW11_PRESS - KW11["lever"]
    for dx in (-KW11["hole_dx"], KW11["hole_dx"]):
        J.append(Joint(f"y_switch{dx:+.0f}", "lift", "sh", 2, 10, (xb1 - KW11["l"] / 2 + dx, front - KW11["h"] +
                       KW11["hole_up"], YFRAME_DZ[1]), NZ, "kw11:y_home", KW11["t"], "tap", "rail_bracket", 8.0,
                       through=("kw11:y_home",)))
    x0 = YRAIL_X[1] + y_idler_bracket.PLATE_T
    J.append(Joint("idler_bracket_rail", "lift", "cs", 5, 10, (x0, sum(IDLER_BRACKET_Y) / 2, zc), NX, "y_idler_bracket",
                   y_idler_bracket.PLATE_T, "tnut", "y_rail_2020"))
    z_lo = BELT_DZ[0] - 1.0 - y_idler_bracket.GAP - y_idler_bracket.ARM_T
    z_hi = BELT_DZ[1] + 1.0 + y_idler_bracket.GAP + y_idler_bracket.ARM_T
    J.append(Joint("idler_axle", "lift", "bh", 5, 25, (BELT_X, IDLER_Y, z_hi), NZ, "y_idler_bracket", z_hi - z_lo,
                   "nylock", through=("gt2_idler",)))
    return J


def extractor_joints():
    from robot.belt_clamp import T as CLAMP_T
    from robot.y_carriage import CLAMP_DY, CLAMP_SCREW_DZ, LEDGE_DEPTH, SERVO_SHIM, ledge_spans
    J = []
    xc = sum(YRAIL_X) / 2
    for dy in YWHEEL_DY:
        for dz in YWHEEL_DZ:
            wheel = f"vwheel:y{dy:.0f}{dz:.0f}"
            x_head = xc - VWHEEL["w"] / 2
            J.append(Joint(f"ywheel_{dy:.0f}_{dz:.0f}", "ext", "bh", 5, 30, (x_head, dy, dz), X, wheel,
                           YPLATE_X[1] - x_head, "nylock", through=(wheel,)))
    jaw = BELT_STRAND_X[0][1] + CLAMP_T
    for z in CLAMP_SCREW_DZ:
        J.append(Joint(f"belt_clamp{z:.0f}", "ext", "sh", 3, 10, (jaw, sum(CLAMP_DY) / 2, z), NX, "belt_clamp",
                       jaw - YPLATE_X[1], "insert", "y_carriage", YPLATE_X[1] - YPLATE_X[0]))
    tab_back = SERVO_FACE_DY - SERVO["tab_drop"] - 2.5
    for slot, f in FINGER_DZ.items():
        for i, (z0, z1) in enumerate(ledge_spans(f)):
            J.append(Joint(f"servo_{slot}{i}", "ext", "sh", 2, 8, (FINGER_X, tab_back, (z0 + z1) / 2), Y, f"mg90s:{slot}",
                           2.5 + SERVO_SHIM, "tap", "y_carriage", LEDGE_DEPTH, through=(f"mg90s:{slot}",)))
    return J


def finger_joints(slot):
    from robot.finger import HORN_PILOT_DEPTH, HORN_SCREW_R
    arm = 1.5                                                    # horn arm plate between the screw head and the finger
    return [Joint(f"horn_{slot}{r:.0f}", f"finger:{slot}", "sh", 2, 6, (0.0, -FINGER_T / 2 - arm, r), Y, "", arm, "tap",
                  f"finger:{slot}", HORN_PILOT_DEPTH) for r in HORN_SCREW_R]


def all_joints():
    return base_joints() + lift_joints() + extractor_joints() + finger_joints("A") + finger_joints("B")


def placement(group, Z, Y, fingers):
    if group == "base":
        return bd.Location()
    if group == "lift":
        return bd.Location((0, 0, Z))
    pivot_y = Y_NOTCH_HOME + Y
    if group == "ext":
        return bd.Location((0, pivot_y, Z))
    slot = group.split(":")[1]
    angle = -90.0 if fingers.get(slot, "parked") == "engaged" else 0.0
    return bd.Location((FINGER_X, pivot_y, Z + FINGER_DZ[slot])) * bd.Location(bd.Rotation(0, angle, 0))


def fastener_parts(Z, Y=0.0, fingers=None, joints=None):
    """Placed fastener shapes for the pose: [(joint, kind, shape)]."""
    fingers = fingers or {}
    out = []
    for j in joints or all_joints():
        loc = placement(j.group, Z, Y, fingers)
        for kind, s in pieces(j):
            m = loc * s
            m.label, m.color = s.label, s.color
            out.append((j, kind, m))
    return out
