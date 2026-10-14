"""Energy accounting from motion telemetry (03-software §7): Wh used and Wh charged."""

from __future__ import annotations

from .protocol import Telemetry


class EnergyMeter:
    MAX_GAP_S = 2.0  # ignore gaps (link loss) instead of integrating across them

    def __init__(self):
        self.wh_used = 0.0  # cumulative discharge
        self.wh_charged = 0.0  # cumulative charge from the dock
        self.wh_active = 0.0  # discharge while a job runs
        self.wh_idle = 0.0
        self.power_w = 0.0
        self._last_t: int | None = None
        self.active = False

    def on_telemetry(self, tel: Telemetry) -> None:
        self.power_w = tel.vbat * tel.ibat
        if self._last_t is not None:
            dt = (tel.t - self._last_t) / 1000.0
            if 0 < dt <= self.MAX_GAP_S:
                wh = self.power_w * dt / 3600.0
                if wh >= 0:
                    self.wh_used += wh
                    if self.active:
                        self.wh_active += wh
                    else:
                        self.wh_idle += wh
                else:
                    self.wh_charged -= wh
        self._last_t = tel.t

    def snapshot(self) -> dict:
        return {
            "power_w": round(self.power_w, 2),
            "wh_used": round(self.wh_used, 4),
            "wh_charged": round(self.wh_charged, 4),
            "wh_active": round(self.wh_active, 4),
            "wh_idle": round(self.wh_idle, 4),
        }
