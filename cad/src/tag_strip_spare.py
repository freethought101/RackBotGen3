"""Tag strip (PLA): 2 slot tags (IDs 11-12), front-left upright of the spare station."""

from cadgen import step, stl

from lib.dims import H_SPARE
from lib.tags import tag_strip


@step(out="../STEP/tag_strip_spare.step")
@stl(out="../STL/tag_strip_spare.stl")
def tag_strip_spare():
    part = tag_strip(H_SPARE)
    part.label = "tag_strip_spare"
    return part


if __name__ == "__main__":
    tag_strip_spare()
