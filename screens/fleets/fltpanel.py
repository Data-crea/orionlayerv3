"""The scanned ship's lines, and how they fit the box they go in.

**SPLIT OUT OF `fltdraw` (decision 6)**, which went over 300 lines the
moment the panel stopped being six lines of blitting. It is its own
thing: everything else in `fltdraw` draws a shape at a rect, and this
decides a FONT SIZE and a LINE BREAK from data, which is a different
kind of question and carries its own rules.

**NOTHING HERE IS A LAYOUT NUMBER.** The area is a box in
`boxes.json`, the size is that box's `font_size` times its
`font_scale`, and the wording of the overflow marker is
`layout.json`'s (decisions 14, 15, 37). The three constants below are
FALLBACKS for a file that has lost the box, not a layout — decision 22
— and with the box present none of them is read.

What the panel shows is `fltrows.panel_lines`, which transcribes
`FLT2::Print_Scanned_Ship_Data_` (flt2.cpp:524-747) minus what that
module's docstring lists as omitted.
"""
import logging

from core import textfit

from . import fltrows
from .fltdraw import _rect, col, content_rect

log = logging.getLogger("fleets")


#: The text area's box. NOT `ship_panel`: that one is a cutout, its
#: rect is the artwork's hole and the F5 editor locks it. This is the
#: free box inside it, the same split `picks_popup` / `picks_popup_text`
#: uses on Custom Race, so the words can be moved, resized and scaled
#: without moving the hole they sit in.
PANEL_TEXT_BOX = "ship_panel_text"

#: What the panel falls back to when `boxes.json` has no
#: `ship_panel_text` at all — a bad edit must not make a scanned ship
#: unreadable (decision 22). NOT a layout number: with the box present,
#: which is every shipped resolution, neither of these is read.
PANEL_FALLBACK_FONT = 14
PANEL_FALLBACK_INSET = 5        # reference px inside `ship_panel`

#: How small the panel may shrink before it starts dropping lines,
#: in reference px. Below this the words stop being words.
PANEL_MIN_FONT = 8

#: Only when `layout.json` is missing or has lost the key: the marker
#: must not become an empty string, because an empty marker is exactly
#: the silent drop it exists to prevent. The WORDING lives in
#: `layout.json` under `words.panel_more` (decision 15).
PANEL_MORE_FALLBACK = "+{n} more"

#: The last overflow state written to the log, so the render loop says
#: it once instead of sixty times a second. Module level because
#: `draw_panel` is a function and the screen should not have to carry
#: a field for a diagnostic.
_LAST_OVERFLOW = None


def _log_overflow(rect, asked, size, shown, dropped):
    """The developer's half of the marker.

    **THE PLAYER'S MARKER SAYS "+n more" AND NOTHING ELSE** (Data,
    20 September 2026): it is on the player's screen and the editor is
    not the player's business. Which box, how big it is, how many lines
    it held and at what size — the things somebody fixing the layout
    needs — belong here, where only a developer looks.
    """
    global _LAST_OVERFLOW
    state = (dropped, size, shown, rect.width, rect.height)
    if state == _LAST_OVERFLOW:
        return
    _LAST_OVERFLOW = state
    if not dropped:
        return
    log.info("ship panel: %d line(s) not shown — box '%s' is %dx%d window "
             "px and holds %d line(s) at %d px, having asked for %d. "
             "Move, resize or rescale it in F5, or lower its font_size.",
             dropped, PANEL_TEXT_BOX, rect.width, rect.height, shown,
             size, asked)


def panel_text_rect(screen):
    """The rect the ship panel's words go in, or None.

    `ship_panel_text` when `boxes.json` has it; otherwise the hole's
    content rect inset by `PANEL_FALLBACK_INSET`, which is what the
    panel did before the box existed.
    """
    r = _rect(screen, PANEL_TEXT_BOX)
    if r is not None:
        return r
    r = content_rect(screen, "ship_panel")
    if r is None:
        return None
    pad = max(1, int(round(PANEL_FALLBACK_INSET * screen.layout.scale)))
    return r.inflate(-2 * pad, -2 * pad)


def panel_font_px(screen):
    """The panel's font size in WINDOW px, scaled exactly once.

    `font_size` is the box's own reference size and `font_scale` is
    what the F5 wheel writes; they multiply, and `Layout.font_size`
    applies the window scale to the product — ONCE. Taking the window
    factor before it as well is the squaring the fundament's "Scaling
    twice looks correct at the resolution you tested" is about, and
    `ScreenBase.box_font_scale_stored` says the same thing from the
    other end: 1.0 at 1080p, 1.78 at 1440p and 4.0 at 2160p against an
    intended 2.0.
    """
    style = screen.box_style(PANEL_TEXT_BOX)
    ref = float(style.get("font_size", PANEL_FALLBACK_FONT))
    ref *= float(style.get("font_scale", 1.0))
    return screen.layout.font_size(max(1, int(round(ref))))


