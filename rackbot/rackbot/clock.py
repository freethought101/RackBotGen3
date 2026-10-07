"""Time source. Real hardware runs at scale 1; the simulator can run faster (scale < 1)."""

from __future__ import annotations

import asyncio
import time


class Clock:
    """`now()` and `sleep()` in simulated seconds. `scale` = real seconds per simulated second."""

    def __init__(self, scale: float = 1.0):
        if scale <= 0:
            raise ValueError("scale must be > 0")
        self.scale = scale
        self._t0 = time.monotonic()

    def now(self) -> float:
        return (time.monotonic() - self._t0) / self.scale

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(max(0.0, seconds) * self.scale)

    async def wait_for(self, awaitable, seconds: float):
        return await asyncio.wait_for(awaitable, seconds * self.scale)

    def wall(self) -> float:
        """Wall-clock timestamp for logs and the database."""
        return time.time()
