"""Pi <-> ESP32 line protocol (03-software §3). Pure encode/parse, no I/O."""

from __future__ import annotations

from dataclasses import dataclass, fields

# sw bitmask (1 = pressed)
SW_Z_HOME = 1 << 0
SW_Y_HOME = 1 << 1
SW_NOSE = 1 << 2
SW_SLOT_A = 1 << 3
SW_SLOT_B = 1 << 4

ERROR_CODES = {
    "E_ARG", "E_BUSY", "E_NOT_HOMED", "E_INTERLOCK", "E_LIMIT", "E_ESTOP", "E_NODOCK", "E_TIMEOUT",
    # Not in the spec list: reported for a motion cancelled by STOP (spec gap, see rackbot/README.md).
    "E_STOPPED",
}

# Commands that answer OK and later DONE/FAIL.
MOTION_COMMANDS = {"HOME", "Z", "Y", "FINGER", "DRIVE", "TURN", "DOCK"}


class ProtocolError(ValueError):
    pass


@dataclass
class Reply:
    seq: int
    kind: str  # OK | ERR | DONE | FAIL
    code: str = ""  # error code for ERR/FAIL
    data: str = ""


@dataclass
class Event:
    name: str
    data: str = ""


@dataclass
class Telemetry:
    t: int = 0  # firmware ms
    z: float = 0.0
    y: float = 0.0
    l: float = 0.0
    r: float = 0.0
    en: bool = False
    busy: str = ""  # axes in motion, e.g. "ZY"
    sw: int = 0
    vbat: float = 0.0
    ibat: float = 0.0
    vmot: float = 0.0
    dock: float = 0.0
    fa: str = "P"  # finger A: E(ngaged) | P(arked)
    fb: str = "P"
    homed: str = ""  # homed axes, e.g. "ZY"

    def pressed(self, bit: int) -> bool:
        return bool(self.sw & bit)

    @property
    def nose(self) -> bool:
        return self.pressed(SW_NOSE)

    def slot_loaded(self, slot: str) -> bool:
        return self.pressed(SW_SLOT_A if slot == "A" else SW_SLOT_B)

    def to_dict(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(self)}


def encode_request(seq: int, cmd: str, *args: object) -> str:
    if not 1 <= seq <= 65535:
        raise ProtocolError(f"seq out of range: {seq}")
    parts = [str(seq), cmd] + [_fmt(a) for a in args if a is not None]
    return " ".join(parts) + "\n"


def _fmt(value: object) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def parse_line(line: str) -> Reply | Event | Telemetry:
    """Parse one line from the firmware."""
    line = line.strip()
    if not line:
        raise ProtocolError("empty line")
    head, _, rest = line.partition(" ")
    if head == "TEL":
        return parse_telemetry(rest)
    if head == "EVT":
        name, _, data = rest.partition(" ")
        if not name:
            raise ProtocolError(f"EVT without name: {line!r}")
        return Event(name, data)
    try:
        seq = int(head)
    except ValueError as exc:
        raise ProtocolError(f"unknown line: {line!r}") from exc
    kind, _, data = rest.partition(" ")
    if kind in ("OK", "DONE"):
        return Reply(seq, kind, data=data)
    if kind in ("ERR", "FAIL"):
        code, _, msg = data.partition(" ")
        if not code:
            raise ProtocolError(f"{kind} without code: {line!r}")
        return Reply(seq, kind, code=code, data=msg)
    raise ProtocolError(f"unknown reply kind: {line!r}")


_TEL_FLOAT = {"z", "y", "l", "r", "vbat", "ibat", "vmot", "dock"}


def parse_telemetry(body: str) -> Telemetry:
    tel = Telemetry()
    for token in body.split():
        key, sep, value = token.partition("=")
        if not sep:
            raise ProtocolError(f"bad TEL token: {token!r}")
        if key == "t":
            tel.t = int(value)
        elif key in _TEL_FLOAT:
            setattr(tel, key, float(value))
        elif key == "en":
            tel.en = value == "1"
        elif key == "sw":
            tel.sw = int(value, 16)
        elif key in ("busy", "fa", "fb", "homed"):
            setattr(tel, key, value)
        # unknown keys are ignored so newer firmware stays compatible
    return tel


def format_telemetry(tel: Telemetry) -> str:
    """Inverse of parse_telemetry (used by the mock firmware and tests)."""
    return (
        f"TEL t={tel.t} z={tel.z:.2f} y={tel.y:.2f} l={tel.l:.1f} r={tel.r:.1f} en={int(tel.en)} "
        f"busy={tel.busy} sw={tel.sw:02x} vbat={tel.vbat:.2f} ibat={tel.ibat:.2f} vmot={tel.vmot:.1f} "
        f"dock={tel.dock:.1f} fa={tel.fa} fb={tel.fb} homed={tel.homed}"
    )

