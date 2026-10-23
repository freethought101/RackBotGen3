"""Swap-job mission (03-software §5): primitives, the job state machine, faults and operator control.

The mission only talks to the MotionBase / RackBase / VisionBase interfaces, so it runs unchanged
against the real robot and the simulator.

Resume semantics: every job state first checks whether its goal is already met (e.g. EXTRACT_FAILED
is done once slot B is loaded), so after a FAULT the operator can resume and the failed state simply
runs again from a safe pose.
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from enum import Enum

from .config import HOME, Config, Op, Shelf
from .motion import MotionError
from .vision import approach_step

log = logging.getLogger(__name__)


class S(str, Enum):
    STARTUP = "STARTUP"
    IDLE_DOCKED = "IDLE_DOCKED"
    PICK_GOOD = "PICK_GOOD"
    TO_RACK = "TO_RACK"
    EXTRACT_FAILED = "EXTRACT_FAILED"
    INSERT_GOOD = "INSERT_GOOD"
    TO_SPARE_RMA = "TO_SPARE_RMA"
    PLACE_RMA = "PLACE_RMA"
    RETURN = "RETURN"
    FAULT = "FAULT"


# A job starts docked at HOME (the spare station), so the first step is the pick; RETURN only drives
# after an abort and otherwise just turns the dock power back on.
JOB_STATES = [S.PICK_GOOD, S.TO_RACK, S.EXTRACT_FAILED, S.INSERT_GOOD, S.TO_SPARE_RMA, S.PLACE_RMA, S.RETURN]

# Faults that must not be retried by a primitive
NO_RETRY = {"E_ESTOP", "E_ABORT", "E_CADDY_ID", "E_ALIGN"}


class Fault(Exception):
    def __init__(self, code: str, msg: str = ""):
        super().__init__(f"{code}: {msg}" if msg else code)
        self.code = code
        self.msg = msg


class AbortRequested(Exception):
    pass


class JobRejected(Exception):
    pass


@dataclass
class JobCtx:
    id: int
    bay: int
    caddy_out: int | None
    caddy_in: int | None = None
    index: int = 0
    t_start: float = 0.0
    wh_start: float = 0.0
    states: list[dict] = field(default_factory=list)


class Mission:
    def __init__(self, cfg: Config, clock, motion, rack, vision, store, energy, events):
        self.cfg = cfg
        self.g = cfg.geometry
        self.ap = cfg.approach
        self.clock = clock
        self.motion = motion
        self.rack = rack
        self.vision = vision
        self.store = store
        self.energy = energy
        self.events = events  # callable(level, source, msg)
        self.state = S.STARTUP
        self.step = ""
        self.location: str | None = None  # station the robot believes it is docked at
        self.fault: Fault | None = None
        self.fault_state: S | None = None
        self.paused = False
        self.estop = False
        self.job: JobCtx | None = None
        self.queue: deque[int] = deque()
        self._wake = asyncio.Event()
        self._operator: asyncio.Queue[str] = asyncio.Queue()
        self._abort = False
        self._task: asyncio.Task | None = None
        motion.subscribe(self._on_motion)

    # --- public control (dashboard / API) ---------------------------------------------------------
    async def start(self) -> None:
        for job in self.store.open_jobs():  # jobs left over from a restart are not resumed blindly
            self.store.update_job(job["id"], result="aborted", detail="application restarted")
        self._task = asyncio.create_task(self._run(), name="mission")

    async def close(self) -> None:
        if self._task:
            self._task.cancel()

    def submit(self, bay: int, source: str = "manual") -> dict:
        if not 1 <= bay <= self.cfg.n_bays:
            raise JobRejected(f"no bay {bay}")
        if any(j["bay"] == bay for j in self.store.open_jobs()):
            raise JobRejected(f"bay {bay} already has an open job")
        job = self.store.create_job(bay, source)
        self.queue.append(job["id"])
        self.events("info", "mission", f"job {job['id']} queued: swap bay {bay} ({source})")
        self._wake.set()
        return job

    def pause(self) -> None:
        self.paused = True
        self.events("info", "operator", "pause")

    def resume(self) -> None:
        if self.state == S.FAULT:
            if self.estop:
                raise JobRejected("release the E-stop first")
            self._operator.put_nowait("resume")
        self.paused = False
        self.events("info", "operator", "resume")
        self._wake.set()

    def abort(self) -> None:
        self.events("warn", "operator", "abort")
        if self.state == S.FAULT:
            if self.estop:
                raise JobRejected("release the E-stop first")
            self._operator.put_nowait("abort")
        elif self.job is not None:
            self._abort = True
            asyncio.get_running_loop().create_task(self._stop_quietly())
        self.paused = False
        self._wake.set()

    async def _stop_quietly(self) -> None:
        try:
            await self.motion.stop()
        except MotionError:
            pass

    def request_home(self) -> None:
        if self.job is not None and self.state != S.FAULT:
            raise JobRejected("a job is running")
        self._operator.put_nowait("home")
        self._wake.set()

    def snapshot(self) -> dict:
        job = None
        if self.job:
            job = {"id": self.job.id, "bay": self.job.bay, "caddy_out": self.job.caddy_out,
                   "caddy_in": self.job.caddy_in, "elapsed_s": round(self.clock.now() - self.job.t_start, 1)}
        return {
            "state": self.state.value, "step": self.step, "location": self.location,
            "paused": self.paused, "estop": self.estop, "job": job, "queue": list(self.queue),
            "fault": {"code": self.fault.code, "msg": self.fault.msg, "state": self.fault_state.value}
            if self.fault and self.state == S.FAULT else None,
        }

    # --- motion events ----------------------------------------------------------------------------
    def _on_motion(self, item) -> None:
        name = getattr(item, "name", None)
        if name == "ESTOP":
            self.estop = True
            self.events("error", "robot", "E-stop pressed")
            self._wake.set()
        elif name == "DRIVER_RESET":
            self.events("error", "robot", "stepper drivers lost their configuration (VS brown-out): re-homing needed")
            self._wake.set()
        elif name == "ESTOP_CLEAR":
            self.estop = False
            self.events("info", "robot", "E-stop released: resume or abort")
            self._wake.set()

    # --- main loop --------------------------------------------------------------------------------
    async def _run(self) -> None:
        try:
            await self._loop()
        except asyncio.CancelledError:
            raise
        except BaseException as exc:  # never die silently: the dashboard must show it
            log.exception("mission loop crashed")
            self.fault, self.fault_state = Fault("E_INTERNAL", repr(exc)), self.state
            self._set_state(S.FAULT)
            self.events("error", "mission", f"internal error: {exc!r} (restart the application)")

    async def _loop(self) -> None:
        await self._guarded(self._startup, S.STARTUP)
        while True:
            if self.estop and self.state != S.FAULT:
                cmd = await self._fault_loop(Fault("E_ESTOP"), self.state, None)
                if cmd == "resume":
                    await self._guarded(self._startup, S.STARTUP)
                continue
            if self.queue and not self.paused and self.state == S.IDLE_DOCKED:
                await self._run_job(self.queue.popleft())
                continue
            if not self._operator.empty():
                cmd = self._operator.get_nowait()
                if cmd == "home" or (cmd == "resume" and self.state == S.FAULT):
                    await self._guarded(self._startup, S.STARTUP)
                continue
            if self.state == S.IDLE_DOCKED:
                await self._idle_housekeeping()
            self._wake.clear()
            try:
                await self.clock.wait_for(self._wake.wait(), 1.0)
            except asyncio.TimeoutError:
                pass

    async def _guarded(self, fn, state: S) -> None:
        """Run fn; on a fault wait for the operator and retry on resume."""
        while True:
            self._set_state(state)
            try:
                await fn()
                return
            except (Fault, MotionError) as exc:
                cmd = await self._fault_loop(_as_fault(exc), state, None)
                if cmd == "abort":
                    self._set_state(S.FAULT)
                    return

    async def _fault_loop(self, fault: Fault, state: S, job: JobCtx | None) -> str:
        """Enter FAULT and wait for resume/abort (a home request re-homes and keeps waiting)."""
        self.fault, self.fault_state = fault, state
        self._set_state(S.FAULT)
        self.events("error", "mission", f"FAULT in {state.value}: {fault.code} {fault.msg}".strip())
        if job is not None:
            self.store.update_job(job.id, result="fault", detail=f"{state.value}: {fault.code}")
        try:
            await self.motion.stop()
        except MotionError:
            pass
        while True:
            cmd = await self._operator.get()
            if cmd == "home":
                try:
                    await self._rehome()
                    self.events("info", "mission", "re-homed")
                except (Fault, MotionError) as exc:
                    self.events("error", "mission", f"re-home failed: {_as_fault(exc)}")
                continue
            if cmd == "resume":
                try:
                    await self._prepare_resume()
                except (Fault, MotionError) as exc:
                    self.fault = _as_fault(exc)
                    self.events("error", "mission", f"resume failed: {self.fault}")
                    continue
            self.fault = None
            return cmd

    async def _prepare_resume(self) -> None:
        tel = await self.motion.status()
        if not tel.en or "Y" not in tel.homed or "Z" not in tel.homed:
            await self._rehome()

    # --- startup / homing -------------------------------------------------------------------------
    async def _startup(self) -> None:
        fw = await self.motion.ping()
        self.events("info", "robot", f"motion controller: {fw}")
        await self._rehome()
        if not await self.rack.wait_for(lambda s: s.online, 5.0):
            raise Fault("E_RACK_OFFLINE", "no Modbus link to the rack PLC")
        tel = await self.motion.status()
        if not (tel.nose and self.rack.state.dock):
            self.location = None
            raise Fault("E_NOT_DOCKED", "place the robot docked at the spare station, then resume")
        self.location = HOME
        await self.rack.set_dock_power(True)
        self._set_state(S.IDLE_DOCKED)

    async def _rehome(self) -> None:
        for _ in range(30):  # drivers re-configure after VMOT returns; ENABLE is refused until then
            try:
                await self.motion.enable(True)
                break
            except MotionError as exc:
                if exc.code != "E_ESTOP":
                    raise
                await self.clock.sleep(0.2)
        else:
            raise Fault("E_ESTOP", "drivers did not come back")
        await self._step("home Y", self.motion.home, "Y")
        await self._step("home Z", self.motion.home, "Z")
        await self._step("Z drive", self.motion.move_z, self.g.z_drive)
        await self._secure_fingers()

    # --- jobs -------------------------------------------------------------------------------------
    async def _run_job(self, job_id: int) -> None:
        job = self.store.job(job_id)
        await self.rack.refresh()
        try:
            self._check_preconditions(job["bay"])
        except JobRejected as exc:
            self.store.update_job(job_id, result="rejected", detail=str(exc), ended=self.clock.wall())
            self.events("warn", "mission", f"job {job_id} rejected: {exc}")
            return
        inv = self.store.inventory()
        ctx = JobCtx(job_id, job["bay"], caddy_out=inv.get(f"bay{job['bay']}"),
                     t_start=self.clock.now(), wh_start=self.energy.wh_used)
        self.job = ctx
        self.energy.active = True
        self.store.update_job(job_id, result="running", started=self.clock.wall(), caddy_out=ctx.caddy_out)
        self.events("info", "mission", f"job {job_id} started: bay {ctx.bay}, caddy out {ctx.caddy_out}")
        try:
            while ctx.index < len(JOB_STATES):
                st = JOB_STATES[ctx.index]
                self._set_state(st)
                try:
                    await self._job_state(st, ctx)
                    ctx.index += 1
                except (Fault, MotionError) as exc:
                    if await self._fault_loop(_as_fault(exc), st, ctx) == "abort":
                        raise AbortRequested() from None
                    self.store.update_job(ctx.id, result="running")
            self._finish_job(ctx, "ok")
        except AbortRequested:
            self._abort = False
            self._finish_job(ctx, "aborted")
            self.job = None
            self.energy.active = False
            await self._guarded(self._return_home, S.RETURN)
        finally:
            self.job = None
            self._abort = False
            self.energy.active = False
            self.step = ""

    def _finish_job(self, ctx: JobCtx, result: str) -> None:
        now = self.clock.now()
        ctx.states.append({"state": "END", "t": round(now - ctx.t_start, 2)})
        cycle = now - ctx.t_start
        wh = self.energy.wh_used - ctx.wh_start
        self.store.update_job(ctx.id, result=result, ended=self.clock.wall(), cycle_s=round(cycle, 1),
                              wh=round(wh, 4), states=ctx.states, caddy_in=ctx.caddy_in)
        self.events("info" if result == "ok" else "warn", "mission",
                    f"job {ctx.id} {result}: {cycle:.1f} s, {wh:.3f} Wh")
        if result == "ok":
            self._set_state(S.IDLE_DOCKED)

    def _check_preconditions(self, bay: int) -> None:
        rs = self.rack.state
        tel = self.motion.telemetry
        if self.location != HOME:
            raise JobRejected("robot is not docked at the spare station")
        if not rs.online:
            raise JobRejected("rack PLC offline")
        if not rs.bay_present[bay - 1]:
            raise JobRejected(f"bay {bay} is empty")
        if not rs.s1_present:
            raise JobRejected("no good spare in S1")
        if rs.s2_present:
            raise JobRejected("RMA slot S2 is occupied")
        if tel.slot_loaded("A") or tel.slot_loaded("B"):
            raise JobRejected("tray is not empty")

    async def _job_state(self, st: S, ctx: JobCtx) -> None:
        ctx.states.append({"state": st.value, "t": round(self.clock.now() - ctx.t_start, 2)})
        bay = self.cfg.bay(ctx.bay)
        tel = await self.motion.status()
        if st == S.TO_SPARE_RMA:
            await self._attempt("goto spare", lambda: self._goto("spare"), self._recover_drive)
        elif st == S.TO_RACK:
            await self._attempt("goto rack", lambda: self._goto("rack"), self._recover_drive)
        elif st == S.RETURN:
            await self._attempt("goto home", lambda: self._goto(HOME), self._recover_drive)
            await self._start_charging()
        elif st == S.PICK_GOOD:
            await self.rack.set_dock_power(False)  # no charging during a job
            if not tel.slot_loaded("A"):
                s1 = self.cfg.spare("S1")
                ctx.caddy_in = await self._attempt("pull A", lambda: self._pull("A", s1, None), self._recover_y)
                self.store.update_job(ctx.id, caddy_in=ctx.caddy_in)
            elif ctx.caddy_in is None:
                ctx.caddy_in = self.store.inventory().get("trayA")
        elif st == S.EXTRACT_FAILED:
            if not tel.slot_loaded("B"):
                await self._attempt("pull B", lambda: self._pull("B", bay, ctx.caddy_out), self._recover_y)
        elif st == S.INSERT_GOOD:
            if tel.slot_loaded("A"):
                await self._attempt("push A", lambda: self._push("A", bay, ctx.caddy_in), self._recover_y)
        elif st == S.PLACE_RMA:
            if tel.slot_loaded("B"):
                s2 = self.cfg.spare("S2")
                await self._attempt("push B", lambda: self._push("B", s2, ctx.caddy_out), self._recover_y)

    async def _return_home(self) -> None:
        await self._attempt("goto home", lambda: self._goto(HOME), self._recover_drive)
        await self._start_charging()
        self._set_state(S.IDLE_DOCKED)

    # --- retries ----------------------------------------------------------------------------------
    async def _attempt(self, name: str, fn, recover):
        retries = int(self.cfg.mission.retries)
        for attempt in range(retries + 1):
            try:
                return await fn()
            except (Fault, MotionError) as exc:
                if self._abort:
                    raise AbortRequested() from None
                fault = _as_fault(exc)
                if fault.code in NO_RETRY or self.estop or attempt == retries:
                    raise fault from None
                self.events("warn", "mission", f"{name} failed ({fault}), retry {attempt + 1}/{retries}")
                try:
                    await recover()
                except (Fault, MotionError) as rexc:
                    raise _as_fault(rexc) from None

    async def _recover_y(self) -> None:
        tel = await self.motion.status()
        if tel.y > self.g.y_safe:
            await self._step("recover Y 0", self.motion.move_y, 0)

    async def _recover_drive(self) -> None:
        await self._recover_y()
        tel = await self.motion.status()
        if not tel.nose:
            await self._step("back off", self.motion.drive, -self.ap.backoff_mm)

    # --- primitives (03 §5.1) ---------------------------------------------------------------------
    async def _checkpoint(self) -> None:
        while True:
            if self._abort:
                raise AbortRequested()
            if not self.paused:
                return
            self._wake.clear()
            try:
                await self.clock.wait_for(self._wake.wait(), 1.0)
            except asyncio.TimeoutError:
                pass

    async def _step(self, label: str, fn, *args):
        await self._checkpoint()
        self.step = label
        return await fn(*args)

    async def _ensure_y_home(self) -> None:
        if (await self.motion.status()).y > self.g.y_safe:
            await self._step("Y 0", self.motion.move_y, 0)

    async def _secure_fingers(self) -> None:
        """Travel rule: fingers engaged on loaded slots, parked on empty ones."""
        tel = await self.motion.status()
        for slot, cur in (("A", tel.fa), ("B", tel.fb)):
            want = "E" if tel.slot_loaded(slot) else "P"
            if cur != want:
                await self._step(f"finger {slot}", self.motion.finger, slot, "ENGAGE" if want == "E" else "PARK")

    async def _fine_align(self, shelf: Shelf, z: float) -> float:
        err = await self.vision.shelf_z_error(shelf.tag_id)
        if err is None:
            raise Fault("E_TAG_LOST", f"shelf tag {shelf.tag_id} not seen")
        if abs(err) > self.cfg.vision.bay_align_max_mm:
            raise Fault("E_ALIGN", f"shelf tag {shelf.tag_id}: Z error {err:.1f} mm (wrong bay or calibration)")
        if abs(err) >= 0.2:
            z += err
            await self._step(f"Z align {z:.1f}", self.motion.move_z, z)
        return z

    async def _verify_shelf(self, shelf: Shelf, present: bool) -> None:
        if shelf.station == "rack":
            i = int(shelf.name) - 1
            ok = await self.rack.wait_for(lambda s: s.bay_present[i] == present, 2.0)
        else:
            attr = "s1_present" if shelf.name == "S1" else "s2_present"
            ok = await self.rack.wait_for(lambda s: getattr(s, attr) == present, 2.0)
        if not ok:
            raise Fault("E_VERIFY", f"PLC: {shelf.location} {'not seated' if present else 'still present'}")

    async def _pull(self, slot: str, shelf: Shelf, expected: int | None) -> int | None:
        other = "B" if slot == "A" else "A"
        await self._ensure_y_home()
        z = self.cfg.z_for(slot, shelf.height, Op.EXTRACT)
        await self._step(f"Z {z:.1f}", self.motion.move_z, z)
        await self._fine_align(shelf, z)
        tel = await self.motion.status()
        caddy = None
        if not tel.slot_loaded("B"):  # the camera sees the shelf through the empty slot B window
            self.step = "read caddy tag"
            caddy = await self.vision.read_caddy_tag(shelf.station, shelf.height)
            if expected is not None and caddy is not None and caddy != expected:
                raise Fault("E_CADDY_ID", f"{shelf.location}: expected caddy {expected}, saw {caddy}")
            if caddy is None:
                self.events("warn", "vision", f"{shelf.location}: caddy tag not read")
        caddy = caddy or expected or self.store.inventory().get(shelf.location)
        await self._step("fingers park", self.motion.finger, "both", "PARK")
        await self._step("Y pull", self.motion.move_y, self.g.y_pull)
        await self._step(f"finger {slot} engage", self.motion.finger, slot, "ENGAGE")
        await self._step("Y 0", self.motion.move_y, 0)
        if tel.slot_loaded(other):
            await self._step(f"finger {other} engage", self.motion.finger, other, "ENGAGE")
        tel = await self.motion.status()
        if not tel.slot_loaded(slot):
            raise Fault("E_VERIFY", f"slot {slot} switch not pressed after pull")
        await self._verify_shelf(shelf, present=False)
        if caddy is not None:
            self.store.move_caddy(caddy, f"tray{slot}")
        self.events("info", "mission", f"pulled caddy {caddy} from {shelf.location} into slot {slot}")
        return caddy

    async def _push(self, slot: str, shelf: Shelf, caddy: int | None) -> None:
        other = "B" if slot == "A" else "A"
        await self._ensure_y_home()
        z = self.cfg.z_for(slot, shelf.height, Op.INSERT)
        await self._step(f"Z {z:.1f}", self.motion.move_z, z)
        await self._fine_align(shelf, z)
        tel = await self.motion.status()
        await self._step(f"finger {slot} engage", self.motion.finger, slot, "ENGAGE")
        await self._step(f"finger {other} park", self.motion.finger, other, "PARK")
        await self._step("Y push", self.motion.move_y, self.g.y_push)
        await self._step(f"finger {slot} park", self.motion.finger, slot, "PARK")
        await self._step("Y 0", self.motion.move_y, 0)
        if tel.slot_loaded(other):
            await self._step(f"finger {other} engage", self.motion.finger, other, "ENGAGE")
        tel = await self.motion.status()
        if tel.slot_loaded(slot):
            raise Fault("E_VERIFY", f"slot {slot} still loaded after push")
        await self._verify_shelf(shelf, present=True)
        caddy = caddy or self.store.inventory().get(f"tray{slot}")
        if caddy is not None:
            self.store.move_caddy(caddy, shelf.location)
        self.events("info", "mission", f"pushed caddy {caddy} from slot {slot} into {shelf.location}")

    async def _goto(self, station: str) -> None:
        tel = await self.motion.status()
        if self.location == station and tel.nose:
            return
        tag = self.cfg.station_tag(station)
        await self._ensure_y_home()
        await self._secure_fingers()
        if self.location == HOME:
            await self.rack.set_dock_power(False)
        await self._step("Z approach", self.motion.move_z, self.g.z_approach)
        if tel.nose:
            await self._step("undock", self.motion.drive, -self.ap.undock_mm)
            self.location = None
            await self._step("turn", self.motion.turn, 180)
        await self._approach(tag)
        await self._step("dock", self.motion.dock, self.ap.dock_max_mm, self.ap.dock_speed)
        tel = await self.motion.status()
        if not tel.nose:
            raise Fault("E_NODOCK", "NOSE not pressed after DOCK")
        if station == HOME and not await self.rack.wait_for(lambda s: s.dock, 2.0):
            raise Fault("E_NODOCK", "PLC does not see the robot docked at the spare station (X4)")
        self.location = station
        await self._step("Z drive", self.motion.move_z, self.g.z_drive)

    async def _approach(self, tag: int) -> None:
        """Visual servoing onto a station tag until hand-off (03 §6.2)."""
        ap = self.ap
        retries = 0
        lost_since: float | None = None
        deadline = self.clock.now() + 120.0
        self.step = f"approach tag {tag}"
        while True:
            await self._checkpoint()
            if self.clock.now() > deadline:
                raise Fault("E_TIMEOUT", "approach took too long")
            pose = await self.vision.find_tag(tag)
            now = self.clock.now()
            backoff = None
            if pose is None:
                lost_since = lost_since if lost_since is not None else now
                if now - lost_since > ap.lost_s:
                    backoff = f"tag {tag} lost"
            else:
                lost_since = None
                cmd = approach_step(pose, ap)
                if cmd.handoff:
                    await self.motion.vel(0, 0)
                    return
                if cmd.too_close:
                    backoff = f"too close without alignment (x={pose.x:.0f} mm, psi={pose.psi:.1f} deg)"
                else:
                    await self.motion.vel(cmd.v, cmd.w)
            if backoff:
                retries += 1
                if retries > ap.max_retries:
                    raise Fault("E_TAG_LOST", backoff)
                self.events("warn", "vision", f"approach: {backoff}, backing off ({retries}/{ap.max_retries})")
                await self.motion.stop()
                await self._step("back off", self.motion.drive, -ap.backoff_mm)
                self.step = f"approach tag {tag}"
                lost_since = None

    async def _start_charging(self) -> None:
        await self.rack.set_dock_power(True)
        ok = False
        for _ in range(20):
            tel = await self.motion.status()
            full = tel.vbat >= 16.6  # a full pack draws no charge current
            if tel.nose and tel.dock > self.cfg.mission.dock_v_min and (tel.ibat < 0 or full):
                ok = True
                break
            await self.clock.sleep(0.25)
        if not ok:
            raise Fault("E_NOCHARGE", "dock power on but no charging current")
        self.events("info", "robot", "docked at the spare station, charging")

    async def _idle_housekeeping(self) -> None:
        tel = self.motion.telemetry
        m = self.cfg.mission
        if self.rack.coils[0] and tel.dock > m.dock_v_min and tel.ibat > -m.charge_taper_a:
            await self.rack.set_dock_power(False)
            self.events("info", "robot", "charge complete, dock power off")
        elif not self.rack.coils[0] and 0 < tel.vbat < m.charge_restart_v:
            await self.rack.set_dock_power(True)
            self.events("info", "robot", f"battery {tel.vbat:.2f} V, charging")

    # --- helpers ----------------------------------------------------------------------------------
    def _set_state(self, st: S) -> None:
        if st == S.IDLE_DOCKED:
            self.step = ""
        if st != self.state:
            self.events("debug", "mission", f"state {self.state.value} -> {st.value}")
        self.state = st


def _as_fault(exc: Exception) -> Fault:
    if isinstance(exc, Fault):
        return exc
    if isinstance(exc, MotionError):
        return Fault(exc.code, f"{exc.cmd} {exc.msg}".strip())
    return Fault("E_INTERNAL", str(exc))
