"""What a Planets row and the status line SAY.

TRANSCRIBED from `Summary_Screen_Print_Data_` (plntsum.cpp:49-205) and
`Summary_Screen_Print_Scanned_` (:1831-1926). The words come from the
user's own install, byte for byte (decision 38): ESTRINGS.LBX through
`core.estrings` for the climate, gravity, mineral, size, special and
monster race names — the indices are the ones `ESTRINGS::` assigns to
`MOX::_planet_climate_string` and its neighbours (estrings.cpp:14-33,
61-97, 204-213) — and HESTRNGS.LBX through `core.hestrings` for the three
lower-line templates and the status line.

**ABSENCE IS A STATE.** Without ESTRINGS a word is None and nothing is
drawn in its place; without HESTRNGS a lower line shows its bare number,
because the value is the snapshot's and only the wording is missing.
"""
from core import hestrings
from core.estrings import EStrings
from core.structs import star as star_struct
from screens.colony_summary import colonyrows

from . import planetrows

CLIMATE_WORDS = (0x21B, 0x2CF, 0x2D0, 0x2D1, 0x2D2,
                 0x18F, 0x1F5, 0x0B8, 0x2D3, 0x12F)   # estrings.cpp:204-213
SIZE_WORDS = (0x2AB, 0x1E0, 0x173, 0x168, 0x143)     # estrings.cpp:61-65
MINERAL_WORDS = (0x2AC, 0x1A7, 0x2AD, 0x1C2, 0x2AE)  # estrings.cpp:67-71
GRAVITY_WORDS = (0x2AF, 0x2B0, 0x2B1)                # estrings.cpp:73-75
SPECIAL_WORDS = tuple(range(0x2B9, 0x2C5))           # estrings.cpp:86-97
#: `HACCESS::Race_Name_` (haccess.cpp:683): owner 8 reads _race_names[13],
#: 9..14 read _race_names[owner + 5] (estrings.cpp:27-33).
RACE_NAME_WORDS = {8: 0x292, 9: 0x293, 10: 0x0AD, 11: 0x0F6,
                   12: 0x110, 13: 0x119, 14: 0x144}

H_PENALTY = 0x142        # "-%d%% prod",     plntsum.cpp:176
H_MAX_POP = 0x143        # "%d max pop",     plntsum.cpp:193
H_PROD_WORKER = 0x152    # "%d prod/worker", plntsum.cpp:185
H_BLACK_HOLE = 325       # plntsum.cpp:1880
H_UNEXPLORED = 148       # plntsum.cpp:1895

SPECIAL_SPACE_MONSTER, SPECIAL_ANCIENT_ARTIFACTS, SPECIAL_ORION_STAR = 9, 10, 11
#: `HACCESS::Special_Is_Planet_Special_` (haccess.cpp:639): gold, gems,
#: natives, splinter colony, ancient artifacts.
PLANET_SPECIALS = (4, 5, 6, 7, 10)


class Words:
    """The two string tables and the one literal the row print uses."""

    def __init__(self, estrings, hstrings, food_template="%s Food"):
        self.estrings = estrings
        self.hstrings = hstrings
        self.food_template = food_template

    @classmethod
    def load(cls, language, food_template):
        return cls(EStrings(language), hestrings.HStrings(language),
                   food_template)

    def e(self, index):
        text = self.estrings.string(index)
        return text or None

    def h(self, index):
        return self.hstrings.message(index)


def _pick(table, value):
    return table[value] if 0 <= value < len(table) else None


def food_text(food):
    """`COLCALC::Format_Food2` (colcalc_base.cpp:4) over the row's value
    cast to uint16_t (plntsum.cpp:150) — so a negative food value prints
    as the wrapped number, as the original's does."""
    value = int(food) & 0xFFFF
    return f"{value // 2}{'.5' if value % 2 else ''}"


def lower_line(words, h_index, value):
    template = words.h(h_index)
    return hestrings.printf(template, value) if template else str(value)


