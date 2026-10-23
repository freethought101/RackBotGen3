"""Deck cut file (DXF) for a laser shop: the deck's outline and every through-hole, 1:1 in mm, viewed from above.
Same geometry as the printed deck (deck.py); for 5 mm acrylic, or another sheet once DECK_Z is changed to match.
"""

from cadgen import build123d as bd
from cadgen import dxf

from lib.robot_dims import DECK_Z
from robot.deck import deck


@dxf(out="../../DXF/robot/deck.dxf")
def deck_dxf():
    z0, z1 = DECK_Z
    cut = bd.section(deck(), bd.Plane.XY.offset((z0 + z1) / 2))
    cut = bd.Pos(0, 0, -(z0 + z1) / 2) * cut
    cut.label = "deck_cut"
    return cut


if __name__ == "__main__":
    deck_dxf()
