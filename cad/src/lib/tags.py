"""Printed AprilTag carriers (PLA). Station frame: x = 0 on the bay centerline,
y = 0 at the rack face, z = 0 on the table. Tags are printed on paper/vinyl and glued
into 0.5 mm recesses on the front face (y = TAG_FACE_Y)."""

from cadgen import build123d as bd

from lib.dims import (EXT, M5_CLEAR, TAG_APPROACH, TAG_APPROACH_Z, TAG_BAY, TAG_FACE_Y,
                      UPRIGHT_INNER_X, UPRIGHT_Y)
from lib.prims import box

RECESS = 0.5
STRIP_T = 3.0
TAG_ABOVE_FLOOR = 15.0         # bay tag centre above the shelf floor


def _y_hole(x, z, y0, y1, d=M5_CLEAR):
    return bd.Pos(x, y0, z) * bd.Rot(-90, 0, 0) * bd.Cylinder(
        d / 2, y1 - y0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


def tag_strip(shelf_heights):
    """Strip on the front face of the front-left upright, one TAG_BAY tag per shelf."""
    x0, x1 = -UPRIGHT_INNER_X - EXT, -UPRIGHT_INNER_X
    xc = (x0 + x1) / 2
    y_back = UPRIGHT_Y[0] - EXT / 2            # upright front face
    centres = [h + TAG_ABOVE_FLOOR for h in shelf_heights]
    z0 = centres[0] - TAG_BAY / 2 - 8
    z1 = centres[-1] + TAG_BAY / 2 + 8 + (12 if len(centres) < 3 else 0)
    strip = box(x0, x1, y_back - STRIP_T, y_back, z0, z1)
    for zc in centres:
        strip -= box(xc - TAG_BAY / 2, xc + TAG_BAY / 2, TAG_FACE_Y - 0.1, TAG_FACE_Y + RECESS,
                     zc - TAG_BAY / 2, zc + TAG_BAY / 2)
    gaps = [(a + b) / 2 for a, b in zip(centres, centres[1:])][::2]
    holes = gaps if len(gaps) >= 2 else gaps + [z1 - 6]
    for z in holes:
        strip -= _y_hole(xc, z, y_back - STRIP_T - 0.1, y_back + 0.1)
    return strip


def tag_fin():
    """Approach-tag fin on the outer face of the front-right upright, TAG_APPROACH tag."""
    zc = TAG_APPROACH_Z
    half = TAG_APPROACH / 2 + 10
    xo = UPRIGHT_INNER_X + EXT                 # upright outer face
    y_front = UPRIGHT_Y[0] - EXT / 2
    plate_x1 = xo + 2 * half
    fin = box(xo, xo + 3, y_front, y_front + EXT, zc - half, zc + half)      # flange on the upright
    fin += box(xo, plate_x1, y_front - STRIP_T, y_front, zc - half, zc + half)  # tag plate
    fin += box(plate_x1 - 3, plate_x1, y_front, y_front + 10, zc - half, zc + half)  # stiffening rib
    xc = xo + half
    fin -= box(xc - TAG_APPROACH / 2, xc + TAG_APPROACH / 2, TAG_FACE_Y - 0.1, TAG_FACE_Y + RECESS,
               zc - TAG_APPROACH / 2, zc + TAG_APPROACH / 2)
    for z in (zc - 25, zc - 5):                # both inside the spare station's shorter uprights
        fin -= bd.Pos(xo - 0.1, UPRIGHT_Y[0], z) * bd.Rot(0, 90, 0) * bd.Cylinder(
            M5_CLEAR / 2, 3.2, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    return fin
