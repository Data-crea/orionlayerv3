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

#: Every colour `col` / `require` has handed out since the last `init`,
#: `(section, key) -> (value, default)`. A module that binds a colour at
#: import keeps it for good (decision 18), so a later `init` that changes
#: such a colour leaves that module on the old one while modules imported
#: afterwards get the new one: a picture mixing both tables, decided by
#: import order. Work order 310 found it: a live driver imported a map
#: module between livedrive's palette (no preset) and `main.App`'s (the
#: player's), and Altair's name came out in the original's purple in one
#: run and the preset's sky blue in another. `init` names the first such
#: colour instead of letting the mix pass silently.
_SERVED = {}


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
    stale = stale_bindings()
    if stale:
        import logging
        section_, key = stale[0]
        logging.getLogger(__name__).warning(
            "palette: %d colour(s) were bound before this palette.init and "
            "keep their old value, first %s.%s — a module was imported "
            "before the palette it should have read (decision 18)",
            len(stale), section_, key)
    _SERVED.clear()


def stale_bindings():
    """The colours handed out before the current `init` that it changed,
    sorted `(section, key)` — empty when every binding still holds."""
    out = []
    for (section_, key), (value, default) in _SERVED.items():
        now = _COLORS.get(section_, {}).get(key)
        now = tuple(default) if now is None and default is not None else now
        if now is not None:
            now = tuple(now)
        if now != value:
            out.append((section_, key))
    return sorted(out)


def active_preset():
    """The preset `init` applied — what is on screen until a restart."""
    return _ACTIVE_PRESET


def col(section, key, default):
    """Color from skin section, falling back to the code default.

    Returns a tuple (RGB or RGBA, matching whatever is stored).
    """
    value = _COLORS.get(section, {}).get(key)
    value = tuple(default) if value is None else tuple(value)
    _SERVED[(section, key)] = (value, default)
    return value


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
    _SERVED[(section, key)] = (tuple(value), None)
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
