"""The building column: what a colony is producing, and its Buy button.

Its own module because the text-fitting behaviour is a transcription
with its own source, and because `colonylist.py` is already at the
~300 guideline (decision 6).

**The column is 190 reference px and that is a HARD width.**
Transcribed from the original, which prints the producing text with
`BILL::Squeeze_Print_Formatted_Paragraph_(0x200, y, 0x55, 0x16, ...)`
(colsum.cpp:621) — x 512, width 85, max height 22, of a 640 px
screen. 85/640 is 13.3 %, which is 190 of 1408.

**Why 190 is a reservation and not a squeeze target.**
`BILL::_Squeeze_Print_Paragraph_` (bill.cpp:147) passes `width`
straight to `get_height(width, text)` and then loops on
`max_height >= height`: the text is WRAPPED into the width, and what
must be made to fit is the HEIGHT. Width never moves. There is no
truncation branch anywhere in that function — when it runs out of
things to shrink it prints the whole paragraph regardless.

That is worth stating because measuring it the other way gives a
number nearly twice as large and looks just as authoritative: the
widest producing string, on ONE line, at FULL size, is 311 px at
small_font. The original never imposes any of those three
constraints. A requirement the original does not have is not a
measurement of the original.

**TRANSCRIBED: the behaviour, not the mechanism.** The original
squeezes in three steps — narrow the space glyph, then the leading,
then step down one font style. The first is a bitmap-font trick
(`font_style_widths[32]--`) with no Aldrich equivalent, and the third
steps between discrete bitmap faces. What carries over is the shape
of it: WRAP into the width, then REDUCE SIZE until it fits the
height, and NEVER TRUNCATE. `squeeze_lines` does exactly that.

**The width condition is a TRANSCRIPTION of the guarantee and a
DEVIATION in how it is kept.** `_Squeeze_Print_Paragraph_` loops on
height alone, and `fmtpara.cpp` offers
`Get_Formatted_Paragraph_Max_Width_` right beside the height function
without ever calling it — which raises the question of whether the
original lets an over-wide token overflow. It does not.
`_Print_Formatted_Paragraph_` places a character when
`char_x_end <= right_limit_x || line_started != 0` (fmtpara.cpp:567).
`line_started` is 1 at the start of a line and 0 after the first
character (:540, :572), so the first character goes down
unconditionally and every later one must fit. When one does not and
it is not a space, `Return_To_Last_Break_()` is tried — and break
positions are only recorded at spaces, tabs and soft hyphens (:723,
:731) — but `_para_p->str--` runs whether that succeeded or not, and
the line ends (:583-587). **A token with no break in it is therefore
broken mid-token**, and the paragraph never exceeds the width. Height
alone is sufficient BECAUSE the width can never be exceeded.

So the guarantee — no ink past the reserved width, and nothing
truncated — is transcribed. The means is not: the original character-
wraps the token, this reduces the size and keeps it whole. That is
visible, so it is marked. The reason is that the over-wide token here
is a ship design name, user-typed data whose exact form is the point;
at 640x480 in a five-pixel face a hyphen-less mid-word break reads as
wrapping, and at HD it reads as corruption of a name somebody chose.

**The Buy control is transcribed in POSITION and deviates TWICE in
form.** The original adds one per row at native x=599
(`colsum.cpp:302`, `_list_buy_fields[10]`, `buy_btn_y_coords`), right
of the producing text, as a `Locked_Button_Field_` or a hidden field
depending on `Colony_Can_Buy_Product_0_`. That much is transcribed.
Two things are not:

  1. The LABEL. `E_Strings_(12)` is empty, so "Buy" is a word this
     project chose. It lives in `layout.json` per decision 15.
  2. Drawing TEXT AT ALL. The original's control is a sprite —
     `_anims[i + 11]` supplies the artwork and the empty label is why
     it can be. A text button is a different object, not a
     translation of that one, and it is drawn this way because the
     sprite is in the player's LBX and is not shipped.

Both are deviations, and naming only the first would leave the larger
one unmarked.
"""
import pygame

from core import palette

BUILD_NAME = palette.col("colony_summary", "build_name", (196, 208, 232))
BUILD_TURNS = palette.col("colony_summary", "build_turns", (132, 148, 180))
BUY_BG = palette.col("colony_summary", "buy_background", (34, 52, 88))
BUY_EDGE = palette.col("colony_summary", "buy_edge", (72, 104, 160))
BUY_TEXT = palette.col("colony_summary", "buy_text", (198, 214, 240))


