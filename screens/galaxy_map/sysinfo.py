"""The star system window's planet information — work order 226 F.

Data's decision 5 of 9 October 2026: while the pointer is over a planet the
window shows the planet's information as the original does.

TRANSCRIPTION of `SYS::Do_Print_Planet_Info_` (sys.cpp:1326-1533), drawn
while the planet is scanned (`Draw_System_Display_Popup_`, :824-844) in a
darkened box at the window's content corner (`MISC::Draw_Darkened_Box_`,
:841). Every word is the player's own (ESTRINGS through `planetwords`,
HESTRNGS, the building names), every number off the wire — nothing needs
the engine:

  gas giant / asteroids   H 0x15F / H 0x160 alone
  the name                the planet's name without "Prime" and, for a
                          colony, "(" + its owner's race name + ")" — H 0x161
                          in place of ")" for an outpost
  size, climate           the colony's climate where there is one
  population              H 0x181 (n pops, maximum) for a colony, H 0x162
                          (maximum) otherwise; the maximum is the LOCAL
                          player's (`Planet_Max_Population_For_Player_`;
                          `colonyrows.max_population`, with its two marked
                          deviations)
  minerals[, gravity]     gravity only when it is not normal
  the orbit               star fortress, star base, battlestation, missile
                          base, ground batteries, stellar converter, fighter
                          garrison — where the colony has them and the
                          player has a ship or colony in the system or
                          Omniscience (`Print_Special_Building_Data_`,
                          :1056-1106), after a gap
  the special             the planet's special, unless none or Orion's
                          (11), after a gap where no building stood
"""
from core.structs import colony as colony_struct
from core.structs import planet as planet_struct
from core.structs import player as player_struct
from core.structs import ship as ship_struct
from core.structs import star as star_struct
from screens.colony_summary import colonyrows
from screens.planets import planetwords

PLANET_TYPE_ASTEROID, PLANET_TYPE_GAS_GIANT = 1, 2
GRAVITY_NORMAL = 1
H_GAS_GIANT, H_ASTEROIDS, H_OUTPOST, H_MAX_ONLY, H_POP = \
    0x15F, 0x160, 0x161, 0x162, 0x181
#: `Print_Special_Building_Data_`'s order (sys.cpp:1065-1073).
ORBIT_BUILDINGS = (41, 40, 8, 26, 27, 42, 47)
TRAIT_OMNISCIENCE = 27            # orion2_consts.h:976
SPECIAL_NONE, SPECIAL_ORION = 0, 11


def _fmt(template, *values):
    try:
        return (template or "") % values
    except (TypeError, ValueError):
        return template or ""


