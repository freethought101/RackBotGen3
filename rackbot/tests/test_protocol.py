import pytest

from rackbot import protocol as P


def test_encode():
    assert P.encode_request(7, "Z", 194.0, 15.0) == "7 Z 194 15\n"
    assert P.encode_request(8, "FINGER", "A", "ENGAGE") == "8 FINGER A ENGAGE\n"
    assert P.encode_request(9, "Y", 178.5) == "9 Y 178.5\n"
    assert P.encode_request(10, "ENABLE", True) == "10 ENABLE 1\n"
    assert P.encode_request(11, "DOCK", 300.0, None) == "11 DOCK 300\n"
    with pytest.raises(P.ProtocolError):
        P.encode_request(0, "PING")


@pytest.mark.parametrize("line,expected", [
    ("12 OK RBG3-FW 0.1.0", P.Reply(12, "OK", data="RBG3-FW 0.1.0")),
    ("12 OK", P.Reply(12, "OK")),
    ("13 ERR E_INTERLOCK Y > 2", P.Reply(13, "ERR", code="E_INTERLOCK", data="Y > 2")),
    ("14 DONE", P.Reply(14, "DONE")),
    ("15 FAIL E_NODOCK", P.Reply(15, "FAIL", code="E_NODOCK")),
    ("EVT ESTOP", P.Event("ESTOP")),
    ("EVT NOSE 1", P.Event("NOSE", "1")),
    ("EVT LIMIT Z_HOME\r\n", P.Event("LIMIT", "Z_HOME")),
])
def test_parse_golden(line, expected):
    assert P.parse_line(line) == expected


def test_parse_telemetry():
    tel = P.parse_line("TEL t=1234 z=194.00 y=177.0 l=10.5 r=-3 en=1 busy=ZY sw=1c vbat=15.42 ibat=-1.20 "
                       "vmot=15.2 dock=24.0 fa=E fb=P homed=ZY extra=9")
    assert tel.t == 1234 and tel.z == 194.0 and tel.y == 177.0 and tel.en and tel.busy == "ZY"
    assert tel.nose and tel.slot_loaded("A") and tel.slot_loaded("B")
    assert not tel.pressed(P.SW_Z_HOME)
    assert tel.ibat == -1.2 and tel.fa == "E" and tel.homed == "ZY"


def test_telemetry_roundtrip():
    tel = P.Telemetry(t=5, z=110, y=0, en=True, busy="", sw=0x06, vbat=15.1, ibat=0.3, vmot=15, dock=0, homed="ZY")
    assert P.parse_line(P.format_telemetry(tel)) == tel


@pytest.mark.parametrize("bad", ["", "hello", "12 MAYBE", "13 ERR", "EVT", "TEL z"])
def test_parse_rejects(bad):
    with pytest.raises(P.ProtocolError):
        P.parse_line(bad)
