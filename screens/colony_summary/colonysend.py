"""The two clicks on the wire, one step at a time.

`colonypick` decides WHETHER a move is legal; this drives it. The
split is the one section 3 of the package is about: the HD selection
never reaches the game, and everything that does reach the game is
here, so "a preview must not inject" is a property of the import
graph rather than a promise in a comment.

**THE ORDER, AND WHY EACH STEP IS WHERE IT IS.**

  1. the sort key, which is not housekeeping and is not last. See
     below.
  2. `_first`, established one activation at a time and read back off
     the scroll thumb (`colonyfirst`). It is not on the wire, a human
     can move it (platform.cpp:1379), and `ext::g_pending_field` is a
     single slot so a batch would leave only the last (decision 46).
     It comes AFTER the sort because `Sort_Col_List_`'s handler sets
     `_first = 0` (colsum.cpp:832) — establishing first and sorting
     second would establish a window the sort then moves.
  3. click 1, the pick-up. Its effect is on the wire: `Get_Cluster_`
     clears bit 0x200 on exactly the pops it takes (colmove.cpp:70).
  4. click 2, the drop, ONLY once step 3's cluster is the predicted
     one. A mis-aimed pick-up takes a cluster nobody chose, and there
     is no cancel that stays on this screen — so the interlock is
     what makes step 3 safe to attempt at all.

**EVERY STEP WAITS FOR ITS EFFECT, AND THE FIRST SNAPSHOT AFTER A
SEND CANNOT CARRY IT.** `ext::Tick()` calls `ProcessInput()` before it
serializes anything (ext_api.cpp:341-386), so the tick that consumes
an injected command also ships the world from before the game acted
on it. Measured 5 September 2026: one increment of the game's list
window read `_first` unchanged on the first state/visual pair and
moved on the second, every time. Hence `_Wait`, which requires two
pairs AND the caller's own predicate. Counting sends would have
"confirmed" the step one tick early, which is the direction that
aims the next click at a window that has not moved yet.

**STEP 1 IS THE ONE THAT IS EASY TO LEAVE OUT, AND IT MOVED TO THE
FRONT ON 5 SEPTEMBER 2026.** `COLSUM::Sort_Col_List_` runs at exactly
two places in the whole engine: once when the screen is entered
(colsum.cpp:110) and once in the sort handler (colsum.cpp:830). It
never re-sorts on its own. HD, meanwhile, rebuilds and re-sorts its
rows from every snapshot. So the game's order is frozen for a whole
visit while HD's follows the data — and a row then maps to a game
slot holding a different colony, with every value on both screens
still correct. Same failure mode as decision 46's, one axis over:
that one is about WHERE the window starts, this one about what order
it is a window ONTO.

**It is sent ALWAYS, not only when the key is one this move could
change** — the choice, since both are buildable:

  the condition that matters is not "did my move change this key",
  it is "are both lists still in the same order", and nothing on the
  wire reports the game's order. Our own move is not the only thing
  that can drift it: the game's window is visible and clickable
  (platform.cpp:1379), so a human can press a sort header in it, and
  that changes the game's order with HD's key untouched. A rule
  keyed on our own effect would be exactly right about our effect
  and blind to that;

  the conditional version also needs a table of which sort keys a
  pop move changes — food, industry, research and BC today, name and
  population not. That table is a second copy of a fact about the
  engine, in the shape this project has been bitten by repeatedly:
  correct on the day it is written, and silently wrong the day a key
  is added;

  and it costs one keystroke, idempotently: `Switched_cmp_` has no
  direction toggle (colsum.cpp:378-401), so re-sorting by the key
  the game already holds re-sorts identically.

**Its confirmation is weak, and that is stated rather than dressed
up.** The effect waited on is `_first = 0`, which the sort handler
sets (colsum.cpp:832) — but if the window was already at 0, a sort
that never arrived looks exactly like one that did. The real guard
is the interlock at step 3: a wrong order puts the click on another
row, and the cluster that comes back is then not the predicted one.
The sort makes the failure rare; the interlock makes it visible.

`_first` is re-established from scratch for every move even though
the sort has just zeroed it. Shortening the plan because we know
what the sort did would be remembering a state instead of
establishing it, which is the thing decision 46 exists to refuse.

**A FAILURE STOPS, IT DOES NOT UNWIND.** If the pick-up lands
somewhere unexpected, the game holds a cluster; that state is on the
wire and is reported as itself. Nothing here clicks again with
geometry that has just been shown wrong, and nothing here leaves the
screen to clear the cluster: leaving is one of the two
`Clear_Cluster_` paths (colsum.cpp:804, :938) and is a decision for
the player, not for a chain that has just been surprised.
"""
import logging
import time