def squeeze_lines(style, text, width, max_h, sizes, color):
    """Wrap into `width`, shrink until it fits `max_h`, never truncate.

    `sizes` is tried largest first. The last one is used even when it
    still does not fit, because the original does the same: its loop
    ends when there is nothing left to shrink and it prints the whole
    paragraph anyway. Losing a character is not one of the outcomes.

    Measured by rendering, never by `font.size()` — `render_text` can
    mix two fonts inside one string wherever a glyph is substituted,
    so one font's metrics are not the width that reaches the screen
    (decision 30). This is the SECOND word-wrap in the tree, after
    `helppopup._wrap`; the third is the one that should be extracted
    to a shared helper rather than pasted again.
    """
    rgb = tuple(color[:3])
    size = sizes[-1]
    for size in sizes:
        lines = wrap_text(style, text, size, width)
        rendered = [style.render_text(l, size, rgb) for l in lines]
        # BOTH dimensions. Height alone is not enough: a single word
        # wider than the column cannot be broken, so it fits the
        # height on one line and never triggers a shrink — a 15-glyph
        # ship design measured 225 px in a 190 px column and sat
        # there. The width is the hard side, so it has to be part of
        # what the reduction is trying to satisfy.
        if (sum(s.get_height() for s in rendered) <= max_h
                and max(s.get_width() for s in rendered) <= width):
            return rendered, size
    # Nothing left to shrink. Print it whole regardless, which is
    # what the original does when its own loop runs out of steps —
    # losing a character is not one of the outcomes.
    return [style.render_text(l, size, rgb)
            for l in wrap_text(style, text, size, width)], size


def wrap_text(style, text, size, width):
    """One source string into lines that each fit `width` if they can.

    Returns TEXT, not surfaces, so a test can assert that nothing was
    dropped. A word longer than `width` is left whole on its own line
    rather than cut — `squeeze_lines` answers that by shrinking.
    """
    if style.render_text(text, size, (255, 255, 255)).get_width() <= width:
        return [text]
    lines, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if current and style.render_text(
                trial, size, (255, 255, 255)).get_width() > width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def draw(surface, row, x, y, width, row_h, cfg, style, layout):
    """The column for one row: production name, then turns and Buy.

    Two lines, and the ORIGINAL BUDGETS TWO IN THE SAME BOX: it
    passes max height 0x16 = 22 (colsum.cpp:621) into a row whose
    pitch is 31 — `buy_btn_y_coords` steps 35, 65, 96, 128, ... — so
    the box is two thirds of the row and holds more than one line of
    its own font. The two-line column is the same PLACE as the
    original's, not merely the same technique applied elsewhere. Our
    vertical reserve is the one that freed `tail_width`,
    `row_height` 62 against `bar_height` 34.

    Nothing here is squeezed horizontally into a narrower column; the
    width is the fixed side.
    """
    name = row.get("producing") or ""
    if not name:
        return
    small = layout.font_size(cfg.get("small_font", 15))
    floor = layout.font_size(cfg.get("build_font_min", 10))
    sizes = list(range(small, floor - 1, -1)) or [small]

    turns = row.get("producing_turns")
    turn_text = (cfg.get("turns", "- {turns}t").replace(
        "{turns}", str(turns)) if turns else "")
    buy_surf = _buy_button(cfg, style, small) if row.get("can_buy") else None

    # Line two's height is what line one may not take.
    second_h = max(
        buy_surf.get_height() if buy_surf else 0,
        style.render_text(turn_text or "0", small, BUILD_TURNS).get_height())
    lines, _size = squeeze_lines(style, name, width, row_h - second_h,
                                 sizes, BUILD_NAME)

    top = y + (row_h - sum(s.get_height() for s in lines) - second_h) // 2
    for surf in lines:
        surface.blit(surf, (x, top))
        top += surf.get_height()
    if turn_text:
        surface.blit(style.render_text(turn_text, small, BUILD_TURNS),
                     (x, top))
    if buy_surf:
        surface.blit(buy_surf, (x + width - buy_surf.get_width(), top))


def _buy_button(cfg, style, px):
    """A small labelled button. The original's is a sprite with an
    empty label string (E_Strings_(12)), so the word is ours."""
    label = style.render_text(cfg.get("buy_label", "Buy"), px, BUY_TEXT)
    pad = max(2, px // 3)
    surf = pygame.Surface((label.get_width() + 2 * pad,
                           label.get_height() + pad), pygame.SRCALPHA)
    rect = surf.get_rect()
    pygame.draw.rect(surf, BUY_BG[:3], rect, border_radius=max(2, px // 5))
    pygame.draw.rect(surf, BUY_EDGE[:3], rect, 1,
                     border_radius=max(2, px // 5))
    surf.blit(label, (pad, pad // 2))
    return surf
