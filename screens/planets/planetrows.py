"""Which planets the Planets list holds, and in which order.

TRANSCRIBED from `PLNTSUM::Filter_Explored_Planets_` (plntsum.cpp:976-1053)
and `Sort_Planet_Summary_` (:1216-1248), orion2re 1.60. No pygame, no
pixels: rows are plain dicts, and `planetwords` turns them into text.

**THE ORDER OF THE TESTS IS THE SOURCE'S**, and the first one is the trap
`core/structs/planet.py` warns about: `planet_type` is tested before
anything reads `colony_index`.

**THE RANGE TOGGLE IS A TRANSCRIPTION since work order 322 A3**:
`planetrange` computes `Star_In_Extended_Range_Of_Player_` (shipmove.cpp:327,
v2 :363) from `s_player.ship_range`, the treaties and each star's black-hole
bitmap, all on the wire; `FILTER_GAPS` is empty, and a smoke check fails if
the toggle goes inert while nothing marks it.

**OMNISCIENCE AND ADVANCED CITY PLANNING, work order 322 A2.** Omniscience
is `HAROLD::Player_Is_Omniscient_` whole (harold.cpp:765-775, v2 :708-718):
the trait OR a hired Galactic Lore leader, which the player record keeps as
`has_galactic_lore` (`player_struct.is_omniscient`); the explored bits the
enemy toggle also asks for are the trait's alone, as the source sets them
(`Set_Planet_Explored_Flags_`, plntsum.cpp:649-662). Advanced City Planning
adds `CITY_PLANNING_BONUS` when `tech_applications[3]` reads researched
(colcalc.cpp:927-929, :1021-1023; v2 :1017-1019, :1112-1114).
DEVIATION `city_planning_config`: v2 reads the bonus from its config
(`colony.pop_bonus.advanced_city_planning`, colcalc_config.cpp:79-82, 5 by
default); HD transcribes 1.60's 5, which is that default, and cannot read a
mod's other number. UNVERIFIED `lore_and_city_planning`: a live run would
show an unvisited system's planets after a lore leader is hired and every
max pop 5 higher after the research (no live runs, Data, 20 October 2026);
`has_galactic_lore`'s offset has no second source yet (`core/structs/
player.py`).
"""
from core.structs import colony as colony_struct
from core.structs import planet as planet_struct
from core.structs import player as player_struct
from core.structs import ship as ship_struct
from core.structs import star as star_struct
from core import colonyfacts

from . import planetrange

PLANET_TYPE_PLANET = 3                  # orion2_consts.h:404
MAX_PLAYERS = 8
MINERALS_PER_MINE = (1, 2, 3, 5, 8)     # COLCALC::_minerals_per_mine, colcalc.cpp:19
MINERAL_ULTRA_POOR, MINERAL_POOR = 0, 1
GRAVITY_LOW, GRAVITY_NORMAL, GRAVITY_HEAVY = 0, 1, 2
TRAIT_LOW_G_WORLD, TRAIT_HEAVY_G_WORLD = 10, 11   # orion2_consts.h:959-960
TRAIT_BIOSPHERE_BONUS = colonyfacts.POP_BONUS_BIOSPHERES
#: `Find_Ship_Stacks_` gives no node to a ship with status >= 3
#: (shipstak.cpp:56), so the enemy test's stack walk never sees one.
STACK_SKIP = ship_struct.STATUS_STACK_SKIP

#: The five toggles, in the original's field order and hotkeys 1-5
#: (Add_Plntsum_Fields_, plntsum.cpp:697-701).
FILTERS = ("enemy", "gravity", "hostile", "minerals", "range")
#: The toggles' state when the game starts: `filter_out_planets_out_of_range
#: = 1` is the one global that does not start at 0 (plntsum.cpp:19-20), so
#: the original's list opens limited to planets in range of a colony.
#: TRANSCRIPTION `range_default_on`.
DEFAULT_FILTERS = {key: key == "range" for key in FILTERS}
#: Toggles the game applies and this module does not — none since work
#: order 322 A3 built the range filter (`planetrange`). Kept, empty, because
#: a smoke check holds a toggle that changes nothing to an entry here.
FILTER_GAPS = {}

