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

HOW MUCH OF IT (Data's decision 6 of work order 219, amending how decision 82
is applied, not what it selects): at full strength 40 painted ships of
80-90 % grey plating turned one flat green — plates, panel lines and the
copper drowned in the hue. The selected grey now takes `STRENGTH` (70 %) of
the coloured value and keeps 30 % as painted, and the colour fades out at
both ends of the plating's lightness: above `HIGHLIGHT` the lit edges and
glints stay metal-grey, below `SHADOW` the panel lines and recesses stay dark
and neutral, so the mid-tones carry the owner's colour. The ranges are
placed on the painted fleet's plating (2.16 M selected pixels, 40 ships at
8 x; `dev:tools/combat_plating.py --light`): lightness median 0.33, 10 %
below 0.08, 10 % above 0.64.

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

from core import livery

from . import cbart

log = logging.getLogger("combat")

#: The colour-free name's prefix: `all_<picture>_<frame>.png` in cmbtshp/.
ALL = "all"
#: Chroma (0..1) at or below which a pixel takes the owner's colour fully,
#: and at or above which not at all (measured, see the module's docstring).
GREY, COLOURED = 0.05, 0.10
#: Lightness above which a grey pixel keeps its white (engine cores, glints).
GLINT = (0.90, 0.98)
#: Decision 6 of work order 219, the one place its numbers live: the share of
#: the coloured value a selected pixel takes, and the lightness ranges over
#: which the colour fades out — from full at HIGHLIGHT[0] to none at
#: HIGHLIGHT[1] (lit plating stays metal), from none at SHADOW[0] to full at
#: SHADOW[1] (dark lines stay neutral).
STRENGTH = 0.70
HIGHLIGHT = (0.55, 0.80)
SHADOW = (0.06, 0.16)
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
    """Which pixels are the plating (0..1), `rgb` 0..1 (w, h, 3): decision
    82's selection, unchanged by decision 6 (`amount`)."""
    mx, mn = rgb.max(-1), rgb.min(-1)
    chroma = mx - mn
    w = np.clip((COLOURED - chroma) / (COLOURED - GREY), 0, 1)
    light = (mx + mn) / 2
    return w * np.clip((GLINT[1] - light) / (GLINT[1] - GLINT[0]), 0, 1)


def tone(rgb):
    """How much of the colour a plating pixel's lightness lets through
    (0..1): none in the deep shadows and on the bright highlights."""
    light = (rgb.max(-1) + rgb.min(-1)) / 2
    hi = np.clip((HIGHLIGHT[1] - light) / (HIGHLIGHT[1] - HIGHLIGHT[0]), 0, 1)
    lo = np.clip((light - SHADOW[0]) / (SHADOW[1] - SHADOW[0]), 0, 1)
    return hi * lo


def amount(rgb):
    """How much each pixel moves towards its coloured value (0..1): the
    selection (`weights`) times `STRENGTH` times its `tone`."""
    return weights(rgb) * STRENGTH * tone(rgb)


def _lum(c):
    return c[..., 0] * 0.3 + c[..., 1] * 0.59 + c[..., 2] * 0.11


def color_blend(rgb, colour):
    """W3C compositing "color": SetLum(colour, Lum(rgb)), clipped."""
    return at_lum(_lum(rgb), colour)


def at_lum(lum, colour):
    """`colour` (0-255) at the lightness `lum` (0..1, any shape): its hue
    and saturation kept, clipped into the gamut (W3C SetLum, ClipColor)."""
    shape = np.shape(lum) + (3,)
    col = np.broadcast_to(np.array(colour, float)[:3] / 255, shape)
    c = col + (lum - _lum(col))[..., None]
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
    w = amount(rgb)[..., None]
    out = rgb * (1 - w) + color_blend(rgb, colour_rgb) * w
    res = surf.copy()
    pygame.surfarray.pixels3d(res)[:] = np.clip(out * 255 + 0.5, 0,
                                                255).astype("uint8")
    return cbart.painted_as(res, cbart.hd_factor(surf))


# ── the livery (work order 220, `core/livery`) ─────────────────────
#: The plates' middle lightness (W3C Lum): the median of the neutral pixels
#: under both zones of all four patterns, 40 ships at 8 x, 3.9 M pixels
#: (work order 220; p25 0.40, p75 0.65). A plate this light shows the laid
#: colour exactly; lighter and darker ones keep their difference.
REF = 0.52
#: Over a zone, the lightness above which a glint fades back to neutral, from
#: full at ZONE_GLINT[0] to none at ZONE_GLINT[1] — the zones' plates' 90th
#: and 98th percentile, so a lit edge stays metal and the plate itself does
#: not (219's HIGHLIGHT, 0.55-0.80, would take the colour off half of them).
ZONE_GLINT = (0.78, 0.94)


def _lum1(rgb):
    return (rgb[0] * 0.3 + rgb[1] * 0.59 + rgb[2] * 0.11) / 255


def remap(lum, pin):
    """The plates' lightness with REF moved to `pin`, 0 and 1 kept: light
    and shade keep their order and the colour's own lightness shows."""
    pin = min(max(float(pin), 1e-3), 1 - 1e-3)
    return np.where(lum <= REF, lum * (pin / REF),
                    pin + (lum - REF) * ((1 - pin) / (1 - REF)))


def lay(rgb, colour):
    """`colour` laid onto plating `rgb` (0..1): the plate at REF shows the
    colour as it is — a dark colour dark, white white — its light and
    shade around it kept. One function for both zones (part C)."""
    return at_lum(remap(_lum(rgb), _lum1(colour)), colour)


