"""The Leaders screen's picture places — work order 237 (Data, 11 October 2026).

HD EXTENSION `box_pictures`: the original draws its rows, galaxy box and
screen into OFFICER.LBX 0 (officer.cpp:648) and has no picture per box; HD
gives eight places a painted picture from the player's mod folder:

    screen        the screen's own background, the whole window
    slot_1..4     a row's box while a leader stands in it (row 1 to 4, the
                  same on both tabs — the chat's setting, parked)
    slot_empty    a row's box with no leader, under HD's caption
    minimap       the galaxy box, under the stars and fleets
    view          the view box in the colony view: a star in space, the
                  system's orbits and planets drawn over it (`ldrsystem`,
                  Data, 16 Oct 2026); the ship view keeps the glass panel

WHERE THEY LIVE (Data's decision): `files/screens/leaders/assets/pictures/
<name>.png` in the mod folder, `FOLDER` + `NAMES`; none is in either tree.
`Resources.resolve` asks the folder first (decision 72), so a modder's file
of the same name replaces Data's. The names are `usermod.SLOTS` entries, a
file under another name says so once at start.

WHEN. Only while the mod folder is on (`usermod.active()`), each place on its
own: a missing or unreadable picture (one log line, once) draws that box as
before this order — the HUD panel — and the screen the background chain.

HOW. Cover, never stretch: scaled smoothly to fill the box at its own
proportion, the overflow cut evenly (`cover`); the empty slot's overflow is
cut on the right (`ANCHOR`), because a centred cut of no_leader.png (6.3 : 1
against the box's 5.06 : 1) takes away the emblem at its left. Clipped to the
panel's own outline (`blocks.panel_polygon`), the panel's edge drawn over it
with the player's frame colour (`blocks.panel(filled=False)`): the picture
REPLACES the fill — no glass, no fill colour on it.

THE MARKS STAY READABLE in the galaxy box the same way, over the whole
box: no ground brighter than the plain box (`ldrdraw.map_zones`).

THE WORDS STAY READABLE (decision 94's floor, 4.5 : 1): under each place a
word is drawn on (`dim`'s zones) every pixel brighter than the floor allows
for the word's ink is darkened to it in linear light, hue kept; a ramp of
`FEATHER` of the box's height outside the zone; nothing outside. Where an ink
stands under 4.5 : 1 on the plain box already (the red status line: 2.8 : 1
on the starting fill) its floor is that box's contrast — the picture never
makes a word harder to read than the box it replaces.

DEVIATION `own_background`: one universal background stands behind every
screen (decision 71's slot, `core.backgrounds`); the Leaders screen wears
its own picture first when the mod folder holds one (the chat's setting,
parked: whether other screens follow).
"""
import logging
import os

import numpy as np
import pygame

from core import usermod
from core.hud import blocks as hud
from core.hud import tint

log = logging.getLogger("leaders")

FOLDER = "screens/leaders/assets/pictures"
#: place -> the file's name in `FOLDER`.
NAMES = {"screen": "screen_background.png",
         "slot_1": "slot_1_background.png",
         "slot_2": "slot_2_background.png",
         "slot_3": "slot_3_background.png",
         "slot_4": "slot_4_background.png",
         "slot_empty": "slot_empty_background.png",
         "minimap": "minimap_background.png",
         "view": "view_background.png"}
#: The box each place fills at 3840x2160, measured through the screen's own
#: geometry (`ldrdraw.row_box`, `ldrgeom.GALAXY_BOX`; work order 237, the
#: wider boxes of 238's even margins): the size the mod kit recommends. 1920x1080 and 3440x1440 draw it smaller.
RECOMMENDED = {"screen": (3840, 2160), "slot": (2158, 413),
               "minimap": (1444, 700), "view": (1498, 784)}
#: Where a cover cut sits across, 0 left .. 1 right; 0.5 unless named.
ANCHOR = {"slot_empty": 0.0}
#: The floor every word keeps on its ground (decision 94).
FLOOR = 4.5
#: The dimmed zone's soft edge, a fraction of the box's height.
FEATHER = 0.08

_sources = {}
_drawn = {}
_DRAWN_MAX = 24


