"""The Info screen's text boxes: every text wraps, and scrolls where it does
not fit — HD EXTENSION `wrap_and_scroll` (work order 175 D).

The original prints its long texts into fixed bitmaps with FMTPARA and
cuts what does not fit (the category text into 190 x 314, info.cpp:1086-
1093) or lets it run past its box (the "How to?" body, :1893-1906), and
pages its lists instead of scrolling them. The order: no text may be cut
off or run out of its box at any window size. So every text here is
wrapped to its box's width — a word too long for the line is broken, never
left hanging over the edge — and a box whose lines do not fit gets a
scroll offset (the mouse wheel over it) and a HUD scroll bar.

`Box.draw` records every line in `screen._drawn` as (line rect, box
rect, drawn), which is what the smoke check holds: every line inside its
box's width, and every line it DRAWS wholly inside its box — a line the
scroll offset leaves partly outside is not drawn at all (the wheel brings
it in), so nothing is ever cut in half.
"""
import pygame

from core.hud import blocks as hud
from core import helpformat

MIN_FONT = 8


def paragraphs(text):
    """A text — plain, or a HELP.LBX body with FMTPARA codes — as a list
    of source lines (`core/helpformat.parse`), blank lines kept."""
    if not text:
        return []
    if any(c in text for c in "\a\r\v\f\t"):
        return [line.plain() for line in helpformat.parse(text)]
    return text.split("\n")


def wrap(style, text, size, width):
    """Lines that each fit `width`: words, and a word wider than the line
    broken by characters."""
    out = []
    for source in paragraphs(text):
        if not source.strip():
            out.append("")
            continue
        current = ""
        for word in source.split():
            trial = f"{current} {word}".strip()
            if style.render_text(trial, size, (255, 255, 255)).get_width() \
                    <= width:
                current = trial
                continue
            if current:
                out.append(current)
            current = ""
            while style.render_text(word, size, (255, 255, 255)
                                    ).get_width() > width and len(word) > 1:
                k = len(word)
                while k > 1 and style.render_text(
                        word[:k], size, (255, 255, 255)).get_width() > width:
                    k -= 1
                out.append(word[:k])
                word = word[k:]
            current = word
        if current:
            out.append(current)
    return out


class Box:
    """One text box: its rect, its lines, its scroll offset in pixels."""

    def __init__(self, key, rect, text, size, colour, align="left",
                 line_gap=1.2):
        self.key, self.rect = key, pygame.Rect(rect)
        self.text, self.size, self.colour = text, size, colour
        self.align, self.line_gap = align, line_gap

    def layout(self, style):
        pad = max(2, self.size // 3)
        self.inner = self.rect.inflate(-2 * pad, -2 * pad)
        bar = max(6, self.size // 2)
        lines = wrap(style, self.text, self.size, self.inner.w)
        step = int(self.size * self.line_gap)
        if len(lines) * step > self.inner.h:
            # Room for the scroll bar, then wrap again to the narrower box.
            self.inner.w -= bar + 2
            lines = wrap(style, self.text, self.size, self.inner.w)
        self.lines, self.step = lines, step
        self.content_h = len(lines) * step
        self.overflow = max(0, self.content_h - self.inner.h)
        return self

    def draw(self, surface, screen):
        style = screen.style
        self.layout(style)
        offset = max(0, min(screen._scroll.get(self.key, 0), self.overflow))
        screen._scroll[self.key] = offset
        previous = surface.get_clip()
        surface.set_clip(self.inner)
        y = self.inner.y - offset
        for line in self.lines:
            if line:
                img = style.render_text(line, self.size, self.colour)
                x = self.inner.x
                if self.align == "center":
                    x = self.inner.centerx - img.get_width() // 2
                r = pygame.Rect(x, y, img.get_width(), img.get_height())
                drawn = self.inner.contains(r)
                if drawn:
                    surface.blit(img, r.topleft)
                screen._drawn.append((r, self.inner, drawn))
            y += self.step
        surface.set_clip(previous)
        if self.overflow:
            bar = pygame.Rect(self.inner.right + 2, self.inner.y,
                              max(6, self.size // 2), self.inner.h)
            hud.scrollbar(surface, bar, screen.layout.scale, offset,
                          self.inner.h, self.content_h)
        screen._boxes[self.key] = self


def line(surface, screen, text, rect, size, colour, align="left"):
    """One label that must stay one line: shrunk to fit its rect's width,
    down to `MIN_FONT`; below that it wraps (a `Box`), never runs out."""
    rect = pygame.Rect(rect)
    style = screen.style
    while size > MIN_FONT and style.render_text(
            text, size, colour).get_width() > rect.w:
        size -= 1
    img = style.render_text(text, size, colour)
    if img.get_width() > rect.w or img.get_height() > rect.h + size:
        Box(("line", text, tuple(rect)), rect, text, size, colour,
            align).draw(surface, screen)
        return
    x = rect.x if align == "left" else (
        rect.centerx - img.get_width() // 2 if align == "center"
        else rect.right - img.get_width())
    r = pygame.Rect(x, rect.centery - img.get_height() // 2, img.get_width(),
                    img.get_height())
    surface.blit(img, r.topleft)
    screen._drawn.append((r, rect.inflate(0, img.get_height()), True))


def scroll(screen, point, direction):
    """The mouse wheel over a box moves its offset by three lines."""
    for key, box in screen._boxes.items():
        if box.rect.collidepoint(point) and box.overflow:
            now = screen._scroll.get(key, 0)
            screen._scroll[key] = max(0, min(box.overflow,
                                             now - direction * 3 * box.step))
            return True
    return False
