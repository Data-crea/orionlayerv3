"""The territory panel on the galaxy map's left edge, and its input.

the territory view (`terrfield`) (Data's mockups): TERRITORY VIEW with three
switches — Show Territories, Show Borders, Show Nebulae — the opacity
slider, and a legend of the empires the map shows. Every shape is a
`core.hud` block (the panel, the checkboxes, the separators); the slider is
the one thing drawn here, in the HUD style's own colours.

**ONE FUNCTION PER PLACE** (decision 5): `rects` says where every part is,
and the drawing, the click and the drag all read it.

**AN OVERLAY THE PLAYER MOVES AND HIDES** (Data, 4 November 2026: the map
must not get narrower). The panel stands over the map — the glass shows what
is under it — at its box's default place, or where the player dragged it by
its title (`territory_panel_pos`, reference px, kept inside the window). A
key (H, `layout.json` `territory_panel.key`; the galaxy map's other keys are
G T C P F L R I, + - 0, Home, Enter, ESC, F1-F10 and the typed cheats, so H
is free) shows and hides it (`territory_panel_shown`); hidden, the territories
stay drawn and only the controls are gone.

The legend lists only empires that have territory on the map right now
(what the player knows), each with the colour swatch and — while a
colour-blind palette is chosen — a sample of its border pattern, so the
legend answers "which line is whose" without relying on colour.
"""
import logging

import pygame

from core import lang
from core import mouse as mouse_input
from core import usersettings
from core.hud import blocks as hud
from core.hud import style as hudstyle
from core.hud import text as hudtext
from screens.galaxy_map import terrdraw
from screens.galaxy_map import terrview

log = logging.getLogger("galaxy_map.territory")
BOX = "territory_panel"
#: Layout px: padding, row heights, the swatch and checkbox squares.
PAD, TITLE_H, ROW_H, BOX_SIDE, SLIDER_H, LEGEND_H = 14, 30, 34, 22, 30, 30
SWATCH = 20
POS, SHOWN = "territory_panel_pos", "territory_panel_shown"
DEFAULT_KEY = "h"
KEYS = (("Show Territories", terrdraw.SHOW), ("Show Borders", terrdraw.BORDERS),
        ("Show Nebulae", terrdraw.NEBULAE))


def _origin(screen):
    """(x, y, w) of the panel's top-left in device px: the player's place
    (reference px, `territory_panel_pos`) or the box's own."""
    box = screen.box_rect(BOX)
    if not box:
        return None
    L = screen.layout
    x, y, w, _h = L.rect(box)
    us = getattr(screen.app, "user_settings", None)
    pos = us.get(POS) if us is not None else None
    if isinstance(pos, (list, tuple)) and len(pos) == 2:
        ox, oy = L.rect([0, 0, 1, 1])[:2]
        x, y = int(ox + pos[0] * L.scale), int(oy + pos[1] * L.scale)
    return x, y, w


def shown(app):
    us = getattr(app, "user_settings", None)
    return us is None or us.get(SHOWN) != "off"


def rects(screen, legend_rows):
    """Every part's device rect, or None while the box has none:
    {panel, title, checks: [(rect, label, key)], slider_label, track,
    legend: [rect]}. Kept inside the window."""
    org = _origin(screen)
    if org is None:
        return None
    r = _layout(screen, org, legend_rows)
    win = pygame.Rect(0, 0, screen.app.win_w, screen.app.win_h)
    p = r["panel"]
    dx = min(0, win.right - p.right) or max(0, win.left - p.left)
    dy = min(0, win.bottom - p.bottom) or max(0, win.top - p.top)
    if dx or dy:
        r = _layout(screen, (org[0] + dx, org[1] + dy, org[2]), legend_rows)
    return r


