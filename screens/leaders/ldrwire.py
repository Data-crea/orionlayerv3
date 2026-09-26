"""What the wire lets the Leaders screen believe, and what it does not.

`View` is built from ONE snapshot and says, in one of six states, what
HD may draw and what it may send. It holds no rule the screen could
also hold: `screen.py` turns the answer into pixels and sends.

WHAT IS ON THE WIRE WITHOUT ANY PATCH, and how each is read:

  the leaders      all 67 records (ext_api.cpp:156-159), verified
                   (`core/structs/leader.py`)
  the VIEW         the ship view adds the scroll arrows `-` / `+` and the
                   colony view does not (officer.cpp:2942-2963) — read
                   off the field list, never remembered
  HIRE MODE        CANCEL `X` replaces HIRE `H` (officer.cpp:2857-2881)
  the rows         `Build_Captain_Id_List_` rebuilt from the records
                   (`core/leaderskills.captain_id_list`) and CHECKED
                   against the list: one text field per row
                   (officer.cpp:2913-2936). A disagreement is a refusal.
  the buttons      each live field by type and rectangle
                   (decision 20; `ldrgeom.button_rect`)
  a native box     `core/gamebox.detect` — the confirmation, the message
                   and the warning, and the text boxes that share the
                   warning's one catcher
  the hire popup   its two buttons at the popup's own rectangles
                   (`ldrpopup`)

**AND WHAT THE OFFS BLOCK ADDS — open fix 30, APPLIED** (work order 175,
orion2re orionlayer-local cc542e02). The button mode beyond hire, the
selection, the colony view's displayed and chosen star, the ship view's
stack, grid and scroll row, the popup's leader (`doc/ext_officer_
screen_state.patch`). With it `sendable()` lets POOL, DISMISS, PREV /
NEXT, the scroll arrows, every leader click and the galaxy box and grid
(`ldrmap`) go: the game answers in state HD reads back. An engine
WITHOUT the fix still sends no block — `View.block` is None, and then
`sendable()` says no to everything whose effect HD could not see
confirmed, as before: a click on a leader in pool or dismiss mode ACTS
(officer.cpp:1415-1438), so guessing the mode would be sending an order
nobody gave (decision 65). `tools/version_check.py` names such an
engine.
"""
from core import gamebox
from core import leaderskills as ls
from core import livefields
from core.structs import leader as leader_struct

from . import ldrgeom as geom
from . import ldrpopup

#: The six states. READY and WAITING and IN_BOX and POPUP keep the HD
#: picture up; the two refusals hand over (decision 22).
READY = "ready"
WAITING = "waiting"          # screen 29, the list not built yet
IN_BOX = "in_box"            # a native box is up over the screen
POPUP = "popup"              # the hire popup is up over the screen
MISMATCH = "mismatch"        # a list that disagrees with the rebuild
UNVALIDATED = "unvalidated"  # no list of this screen's, past the bound

#: How long WAITING may last before it is UNVALIDATED, in snapshots.
#: Work order 166's measured bound for the research screen (22 frames,
#: three times over); a bound is the give-up, never a timer — what ends
#: the wait is the list arriving (decision 21). The Leaders screen's own
#: entry has not been measured live (parked, item L).
WAIT_BOUND = 66


def _live(fields, name):
    """The live field for one button — type and rectangle — or None."""
    (_xy, _hk, ftype, _art) = geom.BUTTONS[name]
    return livefields.live_field(fields, {"field_type": ftype,
                                          "rect": geom.button_rect(name)})


def _has(fields, ftype, rect):
    return livefields.live_field(fields, {"field_type": ftype,
                                          "rect": rect}) is not None


def is_officer_list(fields):
    """True when the list is this screen's: its RETURN, its two tabs and
    the catch-all it adds last (officer.cpp:2883-2908, :3013-3020).

    The catcher alone is not enough: the Fleets screen ends with the
    same rectangle (flt1.cpp:1262). RETURN at (538, 441) and the two
    tab fields are this screen's own.
    """
    live = [f for f in (fields or []) if f.index != 0]
    if not live:
        return False
    catcher = any(livefields.rect(f) == geom.CATCHER
                  and f.field_type == geom.TYPE_HIDDEN and f.hotkey == 0
                  for f in live)
    return (catcher and _live(live, "return") is not None
            and _live(live, "tab_colony") is not None
            and _live(live, "tab_ship") is not None)


def leaders_of(game_state):
    """The 67 parsed records, or [] when the snapshot has none."""
    raw = getattr(game_state, "leaders_raw", None) or []
    if len(raw) != leader_struct.COUNT:
        return []
    return leader_struct.parse_all(raw)


