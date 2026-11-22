"""The treaty emblems and agreement icons of the Races screen's text box.

HD EXTENSION `treaty_emblems`: the original prints the treaty paragraph as
plain text (`Draw_Race_Text_`, racescrn.cpp:148-213). HD draws Data's
emblem of the treaty at the left of the box, the treaty's label in the
emblem's colour with one line of our own under it (`SUBTITLE`, an
INVENTION: the original has no such sentence), and the agreements
(research, trade, tribute) as chips with a round icon.

WHERE THEY LIVE (as the race leaders, decision 95): the player's mod
folder `races/treaty/` = `screens/races/assets/treaty/`, exact names
`treaty_0.png` .. `treaty_5.png` (the six labels; the game's 6 shows as 5)
and `line_research.png`, `line_trade.png`, `line_give.png`, `line_get.png`.
Not in the base pack and not in git.

NONE FOR A NAME (no file, the mod folder off, an unreadable file): None,
and the caller draws the treaty paragraph as plain text, as before — never
the original's screen (Data's rule since work order 187).
"""
import logging
import os

import pygame

log = logging.getLogger("races")

FOLDER = "screens/races/assets/treaty"
KINDS = ("research", "trade", "give", "get")

#: Title colours, one per treaty 0-5: the emblem's glow colour, but No
#: Treaty a muted gold (Data, 22 Nov 2026) so it does not read as green
#: "good".
COLOURS = ((200, 168, 92), (110, 180, 255), (255, 200, 70),
           (90, 225, 210), (255, 150, 50), (255, 80, 70))
#: The sentence's colour: light grey, readable on every skin's field.
SUBTITLE_INK = (205, 215, 225)
#: INVENTION `treaty_subtitle`: the sentence under the label.
SUBTITLE = ("No formal treaty in place.", "Bound not to attack.",
            "Allied with your empire.", "At peace with your empire.",
            "Fighting a limited war.", "At war with your empire.")

_cache = {}
_fitted = {}


def _path(name):
    from core import resources
    for root in tuple(resources.res.roots()):
        path = os.path.join(root, FOLDER, name + ".png")
        if os.path.isfile(path):
            return path
    return None


def _load(name):
    path = _path(name)
    if path is None:
        return None
    try:
        stamp = os.stat(path).st_mtime_ns
    except OSError:
        return None
    hit = _cache.get(path)
    if hit is not None and hit[0] == stamp:
        return path, hit[1]
    try:
        img = pygame.image.load(path)
        img = img.convert_alpha() if pygame.display.get_surface() else img
    except (pygame.error, OSError) as exc:
        log.warning("treaty pictures: %s unreadable (%s) — drawn as text",
                    path, exc)
        img = None
    _cache[path] = (stamp, img)
    return path, img


def _scaled(name, box):
    """`name` scaled to fit inside `box` (w, h), proportions kept."""
    got = _load(name)
    if got is None or got[1] is None:
        return None
    path, img = got
    key = (path, _cache[path][0], int(box[0]), int(box[1]))
    hit = _fitted.get(key)
    if hit is None:
        if len(_fitted) > 64:
            _fitted.clear()
        w, h = img.get_size()
        k = min(box[0] / w, box[1] / h)
        hit = _fitted[key] = pygame.transform.smoothscale(
            img, (max(1, round(w * k)), max(1, round(h * k))))
    return hit


def emblem(treaty, box):
    return _scaled(f"treaty_{int(treaty)}", box)


def icon(kind, box):
    return _scaled(f"line_{kind}", box)
