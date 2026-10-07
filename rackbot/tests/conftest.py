import asyncio
import time

import pytest

from rackbot.config import Config
from rackbot.system import System

TIME_SCALE = 0.01  # 100x faster than real time: a full swap takes ~1.6 s


@pytest.fixture
def cfg():
    return Config.load(overrides={"sim": {"time_scale": TIME_SCALE}, "health": {"fault_ramp_s": 2}})


async def wait_until(pred, timeout=15.0, what="condition"):
    t0 = time.monotonic()
    while not pred():
        if time.monotonic() - t0 > timeout:
            raise AssertionError(f"timed out waiting for {what}")
        await asyncio.sleep(0.005)


@pytest.fixture
async def system(cfg):
    s = System(cfg, sim=True, db_path=":memory:")
    s.auto_mode = False
    await s.start()
    await wait_until(lambda: s.mission.state.value == "IDLE_DOCKED", what="startup")
    yield s
    await s.stop()
