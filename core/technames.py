"""The original's research field and application names, from a derived file.

**THE SAME SHAPE AS THE BUILDING AND SHIP-PART NAMES**
(`core/buildnames.py`, `core/shipparts.py`, decision 38): not in the
orion2re source, but in the player's own TECHNAME.LBX.
`tools/techname_extract.py` writes `techfields_<lang>.json` beside
the other two; the file carries a format version, is never committed,
and its absence is a STATE THE SCREEN EXPLAINS rather than an error —
the research screen hands over to the fallback view and logs why.

WHERE THE NAMES ARE. They are the FIRST two tables of the block
`TECHINIT::Load_Tech_Names_` walks (techinit.cpp:43-160), before the
building names the same file already reads:

    string 0                _technology_fields[0], the unused row
    strings 1 .. 82         _technology_fields[1 .. 82]      <- read
    strings 83 .. 294       _technology_applications[0 .. 211] <- read
    strings 295 .. 343      _buildings[0 .. 48]
    then specials, armour, shields, weapons, ...

Both first indices are sums of counts `orion2_consts.h` asserts for
itself (TECH_FIELD_COUNT 83, TECH_APP_COUNT 212), not positions
measured off one file — which is what makes them a transcription.

TWO NAMES THIS FILE DOES NOT HOLD, both marked rather than guessed:

  - the HYPER-ADVANCED field title. Fields 75..82 are not named from
    this block at all: `Technology_Fields_Name_` (tech.cpp:1086-1099)
    returns `MOX::_hyper_field_title`, which is `E_Strings_(0x284)`
    (estrings.cpp:294) — already in `estrings_<lang>.json` and read
    through `core/estrings.py`. `field_name` goes there for them.
  - the ROMAN NUMERAL an application above id 203 carries
    (`Technology_Applications_Name_`, tech.cpp:1117-1136: the name,
    a space, then `_roman_literals[hyper + 1]`, mox.cpp:426). The
    numerals are static and are here as NUMERALS; the hyper count
    they index is `s_player.hyper_advanced_tech`, which is still
    unverified (`core/structs/unverified.py`), so `application_name`
    returns the bare name and says so through `hyper_suffix`.
"""
import json
import logging
import os

from core.config import BASE_DIR
from core.researchlist import FIELD_HYPER_FIRST

log = logging.getLogger("technames")

#: Bumped when the extractor's output shape changes (decision 38).
FORMAT_VERSION = 1

#: orion2_consts.h:945 and :857, each with a static_assert beside it.
TECH_FIELD_COUNT = 83
TECH_APP_COUNT = 212

#: The block's own order: field 0 is string 0, application 0 is the
#: string after the last field.
FIELD_FIRST_STRING = 0
APP_FIRST_STRING = FIELD_FIRST_STRING + TECH_FIELD_COUNT

#: `MOX::_roman_literals` (mox.cpp:426) — the suffix an application at
#: or above `TECH_APP_BIOLOGY` wears, indexed by hyper count + 1.
#: Static, so it is transcribed here and not extracted.
ROMAN_LITERALS = ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII",
                  "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI",
                  "XVII", "XVIII", "XIX", "XX")

#: `Technology_Applications_Name_` prints `%u` instead of a numeral
#: above twenty (tech.cpp:1117-1136).
ROMAN_MAX = 20


def name_file(language="en"):
    """Where the extractor writes and the loader reads."""
    return os.path.join("assets", "shared", "names",
                        f"techfields_{language}.json")


def roman(count):
    """The numeral for a hyper-advanced count, or its number above XX."""
    if count is None:
        return ""
    index = int(count) + 1
    if 0 <= index <= ROMAN_MAX:
        return ROMAN_LITERALS[index]
    return str(index)


class TechNames:
    """Loaded names, or a stated absence ("ok", "missing", "stale")."""

    def __init__(self, language="en", root=None):
        self.language = language
        self.state = "missing"
        self.fields = {}
        self.applications = {}
        self._load(root or BASE_DIR)

    def _load(self, root):
        path = os.path.join(root, *name_file(self.language).split("/"))
        if not os.path.exists(path):
            log.info("research names: %s absent — run "
                     "`python tools/techname_extract.py`", path)
            return
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (ValueError, OSError) as err:
            log.warning("research names: %s will not load (%s)", path, err)
            return
        if int(data.get("format", 0)) < FORMAT_VERSION:
            self.state = "stale"
            log.warning("research names: %s is format %s, this build reads "
                        "%s — re-run tools/techname_extract.py",
                        path, data.get("format"), FORMAT_VERSION)
            return
        self.fields = {int(k): v for k, v in data.get("fields", {}).items()}
        self.applications = {int(k): v
                             for k, v in data.get("applications", {}).items()}
        self.state = "ok" if self.fields and self.applications else "missing"

    def field_name(self, field):
        """A research field's name, or None.

        None above the hyper-advanced boundary as well as for an absent
        file: those eight are not named from this block (see the module
        docstring). The block DOES carry a string at 75 — "Biology" in
        the English file — and returning it would be a plausible wrong
        name, which is the worst kind. `Technology_Fields_Name_`
        (tech.cpp:1086-1099) returns `_hyper_field_title` there, and the
        caller reads it out of ESTRINGS.
        """
        if field is None:
            return None
        field = int(field)
        if not 1 <= field < FIELD_HYPER_FIRST:
            return None
        return self.fields.get(field)

    def application_name(self, app, hyper_count=None):
        """An application's name, with its numeral when one applies.

        `hyper_count` is `s_player.hyper_advanced_tech[field - 75]`,
        which is UNVERIFIED — pass None and the bare name comes back,
        which is what the screen does today.
        """
        if app is None:
            return None
        base = self.applications.get(int(app))
        if base is None or hyper_count is None:
            return base
        suffix = roman(hyper_count)
        return f"{base} {suffix}" if suffix else base