#: Advanced City Planning's application, status and bonus: one home,
#: `colonyrows` (DEVIATION `city_planning_config`, see the docstring).
TECH_APP_ADVANCED_CITY_PLANNING = colonyfacts.TECH_APP_ADVANCED_CITY_PLANNING
TECH_RESEARCH_STATUS_RESEARCHED = colonyfacts.TECH_RESEARCH_STATUS_RESEARCHED
CITY_PLANNING_BONUS = colonyfacts.CITY_PLANNING_BONUS

#: The three sort keys and the row value each sorts on, descending
#: (qsort_by_climate_ / _minerals_ / _max_population_, plntsum.cpp:1216-1230).
SORT_VALUES = {"climate": "climate", "minerals": "minerals", "size": "max_pop"}


def _parse_list(module, raws):
    """Parsed records, index-aligned; a short record is None, never skipped,
    because every other array indexes this one by position."""
    return [module.parse(r) if len(r) >= module.SIZE else None
            for r in (raws or [])]


class View:
    """The snapshot arrays the list reads, parsed once per refresh."""

    def __init__(self, state):
        self.player_num = int(getattr(state, "player_num", 0))
        self.planets = _parse_list(planet_struct,
                                   getattr(state, "planets_raw", None))
        self.colonies = _parse_list(colony_struct,
                                    getattr(state, "colonies_raw", None))
        self.players = _parse_list(player_struct,
                                   getattr(state, "player_raw", None))
        self.ships = _parse_list(ship_struct,
                                 getattr(state, "ships_raw", None))
        self.stars = list(getattr(state, "stars", None) or [])

    def colony(self, index):
        index = int(index)
        return self.colonies[index] if 0 <= index < len(self.colonies) else None

    def player(self, index):
        index = int(index)
        return self.players[index] if 0 <= index < len(self.players) else None

    def traits(self, index):
        view = self.player(index) if int(index) < MAX_PLAYERS else None
        return player_struct.traits(view) if view is not None else None

    def local_traits(self):
        return self.traits(self.player_num)


def omniscient(view):
    """`HAROLD::Player_Is_Omniscient_` for the local player: the trait or a
    Galactic Lore leader (`player_struct.is_omniscient`)."""
    local = view.player(view.player_num)
    return local is not None and player_struct.is_omniscient(local)


def visited(view, star_index):
    """`Planet_Has_Been_Visited_` (plntsum.cpp:376-384, v2 :376-386): the
    star's visited bit, or omniscience — the trait or a lore leader."""
    if not 0 <= star_index < len(view.stars):
        return False
    return (star_struct.visited_by(view.stars[star_index], view.player_num)
            or omniscient(view))


def explored(view, star_index):
    """The planet's bit in `_explored_bitmap`, set by
    `Set_Planet_Explored_Flags_` (plntsum.cpp:649-662) from the omniscience
    TRAIT or the visited bit — not from a lore leader, so with the enemy
    toggle on a planet only a leader reveals stays out (:1005-1008)."""
    if not 0 <= star_index < len(view.stars):
        return False
    local = view.player(view.player_num)
    return (star_struct.visited_by(view.stars[star_index], view.player_num)
            or (local is not None and player_struct.has_omniscience(local)))


def city_planning(view, player):
    """Has `player` researched Advanced City Planning?"""
    record = view.player(player) if 0 <= int(player) < MAX_PLAYERS else None
    return colonyfacts.city_planning(record)


def productivity_penalty(traits, gravity):
    """`Productivity_Penalty_` (plntsum.cpp:664-690), case for case."""
    low = bool(traits and traits[TRAIT_LOW_G_WORLD])
    heavy = bool(traits and traits[TRAIT_HEAVY_G_WORLD])
    if (low or not heavy) and gravity == GRAVITY_HEAVY:
        return 50
    if (low and gravity == GRAVITY_NORMAL) or (not low and gravity == GRAVITY_LOW):
        return 25
    return 0


