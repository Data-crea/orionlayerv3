"""What one snapshot lets the Races screen believe, and what it may send.

The Leaders screen's shape (`screens/leaders/ldrwire.py`): `View` is
built from ONE snapshot, says in one of its states what HD may draw and
send, and holds no rule the screen could also hold.

WHAT IS ON THE WIRE, and how each is read:

  the players    all eight `s_player` records (`player_raw`) — name,
                 race, colour, contact, treaty, relations, the treaties'
                 levels, spies, ignoring (core/structs/player.py, the
                 offsets added by work order 175 C: header route and
                 `tools/races_check.py` over 14 saves)
  the lists      `Get_Players_Dead_Or_Alive_Or_Omniscient_` for the
                 portraits and texts, `Get_Active_Players_(0, 0)` for the
                 bars, spies and fields (bill.cpp:312-338, :565-596;
                 racescrn.cpp:766, :792) — rebuilt here, and CHECKED: the
                 live field list must be the main or the WHO mode's shape
                 for exactly that many races (`racesgeom.main_shape`,
                 `who_shape`), or the screen refuses
  the mode       MAIN (8 + 5n fields) or WHO (7 + n) — read off the list,
                 never remembered (racescrn.cpp:426-488)
  a native box   `core/gamebox.detect` — the declare-war confirmation

WHAT IS NOT: which action WHO mode has armed (a local of `Race_Screen_`,
`active_action_field`); the spy drag and the missions before they are
committed (`Update_Spy_Stuff_`, :518-530); the race report's and the
diplomacy screen's state — both report screen 6 and show a list that is
neither shape, so they are handed to the fallback picture with a reason
(decision 22), which is the game's own screen and fully playable.
"""
from core import gamebox
from core.structs import player as player_struct

from . import racesgeom as geom

MAIN = "main"
WHO = "who"
IN_BOX = "in_box"
WAITING = "waiting"
DIALOG = "dialog"            # the report, diplomacy, anything else
NO_PLAYER = "no_player"

#: How long a list that is neither shape may be the previous screen's,
#: in snapshots, before it is read as a dialog. The research screens'
#: measured bound (work order 166), as the Leaders screen uses it.
WAIT_BOUND = 66


def _live(fields):
    return [f for f in (fields or []) if f.index != 0]


def _shape_of(fields):
    return [((f.x, f.y, f.x_end, f.y_end), f.field_type) for f in fields]


def players_of(game_state):
    raws = getattr(game_state, "player_raw", None) or []
    return [player_struct.parse(r) for r in raws
            if len(r) >= player_struct.SIZE]


def active_players(players, me, num_players):
    """`Get_Active_Players_(0, 0)`: contacted living players, index order."""
    if not 0 <= me < len(players):
        return []
    met = player_struct.contacts(players[me])
    return [i for i in range(min(num_players, len(players)))
            if i != me and not players[i].eliminated and met[i]]


def shown_players(players, me, num_players):
    """`Get_Players_Dead_Or_Alive_Or_Omniscient_(0, 0)`: the active list,
    then every eliminated player — and, for an omniscient player, every
    other one — not yet in it (bill.cpp:312-338)."""
    out = active_players(players, me, num_players)
    if not 0 <= me < len(players):
        return out
    omni = player_struct.has_omniscience(players[me])
    for i in range(min(num_players, len(players))):
        if i != me and i not in out and (omni or players[i].eliminated):
            out.append(i)
    return out[:geom.SLOTS]


class View:
    def __init__(self, game_state, waited=0):
        self.state = NO_PLAYER
        self.reason = ""
        self.fields = _live(getattr(game_state, "fields", None))
        self.players = players_of(game_state)
        self.me = int(getattr(game_state, "player_num", 0) or 0)
        n = int(getattr(game_state, "num_players", 0) or 0) or \
            len(self.players)
        self.active = active_players(self.players, self.me, n)
        self.shown = shown_players(self.players, self.me, n)
        self.box = None
        self.buttons = {}
        self._classify(waited)

    def _classify(self, waited):
        if not 0 <= self.me < len(self.players):
            self.reason = "The snapshot carries no player records."
            return
        box = gamebox.detect(self.fields)
        if box is not None:
            self.box, self.state = box, IN_BOX
            return
        shape = _shape_of(self.fields)
        n = len(self.active)
        for state, want in ((MAIN, geom.main_shape(n)),
                            (WHO, geom.who_shape(n))):
            if shape == [(r, t) for r, t, _hk in want]:
                self.state = state
                self.buttons = {name: f for name in geom.BUTTONS
                                for f in self.fields
                                if (f.x, f.y, f.x_end, f.y_end)
                                == geom.button_rect(name)}
                return
        if waited < WAIT_BOUND:
            self.state = WAITING
            self.reason = ("The game reports the Races screen and has not "
                           "built its field list yet.")
            return
        self.state = DIALOG
        self.reason = (f"The game shows one of the Races screen's own "
                       f"dialogs (the race report or diplomacy — "
                       f"{len(self.fields)} fields, neither the main nor "
                       f"the WHO list for {n} race(s)); its own picture "
                       f"is shown.")

    @property
    def in_box(self):
        """`screens/fleets/fltbox` asks this — the native box's drawing and
        its buttons are reused as they are (the Leaders screen's way).
        Missing in 175: the declare-war box crashed the screen, found by
        work order 176's live run."""
        return self.state == IN_BOX

    @property
    def draws(self):
        return self.state in (MAIN, WHO, IN_BOX, WAITING)

    def field(self, rect):
        return next((f for f in self.fields
                     if (f.x, f.y, f.x_end, f.y_end) == tuple(rect)), None)

    def sendable(self, action):
        """Every button and, in WHO mode, a race: each answers in the list
        HD reads back (a mode change, a dialog, a box). The missions and
        the spy drag are not sent: their effect is not on the wire until
        the screen commits it (HD STATE `missions_and_spies`, parked)."""
        if self.state == MAIN:
            return action in self.buttons
        if self.state == WHO:
            return action in self.buttons or action == "race"
        return False
