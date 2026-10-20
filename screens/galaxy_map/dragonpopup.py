"""The Space Dragon's star choice over the map — work order 319, on open fix
108's TPOP kind 24 (id 84), mode 1.

When the Space Dragon reaches a colony of a human player the original asks
for a bribe (`MAINPUPS::Dragon_New_Star_Popup_`, mainpups.cpp:493-543,
from combfind.cpp:157). The offer (mode 0) and "too poor" (mode 2) are the
turn popups' panel (`core/turnpopupcontent.py`, TRANSCRIPTION
`dragon_bribe`); this module is mode 1, after YES was paid for: E 464 asks
the player to choose the star the dragon goes to, and a click on a star's
field of the popup's own galaxy map ends the popup with that star
(`Evaluate_Dragon_New_Star_Input_`, :2611-2660; the BC are taken by
`COMBFIND::Do_Dragon_Bribe_`, combfind.cpp:521).

TRANSCRIPTION `dragon_bribe` — what a click does: the star's own field is
activated, the
one the engine's tail names for that star (`core.dragonwire.star_field`,
resolved in the list just read by its index, type and rectangle, P816);
the dragon's own star is sent as well, and the engine answers it with its
help box (E 576, :2647), drawn as HD's message box. Mode 1 keeps
mp_fields[2] (CLOSE, ESC): -1, no bribe, the battle goes on.

DEVIATION `dragon_star_on_map`: the original's star choice is a galaxy map
of its own inside the popup (`MOVEBOX::Draw_Galaxy_Map_Box_` at (302, 156)
148 x 94, one 5 x 5 field per star, mainpups.cpp:2155-2167, :2592); HD
shows no second map — the HD map under the popup is the map, its own star
hit test (`GalaxyMapScreen._star_at`, `Check_Stars_XY_`'s radius) picks the
star, and the panel is one row — the message, then CLOSE — just above the
nav bar, not dimmed, so the map stays clear. A star under the strip, under the HUD (the nav bar, the
sidebar, the title plate: a click there reaches no star, `on_hud`), or
outside the HD map's view as it stands, cannot be chosen (the popup takes
the map's input, so the view does not move while it is up). The star click
is offered only where the backdrop drew this game's galaxy map
(`core.turnpopup.View._render_dragon`).
UNVERIFIED `dragon_bribe_live`: drawn from stand-in bytes only, not yet
from the engine (Data's decision of 20 October 2026: no live runs).
OMISSION `dragon_scanned_name`: the original prints the hovered star's name
under its map (`fonts::Print_Centered_(376, 254, …)`, :2606-2607); HD's map
names its stars itself.
"""
import pygame

from core import dragonwire, lang, turnpopup
from core.hud import blocks as hud
from core.hud import text as hudtext

#: The gap between the strip and the nav bar (or the window's bottom edge
#: where the bar is not laid out), in reference px of 1080 — HD's choice.
REF_GAP = 12


def render(host, surface, style, c, popup, state):
    """Draw the strip and return `(rects, buttons, point)`: its rects (the
    strip itself first, taking no click, so a click on its text reaches no
    star under it, then CLOSE), its buttons' actions, and `point(x, y)` ->
    the star field's action, or None. Without the map (`host` None) no star
    can be clicked."""
    win_w, win_h = surface.get_size()
    s = win_h / 1080
    pad = int(turnpopup.REF_PAD * s)
    w = min(int(turnpopup.REF_W * s), win_w - 2 * pad)
    size = max(10, int(turnpopup.REF_FONT * s))
    colour = hudtext.colour("value")
    bw, bh = int(turnpopup.REF_BUTTON[0] * s), int(turnpopup.REF_BUTTON[1] * s)
    text_w = w - 3 * pad - bw
    with lang.verbatim():                 # the engine's own message
        rows = [r for r in turnpopup._wrap(style, " ".join(c["lines"]), size,
                                           text_w, colour) if r is not None]
    step = int(size * 1.3)
    h = max(bh, len(rows) * step) + pad
    bar = None
    if host is not None:
        from screens.galaxy_map import hudview
        bar = hudview.nav_rect(host, "turn")
    bottom = (bar.top if bar is not None else win_h) - int(REF_GAP * s)
    strip = pygame.Rect((win_w - w) // 2, bottom - h, w, h)
    hud.popup(surface, strip, s)
    y = strip.y + (h - len(rows) * step) // 2
    for r in rows:
        surface.blit(r, (strip.x + pad, y))
        y += step
    rects, buttons = [(strip.copy(), None)], []
    for label, action in c["buttons"]:
        r = pygame.Rect(strip.right - pad - bw, strip.y + (h - bh) // 2,
                        bw, bh)
        hud.action_button(surface, r, s,
                          "normal" if action is not None else "disabled",
                          label, style_renderer=style)
        rects.append((r, action))
        buttons.append(action)

    def point(x, y):
        return star_action(host, popup, state, x, y)
    return rects, buttons, point


def star_action(host, popup, state, x, y):
    """The action a click at HD point (x, y) answers in mode 1: the star
    the HD map finds there, through its own field — or None."""
    if host is None or on_hud(host, x, y):
        return None
    star = host._star_at(x, y)
    if star is None:
        return None
    stars = getattr(host, "_stars", None) or []
    index = next((i for i, st in enumerate(stars) if st is star), None)
    if index is None:
        return None
    field = dragonwire.star_field(popup, state, index)
    return ("activate", field) if field is not None else None


#: The HUD's boxes over the map: a click on one is the HUD's, never a star's.
HUD_BOXES = ("sidebar", "nav_turn", "nav_colonies", "nav_planets",
             "nav_fleets", "nav_leaders", "nav_races", "nav_info")


def on_hud(host, x, y):
    """True when (x, y) lies on the map's HUD — the sidebar, a nav button,
    the title plate — which stands over stars the view may place there."""
    from screens.galaxy_map import hudview
    for name in HUD_BOXES:
        r = host.box_screen_rect(name)
        if r is None and host.box_rect(name):      # boxes not laid out
            r = pygame.Rect(*host.layout.rect(host.box_rect(name)))
        if r is not None and r.collidepoint(x, y):
            return True
    title = hudview.title_rect(host)
    return title is not None and pygame.Rect(title).collidepoint(x, y)
