# Fit test 2: hole coupon R5 (before the robot print run)

Fit test 1 measured 6 holes once each (`fit-test-01.md`): design → printed 2.5 → 2.11, 3.4 → 3.19, 4.0 → 3.58,
5.3 → 5.08, 6.4 → 5.75, i.e. **0.2–0.65 mm under**, worst on the larger holes. All hole sizes are now constants in
`cad/src/lib/dims.py` (and `ECC_HOLE_D` in `robot_dims.py`) modeled oversize from those numbers. Several sizes were
never printed, and one reading per hole is noisy, so print this coupon with the robot run's slicer profile first.

File: `cad/STL/fit/hole_coupon.stl` (135 × 36 × 14, PETG, flat as modeled, ≈ 1 h). Small end = chamfered corner.

## Row 1 (through holes, small → large)

| # | Hole | Design Ø | Expected printed | Test (pass) | Measured |
|---|---|---|---|---|---|
| 1 | M2 self-tap pilot (switches, servo tabs, horn) | 1.95 | ≈ 1.6 | M2 self-tapper bites firmly, no split | |
| 2 | M2.5 self-tap pilot (Pi) | 2.4 | ≈ 2.05 | M2.5 self-tapper bites firmly | |
| 3 | M3 self-tap (dummy drive) | 2.85 | ≈ 2.5 | M3 self-tapper bites firmly | |
| 4 | M3 clearance | 3.6 | ≈ 3.3–3.4 | M3 passes freely | |
| 5 | 6-32 drive screw (caddy) | 4.0 | ≈ 3.6–3.8 | 6-32 / M3.5 passes freely | |
| 6 | M3 heat-set insert | 4.4 | ≈ 4.0 | insert goes in straight and holds (measure its OD) | |
| 7 | M5 clearance | 5.5 | ≈ 5.3 | M5 passes freely | |
| 8 | 5 mm shaft bore (drive hub) | 5.3 | ≈ 5.1 | NEMA17 shaft slides in, no wobble | |

## Row 2

| # | Hole | Design | Expected printed | Test (pass) | Measured |
|---|---|---|---|---|---|
| 9 | M3 nut pocket (hex, 3 deep) | 6.3 AF | ≈ 5.7–6.0 | M3 nut drops in, doesn't turn | |
| 10 | M3 button-head counterbore (3 deep) | 6.9 | ≈ 6.25 | M3 button head (Ø5.7) sits flush | |
| 11 | M5 heat-set insert (blind 12) | 7.0 | ≈ 6.35 | insert goes in straight and holds | |
| 12 | Eccentric spacer boss | 7.9 | ≈ 7.25 | the Ø7.11 boss turns by hand, no play | |
| 13 | M5 button-head counterbore (3 deep) | 10.4 | ≈ 9.75 | M5 button head (Ø9.5) + hex key fit | |

Send the measurements (two readings per hole, at 90°) and I'll adjust the constants. Most important: 1, 6, 9, 11, 12.

## Sizes that don't need the coupon

Clearances big enough to absorb 0.65 mm: NEMA boss Ø23 (boss 22), Tr8 clearance Ø10, drive-bracket head access 10.5,
tray axle-nut pocket Ø12 (nylock 9.2 across corners), M2 head access 5.5, preload-key access 5.5, horn screw 2.5
(prints ≈ 2.1 for M2), idler countersink 10.4 (head 9.4), camera slot (0.4 fit per side, set from fit test 1).
