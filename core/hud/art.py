"""The pieces cut out of Data's HUD, scaled once per size (decision 71).

`tools/hud_cut.py` writes them to `assets/shared/hud/cut/` — DERIVED,
unscaled crops, ignored by git and built by `tools/setup.py`. They are
resolved through the resource roots, so a mod that ships
`assets/shared/hud/cut/icon_food.png` replaces that one icon and nothing
else (decision 50's per-file fallback, for the same reason).

**Absent is a state, not an error** (decision 38): a clone that has not
run setup has no pieces, `icon()` returns None, and every block that
would have shown one draws its text alone. The log says once which
command brings them back.
"""
import logging

import pygame

from core import resources
from core.hud import style as hudstyle
from core.hud import tint

log = logging.getLogger("hud")

#: What the cutter makes — the names a block may ask for. A name outside
#: this set is a typo, and a typo must not read as "not built yet".
ICONS = ("treasury", "command", "food", "freighters", "research",
         "colonies", "planets", "fleets", "leaders", "races", "info", "turn")
TITLE_PLATE = "title_plate"

_raw = {}
_scaled = {}
_warned = set()


def _load(name):
    if name not in _raw:
        path = resources.res.shared("hud", "cut", name + ".png")
        img = None
        if path:
            try:
                img = pygame.image.load(path).convert_alpha()
            except pygame.error:
                img = pygame.image.load(path)
        elif name not in _warned:
            _warned.add(name)
            log.info("HUD piece %s not built — run python tools/setup.py "
                     "(or tools/hud_cut.py); drawn without it", name)
        _raw[name] = img
    return _raw[name]


def available(name):
    return _load(name) is not None


def raw(name):
    """The unscaled piece, or None."""
    return _load(name)


def icon(key, height):
    """Icon `key` smoothscaled to `height` device px, aspect kept."""
    assert key in ICONS, f"no HUD icon named {key!r}"
    return fit("icon_" + key, height)


def fit(name, height, width=None):
    """A piece scaled to `height` (and `width`, when given) device px.

    Scaled ONCE per size and kept: a piece is never resampled per frame,
    and never upscaled twice from something already scaled."""
    img = _load(name)
    if img is None or height < 1:
        return None
    iw, ih = img.get_size()
    if width is None:
        width = max(1, round(iw * height / ih))
    key = (name, int(width), int(height))
    if key not in _scaled:
        _scaled[key] = pygame.transform.smoothscale(
            _tinted(name, img), (int(width), int(height)))
    return _scaled[key]


def _tinted(name, img):
    """The piece in the player's frame colour (HD EXTENSION, work order
    170): the same rule as every code-drawn colour, per pixel, for the
    pieces in `tint.FOLLOWS`; the picture icons are returned as they
    are. Alpha is untouched."""
    if name not in tint.FOLLOWS or tint.delta() == 0:
        return img
    out = img.copy()
    px = pygame.surfarray.pixels3d(out)
    px[...] = tint.rotate_pixels(px)
    del px
    return out


def clear():
    """Drop the scaled copies (a resize makes every size stale)."""
    _scaled.clear()


hudstyle.on_change(lambda: _scaled.clear())


def reset():
    """Forget everything, loaded pieces included (the smoke test)."""
    _raw.clear()
    _scaled.clear()
    _warned.clear()
