"""Simplified stand-ins for purchased parts (envelope-accurate, not detailed).

Used for fit, clearance, mass and packing checks. Swap for vendor STEP files (step.parts) when
detailing; masses are typical catalogue values.
"""

from cadgen import build123d as bd
from cadgen import srgb

from lib.prims import box, cyl_x, cyl_z

STEEL = srgb("#8C939B")
BLACK = srgb("#2B2F36")
BLUE = srgb("#2563EB")
GREEN = srgb("#1F7A4D")
RUBBER = srgb("#1F2328")

MASS_G = {"nema17": 280, "mg90s": 14, "kfl08": 45, "ball_caster": 35, "pi3": 45, "camera": 5,
          "leadscrew_350": 130, "coupler": 15, "kfl08": 45, "v_wheel": 12, "wheel_80": 60,
          "shaft_8x100": 40, "pulley_60t": 25, "pulley_20t": 8, "battery_4s": 200, "bms": 20,
          "motion_board": 130, "estop": 60, "buck": 25}


def _tag(shape, label, color):
    shape.label = label
    shape.color = color
    return shape


def nema17_x(x_face, y, z, direction, label, length=40.0):
    """NEMA17 with its shaft along x: body behind x_face, shaft pointing `direction` (+1/-1)."""
    x0, x1 = sorted((x_face, x_face - direction * length))
    body = box(x0, x1, y - 21.15, y + 21.15, z - 21.15, z + 21.15)
    sx0, sx1 = sorted((x_face, x_face + direction * 22.0))
    body += cyl_x(5.0, sx0, sx1, y, z)
    return _tag(body, label, BLACK)


def nema17_z(x, y, z_bottom, label, length=40.0, shaft_up=True):
    body = box(x - 21.15, x + 21.15, y - 21.15, y + 21.15, z_bottom, z_bottom + length)
    if shaft_up:
        body += cyl_z(5.0, x, y, z_bottom + length, z_bottom + length + 22.0)
    else:
        body += cyl_z(5.0, x, y, z_bottom - 22.0, z_bottom)
    return _tag(body, label, BLACK)


def gt2_wheel(x, y, z0, z1, core_d, flange_d, label, bore=5.0):
    """GT2 pulley or idler: toothed core across the belt band [z0, z1], flanges just outside it."""
    w = cyl_z(core_d, x, y, z0, z1) + cyl_z(flange_d, x, y, z0 - 1.0, z0) + cyl_z(flange_d, x, y, z1, z1 + 1.0)
    w -= cyl_z(bore, x, y, z0 - 1.1, z1 + 1.1)
    return _tag(w, label, STEEL)


def nema17_y(x, y_face, z, direction, label, length=40.0):
    y0, y1 = sorted((y_face, y_face - direction * length))
    body = box(x - 21.15, x + 21.15, y0, y1, z - 21.15, z + 21.15)
    return _tag(body, label, BLACK)


def mg90s_y(pivot_x, face_y, pivot_z, label, servo):
    """MG90S with its output face at face_y (shaft along +y), axis at (pivot_x, pivot_z), plus the horn hub.
    The case extends behind the face (-y) and upward from the shaft (shaft near the case's lower end)."""
    w, h, ln, off, tab = servo["wid"], servo["h"], servo["len"], servo["shaft_from_end"], servo["tab"]
    td = servo["tab_drop"]
    z0, z1 = pivot_z - off, pivot_z - off + ln
    body = box(pivot_x - w / 2, pivot_x + w / 2, face_y - h, face_y, z0, z1)
    body += box(pivot_x - w / 2, pivot_x + w / 2, face_y - td - 2.5, face_y - td, z0 - tab, z1 + tab)   # tabs
    body += bd.Pos(pivot_x, face_y, pivot_z) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        3.5, servo["horn"], align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))                     # horn hub
    return _tag(body, label, BLUE)


def wheel_x(x0, x1, y, z, d, label):
    w = cyl_x(d, x0, x1, y, z) - cyl_x(8.0, x0 - 0.1, x1 + 0.1, y, z)
    return _tag(w, label, RUBBER)


