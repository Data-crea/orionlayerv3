"""The band under the words the original prints over a race's picture —
work order 316 C (Data: "the race name and NEUTRAL are hard to read").

HD EXTENSION `name_band`. WHAT THE ORIGINAL DOES: it prints the race's
name at the portrait cell's foot (`Draw_Race_Text_`, racescrn.cpp:140-146:
`Squeeze_Centered_Print_(x, y + 0x4C, name, 0x4C)`), IGNORED above it
(:569-572) and, under the pointer, the relation word over the bar and the
cell's right edge (:563-566) — each in an OUTLINED font,
`Set_Font_Style_Outline` (fonts.cpp:812-815: style 4, the text printed
first in the outline colour at its eight neighbours, :554-584), outline
colour 177 (`Set_Outline_Color(177, 177)`, racescrn.cpp:794). That
outline is what keeps them readable over any portrait and over the bar's
green-to-red. HD draws these words in the HD font WITHOUT the outline
(`hd_font`), and over Data's bright paintings — and over the original's
own Trilarian portrait — the name fell to 2.2 : 1 (work order 316's
measurement, `dev:evidence/work_order_316/races/README.md`). So HD lays a
band under each instead: what the original has no picture of, a band, in
place of what HD does not draw, the outline.

THE BAND IS THE HUD'S GLASS, not a box of its own: the box fill's
`panel` colour (decision 94, `fill.member`, the player's colour) at the
glass's MEASURED opacity, `glass.alpha_top` to `glass.alpha_bottom` down
the band (`measured.glass`, off Data's Select Race mockup — the panels'
own gradient), made denser where the word needs it — never the word
dimmer: the lowest opacity at or above the glass's at which the word's
own ink keeps `glass.floor_contrast` (4.5 : 1) against the band over the
picture under the word, by the glass floor's statistic
(`glass.peak_pixels`: a 3x3 mean, each row's 99th percentile). Its top
fades in over `FADE` of the line's height, so the band reads as shading
on the picture, not a strip pasted on it. It stays translucent with the
glass switched off: the cell is a picture, not a box, and an opaque band
would cut the painting's foot away.

UNDER EVERY CELL, not only under a painting: the original's outline is
on every portrait, and the original's own Trilarian portrait puts the
name at 2.2 : 1 as Data's brightest painting does (316's table). One rule
for every race; a cell where the picture is dark gets the glass's own
opacity, which is all the band ever is there.
"""
import numpy as np
import pygame

from core.hud import fill as boxfill
from core.hud import glass
from core.hud import style as hudstyle
from screens.leaders import ldrdraw as nd

#: The fade-in at the band's top, as a share of the word's line height:
#: ours (decision 53), chosen on 316's renders — a hard top edge read as a
#: black strip laid on the painting.
FADE = 0.5
#: Added to the floor contrast the band is solved for: the box fill's
#: margin (`[core.box_fill]`, "plus 0.1"), which here absorbs the band's
#: 8-bit alpha and the measurement's own box mean at the word's edge.
MARGIN = 0.1
#: Room left and right of a word whose band is as wide as the word (the
#: relation word), as a share of the line height; the fade runs there.
SIDE = 0.4


def _ink_limit(ink):
    """The brightest the ground under the word may read: the word's ink
    at the floor contrast (`glass._word_floor`'s arithmetic, for one
    ink)."""
    lt = float(glass.lum(np.array(ink[:3], float)))
    floor = float(hudstyle.get().get("glass.floor_contrast")) + MARGIN
    return (lt + 0.05) / floor - 0.05


