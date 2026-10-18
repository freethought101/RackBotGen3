import pytest

from rackbot.mission import JOB_STATES, S
from tests.conftest import wait_until


def job_result(system, job_id):
    return system.store.job(job_id)["result"]


async def run_job(system, bay, timeout=20.0):
    job = system.mission.submit(bay)
    await wait_until(lambda: job_result(system, job["id"]) not in ("queued", "running"), timeout, "job end")
    return system.store.job(job["id"])


def assert_swapped(system, bay, out, new):
    inv = system.store.inventory()
    assert inv[f"bay{bay}"] == new and inv["S2"] == out and "S1" not in inv
    assert system.world.caddy_on_shelf("rack", system.cfg.bay(bay).height) == new
    assert system.world.locate(out) == "S2"
    assert system.world.tray == {"A": None, "B": None}
    assert system.world.incidents == []


async def test_full_swap(system):
    job = await run_job(system, 2)
    assert job["result"] == "ok", job
    assert job["caddy_out"] == 102 and job["caddy_in"] == 105
    assert [s["state"] for s in job["states"]] == [s.value for s in JOB_STATES] + ["END"]
    assert 60 < job["cycle_s"] < 300 and 0.2 < job["wh"] < 2.0
    assert_swapped(system, 2, 102, 105)
    assert system.mission.state == S.IDLE_DOCKED and system.mission.location == "spare"
    await wait_until(lambda: system.rack.state.dock_power, what="dock power")


async def test_two_swaps_with_restock(system):
    assert (await run_job(system, 1))["result"] == "ok"
    rejected = await run_job(system, 3)
    assert rejected["result"] == "rejected" and "S1" in rejected["detail"]
    system.world.restock(106)
    system.store.move_caddy(101, None)
    system.store.move_caddy(106, "S1")
    assert (await run_job(system, 3))["result"] == "ok"
    assert system.store.inventory()["bay3"] == 106


# RETURN only drives after an abort (a job ends docked at home); that drive is in test_abort_*.
@pytest.mark.parametrize("state", JOB_STATES[:-1], ids=lambda s: s.value)
async def test_estop_in_every_state_then_resume(system, state):
    m = system.mission
    job = m.submit(4)
    await wait_until(lambda: m.state == state, what=state.value)
    await system.clock.sleep(0.2)
    system.motion.set_estop(True)
    await wait_until(lambda: m.state == S.FAULT, what="FAULT")
    assert m.fault.code == "E_ESTOP"
    assert job_result(system, job["id"]) == "fault"
    system.motion.set_estop(False)
    await wait_until(lambda: not m.estop, what="estop clear")
    m.resume()
    await wait_until(lambda: job_result(system, job["id"]) not in ("queued", "running", "fault"), 20, "job end")
    assert job_result(system, job["id"]) == "ok", system.store.events(20)
    assert_swapped(system, 4, 104, 105)


async def test_caddy_id_mismatch_faults(system):
    rack = system.world.stations["rack"].shelves
    rack[195.0] = 106  # someone swapped bay 2 by hand; inventory still says 102
    job = system.mission.submit(2)
    await wait_until(lambda: system.mission.state == S.FAULT, what="FAULT")
    assert system.mission.fault.code == "E_CADDY_ID" and system.mission.fault_state == S.EXTRACT_FAILED
    system.mission.abort()
    await wait_until(lambda: job_result(system, job["id"]) == "aborted", what="aborted")
    await wait_until(lambda: system.mission.state == S.IDLE_DOCKED, what="back home")
    assert system.mission.location == "spare"


async def test_bay_alignment_error_faults(system):
    system.world.shelf_z_error[3] = 6.0  # bay 3 tag 6 mm off: wrong bay or lost calibration
    system.mission.submit(3)
    await wait_until(lambda: system.mission.state == S.FAULT, what="FAULT")
    assert system.mission.fault.code == "E_ALIGN"


async def test_small_alignment_error_is_corrected(system):
    system.world.shelf_z_error[2] = 1.5
    job = await run_job(system, 2)
    assert job["result"] == "ok"


async def test_abort_while_running_returns_home(system):
    m = system.mission
    job = m.submit(1)
    await wait_until(lambda: m.state == S.TO_RACK, what="TO_RACK")
    await system.clock.sleep(2)  # undocked, on the way
    m.abort()
    await wait_until(lambda: job_result(system, job["id"]) == "aborted", what="aborted")
    await wait_until(lambda: m.state == S.IDLE_DOCKED, 20, "back home")
    assert m.location == "spare" and system.world.docked_at == "spare"
    assert system.world.incidents == []


async def test_pause_and_resume(system):
    m = system.mission
    job = m.submit(2)
    await wait_until(lambda: m.state == S.TO_RACK, what="TO_RACK")
    m.pause()
    await system.clock.sleep(5)
    paused_state = m.state
    await system.clock.sleep(20)
    assert m.state == paused_state and job_result(system, job["id"]) == "running"
    m.resume()
    await wait_until(lambda: job_result(system, job["id"]) == "ok", 20, "job end")


async def test_rejections(system):
    from rackbot.mission import JobRejected

    with pytest.raises(JobRejected):
        system.mission.submit(9)
    system.mission.pause()
    system.mission.submit(1)
    with pytest.raises(JobRejected):
        system.mission.submit(1)


async def test_auto_mode_swaps_failed_drive(system):
    system.auto_mode = True
    system.health.inject_fault(103)
    await wait_until(lambda: any(j["source"] == "auto" for j in system.store.jobs()), 10, "auto job")
    job = next(j for j in system.store.jobs() if j["source"] == "auto")
    assert job["bay"] == 3
    await wait_until(lambda: job_result(system, job["id"]) == "ok", 20, "auto job end")
    assert system.store.inventory()["bay3"] == 105
    assert system.health.get(105).status == "OK"


async def test_pi_watchdog_cuts_dock_power(system):
    await wait_until(lambda: system.rack.state.dock_power, what="dock power")
    system.rack.pi_heartbeat_frozen = True
    await wait_until(lambda: system.rack.state.plc_state == "WATCHDOG_LOST", what="watchdog")
    assert not system.rack.state.dock_power and system.rack.state.lamp == "red"
