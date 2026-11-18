"""The battle's pointer over a reachable cell — work order 303 (Data's
P1 of 302).

TRANSCRIPTION `move_pointer`: over a cell the acting ship may move to, the
original's pointer is an arrow in the move's direction — `icon =
Get_Facing(ship, cell) / 2 + 4`, icons 4-11 counter-clockwise from east
(`Assign_Mouse_Images`, combat1.cpp:2289-2296; `Get_Facing`,
cmbtmov1.cpp:573-592), its shapes the battle palette's entry's (FONTS.LBX
4, `cbart.cursor_shape`), its point the picture's middle, frame 12
(`Check_Mouse_Shape`, mouse.cpp:80-101). Elsewhere HD keeps its own
pointer. The direction is from the ship's corner cell to the cell the
click moves that corner to, as the original's.
TRANSCRIPTION `move_target` (work order 304, Data's P1 of 303): that cell
is `cbinput.move_target`'s — for a ship of size class 1 and up one cell
(size class 1-2: in the cell's left or top half) up and left of the
pointer, so the ship's middle lands under it, the arrow areas shifted to
match (combat1.cpp:850-862, :2321-2373); the red frame stands on the same
cell (`cbdraw.draw_footprint`).

TRANSCRIPTION `pointer_pictures` (work order 398, gap 6 of 397): the other
pictures of `Assign_Mouse_Images` (combat1.cpp:2213-2330), chosen by `pick`
from the same facts as the C++, each with the list entry's `frame` as its
point (`Get_Pointer_Offset`, mouse.cpp:80-101, :112-124):
  12  an enemy not held in stasis under the pointer (:2316-2322), frame 12;
      an enemy missile's, own missile's too, field (:2158-2163), frame 0
  2   an empty cell, the acting unit itself, in BOARD an own unit or no
      unit (:2279-2283, :2310-2312, :2296-2302), frame 12
  3   BOARD over a unit of another owner (:2284-2286), frame 12
  13  SCAN over a unit, 14 over none (:2269-2277), frame 12
  15-18 the clock, over the whole window, while the acting unit is not the
      player's (`cmbt_mouse_list_clock`, {icon, frame 0, 0..639 x 0..479},
      mox.cpp:892; :2214-2217; `combat_clock_frame` 15..18, cmbtdrw1.cpp:
      685-688)
The order is the C++'s: the computer's turn, then OPTIONS (the arrow),
SCAN, BOARD, the move arrows over cells the engine marks legal, the unit.
Their shapes are FONTS.LBX 4's 20 (`cbart.cursor_shape`; the extraction
holds all of 1-18). The point is the physical pointer, the same convention
as `move_target`: a frame-12 picture's middle, a frame-0 picture's corner.
DEVIATION `arrow_is_hd_pointer`: icon 1 — the original's plain arrow over its
panel, in the OPTIONS panel's orders, and over another own unit or an enemy
held in stasis (:2323-2335, mouse_list_arrow) — is HD's own pointer, as on
every HD screen. DEVIATION `clock_animates`: the original copies
`combat_clock_frame` into the clock's icon only when it rebuilds the list
(a still picture between those moments); HD steps 15 -> 18 with the
battle's own tick (`screen.ship_frame`), so the clock turns. UNVERIFIED
live: how either looks in the original and the pictures' hot points.
Under AUTO, playback, a box, the log or the help over the field: HD's own
pointer (the original keeps whatever list it set last).
"""
from core import cursor
from core import nativeview as nat
from .cbbeamfx import get_angle

#: the original's pointer pictures are 24 px a side, the point 12 px in
SIDE, HOTSPOT = 24, 12


def get_facing(x1, y1, x2, y2):
    """`Get_Facing` (cmbtmov1.cpp:573-592): 16 facings, 0 east, counter-
    clockwise on the screen, rounded half up."""
    a = (-get_angle(x2 - x1, y2 - y1)) % 360
    return ((a * 4 + 45) // 90) & 15


#: the clock's pictures (`combat_clock_frame`, cmbtdrw1.cpp:685-688)
CLOCK_FIRST, CLOCK_LAST = 15, 18
#: the list entries' `frame` = the picture's point: the grid's and the
#: whole-field entry's 12 (combinit.cpp:949-954, :961-967 and
#: combat1.cpp:2262-2330), the missile fields' and the clock's 0
#: (combat1.cpp:2162, mox.cpp:892)
GRID_FRAME, CORNER_FRAME = 12, 0


def pick(tick=None, missile=False, scan=False, board=False, move=None,
         target=None):
    """`Assign_Mouse_Images`' choice (combat1.cpp:2213-2330) as (icon,
    frame), or None where the original's picture is its arrow (icon 1: HD's
    own pointer, DEVIATION `arrow_is_hd_pointer`). `tick` is not None while
    the acting unit is not the player's (the clock); `missile` a missile
    under the pointer (its field comes after the grid's, so it wins);
    `move` the arrow's icon over a legal cell; `target` what stands on the
    pointer's cell: None, "self", "own", "enemy" or "held" (an enemy in
    stasis)."""
    if tick is not None:
        return (CLOCK_FIRST + tick % (CLOCK_LAST - CLOCK_FIRST + 1),
                CORNER_FRAME)
    if missile:
        return 12, CORNER_FRAME
    if scan:
        return (14 if target is None else 13), GRID_FRAME
    if board:
        return (3 if target in ("enemy", "held") else 2), GRID_FRAME
    if move is not None:
        return move, GRID_FRAME
    if target == "enemy":
        return 12, GRID_FRAME
    if target in (None, "self"):
        return 2, GRID_FRAME
    return None


def icon(unit, cell):
    """The arrow's picture for a move of `unit` to `cell`: 4-11."""
    return get_facing(int(unit["x"]), int(unit["y"]), cell[0], cell[1]) \
        // 2 + 4


class Pointer:
    """Sets the arrow while the pointer is over a reachable cell, gives
    the HD pointer back otherwise; scales the shape by whole steps of the
    window's height over the original's 480 lines."""

    def __init__(self):
        self._scaled = {}

    def update(self, art, unit, cell, win_h):
        if unit is None or cell is None or art is None:
            cursor.clear_override()
            return None
        return self.show(art, icon(unit, cell), GRID_FRAME, win_h)

    def show(self, art, n, frame, win_h):
        """Picture `n` with its point at `frame` px; the HD pointer when
        there is none or the extraction has no shapes."""
        if n is None or art is None:
            cursor.clear_override()
            return None
        k = max(1, int(win_h / nat.NATIVE_H))
        key = (n, k, id(art))
        img = self._scaled.get(key)
        if img is None:
            shape = art.cursor_shape(n)
            if shape is None:
                cursor.clear_override()
                return None
            import pygame
            if len(self._scaled) > 32:
                self._scaled.clear()
            img = self._scaled[key] = pygame.transform.scale(
                shape, (SIDE * k, SIDE * k))
        cursor.set_override(img, (frame * k, frame * k))
        return n

    def clear(self):
        cursor.clear_override()
