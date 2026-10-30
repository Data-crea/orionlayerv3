"""Fitting a string into a box: wrap it, and shrink it if it still
does not fit.

**THE THIRD COPY, EXTRACTED.** `colonybuild.wrap_text` said so in as
many words — *"This is the SECOND word-wrap in the tree, after
`helppopup._wrap`; the third is the one that should be extracted to a
shared helper rather than pasted again"* — and the colony summary's
move message is the third. Both originals now call this.

**MEASURED AS RENDERED, NEVER BY A PLAIN `font.size()`.** `measure` below
is the one cheap way: `Style.text_width` splits the string into the same
runs `render_text` does and sums each run's own font, cached per (text,
size), so a wrap or an ellipsis loop no longer draws a picture per trial
(work order 324). A style without it is measured by rendering.
`Style.render_text` can mix two fonts inside one string wherever a
glyph is substituted (decision 30), so a single font's metrics are
not the width that reaches the screen. That is the one rule this
module exists to keep in one place; it is also why every function
here takes a `style` rather than a font.

**A WORD WIDER THAN THE BOX IS LEFT WHOLE.** Wrapping cannot break
it, and cutting it would lose a character — which is not one of the
outcomes. `squeeze_lines` answers that case by shrinking the size
instead, and if there is nothing left to shrink it prints the string
anyway, which is what the original does when its own loop runs out
of steps (`BILL::Squeeze_Print_Paragraph_`).
"""
from core import fontscale, lang


def measure(style, text, size):
    """The width in px `style.render_text(text, size, ...)` would have —
    without drawing it. Decision 30: the width of what reaches the screen,
    glyph substitution included."""
    fast = getattr(style, "text_width", None)
    if fast is not None:
        return fast(text, size)
    return style.render_text(text, size, (255, 255, 255)).get_width()


def wrap_text(style, text, size, width):
    """One source string into lines that each fit `width` if they can.

    Returns TEXT, not surfaces, so a caller — and a test — can assert
    that nothing was dropped. OrionLayer's own sentence is translated
    WHOLE first (`core.lang.tr`, work order 200 C), then cut.
    """
    text = lang.tr(text)
    if measure(style, text, size) <= width:
        return [text]
    lines, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if current and measure(style, trial, size) > width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def wrap_rendered(style, text, size, width, color):
    """The same wrap, already rendered in `color`."""
    rgb = tuple(color[:3])
    return [style.render_text(line, size, rgb)
            for line in wrap_text(style, text, size, width)]


def squeeze_lines(style, text, width, max_h, sizes, color):
    """(surfaces, size) — the largest of `sizes` that fits both ways.

    BOTH dimensions. Height alone is not enough: a single word wider
    than the column cannot be broken, so it fits the height on one
    line and never triggers a shrink — a 15-glyph ship design
    measured 225 px in a 190 px column and sat there. The width is
    the hard side, so it has to be part of what the reduction is
    trying to satisfy.

    `sizes` is tried in order and the first that fits wins, so a
    caller passes them largest first. If none fits, the smallest is
    used and the string is printed whole regardless.
    """
    rgb = tuple(color[:3])
    text = lang.tr(text)
    size = sizes[-1]
    for size in sizes:
        lines = wrap_text(style, text, size, width)
        rendered = [style.render_text(line, size, rgb) for line in lines]
        if (sum(s.get_height() for s in rendered) <= max_h
                and max(s.get_width() for s in rendered) <= width):
            return rendered, size
    return wrap_rendered(style, text, size, width, rgb), size


def squeeze_block(style, paragraphs, width, max_h, sizes, color, gap=0):
    """(surfaces, size) for SEVERAL strings that have to fit together.

    `squeeze_lines` answers "one string in a box"; this answers "a
    list of them", which is not the same question and was being
    answered privately. Each paragraph is wrapped on its own — they
    are separate facts and must not re-flow into each other — and the
    size that wins is the largest at which ALL of them, wrapped, fit
    the box **together**. Measuring each line against the whole box
    height is the fault brief 97 found on the colony summary: every
    line fitted alone and the five together ran past the box.

    `gap` is extra leading between the rendered lines, in the caller's
    own pixels, and it counts toward the height like the glyphs do.

    Both dimensions, for the reason `squeeze_lines` gives: a single
    word wider than the box cannot be broken, so it satisfies the
    height on one line and never triggers a shrink.

    `sizes` is tried in order, largest first. If none fits, the
    smallest is used and the block is drawn whole — the caller decides
    what to do about the overflow, and `fits` below is how it asks.
    """
    rgb = tuple(color[:3])
    size = sizes[-1]
    rendered = []
    for size in sizes:
        rendered = [style.render_text(part, size, rgb)
                    for para in paragraphs
                    for part in wrap_text(style, para, size, width)]
        if not rendered:
            return [], size
        if block_height(rendered, gap) <= max_h and max(
                s.get_width() for s in rendered) <= width:
            return rendered, size
    return rendered, size


def block_height(rendered, gap=0):
    """How tall a list of rendered lines is, leading included."""
    if not rendered:
        return 0
    return (sum(s.get_height() for s in rendered)
            + gap * (len(rendered) - 1))


def fit_height_size(style, size, max_h):
    """The size to render at so a line of text fits `max_h` px of height.

    HD EXTENSION `font_scale` (work order 356): a row pitch or a band that
    boxes.json fixes does not grow with the player's text size, so above
    1.0 the size is stepped down until the scaled font is no taller than
    the band — but never below what the font was at 1.0, which is the
    look the screen was accepted with. At 1.0 and below `size` comes back
    unchanged, so the picture is pixel-identical to before the factor.
    """
    if fontscale.factor() <= 1.0:
        return size
    limit = max(max_h, style.raw_font(size).get_height())
    while size > 8 and style.get_font(size).get_height() > limit:
        size -= 1
    return size


def fit_width_size(style, text, size, max_w):
    """The same for a line of text that must fit `max_w` px of width
    (a button label, a table cell): above 1.0 only, down to the width it
    had at 1.0 if that is wider than `max_w`."""
    if fontscale.factor() <= 1.0:
        return size
    limit = max(max_w, style.raw_width(text, size))
    while size > 8 and measure(style, text, size) > limit:
        size -= 1
    return size
