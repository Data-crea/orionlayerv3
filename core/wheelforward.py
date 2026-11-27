"""Forward the mouse wheel to a list the ENGINE owns (work order 441).

HD EXTENSION `wheel_forward`: the original game has no wheel. orion2re
v2.0.2 does: `fields::Handle_Mouse_Wheel` (fields.cpp:2813-2872) steps a
hovered scroll field by max(1, range / 10) per notch, and a scroll field
that is the only one of its axis on the screen takes the event wherever the
pointer is (:2844-2870). Open fix 132 (`MSG_INJECT_WHEEL`, `CAP_WHEEL`)
feeds such an event into the game's own queue; the screens that draw a list
whose offset the engine holds (the design pickers' `first_row` in DSBX,
Refit's `first` in RFIT, the Leaders' ship grid `first_row` in OFFS) send
the notches here and do NOT move anything themselves: the next snapshot
carries the new offset, as it does after one of the list's arrows.

Without CAP_WHEEL nothing is sent and the caller carries on as it did
before: no wheel on that list.

HD EXTENSION `wheel_rows` (the measured exception): the engine's own
per-notch step is lumpy on Refit (`colrefit.cpp:20-36`, `:367`: the step is
two units of a five-unit row and `Update_First_Ship` snaps back, so single
notches are lost) and on the design pickers (`scroll.cpp:128-143`,
`desbox.cpp:375-385`: `first_row` is recomputed from the thumb only after
half a thumb, so every second notch jumps 7-8 rows). Those two lists
therefore do NOT use `forward`: a notch presses the list's one-row arrow
field once (`over`, `notches`), the path the arrow click takes. Leaders
keeps `forward`; the generic path stays for later lists.
"""
from core import nativeview as nat


def native_point(layout, screen_x, screen_y):
    """The 640x480 pixel under a window point, or None outside the picture."""
    return nat.from_hd_point(layout.to_ref(screen_x, screen_y), layout)


def inside(point, rect):
    """Is `point` in the INCLUSIVE native rect (x1, y1, x2, y2)?"""
    return point is not None and rect[0] <= point[0] <= rect[2] and \
        rect[1] <= point[1] <= rect[3]


def forward(app, layout, direction, screen_x, screen_y, rects):
    """Send `direction` notches (pygame: +1 = up, the wire's sign too) at
    the pointer's own game-space pixel when it lies in one of the native
    `rects`, and only to an engine with CAP_WHEEL. True when a frame went
    out; the caller must not scroll locally either way."""
    if not direction or not getattr(app, "connected", False):
        return False
    client = getattr(app, "client", None)
    if client is None or not getattr(client, "can_wheel", False):
        return False
    point = native_point(layout, screen_x, screen_y)
    if not any(inside(point, r) for r in rects):
        return False
    return bool(client.inject_wheel(point[0], point[1], int(direction)))


#: HD EXTENSION `wheel_rows`: most one-row arrow presses one frame's wheel
#: events may queue, so a fast spin does not send hundreds. INVENTION (no
#: original value; five rows is a screenful of a refit list).
ROWS_PER_FRAME = 5


def over(app, layout, screen_x, screen_y, rects):
    """True when the pointer is in one of the native `rects` and the game
    is connected: the rect rule the lists whose wheel is `rows` share with
    `forward`."""
    if not getattr(app, "connected", False):
        return False
    point = native_point(layout, screen_x, screen_y)
    return any(inside(point, r) for r in rects)


def notches(direction):
    """`direction` (pygame's signed notch count) clamped to what one frame
    may press: (+1 up / -1 down, how many), or (0, 0) for none."""
    if not direction:
        return 0, 0
    return (1 if direction > 0 else -1), min(abs(int(direction)),
                                             ROWS_PER_FRAME)
