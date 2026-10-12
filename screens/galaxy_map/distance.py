"""The distance between stars — the original's F9 on the galaxy map, drawn by
HD (work order 231 D, Data's decision 4).

F9 sends the game into `MAINSCR2::Distance_Between_Stars_Screen_` (screen
28, mainscr.cpp:3076-3080; mainscr2.cpp:193-262), a loop of its own over the
map. HD answers screen 28 with the galaxy map (`EXTRA_SCREEN_IDS`) in this
mode. TRANSCRIPTION of what the loop shows and takes:

  * the map as it stands — the loop darkens the four strips round the map
    window once (`MISC::_Darken_Fill_`, mainscr2.cpp:221-224) and then
    redraws the whole main screen every frame (`Draw_Mini_Main_Screen_`,
    `Draw_Main_Main_Screen_`, :48-49), so nothing stays darkened: measured
    live, work order 231 — the sidebar's pixels in screen 28's framebuffer
    are those of screen 0's; HD darkens nothing either;
  * a left click on a star makes it the FROM star (`_screen_mouse_list_
    type = i`, :236-240) — HD sends the click at the star's native point,
    as the map's own star click, and keeps the star (HD STATE `from_star`:
    the engine's choice is not on the wire); a left click elsewhere on the
    map does nothing (the starmap field, :243-247), anywhere else it ends
    the view (the full-screen field) — HD sends that field;
  * with a FROM star, the star under the pointer (`_scanned_field`) gets
    the green directional line from it, animated (`Draw_Directional_Multi_
    Colored_Line_`, :103-107), and beside it H 0xEB "%d parsecs" of
    `GEO::Parsecs_Between_Stars_` — ceil(sqrt((dx² + dy²) / 900)),
    geo.cpp:73-100 — or H 0xEA when a black hole blocks the way (the FROM
    star's `black_hole_blocks` bit for it, :80-92), at the star plus 10
    native px or right-aligned at native 522 when it would run past it
    (:94-99);
  * ESC (the hot key, :204), F9 again (input -1009) and a right click
    anywhere (the negative of a field, :240, :243-247) end it — ESC and F9
    go by `core/keyfwd.py`'s rule, a right click is the full-screen field's
    cancel.

HD EXTENSION `distance_hover`: the original's TO star is the one under the
ENGINE's pointer; HD's is the one under HD's (as the map's own hover line,
`hover_line`) — the engine's pointer never moves in HD.
DEVIATION `distance_highlight`: the original tints the FROM star's name in a
pulsing highlight (`Highlight_Star_`, mainscr.cpp:1607-1617); HD rings the
star as its own hover does, in the highlight colour.
DEVIATION `distance_text_colour`: the original prints in fonts outlined in
palette 0x70-0x72 (0x4C-0x50 when blocked), not measured; HD prints the
words in the brightest colour of the line's own green (the blocked line's
red).
"""
import logging
import math

import pygame

from core import hestrings
from core import mapcoords as mc
from screens.galaxy_map import maplines

log = logging.getLogger("galaxy_map.distance")

SCREEN_ID = 28                  # SCREEN_DISTANCE_BETWEEN_STARS
H_PARSECS, H_BLOCKED = 0xEB, 0xEA
#: The engine's own rectangles (mainscr2.cpp:205-208).
FULL_SCREEN = (0, 0, 639, 479)
STARMAP = (22, 22, 506, 400)
TYPE_HIDDEN = 7
#: The text stands 10 native px right of the TO star, or ends at 522.
TEXT_DX, TEXT_RIGHT = 10, 522
BLACK_HOLE_BLOCKS_AT = 31       # s_star_data: name 15, x, y, 4 bytes, 8


def active(state):
    return getattr(state, "current_screen", None) == SCREEN_ID


