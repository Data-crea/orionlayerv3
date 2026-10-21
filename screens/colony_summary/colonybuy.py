"""BUY in the Colonies list — work order 322 B1.

The v2 colsum.cpp lines below are the tree before open fix 110, which
moves them by 8 (they all follow :207): :346 is :354, :394-405 is :402-413.

WHEN THE ORIGINAL DRAWS IT (`COLSUM::Add_Fields_`, colsum.cpp:292-303, v2
:394-405): one field per occupied slot of the game's ten, at native x 599,
y `buy_btn_y_coords[slot]` (colsum.cpp:254, v2 :346):

    Colony_Can_Buy_Product_0_ == 0 && bought_outright == 0
                    -> Add_Hidden_Field_     (type 7, nothing drawn)
    otherwise       -> Add_Locked_Button_Field_ (type 2, the BUY sprite;
                       drawn down while `_list_buy_data[slot]`, the
                       colony's `bought_outright`, is set — fields.cpp
                       v2 :1825-1845)

`Colony_Can_Buy_Product_0_` (colony.cpp:601, v2 :569-585) asks the cost to
buy, the treasury and the blockade — the cost is `Colony_Product_Cost_`,
whose building, lander-ship and misc tables v2 reads from its config. So
HD never decides it: in the game's window **the field list is the
decision** (P816) — the live field at (599, y) of the slot says what the
game drew: type 2 is BUY, type 7 is none — and outside it the engine's own
answer, `Colony_Can_Buy_Product_0` per colony in CSUM (open fix 110).

WHAT A CLICK DOES (`Evaluate_Col_List_Input_`, colsum.cpp:952-955, v2
:1129-1131): `COLONY::Tested_Colony_Buys_Outright_` (colony_main.cpp:740,
v2 :719-776) — a bought product is un-bought, else the game's own boxes:
the confirmation "spend %d BC to buy %d production", or why not (blockade,
housing or trade goods, short by %d BC). HD sends the slot's own field and
the boxes are HD's message box (MSGB, open fix 29).

TRANSCRIPTION `list_buy`: drawn where the game's field is a locked button,
selected while `bought_outright` is set — whether HD can name the product or
not; a click on a row the game's window shows activates that slot's buy
field at once, any other row's after the window is stepped to it
(`colonyjump`, decision 21). The click stays in flight until its effect is
on the wire — the slot's field or `bought_outright` changed, a box up
(MSGB), or another screen — and the screen takes no click meanwhile, so a
second click is never sent from the snapshot before the first one's effect.
TRANSCRIPTION `buy_csum` (work order 322 B2): a row outside the game's
window has BUY by `Add_Fields`' own rule — `Colony_Can_Buy_Product_0` or
`bought_outright` — with the first read from CSUM (open fix 110,
`core/colsumblock.py`: the engine's answer per colony of its list), the
second from the colony's record; a click steps the window to it and
sends the slot's field only if the list just read shows it drawn (P816).
HD STATE `buy_off_window` (narrowed by 322 B2): without CSUM a row
outside the game's ten slots shows no BUY — the field list says nothing
about it; a list whose order does not bind shows none at all.
UNVERIFIED `colsum_block_live`: CSUM itself was never seen from a
running engine. OMISSION `hidden_buy_field`: the original's hidden field under an
undrawn BUY still answers a click with the refusal boxes; HD draws nothing
there and offers no target. UNVERIFIED `list_buy_live`: the click and the
game's confirmation were never seen live — no live runs (Data, 20 October
2026).
"""
from core import colsumblock
from core.structs import colony as colony_struct

from . import colonybuild, colonyjump, colonypick, colonytrack
from .colonyselect import GameWindow

#: `buy_btn_y_coords` (colsum.cpp:254, v2 :346) and the x of every buy
#: field (colsum.cpp:296, :302; v2 :398, :404).
BUY_X = 599
BUY_Y = (35, 65, 96, 128, 159, 190, 221, 251, 283, 314)
#: `FIELD_TYPE_LOCKED` and `FIELD_TYPE_HIDDEN` (orion2_consts.h:238, :244).
TYPE_LOCKED, TYPE_HIDDEN = 2, 7

BUY, BOUGHT, NONE = "buy", "bought", "none"


def live_buy_field(state, slot):
    """The live field of slot `slot`'s buy control, or None."""
    if not 0 <= int(slot) < len(BUY_Y):
        return None
    at = (BUY_X, BUY_Y[int(slot)])
    return next((f for f in (getattr(state, "fields", None) or [])
                 if getattr(f, "index", 0) > 0 and (f.x, f.y) == at), None)


def slot_state(state, slot, bought_outright):
    """BUY, BOUGHT or NONE for the game's slot, or None when the live list
    has no field there."""
    field = live_buy_field(state, slot)
    if field is None:
        return None
    if field.field_type != TYPE_LOCKED:
        return NONE
    return BOUGHT if bought_outright else BUY


def annotate(rows, state, sort_key, order_known=True):
    """Set every row's `can_buy` from the game's field list: False (no BUY
    drawn), BUY, or BOUGHT (drawn selected) — the one key the row dict
    already carries (check 022 pins the set), now three-valued.

    `rows` are the screen's rows in the game's order. A row the game's
    window shows is decided by its slot's field; any other by CSUM
    (TRANSCRIPTION `buy_csum`), and without CSUM it stays False (HD STATE
    `buy_off_window`). The slots are read once per snapshot: the window is read off the game's
    scroll thumb, a framebuffer walk the frames between snapshots need
    not repeat."""
    for row in rows:
        row["can_buy"] = False
    if state is None or not rows or not colonypick.sort_binds(
            sort_key, order_known):
        return
    # The slots are a function of the snapshot's field list and picture
    # (the thumb) and of the row order: all four are in the key.
    key = (id(getattr(state, "fields", None)),
           id(getattr(state, "framebuffer", None)),
           id(getattr(state, "colony_list_numbers", None)),
           tuple(row["index"] for row in rows))
    if _CACHE["state"] is not state or _CACHE["key"] != key:
        _CACHE.update(state=state, key=key, map=_slots(rows, state))
    for position, value in _CACHE["map"].items():
        rows[position]["can_buy"] = value


