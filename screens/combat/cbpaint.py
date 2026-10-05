"""One painted ship for every owner — work order 217, decision 82.

HD EXTENSION `plating_colour` (Data's decision, 216 P1): a painted battle
picture saved under the COLOUR-FREE name `cmbtshp/all_<picture>_<frame>.png`
(`all_43_0.png`: the Doom Star, facing 0, no glow) serves every owner whose
colour has no file of its own. Its neutral grey takes the owner's colour,
keeping its light and shade; what is painted in colour — engines, accents,
lights — stays as painted. The original has eight drawings per ship, one per
colour, and no such rule.

THE ORDER, per frame (`CombatArt.ship`): the colour's own file
`<colour * 45 + picture>_<frame>.png` drawn as painted, as before; else the
colour-free picture, recoloured; else the stored drawing. Without either
file nothing here runs and the battle draws exactly what it drew.

NEUTRAL GREY, measured on the one painted ship there is (Data's Doom Star,
236 x 240, 35 831 opaque pixels; `dev:tools/combat_plating.py`): the chroma
max(r, g, b) - min(r, g, b) of 80 % of its pixels lies below 0.05 — the
plating, leaning blue, its highlights and dark lines included — and the
counts fall from 8 329 to 335 a 0.025 bin between 0.05 and 0.10, the copper
and the purple engines above. So a pixel takes the colour fully below
`GREY` 0.05, not at all above `COLOURED` 0.10, in between in proportion;
the selection moves by two points of the ship between 0.04-0.08 and
0.06-0.12, the valley is wide. Near-white (lightness above `GLINT`) is faded
out of it, so the white-hot engine cores and the glints stay white.

THE COLOUR is the owner's colour as HD shows it everywhere
(`galaxy_map.owner_<colour>`, the player-colour presets included), laid on by
the W3C compositing "color" blend: its hue and saturation at the pixel's own
lightness. Computed once per picture and colour, then cached.

MISSING FRAMES, colour-free pictures only (a colour's own files are drawn as
before): a missing glow frame (1-3) is its facing's frame 0; a missing
STORED facing (the original draws five, 0-4, and mirrors and flips them
into the other eleven) is TURNED in code from the nearest stored facing
given, only from a picture larger than 1 x (216: 1 x goes soft) — a 1 x
picture with a facing missing leaves that facing to the stored drawing;
the other eleven facings are mirrors and flips of the five, as the
original's. The stored drawings are never turned. One file, `all_<picture>_0.png` at 2 x or more, is a whole ship.
"""
import logging

import numpy as np
import pygame

from . import cbart

log = logging.getLogger("combat")

#: The colour-free name's prefix: `all_<picture>_<frame>.png` in cmbtshp/.
ALL = "all"
#: Chroma (0..1) at or below which a pixel takes the owner's colour fully,
#: and at or above which not at all (measured, see the module's docstring).
GREY, COLOURED = 0.05, 0.10
#: Lightness above which a grey pixel keeps its white (engine cores, glints).
GLINT = (0.90, 0.98)
#: The original's owner colours, if the palette is not loaded (a tool).
_DEFAULT = ((196, 74, 56), (206, 172, 34), (86, 166, 70), (226, 226, 234),
            (126, 174, 216), (196, 130, 88), (162, 104, 136), (238, 132, 12))


def name(picture, frame):
    return f"{ALL}_{int(picture)}_{int(frame)}.png"


def owner_rgb(colour):
    from core import palette
    c = max(0, min(7, int(colour)))
    return tuple(palette.col("galaxy_map", f"owner_{c}", _DEFAULT[c]))[:3]


def weights(rgb):
    """How much each pixel takes the colour (0..1), `rgb` 0..1 (w, h, 3)."""
    mx, mn = rgb.max(-1), rgb.min(-1)
    chroma = mx - mn
    w = np.clip((COLOURED - chroma) / (COLOURED - GREY), 0, 1)
    light = (mx + mn) / 2
    return w * np.clip((GLINT[1] - light) / (GLINT[1] - GLINT[0]), 0, 1)


def _lum(c):
    return c[..., 0] * 0.3 + c[..., 1] * 0.59 + c[..., 2] * 0.11