def panel_block(screen, lines, words=None, rect=None, px=None):
    """`(surfaces, size, dropped)` for the scanned ship's lines.

    **WRAPPED AND SHRUNK, MEASURED BY RENDERING** (decision 30,
    `core/textfit`): each line is a separate fact and is wrapped on its
    own, and the size that wins is the largest at which all of them fit
    the box TOGETHER. The colony summary's scan panel answers the same
    question through the same function.

    **AND IT SAYS WHAT IT DROPPED.** Below `PANEL_MIN_FONT` the words
    stop being words, so the block is cut to what fits and the last
    line becomes `words.panel_more` with the count. The original clips
    silently at its drawing window (`Set_Window_(15, 282, 320, 465)`,
    flt1.cpp:402) and has no marker; this is the deviation
    `layout.json` marks as `deviation_panel_overflow`, and the reason
    for it is that a ship's weapon silently missing from the list is
    the one outcome this screen may not have.
    """
    rect = panel_text_rect(screen) if rect is None else rect
    px = panel_font_px(screen) if px is None else px
    floor = max(1, screen.layout.font_size(PANEL_MIN_FONT))
    sizes = [n for n in range(px, floor - 1, -1)] or [px]
    texts = [f"{label}: {value}" if label else str(value)
             for label, value in lines]
    colour = col("label")
    rendered, size = textfit.squeeze_block(
        screen.style, texts, rect.width, rect.height, sizes, colour)
    if textfit.block_height(rendered) <= rect.height:
        return rendered, size, 0

    # It still does not fit at the floor. Keep whole lines, and spend
    # the last one saying how many are not there.
    more = (words or {}).get("panel_more") or PANEL_MORE_FALLBACK
    keep = []
    height = 0
    for surf in rendered:
        if height + surf.get_height() > rect.height:
            break
        keep.append(surf)
        height += surf.get_height()
    dropped = len(rendered) - len(keep)
    if keep:
        keep.pop()
        dropped += 1
    marker = screen.style.render_text(
        more.replace("{n}", str(dropped)), size, col("label_dim"))
    keep.append(marker)
    return keep, size, dropped


#: **THE ORIGINAL'S TAB STOPS**, work order 154. Every value below is
#: a native x from `Print_Scanned_Ship_Data_` (flt2.cpp:524-747),
#: taken relative to the drawing window's own left edge and divided by
#: its width — `Set_Window_(15, 282, 320, 465)` (flt1.cpp:402), so the
#: origin is 15 and the width 305. Fractions and not pixels, because
#: the HD hole is not 305 px wide and never will be.
#:
#: **MEASURED TWICE.** Each one is a constant in the source AND was
#: read off a native screenshot of this very panel
#: (`evidence/work_order_152/panel/001_20_panel_native.png`, the ship
#: "Rafale"): the name starts at x 18, the weapon entries at 23,
#: "Beam DCV:" and "Specials:" at 173, the special entries at 188, the
#: OCV value ends at 133 and the DCV value starts at 288. A smoke
#: check re-derives the fractions from those same native pixels.
_WIN_X, _WIN_W = 15, 305.0

#: head lines, and the "Weapons:" heading — `Print_(0x12, …)`
COL_LABEL = (0x12 - _WIN_X) / _WIN_W
#: weapon entries, indented under their heading — `Print_(0x17, …)`
COL_ENTRY = (0x17 - _WIN_X) / _WIN_W
#: "Beam DCV:" and the "Specials:" heading — `Print_(0xAD, …)`
COL_RIGHT_LABEL = (0xAD - _WIN_X) / _WIN_W
#: special entries, indented under their heading — `Print_(0xBC, …)`
COL_RIGHT_ENTRY = (0xBC - _WIN_X) / _WIN_W

#: THE TWO VALUE STOPS, TRANSCRIBED AND NOT YET DRAWN. The OCV value
#: is RIGHT-aligned so that it ENDS here (`Print_Right_(0x85, …)`);
#: the DCV value starts at `w + 0xAD` where `w` is the label's width
#: floored at 0x73 (flt2.cpp:615-622) — the label is far narrower than
#: 0x73 in every language this tree has seen, so the floor wins and
#: the stop is fixed at 0x73 + 0xAD = 288. Both are here because the
#: order asked for the positions transcribed; neither is used until
#: the numbers themselves are reachable, and a smoke check holds them
#: so they cannot rot in the meantime.
COL_OCV_VALUE_END = (0x85 - _WIN_X) / _WIN_W
COL_DCV_VALUE = (0x73 + 0xAD - _WIN_X) / _WIN_W

