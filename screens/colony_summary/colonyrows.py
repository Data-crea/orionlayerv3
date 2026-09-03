"""The numbers behind the colony list: one dict per colony, and the
engine facts those numbers are transcribed from.

Split from `colonylist.py` along the seam the data flow already had.
`build_rows()` hands the renderer plain dicts, so the coupling between
the two halves is a data shape and not a call graph — this module
imports no pygame and knows nothing about pixels, and the renderer
cannot reach back into a struct. The split also put both files back
under the ~300-line guideline (decision 6) without inventing a seam.

TRANSCRIBED, and each with its source:
  the row set        colonies whose `owner` is the local player.
                     HALF of the original's condition, and the half
                     that is missing is named in `build_rows`:
                     `Build_Global_Colony_List_` (colxport.cpp:91)
                     takes TWO conditions — the colony's `owner`
                     has to be the local player and its
                     `outpost_flag` has to be zero — and only the
                     first is applied here. An outpost of the local player
                     would appear as a row the original's list does
                     not have.
  the job split      one colonist per `pop[]` word, counted by
                     profession — ECON_FOOD=0, ECON_INDUSTRY=1,
                     ECON_RESEARCH=2 (orion2_consts.h:119). The
                     left-to-right ORDER those three are drawn in is
                     the renderer's, and matches the original's own
                     columns (colsum.cpp:318-329).
  "No Farming"       the CONDITION, `max_farms == 0` (coldraw.cpp:315,
                     ESTR_NO_FARMING 387). The wording lives in
                     layout.json and the drawing in `colonylist.py`.
  the climate        `s_colony.climate` (offset 226) as an index into
                     `PLANET_CLIMATE` (orion2_consts.h:362-374), 0
                     Toxic to 9 Gaia. The COLONY's field, not the
                     planet's: `Colony_Calculation_` rewrites it when
                     a shield turns a Radiated world Barren
                     (colcalc.cpp:682), so it is already the climate
                     the game displays. NOT `player_climate()`, which
                     is an Aquatic transform for the pop limit and
                     would print Terran for an Ocean world.
  the population     `n_pops` over the computed maximum, which is how
                     the original prints it — `sys.cpp:1444` renders
                     "Population (3/5)" from `colony->n_pops` and
                     `Planet_Max_Population_For_Player_`.
  the planet name    colony -> planet -> star, with the numeral from
                     `HAROLD::Planet_Number_` (harold.cpp): it counts
                     the OCCUPIED slots of `star->planet_index[5]`
                     before the planet, NOT the orbit. An empty slot
                     earlier in a system shifts every numeral after it.
  the bar length     `COLCALC::Planet_Max_Population_For_Player_`
                     (colcalc.cpp:896) — see max_population() below.
                     That is where a row's FILLED and FREE regions
                     end, not where the track does.
  the track length   `POP_LIMIT_CAP`, the engine's own ceiling —
                     three sources on the constant, which also says
                     why the square is measured from it and not from
                     anything on screen.

NOT DRAWN — two states the original's row string carries and the HD
row does not. Neither is a task in disguise and neither is on
`doc/orion2re_open_fixes.md`; they are written down because they were
found while reading `Draw_Colony_Summary_For_Colony_` for something
else, and an omission nobody has recorded is indistinguishable from
an omission nobody noticed.

  the star's BLOCKADE   colsum.cpp:557-569. The branch tests
                        `star->blockaded` as a BITMASK over players,
                        shifted by the local player and masked to one
                        bit (colsum.cpp:562) — the same shape as
                        `s_star_data.visited`, and read the same way
                        by `star.visited_by`. A blockaded system
                        colours the row through an inline attribute
                        and appends a marker string (ESTR 0x46 and
                        0x86); an unblockaded one substitutes the
                        empty string twice, which is why the name
                        column is 89 px wide and not 87.
                        REACHABLE: `blockaded` is offset 162 in the
                        verified `core/structs/star.py` spec and the
                        stars are in the snapshot. Not drawn because
                        nothing has been built for it, not because
                        the data is missing.
  a COLONY EVENT        colsum.cpp:553, `EVENTS::Colony_Has_Event_`
                        (events.cpp:635). A colony with an event
                        takes the OTHER branch entirely: a different
                        paragraph type, an inline colour attribute
                        chosen by `Event_Good_` (colsum.cpp:534), and
                        the event's own label appended to the name.
                        NOT REACHABLE: the function reads
                        `EVENTS::_event_data[]`, and the snapshot
                        carries settings, players, stars, ships,
                        colonies, planets, nebulas, leaders, antarans
                        and ship icons and no events at all
                        (ext_api.cpp:53-136). So this one cannot be
                        drawn from what is on the wire today, which
                        is a different kind of absence from the
                        blockade's and is why the two are listed
                        apart rather than as one line.

NOT READ, deliberately: race groups as shades, and androids and
natives as locked. The mask is no longer the obstacle — the pop
word's low nibble has a second source for 0..7, verified live, and
that source refutes the "race" reading rather than merely agreeing
with the player one (see `core/structs/colony.py`). What is still
open is the meaning of 8 and 9: the android and native sentinels
resolve to the colony's owner in `Get_Effective_Pop_Player_`
(colony.cpp:1261) and occur in no sample save, so that branch stays
transcription only — and those two are exactly the cases the locking
was wanted for. Nothing here reads the nibble, so nothing on screen
depends on the unverified part; the zone split is built as a list of
runs so the shading can be added inside a run later without moving
anything else.
"""
from core.structs import colony as colony_struct
from core.structs import planet as planet_struct
from core.structs import player as player_struct
from core.structs import star as star_struct

