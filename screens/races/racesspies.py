"""Moving spies and choosing a mission on the Races screen — work order 197
(196's parked E1), through open fix 64 (`MSG_SET_SPIES`).

THE ORIGINAL (racescrn.cpp): a click on a spy group picks icons — the one
under the pointer and every icon right of it (`Draw_Icon_Group_Cursor_`,
:600-635: index = (x - x1) / spacing, remaining = count - index) — and a
click on another group drops them there, no group above 63; what does not
fit stays in hand (`Move_Spy_Group_From_Mouse_`, :390-408). A mission is a
multi-button per race (:441-443). Both reach the player record only when
the screen is left (`Update_Spy_Stuff_`, :518-527).

HD (TRANSCRIPTION `spy_move`, one command per change): the same two clicks — the
pick is computed here from HD's own drawing of the group, which uses the
original's spacing (`racesgeom.icon_spacing`); the drop builds the whole
list (every race the screen shows, their spies and missions, the agent
pool) and sends it as ONE command, which the engine applies all or nothing
and writes into the record; HD then shows what the wire says. A mission
click sends the same list with that race's mission changed. The hand
(`Hand`) is HD's own state until the drop; ESC or a right click drops it
back where it came from (nothing is sent: nothing moved on the engine's
side). Without the fix the engine drops the message and the counts on the
wire stay as they were.

THE CARRIED SPIES (work order 226 E, Data's decision 4): while in hand they
have left their group, which shows what stays, and ride on the pointer as
the original's mouse picture does — the spy icon and, for more than one,
the count (`racesdraw.draw_spy_hand`, racescrn.cpp:584-622). A click on no
group puts them back where they came from, as the original's loop does,
and the click then does what it does (a button, a mission).

DEVIATION `spy_drop_rest`: what does not fit the target group stays in the
group it came from (the original keeps it in hand for another drop); HD
keeps no hand across a command.

SET DOWN IS SET DOWN (work order 228 C, Data: "when it is set down it
appears for a moment at its starting place and then at the target"). The
cause: at the drop the hand was emptied and the command sent, but the
groups were drawn from the wire, which shows the move only from the
engine's first snapshot after it — so for the frames between, the spies
stood in their old group again; a mission click had the same gap. The
original moves its own arrays at once (`Move_Spy_Group_From_Mouse_`,
racescrn.cpp:390-408) and writes the record when the screen is left
(:518-527), so its picture never goes back. HD now draws what the send
expects (`Sent`, `shown`) from the drop on, until the wire shows it; if the
engine refuses (no such state within `REFUSED_AFTER` new snapshots) the
wire's groups are drawn again — the spies go back once.
"""
from dataclasses import dataclass

from . import racesgeom as geom

#: `Move_Spy_Group_From_Mouse_` (racescrn.cpp:394): no group above 63.
GROUP_MAX = 63
AGENTS = "agents"


def pick_count(count, box, icon_w, x):
    """`Draw_Icon_Group_Cursor_` (racescrn.cpp:600-635) for native x: the
    icons from the one under the pointer to the right end."""
    if count <= 0:
        return 0
    step = geom.icon_spacing(count, box, icon_w)
    total_w = min(icon_w + (count - 1) * step, box[2] - box[0] + 1) \
        if count > 1 else icon_w
    max_x = box[0] + total_w - 1
    x = max(box[0], min(x, max_x))
    index = (x - box[0]) // step if step else count - 1
    return count - min(index, count - 1)


@dataclass
class Hand:
    source: object          # a slot index, or AGENTS
    count: int


def groups(slots, agents):
    """{slot index or AGENTS: spies} for every race the screen shows."""
    out = {s.index: int(s.spies) for s in slots if movable(s)}
    out[AGENTS] = int(agents)
    return out


def drop(counts, hand, target):
    """`(new counts, what stays in hand)` — the original's drop."""
    counts = dict(counts)
    counts[hand.source] -= hand.count
    room = GROUP_MAX - counts[target]
    moved = min(room, hand.count)
    counts[target] += moved
    rest = hand.count - moved
    if rest:
        counts[hand.source] += rest     # HD keeps no hand across a send
    return counts, rest


#: New snapshots without the expected groups after which a send counts as
#: refused (the turn popups' `RESEND_AFTER`, core/turnpopup.py).
REFUSED_AFTER = 20


@dataclass
class Sent:
    groups: dict            # {slot index or AGENTS: spies} the send expects
    missions: dict          # {slot index: mission 0-2} it sets
    snapshots: int = 0      # new snapshots seen since


def on_wire(sent, slots, agents):
    """True once the wire shows every group and mission the send set."""
    return groups(slots, agents) == sent.groups and all(
        s.mission == sent.missions[s.index] for s in slots
        if s.index in sent.missions)


def settle(sent, slots, agents, new_snapshot):
    """The pending send after one update: None once the wire shows it or
    after `REFUSED_AFTER` new snapshots without it."""
    if sent is None or on_wire(sent, slots, agents):
        return None
    sent.snapshots += int(bool(new_snapshot))
    return None if sent.snapshots > REFUSED_AFTER else sent


def shown(slots, agents, hand, sent):
    """({group: spies drawn}, {slot: mission drawn}): the pending send's
    groups and missions while one is pending, else the wire's; what is in
    hand has left its group."""
    counts = dict(sent.groups) if sent is not None else \
        groups(slots, agents)
    if hand is not None and hand.source in counts:
        counts[hand.source] -= hand.count
    return counts, dict(sent.missions) if sent is not None else {}


def races_list(slots, counts, missions=None):
    """MSG_SET_SPIES's list: (player, spies, mission 1-3 or 0 kept) for
    every race the screen shows, in slot order."""
    missions = missions or {}
    return [(s.player, counts[s.index], missions.get(s.index, 0))
            for s in slots if movable(s)]


def movable(slot):
    """A race whose group the original lets the player use: shown, not
    eliminated (`Setup_Race_Screen_Data_`, racescrn.cpp:314-327)."""
    return slot.active and not slot.eliminated