def color_blend(rgb, colour):
    """W3C compositing "color": SetLum(colour, Lum(rgb)), clipped."""
    col = np.broadcast_to(np.array(colour, float) / 255, rgb.shape)
    c = col + (_lum(rgb) - _lum(col))[..., None]
    lum = _lum(c)[..., None]
    lo = c.min(-1, keepdims=True)
    hi = c.max(-1, keepdims=True)
    c = np.where(lo < 0, lum + (c - lum) * lum / np.maximum(lum - lo, 1e-6),
                 c)
    return np.where(hi > 1, lum + (c - lum) * (1 - lum) /
                    np.maximum(hi - lum, 1e-6), c)


def recoloured(surf, colour_rgb):
    """`surf` with its neutral grey in `colour_rgb`; alpha and every
    coloured pixel as painted; the painted factor kept."""
    rgb = pygame.surfarray.array3d(surf).astype(float) / 255
    w = weights(rgb)[..., None]
    out = rgb * (1 - w) + color_blend(rgb, colour_rgb) * w
    res = surf.copy()
    pygame.surfarray.pixels3d(res)[:] = np.clip(out * 255 + 0.5, 0,
                                                255).astype("uint8")
    return cbart.painted_as(res, cbart.hd_factor(surf))


def _file(art, picture, frame):
    return art.painted_file("cmbtshp", name(picture, frame), int(picture))


def source(art, picture, facing, glow):
    """(picture, mirror, flip, turn degrees) of the colour-free frame for
    `facing` and `glow`, or None. The original's own scheme: five stored
    facings, the other eleven their mirrors and flips (`stored_facing`).
    A stored facing's frame, else its frame 0 (the glow); a stored facing
    not given at all is the nearest given one turned, from 2 x and up."""
    stored, mirror, flip = cbart.stored_facing(facing)
    for g in dict.fromkeys((max(0, min(3, int(glow))), 0)):
        p = _file(art, picture, 4 * stored + g)
        if p is not None:
            return p, mirror, flip, 0.0
    have = [s for s in range(5) if _file(art, picture, 4 * s) is not None
            or _file(art, picture, 4 * s + int(glow)) is not None]
    if not have:
        return None
    s = min(have, key=lambda s: (abs(stored - s), s))
    p = _file(art, picture, 4 * s + int(glow)) or _file(art, picture, 4 * s)
    if cbart.hd_factor(p) <= 1:
        return None
    return p, mirror, flip, (stored - s) * 22.5


def turned(surf, degrees):
    """`surf` turned `degrees` counter-clockwise about its canvas's centre,
    on its own canvas (`rotozoom`, decision 32), the factor kept."""
    r = pygame.transform.rotozoom(surf, degrees, 1.0)
    out = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    out.blit(r, (round((surf.get_width() - r.get_width()) / 2),
                 round((surf.get_height() - r.get_height()) / 2)))
    return cbart.painted_as(out, cbart.hd_factor(surf))


def ship(art, colour, picture, facing, glow=0):
    """The colour-free painted picture of a player's ship in `colour`, or
    None: the colour has its own file for this frame, or there is no
    colour-free picture for it."""
    stored, _m, _f = cbart.stored_facing(facing)
    frame = 4 * stored + max(0, min(3, int(glow)))
    if art._painted("cmbtshp", int(colour) * 45 + int(picture),
                    frame) is not None:
        return None
    key = ("plating", int(colour), int(picture), int(facing) & 15, frame)
    cache = art._cache
    if key in cache:
        return cache[key]
    out = None
    src = source(art, picture, facing, glow)
    if src is not None:
        pic, mirror, flip, turn = src
        ck = ("plating_src", id(pic), int(colour))
        if ck not in cache:
            cache[ck] = (pic, recoloured(pic, owner_rgb(colour)))
        out = cache[ck][1]
        if turn:
            out = turned(out, turn)
        if mirror or flip:
            k = cbart.hd_factor(out)
            out = cbart.painted_as(pygame.transform.flip(out, mirror, flip),
                                   k)
    cache[key] = out
    return out
