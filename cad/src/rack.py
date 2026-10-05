"""Rack assembly: 1 column x 4 bays on a 2020 frame, dock block, tags, and rear DIN-rail
electronics (Delta PSU + Delta PLC placeholders). Spec: docs/spec/01-mechanical.md §4.

Frame: x = 0 on the bay centerline, y = 0 at the rack face (robot side is -y), z = 0 on the table.
"""

from cadgen import build123d as bd
from cadgen import srgb, step

from lib.dims import H_BAY, RACK_TOP_Z, UPRIGHT_Y, EXT
from lib.prims import box, cyl_z
from lib.station import color, dock, frame, shelves
from tag_fin import tag_fin
from tag_strip_rack import tag_strip_rack

FILLED = (True, True, False, True)   # bay 3 left empty in the model to show the shelf

# Rear electronics on a 35 mm DIN rail on the rear uprights' back faces (placeholders, check real sizes).
REAR_FACE_Y = UPRIGHT_Y[1] + EXT / 2         # 145
DIN = (-120.0, 65.0, 42.5, 77.5)             # x0, x1, z0, z1 (router sits right of the rail)
DIN_DEPTH = 7.5
DEVICES = [
    # label, x0, x1, depth, height, colour
    ("delta_psu_24v", -115.0, -70.0, 100.0, 90.0, "#C9CED6"),
    ("delta_plc_dvp12se", -62.0, -25.0, 60.0, 90.0, "#2B2F36"),
    ("dock_relay", -18.0, 8.0, 50.0, 70.0, "#2563EB"),
    ("terminal_blocks", 15.0, 63.0, 45.0, 50.0, "#9CA3AF"),
]


def _placeholder(label, shape, hex_color):
    shape.label = label
    shape.color = srgb(hex_color)
    return shape


def electronics():
    y0 = REAR_FACE_Y
    yr = y0 + DIN_DEPTH
    parts = [_placeholder("din_rail", box(DIN[0], DIN[1], y0, yr, DIN[2], DIN[3]), "#B8BEC6")]
    zc = (DIN[2] + DIN[3]) / 2
    for label, x0, x1, depth, h, c in DEVICES:
        parts.append(_placeholder(label, box(x0, x1, yr, yr + depth, zc - h / 2, zc + h / 2), c))
    parts.append(_placeholder("travel_router", box(70.0, 128.0, y0, y0 + 25.0, 20.0, 78.0), "#E5E7EB"))
    # On top: tower light (rear right) and E-stop (rear left), on the rear top cross member.
    ym = UPRIGHT_Y[1]
    parts.append(_placeholder("tower_light", cyl_z(40.0, 60.0, ym, RACK_TOP_Z, RACK_TOP_Z + 120.0), "#E5E7EB"))
    parts.append(_placeholder("estop_box", box(-80.0, -40.0, ym - 20.0, ym + 20.0, RACK_TOP_Z, RACK_TOP_Z + 40.0),
                              "#FACC15"))
    parts.append(_placeholder("estop_button", cyl_z(40.0, -60.0, ym, RACK_TOP_Z + 40.0, RACK_TOP_Z + 60.0),
                              "#DC2626"))
    return parts


@step(out="../STEP/rack.step")
def rack():
    frame_parts, _ = frame(RACK_TOP_Z, "")
    strip = color(tag_strip_rack(), "tag")
    fin = color(tag_fin(), "tag")
    strip.label, fin.label = "tag_strip:bays_1_4", "tag_fin:id0"
    children = [*frame_parts, *shelves(H_BAY, FILLED, "bay"), dock(), strip, fin, *electronics()]
    return bd.Compound(children=children, label="rack")


if __name__ == "__main__":
    rack()