#: Where the specials column starts. The name is kept because it is
#: what the rest of the tree calls this stop; it IS `COL_RIGHT_ENTRY`
#: and is not a second copy of the number.
SPECIALS_SPLIT = COL_RIGHT_ENTRY


def _stops(rect):
    """The five drawing stops in window px, for a text rect."""
    return {name: rect.x + int(rect.width * frac) for name, frac in (
        ("label", COL_LABEL), ("entry", COL_ENTRY),
        ("right_label", COL_RIGHT_LABEL), ("right_entry", COL_RIGHT_ENTRY),
        ("dcv", COL_DCV_VALUE))}


def _head_row(screen, slot, size, colour, stops):
    """One head slot as `[(surface, x)]` — empty for a blank line."""
    if not slot:
        return []
    return [(screen.style.render_text(slot, size, colour), stops["label"])]


def draw_columns(surface, screen, panel, rect):
    """The head block, the two headings, then the two columns.

    **THE LINE GRID IS THE ORIGINAL'S, LESS ONE LINE** (work order 154,
    and Data's decision of 20 September 2026). The head is four slots and an empty one is a BLANK
    LINE, because the original advances its cursor by a line per slot
    whether or not it printed in it (flt2.cpp:596-645) — that is the
    empty line above Weapons/Specials, and it is there only because a
    parked ship has no destination. The headings sit at the left and
    right LABEL stops; the entries are INDENTED under them, to their
    own stops.

    The line HD does not have is the original's fifth head slot, Beam
    OCV / Beam DCV: neither number is computable and Data's answer to
    drawing the labels with nothing after them was no, so the line is
    not there at all (`omission_panel_beam_bonuses`). Its two value
    stops stay transcribed below against the day it comes back.

    ONE SIZE FOR ALL OF IT, and one line height. The original uses
    three font styles — 3 for the name, 2 for the head, 1 for the
    entries (`Set_Font_Style_`, :578, :580, :688) — and adds 2 px of
    leading in the head against 1 in the columns. HD has one font at
    one size, so it draws one pitch throughout; marked in
    `layout.json` as `deviation_panel_one_font`. The size that wins is
    the largest at which everything fits together, measured by
    rendering (decision 30).
    """
    px = panel_font_px(screen)
    floor = max(1, screen.layout.font_size(PANEL_MIN_FONT))
    colour, dim = col("label"), col("label_dim")
    stops = _stops(rect)
    # The left column runs from its own stop to where the right
    # column's HEADING starts, so a long weapon cannot run into
    # "Specials:"; the right one runs to the edge.
    widths = (max(8, stops["right_label"] - stops["entry"]),
              max(8, rect.x + rect.width - stops["right_entry"]))
    for size in range(px, floor - 1, -1):
        line_h = screen.style.render_text("Wg", size, colour).get_height()
        head = [_head_row(screen, slot, size, colour, stops)
                for slot in panel.head]
        headings = []
        if panel.weapons_heading:
            headings.append((screen.style.render_text(
                panel.weapons_heading, size, dim), stops["label"]))
        if panel.specials_heading:
            headings.append((screen.style.render_text(
                panel.specials_heading, size, dim), stops["right_label"]))
        cols = []
        for i, items in enumerate((panel.weapons, panel.specials)):
            block = []
            for text in items:
                block.extend(textfit.wrap_rendered(
                    screen.style, text, size, widths[i], colour))
            cols.append(block)
        rows = len(head) + bool(headings) + max(len(c) for c in cols)
        if rows * line_h > rect.height:
            continue
        if any(s.get_width() + x - rect.x > rect.width
               for row in head for s, x in row):
            continue
        if any(s.get_width() > widths[i]
               for i, c in enumerate(cols) for s in c):
            continue
        y = rect.y
        for row in head:
            for surf, x in row:
                surface.blit(surf, (x, y))
            y += line_h
        if headings:
            for surf, x in headings:
                surface.blit(surf, (x, y))
            y += line_h
        for i, block in enumerate(cols):
            cy = y
            cx = stops["entry" if i == 0 else "right_entry"]
            for surf in block:
                surface.blit(surf, (cx, cy))
                cy += line_h
        return True
    return False


def paragraph_text(helptext, para):
    """The lines a `fltrows.Paragraph` shows, as whole paragraphs.

    Separate from the drawing because WHICH WORDS APPEAR is the part a
    check can hold cheaply and exactly, and the part that has two
    states: the player's own HELP.LBX record, and the wording for an
    install that has never extracted it.

    **ONLY THE BODY, when there is one.** `Print_Scanned_Ship_Data_`
    passes `lbx_data->body` and never the record's title
    (flt2.cpp:572). The title is used only if a record somehow carries
    one and no body, which the loader permits and the original would
    print as an empty paragraph.

    **AND THE DATA PANEL IS NOT THE FALLBACK.** Falling back to it
    would restore exactly the "HD shows more than the original" this
    mode exists to remove, and it would do so on the machines least
    able to notice — the ones that have not run the extractor. What an
    absent file gets is `HelpText.missing_entry`, the same wording the
    right-click popup shows, which lives once in
    `assets/shared/help/labels.json` (decision 15). Marked in
    `layout.json` as `fallback_panel_help_missing`.
    """
    text = helptext.entry(para.help_id) if helptext is not None else None
    if text is not None:
        return [text[1]] if text[1] else [text[0]]
    if helptext is None:
        return []
    title, body = helptext.missing_entry(para.help_id)
    return [line for line in (title, body) if line]


