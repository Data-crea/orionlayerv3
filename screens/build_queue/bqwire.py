"""The build popup (wire id 25): its geometry and its state off the wire.

`COLBLDG::Build_Queue_Popup_` (colbldg.cpp:458-571), a switched screen of
its own id reached from the colony screen's CHANGE and the Colonies
screen's producing column. Inventory: `~/orionlayerv3-dev/doc/briefs/180-build-inventory.md`.

**IT CLAIMS ITS ID ONLY WITH FOUR BLOCKS** — open fix 35's colony, 38's
cost and turns (the summary's "Turn(s) Left"), 39's queue under edit and
40's two lists, which the engine writes together on screen 25 (applied by
work order 181, required by `tools/version_check.py`); without them the
game's picture stands, as before.
With them, the colony is used only when the pair and the handle agree
(the first tick carries the previous handle, `screens/colony/colwire`),
and the lists only when their LENGTHS equal the rows the live field list
carries at x 13 and x 485 — the list's own count is the second source for
the block's, and a disagreement is a screen that cannot vouch for what it
would draw (it hands over, and the gate counts it as a failure).

Geometry: every rectangle is a literal of colbldg.cpp (§2b of the
reading); the list and queue rows are the live list's own fields, found
by their x and sorted by y, so a squished list lands where the game put
it (`Calculate_Squish_Step_`, coldraw.cpp:12-34).
"""
from core.structs import colony as colony_struct
from core.structs import planet as planet_struct

GAME_SCREEN_ID = 25                      # orion2_consts.h:482
TYPE_BUTTON, TYPE_RADIO, TYPE_HIDDEN = 0, 1, 7
BUILDING_COUNT = 49                      # s_colony.buildings[49]
SEPARATOR = -9                           # COLONY_PRODUCTION_SEPARATOR
NONE = -1                                # COLONY_PRODUCTION_NONE

#: The frame's windows (the help table's rectangles, erichelp.cpp:49-63).
BUILDINGS_BOX = (13, 9, 184, 469)
PICTURE_BOX = (203, 9, 285, 103)
SUMMARY_BOX = (302, 10, 462, 103)
OTHERS_BOX = (482, 10, 626, 308)
DESCRIPTION_BOX = (204, 114, 461, 302)
QUEUE_BOX = (207, 332, 458, 465)
#: "Build List for %s", `Squeeze_Paragraph_Centered_(235, 309, 194, 17)`.
TITLE = (235, 309, 194, 17)
#: The summary lines: `Print_(306, 21 + 13n)` (colbldg.cpp:830, :1125).
SUMMARY_X, SUMMARY_Y, SUMMARY_PITCH, SUMMARY_W = 306, 21, 13, 156
#: The queue rows' text: `Squeeze_Print_Centered_(332, 335 + 20i, …, 251)`.
QUEUE_TEXT_X, QUEUE_TEXT_Y, QUEUE_PITCH, QUEUE_W = 332, 335, 20, 251
LIST_X_BUILDINGS, LIST_X_OTHERS = 13, 485

#: The buttons by (type, x, y) — the live list gives the rect.
CANCEL = (TYPE_BUTTON, 493, 447)
OK = (TYPE_BUTTON, 560, 447)
REFIT = (TYPE_BUTTON, 492, 379)
DESIGN = (TYPE_BUTTON, 561, 379)
REPEAT = (TYPE_BUTTON, 503, 411)
AUTO_BUILD = (TYPE_RADIO, 490, 342)

HELP = ((501, BUILDINGS_BOX), (502, PICTURE_BOX), (503, SUMMARY_BOX),
        (504, OTHERS_BOX), (505, DESCRIPTION_BOX), (506, QUEUE_BOX),
        (507, (490, 342, 623, 363)), (508, (492, 379, 552, 397)),
        (509, (561, 379, 621, 397)), (510, (503, 411, 615, 431)),
        (537, (493, 447, 554, 465)), (511, (560, 447, 623, 465)),
        (512, (1, 1, 638, 478)))

#: The blocks the engine writes on screen 25 (open fixes 35, 38-40).
BLOCKS = ("colony_screen", "colony_product", "build_queue", "build_lists")

READY, WAITING, GAME_BOX, MISMATCH = "READY", "WAITING", "GAME_BOX", \
    "MISMATCH"


def claims(state):
    return (getattr(state, "current_screen", None) == GAME_SCREEN_ID
            and all(getattr(state, k, None) is not None for k in BLOCKS))


def live_field(fields, ident):
    ftype, x, y = ident
    return next((f for f in (fields or []) if (f.x, f.y) == (x, y)
                 and f.field_type == ftype), None)


def rows_at(fields, x):
    """The list rows the game built at native x, top to bottom."""
    return sorted((f for f in (fields or []) if f.field_type == TYPE_HIDDEN
                   and f.x == x and f.y < 470), key=lambda f: f.y)


def queue_rows(fields):
    return sorted((f for f in (fields or []) if f.field_type == TYPE_HIDDEN
                   and f.x == 207 and 329 <= f.y <= 449),
                  key=lambda f: f.y)


class View:
    def __init__(self, state):
        self.state, self.reason = WAITING, ""
        self.index = -1
        self._read(state)

    @property
    def draws(self):
        return self.state == READY

    def _read(self, state):
        block = state.colony_screen
        planets = [planet_struct.parse(r) for r in
                   (getattr(state, "planets_raw", None) or [])]
        at = [p for p in planets if p.star_index == block["star"]
              and p.orbit == block["orbit"]]
        derived = at[0].colony_index if at else -1
        raws = getattr(state, "colonies_raw", None) or []
        if derived < 0 or derived != block["colony"] or \
                not 0 <= derived < len(raws):
            self.reason = "The popup's colony is not settled yet."
            return
        fields = getattr(state, "fields", None) or []
        if live_field(fields, CANCEL) is None:
            self.state = GAME_BOX
            self.reason = ("The game has opened its own box over the build "
                           "list; its fields are the only ones on the wire.")
            return
        lists = state.build_lists
        self.buildings = lists["buildings"]
        self.others = lists["others"]
        self.queue_numbers = lists.get("queue", [])
        self.building_rows = rows_at(fields, LIST_X_BUILDINGS)
        self.other_rows = rows_at(fields, LIST_X_OTHERS)
        if len(self.building_rows) != len(self.buildings) or \
                len(self.other_rows) != len(self.others):
            self.state = MISMATCH
            self.reason = (f"The lists the game sent ({len(self.buildings)} "
                           f"buildings, {len(self.others)} others) and the "
                           f"rows it built ({len(self.building_rows)}, "
                           f"{len(self.other_rows)}) disagree.")
            return
        self.state = READY
        self.index = derived
        self.colony = colony_struct.parse(raws[derived])
        self.planet = at[0]
        q = state.build_queue
        self.items = q["items"]
        self.active = q["active"]
        self.field_mode = q["field_mode"]
        self.auto_building = q["auto_building"]
        self.queue = queue_rows(fields)

    def queued(self, product):
        """`Has_Prod_In_Queue_`: the item is in the queue under edit."""
        return product in self.items

    def active_queue_row(self):
        """`Draw_Build_Queue_`'s `active_idx` (colbldg.cpp:714): a queue row
        when `_active_prod[0]` is BUILDING_COUNT or more, else -1."""
        a = self.active[0]
        return -1 if a < BUILDING_COUNT else a - BUILDING_COUNT

    def entry(self, product):
        """BLDL's numbers for a product in either list, or None."""
        for e in list(self.buildings) + list(self.others) + \
                list(self.queue_numbers):
            if e["id"] == product and e["cost"] >= 0:
                return e
        return None
