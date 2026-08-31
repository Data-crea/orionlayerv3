"""TextInput — single-line text entry widget.

For Enter Ruler Name, Enter Home Star Name, savegame names.
Consumes full KEYDOWN events (needs event.unicode), so the
owning screen overrides handle_key_event() and forwards events
while the input is focused.

Rendering note: the value is drawn with the PROPORTIONAL system
font, not Bank Gothic — the demo Bank Gothic renders watermark
glyphs for hyphen/minus/plus, and names may contain hyphens.
The label above the field can safely use Bank Gothic.

Usage:
    self.input = TextInput(max_len=14, on_submit=self._accept,
                           on_cancel=self._back)
    # render():   self.input.render(surface, rect, style, layout)
    # key event:  if self.input.handle_key_event(event): return
    # click:      self.input.handle_click(x, y)  (focus on hit)
"""
import time
import pygame
from core import palette

_c = palette.for_section("widgets")

COL_BG        = _c("input_bg",        (12, 16, 30))
COL_BORDER    = _c("input_border",    (60, 80, 120))
COL_FOCUS     = _c("input_focus",     (120, 170, 255))
COL_TEXT      = _c("input_text",      (220, 235, 255))
COL_PLACEHOLD = _c("input_placeholder", (100, 110, 140))
COL_CARET     = _c("input_caret",     (140, 185, 240))

FONT_REF = 20         # reference font size (1080p)
PAD_X = 12
CARET_BLINK = 0.53    # seconds


class TextInput:
    def __init__(self, value="", max_len=20, placeholder="",
                 on_submit=None, on_cancel=None, allowed=None,
                 font_ref=FONT_REF):
        """allowed: optional predicate(char) -> bool to filter input
        (default: printable latin-1, no control chars).
        font_ref: text size in 1080p reference pixels."""
        self.value = value
        self.font_ref = font_ref
        self.max_len = max_len
        self.placeholder = placeholder
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.allowed = allowed or self._default_allowed
        self.focused = True
        self._rect = pygame.Rect(0, 0, 0, 0)

    @staticmethod
    def _default_allowed(ch):
        return ch.isprintable() and ord(ch) < 256

    # ── Input ───────────────────────────────────────────

    def handle_key_event(self, event):
        """Consume a KEYDOWN event. Returns True if handled."""
        if not self.focused or event.type != pygame.KEYDOWN:
            return False
        if event.key == pygame.K_RETURN:
            if self.on_submit:
                self.on_submit(self.value)
            return True
        if event.key == pygame.K_ESCAPE:
            if self.on_cancel:
                self.on_cancel()
            return True
        if event.key == pygame.K_BACKSPACE:
            self.value = self.value[:-1]
            return True
        ch = getattr(event, "unicode", "")
        if ch and len(self.value) < self.max_len and self.allowed(ch):
            self.value += ch
            return True
        # Swallow other keys while focused so hotkeys (F-keys pass
        # through main.py before reaching us) don't leak into the
        # game as INJECT_KEY.
        return True

    def handle_click(self, x, y):
        """Focus when clicked inside, defocus outside.
        Returns True if the click hit the field."""
        self.focused = self._rect.collidepoint(x, y)
        return self.focused

    # ── Render ──────────────────────────────────────────

    def render(self, surface, rect, style, layout):
        self._rect = pygame.Rect(rect)
        pygame.draw.rect(surface, COL_BG, rect, border_radius=4)
        border = COL_FOCUS if self.focused else COL_BORDER
        pygame.draw.rect(surface, border, rect, width=2,
                         border_radius=4)

        # Proportional font — Bank Gothic demo watermarks '-'/'+'
        font = style.get_prop_font(layout.font_size(self.font_ref))
        pad = int(PAD_X * layout.scale)
        if self.value:
            text = font.render(self.value, True, COL_TEXT)
        else:
            text = font.render(self.placeholder, True, COL_PLACEHOLD)
        ty = rect.y + (rect.h - text.get_height()) // 2
        surface.blit(text, (rect.x + pad, ty))

        # Caret (blinking, after the value text)
        if self.focused and (time.monotonic() % (2 * CARET_BLINK)
                             < CARET_BLINK):
            cx = rect.x + pad + (
                font.size(self.value)[0] if self.value else 0) + 2
            ch = int(rect.h * 0.6)
            cy = rect.y + (rect.h - ch) // 2
            pygame.draw.line(surface, COL_CARET,
                             (cx, cy), (cx, cy + ch), 2)
