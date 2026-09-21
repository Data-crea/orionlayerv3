"""The original's HESTRNGS table — HAROLD's message strings — loaded
from a derived file.

**THE HELP-TEXT PATTERN AGAIN** (decision 38), after the help texts,
the building names and ESTRINGS: the strings are not in the orion2re
source but in the player's installation, so
`tools/hestrings_extract.py` moves the bytes out untouched and this
module decodes at load time. Format version, never committed, a
`setup.py` report, and absence a state the caller explains.

**THE FILE AND THE WALK ARE HAROLD'S** (`HAROLD::Load_H_Strings_`,
harold.cpp:1515-1590):

  the LANGUAGE picks the file — HESTRNGS (default), HGSTRNGS (1),
  HFSTRNGS (2), HSSTRNGS (3), HISTRNGS (4) — always entry 0, loaded
  through `Farload_Data_Static_` (farload.cpp:215), so the entry
  opens with the 4-byte (total_count, element_size) header and the
  block starts at 4, exactly as ESTRINGS does;

  the walk is `strlen + 1` with NO run skipping — an empty string is a
  valid entry — and stops after 397 strings (harold.cpp:1583).

`H_Message_(id)` returns `_h_strings[_h_string_ix[id]]` for ids 0..396
and string 0 otherwise (harold.cpp:637-648); `message()` below returns
None for an id outside the table instead, so a caller can tell a
missing string from string 0.
"""
import json
import logging
import os

from core.config import BASE_DIR

log = logging.getLogger("hestrings")

#: harold.cpp:1583 — the walk stops at 397.
HSTRINGS_COUNT = 397

FORMAT_VERSION = 1

#: harold.cpp:1524-1561 — the language picks the FILE.
LANGUAGE_FILES = {
    "en": "HESTRNGS.LBX", "de": "HGSTRNGS.LBX", "fr": "HFSTRNGS.LBX",
    "es": "HSSTRNGS.LBX", "it": "HISTRNGS.LBX",
}


def string_file(language="en"):
    """Where the extractor writes and the loader reads."""
    return os.path.join("assets", "shared", "names",
                        f"hestrings_{language}.json")


class HStrings:
    """The loaded table, or a stated absence. Never an exception.

    `state` is "ok", "missing" or "stale", like `EStrings`.
    """

    def __init__(self, language="en", root=None):
        self.language = language
        self.state = "missing"
        self.strings = []
        self._load(root or BASE_DIR)

    def _load(self, root):
        path = os.path.join(root, *string_file(self.language).split("/"))
        if not os.path.exists(path):
            log.info("hestrings: %s absent — run "
                     "`python tools/hestrings_extract.py`", path)
            return
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (ValueError, OSError) as err:
            log.warning("hestrings: %s will not load (%s)", path, err)
            return
        if int(data.get("format", 0)) < FORMAT_VERSION:
            self.state = "stale"
            log.warning("hestrings: %s is format %s, this build reads %s "
                        "— re-run tools/hestrings_extract.py",
                        path, data.get("format"), FORMAT_VERSION)
            return
        strings = list(data.get("strings", []))
        if len(strings) != HSTRINGS_COUNT:
            log.warning("hestrings: %s holds %d strings, the loader walks "
                        "%d — re-run tools/hestrings_extract.py",
                        path, len(strings), HSTRINGS_COUNT)
            return
        self.strings = strings
        self.state = "ok"

    def message(self, index):
        """`H_Message_(index)`, or None when there is no such entry."""
        try:
            position = int(index)
        except (TypeError, ValueError):
            return None
        if not 0 <= position < len(self.strings):
            return None
        return self.strings[position]


def printf(template, *values):
    """The original's `%d` / `%s` / `%%` substitution, and nothing more.

    A replace walk, not `str %` or `str.format` (decision 37): a
    template from a player's file that carries a code this does not
    know leaves it standing rather than raising in a render path.
    """
    out, vals, i = [], list(values), 0
    while i < len(template):
        ch = template[i]
        if ch == "%" and i + 1 < len(template):
            nxt = template[i + 1]
            if nxt == "%":
                out.append("%")
                i += 2
                continue
            if nxt in "ds" and vals:
                out.append(str(vals.pop(0)))
                i += 2
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def for_app(app):
    """The one `HStrings`, owned by the App and built on first use.

    **ONE CONSTRUCTION SITE — D17, Data's decision, 21 September 2026.**
    It was built at four: `galaxy_map/boxdraw` cached it on the SCREEN,
    `game_menu/screen` on the APP, `planets/planetwords` built a fresh
    one on every Planets `enter`, and `screens/fleets/screen` cached it
    per screen. So HESTRNGS.LBX's table was read into as many as four
    separate objects in one session, and the language was looked up two
    different ways — one of which raised where the others defaulted.

    **WHY ONE IS SAFE, and it is a trade rather than an obvious win.**
    The table is read-only game data from the player's installation and
    does not change while the game runs; re-extracting it needs a
    restart to be picked up, which is decision 18's trade for palettes
    applied to text. What it buys is that the file is read once and
    that a screen cannot disagree with another about what 0x9B says.

    **THE LANGUAGE LOOKUP IS THE TOLERANT ONE.** `getattr(app,
    "settings", {}) or {}` — the form `boxdraw` and `game_menu` already
    used. `colonybuild`'s `app.settings.get(...)` raised on an
    app-shaped object without `settings`, which a harness or a mod can
    easily be; that path now defaults like the rest.

    Built lazily rather than in `App.__init__`, for the reason
    `screenhelp.helptext` gives for `HelpText`: any harness holding an
    app-like object gets the same instance without a second copy of
    these lines.
    """
    existing = getattr(app, "hstrings", None)
    if existing is None:
        settings = getattr(app, "settings", {}) or {}
        existing = HStrings(settings.get("language", "en"))
        app.hstrings = existing
    return existing
