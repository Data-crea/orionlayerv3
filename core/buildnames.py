"""The original's building names, loaded from a derived file.

**THE SAME SHAPE AS THE HELP TEXTS** (decision 38): the names are not
in the orion2re source, they are in the player's own TECHNAME.LBX.
`tools/techname_extract.py` moves the bytes out untouched and this
module decodes at load time, so a fix here needs no re-extraction.
The file carries a format version, is never committed, and its
absence is a STATE THE SCREEN EXPLAINS — the BUILDING column shows the
"not extracted yet" wording rather than nothing.

WHERE THE NAMES COME FROM, and it is one entry, not one per string.
`TECHINIT::Load_Tech_Names_` (techinit.cpp:43) loads `techname.lbx`
entry `MOX::_settings.language` as ONE contiguous block of
NUL-separated strings and walks it with `Advance_To_Next_String_`
(techinit.cpp:11-21 — skip to the next NUL, then skip every NUL after
it) in a fixed order:

    string 0                      _technology_fields[0]
    strings 1 .. 82               _technology_fields[1 .. 82]
    strings 83 .. 294             _technology_applications[0 .. 211]
    strings 295 .. 343            _buildings[0 .. 48]      <- these
    then _specials, _armor, _shields, _weapons, ...

so building `id` is string `BUILDING_FIRST_STRING + id`. The three
counts are `orion2_consts.h` enums with `static_assert`s beside them
(TECH_FIELD_COUNT 83, TECH_APP_COUNT 212, BUILDING_COUNT 49), which
is the second source for the offset: it is not measured off the
file, it is computed from the constants the game itself asserts.

WHAT THE COLONY RECORD CARRIES. `colony->producing[0]`, drawn through
`COLBLDG::Selection_Name_` (colbldg.cpp:796): a BUILDING id goes to
`COLONY::Real_Building_Name_` (colony.cpp:185), which is
`TECHDATA::_buildings[id].name`. A queued ship or an option id takes
another branch and is NOT a building name — `is_building` says which,
and this module answers None for the rest rather than guessing.
"""
import json
import logging
import os

from core.config import BASE_DIR

log = logging.getLogger("buildnames")

#: Bumped when the extractor's output shape changes. A file written by
#: an older extractor renders ALMOST right, which is worse than not
#: loading at all — the help texts' lesson (decision 38).
FORMAT_VERSION = 1

#: orion2_consts.h:945, :857, :62, each with a static_assert.
TECH_FIELD_COUNT = 83
TECH_APP_COUNT = 212
BUILDING_COUNT = 49

#: orion2_consts.h:13. **NOT A BUILDING**, and the constant is named
#: here rather than written as 0 because that is the whole of the
#: correction below: `Colony_Production_Is_Building_` compares against
#: this name, and a literal 0 in an `is_building` is what let the
#: bound drift in the first place.
BUILDING_NO_BUILDING = 0

#: The first building's index in the string walk: string 0 is
#: `_technology_fields[0]`, so the fields consume `TECH_FIELD_COUNT`
#: strings in total and the applications `TECH_APP_COUNT` after them.
BUILDING_FIRST_STRING = TECH_FIELD_COUNT + TECH_APP_COUNT


def name_file(language="en"):
    """Where the extractor writes and the loader reads."""
    return os.path.join("assets", "shared", "names",
                        f"buildings_{language}.json")


class BuildingNames:
    """Loaded names, or a stated absence. Never an exception.

    `state` is one of "ok", "missing", "stale" — the same three the
    help loader distinguishes, because "no file" and "a file an older
    extractor wrote" are different problems with different fixes and
    a screen that shows one message for both sends the reader to the
    wrong place.
    """

    def __init__(self, language="en", root=None):
        self.language = language
        self.state = "missing"
        self.names = {}
        self._load(root or BASE_DIR)

    def _load(self, root):
        path = os.path.join(root, *name_file(self.language).split("/"))
        if not os.path.exists(path):
            log.info("building names: %s absent — run "
                     "`python tools/techname_extract.py`", path)
            return
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (ValueError, OSError) as err:
            log.warning("building names: %s will not load (%s)", path, err)
            return
        if int(data.get("format", 0)) < FORMAT_VERSION:
            self.state = "stale"
            log.warning("building names: %s is format %s, this build "
                        "reads %s — re-run tools/techname_extract.py",
                        path, data.get("format"), FORMAT_VERSION)
            return
        self.names = {int(k): v for k, v in data.get("buildings", {}).items()}
        self.state = "ok" if self.names else "missing"

    def building(self, production_id):
        """The name for a colony's `producing[0]`, or None.

        None covers three different things and the caller treats them
        alike: nothing is being produced, the id is not a building
        (`Selection_Name_`'s other two branches), or the file is not
        there. What the SCREEN shows differs — see `colonybuild`.
        """
        if production_id is None or not is_building(production_id):
            return None
        return self.names.get(int(production_id))


def is_building(production_id):
    """Whether `producing[0]` names a building at all.

    **CORRECTED 7 September 2026, and it was a real defect.** This
    read `0 <= value < BUILDING_COUNT`. The original is

        production_id > BUILDING_NO_BUILDING &&
        production_id < BUILDING_COUNT                (colbldg.h:16)

    — id 0 is EXCLUDED. `Option_String_` claims it instead, with an
    explicit `case 0:` returning `E_Strings_(0x00C)`, the empty
    string (colbldg.cpp:2356-2359). So a colony producing 0 draws
    nothing in the original and would have drawn `_buildings[0].name`
    here, which the extracted table gives as "No Building".

    It could not be seen until `core.estrings` existed, because 0 was
    the ONE id both branches claimed and there was no second branch to
    disagree with. That is the argument for transcribing a function's
    neighbours and not only the function: the bound is in the
    predicate, and the predicate had never been read.
    """
    try:
        value = int(production_id)
    except (TypeError, ValueError):
        return False
    return BUILDING_NO_BUILDING < value < BUILDING_COUNT
