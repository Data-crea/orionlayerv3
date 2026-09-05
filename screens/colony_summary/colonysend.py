"""The two clicks on the wire, one step at a time.

`colonypick` decides WHETHER a move is legal; this drives it. The
split is the one section 3 of the package is about: the HD selection
never reaches the game, and everything that does reach the game is
here, so "a preview must not inject" is a property of the import
graph rather than a promise in a comment.

**THE ORDER, AND WHY EACH STEP IS WHERE IT IS.**

  1. `_first`, established one activation at a time and read back off
     the scroll thumb (`colonyfirst`). It is not on the wire, a human
     can move it (platform.cpp:1379), and `ext::g_pending_field` is a
     single slot so a batch would leave only the last (decision 46).
  2. click 1, the pick-up. Its effect is on the wire: `Get_Cluster_`
     clears bit 0x200 on exactly the pops it takes (colmove.cpp:70).
  3. click 2, the drop, ONLY once step 2's cluster is the predicted
     one. A mis-aimed pick-up takes a cluster nobody chose, and there
     is no cancel that stays on this screen — so the interlock is
     what makes step 2 safe to attempt at all.
  4. the sort key again, which is not housekeeping. See below.

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

**STEP 4 IS THE ONE THAT IS EASY TO LEAVE OUT.** A pop move changes
food, industry and research, and HD re-sorts its rows from every
snapshot while the GAME re-sorts only when a sort field is activated
(`Sort_Col_List_`, colsum.cpp:829-838). So the moment a move lands
under a production sort key, HD's order and the game's order stop
being the same list — and the next move would map an HD row to a game
slot that holds a different colony, with every value on both screens
still correct. Re-pushing the key re-sorts the game with the new
values and sets `_first = 0` in the same handler (colsum.cpp:832),
which is also a confirmable effect. It is idempotent by the
original's own design: `Switched_cmp_` has no direction toggle
(colsum.cpp:378-401).

The trap the package named — the row moving after the move because
the list is sorted by an affected key — is the same fault seen from
HD's side, and this is where it is answered. `_first` itself is
re-established from scratch for every move and never carried.

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

#: The pre-effect floor, in state/visual pairs. Not a duration — the
#: tick ordering above.
EFFECT_PAIRS = 2

#: Geometry of the two window steppers, `_x_fields[1]` and
#: `_x_fields[2]` (colsum.cpp:263-264). Matched on the reported rect
#: rather than on a field index, because an index is a field dump's
#: word for it and those have been wrong before.
STEP_UP_XY = (619, 15)      # Decrement_First_ — towards row 0
STEP_DOWN_XY = (619, 316)   # Increment_First_

#: States. `HOLDING` is not a failure with a nicer name: it says the
#: GAME has a cluster in hand, which is a different thing for the
#: player to be told than "nothing happened".
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

    The counters are the client's own monotonic message counts. Two
    pairs is the floor described in the module docstring; the
    predicate is what actually ends the wait.
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
        self.state = ESTABLISH

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
        if self.state == ESTABLISH:
            return self._establish(state)
        if self.state == PICK:
            return self._pick(state)
        if self.state == DROP:
            return self._drop(state)
        if self.state == RESORT:
            return self._resort(state)
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

    def _drop(self, state):
        """The drop confirmed. Re-sort, so the two lists still bind."""
        if self.sort_hotkey is None:
            self.state = DONE
            return self.state
        self.state = RESORT
        self.client.inject_key(self.sort_hotkey)
        want_first = 0
        self._wait = _Wait(
            self.client,
            lambda st: (self._first_now(st) == want_first
                        or self.n_colonies < GameWindow.SLOTS),
            "the list re-sorted")
        return self.state

    def _resort(self, _state):
        self.state = DONE
        return self.state

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
