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
from core.hud import glyphs
from core.hud import lru
from core.hud import style as hudstyle
from core.hud import tint

log = logging.getLogger("hud")

#: What the cutter makes — the names a block may ask for. A name outside
#: this set is a typo, and a typo must not read as "not built yet".
ICONS = ("treasury", "command", "food", "freighters", "research",
         "colonies", "planets", "fleets", "leaders", "races", "info", "turn")
TITLE_PLATE = "title_plate"
#: The settings window's masks (work order 251, `tools/hud_cut.py`
#: SETTINGS_ICONS): white with alpha, drawn in a word's colour by `mask`.
MASKS = ("appearance", "gameplay", "graphics", "system")

# THE BUTTON GLYPHS (work order 179, part 6): the icons 169 listed as
# missing, drawn from `assets/shared/hud/glyphs.json` by
# `tools/hud_glyphs.py` into the same derived folder as the cut pieces —
# so they load, scale, tint and are replaced by a mod exactly like them.
GLYPHS = glyphs.GLYPHS
#: Every piece by file name — what a mod folder's `hud/` may replace.
PIECES = (tuple("icon_" + k for k in ICONS) + (TITLE_PLATE,)
          + tuple("icon_" + k for k in GLYPHS)
          + tuple("icon_" + k for k in MASKS))

_raw = {}
#: BOUNDED, like the shapes and the glass (`core/hud/lru.py`): a window
#: dragged through fifty widths made fifty sizes of the title plate, and
#: nothing cleared them — a resize does not run `clear` — so a session's
#: memory only grew (measured: 500 widths, about 300 entries, ~98 MB).
#: The least recently used size goes first; the newest always stays.
_SCALED_MAX, _SCALED_BYTES = 300, 96 * 1024 * 1024
_scaled = lru.Cache(_SCALED_MAX, _SCALED_BYTES)
#: The scaled pieces before tinting — they do not change with the colour.
_plain = lru.Cache(_SCALED_MAX, _SCALED_BYTES)
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
    """Icon `key` (a cut icon or a glyph) smoothscaled to `height` device
    px, aspect kept."""
    assert key in ICONS or key in GLYPHS, f"no HUD icon named {key!r}"
    return fit("icon_" + key, height)


for_button = glyphs.for_button


def mask(key, height, colour):
    """Mask `key` (`MASKS`) at `height` device px in `colour`: the white
    piece's alpha kept, its white turned to the colour. None when the
    piece is not built (absent is a state, decision 38)."""
    assert key in MASKS, f"no settings mask named {key!r}"
    img = fit("icon_" + key, height)
    if img is None:
        return None
    ck = ("mask", key, img.get_size(), tuple(colour[:3]))
    out = _scaled.get(ck)
    if out is None:
        out = img.copy()
        out.fill(tuple(colour[:3]) + (255,), special_flags=pygame.BLEND_RGBA_MULT)
        _scaled.put(ck, out)
    return out


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
    out = _scaled.get(key)
    if out is None:
        # SCALED FIRST, THEN TINTED (work order 253): tinting the piece at
        # the HUD's own size cost 0.6 s after every change of the frame
        # colour (the title plate is 4780 px wide); the scaled copy is kept
        # untinted, so a new colour only tints the few pixels on screen.
        plain = ("plain",) + key
        small = _plain.get(plain)
        if small is None:
            small = _plain.put(plain, pygame.transform.smoothscale(
                img, (int(width), int(height))))
        out = _scaled.put(key, _tinted(name, small))
    return out


def _tinted(name, img):
    """The piece in the player's frame colour (HD EXTENSION, work order
    170): the same rule as every code-drawn colour, per pixel, for the
    pieces in `tint.FOLLOWS` — the WHOLE piece, since 172, the plate's
    lamps excepted; the picture icons are returned as they are. Alpha
    is untouched."""
    if name not in tint.FOLLOWS or tint.is_default():
        return img
    out = img.copy()
    px = pygame.surfarray.pixels3d(out)
    keep = tint.lamp_mask(px) if name == TITLE_PLATE else None
    px[...] = tint.rotate_pixels(px, keep=keep)
    del px
    return out


def clear():
    """Drop the scaled copies (a resize makes every size stale)."""
    _scaled.clear()
    _plain.clear()


hudstyle.on_change(lambda: _scaled.clear())


def reset():
    """Forget everything, loaded pieces included (the smoke test)."""
    _raw.clear()
    _scaled.clear()
    _plain.clear()
    _warned.clear()
