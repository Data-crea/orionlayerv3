"""The council's hall — the chamber as a picture, the leaders in it.

**HD EXTENSION `council_hall`.** When the player (or a mod, or the base
pack) puts a picture at `assets/shared/backgrounds/council.png`, the
council is that hall instead of panels: the six wall screens show the
members' leaders, the two nominees stand in front, and the game's lines
and message stay on the plates the shell cuts (`screen`). Without the
picture the screen is what it was (the DEVIATION `no_chamber` panels).

**Where the original puts them (a transcription).** `Draw_Main_Council_
Screen` draws member i at the i-th of six places (x_coords {44, 520, 143,
444, 215, 377}, council.cpp:158-159) — the light picture for the one voting
now in state 2 or 3, the dark one for the rest (:182-190) — and the two
nominees at (115, 225) and (320, 225), the second 205 right (:192-201).
The six places run far left, far right, then inwards: `SLOT` is that order
read left to right. HD keeps the rule: the voting member's screen is lit,
the others are dimmed.

**Where the screens are in the picture (a measurement).** Data's hall
(1672 x 941) was measured off the picture: each screen's dark disc found
by threshold and opening, its centre and radii in pixels — not eyed. The
numbers are fractions of the picture, so a mod's hall drawn on the same
plan at another size keeps them.

**The leaders** are the first frame of the race's audience clip
(`auvideo.clip_dir`): the ambassador and his room in one picture, cut to
the head and shoulders for a screen and to the figure for a nominee, with
a soft edge. A race with no clip shows a dark screen and its name.
"""
import os

import pygame

from core import backgrounds
from core.structs import player as player_struct

PICTURE = (1672, 941)
#: (centre x, centre y, radius x, radius y) in picture px, measured; a
#: margin of 3 px puts the picture under the screen's rim.
_MARGIN = 3
SCREENS = tuple(
    ((cx) / PICTURE[0], (cy) / PICTURE[1],
     (rx + _MARGIN) / PICTURE[0], (ry + _MARGIN) / PICTURE[1])
    for cx, cy, rx, ry in (
        (211.5, 263.5, 95.0, 100.0), (448.0, 337.5, 70.5, 70.0),
        (639.0, 369.0, 60.5, 58.5), (1032.0, 368.5, 59.5, 58.0),
        (1223.5, 337.0, 70.0, 70.5), (1458.0, 263.0, 95.5, 98.5)))
#: member i -> the screen counted from the left (x_coords, council.cpp:158).
SLOT = (0, 5, 1, 4, 2, 3)
#: nominee centres across the picture, feet at FEET, height as a share of
#: the picture's. The original's (115, 225) and (320, 225), 206 x 255
#: (council.cpp:192; COUNCIL.LBX 158/159), stand BELOW the screens (they end
#: at y 222) with the message over the floor; HD keeps the order — screens,
#: nominees, message — in a 16:9 hall, so the figures start under the
#: screens' foot (0.47 of the picture) and the message plate is slimmed to
#: stay under their feet (`message_rect`).
NOMINEE_X = (0.33, 0.67)
FEET, TALL = 0.78, 0.30
#: Where the head and shoulders, and the figure, are in an audience clip's
#: frame, as fractions (x, y, w, h). The ambassadors stand on one pedestal
#: in one room, centred; the HEAD cut starts under the green light (it ends
#: at 0.17 of the frame) and is as wide as it is tall, so the face fills a
#: round screen. Seen on the twelve clips Data has (a contact sheet of the
#: cuts, work order 385): every head inside it, none touching the edge.
HEAD = (0.37, 0.15, 0.26, 0.46)
FIGURE = (0.33, 0.155, 0.34, 0.775)
#: The green light sits over the head (frame rows 0 to 0.17): its pixels
#: are blacked at the top of a cut (`_clean`), nowhere else, so a figure's
#: own green (an eye, a jewel) stays.
#: How much the edge of a screen's cut is darkened (a round vignette): the
#: room's ribs and arcs fall away into the screen's black.
VIGNETTE = 0.45
#: the figure's width over its height: the clip is 16:9.
ASPECT = FIGURE[2] * 16 / 9 / FIGURE[3]
DIM = (96, 96, 96)

_frames = {}                  # race -> frame surface, or None
_made = {}                    # (race, w, h, kind) -> surface


def hall_path():
    """The hall picture the council wears, or None."""
    path = backgrounds.source_path("council")
    return path if path and os.path.basename(path) == "council.png" \
        else None


def active():
    return hall_path() is not None


