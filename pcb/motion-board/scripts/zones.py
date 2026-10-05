"""Add the antenna keep-out and GND pours for RBG3-MOTION v1 (idempotent).

  .../python3 scripts/zones.py [B|F|both]     default: both
"""

import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "rbg3-motion.kicad_pcb")
MM = pcbnew.FromMM

BOARD_RECT = (100.0, 100.0, 200.0, 200.0)
ANTENNA_KEEPOUT = (167.5, 100.0, 200.0, 116.0)   # DevKit antenna end (above J1 pin 1 at y = 117)


def outline(zone, x0, y0, x1, y1):
    poly = pcbnew.SHAPE_POLY_SET()
    poly.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        poly.Append(MM(x), MM(y))
    zone.SetOutline(poly)
    poly.thisown = False   # the zone owns the outline now; Python must not free it


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    layers = {"B": [pcbnew.B_Cu], "F": [pcbnew.F_Cu], "both": [pcbnew.F_Cu, pcbnew.B_Cu]}[which]
    board = pcbnew.LoadBoard(BOARD)

    # Add-only: pcbnew's SWIG wrappers misbehave after a Remove(), so old pours and tracks are
    # stripped beforehand as text by scripts/fix_text.py, and this script adds what is missing.
    have_keepout = any(z.GetIsRuleArea() and z.GetZoneName() == "antenna_keepout" for z in board.Zones())
    have_pour = {z.GetLayer() for z in board.Zones() if not z.GetIsRuleArea()}

    if not have_keepout:
        add_keepout(board)
    gnd = board.FindNet("/GND")
    for layer in layers:
        if layer not in have_pour:
            add_pour(board, gnd, layer)

    board.BuildConnectivity()
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.Save(BOARD)
    print(f"keep-out + GND pour on {which}; zones now: {len(list(board.Zones()))}")


def add_keepout(board):
    keep = pcbnew.ZONE(board)
    keep.SetIsRuleArea(True)
    keep.SetZoneName("antenna_keepout")
    keep.SetDoNotAllowTracks(True)
    keep.SetDoNotAllowVias(True)
    keep.SetDoNotAllowZoneFills(True)
    keep.SetDoNotAllowPads(False)
    keep.SetDoNotAllowFootprints(False)
    lset = pcbnew.LSET()
    lset.AddLayer(pcbnew.F_Cu)
    lset.AddLayer(pcbnew.B_Cu)
    keep.SetLayerSet(lset)
    outline(keep, *ANTENNA_KEEPOUT)
    board.Add(keep)


def add_pour(board, gnd, layer):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(gnd)
    z.SetLocalClearance(MM(0.3))
    z.SetMinThickness(MM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)   # solid: avoids starved thermals on the crowded 2-layer board
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetThermalReliefGap(MM(0.4))
    z.SetThermalReliefSpokeWidth(MM(0.5))
    outline(z, *BOARD_RECT)
    board.Add(z)

if __name__ == "__main__":
    main()
