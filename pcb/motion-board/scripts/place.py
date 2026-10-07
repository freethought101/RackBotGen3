"""Place footprints and draw the board outline for RBG3-MOTION v1.

Run with KiCad's bundled Python (pcbnew):
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 scripts/place.py

Board: 100 x 100 mm, origin (100, 100) top-left, y down (KiCad convention).
"""

import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "rbg3-motion.kicad_pcb")

X0, Y0, W, H = 100.0, 100.0, 100.0, 100.0

# reference: (x, y, rotation_deg, side)   side "F" = top, "B" = bottom
PLACEMENT = {
    # Drivers (footprint origin = pad 1, top-left) in a 2 x 2 grid, bulk caps to their right.
    "U2": (113.5, 118.0, 0, "F"), "C1": (132.6, 121.0, 0, "F"), "C2": (137.5, 114.0, 0, "F"),
    "U3": (141.5, 118.0, 0, "F"), "C3": (160.4, 121.0, 0, "F"), "C4": (164.0, 114.0, 0, "F"),
    "U4": (113.5, 150.0, 0, "F"), "C5": (132.6, 153.0, 0, "F"), "C6": (137.5, 146.0, 0, "F"),
    "U5": (141.5, 150.0, 0, "F"), "C7": (160.4, 153.0, 0, "F"), "C8": (164.0, 146.0, 0, "F"),
    # PDN_UART pin-5 solder jumpers between each socket's rows, pad 2 toward pin 5 (open by default;
    # reachable with the module unplugged).
    "JP1": (117.0, 128.16, 180, "F"), "JP2": (145.0, 128.16, 180, "F"),
    "JP3": (117.0, 160.16, 180, "F"), "JP4": (145.0, 160.16, 180, "F"),
    # ESP32-S3-DevKitC-1 socket (origin = J1 pin 1), antenna end toward the top edge.
    "U1": (170.0, 117.0, 0, "F"),
    # Motor connectors along the top edge.
    "J4": (112.0, 104.5, 0, "F"), "J5": (126.5, 104.5, 0, "F"),
    "J6": (141.0, 104.5, 0, "F"), "J7": (155.5, 104.5, 0, "F"),
    # Power and switch connectors along the bottom edge.
    # J1 XT30 rotated so its mating face sits 1.7 mm past the bottom edge (plug enters from outside).
    "J1": (111.9, 188.5, 180, "F"), "J2": (125.0, 194.5, 0, "F"), "J3": (136.5, 194.5, 0, "F"),
    "J8": (149.0, 195.5, 0, "F"), "J9": (160.0, 195.5, 0, "F"), "J10": (171.0, 195.5, 0, "F"),
    "J11": (182.0, 195.5, 0, "F"),
    # Two more switch connectors left of the DevKit USB end (a USB plug occupies y 179.5-191 under
    # the module, so nothing tall goes there).
    "J12": (155.0, 175.5, 0, "F"), "J13": (155.0, 183.5, 0, "F"),
    # Small connectors along the left edge.
    "J16": (104.5, 112.0, 270, "F"), "J17": (104.5, 129.0, 270, "F"), "J18": (104.5, 142.0, 270, "F"),
    "J19": (104.5, 152.0, 270, "F"),
    # Servo headers next to the 6 V input terminal J3.
    "J14": (127.0, 184.0, 90, "F"), "J15": (137.0, 184.0, 90, "F"),
    # Power input protection: TVS right next to J1 (a reversed harness clamps into the fuse), bulk cap above.
    "C9": (116.0, 175.0, 0, "F"), "D1": (108.5, 181.0, 90, "F"),
    # Sense dividers.
    "R1": (150.0, 172.0, 0, "F"), "R2": (150.0, 175.0, 0, "F"), "C10": (150.0, 178.0, 0, "F"),
    "R3": (110.0, 142.0, 90, "F"), "R4": (110.0, 146.0, 90, "F"), "C11": (110.0, 136.5, 90, "F"),
    # EN pull-up and UART series resistor between drivers and MCU.
    "R5": (166.5, 131.0, 90, "F"), "R6": (166.5, 136.0, 90, "F"),
    # Servo, LED, I2C, buzzer support parts near their connectors.
    "R19": (124.0, 180.0, 0, "F"), "R20": (134.0, 180.0, 0, "F"),
    "R21": (110.0, 112.0, 90, "F"), "R22": (110.0, 117.0, 90, "F"), "R23": (110.0, 129.0, 90, "F"),
    "R24": (127.0, 173.0, 0, "F"), "Q1": (132.0, 173.0, 0, "F"), "D2": (138.0, 173.0, 0, "F"),
    # Mounting holes, 93 x 93 mm pitch.
    "H1": (103.5, 103.5, 0, "F"), "H2": (196.5, 103.5, 0, "F"),
    "H3": (103.5, 196.5, 0, "F"), "H4": (196.5, 196.5, 0, "F"),
}