def race_of(state, player):
    """The player's race index (0..12) or None."""
    raws = getattr(state, "player_raw", None) or []
    if not isinstance(player, int) or player < 0:
        return None            # -1 is no player, not the last record
    try:
        race = int(player_struct.SPEC.parse(raws[player]).race)
    except (ValueError, IndexError, TypeError):
        return None
    return race if 0 <= race < 13 else None


def _frame(race):
    if race not in _frames:
        img = None
        from screens.audience import auvideo
        folder = auvideo.clip_dir(race, "default")
        if folder is not None:
            try:
                names = sorted(n for n in os.listdir(folder)
                               if n.lower().endswith((".jpg", ".jpeg",
                                                      ".png")))
                # smoothscale refuses a palettised picture
                img = pygame.image.load(
                    os.path.join(folder, names[0])).convert_alpha()
            except (OSError, IndexError, pygame.error):
                img = None
        _frames[race] = img
    return _frames[race]


def forget():
    """Drop the cached frames and cuts (a changed mod, a new clip)."""
    _frames.clear()
    _made.clear()


def _soft_ellipse(w, h):
    """An alpha mask: an ellipse with a soft edge."""
    small = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.ellipse(small, (255, 255, 255, 255), (3, 3, 26, 26))
    return pygame.transform.smoothscale(small, (w, h))


def _hard_ellipse(w, h):
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(mask, (255, 255, 255, 255), (0, 0, w, h))
    return mask


def _clean(pic, kind):
    """Black the green light in the top of the cut and, for a screen,
    darken the edge (`LIGHT`, `VIGNETTE`)."""
    import numpy as np
    px = pygame.surfarray.pixels3d(pic)
    w, h = px.shape[0], px.shape[1]
    # the light fills frame rows 0-0.17: the first 0.04 of a head cut (the figure cut starts under it)
    top = px[:, :max(1, int(h * 0.08))]
    r, g, b = (top[..., i].astype(int) for i in range(3))
    top[(g > r * 1.6) & (g > b * 1.15) & (g > 140)] = 0
    if kind == "head":
        xs = (np.arange(w)[:, None] - w / 2) / (w / 2)
        ys = (np.arange(h)[None, :] - h / 2) / (h / 2)
        d = np.clip(np.hypot(xs, ys), 0, 1)
        k = np.clip(1.15 - VIGNETTE * d * d, 0, 1)
        px[...] = (px * k[..., None]).clip(0, 255).astype(px.dtype)
    del px                    # unlocks the surface


def leader(race, w, h, kind, dim=False):
    """The race's leader cut to a w x h ellipse (`kind` "head": a wall
    screen, hard edge; "figure": a nominee, soft edge), or None."""
    key = (race, w, h, kind, dim)
    if key not in _made:
        if len(_made) > 64:       # a window dragged through many sizes
            _made.clear()
        src = _frame(race)
        pic = None
        if src is not None and w > 0 and h > 0:
            fx, fy, fw, fh = HEAD if kind == "head" else FIGURE
            sw, sh = src.get_size()
            crop = src.subsurface((int(fx * sw), int(fy * sh),
                                   int(fw * sw), int(fh * sh)))
            pic = pygame.transform.smoothscale(crop, (w, h)).convert_alpha()
            _clean(pic, kind)
            mask = _hard_ellipse(w, h) if kind == "head" \
                else _soft_ellipse(w, h)
            pic.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            if dim:
                pic.fill(DIM + (255,), special_flags=pygame.BLEND_RGB_MULT)
        _made[key] = pic
    return _made[key]


def member_rects(w, h):
    """The six wall screens as window rects, left to right, or None."""
    out = []
    for fx, fy, rx, ry in SCREENS:
        got = backgrounds.point("council", w, h, fx, fy)
        if got is None:
            return None
        x, y, scale = got
        pw, ph = rx * PICTURE[0] * scale, ry * PICTURE[1] * scale
        out.append(pygame.Rect(round(x - pw), round(y - ph),
                               round(2 * pw), round(2 * ph)))
    return out


def nominee_rects(w, h):
    """The two nominee figures as window rects, or None."""
    out = []
    for fx in NOMINEE_X:
        got = backgrounds.point("council", w, h, fx, FEET)
        if got is None:
            return None
        x, y, scale = got
        ph = TALL * PICTURE[1] * scale
        pw = ph * ASPECT
        out.append(pygame.Rect(round(x - pw / 2), round(y - ph),
                               round(pw), round(ph)))
    return out


def message_rect(box, share=0.55):
    """The message plate in the hall: the lower `share` of the shell's box,
    so the nominees stand clear above it."""
    cut = int(box.h * (1 - share))
    return pygame.Rect(box.x, box.y + cut, box.w, box.h - cut)
