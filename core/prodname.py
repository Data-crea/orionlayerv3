"""What a colony is producing, as a word — `COLBLDG::Selection_Name_`.

**ONE FUNCTION, TWO CONSUMERS** (decision 5). The BUILDING column and
the `producing` sort key both need the same string, and until now
only the column had one — it read `core.buildnames` directly and the
sort key fell back to the planet name. Two call sites resolving the
same id through different code is the shape decision 5 exists to
stop, and here it had already produced a visible disagreement: the
column showed nothing on the reference save while the sort claimed to
order by something.

`Selection_Name_` (colbldg.cpp:796-820) has THREE branches, and this
module answers all three — two with a string and one with a stated
absence:

    Colony_Production_Is_Building_(id)      -> Real_Building_Name_(id)
      id > BUILDING_NO_BUILDING && id < BUILDING_COUNT (colbldg.h:16),
      so 1..48. `core.buildnames`, out of the player's techname.lbx.

    not Colony_Production_Is_Queued_Ship_   -> Option_String_(id)
      the sixteen-case switch at colbldg.cpp:2338, every case an
      `E_Strings_` index. `core.estrings`, out of the player's
      estrings.lbx. **THIS IS THE BRANCH THE REFERENCE SAVE TAKES ON
      EVERY ROW** — producing[0] is -2, TRADE_GOODS, E_Strings_(0x21D).

    Colony_Production_Is_Queued_Ship_(id)   -> _ship[i].d.name
      id <= COLONY_PRODUCTION_QUEUED_SHIP_BASE (-100). ANSWERED through
      `ShipNames` below: `d.name` is offset 0 of the ship record, verified
      by both of decision 23's sources on 14 September 2026 (ship.py).

and `Option_String_`'s own tail splits once more: a SHIP DESIGN id
(-99..-50, colbldg.h:24) returns
`_player[owner].ship_designs[idx].name` — verified in `player.py`
(work order 180), also through `ShipNames` — and anything else pops an
error dialog and returns the empty string (colbldg.cpp:2380-2384).

**UNTIL WORK ORDER 196 THE COLONIES LIST NEVER ASKED.** Both names were
verified by 180 for the single-colony screen, which passes `ShipNames`;
`Resolver.name` did not take one, so every ship a colony built read
"ship name not on the wire" on the Colonies list (Data's C3). STATE_
UNSOURCED is left for a record the wire does not carry (an index past
`ships_raw`, no player record).

**ID 0 IS NOT A BUILDING, AND WE HAD IT WRONG.** Found 7 September
2026 while transcribing this function. `Colony_Production_Is_Building_`
excludes `BUILDING_NO_BUILDING` = 0 (orion2_consts.h:13) and
`Option_String_` has an explicit `case 0:` returning
`E_Strings_(0x00C)` — the empty string. `core.buildnames.is_building`
said `0 <= id < 49` and would have printed `_buildings[0].name`, which
the extracted table gives as **"No Building"**, where the original
prints nothing. It was invisible until the option table existed to
disagree with it: a colony producing 0 is the one case where the two
branches both claim the id. Fixed in `buildnames.is_building`, and
the range now comes from the two named constants rather than from 0.
"""
from core import buildnames

#: colbldg.h:20, :24 and orion2_consts.h:87-88. A queued ship is
#: `id <= -100`; a ship design is `-99 <= id <= -50`.
QUEUED_SHIP_BASE = -100
SHIP_DESIGN_BASE = -50

KIND_BUILDING = "building"
KIND_OPTION = "option"
KIND_SHIP_DESIGN = "ship_design"
KIND_QUEUED_SHIP = "queued_ship"

#: What `production_name` reports beside the text.
#:   "ok"        the text is the original's own word for this id,
#:               and an EMPTY string is a legitimate "ok" — that is
#:               what E_Strings_(0x00C) is.
#:   "missing"   the branch is known but its file is not extracted.
#:   "unsourced" the branch reads something that is not on the wire.
STATE_OK = "ok"
STATE_MISSING = "missing"
STATE_UNSOURCED = "unsourced"


def kind(production_id):
    """Which of `Selection_Name_`'s branches an id takes.

    Transcribed in the source's own ORDER, which is load-bearing:
    `Selection_Name_` tests building first and queued-ship second, so
    a positive id can never be read as a ship however the ranges are
    written.
    """
    try:
        value = int(production_id)
    except (TypeError, ValueError):
        return KIND_OPTION
    if buildnames.is_building(value):
        return KIND_BUILDING
    if value <= QUEUED_SHIP_BASE:
        return KIND_QUEUED_SHIP
    if value <= SHIP_DESIGN_BASE:
        return KIND_SHIP_DESIGN
    return KIND_OPTION