def lines(state, planet_index, words, buildings):
    """[(text, gap_before)] the box prints for planet `planet_index`, or
    [] when the wire cannot name it. `words`: `planetwords.Words`;
    `buildings`: `core.buildnames.BuildingNames`."""
    planets = getattr(state, "planets_raw", None) or []
    if not 0 <= planet_index < len(planets):
        return []
    planet = planet_struct.parse(planets[planet_index])
    if int(planet.planet_type) == PLANET_TYPE_GAS_GIANT:
        return [(words.h(H_GAS_GIANT) or "", 0)]
    if int(planet.planet_type) == PLANET_TYPE_ASTEROID:
        return [(words.h(H_ASTEROIDS) or "", 0)]
    colonies = getattr(state, "colonies_raw", None) or []
    ci = int(planet.colony_index)
    colony = colony_struct.parse(colonies[ci]) \
        if 0 <= ci < len(colonies) else None
    players = getattr(state, "player_raw", None) or []
    me = int(getattr(state, "player_num", 0) or 0)
    stars = getattr(state, "stars", None) or []
    star = stars[planet.star_index] if 0 <= planet.star_index < len(stars) \
        else None
    name = colonyrows.star_planet_name(star, planet_index) if star else "?"
    title = f"{name} "
    if colony is not None:
        owner = int(colony.owner)
        race = player_struct.parse(players[owner]).race_name \
            if 0 <= owner < len(players) else ""
        title += f"({race}"
        title += (words.h(H_OUTPOST) or ")") if colony.outpost_flag else ")"
    climate = int(colony.climate) if colony is not None else \
        int(planet.climate)
    size_word = planetwords._pick(planetwords.SIZE_WORDS, int(planet.size))
    climate_word = planetwords._pick(planetwords.CLIMATE_WORDS, climate)
    out = [(title, 0),
           (f"{words.e(size_word) or ''}, {words.e(climate_word) or ''}", 0)]
    traits = player_struct.traits(player_struct.parse(players[me])) \
        if 0 <= me < len(players) else None
    stand_in = colony if colony is not None else _bare_colony(planet)
    maximum = colonyrows.max_population(stand_in, planet, traits)
    if colony is not None:
        out.append((_fmt(words.h(H_POP), int(colony.n_pops), maximum), 0))
    else:
        out.append((_fmt(words.h(H_MAX_ONLY), maximum), 0))
    mineral = words.e(planetwords._pick(planetwords.MINERAL_WORDS,
                                        int(planet.mineral_class))) or ""
    if int(planet.gravity_class) == GRAVITY_NORMAL:
        out.append((mineral, 0))
    else:
        gravity = words.e(planetwords._pick(planetwords.GRAVITY_WORDS,
                                            int(planet.gravity_class))) or ""
        out.append((f"{mineral}, {gravity}", 0))
    built = 0
    if colony is not None and _may_see_orbit(state, planet, me, traits):
        for b in ORBIT_BUILDINGS:
            if colony.buildings[b]:
                out.append((buildings.building(b) or "", 1 if not built else 0))
                built += 1
    special = int(planet.planet_special)
    if special not in (SPECIAL_NONE, SPECIAL_ORION):
        out.append((words.e(planetwords._pick(planetwords.SPECIAL_WORDS,
                                              special)) or "",
                    0 if built else 1))
    return out


def _bare_colony(planet):
    """A colony-shaped stand-in for an unsettled planet: its climate, no
    buildings — what `max_population` reads."""
    class _Bare:
        climate = int(planet.climate)
        buildings = [0] * 64
    return _Bare()


def _may_see_orbit(state, planet, me, traits):
    """`can_show_special_buildings` (sys.cpp:1343-1349): a ship of the
    player's in the system, a colony of the player's there, or
    Omniscience."""
    if traits and len(traits) > TRAIT_OMNISCIENCE and \
            traits[TRAIT_OMNISCIENCE]:
        return True
    star = planet.star_index
    for raw in getattr(state, "colonies_raw", None) or []:
        c = colony_struct.parse(raw)
        if int(c.owner) == me and 0 <= c.planet < len(
                getattr(state, "planets_raw", None) or []):
            p = planet_struct.parse(state.planets_raw[c.planet])
            if p.star_index == star:
                return True
    for raw in getattr(state, "ships_raw", None) or []:
        if len(raw) < ship_struct.SIZE:
            continue
        s = ship_struct.parse(raw)
        if int(s.owner) == me and int(s.status) < 3 and \
                int(s.location) == star:
            return True
    return False


def owner_colour(state, planet_index):
    """The colour index of the planet's colony owner (`Draw_System_
    Highlight_`, sys.cpp:599-633), or None for an unsettled planet."""
    planets = getattr(state, "planets_raw", None) or []
    if not 0 <= planet_index < len(planets):
        return None
    ci = int(planet_struct.parse(planets[planet_index]).colony_index)
    colonies = getattr(state, "colonies_raw", None) or []
    players = getattr(state, "player_raw", None) or []
    if not 0 <= ci < len(colonies):
        return None
    owner = int(colony_struct.parse(colonies[ci]).owner)
    if not 0 <= owner < len(players):
        return None
    return int(player_struct.parse(players[owner]).color)
