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

Build (from `cad/`): `PYTHONPATH=src python src/<model>.py` (with `python` = the cadgen uvx Python).
Check: `PYTHONPATH=src python checks/bay_fit_check.py`.

To verify on real hardware: 3.5" bottom hole positions (`HDD_HOLE_Y`, slotted ±3 mm),
KW11-3Z switch hole pitch and actuation point (bracket slotted ±2 mm).
