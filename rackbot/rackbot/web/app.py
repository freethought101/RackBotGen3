"""FastAPI app: REST API, WebSocket state push and the static dashboard (03-software §7)."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..mission import JobRejected
from ..system import System

STATIC = Path(__file__).parent / "static"


class JobRequest(BaseModel):
    bay: int


class AutoMode(BaseModel):
    on: bool


class EstopRequest(BaseModel):
    pressed: bool


class RestockRequest(BaseModel):
    caddy: int | None = None


def create_app(system: System, manage_lifecycle: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if manage_lifecycle:
            await system.start()
        yield
        if manage_lifecycle:
            await system.stop()

    app = FastAPI(title="RackBotGen3", lifespan=lifespan)
    app.state.system = system

    def state() -> dict:
        return {
            "rack": system.rack_view(),
            "robot": system.robot_view(),
            "energy": system.energy_view(),
            "jobs": system.store.jobs(20),
            "events": list(system.recent_events)[-30:],
        }

    def rejected(exc: Exception) -> HTTPException:
        return HTTPException(status_code=409, detail=str(exc))

    # --- read ---------------------------------------------------------------------------------------
    @app.get("/api/rack")
    def get_rack():
        return system.rack_view()

    @app.get("/api/robot")
    def get_robot():
        return system.robot_view()

    @app.get("/api/jobs")
    def get_jobs(limit: int = 50):
        return system.store.jobs(limit)

    @app.get("/api/energy")
    def get_energy():
        return {**system.energy_view(), "samples": system.store.energy_samples(limit=300)}

    @app.get("/api/events")
    def get_events(limit: int = 100, level: str | None = None):
        return system.store.events(limit, level)

    @app.get("/api/state")
    def get_state():
        return state()

    # --- control ------------------------------------------------------------------------------------
    @app.post("/api/jobs", status_code=201)
    def post_job(req: JobRequest):
        try:
            return system.mission.submit(req.bay)
        except JobRejected as exc:
            raise rejected(exc) from None

    @app.post("/api/bays/{n}/fault")
    def inject_fault(n: int):
        if not 1 <= n <= system.cfg.n_bays:
            raise HTTPException(404, f"no bay {n}")
        caddy = system.bay_caddies()[n - 1]
        if caddy is None:
            raise HTTPException(409, f"bay {n} has no caddy")
        system.health.inject_fault(caddy)
        system.event("warn", "operator", f"fault injected on bay {n} (caddy {caddy})")
        return system.health.get(caddy).to_dict()

    @app.post("/api/robot/{action}")
    def robot_action(action: str):
        m = system.mission
        actions = {"pause": m.pause, "resume": m.resume, "abort": m.abort, "home": m.request_home}
        if action not in actions:
            raise HTTPException(404, f"unknown action {action}")
        try:
            actions[action]()
        except JobRejected as exc:
            raise rejected(exc) from None
        return m.snapshot()

    @app.post("/api/auto")
    def set_auto(req: AutoMode):
        system.auto_mode = req.on
        system.event("info", "operator", f"auto mode {'on' if req.on else 'off'}")
        return {"auto_mode": system.auto_mode}

    # --- simulator only -----------------------------------------------------------------------------
    def need_sim():
        if not system.sim:
            raise HTTPException(404, "simulator endpoints are only available with --sim")

    @app.post("/api/sim/estop")
    def sim_estop(req: EstopRequest):
        need_sim()
        system.motion.set_estop(req.pressed)
        return {"pressed": req.pressed}

    @app.post("/api/sim/restock")
    def sim_restock(req: RestockRequest):
        """Operator takes the RMA caddy out of S2 and puts a good caddy in S1."""
        need_sim()
        inv = system.store.inventory()
        placed = set(inv.values())
        new = req.caddy or next((c for c in system.cfg.tags.caddy_ids if c not in placed), None)
        if inv.get("S1") is not None:
            new = None
        removed = system.world.restock(new)
        if removed is not None:
            system.store.move_caddy(removed, None)
            system.health.drives.pop(removed, None)  # the drive gets replaced in its caddy
        if new is not None:
            system.store.move_caddy(new, "S1")
        system.event("info", "operator", f"spare station restocked: removed {removed}, S1 = {new or inv.get('S1')}")
        return {"removed": removed, "s1": new or inv.get("S1")}

    # --- camera -------------------------------------------------------------------------------------
    @app.get("/video.mjpg")
    def video():
        raise HTTPException(503, "camera stream not available" + (" in simulation" if system.sim else " yet"))

    # --- push ---------------------------------------------------------------------------------------
    @app.websocket("/ws")
    async def ws(socket: WebSocket):
        await socket.accept()
        period = 1.0 / float(system.cfg.web.ws_hz)
        try:
            while True:
                await socket.send_json(state())
                await asyncio.sleep(period)
        except (WebSocketDisconnect, RuntimeError):
            pass

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app
