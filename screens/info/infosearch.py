"""The Tech Review's search row — a one-line text field for a screen that
draws only on input (`STILL`): its cursor stands still, so nothing here
moves with time (`core/widgets/text_input.py` blinks and is therefore not
used on a STILL screen, check 006q). The extension's marking is in
`screen.py` (`tech_review_search`).
"""
import pygame

from . import infobox


class SearchField:
    def __init__(self, max_len=24, on_leave=None):
        self.value, self.placeholder = "", ""
        self.max_len, self.on_leave = max_len, on_leave
        self.focused = False
        self._rect = pygame.Rect(0, 0, 0, 0)

    def handle_click(self, x, y):
        """Focus when the click is inside, leave when it is outside;
        True when it hit the field."""
        self.focused = self._rect.collidepoint(x, y)
        return self.focused

    def handle_key_event(self, event):
        if not self.focused or event.type != pygame.KEYDOWN:
            return False
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                         pygame.K_ESCAPE):
            self.focused = False
            if self.on_leave:
                self.on_leave()
        elif event.key == pygame.K_BACKSPACE:
            self.value = self.value[:-1]
        else:
            ch = getattr(event, "unicode", "")
            if ch and len(ch) == 1 and ch.isprintable() and \
                    len(self.value) < self.max_len:
                self.value += ch
        return True

    def render(self, surface, screen, rect):
        """The field as the screen's other boxes (`infodraw.field`), the
        text and the standing cursor in the list's tones."""
        from . import infodraw
        self._rect = pygame.Rect(rect)
        infodraw.hud.field(surface, self._rect, screen.layout.scale,
                           on=self.focused)
        inner = self._rect.inflate(-int(self._rect.h * 0.6), 0)
        shown = self.value + ("|" if self.focused else "")
        typed = bool(self.value or self.focused)
        infobox.line(surface, screen, shown if typed else self.placeholder,
                     inner, infodraw.px(screen, "skill"),
                     infodraw.HIGH if typed else infodraw.NORMAL)
