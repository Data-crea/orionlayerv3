"""The HUD style values — one file every screen reads (decision 71).

`assets/shared/hud/style.json`, resolved through the resource roots so a
mod can replace the look (decision 16). Its `measured` block is held to
`tools/hud_measure.py` by the smoke test; its `chosen` block carries what
nothing in Data's material shows, each value with its reason.

Read ONCE per process, like the palette (decision 18): the blocks cache
drawn surfaces keyed on sizes, and a style that changed under them would
leave yesterday's panels in the cache.
"""
import logging

from core import resources
from core.hud import tint

log = logging.getLogger("hud")

PATH = "assets/shared/hud/style.json"

_STYLE = None


class HudStyle:
    """Dotted access to style.json: `get("panel.edge")`.

    A key that starts in `measured` or `chosen` is looked up there;
    anything else is looked up in `measured` first, then `chosen`, so a
    block names a value by what it is and not by where it came from.
    `*_from` values in `chosen` are indirections ("action.edge") and are
    resolved here, once, so no block has to know which values borrow.
    """

    def __init__(self, data):
        self.data = data or {}
        self.measured = self.data.get("measured", {})
        self.chosen = self.data.get("chosen", {})

    def _walk(self, root, path):
        node = root
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node

    def get(self, path, default=None):
        for root in (self.measured, self.chosen):
            v = self._walk(root, path)
            if v is not None:
                return v
        if default is None:
            raise KeyError(f"hud style has no value {path!r}")
        return default

    def colour(self, path):
        """An RGB tuple; a `*_from` indirection is followed.

        Turned to the player's frame colour (`core.hud.tint`, HD
        EXTENSION, work order 170) — except a TEXT colour and the
        background placeholder, which the setting never touches."""
        v = self._walk(self.chosen, path + "_from")
        if isinstance(v, str):
            return self.colour(v)
        c = tuple(int(x) for x in self.get(path)[:3])
        if not_tinted(path):
            return c
        return tint.rotate(c)

    def mix(self, a, b, t):
        """`a` moved a fraction `t` towards `b`, both RGB tuples."""
        return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def not_tinted(path):
    """The style values the frame colour never turns: every word and the
    background placeholder (work order 170, the never-recolour list)."""
    return (path.startswith("text.") or path.startswith("mockup_colony.text_")
            or path == "background_placeholder")


_listeners = []


def on_change(fn):
    """Call `fn()` whenever the frame colour changes — the block and
    piece caches, which are built per colour."""
    _listeners.append(fn)


def set_hue(value):
    """Set the frame colour (None = the measured blue) and invalidate
    every cache built for the old one. Applies at once, no restart."""
    if tint.set_hue(value):
        for fn in _listeners:
            fn()
        return True
    return False


def get():
    """The process's HUD style, loaded on first use."""
    global _STYLE
    if _STYLE is None:
        data = resources.res.load_json(PATH, None)
        if data is None:
            log.error("HUD style %s missing or unreadable — every block "
                      "will fail; run from a complete tree", PATH)
        _STYLE = HudStyle(data)
    return _STYLE


def reset():
    """Forget the loaded style (the smoke test, after swapping roots)."""
    global _STYLE
    _STYLE = None