from core import wire_protocol
from core.structs import colony as colony_struct
from . import colonyfirst
from . import colonyicons
from .colonyselect import GameWindow

log = logging.getLogger("colonysend")

#: How long one step may take before it is reported as unconfirmed.
#: Generous on purpose: the server only talks inside an input loop
#: (`ext::Tick()` from `fields::Get_Input_()`), so a busy game is
#: silent rather than dead, and the cost of waiting is a message
#: arriving late while the cost of giving up early is a chain that
#: reports a step that worked as one that did not.
STEP_TIMEOUT_S = 4.0

#: The pre-effect floor. ONE HOME, in `core/wire_protocol`, because
#: it is a property of the API's tick ordering rather than of this
#: screen — and that is also where the argument lives for why a
#: COUNT is admissible at all under decision 21: it is not a settling
#: time, it is a bolt against a predicate that was already true
#: before the send. Read it there before changing it; the smoke test
#: pins both sides of the two.
EFFECT_PAIRS = wire_protocol.EFFECT_PAIRS

#: Geometry of the two window steppers, `_x_fields[1]` and
#: `_x_fields[2]` (colsum.cpp:263-264). Matched on the reported rect
#: rather than on a field index, because an index is a field dump's
#: word for it and those have been wrong before.
STEP_UP_XY = (619, 15)      # Decrement_First_ — towards row 0
STEP_DOWN_XY = (619, 316)   # Increment_First_

#: States, in the order they run: RESORT, ESTABLISH, PICK, DROP.
#: `HOLDING` is not a failure with a nicer name: it says the GAME has
#: a cluster in hand, which is a different thing for the player to be
#: told than "nothing happened".
IDLE, ESTABLISH, PICK, DROP, RESORT, DONE, FAILED, HOLDING = (
    "idle", "establish", "pick", "drop", "resort", "done", "failed",
    "holding")


def held_cluster(state):
    """(colony index, pops) the game currently has in hand, or None.

    `Get_Cluster_` clears POP_MASK_ASSIGNED on exactly the pops it
    takes, so a held cluster is visible on the wire — which is what
    makes the interlock a measurement instead of a hope.

    It scans EVERY colony, and the consequence is deliberate: an
    unassigned pop anywhere reads as a cluster in hand and stops the
    move. That is the fail-safe direction, because a cluster taken in
    a colony we did not aim at is precisely the mis-landing this
    interlock exists to catch (decision 46: an injected click names a
    position in the game's window, and the window is the thing that
    can be wrong). Narrowing the scan to the target colony would hide
    exactly that case. The reference save has no unassigned pop
    outside a move; a save that did would refuse to move pops and say
    so, which is a state a player can act on.
    """
    for i, raw in enumerate(getattr(state, "colonies_raw", None) or []):
        if len(raw) < colony_struct.SIZE:
            continue
        col = colony_struct.parse(raw)
        loose = tuple(p for p in range(col.n_pops)
                      if not colony_struct.pop_is_assigned(col.pop[p]))
        if loose:
            return (i, loose)
    return None


def field_at(state, x, y, tolerance=6):
    """The id of the field whose rect starts at (x, y), or None."""
    found = None
    for f in getattr(state, "fields", None) or []:
        fx, fy = getattr(f, "x", None), getattr(f, "y", None)
        if fx is None or fy is None:
            continue
        if abs(fx - x) <= tolerance and abs(fy - y) <= tolerance:
            found = f.index
    return found


class _Wait:
    """One send and the effect it must have, with a deadline.

    The counters are the client's own monotonic message counts.
    **The predicate is what ends the wait**; `EFFECT_PAIRS` is a bolt
    against the one message that cannot carry the effect, and its
    constant says at length why it is not a duration. The deadline is
    a give-up, never a trigger — nothing here advances because time
    passed (decision 21).
    """

    __slots__ = ("client", "ready", "state_at", "visual_at", "deadline",
                 "what")

    def __init__(self, client, ready, what, timeout=STEP_TIMEOUT_S):
        self.client = client
        self.ready = ready
        self.what = what
        self.state_at = client.stats.get("state", 0)
        self.visual_at = client.stats.get("visual", 0)
        self.deadline = time.monotonic() + timeout

    def settled(self, state):
        stats = self.client.stats
        if (stats.get("state", 0) < self.state_at + EFFECT_PAIRS
                or stats.get("visual", 0) < self.visual_at + EFFECT_PAIRS):
            return False
        return bool(self.ready(state))

    def expired(self):
        return time.monotonic() > self.deadline


