"""Robot docked at the rack, mid-swap: slot B aligned to extract from bay 2, extractor fully
out (Y = 175) with finger B engaged in the caddy notch. Used for visual review of the docking
and extraction geometry (checks/robot_check.py sweeps all poses)."""

from cadgen import build123d as bd
from cadgen import step

from lib.dims import H_BAY
from lib.robot_build import robot_parts
from lib.robot_dims import Y_MAX
from rack import rack

EXTRACT_OFFSET = -1.0


@step(out="../STEP/robot_docked.step")
def robot_docked():
    z = H_BAY[1] + EXTRACT_OFFSET
    bot = bd.Compound(children=robot_parts(z, Y_MAX, {"B": "engaged"}), label="robot")
    return bd.Compound(children=[rack(), bot], label="robot_docked")


if __name__ == "__main__":
    robot_docked()
