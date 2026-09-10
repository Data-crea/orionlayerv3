"""One command on the wire, and the wait that confirms it.

`colonypick` decides WHETHER a move is legal; this sends it. The
split is the one section 3 of the package is about: the HD selection
never reaches the game, and everything that does reach the game is
here, so "a preview must not inject" is a property of the import
graph rather than a promise in a comment.

**A MOVE IS ONE MESSAGE — fundament 52.** `MSG_SET_JOBS` names a
colony and a list of (pop_index, job), and the engine applies the
whole list or none of it. `doc/ext_move_pop.patch` is the engine
side; `tools/version_check.py` fails on a tree without it, because
an unpatched engine drops the message and moves nothing, silently.

**WHAT THIS FILE USED TO BE, and why the four states are gone.**
Until 10 September 2026 a move was a click choreography — RESORT,
ESTABLISH, PICK, DROP — because a click names a SLOT in the game's
own ten-row window and the window had to be steered under the target
row first. Run A measured what that cost: 597 ms of a 725 ms drop,
four snapshot round trips, and every one of them existed only to
turn "this colony" into "that slot". Addressing the colony by index
deletes the whole apparatus. Measured after: **55 ms, one snapshot
round, and the same 55 ms whether the row is the first or the last**
— the window-stepping had been the entire difference between them.

Two paths that move pops would be the duplicate this project keeps
paying for, so the chain is deleted rather than kept as a fallback.
What it taught is not: see decision 46, which is why `_first` is
still established rather than remembered wherever the list window
still matters, and `colonyscroll`, which still drives the game's own
arrows as a courtesy and now owns their coordinates.

**THE WAIT IS STILL AN EFFECT, NEVER A MESSAGE.** `ext::Tick()`
calls `ProcessInput()` before it serializes anything
(ext_api.cpp:341-386), so the tick that consumes a command also
ships the world from before the game acted on it. A wait that
accepted the first snapshot would report every move as landed the
instant it was sent. Hence `_Wait`, which requires `EFFECT_PAIRS`
state/visual pairs AND the caller's own predicate — and the
predicate here is the strongest one available: the colony's pop
words equal what `colonymove.predict_pops` said they would be,
word for word.

**A REFUSAL IS NOT EXPECTED AND IS STILL HANDLED.** HD checks the
same four conditions before sending (decision 33), so the engine
refusing is a disagreement between the two, not a normal outcome.
When it happens the engine rolls the colony back and nothing
changes, so the predicate never comes true and the wait times out
saying so. That is the honest report: "the game did not do what we
predicted" is exactly what happened, and it is a state a player can
act on rather than a silent no-op.

**A FAILURE STOPS, IT DOES NOT RETRY.** Nothing here sends twice
with a prediction that has just been shown wrong.
"""
import logging
import time

from core import wire_protocol
from core.structs import colony as colony_struct

log = logging.getLogger("colonysend")

#: How long the send may take before it is reported as unconfirmed.
#: Generous on purpose: the server only talks inside an input loop
#: (`ext::Tick()` from `fields::Get_Input_()`), so a busy game is
#: silent rather than dead, and the cost of waiting is a message
#: arriving late while the cost of giving up early is reporting a
#: move that worked as one that did not.
STEP_TIMEOUT_S = 4.0

#: The pre-effect floor. ONE HOME, in `core/wire_protocol`, because
#: it is a property of the API's tick ordering rather than of this
#: screen — and that is also where the argument lives for why a
#: COUNT is admissible at all under decision 21: it is not a settling
#: time, it is a bolt against a predicate that was already true
#: before the send. Read it there before changing it; the smoke test
#: pins both sides of the two.
EFFECT_PAIRS = wire_protocol.EFFECT_PAIRS

#: The states. One send, so there is one in-flight state.
#: `HOLDING` is not a failure with a nicer name: it says the GAME has
#: a cluster in hand, which is a different thing for the player to be
#: told than "nothing happened".
IDLE, SENT, DONE, FAILED, HOLDING = (
    "idle", "sent", "done", "failed", "holding")


