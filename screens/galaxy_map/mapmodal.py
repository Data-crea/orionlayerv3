"""The modals the engine shows over the galaxy map — work order 177.

The inventory is `dev:doc/briefs/177-progress.md` part A. The map reports
screen 0 through all of them; what tells them apart is the FIELD LIST
(`classify`), and the rule of the screen is:

  own list          the map's grid field and zoom-out button (the map)
  HOME STAR NAME    drawn here: the popup, the prompt, the name being
                    typed, ACCEPT (#1)
  CONFIRMATION      drawn here: the game's own box pixels (their text is
                    not on the wire, open fix 29) in a HUD popup, YES / NO
                    (#4, #5, #6, #12)
  anything else     the safety net (`core/modalnet`): the game's own
                    picture, clicks and keys passed through, one log line

THE HOME STAR NAME — TRANSCRIPTION of `Input_Box_Popup_` (namestar.cpp:
236-395) and the continuous input field (fields.cpp:1171-1227):

  prompt      HESTR 0x101 "Enter Home Star Name" (namestar.cpp:157-160)
  the name    prefilled with the home star's (`home_planet_id` → planet →
              star, the map's own `home_star()`); at most 14 characters
  typing      a printable key but '_' APPENDS; the FIRST Backspace clears
              the whole prefilled name, later ones delete one character;
              each key is sent to the game as INJECT_KEY with its ASCII
              code (platform.cpp:412-500)
  ACCEPT      Enter — also the ACCEPT button, which sends Enter and NOT
              ACTIVATE_FIELD: an activation returns before
              `Copy_Continuous_String_` and the typed name would be lost
              (fields.cpp:172-183)
  ESC         the game restores the old name (namestar.cpp:369-373)

**HD STATE `typed_name_mirror`.** The text being typed is not on the wire
(`_continuous_string`): HD keeps its own copy by the field's own rules and
shows it; the game's result — `star.name` — arrives with the next snapshot
once accepted. The game also refuses a character that would not fit the
field's pixel width, which HD cannot measure in the game's font; the
mirror may then show a character the game dropped, until the accept.
"""
import logging

import pygame

from core import gamebox, hestrings
from core.hud import blocks as hud
from core.hud import text as hudtext

log = logging.getLogger("galaxy_map")

HOME_STAR_BUTTON = (227, 246, 324, 273)      # namestar.cpp:96-103
HOME_STAR_INPUT_AT = (165, 200)              # namestar.cpp:118-129
TYPE_BUTTON, TYPE_INPUT = 0, 11
MAX_CHARS = 14                               # 15-byte buffer (namestar.cpp:262)
H_HOME_STAR = 0x101
KEY_BACKSPACE, KEY_ENTER, KEY_ESC = 8, 13, 27


def live(fields):
    return [f for f in (fields or []) if f.index != 0]


def is_home_star(fields):
    rest = live(fields)
    if len(rest) != 2:
        return False
    button = next((f for f in rest if f.field_type == TYPE_BUTTON), None)
    entry = next((f for f in rest if f.field_type == TYPE_INPUT), None)
    return (button is not None and entry is not None and
            (button.x, button.y, button.x_end, button.y_end) ==
            HOME_STAR_BUTTON and (entry.x, entry.y) == HOME_STAR_INPUT_AT)


def is_confirmation(fields):
    box = gamebox.detect(fields)
    return box is not None and box.name == "confirmation"


