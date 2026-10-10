"""The tax rate popup — work order 230 D (a dialog only F12 answered).

What the original does (mainscr.cpp:2385-2425, mainpups.cpp:207-262):
the sidebar's treasury window (`_treasury_window_field`, mainscr.cpp:1401;
mainscr_main.cpp:733-748) clears the map's fields and runs
`Tax_Rate_Popup_` under SCREEN_MAIN. Its fields (`Add_Tax_Rate_Fields_`):

  TRANSCRIPTION  six multi buttons at native y 0xC6, x 0x93, 0xC1, 0xEA,
                 0x113, 0x13C, 0x165 — 0 to 50 %, each sets
                 `_g_temp_tax_rate`; every input but ACCEPT applies it at
                 once (`player.tax_rate`, the colonies recalculated,
                 `Evaluate_Tax_Rate_Input_`, :250-262); hotkeys 0-5
  TRANSCRIPTION  ACCEPT, a button at (0xED, 0xFE), hotkey ESC: applies and
                 closes
  TRANSCRIPTION  which rate is on: `player.tax_rate` off the wire (the
                 popup starts from it, mainscr.cpp:2402)
  DEVIATION      `tax_popup_hud`: the original's TAXRATE pictures (the
                 popup, the six rate buttons, ACCEPT: artwork, no string);
                 HD draws the HUD popup, its small buttons and the words of
                 `layout.json` `tax_rate` (decision 15)

A rate button is a multi button, which the engine resolves through the
pointer (fields.cpp, a radio's rule): HD sends an injected click at its
centre, not ACTIVATE. ACCEPT is a button whose id the loop compares: it is
activated.
"""
import logging

import pygame

from core import lang
from core.hud import blocks as hud
from core.hud import text as hudtext
from core.structs import player as player_struct

log = logging.getLogger("galaxy_map")

RATE_Y = 0xC6
RATE_X = (0x93, 0xC1, 0xEA, 0x113, 0x13C, 0x165)
RATES = (0, 10, 20, 30, 40, 50)
ACCEPT_AT = (0xED, 0xFE)
TYPE_BUTTON, TYPE_MULTI = 0, 3


def live(fields):
    return [f for f in (fields or []) if f.index != 0]


def fields_of(fields):
    """{"rates": [field per rate, in RATES order], "accept": field} when the
    list is the tax rate popup's, else None."""
    rest = live(fields)
    if len(rest) != 7:
        return None
    accept = next((f for f in rest if f.field_type == TYPE_BUTTON and
                   (f.x, f.y) == ACCEPT_AT), None)
    rates = []
    for x in RATE_X:
        f = next((f for f in rest if f.field_type == TYPE_MULTI and
                  (f.x, f.y) == (x, RATE_Y)), None)
        rates.append(f)
    if accept is None or None in rates:
        return None
    return {"rates": rates, "accept": accept}


def is_tax_rate(fields):
    return fields_of(fields) is not None


def current_rate(state):
    raws = getattr(state, "player_raw", None) or []
    n = getattr(state, "player_num", 0)
    if not 0 <= n < len(raws):
        return None
    return int(player_struct.parse(raws[n]).tax_rate)


def words(screen):
    data = (screen._data.get("tax_rate") or {})
    return (lang.tr(data.get("title", "Set Tax Rate")),
            [lang.tr(w) for w in data.get("rates", [f"{r}%" for r in RATES])],
            lang.tr(data.get("accept", "ACCEPT")))


def render(screen, surface, state, rects):
    """The popup over the map; fills `rects` with key -> (rect, action)."""
    L = screen.layout
    s = L.scale
    win = (screen.app.win_w, screen.app.win_h)
    box = pygame.Rect(0, 0, int(760 * s), int(300 * s))
    box.center = (win[0] // 2, win[1] // 2)
    hud.popup(surface, box, s)
    title, labels, accept = words(screen)
    size = max(12, int(34 * s))
    img = screen.style.render_text(title, size, hudtext.colour("title"))
    surface.blit(img, img.get_rect(midtop=(box.centerx,
                                           box.y + int(22 * s))))
    on = current_rate(state)
    fl = fields_of(getattr(state, "fields", None)) or {}
    bw, bh, gap = int(100 * s), int(56 * s), int(12 * s)
    x0 = box.centerx - (6 * bw + 5 * gap) // 2
    y = box.y + int(100 * s)
    for k, rate in enumerate(RATES):
        r = pygame.Rect(x0 + k * (bw + gap), y, bw, bh)
        hud.small_button(surface, r, s, "active" if rate == on else "normal",
                         labels[k], style_renderer=screen.style)
        if fl:
            rects[f"rate_{rate}"] = (r, ("click", fl["rates"][k]))
    btn = pygame.Rect(0, 0, int(240 * s), int(60 * s))
    btn.midbottom = (box.centerx, box.bottom - int(26 * s))
    hud.action_button(surface, btn, s, "normal")
    img = screen.style.render_text(accept, max(12, int(30 * s)),
                                   hudtext.colour("button"))
    surface.blit(img, img.get_rect(center=btn.center))
    if fl:
        rects["accept"] = (btn, ("activate", fl["accept"]))


def send(screen, action, what):
    how, field = action
    client = screen.app.client
    if not screen.app.connected:
        return
    if how == "click":
        cx = field.x + (field.x_end - field.x) // 2
        cy = field.y + (field.y_end - field.y) // 2
        log.info("tax rate: %s -> click (%d, %d), field %d", what, cx, cy,
                 field.index)
        client.inject_click(cx, cy)
    else:
        log.info("tax rate: %s -> field %d", what, field.index)
        client.activate_field(field.index)


def click(screen, rects, x, y):
    for key, (rect, action) in rects.items():
        if rect.collidepoint(x, y):
            send(screen, action, key)
            return


def key(screen, rects, event):
    """0-5 the rates, ESC ACCEPT — the popup's own hotkeys (E 0x8E-0x9B,
    0x87). Enter is not ACCEPT: the original's Enter presses the field
    under its pointer (F904), which HD does not know."""
    ch = getattr(event, "unicode", "") or ""
    if ch and ch in "012345" and f"rate_{int(ch) * 10}" in rects:
        send(screen, rects[f"rate_{int(ch) * 10}"][1], f"key {ch}")
    elif event.key == pygame.K_ESCAPE and "accept" in rects:
        send(screen, rects["accept"][1], "accept key")
