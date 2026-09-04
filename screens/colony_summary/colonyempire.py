"""The empire sidebar — six s_player scalars, the original's own.

TRANSCRIBED from `COLSUM::Draw_Empire_Info_` (colsum.cpp:418): six
lines printed at native (520, 354), each one an `s_player` field, in
the original's order, with its explicit plus and its red-if-negative.
All six offsets were read against the original's own box on
3 September 2026 and all six agreed — see `core/structs/player.py`.

**Every file:line in this module and in `layout.json`'s `empire`
block was read in orion2re 1.60.** A 1.31 archive numbers them
differently, and three were carried in from one before being
corrected.

**Split out of `screen.py` on 3 September 2026**, which had reached
647 lines against a ~300 guideline (decision 6). This was the last
cohesive block left in that file after the selection went to
`colonyselect` and the scan box to `colonyoutput`: one box, one
config block, six values, and one DEVIATION that is live in every
frame.

**The two smoke checks that hold decision 44's clamp moved with it,
and that is the whole reason this was its own commit.** They call
`native_column_width` and `value_column` directly and they grep a
source file for the DEVIATION marking. Left pointing at `screen.py`
they would have gone on passing against a file that no longer
contains the thing they assert — a check whose subject has moved out
from under it is worse than no check, because it still reports green.

Module functions rather than methods: nothing here needs a screen,
only a rect, a config block and a parsed `s_player`. That is also
what lets the clamp be measured without standing a screen up.
"""
import pygame

from core import palette
from core.config import REF_W

LABEL_COLOR = palette.col("colony_summary", "label", (140, 155, 190))
VALUE_COLOR = palette.col("colony_summary", "value", (220, 228, 245))
WARN_COLOR = palette.col("colony_summary", "warn", (235, 90, 80))
PANEL_BG = palette.col("colony_summary", "panel_background", (8, 11, 20))

#: The native screen the original draws under this one. ONE home for
#: it — `screen.py` imports these rather than keeping its own pair,
#: because `_inject`'s bounds check and this module's scaling are
#: statements about the same 640x480 slice, and two copies of a
#: screen size is how one of them ends up describing a window.
NATIVE_W, NATIVE_H = 640, 480


def format_value(value, signed=False):
    """'+12' / '-3' with signed, else plain — the original's %+d / %d."""
    if signed and value >= 0:
        return f"+{value}"
    return str(value)


def empire_value(row, local):
    """(text, warn). '--' while disconnected, never a fake zero."""
    if local is None:
        return "--", False
    value = getattr(local, row["field"], None)
    if value is None:
        return "--", False
    warn = bool(row.get("warn_negative")) and value < 0
    return format_value(value, row.get("signed", False)), warn


#: Fallback only. The real number is `frame_inset` at the TOP LEVEL
#: of layout.json, because `colonylist` needs the same one for the
#: colony name's leftward overflow and two copies of a number that
#: must agree is this project's oldest fault. See
#: `_frame_inset_note` there for the measurement.
FRAME_INSET_DEFAULT = 8


def native_column_width(cfg, layout):
    """The original's 104 px paragraph, in this screen's pixels.

    Separate from `value_column` so the smoke check can ask for the
    unclamped number without re-deriving it, and so deleting it
    breaks a test rather than silently ending the marking.
    """
    return int(cfg.get("native_width", 104)
               * (REF_W / NATIVE_W) * layout.scale)


