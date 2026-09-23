"""Where the hover band goes: centred on the line the eye reads.

Data, on the live panel: the band's top edge sat on the label's top
edge, so the words clung to the ceiling of it ("Holo Simulator"). The
band's PLACE is ours — the original cycles a palette index and draws a
little arrow instead (`Draw_Little_Arrow_`, tech.cpp:740-775), and an
RGB surface has neither — so the rule is Data's too: the band is
centred on the text, the same distance above and below.

**ON THE LINE THE EYE READS, which is not the line the font occupies.**
From the top of the capitals to the baseline. A descender — g, p, y —
hangs below the baseline and does not count: centring on the FULL glyph
box would push the band down on "Holo Simulator" and not on "Ion Drive",
and two rows of the same panel would sit differently for a reason
nobody can see.

**MEASURED, NOT COMPUTED FROM METRICS.** `Font.get_ascent()` is the
font's own promise and the cap height is not in it at all, so the span
comes from rendering capitals and reading the ink back
(`Surface.get_bounding_rect`). It is the same move the smoke checks
make on this screen: measure the drawing, do not recompute where the
drawing should have gone (decision 5).

THE TEXT DOES NOT MOVE. Every anchor here is transcribed
(tech.cpp:735, :492, list.cpp:94-116) and stays where the original puts
it; only the band moves. So does the click area: `row_rect` is the
original's own field and this module never touches it.
"""
import pygame

from core import researchlist
from core import researchnative as geom_mod

#: The band's height in the original's own pixels, the same for every
#: row — see `researchlist.BAND_H` for why it is derived and not typed.
HEIGHT = researchlist.BAND_H

#: What the span is measured on: capitals, no descenders. The string is
#: irrelevant beyond that — every glyph in it has the same cap top and
#: sits on the same baseline, which is the whole point of a baseline.
REFERENCE = "HX"


def cap_span(style, size):
    """(top, bottom) of the capitals' ink inside one rendered line.

    Relative to the surface `render_text` returns, which is what the
    caller blits at the label's own anchor — so adding the label's
    window y to these two numbers gives the line the eye reads.
    """
    box = style.render_text(REFERENCE, size, (255, 255, 255)) \
        .get_bounding_rect()
    return box.top, box.bottom


def band(layout, style, size, label_native, x1_native, x2_native):
    """The band's WINDOW rectangle for a label drawn at `label_native`.

    `size` is the size the label is ACTUALLY drawn at, after the shrink
    rule (`researchpanel._fit`) has had it: a name that had to come
    down two points has a shorter line to be centred on, and taking the
    nominal size here would put the band a pixel off on exactly the
    rows the shrink touches.

    The x span is the row's, which is transcribed; only y is ours.
    """
    _, ly = geom_mod.window_point(label_native, layout)
    top, bottom = cap_span(style, size)
    x, _, w, h = geom_mod.window_rect(
        (x1_native, 0, x2_native, HEIGHT - 1), layout)
    return pygame.Rect(x, round(ly + (top + bottom) / 2.0 - h / 2.0), w, h)
