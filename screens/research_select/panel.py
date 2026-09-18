"""Drawing the eight category panels, their rows and the hover.

Everything here is positioned from `core.researchlist`'s own native
rectangles through `native.window_rect`, so DRAWING AND HIT-TESTING
CANNOT DISAGREE: `screen.py` resolves a click back to a native pixel
and tests it against `Entry.row_rect`, which is the rectangle this
module draws in (decision 5).

That guarantees agreement and NOT correctness — the stacked colony
figures agreed with themselves through 165 of 210 missed clicks
(decision 5's own amendment). So the smoke check for this screen
asserts against the DRAWN PIXELS, as work order 128 D did for the
Planets list: it renders, then picks the visible centre of each row and
requires the hit test to name that row.

THE COLOURS the original uses are `TECH::_tech_color[0]` and `[2]` —
`[2]` for the field the player is already researching and for its
chosen application, `[0]` otherwise (tech.cpp:686-696). In SELECT mode
there is no current field: `Tech_Select_` zeroes it before the list is
built (tech.cpp:104-105), so `[2]` is unreachable here and this module
draws one colour for every row. Written down rather than discovered
later: the second colour is not missing, it has nothing to mark.

THE ORIGINAL SQUEEZES, HD SHRINKS. `BILL::Squeeze_Print_`
(tech.cpp:700, :735) compresses the glyphs of a name to fit its width
rather than clipping it. An HD font cannot be squeezed, so the size
comes down until the string fits — the same intent, and the nearest
thing available. DEVIATION, in `screen.py`'s marked list.
"""
import pygame

from core import palette

from . import native

#: The smallest the shrink may go before it gives up and clips.
MIN_FONT = 8


def col(key, default):
    return palette.col("research_select", key, default)


def _fit(style, text, max_w, size):
    """The largest size at or below `size` whose render fits `max_w`."""
    while size > MIN_FONT:
        if style.get_font(size).size(text)[0] <= max_w:
            return size
        size -= 1
    return MIN_FONT


def _blit_text(surface, style, text, pos, max_w, size, color):
    """One name, shrunk to fit, through Style.render_text (decision 30).

    Every string here can carry game data — a field name, an
    application name, a cost — so none of them goes through a bare
    `font.render`: `render_text` is what falls back per character on a
    glyph the display font cannot draw.
    """
    if not text:
        return None
    size = _fit(style, text, max_w, size)
    surf = style.render_text(text, size, color)
    surface.blit(surf, pos)
    return surf


def draw(surface, layout, style, entries, hover, words, names, wording):
    """Draw the eight entries. `hover` is (entry index, row) or None."""
    for entry in entries:
        if entry.offered:
            _draw_entry(surface, layout, style, entry, hover, words,
                        names, wording)


def _draw_entry(surface, layout, style, entry, hover, words, names, wording):
    # The category's own name. The original paints it into the TECHSEL
    # art; HD prints it, and the WORD is still the game's own —
    # billtext 64 + group (tech.cpp:802-816). Marked in screen.py.
    label = wording.group_name(entry.group) if wording else None
    if label:
        _blit_text(surface, style, label,
                   native.window_point((entry.x, entry.y + 2), layout),
                   native.window_width(entry.x, entry.y + 2, 150, layout),
                   layout.font_size(13), col("category", (128, 148, 186)))

    # The cost, right-aligned where Print_Right_ puts it (tech.cpp:703).
    cost_of = words.get("cost")
    cost = cost_of(entry) if cost_of else None
    if cost:
        size = layout.font_size(13)
        surf = style.render_text(cost, size, col("cost", (188, 204, 236)))
        cx, cy = native.window_point(entry.cost_anchor(), layout)
        surface.blit(surf, (cx - surf.get_width(), cy))

    # The field name, on row 0's own first line (tech.cpp:700).
    name_x, name_y, name_w = entry.field_name_anchor()
    _blit_text(surface, style,
               names.field_name(entry.field) if names else None,
               native.window_point((name_x, name_y), layout),
               native.window_width(name_x, name_y, name_w, layout),
               layout.font_size(17), col("field", (226, 234, 250)))

    for row, app in enumerate(entry.apps):
        if hover == (entry.index, row):
            # The original marks the hovered row with a cycling box and
            # a little arrow (`Draw_Little_Arrow_`, tech.cpp:740). HD
            # fills the row instead — INVENTION: MOO2 cycles a palette
            # index, which an RGB surface does not have.
            rect = pygame.Rect(*native.window_rect(entry.row_rect(row),
                                                   layout))
            shade = pygame.Surface(rect.size, pygame.SRCALPHA)
            shade.fill(col("hover", (70, 104, 168, 90)))
            surface.blit(shade, rect.topleft)
        label_x, label_y, label_w = entry.app_label_anchor(row)
        _blit_text(surface, style,
                   words.get("placeholder") if entry.placeholder
                   else (names.application_name(app) if names else None),
                   native.window_point((label_x, label_y), layout),
                   native.window_width(label_x, label_y, label_w, layout),
                   layout.font_size(14), col("row", (198, 212, 238)))
