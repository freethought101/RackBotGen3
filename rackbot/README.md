# rackbot — Raspberry Pi application

Implements `docs/spec/03-software.md` §2–§7: mission state machine, ESP32 serial client, rack Modbus client,
vision/approach controller, simulated drive health, energy accounting, SQLite store and the IIoT dashboard.

## Run (laptop, simulation)

```
cd rackbot
uv sync
uv run python -m rackbot.main --sim --speed 4     # dashboard on http://localhost:8000
uv run pytest                                     # ~30 s, the simulator runs 100x real time
```

`--sim` swaps in `MockMotion` (simulated firmware with the §3 interlocks), `MockRack` (in-memory PLC running
the §4 ladder) and `SimVision`, all sharing one `SimWorld` (robot pose, stations, shelves, caddies).
`--speed N` runs the simulation N times faster. In the dashboard: **Inject fault** on a bay → WARN → FAILED →
auto mode queues a swap. The Simulator card presses the robot E-stop and restocks the spare station.

On the Pi (no `--sim`): `SerialMotion` on `/dev/ttyACM0`, `ModbusRack` at `192.168.8.10:502`,
`AprilTagVision` (needs `pip install .[pi]` plus `python3-picamera2`/`python3-opencv` from apt).

## Layout

| Module | Spec | Content |
|---|---|---|
| `config.py`, `config.yaml` | 01 §1, 03 §5.1 | geometry, `z_for()`, shelves |
| `protocol.py` | 03 §3 | line encode/parse, TEL, sw bits |
| `motion.py` | 03 §3, §8 | `SerialMotion`, `MockMotion` |
| `rack.py` | 03 §4 | register map, `decode()`, `plc_scan()`, `ModbusRack`, `MockRack` |
| `vision.py` | 03 §6 | `approach_step()`, `SimVision`, `AprilTagVision` |
| `mission.py` | 03 §5 | primitives, job states, retries, FAULT/resume/abort, E-stop |
| `health.py`, `energy.py`, `store.py` | 03 §7 | SMART model, Wh integration, SQLite |
| `system.py`, `web/`, `main.py` | 03 §2, §7 | wiring, auto mode, lamps, REST/WS, dashboard |

## Behaviour beyond the spec / open points

- **Resume** re-runs the faulted state; each state first checks whether its goal is already met (slot switches),
  so resuming after a fault that happened mid-state is safe. If the drivers lost power, resume re-homes Y then Z first.
- **Home** is the spare station (`config.HOME`): it has the charging dock and the PLC dock switch X4. A job starts
  there with the pick from S1 and ends there after placing the RMA caddy in S2, so RETURN normally just turns the
  dock power back on.
- **Abort** marks the job aborted and drives back home; caddies stay where they are (inventory shows them).
- **Job preconditions**: robot docked at the spare station, bay occupied, a good spare in S1, S2 empty, tray empty.
  Otherwise the job is `rejected`.
- **Approach**: besides "tag lost > 0.5 s", the robot also backs off when it gets closer than `abort_d` (200 mm)
  without meeting the hand-off criteria; otherwise it would creep into the station misaligned.
- **Protocol details fixed by the firmware** (`firmware/motion`, recorded in 03 §3 since spec v0.1.9):
  - A motion cancelled by `STOP` (or `ENABLE 0`) answers `FAIL E_STOPPED`.
  - `STATUS` answers `OK` followed by one `TEL` line.
  - `TEL busy=` letters: `Z`, `Y`, `D` (drive/turn/dock), `F` (finger), `V` (velocity mode).
  - Extra events: `EVT BOOT RBG3-FW <ver>`, `EVT DRIVER_RESET`, `EVT SLOT_A|SLOT_B 0|1`, `EVT BADLINE`.
  - When the battery is full there is no charge current, so RETURN accepts `vbat ≥ 16.6 V` instead of `ibat < 0`.
- `tests/test_firmware_link.py` runs `SerialMotion` against the firmware core (host simulator on a pty);
  build it first with `make -C ../firmware/motion/sim`, otherwise the test is skipped.
- Camera stream (`/video.mjpg`) returns 503 for now; the real camera pipeline and calibration tools (`tools/`) are next.
