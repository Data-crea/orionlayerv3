"""The scanned ship's picture in the ship panel — work order 326 Part B.

HD EXTENSION `panel_ship_picture` (Data, WO 326, mockup.png): the ship
the panel describes is drawn a second time, large, at the panel's right,
where Data's mockup puts it (`fltplaced.SHIP_PICTURE`, the placed box
`ship_picture`, F3-editable). The original draws no ship there:
`Print_Scanned_Ship_Data_` prints only words into the window
`Set_Window_(15, 282, 320, 465)` (flt2.cpp:515-747, flt1.cpp:422-424);
the one picture it places in the panel is the captain's portrait at
(0xF2, 0x11C), top right (`Draw_Captains_Picture_`, flt2.cpp:569, :846),
which HD omits (OMISSION `captain_portrait`). Should the portrait come,
it shares this side of the panel with the picture — a layout question
then, not now.

WHICH SHIP: the panel's own — `fltscan`'s scanned icon, the ship the grid
marks (flt1.cpp:89-91) — so the picture, the mark and the words are one
value; with nothing scanned, nothing is drawn.

THE PICTURE IS THE GRID'S, through the grid's own route (`fltdraw.cell_art`'s
two steps, not a fork of them): the painted ship from the mod folder by
`core.shippicture.fitted`, fitted into the box at its own proportions; else
the original's SHIPS.LBX sprite (`fltart.Art.ship`, ken.cpp:451-466) at the
largest whole magnification that fits (`fltart.magnified`, decision 28's
deviation as in the grid). Without either (a clone with no extraction and
no mod folder) nothing is drawn and the words keep the whole panel: the
look before this order.

THE WORDS MAKE ROOM: while a picture is drawn, the panel's text area ends
`TEXT_GAP` of the panel's width before the picture's box
(`text_limit`), so the two never overlap, as in the mockup; the original's
tab stops stay fractions of whatever width that leaves (`fltpanel`).
"""
import pygame

from core import shippicture

from . import fltart
from . import fltrows

#: The placed box the picture is fitted into (`fltplaced.NAMES`).
BOX = "ship_picture"
#: The gap between the words and the picture, a share of the panel's
#: width: the mockup's specials column ends at native x ~450 and its
#: ship starts at 532 (WO 326, mockup.png). 0.01 (10 ref px; the ship is
#: centred in its box, so the drawn gap is larger): at 0.02 the longest
#: weapon line of a test ship ("6 Ion Pulse Cannon (360)", 255 ref px at
#: the panel's 20) wrapped at 3840x2160 by one pixel of rounding.
TEXT_GAP = 0.01


class _OneRow:
    """`fltrows.cells` asks a view for its rows; this is one row, so the
    panel's ship gets the grid's own sprite set and ramp rule."""

    def __init__(self, ship_idx):
        self.rows = [(-1, ship_idx, False)]


def box_rect(screen):
    box = screen.box_by_name(BOX)
    return box.screen_rect if box is not None and box.screen_rect else None


#: One snapshot's work, kept: [block, state, cell, size, fallback]. The
#: objects themselves are held and compared with `is`, so a freed block's
#: address reused by the next one cannot pass for it. The cell (a struct
#: parse) and the magnified sprite are per snapshot, not per frame.
_KEPT = [None, None, None, None, None, None]


def scanned_cell(screen):
    """The panel's ship as a `fltrows.Cell`, or None."""
    view = getattr(screen, "_view", None)
    block = getattr(view, "block", None)
    state = getattr(screen, "_state", None)
    if not block or state is None:
        return None
    icon = screen._scan.resolve(block)
    if _KEPT[0] is block and _KEPT[1] is state and _KEPT[5:] == [icon]:
        return _KEPT[2]
    ships = block.get("ship_idx") or []
    cell = None
    if 0 <= icon < len(ships):
        cells = fltrows.cells(_OneRow(ships[icon]), state)
        cell = cells[0] if cells else None
        if cell is not None and cell.picture is None:
            cell = None
    _KEPT[:] = [block, state, cell, None, None, icon]
    return cell


def picture(screen):
    """(surface, topleft) of the panel's ship in its box, or None."""
    rect = box_rect(screen)
    cell = scanned_cell(screen)
    if rect is None or cell is None or rect.w < 2 or rect.h < 2:
        return None
    hd = shippicture.fitted(getattr(screen, "app", None), cell.ramp,
                            int(cell.picture), rect, state=screen._state,
                            size=getattr(cell.view, "size", None))
    if hd is not None:
        return hd
    art = getattr(screen, "_art", None)
    if art is None or not art.available:
        return None
    if _KEPT[2] is cell and _KEPT[3] == rect.size and _KEPT[4] is not None:
        big = _KEPT[4]
    else:
        sprite = art.ship(int(cell.picture), cell.sprite_set, owner=cell.ramp)
        if sprite is None:
            return None
        drawn = sprite.get_bounding_rect(min_alpha=1)
        if drawn.w < 1 or drawn.h < 1:
            return None
        step = max(1, min(rect.w // drawn.w, rect.h // drawn.h))
        big = fltart.magnified(sprite.subsurface(drawn), step)
        _KEPT[3], _KEPT[4] = rect.size, big
    return big, (rect.x + (rect.w - big.get_width()) // 2,
                 rect.y + (rect.h - big.get_height()) // 2)


def text_limit(screen, rect):
    """`rect` (the panel's text area) ending before the picture's box
    while a picture is drawn this frame; unchanged otherwise."""
    if getattr(screen, "_panel_picture", None) is None:
        return rect
    pic = box_rect(screen)
    panel = screen.box_by_name("ship_panel")
    if pic is None or panel is None or not panel.screen_rect:
        return rect
    right = pic.x - int(round(TEXT_GAP * panel.screen_rect.w))
    if right <= rect.x or right >= rect.right:
        return rect
    return pygame.Rect(rect.x, rect.y, right - rect.x, rect.h)


def draw(surface, screen):
    drawn = getattr(screen, "_panel_picture", None)
    if drawn is not None:
        surface.blit(*drawn)
