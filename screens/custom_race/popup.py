"""Custom Race — the message box for a rejected Accept.

MOO2 refuses a race whose remaining picks are negative and answers
with a small error box drawn over the screen ("Picks remaining must
be greater than or equal to zero."). OrionLayer tests the same
condition *before* it forwards Accept, so orion2re never receives the
invalid Accept, never draws its own box into the framebuffer, and the
HD screen keeps the message.

Layout is two F5 boxes, the same split the picks/score bar uses:

    picks_popup        panel rect, outlined with the thin blue border
                       the three Custom Race columns already use
    picks_popup_text   text area, with its own font_scale

Both are movable, resizable and scalable in the editor (Ctrl+Wheel on
the text box changes the font scale), and the popup renders while the
editor is open so the scale can be judged against the real string.

The fill is not a colour constant: the popup blits the screen's own
scaled background at the same window coordinates, so it reads as a
piece of the Custom Race backdrop with the panels lifted off it. A
sampled RGB value would have been a number copied out of the artwork,
wrong the day the artwork changes.

No dimming layer under the popup: MOO2 is palette-indexed and cannot
alpha-blend a sprite at all, so a darkened backdrop would be an
invention rather than a transcription.
"""
import pygame
from screens.custom_race.renderer import _c

# Only used when the screen has no background surface to borrow.
COL_BG   = _c("popup_bg",   (19, 26, 31, 255))
COL_TEXT = _c("popup_text", (216, 88, 78))

FONT     = 26      # reference units, before font_scale
LINE_GAP = 8       # reference units between wrapped lines

# Used only when the box is missing from boxes.json, so a bad edit
# cannot make the message unreachable.
FALLBACK_PANEL = (560, 400, 800, 280)
FALLBACK_INSET = (60, 50)


def fallback_text_rect(panel):
    """Text area inset into a panel rect (reference units)."""
    ix, iy = FALLBACK_INSET
    return (panel[0] + ix, panel[1] + iy,
            panel[2] - 2 * ix, panel[3] - 2 * iy)


class MessagePopup:
    """One short message in a bordered box, dismissed by any input.

    The popup owns nothing but its text: geometry comes from the
    screen's boxes, the wording from traits.json. Rendered lines are
    cached per (text, pixel size, width) so wrapping does not re-run
    every frame.
    """

    def __init__(self):
        self.message = ""
        self._cache = {}

    @property
    def visible(self):
        return bool(self.message)

    def open(self, message):
        self.message = message or ""

    def close(self):
        self.message = ""

    def clear_cache(self):
        """Drop rendered lines (resolution or skin change)."""
        self._cache.clear()

    def render(self, surface, L, style, panel, text_rect, fs,
               message=None, backdrop=None):
        """Draw panel and centred text. `message` overrides the state.

        Passing a message explicitly is what lets the editor preview
        the popup while it is closed. `backdrop` is the screen's own
        scaled background, aligned to the window origin; the popup
        cuts its fill out of it rather than inventing a colour.
        """
        text = message if message is not None else self.message
        px, py = L.pos(panel[0], panel[1])
        pw, ph = L.size(panel[2], panel[3])
        if pw < 8 or ph < 8:
            return

        # Opaque on purpose — a translucent box would be an effect the
        # original could not produce. The fill is the screen's own
        # background at these very coordinates, so the box reads as
        # bare backdrop with the panels lifted off it.
        rect = pygame.Rect(px, py, pw, ph)
        if backdrop and backdrop.get_rect().contains(rect):
            surface.blit(backdrop, (px, py), rect)
        else:
            back = pygame.Surface((pw, ph), pygame.SRCALPHA)
            back.fill(COL_BG)
            surface.blit(back, (px, py))
        style.draw_thin_border(surface, rect, L.scale)

        if not text:
            return

        size = max(8, L.font_size(int(FONT * fs)))
        tx, ty = L.pos(text_rect[0], text_rect[1])
        tw, th = L.size(text_rect[2], text_rect[3])
        lines = self._lines(style, text, size, max(20, tw))
        gap = max(1, int(LINE_GAP * fs * L.scale))
        total = (sum(s.get_height() for s in lines)
                 + gap * (len(lines) - 1))
        y = ty + (th - total) // 2
        for surf in lines:
            surface.blit(surf, (tx + (tw - surf.get_width()) // 2, y))
            y += surf.get_height() + gap

    def _lines(self, style, text, size, max_w):
        """Word-wrap into rendered line surfaces, cached.

        Measuring happens by rendering: `Style.render_text` mixes two
        fonts inside one string wherever the DEMO font substitutes a
        glyph, so a single font's `.size()` is not the width that
        ends up on screen.
        """
        key = (text, size, max_w)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        lines, current = [], ""
        for word in text.split():
            trial = f"{current} {word}".strip()
            width = style.render_text(trial, size, COL_TEXT).get_width()
            if current and width > max_w:
                lines.append(current)
                current = word
            else:
                current = trial
        if current:
            lines.append(current)

        rendered = [style.render_text(line, size, COL_TEXT)
                    for line in lines]
        self._cache[key] = rendered
        return rendered
