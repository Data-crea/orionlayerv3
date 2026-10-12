"""Mouse cursor sizing.

The cursor was loaded at its artwork size and handed to SDL
unscaled, so it stayed 96 device pixels tall at every resolution.
That is right at 4K and wrong everywhere below — half again too
large at 1440p, twice too large at 1080p.

The size the original uses, measured off a native screenshot:

    cursor        24.9 x 21.0 native pixels
    fraction      21 / 480 = 4.38 % of screen height

Stable across a brightness threshold sweep from 24 to 80; the
measurement only collapses at 110, where the threshold starts
cutting into the sprite itself. And the shipped artwork is 96 px
tall, while 4.38 % of 2160 is 95 — the drawing was made for 4K at
exactly the original's proportion and then never scaled down. Two
sources agreeing to one pixel, which is why this is a fraction and
not a table of per-resolution sizes.

Width follows the artwork's own aspect. The HD cursor is a
different drawing from MOO2's hand and is taller than it is wide,
so height is the honest anchor.

Never upscaled past the master: above roughly 2190 px of window
height the cursor stays at its native size rather than turning into
a blurred version of itself.

Hotspot stays at (0, 0) — the tip of the pointer is the top-left
pixel, and scaling a corner leaves it a corner.
"""
import logging

import pygame

log = logging.getLogger("cursor")

#: Cursor height in native pixels, and the screen it was measured
#: on. MEASURED — see the module docstring for the sweep.
NATIVE_CURSOR_H = 21.0
NATIVE_SCREEN_H = 480.0

#: 4.38 % of the window height.
HEIGHT_FRACTION = NATIVE_CURSOR_H / NATIVE_SCREEN_H

_source = None          # unscaled artwork, loaded once
_last = None            # (w, h) actually applied, for diagnostics


def height_fraction(settings=None):
    """Fraction in use, honouring a settings override."""
    cfg = (settings or {}).get("cursor", {})
    try:
        value = float(cfg.get("height_fraction", HEIGHT_FRACTION))
    except (TypeError, ValueError):
        return HEIGHT_FRACTION
    return value if 0.005 <= value <= 0.25 else HEIGHT_FRACTION


def target_size(win_h, settings=None, source_size=None):
    """Cursor size in device pixels for a window this tall."""
    height = max(8, int(round(win_h * height_fraction(settings))))
    if source_size:
        sw, sh = source_size
        height = min(height, sh)          # never upscale the master
        width = max(1, int(round(sw * height / float(sh))))
    else:
        width = height
    return width, height


def last_size():
    return _last


def apply(res, win_h, settings=None):
    """Load if needed, scale to the window, hand to SDL.

    Called once at startup and again after every resolution or
    fullscreen change, so the cursor cannot end up sized for a
    window that no longer exists.
    """
    global _source, _last
    cfg = (settings or {}).get("cursor", {})
    if not cfg.get("enabled", True):
        try:
            pygame.mouse.set_cursor(pygame.cursors.arrow)
        except pygame.error:
            pass
        _last = None
        return None

    if _source is None:
        path = res.shared("cursor.png") if res else None
        if not path:
            return None
        try:
            _source = pygame.image.load(path).convert_alpha()
        except pygame.error as exc:
            log.warning("Custom cursor unavailable: %s", exc)
            _source = None
            return None

    size = target_size(win_h, settings, _source.get_size())
    scaled = (_source if size == _source.get_size()
              else pygame.transform.smoothscale(_source, size))
    _last = size
    # Sizing is decided above and recorded whether or not SDL can act
    # on it: headless drivers reject set_cursor outright, and a
    # diagnostic should degrade rather than make the size unknowable.
    try:
        pygame.mouse.set_cursor(pygame.cursors.Cursor((0, 0), scaled))
    except pygame.error as exc:
        log.debug("Cursor not settable on this driver: %s", exc)
    return size


def reset():
    """Drop the cached artwork — for tests and skin changes."""
    global _source, _last
    _source = None
    _last = None
