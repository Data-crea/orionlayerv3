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

DEVIATION `spy_drop_rest`: what does not fit the target group stays in the
group it came from (the original keeps it in hand for another drop); HD
keeps no hand across a command, and draws the hand as its number beside
the pointer, not as the original's pointer icon.
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