def held_cluster(state):
    """(colony index, pops) the game currently has in hand, or None.

    `Get_Cluster_` clears POP_MASK_ASSIGNED on exactly the pops it
    takes, so a held cluster is visible on the wire.

    **STILL CHECKED, THOUGH NOTHING HD DOES CAN CAUSE ONE NOW.** The
    command never picks a cluster up, so a held one can only come
    from the game's own window — and the engine's handler refuses
    `MSG_SET_JOBS` outright while `_cluster_colony_n != -1`, because
    writing `pop[]` underneath a gesture in progress would strand
    it. This function is what lets HD say WHICH state that is
    instead of reporting a move that quietly did nothing.

    It scans EVERY colony, and the consequence is deliberate: an
    unassigned pop anywhere reads as a cluster in hand. That is the
    fail-safe direction and it costs nothing now that no HD gesture
    creates one.
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
    """The id of the field whose rect starts at (x, y), or None.

    Kept here because it is about the FIELD LIST and not about any
    one screen; `colonyscroll` is the caller that remains.
    """
    found = None
    for f in getattr(state, "fields", None) or []:
        fx, fy = getattr(f, "x", None), getattr(f, "y", None)
        if fx is None or fy is None:
            continue
        if abs(fx - x) <= tolerance and abs(fy - y) <= tolerance:
            found = f.index
    return found


class _Wait:
    """The send and the effect it must have, with a deadline.

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
    """One pop move: one message, one wait on the predicted pops.

    Constructed with everything decided: which colony, which pops,
    which column, and the pop array the move was predicted against.
    Nothing is re-planned here — a send that re-decided mid-flight
    would be deciding against a snapshot the player never saw.
    """

    def __init__(self, client, *, colony, target_job, cluster, predicted):
        self.client = client
        self.colony = int(colony)
        self.target_job = int(target_job)
        # ASCENDING, and it is not cosmetic. The engine applies the
        # list in the order it is given, and `predict_pops` walks the
        # pop array from index 0 (colmove.cpp:160-176). Sorting here
        # is what makes the prediction and the command the same walk.
        self.cluster = tuple(sorted(cluster.indices))
        self.predicted = tuple(predicted)
        self.reason = None
        self._wait = None

        if not self.cluster:
            self.state = FAILED
            self.reason = "empty_cluster"
            return

        self.state = SENT
        client.set_jobs(self.colony,
                        [(i, self.target_job) for i in self.cluster])
        log.info("pop move: colony %d, pops %r -> job %d, one command",
                 self.colony, self.cluster, self.target_job)
        self._wait = _Wait(client, self._landed, "the move")

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
                f"pops={self.cluster}->{self.target_job}, "
                f"reason={self.reason!r})")

    # ── The loop ──────────────────────────────────────────

    def update(self, state):
        """Advance by at most one step. Called once per frame.

        Returns the state name, so a caller can drive without knowing
        the constants.
        """
        if self.finished or state is None:
            return self.state
        if self._wait is None:
            return self.state
        if self._wait.settled(state):
            self._wait = None
            self.state = DONE
            return self.state
        if self._wait.expired():
            return self._timeout(state)
        return self.state

    def _landed(self, state):
        """The colony's pop words ARE the predicted ones.

        Word for word, not a summary: a move that landed on the wrong
        pop leaves every count correct and only the identity wrong,
        which is the failure shape decision 46 exists for.
        """
        raws = getattr(state, "colonies_raw", None) or []
        if not 0 <= self.colony < len(raws):
            return False
        raw = raws[self.colony]
        if len(raw) < colony_struct.SIZE:
            return False
        col = colony_struct.parse(raw)
        return tuple(col.pop[:len(self.predicted)]) == self.predicted

    def _timeout(self, state):
        """The move did not confirm. Report what IS on the wire."""
        what = self._wait.what if self._wait else "?"
        self._wait = None
        held = held_cluster(state)
        if held is not None:
            # Only the game's own window can produce this, and the
            # engine refuses the command while it lasts.
            log.warning("pop move: timed out waiting for %s; the game "
                        "holds %r", what, held)
            self.state = HOLDING
            self.reason = "game_holds_cluster"
            return self.state
        # Nothing held and the pops are not what was predicted: the
        # engine refused the list and rolled it back, or the tree is
        # unpatched and dropped the message. Both are "the game did
        # not do what we predicted", and `version_check` is what
        # tells the two apart.
        return self._fail("move_unconfirmed",
                          "timed out waiting for %s", what)

    def _fail(self, reason, msg, *args):
        log.warning("pop move failed (%s): " + msg, reason, *args)
        self.state = FAILED
        self.reason = reason
        return self.state
