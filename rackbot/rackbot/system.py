"""Wires the application together: real hardware or the simulator, plus the background loops
(health model + auto mode, energy sampling, rack lamps)."""

from __future__ import annotations

import asyncio
import logging
from collections import deque

from .clock import Clock
from .config import Config
from .energy import EnergyMeter
from .health import HealthModel
from .mission import JobRejected, Mission, S
from .motion import MockMotion, SerialMotion
from .protocol import Telemetry
from .rack import MockRack, ModbusRack
from .sim import SimWorld
from .store import Store

log = logging.getLogger("rackbot")

_LEVELS = {"debug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARNING, "error": logging.ERROR}


class System:
    def __init__(self, cfg: Config, sim: bool = True, db_path: str | None = None, clock: Clock | None = None):
        self.cfg = cfg
        self.sim = sim
        self.clock = clock or Clock(float(cfg.sim.time_scale) if sim else 1.0)
        self.store = Store(db_path if db_path is not None else cfg.store.path)
        self.store.seed_inventory(dict(cfg.inventory))
        self.recent_events: deque[dict] = deque(maxlen=200)
        self.energy = EnergyMeter()
        self.health = HealthModel(cfg, list(cfg.tags.caddy_ids))
        self.auto_mode = True
        self.world: SimWorld | None = None
        if sim:
            from .vision import SimVision

            self.world = SimWorld(cfg, self.store.inventory())
            self.motion = MockMotion(cfg, self.clock, self.world)
            self.rack = MockRack(cfg, self.clock, self.world)
            self.vision = SimVision(self.world, self.clock, fps=float(cfg.vision.fps))
            self.vision.motion = self.motion
        else:
            from .vision import AprilTagVision

            self.motion = SerialMotion(cfg, self.clock)
            self.rack = ModbusRack(cfg, self.clock)
            self.vision = AprilTagVision(cfg)
        self.motion.subscribe(self._on_motion)
        self.mission = Mission(cfg, self.clock, self.motion, self.rack, self.vision, self.store, self.energy,
                               self.event)
        self._tasks: list[asyncio.Task] = []
        self._last_energy_sample = 0.0

    # --- lifecycle --------------------------------------------------------------------------------
    async def start(self) -> None:
        self.event("info", "system", f"starting ({'simulation' if self.sim else 'hardware'})")
        await self.motion.start()
        await self.rack.start()
        await self.vision.start()
        await self.mission.start()
        self._tasks = [
            asyncio.create_task(self._health_loop(), name="health"),
            asyncio.create_task(self._lamp_loop(), name="lamps"),
        ]

    async def stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        await self.mission.close()
        await self.vision.stop()
        await self.rack.close()
        await self.motion.close()
        self.store.close()

    # --- events -----------------------------------------------------------------------------------
    def event(self, level: str, source: str, msg: str) -> None:
        log.log(_LEVELS.get(level, logging.INFO), "[%s] %s", source, msg)
        if level == "debug" and not msg.startswith("state "):
            return
        self.recent_events.append(self.store.log_event(level, source, msg, self.clock.wall()))

    def _on_motion(self, item) -> None:
        if isinstance(item, Telemetry):
            self.energy.on_telemetry(item)
            now = self.clock.now()
            if now - self._last_energy_sample >= float(self.cfg.energy.sample_s):
                self._last_energy_sample = now
                self.store.add_energy(self.clock.wall(), item.vbat, item.ibat, self.energy.wh_used,
                                      self.energy.wh_charged)

    # --- background loops -------------------------------------------------------------------------
    def bay_caddies(self) -> list[int | None]:
        inv = self.store.inventory()
        return [inv.get(f"bay{n}") for n in range(1, self.cfg.n_bays + 1)]

    async def _health_loop(self) -> None:
        dt = 1.0
        while True:
            await self.clock.sleep(dt)
            bays = self.bay_caddies()
            for d in self.health.tick(dt, {c for c in bays if c is not None}):
                where = self.store_location(d.caddy)
                self.event("warn" if d.status != "OK" else "info", "health",
                           f"caddy {d.caddy} ({where}) is {d.status} ({d.realloc} reallocated sectors)")
            if self.auto_mode:
                self._auto_queue(bays)

    def _auto_queue(self, bays: list[int | None]) -> None:
        open_bays = {j["bay"] for j in self.store.open_jobs()}
        for n, caddy in enumerate(bays, start=1):
            if caddy is None or n in open_bays:
                continue
            if self.health.get(caddy).status == "FAILED":
                try:
                    self.mission.submit(n, source="auto")
                except JobRejected as exc:
                    log.debug("auto job not queued: %s", exc)

    def store_location(self, caddy: int) -> str:
        return next((loc for loc, c in self.store.inventory().items() if c == caddy), "?")

    async def _lamp_loop(self) -> None:
        while True:
            degraded = any(c is not None and self.health.get(c).status != "OK" for c in self.bay_caddies())
            yellow = self.mission.job is not None or degraded
            red = self.mission.state == S.FAULT
            try:
                await self.rack.set_lamps(yellow, red)
            except Exception as exc:
                log.debug("lamp write failed: %s", exc)
            await self.clock.sleep(0.5)

    # --- views for the API ------------------------------------------------------------------------
    def rack_view(self) -> dict:
        rs = self.rack.state
        bays = []
        for n, caddy in enumerate(self.bay_caddies(), start=1):
            h = self.health.get(caddy).to_dict() if caddy is not None else None
            bays.append({"bay": n, "caddy": caddy, "serial": f"RBG3-C{caddy - 100:02d}" if caddy else None,
                         "present": rs.bay_present[n - 1], "health": h})
        inv = self.store.inventory()
        spare = {name: {"caddy": inv.get(name), "present": getattr(rs, f"{name.lower()}_present")}
                 for name in ("S1", "S2")}
        return {"bays": bays, "spare": spare, "plc": rs.to_dict(), "auto_mode": self.auto_mode}

    def robot_view(self) -> dict:
        tel = self.motion.telemetry
        frac = min(1.0, max(0.0, (tel.vbat - 12.0) / 4.8)) if tel.vbat else 0.0
        inv = self.store.inventory()
        return {
            "mission": self.mission.snapshot(),
            "telemetry": tel.to_dict(),
            "docked": tel.nose,
            "battery_pct": round(frac * 100),
            "charging": tel.ibat < 0 and tel.dock > 20,
            "tray": {"A": inv.get("trayA"), "B": inv.get("trayB")},
            "estop": self.mission.estop,
            "sim": self.sim,
        }

    def energy_view(self) -> dict:
        jobs = [j for j in self.store.jobs(100) if j["result"] == "ok" and j["wh"] is not None]
        per_swap = sum(j["wh"] for j in jobs) / len(jobs) if jobs else None
        return {**self.energy.snapshot(), "wh_per_swap": round(per_swap, 4) if per_swap else None,
                "swaps": len(jobs)}