class View:
    """One snapshot's answer. Construct, then read the attributes."""

    def __init__(self, game_state, waited=0, warlord_of=None,
                 last_view=None):
        self.state = UNVALIDATED
        self.reason = ""
        self.view = geom.VIEW_COLONY
        self.hire_mode = False
        self.rows = []               # leader ids, in display order
        self.buttons = {}            # name -> live FieldInfo
        self.box = None              # gamebox.GameBox
        self.popup = None            # ldrpopup.Popup
        self.leaders = leaders_of(game_state)
        self.player = int(getattr(game_state, "player_num", 0) or 0)
        self.block = getattr(game_state, "officer_screen", None)
        self.fields = [f for f in (getattr(game_state, "fields", None) or [])
                       if f.index != 0]
        self._warlord_of = warlord_of or (lambda _p: False)
        #: True when `view` was READ — off the list or the block — in
        #: this snapshot, False when a box or the popup hid it and the
        #: screen has to keep the view it last read.
        self.view_known = False
        self._last_view = last_view
        self._classify(waited)

    # ── The decision ───────────────────────────────────────

    def _classify(self, waited):
        if not self.leaders:
            self.reason = ("The snapshot carries no leader records, so "
                           "there is nothing to list.")
            return
        box = gamebox.detect(self.fields)
        if box is not None:
            self.box, self.state = box, IN_BOX
            self._view_from_block_or_keep()
            self.rows = self._rebuild()
            return
        popup = ldrpopup.detect(self.fields, self)
        if popup is not None:
            self.popup, self.state = popup, POPUP
            self._view_from_block_or_keep()
            self.rows = self._rebuild()
            return
        if not is_officer_list(self.fields):
            if waited < WAIT_BOUND:
                self.state = WAITING
                self.reason = ("The game reports the Leaders screen and "
                               "has not built its field list yet.")
                self._view_from_block_or_keep()
                self.rows = self._rebuild()
                return
            self.state = UNVALIDATED
            self.reason = (f"The game reports the Leaders screen and its "
                           f"field list is still not this screen's after "
                           f"{waited} snapshots.")
            return
        self.view = (geom.VIEW_SHIP
                     if _live(self.fields, "scroll_up") is not None
                     and _live(self.fields, "scroll_down") is not None
                     else geom.VIEW_COLONY)
        self.view_known = True
        self.hire_mode = _live(self.fields, "cancel") is not None
        self.buttons = {name: f for name in geom.BUTTONS
                        if (f := _live(self.fields, name)) is not None}
        self.rows = self._rebuild()
        listed = sum(_has(self.fields, geom.TYPE_HIDDEN, geom.text_field(i))
                     for i in range(geom.ROWS))
        if listed != len(self.rows):
            self.state = MISMATCH
            self.reason = (f"The game lists {listed} leader row(s) and the "
                           f"records give {len(self.rows)} for this view — "
                           f"the rebuild of Build_Captain_Id_List_ does "
                           f"not hold, so nothing is drawn from it.")
            return
        if self.block is not None:
            engine = [i for i in self.block.get("id_list", []) if i >= 0]
            if engine != self.rows:
                self.state = MISMATCH
                self.reason = (f"The engine lists leaders {engine}, the "
                               f"rebuild gives {self.rows}.")
                return
        self.state = READY

    def _view_from_block_or_keep(self):
        """A box or the popup REPLACES the list, so the view cannot be
        read off it; the block says it when it is there, and otherwise
        the caller keeps the view it last read (`screen.py`)."""
        if self.block is not None and self.block.get("view") in (
                geom.VIEW_SHIP, geom.VIEW_COLONY):
            self.view = int(self.block["view"])
            self.view_known = True
        else:
            self.view_known = False
            if self._last_view is not None:
                self.view = self._last_view

    def _rebuild(self):
        """The listed leaders — but only for a view that is KNOWN, read
        now or read before. On the first snapshot of an entry neither is
        true, and an empty list is drawn rather than the other view's
        leaders for a frame (the no-glimpse rule, work order 166 A)."""
        if not self.view_known and self._last_view is None:
            return []
        return ls.captain_id_list(self.leaders, self.player, self.view)

    # ── What the screen may do ─────────────────────────────

    @property
    def in_box(self):
        """`screens/fleets/fltbox` asks this — the native box's drawing
        and its buttons are reused as they are."""
        return self.state == IN_BOX

    @property
    def draws(self):
        """Whether HD keeps its own picture up."""
        return self.state in (READY, WAITING, IN_BOX, POPUP)

    @property
    def mode(self):
        """The button mode, where it can be known: from the block, or
        hire mode off the list; None otherwise (HD STATE)."""
        if self.block is not None:
            return int(self.block.get("mode", -1))
        if self.state == READY and self.hire_mode:
            return 0
        return None

    def sendable(self, action):
        """May HD send `action` now? Only where the effect is visible on
        the wire afterwards, unless the block says what the game is in.

        Without the block: the tabs (the list changes), HIRE and CANCEL
        (the list changes), RETURN (the screen changes) and a click on a
        leader who is for hire (a popup or a message follows, in every
        mode — officer.cpp:1409-1414, :1430-1437, :1800-1811).
        """
        if self.state != READY:
            return False
        if action in ("tab_colony", "tab_ship", "hire", "cancel", "return"):
            return action in self.buttons
        if action == "hire_leader":
            return True
        return self.block is not None

    def listed(self):
        """`[(slot, leader id, record)]` for the rows HD draws."""
        return [(slot, idx, self.leaders[idx])
                for slot, idx in enumerate(self.rows)]

    def for_hire_here(self):
        """HIRE's own condition (`Leaders_In_Hiring_Pool_`)."""
        return ls.leaders_for_hire(self.leaders, self.player, self.view)
