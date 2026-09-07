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
      id <= COLONY_PRODUCTION_QUEUED_SHIP_BASE (-100). NOT ANSWERED:
      `d.name` is not on the wire. `core/structs/ship.py` verifies
      five fields — owner, status, location, x, y — and a name at a
      guessed offset is exactly what decision 23 forbids.

and `Option_String_`'s own tail splits once more: a SHIP DESIGN id
(-99..-50, colbldg.h:24) returns
`_player[owner].ship_designs[idx].name`, which is not on the wire
either, and anything else pops an error dialog and returns the empty
string (colbldg.cpp:2380-2384).

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


def production_name(production_id, buildings=None, strings=None):
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
        # NOT A MISSING FILE — a field that is not on the wire. The
        # column must not offer `techname_extract` as the fix for it.
        return None, STATE_UNSOURCED
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


# ── The sort key: `cmp_Prod_` as far as it is sourced ───────────────
#
# `cmp_Prod_` (colsum.cpp:1091-1116) is THREE levels, and the
# direction is not what this project's table said. `Switched_cmp_`
# case 5 does NOT negate (colsum.cpp:395) — unlike cases 1,2,3,4,6 —
# but `cmp_Prod_` negates internally, twice:
#
#   1  -cmp_(Prod_To_Sort_Type_(a), Prod_To_Sort_Type_(b))  DESCENDING
#   2  -sign(strcmp(Selection_Name_(a), Selection_Name_(b))) DESCENDING
#   3   cmp_(turn_count(a), turn_count(b))                  ascending
#
# so producing is DESCENDING on tier and DESCENDING on name, and the
# comment block in `colonyrows` calling it "ascending" was wrong.
# Level 2 is `strcmp`, CASE-SENSITIVE — `cmp_Alpha_` uses
# `strcasecmp` (colsum.cpp:1053) and this one does not, which is a
# difference between the two keys and not a slip in one of them.
#
# WHAT IS SOURCED AND WHAT IS NOT. `Prod_To_Sort_Type_`
# (colsum.cpp:1212-1264) transcribes completely except in one place:
#
#   queued ship      _ship[i].d.size + 10000    not on the wire
#   FREIGHTERS                        9999      literal
#   building         _buildings[id].cost + 10   COST TABLE, absent
#   FARMER/WORKER/SCIENTIST/SPY/NONE    -1      literal
#   HOUSING/TRADE_GOODS/REPEAT          -2      literal
#   everything else                      0      literal
#
# Building costs live in the player's techname.lbx beside the names
# and are NOT extracted — `techname_extract` takes names only. But
# the cost is `>= 0`, so `cost + 10 >= 10`: every building outranks
# every option (0, -1, -2) and is outranked by FREIGHTERS and by any
# queued ship. **The TIER ORDER is fully sourced; only the order of
# buildings AMONG THEMSELVES is not.** That is why this key sorts
# correctly for the reference save, where no colony builds a
# building, and is still declared unavailable: a set with two
# buildings in it would order them by name where the original orders
# them by cost, and a control that is right on one save and wrong on
# the next is worse than one that says it cannot do the job.

#: The tier every building collapses into while `_buildings[].cost`
#: is not extracted. 10 is `cost + 10` at cost 0 — the bottom of the
#: building band, so the band still sits where the source puts it.
BUILDING_TIER_UNSOURCED = 10

#: colsum.cpp:1218-1239, literal for literal.
TIER_FREIGHTERS = 9999
_TIER_MINUS_ONE = (-4, -5, -6, -7, -1)      # FARMER WORKER SCIENTIST SPY NONE
_TIER_MINUS_TWO = (-3, -2, -10)             # HOUSING TRADE_GOODS REPEAT


def sort_tier(production_id):
    """`Prod_To_Sort_Type_`, with the two unsourced branches folded.

    A queued ship is `d.size + 10000` and `d.size` is not on the
    wire, so every queued ship shares one tier — above everything
    else, which is where the source puts the whole band.
    """
    try:
        value = int(production_id)
    except (TypeError, ValueError):
        return 0
    if value <= QUEUED_SHIP_BASE:
        return 10000
    if value == -15:
        return TIER_FREIGHTERS
    if buildnames.is_building(value):
        return BUILDING_TIER_UNSOURCED
    if value in _TIER_MINUS_ONE:
        return -1
    if value in _TIER_MINUS_TWO:
        return -2
    return 0


class _ProdOrder:
    """`cmp_Prod_`'s first two levels as a sort key.

    A comparator rather than a tuple because level 2 is a DESCENDING
    string compare and a key tuple cannot negate a string. Level 3 —
    `Calculate_Current_Production_Turn_Count_` — is not implemented,
    so equal tier and equal name compare EQUAL, and `list.sort` being
    stable leaves them in array order. That is the same tie behaviour
    the other six keys have and it is the original's: `cmp_` returns
    0 on equality and `Sort_Col_List_` swaps only on strictly greater
    than zero (colsum.cpp:363, :1056).
    """

    __slots__ = ("tier", "name")

    def __init__(self, row):
        self.tier = sort_tier(row.get("producing_id"))
        self.name = row.get("producing") or ""

    def __lt__(self, other):
        if self.tier != other.tier:
            return self.tier > other.tier          # level 1, descending
        return self.name > other.name              # level 2, descending

    def __eq__(self, other):
        return self.tier == other.tier and self.name == other.name


def sort_key(row):
    """The `producing` key. See the block above for what it cannot do."""
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

    def name(self, production_id):
        """(text, state) — `production_name` with both files bound."""
        return production_name(production_id, self.buildings, self.strings)
