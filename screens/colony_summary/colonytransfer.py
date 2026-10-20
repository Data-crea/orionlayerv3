"""The Colonies list's move to ANOTHER colony — work order 316 B (Data's P8:
"The original moves colonists between colonies from the Colonies list,
including to another star by freighters ... Build it as the original's,
transcribed.").

THE ORIGINAL: with a cluster held, a click on another colony's job column is
`Send_Cluster_(that colony, job)` (colsum.cpp:869) and a click on its name
`Send_Cluster_(that colony, -1)` (colsum.cpp:909): the same walk the colony
screen's drop takes (colmove.cpp:145-531) — to a colony at the same star or,
by freighters, at another — with a job column the colonists first take that
job (`Give_Colonist_New_Job_` for a transfer, colmove.cpp:279-289). The
list's freighter count is its sidebar's "Freighters" (surplus_freighters,
colsum.cpp:436-437), which the move changes through the engine's own
recalculation; HD's sidebar draws it from the wire.

HD (TRANSCRIPTION `list_transfer`): on an engine with open fix 103 the
second click on another row starts `screens/colony/colxferflow.Flow` with
that colony and the column's job (-1 on the name) — the questions, ONE
long-form MSG_SETTLE_POPS, the boxes — and whoever did not go stays in hand
(`Send_Cluster_` resets the field mode only when nobody is left,
colmove.cpp:528-531). On an engine without it the row refuses, as before
(`colonypick.REFUSE_OTHER_COLONY`, DEVIATION `list_without_fix103`).
"""
from core import settlewire
from core.estrings import EStrings
from screens.colony import colxferflow

from . import colonymove, colonypick

_STRINGS = {}


def strings(screen):
    lang = (getattr(screen.app, "settings", None) or {}).get("language",
                                                              "en")
    if lang not in _STRINGS:
        _STRINGS[lang] = EStrings(lang)
    return _STRINGS[lang]


def start(move, state, row, job, client, connected, estrings):
    """`Send_Cluster_(row's colony, job)` with the pick in hand: a flow on
    `move` (a `colonymoveui.MoveController`). True when it was started."""
    pick = move.pick
    if pick is None or not settlewire.available(state):
        return False
    dest = row["index"]
    held = pick.cluster.indices
    move.flow = colxferflow.Flow(
        estrings, client, state, pick.colony, held, dest, job,
        colxferflow.names(state, estrings, pick.colony, dest, held), None,
        connected)
    move.message = ""
    return True


def advance(move, state):
    """Per snapshot: the flow's wait, and the hand after its outcome."""
    flow = move.flow
    if flow is None:
        return
    was = flow.phase
    flow.update(state, True)
    if was == colxferflow.SENDING and flow.phase != colxferflow.SENDING:
        _retake(move, state, flow)
    if flow.done:
        move.flow = None


def _retake(move, state, flow):
    hand, w = move.pick, flow.outcome
    if hand is None or w is None or not w.settled:
        return
    rest = colxferflow.rest_of(hand, state, w)
    if rest is None:
        move.pick = None
        return
    indices, words, n = rest
    move.pick = colonypick.Pick(hand.colony, hand.position, hand.job,
                                hand.slot, indices[0],
                                colonymove.Cluster(indices), words, n,
                                hand.icon_count)


def click(screen, x, y):
    """A click while a flow's box is up (or it waits): the flow's."""
    move = screen._move
    if move.flow is None:
        return False
    move.flow.click(screen._state, x, y)
    advance(move, screen._state)
    screen._rebuild_rows()
    return True


def key(screen, event_key):
    move = screen._move
    if move.flow is None:
        return False
    move.flow.key(screen._state, event_key,
                  chr(event_key) if 0 < event_key < 128 else "")
    advance(move, screen._state)
    screen._rebuild_rows()
    return True


def boxed(screen):
    """Is a question or a box on screen (the cluster then hangs on no
    pointer: `Reset_Mouse_Picture_` before each box, colmove.cpp:262)?"""
    flow = screen._move.flow
    return flow is not None and flow.box() is not None


def render(screen, surface):
    flow = screen._move.flow
    if flow is not None:
        flow.render(surface, screen.app.style, screen.app.res.load_json(
            "assets/shared/msgbox/labels.json", {}) or {})
