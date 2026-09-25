"""The Fleets screen's HUD blocks (decision 71, work order 169).

Split from `fltdraw` so that module stays under the line guideline: this
draws the panels and the button blocks UNDER the screen's content;
`fltdraw` draws the content — the slots, the cells, the words — as
before.
"""
from core import mouse as mouse_input
from core.hud import blocks as hud

from .fltdraw import CONTROL_WORDS, _rect


#: The windows that are HUD panels since decision 71 (work order 169),
#: in the order they are drawn: the map, the ship panel, the ship grid,
#: the strip with PREV/NEXT, and the button band.
HUD_PANELS = ("inset_map", "ship_panel", "icon_area", "status_band",
              "button_band")


def draw_hud(surface, screen, enabled=None, filters=None):
    """The Fleets screen's HUD, under its content (decision 71): a panel
    per window and the HUD's small button behind each of the nine
    controls — lit ("active") while its filter is on, dim ("disabled")
    while the control is not live, lit on hover. The words are drawn by
    `draw_labels`, as before."""
    scale = screen.layout.scale
    for name in HUD_PANELS:
        rect = _rect(screen, name)
        if rect is not None:
            hud.panel(surface, rect, scale)
    mouse = mouse_input.pos()
    for name, _key in CONTROL_WORDS:
        rect = _rect(screen, name)
        if rect is None:
            continue
        if (filters or {}).get(name):
            state = "active"
        elif enabled is not None and name not in enabled:
            state = "disabled"
        elif rect.collidepoint(mouse):
            state = "hover"
        else:
            state = "normal"
        hud.small_button(surface, rect, scale, state)
