"""The hover popup: what a job group is, shown below its row.

**HD EXTENSION.** The original has no hover text on this screen at
all. It answers a hover by SCANNING — `Evaluate_Colony_Pop_Input_`
assigns `COLONY::_g_colony_n` from the scanned field
(colsum.cpp:880-890) and the bottom-left box redraws for that colony
— so the information exists there and appears somewhere else
entirely. The popup is ours.

*Marked here since 9 September 2026, and it is the third home
arriving late.* `layout.json`'s `_hd_extension_popup` and
`v3_projektstatus.md` both listed "colonypopup" as one of the places
this is marked, and this file said nothing of the kind for as long as
both of them did — the fundament's "a marking that two documents
claim exists is not a marking", in a file that describes the
behaviour at length and never names it. The smoke check that guards
this class read only the status document, so it defended the
sentence that was wrong. It walks the source now.

**IT OVERLAYS AND IT NEVER REFLOWS.** The list is the click frame
(decision 46): an HD row that moves against the game's ten-slot
window is the invisible failure that decision exists for, so a box
that inserts itself between two rows is refused outright. This one is
drawn over the rows below it and moves nothing.

**IT FLIPS ABOVE IN THE LAST ROW, and that is not a preference.**
`screen.render` draws the frame image AFTER the content
(screen.py:349-358), so anything outside a cutout is covered by the
frame's metal. The popup therefore has to stay inside `list_area`,
and when there is no room below the hovered row the only place left
is above it. Adjacency is what makes it readable at all; the row it
then covers is the neighbour, which is the same cost the other
direction pays.

**IT DOES NOT APPEAR WHILE A SELECTION IS HELD.** Aiming happens on
the hovered row itself, so a popup following the pointer would
flicker under the very gesture it interrupts — and in the last row
the flipped-above box would sit over the drop targets of the row
above. One rule, and it is checkable: no popup while
`MoveController` holds a pick.

Wording is `layout.json`'s (decision 15) and every width is measured
by RENDERING, never by one font's `.size()` — `Style.render_text`
can mix two fonts inside one string wherever a glyph is substituted
(decision 30).
"""
import pygame

from core import palette
from core import textfit

from . import colonytrack

BG = palette.col("colony_summary", "popup_bg", (14, 20, 34))
EDGE = palette.col("colony_summary", "popup_edge", (108, 132, 170))
TEXT = palette.col("colony_summary", "popup_text", (206, 216, 238))

#: Reference px of padding inside the box, and how far below the row
#: it sits. Small numbers, but they are layout and they are here
#: rather than in the drawing so one reader changes both.
PAD = 8
OFFSET = 4


def lines_for(row, job, words):
    """The sentences for one job group of one row.

    Substitution is `replace` and never `str.format` (decision 37):
    a brace in a translated string must not raise inside a render
    path.
    """
    def fill(template, **values):
        text = str(template or "")
        for key, value in values.items():
            text = text.replace("{" + key + "}", str(value))
        return text

    names = words.get("job_names", ["Farmers", "Workers", "Scientists"])
    cells = (row.get("cells") or ((), (), ()))[job]
    out = [fill(words.get("group", "{job}: {count}"),
                job=names[job] if job < len(names) else job,
                count=len(cells),
                pops=row.get("pops", 0))]
    # Identity, only when there is any — the common case says nothing
    # extra, which is the same rule the cell marks follow.
    kinds = {}
    for cell in cells:
        # `.kind`, not the cell — a cell is `colonyrows.Cell(kind,
        # figure)` since the figures arrived, and the popup counts
        # identities, never sprites.
        kind = cell.kind
        if kind:
            kinds[kind] = kinds.get(kind, 0) + 1
    for kind, count in sorted(kinds.items()):
        out.append(fill(words.get("group_" + kind, "{count} " + kind),
                        count=count))
    return [line for line in out if line]


def rect_for(area, cfg, scale, row, job, band, style, px, words):
    """(Rect, [surfaces]) for the popup, or None if there is nothing.

    The box is placed below `band` and flipped above it when the
    bottom of `area` is closer than its own height. It is clamped
    horizontally to `area` so a long line at a narrow resolution
    cannot run under the frame either.
    """
    lines = lines_for(row, job, words)
    if not lines:
        return None
    pad = max(2, int(PAD * scale))
    offset = max(1, int(OFFSET * scale))
    room = max(40, area.w // 3)
    rendered = []
    for line in lines:
        rendered.extend(textfit.wrap_rendered(style, line, px, room, TEXT))
    width = max(s.get_width() for s in rendered) + 2 * pad
    height = sum(s.get_height() for s in rendered) + 2 * pad
    top, row_h = band
    x = colonytrack.row_boxes(area, cfg, scale, row, band).targets[job][1].x
    x = max(area.x, min(x, area.right - width))
    y = top + row_h + offset
    if y + height > area.bottom:
        y = top - offset - height
    return pygame.Rect(x, y, width, height), rendered


def draw(surface, area, cfg, scale, row, job, band, style, px, words):
    """Draw it, or nothing. Returns the rect it took, or None."""
    made = rect_for(area, cfg, scale, row, job, band, style, px, words)
    if made is None:
        return None
    rect, rendered = made
    surface.fill(BG[:3], rect)
    pygame.draw.rect(surface, EDGE[:3], rect, 1)
    pad = max(2, int(PAD * scale))
    y = rect.y + pad
    for surf in rendered:
        surface.blit(surf, (rect.x + pad, y))
        y += surf.get_height()
    return rect
