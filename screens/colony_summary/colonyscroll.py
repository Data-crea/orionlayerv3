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

**HOW WIDE THAT COLUMN IS, AND IT IS A TRANSCRIPTION NOW —
9 September 2026.** `col_scroll` used to be 36 reference px and the
number had no source: it was `1693 - 302 - 342 - 360 - 339 - 314`,
the leftover after the other five, which is precisely what a column
must not be when something is drawn in it.

The original states the column in two places and they agree:

- the TRACK is native x **621..626**. `Add_Scroll_Field_(621, 40, 0,
  n, 0, n - 10, 5, 271, …)` (colsum.cpp:278) counts it exclusively as
  width 5; `Draw_Bar_Indicator_`'s `Fill_(621, y1, 626, y2, 229)`
  (colsum.cpp:759) counts the same rectangle inclusively as 6, with
  the corner dots at 621 and 626 (colsum.cpp:767-770). One rectangle,
  two counts — the same shape as the map viewport's 506 against 505.
- the ARROWS start at native x **619** (colsum.cpp:263-264), and
  their extent is `animate::Get_Width_(pic)`, which lives in the
  player's LBX and is in no source file.

So the anim's width is MEASURED, off the original's own framebuffer
in `evidence/colony_summary_native_split.png`: the up arrow's blue
bbox is native x **619..627**, nine px. **Its left edge reproduces
the source's 619 exactly, and that is what makes the right edge
worth trusting** — the measurement is anchored on a feature the
source names, rather than on the picture alone.

Nine native px is **27 reference px**, and that is what the box
carries. The nine that were freed go to `col_building`, 314 -> 323,
because that column is already the declared home of this screen's
surplus width (`layout_reference._list_columns_note`, Data's Stage 1
decision) — so the residue lands somewhere that says why it is there
instead of somewhere that merely had room.

**AND THERE IS NO RESIDUE LEFT TO PLACE.** Since 9 September the six
columns are fractions of the `list_area` cutout
(`colonytrack.columns`), so they tile it exactly at any window size
by construction: the first starts at the cutout's left edge, the last
ends at its right, and a wider window widens all six in proportion
rather than handing the difference to whichever column is last. The
question "where does the leftover go" no longer has an answer because
it no longer has a subject.

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

from core import palette

from . import colonyfirst
from . import colonytrack

#: The scroll column's key in `layout_reference.list_columns`.
COLUMN = "scroll"

#: The arrow anim's height against the ORIGINAL'S OWN ROW BAND:
#: 16 native px in a 31 px band (`31*i + 34`, colsum.cpp:311). Both
#: halves are needed — a bare 16 is a pixel count and does not
#: survive a resolution change, so what is stored is the share the
#: original states and the pixels are derived from it.
#:
#: The 16 is MEASURED and single-source, like the "No Farming" size
#: and `SHIP_ICON_DIM`: `Add_Button_Field_` takes its extent from
#: `animate::Get_Width_/Get_Height_(pic)` (fields.cpp), so the anim's
#: size lives in the player's LBX and is in no source file. Measured
#: off the original's own framebuffer
#: (`evidence/colony_summary_native_split.png`), blue bbox y 23..38
#: for the up arrow and 325..341 for the down one — a 301 px
#: separation against the fields' own 316 - 15 = 301.
BAND_SHARE = 16 / 31

#: Inset from the list area's edges, reference px, so an arrow does
#: not sit under the frame's rim (the `_frame_bleed_note` strip).
INSET_REF = 4

#: The slider's four colours, transcribed from
#: `COLSUM::Draw_Bar_Indicator_` (colsum.cpp:747-771) and resolved
#: from the game's own palette — see `colors.json._slider_note`.
#: `colonyfirst` carries the INDICES (229 / 230 / 228) because it
#: reads them back off the framebuffer; these are the same indices
#: resolved, and the two must not drift, which a check asserts.
SLIDER_FILL = palette.col("colony_summary", "slider_fill", (28, 28, 164))
SLIDER_LIGHT = palette.col("colony_summary", "slider_light", (60, 60, 212))
SLIDER_DARK = palette.col("colony_summary", "slider_dark", (0, 0, 108))
TRACK_DOT = palette.col("colony_summary", "slider_track_dot", (0, 0, 0))


def track(area, cfg, scale):
    """The slider's track: one rect between the two arrows, or None.

    **ONE TRACK, NOT TEN CELLS — 9 September 2026.** `col_scroll` was
    plated per band like every other column, which drew ten stacked
    boxes where the original has a single continuous channel. The
    original's track is native x 621..626 running y 40..311, marked
    by four corner `Dot_`s (colsum.cpp:767-770) and matching the
    `Add_Scroll_Field_(621, 40, …, 5, 271)` that owns it
    (colsum.cpp:278). Its extent is exactly the span between the two
    step buttons at y 15 and y 316 (colsum.cpp:263-264), which is
    what this reproduces: the arrows' own inner edges.
    """
    up, down = arrows(area, cfg, scale)
    if up is None:
        return None
    return pygame.Rect(up.x, up.bottom, up.width, down.top - up.bottom)


