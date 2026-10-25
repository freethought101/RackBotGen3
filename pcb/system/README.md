# RBG3 system wiring (KiCad 10)

Wiring of the whole electrical system, as a KiCad schematic: the robot harness and the rack + spare station.
The motion board's own circuit is in [`../motion-board/`](../motion-board/); here it is one block (`A1`) with its
connectors J1–J19.

| Sheet | File | Contents |
|---|---|---|
| 1 | `rbg3-system.kicad_sch` | Overview |
| 2 | `robot.kicad_sch` | Battery + BMS, XT60, fuse, main switch, INA226, E-stop + VMOT relay, 5 V and servo bucks, dock pads → SS54 → charger, Pi + camera, motion board connectors, motors, switches, servos, LED, buzzer |
| 3 | `rack.kicad_sch` | Mains, 24 V PSU, rack controller terminals (PLC X0–X7 / Y0–Y3), bay switches, rack E-stop, dock relay + fuse, lamps, station cables, spare-station switches and dock contacts |
| 4 | `rack-esp32.kicad_sch` | ESP32 rack controller (PLC fallback, P40): opto input board, MOSFET modules, buck, wired to the same terminal names. The GPIO choice is a proposal until the rack firmware is written |

`rbg3-system.pdf` is the printable version.

## Conventions

- Nets connect by name: every pin end carries a local label, as on the motion board. ERC: 0 violations.
- Modules (bucks, charger, INA226, Pi, relay modules, opto board, MOSFET modules) are blocks with the pin names of a
  typical module. Check them against the module you bought before wiring.
- `GND`, `GND_5V` and `GND_6V` on the robot sheet are one node; the separate names show where each ground wire runs
  (buck output grounds go to J2/J3, spec 02 §3.3). Likewise `DOCK_PAD−` must only reach the charger's IN−.
- Cables between the rack and the spare station are blocks (`W201`, `W202`); station-side nets start with `STN_`.
- Wire gauges, connectors and the polarity rules are in the notes on each sheet.

## Rebuild

The files are generated; edit the script, not the schematics:

```
python3 pcb/system/scripts/gen_system.py
kicad-cli sch erc rbg3-system.kicad_sch          # in pcb/system/
kicad-cli sch export pdf -o rbg3-system.pdf rbg3-system.kicad_sch
```

Source of truth: [`docs/spec/02-electrical.md`](../../docs/spec/02-electrical.md) §1 (robot power), §3.2 (board
connectors), §4 (rack), §5 (safety). If the spec changes, update the script and regenerate.
