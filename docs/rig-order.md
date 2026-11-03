# Rig order: still to buy (Richard), 2 Nov

Order list for the 3-bay table rig (no wheels, positions hardcoded). It is the "Dibeli Richard" table from the rig page
with the fastener fixes: fastener counts are from the CAD fastener model (`cad/src/lib/robot_fasteners.py`, the rig's
79 robot joints) plus the rack side (3 bay shelves, 4 dummy drives + caddies). Saleh's 20 orders (≈ Rp1,857,950) are
already paid and not repeated here. Prices are estimates; check each one before paying.

## Motion
- [ ] NEMA17 JK42HS40-1704 ×2 (Z and Y), make sure the 1 m cable is included, ≈ Rp336,000

## Electrical
- [ ] 22 mm push-button box, 1 hole ×1 (E-stop housing on the mast), ≈ Rp15,000
- [ ] USB-A to right-angle USB-C cable ×1 (laptop to ESP32), ≈ Rp29,000
- [ ] Heat-shrink, zip ties, double-sided tape, 1 set, ≈ Rp30,000

## Frame and fasteners
| Item | Buy | Used | Where | Est. Rp |
|---|---|---|---|---|
| 2020 corner bracket (Rajawali3D) | ≈ 26 | count the frame joints first | rack + robot frame | 50,000 |
| M5 button head ×16 / ×20 / ×25 / ×30 | 11 / 2 / 8 / 8 | 11 / 2 / 4 / 8 | collar + tray + rail bracket / nut block / tray-through-bracket + idler axle / V-wheel axles | 50,000 |
| + M5 ×10 countersunk, M5 washers | 1 + 8 | 1 | idler bracket | (above) |
| **M5 ×40 + washers** (or wood screws) | ≈ 12 | ≈ 12 | robot legs and rack feet to the 18 mm plywood (not in the CAD) | 25,000 |
| **M5 drop-in T-nuts, slot 6 (extra)** | **20** | total ≈ 90–96 with the 90 already bought | robot 18, brackets ≈ 52, shelves 18, under the board ≈ 8 | 22,000 |
| M3 socket head ×6 / ×8 / ×10 / ×12 | **22 / 12** / 2 / 4 | 22 / 8 / 2 / 4 | ×6: E-stop 2 + PCB 4 + **dummy lids 16**; ×8: Z and Y motors; ×10: belt clamp; ×12: Z mount + electronics tray to deck | 45,000 |
| M3 hex nuts | **10** | 4 | Z mount + electronics tray to deck | 2,000 |
| **M3 ×8 self-tapping, pan head** | **30** | 24 | caddy floor to dummy drive, 6 per drive (1.9 mm wall: not machine screws) | 15,000 |
| M4 ×16 socket + M4 nut | 2 + 2 | 2 + 2 | KFL08 bearing | 15,000 |
| M2 self-tapping ×6 / ×8 / ×10 | pack of 10 each | 4 / 4 / 8 | horn / servo tabs / switches (M2 strips easily) | in the M3 line |
| Heat-set inserts 3Din, M3 ×4 (OD 4.2) / M5 ×8 (OD 7) | 30 / 12 | 24 / 10 | M3: robot 8 + dummy lids 16; M5: tray back plate | 66,000 |

M5 nylock (11 used) is covered by Saleh's 15.

## Tools
- [ ] **HSS drill bits 7.0 and 7.5 mm** (open up tight eccentric-spacer holes, Ø7.9 design, and any other hole that prints small), ≈ Rp20,000
- Check the team has a soldering iron, solder and a multimeter (the multimeter sets the XL4015s to 16.8 V and 5.8 V).

## Local shop, Bali
- [ ] Plywood 18 mm, 660 × 300, and 5 mm, ≈ 250 × 300 (ask the shop to cut), ≈ Rp130,000
- [ ] Steel ballast + epoxy, ≈ 1.1 kg (2 moving dummies, 600 ± 30 g each), ≈ Rp50,000

**Total ≈ Rp900,000** (was ≈ Rp806,000 before the fastener fixes). Rig total ≈ Rp1,858k paid + ≈ Rp900k + ≈ Rp1,100k
printing ≈ **Rp3.86 M**, before shipping.

## Optional, not in the total
- MG90S spare ×1 (≈ Rp34,000, recommended), JST-XH crimp tool (≈ Rp100,000, if the team has none),
  INA226 + R010 shunt (≈ Rp28,000, only for energy per swap), AC cable + plug (≈ Rp30,000, if the adapter comes
  without one), TMC2209 spare (skip), Delta PSU DRL-24V120W1EN (≈ Rp622,000, only for a Delta part on the rig).

## Print order (same shop as fit test 1)
- Export fresh STLs from the current CAD, not the old `quote.zip`: the Z carriage changed on 2 Nov (adjustable nut
  mount, fin 2 mm higher) and the belt clamp was missing.
- Add `cad/STL/fit/hole_coupon.stl` to the batch (≈ 1 h). On pickup, check it and caliper the 4 eccentric holes
  (Z carriage +x pair, Y carriage lower pair) before assembling: 7.1–7.5 as is, 7.5–7.7 tape + CA on the collar,
  over 7.7 reprint that carriage with `ECC_HOLE_D` ≈ 7.4.
- If a different shop prints the run, set `ECC_HOLE_D` ≈ 7.4 first: the hole sizes are tuned for this shop's shrink.
