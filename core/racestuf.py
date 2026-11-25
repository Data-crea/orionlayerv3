"""The stock races' traits (RACESTUF.LBX), loaded from a derived file.

**THE HELP-TEXT PATTERN** (decision 38), for Select Race (work order 209
A2): the traits are in the player's installation, so
`tools/racestuf_extract.py` moves the records and the names out
untouched and this module builds the list at load time. Format version,
never committed (`assets/shared/names/` is gitignored), a `setup.py`
report, and absence a state the screen states.

**WHAT THE ORIGINAL READS.** `Reload_Race_Selection_Screen_` takes one
record of `TRAIT_COUNT` (31) bytes per stock race out of entry 7
(racesel.cpp:137-140, the same records `Init_Players_` copies into the
players, initgame.cpp:280-296); `Load_Player_Special_Names_` takes the
32 trait names out of entry `language + 8` (loader.cpp:105-127), one
file for every language.

**WHAT IT PRINTS** (`Draw_Race_Selection_Screen_`, race_display.cpp:81-140):
first every bonus trait (1..9) whose byte is not 0, as its name and
`_special_bonus[trait - 1][level - 1]` as `Format_Numeric_Trait` prints it
(raceopt_display.cpp:4-21, WO 428: a sign, Food and Tax halved with ".5"
when odd, " BC" after the Tax);
then every trait from Low-G World on whose byte is not 0, as its name; last
the government, `_government_labels[byte 0]` (ESTRINGS 0x27C + n,
estrings.cpp:99-106). The original joins them into one sentence with
", " and KEN 0x68 before the last; HD lists them one per row in its own
box (`[select_race.traits]`).
"""
import logging
import os

from core import derivedjson
from core.config import BASE_DIR

log = logging.getLogger("racestuf")

FORMAT_VERSION = 1

#: Entry 7: 13 records of `TRAIT_COUNT` bytes (orion2_consts.h:949-980).
TRAIT_ENTRY, RACE_COUNT, TRAIT_COUNT = 7, 13, 31
#: `Load_Player_Special_Names_` reads entry `_settings.language + 8`
#: (loader.cpp:107-108) and walks 32 names (:113-126).
NAME_ENTRY = {"en": 8, "de": 9, "fr": 10, "es": 11, "it": 12}
NAME_COUNT = 32

#: Trait indices (orion2_consts.h:949-980).
TRAIT_GOVERNMENT, TRAIT_FOOD, TRAIT_TAX, TRAIT_LOW_G = 0, 2, 5, 10
TRAIT_RICH_HOME = 15            # a negative byte is Poor Home World

#: `MOX::_special_bonus[9][3]` (mox.cpp:759-769) — a table in the engine,
#: not in the LBX, so it is transcribed: row = trait - 1, column =
#: level - 1.
SPECIAL_BONUS = (
    (-50, 50, 100), (-1, 2, 4), (-1, 1, 2), (-1, 1, 2), (-1, 1, 2),
    (-20, 25, 50), (-20, 20, 50), (-10, 10, 20), (-10, 10, 20),
)

#: ESTRINGS index of `_government_labels[0]` (estrings.cpp:99).
GOVERNMENT_ESTRING = 0x27C

HOW = "python tools/racestuf_extract.py"


def string_file(language="en"):
    """Where the extractor writes and the loader reads."""
    return os.path.join("assets", "shared", "names",
                        f"racestuf_{language}.json").replace(os.sep, "/")


def bonus_text(trait, level):
    """The value the original appends to a bonus trait's name
    (race_display.cpp:95-117), with its "+" — or None for a level the
    table does not hold."""
    if not (1 <= trait <= len(SPECIAL_BONUS) and 1 <= level <= 3):
        return None
    bonus = SPECIAL_BONUS[trait - 1][level - 1]
    # `raceopt::Format_Numeric_Trait` (raceopt_display.cpp:4-21, the v2 text
    # the engine prints now): a sign, the magnitude, for Food and Tax the
    # magnitude / 2 with ".5" when odd, " BC" after the Tax; WO 428 (this
    # followed the 1.60 text: -1 Food read "0", a negative Tax had no sign)
    sign = "-" if bonus < 0 else "+"
    magnitude = abs(bonus)
    if trait in (TRAIT_FOOD, TRAIT_TAX):
        text = f"{magnitude // 2}{'.5' if magnitude % 2 else ''}"
        return sign + text + (" BC" if trait == TRAIT_TAX else "")
    return sign + str(magnitude)