def slider(area, cfg, scale, first, total):
    """The thumb's rect inside the track, or None when none is drawn.

    **NONE IS A STATE AND IT IS THE ORIGINAL'S.**
    `Draw_Bar_Indicator_` draws nothing at all — not even the track's
    corner dots — while `num_colonies < 10` (colsum.cpp:751), because
    below the window size there is nothing to scroll. `colonyfirst`
    already encodes that as `NOT_DRAWN` for the reading direction;
    this is the same fact for the drawing direction.

    THE ARITHMETIC IS THE ORIGINAL'S, with its line:

        y1 = 271 * _first / n + 40
        y2 = 271 * (_first + 10) / n + 40          colsum.cpp:752-753

    271 is the track's own height and 40 its top, so the expression
    is `track.h * first / n + track.y` — position from `first`,
    EXTENT from the visible-to-total ratio, which is what makes the
    thumb's LENGTH say how much of the list the window covers. The
    divisions are C integer division; both operands are non-negative
    here so `//` is the same truncation.

    **THE 10 IS THE ORIGINAL'S WINDOW, NOT HD'S ROW COUNT.**
    `colonyfirst.WINDOW`, from `_list_col[10]` (colsum.cpp:348). They
    are the same number today and they are not the same fact — the
    fundament's decision 46 corollary says any future k is computed
    against the original's ten.

    **AND `first` IS HD'S OWN VIEW, which decision 46 permits.** The
    original's slider reports the window its own rows are drawn from;
    so does this one. While the two windows are decoupled — HD scrolls
    freely for viewing and `_first` is re-established before anything
    is injected — the two sliders can differ, and a slider reporting
    the OTHER window would be the one that disagreed with the rows
    beside it.
    """
    tr = track(area, cfg, scale)
    if tr is None or total < colonyfirst.WINDOW or tr.height <= 0:
        return None
    y1 = tr.y + tr.height * max(0, first) // total
    y2 = tr.y + tr.height * min(total, first + colonyfirst.WINDOW) // total
    return pygame.Rect(tr.x, y1, tr.width, max(1, y2 - y1))


def arrows(area, cfg, scale):
    """(up_rect, down_rect) in window pixels, or (None, None).

    ONE function, and both the renderer and `handle_click` call it —
    decision 5, in the form the cells already take. None when the
    column table is absent, which is the single-track fixture's case.

    **THE HEIGHT COMES FROM THE ROW BAND, NOT FROM THE COLUMN WIDTH
    — 9 September 2026.** It used to be `int(width * HEIGHT_RATIO)`
    with the ratio at 1.0, i.e. the arrow was as tall as its column
    was wide. Two things were wrong with that. It is not a
    transcription of anything: the original's arrow is 9 px wide and
    16 tall, not square. And it made the arrow a function of a width
    that was itself the leftover of the other five columns, so the
    day `col_scroll` swelled to 1837 px the arrows became 1837 px
    tall — a control the height of the whole list, which is what
    Data's 4K screenshot shows.

    The band is what an arrow is measured against in the original and
    it is what HD measures against now, so an arrow is one row's
    worth of control at every window size and cannot outgrow the list
    however the columns are dragged. The WIDTH is still the column's,
    which IS the transcription: the anim is 9 native px and so is the
    column (native x 619..627).
    """
    columns = colonytrack.columns(area, cfg)
    if COLUMN not in columns:
        return None, None
    x, width = columns[COLUMN]
    inset = max(1, int(INSET_REF * scale))
    band = colonytrack.band_height(area, cfg)
    # Never taller than the band it is measured against: the check
    # asserts it, and the clamp is what makes the assertion a
    # property rather than a hope at a row count nobody has tried.
    size = max(6, min(band, int(round(band * BAND_SHARE))))
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
    # THE TRACK AND ITS THUMB, under the arrows. Nothing at all below
    # ten colonies — see `slider`.
    thumb = slider(area, cfg, scale, first, total)
    if thumb is not None:
        tr = track(area, cfg, scale)
        # The four corner dots mark the track's own ends
        # (colsum.cpp:767-770); they are the only thing the original
        # draws for the track itself.
        for cx in (tr.left, tr.right - 1):
            for cy in (tr.top, tr.bottom - 1):
                surface.fill(TRACK_DOT[:3], pygame.Rect(cx, cy, 1, 1))
        surface.fill(SLIDER_FILL[:3], thumb)
        # Borders drawn OVER the fill's own edge rows, light on top
        # and left, dark on bottom and right (colsum.cpp:762-765).
        surface.fill(SLIDER_LIGHT[:3],
                     pygame.Rect(thumb.left, thumb.top, thumb.width, 1))
        surface.fill(SLIDER_LIGHT[:3],
                     pygame.Rect(thumb.left, thumb.top, 1, thumb.height))
        surface.fill(SLIDER_DARK[:3],
                     pygame.Rect(thumb.left, thumb.bottom - 1, thumb.width, 1))
        surface.fill(SLIDER_DARK[:3],
                     pygame.Rect(thumb.right - 1, thumb.top, 1, thumb.height))
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
