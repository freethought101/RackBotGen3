"""Y belt clamp jaw (PETG), modeled at Z = 0 with the finger pivot at y = 0 (moves with the Y carriage).

The open GT2 belt's two ends lie on the carriage plate's clamp pad, teeth outward; this jaw presses them onto the pad.
Tension the belt by hand, then tighten the 2 x M3 x 10 into the plate's heat-set inserts (the idler slot adds +/-3 mm).
Print with the clamp face down; add a GT2 tooth comb to that face if the flat jaw slips.
"""

from cadgen import step, stl

from lib.dims import M3_CLEAR
from lib.prims import box, cyl_x
from lib.robot_dims import BELT_STRAND_X
from robot.y_carriage import CLAMP_DY, CLAMP_SCREW_DZ

T = 4.0
MARGIN = 3.5                # beyond the screw holes in z


@step(out="../../STEP/robot/belt_clamp.step")
@stl(out="../../STL/robot/belt_clamp.stl")
def belt_clamp():
    x0 = BELT_STRAND_X[0][1]                                    # the belt's tooth side
    z0, z1 = CLAMP_SCREW_DZ[0] - MARGIN, CLAMP_SCREW_DZ[1] + MARGIN
    part = box(x0, x0 + T, *CLAMP_DY, z0, z1)
    for z in CLAMP_SCREW_DZ:
        part -= cyl_x(M3_CLEAR, x0 - 0.1, x0 + T + 0.1, sum(CLAMP_DY) / 2, z)
    part.label = "belt_clamp"
    return part


if __name__ == "__main__":
    belt_clamp()
