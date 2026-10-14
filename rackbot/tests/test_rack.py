from rackbot import rack as R


def test_decode():
    st = R.decode(0b1011_0101, 0b0011, 42, 0)
    assert st.bay_present == [True, False, True, False]
    assert st.dock and st.estop_ok and not st.s1_present and st.s2_present
    assert st.dock_power and st.lamp == "green" and st.plc_heartbeat == 42 and st.plc_state == "OK"


def test_plc_dock_power_interlock():
    docked_ok = 1 << R.IN_DOCK | 1 << R.IN_ESTOP_OK
    on = lambda x, lost=False: R.plc_scan(x, (True, False, False), lost)[0] & 1  # noqa: E731
    assert on(docked_ok) == 1
    assert on(1 << R.IN_ESTOP_OK) == 0            # not docked
    assert on(1 << R.IN_DOCK) == 0                # rack E-stop
    assert on(docked_ok, lost=True) == 0          # Pi watchdog lost
    assert R.plc_scan(docked_ok, (False, False, False), False)[0] & 1 == 0


def test_plc_lamps_and_state():
    ok = 1 << R.IN_ESTOP_OK
    lamp = lambda x, m, lost=False: R.decode(x, R.plc_scan(x, m, lost)[0], 0, 0).lamp  # noqa: E731
    assert lamp(ok, (False, False, False)) == "green"
    assert lamp(ok, (False, True, False)) == "yellow"
    assert lamp(ok, (False, True, True)) == "red"
    assert lamp(0, (False, False, False)) == "red"
    assert R.plc_scan(0, (False, False, False), False)[1] == 1
    assert R.plc_scan(ok, (False, False, False), True)[1] == 2
