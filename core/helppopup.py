"""The right-click help popup, shared by every HD screen.

MOO2 answers a right click over a help region with a bordered box
holding a title and a body of text and a CLOSE button
(`TEXTBOX::Draw_Help_Entry_`, textbox.cpp:307). This is the HD
counterpart: same trigger, same content, drawn in OrionLayer's own
skin — the thin blue border that already groups panels everywhere
else, filled with the screen's own background.

What is transcribed and what is not:

  transcribed   the trigger (right button), the regions, the text,
                the title/body split, the paragraph and column
                layout codes (`core/helpformat.py`), the green the original draws
                both in (measured off a native screenshot at
                RGB 72,144,56 — one colour, the title is merely a
                heavier font style), the CLOSE affordance, and the
                fact that the click is swallowed rather than acting
                as Cancel
  HD EXTENSION  the panel auto-sizes to its text and scrolls when it
                cannot fit. The original draws a fixed box and lets
                `FMTPARA` wrap into it at a fixed 339 px; at four
                different HD resolutions a fixed box either wastes
                half the screen on two lines or clips a long entry.
                Marked here, in `screens/*/help.json`, and asserted
                by the smoke test.
  NOT drawn     the per-entry animation. `s_help_record` carries an
                `anim_lbx` / `anim_info` pair and the original plays
                it beside the text. `tools/help_extract.py` extracts
                the reference so nothing is lost, but nothing renders
                it yet. A deliberate omission, not an oversight.

No dimming layer under the popup, for the same reason the Custom Race
message box has none: MOO2 is palette-indexed and cannot alpha-blend,
so a darkened backdrop would be an invention.
"""
import pygame

from core import helpformat
from core import palette

# The original renders title and body in the same green; only the
# font style differs (Font_Colors2_(4, ...) vs (2, ...),
# textbox.cpp:317-321). Measured, not estimated.
COL_TITLE = palette.col("help", "title", (72, 144, 56))
COL_BODY = palette.col("help", "body", (72, 144, 56))
COL_CLOSE = palette.col("help", "close", (150, 168, 200))
COL_FILL = palette.col("help", "fill", (16, 16, 24))

# Reference units (1920x1080), before the box's font_scale.
FONT_TITLE = 30
FONT_BODY = 22
FONT_CLOSE = 18
LINE_GAP = 5           # between wrapped lines of one paragraph
PARA_GAP = 14          # between paragraphs (a blank source line)
TITLE_GAP = 22         # under the title
PAD_X = 40
PAD_TOP = 30
PAD_BOTTOM = 56        # room for the CLOSE line
MIN_H = 140
SCROLL_STEP = 60       # reference pixels per wheel notch

#: Used when the screen has no `help_popup` box, so a missing or
#: mis-edited box can never make the help unreachable.
FALLBACK_BOX = (420, 170, 1080, 745)


class Backdrop:
    """The cockpit texture the popup cuts its fill out of.

    The Custom Race message box fills itself from its OWN screen's
    background, which works there because that screen already sits on
    the shared cockpit texture — cutting it back out reads as bare
    backdrop with the panels lifted off. The same trick fails on a
    screen whose background is a picture: over the Main Menu artwork
    or the star field it reproduces exactly what was already there,
    and the popup turns invisible.

    So the help popup always fills from `background_cockpit.png` —
    the backdrop every panel-less screen in the tree already uses.
    Still not a sampled colour constant, and now identical on all six
    screens. Cover-scaled to the window and cached per size.
    """

    def __init__(self):
        self._source = None
        self._scaled = None
        self._size = None

    def surface(self, res, win_w, win_h):
        if self._source is None:
            path = res.shared("background_cockpit.png")
            if not path:
                return None
            self._source = pygame.image.load(path).convert()
        if self._size != (win_w, win_h):
            sw, sh = self._source.get_size()
            scale = max(win_w / sw, win_h / sh)
            big = pygame.transform.smoothscale(
                self._source, (max(win_w, int(sw * scale)),
                               max(win_h, int(sh * scale))))
            x = (big.get_width() - win_w) // 2
            y = (big.get_height() - win_h) // 2
            self._scaled = big.subsurface((x, y, win_w, win_h)).copy()
            self._size = (win_w, win_h)
        return self._scaled


