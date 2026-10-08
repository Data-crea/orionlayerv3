"""The screen shell — work order 225, decisions 86-92 (Data, 8 October 2026).

Every full screen wears the galaxy map's arrangement: the title plate with
its orange lamps at the top, ONE content rectangle under it that is the
same on every screen, slanted buttons for the screen's own actions in a row
along the rectangle's bottom edge, and the closing action at its bottom
right. The numbers are `style.json` `chosen.shell` (where each comes from
is said there); nothing here or in a screen types one.

Why one rectangle (decision 89): no frame is shipped, but a frame must be
possible later, and a frame is drawn round ONE rectangle with bars of one
width between panels. So every screen fits its panels into `content()`,
with `gap()` between two panels and `inset()` inside one.

THE SHELL IS DECLARED, NOT DRAWN BY THE SCREEN. A screen builds a `Shell`
with its title (a callable: the title comes from where the screen's title
always came from) and its buttons, and calls `render` last before its help
and `button_at` first in its click handler. Every rect a shell button is
drawn in is the rect it is hit in — `button_rect` (decision 5).

HD EXTENSION `shell`: the original's screens are 640x480 pictures, each
with its own edges; one rectangle, one spacing and one button row for all
of them are ours (decision 89: a frame stays possible).

"Selected" and "pressed" (decision 92) are the blocks' states: a selected
control is "active" (the shared 'on' fill and the lit edge), a pressed one
is "pressed" (the GAME menu's orange word, `core.pressfeedback`); the two
never look alike.
"""
import time

import pygame

from core import mouse as mouse_input
from core.hud import blocks as hud
from core.hud import style as hudstyle

#: How long a clicked shell button shows "pressed", in seconds — the frame
#: buttons' own span (`screenframe.ACTIVE_FOR`), one value for both.
PRESSED_FOR = 0.30


def _tok(name):
    return hudstyle.get().get(f"shell.{name}")


def content_ref():
    """The content rectangle in reference px, (x, y, w, h)."""
    return tuple(_tok("content"))


def content(layout):
    """The content rectangle in device px. Its top and bottom keep their
    distance from the WINDOW's edges (`Layout.vertical`, "stretch"), as the
    galaxy map's plate and bar do, so on a window taller than 16:9 the
    rectangle still meets the title plate and the bar."""
    x, y, w, h = content_ref()
    sy, sh = layout.vertical(y, h, "stretch")
    return pygame.Rect(int(x * layout.scale + layout.offset_x), sy,
                       int(w * layout.scale), sh)


def gap(layout):
    """Device px between two panels."""
    return int(round(_tok("panel_gap") * layout.scale))


def inset(layout):
    """Device px from a panel's rect to what stands inside it."""
    return int(round(_tok("panel_inset") * layout.scale))


def element_gap(layout):
    """Device px between two elements inside a panel."""
    return int(round(_tok("element_gap") * layout.scale))


def inner(rect, layout):
    """`rect` less the panel inset on every side."""
    i = inset(layout)
    return pygame.Rect(rect).inflate(-2 * i, -2 * i)


def button_size(layout):
    w, h = _tok("button")
    return int(w * layout.scale), int(h * layout.scale)


def row_rect(layout):
    """The band the button row stands in: the rectangle's bottom, one
    button high, the whole width."""
    c = content(layout)
    _w, h = button_size(layout)
    return pygame.Rect(c.x, c.bottom - h, c.w, h)


def panels(layout, row=False):
    """Where a screen's panels go: the whole rectangle, or — with a button
    row — the rectangle above the row less one gap (decision 90: a row lies
    INSIDE the rectangle)."""
    c = content(layout)
    if not row:
        return c
    r = row_rect(layout)
    return pygame.Rect(c.x, c.y, c.w, r.y - gap(layout) - c.y)


def split(rect, layout, shares, vertical=False):
    """`rect` cut into len(shares) pieces with `gap()` between them. A
    share is a weight (float) or a fixed size in REFERENCE px (int); the
    weights share what the fixed pieces leave. The last piece takes the
    rounding, so the pieces meet `rect`'s far edge exactly."""
    r = pygame.Rect(rect)
    total = r.h if vertical else r.w
    g = gap(layout)
    fixed = [int(round(s * layout.scale)) if isinstance(s, int) else None
             for s in shares]
    free = total - g * (len(shares) - 1) - sum(f for f in fixed if f)
    weight = sum(s for s, f in zip(shares, fixed) if f is None) or 1.0
    out, pos = [], (r.y if vertical else r.x)
    for i, (s, f) in enumerate(zip(shares, fixed)):
        size = f if f is not None else int(free * s / weight)
        if i == len(shares) - 1:
            size = (r.bottom if vertical else r.right) - pos
        out.append(pygame.Rect(r.x, pos, r.w, size) if vertical
                   else pygame.Rect(pos, r.y, size, r.h))
        pos += size + g
    return out


