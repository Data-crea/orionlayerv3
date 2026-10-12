"""The safety net for modals HD has no view for — work order 177, part C.

**WHY.** Data pressed CONTINUE and the HD galaxy map showed the map while
the engine was waiting in "Enter Home Star Name"; 174 had seen the same
after TURN with three colony-base questions. The screen number stayed
the map's (0) and the map drew itself over a game that was no longer
listening to it: the player was stuck in front of a map that ignored him.

**THE RULE.** A screen that owns a game screen id says what its OWN
field list looks like, and which modals it DRAWS itself (`known`).
Anything else the engine shows under that id — a field list that is
neither — is a modal HD does not know, and once it has stood for
`SETTLE` snapshots (a transition's first ticks still carry the old or a
half-built list; the no-glimpse rule of work order 166 A) the screen hands
over: `wants_original()` is true, the window shows the game's own picture
of that moment, clicks go through the existing fallback and keys through
`OriginalView.forward_key` (main.py). DEVIATION `modal_fallback`: the
original has no second picture; the net is how an HD client that does not
know a dialog still lets the player answer it.

**ONE LOG LINE PER UNKNOWN MODAL**, naming its shape — the field count and
each field's type, hotkey and size — so it can be built later.
"""
import logging

log = logging.getLogger("modalnet")

#: How long an unknown list must stand before the net takes over: `check`
#: runs once per FRAME (the screens' per-frame `update`), so here it is
#: five frames — measured in work order 186 part 4, where this comment still
#: said "snapshots". The hand-over gate counts the same number in SNAPSHOTS
#: for a modal box's early release (`handover.MODAL_SETTLE`, work order 187).
SETTLE = 5


def live(fields):
    return [f for f in (fields or []) if getattr(f, "index", 0) != 0]


def signature(fields):
    """The shape of a list, for the log: count, then type/hotkey/size."""
    rows = []
    for f in live(fields):
        hk = f.hotkey
        key = chr(hk) if 32 < hk < 127 else f"{hk:#x}"
        rows.append(f"t{f.field_type}/{key}/{f.x_end - f.x}x{f.y_end - f.y}"
                    f"@{f.x},{f.y}")
    return f"{len(rows)} fields: " + " ".join(rows[:12]) + (
        " …" if len(rows) > 12 else "")


class Net:
    """One screen's net. `own(fields)` and each of `known` are predicates
    over a live field list; `check(state, screen_id)` answers "hand over
    now?" and is called once per snapshot."""

    def __init__(self, name, own, known=(), settle=SETTLE):
        self.name, self.own, self.known = name, own, tuple(known)
        self.settle = settle
        self._streak = 0
        self._logged = set()
        self.unknown_signature = None
        #: The screen's own list was seen since its id came up — so an
        #: unknown list now REPLACED the page: a box, not a transition
        #: (work order 187, `ScreenBase.modal_is_box`).
        self.own_seen = False

    def classify(self, fields):
        """"own", the name of a known modal, or None (unknown)."""
        rest = live(fields)
        if not rest:
            return "empty"
        if self.own(rest):
            return "own"
        for name, pred in self.known:
            if pred(rest):
                return name
        return None

    def check(self, state, screen_id):
        if state is None or getattr(state, "current_screen", None) != screen_id:
            self._streak = 0
            self.own_seen = False
            return False
        kind = self.classify(getattr(state, "fields", None))
        if kind == "own":
            self.own_seen = True
        if kind is not None:
            self._streak = 0
            self.unknown_signature = None
            return False
        self._streak += 1
        if self._streak < self.settle:
            return False
        sig = signature(state.fields)
        self.unknown_signature = sig
        if sig not in self._logged:
            self._logged.add(sig)
            log.warning("%s: a modal HD has no view for — shown as the "
                        "game's picture, input passed through (%s)",
                        self.name, sig)
        return True

    @property
    def box(self):
        """The net's hand-over is a box over the page (see `own_seen`)."""
        return self.own_seen and self.unknown_signature is not None
