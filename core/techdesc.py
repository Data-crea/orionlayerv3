"""The Ship Designer's description texts, extracted from the player's
TECHDESC.LBX (work order 185).

The designer prints, beside each special system, a one-line description
(`MOX::_special_desc_string`, TECHDESC entry 1, 39 records) and, beside
each weapon in its picker, a note (`MOX::_weapon_notes_string`, entry 3,
40 records) — each a 100-byte record read by index
(`Far_Reload_Next_Data_(lbx, entry, seg, i, 1, 100)`, design_main.cpp:
580-590). The file is chosen by the game's language
(`Get_Tech_Description_Lbx_Name_`, design.cpp:1016-1042).

**Decision 38's pattern**, as `core/skildesc.py`: `tools/techdesc_extract.py`
moves the records out untouched — each cut at its first NUL, nothing else —
this module decodes at load time, the file carries a format version and is
never committed. Absent, every lookup answers None and the state says why;
the screen draws no invented text.
"""
import logging
import os

from core import derivedjson
from core.config import BASE_DIR

log = logging.getLogger("techdesc")

FORMAT_VERSION = 1
RECORD_SIZE = 100
SPECIAL_COUNT = 39
WEAPON_NOTE_COUNT = 40
#: design.cpp:1016-1042, by the codes settings.json uses.
LANGUAGE_FILES = {"en": "TECHDESC.LBX", "de": "GERTECD.LBX",
                  "fr": "FRETECD.LBX", "es": "SPATECD.LBX",
                  "it": "ITATECD.LBX"}


def string_file(language="en"):
    """Where the extractor writes and the loader reads."""
    return os.path.join("assets", "shared", "names",
                        f"techdesc_{language}.json")


class TechDesc:
    """Loaded texts, or a stated absence ("ok", "missing", "stale")."""

    def __init__(self, language="en", root=None):
        self.language = language
        self.state = "missing"
        self.specials = []
        self.weapon_notes = []
        path = os.path.join(root or BASE_DIR,
                            *string_file(language).split("/"))
        # THE SHARED HEAD (work order 191, audit D1) — and with it the
        # warning on a stale file this loader alone did not give.
        data, stale = derivedjson.load(path, log, "tech descriptions",
                                       "python tools/techdesc_extract.py",
                                       "tools/techdesc_extract.py",
                                       FORMAT_VERSION)
        if stale:
            self.state = "stale"
        if data is None:
            return
        self.specials = list(data.get("specials", []))
        self.weapon_notes = list(data.get("weapon_notes", []))
        if len(self.specials) == SPECIAL_COUNT and \
                len(self.weapon_notes) == WEAPON_NOTE_COUNT:
            self.state = "ok"

    def special(self, index):
        """The special's description, or None."""
        return _at(self.specials, index)

    def weapon_note(self, index):
        """The weapon's note, or None."""
        return _at(self.weapon_notes, index)


def _at(table, index):
    try:
        i = int(index)
    except (TypeError, ValueError):
        return None
    return table[i] if 0 <= i < len(table) else None
