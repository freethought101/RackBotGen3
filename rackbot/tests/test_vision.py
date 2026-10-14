import math

from rackbot.sim import SimWorld
from rackbot.vision import TagPose, approach_step


def test_handoff_and_too_close(cfg):
    ap = cfg.approach
    assert approach_step(TagPose(0, d=255, x=3, theta=0.7, psi=1), ap).handoff
    assert not approach_step(TagPose(0, d=255, x=15, theta=3, psi=1), ap).handoff
    assert approach_step(TagPose(0, d=190, x=15, theta=4, psi=1), ap).too_close


def test_speed_clamp_and_steering_sign(cfg):
    ap = cfg.approach
    far = approach_step(TagPose(0, d=1500, x=0, theta=0, psi=0), ap)
    assert far.v == ap.v_max and far.w == 0
    near = approach_step(TagPose(0, d=262, x=40, theta=8, psi=0), ap)
    assert near.v == ap.v_min
    assert near.w < 0  # tag to the right -> turn clockwise


def test_sim_observation_conventions(cfg):
    w = SimWorld(cfg, {})
    w.docked_at = None
    # 600 mm in front of the rack tag, facing it squarely, 30 mm to its left (as seen from the robot)
    w.x, w.y, w.th = 30.0, 600.0, -90.0
    p = w.observe(0)
    assert math.isclose(p.d, 600, abs_tol=1e-6) and p.x > 0 and p.theta > 0 and abs(p.psi) < 1e-9
    w.th = -80.0  # turned 10 deg counter-clockwise
    assert math.isclose(w.observe(0).psi, 10.0, abs_tol=1e-9)
    w.th = 90.0  # facing away
    assert w.observe(0) is None
