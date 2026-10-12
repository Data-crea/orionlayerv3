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


_ACTIVE_PRESET = "original"


def init(colors, preset="original", base=None):
    """Set the active skin's colour dict, with a player-colour preset.

    **THE PRESET IS READ HERE, ONCE** — decision 18: every screen binds
    its colours at import, so a preset has to be in the dict before the
    first screen module is imported. `main.App` therefore loads
    `core.usersettings` BEFORE calling this and passes the player's
    preset (and their own base table, if the file has one). Tools and
    the smoke test pass nothing and always get the original.

    `preset` other than "original" replaces the four player-colour
    tables in a COPY of `colors` (core/playercolors.py, an HD EXTENSION,
    fundament 63); the skin dict itself is never modified.
    """
    global _COLORS, _ACTIVE_PRESET
    from core import playercolors
    _COLORS, _ACTIVE_PRESET = playercolors.apply(colors or {}, preset, base)


def active_preset():
    """The preset `init` applied — what is on screen until a restart."""
    return _ACTIVE_PRESET


def col(section, key, default):
    """Color from skin section, falling back to the code default.

    Returns a tuple (RGB or RGBA, matching whatever is stored).
    """
    value = _COLORS.get(section, {}).get(key)
    if value is None:
        return tuple(default)
    return tuple(value)


def require(section, key):
    """Color from skin section, with NO code default — decision 14.

    For a colour that exists because the skin names it and for no
    other reason: a default in code would be a second home for the
    value, the one a skin edit silently fails to reach. A skin that
    lacks the key is a broken skin, so this raises and names what to
    add rather than drawing a colour nobody chose. The default skin
    carries every such key, and a smoke check holds it to that.
    """
    value = _COLORS.get(section, {}).get(key)
    if value is None:
        raise KeyError(
            f"colors.json [{section}] has no {key!r}. This colour has no "
            f"code default (decision 14) — add it to the skin")
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

def banner_table(section):
    """A banner tint table, `{colour: ((multiply), (add))}`, from the skin.

    For the tables that moved out of literals in `core/banner.py`
    (14 September 2026). Like `require` it has NO code default: a skin
    without the section is a broken skin, and this raises naming what
    to add rather than tinting with colours nobody chose. Read when a
    banner renderer is built, not at import, so a module that imports
    `core.banner` before the palette exists does not fail.
    """
    table = _COLORS.get(section)
    if not isinstance(table, dict):
        raise KeyError(
            f"colors.json has no [{section}] banner table. It has no "
            f"code default (decision 14) — add it to the skin")
    out = {}
    for name, entry in table.items():
        if name.startswith("_"):
            continue
        out[name] = (tuple(entry["multiply"]), tuple(entry["add"]))
    return out
