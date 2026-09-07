"""The original's ESTRINGS table, loaded from a derived file.

**THE THIRD USE OF THE HELP-TEXT PATTERN** (decision 38), after the
help texts themselves and the building names: the strings are not in
the orion2re source, they are in the player's own installation, so
`tools/estrings_extract.py` moves the bytes out untouched and this
module decodes at load time. Format version, never committed,
`setup.py` step, absence a state the caller explains.

**A DIFFERENT FILE AND A DIFFERENT WALK FROM TECHNAME.** The two look
alike and are not, and reusing one for the other mis-indexes it:

  TECHNAME   ONE file, and the LANGUAGE picks the ENTRY. The walk
             (`Advance_To_Next_String_`, techinit.cpp:11-21) skips to
             the next NUL and then skips EVERY NUL after it, so a run
             of NULs is one separator and an empty string cannot
             exist.
  ESTRINGS   The LANGUAGE picks the FILE — estrings / estrGERM /
             estrFREN / estrSPAN / estrITAL / estrPOLI — and it is
             always ENTRY 0. The walk (`Load_E_Strings_`,
             estrings.cpp:33-36) is `current += strlen(current) + 1`
             with NO run-skipping, so **an empty string is a valid
             entry** and consuming a run of NULs would shift every
             index after the first gap.

`ESTRINGS_COUNT` is 812 (estrings.h:4) and the loader walks exactly
that many, which is the second source for the count: it is asserted
against the file rather than taken from it.

WHAT READS IT. `COLBLDG::Option_String_` (colbldg.cpp:2338) resolves
every production OPTION through `E_Strings_` — Trade Goods is
`E_Strings_(0x21D)` — and that is the branch of
`COLBLDG::Selection_Name_` (colbldg.cpp:796-802) the reference save
takes on every row. Buildings take the other branch and come from
`core.buildnames`; the two loaders read different files and a check
asserts neither reaches for the other's.
"""
import json
import logging
import os

from core.config import BASE_DIR

log = logging.getLogger("estrings")

#: Bumped when the extractor's output shape changes. A body an older
#: extractor wrote renders almost right, which is worse than not
#: loading at all — decision 38's own lesson.
FORMAT_VERSION = 1

#: estrings.h:4. The loader walks exactly this many strings, so a
#: file that yields fewer is refused rather than half-read.
ESTRINGS_COUNT = 812

#: `COLBLDG::Option_String_` (colbldg.cpp:2338), case for case, with
#: the ids from `COLONY_PRODUCTION_ID` (orion2_consts.h:65-84). The
#: three that share `E_Strings_(0x00C)` share it in the source too.
OPTION_STRINGS = {
    -1: 0x00C,    # NONE      \\
    -9: 0x00C,    # SEPARATOR  } one string, three ids
     0: 0x00C,    # 0         /
    -2: 0x21D,    # TRADE_GOODS
    -3: 0x142,    # HOUSING
    -4: 0x0B0,    # FARMER
    -5: 0x0B2,    # WORKER
    -6: 0x0B1,    # SCIENTIST
    -7: 0x1EC,    # SPY
    -8: 0x1BD,    # REFIT
    -10: 0x088,   # REPEAT
    -11: 0x21E,   # TRANSPORT_SHIP
    -12: 0x0E6,   # COLONY_SHIP
    -13: 0x0FA,   # CUSTOM_DESIGN
    -15: 0x12D,   # FREIGHTERS
    -16: 0x10F,   # DOOM_STAR
    -17: 0x195,   # OUTPOST_SHIP
}


def string_file(language="en"):
    """Where the extractor writes and the loader reads."""
    return os.path.join("assets", "shared", "names",
                        f"estrings_{language}.json")


class EStrings:
    """The loaded table, or a stated absence. Never an exception.

    `state` is "ok", "missing" or "stale", the same three the help
    loader distinguishes: an absent file and one an older extractor
    wrote are different problems with different fixes.
    """

    def __init__(self, language="en", root=None):
        self.language = language
        self.state = "missing"
        self.strings = {}
        self._load(root or BASE_DIR)

    def _load(self, root):
        path = os.path.join(root, *string_file(self.language).split("/"))
        if not os.path.exists(path):
            log.info("estrings: %s absent — run "
                     "`python tools/estrings_extract.py`", path)
            return
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (ValueError, OSError) as err:
            log.warning("estrings: %s will not load (%s)", path, err)
            return
        if int(data.get("format", 0)) < FORMAT_VERSION:
            self.state = "stale"
            log.warning("estrings: %s is format %s, this build reads %s "
                        "— re-run tools/estrings_extract.py",
                        path, data.get("format"), FORMAT_VERSION)
            return
        # A DENSE LIST of exactly ESTRINGS_COUNT entries, and the
        # length is CHECKED rather than trusted. An empty string is a
        # legitimate entry here — 0x00C is one — so "absent" cannot be
        # spelled as "falsy", and a short list would shift every
        # index after the gap while still looking like data.
        self.strings = list(data.get("strings", []))
        if len(self.strings) != ESTRINGS_COUNT:
            log.warning("estrings: %s holds %d strings, the loader "
                        "walks %d — re-run tools/estrings_extract.py",
                        path, len(self.strings), ESTRINGS_COUNT)
            self.strings = []
            return
        self.state = "ok"

    def string(self, index):
        """One ESTRINGS entry, or None when there is no such entry.

        None means NO SUCH ENTRY — out of range, or nothing loaded.
        A loaded entry that is blank comes back as `""`, because that
        is what the original returns for it and the caller has to be
        able to tell the two apart.
        """
        try:
            position = int(index)
        except (TypeError, ValueError):
            return None
        if not 0 <= position < len(self.strings):
            return None
        return self.strings[position]

    def option(self, production_id):
        """`Option_String_`'s answer for a production id, or None.

        None for an id the switch does not name — a queued ship or a
        ship design, which `Selection_Name_` answers from the ship
        itself and not from this table.
        """
        entry = OPTION_STRINGS.get(int(production_id))
        return None if entry is None else self.string(entry)
