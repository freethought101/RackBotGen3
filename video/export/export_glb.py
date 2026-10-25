"""Export the CAD as rigid GLB groups for the pitch video (run from repo root:
PYTHONPATH=cad/src <cadgen python> video/export/export_glb.py).

Groups move rigidly in the video: base (whole robot frame), lift (+Z), extractor (+Z, +Y),
finger (rotates about its pivot), caddy (one per instance), rack and spare station without caddies.
All geometry is in the docked-at-rack frame, mm.
"""

from cadgen import build123d as bd
from cadgen import glb

from caddy import POCKET_FLOOR_Z, caddy as caddy_part
from dummy_drive_lid import dummy_drive_lid
from dummy_drive_shell import dummy_drive_shell
from lib.dims import H_BAY, H_SPARE, RACK_TOP_Z, SPARE_TOP_Z
from lib.robot_build import base_parts, extractor_parts, lift_parts
from lib.station import color, dock, frame, shelves
from rack import electronics
from robot.finger import finger as finger_part
from tag_fin import tag_fin
from tag_strip_rack import tag_strip_rack
from tag_strip_spare import tag_strip_spare

OUT = "../public/models/"


@glb(out=OUT + "robot_base.glb")
def robot_base():
    return bd.Compound(children=base_parts(), label="robot_base")


@glb(out=OUT + "robot_lift.glb")
def robot_lift():
    return bd.Compound(children=lift_parts(0.0), label="robot_lift")


@glb(out=OUT + "robot_extractor.glb")
def robot_extractor():
    parts = [p for p in extractor_parts(0.0, 0.0, {}) if not p.label.startswith("finger:")]
    return bd.Compound(children=parts, label="robot_extractor")


@glb(out=OUT + "finger.glb")
def finger():
    f = finger_part()
    color(f, "caddy")
    return bd.Compound(children=[f], label="finger")


@glb(out=OUT + "caddy.glb")
def caddy():
    parts = [color(caddy_part(), "caddy"),
             color(bd.Pos(0, 0, POCKET_FLOOR_Z) * dummy_drive_shell(), "dummy"),
             color(bd.Pos(0, 0, POCKET_FLOOR_Z) * dummy_drive_lid(), "lid")]
    return bd.Compound(children=parts, label="caddy")


@glb(out=OUT + "rack.glb")
def rack():
    frame_parts, _ = frame(RACK_TOP_Z, "")
    strip, fin = color(tag_strip_rack(), "tag"), color(tag_fin(), "tag")
    children = [*frame_parts, *shelves(H_BAY, (False,) * 4, "bay"), dock(), strip, fin, *electronics()]
    return bd.Compound(children=children, label="rack")


@glb(out=OUT + "spare.glb")
def spare():
    frame_parts, _ = frame(SPARE_TOP_Z, "")
    strip, fin = color(tag_strip_spare(), "tag"), color(tag_fin(), "tag")
    children = [*frame_parts, *shelves(H_SPARE, (False, False), "s"), dock(), strip, fin]
    return bd.Compound(children=children, label="spare_station")


if __name__ == "__main__":
    for model in (robot_base, robot_lift, robot_extractor, finger, caddy, rack, spare):
        model()