def full(rgb, owner, liv):
    """Full (decision 82 as 219 left it): the grey's `amount` towards the
    owner's colour by the color blend. The core variant moves the lightness
    by its own over the owner's; Strong at full strength is 219's colour
    byte for byte."""
    lum = _lum(rgb)
    core = livery.core_rgb(owner, liv.core)
    if liv.core != "strong":
        lum = remap(lum, REF * _lum1(core) / max(_lum1(owner), 1e-3))
    w = (amount(rgb) * liv.strength)[..., None] if liv.strength != 1 else \
        amount(rgb)[..., None]
    return rgb * (1 - w) + at_lum(lum, core) * w


def zoned(rgb, core, second, zone1, zone2, strength):
    """The livery's zones: the grey under zone 1 takes `core`, under zone 2
    `second` (if any), at `strength`; the rest stays as painted, every
    coloured pixel too (`weights`), and bright glints fade (`ZONE_GLINT`)."""
    light = (rgb.max(-1) + rgb.min(-1)) / 2
    sel = weights(rgb) * np.clip((ZONE_GLINT[1] - light) /
                                 (ZONE_GLINT[1] - ZONE_GLINT[0]), 0, 1) \
        * strength
    w = (zone1 * sel)[..., None]
    out = rgb * (1 - w) + lay(rgb, core) * w
    if second is not None and zone2 is not None:
        w = (zone2 * sel)[..., None]
        out = out * (1 - w) + lay(rgb, second) * w
    return out


def masks(art, picture, frame, pattern, size):
    """(zone 1, zone 2) of a painted frame for a pattern, each 0..1 (w, h)
    or None: read through the picture's own loader, so held and sized as it
    is (decision 83); a mask of another size than its picture is not used,
    with one log line."""
    if pattern not in livery.MASK_PATTERNS:
        return None, None
    out = []
    for zone in (1, 2):
        nm = livery.mask_name(picture, frame, pattern, zone)
        m = art.painted_file("cmbtshp", nm, int(picture))
        if m is not None and m.get_size() != size:
            key = ("mask_size", nm)
            if key not in art._cache:
                art._cache[key] = True
                log.warning("combat: %s is %d x %d, its picture %d x %d — "
                            "not used", nm, *m.get_size(), *size)
            m = None
        out.append(None if m is None else
                   pygame.surfarray.array3d(m)[..., 0].astype(float) / 255)
    return tuple(out)


def livery_recoloured(art, surf, picture, frame, colour, liv):
    """`surf`, a colour-free painted frame, in the livery `liv` for the
    owner `colour`: its pattern's zones where the ship has them, else Full.
    The factor kept (`cbart.painted_as`)."""
    owner = owner_rgb(colour)
    if liv.pattern == "full" and liv.core == "strong" and \
            liv.strength == 1:
        return recoloured(surf, owner)
    rgb = pygame.surfarray.array3d(surf).astype(float) / 255
    z1, z2 = masks(art, picture, frame, liv.pattern, surf.get_size())
    if z1 is None:
        out = full(rgb, owner, liv)
    else:
        out = zoned(rgb, livery.core_rgb(owner, liv.core),
                    liv.second_for(colour), z1, z2, liv.strength)
    res = surf.copy()
    pygame.surfarray.pixels3d(res)[:] = np.clip(out * 255 + 0.5, 0,
                                                255).astype("uint8")
    return cbart.painted_as(res, cbart.hd_factor(surf))


def _file(art, picture, frame):
    return art.painted_file("cmbtshp", name(picture, frame), int(picture))


def source(art, picture, facing, glow):
    """(picture, mirror, flip, turn degrees, its frame) of the colour-free
    frame for `facing` and `glow`, or None. The original's own scheme: five stored
    facings, the other eleven their mirrors and flips (`stored_facing`).
    A stored facing's frame, else its frame 0 (the glow); a stored facing
    not given at all is the nearest given one turned, from 2 x and up."""
    stored, mirror, flip = cbart.stored_facing(facing)
    for g in dict.fromkeys((max(0, min(3, int(glow))), 0)):
        p = _file(art, picture, 4 * stored + g)
        if p is not None:
            return p, mirror, flip, 0.0, 4 * stored + g
    have = [s for s in range(5) if _file(art, picture, 4 * s) is not None
            or _file(art, picture, 4 * s + int(glow)) is not None]
    if not have:
        return None
    s = min(have, key=lambda s: (abs(stored - s), s))
    frame = 4 * s + int(glow)
    p = _file(art, picture, frame)
    if p is None:
        frame = 4 * s
        p = _file(art, picture, frame)
    if cbart.hd_factor(p) <= 1:
        return None
    return p, mirror, flip, (stored - s) * 22.5, frame


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
    liv = getattr(art, "livery", livery.DEFAULT)
    key = ("plating", int(colour), int(picture), int(facing) & 15, frame,
           liv.key())
    cache = art._cache
    if key in cache:
        return cache[key]
    out = None
    src = source(art, picture, facing, glow)
    if src is not None:
        pic, mirror, flip, turn, at = src
        ck = ("plating_src", id(pic), int(colour), liv.key())
        if ck not in cache:
            cache[ck] = (pic, livery_recoloured(art, pic, picture, at,
                                                colour, liv))
        out = cache[ck][1]
        if turn:
            out = turned(out, turn)
        if mirror or flip:
            k = cbart.hd_factor(out)
            out = cbart.painted_as(pygame.transform.flip(out, mirror, flip),
                                   k)
    cache[key] = out
    return out
