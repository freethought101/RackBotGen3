"""SerialMotion (Pi side) against the real firmware core (firmware/motion, host simulator on a pty).

Checks that both ends agree on the §3 wire protocol. Skipped if the simulator is not built:
    make -C ../firmware/motion/sim
"""

import asyncio
import subprocess
from pathlib import Path

import pytest

from rackbot.clock import Clock
from rackbot.motion import MotionError, SerialMotion
from rackbot.protocol import Event

FWSIM = Path(__file__).resolve().parents[2] / "firmware" / "motion" / "sim" / "build" / "fwsim"
SPEED = 10  # simulator runs 10x real time

pytestmark = pytest.mark.skipif(not FWSIM.exists(), reason="firmware simulator not built")


@pytest.fixture
async def link(cfg):
    proc = subprocess.Popen([str(FWSIM), "--speed", str(SPEED)], stdout=subprocess.PIPE, text=True)
    port = proc.stdout.readline().strip()
    cfg["motion"]["port"] = port
    motion = SerialMotion(cfg, Clock(1.0))
    events = []
    motion.subscribe(lambda item: events.append(item) if isinstance(item, Event) else None)
    await motion.start()
    try:
        yield motion, events
    finally:
        await motion.close()
        proc.kill()
        proc.wait()


async def enable(motion):
    for _ in range(50):  # the drivers are configured shortly after boot
        try:
            return await motion.enable(True)
        except MotionError as exc:
            assert exc.code == "E_ESTOP"
            await asyncio.sleep(0.05)
    raise AssertionError("ENABLE never accepted")


async def test_protocol_roundtrip(link):
    motion, events = link
    assert (await motion.ping()).startswith("RBG3-FW ")
    await enable(motion)
    assert any(e.name == "ESTOP_CLEAR" for e in events)

    with pytest.raises(MotionError) as ei:
        await motion.home("Z")
    assert ei.value.code == "E_NOT_HOMED"
    await motion.home("Y")
    await motion.home("Z")
    tel = await motion.status()
    assert tel.homed == "ZY" and tel.en and tel.nose
    assert tel.z == pytest.approx(100, abs=0.01) and tel.y == pytest.approx(0, abs=0.01)

    await motion.move_z(150)
    await motion.move_y(177)
    with pytest.raises(MotionError) as ei:
        await motion.move_z(160)  # Y extended
    assert ei.value.code == "E_INTERLOCK"
    await motion.finger("A", "ENGAGE")
    await motion.move_y(0)
    tel = await motion.status()
    assert tel.z == pytest.approx(150, abs=0.01) and tel.fa == "E" and tel.fb == "P"

    await motion.configure("bench", 1)
    with pytest.raises(MotionError) as ei:
        await motion.configure("warp", 9)
    assert ei.value.code == "E_ARG"


async def test_stop_cancels_with_e_stopped(link):
    motion, _ = link
    await enable(motion)
    await motion.home("Y")
    await motion.home("Z")
    drive = asyncio.create_task(motion.drive(2000))
    await asyncio.sleep(0.2)
    await motion.stop()
    with pytest.raises(MotionError) as ei:
        await drive
    assert ei.value.code == "E_STOPPED"
