import time

from fastapi.testclient import TestClient

from rackbot.system import System
from rackbot.web.app import create_app


def wait(pred, timeout=15):
    t0 = time.monotonic()
    while not pred():
        assert time.monotonic() - t0 < timeout, "timeout"
        time.sleep(0.02)


def test_api_smoke(cfg):
    system = System(cfg, sim=True, db_path=":memory:")
    with TestClient(create_app(system)) as client:
        wait(lambda: client.get("/api/robot").json()["mission"]["state"] == "IDLE_DOCKED")
        rack = client.get("/api/rack").json()
        assert [b["caddy"] for b in rack["bays"]] == [101, 102, 103, 104]
        assert client.get("/").status_code == 200
        assert client.get("/static/app.js").status_code == 200

        client.post("/api/auto", json={"on": False})
        r = client.post("/api/jobs", json={"bay": 2})
        assert r.status_code == 201
        job_id = r.json()["id"]
        assert client.post("/api/jobs", json={"bay": 2}).status_code == 409
        assert client.post("/api/jobs", json={"bay": 7}).status_code == 409
        assert client.post("/api/robot/fly").status_code == 404
        assert client.post("/api/bays/1/fault").json()["fault_ramp"] is True

        with client.websocket_connect("/ws") as ws:
            msg = ws.receive_json()
            assert {"rack", "robot", "energy", "jobs", "events"} <= msg.keys()

        wait(lambda: client.get("/api/jobs").json()[0]["result"] == "ok", 20)
        jobs = client.get("/api/jobs").json()
        assert jobs[0]["id"] == job_id and jobs[0]["cycle_s"] > 0
        assert client.get("/api/energy").json()["wh_per_swap"] > 0

        r = client.post("/api/sim/restock", json={})
        assert r.json() == {"removed": 102, "s1": 106}
        assert client.get("/video.mjpg").status_code == 503
