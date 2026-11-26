"""`COLCALC::Colony_Can_Build_Product` for a SHIP, off the wire (work order 437, F4).

TRANSCRIPTION, `colcalc.cpp:3130-3160` (the ship branch of the function):

    ship_range == 0 or ship_speed == 0 (the owner's)             -> no
    combat:  size < minimum_orbital_base_ship_class              -> yes
             else no star base / fortress / battlestation        -> no
                  (`Colony_Can_Build_Large_Ships`, :2768-2775)
             else size 4 (Titan)     needs TECH_APP_TITAN_CONSTRUCTION
                  size 5 (Doom Star) needs TECH_APP_DOOM_STAR_CONSTRUCTION
                  smaller            -> yes
    colony:    TECH_APP_COLONY_SHIP researched
    transport: Marine Barracks in the colony and TECH_APP_TRANSPORT researched
    outpost:   TECH_APP_OUTPOST_SHIP researched
    anything else                                                -> no

Every input is on the wire: the owner's `ship_range`, `ship_speed` and
`tech_applications` (core/structs/player.py), the design's or ship's
`size` and `ship_type`, the colony's `buildings`. The build popup's dim
(`colbldg.cpp:697-755`) and the refit cell's "NO STAR BASE" word
(`colrefit.cpp:417-427`, E 0x18B) both ask this one question.

OMISSION `config_minimum_orbital_base_ship_class`: the engine reads the
size from which a base is needed from its config
(`colcalc_config.cpp:257`, default `SHIP_SIZE_LARGE`); no wire block
reports the effective value, so the default stands here. UNVERIFIED with
a modded config. Wished from the engine: one `can_build` byte per BLDL
entry and per RFIT ship (the engine calls this function for both anyway),
which would make this module a fallback.

OMISSION `ship_row_special`: the special ship rows (Transport, Colony
Ship, Custom Design, Outpost Ship, Doom Star), dimmed by
`Auto_Design_Type` (`colbldg.cpp:742-752`), are not transcribed.
"""
SHIP_SIZE_LARGE = 2
SHIP_SIZE_TITAN, SHIP_SIZE_DOOM_STAR = 4, 5
SHIP_TYPE_COMBAT, SHIP_TYPE_COLONY, SHIP_TYPE_TRANSPORT = 0, 1, 2
SHIP_TYPE_OUTPOST = 4
#: the config default; see OMISSION `config_minimum_orbital_base_ship_class`
MINIMUM_ORBITAL_BASE_SHIP_CLASS = SHIP_SIZE_LARGE

#: orion2_consts.h:743, :757, :811, :888, :891 and :1394
TECH_APP_COLONY_SHIP = 41
TECH_APP_DOOM_STAR_CONSTRUCTION = 55
TECH_APP_OUTPOST_SHIP = 109
TECH_APP_TITAN_CONSTRUCTION = 186
TECH_APP_TRANSPORT = 189
TECH_RESEARCH_STATUS_RESEARCHED = 3

#: BUILDING_BATTLESTATION, BUILDING_MARINE_BARRACKS, BUILDING_STAR_BASE,
#: BUILDING_STAR_FORTRESS (orion2_consts.h:23, :37, :55, :56)
BUILDING_BATTLESTATION = 8
BUILDING_MARINE_BARRACKS = 22
BASES = (40, 41, 8)


def has_base(buildings):
    """`Colony_Can_Build_Large_Ships` (colcalc.cpp:2768-2775)."""
    return any(0 <= b < len(buildings) and buildings[b] for b in BASES)


def can_build(player, buildings, ship_type, size):
    """True/False, or None when the owner's record is too short to say
    (a stand-in or an early frame): the caller then does not dim."""
    if player is None:
        return None
    try:
        rng, speed = int(player.ship_range), int(player.ship_speed)
        apps = list(player.tech_applications)
    except (AttributeError, TypeError, ValueError):
        return None
    if rng == 0 or speed == 0:
        return False

    def researched(app):
        return (0 <= app < len(apps) and
                apps[app] == TECH_RESEARCH_STATUS_RESEARCHED)

    ship_type, size = int(ship_type), int(size)
    if ship_type == SHIP_TYPE_COMBAT:
        if size < MINIMUM_ORBITAL_BASE_SHIP_CLASS:
            return True
        if not has_base(buildings):
            return False
        if size == SHIP_SIZE_TITAN:
            return researched(TECH_APP_TITAN_CONSTRUCTION)
        if size == SHIP_SIZE_DOOM_STAR:
            return researched(TECH_APP_DOOM_STAR_CONSTRUCTION)
        return True
    if ship_type == SHIP_TYPE_COLONY:
        return researched(TECH_APP_COLONY_SHIP)
    if ship_type == SHIP_TYPE_TRANSPORT:
        return bool(0 <= BUILDING_MARINE_BARRACKS < len(buildings) and
                    buildings[BUILDING_MARINE_BARRACKS]) and \
            researched(TECH_APP_TRANSPORT)
    if ship_type == SHIP_TYPE_OUTPOST:
        return researched(TECH_APP_OUTPOST_SHIP)
    return False
