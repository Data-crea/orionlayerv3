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
(`glass.peak_pixels`: a 3x3 mean, each row's 99th percentile, with one
pixel of the picture round the word, `word_peak`) on the band as it is
DRAWN (8-bit alpha, pygame's blend). Solved once per ground and kept
(`_solved`), not every frame. Its top fades in over `FADE` of the
line's height, so the band reads as shading on the picture, not a strip
pasted on it. It stays translucent with the glass switched off: the cell
is a picture, not a box, and an opaque band would cut the painting's foot
away.

UNDER EVERY CELL, not only under a painting: the original's outline is
on every portrait, and the original's own Trilarian portrait puts the
name at 2.2 : 1 as Data's brightest painting does (316's table). One rule
for every race; a cell where the picture is dark gets the glass's own
opacity, which is all the band ever is there.
"""
import zlib

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
#: margin (`[core.box_fill]`, "plus 0.1"): the float search's head start,
#: so the check on what is drawn (`_solve`) rarely has to step.
MARGIN = 0.1
#: Room left and right of a word whose band is as wide as the word (the
#: relation word), as a share of the line height; the fade runs there.
SIDE = 0.4


def _ink_limit(ink, margin=MARGIN):
    """The brightest the ground under the word may read: the word's ink
    at the floor contrast (`glass._word_floor`'s arithmetic, for one
    ink), plus `margin`."""
    lt = float(glass.lum(np.array(ink[:3], float)))
    floor = float(hudstyle.get().get("glass.floor_contrast")) + margin
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


def _alpha(h, w, a0, a1, fade_top, side):
    """The band's opacity per pixel, (h, w): `a0` to `a1` down it, times
    the fade (`_profile`)."""
    return (a0 + (a1 - a0) * np.linspace(0.0, 1.0, h, dtype=np.float32)
            )[:, None] * _profile(h, w, fade_top, side)


def word_peak(picture, word):
    """The brightest the ground under `word` (a Rect inside `picture`, an
    (h, w, 3) array) reads by the glass floor's statistic
    (`glass.peak_pixels`: the 3x3 mean, each row's 99th percentile) — the
    3x3 mean taken with ONE PIXEL OF CONTEXT round the word, as it is on
    the whole picture, the picture's own edge repeated only where the word
    meets it. The solver, the evidence tool and the smoke check all
    measure by this (review of work order 316: a solver that read its own
    slice with repeated edges stopped at 4.49 : 1 measured on the
    picture)."""
    h, w = picture.shape[:2]
    y0, y1 = max(0, word.top), min(h, word.bottom)
    x0, x1 = max(0, word.left), min(w, word.right)
    if y1 <= y0 or x1 <= x0:
        return 0.0
    cy0, cy1, cx0, cx1 = max(0, y0 - 1), min(h, y1 + 1), max(0, x0 - 1), \
        min(w, x1 + 1)
    blk = np.asarray(picture[cy0:cy1, cx0:cx1], np.float32)
    # glass._box3's mean (edges repeated), on the word and its ring
    p = np.pad(blk, [(1, 1), (1, 1), (0, 0)], mode="edge")
    bh, bw = blk.shape[:2]
    soft = sum(p[dy:dy + bh, dx:dx + bw] for dy in range(3)
               for dx in range(3)) / 9.0
    soft = soft[y0 - cy0:y1 - cy0, x0 - cx0:x1 - cx0]
    return float(glass.lum(glass.peak_pixels(soft, soft=True)).max())


def _search(ground, band, word, ink, fade_top, side, col, a0, a1):
    """The least `u` (0 = the glass's own opacity, 1 = opaque) whose band
    keeps the word's ground under `_ink_limit` by `word_peak`, in float;
    `band` and `word` are Rects in `ground`. 1.0 when nothing less does."""
    limit = _ink_limit(ink)
    # only the word and its ring are measured: composite that block
    h, w = ground.shape[:2]
    blk = pygame.Rect(word).inflate(2, 2).clip(pygame.Rect(0, 0, w, h))
    if blk.w < 1 or blk.h < 1:
        return 0.0
    under = ground[blk.top:blk.bottom, blk.left:blk.right]
    grad = np.zeros((h, w), np.float32)
    prof = np.zeros((h, w), np.float32)
    grad[band.top:band.bottom, band.left:band.right] = _alpha(
        band.h, band.w, a0, a1, 0, 0)
    prof[band.top:band.bottom, band.left:band.right] = _profile(
        band.h, band.w, fade_top, side)
    grad = grad[blk.top:blk.bottom, blk.left:blk.right, None]
    prof = prof[blk.top:blk.bottom, blk.left:blk.right, None]
    inner = pygame.Rect(word).move(-blk.x, -blk.y)

    def ok(u):
        a = (grad * (1 - u) + u) * prof
        return word_peak(under * (1 - a) + col * a, inner) <= limit

    if ok(0.0):
        return 0.0
    lo, hi = 0.0, 1.0
    for _ in range(12):
        mid = (lo + hi) / 2
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return hi


def _raised(a0, a1, u):
    return a0 * (1 - u) + u, a1 * (1 - u) + u


def opacity(ground, word_rows, ink, word_cols=slice(None)):
    """(alpha_top, alpha_bottom) for a band over all of `ground` (h, w, 3
    float): the glass's measured pair, raised by one factor until the
    ground under the word — rows `word_rows`, columns `word_cols` — keeps
    the floor for `ink`; 1.0 when nothing less does. In float, before the
    band is drawn; `draw` then holds it on what is drawn."""
    st = hudstyle.get()
    a0 = float(st.get("glass.alpha_top"))
    a1 = float(st.get("glass.alpha_bottom"))
    h, w = ground.shape[:2]
    ys, xs = range(h)[word_rows], range(w)[word_cols]
    if not len(ys) or not len(xs):
        return a0, a1
    word = pygame.Rect(xs[0], ys[0], len(xs), len(ys))
    u = _search(np.asarray(ground, np.float32), pygame.Rect(0, 0, w, h),
                word, ink, 0, 0,
                np.array(boxfill.member("panel"), np.float32), a0, a1)
    return (a0, a1) if u == 0.0 else _raised(a0, a1, u)


#: The solved bands: key -> (alpha_top, alpha_bottom, the band Surface).
#: WHAT INVALIDATES IT (P809: a cached value has a lifetime): nothing has
#: to — the key IS everything the band depends on, read on every call: the
#: pixels under the band and round the word (their bytes' hashes — a new
#: painting, a preset, a resize, the eliminated mark, the bar's colours all
#: change them), the band's and the word's size and place in that area,
#: the ink, the fade, the panel colour (`fill.member`, the player's colour
#: and the glass switch) and the style's three numbers. A change of any of
#: them is a new key; the old entry is never served for it.
_solved = {}
CACHE = 64
#: How far one step raises the band when what is DRAWN (8-bit alpha,
#: pygame's blend) still misses the floor the float search met.
STEP = 1 / 64


def _key(raw, area, rect, word, ink, fade_top, side, col, st):
    return (len(raw), hash(raw), zlib.crc32(raw), area.size,
            tuple(rect.move(-area.x, -area.y)),
            tuple(word.move(-area.x, -area.y)), tuple(ink[:3]), fade_top,
            side, col, st)


def _band(w, h, a0, a1, fade_top, side, col):
    band = pygame.Surface((w, h), pygame.SRCALPHA)
    band.fill(col + (0,))
    pa = pygame.surfarray.pixels_alpha(band)
    pa[...] = np.clip(np.round(_alpha(h, w, a0, a1, fade_top, side) * 255.0),
                      0, 255).astype(np.uint8).T
    del pa
    return band


def _solve(raw, base, area, rect, word, ink, fade_top, side, col, a0, a1):
    """(alpha_top, alpha_bottom, band) for the band at `rect` over the
    `area` whose RGB bytes are `raw` and whose copy is `base`: the float search, then held on what
    is drawn — the band blitted on a copy, the word's ground measured by
    `word_peak`, raised by `STEP` until it keeps the floor itself (no
    margin) or is opaque."""
    ground = np.frombuffer(raw, np.uint8).reshape(area.h, area.w, 3)
    band_r, word_r = rect.move(-area.x, -area.y), word.move(-area.x, -area.y)
    u = _search(ground.astype(np.float32), band_r, word_r, ink, fade_top,
                side, np.array(col, np.float32), a0, a1)
    limit = _ink_limit(ink, 0.0)
    while True:
        t, b = _raised(a0, a1, u) if u > 0 else (a0, a1)
        band = _band(rect.w, rect.h, t, b, fade_top, side, col)
        if u >= 1.0:
            return t, b, band
        trial = base.copy()
        trial.blit(band, band_r.topleft)
        drawn = pygame.surfarray.array3d(trial).transpose(1, 0, 2)
        if word_peak(drawn, word_r) <= limit:
            return t, b, band
        u = min(1.0, u + STEP)


def draw(surface, rect, word_rect, ink, fade_top=0, side=0):
    """The band over `rect` (window px) for a word drawn at `word_rect` in
    `ink`. Returns (alpha_top, alpha_bottom) used, or None where nothing
    was drawn. Solved once per ground (`_solved`), then blitted."""
    bounds = surface.get_rect()
    rect = pygame.Rect(rect).clip(bounds)
    if rect.w < 1 or rect.h < 1:
        return None
    word = pygame.Rect(word_rect).clip(bounds)
    area = rect.union(word.inflate(2, 2)).clip(bounds)
    raw = pygame.image.tobytes(surface.subsurface(area), "RGB")
    st = hudstyle.get()
    a0 = float(st.get("glass.alpha_top"))
    a1 = float(st.get("glass.alpha_bottom"))
    col = tuple(int(v) for v in boxfill.member("panel")[:3])
    key = _key(raw, area, rect, word, ink, fade_top, side, col,
               (a0, a1, float(st.get("glass.floor_contrast"))))
    hit = _solved.get(key)
    if hit is None:
        if len(_solved) >= CACHE:
            _solved.clear()
        hit = _solved[key] = _solve(raw, surface.subsurface(area).copy(),
                                    area, rect, word, ink, fade_top, side,
                                    col, a0, a1)
    surface.blit(hit[2], rect.topleft)
    return hit[0], hit[1]


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


def inner(layout, cell):
    """The portrait cell inside its banner frame — where the band lies,
    and so the width the words over the cell are fitted to."""
    frame = max(1, int(nd.native_scale(layout)))
    return pygame.Rect(cell).inflate(-2 * frame, -2 * frame)


def in_cell(surface, layout, style, cell, text, x, y, max_w, size, ink,
            align="center", reach=None):
    """The name over its portrait cell: the band across the cell inside
    its banner frame, from the fade above the word — or above `reach`, the
    line of IGNORED when that stands over the same cell (:569-572), so
    one band carries both — to the cell's foot, then the word.

    The name is fitted to the band's width, not to `max_w` where that is
    wider: the original squeezes it to 0x4C (:140-146), its portrait's
    full 76 px with the frame's two pixels each side under the name's
    ends, readable there by the outline; HD has the band in the outline's
    place and the band stops at the frame (covering the frame would hide
    the player's colour), so a word wider than the band would stand off
    it (review of work order 316). The centre, the line and the font are
    the transcription's; only a name wider than the cell inside its frame
    is squeezed by those few pixels more."""
    inside = inner(layout, cell)
    max_w = min(max_w, inside.w)
    r = line_rect(style, text, x, y, max_w, size, align)
    if r is None:
        return None
    words = r.union(reach) if reach is not None else r
    fade = max(1, round(r.h * FADE))
    top = max(inside.y, words.y - fade)
    if inside.bottom > top:
        draw(surface, (inside.x, top, inside.w, inside.bottom - top), words,
             ink, fade_top=words.y - top)
    return nd.blit_text(surface, style, text, x, y, max_w, size, ink, align)


def free(surface, style, text, x, y, max_w, size, ink, align="center"):
    """A word over whatever lies there (the relation word over the bar):
    the band as wide as the word and `SIDE` more at each end, fading in
    at its top and its ends, one row below it, then the word."""
    r = line_rect(style, text, x, y, max_w, size, align)
    if r is None:
        return None
    pad = max(1, round(r.h * SIDE))
    fade = max(1, round(r.h * FADE))
    # one row below the word: the statistic's pixel of context
    # (`word_peak`) — a band ending at the word's last row leaves the 3x3
    # mean of that row a third unbanded, which no opacity can bring under
    # the floor (the review of 316 measured NEUTRAL at 2.5 : 1 so)
    band = pygame.Rect(r.x - pad, r.y - fade, r.w + 2 * pad,
                       r.h + fade + 1)
    draw(surface, band, r, ink, fade_top=fade, side=pad)
    return nd.blit_text(surface, style, text, x, y, max_w, size, ink, align)
