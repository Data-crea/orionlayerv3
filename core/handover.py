"""A screen HD draws never presents a native frame — work order 180, part A2.

**THE RULE (proposed as a decision in `doc/briefs/180-parked-for-data.md`).**
While a transition waits for the data an HD screen needs, the window keeps
showing the last HD frame, or the universal background. The game's own
picture is shown only for a screen or a modal HD has no view for at all.
If a known screen's data does not arrive within `HOLD` snapshots, the
picture is shown ONCE — logged, and counted as a failure, not as normal.

**WHY IT IS HERE AND NOT IN THE SCREENS.** Work order 180 A1 measured three
transitions that presented the game's picture (`180-flash-findings.md`):
Fleets judged its first snapshot a refusal, the main menu's modal net took
the engine's opening animation for a modal, and the load passed through an
id with no HD screen and an empty list. 142 A (Fleets) and 166 A (the
research panel) had each fixed one such moment inside one screen, and the
third instance was waiting behind the second. Every hand-over passes
through `main.App._showing_original` (139 A made it the one place), so the
gate sits there and every screen — including the next one — is under it.

**THE FOUR WAYS IN**, as `core.frametrace` names them, and what each gets:

    f12        the player's own mode — never held
    no_screen  an id no HD screen claims (decision 22): shown at once when
               its list holds a field to answer; HELD while the list is
               empty, because a picture with nothing on it to answer is a
               transition, not a screen (the load's screen 39)
    modal      a screen's modal net says "a modal HD has no view for"
               (`ScreenBase.handover_is_modal`): held, then shown — the
               net is allowed for exactly that, so it is not a failure.
               A modal BOX — a list that replaced the screen's own page,
               its data already there (`ScreenBase.modal_is_box`) — is
               shown once its live list has stood unchanged for
               `MODAL_SETTLE` snapshots (work order 187, option C of
               `doc/briefs/186-modal-hold.md`): no late data can end its
               hold, which is why the full hold made every box ~4 s
    hand_over  a known screen cannot vouch for its data: held, then shown
               ONCE and counted in `failures`

**COUNTED IN SNAPSHOTS, NOT SECONDS** (decision 21): the engine is silent
while it loads, generates or ends a turn, and a clock would run out in a
silence that is not a failure. `client.stats["state"]` is the count.

**DEVIATION `hold_last_frame`.** The original draws each screen the moment
it draws it and has no second picture to wait with. HD, while a
transition waits for its data, keeps its last frame (or the universal
background) and takes no input — for at most `HOLD` snapshots. Measured
live in work order 180 A2: 1 snapshot entering Fleets, 2 through a load,
24 through the main menu's opening animation; 202 transitions, no native
frame and no fallback.

**WHAT HOLDING MEANS FOR INPUT.** Nothing reaches the game or the screen
while a hold stands (`main.App`): a click on a frame that no longer shows
the game's state is not a choice (decision 65's reasoning), and the
screen underneath may be measuring a list that is the previous screen's.
"""
import logging

log = logging.getLogger("handover")

#: Snapshots a known screen's hand-over is held before the picture is
#: shown. At the ~18 snapshots a second measured in work order 177, two
#: seconds; the longest transition A1 measured is the main menu's opening
#: animation, 1.29 s. Longer than any transition seen, short enough that a
#: screen whose data never comes still reaches the picture.
HOLD = 36
#: Snapshots an id with no HD screen may stand with an EMPTY list before
#: its picture is shown anyway — the same bound, for the same reason.
EMPTY_HOLD = 36
#: Snapshots a modal BOX's live list must stand unchanged before it is
#: shown (work order 187, Data's approval of option C): the modal net's
#: SETTLE, counted in snapshots as its own docstring says — at a box's own
#: pace (~106-113 ms, `186-modal-hold.md`) about half a second.
from core.modalnet import SETTLE as MODAL_SETTLE  # noqa: E402

F12, NO_SCREEN, MODAL, HAND_OVER = "f12", "no_screen", "modal", "hand_over"


