"""Spare station assembly: S1 GOOD (bottom) and S2 RMA (top) on a short 2020 frame, same
dock block and tag layout as the rack. Spec: docs/spec/01-mechanical.md §5.

Frame: same convention as the rack (robot side is -y); placed facing the rack in the demo layout.
"""

from cadgen import build123d as bd
from cadgen import step

from lib.dims import H_SPARE, SPARE_TOP_Z
from lib.station import color, dock, frame, shelves
from tag_fin import tag_fin
from tag_strip_spare import tag_strip_spare

FILLED = (True, False)   # good spare waiting in S1, RMA slot empty


@step(out="../STEP/spare_station.step")
def spare_station():
    frame_parts, _ = frame(SPARE_TOP_Z, "")
    strip = color(tag_strip_spare(), "tag")
    fin = color(tag_fin(), "tag")
    strip.label, fin.label = "tag_strip:slots_s1_s2", "tag_fin:id10"
    children = [*frame_parts, *shelves(H_SPARE, FILLED, "s"), dock(), strip, fin]
    return bd.Compound(children=children, label="spare_station")


if __name__ == "__main__":
    spare_station()
