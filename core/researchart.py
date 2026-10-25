"""The research panel's category pictures — work order 326 E (Data).

HD EXTENSION `field_pictures`: the original paints its eight category
boxes into the TECHSEL art (tech.cpp:225-231) and has no picture per
category; HD gives every box a painted picture from the player's mod
folder, on both panels the box drawing serves — the research screen
(`screens/research_select`, SELECT NEW RESEARCH) and the research choice
popup over the map (`screens/research_change`, CHANGE CURRENT RESEARCH),
both drawn by `core.researchpanel`. Data's Mockup.png (work order 326)
binds the arrangement: the heading line (the category and its cost) stays
above the box, the picture fills the box, the field name and its
applications stand over the picture's darkened left side.

WHERE THEY LIVE (decision 95; Data's decision for this order: every new
picture of it goes into the mod folder): `files/assets/shared/research/
<category>.png`, `FOLDER` + `NAMES`, slots of `core.usermod`. One set for
both panels, so under `assets/shared/`. The category is the original's
technology group (`ENTRY_TO_GROUP`, tech.cpp:42; the groups' order is
TECH_FIELD_BIOLOGY .. TECH_FIELD_SOCIOLOGY, orion2_consts.h:991-998, and
each group's first field, mox.cpp:103, names it the same way: 18 Astro
Biology, 55 Nuclear Fission, 57 Physics, 29 Engineering, 7 Advanced
Magnetism, 22 Chemistry, 28 Electronics, 10 Military Tactics). The names
are English words, not the game's text, so a translated game finds the
same files.

NONE FOR A CATEGORY (no mod folder, the folder off, no file, an unreadable
one): None, and the box is the HUD panel as before this order.

HOW. Cover, never stretch, centred both ways (`ldrpics.cover`, the
Leaders screen's rule of work order 237): the pictures are 2 : 1 and a
box is about 2.7 : 1, so a strip above and below is cut. Clipped to the
panel's own outline (`blocks.panel_polygon`), the panel's edge drawn over
it (`blocks.panel(filled=False)`): the picture REPLACES the fill.

THE LEFT SIDE IS DARKENED (Data's order): a ramp across the box — `DARK`
of the picture's brightness kept up to `DARK_HOLD` of its width, rising
smoothly to the full picture at `DARK_END` — so the words read cleanly
over any picture. ON TOP OF IT, THE FLOOR (decision 94, the Leaders
screen's rule): under the words (`dim`'s zones, measured from the drawn
words) no pixel stays brighter than the dimmest ink drawn there keeps
4.5 : 1 against — or the plain box's contrast where that is less. INVENTION
`field_picture_shade`: the ramp's numbers are ours (decision 53), chosen on
work order 326's renders at 1920 x 1080 and 3840 x 2160.
"""
import logging
import os

import numpy as np
import pygame

from core.hud import blocks as hud
from screens.leaders import ldrpics

log = logging.getLogger("research")

FOLDER = "assets/shared/research"
#: The original's technology group (1..8) -> the picture's file name.
NAMES = {1: "biology.png", 2: "power.png", 3: "physics.png",
         4: "construction.png", 5: "force_fields.png", 6: "chemistry.png",
         7: "computers.png", 8: "sociology.png"}
#: The darkened left side: brightness kept at the left edge, how far it
#: holds, where the picture is whole again (fractions of the box width).
DARK = 0.04
DARK_HOLD = 0.60
DARK_END = 0.95
#: The words' zone's soft edge, a fraction of the box's height.
FEATHER = 0.10

_sources = {}
_drawn = {}
_DRAWN_MAX = 24


def path(group):
    """The picture file for a technology group, or None."""
    name = NAMES.get(int(group))
    if name is None:
        return None
    from core import resources
    return resources.res.resolve(f"{FOLDER}/{name}")


def source(group):
    """The group's picture as loaded, or None — read again when the file
    changes, a bad file said once."""
    p = path(group)
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
                log.warning("research: picture %s unreadable (%s) — the box "
                            "is drawn as without it", p, exc)
            img = None
        hit = (stamp, img)
        _sources[p] = hit
    return hit[1]


def _smooth(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92,
                    1.055 * c ** (1 / 2.4) - 0.055) * 255.0


def darken_left(img):
    """`img` with the left-side ramp applied, in linear light (hue kept)."""
    w, h = img.get_size()
    xs = (np.arange(w, dtype=np.float64) + 0.5) / max(1, w)
    ramp = DARK + (1.0 - DARK) * _smooth((xs - DARK_HOLD)
                                         / (DARK_END - DARK_HOLD))
    rgb = pygame.surfarray.array3d(img).astype(np.float64)
    out = _srgb(_lin(rgb) * ramp[:, None, None])
    surf = img.copy()
    pygame.surfarray.blit_array(surf, np.round(out).astype(np.uint8))
    return surf


def picture(group, size, scale, zones=()):
    """The group's picture made for a box of `size`: covered, darkened on
    the left, every zone `[(Rect in the box's px, ceiling)]` held under its
    ceiling, clipped to the panel's outline. None without a picture."""
    img = source(group)
    if img is None:
        return None
    w, h = int(size[0]), int(size[1])
    if w < 4 or h < 4:
        return None
    key = (id(img), w, h, round(scale, 4),
           tuple((tuple(r), round(c, 6)) for r, c in zones))
    hit = _drawn.get(key)
    if hit is not None:
        return hit
    pic = darken_left(ldrpics.cover(img, (w, h)))
    pic = ldrpics.dim(pic, zones, FEATHER * h)
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


#: The ceiling a little under the floor's own: the dimmed ground is
#: rounded to 8 bits, which put the brightest pixel under a word at 4.47 : 1
#: on work order 326's renders with the exact ceiling.
ROUNDING = 0.96


def ceiling(inks, box_fill, over=None):
    """The brightest ground every ink in `inks` keeps its floor on — and,
    with `over` (an RGBA band laid on the ground under a word: the
    panel's hover band), the brightest ground that keeps it with the band
    on it, found on a grey ramp (the band's blend is per channel)."""
    top = ROUNDING * min(ldrpics.ceiling(ink, box_fill) for ink in inks)
    if over is None or len(over) < 4:
        return top
    from core.hud import tint
    a = over[3] / 255.0
    best = 0.0
    for g in range(256):
        mixed = [g * (1 - a) + c * a for c in over[:3]]
        if float(tint.luminance(mixed)) > top:
            break
        best = float(tint.luminance((g, g, g)))
    return best


def draw_box(surface, rect, scale, group, words=(), inks=(), box_fill=None,
             over=None):
    """The box with its group's picture and the panel's edge; False when
    there is no picture (the caller draws the box as before). `words`:
    the window rectangles the words will be drawn in; `over`: the band a
    word may stand on (`ceiling`)."""
    r = pygame.Rect(rect)
    if r.w < 4 or r.h < 4 or source(group) is None:
        return False
    zones = ()
    if words and inks and box_fill is not None:
        top = ceiling(inks, box_fill, over)
        zones = tuple((pygame.Rect(wr).move(-r.x, -r.y).clip(
            pygame.Rect(0, 0, r.w, r.h)), top) for wr in words)
    pic = picture(group, r.size, scale, zones)
    if pic is None:
        return False
    surface.blit(pic, r.topleft)
    hud.panel(surface, r, scale, filled=False)
    return True


def clear():
    """Forget every loaded and made picture (the checks, a mod switch)."""
    _sources.clear()
    _drawn.clear()
