"""Shared builder for the rack and the spare station (same frame, dock, tags; different heights)."""

from cadgen import build123d as bd
from cadgen import srgb

from bay_shelf import bay_shelf
from caddy import POCKET_FLOOR_Z, caddy
from dock_block import dock_block
from dummy_drive_lid import dummy_drive_lid
from dummy_drive_shell import dummy_drive_shell
from lib.dims import BASE_HALF_L, EXT, TOP_HALF_L, UPRIGHT_INNER_X, UPRIGHT_Y
from lib.extrusion import vslot

COLORS = {"shelf": "#3C6E9E", "caddy": "#E07A1F", "dummy": "#4A4F57", "lid": "#6B7280",
          "dock": "#2F855A", "tag": "#F2F2F2"}


def color(part, key):
    part.color = srgb(COLORS[key])
    return part


def frame(top_z, prefix):
    """Base cross members on the table, four uprights, top cross members. Returns (parts, cut list)."""
    parts, cuts = [], []
    ends = ("front", "rear")
    for y, end in zip(UPRIGHT_Y, ends):
        y0, y1 = y - EXT / 2, y + EXT / 2
        parts.append(vslot(-BASE_HALF_L, BASE_HALF_L, y0, y1, 0, EXT, f"{prefix}base_2020:{end}"))
        cuts.append(("base cross member", 2 * BASE_HALF_L))
        parts.append(vslot(-TOP_HALF_L, TOP_HALF_L, y0, y1, top_z - EXT, top_z, f"{prefix}top_2020:{end}"))
        cuts.append(("top cross member", 2 * TOP_HALF_L))
        for sx, side in ((-1, "left"), (1, "right")):
            x0, x1 = sorted((sx * UPRIGHT_INNER_X, sx * (UPRIGHT_INNER_X + EXT)))
            parts.append(vslot(x0, x1, y0, y1, EXT, top_z - EXT, f"{prefix}upright_2020:{side}_{end}"))
            cuts.append(("upright", top_z - 2 * EXT))
    return parts, cuts


def shelves(heights, filled, name):
    """Shelves at the given floor heights; a caddy with a dummy drive where filled[i] is True."""
    parts = []
    for i, (h, full) in enumerate(zip(heights, filled), start=1):
        parts.append(color(bd.Pos(0, 0, h) * bay_shelf(), "shelf"))
        parts[-1].label = f"bay_shelf:{name}{i}"
        if full:
            at = bd.Pos(0, 0, h)
            for p, key, lab in ((caddy(), "caddy", "caddy"),
                                (bd.Pos(0, 0, POCKET_FLOOR_Z) * dummy_drive_shell(), "dummy", "dummy_drive"),
                                (bd.Pos(0, 0, POCKET_FLOOR_Z) * dummy_drive_lid(), "lid", "dummy_lid")):
                placed = color(at * p, key)
                placed.label = f"{lab}:{name}{i}"
                parts.append(placed)
    return parts


def dock():
    return color(dock_block(), "dock")