# Switch-input RC networks (R pull-up, R series, C filter) in a grid under the DevKit module,
# between the two socket rows (x 172..191). Low-profile 0805 parts clear the plugged-in module.
SWITCH_RC = [("R7", "R8", "C12"), ("R9", "R10", "C13"), ("R11", "R12", "C14"),
             ("R13", "R14", "C15"), ("R15", "R16", "C16"), ("R17", "R18", "C17")]
for i, (rp, rs, c) in enumerate(SWITCH_RC):
    y = 140.0 + i * 4.5
    PLACEMENT[rp] = (175.5, y, 0, "F")
    PLACEMENT[rs] = (181.5, y, 0, "F")
    PLACEMENT[c] = (187.5, y, 0, "F")


def schematic_info():
    """{ref: description} and the set of net names from the schematic netlist (kicad-cli export)."""
    import re
    import subprocess
    net = os.path.join(HERE, "..", "build", "schematic.net")
    os.makedirs(os.path.dirname(net), exist_ok=True)
    subprocess.run(["/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli", "sch", "export", "netlist",
                    "--format", "kicadsexpr", "-o", net, os.path.join(HERE, "..", "rbg3-motion.kicad_sch")],
                   check=True, capture_output=True)
    text = re.sub(r"\s+", " ", open(net).read())
    desc = {}
    for ref, body in re.findall(r'\(comp \(ref "([^"]+)"\)(.*?)\(sheetpath', text):
        fields = dict(re.findall(r'\(field \(name "([^"]+)"\) "([^"]*)"\)', body))
        m = re.search(r'\(datasheet "([^"]*)"\)', body)
        if m:
            fields.setdefault("Datasheet", m.group(1))
        m = re.search(r'\(description "([^"]*)"\)', body)
        if m:
            fields.setdefault("Description", m.group(1))
        desc[ref] = fields
    names = set(re.findall(r'\(net \(code "?\d+"?\) \(name "([^"]+)"\)', text))
    return desc, names


def fixups(board):
    desc, _ = schematic_info()   # net names are fixed beforehand by scripts/fix_netnames.py
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in desc:
            for field in fp.GetFields():
                name = field.GetName()
                if name in ("Description", "Datasheet") and name in desc[ref]:
                    text = desc[ref][name]
                    field.SetText("" if text == "~" else text)
        if ref.startswith("H"):
            fp.SetExcludedFromBOM(True)


def main():
    board = pcbnew.LoadBoard(BOARD)
    missing = []
    for ref, (x, y, rot, side) in PLACEMENT.items():
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            missing.append(ref)
            continue
        if side == "B" and not fp.IsFlipped():
            fp.Flip(fp.GetPosition(), False)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        fp.SetOrientationDegrees(rot)
    unplaced = [fp.GetReference() for fp in board.GetFootprints() if fp.GetReference() not in PLACEMENT]
    fixups(board)

    # Board outline on Edge.Cuts.
    # Outline is added only when missing: a Remove() leaves pcbnew's SWIG wrappers returning raw
    # handles for the rest of the process, so this script never removes anything.
    if any(d.GetLayer() == pcbnew.Edge_Cuts for d in board.GetDrawings()):
        board.Save(BOARD)
        print(f"placed {len(PLACEMENT) - len(missing)} footprints; missing={missing}; unplaced={unplaced}")
        return
    rect = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_RECT)
    rect.SetLayer(pcbnew.Edge_Cuts)
    rect.SetWidth(pcbnew.FromMM(0.1))
    rect.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(X0), pcbnew.FromMM(Y0)))
    rect.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(X0 + W), pcbnew.FromMM(Y0 + H)))
    board.Add(rect)

    board.Save(BOARD)
    print(f"placed {len(PLACEMENT) - len(missing)} footprints; missing={missing}; unplaced={unplaced}")


if __name__ == "__main__":
    main()