def enemy_controlled(view, star_index):
    """`Planet_Is_Enemy_Controlled_` (plntsum.cpp:415-458): another owner's
    colony in the system, or any stacked ship at the star that is not ours.
    The stack walk visits every ship with status < 3 (shipstak.cpp:56) and
    compares the RAW location with the star index, as the source does."""
    star = view.stars[star_index] if 0 <= star_index < len(view.stars) else None
    if star is not None:
        for slot in star_struct.planet_indices(star):
            planet = view.planets[slot] if 0 <= slot < len(view.planets) else None
            if planet is None or planet.colony_index <= -1:
                continue
            colony = view.colony(planet.colony_index)
            if colony is not None and colony.owner != view.player_num:
                return True
    return any(s is not None and s.status < STACK_SKIP
               and s.location == star_index and s.owner != view.player_num
               for s in view.ships)


def monster_ship(view, star_index):
    """`HAROLD::Star_Guarded_By_Monster_` (harold.cpp:850): the ship with
    status 0 and owner >= 8 at the star, or None. The source walks the
    stacks; stacks are built in ship order, so the first match by ship
    index is the one it finds unless two monster owners share a star."""
    for ship in view.ships:
        if (ship is not None and ship.status == 0
                and ship.owner >= MAX_PLAYERS and ship.location == star_index):
            return ship
    return None


def monster_owner(view, star_index):
    """The owner of `monster_ship`, or None."""
    ship = monster_ship(view, star_index)
    return int(ship.owner) if ship is not None else None


def race_pop_limit(view, size, climate, race):
    """`Size_And_Climate_Race_Pop_Limit_` (colcalc.cpp): immune by trait, or
    race 8 always; the aquatic climate shift and the subterranean bonus only
    for a player index."""
    traits = view.traits(race) if race < MAX_PLAYERS else None
    immune = bool(traits[colonyfacts.TRAIT_ENVIRONMENT_IMMUNE]) if traits \
        else race == MAX_PLAYERS
    climate = colonyfacts.player_climate(int(climate), traits)
    factor = min(100, (25 if immune else 0)
                 + colonyfacts.CLIMATE_FACTOR[max(0, min(9, climate))])
    size = max(0, min(len(colonyfacts.SIZE_BASE) - 1, int(size)))
    limit = (factor * colonyfacts.SIZE_BASE[size] + 50) // 100
    if traits and traits[colonyfacts.TRAIT_SUBTERRANEAN]:
        limit += 2 * size + 2
    return limit


def max_population(view, planet):
    """`COLCALC::Planet_Max_Population_For_Player_` (colcalc.cpp:896-936,
    v2 :986-1025) for the local player. A settled (non-outpost) colony
    answers the best limit over the races living in it, each through
    `Colony_Race_Pop_Limit_` (colcalc.cpp:1012-1033, v2 :1103-1125): the
    COLONY OWNER's Advanced City Planning, then biospheres +2, capped at
    42; anything else answers the local player's limit with the LOCAL
    player's Advanced City Planning (colcalc.cpp:927-929), capped at 42."""
    colony = view.colony(planet.colony_index) if planet.colony_index != -1 \
        else None
    if colony is not None and not colony.outpost_flag:
        races = ({view.player_num} if colony.n_pops == 0 else
                 {int(colony.pop[i]) & 0x0F for i in range(colony.n_pops)})
        best = 0
        for race in races:
            limit = race_pop_limit(view, planet.size, colony.climate, race)
            if city_planning(view, int(colony.owner)):
                limit += CITY_PLANNING_BONUS
            if colony.buildings[colonyfacts.BUILDING_BIOSPHERES]:
                limit += TRAIT_BIOSPHERE_BONUS
            best = max(best, min(limit, colonyfacts.POP_LIMIT_CAP))
        return best
    limit = race_pop_limit(view, planet.size, planet.climate,
                           view.player_num)
    if city_planning(view, view.player_num):
        limit += CITY_PLANNING_BONUS
    return min(limit, colonyfacts.POP_LIMIT_CAP)


