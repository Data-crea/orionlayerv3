"""The colony screen's moves to another colony on an engine with open fix
103: the drop on a planet of the system display, the TRANSPORT button and
its popup, the questions and boxes on the way (work order 316).

TRANSCRIPTION `transport_button`: while colonists are in hand the original
adds its button at (307, 159) (colony.cpp:1771-1781: field [11], C_Anims_
24, while an unassigned pop is left and the colony is valid) — HD draws it
as a shell button at the surface panel's top, its left edge at 307 of the
640 native columns, the shell's button size (the word typed in layout.json,
DEVIATION `button_words`). Its click opens the transport popup
(`colxport`); a row there, like a planet of the system display, is
`Send_Cluster_(colony, -1)` (colony_main.cpp:1072, colony.cpp:1798) — HD's
`colxferflow`: the questions, the command, the boxes. The colonists' own
colony puts them back (the re-flag branch, colmove.cpp:178-183); cancel
keeps them in hand.

WHAT STAYS IN HAND: after the walk the original still holds whoever did not
go (`Reset_Field_Mode_` only when no unassigned pop is left, colmove.cpp:
528-531). HD keeps the same colonists in its hand, taken again off the wire
at the indices the walk left them — and only if the wire holds them there;
otherwise they go back (the engine has re-assigned them already).
"""
import logging

import pygame

from core import settlewire
from core.hud import shell
from screens.colony_summary import colonymove, colonypick

from . import colgeom as geom
from . import colxferflow, colxport

log = logging.getLogger("colony.transfer")


class Transfer:
    """The screen's popup and flow, one at a time."""

    def __init__(self):
        self.popup = None
        self.flow = None
        self.button = None          # the TRANSPORT button's rect, drawn

    @property
    def busy(self):
        return self.popup is not None or self.flow is not None

    def clear(self):
        self.popup = self.flow = None


def available(screen):
    return settlewire.available(screen._state)


def button_rect(screen):
    """TRANSCRIPTION `transport_button`'s rect: the surface panel's top,
    left edge at 307 of 640 (colony.cpp:1780)."""
    surface = pygame.Rect(screen.box_screen_rect(geom.SURFACE_REGION[0]))
    inner = shell.inner(surface, screen.layout)
    w, h = shell.button_size(screen.layout)
    x = surface.x + surface.w * 307 // 640
    return pygame.Rect(min(x, inner.right - w), inner.y, w, h)


def shows_button(screen):
    t = screen.transfer
    return screen.pick is not None and not t.busy and available(screen) \
        and screen.carry.sent is None and screen.send_ is None


def names(screen, source, dest, held):
    return colxferflow.names(screen._state, screen._words.strings, source,
                             dest, held)


def start(screen, dest):
    """`Send_Cluster_(dest, -1)` with the colonists in hand."""
    pick = screen.pick
    if pick is None:
        return
    if dest == pick.colony:
        screen.carry.put_back()       # the re-flag branch
        return
    plague = None
    view = screen._wire
    if view is not None and view.draws and view.index == pick.colony:
        try:
            plague = view.events(screen._state)[0]   # CEVT, open fix 37
        except (KeyError, TypeError):
            plague = None
    held = pick.cluster.indices
    screen.transfer.flow = colxferflow.Flow(
        screen._words.strings, screen.app.client, screen._state, pick.colony,
        held, dest, -1, names(screen, pick.colony, dest, held), plague,
        screen.app.connected)


def update(screen, state, fresh):
    flow = screen.transfer.flow
    if flow is None:
        return
    was = flow.phase
    flow.update(state, fresh)
    if was == colxferflow.SENDING and flow.phase != colxferflow.SENDING:
        _retake(screen, state, flow)
    if flow.done:
        screen.transfer.flow = None


def _retake(screen, state, flow):
    """After the engine's outcome: whoever did not go stays in hand."""
    hand, w = screen.pick, flow.outcome
    if hand is None or w is None or not w.settled:
        return                        # nobody went: the same hand
    rest = colxferflow.rest_of(hand, state, w)
    if rest is None:
        log.info("transfer: the rest goes back (rest %s, wire n_pops %s)",
                 list(w.rest), w.pops.get(hand.colony, (None,))[0]
                 if w.pops else None)
        screen.carry.put_back()
        return
    indices, words, n = rest
    screen.carry.take(colonypick.Pick(
        hand.colony, hand.position, hand.job, hand.slot, indices[0],
        colonymove.Cluster(indices), words, n, hand.icon_count))


def click(screen, x, y):
    """A left click the transfer takes: True when it was its own."""
    t = screen.transfer
    if t.flow is not None:
        t.flow.click(screen._state, x, y)
        update(screen, screen._state, False)
        return True
    if t.popup is not None:
        what = t.popup.click(x, y)
        if what is None:
            return True
        kind, colony = what
        if kind == "cancel":
            t.popup = None            # cancel: -1, the colonists in hand
        elif kind == "choose":
            t.popup = None
            start(screen, colony)
        return True
    if shows_button(screen) and button_rect(screen).collidepoint(x, y):
        t.popup = colxport.Popup(screen._state, screen.pick.colony,
                                   screen.pick.cluster.indices)
        return True
    return False


def key(screen, event_key, unicode=""):
    t = screen.transfer
    if t.flow is not None:
        t.flow.key(screen._state, event_key, unicode)
        update(screen, screen._state, False)
        return True
    if t.popup is not None:
        if event_key == pygame.K_ESCAPE:
            t.popup = None            # HD EXTENSION `transport_escape`
        return True
    return False


def render(screen, surface, draw_hand):
    """The button and the popup, the colonists in hand over them as the
    popup draws its cluster (`Draw_Xport_Popup_` ends in `Draw_Cluster_`,
    colxport.cpp:55-57), then a question or a box over everything — with
    no cluster on the pointer (`Reset_Mouse_Picture_` before each box,
    colmove.cpp:262, :370)."""
    t = screen.transfer
    if shows_button(screen):
        r = button_rect(screen)
        shell.draw_button(surface, r, screen.layout,
                          screen.word("transport"), screen.app.style)
        t.button = r
    else:
        t.button = None
    if t.popup is not None:
        t.popup.render(surface, screen._state, screen.app.style,
                       (screen._data.get("transport") or {}),
                       getattr(screen, "_figures", None))
    if t.flow is None or t.flow.box() is None:
        draw_hand()
    if t.flow is not None:
        t.flow.render(surface, screen.app.style, screen.app.res.load_json(
            "assets/shared/msgbox/labels.json", {}) or {})
