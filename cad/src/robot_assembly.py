"""Robot assembly at a travel pose (lift at Z = 210, extractor home, fingers parked).
Frame: docked-at-rack frame (see lib/robot_dims.py)."""

from cadgen import build123d as bd
from cadgen import step

from lib.robot_build import robot_parts

POSE_Z, POSE_Y = 210.0, 0.0


@step(out="../STEP/robot_assembly.step")
def robot_assembly():
    return bd.Compound(children=robot_parts(POSE_Z, POSE_Y), label="robot")


if __name__ == "__main__":
    robot_assembly()
