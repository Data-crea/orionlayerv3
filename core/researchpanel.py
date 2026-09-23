"""Drawing the research panel — the eight categories, their rows, the hover.

One implementation for both modes (work order 165 part B). Everything
is positioned through the `Geometry` the caller hands in, so the panel
that is 81 px further left is the same code with a different origin —
which is what `TECH::_Tech_Select_(changing_tech)` itself is.

DRAWING AND HIT-TESTING CANNOT DISAGREE: the screen resolves a click
back to a native pixel and tests it against `Entry.row_rect`, which is
the rectangle this module draws in (decision 5).

That guarantees agreement and NOT correctness — the stacked colony
figures agreed with themselves through 165 of 210 missed clicks
(decision 5's own amendment). So the smoke check for these screens
asserts against the DRAWN PIXELS, as work order 128 D did for the
Planets list: it renders, then picks the visible centre of each row and
requires the hit test to name that row.

THE ORIGINAL SQUEEZES, HD SHRINKS. `BILL::Squeeze_Print_`
(tech.cpp:700, :735) compresses the glyphs of a name to fit its width
rather than clipping it. An HD font cannot be squeezed, so the size
comes down until the string fits — the same intent, and the nearest
thing available. DEVIATION, in each screen's marked list.
"""
import pygame

from core import palette
from core import researchlist
from core import researchnative as geom_mod

#: The smallest the shrink may go before it gives up and clips.
MIN_FONT = 8

#: THE SECOND COLOUR, and which mode can reach it.
#:
#: The original has `TECH::_tech_color[0]` and `[2]`, and uses `[2]`
#: for the field the player is ALREADY researching and for its chosen
#: application (tech.cpp:686-696). In SELECT mode that is unreachable:
#: `Tech_Select_` zeroes `current_research_field` before the list is
#: built (tech.cpp:104-105), so nothing on the panel is the current
#: one and every row is drawn in the first colour. In CHANGE mode it
#: is the point — the field you are on is offered, and it is marked.
#:
#: Written down rather than discovered later: while only select mode
#: existed this module drew one colour and said the second was "not
#: missing, it has nothing to mark". Change mode is what gives it
#: something, and `current=(0, 0)` is how select mode keeps saying so.
#:
#: The palette section stays `research_select` for both, because there
#: is one panel and the original has one colour table for it; a second
#: section would be a second set of numbers to keep equal.
CURRENT = "field_current", "row_current"


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


def marks_every_row(field, creative):
    """Whether EVERY application of the current field is marked.

    `Display_Entry_Text_` (tech.cpp:661-666): a Creative player gets
    every application of the field being researched, and so does any
    player researching one of the six `_starting_tech_field_ids`
    (techdata.cpp:548 — the same six the function tests inline). In
    both cases the original marks all of the entry's rows, not one.

    TRAIT_UNCREATIVE is NOT tested here, and its absence is the
    transcription: it changes what the player GETS, not what is
    marked, so an Uncreative player's entry is coloured like any other
    player's.
    """
    return bool(creative) or field in researchlist.ALL_APPLICATIONS_FIELDS


def marks_row(names, app, current_app):
    """Whether the original marks THIS row when only one is marked.

    **THE ORIGINAL COMPARES NAMES, NOT IDS** —
    `strcasecmp(item->app_names[i],
    _technology_applications[cur_app].name)`, tech.cpp:697-700 — so two
    applications that share a name are both marked. Transcribed; where
    the names are distinct it is the id comparison this was, and where
    a name is missing it falls back to the id rather than marking
    nothing.
    """
    if not current_app or not app:
        return False
    if names is None:
        return app == current_app
    mine, theirs = (names.application_name(app),
                    names.application_name(current_app))
    if not mine or not theirs:
        return app == current_app
    return mine.strip().casefold() == theirs.strip().casefold()


