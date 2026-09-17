"""The galaxy map's movable boxes, read off the live field list.

The original opens two boxes ON screen 0 — the system window (box 0,
`SYS::Add_System_Display_Popup_Fields_`, sys.cpp:1746-1940) and the
fleet box (box 2, `FLEETPOP::Add_Fleet_Movement_Box_Fields_`,
fleetpop.cpp:127-227) — and `current_screen` does not change. What does
change is the FIELD_LIST, and that is the signal (decision 21): every
reading here is taken from the list on the wire, never remembered.

WHERE THE BOX FIELDS SIT. `MAINSCR::Add_Map_Fields_` adds the frame
buttons and the five sidebar windows, then `Add_Moveable_Box_Fields_`
(mainscr.cpp:1407), then the Q and V hotkeys and the map grid last
(:1424-1427). So an open box's fields are exactly those between the
research window field (the last sidebar window, :1405) and the Q/V/grid
tail — measured live on 15 September 2026 (brief 110 Stop 1,
`tools/galaxy_box_fields.json`): indices 0-20 identical with and
without a box, the box inserted from 21. The debug field (:1418) can sit
in the same gap and is not part of a box.

WHICH BOX. Each box's fields end in its whole-window hidden field
(`MOVEBOX::Add_Whole_Window_Field_`, movebox.cpp:853, and sys.cpp:1933),
whose rect contains every field of that box. A fleet box starts with its
drag strip, 0x23 high across the whole width (fleetpop.cpp:142); a
system window carries an ESC close button (sys.cpp:1781), a title strip
0x2F high (:1789) and a grid (:1922). The rectangles are read, not
assumed, so a box that has moved is simply wherever the list says —
and the list is only as fresh as the engine sends it (brief 110 A.1.4:
after a drag in the game window, the fleet box's new rect is probably
never sent).

A MODAL TEXT BOX (a warning, "%s is an outpost planet") replaces the
whole list with two fields: entry 0 and one full-screen hidden field
with the ESC hotkey — `Add_Hidden_Field_(0, 0, 639, 479, "\\x1B", 41)`,
textbox.cpp:249, and measured live in brief 110 Stop 1.

Anything else is `known = False`: a list this module cannot read is
said to be unreadable, never guessed at.
"""
from dataclasses import dataclass, field

#: `Add_Grid_Field_(22, 22, 1, 1, 506, 400, ...)`, mainscr.cpp:1427.
GRID_RECT = (22, 22, 527, 421)
TYPE_BUTTON = 0
TYPE_HIDDEN = 7
TYPE_MULTI_HOTKEY = 8
TYPE_GRID = 12
#: `_research_window_field`, mainscr.cpp:1405 — the last sidebar window.
SIDEBAR_LAST_RECT = (545, 344, 613, 415)
#: `_debug_field`, mainscr.cpp:1418, only while debugging is enabled.
DEBUG_RECT = (630, 470, 639, 479)
FULL_SCREEN_RECT = (0, 0, 639, 479)
ESC = 0x1B
#: Fleet box drag strip height, fleetpop.cpp:142 (`box_y + 0x23`).
FLEET_DRAG_HEIGHT = 0x23
#: System window title strip height, sys.cpp:1789-1795 (`+ 0x2F`).
SYSTEM_TITLE_HEIGHT = 0x2F


def rect(f):
    return (f.x, f.y, f.x_end, f.y_end)


def live_field(fields, spec):
    """The field `spec` names — its type and native rect — in the LIVE list.

    None when the list holds no such field. A field NUMBER means something
    else in every other list (decision 20, decision 59), so a send goes to
    the index this returns at the moment, or does not go at all. Extracted
    17 September 2026 (work order 128 C) from the map cancel's own lookup,
    when parking became its second caller.
    """
    if not spec:
        return None
    want = tuple(spec.get("rect") or ())
    return next((f for f in (fields or [])
                 if f.field_type == spec.get("field_type")
                 and rect(f) == want), None)


def _contains(outer, inner):
    return (outer.x <= inner.x and outer.y <= inner.y
            and outer.x_end >= inner.x_end and outer.y_end >= inner.y_end)


@dataclass
class Box:
    kind: str                       # "fleet" or "system"
    fields: list
    close: object = None            # the ESC button, looked up by hotkey

    @property
    def rect(self):
        """(x, y, x_end, y_end) of the whole window, inclusive."""
        return rect(self.fields[-1])


@dataclass
class BoxState:
    known: bool = False
    fleet: Box = None
    system: Box = None
    modal: bool = False
    boxes: list = field(default_factory=list)

    @property
    def open(self):
        return self.modal or self.fleet is not None or self.system is not None


def box_fields(fields):
    """The fields an open box added, or None if this is not a map list."""
    if len(fields) < 4:
        return None
    grid, v_key, q_key = fields[-1], fields[-2], fields[-3]
    if grid.field_type != TYPE_GRID or rect(grid) != GRID_RECT:
        return None
    if (v_key.field_type != TYPE_MULTI_HOTKEY
            or q_key.field_type != TYPE_MULTI_HOTKEY):
        return None
    start = next((i for i, f in enumerate(fields)
                  if f.field_type == TYPE_HIDDEN
                  and rect(f) == SIDEBAR_LAST_RECT), None)
    if start is None or start >= len(fields) - 3:
        return None
    return [f for f in fields[start + 1:-3] if rect(f) != DEBUG_RECT]


def _groups(span):
    """Split at each whole-window field; None if something is left over."""
    groups, current = [], []
    for f in span:
        current.append(f)
        if (len(current) >= 2 and f.field_type == TYPE_HIDDEN
                and all(_contains(f, g) for g in current[:-1])):
            groups.append(current)
            current = []
    return None if current else groups


def _kind(group):
    whole, first = group[-1], group[0]
    if (first.field_type == TYPE_HIDDEN
            and first.y_end - first.y == FLEET_DRAG_HEIGHT
            and (first.x, first.y, first.x_end)
            == (whole.x, whole.y, whole.x_end)):
        return "fleet"
    has_grid = any(f.field_type == TYPE_GRID for f in group)
    has_title = any(f.field_type == TYPE_HIDDEN
                    and f.y_end - f.y == SYSTEM_TITLE_HEIGHT
                    and (f.x, f.y, f.x_end) == (whole.x, whole.y, whole.x_end)
                    for f in group)
    if has_grid and has_title and _close(group) is not None:
        return "system"
    return None


def _close(group):
    return next((f for f in group
                 if f.field_type == TYPE_BUTTON and f.hotkey == ESC), None)


def classify(fields):
    """BoxState for one FIELD_LIST (a list of FieldInfo)."""
    fields = list(fields or [])
    if (len(fields) == 2 and rect(fields[1]) == FULL_SCREEN_RECT
            and fields[1].hotkey == ESC):
        return BoxState(known=True, modal=True)
    span = box_fields(fields)
    if span is None:
        return BoxState(known=False)
    groups = _groups(span)
    if groups is None:
        return BoxState(known=False)
    state = BoxState(known=True)
    for group in groups:
        kind = _kind(group)
        if kind is None:
            return BoxState(known=False)
        box = Box(kind, group, _close(group))
        state.boxes.append(box)
        setattr(state, kind, box)
    return state
