"""Board silkscreen for RBG3-MOTION v1: board name, connector functions, pin order, polarity and
StepStick orientation marks (spec 02-electrical §3.3). Plain text, no pcbnew; safe to repeat:
every board-level gr_text is replaced by the list below.

  python3 scripts/silk.py
"""

import os
import uuid

from fix_text import block_end, strip_top_level

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "rbg3-motion.kicad_pcb")

S = 0.8   # text height (mm); stroke 0.15 mm

# (text, x, y, rotation_deg, size)
TEXTS = [
    ("RBG3-MOTION v1", 102.4, 167.0, 90, 1.2),

    # Motor connectors J4-J7: pin order under each housing, axis name below that.
    *[(pin, x0 + i * 2.5, 109.9, 0, S) for x0 in (112.0, 126.5, 141.0, 155.5)
      for i, pin in enumerate(("2B", "2A", "1A", "1B"))],
    ("MOTOR L", 115.75, 111.6, 0, S), ("MOTOR R", 130.25, 111.6, 0, S),
    ("MOTOR Z", 144.75, 111.6, 0, S), ("MOTOR Y", 159.25, 111.6, 0, S),

    # StepStick orientation: module pin names at the four corners of every socket.
    *[t for x, y in ((113.5, 118.0), (141.5, 118.0)) for t in (
        ("EN", x, y - 3.4, 0, S), ("VM", x + 12.7, y - 3.4, 0, S),
        ("DIR", x, y + 20.4, 0, S), ("GND", x + 12.7, y + 20.4, 0, S))],
    *[t for x, y in ((113.5, 150.0), (141.5, 150.0)) for t in (
        ("EN", x, y - 3.4, 0, S), ("VM", x + 12.7, y - 3.4, 0, S),
        ("DIR", x - 3.6, y + 17.78, 0, S), ("GND", x + 16.0, y + 17.78, 0, S))],
    # Socket names between the rows (visible with the module out), pin-5 UART jumper label.
    *[t for x, y, name, jp in ((113.5, 118.0, "DRIVE L", "JP1"), (141.5, 118.0, "DRIVE R", "JP2"),
                               (113.5, 150.0, "Z", "JP3"), (141.5, 150.0, "Y", "JP4")) for t in (
        (name, x + 6.35, y + 4.0, 0, S), (f"{jp} UART P5", x + 6.35, y + 12.0, 0, S))],

    # ESP32-S3-DevKitC-1 socket orientation.
    ("ANTENNA END", 181.0, 119.5, 0, S), ("ESP32-S3-DevKitC-1", 181.0, 121.5, 0, S),
    ("USB END", 181.0, 168.5, 0, S),

    # Power inputs.
    ("VMOT IN", 117.0, 184.5, 0, S),
    ("+5V", 125.0, 187.3, 0, S), ("GND", 130.08, 187.3, 0, S),
    ("+6V", 136.5, 187.3, 0, S), ("GND", 141.58, 187.3, 0, S),

    # Servo headers J14/J15: GND, +6V, signal.
    *[(pin, x0 + i * 2.54, 181.3, 0, S) for x0 in (127.0, 137.0) for i, pin in enumerate(("G", "+", "S"))],
    ("J14 SRV", 124.3, 184.0, 90, S), ("J15 SRV", 134.55, 184.0, 90, S),

    # Switch inputs J8-J13 (1 = GND, 2 = signal, 3 = 3V3).
    *[(pin, x0 + i * 2.5, 191.0, 0, S) for x0 in (149.0, 160.0, 171.0, 182.0)
      for i, pin in enumerate(("G", "S", "3V3"))],
    ("J8 Z_HOME", 151.5, 189.0, 0, S), ("J9 Y_HOME", 162.5, 189.0, 0, S),
    ("J10 NOSE", 173.5, 189.0, 0, S), ("J11 SLOT_A", 184.5, 189.0, 0, S),
    *[(pin, 155.0 + i * 2.5, y, 0, S) for y in (171.0, 180.0) for i, pin in enumerate(("G", "S", "3V3"))],
    ("J12 SLOT_B", 165.5, 176.0, 90, S), ("J13 AUX", 165.5, 184.0, 90, S),

    # Left-edge connectors (pin 1 at the top): function and pin order on one row below each housing.
    ("J16 I2C", 104.5, 123.3, 0, S), ("3V3 G SDA SCL", 106.1, 124.9, 0, S),
    ("LED 5V DI G", 103.9, 138.2, 0, S),
    ("DOCK+ V+ NC", 106.0, 148.25, 0, S),
    ("BUZZER 5V BZ-", 106.1, 158.6, 0, S),
]

# Footprints whose reference designator moves to F.Fab: the labels above already name them, and the
# designators otherwise sit on top of the pin-order rows.
FAB_REFS = ["J8", "J9", "J10", "J11", "J12", "J13", "J14", "J15", "JP1", "JP2", "JP3", "JP4"]


def ref_to_fab(board, ref):
    i = board.index(f'(property "Reference" "{ref}"')
    end = block_end(board, i)
    return board[:i] + board[i:end].replace('(layer "F.SilkS")', '(layer "F.Fab")') + board[end:]


def gr_text(text, x, y, rot, size):
    return (f'\t(gr_text "{text}"\n\t\t(at {x:g} {y:g} {rot:g})\n\t\t(layer "F.SilkS")\n'
            f'\t\t(uuid "{uuid.uuid4()}")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size:g} {size:g})\n'
            f'\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)\n')


def main():
    board = open(BOARD).read()
    board, removed = strip_top_level(board, ("gr_text",))
    for ref in FAB_REFS:
        board = ref_to_fab(board, ref)
    end = board.rstrip().rfind(")")
    board = board[:end] + "".join(gr_text(*t) for t in TEXTS) + board[end:]
    open(BOARD, "w").write(board)
    print(f"silkscreen: removed {removed}, added {len(TEXTS)} texts")


if __name__ == "__main__":
    main()