class Modal:
    """The galaxy map's modal state, one per screen."""

    def __init__(self, screen):
        self.screen = screen
        self.kind = None             # None, "home_star", "confirmation"
        self.text = ""
        self.fresh = True            # the prefilled name, untouched
        self._rects = {}
        # The snapshot `update` was handed — the modal's fields and the
        # box's pixels; never the client's own snapshot (the map's one adoption
        # point, smoke check 088).
        self._state = None
        from core import modalnet
        self.net = modalnet.Net(
            "galaxy map", screen.owns_field_list,
            known=(("home_star", is_home_star),
                   ("confirmation", is_confirmation)))
        self.fallback = False

    # ── state ─────────────────────────────────────────────
    def update(self, state):
        self._state = state
        fields = getattr(state, "fields", None)
        on_map = getattr(state, "current_screen", -1) == 0
        kind = None
        if on_map and is_home_star(fields):
            kind = "home_star"
        elif on_map and is_confirmation(fields):
            kind = "confirmation"
        if kind == "home_star" and self.kind != "home_star":
            star = self.screen.home_star()
            self.text = (star.name if star is not None else "")[:MAX_CHARS]
            self.fresh = True
            log.info("galaxy map: the home star name dialog (prefilled %r)",
                     self.text)
        self.kind = kind
        self.fallback = self.net.check(state, 0)

    @property
    def active(self):
        return self.kind is not None

    # ── drawing ───────────────────────────────────────────
    def render(self, surface):
        self._rects = {}
        if self.kind == "home_star":
            self._render_home_star(surface)
        elif self.kind == "confirmation":
            self._render_confirmation(surface)

    def _popup_rect(self, w_ref, h_ref):
        L = self.screen.layout
        w, h = int(w_ref * L.scale), int(h_ref * L.scale)
        win = surface_size(self.screen)
        return pygame.Rect((win[0] - w) // 2, (win[1] - h) // 2, w, h)

    def _render_home_star(self, surface):
        s = self.screen
        L = s.layout
        box = self._popup_rect(760, 330)
        hud.popup(surface, box, L.scale)
        inner = hud.panel_inner(box, L.scale).inflate(-int(24 * L.scale), 0)
        prompt = hestrings.for_app(s.app).message(H_HOME_STAR) or ""
        size = max(12, int(34 * L.scale))
        _text(surface, s, prompt, pygame.Rect(inner.x, inner.y + int(
            16 * L.scale), inner.w, size), size, hudtext.colour("title"))
        field = pygame.Rect(inner.x + int(60 * L.scale), inner.y + int(
            100 * L.scale), inner.w - int(120 * L.scale), int(64 * L.scale))
        hud.panel(surface, field, L.scale, dense=True)
        tsize = max(12, int(34 * L.scale))
        img = s.style.render_text(self.text or " ", tsize,
                                  hudtext.colour("button"))
        tx = field.x + int(18 * L.scale)
        ty = field.centery - img.get_height() // 2
        surface.blit(img, (tx, ty))
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            cx = tx + (img.get_width() if self.text else 0) + 2
            # A filled bar, not a map line: the map's one line routine
            # (maplines.py) is for the map's lines only.
            surface.fill(hudtext.colour("button"), pygame.Rect(
                cx, ty, max(2, int(3 * L.scale)), img.get_height()))
        btn = pygame.Rect(0, 0, int(240 * L.scale), int(64 * L.scale))
        btn.midbottom = (box.centerx, box.bottom - int(34 * L.scale))
        hud.action_button(surface, btn, L.scale, "normal")
        _text(surface, s, "ACCEPT", btn, max(12, int(30 * L.scale)),
              hudtext.colour("button"))
        self._rects["accept"] = btn

    def _render_confirmation(self, surface):
        """The game's own confirmation pixels (open fix 29: the text is not
        on the wire) in a HUD popup, YES / NO over its own buttons —
        `screens/fleets/fltbox`'s placement, the Leaders screen's way."""
        from screens.fleets import fltbox
        s = self.screen
        state = self._state
        box = gamebox.detect(getattr(state, "fields", None))
        if box is None:
            return
        view = _BoxView(box)
        s._view = view
        try:
            scale, dest = fltbox.placement(s, box)
            if not fltbox.SHOW_CROP:
                # Work order 188, Stage 1: the F12 notice, never the crop.
                fltbox.draw_notice(surface, s, box.name, dest)
                return
            pad = max(2, int(round(10 * s.layout.scale)))
            hud.popup(surface, dest.inflate(2 * pad, 2 * pad), s.layout.scale)
            piece = gamebox.crop(fltbox._framebuffer_surface(state), box.rect)
            if piece is not None:
                surface.blit(pygame.transform.scale(piece, dest.size),
                             dest.topleft)
            for key, field, rect in fltbox.button_rects(s):
                self._rects[key] = (rect, field)
        finally:
            s._view = None

    # ── input ─────────────────────────────────────────────
    def click(self, x, y):
        """True when the click belonged to the modal (always, while one is
        up: the map under it must not answer)."""
        client = self.screen.app.client
        if self.kind == "home_star":
            if "accept" in self._rects and self._rects["accept"].collidepoint(
                    x, y) and self.screen.app.connected:
                log.info("galaxy map: home star name ACCEPT (Enter) %r",
                         self.text)
                client.inject_key(KEY_ENTER)
            return True
        if self.kind == "confirmation":
            for key, (rect, field) in self._rects.items():
                if rect.collidepoint(x, y) and self.screen.app.connected:
                    log.info("galaxy map: confirmation %s -> field %d", key,
                             field.index)
                    client.activate_field(field.index)
            return True
        return False

    def key_event(self, event):
        """True when the key belonged to the modal."""
        if self.kind == "confirmation":
            ch = (getattr(event, "unicode", "") or "").upper()
            for key, (rect, field) in self._rects.items():
                if ch and ord(ch) == field.hotkey and self.screen.app.connected:
                    self.screen.app.client.activate_field(field.index)
            return True
        if self.kind != "home_star":
            return False
        code = edit(self, event)
        if code is not None and self.screen.app.connected:
            self.screen.app.client.inject_key(code)
        return True


def edit(modal, event):
    """Apply one key to the mirror by the field's own rules; returns the
    code to send (or None). fields.cpp:1171-1227."""
    if event.key == pygame.K_BACKSPACE:
        modal.text = "" if modal.fresh else modal.text[:-1]
        modal.fresh = False
        return KEY_BACKSPACE
    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return KEY_ENTER
    if event.key == pygame.K_ESCAPE:
        return KEY_ESC
    ch = getattr(event, "unicode", "") or ""
    if len(ch) == 1 and 32 <= ord(ch) < 127 and ch != "_":
        if len(modal.text) < MAX_CHARS:
            modal.text += ch
        modal.fresh = False
        return ord(ch)
    return None


class _BoxView:
    """What `fltbox` asks of a screen's view: the box and `in_box`."""

    def __init__(self, box):
        self.box, self.in_box = box, True


def surface_size(screen):
    return (screen.app.win_w, screen.app.win_h)


def _text(surface, screen, text, rect, size, colour):
    style = screen.style
    while size > 10 and style.render_text(text, size, colour).get_width() \
            > rect.w:
        size -= 1
    img = style.render_text(text, size, colour)
    surface.blit(img, img.get_rect(center=rect.center))
