"""Approach-tag fin (PLA, x2): tag ID 0 on the rack, ID 10 on the spare station."""

from cadgen import step, stl

from lib.tags import tag_fin as make_tag_fin


@step(out="../STEP/tag_fin.step")
@stl(out="../STL/tag_fin.stl")
def tag_fin():
    part = make_tag_fin()
    part.label = "tag_fin"
    return part


if __name__ == "__main__":
    tag_fin()
