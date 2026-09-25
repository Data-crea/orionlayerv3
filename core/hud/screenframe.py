"""The HUD's title plate and frame buttons on a `USE_FRAME` screen.

Decision 71 (work order 169). The pre-game screens — New Game, Select
Race, Custom Race, Empire Identity — wore the skin's 9-slice frame, and
the frame carried their title and their CANCEL / ACCEPT bars. The frame
is no longer drawn; these three things are HUD blocks now, in the places
the frame's own title bar and button bars had (`chosen.frame_buttons`),
so no screen's content had to move.

`ScreenBase` keeps the hooks (decision 13: the click is handled there)
and hands the drawing and the geometry to this module. One function says
where a button is — `button_rect` — and both the drawing and the hit
read it (decision 5).
"""
import time

import pygame

from core import mouse as mouse_input
from core.config import REF_W
from core.hud import blocks as hud
from core.hud import style as hudstyle

#: How long a pressed frame button stays drawn active, in seconds —
#: `ScreenBase.BTN_FLASH_DURATION`'s value, the press feedback the old
#: frame buttons flashed for.
ACTIVE_FOR = 0.30


def render(screen, surface):
    L = screen.layout
    # From the window's top edge (work order 170).
    hud.title_plate(surface, L.offset_x + REF_W * L.scale / 2, 0,
                    L.scale, screen.FRAME_TITLE, screen.style)
    for side in ("left", "right"):
        _button(screen, surface, side)


def button_rect(screen, side):
    """The device rect of frame button `side`, or None when the screen
    has none."""
    spec = screen.FRAME_BTN_LEFT if side == "left" else screen.FRAME_BTN_RIGHT
    if not spec:
        return None
    ref = hudstyle.get().get(f"frame_buttons.{side}")
    if not getattr(screen, "FRAME_BTN_AT_BOTTOM", True):
        return pygame.Rect(*screen.layout.rect(ref))
    # ON THE WINDOW'S BOTTOM EDGE (work order 170), the HUD's own
    # screen-edge margin above it, as the galaxy map's bar: the old
    # frame's button bars left a band under them once the frame went.
    x, _y, w, h = ref
    margin = hudstyle.get().get("galaxy.edge_margin")
    L = screen.layout
    sy, sh = L.vertical(1080 - margin - h, h, "bottom")
    return pygame.Rect(int(x * L.scale + L.offset_x), sy,
                       int(w * L.scale), sh)


def hit(screen, side, x, y):
    """The right button is the action button (a chamfered rect), the left
    a slanted one; each is hit as the shape it is drawn as."""
    r = button_rect(screen, side)
    if r is None:
        return False
    return r.collidepoint(x, y) if side == "right" else hud.slant_hit(r, x, y)


def side_at(screen, x, y):
    for side in ("left", "right"):
        if hit(screen, side, x, y):
            return side
    return None


def _button(screen, surface, side):
    r = button_rect(screen, side)
    if r is None:
        return
    label = (screen.FRAME_BTN_LEFT if side == "left"
             else screen.FRAME_BTN_RIGHT)[0]
    state = "normal"
    flash = screen._btn_flash
    if flash and flash[0] == side:
        if time.monotonic() - flash[1] < ACTIVE_FOR:
            state = "active"
        else:
            screen._btn_flash = None
    if state == "normal" and hit(screen, side, *mouse_input.pos()):
        state = "hover"
    draw = hud.action_button if side == "right" else hud.slant_button
    draw(surface, r, screen.layout.scale, state, label,
         style_renderer=screen.style)