class HelpPopup:
    """One help entry, modal over its screen.

    Owns no content: the screen hands it a title and a body. Geometry
    comes from the `help_popup` box, so it is F5-movable like every
    other panel; the panel then shrinks to its text inside that box.
    """

    def __init__(self):
        self.help_id = None
        self._title = ""
        self._lines = []
        self._scroll = 0
        self._max_scroll = 0
        self._cache = {}

    # ── State ────────────────────────────────────────────

    @property
    def visible(self):
        return self.help_id is not None

    def open(self, help_id, title, body):
        """Show an entry. `body` is a raw HELP.LBX string.

        Decoding happens here, once, rather than in the render path:
        MOO2's bodies carry `FMTPARA` control codes, and the column
        positions in them are what makes a table a table (see
        `core/helpformat.py`).
        """
        self.help_id = help_id
        self._title = helpformat.parse(title or "")
        self._lines = helpformat.parse(body or "")
        self._scroll = 0

    def close(self):
        self.help_id = None
        self._title = ""
        self._lines = []
        self._scroll = 0

    def clear_cache(self):
        """Drop rendered lines (resolution or skin change)."""
        self._cache.clear()

    # ── Input ────────────────────────────────────────────

    def handle_wheel(self, direction):
        """Scroll a long entry. Always consumes the wheel."""
        if self._max_scroll > 0:
            self._scroll = max(0, min(self._max_scroll,
                                      self._scroll - direction
                                      * SCROLL_STEP))
        return True

    # ── Render ───────────────────────────────────────────

    def render(self, surface, L, style, box, fs, backdrop=None,
               close_label="CLOSE", scroll_label="scroll"):
        """Draw the popup inside `box` (reference rect), auto-sized.

        `backdrop` is the screen's own scaled background aligned to
        the window origin; the popup cuts its fill out of it rather
        than inventing a colour, exactly like the Custom Race message
        box. A screen that has no such surface (the galaxy map paints
        its own) passes None and gets the flat fill.
        """
        if not self.visible:
            return
        bx, by, bw, bh = box
        title_size = max(8, L.font_size(int(FONT_TITLE * fs)))
        body_size = max(8, L.font_size(int(FONT_BODY * fs)))
        close_size = max(8, L.font_size(int(FONT_CLOSE * fs)))

        inner_w = max(40, int((bw - 2 * PAD_X) * L.scale))
        blocks = self._blocks(style, title_size, body_size, inner_w)
        content_h = sum(h for _, h in blocks)

        pad_top = int(PAD_TOP * L.scale)
        pad_bot = int(PAD_BOTTOM * L.scale)
        max_h = int(bh * L.scale)
        want_h = content_h + pad_top + pad_bot
        panel_h = max(int(MIN_H * L.scale), min(want_h, max_h))
        view_h = panel_h - pad_top - pad_bot

        self._max_scroll = max(0, content_h - view_h)
        self._scroll = min(self._scroll, self._max_scroll)

        px, _ = L.pos(bx, by)
        pw = int(bw * L.scale)
        # Centred vertically in the box so a two-line entry does not
        # hang off the top edge of a tall editor rect.
        py = int(by * L.scale + L.offset_y) + (max_h - panel_h) // 2
        rect = pygame.Rect(px, py, pw, panel_h)

        if backdrop is not None and backdrop.get_rect().contains(rect):
            surface.blit(backdrop, (px, py), rect)
        else:
            fill = pygame.Surface((pw, panel_h))
            fill.fill(tuple(COL_FILL[:3]))
            surface.blit(fill, (px, py))
        style.draw_thin_border(surface, rect, L.scale)

        # Text area, clipped so a scrolled entry cannot bleed over
        # the border or the CLOSE line.
        tx = px + int(PAD_X * L.scale)
        ty = py + pad_top
        clip = surface.get_clip()
        surface.set_clip(pygame.Rect(tx, ty, inner_w, view_h))
        y = ty - self._scroll
        for surf, height in blocks:
            if surf is not None and y + height > ty and y < ty + view_h:
                surface.blit(surf, (tx, y))
            y += height
        surface.set_clip(clip)

        label = close_label
        if self._max_scroll > 0:
            # A word, not an arrow glyph. The DEMO Bank Gothic drew
            # its watermark for a triangle; Aldrich has no triangle
            # either and draws the missing-glyph box. `blocked_glyphs`
            # cannot help with either, because it finds characters
            # that SHARE a bitmap, not ones the font simply lacks.
            # A display font is not guaranteed to have symbols.
            label = f"{close_label}  -  {scroll_label}"
        text = style.render_text(label.upper(), close_size,
                                 tuple(COL_CLOSE[:3]))
        surface.blit(text,
                     (px + (pw - text.get_width()) // 2,
                      py + panel_h - pad_bot
                      + (pad_bot - text.get_height()) // 2))

    # ── Layout helpers ───────────────────────────────────

    def _blocks(self, style, title_size, body_size, width):
        """[(surface|None, height)] for title + body, cached.

        Two kinds of line come out of `helpformat.parse`. A line with
        no fixed columns is ordinary prose and gets word-wrapped to
        the panel. A line that carries column positions is a table
        row, and is laid out by placing each run at its own native
        column scaled to the panel width — never wrapped, because
        wrapping is exactly what would destroy it.
        """
        key = (self.help_id, title_size, body_size, width)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        out = []
        for line in self._title:
            text = line.plain()
            if not text:
                continue
            for surf in self._wrap(style, text, title_size, width,
                                   COL_TITLE):
                out.append((surf, surf.get_height() + int(LINE_GAP)))
        if out:
            out.append((None, TITLE_GAP))

        blank_h = style.get_font(body_size).get_height() + int(LINE_GAP)
        for line in self._lines:
            if line.columns:
                surf = self._columns(style, line, body_size, width)
                if surf is not None:
                    out.append((surf, surf.get_height() + int(LINE_GAP)))
            else:
                text = line.plain()
                if text.strip():
                    for surf in self._wrap(style, text, body_size,
                                           width, COL_BODY):
                        out.append(
                            (surf, surf.get_height() + int(LINE_GAP)))
                else:
                    # An empty source line is not nothing: \r runs
                    # Complete_Line_ and then advances a line either
                    # way (fmtpara.cpp:324), so the blank lines
                    # between MOO2's paragraphs are real spacing.
                    out.append((None, blank_h))
            if line.paragraph_break:
                out.append((None, PARA_GAP))

        self._cache[key] = out
        return out

    @staticmethod
    def _columns(style, line, size, width):
        """One table row: each run at its own scaled native column.

        `helpformat.HELP_PARA_W` is the paragraph width the original
        laid help text out at, so a column position divided by it is
        a fraction of the text area — which is what makes the table
        line up at 1080p and at 4K rather than at one of them.
        """
        pieces = []
        for run in line.runs:
            if not run.text.strip():
                continue
            surf = style.render_text(run.text, size, tuple(COL_BODY[:3]))
            if run.x is None:
                x = (pieces[-1][0] + pieces[-1][1].get_width()
                     if pieces else 0)
            else:
                x = int(run.x * width / helpformat.HELP_PARA_W)
            pieces.append((x, surf))
        if not pieces:
            return None

        height = max(s.get_height() for _, s in pieces)
        row = pygame.Surface((width, height), pygame.SRCALPHA)
        for x, surf in pieces:
            row.blit(surf, (min(x, max(0, width - surf.get_width())), 0))
        return row

    @staticmethod
    def _wrap(style, text, size, width, color):
        """Word-wrap one source line into rendered surfaces.

        Measured by rendering, never by `font.size()`:
        `Style.render_text` mixes two fonts inside one string wherever
        the font substitutes a glyph, so a single font's metrics are
        not necessarily the width that ends up on screen — true again
        the moment a mod ships a substituting font.
        """
        col = tuple(color[:3])
        surf = style.render_text(text, size, col)
        if surf.get_width() <= width:
            return [surf]

        lines, current = [], ""
        for word in text.split():
            trial = f"{current} {word}".strip()
            if current and style.render_text(
                    trial, size, col).get_width() > width:
                lines.append(current)
                current = word
            else:
                current = trial
        if current:
            lines.append(current)
        return [style.render_text(line, size, col) for line in lines]
