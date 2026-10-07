"""SQLite persistence: jobs, events, energy samples and the caddy inventory."""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bay INTEGER NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual',
    caddy_out INTEGER,
    caddy_in INTEGER,
    created REAL NOT NULL,
    started REAL,
    ended REAL,
    result TEXT NOT NULL DEFAULT 'queued',
    detail TEXT,
    wh REAL,
    cycle_s REAL,
    states TEXT
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    level TEXT NOT NULL,
    source TEXT NOT NULL,
    msg TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS energy (
    ts REAL NOT NULL,
    vbat REAL, ibat REAL, wh_used REAL, wh_charged REAL
);
CREATE TABLE IF NOT EXISTS inventory (
    caddy INTEGER PRIMARY KEY,
    location TEXT
);
"""


class Store:
    def __init__(self, path: str = ":memory:"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    # --- events -----------------------------------------------------------------------------------
    def log_event(self, level: str, source: str, msg: str, ts: float | None = None) -> dict:
        ts = ts or time.time()
        cur = self.db.execute("INSERT INTO events (ts, level, source, msg) VALUES (?,?,?,?)", (ts, level, source, msg))
        self.db.commit()
        return {"id": cur.lastrowid, "ts": ts, "level": level, "source": source, "msg": msg}

    def events(self, limit: int = 100, min_level: str | None = None) -> list[dict]:
        if min_level == "warn":
            rows = self.db.execute(
                "SELECT * FROM events WHERE level IN ('warn','error') ORDER BY id DESC LIMIT ?", (limit,))
        else:
            rows = self.db.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in rows]

    # --- jobs -------------------------------------------------------------------------------------
    def create_job(self, bay: int, source: str = "manual") -> dict:
        cur = self.db.execute("INSERT INTO jobs (bay, source, created) VALUES (?,?,?)", (bay, source, time.time()))
        self.db.commit()
        return self.job(cur.lastrowid)

    def update_job(self, job_id: int, **fields: Any) -> None:
        if "states" in fields and not isinstance(fields["states"], str):
            fields["states"] = json.dumps(fields["states"])
        cols = ", ".join(f"{k} = ?" for k in fields)
        self.db.execute(f"UPDATE jobs SET {cols} WHERE id = ?", (*fields.values(), job_id))
        self.db.commit()

    def job(self, job_id: int) -> dict | None:
        row = self.db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return _job(row) if row else None

    def jobs(self, limit: int = 50) -> list[dict]:
        return [_job(r) for r in self.db.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT ?", (limit,))]

    def open_jobs(self) -> list[dict]:
        rows = self.db.execute("SELECT * FROM jobs WHERE result IN ('queued','running','fault') ORDER BY id")
        return [_job(r) for r in rows]

    # --- energy -----------------------------------------------------------------------------------
    def add_energy(self, ts: float, vbat: float, ibat: float, wh_used: float, wh_charged: float) -> None:
        self.db.execute("INSERT INTO energy VALUES (?,?,?,?,?)", (ts, vbat, ibat, wh_used, wh_charged))
        self.db.commit()

    def energy_samples(self, since: float = 0.0, limit: int = 600) -> list[dict]:
        rows = self.db.execute(
            "SELECT * FROM (SELECT * FROM energy WHERE ts >= ? ORDER BY ts DESC LIMIT ?) ORDER BY ts", (since, limit))
        return [dict(r) for r in rows]

    # --- inventory --------------------------------------------------------------------------------
    def inventory(self) -> dict[str, int]:
        """location -> caddy for every placed caddy."""
        rows = self.db.execute("SELECT caddy, location FROM inventory WHERE location IS NOT NULL")
        return {r["location"]: r["caddy"] for r in rows}

    def seed_inventory(self, initial: dict[str, int]) -> None:
        if self.db.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]:
            return
        for loc, caddy in initial.items():
            self.db.execute("INSERT INTO inventory VALUES (?,?)", (int(caddy), loc))
        self.db.commit()

    def move_caddy(self, caddy: int, location: str | None) -> None:
        if location is not None:  # a location holds one caddy
            self.db.execute("UPDATE inventory SET location = NULL WHERE location = ? AND caddy != ?", (location, caddy))
        self.db.execute(
            "INSERT INTO inventory VALUES (?,?) ON CONFLICT(caddy) DO UPDATE SET location = excluded.location",
            (caddy, location))
        self.db.commit()


def _job(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["states"] = json.loads(d["states"]) if d["states"] else []
    return d
