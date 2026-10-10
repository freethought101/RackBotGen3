"""Drive wheel, right side: printed PETG hub + TPU 95A tire (print 2 of each; the left wheel is the same part).

Ø80 x 24 assembled, direct on the NEMA17 D-shaft (22 mm, ends at x 141). The hub clamps the shaft flat with an
M3 set screw in a radial M3 x 4 heat-set insert; an Ø8 window in the rim gives the iron and the hex key a straight
path (the tire has an Ø4 hole that is lined up with it after fitting). The web is on the outboard face so the hub
prints outboard face down without supports. The tire is 0.5 mm undersize on the rim seat and is held between two
1.5 mm lips.
"""

from cadgen import build123d as bd
from cadgen import step, stl

from lib.dims import M3_CLEAR, M3_INSERT_D
from lib.prims import box, cyl_x, cyl_z
from lib.robot_dims import AXLE_Y, AXLE_Z, WHEEL_D, WHEEL_X

X0, X1 = WHEEL_X                  # 125 .. 149 (inboard .. outboard)
SHAFT_END_X = 141.0               # 22 mm shaft from the motor face at x 119
LIP_W, LIP_D = 1.5, 75.0
SEAT_D = 72.0                     # rim seat under the tire
RIM_ID = 64.0
CORE_D = 18.0
WEB_T = 4.0                       # outboard web (print face)
BORE_D = 5.15                     # 5 mm shaft + clearance
FLAT_R = 2.1                      # D-flat at 2.0 from the axis (4.5 across) + 0.1
SCREW_X = 132.0                   # set screw plane (mid shaft engagement)
INSERT_DEPTH = 4.5
WINDOW_D = 8.0                    # rim window for the iron and the hex key
TIRE_ID = SEAT_D - 0.5
TIRE_HOLE_D = 4.0


def _radial_z(d, x, r0, r1):
    """Cylinder along +z from radius r0 to r1 above the axle, at plane x."""
    return cyl_z(d, x, AXLE_Y, AXLE_Z + r0, AXLE_Z + r1)


@step(out="../../STEP/robot/drive_hub.step")
@stl(out="../../STL/robot/drive_hub.stl")
def drive_hub():
    hub = cyl_x(SEAT_D, X0 + LIP_W, X1 - LIP_W, AXLE_Y, AXLE_Z)
    for x0, x1 in ((X0, X0 + LIP_W), (X1 - LIP_W, X1)):
        hub += cyl_x(LIP_D, x0, x1, AXLE_Y, AXLE_Z)
    hub -= cyl_x(RIM_ID, X0 - 0.1, X1 - WEB_T, AXLE_Y, AXLE_Z)          # open inboard, web on the outboard face
    hub += cyl_x(CORE_D, X0, X1, AXLE_Y, AXLE_Z)
    bore = cyl_x(BORE_D, X0 - 0.1, SHAFT_END_X + 1.0, AXLE_Y, AXLE_Z)
    bore -= box(X0 - 0.2, SHAFT_END_X + 1.1, AXLE_Y - BORE_D, AXLE_Y + BORE_D, AXLE_Z + FLAT_R, AXLE_Z + BORE_D)
    hub -= bore                                                          # D bore, flat facing +z (the set screw)
    hub -= _radial_z(M3_CLEAR, SCREW_X, 0.0, CORE_D / 2 + 0.1)
    hub -= _radial_z(M3_INSERT_D, SCREW_X, CORE_D / 2 - INSERT_DEPTH, CORE_D / 2 + 0.1)
    hub -= _radial_z(WINDOW_D, SCREW_X, RIM_ID / 2 - 0.5, LIP_D / 2 + 0.1)
    hub.label = "drive_hub"
    return hub


@step(out="../../STEP/robot/drive_tire.step")
@stl(out="../../STL/robot/drive_tire.stl")
def drive_tire():
    tire = cyl_x(WHEEL_D, X0 + LIP_W, X1 - LIP_W, AXLE_Y, AXLE_Z)
    tire -= cyl_x(TIRE_ID, X0, X1, AXLE_Y, AXLE_Z)
    tire -= _radial_z(TIRE_HOLE_D, SCREW_X, TIRE_ID / 2 - 0.5, WHEEL_D / 2 + 0.1)
    tire.label = "drive_tire"
    return tire


if __name__ == "__main__":
    drive_hub()
    drive_tire()
