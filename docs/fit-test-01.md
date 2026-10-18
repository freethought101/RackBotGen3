# Fit test 1: caddy, shelf, dummy drive (7–12 Oct)

Goal: catch printer tolerance errors before printing the 6 caddies, 6 shelves and the robot parts.
STLs in `cad/STL/fit/` (coupons) and `cad/STL/` (full parts). Record results in the Notion backlog (T1, T2).

## Print order

| # | File | Material | Orientation | ≈ time | Why |
|---|---|---|---|---|---|
| 1 | `fit/hole_coupon.stl` | PETG | flat, as modeled | 40 min | Hole sizes used on all printed parts |
| 2 | `fit/shelf_slice.stl` | PETG | floor down | 50 min | Front 40 mm of the shelf: lead-in, guide walls, M5 flange |
| 3 | `fit/caddy_slice.stl` | PETG | floor down | 40 min | Rear 40 mm of the caddy (rails, walls, rear ramp) |
| 4 | `caddy.stl` | PETG | floor down, no supports | 6 h | Full caddy: notch, labels, drive screws |
| 5 | `bay_shelf.stl` | PETG | floor down | 3 h | Full shelf: switch bracket, back stop |
| 6 | `dummy_drive_shell.stl` + `dummy_drive_lid.stl` | PLA | floor down / flat | 3 h | Envelope and ballast |

Use the same slicer profile you will use for the full set (≥ 4 walls on the caddy handle block), at 100 % scale with
no hole compensation. If a print service makes the parts, ask them to print the hole coupon first and send caliper
readings of its 6 holes before the full run.
Don't print 4–6 until 1–3 pass.

## 1. Hole coupon (holes small → large from the chamfered corner)

| Hole | Design Ø | Test | Pass |
|---|---|---|---|
| 1 | 1.7 | M2 self-tapping screw threads in firmly, no splitting | [ ] |
| 2 | 2.5 | M3 self-tapping screw threads in (dummy drive bottom holes) | [ ] |
| 3 | 3.4 | M3 bolt passes freely (the caddy drive-screw slots are 3.7 for 6-32 HDD screws) | [ ] |
| 4 | 4.0 | M3 heat-set insert goes in straight and holds | [ ] |
| 5 | 5.3 | M5 bolt passes freely; the NEMA17 5 mm shaft slides in (same size as the drive hub bore) | [ ] |
| 6 | 6.4 (blind 12) | M5 heat-set insert goes in straight and holds | [ ] |

If a hole is off, measure it with calipers and tell me the result, e.g. "5.3 printed as 5.0". I'll update
`M5_CLEAR` and the other hole constants in `cad/src/lib/dims.py` and regenerate everything.

## 2–3. Slice fit (the 1 mm/side channel clearance)

- [ ] Caddy slice slides into the shelf slice from the front by hand, ≤ 5 N, no binding, no rocking > 1 mm.
- [ ] Rear ramp rides over the front edge of the shelf even when started 1–2 mm low.
- [ ] Lead-in centers the slice when started 5 mm off to either side.
- [ ] Measure: shelf channel (design 116.0) ____ mm; caddy over rails (design 114.0) ____ mm.

Too tight or too loose → send me both measurements and I'll adjust `BAY_CHANNEL_W` or `CADDY_RAIL_W`.

## 4–6. Full parts

- [ ] Caddy slides fully home to the back stop; rear face meets the stop flat.
- [ ] Hook notch 12 × 8 is clean (no sagging on the top edge) and the 10 mm finger enters it with ≈ 1 mm play each side.
- [ ] A real 3.5" drive (if you have one) fits the pocket. Check that its bottom screw holes line up with the slots (`HDD_HOLE_Y`)
      and that 6-32 HDD screws pass the 3.7 mm slots.
- [ ] KW11-3Z switch screws onto the shelf bracket (9.5 mm hole pitch?), and the lever clicks in the last ≈ 3 mm of caddy travel.
- [ ] Dummy lid drops into the rebate flush, with the 4 × M3 inserts holding.
- [ ] **T2:** dummy + ballast weighs 600 ± 30 g. Caddy + dummy is ≈ 0.75 kg, under the 1.0 kg design load.
- [ ] Shelf bolts to a 2020 offcut with M5 button heads + T-nuts, and a hex key reaches the counterbores through the channel.
- [ ] Masses: caddy ____ g (CAD ≈ 96), shelf ____ g (≈ 61).

## Robot parts (when printed)

- [ ] Drive hub slides onto the motor shaft by hand (bore 5.3); the set screw locks it with no wobble.
- [ ] Mast collar slides onto the 2040 by hand (0.3 mm per side) and doesn't rock once the gusset screws are in.
