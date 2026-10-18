"""Rack PLC link over Modbus TCP (03-software §4), plus an in-memory PLC for --sim."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field

from .config import HOME

log = logging.getLogger(__name__)

# Delta DVP Modbus addresses (verify against the DVP-SE manual during PLC bring-up)
REG_INPUTS = 0x1000  # D0
REG_OUTPUTS = 0x1001  # D1
REG_HEARTBEAT = 0x1002  # D2
REG_STATE = 0x1003  # D3
REG_PI_HEARTBEAT = 0x100C  # D12
COIL_DOCK_POWER = 0x0800  # M0
COIL_YELLOW = 0x0801  # M1
COIL_RED = 0x0802  # M2

# D0 bits (= X0..X7)
IN_BAY0 = 0  # b0..b3 bay 1..4 present
IN_DOCK = 4  # dock switch of the charging dock (spare station)
IN_ESTOP_OK = 5
IN_S1 = 6
IN_S2 = 7
# D1 bits (= Y0..Y3)
OUT_DOCK_POWER = 0
OUT_GREEN = 1
OUT_YELLOW = 2
OUT_RED = 3

PLC_STATES = {0: "OK", 1: "E_STOP", 2: "WATCHDOG_LOST"}
WATCHDOG_S = 2.0


@dataclass
class RackState:
    bay_present: list[bool] = field(default_factory=lambda: [False] * 4)
    dock: bool = False
    estop_ok: bool = False
    s1_present: bool = False
    s2_present: bool = False
    dock_power: bool = False
    lamp: str = "off"  # green | yellow | red | off
    plc_heartbeat: int = 0
    plc_state: str = "UNKNOWN"
    online: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _bit(word: int, n: int) -> bool:
    return bool(word >> n & 1)


def decode(d0: int, d1: int, d2: int, d3: int, n_bays: int = 4) -> RackState:
    lamp = "red" if _bit(d1, OUT_RED) else "yellow" if _bit(d1, OUT_YELLOW) else "green" if _bit(d1, OUT_GREEN) else "off"
    return RackState(
        bay_present=[_bit(d0, IN_BAY0 + i) for i in range(n_bays)],
        dock=_bit(d0, IN_DOCK),
        estop_ok=_bit(d0, IN_ESTOP_OK),
        s1_present=_bit(d0, IN_S1),
        s2_present=_bit(d0, IN_S2),
        dock_power=_bit(d1, OUT_DOCK_POWER),
        lamp=lamp,
        plc_heartbeat=d2,
        plc_state=PLC_STATES.get(d3, f"UNKNOWN({d3})"),
        online=True,
    )


def plc_scan(x: int, m: tuple[bool, bool, bool], watchdog_lost: bool) -> tuple[int, int]:
    """One scan of the §4 ladder outline: inputs X0-X7 and coils M0-M2 -> (D1 outputs, D3 state)."""
    m0, m1, m2 = m
    dock, estop_ok = _bit(x, IN_DOCK), _bit(x, IN_ESTOP_OK)
    y0 = m0 and dock and estop_ok and not watchdog_lost
    red = (not estop_ok) or watchdog_lost or m2
    yellow = m1 and not red
    green = not red and not yellow
    d1 = y0 << OUT_DOCK_POWER | green << OUT_GREEN | yellow << OUT_YELLOW | red << OUT_RED
    state = 1 if not estop_ok else 2 if watchdog_lost else 0
    return d1, state


class RackBase(ABC):
    def __init__(self, cfg, clock):
        self.cfg = cfg
        self.clock = clock
        self.state = RackState(bay_present=[False] * cfg.n_bays)
        self._changed = asyncio.Event()
        self._tasks: list[asyncio.Task] = []
        self._hb = 0
        self.coils = [False, False, False]
        self._polls_started = 0
        self._fresh_from = 0  # number of the poll that produced self.state

    async def start(self) -> None:
        await self._connect()
        self._tasks = [
            asyncio.create_task(self._poll_loop(), name="rack-poll"),
            asyncio.create_task(self._heartbeat_loop(), name="rack-heartbeat"),
        ]

    async def close(self) -> None:
        for t in self._tasks:
            t.cancel()

    async def _poll_loop(self) -> None:
        period = 1.0 / self.cfg.rack.poll_hz
        while True:
            self._polls_started += 1
            started = self._polls_started
            try:
                regs = await self._read_status()
                self.state = decode(*regs, n_bays=self.cfg.n_bays)
                self._fresh_from = started
            except Exception as exc:  # keep polling; the dashboard shows the rack offline
                if self.state.online:
                    log.warning("rack poll failed: %s", exc)
                self.state.online = False
            self._changed.set()
            self._changed = asyncio.Event()
            await self.clock.sleep(period)

    async def _heartbeat_loop(self) -> None:
        while True:
            self._hb = (self._hb + 1) & 0xFFFF
            try:
                await self._write_register(REG_PI_HEARTBEAT, self._hb)
            except Exception as exc:
                log.debug("heartbeat write failed: %s", exc)
            await self.clock.sleep(self.cfg.rack.heartbeat_s)

    async def wait_for(self, predicate, timeout: float = 2.0) -> bool:
        """Wait until predicate(state) holds on a fresh poll. False on timeout."""
        deadline = self.clock.now() + timeout
        while True:
            if predicate(self.state):
                return True
            remaining = deadline - self.clock.now()
            if remaining <= 0:
                return False
            try:
                await self.clock.wait_for(self._changed.wait(), remaining)
            except asyncio.TimeoutError:
                return predicate(self.state)

    async def refresh(self, timeout: float = 1.0) -> None:
        """Wait for a poll that started after this call, so decisions use current PLC inputs."""
        target = self._polls_started + 1
        deadline = self.clock.now() + timeout
        while self._fresh_from < target:
            remaining = deadline - self.clock.now()
            if remaining <= 0:
                return
            try:
                await self.clock.wait_for(self._changed.wait(), remaining)
            except asyncio.TimeoutError:
                return

    async def set_coil(self, index: int, on: bool) -> None:
        self.coils[index] = on
        await self._write_coil(COIL_DOCK_POWER + index, on)

    async def set_dock_power(self, on: bool) -> None:
        await self.set_coil(0, on)

    async def set_lamps(self, yellow: bool, red: bool) -> None:
        if self.coils[1] != yellow:
            await self.set_coil(1, yellow)
        if self.coils[2] != red:
            await self.set_coil(2, red)

    @abstractmethod
    async def _connect(self) -> None: ...

    @abstractmethod
    async def _read_status(self) -> tuple[int, int, int, int]: ...

    @abstractmethod
    async def _write_register(self, address: int, value: int) -> None: ...

    @abstractmethod
    async def _write_coil(self, address: int, value: bool) -> None: ...


class ModbusRack(RackBase):
    """Delta DVP-12SE (or the ESP32 fallback) over Modbus TCP."""

    async def _connect(self) -> None:
        from pymodbus.client import AsyncModbusTcpClient

        r = self.cfg.rack
        self._client = AsyncModbusTcpClient(r.host, port=r.port, timeout=1)
        if not await self._client.connect():
            log.warning("rack PLC %s:%s not reachable yet (will keep retrying)", r.host, r.port)

    async def close(self) -> None:
        await super().close()
        self._client.close()

    async def _read_status(self) -> tuple[int, int, int, int]:
        rr = await self._client.read_holding_registers(REG_INPUTS, count=4, device_id=self.cfg.rack.unit_id)
        if rr.isError():
            raise IOError(str(rr))
        return tuple(rr.registers[:4])

    async def _write_register(self, address: int, value: int) -> None:
        await self._client.write_register(address, value, device_id=self.cfg.rack.unit_id)

    async def _write_coil(self, address: int, value: bool) -> None:
        await self._client.write_coil(address, value, device_id=self.cfg.rack.unit_id)


class MockRack(RackBase):
    """In-memory PLC running the §4 ladder against the SimWorld inputs."""

    SCAN_S = 0.1

    def __init__(self, cfg, clock, world):
        super().__init__(cfg, clock)
        self.world = world
        self.regs = {REG_INPUTS: 0, REG_OUTPUTS: 0, REG_HEARTBEAT: 0, REG_STATE: 0, REG_PI_HEARTBEAT: 0}
        self.m = [False, False, False]
        self.pi_heartbeat_frozen = False  # sim: simulate a dead Pi link
        self._last_pi_hb = None
        self._last_pi_hb_t = 0.0

    async def _connect(self) -> None:
        self._last_pi_hb_t = self.clock.now()
        self._tasks_plc = asyncio.create_task(self._scan_loop(), name="mock-plc")

    async def close(self) -> None:
        await super().close()
        self._tasks_plc.cancel()

    def inputs(self) -> int:
        w = self.world
        x = 0
        for i, present in enumerate(w.bay_present()):
            x |= present << (IN_BAY0 + i)
        spare = w.spare_present()
        x |= (w.docked_at == HOME) << IN_DOCK
        x |= w.rack_estop_ok << IN_ESTOP_OK
        x |= spare["S1"] << IN_S1
        x |= spare["S2"] << IN_S2
        return x

    def scan(self) -> None:
        now = self.clock.now()
        hb = self.regs[REG_PI_HEARTBEAT]
        if hb != self._last_pi_hb:
            self._last_pi_hb, self._last_pi_hb_t = hb, now
        lost = now - self._last_pi_hb_t > WATCHDOG_S
        x = self.inputs()
        d1, state = plc_scan(x, tuple(self.m), lost)
        self.regs[REG_INPUTS] = x
        self.regs[REG_OUTPUTS] = d1
        self.regs[REG_STATE] = state
        self.world.dock_power = _bit(d1, OUT_DOCK_POWER)

    async def _scan_loop(self) -> None:
        while True:
            self.scan()
            self.regs[REG_HEARTBEAT] = (self.regs[REG_HEARTBEAT] + 1) & 0xFFFF
            await self.clock.sleep(self.SCAN_S)

    async def _read_status(self) -> tuple[int, int, int, int]:
        self.scan()  # a real PLC scans every few ms, so a read always reflects current inputs
        return tuple(self.regs[a] for a in (REG_INPUTS, REG_OUTPUTS, REG_HEARTBEAT, REG_STATE))

    async def _write_register(self, address: int, value: int) -> None:
        if address == REG_PI_HEARTBEAT and self.pi_heartbeat_frozen:
            return
        self.regs[address] = value

    async def _write_coil(self, address: int, value: bool) -> None:
        self.m[address - COIL_DOCK_POWER] = value