def title_rects(layout):
    """(plate rect, text rect): the plate centred on the content rectangle,
    its top on the window's top edge — the galaxy map's place (work order
    170), centred on the rectangle as the map's is on the map."""
    c = content(layout)
    return hud.title_plate_rect(c.centerx, 0, layout.scale)


def button_rect(layout, slot):
    """A shell button's device rect: `slot` an int counts row buttons from
    the rectangle's left edge, one button wide with `element_gap` between;
    "action" is the bottom-right closing action, its rect's right edge on
    the rectangle's right edge (decision 87)."""
    row = row_rect(layout)
    w, h = button_size(layout)
    if slot == "action":
        return pygame.Rect(row.right - w, row.y, w, h)
    step = w + element_gap(layout)
    return pygame.Rect(row.x + int(slot) * step, row.y, w, h)


def hit(rect, x, y):
    """A shell button is hit as the parallelogram it is drawn as."""
    return hud.slant_hit(rect, x, y)


def draw_button(surface, rect, layout, label, style, state="normal"):
    """A shell button: the slanted button, its word in capitals and NO icon
    (decision 91 — the glyphs read as grey placeholder squares)."""
    hud.slant_button(surface, rect, layout.scale,
                     _pointer(rect, state), label.upper(),
                     icon=None, style_renderer=style)


def _pointer(rect, state):
    if state != "normal":
        return state
    return "hover" if hit(rect, *mouse_input.pos()) else "normal"


class Shell:
    """What one screen declares: its title and its buttons.

        Shell(title=lambda: words["title"],
              buttons=[("hire", "Hire", 0), ("return", "Return", "action")],
              row=True)

    `title` is a callable (or None: a screen without a title in the game,
    the main menu, takes only the rectangle). Each button is (key, label,
    slot); a label may be a callable. `enabled(key)`, `selected(key)` and
    `visible(key)` are asked per frame when given. `row` says whether the panels leave
    room for a button row (`panels(layout, row)`)."""

    def __init__(self, title=None, buttons=(), row=False, enabled=None,
                 selected=None, visible=None):
        self.title = title
        self.buttons = list(buttons)
        self.row = row
        self.enabled = enabled
        self.selected = selected
        self.visible = visible        # visible(key): False = not drawn, not hit
        self._pressed = None          # (key, monotonic time)

    def shown(self):
        return [b for b in self.buttons
                if self.visible is None or self.visible(b[0])]

    def rect(self, layout, key):
        for k, _label, slot in self.buttons:
            if k == key:
                return button_rect(layout, slot)
        return None

    def panels(self, layout):
        return panels(layout, self.row)

    def state(self, key):
        if self.enabled is not None and not self.enabled(key):
            return "disabled"
        p = self._pressed
        if p and p[0] == key:
            if time.monotonic() - p[1] < PRESSED_FOR:
                return "pressed"
            self._pressed = None
        if self.selected is not None and self.selected(key):
            return "active"
        return "normal"

    def render(self, surface, layout, style):
        if self.title is not None:
            text = self.title() if callable(self.title) else self.title
            c = content(layout)
            hud.title_plate(surface, c.centerx, 0, layout.scale, text or "",
                            style)
        for key, label, slot in self.shown():
            word = label() if callable(label) else label
            draw_button(surface, button_rect(layout, slot), layout, word,
                        style, self.state(key))

    def key_at(self, layout, x, y):
        """The key of the shown shell button under (x, y), or None — a
        question only: nothing is pressed (the right click's help)."""
        for key, _label, slot in self.shown():
            if hit(button_rect(layout, slot), x, y):
                return key
        return None

    def button_at(self, layout, x, y):
        """The key of the enabled shell button under (x, y), or None; a hit
        starts its pressed feedback."""
        for key, _label, slot in self.shown():
            if hit(button_rect(layout, slot), x, y):
                if self.state(key) == "disabled":
                    return None
                self._pressed = (key, time.monotonic())
                return key
        return None
