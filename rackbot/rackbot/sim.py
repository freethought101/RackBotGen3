"""Shared simulated world for --sim: robot pose, stations, shelves, caddies, rack inputs.

MockMotion, MockRack and SimVision all read and write this one object, so a pull done by the mock
firmware clears the PLC presence bit the mission then checks, exactly as on the real rack.

World frame: rack approach tag 0 at the origin, facing +y. The spare station faces it at
y = station_distance. The robot pose is the camera position (mm) and heading (deg, CCW from +x).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .config import Config
from .vision import TagPose


def wrap_deg(a: float) -> float:
    return (a + 180.0) % 360.0 - 180.0


@dataclass
class Station:
    name: str
    tag_id: int
    x: float
    y: float
    normal: float  # deg, direction the station faces (out toward the robot)
    shelves: dict[float, int | None] = field(default_factory=dict)  # shelf height -> caddy ID


class SimWorld:
    SHELF_TOL = 2.5  # tray slot floor must be within this of the shelf floor for a stroke

    def __init__(self, cfg: Config, inventory: dict[str, int]):
        self.cfg = cfg
        sim = cfg.sim
        g = cfg.geometry
        self.dock_d = float(sim.dock_d_mm)
        self.turn_error = float(sim.turn_error_deg)
        dist = float(sim.station_distance_mm)
        self.stations = {
            "rack": Station("rack", cfg.station_tag("rack"), 0.0, 0.0, 90.0,
                            {float(h): None for h in g.h_bay}),
            "spare": Station("spare", cfg.station_tag("spare"), 0.0, dist, -90.0,
                             {float(h): None for h in g.h_spare.values()}),
        }
        for loc, caddy in inventory.items():
            if loc.startswith(("bay", "S")):
                shelf = cfg.shelf_by_location(loc)
                self.stations[shelf.station].shelves[float(shelf.height)] = caddy
        self.tray: dict[str, int | None] = {"A": inventory.get("trayA"), "B": inventory.get("trayB")}
        self.docked_at: str | None = "rack"
        self.x, self.y, self.th = self.dock_pose("rack")
        self.dock_power = False  # PLC output Y0
        self.rack_estop_ok = True  # PLC input X5
        self.robot_estop = False  # robot mushroom pressed
        self.shelf_z_error: dict[int, float] = {}  # shelf tag -> Z miscalibration (mm) seen by vision
        self.incidents: list[str] = []  # physical problems the mock detected (dragged caddy, ...)

    # --- geometry ---------------------------------------------------------------------------------
    def dock_pose(self, name: str) -> tuple[float, float, float]:
        st = self.stations[name]
        n = math.radians(st.normal)
        return st.x + self.dock_d * math.cos(n), st.y + self.dock_d * math.sin(n), wrap_deg(st.normal + 180)

    def station_by_tag(self, tag_id: int) -> Station | None:
        return next((s for s in self.stations.values() if s.tag_id == tag_id), None)

    def observe(self, tag_id: int, fov_deg: float = 100.0, max_d: float = 3000.0) -> TagPose | None:
        """Pose of a station approach tag in the camera frame, or None if not visible."""
        st = self.station_by_tag(tag_id)
        if st is None:
            return None
        vx, vy = st.x - self.x, st.y - self.y
        h = math.radians(self.th)
        forward = vx * math.cos(h) + vy * math.sin(h)
        right = vx * math.sin(h) - vy * math.cos(h)
        if forward < 20 or forward > max_d:
            return None
        theta = math.degrees(math.atan2(right, forward))
        if abs(theta) > fov_deg / 2:
            return None
        psi = wrap_deg(self.th - (st.normal + 180))
        if abs(psi) > 60:  # tag seen too obliquely to decode
            return None
        return TagPose(tag_id=tag_id, d=forward, x=right, theta=theta, psi=psi)

    def facing_offset(self, name: str) -> tuple[float, float, float]:
        """(distance along the station normal, lateral offset, heading error) of the camera."""
        st = self.stations[name]
        n = math.radians(st.normal)
        vx, vy = self.x - st.x, self.y - st.y
        along = vx * math.cos(n) + vy * math.sin(n)
        lateral = -vx * math.sin(n) + vy * math.cos(n)
        return along, lateral, wrap_deg(self.th - (st.normal + 180))

    # --- caddies ----------------------------------------------------------------------------------
    def shelf_level(self, slot_floor: float) -> float | None:
        """Shelf height at the docked station within tolerance of a tray slot floor."""
        if self.docked_at is None:
            return None
        for h in self.stations[self.docked_at].shelves:
            if abs(h - slot_floor) <= self.SHELF_TOL:
                return h
        return None

    def caddy_on_shelf(self, station: str, h: float) -> int | None:
        return self.stations[station].shelves.get(float(h))

    def bay_present(self) -> list[bool]:
        return [c is not None for c in self.stations["rack"].shelves.values()]

    def spare_present(self) -> dict[str, bool]:
        spare = self.stations["spare"].shelves
        return {name: spare[float(h)] is not None for name, h in self.cfg.geometry.h_spare.items()}

    def locate(self, caddy: int) -> str | None:
        for slot, c in self.tray.items():
            if c == caddy:
                return f"tray{slot}"
        for st in self.stations.values():
            for h, c in st.shelves.items():
                if c == caddy:
                    shelf = self._shelf_name(st.name, h)
                    return shelf
        return None

    def _shelf_name(self, station: str, h: float) -> str:
        if station == "rack":
            return f"bay{list(self.stations['rack'].shelves).index(h) + 1}"
        return next(n for n, hh in self.cfg.geometry.h_spare.items() if float(hh) == h)

    # --- operator actions (sim only) --------------------------------------------------------------
    def restock(self, new_caddy: int | None) -> int | None:
        """Operator empties S2 (RMA) and puts a good caddy in S1. Returns the removed RMA caddy."""
        h = self.cfg.geometry.h_spare
        spare = self.stations["spare"].shelves
        removed = spare[float(h["S2"])]
        spare[float(h["S2"])] = None
        if spare[float(h["S1"])] is None and new_caddy is not None:
            spare[float(h["S1"])] = new_caddy
        return removed
