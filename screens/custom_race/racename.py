"""The race's name on Custom Race — work order 230 E (228 E: "Custom Race
has no name field").

The original's screen has one (raceopt.cpp:1157-1167): a continuous input
field at native (0xF8, 0x0F), 0x96 wide, 15 characters, its buffer
`raceopt::_cur_race_name`, filled from the player's race name when the
screen opens (racesel.cpp:482) and written back into the player when the
race is finally taken (:708).

  TRANSCRIPTION  the name shown is the field's buffer, or the typed text
                 while it is edited — open fix 88's TXTF, the game's own
                 values, nothing HD keeps
  TRANSCRIPTION  it opens only by a click (fields.cpp:1076-1105, F904): a
                 click on HD's field is an injected click at the engine
                 field's centre; then keys go into it by the one rule every
                 screen shares (`core/keyfwd.py`): printable but '_',
                 Backspace, Enter stores, ESC restores
  DEVIATION      `race_name_place`: the original's field stands above the
                 picks; HD's is at the foot of the description column
                 (`boxes.json` `race_name_field`), labelled (decision 15:
                 `layout.json` would hold no words here, so `traits.json`
                 `messages.race_name` carries the label)
"""
import logging

import pygame

from core import keyfwd, textfields
from core.hud import blocks as hud
from core.hud import text as hudtext

log = logging.getLogger("custom_race")

TYPE_CONTINUOUS_INPUT = 11
LABEL = "Race Name"


def live_field(state):
    """The engine's name field in the live list (the screen's only
    continuous input field), or None."""
    return next((f for f in (getattr(state, "fields", None) or [])
                 if getattr(f, "field_type", None) == TYPE_CONTINUOUS_INPUT
                 and getattr(f, "index", 0)), None)


def entry(state):
    """TXTF's entry for the name field, or None."""
    f = live_field(state)
    if f is None:
        return None
    return (getattr(state, "text_fields", None) or {}).get(f.index)


def rects(screen):
    lab, fld = screen.box_rect("race_name_label"), \
        screen.box_rect("race_name_field")
    if not lab or not fld:
        return None, None
    return (pygame.Rect(*screen.layout.rect(lab)),
            pygame.Rect(*screen.layout.rect(fld)))


def render(screen, surface, label):
    lab, fld = rects(screen)
    if fld is None:
        return
    L = screen.layout
    st = getattr(screen.app.client, "state", None) if \
        getattr(screen.app, "client", None) is not None else None
    e = entry(st) if st is not None else None
    size = L.font_size(18)
    img = screen.style.render_text(label, size, hudtext.colour("label"))
    surface.blit(img, (lab.x, lab.y + (lab.h - img.get_height()) // 2))
    hud.field(surface, fld, L.scale)
    name = textfields.typed_text(e) if e is not None else ""
    img = screen.style.render_text(name or " ", L.font_size(22),
                                   hudtext.colour("button"))
    tx = fld.x + int(12 * L.scale)
    surface.blit(img, (tx, fld.centery - img.get_height() // 2))
    if e is not None and e["editing"] and \
            (pygame.time.get_ticks() // 500) % 2 == 0:
        cx = tx + (img.get_width() if name else 0) + 2
        # the field's cursor while it is edited: a bar in the word colour
        surface.fill(hudtext.colour("button"), pygame.Rect(
            cx, fld.centery - img.get_height() // 2, max(2, int(3 * L.scale)),
            img.get_height()))


def click(screen, x, y):
    """True when the click was on HD's name field (sent or not)."""
    _lab, fld = rects(screen)
    if fld is None or not fld.collidepoint(x, y):
        return False
    st = getattr(screen.app.client, "state", None)
    f = live_field(st)
    if f is not None and screen.app.connected and \
            not (entry(st) or {}).get("editing"):
        cx = f.x + (f.x_end - f.x) // 2
        cy = f.y + (f.y_end - f.y) // 2
        log.info("race name: click (%d, %d), field %d — opens it", cx, cy,
                 f.index)
        screen.app.client.inject_click(cx, cy)
    return True


def editing(screen):
    st = getattr(screen.app.client, "state", None) if \
        getattr(screen.app, "client", None) is not None else None
    return keyfwd.editing(st) is not None
