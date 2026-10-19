"""The merge-relocation mode, shown on the map — work order 310 (309's finding 5).

F4 turns the original's merge-relocation mode on or off (`Check_Function_
Keys_`, mainscr.cpp:3112-3129): with two or more relocations it swaps the
pointer over the map to the relocation cursor (:3120, `_mouse_list_
relocation`, mox.cpp:930; v2 mainscr.cpp:192-195 names it: cursor 18 over
the map, 22,22-526,420, cursor 2 elsewhere), and the next
star click that is not a black hole sets EVERY relocation to that star, with
HESTR 0xDD's box (mainscr_main.cpp:455-462). ANY negative input ends it
first (:396-399): a right click on the map (HD's `map_cancel`), another F
key — and F4 itself, whose own case then turns it on again (:599 calls
`Check_Function_Keys_` after), so F4 never turns the mode off (seen live,
work order 310, run `wo310_B1_scratch`). Fewer than two relocations: no
mode, the box 0xD1 / 0xD2 (mainscr.cpp:3123-3127). The mode is the
engine's flag, on the wire since open fix 102 (`core/mergemode.py`).

HD EXTENSION `merge_relocation_marker`: HD keeps one pointer drawing on every
screen and has no picture of the original's cursor 18, so while the flag is
on and the pointer is over the map window, a target ring is drawn at the
pointer with the words `labels.merge_relocation` (layout.json) beside it —
where the original shows its relocation cursor and no words. Without the
block (an engine without fix 102) nothing is drawn, as before.
"""
import pygame

from core import lang
from core import mouse as mouse_input
from core import palette

COLOUR = palette.col("galaxy_map", "hover_ring", (170, 200, 255))
#: The ring's radius in native pixels: about the original's cursor (21
#: native px tall, `core/cursor.NATIVE_CURSOR_H`), so it reads as a pointer.
RING_NATIVE = 7
DEFAULT_WORDS = "Relocation: click a star"


def active(screen):
    """True while the engine reports the mode on this screen's own page."""
    st = getattr(screen, "_state", None)
    return (st is not None and getattr(st, "current_screen", -1) == 0 and
            getattr(st, "merging_relocations", None) is True)


def window_rect(view):
    """The map window the original's cursor 18 covers (22,22-526,420), in
    HD pixels of `view` — the whole box while the HD view is decoupled
    (the game is parked at full zoom-out then, and every point of the box
    is map)."""
    from core import mapcoords as mc
    if isinstance(view, mc.SmoothMapView):
        return pygame.Rect(*view.box)
    return pygame.Rect(*view.box).clip(view.native_window())


def render(screen, surface, ctx, pos=None):
    """Draw the marker at `pos` (default: the pointer). Returns the ring's
    rect, or None when nothing was drawn."""
    if ctx is None or not active(screen):
        return None
    x, y = pos if pos is not None else mouse_input.pos()
    if not window_rect(ctx.view).collidepoint(x, y):
        return None
    r = max(4, int(round(RING_NATIVE * ctx.px)))
    w = max(1, int(round(ctx.px)))
    rgb = COLOUR[:3]
    pygame.draw.circle(surface, rgb, (x, y), r, w)
    # The ticks are filled bars, not map lines: the map's one line routine
    # (`maplines.stroke`) is for the map's lines only.
    a, b = r // 2, r + r // 2
    for rect in ((x + a, y - w // 2, b - a, w), (x - b, y - w // 2, b - a, w),
                 (x - w // 2, y + a, w, b - a), (x - w // 2, y - b, w, b - a)):
        # LOOK EXCEPTION marking: the relocation marker's ticks, in the
        # hover ring's colour (HD EXTENSION merge_relocation_marker)
        surface.fill(rgb, pygame.Rect(rect))
    words = lang.tr((screen._data.get("labels") or {}).get(
        "merge_relocation") or DEFAULT_WORDS)
    size = screen.layout.font_size(14)
    img = screen.style.render_text(words, size, rgb)
    surface.blit(img, (x + r + r // 2 + w * 2, y + r // 2))
    return pygame.Rect(x - r, y - r, 2 * r + 1, 2 * r + 1)
