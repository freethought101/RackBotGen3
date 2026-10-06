# Models

Frame for all bay-side parts: x = across the bay (0 = centerline), y = into the bay
(0 = rack face), z = up (0 = shelf floor top). Shared numbers: `lib/dims.py`
(source of truth: `docs/spec/01-mechanical.md` §1).

| Script | Output | Purpose | Print |
| --- | --- | --- | --- |
| caddy.py | STEP/caddy.step, STL/caddy.stl | 3.5" drive caddy with hook notch and tag/QR recesses | PETG ×6, floor down, no supports |
| dummy_drive_shell.py | STEP/…, STL/dummy_drive_shell.stl | Ballast shell, 3.5" envelope, heat-set inserts | PLA ×6, floor down |
| dummy_drive_lid.py | STEP/…, STL/dummy_drive_lid.stl | Screw-on lid with label recess | PLA ×6, flat |
| bay_shelf.py | STEP/bay_shelf.step, STL/bay_shelf.stl | Bay shelf: guide walls, lead-in, back stop, switch bracket, M5 flanges | PETG ×6 (4 rack + 2 spare), floor down |
| bay_fit.py | STEP/bay_fit.step | Fit check: 2 shelves + caddy + dummy + 2020 stubs | — |
| dock_block.py | STEP/…, STL/dock_block.stl | Dock: V-funnel + 10 mm throat, stop at y = −30, charging-contact recesses, dock switch bracket | PETG ×2, floor down |
| tag_fin.py | STEP/…, STL/tag_fin.stl | 50 mm approach tag (ID 0 rack / ID 10 spare) on the front-right upright | PLA ×2 |
| tag_strip_rack.py | STEP/…, STL/tag_strip_rack.stl | Bay tags IDs 1–4 on the front-left upright | PLA ×1 |
| tag_strip_spare.py | STEP/…, STL/tag_strip_spare.stl | Slot tags IDs 11–12 | PLA ×1 |
| rack.py | STEP/rack.step | Rack assembly: 2020 frame, 4 shelves, caddies, dock, tags, Delta PSU/PLC placeholders | — |
| spare_station.py | STEP/spare_station.step | Spare station assembly: S1 GOOD / S2 RMA | — |

| robot/*.py | STEP/robot/…, STL/robot/… | 14 printed robot parts: nose, deck, drive_bracket (×2, one mirrored), mast_collar, mast_top_plate, z_carriage, tray_stack, rail_bracket, y_idler_bracket, y_carriage (with belt clamp), finger (×2), electronics_tray, pi_tray, battery_box | PETG |
| robot_assembly.py | STEP/robot_assembly.step | Robot at a travel pose (Z 210, extractor home) | — |
| robot_docked.py | STEP/robot_docked.step | Rack + robot docked, extracting from bay 2 (Y = 175, finger B engaged) | — |

Robot frame = rack frame with the robot docked (nose tip on the stop at y = −30). Dimensions:
`lib/robot_dims.py`; assembly factory `lib/robot_build.py` (`robot_parts(Z, Y, fingers)`); purchased parts
are envelope stand-ins in `lib/vendor.py` (NEMA17, MG90S, wheels, casters, Pi, battery, KP08…), and the motion
board is the real KiCad STEP export. Robot nested scripts run as `PYTHONPATH=src python src/robot/<part>.py`.

2020 cut list: rack 2 × 220, 4 × 320, 2 × 180; spare station 2 × 220, 4 × 215, 2 × 180;
robot 2 × 300 (rails), 3 × 110 (cross members), 1 × 285 (Y rail); 2040 × 420 (mast).

Build (from `cad/`): `PYTHONPATH=src python src/<model>.py` (with `python` = the cadgen uvx Python).
Checks: `PYTHONPATH=src python checks/bay_fit_check.py`, `checks/station_check.py` (station vs robot probe boxes) and
`checks/robot_check.py` (self-interference over 18 poses, lift sweep while docked, extract/insert at every bay and
spare slot with finger-in-notch, carrying two caddies, camera sight lines and FOV, mass/CG/tip-over, packing, print bed).

To verify on real hardware: 3.5" bottom hole positions (`HDD_HOLE_Y`, slotted ±3 mm),
KW11-3Z switch hole pitch and actuation point (bracket slotted ±2 mm).