ROMAN = ("I", "II", "III", "IV", "V")

#: orion2_consts.h:119-123. `s_colony.production[4]` is indexed by
#: these, and the four sort keys that read it use them.
ECON_FOOD, ECON_INDUSTRY, ECON_RESEARCH, ECON_BC = 0, 1, 2, 3

#: colcalc.cpp:57, _size_climate_max_pop_lookup, indexed by climate.
CLIMATE_FACTOR = (25, 25, 25, 25, 25, 25, 40, 60, 80, 100)
#: mox.cpp:796, _planet_max_population, indexed by PLANET_SIZE. This
#: is the BASE of a computation and never an answer on its own — see
#: the fundament, section 3.
SIZE_BASE = (5, 10, 15, 20, 25)

TRAIT_AQUATIC = 12            # orion2_consts.h:961
TRAIT_SUBTERRANEAN = 13       # orion2_consts.h:962
TRAIT_ENVIRONMENT_IMMUNE = 23  # orion2_consts.h:972
BUILDING_BIOSPHERES = 15      # orion2_consts.h:28
POP_BONUS_BIOSPHERES = 2      # colcalc_config.cpp:40
#: The engine's hard population ceiling, and therefore the length of
#: the track every row is drawn on. Three sources, one number: a
#: colonist lives in `s_colony.pop[42]` (orion2.h:497), so no colony
#: holds more; `COLCALC::Planet_Max_Population_For_Player_` ends
#: `if (pop_limit > 42) pop_limit = 42;` (colcalc.cpp:930), so no
#: computed maximum passes it; and `COLMOVE::Give_Colonist_New_Job_`
#: caps ONE job at the same number (`Sum_Colonists_ >= 42`,
#: colmove.cpp:518) — which is why a single zone may legitimately
#: span the whole track, and why it cannot be drawn shorter.
#:
#: This is the only copy in the tree. `max_population()` clamps with
#: it and `colonylist.render()` measures the square with it, so the
#: two can never disagree about how long a full bar is.
#:
#: It is also why the square is a fixed unit. The unit used to be
#: derived from the widest `max_pop` in the list being drawn, which
#: made the ruler move with the empire: one new Gaia colony, or a
#: finished Biosphere, lengthened the longest bar and shrank every
#: square on the screen, so a square counted last turn was not the
#: square counted this turn — and nothing about the picture said the
#: scale had changed. A ceiling the engine enforces cannot do that.
POP_LIMIT_CAP = 42

CLIMATE_TUNDRA, CLIMATE_OCEAN, CLIMATE_SWAMP = 4, 5, 6
CLIMATE_TERRAN, CLIMATE_GAIA = 8, 9


