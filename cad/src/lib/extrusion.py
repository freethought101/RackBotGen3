"""2020 / 2040 V-slot stand-ins (outer envelope with the four slot grooves), for assemblies."""

from cadgen import srgb

from lib.prims import box

SLOT_W = 6.2
SLOT_D = 6.0
ALU = srgb("#A7AFB8")


def vslot(x0, x1, y0, y1, z0, z1, label):
    """Extrusion occupying the given box; grooves run along its longest axis, centered on each 20 mm face module."""
    ext = [(x0, x1), (y0, y1), (z0, z1)]
    lengths = [b - a for a, b in ext]
    axis = lengths.index(max(lengths))
    body = box(x0, x1, y0, y1, z0, z1)
    for side_axis in (i for i in range(3) if i != axis):
        other = next(i for i in range(3) if i not in (axis, side_axis))
        lo, hi = ext[other]
        for center in [lo + 10 + 20 * k for k in range(round((hi - lo) / 20))]:
            for face in ext[side_axis]:
                g = [list(e) for e in ext]
                g[axis] = [ext[axis][0] - 1, ext[axis][1] + 1]
                g[other] = [center - SLOT_W / 2, center + SLOT_W / 2]
                g[side_axis] = [face - SLOT_D, face] if face == ext[side_axis][1] else [face, face + SLOT_D]
                body -= box(*g[0], *g[1], *g[2])
    body.label = label
    body.color = ALU
    return body
