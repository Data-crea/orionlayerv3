"""The colony landing in HD — work order 388 (Data, 11 November 2026).

HD EXTENSION `landing_scene`: the original's landing (`COLLAND::
Colony_Landing_Screen`, colland.cpp:178-258) draws the planet's ground in
640 x 480 and plays COLONY.LBX entry 6 (73 frames, two pods) over it until
any input ends it. HD draws, over the whole window, THE GROUND THE COLONY
SCREEN WILL SHOW for this world (`screens.colony.colsurface.picture`:
climate and ground type, Data's painted pictures) and one landing craft
that comes down, throttles back, touches down and opens its landing pods.
The craft is three pictures of Data's in the mod folder
(`popups/landing_ship_body.png`, `landing_ship_flame.png`,
`landing_ship_landed.png`); with any of them, or the ground, missing the
popup's panel stays (`render` answers False).

The timeline is HD's own — the engine does not say which frame it is on
(the TPOP block of open fix 49 carries the planet, the colony, the star and
the dismiss field, nothing of the animation) — and starts when the popup is
first drawn. TRANSCRIPTION `landing_touchdown`: the craft touches down at
`T_TOUCH` = 3.4 s, between the original's two landing sounds (frame 0x39
and 0x3E of 73 at the 57 ms a tick measured live in work order 386:
3.27 s and 3.55 s, colland.cpp:127-146); the pods are open at 4.3 s, as
the original's animation ends at about 4.2 s. INVENTION `landing_path`:
the descent is straight down and slows towards the ground (the original's
pods drift diagonally, 17 frames a second); the throttling flame, the
craft's growth towards the camera and the shadow are HD's.
OMISSION `landing_planet_data`: the original prints the planet's data
(`Print_Planet_Data`, colland.cpp:117-120) in the animation's last frames;
HD's popup never showed it and this scene does not either.
"""
import logging
import os
import struct
import time

import numpy as np
import pygame

from core import resources
from core.hud import text as hudtext

log = logging.getLogger("landing")

FOLDER = "assets/shared/turnpopup/"
NAMES = {"body": "landing_ship_body.png", "flame": "landing_ship_flame.png",
         "landed": "landing_ship_landed.png"}
SLOTS = tuple(FOLDER + n for n in NAMES.values())

#: Seconds from the first draw.
T_TOUCH = 3.4
#: The flame draws back into the nozzle over the last second, then fades.
FLAME_BACK = (1.1, 0.05)          # starts before / ends before touchdown
FLAME_FADE = (0.3, -0.25)         # fades from before / until after touchdown
OPEN_TIME = 0.9
#: Reference geometry at 1080 px of window height: the landed craft's
#: scale, where it stands (fraction of the height) and the first drift.
REF_H = 1080
SHIP_SCALE = 0.34
GROUND_Y = 930 / 1080
DRIFT_X = -40
TITLE_FONT = 38

_pics = {}
_ground = {}
_shadow = {}
_started = {"key": None, "t": 0.0}


def smooth(a, b, v):
    t = min(1.0, max(0.0, (v - a) / (b - a)))
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = min(1.0, max(0.0, t))
    return 1 - (1 - t) ** 2.4


def _picture(key):
    """One of the craft's pictures, or None (absent or unreadable)."""
    path = resources.res.resolve(FOLDER + NAMES[key])
    if not path:
        return None
    try:
        stamp = os.stat(path).st_mtime_ns
    except OSError:
        return None
    got = _pics.get(key)
    if got is not None and got[0] == (path, stamp):
        return got[1] or None
    try:
        img = pygame.image.load(path)
        if pygame.display.get_surface():
            img = img.convert_alpha()
    except (pygame.error, OSError, ValueError) as err:
        log.warning("landing picture %s unreadable (%s)", path, err)
        img = None
    _pics[key] = ((path, stamp), img if img is not None else False)
    return img


def _world(popup, state):
    """(climate, ground type) of the landing's planet: the colony's climate
    where it has one, as the colony screen shows it."""
    from core.structs import colony as colony_struct
    from core.structs import planet as planet_struct
    args = popup["args"]
    planets = getattr(state, "planets_raw", None) or []
    if not 0 <= args[0] < len(planets):
        return None
    try:
        planet = planet_struct.parse(planets[args[0]])
        climate = planet.climate
        colonies = getattr(state, "colonies_raw", None) or []
        if 0 <= args[1] < len(colonies):
            climate = colony_struct.parse(colonies[args[1]]).climate
        return int(climate), int(planet.climate_bg_type)
    except (ValueError, IndexError, TypeError, struct.error):
        return None        # a record that does not parse: the panel stands


