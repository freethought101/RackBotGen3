"""Configuration loading and the geometry helpers of 03-software §5.1."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "config.yaml"
# The station with the charging contacts and the PLC dock switch (X4): the robot waits and charges here.
HOME = "spare"


class Section(dict):
    """A dict with attribute access, recursively (cfg.geometry.y_pull)."""

    def __getattr__(self, name: str) -> Any:
        try:
            value = self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc
        return Section(value) if isinstance(value, dict) and not isinstance(value, Section) else value


class Op(str, Enum):
    INSERT = "INSERT"
    EXTRACT = "EXTRACT"


@dataclass(frozen=True)
class Shelf:
    """A shelf the robot can serve: a rack bay (1-4) or a spare slot (S1/S2)."""

    station: str  # "rack" | "spare"
    name: str  # "1".."4" | "S1" | "S2"
    height: float
    tag_id: int

    @property
    def location(self) -> str:
        """Inventory location key ("bay2", "S1")."""
        return f"bay{self.name}" if self.station == "rack" else self.name


class Config(Section):
    @classmethod
    def load(cls, path: str | Path | None = None, overrides: dict | None = None) -> "Config":
        with open(path or DEFAULT_PATH) as fh:
            data = yaml.safe_load(fh)
        if overrides:
            data = _merge(data, overrides)
        return cls(data)

    # --- geometry ---------------------------------------------------------------------------------
    def z_for(self, slot: str, shelf_h: float, op: Op) -> float:
        """Lift height (slot B floor) that puts tray `slot` level with a shelf for `op` (03 §5.1)."""
        g = self.geometry
        offset = g.z_insert_offset if op == Op.INSERT else g.z_extract_offset
        return shelf_h + offset - (g.bay_pitch if slot == "A" else 0)

    def bay(self, n: int) -> Shelf:
        if not 1 <= n <= len(self.geometry.h_bay):
            raise ValueError(f"no bay {n}")
        return Shelf("rack", str(n), self.geometry.h_bay[n - 1], int(self.stations.rack.shelf_tags[n]))

    def spare(self, name: str) -> Shelf:
        return Shelf("spare", name, self.geometry.h_spare[name], int(self.stations.spare.shelf_tags[name]))

    @property
    def n_bays(self) -> int:
        return len(self.geometry.h_bay)

    def shelf_by_location(self, location: str) -> Shelf:
        return self.bay(int(location[3:])) if location.startswith("bay") else self.spare(location)

    def station_tag(self, station: str) -> int:
        return int(self.stations[station]["approach_tag"])


def _merge(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out