class ShipNames:
    """`Selection_Name_`'s two ship branches, from the wire (work order 180):
    a queued ship is `_ship[-100 - id].d.name` (colbldg.h:33-35, ship.py
    `name`, verified), a design `_player[owner].ship_designs[-50 - id]
    .name` (colbldg.h:37-39, player.py `ship_designs`, verified)."""

    def __init__(self, state, player_num, player=None):
        self._ships = getattr(state, "ships_raw", None) or []
        raws = getattr(state, "player_raw", None) or []
        # `player` is the caller's own parse of that record (work order
        # 324: the colony rows parse every player once)
        self._player = player
        if player is None and 0 <= int(player_num) < len(raws):
            from core.structs import player as player_struct
            self._player = player_struct.parse(raws[int(player_num)])

    def size(self, production_id):
        """`_ship[i].d.size` of a queued ship (`Prod_To_Sort_Type`,
        colsum_details.cpp:324-327), or None when the record is not on
        the wire or the id is no queued ship."""
        from core.structs import ship as ship_struct
        value = int(production_id)
        idx = QUEUED_SHIP_BASE - value
        if value <= QUEUED_SHIP_BASE and 0 <= idx < len(self._ships):
            return ship_struct.SPEC.parse(self._ships[idx]).size
        return None

    def name(self, production_id):
        from core.structs import player as player_struct
        from core.structs import ship as ship_struct
        value = int(production_id)
        if value <= QUEUED_SHIP_BASE:
            idx = QUEUED_SHIP_BASE - value
            if 0 <= idx < len(self._ships):
                return ship_struct.SPEC.parse(self._ships[idx]).name
            return None
        idx = SHIP_DESIGN_BASE - value
        return (player_struct.design_name(self._player, idx)
                if self._player is not None else None)


def production_name(production_id, buildings=None, strings=None,
                    ships=None):
    """(text, state) for one `producing[0]`. Never raises.

    `buildings` is a `core.buildnames.BuildingNames` and `strings` a
    `core.estrings.EStrings`; either may be None, which reads as an
    absent file rather than as an error. The two loaders read
    DIFFERENT FILES and neither ever reaches for the other's — the
    walks are different (`strlen+1` against skip-the-NUL-run) and
    crossing them mis-indexes the result silently, so a smoke check
    asserts the separation rather than trusting this sentence.
    """
    if production_id is None:
        return "", STATE_OK
    branch = kind(production_id)
    if branch == KIND_BUILDING:
        if buildings is None or buildings.state != "ok":
            return None, STATE_MISSING
        name = buildings.building(production_id)
        return (name, STATE_OK) if name else (None, STATE_MISSING)
    if branch in (KIND_QUEUED_SHIP, KIND_SHIP_DESIGN):
        # NOT A MISSING FILE — without a `ShipNames` the caller has not
        # read the ship records, and the column must not offer
        # `techname_extract` as the fix for it.
        name = ships.name(production_id) if ships is not None else None
        return (name, STATE_OK) if name else (None, STATE_UNSOURCED)
    if strings is None or strings.state != "ok":
        return None, STATE_MISSING
    text = strings.option(production_id)
    if text is None:
        # `Option_String_`'s default: an id the switch does not name
        # (-14, -37..-41) shows an error and returns the empty string
        # (colbldg.cpp:2380-2384). Empty is the original's answer, so
        # it is "ok" and the column draws nothing.
        return "", STATE_OK
    return text, STATE_OK


# ── The sort key: `cmp_Prod_`, all three levels (work order 437) ─────
#
# `cmp_Prod` (colsum_details.cpp:225-250) is THREE levels, and the
# direction is not what this project's table said. `Switched_cmp`
# case 5 does NOT negate (colsum_details.cpp:81-109) — unlike cases
# 1,2,3,4,6 — but `cmp_Prod` negates internally, twice:
#
#   1  -cmp(Prod_To_Sort_Type(a), Prod_To_Sort_Type(b))     DESCENDING
#   2  -sign(strcmp(Selection_Name(a), Selection_Name(b)))  DESCENDING
#   3   cmp(turn_count(a), turn_count(b))                   ascending
#
# so producing is DESCENDING on tier and DESCENDING on name, and the
# comment block in `colonyrows` calling it "ascending" was wrong.
# Level 2 is `strcmp`, CASE-SENSITIVE — `cmp_Alpha` uses `strcasecmp`
# (colsum_details.cpp:180-184) and this one does not, which is a
# difference between the two keys and not a slip in one of them.
#
# EVERYTHING IS SOURCED NOW. `Prod_To_Sort_Type`
# (colsum_details.cpp:323-376):
#
#   queued ship      _ship[i].d.size + 10000   `ShipNames.size`, the ship
#                                              record on the wire
#   FREIGHTERS                        9999      literal
#   building         buildings[id].cost + 10   `core.buildcost` (the table
#                                              is compiled into the engine,
#                                              techdata.cpp:41-90 — the
#                                              old "not extracted" was
#                                              wrong; OMISSION
#                                              `config_building_cost`)
#   FARMER/WORKER/SCIENTIST/SPY/NONE    -1      literal
#   HOUSING/TRADE_GOODS/REPEAT          -2      literal
#   everything else                      0      literal
#
# Level 3 is `Calculate_Current_Production_Turn_Count`
# (colony.cpp:407-419: 1 when bought, 10000 for "never"), which
# the engine computes from `Colony_Product_Cost` — config-bound, so
# HD never computes it: CSUM carries it for every colony of the list
# (`core.colsumblock`), and a row without the block compares EQUAL at
# this level (UNVERIFIED live: the engine without open fix 110 sends no
# CSUM; the tie then stays in array order, as before work order 437).

