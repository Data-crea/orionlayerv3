"""Fitting a string into a box: wrap it, and shrink it if it still
does not fit.

**THE THIRD COPY, EXTRACTED.** `colonybuild.wrap_text` said so in as
many words — *"This is the SECOND word-wrap in the tree, after
`helppopup._wrap`; the third is the one that should be extracted to a
shared helper rather than pasted again"* — and the colony summary's
move message is the third. Both originals now call this.

**MEASURED BY RENDERING, NEVER BY `font.size()`.**
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


def wrap_text(style, text, size, width):
    """One source string into lines that each fit `width` if they can.

    Returns TEXT, not surfaces, so a caller — and a test — can assert
    that nothing was dropped.
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
    size = sizes[-1]
    for size in sizes:
        lines = wrap_text(style, text, size, width)
        rendered = [style.render_text(line, size, rgb) for line in lines]
        if (sum(s.get_height() for s in rendered) <= max_h
                and max(s.get_width() for s in rendered) <= width):
            return rendered, size
    return wrap_rendered(style, text, size, width, rgb), size
