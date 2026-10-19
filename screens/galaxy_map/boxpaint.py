"""The fleet box's painted selection — work order 310 (309's finding 7).

TRANSCRIPTION `drag_select` of the original's paint (mainscr_main.cpp:
983-995, `Set_Painted_Fleet_Fields_` mainscr.cpp:2468-2489): while the left
button is held over the open fleet box of the player's own stack
(`Can_Select_Fleet_Box_Ship_(0)`, fleetpop.cpp:396-401; within the box,
`Mouse_Within_Fleet_Box_`, movebox.cpp:168), every frame the ship cell
under the pointer takes ONE value — fixed at the press: the opposite of
the cell pressed (`Icon_Selection_Status_ == 0`, fleetpop.cpp:403-419),
"selected" for a press on the box beside the cells (no icon there, status
0). A press on the drag strip paints nothing (`scanned_field !=
drag_field`; HD's title stands there). The paint is the click: a single
press is a one-cell paint, which is why a cell click toggles (the box's
own scan does not, mainscr.cpp:3404-3430). The release ends it
(mainscr_main.cpp:893-897). v2 the same: mainscr_main.cpp:1008,
mainscr.cpp:2687.

HD sends the value as `MSG_SELECT_SHIP` (open fix 21) once per cell HD
offers (a "select" hit of `boxdraw`) that the pointer newly paints in the
gesture, in the order it crosses them, and sends nothing for a cell it does
not offer. The original paints every cell the pointer crosses and lets
`Ship_Can_Be_Selected_` → `Player_Can_Order_Ship_` refuse one
(mainscr.cpp:2482, :2674-2676); for the cells HD sends, that gate still
decides, so a ship that may not be ordered stays unselected, and the FSEL
block shows what took.

The paint lives only while ITS press is held: a frame of motion with the
left button no longer down by HD's own record of the press (`main.App`'s
pointer gate, armed by the press and cleared by any release, wherever it
went; posted debug-input events included) ends it, and so does the
screen's `enter` (the original reads `Mouse_Button_() == 1` every frame,
mainscr_main.cpp:983).

OMISSION `drag_strip_paint`: in the original a press on the drag strip
still sets `_mouse_btn_pressed`, so a drag from the strip into the cells
paints with the value the LAST gesture fixed (mainscr_main.cpp:986-993).
HD's title stands on the strip and its press starts no paint, so such a
drag paints nothing (`layout.json` `_markings`).
"""
import logging

log = logging.getLogger("galaxy_map.boxes")


def start(screen, value, ship=None):
    """A press in the fleet box: the gesture's value; `ship` the cell
    pressed, already sent by the click."""
    screen._box_paint = {"value": bool(value),
                         "painted": set() if ship is None else {ship}}


def active(screen):
    return getattr(screen, "_box_paint", None) is not None


def cell_at(screen, x, y):
    """The selectable ship cell under (x, y) as the last frame drew it:
    (ship, shown selected), or None."""
    for rect, action in reversed(getattr(screen, "_box_hits", None) or []):
        if isinstance(action, tuple) and action[0] == "select" and \
                rect.collidepoint(x, y):
            return action[1], not action[2]
    return None


def left_held(screen):
    """Whether the left press that began the paint is still down, by HD's
    own record (`main.App._pointer_gate.armed`); a host without that
    record (a tool's stand-in app) counts as held."""
    gate = getattr(getattr(screen, "app", None), "_pointer_gate", None)
    return True if gate is None else bool(gate.armed)


def own_cell_at(screen, x, y):
    """Whether (x, y) is on a cell of the player's own stack as the last
    frame drew it, offered or not: the original's right click finds every
    such cell (`Can_Select_Fleet_Box_Ship_`, the stack's owner only,
    mainscr.cpp:3319-3328; fleetpop.cpp:396-401)."""
    return any(rect.collidepoint(x, y)
               for rect in getattr(screen, "_box_own_cells", None) or [])


def motion(screen, x, y):
    """The held button over a cell: paint it, once per gesture. Returns the
    ship sent, or None. Motion without the press held ends the paint."""
    paint = getattr(screen, "_box_paint", None)
    if paint is None:
        return None
    if not left_held(screen):
        end(screen)
        return None
    cell = cell_at(screen, x, y)
    if cell is None or cell[0] in paint["painted"]:
        return None
    ship = cell[0]
    paint["painted"].add(ship)
    log.info("Box: ship %s painted -> %s", ship, paint["value"])
    if screen.app.connected:
        screen.app.client.select_ship(ship, paint["value"])
    return ship


def end(screen):
    """The release, or the gesture cancelled: nothing more is painted."""
    screen._box_paint = None