def _profile(h, w, fade_top, side):
    """Per pixel the band's share of the glass's opacity, (h, w): 1 inside,
    rising from 0 over `fade_top` rows at the top and `side` columns at
    each end."""
    y = np.ones(h, np.float32)
    if fade_top > 0:
        k = min(h, fade_top)
        y[:k] = (np.arange(k, dtype=np.float32) + 1) / (k + 1)
    x = np.ones(w, np.float32)
    if side > 0:
        k = min(w // 2, side)
        ramp = (np.arange(k, dtype=np.float32) + 1) / (k + 1)
        x[:k] = ramp
        x[w - k:] = ramp[::-1]
    return y[:, None] * x[None, :]


def opacity(ground, word_rows, ink, word_cols=slice(None)):
    """(alpha_top, alpha_bottom) for a band over `ground` (h, w, 3 float):
    the glass's measured pair, raised by one factor until the ground under
    the word — rows `word_rows`, columns `word_cols` — keeps the floor for
    `ink`; 1.0 when nothing less does."""
    st = hudstyle.get()
    a0 = float(st.get("glass.alpha_top"))
    a1 = float(st.get("glass.alpha_bottom"))
    col = np.array(boxfill.member("panel"), np.float32)
    limit = _ink_limit(ink)
    h = ground.shape[0]
    under = ground[word_rows, word_cols]
    rows = np.linspace(0.0, 1.0, max(1, h), dtype=np.float32)[word_rows]

    def ok(u):
        # u: 0 = the glass's own opacity, 1 = opaque
        a = (a0 + (a1 - a0) * rows) * (1 - u) + u
        comp = under * (1 - a[:, None, None]) + col * a[:, None, None]
        return float(glass.lum(glass.peak_pixels(comp)).max()) <= limit

    if under.size == 0 or ok(0.0):
        return a0, a1
    lo, hi = 0.0, 1.0
    for _ in range(12):
        mid = (lo + hi) / 2
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return a0 * (1 - hi) + hi, a1 * (1 - hi) + hi


def draw(surface, rect, word_rect, ink, fade_top=0, side=0):
    """The band over `rect` (window px) for a word drawn at `word_rect` in
    `ink`. Returns (alpha_top, alpha_bottom) used, or None where nothing
    was drawn."""
    rect = pygame.Rect(rect).clip(surface.get_rect())
    if rect.w < 1 or rect.h < 1:
        return None
    sub = surface.subsurface(rect)
    ground = pygame.surfarray.array3d(sub).transpose(1, 0, 2).astype(
        np.float32)
    wr = pygame.Rect(word_rect).clip(rect)
    rows = slice(max(0, wr.y - rect.y), max(0, wr.bottom - rect.y))
    cols = slice(max(0, wr.x - rect.x), max(0, wr.right - rect.x))
    a0, a1 = opacity(ground, rows, ink, cols)
    h, w = rect.h, rect.w
    alpha = (a0 + (a1 - a0) * np.linspace(0.0, 1.0, h, dtype=np.float32)
             )[:, None] * _profile(h, w, fade_top, side)
    band = pygame.Surface((w, h), pygame.SRCALPHA)
    band.fill(tuple(int(v) for v in boxfill.member("panel")[:3]) + (0,))
    pa = pygame.surfarray.pixels_alpha(band)
    pa[...] = np.clip(np.round(alpha * 255.0), 0, 255).astype(
        np.uint8).T
    del pa
    surface.blit(band, rect.topleft)
    return a0, a1


def line_rect(style, text, x, y, max_w, size, align="left"):
    """Where `nd.blit_text` will draw `text` — the same fit, render and
    anchor (ldrdraw.py:157-169), so the band is laid before the word; a
    smoke check holds the two equal. None for no text."""
    if not text:
        return None
    size = nd.fit(style, text, max(1, max_w), size)
    w, h = style.render_text(text, size, (255, 255, 255)).get_size()
    if align == "right":
        x -= w
    elif align == "center":
        x -= w // 2
    return pygame.Rect(x, y, w, h)


def in_cell(surface, layout, style, cell, text, x, y, max_w, size, ink,
            align="center", reach=None):
    """The name over its portrait cell: the band across the cell inside
    its banner frame, from the fade above the word — or above `reach`, the
    line of IGNORED when that stands over the same cell (:569-572), so
    one band carries both — to the cell's foot, then the word."""
    r = line_rect(style, text, x, y, max_w, size, align)
    if r is None:
        return None
    frame = max(1, int(nd.native_scale(layout)))
    inner = pygame.Rect(cell).inflate(-2 * frame, -2 * frame)
    words = r.union(reach) if reach is not None else r
    fade = max(1, round(r.h * FADE))
    top = max(inner.y, words.y - fade)
    if inner.bottom > top:
        draw(surface, (inner.x, top, inner.w, inner.bottom - top), words,
             ink, fade_top=words.y - top)
    return nd.blit_text(surface, style, text, x, y, max_w, size, ink, align)


def free(surface, style, text, x, y, max_w, size, ink, align="center"):
    """A word over whatever lies there (the relation word over the bar):
    the band as wide as the word and `SIDE` more at each end, fading in
    at its top and its ends, then the word."""
    r = line_rect(style, text, x, y, max_w, size, align)
    if r is None:
        return None
    pad = max(1, round(r.h * SIDE))
    fade = max(1, round(r.h * FADE))
    band = pygame.Rect(r.x - pad, r.y - fade, r.w + 2 * pad, r.h + fade)
    draw(surface, band, r, ink, fade_top=fade, side=pad)
    return nd.blit_text(surface, style, text, x, y, max_w, size, ink, align)
