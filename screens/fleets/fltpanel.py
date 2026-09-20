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


def draw_panel(surface, screen, lines, words=None):
    """The scanned ship's lines, top down inside `ship_panel_text`.

    `words` is `layout.json`'s own dict, handed in like `draw_labels`
    takes it: the renderer draws what it is given and does not know
    the wording (decision 15).
    """
    rect = panel_text_rect(screen)
    if rect is None or not lines:
        return
    asked = panel_font_px(screen)
    rendered, size, dropped = panel_block(screen, lines, words, rect, asked)
    _log_overflow(rect, asked, size, len(rendered) - bool(dropped), dropped)
    y = rect.y
    for surf in rendered:
        surface.blit(surf, (rect.x, y))
        y += surf.get_height()