def race_name(view, owner, words):
    """`HACCESS::Race_Name_` (haccess.cpp:683), or None."""
    if 0 <= owner < planetrows.MAX_PLAYERS:
        player = view.player(owner)
        return player.race_name if player is not None else None
    if owner == planetrows.MAX_PLAYERS:
        return words.e(RACE_NAME_WORDS[owner])
    index = RACE_NAME_WORDS.get(owner)
    return words.e(index) if index is not None else None


def owner_label(view, row, words):
    """"(Race)" under the name: the colony owner's race, else the race of a
    monster guarding the star (plntsum.cpp:100-115); "" when neither."""
    if row["owner"] >= 0:
        name = race_name(view, row["owner"], words)
    else:
        monster = planetrows.monster_owner(view, row["star"])
        name = race_name(view, monster, words) if monster is not None else None
    return f"({name})" if name else ""


def special_line(view, row, words):
    """(text, pending) — the line above the name (plntsum.cpp:72-97).

    `pending` is True in the one branch HD cannot print: a planet special
    in a SPACE MONSTER system, where the original names the first ship
    orbiting the star (`s_ship_data.d.name`) — the design part of the
    ship spec is not verified, Data's decision, brief 101 Stop 1."""
    planet = view.planets[row["index"]]
    star = view.stars[row["star"]] if 0 <= row["star"] < len(view.stars) \
        else None
    if star is None:
        return "", False
    system = int(star.system_special)
    special = system if 0 < system != SPECIAL_ORION_STAR else 0
    if planet.planet_special == SPECIAL_ANCIENT_ARTIFACTS:
        special = SPECIAL_ANCIENT_ARTIFACTS
    if special <= 0 or special not in PLANET_SPECIALS:
        return "", False
    if system == SPECIAL_SPACE_MONSTER:
        return "", True
    if planet.planet_special == special:
        return words.e(SPECIAL_WORDS[special]) or "", False
    return "", False


def planet_name(view, row):
    star = view.stars[row["star"]] if 0 <= row["star"] < len(view.stars) \
        else None
    return colonyrows.star_planet_name(star, row["index"]) if star else "?"


def cells(view, row, words):
    """{column: ...} for one row. The planet column is a dict; the other
    four are (upper, lower) with lower None when the original prints one
    line — gravity without a penalty, which then sits half a line down
    (plntsum.cpp:171-179)."""
    special, pending = special_line(view, row, words)
    return {
        "planet": {"special": special, "special_pending": pending,
                   "name": planet_name(view, row),
                   "owner": owner_label(view, row, words)},
        "climate": (words.e(_pick(CLIMATE_WORDS, row["climate"])),
                    hestrings.printf(words.food_template,
                                     food_text(row["food"]))),
        "gravity": (words.e(_pick(GRAVITY_WORDS, row["gravity"])),
                    (lower_line(words, H_PENALTY, row["penalty"])
                     if row["penalty"] else None)),
        "minerals": (words.e(_pick(MINERAL_WORDS, row["mineral_class"])),
                     lower_line(words, H_PROD_WORKER, row["minerals"])),
        "size": (words.e(_pick(SIZE_WORDS, row["size"])),
                 lower_line(words, H_MAX_POP, row["max_pop"])),
    }


def status_line(view, scanned, words):
    """(text, status) for the scanned field, or None.

    The unarmed branch of `Summary_Screen_Print_Scanned_`: `scanned` is a
    star index + 1000. Black hole -> H 325 red; not visited -> H 148
    neutral; otherwise the star's name, neutral."""
    if scanned is None or scanned < 1000:
        return None
    star_index = scanned - 1000
    if not 0 <= star_index < len(view.stars):
        return None
    star = view.stars[star_index]
    if star_struct.is_black_hole(star):
        return words.h(H_BLACK_HOLE), "red"
    if not planetrows.visited(view, star_index):
        return words.h(H_UNEXPLORED), "neutral"
    return star.name, "neutral"