def slot_place(slot, has_leader):
    return f"slot_{int(slot) + 1}" if has_leader else "slot_empty"


def path(place):
    """The picture file for `place`, or None (folder off, or no file)."""
    if not usermod.active():
        return None
    from core import resources
    return resources.res.resolve(f"{FOLDER}/{NAMES[place]}")


def source(place):
    """The picture for `place` as loaded, or None."""
    p = path(place)
    if p is None:
        return None
    try:
        stamp = os.stat(p).st_mtime_ns
    except OSError:
        return None
    hit = _sources.get(p)
    if hit is None or hit[0] != stamp:
        try:
            img = pygame.image.load(p)
            img = img.convert() if pygame.display.get_surface() else img
        except (pygame.error, OSError) as exc:
            if hit is None or hit[1] is not None:
                log.warning("leaders: picture %s unreadable (%s) — the box "
                            "is drawn as without it", p, exc)
            img = None
        hit = (stamp, img)
        _sources[p] = hit
    return hit[1]


def cover_box(src_size, size, anchor=0.5):
    """The part (x, y, w, h) of a `src_size` picture a `size` box shows
    at cover scale — the one rule `cover` draws and the report measures."""
    iw, ih = src_size
    w, h = max(1, int(size[0])), max(1, int(size[1]))
    k = max(w / iw, h / ih)
    cw, ch = w / k, h / k
    x = (iw - cw) * anchor
    y = (ih - ch) / 2
    return x, y, cw, ch