def _layout(screen, org, legend_rows):
    L = screen.layout
    s = L.scale
    x, y, w = org
    pad = int(PAD * s)
    y0 = y + pad
    out = {"title": pygame.Rect(x + pad, y0, w - 2 * pad, int(TITLE_H * s))}
    y0 += int((TITLE_H + 8) * s)
    out["sep1"] = y0 - int(4 * s)
    checks = []
    for label, key in KEYS:
        row = pygame.Rect(x + pad, y0, w - 2 * pad, int(ROW_H * s))
        checks.append((row, label, key))
        y0 += int(ROW_H * s)
    out["checks"] = checks
    y0 += int(6 * s)
    out["slider_label"] = pygame.Rect(x + pad, y0, w - 2 * pad, int(24 * s))
    y0 += int(26 * s)
    out["track"] = pygame.Rect(x + pad, y0, int((w - 2 * pad) * 0.66),
                               int(SLIDER_H * s))
    out["value"] = pygame.Rect(out["track"].right + int(8 * s), y0,
                               x + w - pad - out["track"].right - int(8 * s),
                               int(SLIDER_H * s))
    y0 += int((SLIDER_H + 12) * s)
    out["sep2"] = y0 - int(6 * s)
    legend = []
    for _ in range(legend_rows):
        legend.append(pygame.Rect(x + pad, y0, w - 2 * pad, int(LEGEND_H * s)))
        y0 += int(LEGEND_H * s)
    out["legend"] = legend
    out["panel"] = pygame.Rect(x, y, w, y0 - y + pad - (
        0 if legend_rows else int(14 * s)))
    return out


def key(screen, k):
    """True when `k` is the panel's key (it toggles the panel)."""
    cfg = screen._data.get("territory_panel") or {}
    try:
        want = pygame.key.key_code(cfg.get("key", DEFAULT_KEY))
    except ValueError:
        return False
    if k != want:
        return False
    us = getattr(screen.app, "user_settings", None)
    if us is not None:
        us.set(SHOWN, "off" if shown(screen.app) else "on")
        _save(us)
    return True


def _save(us):
    """A settings file that cannot be written must not stop the map: the
    value stays for this session."""
    try:
        usersettings.save(us)
    except OSError as err:
        log.warning("territory panel: settings not saved (%s)", err)


def _set(screen, key, value):
    us = getattr(screen.app, "user_settings", None)
    if us is None:
        return
    us.set(key, value)
    _save(us)


def _slider_value(r, x):
    t = (x - r["track"].x) / max(1, r["track"].w)
    return int(round(min(1.0, max(0.0, t)) * 100))


def click(screen, x, y):
    """True when the click was the panel's (any click on it is)."""
    if not shown(screen.app):
        return False
    r = rects(screen, len(terrview.legend(screen)))
    if r is None or not r["panel"].collidepoint(x, y):
        return False
    if r["title"].collidepoint(x, y):
        # the title is the handle: the grab keeps the pointer where it
        # took hold of the panel
        screen._territory_drag = ("move", x - r["panel"].x, y - r["panel"].y)
        return True
    for row, _label, key_ in r["checks"]:
        if row.collidepoint(x, y):
            _set(screen, key_,
                 "off" if terrdraw.is_on(screen.app, key_) else "on")
            return True
    grab = r["track"].inflate(0, int(14 * screen.layout.scale))
    if grab.collidepoint(x, y):
        screen._territory_drag = ("slider",)
        _set(screen, terrdraw.OPACITY, _slider_value(r, x))
    return True


def drag(screen, x, y):
    """The held button moves the panel or the slider; saved on release."""
    us = getattr(screen.app, "user_settings", None)
    mode = screen._territory_drag
    if us is None or not mode:
        return
    if mode[0] == "slider":
        r = rects(screen, len(terrview.legend(screen)))
        if r is not None:
            us.set(terrdraw.OPACITY, _slider_value(r, x))
        return
    L = screen.layout
    ox, oy = L.rect([0, 0, 1, 1])[:2]
    us.set(POS, [round((x - mode[1] - ox) / L.scale),
                 round((y - mode[2] - oy) / L.scale)])


def release(screen):
    if getattr(screen, "_territory_drag", False):
        screen._territory_drag = False
        us = getattr(screen.app, "user_settings", None)
        if us is not None:
            _save(us)


