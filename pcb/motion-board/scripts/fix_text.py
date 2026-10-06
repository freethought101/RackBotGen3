"""Plain-text fix-ups on the board and library files (no pcbnew; safe to repeat).

1. Net names get the schematic's sheet prefix ("GND" -> "/GND"). The MCP schematic->board sync
   writes bare label names, while KiCad names local-label nets "/NAME" on the root sheet; DRC
   parity and the net-class patterns expect the prefixed form.
2. Old copper pours, rule areas and tracks are stripped: zones.py and Freerouting regenerate them
   (pcbnew's SWIG wrappers misbehave after Remove(), so removal happens here as text).
3. Pads of intentionally unconnected pins get the schematic's "unconnected-(...)" net names, so
   the DRC schematic-parity check is clean.
4. The ESP32-S3-DevKitC-1 socket courtyard covers only the two header strips, so low SMD parts can
   sit under the plugged-in module (~8.5 mm above the board). The module outline stays on F.Fab.
"""

import os
import re
import subprocess
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "rbg3-motion.kicad_pcb")
FP_LIB = os.path.join(HERE, "..", "lib", "rbg3.pretty", "ESP32-S3-DevKitC-1_Socket.kicad_mod")
U1_COURTYARD = [(-1.5, -1.5, 1.5, 54.84), (21.5, -1.5, 26.9, 54.84)]


def block_end(text, start):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i + 1
    raise ValueError("unbalanced")


def courtyard_rects(indent):
    out = []
    for x0, y0, x1, y1 in U1_COURTYARD:
        out.append(f'(fp_rect (start {x0} {y0}) (end {x1} {y1}) (stroke (width 0.05) (type default)) '
                   f'(fill none) (layer "F.CrtYd") (uuid "{uuid.uuid4()}"))')
    return ("\n" + indent).join(out)


def replace_courtyard(text, scope_start, scope_end):
    """Replace every F.CrtYd fp_rect/fp_line inside text[scope_start:scope_end] with U1_COURTYARD."""
    pieces, pos, done = [], scope_start, False
    for m in re.finditer(r"\((fp_rect|fp_line)\b", text[scope_start:scope_end]):
        s = scope_start + m.start()
        if s < pos:
            continue
        e = block_end(text, s)
        if '"F.CrtYd"' in text[s:e]:
            line_start = text.rfind("\n", 0, s) + 1
            indent = text[line_start:s]
            pieces.append(text[pos:s])
            pieces.append("" if done else courtyard_rects(indent))
            done = True
            pos = e
    pieces.append(text[pos:scope_end])
    return text[:scope_start] + "".join(pieces) + text[scope_end:], done


def strip_top_level(text, kinds):
    """Remove top-level (kind ...) blocks of the board (depth 1 under kicad_pcb)."""
    out, pos, depth, count, i = [], 0, 0, 0, 0
    while i < len(text):
        c = text[i]
        if c == "(":
            if depth == 1 and re.match(r"\((%s)\b" % "|".join(kinds), text[i:i + 12]):
                end = block_end(text, i)
                line_start = text.rfind("\n", 0, i) + 1
                out.append(text[pos:line_start])
                pos = i = end
                if pos < len(text) and text[pos] == "\n":
                    pos = i = pos + 1
                count += 1
                continue
            depth += 1
        elif c == ")":
            depth -= 1
        elif c == '"':
            i = text.index('"', i + 1)
            while text[i - 1] == "\\":
                i = text.index('"', i + 1)
        i += 1
    out.append(text[pos:])
    return "".join(out), count


def unconnected_nodes():
    """[(net_name, ref, pin)] for the schematic's unconnected-(...) nets (kicad-cli netlist)."""
    net = os.path.join(HERE, "..", "build", "schematic.net")
    os.makedirs(os.path.dirname(net), exist_ok=True)
    subprocess.run(["/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli", "sch", "export", "netlist",
                    "--format", "kicadsexpr", "-o", net, os.path.join(HERE, "..", "rbg3-motion.kicad_sch")],
                   check=True, capture_output=True)
    text = re.sub(r"\s+", " ", open(net).read())
    out = []
    for blk in text.split("(net (code")[1:]:
        name = re.search(r'\(name "([^"]+)"\)', blk).group(1)
        if name.startswith("unconnected-"):
            out += [(name, ref, pin) for ref, pin in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', blk)]
    return out


def assign_unconnected(board):
    count = 0
    for name, ref, pin in unconnected_nodes():
        m = re.search(r'\(property "Reference" "%s"' % re.escape(ref), board)
        if not m:
            continue
        fp_start = board.rfind("(footprint ", 0, m.start())
        fp_end = block_end(board, fp_start)
        pos = fp_start
        while True:
            pm = re.compile(r'\(pad "%s" ' % re.escape(pin)).search(board, pos, fp_end)
            if not pm:
                break
            pad_end = block_end(board, pm.start())
            pad = board[pm.start():pad_end]
            if "(net " not in pad:
                pad = pad.replace("(uuid", '(net "%s")\n\t\t\t(uuid' % name, 1)
                board = board[:pm.start()] + pad + board[pad_end:]
                fp_end = block_end(board, fp_start)
                pad_end = pm.start() + len(pad)
                count += 1
            pos = pad_end
    return board, count


def main():
    board = open(BOARD).read()
    board, n = re.subn(r'\(net "(?!/|unconnected-)([^"]+)"\)', r'(net "/\1")', board)
    board = board.replace('(net "/unconnected-', '(net "unconnected-')
    board, stripped = strip_top_level(board, ("zone", "segment", "via", "arc"))
    board, nc = assign_unconnected(board)

    m = re.search(r'\(footprint "rbg3:ESP32-S3-DevKitC-1_Socket"', board)
    if m:
        end = block_end(board, m.start())
        board, ok = replace_courtyard(board, m.start(), end)
    open(BOARD, "w").write(board)

    lib = open(FP_LIB).read()
    have = re.findall(r'\(fp_rect \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)[^\n]*"F\.CrtYd"', lib)
    lib_ok = sorted(tuple(float(v) for v in r) for r in have) == sorted(U1_COURTYARD)
    if not lib_ok:   # rewrite only when needed, so rebuilds don't churn the library file
        lib, lib_ok = replace_courtyard(lib, 0, len(lib))
        open(FP_LIB, "w").write(lib)
    print(f"stripped {stripped} zones/tracks; prefixed {n} net refs; named {nc} unconnected pads; U1 courtyard replaced on board={bool(m)} library={lib_ok}")


if __name__ == "__main__":
    main()
