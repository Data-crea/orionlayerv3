"""Skin color palette.

Screens and renderers read their colors through col() so every
color can be changed in the skin's colors.json without touching
code. Code passes a default, which is used when the skin doesn't
define the key — so colors.json only needs the values a skin
actually wants to change.

colors.json structure (per-screen sections are optional):

    {
      "button": { ... },            core UI (style.py)
      "text": { ... },
      "select_race": {              per-screen palettes
        "heading": [138, 180, 232],
        ...
      },
      "custom_race": { ... },
      "main_menu": { ... }
    }

init() must run before screen modules are imported, because
renderers resolve their color constants at import time.
Changing the skin therefore requires a restart.
"""

_COLORS = {}


def init(colors):
    """Set the active skin's color dict (from colors.json)."""
    global _COLORS
    _COLORS = colors or {}


def col(section, key, default):
    """Color from skin section, falling back to the code default.

    Returns a tuple (RGB or RGBA, matching whatever is stored).
    """
    value = _COLORS.get(section, {}).get(key)
    if value is None:
        return tuple(default)
    return tuple(value)


def section(name):
    """Whole section dict (read-only use)."""
    return _COLORS.get(name, {})


def for_section(name):
    """Bind a screen's section name once, get back a col() shorthand.

    Replaces the per-screen ``def _c(key, default): return
    palette.col("my_screen", key, default)`` copies that used to be
    pasted into every renderer module. Usage at module scope::

        _c = palette.for_section("my_screen")
        COL_HEADING = _c("heading", (138, 180, 232))
    """
    def _bound(key, default):
        return col(name, key, default)
    return _bound