def render(screen, surface):
    if not shown(screen.app):
        return
    legend = terrview.legend(screen)
    r = rects(screen, len(legend))
    if r is None:
        return
    L = screen.layout
    s = L.scale
    st = hudstyle.get()
    hud.panel(surface, r["panel"], s)
    style = screen.style
    mx, my = mouse_input.pos()
    hudtext.blit(surface,
                 hudtext.render(style, lang.tr("Territory View").upper(),
                                "title", r["title"].h, scale=1.0),
                 r["title"], "left")
    hint = (screen._data.get("territory_panel") or {}).get("key", DEFAULT_KEY)
    hudtext.blit(surface, _word(style, f"[{hint.upper()}]", s, "sub"),
                 r["title"], "right")
    x0, x1 = hud.separator_span(r["panel"], s)
    hud.separator(surface, x0, x1, r["sep1"], s)
    for row, label, key in r["checks"]:
        sq = pygame.Rect(row.x, row.y + (row.h - int(BOX_SIDE * s)) // 2,
                         int(BOX_SIDE * s), int(BOX_SIDE * s))
        hud.checkbox(surface, sq, s, terrdraw.is_on(screen.app, key),
                     row.collidepoint(mx, my))
        text = _word(style, lang.tr(label), s)
        hudtext.blit(surface, text, pygame.Rect(
            sq.right + int(10 * s), row.y, row.right - sq.right - int(10 * s),
            row.h), "left")
    hudtext.blit(surface, _word(style, lang.tr("Territory Opacity"), s),
                 r["slider_label"], "left")
    _slider(surface, r, terrdraw.opacity(screen.app), s, st)
    pct = f"{int(round(terrdraw.opacity(screen.app) * 100))} %"
    hudtext.blit(surface, _word(style, pct, s, "value"),
                 r["value"], "right")
    if legend:
        hud.separator(surface, x0, x1, r["sep2"], s)
    for row, (colour, name, rgb) in zip(r["legend"], legend):
        sw = pygame.Rect(row.x, row.y + (row.h - int(SWATCH * s)) // 2,
                         int(SWATCH * s), int(SWATCH * s))
        # LOOK EXCEPTION data: the swatch is the empire's own colour, the very table the star names and the borders use
        pygame.draw.rect(surface, rgb[:3], sw)
        text_x = sw.right + int(10 * s)
        pattern = terrdraw.pattern_for(colour)
        if pattern is not None:
            _sample(surface, rgb[:3], pattern,
                    pygame.Rect(row.right - int(46 * s), row.y,
                                int(46 * s), row.h), s)
        text = _word(style, name, s)
        right = row.right - (int(54 * s) if pattern is not None else 0)
        hudtext.blit(surface, text, pygame.Rect(
            text_x, row.y, right - text_x, row.h), "left")


def _word(style, text, s, role="label"):
    """A panel word. The HUD's own text sizes are fractions of a tall
    sidebar box (`text.label.cap` is 0.10 of it), so a row this small
    takes the button role's size, in the role's colour."""
    return hudtext.render(style, text, "button", int(ROW_H * 1.5 * s),
                          colour_=hudtext.colour(role))


def _slider(surface, r, value, s, st):
    track = r["track"]
    mid = track.centery
    h = max(2, int(3 * s))
    base = pygame.Rect(track.x, mid - h // 2, track.w, h)
    pygame.draw.rect(surface, st.colour("separator.color"), base)
    lit = base.copy()
    lit.w = int(track.w * value)
    pygame.draw.rect(surface, st.colour("action.edge"), lit)
    pygame.draw.circle(surface, st.colour("action.edge"),
                       (track.x + lit.w, mid), max(5, int(8 * s)))


def _sample(surface, rgb, pattern, rect, s):
    """The border pattern as a short line, so the legend carries it."""
    x, y = rect.x, rect.centery
    pos, k = 0.0, 0
    while pos < rect.w:
        step = pattern[k % len(pattern)] * s * 0.7
        if k % 2 == 0:
            end = min(rect.w, pos + step)
            # LOOK EXCEPTION marking: a sample of the border's own dash pattern in the empire's colour, as the map draws it
            pygame.draw.rect(surface, rgb, (x + int(pos), y - max(1, int(s)),
                                            max(1, int(end - pos)),
                                            max(2, int(2 * s))))
        pos += step
        k += 1