def planet_row(view, index, planet):
    """The values `Filter_Explored_Planets_` stores (plntsum.cpp:1029-1036)
    plus what the row print reads straight from the planet."""
    colony = view.colony(planet.colony_index) if planet.colony_index != -1 \
        else None
    owner = int(colony.owner) if colony is not None else -1
    owner_view = view.player(owner) if 0 <= owner < MAX_PLAYERS else None
    mineral = int(planet.mineral_class)
    return {
        "index": index,
        "star": int(planet.star_index),
        "owner": owner,
        "owner_color": (int(owner_view.color) if owner_view is not None
                        else None),
        "climate": int(planet.climate),
        "size": int(planet.size),
        "gravity": int(planet.gravity_class),
        "mineral_class": mineral,
        "minerals": (MINERALS_PER_MINE[mineral]
                     if 0 <= mineral < len(MINERALS_PER_MINE) else 0),
        "food": int(planet.food_per_farmer),
        "max_pop": max_population(view, planet),
        "penalty": productivity_penalty(view.local_traits(),
                                        int(planet.gravity_class)),
    }


def build_rows(view, filters):
    """Every row the original would list, in planet index order."""
    rows = []
    on = {key for key in FILTERS if filters.get(key)}
    for index, planet in enumerate(view.planets):
        if planet is None or planet.planet_type != PLANET_TYPE_PLANET:
            continue
        colony = view.colony(planet.colony_index) \
            if planet.colony_index != -1 else None
        if colony is not None and colony.owner == view.player_num:
            continue                          # Planet_Has_Players_Colony_
        if planet.colony_index > -1 and colony is not None \
                and colony.outpost_flag != 0:
            continue                          # Planet_Is_Outpost_Planet_
        star = int(planet.star_index)
        if not visited(view, star):
            continue
        # The enemy toggle ALSO requires the explored bit
        # (plntsum.cpp:1005-1008), set from the omniscience TRAIT or the
        # visited bit alone — a lore leader does not set it.
        if "enemy" in on and not explored(view, star):
            continue
        # The range toggle first, as the source tests it (plntsum.cpp:1013,
        # v2 :1012): `Planet_In_Range_Of_A_Colony_` (work order 322 A3).
        if "range" in on and not planetrange.star_in_range(
                view, star, view.player_num):
            continue
        if "gravity" in on and productivity_penalty(
                view.local_traits(), int(planet.gravity_class)) > 0:
            continue
        if "enemy" in on and enemy_controlled(view, star):
            continue
        if "hostile" in on and planet.food_per_farmer <= 0:
            continue
        if "minerals" in on and planet.mineral_class in (MINERAL_POOR,
                                                         MINERAL_ULTRA_POOR):
            continue
        rows.append(planet_row(view, index, planet))
    return rows


def sort_rows(rows, sort_key):
    """Descending on the key's value, STABLE — the original's qsort is not,
    so rows with equal keys may stand in a different order than the game's
    (Data's acceptance, brief 101: same set, same order between distinct
    keys)."""
    value = SORT_VALUES[sort_key]
    return sorted(rows, key=lambda row: -row[value])


class PlanetList:
    """The list and the original's rebuild rule.

    `Filter_Explored_Planets_` copies the new array in and re-sorts ONLY
    when the count changed (plntsum.cpp:1044-1049). A toggle only removes
    or only adds, so an unchanged count is an unchanged set, and the rows
    keep their order; their values are refreshed from the new snapshot.
    """

    def __init__(self, sort_key="climate"):
        self.sort_key = sort_key
        self.rows = []

    def refresh(self, view, filters):
        """Rebuild. True when the count changed (the caller clears the
        scanned field, as :1048 does)."""
        fresh = build_rows(view, filters)
        old = {row["index"]: n for n, row in enumerate(self.rows)}
        if len(fresh) == len(self.rows) and set(old) == {
                row["index"] for row in fresh}:
            self.rows = sorted(fresh, key=lambda row: old[row["index"]])
            return False
        changed = len(fresh) != len(self.rows)
        self.rows = sort_rows(fresh, self.sort_key)
        return changed

    def sort(self, sort_key):
        """A sort click re-sorts the CURRENT array (plntsum.cpp:2013-2018)."""
        self.sort_key = sort_key
        self.rows = sort_rows(self.rows, sort_key)

    def first_row_of_star(self, star_index):
        """`First_Planet_In_Summary_List_` (plntsum.cpp:536), or -1."""
        for n, row in enumerate(self.rows):
            if row["star"] == star_index:
                return n
        return -1