class Send:
    """One pop move, driven from the screen's own update loop.

    Constructed with everything decided: which colony, which icon,
    which column, and the pop array the drop was predicted against.
    Nothing is re-planned here — a chain that re-decided mid-flight
    would be deciding against a snapshot the player never saw.
    """

    def __init__(self, client, *, n_colonies, position, colony,
                 source_job, slot, icon_count, target_job, cluster,
                 predicted, sort_hotkey=None):
        self.client = client
        self.colony = colony
        self.source_job = source_job
        self.slot = slot
        self.icon_count = icon_count
        self.target_job = target_job
        self.cluster = tuple(cluster.indices)
        self.predicted = tuple(predicted)
        self.n_colonies = int(n_colonies)
        self.sort_hotkey = sort_hotkey
        self.reason = None
        self._wait = None
        self._steps = []
        self._game_slot = None

        plan, game_slot = GameWindow.slot_for(n_colonies, position)
        if plan.refused:
            self.state = FAILED
            self.reason = plan.refused
            return
        self._game_slot = game_slot
        # Safe direction first and unconditionally (decision 46):
        # `Decrement_First_` clamps at 0, so `max_first` decrements
        # reach the top from wherever a human left the window.
        self._steps = ([STEP_UP_XY] * plan.down
                       + [STEP_DOWN_XY] * plan.up)
        self._target_first = plan.first
        self._resort_sent = False
        # The sort goes FIRST, because it sets `_first = 0`
        # (colsum.cpp:832) and would otherwise move a window this
        # chain had just established. Without a usable hotkey the
        # step is skipped rather than refused: the order may then be
        # stale, and the interlock at the pick-up is what catches it.
        self.state = RESORT if sort_hotkey is not None else ESTABLISH

    # ── What the screen asks ──────────────────────────────

    @property
    def finished(self):
        return self.state in (DONE, FAILED, HOLDING)

    @property
    def holding(self):
        """True when the GAME has a cluster in hand and we stopped."""
        return self.state == HOLDING

    def __repr__(self):
        return (f"Send({self.state}, colony={self.colony}, "
                f"slot={self.slot}->{self.target_job}, "
                f"reason={self.reason!r})")

    # ── The loop ──────────────────────────────────────────

    def update(self, state):
        """Advance by at most one step. Called once per frame.

        Returns the state name, so a caller can drive without knowing
        the constants.
        """
        if self.finished or state is None:
            return self.state
        if self._wait is not None:
            if self._wait.settled(state):
                self._wait = None
            elif self._wait.expired():
                return self._timeout(state)
            else:
                return self.state
        return self._advance(state)

    def _advance(self, state):
        if self.state == RESORT:
            return self._resort(state)
        if self.state == ESTABLISH:
            return self._establish(state)
        if self.state == PICK:
            return self._pick(state)
        if self.state == DROP:
            return self._drop(state)
        return self.state

    def _first_now(self, state):
        frame = getattr(state, "framebuffer", None)
        if not frame:
            return None
        return colonyfirst.read_first(colonyfirst.rows(frame),
                                      self.n_colonies)

    def _establish(self, state):
        """One window step per call, each confirmed on the thumb."""
        if not self._steps:
            if self.n_colonies < GameWindow.SLOTS:
                # NOTHING TO CONFIRM, and that is a state rather than
                # a shortcut: under ten colonies neither stepper runs
                # at all (colsum.cpp:210 and :226), `Update_First_`
                # forces `_first = 0` every draw (colsum.cpp:194-197)
                # and the indicator is not drawn (colsum.cpp:751), so
                # the channel that would confirm it does not exist.
                # Demanding a reading here would fail on a game that
                # is behaving perfectly.
                return self._begin_pick()
            reading = self._first_now(state)
            if reading != self._target_first:
                return self._fail(
                    "window_lost",
                    "the window reads %r, wanted %s", reading,
                    self._target_first)
            return self._begin_pick()
        xy = self._steps[0]
        field = field_at(state, *xy)
        if field is None:
            return self._fail("window_lost",
                              "no stepper field at native %s", xy)
        # Only reachable at ten colonies or more: `GameWindow.plan`
        # returns no steps below that, so the thumb is drawn whenever
        # this line runs and a reading that is not an integer is a
        # real failure rather than an absent channel.
        before = self._first_now(state)
        if not isinstance(before, int):
            return self._fail("window_lost", "the thumb reads %r", before)
        want = (max(0, before - 1) if xy == STEP_UP_XY else before + 1)
        self._steps.pop(0)
        self.client.activate_field(field)
        self._wait = _Wait(self.client,
                           lambda st: self._first_now(st) == want,
                           f"window -> {want}")
        return self.state

    def _begin_pick(self):
        """Click 1. The x is the icon's own right edge."""
        x = colonyicons.slot_click_x(self.source_job, self.slot,
                                     self.icon_count)
        y = colonyicons.row_click_y(self._game_slot)
        self.state = PICK
        log.info("pop move: click 1 (pick up) at native (%d, %d)", x, y)
        self.client.inject_click(x, y)
        # ANY cluster, not the predicted one. The two failures are
        # different — nothing was picked up, and the wrong thing was —
        # and only the second one leaves the game holding something.
        self._wait = _Wait(self.client,
                           lambda st: held_cluster(st) is not None,
                           "a cluster in hand")
        return self.state

    def _pick(self, state):
        """The interlock: is the cluster in hand the predicted one?"""
        held = held_cluster(state)
        want = (self.colony, self.cluster)
        if held != want:
            log.warning("pop move: held %r, predicted %r", held, want)
            self.state = HOLDING
            self.reason = "wrong_pickup"
            return self.state
        x = self._drop_x()
        y = colonyicons.row_click_y(self._game_slot)
        self.state = DROP
        log.info("pop move: click 2 (drop on column %d) at native (%d, %d)",
                 self.target_job, x, y)
        self.client.inject_click(x, y)
        self._wait = _Wait(self.client, self._landed, "the predicted pops")
        return self.state

    def _drop_x(self):
        """Where to click for the target column.

        The middle of the column, not an icon: the drop is
        `Send_Cluster_(colony, job)` (colsum.cpp:869) and reads no
        icon at all — the pointer walk only runs on the pick-up. An
        empty column therefore accepts a drop, which is the whole
        point of being able to move pops into a job nobody holds.
        """
        left_x, right_x = colonyicons.COLUMNS[self.target_job]
        return (left_x + right_x) // 2

    def _landed(self, state):
        raws = getattr(state, "colonies_raw", None) or []
        if not 0 <= self.colony < len(raws):
            return False
        col = colony_struct.parse(raws[self.colony])
        return all(col.pop[i] == self.predicted[i]
                   for i in range(min(col.n_pops, len(self.predicted))))

    def _drop(self, _state):
        """The drop confirmed. Nothing follows it.

        The sort that keeps the two lists in one order is step 1 of
        the NEXT move, not a tail on this one — see the module
        docstring. A trailing sort would also have been the weaker
        placement: it can only repair drift this move caused, and the
        drift a move has to survive is whatever happened before it.
        """
        self.state = DONE
        return self.state

    def _resort(self, _state):
        """Step 1: put the game's list back into HD's order.

        Sent once; the second visit here is the settled wait, which
        hands over to the window steps. The effect waited on is
        `_first = 0` — weak by itself, because a window already at 0
        cannot show it, which is why the module docstring says the
        interlock is the real guard.
        """
        if not self._resort_sent:
            self._resort_sent = True
            log.info("pop move: re-sorting the game's list first")
            self.client.inject_key(self.sort_hotkey)
            self._wait = _Wait(
                self.client,
                lambda st: (self.n_colonies < GameWindow.SLOTS
                            or self._first_now(st) == 0),
                "the list re-sorted")
            return self.state
        self.state = ESTABLISH
        return self._establish(state=_state)

    def _timeout(self, state):
        """A step that did not confirm. Report what IS on the wire.

        `step` is read BEFORE anything is assigned to `self.state` —
        the failing step is what decides both the reason and whether
        the game is left holding, and testing it after the assignment
        would answer about the state this method just wrote.
        """
        what = self._wait.what if self._wait else "?"
        step = self.state
        self._wait = None
        held = held_cluster(state)
        if step == PICK and held is None:
            # The click reached no icon. `Get_Selected_Pop_` resolves
            # one from the scroll field's value, which
            # `Find_Bar_Position_` writes from the POINTER
            # (fields.cpp:1702-1743) — so this is the shape open fix 3
            # describes, and it is a state to report, not to retry.
            return self._fail("no_pickup", "no cluster after click 1")
        if held is not None:
            log.warning("pop move: timed out waiting for %s; the game "
                        "holds %r", what, held)
            self.state = HOLDING
            self.reason = ("drop_unconfirmed" if step == DROP
                           else "wrong_pickup")
            return self.state
        return self._fail("drop_unconfirmed" if step == DROP
                          else "window_lost",
                          "timed out waiting for %s", what)

    def _fail(self, reason, msg, *args):
        log.warning("pop move failed (%s): " + msg, reason, *args)
        self.state = FAILED
        self.reason = reason
        return self.state
