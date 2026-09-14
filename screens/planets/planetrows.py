"""Which planets the Planets list holds, and in which order.

TRANSCRIBED from `PLNTSUM::Filter_Explored_Planets_` (plntsum.cpp:976-1053)
and `Sort_Planet_Summary_` (:1216-1248), orion2re 1.60. No pygame, no
pixels: rows are plain dicts, and `planetwords` turns them into text.

**THE ORDER OF THE TESTS IS THE SOURCE'S**, and the first one is the trap
`core/structs/planet.py` warns about: `planet_type` is tested before
anything reads `colony_index`.

**THE RANGE TOGGLE IS A MARKED GAP** (brief 101, Data's decision (c)). The
game filters on it; this module does not — `FILTER_GAPS` says so, and a
smoke check fails if that entry disappears while the filter is still
missing. `Star_In_Extended_Range_Of_Player_` (shipmove.cpp:327) needs
`s_player.ship_range`, the treaty table and the black-hole block bitmap,
none of them a verified spec (decision 23).

**TWO KNOWN DIFFERENCES FROM THE GAME, both too short rather than too
long:** Advanced City Planning's +5 is not applied to `max_pop`
(`tech_applications` is an anchor offset, not a decoded table — the same
deviation `colonyrows.max_population` states), and omniscience is read from
the racial trait only, so a Galactic Lore LEADER (which
`HAROLD::Player_Is_Omniscient_` also counts, harold.cpp:765) does not reveal
unvisited planets here.
"""
from core.structs import colony as colony_struct
from core.structs import planet as planet_struct
from core.structs import player as player_struct
from core.structs import ship as ship_struct
from core.structs import star as star_struct
from screens.colony_summary import colonyrows

PLANET_TYPE_PLANET = 3                  # orion2_consts.h:404
MAX_PLAYERS = 8
MINERALS_PER_MINE = (1, 2, 3, 5, 8)     # COLCALC::_minerals_per_mine, colcalc.cpp:19
MINERAL_ULTRA_POOR, MINERAL_POOR = 0, 1
GRAVITY_LOW, GRAVITY_NORMAL, GRAVITY_HEAVY = 0, 1, 2
TRAIT_LOW_G_WORLD, TRAIT_HEAVY_G_WORLD = 10, 11   # orion2_consts.h:959-960
TRAIT_BIOSPHERE_BONUS = colonyrows.POP_BONUS_BIOSPHERES
#: `Find_Ship_Stacks_` gives no node to a ship with status >= 3
#: (shipstak.cpp:56), so the enemy test's stack walk never sees one.
STACK_SKIP = ship_struct.STATUS_STACK_SKIP

#: The five toggles, in the original's field order and hotkeys 1-5
#: (Add_Plntsum_Fields_, plntsum.cpp:697-701).
FILTERS = ("enemy", "gravity", "hostile", "minerals", "range")
#: Toggles the game applies and this module does not. See the docstring.
FILTER_GAPS = {"range": "MARKED GAP - Planet_In_Range_Of_A_Colony_ needs "
                        "ship_range, treaties and black-hole blocks; its "
                        "own follow-up brief (brief 101, decision (c))"}

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


def visited(view, star_index):
    """`Planet_Has_Been_Visited_` (plntsum.cpp:376): the star's visited bit,
    or omniscience — from the trait only, see the module docstring."""
    if not 0 <= star_index < len(view.stars):
        return False
    local = view.player(view.player_num)
    return (star_struct.visited_by(view.stars[star_index], view.player_num)
            or (local is not None and player_struct.has_omniscience(local)))


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
    immune = bool(traits[colonyrows.TRAIT_ENVIRONMENT_IMMUNE]) if traits \
        else race == MAX_PLAYERS
    climate = colonyrows.player_climate(int(climate), traits)
    factor = min(100, (25 if immune else 0)
                 + colonyrows.CLIMATE_FACTOR[max(0, min(9, climate))])
    size = max(0, min(len(colonyrows.SIZE_BASE) - 1, int(size)))
    limit = (factor * colonyrows.SIZE_BASE[size] + 50) // 100
    if traits and traits[colonyrows.TRAIT_SUBTERRANEAN]:
        limit += 2 * size + 2
    return limit


def max_population(view, planet):
    """`COLCALC::Planet_Max_Population_For_Player_` (colcalc.cpp:896-936) for
    the local player. A settled (non-outpost) colony answers the best limit
    over the races living in it, each through `Colony_Race_Pop_Limit_`
    (biospheres +2); anything else answers the local player's limit.
    Advanced City Planning (+5) is not applied — see the module docstring."""
    colony = view.colony(planet.colony_index) if planet.colony_index != -1 \
        else None
    if colony is not None and not colony.outpost_flag:
        races = ({view.player_num} if colony.n_pops == 0 else
                 {int(colony.pop[i]) & 0x0F for i in range(colony.n_pops)})
        best = 0
        for race in races:
            limit = race_pop_limit(view, planet.size, colony.climate, race)
            if colony.buildings[colonyrows.BUILDING_BIOSPHERES]:
                limit += TRAIT_BIOSPHERE_BONUS
            best = max(best, min(limit, colonyrows.POP_LIMIT_CAP))
        return best
    return min(race_pop_limit(view, planet.size, planet.climate,
                              view.player_num), colonyrows.POP_LIMIT_CAP)


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
        # The enemy toggle ALSO requires the explored bit, set by
        # Set_Planet_Explored_Flags_ (plntsum.cpp:649) from the omniscience
        # TRAIT or the visited bit — which is `visited` here exactly.
        if not visited(view, star):
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