class RaceTraits:
    """The loaded records and names, or a stated absence. Never an
    exception. `state` is "ok", "missing" or "stale"."""

    def __init__(self, language="en", root=None):
        self.language = language
        self.state = "missing"
        self.records = []
        self.names = []
        self._load(root or BASE_DIR)

    def _load(self, root):
        path = os.path.join(root, *string_file(self.language).split("/"))
        data, stale = derivedjson.load(path, log, "racestuf", HOW, HOW,
                                       FORMAT_VERSION)
        if stale:
            self.state = "stale"
        if data is None:
            return
        records = [list(r) for r in data.get("records", [])]
        names = list(data.get("names", []))
        if (len(records) != RACE_COUNT
                or any(len(r) != TRAIT_COUNT for r in records)
                or len(names) != NAME_COUNT):
            log.warning("racestuf: %s holds %d records and %d names, the "
                        "original reads %d of %d bytes and %d names — "
                        "re-run %s", path, len(records), len(names),
                        RACE_COUNT, TRAIT_COUNT, NAME_COUNT, HOW)
            return
        self.records, self.names = records, names
        self.state = "ok"

    @property
    def available(self):
        return self.state == "ok"

    def traits(self, race_id, estrings=None):
        """The original's list for one stock race, in its order, as
        Select Race's rows: `{"name", "value", "good"}`, the government
        last with `"government": True`. [] when nothing is loaded or the
        race is not a stock race (the Custom Race cell).

        `good` is the bonus's sign for a bonus trait and None otherwise:
        the original colours none of them (HD STATE `trait_colour`).
        """
        if not self.available or not 0 <= int(race_id) < RACE_COUNT:
            return []
        record = self.records[int(race_id)]
        rows = []
        for trait in range(1, TRAIT_LOW_G):
            level = record[trait]
            if level == 0:
                continue
            value = bonus_text(trait, level) or ""
            bonus = (SPECIAL_BONUS[trait - 1][level - 1]
                     if 1 <= level <= 3 else 0)
            rows.append({"name": self.names[trait], "value": value,
                         "good": bonus > 0 if bonus else None,
                         "trait": trait})
        for trait in range(TRAIT_LOW_G, TRAIT_COUNT):
            # any non-zero byte is listed (race_display.cpp:~120-127, not
            # only 1), and a Rich Home World byte below zero is named by the
            # 32nd name, Poor Home World (WO 428)
            if record[trait] != 0:
                name = (self.names[TRAIT_COUNT]
                        if trait == TRAIT_RICH_HOME and record[trait] < 0
                        and len(self.names) > TRAIT_COUNT
                        else self.names[trait])
                # a Poor Home World has an id of its own (31): the icon and
                # the tip are looked up by it (`racepanel`, `traittip`)
                poor = trait == TRAIT_RICH_HOME and record[trait] < 0 and \
                    len(self.names) > TRAIT_COUNT
                rows.append({"name": name, "value": "", "good": None,
                             "trait": TRAIT_COUNT if poor else trait})
        government = None
        if estrings is not None:
            government = estrings.string(GOVERNMENT_ESTRING + record[0])
        rows.append({"name": "Government", "value": government or "",
                     "good": None, "government": True,
                     "gov_id": record[0]})
        return rows


def for_app(app):
    """One `RaceTraits` per App and language, built on first use — the
    pattern of `core.skildesc.for_app` (one construction site, D17)."""
    cached = getattr(app, "_racestuf", None)
    language = (getattr(app, "settings", {}) or {}).get("language", "en")
    if cached is None or cached.language != language:
        cached = RaceTraits(language)
        app._racestuf = cached
    return cached
