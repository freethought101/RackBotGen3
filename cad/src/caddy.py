"""Printed 3.5" drive caddy (PETG, x6). Spec: docs/spec/01-mechanical.md §2.

Frame: seated in a bay. x = 0 on the bay centerline, y = 0 at the rack face
(handle block toward -y), z = 0 on the shelf floor.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import (
    CADDY_BODY_L, CADDY_H, CADDY_HANDLE_L, CADDY_RAIL_H, CADDY_RAIL_W, CADDY_W,
    HDD_HOLE_SPAN_X, HDD_HOLE_Y, M3_CLEAR, NOTCH_DEPTH, NOTCH_FROM_FRONT, NOTCH_L,
)
from lib.prims import box, cyl_z, prism_xy, prism_yz

WALL = 3.5                 # side wall thickness
REAR_WALL = 2.5            # rear wall (pocket 148.5 long for a 147 mm drive)
FLOOR = 2.4                # drive floor thickness
FLOOR_LIFT = 1.0           # floor underside clears the shelf; caddy rides on its side walls and rails
SCREW_SLOT = 3.0           # +/- slot length in y for the drive screws (hole positions to verify)
CBORE_D = 6.5              # M3 button-head counterbore under the floor
CBORE_DEPTH = 1.2
LABEL_RECESS = 0.5
QR_SIZE = 22.0
TAG_SIZE = 24.0
REAR_CHAMFER = 2.0

HALF_W = CADDY_W / 2
FRONT = -CADDY_HANDLE_L
REAR = CADDY_BODY_L
POCKET_FLOOR_Z = FLOOR_LIFT + FLOOR      # drive bottom sits here


def _slot(x, y, d, z0, z1):
    return (
        box(x - d / 2, x + d / 2, y - SCREW_SLOT, y + SCREW_SLOT, z0, z1)
        + cyl_z(d, x, y - SCREW_SLOT, z0, z1)
        + cyl_z(d, x, y + SCREW_SLOT, z0, z1)
    )


@step(out="../STEP/caddy.step")
@stl(out="../STL/caddy.stl")
def caddy():
    inner = HALF_W - WALL
    body = box(-HALF_W, HALF_W, FRONT, REAR, 0, CADDY_H)

    # Guide rails along both bottom edges (114 mm over rails).
    for s in (-1, 1):
        x0, x1 = sorted((s * HALF_W, s * (HALF_W + CADDY_RAIL_W)))
        body += box(x0, x1, 0, REAR, 0, CADDY_RAIL_H)

    cuts = [
        # Underside relief between the side walls so screw heads clear the shelf.
        box(-inner, inner, 0, REAR - REAR_WALL, -0.1, FLOOR_LIFT),
        # Drive pocket, open top; reaches 1 mm into the handle block.
        box(-inner, inner, -1.0, REAR - REAR_WALL, POCKET_FLOOR_Z, CADDY_H + 0.1),
        # Hook notch on the right side of the handle block.
        box(HALF_W - NOTCH_DEPTH, HALF_W + 0.1,
            FRONT + NOTCH_FROM_FRONT - NOTCH_L / 2, FRONT + NOTCH_FROM_FRONT + NOTCH_L / 2,
            -0.1, CADDY_H + 0.1),
        # Label recesses on the front face: AprilTag left (in the robot camera's view through the
        # tray window), QR right.
        box(-HALF_W + 5, -HALF_W + 5 + TAG_SIZE, FRONT - 0.1, FRONT + LABEL_RECESS,
            (CADDY_H - TAG_SIZE) / 2, (CADDY_H + TAG_SIZE) / 2),
        box(HALF_W - 14 - QR_SIZE, HALF_W - 14, FRONT - 0.1, FRONT + LABEL_RECESS,
            (CADDY_H - QR_SIZE) / 2, (CADDY_H + QR_SIZE) / 2),
        # Rear bottom edge ramp so the caddy rides over the shelf/tray lips.
        prism_yz([(REAR + 0.1, -0.1), (REAR + 0.1, 1.5), (REAR - 1.5, -0.1)],
                 -HALF_W - CADDY_RAIL_W - 0.1, HALF_W + CADDY_RAIL_W + 0.1),
    ]
    # Rear vertical corners chamfered (also tapers the rail ends) for the bay lead-in.
    for s in (-1, 1):
        cuts.append(prism_xy(
            [(s * (HALF_W - REAR_CHAMFER), REAR + 0.1),
             (s * (HALF_W + CADDY_RAIL_W + 0.1), REAR + 0.1),
             (s * (HALF_W + CADDY_RAIL_W + 0.1), REAR - REAR_CHAMFER - CADDY_RAIL_W - 0.1)],
            -0.1, CADDY_H + 0.1))
    # Drive screw slots with counterbores from below.
    for x in (-HDD_HOLE_SPAN_X / 2, HDD_HOLE_SPAN_X / 2):
        for y in HDD_HOLE_Y:
            cuts.append(_slot(x, y, M3_CLEAR, FLOOR_LIFT - 0.1, POCKET_FLOOR_Z + 0.1))
            cuts.append(_slot(x, y, CBORE_D, FLOOR_LIFT - 0.1, FLOOR_LIFT + CBORE_DEPTH))

    for c in cuts:
        body -= c
    body.label = "caddy"
    return body


if __name__ == "__main__":
    caddy()
