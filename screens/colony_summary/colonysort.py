"""The seven sort keys inside ONE bar, and RETURN beside it.

**THE BAR IS ONE HOLE NOW.** The superseded frame cut seven separate
button holes and `boxes.json` carried seven boxes; the Stage A3 plate
cuts one `sort_bar`, which is what the original has — a recessed blue
strip with seven labels laid along it (see the framebuffer at native
y 445-470). So the division lives here rather than in the artwork.

**THE ACTIVE KEY IS HIGHLIGHTED AT ITS OWN LABEL WIDTH, and that is
transcribed.** The original fills a rectangle the width of the word
plus a small pad — "Name" lights a short box, "Producing" a long one
— it does not light a cell of a grid, because there is no grid. A row
of equal sevenths would be our invention wearing the original's
colours, and the tell would be a highlight that does not fit its word.

**ONE FUNCTION, TWO ANSWERS** (decision 5). `layout` returns, per
key, both the HIT rect and the HIGHLIGHT rect. The renderer draws the
second and the click test walks the first; there is no second
arithmetic to drift. The hit rect is wider than the highlight on
purpose: a click between two words has to go somewhere, and the
original's own fields are wider than their text too.

**THE GAP BETWEEN LABELS IS DERIVED, NOT TRANSCRIBED.** The original
spaces its words along the bar and the source carries no table of
positions — only one `native_click` point inside each button
(colsum.cpp:267-273, kept in `layout.json` as the injection point and
as the checkable half of decision 39). Even gaps are the reading that
fits those seven points best; they are marked here because a reading
is not a transcription. The points themselves stay the authority for
what gets INJECTED, and a smoke check asserts every one of them still
falls inside the button it belongs to.
"""
import pygame

#: Minimum breathing room around a highlighted word, reference px.
#: The original pads its lit box by about 2 native px on each side.
HIGHLIGHT_PAD = 6


class SortButton:
    """One key's two rectangles and the label that produced them."""

    __slots__ = ("key", "label", "hit", "highlight")

    def __init__(self, key, label, hit, highlight):
        self.key = key
        self.label = label
        self.hit = hit
        self.highlight = highlight


def layout(bar, keys, style, font_size):
    """[SortButton] spanning `bar` left to right, in `keys` order.

    `bar` is the sort_bar box in WINDOW pixels; `keys` is
    [(key, label)]. Widths are measured by RENDERING, never by one
    font's `.size()` — `Style.render_text` may mix two fonts inside a
    string, so a single font's metrics are not the width that will be
    drawn (decision 30's consequence).
    """
    if not keys:
        return []
    bar = pygame.Rect(bar)
    widths = [style.render_text(label, font_size, (255, 255, 255)).get_width()
              for _key, label in keys]
    slack = bar.width - sum(widths)
    # n + 1 gaps: one before the first word and one after the last, so
    # the row is centred in its bar the way the original's is.
    gap = max(0, slack // (len(keys) + 1))
    out = []
    x = bar.x + gap
    edges = []
    for width in widths:
        edges.append((x, width))
        x += width + gap
    for i, ((key, label), (lx, lw)) in enumerate(zip(keys, edges)):
        left = bar.x if i == 0 else (edges[i - 1][0] + edges[i - 1][1] + lx) // 2
        right = (bar.right if i == len(keys) - 1
                 else (lx + lw + edges[i + 1][0]) // 2)
        pad = HIGHLIGHT_PAD
        out.append(SortButton(
            key, label,
            pygame.Rect(left, bar.y, right - left, bar.height),
            pygame.Rect(max(left, lx - pad), bar.y,
                        min(right, lx + lw + pad) - max(left, lx - pad),
                        bar.height)))
    return out


def for_screen(screen):
    """The seven buttons of `screen`'s sort bar, or [].

    Takes the screen the way `colonyframe.frame_source` does, so the
    bar's box, its font size and the label list are read in ONE place
    and the renderer and the click test cannot pick up different ones
    (decision 5). Rebuilt per call rather than cached: the bar moves
    with the window and the labels come from `layout.json`, so there
    is nothing here worth remembering.
    """
    box = screen.box_rect("sort_bar")
    if not box:
        return []
    keys = [(b["key"], b["label"])
            for b in screen._data.get("sort", {}).get("buttons", [])]
    return layout(screen.layout.rect(box), keys, screen.style,
                  font_size(screen))


def font_size(screen):
    return screen.layout.font_size(
        screen.box_style("sort_bar").get("font_size", 18))


def button_at(buttons, x, y):
    """The key under a window point, or None."""
    for button in buttons:
        if button.hit.collidepoint(x, y):
            return button.key
    return None


def render(surface, buttons, active_key, unavailable, mouse,
           style, font_size, active_bg, hover_bg, text, text_dim):
    """Draw the bar's seven words. The renderer's half of `layout`.

    The highlight is filled only for the active key and the hovered
    one; every other word sits on the bar's own fill, which is what
    the original does — six plain words and one lit box.
    """
    for button in buttons:
        active = button.key == active_key
        if active or button.hit.collidepoint(mouse):
            surface.fill((active_bg if active else hover_bg)[:3],
                         button.highlight)
        colour = text_dim if button.key in unavailable else text
        word = style.render_text(button.label.upper(), font_size, colour[:3])
        surface.blit(word, (
            button.highlight.x
            + (button.highlight.width - word.get_width()) // 2,
            button.highlight.y
            + (button.highlight.height - word.get_height()) // 2))


def render_return(surface, screen, mouse, bg, hover_bg, text_color):
    """RETURN, which is a button on this row and not a sort key.

    It keeps its own box because the plate cuts it as its own hole —
    the original draws it as a separate raised plate to the right of
    the bar (see the framebuffer at native x 523+), and it is the one
    control here that takes the CLICK path, because its field reports
    no letter (decision 39's fallback).
    """
    box = screen.box_rect("return")
    if not box:
        return
    rect = pygame.Rect(*screen.layout.rect(box))
    surface.fill((hover_bg if rect.collidepoint(mouse) else bg)[:3], rect)
    label = screen._data.get("return", {}).get("label", "Return")
    word = screen.style.render_text(
        label.upper(),
        screen.layout.font_size(
            screen.box_style("return").get("font_size", 24)),
        text_color[:3])
    surface.blit(word, (rect.x + (rect.w - word.get_width()) // 2,
                        rect.y + (rect.h - word.get_height()) // 2))
