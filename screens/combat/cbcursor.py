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
"""
from core import cursor
from .cbbeamfx import get_angle

#: the original's pointer pictures are 24 px a side, the point 12 px in
SIDE, HOTSPOT = 24, 12


def get_facing(x1, y1, x2, y2):
    """`Get_Facing` (cmbtmov1.cpp:573-592): 16 facings, 0 east, counter-
    clockwise on the screen, rounded half up."""
    a = (-get_angle(x2 - x1, y2 - y1)) % 360
    return ((a * 4 + 45) // 90) & 15


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
        n = icon(unit, cell)
        k = max(1, int(win_h / 480))
        key = (n, k, id(art))
        img = self._scaled.get(key)
        if img is None:
            shape = art.cursor_shape(n)
            if shape is None:
                cursor.clear_override()
                return None
            import pygame
            img = self._scaled[key] = pygame.transform.scale(
                shape, (SIDE * k, SIDE * k))
        cursor.set_override(img, (HOTSPOT * k, HOTSPOT * k))
        return n

    def clear(self):
        cursor.clear_override()