def draw_exit(surface, layout, style, native_rect, label, pressed=False):
    """The exit button, AT THE RECTANGLE THE WIRE REPORTS.

    `Add_Button_Field_(s + 0xBD, 0x1C4, "", TECHSEL 27, "\x1B", '(')`
    (tech.cpp:208-210; the art loaded at :176) takes its rectangle from
    that art (fields.cpp:366-367), so the SOURCE has the origin and
    nothing else — `doc/tech_change_reading.md` §2 had the end as NOT
    SETTLED until the live list was read. The caller therefore hands in
    the rectangle it found in the list read NOW, and where there is no
    such field there is nothing to draw and nothing to click.

    DEVIATION, marked: the word is painted into the button art and
    `Add_Button_Field_` is passed an EMPTY label string, so there is no
    string tech.cpp prints for HD to transcribe. It is printed as text
    until the artwork is extracted — the same deviation the category
    labels carry, and marked the same way.
    """
    box = pygame.Rect(*geom_mod.window_rect(native_rect, layout))
    surface.fill(col("exit_fill", (20, 26, 42)), box)
    pygame.draw.rect(surface, col("exit_border", (108, 140, 200)), box,
                     max(1, box.height // 12))
    if not label:
        return box
    size = _fit(style, label, int(box.width * 0.8),
                layout.font_size(13))
    text = style.render_text(label, size, col("exit_label",
                                              (198, 212, 238)))
    surface.blit(text, (box.centerx - text.get_width() // 2,
                        box.centery - text.get_height() // 2))
    return box


def draw(surface, layout, style, entries, hover, words, names, wording,
         current=(0, 0), creative=False):
    """Draw the eight entries. `hover` is (entry index, row) or None.

    `current` is `(current_research_field, current_research_application)`
    off the wire — see `CURRENT` above for what it colours and why
    select mode passes zeros. `creative` is the player's
    TRAIT_CREATIVE; see `marks_every_row`.
    """
    for entry in entries:
        if entry.offered:
            _draw_entry(surface, layout, style, entry, hover, words,
                        names, wording, current, creative)


def _draw_entry(surface, layout, style, entry, hover, words, names, wording,
                current, creative=False):
    is_current = entry.field == current[0] and entry.field != 0
    every_row = is_current and marks_every_row(entry.field, creative)
    # The category's own name. The original paints it into the TECHSEL
    # art; HD prints it, and the WORD is still the game's own —
    # billtext 64 + group (tech.cpp:802-816). Marked in screen.py.
    label = wording.group_name(entry.group) if wording else None
    if label:
        _blit_text(surface, style, label,
                   geom_mod.window_point((entry.x, entry.y + 2), layout),
                   geom_mod.window_width(entry.x, entry.y + 2, 150, layout),
                   layout.font_size(13), col("category", (128, 148, 186)))

    # The cost, right-aligned where Print_Right_ puts it (tech.cpp:703).
    # AND IN THE CURRENT FIELD'S COLOUR WHEN IT IS THE CURRENT FIELD.
    # `Display_Entry_Text_` picks one `color` and prints the field name
    # (style 4) AND the cost (style 3) in it (tech.cpp:648-657), so the
    # cost follows the name rather than having a colour of its own.
    cost_of = words.get("cost")
    cost = cost_of(entry) if cost_of else None
    if cost:
        size = layout.font_size(13)
        surf = style.render_text(
            cost, size, col("field_current", (250, 226, 150)) if is_current
            else col("cost", (188, 204, 236)))
        cx, cy = geom_mod.window_point(entry.cost_anchor(), layout)
        surface.blit(surf, (cx - surf.get_width(), cy))

    # The field name, on row 0's own first line (tech.cpp:700).
    name_x, name_y, name_w = entry.field_name_anchor()
    _blit_text(surface, style,
               names.field_name(entry.field) if names else None,
               geom_mod.window_point((name_x, name_y), layout),
               geom_mod.window_width(name_x, name_y, name_w, layout),
               layout.font_size(17),
               col("field_current", (250, 226, 150)) if is_current
               else col("field", (226, 234, 250)))

    for row, app in enumerate(entry.apps):
        if hover == (entry.index, row):
            # The original marks the hovered row with a cycling box and
            # a little arrow (`Draw_Little_Arrow_`, tech.cpp:740). HD
            # fills the row instead — INVENTION: MOO2 cycles a palette
            # index, which an RGB surface does not have.
            rect = pygame.Rect(*geom_mod.window_rect(entry.row_rect(row),
                                                   layout))
            shade = pygame.Surface(rect.size, pygame.SRCALPHA)
            shade.fill(col("hover", (70, 104, 168, 90)))
            surface.blit(shade, rect.topleft)
        label_x, label_y, label_w = entry.app_label_anchor(row)
        _blit_text(surface, style,
                   words.get("placeholder") if entry.placeholder
                   else (names.application_name(app) if names else None),
                   geom_mod.window_point((label_x, label_y), layout),
                   geom_mod.window_width(label_x, label_y, label_w, layout),
                   layout.font_size(14),
                   col("row_current", (250, 226, 150))
                   if is_current and (every_row
                                      or marks_row(names, app, current[1]))
                   else col("row", (198, 212, 238)))
