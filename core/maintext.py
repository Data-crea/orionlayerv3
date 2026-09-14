"""The system-special descriptions of MAINTEXT.LBX, from a derived file.

`MAINPUPS::System_Special_Desc_` (mainpups.cpp:1065) reads entry
`desc_id` of the file ESTRINGS string 0x170 names, as a record array of
one 600-byte record (`Far_Reload_Next_Data_(..., 0, 1, 0x258)`), and
`Draw_System_Special_Popup_` (sys.cpp:580) prints it under the special's
name. The file name is set per language at startup (estrings.cpp:44-71):
maintext, maingerm, mainfren, mainspan, mainital, mainpoli.

**DECISION 38'S RULES, the help texts' and the building names':** the
text is in the player's own install, not in the source.
`tools/maintext_extract.py` moves each record out as the game's own
bytes — cut at the first NUL, decoded as code page 437, nothing else
touched — into `maintext_<lang>.json` with a format version; the file is
never committed; its absence is a state ("missing"), and a file from an
older extractor is refused ("stale") rather than rendered almost right.

NOTHING DRAWS THIS YET. The special popup lives inside the system
window, and HD's answer to the galaxy map's movable boxes is its own
brief (Data, 14 September 2026). The extractor and the loader come
first so that brief finds the text in place.
"""
import json
import logging
import os

from core.config import BASE_DIR

log = logging.getLogger("maintext")

#: Bumped when the extractor's output shape changes.
FORMAT_VERSION = 1

#: mainpups.cpp:1073 — `Far_Reload_Next_Data_(..., 0, 1, 0x258)`.
RECORD_SIZE = 600

#: `MOX::_settings.language` -> the file ESTRINGS 0x170 names
#: (estrings.cpp:44-71).
LBX_BY_LANGUAGE = {
    "en": "maintext.lbx",
    "de": "maingerm.lbx",
    "fr": "mainfren.lbx",
    "es": "mainspan.lbx",
    "it": "mainital.lbx",
    "pl": "mainpoli.lbx",
}


def text_file(language="en"):
    """Where the extractor writes and the loader reads."""
    return os.path.join("assets", "shared", "names",
                        f"maintext_{language}.json")


class MainText:
    """Loaded descriptions by entry, or a stated absence."""

    def __init__(self, language="en", root=None):
        self.language = language
        self.state = "missing"
        self.entries = {}
        self._load(root or BASE_DIR)

    def _load(self, root):
        path = os.path.join(root, *text_file(self.language).split("/"))
        if not os.path.exists(path):
            log.info("maintext: %s absent — run "
                     "`python tools/maintext_extract.py`", path)
            return
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (ValueError, OSError) as err:
            log.warning("maintext: %s will not load (%s)", path, err)
            return
        if int(data.get("format", 0)) < FORMAT_VERSION:
            self.state = "stale"
            log.warning("maintext: %s is format %s, this build reads %s — "
                        "re-run tools/maintext_extract.py",
                        path, data.get("format"), FORMAT_VERSION)
            return
        self.entries = {int(k): v for k, v in data.get("entries", {}).items()}
        self.state = "ok" if self.entries else "missing"

    def description(self, desc_id):
        return self.entries.get(int(desc_id))
