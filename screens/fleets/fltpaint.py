"""The Fleets grid's painted selection — work order 403 A (gap 5 of
work order 401's comparison).

TRANSCRIPTION `drag_paint` of the original's paint (flt1.cpp:433-455,
`Draw_Fleet_Screen_`): with the left button held and relocate mode not 1
(:433, the painting is off then), every ship cell the pointer is over
takes the value `fleet_ship_selection_status` — the first cell of the
gesture fixes it as the opposite of its own state (`selected == 0`,
:446-448) — and the cell is marked and boxed. The paint is the click: the
big icons' own click does not select (flt2.cpp:924-934, a click on one is
the right button's detail view), so a single press is a one-cell paint.

HD sends the value as `MSG_SELECT_SHIP` (open fix 28) once per cell the
pointer newly crosses in the gesture, in the order it crosses them; the
selection HD draws next frame is the one FLTS reports, never the one sent.
The galaxy map's fleet box has the same rule (`screens/galaxy_map/
boxpaint.py`, mainscr_main.cpp:983-995); this is its own copy for this
screen's own grid, because a shared name across two screens is a shared
fault (the rule's four lines, not an import of another screen's module).

DEVIATION `drag_value_fixed`: the original clears the status at the top of
EVERY loop pass (flt1.cpp:596), so its value is chosen again each frame
from the cell then under the pointer, and a button held still on one cell
asks the same question every frame. HD fixes the value at the press and
keeps it to the release, which is what the original's own paint looks like
while the pointer moves and is stable while it does not.

The paint lives only while ITS press is held: a frame of motion with the
left button no longer down by HD's own record (`main.App._pointer_gate`,
armed by the press and cleared by any release), the release itself, and
the screen's `enter` end it (the original reads `Mouse_Button() == 1`
every frame, flt1.cpp:431).
"""
import logging

log = logging.getLogger("fleets")


def active(screen):
    return getattr(screen, "_paint", None) is not None


def allowed(screen):
    """Where the engine would let a cell be selected at all (decision 33):
    a snapshot the screen trusts, the player's own stack
    (flt1.cpp:1185, :1193) and not relocate mode 1 (flt1.cpp:433)."""
    view = screen._view
    if not (screen.app.connected and view and view.ok):
        return False
    if not view.own_stack:
        return False
    return int(view.block.get("relocate_mode", 0)) != 1


def press(screen, slot):
    """A press on a grid cell: send its opposite and start the paint."""
    screen._paint = None
    if not allowed(screen):
        return False
    cell = screen._cells[slot]
    value = not cell.selected
    screen.app.client.select_ship(cell.ship_idx, value)
    screen._paint = {"value": value, "painted": {cell.ship_idx}}
    return True


def left_held(screen):
    """Whether the press that began the paint is still down, by HD's own
    record; a host without that record (a tool's stand-in app) counts as
    held."""
    gate = getattr(getattr(screen, "app", None), "_pointer_gate", None)
    return True if gate is None else bool(gate.armed)


def motion(screen, x, y):
    """The held button over a cell: paint it once per gesture. Returns the
    ship sent, or None. Motion with the press no longer held ends it."""
    paint = getattr(screen, "_paint", None)
    if paint is None:
        return None
    if not left_held(screen) or not allowed(screen):
        end(screen)
        return None
    slot = screen._slot_at(x, y)
    if slot is None:
        return None
    cell = screen._cells[slot]
    if cell.ship_idx in paint["painted"]:
        return None
    paint["painted"].add(cell.ship_idx)
    if cell.selected == paint["value"]:
        return None          # the original's assignment would change nothing
    log.info("Fleets: ship %s painted -> %s", cell.ship_idx, paint["value"])
    screen.app.client.select_ship(cell.ship_idx, paint["value"])
    return cell.ship_idx


def end(screen):
    """The release, or the gesture cancelled: nothing more is painted."""
    screen._paint = None
