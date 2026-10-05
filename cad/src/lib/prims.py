"""Small geometry helpers that place primitives by absolute extents."""

from cadgen import build123d as bd


def box(x0, x1, y0, y1, z0, z1):
    """Axis-aligned box spanning the given absolute extents."""
    return bd.Pos(x0, y0, z0) * bd.Box(
        x1 - x0, y1 - y0, z1 - z0, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN)
    )


def prism_xy(points, z0, z1):
    """Extrude a closed XY polygon from z0 to z1."""
    face = bd.Pos(0, 0, z0) * bd.make_face(bd.Polyline(*points, close=True))
    return bd.extrude(face, amount=z1 - z0)


def prism_yz(points, x0, x1):
    """Extrude a closed polygon given as (y, z) points from x0 to x1."""
    face = bd.make_face(bd.Polyline(*[(x0, y, z) for y, z in points], close=True))
    return bd.extrude(face, amount=x1 - x0, dir=(1, 0, 0))


def cyl_x(d, x0, x1, y, z):
    """Cylinder along +x from x0 to x1 centered at (y, z)."""
    return bd.Pos(x0, y, z) * bd.Rot(0, 90, 0) * bd.Cylinder(
        d / 2, x1 - x0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
    )


def cyl_z(d, x, y, z0, z1):
    """Cylinder along +z from z0 to z1 centered at (x, y)."""
    return bd.Pos(x, y, z0) * bd.Cylinder(
        d / 2, z1 - z0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
    )
