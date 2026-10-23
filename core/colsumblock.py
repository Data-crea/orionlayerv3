"""The Colonies list's numbers on the wire — open fix 110, "CSUM" (work order 322 B2).

    "CSUM"  (`doc/ext_colsum_block.patch`): written after STLR, only while
            SCREEN_COLONY_SUMMARY is up and its list exists. A version byte
            (1), int16 `COLSUM::first`, int16 n (the game's list,
            `COLXPORT::g_colony_list_ptr`, at most MAX_COLONIES), then per
            colony in the game's order: int16 colony index, int16
            `producing[0]`, int32 `COLCALC::Colony_Producing_Product_Cost`,
            int32 `COLCALC::Colony_Cost_To_Buy_Producing_Product`, int16
            `COLONY::Calculate_Current_Production_Turn_Count`, uint8
            `COLONY::Colony_Can_Buy_Product_0`; then the ten int16
            `COLSUM::list_buy_fields`.

WHY: the list prints "name - Nt" from the turn count (colsum.cpp:741,
the branch :751-774, E 0x27 at :765 — the tree with open fix 110; :733,
:743-766 before it) and adds BUY where `Colony_Can_Buy_Product_0` or
`bought_outright` holds (`Add_Fields`, :405-413; :397-405 before). Both follow from `Colony_Product_Cost` (colcalc.cpp:2645),
whose tables v2 reads from its config — so no client can compute them,
and the field list answers BUY only for the ten rows of the game's
window. The engine sends what it computes; HD reads it here and nowhere
else (decision 97).

Read WHOLE or left None (`core/colonyblocks.py`'s rule): an engine without
the fix writes none, and the list keeps drawing no suffix and BUY only for
the rows the game's window shows. A refused block leaves `pos` where it
was, so a block after it would be misread — harmless: the one block after
it, FILM (open fix 112, `core/filmblock.py`), is written only under the
film's own id 86, never with the Colonies screen up.

OMISSION `autobuild_line`: under autobuild the original prints E 0x5C
"%sAutobuilding%s\n%s - %dt" (E 0x5D without a count, plus " [Q%d]" for a
preset; colsum.cpp:744-749, :755-781). Whether autobuild is active needs
`BUILD_QUEUE::autobuild_settings`, which the wire carries only on the
colony screen (COLS); HD prints the name and "- Nt" alone.
"""
import struct as _st

from core.blockreader import Reader

HEAD = "<Bhh"
ROW = "<hhiihB"
ROW_SIZE = _st.calcsize(ROW)
BUY_FIELDS = 10
#: `COLONY_PRODUCTION_NONE` (orion2_consts.h:66): the original prints no
#: suffix for it (colsum.cpp:751, the tree with open fix 110).
PRODUCING_NONE = -1
#: The suffix is printed for a turn count in 1..9999 (colsum.cpp:753);
#: `Calculate_Current_Production_Turn_Count` answers 10000 for "never"
#: (colony.cpp:425-427).
TURNS_MIN, TURNS_MAX = 1, 9999
#: MAX_COLONIES (consts.h:8-11: MAX_PLANETS, MAX_STARS * 5): n's bound.
MAX_COLONIES = 1024 * 5


def parse(gs, data, pos):
    """Read CSUM at `pos` into `gs.colony_list_numbers` (None when absent,
    short or of another version, else a dict). Returns the new position."""
    gs.colony_list_numbers = None
    r = Reader(data, pos)
    if not r.enter(b"CSUM"):
        return pos
    if not r.fits(_st.calcsize(HEAD)):
        r.refuse("CSUM", "short", f"{r.left()} bytes")
        return pos
    version, first, n = r.take(HEAD)
    if version != 1 or not 0 <= n <= MAX_COLONIES or \
            not r.fits(n * ROW_SIZE + 2 * BUY_FIELDS):
        r.refuse("CSUM", "version, count or length",
                 f"version {version}, {n} rows")
        return pos
    rows = []
    for _ in range(n):
        colony, producing, cost, buy_cost, turns, can_buy = r.take(ROW)
        rows.append({"colony": colony, "producing": producing,
                     "cost": cost, "buy_cost": buy_cost, "turns": turns,
                     "can_buy": bool(can_buy)})
    buy_fields = list(r.take(f"{BUY_FIELDS}h"))
    gs.colony_list_numbers = {
        "first": first, "rows": rows, "buy_fields": buy_fields,
        "by_colony": {row["colony"]: row for row in rows}}
    return r.pos


def build(first=0, rows=(), buy_fields=None):
    """The block as the engine writes it — for the checks' stand-ins.
    `rows`: dicts with the keys `parse` gives (missing ones 0)."""
    out = b"CSUM" + _st.pack(HEAD, 1, first, len(rows))
    for r in rows:
        out += _st.pack(ROW, r.get("colony", 0), r.get("producing", 0),
                        r.get("cost", 0), r.get("buy_cost", 0),
                        r.get("turns", 0), 1 if r.get("can_buy") else 0)
    fields = list(buy_fields or [-1000] * BUY_FIELDS)
    return out + _st.pack(f"<{BUY_FIELDS}h", *fields)


def available(state):
    """Does the engine carry open fix 110? (The block comes on the
    Colonies screen only.)"""
    return getattr(state, "colony_list_numbers", None) is not None


def of_colony(state, colony):
    """CSUM's row for colony index `colony`, or None (no block, or the
    colony is not in the game's list)."""
    block = getattr(state, "colony_list_numbers", None)
    return None if block is None else block["by_colony"].get(colony)


def turn_suffix(row):
    """The N of "- Nt" as the original prints it, or 0 for none: only for
    a product other than none and a count in 1..9999 (colsum.cpp:751-753,
    E 0x27 at :765; the autobuild form is OMISSION `autobuild_line`)."""
    if row is None or row["producing"] == PRODUCING_NONE:
        return 0
    turns = row["turns"]
    return turns if TURNS_MIN <= turns <= TURNS_MAX else 0
