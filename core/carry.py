"""Pick up, carry on the pointer, set down — the one gesture a screen with
movable things shares (work order 233; first built for the Races screen's
spies by work orders 197, 226 E and 228 C, then for the colony screen's
colonists).

THE ORIGINAL holds the thing in its own arrays from the first click: the
Races screen's `Move_Spy_Group_From_Mouse_` (racescrn.cpp:390-408), the
colony screen's `COLMOVE::Get_Cluster_` (colmove.cpp:60-100, through
`Pickup_Colonists_`, colony.cpp:1621-1626). What is in hand has left its
group, rides on the pointer as its mouse picture (`Redraw_Spy_Mouse_`,
racescrn.cpp:608-622; `COLMOVE::Draw_Cluster_`, colmove.cpp:24-55, drawn
last at the pointer, colony_main.cpp:178-182), and a click on a target sets
it down.

HD (decision 47): what is in hand is HD's own — `hand`, the screen's object
(a `racesspies.Hand`, a `colonypick.Pick`) — and nothing is sent until the
target is known; then ONE command goes out (decision 52), and the screen
draws what that command EXPECTS from the click on (`sent`, `shown`) until
the wire shows it — SET DOWN IS SET DOWN (work order 228 C, Data: "when it
is set down it appears for a moment at its starting place and then at the
target"). The wire shows a command only from the engine's first snapshot
after it (`ext::Tick` serializes after `ProcessInput`, ext_api.cpp:341-386),
so a screen that drew the wire at once drew the thing back at its start for
those frames. If no NEW snapshot shows it within `REFUSED_AFTER`, the engine
refused, and the wire is drawn again — the thing goes back once.

What each screen keeps for itself: what a hand IS, what a drop expects and
how the wire is compared with it (`on_wire`), and how the hand is drawn
(`draw`'s callable) — the screens' arrays and pictures differ, the gesture
does not.
"""

#: New snapshots without the expected state after which a send counts as
#: refused (the turn popups' `RESEND_AFTER`, core/turnpopup.py). Snapshots,
#: never frames: a frame count read a slow engine as a refusal.
REFUSED_AFTER = 20

CONFIRMED = "confirmed"
REFUSED = "refused"


class Carry:
    """One screen's gesture: what is in hand, and what a send expects."""

    def __init__(self):
        self.hand = None        # the screen's object, until the drop
        self.sent = None        # what the send expects, until the wire has it
        self.snapshots = 0      # new snapshots seen since the send

    @property
    def carrying(self):
        return self.hand is not None

    def take(self, hand):
        """Pick up: `hand` is in hand from now on (None takes nothing)."""
        self.hand = hand
        return hand

    def put_back(self):
        """The hand goes back where it came from; nothing was sent, so
        nothing is (decision 47). True if something was in hand."""
        had, self.hand = self.hand is not None, None
        return had

    def expect(self, expected):
        """A command went out: draw `expected` until the wire shows it."""
        self.sent, self.snapshots = expected, 0

    def set_down(self, expected):
        """The drop: the hand is emptied and its command's result drawn.
        Returns what was in hand."""
        hand, self.hand = self.hand, None
        self.expect(expected)
        return hand

    def settle(self, on_wire, new_snapshot):
        """After one update: CONFIRMED once `on_wire(sent)` holds, REFUSED
        after `REFUSED_AFTER` new snapshots without it, else None (also
        with nothing sent). Either outcome ends the pending send."""
        if self.sent is None:
            return None
        if on_wire(self.sent):
            self.sent = None
            return CONFIRMED
        self.snapshots += int(bool(new_snapshot))
        if self.snapshots > REFUSED_AFTER:
            self.sent = None
            return REFUSED
        return None

    def shown(self, wire):
        """What the screen draws: the pending send's expectation while one
        is pending, else the wire's."""
        return self.sent if self.sent is not None else wire

    def clear(self):
        """Leaving the screen, or the thing's owner changed under it."""
        self.hand = self.sent = None
        self.snapshots = 0

    def draw(self, surface, pointer, draw):
        """`draw(surface, hand, pointer)` while something is in hand — LAST,
        over everything, at the pointer, as the original draws its mouse
        picture. Drawing only: nothing is sent while a thing is carried."""
        if self.hand is not None and pointer is not None:
            draw(surface, self.hand, pointer)
