"""The numbers behind the colony list: one dict per colony, and the
engine facts those numbers are transcribed from.

Split from `colonylist.py` along the seam the data flow already had.
`build_rows()` hands the renderer plain dicts, so the coupling between
the two halves is a data shape and not a call graph — this module
imports no pygame and knows nothing about pixels, and the renderer
cannot reach back into a struct. The split also put both files back
under the ~300-line guideline (decision 6) without inventing a seam.

TRANSCRIBED, and each with its source:
  the row set        colonies of the local player that are not
                     outposts — both of the original's conditions,
                     from `Build_Global_Colony_List_`
                     (colxport.cpp:91-99), which walks the colony
                     array in order and keeps the ones whose `owner`
                     is the local player and whose `outpost_flag` is
                     zero. `N_Colonies_` (colxport.cpp:67) counts
                     with the same pair.
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
                     (colcalc.cpp:896) — see `colonyfacts.max_population`.
                     That is where a row's FILLED and FREE regions
                     end, not where the track does.
  the track length   `colonyfacts.POP_LIMIT_CAP`, the engine's own ceiling —
                     three sources on the constant, which also says
                     why the square is measured from it and not from
                     anything on screen.

NOT DRAWN — two states the original's row string carries and the HD
row does not. Neither is a task in disguise and neither is on
`dev:doc/orion2re_open_fixes.md`; they are written down because they were
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
import collections

from core import colonyfacts
from core import colsumblock
from core import prodname
from core.colonyfacts import ECON_BC, ECON_FOOD, ECON_INDUSTRY, ECON_RESEARCH
from core.structs import colony as colony_struct
from core.structs import planet as planet_struct
from core.structs import player as player_struct

from . import colonyfigures
from . import colonyicons


#: One drawn cell. TWO FIELDS AND NOT TWO PARALLEL TUPLES: the
#: identity letter and the figure are both per cell, and the moment
#: they live in two lists indexed the same way, one of them can be
#: rebuilt without the other. `kind` is what `_cell_mark` reads;
#: `figure` is the file name `colonyfigures` resolves, or None where
#: the race is not knowable from the snapshot.
Cell = collections.namedtuple("Cell", "kind figure")


def _pop_cell(word, owner_race, races):
    """One `Cell` for one pop word.

    Both halves come from the SAME word in the SAME place, which is
    the point: `_pop_class` answers "what letter" and
    `colonyfigures.figure_for` answers "what sprite", and both are
    branches of `COLONY::Colony_Pop_Anim_` (colony.cpp:1268-1283).
    Computing them apart would let a cell wear an N and draw an
    android.
    """
    return Cell(_pop_class(word, owner_race),
                colonyfigures.figure_for(word, owner_race, races))


def _pop_class(word, owner):
    """Which identity class one pop word belongs to, or "" for own.

    Four classes, and they are the original's own — see
    `COLONY::Colony_Pop_Anim_` (colony.cpp:1268), which switches on
    exactly these before it picks a sprite. The fifth case, an
    assimilated pop of another race, deliberately answers "" and is
    a recorded gap; see `colonylist._cell_mark`.

    `native` is VERIFIED against `fixture_natives_3502.5.GAM` three
    ways; `android` and `conquered` are the source alone, because no
    save this project holds contains either.
    """
    if colony_struct.pop_is_conquered(word):
        return "conquered"
    nibble = colony_struct.pop_player_index(word)
    if nibble == colony_struct.POP_NATIVE:
        return "native"
    if nibble == colony_struct.POP_ANDROID:
        return "android"
    return ""


def _player_context(game_state):
    """(me, traits, planning, parsed, races) for one `build_rows` pass.

    Split out because it is the one place the players are read: the
    local player's traits and research, and the player -> race map the
    figures need. Nothing below it parses a player again."""
    me = game_state.player_num
    traits = None
    planning = False
    # EVERY PLAYER IS PARSED ONCE (work order 324): the local one for the
    # traits first and unguarded as before, the others for the race map.
    parsed = {}
    if 0 <= me < len(game_state.player_raw):
        _me = parsed[me] = player_struct.parse(game_state.player_raw[me])
        traits = player_struct.traits(_me)
        planning = colonyfacts.city_planning(_me)
    # PLAYER INDEX -> RACE INDEX, for the figures.
    # `Colony_Pop_Anim_` reads `_player[Get_Effective_Pop_Player_(..)]
    # .race` (colony.cpp:1272-1275), and the effective player is the
    # pop word's own low nibble unless that nibble is 8 or 9 — so a
    # conquered or assimilated pop draws ITS OWN race's figure and
    # not the colony owner's. Every player is parsed, not just ours,
    # because that is exactly the case this map exists for. `race` is
    # offset 37 in the verified spec (decision 23).
    races = {}
    for _pi, _raw in enumerate(game_state.player_raw):
        try:
            _p = parsed.get(_pi)
            if _p is None:
                _p = player_struct.parse(_raw)
            races[_pi] = int(_p.race)
        except (AttributeError, ValueError, TypeError):
            continue
    return me, traits, planning, parsed, races


def _job_cells(col, index, races, held):
    """(jobs, cells, held_cells) of one colony: the pops by profession,
    the drawn cells per job, and the cells of the cluster in hand."""
    jobs = [0, 0, 0]
    for i in range(min(col.n_pops, len(col.pop))):
        prof = colony_struct.pop_prof(col.pop[i])
        if 0 <= prof < len(jobs):
            jobs[prof] += 1
    # THE HELD CLUSTER IS APPLIED TO THE WORDS, NOT SUBTRACTED
    # FROM A COUNT. `colonymove.held_pops` is `Get_Cluster_`'s
    # own `pop[i] &= 0xFFFFFDFF` and the walk below is
    # `coldraw.cpp:326-337`, which already refuses an unassigned
    # pop — so there is no second arithmetic to keep in step.
    # Imported here rather than at the top because `colonymove`
    # imports THIS module for the ECON order; the bit clear is a
    # move rule and belongs beside `Get_Cluster_`, so the import
    # yields rather than the home.
    from . import colonymove
    pop_words = col.pop
    held_cells = ()
    if held is not None and held[0] == index and held[1]:
        pop_words = colonymove.held_pops(col.pop, held[1])
        # ARRAY ORDER, because `Draw_Cluster_` walks `pop[]` from
        # 0 and takes every pop whose `0x200` is clear
        # (colmove.cpp:24-29). That is NOT the icon walk's order
        # (coldraw.cpp:326-337), and the two must not be confused
        # — decision 48 is about the column, this is about the
        # cursor.
        held_cells = tuple(
            _pop_cell(col.pop[i], races.get(col.owner), races)
            for i in sorted(held[1])
            if 0 <= i < min(col.n_pops, len(col.pop)))
    cells = tuple(tuple(_pop_cell(pop_words[p], races.get(col.owner),
                                  races)
                        for p in colonyicons.icon_pops(
                            pop_words, col.n_pops, job))
                  for job in range(3))
    return jobs, cells, held_cells


def _output_fields(col, planet, traits, planning):
    """The row keys from `production` on: the sort datum, the net the
    original draws, and everything the output panel reads. Contiguous
    at the end of the dict, so `build_rows` appends them in order."""
    morale, morale_applies = colonyfacts.colony_morale(col, traits)
    return {
        # production[4] in ECON order, orion2_consts.h:119-123.
        # Read for the four sort keys that need it. Nothing in
        # the ROW draws these; the original does not put them in
        # its row either. It does draw all four per colony, in
        # the bottom-left box `output_panel` occupies
        # (coldraw.cpp:60) — decision 43 claimed otherwise and is
        # WITHDRAWN, so output_panel is a TRANSCRIPTION and this
        # comment used to say the opposite.
        "production": list(col.production),
        # WHAT THE ORIGINAL DRAWS, which is not what it stores.
        # `production` above stays because the four SORT keys
        # read it (SORT_KEYS below) and the original sorts on the
        # stored value — Switched_cmp_ compares colony records,
        # not the scan box. The net is its own key so the two can
        # never be confused at a call site: one is the datum, one
        # is the drawing. See `colonyfacts.drawn_production` for the
        # four branches and for the (int8_t) cast that picks between
        # them.
        "drawn_production": [colonyfacts.drawn_production(col, e)
                             for e in range(4)],
        # 0 on every row the original refuses to draw one for —
        # see `colonyfacts.production_shortage`, where the refusal is
        # the part that matters.
        "shortage": [colonyfacts.production_shortage(col, e)
                     for e in range(4)],
        "max_pop": colonyfacts.max_population(col, planet, traits,
                                              planning),
        # ── For output_panel, and NOT drawn in the row ──
        # The original's scan box prints seven values for the
        # SELECTED colony (colsum.cpp:1196-1205) and the row
        # already carries three of them. These are the other
        # four plus morale, decoded here rather than in the
        # panel because all struct reading in this screen lives
        # in this module: the renderers get plain dicts and
        # cannot reach back into a record, which is the seam the
        # split was made along.
        #
        # All five are indices or counts, and the words they
        # index live in layout.json (decision 15).
        "size": planet.size,                    # PLANET_SIZE
        "gravity": planet.gravity_class,        # PLANET_GRAVITY
        "mineral": planet.mineral_class,        # MINERAL_RESOURCE
        # colsum.cpp:1179-1182 sums all ten before printing.
        # See output._growth_note for why it is not scaled.
        "growth": sum(col.pop_growth),
        "morale": morale,
        "morale_applies": morale_applies,
        "morale_icon": colonyfacts.morale_icon(morale),
    }


def build_rows(game_state, sort_key="name", names=None, held=None):
    """One dict per colony of the local player, sorted.

    `held` is `(colony index, pop indices)` for a cluster the HD side
    is holding, or None. It does exactly what `COLMOVE::Get_Cluster_`
    does and nothing more: those pops lose bit `0x200`
    (colmove.cpp:70), so the icon walk stops emitting them
    (coldraw.cpp:336) and the row, its pitch and both hit tests
    shorten because all three read the one list. `pops` and `jobs`
    are NOT touched — the original does not change `n_pops` either,
    and a colonist in hand is still a colonist of that colony.

    `names` is a `core.prodname.Resolver` or None — the two name
    files behind one object, because `COLBLDG::Selection_Name_` reads
    both and the row builder should not have to know that. None reads
    as an absent file. The row carries the branch it took in
    `producing_state`, which the ROW CAN now distinguish and the
    column needs it to: an unextracted file and a ship name that is
    not on the wire have different fixes and one of them has none.

    Only `owner`, `planet`, `n_pops`, `max_farms`, `climate` and
    `buildings` are read, plus `pop_prof` — every one of them backed
    by two sources. The pop word's low nibble is not touched here;
    it is verified for 0..7 but nothing on this screen needs it.

    The dict keys ARE the interface to the two renderers: index,
    name, climate, pops, jobs, cells, held, no_farming, max_pop,
    producing,
    producing_id, producing_state, producing_turns, can_buy for
    `colonylist.render()` — `can_buy` is False here and set by
    `colonybuy.annotate` to False, "buy" or "bought" (work order 322
    B1) — and size,
    gravity, mineral, growth, morale, morale_applies,
    drawn_production, shortage for
    `colonyoutput.render()` on top of climate, pops and max_pop,
    which both use. Nothing else crosses,
    and a smoke check holds the preview tool's fake rows to the same
    set — a stale row dict still renders, so nothing else would
    notice it drift.
    """
    if game_state is None or not getattr(game_state, "colonies_raw", None):
        return []
    planets = game_state.planets_raw
    stars = game_state.stars
    me, traits, planning, parsed, races = _player_context(game_state)

    # The ship branches' names, off the wire (work order 196 C3: the
    # list never passed them, and every ship read "not on the wire").
    ships = prodname.ShipNames(game_state, me, player=parsed.get(me))
    rows = []
    for index, raw in enumerate(game_state.colonies_raw):
        col = colony_struct.parse(raw)
        # TRANSCRIBED, both halves. `Build_Global_Colony_List_`
        # (colxport.cpp:91-99) walks the colony array in order and
        # keeps the ones whose `owner` is the local player and whose
        # `outpost_flag` is zero; `N_Colonies_` (colxport.cpp:67)
        # counts with the same pair. An outpost is a colony record
        # like any other, so without the second condition it appears
        # as a row the original's own list does not have.
        #
        # The outpost half waited for a second source, because a
        # filter is a claim about what the byte at offset 6 MEANS and
        # the header can only fix where it sits (decision 23). It has
        # one now — see `core/structs/colony.py`, and
        # `dev:tools/struct_probe.py colonies --outposts` reproduces it
        # against a live game.
        if col.owner != me or col.outpost_flag != 0:
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
        # RESOLVED ONLY FOR A ROW THAT IS KEPT (work order 324): it used to
        # run for every colony of every player before the owner filter.
        _producing = (names.name(col.producing[0], ships=ships)
                      if names is not None else (None, "missing"))
        planet = planet_struct.parse(planets[col.planet])
        jobs, cells, held_cells = _job_cells(col, index, races, held)
        row = {
            # The colony's index in the snapshot's own array, which is
            # the engine's `MOX::_colony[]` index and therefore the
            # same number `_list_col[]` holds and `_g_colony_n` is set
            # to (colsum.cpp:139). It is here so the SELECTION can be
            # a colony rather than a row: the original never reseats
            # `_g_colony_n` on a sort — the handler at
            # colsum.cpp:830-837 re-sorts, clears the window array and
            # resets `_first`, and leaves the selected colony alone —
            # so the selection follows its colony to wherever the new
            # order puts it. A row index cannot express that.
            #
            # Nothing DRAWS it. It is an identity, and it is the one
            # key in this dict that would be wrong to show.
            "index": index,
            # the PLANET it is on, for the turning sphere (WO 331): its
            # start and speed are the planet's on every screen
            "planet": int(col.planet),
            "name": colonyfacts.planet_name(col, planets, stars),
            "pops": col.n_pops,
            "jobs": jobs,
            # ONE ENTRY PER DRAWN CELL, in the ORIGINAL'S OWN ORDER
            # (decision 48): `colonyicons.icon_pops` is the walk the
            # game draws its column with, so cell m of a job is the
            # pop a click on cell m picks up. Identity and click
            # therefore cannot disagree — which they would the moment
            # this was built from `jobs` and array order instead.
            #
            # It counts ICONS and `jobs` counts POPS, and the two
            # differ by exactly the pops of a held cluster, which the
            # original does not draw either (coldraw.cpp:336).
            "cells": cells,
            # THE POPS IN HAND, empty on every row but the one a
            # cluster was picked from. They are the same pops the
            # `cells` above no longer hold — one `0x200`, two
            # consequences, exactly as the original has it.
            "held": held_cells,
            "no_farming": col.max_farms == 0,
            "climate": col.climate,
            # The building column's content. `producing` is a display
            # STRING, from `producing[0]` at offset 277 through
            # `core.buildnames` — the id indexes
            # `TECHDATA::_buildings[]`, whose names live in the
            # player's own techname.lbx (techinit.cpp:43-73) and are
            # `kEmptyName` in the orion2re source, so they are
            # EXTRACTED like the help texts (decision 38) and decoded
            # at load time. None when the file is absent or the id is
            # not a building, and the SCREEN says which — inventing a
            # name here is the thing this must not do.
            #
            # `producing_turns` — the "- 8t" the original appends — is
            # `COLONY::Calculate_Current_Production_Turn_Count` as the
            # engine computes it, read from CSUM (open fix 110,
            # `core.colsumblock.turn_suffix`: 0 for none, as the
            # original prints none for a product of NONE or a count
            # outside 1..9999, colsum.cpp:751-753 in the tree with open
            # fix 110). TRANSCRIPTION
            # `turn_suffix` (work order 322 B2, `build._turns_note`);
            # the autobuild line is OMISSION `autobuild_line`.
            # The price (`Colony_Product_Cost`) is config-bound in v2,
            # so it is never computed here: without the block the
            # suffix stays 0 and is not drawn.
            # THREE KEYS, not one, because the column now has three
            # things to say and used to be able to say two. `names`
            # is a `core.prodname.Resolver`; `name()` is
            # `COLBLDG::Selection_Name_` transcribed, and it reports
            # WHICH branch it took as well as what it found:
            #   ok         the text is the original's own word, and
            #              "" is a legitimate one — E_Strings_(0x00C)
            #   missing    the branch is known, its file is not
            #              extracted
            #   unsourced  a queued ship or a ship design whose record
            #              the wire does not carry (an index past
            #              `ships_raw`) — the names themselves are read
            #              through `prodname.ShipNames` (196 C3)
            # The third is why the state is per ROW and not per
            # screen: no extraction fixes it, so the column must not
            # offer a command for it.
            #
            # `producing_id` is the raw `producing[0]` and it is here
            # for the SORT — `cmp_Prod_` orders on
            # `Prod_To_Sort_Type_(id)` before it ever looks at a
            # name, so the key needs the id and not only the word.
            "producing_id": col.producing[0],
            "producing": _producing[0] or "",
            "producing_state": _producing[1],
            "producing_turns": colsumblock.turn_suffix(
                colsumblock.of_colony(game_state, index)),
            # False here: the record cannot decide it. `colonybuy`
            # sets it to "buy" or "bought" — from the game's own buy
            # field for the rows the game shows (work order 322 B1),
            # from CSUM for the others (open fix 110, 322 B2).
            "can_buy": False,
        }
        row.update(_output_fields(col, planet, traits, planning))
        rows.append(row)

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


#: `producing` NO LONGER FALLS BACK TO THE PLANET NAME. It is
#: `core.prodname.sort_key` — `cmp_Prod_`'s first two levels,
#: transcribed — and the module block there says exactly which part
#: is still missing. It stays in SORT_UNAVAILABLE below; see that
#: entry for why a key that is right on the reference save is still
#: declared unavailable.
SORT_KEYS = {
    "name": _alpha,
    "population": _by("pops"),
    "food": _by("production", ECON_FOOD),
    "industry": _by("production", ECON_INDUSTRY),
    "science": _by("production", ECON_RESEARCH),
    "bc": _by("production", ECON_BC),
    "producing": prodname.sort_key,
}

#: Keys that do not do what their button says. The screen reads this
#: to mark the control rather than letting a click look like it
#: worked — an absence that is visible is a state, an absence that is
#: silent is a bug.
SORT_UNAVAILABLE = {
    # NARROWED 7 September 2026, and the old reason was half wrong.
    # The NAME table is no longer missing — `core.prodname` resolves
    # both of `Selection_Name_`'s answerable branches. What is still
    # missing is `TECHDATA::_buildings[].cost`, which
    # `Prod_To_Sort_Type_` (colsum.cpp:1224) adds 10 to, and
    # `Calculate_Current_Production_Turn_Count_`, `cmp_Prod_`'s third
    # level. The key is therefore RIGHT on any set where no colony is
    # building a building — the reference save is one, every row
    # produces Trade Goods — and orders buildings among themselves by
    # name where the original orders them by cost. A control that is
    # correct on one save and wrong on the next is worse than one
    # that says it cannot do the job, so it stays declared.
    "producing": "orders buildings among themselves by name; the "
                 "original orders them by cost, and the cost table "
                 "in techname.lbx is not extracted",
}
