"""The officer skill help texts (SKILDESC.LBX), loaded from a derived file.

**THE HELP-TEXT PATTERN** (decision 38), for the Leaders screen: the
texts are in the player's installation and not in the orion2re source,
so `tools/skildesc_extract.py` moves the records out untouched and this
module decodes them at load time. Format version, never committed
(`assets/shared/names/` is gitignored), a `setup.py` report, and
absence a state the screen explains.

**WHAT THE ORIGINAL READS** (`OFFICER::Load_Officer_Skill_Name_Descriptions_`,
officer.cpp:2795-2811): the LANGUAGE picks the file
(`Get_Skill_Description_LBX_Name_`, officer.cpp:3465-3490 — SKILDESC,
GERSKLLS, FRESKLLS, SPASKLLS, ITASKLLS); entry 0 holds 27 NAMES of 0x26
bytes and entry 1 holds 27 DESCRIPTIONS of 0xFF bytes, each read as one
fixed record (`Far_Reload_Next_Data_(lbx, entry, seg, i, 1, size)`).
The record index is the skill PAIR — `skill_id / 2` (:1782-1784) — so
"Famous" and "Famous*" share one text.

`Print_Officer_Skill_Help_` (officer.cpp:1761-1792) shows the NAME as
the box title with `_` turned into spaces, and the DESCRIPTION run
through `snprintf` with the leader's full name and the bonus.
"""
import logging
import os

from core.config import BASE_DIR
from core import derivedjson

log = logging.getLogger("skildesc")

FORMAT_VERSION = 1

#: 27 records per entry — one per skill pair (officer.cpp:2800, :2807).
RECORD_COUNT = 27
#: The record sizes the loader asks for (officer.cpp:2802, :2809).
NAME_SIZE, DESCRIPTION_SIZE = 0x26, 0xFF

#: `Get_Skill_Description_LBX_Name_` (officer.cpp:3465-3490).
LANGUAGE_FILES = {
    "en": "SKILDESC.LBX", "de": "GERSKLLS.LBX", "fr": "FRESKLLS.LBX",
    "es": "SPASKLLS.LBX", "it": "ITASKLLS.LBX",
}

#: How to get the file, said once where the screen can show it.
HOW = "python tools/skildesc_extract.py"


def string_file(language="en"):
    """Where the extractor writes and the loader reads."""
    return os.path.join("assets", "shared", "names",
                        f"skildesc_{language}.json")


class SkillDesc:
    """The loaded texts, or a stated absence. Never an exception.

    `state` is "ok", "missing" or "stale".
    """

    def __init__(self, language="en", root=None):
        self.language = language
        self.state = "missing"
        self.names = []
        self.descriptions = []
        self._load(root or BASE_DIR)

    def _load(self, root):
        path = os.path.join(root, *string_file(self.language).split("/"))
        data, stale = derivedjson.load(path, log, "skildesc",
                                       HOW,
                                       HOW, FORMAT_VERSION)
        if stale:
            self.state = "stale"
        if data is None:
            return
        names = list(data.get("names", []))
        descriptions = list(data.get("descriptions", []))
        if len(names) != RECORD_COUNT or len(descriptions) != RECORD_COUNT:
            log.warning("skildesc: %s holds %d names and %d descriptions, "
                        "the original reads %d of each — re-run %s", path,
                        len(names), len(descriptions), RECORD_COUNT, HOW)
            return
        self.names, self.descriptions = names, descriptions
        self.state = "ok"

    def title(self, skill_id):
        """The help box's title for a skill, `_` as spaces
        (`MISC::Replace_Char_(…, '_', ' ')`, officer.cpp:1784-1785), or
        None."""
        if self.state != "ok":
            return None
        pair = int(skill_id) // 2
        if not 0 <= pair < RECORD_COUNT:
            return None
        return self.names[pair].replace("_", " ")

    def description(self, skill_id):
        """The raw description template for a skill, or None."""
        if self.state != "ok":
            return None
        pair = int(skill_id) // 2
        if not 0 <= pair < RECORD_COUNT:
            return None
        return self.descriptions[pair]


def for_app(app):
    """One `SkillDesc` per App, built on first use — the pattern of
    `core.hestrings.for_app` (one construction site, D17)."""
    cached = getattr(app, "_skildesc", None)
    language = (getattr(app, "settings", {}) or {}).get("language", "en")
    if cached is None or cached.language != language:
        cached = SkillDesc(language)
        app._skildesc = cached
    return cached
