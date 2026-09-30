"""A left click on a row's NAME opens that colony's screen — work order 196
C1 (Data's item 7). TRANSCRIBED: the original does exactly this.

`COLSUM::Evaluate_Col_List_Input_` (colsum.cpp:904-921): a click on
`_list_fields[i]` — the hidden field over the name, `Add_Hidden_Field_(12,
y1, 101, y_row_end)` at colsum.cpp:283-291, y1 = 35 + 31 i — with no
cluster held hands the colony's star and orbit to `SCREEN_COLONY` and
leaves. The HD colony screen claims that id (work order 180, open fixes
35-40), so the click can now go where the original's goes; until this
order it was swallowed on purpose, because there was no HD screen to
arrive at (the comment it replaces is in `screen.handle_click`'s history).

**THE FIELD NAMES A SLOT, NOT A COLONY** (decision 46): which colony slot i
reaches is `_first`'s answer. So the jump is three steps, each sent ONE AT
A TIME and CONFIRMED by its effect, never by time (decision 21):

  READ     `_first` off the scroll thumb the game draws
           (`colonyfirst.read_first`); under ten colonies the window
           cannot move and `_first` is 0 (colsum.cpp:194-197)
  STEP     one arrow per step toward the target window
           (`GameWindow.slot_for`: the row as early in the window as it
           goes), each confirmed by the thumb reading the step's value
  OPEN     `_list_fields[slot]`, found in the live list by its source
           rectangle, activated; done when the game leaves screen 20

**REFUSED, BEFORE ANYTHING IS SENT** (decision 33): a row order that does
not bind (`colonypick.sort_binds` — the sort key HD cannot honour), a
thumb that cannot be read, a slot field the live list does not carry. A
refusal sends nothing and says why in the log; a failure mid-way stops
and never retries.
"""
import logging

from . import colonyfirst, colonypick
from .colonyscroll import ARROW_DOWN_XY, ARROW_UP_XY
from .colonyselect import GameWindow
from .colonysend import _Wait, field_at

log = logging.getLogger("colony_summary")

READING, STEPPING, OPENING, DONE, FAILED = (
    "reading", "stepping", "opening", "done", "failed")

#: The Colonies screen's id and the colony screen's (orion2_consts.h).
SCREEN_COLONY_SUMMARY, SCREEN_COLONY = 20, 1


def list_field_rect(slot):
    """`_list_fields[slot]`'s rectangle, colsum.cpp:283-291."""
    y1 = 35 + 31 * int(slot)
    return (12, y1, 101, y1 + 30)


def live_list_field(state, slot):
    """The live field whose rectangle starts at `list_field_rect(slot)`'s
    corner, or None. By the corner, exactly: the name field is the only
    one starting at x 12 on its row (the producing field starts at 512,
    the job fields at 101 and after)."""
    x, y = list_field_rect(slot)[:2]
    return next((f for f in (getattr(state, "fields", None) or [])
                 if getattr(f, "index", 0) > 0 and (f.x, f.y) == (x, y)),
                None)


def game_first(state, n_colonies):
    """`_first` as the game draws it: an int, or None when unreadable."""
    if not GameWindow.scrolls(n_colonies):
        return 0
    fb = getattr(state, "framebuffer", None)
    if not fb:
        return None
    got = colonyfirst.read_first(colonyfirst.rows(fb), n_colonies)
    return got if isinstance(got, int) else None


class Jump:
    """One jump from row `position` of the HD list (the game's order)."""

    def __init__(self, client, state, *, colony, position, n_colonies,
                 sort_key):
        self.client = client
        self.colony = colony
        self.n = int(n_colonies)
        self.state = FAILED
        self.reason = ""
        self._wait = None
        self._expect = None
        if not colonypick.sort_binds(sort_key):
            self._fail("the game's list is sorted by a key HD cannot "
                       "honour; a slot would name another colony")
            return
        plan, slot = GameWindow.slot_for(self.n, position)
        if plan.refused or slot is None:
            self._fail(f"row {position} of {self.n} has no slot "
                       f"({plan.refused})")
            return
        self.target, self.slot = plan.first, slot
        first = game_first(state, self.n)
        if first is None:
            self._fail("the game's list window cannot be read off its "
                       "scroll thumb")
            return
        self.first = first
        self.state = STEPPING
        log.info("jump: colony %d, row %d -> window %d slot %d (game at %d)",
                 colony, position, self.target, slot, first)
        self._next(state)

    @property
    def finished(self):
        return self.state in (DONE, FAILED)

    def _fail(self, why):
        self.state, self.reason = FAILED, why
        log.warning("jump: refused — %s", why)

    def _next(self, state):
        """Send the next step, or open the colony."""
        if self.first != self.target:
            up = self.first > self.target
            field = field_at(state, *(ARROW_UP_XY if up else ARROW_DOWN_XY))
            if field is None:
                self._fail("the list arrow is not in the live list")
                return
            self._expect = self.first - 1 if up else self.first + 1
            self.client.activate_field(field)
            self._wait = _Wait(self.client, lambda st: game_first(
                st, self.n) == self._expect, "the window step")
            return
        field = live_list_field(state, self.slot)
        if field is None:
            self._fail(f"slot {self.slot}'s name field is not in the live "
                       "list")
            return
        self.state = OPENING
        self.client.activate_field(field.index)
        self._wait = _Wait(self.client, lambda st: getattr(
            st, "current_screen", SCREEN_COLONY_SUMMARY)
            != SCREEN_COLONY_SUMMARY, "the colony screen")

    def update(self, state):
        if self.finished or self._wait is None:
            return
        if self._wait.settled(state):
            self._wait = None
            if self.state == OPENING:
                self.state = DONE
                return
            self.first = self._expect
            self._next(state)
        elif self._wait.expired():
            self._fail(f"{self._wait.what} did not come")
