"""Fit check: two stacked bay shelves at BAY_PITCH on 2020 upright stubs, with a
seated caddy holding the dummy drive. Not a printed part — used for clearance checks
(checks/bay_fit_check.py) and visual review."""

from cadgen import build123d as bd
from cadgen import srgb, step

from bay_shelf import FLOOR_T, bay_shelf
from caddy import POCKET_FLOOR_Z, caddy
from dummy_drive_lid import dummy_drive_lid
from dummy_drive_shell import dummy_drive_shell
from lib.dims import BAY_PITCH, UPRIGHT_INNER_X, UPRIGHT_Y
from lib.prims import box

EXTRUSION = 20.0


@step(out="../STEP/bay_fit.step")
def bay_fit():
    lower = bay_shelf()
    upper = bd.Pos(0, 0, BAY_PITCH) * bay_shelf()
    seated = caddy()
    drive_at = bd.Pos(0, 0, POCKET_FLOOR_Z)
    shell = drive_at * dummy_drive_shell()
    lid = drive_at * dummy_drive_lid()

    uprights = []
    for sx, side in ((-1, "left"), (1, "right")):
        for y, end in zip(UPRIGHT_Y, ("front", "rear")):
            x0, x1 = sorted((sx * UPRIGHT_INNER_X, sx * (UPRIGHT_INNER_X + EXTRUSION)))
            u = box(x0, x1, y - EXTRUSION / 2, y + EXTRUSION / 2, -FLOOR_T - 20, BAY_PITCH + 40)
            u.label = f"upright_2020:{side}_{end}"
            u.color = srgb("#9AA3AD")
            uprights.append(u)

    lower.label, upper.label = "bay_shelf:lower", "bay_shelf:upper"
    seated.label, shell.label, lid.label = "caddy", "dummy_drive_shell", "dummy_drive_lid"
    for part, color in ((lower, "#3C6E9E"), (upper, "#3C6E9E"), (seated, "#E07A1F"),
                        (shell, "#4A4F57"), (lid, "#6B7280")):
        part.color = srgb(color)
    return bd.Compound(children=[lower, upper, seated, shell, lid, *uprights], label="bay_fit")


if __name__ == "__main__":
    bay_fit()