class Gate:
    def __init__(self, hold=HOLD, empty_hold=EMPTY_HOLD,
                 modal_settle=MODAL_SETTLE):
        self.hold, self.empty_hold = hold, empty_hold
        self.modal_settle = modal_settle
        #: Modal boxes shown early (option C), for the report.
        self.early = 0
        self._sig = None
        self._sig_since = 0
        #: Known screens whose data did not arrive within the hold.
        self.failures = 0
        #: Holds that ended with the screen's own picture — no native frame.
        self.resolved = 0
        self.holding = False
        self._episode = None
        self._start = 0
        self._released = False

    def decide(self, want, kind, name, screen, live_fields, snapshots,
               box=False, sig=None):
        """True to present the game's picture, False to draw HD — and
        `holding` says whether "False" means "keep the last HD frame".

        `box`: the modal is a box over the screen's own page
        (`ScreenBase.modal_is_box`); `sig`: its live list's shape — the
        early release counts snapshots since `sig` last changed."""
        if not want or kind == F12 or (kind == NO_SCREEN and live_fields):
            self._close(snapshots)
            self.holding = False
            return bool(want)
        key = (kind, name, screen)
        if key != self._episode:
            self._close(snapshots)
            self._episode, self._start, self._released = key, snapshots, False
            self._sig, self._sig_since = sig, snapshots
            log.info("hold: %s, game screen %s (%s) — HD keeps its last "
                     "frame until the data arrives", name or "-", screen,
                     kind)
        if self._released:
            self.holding = False
            return True
        if sig != self._sig:
            self._sig, self._sig_since = sig, snapshots
        waited = snapshots - self._start
        if kind == MODAL and box and live_fields and \
                snapshots - self._sig_since >= self.modal_settle:
            self._released, self.holding = True, False
            self.early += 1
            log.info("released: %s, game screen %s (modal box) — its list "
                     "stood still for %d snapshots (option C, work order "
                     "187)", name or "-", screen, snapshots - self._sig_since)
            return True
        limit = self.empty_hold if kind == NO_SCREEN else self.hold
        if waited < limit:
            self.holding = True
            return False
        self._released = True
        self.holding = False
        if kind == HAND_OVER:
            self.failures += 1
            log.warning("FALLBACK: %s, game screen %s — its data did not "
                        "arrive within %d snapshots; the game's picture is "
                        "shown (a failure, work order 180 A2)",
                        name or "-", screen, limit)
        else:
            log.info("released: %s, game screen %s (%s) after %d snapshots "
                     "— the game's picture is shown", name or "-", screen,
                     kind, waited)
        return True

    def _close(self, snapshots):
        if self._episode is not None and not self._released:
            self.resolved += 1
            log.info("hold ended: %s, game screen %s after %d snapshots — "
                     "no native frame", self._episode[1] or "-",
                     self._episode[2], snapshots - self._start)
        self._episode = None
        self._released = False


def live_fields(state):
    """Fields a player could answer: every one but the dummy, index 0."""
    return sum(1 for f in (getattr(state, "fields", None) or [])
               if getattr(f, "index", 0) != 0)


def decide_for(app, want, kind, top):
    """`App._showing_original`'s answer, through the gate.

    `want` and `kind` are the app's own reading (the three ways in);
    a hand-over from a modal net is re-named `modal` here, by the screen's
    own `handover_is_modal()`, so a net doing what it is for is never
    counted as a failure.
    """
    if kind == HAND_OVER and top is not None and top.handover_is_modal():
        kind = MODAL
    state = app.client.state
    d = app.dispatcher
    name = ((d.overlay_name or d.active_name) if top is not None
            else "") or ""
    box = bool(kind == MODAL and top is not None and
               getattr(top, "modal_is_box", lambda: False)())
    return app._handover.decide(
        want, kind, name, getattr(state, "current_screen", -1),
        live_fields(state), app.client.stats.get("state", 0),
        box=box, sig=list_sig(state))


def list_sig(state):
    """A live list's shape: each answerable field's type and rectangle."""
    return tuple((getattr(f, "field_type", None), getattr(f, "x", None),
                  getattr(f, "y", None), getattr(f, "x_end", None),
                  getattr(f, "y_end", None))
                 for f in (getattr(state, "fields", None) or [])
                 if getattr(f, "index", 0) != 0)


def render_hold(app):
    """What a held frame shows: the surface as the last HD frame left it,
    or — when the surface holds anything else (the game's picture, or a
    new surface after a resize) — the universal background.

    `app._surface_hd` is True while the surface shows only HD or the
    background; `App._render` clears it whenever it draws the game's
    picture or the window is resized.
    """
    if not app._surface_hd:
        from core import backgrounds
        backgrounds.draw(app.surface, "universal")
        app._surface_hd = True
