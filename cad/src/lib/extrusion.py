"""2020 / 2040 V-slot for assemblies: the step.parts V-slot cross-section (docs/3d-models/P02_/P03_*.step, the
OpenBuilds profile) extruded to each cut length."""

import os

from cadgen import build123d as bd
from cadgen import read_step, srgb

SLOT_W = 6.2
SLOT_D = 6.0
ALU = srgb("#A7AFB8")

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "..", "..", "..", "docs", "3d-models")
PROFILE_STEPS = {40: "P02_vslot_2020_l0300_openbuilds.step", 60: "P03_vslot_2040_l0500_openbuilds.step"}
_profiles = {}


def _profile(size):
    """End face of the library extrusion, moved to x = 0: the section lies in the y-z plane (20 along y, 20 or 40
    along z), centred on the axis."""
    if size not in _profiles:
        s = read_step(os.path.join(MODELS, PROFILE_STEPS[size]))
        x1 = s.bounding_box().max.X
        face = next(f for f in s.faces() if abs(f.center().X - x1) < 1e-3)
        _profiles[size] = face.moved(bd.Location((-x1, 0, 0)))
    return _profiles[size]


def vslot(x0, x1, y0, y1, z0, z1, label):
    """Extrusion occupying the given box, along its longest axis (a 2040's 40 side follows the box)."""
    ext = [(x0, x1), (y0, y1), (z0, z1)]
    lengths = [b - a for a, b in ext]
    axis = lengths.index(max(lengths))
    others = [i for i in range(3) if i != axis]
    if lengths[others[0]] > lengths[others[1]]:                  # the 40 side maps to the profile's z
        others.reverse()
    unit = lambda i: tuple(1.0 if k == i else 0.0 for k in range(3))
    origin = [0.0, 0.0, 0.0]
    origin[axis] = ext[axis][0]
    for i in others:
        origin[i] = (ext[i][0] + ext[i][1]) / 2
    body = bd.extrude(_profile(round(lengths[others[0]] + lengths[others[1]])), amount=lengths[axis], dir=(1, 0, 0))
    body = bd.Location(bd.Plane(origin=tuple(origin), x_dir=unit(axis), z_dir=unit(others[1]))) * body
    body.label = label
    body.color = ALU
    return body