def parsecs(a, b):
    """`GEO::Parsecs_Between_Points_` (geo.cpp:88-100): the ceiling of the
    root of (dx² + dy²) / 900, in integers as the engine counts."""
    d2 = (a.x - b.x) ** 2 + (a.y - b.y) ** 2
    p = math.isqrt(d2 // 900)
    while p * p * 900 < d2:
        p += 1
    return p


def blocked(star, other_index):
    """The FROM star's `black_hole_blocks` bit for `other_index`
    (`struct_::Test_Bit_Field_`, struct.cpp:20-25)."""
    raw = getattr(star, "raw", b"") or b""
    at = BLACK_HOLE_BLOCKS_AT + (other_index >> 3)
    return at < len(raw) and bool((raw[at] >> (other_index & 7)) & 1)


def full_screen_field(fields):
    """The loop's full-screen field (the last hidden field of 0..639 x
    0..479), or None — a click on it, or its cancel, ends the view."""
    return next((f for f in reversed(fields or [])
                 if f.field_type == TYPE_HIDDEN and
                 (f.x, f.y, f.x_end, f.y_end) == FULL_SCREEN), None)


def owns(fields):
    """The loop's list: its full-screen field and its starmap field."""
    rects = {(f.x, f.y, f.x_end, f.y_end) for f in fields or []
             if f.field_type == TYPE_HIDDEN}
    return FULL_SCREEN in rects and STARMAP in rects


class Mode:
    """HD's side of screen 28: the FROM star it sent (HD STATE)."""

    def __init__(self, screen):
        self.screen = screen
        self.from_star = None
        self._was = False

    def update(self, state):
        now = active(state)
        if now and not self._was:
            self.from_star = None       # the loop starts with -1 (:212)
            log.info("distance between stars: the view is up (screen 28)")
        self._was = now

    @property
    def on(self):
        return self._was

    # ── input ──────────────────────────────────────────────
    def click(self, x, y):
        screen = self.screen
        st = screen._state
        app = screen.app
        view = screen._map_view()
        if view is None:
            return True
        if pygame.Rect(*view.box).collidepoint(x, y):
            star = screen._star_at(x, y)
            if star is None:
                return True             # the starmap field: nothing
            index = next((i for i, s in enumerate(screen._stars)
                          if (s.x, s.y) == (star.x, star.y)), None)
            nx, ny = mc.galaxy_to_native(star.x, star.y, st)
            log.info("distance: from %s (star %s), click at native %d,%d",
                     star.name, index, nx, ny)
            if app.connected:
                app.client.inject_click(nx, ny)
            self.from_star = index
            return True
        f = full_screen_field(getattr(st, "fields", None))
        if f is not None and app.connected:
            log.info("distance: a click outside the map ends the view")
            app.client.activate_field(f.index)
        return True

    def right(self, down):
        if not down:
            return True
        st = self.screen._state
        f = full_screen_field(getattr(st, "fields", None))
        if f is not None and self.screen.app.connected:
            log.info("distance: a right click ends the view")
            self.screen.app.client.cancel_field(f.index)
        return True

    # ── drawing ────────────────────────────────────────────
    def render(self, surface, ctx):
        screen = self.screen
        box = pygame.Rect(*ctx.view.box)
        stars = screen._stars
        if self.from_star is None or not 0 <= self.from_star < len(stars):
            return None
        a = stars[self.from_star]
        clip = surface.get_clip()
        surface.set_clip(box)
        try:
            ax, ay = ctx.view.to_screen(a.x, a.y)
            from screens.galaxy_map.screen import HOVER_COLOR
            r = max(6, int(10 * screen.layout.scale))
            # LOOK EXCEPTION marking: the FROM star's ring (DEVIATION
            # `distance_highlight`)
            pygame.draw.circle(surface, HOVER_COLOR[:3], (int(ax), int(ay)),
                               r, 2)
            hover = getattr(screen, "_hover_star", None)
            to = None if hover is None else next(
                (i for i, s in enumerate(stars)
                 if (s.x, s.y) == (hover.x, hover.y)), None)
            if to is None or to == self.from_star:
                return None
            b = stars[to]
            return self._line(surface, ctx, a, b, to)
        finally:
            surface.set_clip(clip)

    def _line(self, surface, ctx, a, b, to):
        screen = self.screen
        st = screen._state
        stop = blocked(a, to)
        n1 = mc.galaxy_to_native(a.x, a.y, st)
        n2 = mc.galaxy_to_native(b.x, b.y, st)
        table, offset = maplines.directional(
            n1[0], n1[1], n2[0], n2[1], maplines.GREEN,
            maplines.phase_at(pygame.time.get_ticks()))
        p = ctx.view.to_screen(a.x, a.y)
        q = ctx.view.to_screen(b.x, b.y)
        seg = maplines.clip(p, q, ctx.view.box)
        if seg is not None:
            for colour, u, v in maplines.wave_pieces(seg[0], seg[1], table,
                                                     offset, ctx.px):
                maplines.stroke(surface, colour, u, v)
        text = hestrings.for_app(screen.app)
        text = text if text.state == "ok" else None
        if stop:
            words = text.message(H_BLOCKED) if text else "blocked"
            colour = max(maplines.RED, key=sum)
        else:
            fmt = text.message(H_PARSECS) if text else "%d"
            words = hestrings.printf(fmt, parsecs(a, b))
            colour = max(maplines.GREEN, key=sum)
        size = screen.layout.font_size(16)
        img = screen.style.render_text(words, size, tuple(colour)[:3])
        # native px -> window px: the map window is native 22..527
        k = ctx.view.box[2] / float(mc.MAP_RIGHT - mc.MAP_LEFT)
        x = q[0] + TEXT_DX * k
        right = ctx.view.box[0] + (TEXT_RIGHT - mc.MAP_LEFT) * k
        if x + img.get_width() > right:
            x = right - img.get_width()
        surface.blit(img, (int(x), int(q[1] - img.get_height() / 2)))
        return {"from": self.from_star, "to": to, "words": words,
                "blocked": stop}