_CACHE = {"state": None, "key": None, "map": {}}


def _slots(rows, state):
    """{row position: BUY or BOUGHT}: the rows in the game's window by
    their slot's field, the others by CSUM when the engine sends it."""
    first = colonyjump.game_first(state, len(rows))
    if first is None:
        return {}
    raws = getattr(state, "colonies_raw", None) or []

    def bought(index):
        raw = raws[index] if 0 <= index < len(raws) else None
        try:
            return colony_struct.parse(raw).bought_outright if raw else 0
        except ValueError:
            return 0

    block = getattr(state, "colony_list_numbers", None)
    if block is not None and block["first"] != first:
        # Two sources of the window, the thumb and CSUM, disagree: no
        # slot can be named (work order 322 B2).
        return {}
    out = {}
    for slot in range(GameWindow.SLOTS):
        position = first + slot
        if position >= len(rows):
            break
        if not csum_names(state, first, slot, rows[position]["index"]):
            continue
        got = slot_state(state, slot, bought(rows[position]["index"]))
        if got in (BUY, BOUGHT):
            out[position] = got
    if not colsumblock.available(state):
        return out
    for position, row in enumerate(rows):
        if first <= position < first + GameWindow.SLOTS:
            continue
        # `Add_Fields`' test (colsum.cpp:405, the tree with open fix 110):
        # the locked button unless both are 0; drawn down while bought.
        csum = colsumblock.of_colony(state, row["index"])
        if bought(row["index"]):
            out[position] = BOUGHT
        elif csum is not None and csum["can_buy"]:
            out[position] = BUY
    return out


def csum_names(state, first, slot, colony):
    """Does CSUM agree that slot `slot` of the window at `first` is
    colony `colony`? True without the block (the field list alone, as
    before open fix 110); with it, CSUM's `first` must be `first` and its
    list must hold `colony` at `first + slot` — the thumb and the
    engine's list, two sources, before a slot's field is used."""
    block = getattr(state, "colony_list_numbers", None)
    if block is None:
        return True
    at = block["first"] + int(slot)
    return (block["first"] == first and 0 <= at < len(block["rows"])
            and block["rows"][at]["colony"] == colony)


def rect(screen, row_index):
    """Where row `row_index`'s BUY is drawn, or None: the list's own area,
    bands and building column (as `colonylist.render` lays them out) and
    `colonybuild.buy_rect`, the function the drawing uses (decision 5)."""
    rows = screen._rows
    area, _cfg, scale, _n = screen._list_view()
    first = screen._first
    if not 0 <= row_index - first < len(rows) - first or not area.w:
        return None
    cfg = colonybuild.list_cfg(screen)
    cols = colonytrack.columns(area, cfg)
    bands = colonytrack.row_bands(area, cfg, scale, len(rows) - first)
    band = row_index - first
    if not cols or band >= len(bands):
        return None
    x, w = cols["building"]
    y, h = bands[band]
    return colonybuild.buy_rect(rows[row_index], x, y, w, h, cfg,
                                screen.style, screen.layout)


def start(client, state, *, colony, position, n_colonies, sort_key,
          order_known=True):
    """The click: a `colonyjump.Jump` that ends on the slot's buy field and
    waits for its effect (`_effect`), refused before anything is sent where
    the jump refuses (decision 33) or where the field there is no longer a
    drawn BUY. A row outside the game's window (BUY from CSUM) is stepped
    to first; the field is then decided from the list read after the last
    step (P816)."""
    def open_field(now, slot):
        # The list just read decides (P816); with CSUM the slot must also
        # be this colony's in the engine's own list at the thumb's window,
        # or nothing is sent — a re-sort under the jump would otherwise
        # buy another colony's product.
        first = colonyjump.game_first(now, n_colonies)
        if first is None or not csum_names(now, first, slot, colony):
            return None
        return _drawn_buy_field(now, slot)

    return colonyjump.Jump(
        client, state, colony=colony, position=position,
        n_colonies=n_colonies, sort_key=sort_key, order_known=order_known,
        open_field=open_field, what="buy", in_window=True,
        wait_open=lambda sent, now, slot: _effect(sent, now, slot, colony))


def _bought(state, colony):
    raws = getattr(state, "colonies_raw", None) or []
    if not 0 <= colony < len(raws) or not raws[colony]:
        return None
    try:
        return colony_struct.parse(raws[colony]).bought_outright
    except ValueError:
        return None


def _field_type(state, slot):
    field = live_buy_field(state, slot)
    return None if field is None else field.field_type


def _effect(sent, now, slot, colony):
    """What `Tested_Colony_Buys_Outright_` leaves on the wire: a box
    (its confirmation or a refusal, MSGB), another screen, the colony's
    `bought_outright` (an un-buy) or the slot's field changed."""
    if getattr(now, "message_box", None) is not None:
        return True
    if getattr(now, "current_screen", 20) != getattr(sent, "current_screen",
                                                     20):
        return True
    return (_bought(now, colony) != _bought(sent, colony)
            or _field_type(now, slot) != _field_type(sent, slot))


def _drawn_buy_field(state, slot):
    field = live_buy_field(state, slot)
    return field if field is not None and \
        field.field_type == TYPE_LOCKED else None