def value_column(rect, cfg, layout, frame_inset=FRAME_INSET_DEFAULT):
    """(left, right) of the row — right is where a value ends.

    The alignment is TRANSCRIBED: the value ends at the column's
    right edge, because the original right-justifies it
    (`para.x2 = x + width - 1`, fmtpara.cpp:657, over
    `Print_Formatted_Paragraph_(520, 354, 104, buffer, 3)` at
    colsum.cpp:418). See `render` for the justification codes that
    establish it.

    **The WIDTH is a DEVIATION, and it is live at every
    resolution.** The original's paragraph is 104 native px of
    640, which is 312 reference px once scaled by
    `REF_W / NATIVE_W`. The `sidebar` cutout gives 286. The
    column is `min` of the two, so the shipped column is always
    the cutout's 286 — the clamp fires everywhere and the
    original's proportion is never the one drawn. Marked in
    `doc/v3_fundament.md` and in a smoke check.

    It is not a rounding difference: 286 against 312 is 8.3 % of
    the column, and every value on the screen sits 26 reference
    px left of where the original's proportion would put it.

    **Both numbers are kept, and the clamp is written to stop
    firing on its own.** The cutout comes from the frame artwork
    via `frame_holes.py` and can move; 104 is the transcription
    and cannot. If a future frame gives this hole 312 reference
    px or more, `min` selects the native width and the deviation
    ends without anybody remembering to come back — which is the
    only reason a clamp is the right shape here rather than a
    note saying "286 for now". The frame art is NOT being changed
    to suit this: that would be deriving geometry from a
    deviation, and the artwork is a separate decision.

    What must not happen is the native number quietly
    disappearing once somebody notices it never wins. The smoke
    check asserts `native_width` is still read and still larger
    than what gets drawn, so deleting it as dead weight fails.

    **`frame_inset` KEEPS THE TEXT OUT FROM UNDER THE FRAME, and
    it is measured rather than chosen.** It is a screen-level key,
    shared with `colonylist`, which needs the same number to bound
    the colony name's leftward overflow. Until 4 September 2026
    this returned `rect.x` and `rect.x + min(...)` — the cutout's
    own edges — and every label on this panel was drawn partly
    beneath the frame's metal rim. It looked like a
    resolution-dependent glitch, clear at one window size and
    clipping the R of RESERVE five pixels later, and it was
    neither: the overlap is there at EVERY size, and what changes
    with the window is only the font size meeting it, so at 18 px
    the stem survives and at 16 px it does not.

    Two things put text under the frame. `frame_holes.to_ref`
    adds `BLEED = 2` reference px OUTWARD on each side so that
    panel FILLS cover the anti-aliased rim — right for a fill and
    wrong for a glyph — and the artwork's rim then reaches a
    little further in. Measured at the six label rows across
    eight window sizes from 1280x720 to 3840x2160, the opaque
    frame reaches at most 4.5 reference px past the box's left
    edge and 3.0 past its right.

    So the inset is applied to BOTH edges: the values are right
    -aligned against the cutout's right edge and were losing their
    last pixels to the same rim, which is the same fault seen
    from the other end.

    **IT DOES NOT MAKE THE DEVIATION WORSE; IT MAKES IT HONEST.**
    286 was never the column a reader could see — some 7 or 8 of
    it was always under metal — so the drawn width was already
    about 278 and was being reported as 286. The number below is
    what is actually legible.
    """
    native_w = native_column_width(cfg, layout)
    inset = int(frame_inset * layout.scale)
    usable = max(1, rect.w - 2 * inset)
    # Still `min`, and still for decision 44's reason: the cutout
    # can move and 104 cannot, so a wider hole ends the deviation
    # with nobody remembering to come back.
    return rect.x + inset, rect.x + inset + min(usable, native_w)


def render(surface, box, cfg, local, layout, style, font_scale,
           frame_inset=FRAME_INSET_DEFAULT):
    """Six rows, label LEFT and value RIGHT — the original's.

    TRANSCRIBED, and it took two passes to read correctly. Each
    entry is built as `<attr>Label: <attr><value>` and the two
    `<attr>` are `ESTRINGS::s_0_0055110c` and `s_1_00551110`.
    Those are not colour codes: they are the bytes `1A 30` and
    `1A 31`, and FMTPARA sends 0x1A to `Set_Justification_`
    (0x1B is `Set_Current_Colors_`, fmtpara.cpp:364-368). The
    1.60 tree spells them a third time, unambiguously and with
    the answer in the comment — `strings.cpp:22`, `"\x1A" "0"`,
    */ switches paragraph justification to left alignment /*,
    and `:24` the same for right.

    So: LEFT for the label, then `Set_Justification_`
    (fmtpara.cpp:999) flushes the label segment when
    `char_count > 0`, then RIGHT for the value —
    `Justify_Line_` mode 1 adds the whole remaining width to the
    first character's advance (fmtpara.cpp:1699). **One row per
    entry, not two:** `Set_Justification_` never advances y, and
    y moves only on \r \n \v \f (fmtpara.cpp:322-341). The CR
    that `String_Builder2_` joins the six with is what ends each
    row.

    The right edge is the paragraph's own: `para.x2 = x + width
    - 1` (fmtpara.cpp:657) over
    `Print_Formatted_Paragraph_(520, 354, 104, ...)`, so 623 of
    640 native. See `value_column` for how that reaches HD.

    `box` is the `sidebar` cutout in reference coordinates and
    `font_scale` is the screen's `box_font_scale("sidebar")`; both
    are handed in rather than looked up, because a renderer that can
    reach a screen can reach anything.
    """
    rows = cfg.get("rows", [])
    if not box or not rows:
        return
    rect = pygame.Rect(*layout.rect(box))
    surface.fill(PANEL_BG[:3], rect)
    left, right = value_column(rect, cfg, layout, frame_inset)
    label_size = layout.font_size(int(cfg.get("label_font", 18) * font_scale))
    value_size = layout.font_size(int(cfg.get("value_font", 26) * font_scale))
    pad = int(rect.h * cfg.get("row_pad", 0.10))
    row_h = (rect.h - 2 * pad) / len(rows)
    for i, row in enumerate(rows):
        top = rect.y + pad + int(i * row_h)
        label = style.render_text(row["label"].upper(), label_size,
                                  LABEL_COLOR[:3])
        value, warn = empire_value(row, local)
        # render_text, not font.render: the sign characters are on
        # Bank Gothic DEMO's watermark list and get substituted.
        # Red-if-negative IS the original's and is kept — see
        # `empire._red_note`. It was queried as possibly resting
        # on a mis-transcribed byte; it does not.
        vt = style.render_text(
            value, value_size, (WARN_COLOR if warn else VALUE_COLOR)[:3])
        block_h = max(label.get_height(), vt.get_height())
        y = top + (int(row_h) - block_h) // 2
        # Both on ONE row: label flush left, value flush right.
        surface.blit(label, (left, y + (block_h - label.get_height())))
        surface.blit(vt, (right - vt.get_width(),
                          y + (block_h - vt.get_height())))