#: colsum_details.cpp:329-350, literal for literal.
TIER_FREIGHTERS = 9999
TIER_QUEUED_SHIP = 10000
TIER_BUILDING = 10
_TIER_MINUS_ONE = (-4, -5, -6, -7, -1)      # FARMER WORKER SCIENTIST SPY NONE
_TIER_MINUS_TWO = (-3, -2, -10)             # HOUSING TRADE_GOODS REPEAT


def sort_tier(production_id, ship_size=None):
    """`Prod_To_Sort_Type`. `ship_size` is the queued ship's `d.size`
    (`ShipNames.size`); None — an index past the wire's ship records —
    counts as 0, the bottom of the ship band, which still sits where the
    source puts it (above every building)."""
    from core import buildcost
    try:
        value = int(production_id)
    except (TypeError, ValueError):
        return 0
    if value <= QUEUED_SHIP_BASE:
        return TIER_QUEUED_SHIP + int(ship_size or 0)
    if value == -15:
        return TIER_FREIGHTERS
    if buildnames.is_building(value):
        return int(buildcost.cost(value) or 0) + TIER_BUILDING
    if value in _TIER_MINUS_ONE:
        return -1
    if value in _TIER_MINUS_TWO:
        return -2
    return 0


class _ProdOrder:
    """`cmp_Prod` as a sort key.

    A comparator rather than a tuple because level 2 is a DESCENDING
    string compare and a key tuple cannot negate a string. Equal on all
    three levels compares EQUAL, and `list.sort` being stable leaves
    them in array order: the tie behaviour the other six keys have and
    the original's (`cmp` returns 0 on equality and `Sort_Col_List`
    swaps only on strictly greater than zero, colsum_details.cpp:62-77).
    The row carries `producing_tier` and `producing_turns_raw`
    (`colonyrows`); a row without them (a stand-in) falls back to the id
    alone.
    """

    __slots__ = ("tier", "name", "turns")

    def __init__(self, row):
        tier = row.get("producing_tier")
        self.tier = (tier if tier is not None
                     else sort_tier(row.get("producing_id")))
        self.name = row.get("producing") or ""
        self.turns = row.get("producing_turns_raw")

    def __lt__(self, other):
        if self.tier != other.tier:
            return self.tier > other.tier          # level 1, descending
        if self.name != other.name:
            return self.name > other.name          # level 2, descending
        if self.turns is None or other.turns is None:
            return False                           # no CSUM: a tie
        return self.turns < other.turns            # level 3, ascending

    def __eq__(self, other):
        return (self.tier == other.tier and self.name == other.name and
                (self.turns is None or other.turns is None or
                 self.turns == other.turns))


def sort_key(row):
    """The `producing` key (`cmp_Prod`, all three levels)."""
    return _ProdOrder(row)


class Resolver:
    """Both loaders behind one object, so the row builder takes one.

    It exists because `production_name` needs TWO files and
    `build_rows` should not learn that: the row builder asks one
    thing "what is this colony producing" and gets a word and a
    state. Held on the App like the help texts, loaded once.

    `state` is the WORST of the two, and that is deliberate rather
    than convenient — a screen whose building names are extracted and
    whose option strings are not is not "ok", and reporting the
    better of the two is how a half-configured install looks fine
    until it meets a row that needs the missing half.
    """

    def __init__(self, buildings=None, strings=None):
        self.buildings = buildings
        self.strings = strings

    @property
    def state(self):
        states = [getattr(self.buildings, "state", "missing"),
                  getattr(self.strings, "state", "missing")]
        for worse in ("stale", "missing"):
            if worse in states:
                return worse
        return "ok"

    def name(self, production_id, ships=None):
        """(text, state) — `production_name` with both files bound, and
        the snapshot's `ShipNames` for the two ship branches."""
        return production_name(production_id, self.buildings, self.strings,
                               ships=ships)