def draw_paragraph(surface, screen, para, words=None):
    """A colony ship's, transport's or outpost's paragraph.

    **THE SECOND PANEL MODE, AND IT IS A TRANSCRIPTION.**
    `Print_Scanned_Ship_Data_` returns early for those three types and
    prints one HELP.LBX record instead of the data panel
    (flt2.cpp:548-575) — `fltrows.PARAGRAPH_HELP` carries which record
    and why. The original's call is

        ERIC::Print_Paragraph_Centered_Vertically_(0x12, 0x11A, 0x12B,
                                                  0xB7, body, 0)

    and that primitive (eric.cpp:171-174) wraps at `width` and prints at
    `y + box_height/2 - paragraph_height/2`: the block is **centred
    vertically in the box and not in the text**, which is why a short
    paragraph and a long one share a centre line rather than a top edge.

    **THE WRAP WIDTH IS HD'S HOLE, AND THAT IS A SCALED TRANSCRIPTION.**
    The original's box is `(18, 282, 299, 183)` native — the width is
    `0x12B`, **299 and not the 305 this project's own open list said**;
    corrected here against eric.cpp's parameter order, which names the
    third argument `width`. HD's hole is a different shape at every
    resolution, so wrapping at 299 scaled would leave the text in a
    column narrower than the box it sits in, which is neither the
    original's picture nor a sensible one. Wrapping at the hole is the
    same decision `panel_block` already takes for the data panel.

    **ONLY THE BODY.** The original passes `lbx_data->body` and never
    the record's title.
    """
    rect = panel_text_rect(screen)
    if rect is None:
        return
    paragraphs = paragraph_text(screen.helptext, para)
    asked = panel_font_px(screen)
    floor = max(1, screen.layout.font_size(PANEL_MIN_FONT))
    rendered, size = textfit.squeeze_block(
        screen.style, paragraphs, rect.width, rect.height,
        [n for n in range(asked, floor - 1, -1)] or [asked],
        col("panel_paragraph"))
    height = textfit.block_height(rendered)
    dropped = 0
    if height > rect.height:
        # THE PANEL'S OWN OVERFLOW, not a second one. `panel_block`
        # owns the "+n more" rule and the reason for it; this reuses
        # the marker rather than inventing a way to clip.
        rendered, size, dropped = panel_block(
            screen, [("", p) for p in paragraphs], words, rect, asked)
        height = textfit.block_height(rendered)
    _log_overflow(rect, asked, size, len(rendered) - bool(dropped), dropped)

    # Centred vertically in the BOX, as the original centres it.
    y = rect.y + max(0, (rect.height - height) // 2)
    for surf in rendered:
        surface.blit(surf, (rect.x, y))
        y += surf.get_height()


def draw_panel(surface, screen, lines, words=None):
    """The scanned ship's lines, top down inside `ship_panel_text`.

    `words` is `layout.json`'s own dict, handed in like `draw_labels`
    takes it: the renderer draws what it is given and does not know
    the wording (decision 15).

    **TWO MODES, AND THE SHIP CHOOSES.** A `fltrows.Paragraph` is a
    colony ship, transport or outpost, which the original answers with
    one HELP.LBX paragraph and none of the data lines; everything else
    is the data panel below. The branch is on the TYPE the row builder
    returned, so this renderer never asks the ship anything.
    """
    if isinstance(lines, fltrows.Paragraph):
        draw_paragraph(surface, screen, lines, words)
        return
    rect = panel_text_rect(screen)
    if rect is None or not lines:
        return
    # TWO COLUMNS WHEN THE CONTENT KNOWS IT HAS TWO. A `Panel` carries
    # the original's own split; a bare list is the older shape and is
    # still drawn as one column, which is also what a Panel falls back
    # to when its two columns cannot be made to fit.
    if hasattr(lines, "flat"):
        if draw_columns(surface, screen, lines, rect):
            return
        lines = [("", t) for t in lines.flat()]
    asked = panel_font_px(screen)
    rendered, size, dropped = panel_block(screen, lines, words, rect, asked)
    _log_overflow(rect, asked, size, len(rendered) - bool(dropped), dropped)
    y = rect.y
    for surf in rendered:
        surface.blit(surf, (rect.x, y))
        y += surf.get_height()