def player_climate(climate, traits):
    """COLCALC::Calc_Player_Climate_ (colcalc.cpp). Aquatic only."""
    if traits and traits[TRAIT_AQUATIC]:
        if climate in (CLIMATE_TUNDRA, CLIMATE_SWAMP):
            return CLIMATE_TERRAN
        if climate in (CLIMATE_OCEAN, CLIMATE_TERRAN):
            return CLIMATE_GAIA
    return climate


def max_population(colony, planet, traits):
    """The maximum the original prints, for the colony's OWNER.

    `COLCALC::Colony_Race_Pop_Limit_` (colcalc.cpp) over
    `Size_And_Climate_Race_Pop_Limit_` and
    `Size_And_Climate_Max_Population_` (colcalc.cpp:1271).

    Two details that are easy to get wrong and were both read out of
    the source rather than assumed. The climate is the COLONY's
    (offset 226), not the planet's: `Colony_Calculation_` rewrites it
    when a shield turns a Radiated world Barren (colcalc.cpp:682).
    And `SIZE_BASE[size]` is only the base — the climate factor and
    the immunity bonus scale it, which is the difference between 10
    and the 5 the game prints for a Small Ocean planet.

    TWO DEVIATIONS, both stated rather than hidden:

    1. Advanced City Planning adds a flat +5 and is NOT applied,
       because it lives in `s_player.tech_applications`, which
       `core/structs/player.py` does not expose and which has no
       verified offset. Adding an unverified one to make a bar
       longer is exactly the trade decision 23 forbids.
    2. The original returns the best limit over the RACES PRESENT in
       the colony; this returns the limit for the owner's race. The
       two agree for a single-race colony. The walk needs the pop
       nibble, which is now confirmed for 0..7 — what it does not
       have is the 8 and 9 sentinels, and a walk that mis-resolves
       androids and natives would pick the wrong race for exactly
       the colonies the walk exists for.

    Both make the bar too SHORT rather than too long, which shows as
    a bar that cannot hold its own squares — visible, not silent.
    """
    climate = player_climate(colony.climate, traits)
    immune = bool(traits[TRAIT_ENVIRONMENT_IMMUNE]) if traits else False
    factor = min(100, (25 if immune else 0) + CLIMATE_FACTOR[climate])
    size = max(0, min(len(SIZE_BASE) - 1, planet.size))
    limit = (factor * SIZE_BASE[size] + 50) // 100
    if traits and traits[TRAIT_SUBTERRANEAN]:
        limit += 2 * size + 2          # COLCALC::Double_Add_Two_
    if colony.buildings[BUILDING_BIOSPHERES]:
        limit += POP_BONUS_BIOSPHERES
    return min(limit, POP_LIMIT_CAP)


def planet_name(colony, planets, stars):
    """'Sol III' — HAROLD::Planet_Number_ counts occupied slots."""
    if not 0 <= colony.planet < len(planets):
        return "?"
    planet = planet_struct.parse(planets[colony.planet])
    if not 0 <= planet.star_index < len(stars):
        return "?"
    star = stars[planet.star_index]
    number = 0
    for slot in star_struct.planet_indices(star):
        if slot == colony.planet:
            break
        if slot > -1:
            number += 1
    numeral = ROMAN[number] if number < len(ROMAN) else str(number + 1)
    return f"{star.name} {numeral}"