def _cover(pic, size):
    """`pic` scaled to cover `size` and cut to it from the middle."""
    key = (id(pic), size)
    got = _ground.get(key)
    if got is None:
        w, h = pic.get_size()
        k = max(size[0] / w, size[1] / h)
        big = pygame.transform.smoothscale(
            pic, (max(size[0], round(w * k)), max(size[1], round(h * k))))
        got = big.subsurface(pygame.Rect(
            (big.get_width() - size[0]) // 2,
            (big.get_height() - size[1]) // 2, *size)).copy()
        if len(_ground) >= 3:
            _ground.clear()
        _ground[key] = got
    return got


def _soft_ellipse(w, h, alpha):
    """A black ellipse with a soft edge, `w` x `h`, at most `alpha`."""
    key = (w, h)
    mask = _shadow.get(key)
    if mask is None:
        yy, xx = np.mgrid[0:h, 0:w]
        d = np.sqrt(((xx + 0.5) / w * 2 - 1) ** 2 + ((yy + 0.5) / h * 2 - 1) ** 2)
        a = np.clip((1.0 - d) / 0.55, 0.0, 1.0)
        mask = a * a * (3 - 2 * a)
        if len(_shadow) > 24:
            _shadow.clear()
        _shadow[key] = mask
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    pygame.surfarray.pixels_alpha(surf)[:] = (mask * alpha).astype(
        np.uint8).T
    return surf


#: A pause between two draws longer than this means the popup was gone and
#: this is a new landing, whatever its arguments say (the same planet can be
#: colonised again, a save can be loaded and land again).
GAP = 2.0


def elapsed(popup, now=None):
    """Seconds since this landing popup was first drawn."""
    now = time.monotonic() if now is None else now
    key = (tuple(popup["args"][:3]), popup.get("title"))
    if _started["key"] != key or now - _started.get("last", now) > GAP:
        _started["key"], _started["t"] = key, now
    _started["last"] = now
    return now - _started["t"]


def reset():
    _started["key"] = None
    _started["last"] = None


def _scaled(img, k):
    w = max(1, round(img.get_width() * k))
    h = max(1, round(img.get_height() * k))
    return pygame.transform.smoothscale(img, (w, h))


def _faded(img, alpha):
    """A new picture of `img` with its own per-pixel alpha scaled by `alpha`,
    built from the pixels: never `Surface.set_alpha` and never a `copy`.
    On Data's real window (his video of 11 Nov 2026) a craft faded that way
    showed as a black rectangle — its transparent pixels, which hold a dark
    glow in their colour, were drawn — while the same picture at full alpha
    was drawn right; no run here could reproduce it (dummy and wayland, any
    destination), so the faded picture is made to be drawn exactly as the
    unfaded one is: a plain per-pixel-alpha surface."""
    if alpha >= 1:
        return img
    w, h = img.get_size()
    rgba = np.empty((h, w, 4), np.uint8)
    rgba[..., :3] = pygame.surfarray.array3d(img).transpose(1, 0, 2)
    rgba[..., 3] = (pygame.surfarray.array_alpha(img).T * max(0.0, alpha)
                    ).astype(np.uint8)
    out = pygame.image.frombuffer(rgba.tobytes(), (w, h), "RGBA")
    return out.convert_alpha() if pygame.display.get_surface() else out


def draw_craft(surface, body, flame, landed, t, win):
    """The craft at second `t`, its ground shadow first."""
    w, h = win
    k = h / REF_H
    sc_end = SHIP_SCALE * k
    cx0, ground = w / 2, GROUND_Y * h
    prog = t / T_TOUCH
    e = ease_out(prog)
    sc = sc_end * (0.62 + 0.38 * e)         # nearer the camera as it comes down
    cx = cx0 + DRIFT_X * k * (1 - smooth(0, 1, prog))
    open_p = smooth(T_TOUCH, T_TOUCH + OPEN_TIME, t)
    top_start = -(body.get_height() + flame.get_height()) * sc_end - 40 * k
    top_end = ground - body.get_height() * sc_end
    top = top_start + (top_end - top_start) * e
    top_open = ground - landed.get_height() * sc_end
    top = top * (1 - open_p) + top_open * open_p
    # the shadow on the ground, wider and darker as the craft comes down
    sw = int(landed.get_width() * sc_end * 0.95 * (0.5 + 0.5 * e))
    sh = max(12, int(sw * 0.2))
    shadow = _soft_ellipse(max(8, sw), sh, 120 + 110 * e)
    surface.blit(shadow, (int(cx0 - sw / 2), int(ground - 6 - sh * 0.7)))
    s_use = sc if open_p == 0 else sc_end
    if open_p < 1:
        img = _faded(_scaled(body, s_use), 1 - smooth(0.35, 1.0, open_p))
        surface.blit(img, (round(cx - img.get_width() / 2), round(top)))
    if open_p > 0:
        img = _faded(_scaled(landed, sc_end), smooth(0.0, 0.65, open_p))
        surface.blit(img, (round(cx - img.get_width() / 2), round(top)))
    # the thrust draws back into the nozzle, tip first, then fades
    length = 1 - smooth(T_TOUCH - FLAME_BACK[0], T_TOUCH - FLAME_BACK[1], t)
    fade = 1 - smooth(T_TOUCH - FLAME_FADE[0], T_TOUCH - FLAME_FADE[1], t)
    if fade > 0 and length > 0.02:
        fw = max(1, round(flame.get_width() * s_use * (0.55 + 0.45 * length)))
        fh = max(2, round(flame.get_height() * s_use * length))
        img = _faded(pygame.transform.smoothscale(flame, (fw, fh)), fade)
        surface.blit(img, (round(cx - fw / 2),
                           round(top + body.get_height() * s_use)))


def render(surface, style, popup, state, title=None, now=None):
    """Draw the landing over the whole window; False when it cannot (a
    picture of the scene is missing), so the panel is drawn instead."""
    from screens.colony import colsurface
    body, flame, landed = (_picture(k) for k in ("body", "flame", "landed"))
    world = _world(popup, state)
    if None in (body, flame, landed) or world is None:
        return False
    pic = colsurface.picture(*world)
    if pic is None:
        return False
    win = surface.get_size()
    surface.blit(_cover(pic, win), (0, 0))
    draw_craft(surface, body, flame, landed, elapsed(popup, now), win)
    if title:
        img = style.render_text(title, max(12, round(
            TITLE_FONT * win[1] / REF_H)), tuple(hudtext.colour("title")[:3]))
        surface.blit(img, ((win[0] - img.get_width()) // 2,
                           int(24 * win[1] / REF_H)))
    return True
