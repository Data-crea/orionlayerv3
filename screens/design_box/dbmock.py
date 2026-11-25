"""The designer's pickers (special, weapon, shield and computer) as Data's mockup draws them —
HD EXTENSION `picker_mockup` (work order 434, Data, 25 November 2026).

DRAWING ONLY, at the original's own positions: a faint rule under every row,
the row under the pointer on a bar (only where the original lets it be
picked: a dim row is not offered, `dbfit`), and between the two scroll
buttons a track with a thumb that says where the window stands in the list
(the buttons stay the engine's own fields; the track is not clicked).
Everything takes the frame colour.
"""
import pygame

from core import nativedraw as nd
from core.hud import hover as hud_hover
from core.hud import text as hudtext


def accent():
    return hudtext.colour("label")


def row_rule(surface, rect):
    """The faint rule under a row, the accent at a quarter of its light."""
    col = tuple(int(c * 0.28) for c in accent())
    # LOOK EXCEPTION marking: the faint rule between two picker rows in the frame colour's accent (Data's mockup of 25 November 2026)
    pygame.draw.line(surface, col, (rect.x, rect.bottom - 1),
                     (rect.right, rect.bottom - 1))


def hover_bar(surface, rect):
    """The bar under the pointer: a dark accent fill under a lit outline."""
    col = accent()
    # LOOK EXCEPTION marking: the picker's row under the pointer on a bar in the frame colour's accent (Data's mockup)
    fill = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(fill, (*col, 46), fill.get_rect(),
                     border_radius=max(3, rect.h // 5))
    surface.blit(fill, rect.topleft)
    pygame.draw.rect(surface, col, rect, width=1,
                     border_radius=max(3, rect.h // 5))


def hovered(rect):
    return hud_hover.pointer_state(rect) != "normal"


def track(surface, screen, buttons, first, visible, total):
    """The scroll track between the two buttons: `buttons` are the engine's
    two fields (up above, down below, as the list gives them)."""
    if len(buttons) != 2 or total <= visible:
        return
    up, down = sorted(buttons, key=lambda f: f.y)
    a = nd.rect(screen.layout, (up.x, up.y, up.x_end, up.y_end))
    b = nd.rect(screen.layout, (down.x, down.y, down.x_end, down.y_end))
    box = pygame.Rect(a.x, a.bottom + 4, a.w, b.y - a.bottom - 8)
    if box.h < 12:
        return
    col = accent()
    # LOOK EXCEPTION marking: the scroll track and thumb in the frame colour's accent (HD EXTENSION picker_mockup)
    pygame.draw.rect(surface, tuple(int(c * 0.28) for c in col), box,
                     border_radius=box.w // 2)
    size = max(box.w * 2, int(box.h * visible / total))
    size = min(size, box.h)
    limit = max(1, total - visible)
    at = box.y + int((box.h - size) * min(first, limit) / limit)
    pygame.draw.rect(surface, col, pygame.Rect(box.x, at, box.w, size),
                     border_radius=box.w // 2)
