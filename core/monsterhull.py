"""A space monster's hull points — transcribed, with a checker.

Hull points are NOT on the wire. The engine computes them when a combat
starts, from two places, and this module is a copy of both:

  `INITSHIP::Get_Ship_Structure_` (initship.cpp:586-632) keys on the
  design's BUILDER, `d.previous_owner`: up to 9 it hands over to
  `Get_Design_Structure_`; 10..14 are fixed numbers, one pair per type,
  the smaller one when `d.ftl_type <= 0` (the stationary start monster)
  and the larger one otherwise (the event monster, which has a drive).

  `Get_Design_Structure_` (initship.cpp:821-841) and
  `Get_Ship_Armor_Hits_` (initship.cpp:569-584) read the hull table and
  the armour table (techdata.cpp:15-23, :77-87). That is the Guardian's
  path — builder 9, Titan hull, Xentronium — and it gives 800 structure
  and 800 armour.

**A COPY IS ONLY LEGITIMATE WITH A CHECKER** (brief, B.2 item 4): a
change in orion2re would leave these numbers quietly wrong on a panel
that looks right. `tools/monster_hull_check.py` reads initship.cpp,
techdata.cpp and orion2_consts.h and fails on any difference, and the
smoke test runs it whenever the orion2re tree is on this disk.

**TACTICAL VALUES ONLY** (Data's decision, 14 September 2026). With the
strategic combat setting `Get_Design_Structure_` returns the hull's
`strat_hits` instead, and `AIPOWER::Max_Ship_Hits_` adds armour as a
bonus — AI heuristics, not player information. Neither is shown.

**ARMOUR IS ITS OWN LINE, and for the five monsters it is 0**: their
templates carry `ARMOR_NO_ARMOR`, whose ships bonus is -100, so
`armor_hp * -100 / 100 + armor_hp` is exactly zero. Combat takes armour
first, which is why structure and armour are two numbers and not a sum.
"""

#: Builders up to this value take the design path (initship.cpp:592).
DESIGN_BUILDER_MAX = 9

#: builder -> (structure without drive, structure with drive),
#: initship.cpp:596-625 — `case N: result = <with>; if (ftl_type <= 0)
#: return <without>;`.
MONSTER_STRUCTURE = {
    10: (400, 750),       # Amoeba
    11: (500, 2500),      # Crystal
    12: (500, 2500),      # Dragon
    13: (300, 1000),      # Eel
    14: (500, 1500),      # Hydra
}

#: `_hull_data[HULL_CLASS_COUNT]` (techdata.cpp:78-86), the columns
#: `armor_hp` and `structure_hp` (s_tech_hull_data, techdata.h:90-107).
HULL_ARMOR_HP = (4, 10, 30, 50, 80, 150, 60, 90, 120)
HULL_STRUCTURE_HP = (4, 10, 30, 50, 80, 150, 60, 90, 120)

#: `_armor[ARMOR_COUNT].ships_bonus` (techdata.cpp:16-22), per cent.
ARMOR_SHIPS_BONUS = (-100, 0, 100, 300, 500, 700, 900)

#: orion2_consts.h:553 and :566 — bit indices into special_device_flags.
SPECIAL_HEAVY_ARMOR = 14
SPECIAL_REINFORCED_HULL = 27

START, EVENT = "start", "event"


def _cdiv(a, b):
    """C integer division: truncates toward zero. Python's // floors, which
    is the same for the positive products here and would differ by one for
    a negative one that does not divide."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def _bit(view, index):
    flags = view.special_device_flags
    return (flags[index >> 3] >> (index & 7)) & 1


def _table(table, index):
    return table[index] if 0 <= index < len(table) else None


def stage(view):
    """START or EVENT for the five fixed-table monsters, None otherwise.

    The one distinction the templates make (SHIP_CONFIG [0] and [1],
    ship_config.cpp:86-139), and it is the same test Get_Ship_Structure_
    makes: no drive is the start monster."""
    if int(view.previous_owner) not in MONSTER_STRUCTURE:
        return None
    return START if view.ftl_type <= 0 else EVENT


def structure(view):
    """`Get_Ship_Structure_` for the tactical game, or None for a builder
    the switch has no case for (its `result` is uninitialised there)."""
    builder = int(view.previous_owner)
    if builder <= DESIGN_BUILDER_MAX:
        base = _table(HULL_STRUCTURE_HP, view.size)
        bonus = _table(ARMOR_SHIPS_BONUS, view.armor_type)
        if base is None or bonus is None:
            return None
        total = base + _cdiv(bonus * base, 100)
        if _bit(view, SPECIAL_REINFORCED_HULL):
            total *= 3
        return total
    pair = MONSTER_STRUCTURE.get(builder)
    if pair is None:
        return None
    return pair[0] if view.ftl_type <= 0 else pair[1]


def armour(view):
    """`Get_Ship_Armor_Hits_`: the hull's armour points scaled by the armour
    type's ships bonus, tripled by Heavy Armor. Every ship, every builder."""
    base = _table(HULL_ARMOR_HP, view.size)
    bonus = _table(ARMOR_SHIPS_BONUS, view.armor_type)
    if base is None or bonus is None:
        return None
    total = _cdiv(bonus * base, 100) + base
    if _bit(view, SPECIAL_HEAVY_ARMOR):
        total *= 3
    return total
