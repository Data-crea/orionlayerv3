"""The single-colony screen's demolish — work order 325.

The original demolishes a building on a LEFT click on it (the branch
`orionlayer` with open fix 111, amended, `25fdf420`). The five orbital
buildings — Star Base, Battlestation, Star Fortress, Artemis System Net,
Dimensional Portal — are satellites (`Satellite_Anim_Pic`,
colony.cpp:196-211; colony_main.cpp:539-540) and are clicked through their
own field (`Check_Satellite_Fields`, colony.cpp:1563-1589), which asks for
each of them like any building. Every other building is clicked on its
cell of the scene (`Check_Bldg_Fields`, colony.cpp:1932-1971), whose one
silent case is the Capitol (its exempt list, :1942-1950, names the five
satellites as well, which never reach it). Past one building a turn it
says so (E 0x243, `Can_Scrap_Building`); otherwise it asks (E 0x107: the
name and half the cost, `Confirmation_Box`) and on YES turns the cell to
rubble, removes the building, recalculates the colony and refunds the
treasury. A building without a field — a station another supersedes, a
building the full grid has no cell for — cannot be clicked, and the
engine refuses it the same way.

HD draws the buildings as a list (the list's deviation is `coldraw`'s).
TRANSCRIPTION `building_demolish`: a left click on a row of that list
sends the colony and the building (open fix 111, `MSG_DEMOLISH`), and the
engine starts the original's own click on that building — which of its
answers follows, the Capitol's silence included, is the game's, and its
boxes come back as HD's message box (MSGB, `core.msgbox`). The decision is
made from the snapshot in hand at the moment of sending (P816): a fresh
`colwire.View` of it must be READY, show the same colony as the page
clicked, have the building, have no box of the game's up (MSGB), and not
be in the planet view (`drawing_display` 2, in which the original skips
the walk, colony.cpp:1319). One click sends once: until
`wire_protocol.EFFECT_PAIRS` snapshots have come since the send — the
first after a command can still show the world before it (P813) — a
second click on a row sends nothing, so a double click cannot ask twice.

Without fix 111 — an engine whose HELLO_REPLY lacks CAP_DEMOLISH — the
click is not taken and nothing changes: a left click on a row does
nothing, as before work order 325.

UNVERIFIED `building_demolish_live`: never run against a live engine
(Data's decision of 20 October 2026, no live runs); the engine side is
built and compiled, the box's arrival as MSGB and the refund are read from
the source.
"""
import logging

from core.wire_protocol import EFFECT_PAIRS

from . import colright, colwire

log = logging.getLogger("colony")

#: `colony_screen["drawing_display"]` while the planet view is up: the
#: original's `Evaluate_Input` skips the building walk there
#: (colony.cpp:1319), and the engine refuses the command.
PLANET_VIEW = 2


def offered(app):
    """The engine takes the demolish (open fix 111's CAP_DEMOLISH)."""
    # `is True`: a stand-in client that answers every attribute with a
    # callable must not read as an engine that takes the command
    client = getattr(app, "client", None)
    return bool(getattr(app, "connected", False)) and \
        getattr(client, "can_demolish", False) is True


def decide(state, page_index, bid):
    """The colony to send for `bid`, read off `state` now, or None."""
    if getattr(state, "message_box", None) is not None:
        return None          # a box of the game's is up: its loop, not ours
    fresh = colwire.View(state)
    if not fresh.draws or fresh.index != page_index:
        return None
    if fresh.block.get("drawing_display") == PLANET_VIEW:
        return None
    if bid not in fresh.buildings():
        return None
    return fresh.index


def _states(client):
    """How many snapshots the client has read (`GameClient.stats`)."""
    return (getattr(client, "stats", None) or {}).get("state", 0)


def latched(screen):
    """A demolish went out and its effect cannot be on the wire yet."""
    mark = getattr(screen, "_demolish_sent_at", None)
    return mark is not None and _states(screen.app.client) < mark + EFFECT_PAIRS


def click(screen, x, y):
    """True when a left click on a building row was the demolish's — sent,
    or refused by the state just read. False leaves the click to the rest
    of the screen (and, without fix 111, to nothing)."""
    view = screen._view
    if view is None or not view.draws or not offered(screen.app):
        return False
    bid = colright.row_at(screen, view.buildings(), x, y)
    if bid is None:
        return False
    if latched(screen):
        log.info("colony: demolish of building %d not sent — the last one's "
                 "effect is not on the wire yet", bid)
        return True
    colony = decide(screen.app.client.state, view.index, bid)
    if colony is None:
        log.info("colony: demolish of building %d not sent — the state "
                 "just read does not show it", bid)
        return True
    log.info("colony: demolish building %d of colony %d", bid, colony)
    screen.app.client.demolish(colony, bid)
    screen._demolish_sent_at = _states(screen.app.client)
    return True
