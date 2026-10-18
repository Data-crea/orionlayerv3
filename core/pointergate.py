"""The pointer's motion, the wheel and the left release ask the same
question as a click and a key — work order 226 A (D13 of the GUI audit,
Data's decision 1 of 9 October 2026, as proposed in
`dev:doc/briefs/224-parked-for-data.md`).

Decision 74: a held frame takes no input — it no longer shows the game's
state. Decision 76: under F12 the input is the game's. `main.App` asked
both before a click or a key reached the HD screen, and routed motion,
the wheel and the left button's release to the screen on top without
asking. A drag that crossed a hold could then end in a click: the GAME
menu's volume bars (`gmsliders.release`) and combat's board slider
(`cbpopups.release`) inject a click on release.

So: motion and wheel reach the screen only while it is the game's
picture; a release reaches it only when its press did AND it is still
the game's picture. A release whose press did reach the screen but which
arrives while the frame is held or the game's picture is up ends the
gesture WITHOUT its effect (`handle_left_cancel`): a drag left armed
would send its click on the next release, after the hold.

The right button has its own gate since work order 299 (Data's P2 of
298): a right press the screen got whose release an overlay takes ends
with `handle_right_cancel`, so the battle's camera never pans with no
button held.
"""

DELIVER, CANCEL, DROP = "deliver", "cancel", "drop"


class PointerGate:
    """Remembers whether the last left press reached the HD screen."""

    def __init__(self):
        self.armed = False
        self.spoilt = False

    def press(self, delivered):
        self.armed, self.spoilt = bool(delivered), False

    def watch(self, open_):
        """Every frame: a hold or F12 that comes while a press is armed
        spoils it, even when it is gone again by the release (a box answered
        with the other hand under a held button, work order 299's review)."""
        if self.armed and not open_:
            self.spoilt = True

    def release(self, open_):
        """What a release does: DELIVER to the screen, CANCEL the gesture
        its press began, or DROP it (its press never arrived)."""
        armed, spoilt = self.armed, self.spoilt
        self.armed = self.spoilt = False
        if not armed:
            return DROP
        return DELIVER if open_ and not spoilt else CANCEL

    @staticmethod
    def passes(open_):
        """Motion and wheel: only while the screen is the game's picture."""
        return bool(open_)
