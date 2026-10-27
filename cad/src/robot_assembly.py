"""Robot assembly at a travel pose (lift at Z = 210, extractor home, fingers parked), with every modeled fastener
and heat-set insert (lib/robot_fasteners.py). Frame: docked-at-rack frame (see lib/robot_dims.py)."""

from cadgen import build123d as bd
from cadgen import step

from lib.robot_build import robot_parts
from lib.robot_fasteners import fastener_parts

POSE_Z, POSE_Y = 210.0, 0.0


@step(out="../STEP/robot_assembly.step")
def robot_assembly():
    fasteners = bd.Compound(children=[s for _, _, s in fastener_parts(POSE_Z, POSE_Y)], label="fasteners")
    return bd.Compound(children=robot_parts(POSE_Z, POSE_Y) + [fasteners], label="robot")


if __name__ == "__main__":
    robot_assembly()
