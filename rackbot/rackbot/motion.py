"""Motion controller clients (03-software §3, §8).

`SerialMotion` talks to the ESP32 over USB CDC. `MockMotion` is a simulated firmware for --sim:
it enforces the same interlocks, moves axes in (scaled) time and moves caddies in the SimWorld.
Both expose the same high-level API; motion commands return after DONE and raise MotionError
on ERR or FAIL.
"""

from __future__ import annotations

import asyncio
import logging
import math
from abc import ABC, abstractmethod
from typing import Callable

from . import protocol as P
from .protocol import Event, Reply, Telemetry

log = logging.getLogger(__name__)


class MotionError(Exception):
    def __init__(self, code: str, msg: str = "", cmd: str = ""):
        super().__init__(f"{cmd} {code} {msg}".strip())
        self.code = code
        self.msg = msg
        self.cmd = cmd


Listener = Callable[[Event | Telemetry], None]


class MotionBase(ABC):
    def __init__(self, clock):
        self.clock = clock
        self.telemetry = Telemetry()
        self._listeners: list[Listener] = []
        self._tel_waiters: list[asyncio.Future] = []

    def subscribe(self, cb: Listener) -> None:
        self._listeners.append(cb)

    def _emit(self, item: Event | Telemetry) -> None:
        if isinstance(item, Telemetry):
            self.telemetry = item
            for fut in self._tel_waiters:
                if not fut.done():
                    fut.set_result(item)
            self._tel_waiters.clear()
        for cb in self._listeners:
            try:
                cb(item)
            except Exception:  # a broken listener must not stop the motion link
                log.exception("motion listener failed")

    async def start(self) -> None:  # noqa: B027
        pass

    async def close(self) -> None:  # noqa: B027
        pass

    @abstractmethod
    async def request(self, cmd: str, *args: object) -> str:
        """Send a command. Returns the OK data (motion commands: after DONE). Raises MotionError."""

    # --- high-level API ---------------------------------------------------------------------------
    async def ping(self) -> str:
        return await self.request("PING")

    async def enable(self, on: bool = True) -> None:
        await self.request("ENABLE", int(on))

    async def home(self, axis: str) -> None:
        await self.request("HOME", axis)

    async def move_z(self, mm: float, speed: float | None = None) -> None:
        await self.request("Z", float(mm), speed)

    async def move_y(self, mm: float, speed: float | None = None) -> None:
        await self.request("Y", float(mm), speed)

    async def finger(self, which: str, action: str) -> None:
        await self.request("FINGER", which, action)

    async def drive(self, mm: float, speed: float | None = None) -> None:
        await self.request("DRIVE", float(mm), speed)

    async def turn(self, deg: float, speed: float | None = None) -> None:
        await self.request("TURN", float(deg), speed)

    async def vel(self, v: float, w: float) -> None:
        await self.request("VEL", float(v), float(w))

    async def dock(self, max_mm: float, speed: float | None = None) -> None:
        await self.request("DOCK", float(max_mm), speed)

    async def stop(self) -> None:
        await self.request("STOP")

    async def configure(self, key: str, value: object) -> None:
        await self.request("CFG", key, value)

    async def status(self) -> Telemetry:
        fut = asyncio.get_running_loop().create_future()
        self._tel_waiters.append(fut)
        await self.request("STATUS")
        return await self.clock.wait_for(fut, 1.0)


