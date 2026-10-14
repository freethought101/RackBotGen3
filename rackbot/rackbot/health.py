"""Simulated drive health (03-software §7): synthetic SMART values per caddy and fault injection."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass


@dataclass
class Smart:
    caddy: int
    temp_c: float
    realloc: int
    poh: float  # power-on hours
    status: str = "OK"  # OK | WARN | FAILED
    fault_ramp: bool = False

    def to_dict(self) -> dict:
        d = asdict(self)
        d["temp_c"] = round(self.temp_c, 1)
        d["poh"] = int(self.poh)
        return d


class HealthModel:
    def __init__(self, cfg, caddy_ids: list[int], seed: int = 3):
        self.cfg = cfg.health
        self.rng = random.Random(seed)
        self.drives: dict[int, Smart] = {
            c: Smart(c, temp_c=self.rng.uniform(31, 38), realloc=self.rng.randint(0, 2),
                     poh=self.rng.uniform(4000, 30000))
            for c in caddy_ids
        }
        self._ramp_rate = self.cfg.fail_realloc / self.cfg.fault_ramp_s  # sectors/s
        self._acc: dict[int, float] = {}

    def get(self, caddy: int) -> Smart:
        if caddy not in self.drives:
            self.drives[caddy] = Smart(caddy, temp_c=34.0, realloc=0, poh=0.0)
        return self.drives[caddy]

    def inject_fault(self, caddy: int) -> None:
        self.get(caddy).fault_ramp = True

    def tick(self, dt: float, spinning: set[int]) -> list[Smart]:
        """Advance the model by dt seconds. Returns drives whose status changed."""
        changed = []
        for d in self.drives.values():
            if d.caddy in spinning:
                d.poh += dt / 3600.0 * 60  # time-lapse so the dashboard visibly ticks
                target = 36.0 + (6.0 if d.fault_ramp else 0.0)
                d.temp_c += (target - d.temp_c) * min(1.0, dt / 30.0) + self.rng.uniform(-0.05, 0.05)
            if d.fault_ramp and d.realloc < self.cfg.fail_realloc:
                acc = self._acc.get(d.caddy, 0.0) + self._ramp_rate * dt
                whole = int(acc)
                self._acc[d.caddy] = acc - whole
                d.realloc = min(self.cfg.fail_realloc, d.realloc + whole)
            status = self._status(d)
            if status != d.status:
                d.status = status
                changed.append(d)
        return changed

    def _status(self, d: Smart) -> str:
        if d.realloc >= self.cfg.fail_realloc:
            return "FAILED"
        if d.realloc >= self.cfg.warn_realloc:
            return "WARN"
        return "OK"
