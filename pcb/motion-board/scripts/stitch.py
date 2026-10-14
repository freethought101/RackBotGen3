"""Drop GND stitching vias on a grid wherever they clear all non-GND copper (add-only).

Ties the F.Cu and B.Cu GND pours together so neither pour fragments into islands.
Run after the routes are imported and before the final zone fill (scripts/build.sh).
"""

import math
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "rbg3-motion.kicad_pcb")
MM = pcbnew.FromMM

PITCH = 5.0
MARGIN = 2.5                      # from the board edge
VIA_D, VIA_DRILL = 0.6, 0.3
CLEAR = 0.45                      # copper-to-copper for the new via (rule 0.2 + margin)
AREA = (100.0, 100.0, 200.0, 200.0)
KEEPOUTS = [(167.5, 100.0, 200.0, 116.0)]   # antenna keep-out (see zones.py)
HOLE_KEEPOUT = 4.0                          # around M3 mounting holes
PAD_VIA_RADII = (2.0, 2.5, 3.0)             # second pass: via rings around through-hole GND pads


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def main():
    board = pcbnew.LoadBoard(BOARD)
    gnd = board.FindNet("/GND")
    to_mm = pcbnew.ToMM

    obstacles = []          # (kind, data) in mm
    for t in board.GetTracks():
        if t.GetNetname() == "/GND" and t.Type() == pcbnew.PCB_TRACE_T:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            obstacles.append(("circle", (to_mm(t.GetX()), to_mm(t.GetY()), to_mm(t.GetWidth(pcbnew.F_Cu)) / 2)))
        else:
            s, e = t.GetStart(), t.GetEnd()
            obstacles.append(("seg", (to_mm(s.x), to_mm(s.y), to_mm(e.x), to_mm(e.y), to_mm(t.GetWidth()) / 2)))
    holes, gnd_pth = [], []
    for fp in board.GetFootprints():
        if fp.GetReference().startswith("H"):
            holes.append((to_mm(fp.GetX()), to_mm(fp.GetY())))
        for pad in fp.Pads():
            if pad.GetNetname() == "/GND" and pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                gnd_pth.append((to_mm(pad.GetX()), to_mm(pad.GetY())))
            bb = pad.GetBoundingBox()
            obstacles.append(("box", (to_mm(bb.GetLeft()), to_mm(bb.GetTop()),
                                      to_mm(bb.GetRight()), to_mm(bb.GetBottom()))))

    r = VIA_D / 2

    def clear(x, y):
        if any(k[0] <= x <= k[2] and k[1] <= y <= k[3] for k in KEEPOUTS):
            return False
        if any(math.hypot(x - hx, y - hy) <= HOLE_KEEPOUT for hx, hy in holes):
            return False
        for kind, d in obstacles:
            if kind == "seg" and seg_dist(x, y, *d[:4]) < d[4] + r + CLEAR:
                return False
            if kind == "circle" and math.hypot(x - d[0], y - d[1]) < d[2] + r + CLEAR:
                return False
            if kind == "box" and (d[0] - r - CLEAR < x < d[2] + r + CLEAR
                                  and d[1] - r - CLEAR < y < d[3] + r + CLEAR):
                return False
        return True

    def add_via(x, y):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        v.SetWidth(MM(VIA_D))
        v.SetDrill(MM(VIA_DRILL))
        v.SetNet(gnd)
        board.Add(v)
        obstacles.append(("circle", (x, y, r)))
        vias.append((x, y))

    vias = []
    x = AREA[0] + MARGIN
    while x <= AREA[2] - MARGIN:
        y = AREA[1] + MARGIN
        while y <= AREA[3] - MARGIN:
            if clear(x, y):
                add_via(x, y)
            y += PITCH
        x += PITCH
    grid = len(vias)

    # Second pass: a via next to every through-hole GND pad that has none close by. Traces can box
    # a pad's pour in on both layers (e.g. a StepStick CLK pin), which the coarse grid misses.
    for px, py in gnd_pth:
        if any(math.hypot(px - vx, py - vy) < PAD_VIA_RADII[-1] + 0.5 for vx, vy in vias):
            continue
        for rad in PAD_VIA_RADII:
            spot = next(((px + rad * math.cos(a), py + rad * math.sin(a))
                         for a in (i * math.pi / 8 for i in range(16))
                         if clear(px + rad * math.cos(a), py + rad * math.sin(a))), None)
            if spot:
                add_via(*spot)
                break
    board.Save(BOARD)
    print(f"stitching vias placed: {grid} on the grid, {len(vias) - grid} next to GND pads")


if __name__ == "__main__":
    main()
