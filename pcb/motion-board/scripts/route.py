"""Autoroute RBG3-MOTION v1 with Freerouting (Specctra DSN -> SES round trip).

  .../python3 scripts/route.py export   -> build/rbg3-motion.dsn (tracks are stripped beforehand by fix_text.py)
  java -jar ~/.kicad-mcp/freerouting.jar -de build/rbg3-motion.dsn -do build/rbg3-motion.ses -mp 60
  .../python3 scripts/route.py import   -> tracks from build/rbg3-motion.ses, zones refilled
"""

import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "rbg3-motion.kicad_pcb")
BUILD = os.path.join(HERE, "..", "build")
DSN = os.path.join(BUILD, "rbg3-motion.dsn")
SES = os.path.join(BUILD, "rbg3-motion.ses")


def main():
    mode = sys.argv[1]
    board = pcbnew.LoadBoard(BOARD)
    os.makedirs(BUILD, exist_ok=True)
    if mode == "export":
        ok = pcbnew.ExportSpecctraDSN(board, DSN)
        print("exported" if ok else "export FAILED", DSN)
    elif mode == "import":
        ok = pcbnew.ImportSpecctraSES(board, SES)
        # Freerouting necks a track down near tight pads (e.g. 0.187 mm); widen those to the 0.2 mm board minimum.
        min_w = pcbnew.FromMM(0.2)
        for t in board.GetTracks():
            if t.GetClass() == "PCB_TRACK" and t.GetWidth() < min_w:
                t.SetWidth(min_w)
        board.BuildConnectivity()
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        board.Save(BOARD)
        print("imported" if ok else "import FAILED", f"tracks={len(list(board.GetTracks()))}")


if __name__ == "__main__":
    main()
