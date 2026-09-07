"""The list's two scroll arrows, where the original puts them.

**THEY ARE NOT BOXES, AND THAT IS THE DECISION.** The plate cuts no
hole for them, so they are not cutout-derived (decision 3) and the
brief's other option was two hand-placed boxes with a `thin_border`
or `text` skin (decisions 34/37). They are neither: their rectangles
come from `colonytrack.columns(...)["scroll"]` — the same column
table the headings and the cells are laid in — and the list area's
own top and bottom.

Two boxes would have been this screen's first non-cutout entries in
`boxes.json` and, worse, **a second copy of a position the column
table already fixes**: the scroll column's x and width are in
`layout_reference.list_columns`, and a box would repeat them where
they could drift. Decision 5 is about exactly that. The cost, stated:
the arrows are not F5-draggable, which every other piece of this
screen's furniture is. That is the right trade while the column table
is the authority — move the column and the arrows follow it, which a
box would not.

WHERE THE ORIGINAL PUTS THEM. `_x_fields[1]` at native (619, 15) and
`_x_fields[2]` at (619, 316) — `Add_Button_Field_`, colsum.cpp:263-264
— which is the column right of BUILDING, at the top and the bottom of
the list. Ours sit in the same column relative to the list, at its
own top and bottom; the native x is 1857 reference px and our list
ends at 1802, because the original's frame edge is thinner than the
plate's ring.

WHAT A CLICK DOES, and why it is two things.
`Decrement_First_` / `Increment_First_` (colsum.cpp:207-231) are what
the fields reach, and `colonysend` already drives both to establish
`_first` before a move. The arrow sends the same activation — so the
game's own window follows the player's eye — AND moves HD's
`Window.top`, which is what actually scrolls the picture.

**The send is not what makes the two agree.** Decision 46 is
unchanged: HD scrolls freely for VIEWING and `_first` is
re-established from scratch before anything is injected
(`colonysend`'s ESTABLISH state, every move, even after a sort that
just zeroed it). So an arrow whose activation the game refused —
`Decrement_First_` does nothing below ten colonies
(`colonies_count >= num_items`, colsum.cpp:210) — leaves the two out
of step and nothing breaks, because the next move re-establishes.
The send is a courtesy to a human watching both windows, not a
correctness mechanism, and it is written down that way so nobody
later removes the re-establishment on the strength of it.
"""
import pygame

from . import colonytrack

#: The scroll column's key in `layout_reference.list_columns`.
COLUMN = "scroll"

#: How tall an arrow is, as a share of the column's own width, so the
#: two stay square-ish at every resolution without a second table.
HEIGHT_RATIO = 1.0

#: Inset from the list area's edges, reference px, so an arrow does
#: not sit under the frame's rim (the `_frame_bleed_note` strip).
INSET_REF = 4


def arrows(area, cfg, scale):
    """(up_rect, down_rect) in window pixels, or (None, None).

    ONE function, and both the renderer and `handle_click` call it —
    decision 5, in the form the cells already take. None when the
    column table is absent, which is the single-track fixture's case.
    """
    columns = colonytrack.columns(area, cfg)
    if COLUMN not in columns:
        return None, None
    x, width = columns[COLUMN]
    inset = max(1, int(INSET_REF * scale))
    size = max(6, int(width * HEIGHT_RATIO))
    up = pygame.Rect(x, area.y + inset, width, size)
    down = pygame.Rect(x, area.bottom - inset - size, width, size)
    return up, down


def arrow_at(area, cfg, scale, point):
    """"up", "down" or None for a window point."""
    up, down = arrows(area, cfg, scale)
    if up is None:
        return None
    if up.collidepoint(point):
        return "up"
    if down.collidepoint(point):
        return "down"
    return None


def render(surface, area, cfg, scale, colour, first, rows_drawn, total):
    """Draw the two triangles, dimmed where the list cannot move.

    Dimmed rather than hidden: the original's buttons are always
    there and always clickable, and a control that disappears at the
    end of a list is a different affordance from one that stops
    responding. `Decrement_First_` clamps at 0 and `Increment_First_`
    is refused below ten colonies, so "cannot move" is the original's
    own state and not ours.
    """
    up, down = arrows(area, cfg, scale)
    if up is None:
        return
    can_up = first > 0
    can_down = first + rows_drawn < total
    for rect, pointing_up, live in ((up, True, can_up),
                                    (down, False, can_down)):
        shade = colour if live else tuple(max(0, c // 2)
                                          for c in colour[:3])
        pad = max(2, rect.width // 5)
        if pointing_up:
            points = [(rect.centerx, rect.top + pad),
                      (rect.left + pad, rect.bottom - pad),
                      (rect.right - pad, rect.bottom - pad)]
        else:
            points = [(rect.centerx, rect.bottom - pad),
                      (rect.left + pad, rect.top + pad),
                      (rect.right - pad, rect.top + pad)]
        pygame.draw.polygon(surface, shade[:3], points)


def handle(screen, x, y):
    """Take a click if it landed on an arrow. True when it did."""
    direction = arrow_at(*screen._list_view()[:3], (x, y))
    if direction is None:
        return False
    click(screen, direction)
    return True


def click(screen, direction):
    """One arrow click: move HD's view, and tell the game too.

    The send is a courtesy — see the module docstring. It goes
    through the field the ORIGINAL's own button reaches, found by its
    native coordinate in the live field list (`colonysend.field_at`),
    so a renumbered list cannot send the wrong one.
    """
    from . import colonysend
    area, cfg, scale, n_rows = screen._list_view()
    screen._window.scroll(-1 if direction == "up" else 1, n_rows,
                          screen._window.visible(area, cfg, scale, n_rows))
    if not screen.app.connected or screen._state is None:
        return
    xy = colonysend.STEP_UP_XY if direction == "up" else colonysend.STEP_DOWN_XY
    field = colonysend.field_at(screen._state, *xy)
    if field is not None:
        screen.app.client.activate_field(field)
