"""The original's names for ship parts, loaded from a derived file.

**THE SAME SHAPE AS THE BUILDING NAMES** (`core/buildnames.py`, decision
38): not in the orion2re source, but in the player's own TECHNAME.LBX.
`tools/techname_extract.py` writes `shipparts_<lang>.json` beside
`buildings_<lang>.json`; the file carries a format version, is never
committed, and its absence is a state the Planets panel explains.

WHERE THE NAMES ARE. `TECHINIT::Load_Tech_Names_` (techinit.cpp:43-160)
walks ONE block of NUL-separated strings in a fixed order, every table
consuming its `_COUNT` from `orion2_consts.h`:

    fields 83, applications 212, buildings 49,
    specials 40     strings 344 .. 383   <- read
    armour 7        strings 384 .. 390   <- read
    shields 6       strings 391 .. 396   <- read
    weapons 46      strings 397 .. 442   <- read
    computers 6, drives 7, units 4, fuel 6, weapon mods 15,
    weapon mod plurals 15, weapon plurals 46,
    hull classes 9  strings 542 .. 550   <- read
    hull plurals 9  strings 551 .. 559   <- read (work order 175)

so every first index is a SUM OF CONSTANTS the game asserts, not a
position measured off one file. Checked against the English
TECHNAME.LBX on 14 September 2026: 295 "No Building", 384 "No Armor",
391 "No Shield", 397 "No Weapons", 437..442 "Dragon Breath" ..
"Caustic Slime", 542 "Frigate". No plural forms are read for the
Planets panel (Data's decision): it shows a count in its own column.
The HULL plurals are read since work order 175, for one reader: the
Leaders screen's fleet strip prints "%d %s, " with `_hull_data[i].name`
for one ship and `.size_name` for more (officer.cpp:2178-2184), and
`size_name` is the second hull table (techinit.cpp:147-157).
"""
import logging
import os

from core.buildnames import BUILDING_COUNT, BUILDING_FIRST_STRING
from core.config import BASE_DIR
from core import derivedjson

log = logging.getLogger("shipparts")

#: Bumped when the extractor's output shape changes (decision 38). 2 since
#: work order 175: the `hull_plurals` table.
FORMAT_VERSION = 2

#: orion2_consts.h — each an enum with, for specials, a static_assert.
SPECIAL_COUNT = 40
ARMOR_COUNT = 7
SHIELD_COUNT = 6
WEAPON_COUNT = 46
COMPUTER_COUNT = 6
DRIVE_COUNT = 7
UNIT_COUNT = 4
FUEL_COUNT = 6
WEAPON_MOD_COUNT = 15
HULL_CLASS_COUNT = 9

SPECIAL_FIRST_STRING = BUILDING_FIRST_STRING + BUILDING_COUNT
ARMOR_FIRST_STRING = SPECIAL_FIRST_STRING + SPECIAL_COUNT
SHIELD_FIRST_STRING = ARMOR_FIRST_STRING + ARMOR_COUNT
WEAPON_FIRST_STRING = SHIELD_FIRST_STRING + SHIELD_COUNT
HULL_FIRST_STRING = (WEAPON_FIRST_STRING + WEAPON_COUNT + COMPUTER_COUNT
                     + DRIVE_COUNT + UNIT_COUNT + FUEL_COUNT
                     + 2 * WEAPON_MOD_COUNT + WEAPON_COUNT)

#: key in the file -> (first string, count), in the walk's order.
TABLES = {
    "specials": (SPECIAL_FIRST_STRING, SPECIAL_COUNT),
    "armor": (ARMOR_FIRST_STRING, ARMOR_COUNT),
    "shields": (SHIELD_FIRST_STRING, SHIELD_COUNT),
    "weapons": (WEAPON_FIRST_STRING, WEAPON_COUNT),
    "hulls": (HULL_FIRST_STRING, HULL_CLASS_COUNT),
    "hull_plurals": (HULL_FIRST_STRING + HULL_CLASS_COUNT, HULL_CLASS_COUNT),
}

#: THE SHIP DESIGNER'S TABLES (work order 185) — the rest of the same walk
#: (techinit.cpp: after the weapons come the computers, drives, units, fuel,
#: the modification names and plurals and the weapon plurals, then the
#: hulls). OPTIONAL keys of the same file: a file written before 185 has
#: none of them and still loads "ok" for every screen that reads TABLES —
#: bumping FORMAT_VERSION would have made every player's file stale for the
#: Planets and Leaders screens until the extractor ran again. A reader of
#: these asks `has_design_names()`.
_AFTER_WEAPONS = WEAPON_FIRST_STRING + WEAPON_COUNT
_FUEL_FIRST = _AFTER_WEAPONS + COMPUTER_COUNT + DRIVE_COUNT + UNIT_COUNT
_MODS_FIRST = _FUEL_FIRST + FUEL_COUNT
DESIGN_TABLES = {
    "computers": (_AFTER_WEAPONS, COMPUTER_COUNT),
    "drives": (_AFTER_WEAPONS + COMPUTER_COUNT, DRIVE_COUNT),
    "fuel": (_FUEL_FIRST, FUEL_COUNT),
    "weapon_mods": (_MODS_FIRST, WEAPON_MOD_COUNT),
    "weapon_mod_plurals": (_MODS_FIRST + WEAPON_MOD_COUNT, WEAPON_MOD_COUNT),
    "weapon_plurals": (_MODS_FIRST + 2 * WEAPON_MOD_COUNT, WEAPON_COUNT),
}
assert DESIGN_TABLES["weapon_plurals"][0] + WEAPON_COUNT == HULL_FIRST_STRING


def name_file(language="en"):
    """Where the extractor writes and the loader reads."""
    return os.path.join("assets", "shared", "names",
                        f"shipparts_{language}.json")


class ShipPartNames:
    """Loaded names, or a stated absence ("ok", "missing", "stale")."""

    def __init__(self, language="en", root=None):
        self.language = language
        self.state = "missing"
        self.tables = {key: {} for key in {**TABLES, **DESIGN_TABLES}}
        self._load(root or BASE_DIR)

    def _load(self, root):
        path = os.path.join(root, *name_file(self.language).split("/"))
        data, stale = derivedjson.load(path, log, "ship part names",
                                       "python tools/techname_extract.py",
                                       "tools/techname_extract.py", FORMAT_VERSION)
        if stale:
            self.state = "stale"
        if data is None:
            return
        for key in {**TABLES, **DESIGN_TABLES}:
            self.tables[key] = {int(k): v
                                for k, v in data.get(key, {}).items()}
        self.state = "ok" if all(self.tables[k] for k in TABLES) \
            else "missing"

    def has_design_names(self):
        """True when the Ship Designer's optional tables were extracted
        (a file from before work order 185 has none — re-run the
        extractor)."""
        return all(self.tables[k] for k in DESIGN_TABLES)

    def name(self, table, index):
        """The name, or None for an absent file or an index it lacks."""
        if index is None:
            return None
        return self.tables.get(table, {}).get(int(index))
