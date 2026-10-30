"""The player's text size — one factor on every font OrionLayer draws.

HD EXTENSION `font_scale` (work order 356, Data): MOO2 has no such thing;
its text is a fixed bitmap font. The factor multiplies the FINAL pixel
size of a font in `StyleRenderer` (`get_font`, `get_prop_font`,
`text_width`), the one place every text path ends: `Layout.font_size`'s
callers, the HUD's cap-height sizing (`core.hud.text.size_for`) and the
direct `get_font` calls. The HUD's cap-height probe reads the font
UNSCALED (`StyleRenderer.raw_font`), or the factor would cancel itself out
of every HUD word.

**WHAT IT DOES NOT SCALE.** Boxes and row pitches stay where `boxes.json`
puts them, and the original's bitmap text (F12) is a picture. A factor
above 1.0 needs room; a screen with a fixed row pitch or a fixed button
width fits its text (`core/textfit`) rather than letting it overflow, and
the range is the one the offline probe of work order 356 found usable
(`RANGE`).

The value lives in `user_settings.json` as `font_scale` (None = 1.0), is
set by the Game Settings row and by Ctrl + mouse wheel (`main.App`), and
applies at once.
"""
import logging
import weakref

log = logging.getLogger("fontscale")

#: smallest and largest factor, and the step the wheel and the slider take.
RANGE = (0.85, 1.20)
STEP = 0.05
DEFAULT = 1.0

_factor = DEFAULT
_listeners = []


def factor():
    return _factor


def clamp(value):
    """`value` on the step grid inside `RANGE`; None or garbage is the
    default."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return DEFAULT
    if v != v:                      # NaN
        return DEFAULT
    v = round(v / STEP) * STEP
    return round(max(RANGE[0], min(RANGE[1], v)), 2)


def on_change(fn):
    """Call `fn()` whenever the factor changes (a cache keyed by a text
    size). A bound method is held weakly, so a cache that belongs to a
    screen does not outlive it here."""
    _listeners.append(weakref.WeakMethod(fn) if hasattr(fn, "__self__")
                      else fn)


def set_factor(value):
    """Set the factor, clamped; True when it changed. Applies at once."""
    global _factor
    new = clamp(value)
    if new == _factor:
        return False
    _factor = new
    for ref in list(_listeners):
        fn = ref() if isinstance(ref, weakref.WeakMethod) else ref
        if fn is None:
            _listeners.remove(ref)
        else:
            fn()
    return True


def apply_settings(user_settings):
    """The saved `font_scale`, applied at start. A value outside the range
    or of the wrong type in the file is repaired in the settings too, so
    what `get` says is what is applied (the file is written at the next
    change)."""
    saved = user_settings.get("font_scale")
    changed = set_factor(saved)
    fixed = clamp(saved)
    if saved is not None and saved != (None if fixed == DEFAULT else fixed):
        user_settings.set("font_scale", None if fixed == DEFAULT else fixed)
    return changed


def scaled(size):
    """A font size in px with the factor applied (min 8, as every font).
    At 1.0 the size is returned as it came, a float included."""
    if _factor == DEFAULT:
        return max(8, size)
    return max(8, int(round(size * _factor)))