def build_rows(game_state, sort_key="name"):
    """One dict per colony of the local player, sorted.

    Only `owner`, `planet`, `n_pops`, `max_farms`, `climate` and
    `buildings` are read, plus `pop_prof` — every one of them backed
    by two sources. The pop word's low nibble is not touched here;
    it is verified for 0..7 but nothing on this screen needs it.

    The dict keys ARE the interface to `colonylist.render()`: name,
    climate, pops, jobs, no_farming, max_pop, producing,
    producing_turns, can_buy. Nothing else crosses,
    and a smoke check holds the preview tool's fake rows to the same
    set — a stale row dict still renders, so nothing else would
    notice it drift.
    """
    if game_state is None or not getattr(game_state, "colonies_raw", None):
        return []
    planets = game_state.planets_raw
    stars = game_state.stars
    me = game_state.player_num
    traits = None
    if 0 <= me < len(game_state.player_raw):
        traits = player_struct.traits(
            player_struct.parse(game_state.player_raw[me]))

    rows = []
    for raw in game_state.colonies_raw:
        col = colony_struct.parse(raw)
        # TRANSCRIBED, and INCOMPLETE. The original's list is built by
        # `Build_Global_Colony_List_` (colxport.cpp:91) on two
        # conditions — the colony's `owner` has to be the local
        # player and its `outpost_flag` has to be zero — and
        # `N_Colonies_` (colxport.cpp:67) counts with the same pair.
        # Only the owner half is here.
        #
        # The outpost half is written down rather than applied,
        # because `outpost_flag` at offset 6 has one source and the
        # project needs two (decision 23). The header route fixes
        # where the byte is and how wide it is; what it cannot fix is
        # that the byte MEANS outpost, and a filter is a claim about
        # the meaning. The obvious second source is a count against
        # the reference save, and that save cannot supply it: all 21
        # of its colonies carry 0, so the filter would be invisible in
        # it either way — see `core/structs/colony.py` and
        # `tools/struct_probe.py colonies --outposts`, which is the
        # probe and prints exactly that.
        if col.owner != me:
            continue
        # OURS, not a transcription: the original indexes
        # `MOX::_planet[]` unguarded because the array is always
        # there. We read a snapshot, where a short or absent planet
        # list is a state that reaches this loop — an early frame, a
        # reconnect, a spec that has moved. Dropping the row is the
        # quiet answer and it is the right one here, because the
        # alternative is a traceback inside a render path.
        if not 0 <= col.planet < len(planets):
            continue
        planet = planet_struct.parse(planets[col.planet])
        jobs = [0, 0, 0]
        for i in range(min(col.n_pops, len(col.pop))):
            prof = colony_struct.pop_prof(col.pop[i])
            if 0 <= prof < len(jobs):
                jobs[prof] += 1
        rows.append({
            "name": planet_name(col, planets, stars),
            "pops": col.n_pops,
            "jobs": jobs,
            "no_farming": col.max_farms == 0,
            "climate": col.climate,
            # The building column's content. `producing` is a display
            # STRING and stays empty here: the production id at offset
            # 277 indexes TECHDATA::_buildings[], whose names are
            # loaded from the player's techname.lbx at runtime
            # (techinit.cpp:43-73) and are `kEmptyName` in the orion2re
            # source. There is no extractor for that table yet, so the
            # column renders empty rather than inventing a name — the
            # same "absent is a state to explain" rule the help texts
            # and the nebulae follow. `producing_turns` needs a cost
            # calculation that is not built either.
            "producing": "",
            "producing_turns": 0,
            "can_buy": False,
            # production[4] in ECON order, orion2_consts.h:119-123.
            # Read for the four sort keys that need it. Nothing in
            # the ROW draws these; the original does not put them in
            # its row either. It does draw all four per colony, in
            # the bottom-left box `output_panel` occupies
            # (coldraw.cpp:60) — decision 43 claimed otherwise and is
            # WITHDRAWN, so output_panel is a TRANSCRIPTION and this
            # comment used to say the opposite.
            "production": list(col.production),
            "max_pop": max_population(col, planet, traits),
        })

    rows.sort(key=SORT_KEYS.get(sort_key, SORT_KEYS["name"]))
    return rows


