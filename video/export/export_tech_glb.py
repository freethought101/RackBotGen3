"""Export the CAD as per-subsystem GLB groups for the Corvin technical film (run from cad/src:
PYTHONPATH=. uvx --no-config --managed-python --python 3.13 --from cadgen==0.7.14 python ../../video/export/export_tech_glb.py).

Same geometry as export_glb.py, split finer so the film can explode, isolate and highlight each subsystem.
Every group stays in the docked-at-rack frame (mm): lift groups at Z = 0, extractor groups at Z = 0, Y = 0.
"""

from cadgen import build123d as bd
from cadgen import glb

from lib.dims import H_BAY, H_SPARE, RACK_TOP_Z, SPARE_TOP_Z
from lib.robot_build import base_parts, extractor_parts, lift_parts
from lib.station import color, dock, frame, shelves
from rack import electronics as rack_devices
from tag_fin import tag_fin
from tag_strip_rack import tag_strip_rack
from tag_strip_spare import tag_strip_spare

OUT = "../public/models/tech/"  # relative to this script, like export_glb.py

# group name -> label prefixes (first match wins, in this order)
BASE = {
    "wheel_left": ("drive_hub:left", "drive_tire:left"),
    "wheel_right": ("drive_hub:right", "drive_tire:right"),
    "drive_motor_left": ("nema17:drive_left",),
    "drive_motor_right": ("nema17:drive_right",),
    "zdrive": ("nema17:z", "z_motor_mount", "coupler", "leadscrew", "kfl08"),
    "mast": ("mast_2040", "mast_collar", "mast_top_plate", "estop_box", "estop_button"),
    "electronics": ("electronics_tray", "motion_board", "pi_tray", "raspberry_pi_3"),
    "power": ("battery_box", "battery_4s1p", "buck:"),
    "nose": ("nose", "kw11:nose"),
    "chassis": ("",),
}
LIFT = {
    "camera": ("camera_module_3_wide",),
    "tray": ("tray_stack", "kw11:slot_"),
    "yrail": ("rail_bracket", "y_rail_2020", "nema17:y", "gt2_", "y_idler_bracket", "kw11:y_home"),
    "zcarriage": ("",),
}
EXTRACTOR = {
    "servo_a": ("mg90s:A",),
    "servo_b": ("mg90s:B",),
    "ycarriage": ("",),
}


def split(parts, groups):
    out = {g: [] for g in groups}
    for p in parts:
        label = p.label or ""
        for g, prefixes in groups.items():
            if any(label.startswith(pre) for pre in prefixes):
                out[g].append(p)
                break
    return out


_CACHE = {}


def _groups():
    if _CACHE:
        return _CACHE
    groups = _CACHE
    groups.update(split(base_parts(), BASE))
    groups.update(split(lift_parts(0.0), LIFT))
    ext = [p for p in extractor_parts(0.0, 0.0, {}) if not p.label.startswith("finger:")]
    groups.update(split(ext, EXTRACTOR))

    rack_frame, _ = frame(RACK_TOP_Z, "")
    groups["rack"] = [*rack_frame, *shelves(H_BAY, (False,) * 4, "bay"), dock(),
                      color(tag_strip_rack(), "tag"), color(tag_fin(), "tag")]
    elec = rack_devices()
    groups["rack_lamps"] = [p for p in elec if p.label == "status_lamp"]
    groups["rack_electronics"] = [p for p in elec if p.label != "status_lamp"]
    spare_frame, _ = frame(SPARE_TOP_Z, "")
    groups["spare"] = [*spare_frame, *shelves(H_SPARE, (False, False), "s"), dock(),
                       color(tag_strip_spare(), "tag"), color(tag_fin(), "tag")]
    for name, children in groups.items():
        assert children, name
    return groups


def _c(name):
    return bd.Compound(children=_groups()[name], label=name)

@glb(out=OUT + "wheel_left.glb")
def wheel_left():
    return _c("wheel_left")


@glb(out=OUT + "wheel_right.glb")
def wheel_right():
    return _c("wheel_right")


@glb(out=OUT + "drive_motor_left.glb")
def drive_motor_left():
    return _c("drive_motor_left")


@glb(out=OUT + "drive_motor_right.glb")
def drive_motor_right():
    return _c("drive_motor_right")


@glb(out=OUT + "zdrive.glb")
def zdrive():
    return _c("zdrive")


@glb(out=OUT + "mast.glb")
def mast():
    return _c("mast")


@glb(out=OUT + "electronics.glb")
def electronics():
    return _c("electronics")


@glb(out=OUT + "power.glb")
def power():
    return _c("power")


@glb(out=OUT + "nose.glb")
def nose():
    return _c("nose")


@glb(out=OUT + "chassis.glb")
def chassis():
    return _c("chassis")


@glb(out=OUT + "camera.glb")
def camera():
    return _c("camera")


@glb(out=OUT + "tray.glb")
def tray():
    return _c("tray")


@glb(out=OUT + "yrail.glb")
def yrail():
    return _c("yrail")


@glb(out=OUT + "zcarriage.glb")
def zcarriage():
    return _c("zcarriage")


@glb(out=OUT + "servo_a.glb")
def servo_a():
    return _c("servo_a")


@glb(out=OUT + "servo_b.glb")
def servo_b():
    return _c("servo_b")


@glb(out=OUT + "ycarriage.glb")
def ycarriage():
    return _c("ycarriage")


@glb(out=OUT + "rack.glb")
def rack():
    return _c("rack")


@glb(out=OUT + "rack_lamps.glb")
def rack_lamps():
    return _c("rack_lamps")


@glb(out=OUT + "rack_electronics.glb")
def rack_electronics():
    return _c("rack_electronics")


@glb(out=OUT + "spare.glb")
def spare():
    return _c("spare")


if __name__ == "__main__":
    for model in (wheel_left, wheel_right, drive_motor_left, drive_motor_right, zdrive, mast, electronics, power, nose, chassis, camera, tray, yrail, zcarriage, servo_a, servo_b, ycarriage, rack, rack_lamps, rack_electronics, spare):
        model()