def ball_caster(x, y, z_bottom, height, label, long_axis="y", base=(48.0, 32.0), pitch=40.0, plate_t=3.0, ball_d=15.0):
    """Ball caster (bought: 20 tall, Ø15 ball, 48 x 32 base plate with 2 x Ø4 holes `pitch` apart along its long side)."""
    bl, bw = base
    ax, ay = (bw, bl) if long_axis == "y" else (bl, bw)
    top = z_bottom + height
    c = box(x - ax / 2, x + ax / 2, y - ay / 2, y + ay / 2, top - plate_t, top)
    for s in (-1, 1):
        hx, hy = (x, y + s * pitch / 2) if long_axis == "y" else (x + s * pitch / 2, y)
        c -= cyl_z(4.2, hx, hy, top - plate_t - 0.1, top + 0.1)
    c += cyl_z(22.0, x, y, z_bottom + ball_d / 2, top - plate_t)
    c += bd.Pos(x, y, z_bottom + ball_d / 2) * bd.Sphere(ball_d / 2)
    return _tag(c, label, STEEL)


def kw11(x0, x1, y0, y1, z0, z1, label):
    """KW11-3Z lever microswitch body (envelope; the lever is not modeled)."""
    return _tag(box(x0, x1, y0, y1, z0, z1), label, BLACK)


def kfl08_x(x0, x1, y, z, label):
    """Two-bolt flange bearing, axis along x, flange long side along y."""
    b = box(x0, x1, y - 24.0, y + 24.0, z - 13.5, z + 13.5)
    b -= cyl_x(8.2, x0 - 0.1, x1 + 0.1, y, z)
    return _tag(b, label, STEEL)


def board(x0, y0, z0, w, l, h, label, color=GREEN):
    return _tag(box(x0, x0 + w, y0, y0 + l, z0, z0 + h), label, color)


def rod_z(d, x, y, z0, z1, label):
    return _tag(cyl_z(d, x, y, z0, z1), label, STEEL)


def rod_x(d, x0, x1, y, z, label):
    return _tag(cyl_x(d, x0, x1, y, z), label, STEEL)


def vwheel(center, axis, wheel, spacer_to=None, label="vwheel"):
    """Mini V-wheel on an axle along `axis` ("x" or "y"); optional eccentric spacer from the wheel face to the
    plate coordinate `spacer_to` (same axis)."""
    d, w, sd = wheel["d"], wheel["w"], wheel["spacer_d"]
    cx, cy, cz = center
    lo, hi = (cx, cy)[axis == "y"] - w / 2, (cx, cy)[axis == "y"] + w / 2
    if axis == "x":
        body = cyl_x(d, lo, hi, cy, cz)
    else:
        body = bd.Pos(cx, lo, cz) * bd.Rot(-90, 0, 0) * bd.Cylinder(d / 2, w, align=(bd.Align.CENTER,) * 2 + (bd.Align.MIN,))
    if spacer_to is not None:
        a, b = sorted((spacer_to, hi if spacer_to > hi else lo))
        if axis == "x":
            body += cyl_x(sd, a, b, cy, cz)
        else:
            body += bd.Pos(cx, a, cz) * bd.Rot(-90, 0, 0) * bd.Cylinder(sd / 2, b - a, align=(bd.Align.CENTER,) * 2 + (bd.Align.MIN,))
    return _tag(body, label, STEEL)


def kfl08_z(x, y, z_top, kfl, label="kfl08"):
    """2-bolt flange bearing hanging under a plate at z_top, bore vertical, long side along y."""
    body = box(x - kfl["w"] / 2, x + kfl["w"] / 2, y - kfl["l"] / 2, y + kfl["l"] / 2, z_top - kfl["flange_t"], z_top)
    body += cyl_z(kfl["boss_d"], x, y, z_top - kfl["h"], z_top - kfl["flange_t"])
    body -= cyl_z(8.2, x, y, z_top - kfl["h"] - 0.1, z_top + 0.1)
    return _tag(body, label, STEEL)
