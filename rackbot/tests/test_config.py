import pytest

from rackbot.config import Op


@pytest.mark.parametrize("slot,h,op,z", [
    ("B", 195, Op.EXTRACT, 194),   # pull the failed caddy out of bay 2 into slot B
    ("B", 195, Op.INSERT, 196),    # RMA caddy into S2
    ("A", 150, Op.EXTRACT, 104),   # pick the good spare from S1 into slot A
    ("A", 285, Op.INSERT, 241),    # insert into bay 4 from slot A
])
def test_z_for(cfg, slot, h, op, z):
    assert cfg.z_for(slot, h, op) == z


def test_z_for_stays_inside_soft_limits(cfg):
    g = cfg.geometry
    heights = list(g.h_bay) + list(g.h_spare.values())
    for h in heights:
        for slot in "AB":
            for op in Op:
                assert g.z_soft_min <= cfg.z_for(slot, h, op) <= g.z_soft_max


def test_shelves(cfg):
    assert cfg.bay(3).height == 240 and cfg.bay(3).tag_id == 3 and cfg.bay(3).location == "bay3"
    assert cfg.spare("S2").height == 195 and cfg.spare("S2").tag_id == 12
    assert cfg.shelf_by_location("bay1") == cfg.bay(1)
    with pytest.raises(ValueError):
        cfg.bay(5)


def test_z_approach_allows_driving(cfg):
    assert cfg.geometry.z_approach <= cfg.geometry.z_drive_max
