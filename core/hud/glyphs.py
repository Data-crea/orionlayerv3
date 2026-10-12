"""The button glyphs' names and uses (work order 179, part 6).

Read from `assets/shared/hud/glyphs.json` and nothing else, so `art`
(which loads the pieces) and `tint` (which turns them) share one list
without importing each other. The shapes themselves are drawn by
`tools/hud_glyphs.py`; this module never draws.
"""
import json
import os

_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "assets", "shared", "hud", "glyphs.json")
with open(_FILE, encoding="utf-8") as _fh:
    _DATA = json.load(_fh)

#: Every glyph by name; its piece is `icon_<name>`.
GLYPHS = tuple(sorted(_DATA["glyphs"]))
#: `<screen>/<button name>` -> glyph — by the button's own name, never its
#: word, which a mod or a language changes.
BUTTONS = dict(_DATA["buttons"])


def for_button(screen, name):
    """The glyph of button `name` on `screen`, or None."""
    return BUTTONS.get(f"{screen}/{name}")
