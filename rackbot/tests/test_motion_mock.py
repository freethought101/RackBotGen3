import pytest

from rackbot.motion import MotionError


async def expect_err(coro, code):
    with pytest.raises(MotionError) as ei:
        await coro
    assert ei.value.code == code


async def test_interlocks_when_homed_and_docked(system):
    m, g = system.motion, system.cfg.geometry
    await m.move_y(50)
    await expect_err(m.move_z(150), "E_INTERLOCK")             # Z needs Y <= 2
    await expect_err(m.drive(100), "E_INTERLOCK")              # DRIVE needs Y <= 2
    await expect_err(m.finger("A", "ENGAGE"), "E_INTERLOCK")   # no swinging mid-stroke
    await m.move_y(0)
    await expect_err(m.move_y(g.y_max + 1), "E_LIMIT")
    await expect_err(m.move_z(g.z_soft_max + 1), "E_LIMIT")
    await m.move_z(g.z_drive_max + 10)
    await expect_err(m.turn(90), "E_INTERLOCK")                # Z too high to drive


async def test_y_needs_dock_unless_bench(system):
    m = system.motion
    await m.move_z(system.cfg.geometry.z_approach)
    await m.drive(-250)
    await expect_err(m.move_y(50), "E_INTERLOCK")
    await m.configure("bench", 1)
    await m.move_y(50)


async def test_estop_disables_and_requires_reconfig(system):
    m = system.motion
    m.set_estop(True)
    await expect_err(m.enable(True), "E_ESTOP")
    m.set_estop(False)
    await expect_err(m.enable(True), "E_ESTOP")  # drivers not re-configured yet
    await system.clock.sleep(0.5)
    await m.enable(True)
    await expect_err(m.move_z(150), "E_NOT_HOMED")
    await expect_err(m.home("Z"), "E_NOT_HOMED")  # Y before Z


async def test_vel_watchdog(system):
    m, w = system.motion, system.world
    await m.move_z(system.cfg.geometry.z_approach)
    await m.drive(-250)
    y0 = w.y
    await m.vel(100, 0)
    await system.clock.sleep(1.0)
    m.update_pose()
    moved = abs(w.y - y0)
    assert 25 <= moved <= 35  # 100 mm/s for 0.3 s, then the watchdog stops it