class SerialMotion(MotionBase):
    """ESP32 over USB CDC (115200 8N1, ASCII lines)."""

    def __init__(self, cfg, clock):
        super().__init__(clock)
        self.cfg = cfg
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._task: asyncio.Task | None = None
        self._seq = 0
        self._pending: dict[int, tuple[str, asyncio.Future, asyncio.Future | None]] = {}
        self._write_lock = asyncio.Lock()

    async def start(self) -> None:
        import serial_asyncio

        m = self.cfg.motion
        self._reader, self._writer = await serial_asyncio.open_serial_connection(url=m.port, baudrate=m.baud)
        self._task = asyncio.create_task(self._read_loop(), name="motion-serial")

    async def close(self) -> None:
        if self._task:
            self._task.cancel()
        if self._writer:
            self._writer.close()

    def _next_seq(self) -> int:
        self._seq = self._seq % 65535 + 1
        return self._seq

    async def request(self, cmd: str, *args: object) -> str:
        loop = asyncio.get_running_loop()
        seq = self._next_seq()
        ok = loop.create_future()
        done = loop.create_future() if cmd in P.MOTION_COMMANDS else None
        self._pending[seq] = (cmd, ok, done)
        try:
            async with self._write_lock:
                self._writer.write(P.encode_request(seq, cmd, *args).encode())
                await self._writer.drain()
            m = self.cfg.motion
            try:
                reply: Reply = await asyncio.wait_for(ok, m.command_timeout_s)
            except asyncio.TimeoutError:
                raise MotionError("E_TIMEOUT", "no reply", cmd) from None
            if reply.kind == "ERR":
                raise MotionError(reply.code, reply.data, cmd)
            if done is None:
                return reply.data
            try:
                final: Reply = await asyncio.wait_for(done, m.motion_timeout_s)
            except asyncio.TimeoutError:
                await self.request("STOP")
                raise MotionError("E_TIMEOUT", "no DONE", cmd) from None
            if final.kind == "FAIL":
                raise MotionError(final.code, final.data, cmd)
            return reply.data
        finally:
            self._pending.pop(seq, None)

    async def _read_loop(self) -> None:
        while True:
            raw = await self._reader.readline()
            if not raw:
                log.error("motion serial closed")
                return
            try:
                item = P.parse_line(raw.decode(errors="replace"))
            except P.ProtocolError as exc:
                log.warning("motion: %s", exc)
                continue
            if isinstance(item, Reply):
                pending = self._pending.get(item.seq)
                if pending is None:
                    log.debug("motion: reply for unknown seq %s", item.seq)
                    continue
                _, ok, done = pending
                if item.kind in ("OK", "ERR") and not ok.done():
                    ok.set_result(item)
                elif item.kind in ("DONE", "FAIL") and done is not None and not done.done():
                    done.set_result(item)
            else:
                self._emit(item)


class _Axis:
    """Linear axis with a time-interpolated position (for live telemetry)."""

    def __init__(self, pos: float):
        self.start = self.end = pos
        self.t0 = self.t1 = 0.0

    def pos(self, now: float) -> float:
        if now >= self.t1 or self.t1 <= self.t0:
            return self.end
        f = (now - self.t0) / (self.t1 - self.t0)
        return self.start + (self.end - self.start) * max(0.0, f)

    def plan(self, target: float, speed: float, now: float) -> float:
        self.start, self.end = self.pos(now), target
        self.t0, self.t1 = now, now + abs(target - self.start) / max(speed, 1e-6)
        return self.t1 - now

    def freeze(self, now: float) -> None:
        p = self.pos(now)
        self.start = self.end = p
        self.t0 = self.t1 = now

    @property
    def moving_to(self) -> float:
        return self.end