def cover(img, size, anchor=0.5):
    """`img` filling `size` at its own proportion, smoothly scaled, the
    overflow cut at `anchor` across and evenly up and down. Exactly `size`."""
    w, h = max(1, int(size[0])), max(1, int(size[1]))
    iw, ih = img.get_size()
    k = max(w / iw, h / ih)
    sw, sh = max(w, round(iw * k)), max(h, round(ih * k))
    big = pygame.transform.smoothscale(img, (sw, sh))
    x = int(round((sw - w) * anchor))
    return big.subsurface((x, (sh - h) // 2, w, h)).copy()


# ── the words' floor ──────────────────────────────────────

def contrast(a, b):
    la, lb = float(tint.luminance(a)), float(tint.luminance(b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def ceiling(ink, box_fill):
    """The brightest ground (relative luminance) `ink` keeps its floor on:
    4.5 : 1, or the plain box's contrast where that is less."""
    want = min(FLOOR, contrast(ink, box_fill))
    return max(0.0, (float(tint.luminance(ink)) + 0.05) / want - 0.05)


def ground(box_fill):
    """The ceiling of a place whose marks are not words (the galaxy box):
    the plain box's own luminance."""
    return float(tint.luminance(box_fill))


def _lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92,
                    1.055 * c ** (1 / 2.4) - 0.055) * 255.0


def dim(img, zones, feather):
    """`img` with every pixel in a zone no brighter than the zone's
    ceiling. `zones` [(Rect in the picture's px, ceiling)]."""
    if not zones:
        return img
    rgb = pygame.surfarray.array3d(img).astype(np.float64)   # (w, h, 3)
    lin = _lin(rgb)
    lum = (lin * np.array([0.2126, 0.7152, 0.0722])).sum(-1)
    factor = np.ones(lum.shape)
    w, h = lum.shape
    f = max(1.0, float(feather))
    for rect, top in zones:
        r = pygame.Rect(rect)
        x0, x1 = max(0, int(r.x - f)), min(w, int(r.right + f) + 1)
        y0, y1 = max(0, int(r.y - f)), min(h, int(r.bottom + f) + 1)
        if x0 >= x1 or y0 >= y1:
            continue
        xs = np.arange(x0, x1)[:, None]
        ys = np.arange(y0, y1)[None, :]
        dx = np.maximum(np.maximum(r.x - xs, xs - (r.right - 1)), 0)
        dy = np.maximum(np.maximum(r.y - ys, ys - (r.bottom - 1)), 0)
        weight = np.clip(1.0 - np.maximum(dx, dy) / f, 0.0, 1.0)
        part = lum[x0:x1, y0:y1]
        s = np.minimum(1.0, top / np.maximum(part, 1e-9))
        factor[x0:x1, y0:y1] = np.minimum(factor[x0:x1, y0:y1],
                                          1.0 - weight * (1.0 - s))
    out = _srgb(lin * factor[..., None])
    surf = img.copy()
    pygame.surfarray.blit_array(surf, np.round(out).astype(np.uint8))
    return surf


# ── the view picture's star ───────────────────────────────

#: A pixel of the painted star: bright and warm (red and green high, blue
#: low — the nebula round it is blue). Measured on Data's
#: view_background.png of 16 Oct 2026: its disc and corona, nothing else.
SUN_RGB_MIN = (200, 110)
SUN_BLUE_MAX = 120
#: Fewer such pixels than this share of the box is no star (a picture
#: without one): the orbits then stand at the original's centre.
SUN_MIN_SHARE = 0.002
_suns = {}


def sun_centre(place, size):
    """(x, y) of the painted star in the picture as `cover` lays it into a
    box of `size` — the centre of its warm pixels' rows and columns that
    are at least a quarter full (the corona's thin rays left out) — or
    None. Measured once per file and size."""
    img = source(place)
    if img is None:
        return None
    key = (path(place), _sources[path(place)][0], tuple(size))
    if key not in _suns:
        pic = cover(img, size, ANCHOR.get(place, 0.5))
        a = pygame.surfarray.array3d(pic).astype(np.int32)    # (w, h, 3)
        warm = (a[..., 0] > SUN_RGB_MIN[0]) & (a[..., 1] > SUN_RGB_MIN[1]) \
            & (a[..., 2] < SUN_BLUE_MAX)
        found = None
        if warm.sum() >= SUN_MIN_SHARE * warm.size:
            cols, rows = warm.sum(1), warm.sum(0)
            xs = np.nonzero(cols > cols.max() * 0.25)[0]
            ys = np.nonzero(rows > rows.max() * 0.25)[0]
            found = ((xs.min() + xs.max()) / 2.0, (ys.min() + ys.max()) / 2.0)
        _suns[key] = found
    return _suns[key]


# ── drawing a box ─────────────────────────────────────────

def boxed(place, size, scale, zones=()):
    """The picture of `place` covering `size`, words' zones dimmed,
    clipped to the panel's outline (transparent outside), or None."""
    img = source(place)
    if img is None:
        return None
    w, h = int(size[0]), int(size[1])
    key = (place, path(place), _sources[path(place)][0], w, h,
           round(scale, 4), tuple((tuple(r), round(c, 6)) for r, c in zones))
    hit = _drawn.get(key)
    if hit is not None:
        return hit
    pic = dim(cover(img, (w, h), ANCHOR.get(place, 0.5)), zones,
              FEATHER * h)
    ss = 4
    big = pygame.Surface((w * ss, h * ss))
    big.fill((0, 0, 0))
    pygame.draw.polygon(big, (255, 255, 255),
                        [(x * ss, y * ss)
                         for x, y in hud.panel_polygon(w, h, scale)])
    mask = pygame.surfarray.array_red(
        pygame.transform.smoothscale(big, (w, h)))
    out = pic.convert_alpha() if pygame.display.get_surface() else \
        pic.convert_alpha(pygame.Surface((1, 1), pygame.SRCALPHA))
    alpha = pygame.surfarray.pixels_alpha(out)
    alpha[:] = np.where(mask > 250, 255, mask)
    del alpha
    if len(_drawn) >= _DRAWN_MAX:
        _drawn.clear()
    _drawn[key] = out
    return out


def draw_box(surface, rect, scale, place, zones=()):
    """The box with its picture and the panel's edge, or False (nothing
    drawn: the caller draws the box as before). `zones` in window px."""
    r = pygame.Rect(rect)
    if r.w < 4 or r.h < 4:
        return False
    local = [(pygame.Rect(z).move(-r.x, -r.y), c) for z, c in zones]
    pic = boxed(place, r.size, scale, local)
    if pic is None:
        return False
    surface.blit(pic, r.topleft)
    hud.panel(surface, r, scale, filled=False)
    return True


def clear():
    """Forget every loaded and drawn picture (the smoke suite)."""
    _sources.clear()
    _drawn.clear()
    _suns.clear()
