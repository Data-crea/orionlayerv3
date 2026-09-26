"""The picture behind every HD screen — work order 173, decision 71's slot.

**ONE PICTURE, ONE PLACE.** Data's universal background,
`assets/shared/backgrounds/universal.png` (authored artwork, decision
58's pattern; LICENSE), stands behind every HD screen and under every
popup, which draws over its screen. A screen with a picture of its own —
`assets/shared/backgrounds/<screen>.png`, today the Main Menu's title
art (169, P6) — wears that one instead.

**THE ORDER, file for file** (decision 72): the player's mod folder
replaces each file of the same name (`core.usermod`, asked through
`Resources.resolve` like every other file), then

    the screen's own picture  >  the universal picture  >  the placeholder

so a mod's `backgrounds/galaxy_map.png` beats its `background.png`, and
a mod's `background.png` replaces the universal picture on every screen
that has no picture of its own.

**COVER, NEVER STRETCH.** Scaled so it fills the window at the picture's
own aspect, the overflow cropped evenly from both sides — at every
window size, 16:9 or not: no distortion, no strip. Scaled ONCE per
picture and window size, and the screens share the copy: thirteen
screens on one picture keep one surface per size, not thirteen.

**NEVER TINTED.** The frame colour turns HUD components only (172's
component rule); nothing here asks `core.hud.tint`.
"""
import logging
from collections import OrderedDict

import pygame

from core import resources

log = logging.getLogger("backgrounds")

DIR = "assets/shared/backgrounds"
UNIVERSAL = DIR + "/universal.png"

#: Scaled copies kept: a window size or two for the universal picture
#: and the Main Menu's. A 3840x2160 copy is 33 MB, so the cache is small.
KEEP = 4

_paths = {}
_sources = {}
_scaled = OrderedDict()
_failed = set()
#: The last picture handed out for drawing — what the panel glass shows
#: through (work order 174): (key, surface) or None.
_current = [None]


def source_path(screen_name):
    """The file this screen wears, or None for the placeholder."""
    if screen_name not in _paths:
        own = resources.res.resolve(f"{DIR}/{screen_name}.png")
        path = own if own and _load(own) is not None else None
        if path is None:
            uni = resources.res.resolve(UNIVERSAL)
            path = uni if uni and _load(uni) is not None else None
        _paths[screen_name] = path
    return _paths[screen_name]


def _load(path):
    if path not in _sources:
        img = None
        try:
            img = pygame.image.load(path)
            if pygame.display.get_surface() is not None:
                img = img.convert()
        except (pygame.error, OSError) as err:
            if path not in _failed:
                _failed.add(path)
                log.warning("background %s cannot be read (%s) — the next "
                            "one in line is used", path, err)
        _sources[path] = img
    return _sources[path]


def cover(img, w, h):
    """`img` filling a w x h window at its own aspect, centred, the
    overflow cropped. Exactly w x h."""
    iw, ih = img.get_size()
    scale = max(w / iw, h / ih)
    sw, sh = max(w, round(iw * scale)), max(h, round(ih * scale))
    big = pygame.transform.smoothscale(img, (sw, sh))
    return big.subsurface(((sw - w) // 2, (sh - h) // 2, w, h)).copy()


def scaled(screen_name, w, h):
    """The screen's picture at the window's size, or None."""
    path = source_path(screen_name)
    if path is None or w < 1 or h < 1:
        return None
    key = (path, int(w), int(h))
    if key in _scaled:
        _scaled.move_to_end(key)
    else:
        _scaled[key] = cover(_sources[path], int(w), int(h))
        while len(_scaled) > KEEP:
            _scaled.popitem(last=False)
    _current[0] = (key, _scaled[key])
    return _scaled[key]


def current(w, h):
    """(key, surface) of the picture last drawn at w x h, or None — the
    background the panel glass shows through. The key names the picture
    and the size, so a cache keyed on it is rebuilt when either changes."""
    cur = _current[0]
    if cur is None or cur[1].get_size() != (int(w), int(h)):
        return None
    return cur


def draw(surface, screen_name):
    """The screen's background over the whole surface, or the
    placeholder where there is no picture at all."""
    pic = scaled(screen_name, *surface.get_size())
    if pic is not None:
        surface.blit(pic, (0, 0))
    else:
        from core.hud import style as hudstyle
        surface.fill(hudstyle.get().colour("background_placeholder"))


def reset():
    """Forget everything (the smoke test, after changing roots)."""
    _paths.clear()
    _sources.clear()
    _scaled.clear()
    _failed.clear()
    _current[0] = None
