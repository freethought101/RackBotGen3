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
          "leadscrew_350": 130, "coupler": 15, "kp08": 40, "v_wheel": 12, "wheel_80": 60,
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
    return _tag(body, label, BLACK)


def nema17_y(x, y_face, z, direction, label, length=40.0):
    y0, y1 = sorted((y_face, y_face - direction * length))
    body = box(x - 21.15, x + 21.15, y0, y1, z - 21.15, z + 21.15)
    return _tag(body, label, BLACK)


def mg90s_y(pivot_x, face_y, pivot_z, label, servo):
    """MG90S with its output shaft along +y ending at face_y, axis at (pivot_x, pivot_z).
    The case extends behind the face (-y) and upward from the shaft (shaft near the case's lower end)."""
    w, h, ln, off, tab = servo["wid"], servo["h"], servo["len"], servo["shaft_from_end"], servo["tab"]
    z0, z1 = pivot_z - off, pivot_z - off + ln
    body = box(pivot_x - w / 2, pivot_x + w / 2, face_y - h, face_y - 4.0, z0, z1)
    body += box(pivot_x - w / 2, pivot_x + w / 2, face_y - 12.0, face_y - 9.5, z0 - tab, z1 + tab)   # tabs
    body += bd.Pos(pivot_x, face_y - 4.0, pivot_z) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        2.3, 4.0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    return _tag(body, label, BLUE)


def wheel_x(x0, x1, y, z, d, label):
    w = cyl_x(d, x0, x1, y, z) - cyl_x(8.0, x0 - 0.1, x1 + 0.1, y, z)
    return _tag(w, label, RUBBER)


def ball_caster(x, y, z_bottom, height, label):
    c = cyl_z(25.0, x, y, z_bottom + height - 6.0, z_bottom + height)
    c += bd.Pos(x, y, z_bottom + 9.5) * bd.Sphere(9.5)
    c += cyl_z(16.0, x, y, z_bottom + 9.5, z_bottom + height - 6.0)
    return _tag(c, label, STEEL)


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