class MockMotion(MotionBase):
    """Simulated ESP32 firmware. Enforces the §3 interlocks and moves caddies in the SimWorld."""

    Z_HOME_POS = 100.0
    TRACK_MM = 274.0  # wheel centre distance, same as the firmware
    FINGER_S = 0.3
    TEL_HZ = 10.0
    RECONFIG_S = 0.3

    def __init__(self, cfg, clock, world):
        super().__init__(clock)
        self.cfg = cfg
        self.g = cfg.geometry
        self.world = world
        self.en = False
        self.homed: set[str] = set()
        self.needs_reconfig = False
        self.bench = False
        self.settings: dict[str, str] = {}
        self.z = _Axis(float(self.g.z_drive))
        self.y = _Axis(0.0)
        self.fingers = {"A": "P", "B": "P"}
        # caddy carried by each finger: (caddy_id, "tray" | shelf height)
        self.attached: dict[str, tuple[int, object] | None] = {"A": None, "B": None}
        self.l = self.r = 0.0
        self.v = self.w = 0.0
        self.last_vel = -1e9
        self.pose_t = 0.0
        self.busy = ""
        self._task: asyncio.Task | None = None
        self._cancel_code = "E_STOPPED"
        self._tel_task: asyncio.Task | None = None
        self.soc_wh = float(cfg.sim.battery_wh) * float(cfg.sim.battery_soc)
        self.capacity_wh = float(cfg.sim.battery_wh)
        self._last_tel = 0.0
        speeds = cfg.motion.speeds
        self.speed = {"Z": float(speeds.z), "Y": float(speeds.y), "D": float(speeds.drive), "T": float(speeds.turn)}

    # --- lifecycle --------------------------------------------------------------------------------
    async def start(self) -> None:
        self.pose_t = self._last_tel = self.clock.now()
        self._tel_task = asyncio.create_task(self._tel_loop(), name="mock-motion-tel")

    async def close(self) -> None:
        for t in (self._tel_task, self._task):
            if t:
                t.cancel()

    async def _tel_loop(self) -> None:
        while True:
            await self.clock.sleep(1.0 / self.TEL_HZ)
            self._emit(self._telemetry())

    # --- telemetry and battery --------------------------------------------------------------------
    def _telemetry(self) -> Telemetry:
        now = self.clock.now()
        self.update_pose()
        dt = max(0.0, now - self._last_tel)
        self._last_tel = now
        ibat = self._battery_current()
        vbat = self._vbat(ibat)
        self.soc_wh = min(self.capacity_wh, max(0.0, self.soc_wh - vbat * ibat * dt / 3600.0))
        z, y = self.z.pos(now), self.y.pos(now)
        sw = 0
        if "Z" in self.homed and z <= self.Z_HOME_POS + 0.5:
            sw |= P.SW_Z_HOME
        if y <= 0.2:
            sw |= P.SW_Y_HOME
        if self.world.docked_at is not None:
            sw |= P.SW_NOSE
        if self.world.tray["A"] is not None:
            sw |= P.SW_SLOT_A
        if self.world.tray["B"] is not None:
            sw |= P.SW_SLOT_B
        busy = self.busy + ("V" if self._vel_active(now) else "")
        return Telemetry(
            t=int(now * 1000), z=round(z, 2), y=round(y, 2), l=round(self.l, 1), r=round(self.r, 1),
            en=self.en, busy=busy, sw=sw, vbat=round(vbat, 2), ibat=round(ibat, 3),
            vmot=0.0 if self.world.robot_estop else round(vbat - 0.2, 1), dock=self._dock_v(),
            fa=self.fingers["A"], fb=self.fingers["B"], homed="".join(a for a in "ZY" if a in self.homed),
        )

    def _charging(self) -> bool:
        return self.world.docked_at == "rack" and self.world.dock_power

    def _dock_v(self) -> float:
        return 24.0 if self._charging() else 0.0

    def _battery_current(self) -> float:
        load = 0.28  # Pi + logic ≈ 4 W
        if self.busy or self._vel_active(self.clock.now()):
            load += 0.9
        if self._charging():
            frac = self.soc_wh / self.capacity_wh
            charge = 2.0 if frac < 0.95 else 2.0 * max(0.0, 1.0 - frac) / 0.05
            return load - charge
        return load

    def _vbat(self, ibat: float) -> float:
        frac = self.soc_wh / self.capacity_wh
        return 12.0 + 4.8 * frac - 0.05 * ibat

    # --- sim controls -----------------------------------------------------------------------------
    def set_estop(self, pressed: bool) -> None:
        """Press or release the robot mushroom (cuts VMOT)."""
        if pressed == self.world.robot_estop:
            return
        self.world.robot_estop = pressed
        if pressed:
            self._abort_motion("E_ESTOP")
            self.en = False
            self.homed.clear()
            self.needs_reconfig = True
            self.fingers = {"A": "P", "B": "P"}  # servos go limp; treat as parked
            self.attached = {"A": None, "B": None}
            self._emit(Event("ESTOP"))
        else:
            asyncio.get_running_loop().create_task(self._reconfigure())
            self._emit(Event("ESTOP_CLEAR"))

    async def _reconfigure(self) -> None:
        await self.clock.sleep(self.RECONFIG_S)  # GSTAT.reset seen -> re-send all driver registers
        if not self.world.robot_estop:
            self.needs_reconfig = False

    # --- pose integration (VEL) -------------------------------------------------------------------
    def _vel_active(self, now: float) -> bool:
        return (self.v or self.w) and now <= self.last_vel + 0.3

    def update_pose(self) -> None:
        now = self.clock.now()
        end = min(now, self.last_vel + 0.3)
        t = self.pose_t
        if (self.v or self.w) and end > t:
            steps = max(1, int((end - t) / 0.01))
            dt = (end - t) / steps
            for _ in range(steps):
                self._integrate(self.v * dt, self.w * dt)
        if now > self.last_vel + 0.3:
            self.v = self.w = 0.0
        self.pose_t = now

    def _integrate(self, ds: float, dth: float) -> None:
        w = self.world
        if ds and w.docked_at is not None:
            w.docked_at = None
        h = math.radians(w.th + dth / 2)
        w.x += ds * math.cos(h)
        w.y += ds * math.sin(h)
        w.th = (w.th + dth + 180) % 360 - 180
        half = math.radians(dth) * self.TRACK_MM / 2
        self.l += ds - half
        self.r += ds + half

    # --- command dispatch -------------------------------------------------------------------------
    async def request(self, cmd: str, *args: object) -> str:
        args = tuple(a for a in args if a is not None)
        handler = getattr(self, f"_cmd_{cmd.lower()}", None)
        if handler is None:
            raise MotionError("E_ARG", "unknown command", cmd)
        try:
            result = handler(*args)
        except TypeError:
            raise MotionError("E_ARG", "bad arguments", cmd) from None
        except MotionError as exc:
            exc.cmd = cmd
            raise
        if asyncio.iscoroutine(result):  # motion command: OK given, now run to DONE/FAIL
            if self._task is not None and not self._task.done():
                result.close()
                raise MotionError("E_BUSY", cmd=cmd)
            self._cancel_code = "E_STOPPED"
            self._task = asyncio.get_running_loop().create_task(result)
            try:
                await asyncio.wait({self._task})
            except asyncio.CancelledError:
                self._abort_motion("E_STOPPED")
                raise
            if self._task.cancelled():
                raise MotionError(self._cancel_code, cmd=cmd)
            exc = self._task.exception()
            if exc is not None:
                if isinstance(exc, MotionError):
                    exc.cmd = cmd
                raise exc
            return ""
        return result or ""

    def _abort_motion(self, code: str) -> None:
        now = self.clock.now()
        self.update_pose()
        self.v = self.w = 0.0
        self.z.freeze(now)
        self.y.freeze(now)
        if self._task is not None and not self._task.done():
            self._cancel_code = code
            self._task.cancel()
        self.busy = ""

    # interlock helpers
    def _require_enabled(self) -> None:
        if self.world.robot_estop or self.needs_reconfig:
            raise MotionError("E_ESTOP")
        if not self.en:
            raise MotionError("E_INTERLOCK", "drivers disabled")

    def _y_now(self) -> float:
        return self.y.pos(self.clock.now())

    def _z_now(self) -> float:
        return self.z.pos(self.clock.now())

    def _require_travel_pose(self) -> None:
        if self._y_now() > self.g.y_safe or self._z_now() > self.g.z_drive_max:
            raise MotionError("E_INTERLOCK", "Y or Z not in travel pose")

    # immediate commands
    def _cmd_ping(self) -> str:
        return "RBG3-FW mock-0.1"

    def _cmd_enable(self, on) -> None:
        on = str(on) == "1"
        if on and (self.world.robot_estop or self.needs_reconfig):
            raise MotionError("E_ESTOP", "drivers not reconfigured")
        self.en = on

    def _cmd_stop(self) -> None:
        self._abort_motion("E_STOPPED")

    def _cmd_status(self) -> None:
        self._emit(self._telemetry())

    def _cmd_cfg(self, key, value) -> None:
        if key == "bench":
            self.bench = str(value) == "1"
        self.settings[str(key)] = str(value)

    def _cmd_vel(self, v, w) -> None:
        self._require_enabled()
        self._require_travel_pose()
        self.update_pose()
        self.v, self.w = float(v), float(w)
        self.last_vel = self.clock.now()

    # motion commands: validate now (ERR), return a coroutine that runs to DONE/FAIL
    def _cmd_home(self, axis):
        self._require_enabled()
        if axis == "Z" and "Y" not in self.homed:
            raise MotionError("E_NOT_HOMED", "home Y first")
        if axis not in ("Y", "Z"):
            raise MotionError("E_ARG")
        return self._run_home(axis)

    async def _run_home(self, axis: str) -> None:
        if axis == "Y":
            await self._stroke_y(0.0, 10.0)
        else:
            await self._move_axis("Z", self.z, self.Z_HOME_POS, 10.0)
        self.homed.add(axis)

    def _cmd_z(self, mm, speed=None):
        self._require_enabled()
        if "Z" not in self.homed:
            raise MotionError("E_NOT_HOMED")
        if self._y_now() > self.g.y_safe:
            raise MotionError("E_INTERLOCK", "Y > 2")
        mm = float(mm)
        if not self.g.z_soft_min <= mm <= self.g.z_soft_max:
            raise MotionError("E_LIMIT")
        return self._move_axis("Z", self.z, mm, float(speed or self.speed["Z"]))

    def _cmd_y(self, mm, speed=None):
        self._require_enabled()
        if "Y" not in self.homed:
            raise MotionError("E_NOT_HOMED")
        mm = float(mm)
        if not 0 <= mm <= self.g.y_max:
            raise MotionError("E_LIMIT")
        if self.world.docked_at is None and not self.bench and mm > self.g.y_safe:
            raise MotionError("E_INTERLOCK", "not docked")
        return self._stroke_y(mm, float(speed or self.speed["Y"]))

    def _cmd_finger(self, which, action):
        self._require_enabled()
        if which not in ("A", "B", "both") or action not in ("ENGAGE", "PARK"):
            raise MotionError("E_ARG")
        y = self._y_now()
        if not (y <= self.g.y_safe or abs(y - self.g.y_pull) <= 0.5 or abs(y - self.g.y_push) <= 0.5):
            raise MotionError("E_INTERLOCK", "Y mid-stroke")
        return self._run_finger(["A", "B"] if which == "both" else [which], action)

    async def _run_finger(self, slots: list[str], action: str) -> None:
        self.busy = "F"
        await self.clock.sleep(self.FINGER_S)
        self.busy = ""
        y, z = self._y_now(), self._z_now()
        for slot in slots:
            self.fingers[slot] = "E" if action == "ENGAGE" else "P"
            if action == "PARK":
                self.attached[slot] = None
                continue
            if y <= self.g.y_safe and self.world.tray[slot] is not None:
                self.attached[slot] = (self.world.tray[slot], "tray")
            elif abs(y - self.g.y_pull) <= 2:
                h = self.world.shelf_level(self._slot_floor(slot, z))
                caddy = self.world.caddy_on_shelf(self.world.docked_at, h) if h is not None else None
                if caddy is not None:
                    self.attached[slot] = (caddy, h)

    def _cmd_drive(self, mm, speed=None):
        self._require_enabled()
        self._require_travel_pose()
        mm, speed = float(mm), float(speed or self.speed["D"])
        return self._run_drive(mm, speed)

    async def _run_drive(self, mm: float, speed: float) -> None:
        self.update_pose()
        self.busy = "D"
        try:
            await self.clock.sleep(abs(mm) / speed)
        finally:
            self.busy = ""
        self._integrate(mm, 0.0)

    def _cmd_turn(self, deg, speed=None):
        self._require_enabled()
        self._require_travel_pose()
        deg, speed = float(deg), float(speed or self.speed["T"])
        return self._run_turn(deg, speed)

    async def _run_turn(self, deg: float, speed: float) -> None:
        self.update_pose()
        self.busy = "D"
        try:
            await self.clock.sleep(abs(deg) / speed)
        finally:
            self.busy = ""
        self._integrate(0.0, deg + deg / 180.0 * self.world.turn_error)

    def _cmd_dock(self, max_mm, speed=None):
        self._require_enabled()
        self._require_travel_pose()
        return self._run_dock(float(max_mm), float(speed or 50.0))

    async def _run_dock(self, max_mm: float, speed: float) -> None:
        self.update_pose()
        target, contact = None, None
        for name in self.world.stations:
            along, lateral, herr = self.world.facing_offset(name)
            dist = along - self.world.dock_d
            if 0 <= dist <= max_mm and abs(lateral) <= 20 and abs(herr) <= 5:
                target, contact = name, dist
        self.busy = "D"
        try:
            await self.clock.sleep((contact if target else max_mm) / speed)
        finally:
            self.busy = ""
        if target is None:
            self._integrate(max_mm, 0.0)
            raise MotionError("E_NODOCK")
        self._integrate(contact, 0.0)  # odometry
        self.world.x, self.world.y, self.world.th = self.world.dock_pose(target)  # funnel centres it
        self.world.docked_at = target

    # --- axis motion ------------------------------------------------------------------------------
    async def _move_axis(self, name: str, axis: _Axis, target: float, speed: float) -> None:
        self.busy = name
        try:
            await self.clock.sleep(axis.plan(target, speed, self.clock.now()))
        finally:
            self.busy = ""

    def _slot_floor(self, slot: str, z: float) -> float:
        return z + (self.g.bay_pitch if slot == "A" else 0.0)

    async def _stroke_y(self, target: float, speed: float) -> None:
        """Y stroke, moving whatever caddies the engaged fingers hold."""
        y0, z = self._y_now(), self._z_now()
        carried = {s: a for s, a in self.attached.items() if a is not None}
        if not carried or abs(target - y0) < 1e-6:
            await self._move_axis("Y", self.y, target, speed)
            return
        stall_at = None
        if len(carried) > 1:
            self.world.incidents.append("both fingers held a caddy during a Y stroke")
            stall_at = min(y0, target) + 15
        else:
            slot, (caddy, where) = next(iter(carried.items()))
            outward = target > y0
            if outward and where == "tray":
                h = self.world.shelf_level(self._slot_floor(slot, z))
                if h is None or self.world.caddy_on_shelf(self.world.docked_at, h) is not None:
                    self.world.incidents.append(f"caddy {caddy} hit the station (slot {slot}, z={z:.1f})")
                    stall_at = 15.0
            elif not outward and where != "tray" and self.world.tray[slot] is not None:
                self.world.incidents.append(f"slot {slot} occupied while pulling caddy {caddy}")
                stall_at = target + 20
        if stall_at is not None:
            await self._move_axis("Y", self.y, stall_at, speed)
            raise MotionError("E_LIMIT", "Y stall")
        await self._move_axis("Y", self.y, target, speed)
        slot, (caddy, where) = next(iter(carried.items()))
        if target > y0 and where == "tray" and target >= self.g.y_pull - 1:
            h = self.world.shelf_level(self._slot_floor(slot, z))
            self.world.tray[slot] = None
            self.world.stations[self.world.docked_at].shelves[h] = caddy
            self.attached[slot] = (caddy, h)
        elif target < y0 and where != "tray" and target <= self.g.y_safe:
            self.world.stations[self.world.docked_at].shelves[where] = None
            self.world.tray[slot] = caddy
            self.attached[slot] = (caddy, "tray")
