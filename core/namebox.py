"""The game's name box — open fix 87, "INBX" (work order 230 D).

    "INBX"  (`doc/ext_name_box.patch`): written after FBTN's place on any
            screen while `namestar::Input_Box_Popup_` runs. A version byte;
            int16 x, y (the box's corner); the input field as fix 51 writes
            one — int16 field, uint8 max characters, s8 the name the box
            was opened with, uint8 editing, s8 the typed text only while
            editing; int16 the button; s8 the prompt; uint8 animated.

WHAT IT IS. "Enter Star Name" after the first colony at a star
(`Change_Star_Name_Popup_`: the landing, colland.cpp:250; the colony
choice with animations off, mainpups.cpp:809, report.cpp:185, :207), the
home star's and the network game's name — one function, namestar.cpp:300-
405. It stands under no screen id of its own (the landing's 33, the map's 0)
and until fix 87 neither its prompt nor the name it opened with was on the
wire, so HD showed the F12 notice (work order 229's "Enter Star Name").

  TRANSCRIPTION  the prompt and the name: the engine's own (HESTR 0x100,
                 0x101); the text shown is the game's typed text
                 (`fields::_continuous_string`), not a copy HD keeps
  TRANSCRIPTION  the answers (namestar.cpp:355-381; fields.cpp:1057-1068,
                 :1180-1240): Enter commits — the box's button too, which
                 sends Enter and not ACTIVATE_FIELD (an activation returns
                 before the string is copied, fields.cpp:172-183); ESC
                 restores the old name; a printable key but '_' and
                 Backspace go to the game as they are
  DEVIATION      `name_box_hud`: the original's INBOX.LBX picture; HD draws
                 the message box's HUD popup with the prompt, the field and
                 ACCEPT (decision 71)

The galaxy map's own home star modal (`screens/galaxy_map/mapmodal.py`,
work order 177) keeps the home star's box; this overlay takes every other.
"""
import logging
import struct as _st

import pygame

from core import lang, textfields
from core.hud import blocks as hud
from core.hud import text as hudtext

log = logging.getLogger("orionlayer")

KEY_BACKSPACE, KEY_ENTER, KEY_ESC = 8, 13, 27


def parse(gs, data, pos):
    """Read INBX at `pos` into `gs.name_box` (None when absent or short).
    Returns the new position."""
    gs.name_box = None
    if data[pos:pos + 4] != b"INBX":
        return pos
    try:
        version, x, y = _st.unpack_from("<Bhh", data, pos + 4)
        if version != 1:
            return pos
        entry, at = textfields.input_field(data, pos + 4 + 5)
        (button,) = _st.unpack_from("<h", data, at)
        prompt, at = textfields.s8(data, at + 2)
        if at >= len(data):
            return pos
        animated = data[at]
        at += 1
    except (ValueError, IndexError, _st.error):
        return pos
    gs.name_box = {"x": x, "y": y, "field": entry["field"],
                   "max": entry["max"], "text": entry["text"],
                   "editing": entry["editing"], "typed": entry["typed"],
                   "button": button, "prompt": prompt,
                   "animated": bool(animated)}
    return at


def build(x, y, field, limit, text, typed, button, prompt, animated=0):
    """The block as the engine writes it — for the checks' stand-ins."""
    def s8(s):
        raw = s.encode("latin-1")
        return bytes([len(raw)]) + raw
    out = b"INBX" + _st.pack("<BhhhB", 1, x, y, field, limit) + s8(text)
    out += bytes([1]) + s8(typed) if typed is not None else bytes([0])
    return out + _st.pack("<h", button) + s8(prompt) + bytes([animated])


def shown(box):
    """The name the box shows: what is typed, else what it opened with.
    The typed text carries the game's own cursor, a trailing '_' (fix 51's
    note: the commit strips it; '_' cannot be typed, fields.cpp:1210-1238)."""
    return textfields.typed_text(box)


def key_code(event):
    """The code a key sends into the box, or None (the field's own rules:
    fields.cpp:1180-1240; '_' is refused there, so it is not sent)."""
    if event.key == pygame.K_BACKSPACE:
        return KEY_BACKSPACE
    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return KEY_ENTER
    if event.key == pygame.K_ESCAPE:
        return KEY_ESC
    ch = getattr(event, "unicode", "") or ""
    if len(ch) == 1 and 32 <= ord(ch) < 127 and ch != "_":
        return ord(ch)
    return None


class View:
    """The name box over the held frame: drawing and input."""

    def __init__(self):
        self.rects = {}
        self.panel = None

    def reset(self):
        self.rects = {}
        self.panel = None

    def render(self, surface, style, labels, box, scale):
        w, h = surface.get_size()
        pw, ph = int(760 * scale), int(330 * scale)
        panel = pygame.Rect((w - pw) // 2, (h - ph) // 2, pw, ph)
        hud.popup(surface, panel, scale)
        inner = hud.panel_inner(panel, scale).inflate(-int(24 * scale), 0)
        size = max(12, int(34 * scale))
        _text(surface, style, box["prompt"], pygame.Rect(
            inner.x, inner.y + int(16 * scale), inner.w, size), size,
            hudtext.colour("title"))
        field = pygame.Rect(inner.x + int(60 * scale), inner.y + int(
            100 * scale), inner.w - int(120 * scale), int(64 * scale))
        hud.panel(surface, field, scale, dense=True)
        name = shown(box)
        img = style.render_text(name or " ", size, hudtext.colour("button"))
        tx = field.x + int(18 * scale)
        ty = field.centery - img.get_height() // 2
        surface.blit(img, (tx, ty))
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            cx = tx + (img.get_width() if name else 0) + 2
            # the field's cursor: a bar in the word colour
            surface.fill(hudtext.colour("button"), pygame.Rect(
                cx, ty, max(2, int(3 * scale)), img.get_height()))
        btn = pygame.Rect(0, 0, int(240 * scale), int(64 * scale))
        btn.midbottom = (panel.centerx, panel.bottom - int(34 * scale))
        hud.action_button(surface, btn, scale, "normal")
        _text(surface, style, lang.tr(labels.get("accept", "ACCEPT")), btn,
              max(12, int(30 * scale)), hudtext.colour("button"))
        self.rects = {"accept": btn}
        self.panel = panel
        return panel

    def click_code(self, x, y):
        """The code a click sends: ACCEPT is Enter (see the module)."""
        rect = self.rects.get("accept")
        return KEY_ENTER if rect is not None and rect.collidepoint(x, y) \
            else None


def _text(surface, style, text, rect, size, colour):
    while size > 10 and style.render_text(text, size, colour).get_width() \
            > rect.w:
        size -= 1
    img = style.render_text(text, size, colour)
    surface.blit(img, img.get_rect(center=rect.center))
