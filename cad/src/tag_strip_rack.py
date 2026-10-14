"""Tag strip (PLA): 4 bay tags (IDs 1-4), front-left upright of the rack."""

from cadgen import step, stl

from lib.dims import H_BAY
from lib.tags import tag_strip


@step(out="../STEP/tag_strip_rack.step")
@stl(out="../STL/tag_strip_rack.stl")
def tag_strip_rack():
    part = tag_strip(H_BAY)
    part.label = "tag_strip_rack"
    return part


if __name__ == "__main__":
    tag_strip_rack()