# ── The seven sort keys, and the directions are transcribed ───────
#
# `COLSUM::Switched_cmp_` (colsum.cpp:378-401, orion2re 1.60) is a
# plain switch on `_g_sort_index` with the DIRECTION BAKED IN as a
# literal minus per case. Five of the seven are descending; Name and
# Producing are not. There is NO direction toggle anywhere — clicking
# the header that is already active re-sorts identically rather than
# reversing, which is worth stating because every list control
# written since 1996 does the opposite and the absence looks like an
# omission rather than a transcription.
#
#   0 name        cmp_Alpha_    :1042   ascending
#   1 population  cmp_Pops_     :1064   DESCENDING
#   2 food        cmp_Food_     :1071   DESCENDING
#   3 industry    cmp_Industry_ :1076   DESCENDING
#   4 science     cmp_Research_ :1081   DESCENDING
#   5 producing   cmp_Prod_     :1091   ascending — NOT IMPLEMENTED
#   6 bc          cmp_BC_       :1086   DESCENDING
#
# ── Ties keep the input order, and that IS the transcription ──────
#
# Every key below used to fall back to the name on a tie, marked as
# an addition of ours against a bubble sort whose behaviour on equal
# elements was assumed to be arbitrary. It is not arbitrary, and the
# addition was buying a stability the chain already had. Four links,
# each one a file the value passes through in order:
#
#   ext_api.cpp:94    the snapshot writes `MOX::_colony[i]` for
#                     ascending i, so `colonies_raw` arrives in the
#                     engine's own array order.
#   colxport.cpp:91   `Build_Global_Colony_List_` fills
#                     `_g_colony_list_ptr` walking the same array
#                     ascending, keeping only the player's colonies.
#                     The original's list therefore starts in array
#                     order too — the same order, filtered the same
#                     way, which is what makes the comparison below
#                     legitimate rather than a coincidence.
#   colsum.cpp:363    `Sort_Col_List_` is a bubble sort that swaps
#                     only when `Switched_cmp_` is STRICTLY greater
#                     than zero. Equal elements are never swapped, so
#                     the sort is stable and a tie comes out in array
#                     order.
#   colsum.cpp:1056   `cmp_` returns -1, 0 or 1 and returns 0 on
#                     equality — the sign that would break that
#                     stability cannot be produced. This is the link
#                     that makes the one above a fact instead of a
#                     property of one implementation: a comparator
#                     that leaked a nonzero value for equal inputs
#                     would reorder ties no matter how the sort
#                     swaps.
#
# `build_rows` walks `colonies_raw` in order and `list.sort` is
# stable, so dropping the name fallback does not make the list
# unstable — it makes it agree with the original. A redraw reads the
# same snapshot in the same order and produces the same list.
#
# The name fallback was not merely redundant. It ordered ties the
# original does not order, so two colonies of equal population sat in
# alphabetical order here and in array order there, and no value on
# either screen was wrong — which is the kind of difference only a
# side-by-side finds.

def _alpha(row):
    """cmp_Alpha_ — `strcasecmp` on the planet name (colsum.cpp:1053).

    CASE-INSENSITIVE, and that is the transcription rather than a
    convenience: `strcasecmp` is what the original calls, so a lower-
    case star name sorts among its peers instead of after all of
    them. Star names are generated capitalised, but a player renames
    a home star with free text (namestar.cpp:262).
    """
    return row["name"].casefold()


def _by(field, econ=None):
    """Descending on one number. No tie-break — see the block above.

    A single negated value, never a tuple: the second element of a
    tuple IS a tie-break, so the absence has to be visible in the
    return rather than stated in a comment beside it.
    """
    if econ is None:
        return lambda r: -r[field]
    return lambda r: -r["production"][econ]


#: `producing` is absent on purpose. `cmp_Prod_` (colsum.cpp:1091)
#: orders by `Prod_To_Sort_Type_`, which reads
#: `TECHDATA::_buildings[].cost` and then breaks ties on
#: `COLBLDG::Selection_Name_` — a cost table and a name table both
#: loaded at runtime from the player's own techname.lbx
#: (techinit.cpp:43-73) and neither shipped. It is the same absence
#: that leaves the building column empty. Sorting by it would need
#: an invented order, so the key falls back to the name and the
#: screen says so rather than pretending.
SORT_KEYS = {
    "name": _alpha,
    "population": _by("pops"),
    "food": _by("production", ECON_FOOD),
    "industry": _by("production", ECON_INDUSTRY),
    "science": _by("production", ECON_RESEARCH),
    "bc": _by("production", ECON_BC),
    "producing": _alpha,
}

#: Keys that do not do what their button says. The screen reads this
#: to mark the control rather than letting a click look like it
#: worked — an absence that is visible is a state, an absence that is
#: silent is a bug.
SORT_UNAVAILABLE = {
    "producing": "needs the building cost and name tables from "
                 "techname.lbx, which are not shipped",
}
