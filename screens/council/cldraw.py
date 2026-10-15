"""The galactic council's drawing — work order 270 (`screen`, `clgeom`).

Everything it writes is the game's: the three top lines and the message as
`Draw_Main_Council_Screen` formats them, the list's title and items as
`Council_Player_Vote` / `Council_Accept_Ruling` build them (open fix 96
sends them), the players' names from their records. HD adds only the
labels of its panels and the hint under the message while the game waits
for a click (HD EXTENSION `council_labels`).
"""
import pygame

from core import palette, textfit
from core.hud import blocks as hud
from core.hud import text as hudtext
from core.structs import player as player_struct

from . import clgeom as geom

NEUTRAL = (200, 200, 200)
#: The council's normal and highlight text: palette 150-155 (council.cpp:
#: 8-9) — the chamber's own palette, which HD does not load; the HUD's
#: roles stand in for them.
TEXT, DIM = "value", "label"


def players(state):
    """{index: (name, race name, colour index)} from the player records."""
    out = {}
    for i, raw in enumerate(getattr(state, "player_raw", None) or []):
        try:
            p = player_struct.SPEC.parse(raw)
        except (ValueError, IndexError):
            continue
        out[i] = (str(p.name).strip(), str(p.race_name).strip(),
                  int(p.color))
    return out


def owner_rgb(colour):
    if colour is None:
        return NEUTRAL
    return tuple(palette.col("galaxy_map", f"owner_{int(colour)}", NEUTRAL))


def _size(scale, k=1.0):
    return max(12, int(round(19 * scale * k)))


def _line(surface, style, text, size, rgb, rect, align):
    if not text:
        return
    img = style.render_text(text, size, rgb)
    if img.get_width() > rect.w:
        img = pygame.transform.smoothscale(img, (rect.w, img.get_height()))
    hudtext.blit(surface, img, rect, align=align)


def draw(surface, screen, council, state):
    """The panels' contents (the shell and the panels are drawn by the
    screen's boxes)."""
    lay = screen.app.layout
    style, scale = screen.style, lay.scale
    who = players(state)
    pad = max(6, int(14 * scale))
    text_rgb = hudtext.colour(TEXT)
    dim_rgb = hudtext.colour(DIM)

    r = screen.box_screen_rect(geom.TOP)
    if r is not None:
        inner = r.inflate(-2 * pad, -pad)
        for line, align in zip(council["lines"], ("left", "center", "right")):
            _line(surface, style, line, _size(scale), text_rgb, inner, align)

    for k, name in enumerate((geom.NOMINEE_A, geom.NOMINEE_B)):
        r = screen.box_screen_rect(name)
        if r is not None:
            _nominee(surface, style, scale, r.inflate(-2 * pad, -2 * pad),
                     council, k, who, text_rgb, dim_rgb)

    r = screen.box_screen_rect(geom.MEMBERS)
    if r is not None:
        _members(surface, style, scale, r.inflate(-2 * pad, -2 * pad),
                 council, who, text_rgb, dim_rgb)

    r = screen.box_screen_rect(geom.MESSAGE)
    if r is not None:
        screen.menu_rects = _message(surface, style, scale,
                                     r.inflate(-2 * pad, -2 * pad), council,
                                     text_rgb, dim_rgb)


def _nominee(surface, style, scale, r, council, k, who, text_rgb, dim_rgb):
    player = council["nominees"][k]
    name, race, colour = who.get(player, (f"#{player}", "", None))
    rgb = owner_rgb(colour)
    h = _size(scale, 1.3)
    y = r.y
    _line(surface, style, "NOMINEE", _size(scale, 0.8), dim_rgb,
          pygame.Rect(r.x, y, r.w, h), "center")
    y += int(h * 1.4)
    _line(surface, style, name, h, rgb, pygame.Rect(r.x, y, r.w, h),
          "center")
    y += int(h * 1.3)
    _line(surface, style, race, _size(scale), rgb,
          pygame.Rect(r.x, y, r.w, h), "center")
    y += int(h * 2.0)
    big = _size(scale, 2.6)
    _line(surface, style, str(council["received"][k]), big, text_rgb,
          pygame.Rect(r.x, y, r.w, big), "center")
    y += int(big * 1.2)
    _line(surface, style, "VOTES RECEIVED", _size(scale, 0.8), dim_rgb,
          pygame.Rect(r.x, y, r.w, h), "center")
    y += int(h * 1.6)
    _line(surface, style, f"{council['own_votes'][k]} OWN VOTES",
          _size(scale, 0.8), dim_rgb, pygame.Rect(r.x, y, r.w, h), "center")
    if council["state"] == "elected" and council["vote_for"] == k:
        _line(surface, style, "ELECTED", _size(scale, 1.2),
              owner_rgb(colour), pygame.Rect(r.x, r.bottom - h, r.w, h),
              "center")
    if council["voter"] == player:
        pad = max(6, int(14 * scale))
        hud.outline(surface, r.inflate(pad, pad), scale)


def _members(surface, style, scale, r, council, who, text_rgb, dim_rgb):
    size = _size(scale)
    row_h = int(size * 1.9)
    _line(surface, style, "COUNCIL MEMBERS", _size(scale, 0.8), dim_rgb,
          pygame.Rect(r.x, r.y, r.w, row_h), "left")
    _line(surface, style, "VOTES", _size(scale, 0.8), dim_rgb,
          pygame.Rect(r.x, r.y, r.w, row_h), "right")
    y = r.y + row_h
    for i, m in enumerate(council["members"]):
        if y + row_h > r.bottom:
            break
        row = pygame.Rect(r.x, y, r.w, row_h)
        voting = council["voter"] == m["player"] and \
            council["state"] in ("vote", "abstain")
        hud.table_row(surface, row, scale, i, selected=voting)
        name, race, colour = who.get(m["player"], (f"#{m['player']}", "",
                                                   None))
        label = f"{race}  {name}" if race else name
        _line(surface, style, label, size, owner_rgb(colour),
              row.inflate(-size, 0), "left")
        _line(surface, style, str(m["votes"]), size, text_rgb,
              row.inflate(-size, 0), "right")
        y += row_h


def _message(surface, style, scale, r, council, text_rgb, dim_rgb):
    """The message, then the list; returns [(rect, item index)]."""
    size = _size(scale, 1.1)
    y = r.y
    for img in textfit.wrap_rendered(style, council["message"] or "", size,
                                     r.w, text_rgb):
        if y + img.get_height() > r.bottom:
            break
        surface.blit(img, (r.centerx - img.get_width() // 2, y))
        y += int(img.get_height() * 1.15)
    menu = council.get("menu")
    rects = []
    if menu:
        y += size
        _line(surface, style, menu["title"].strip(), size, dim_rgb,
              pygame.Rect(r.x, y, r.w, size * 2), "center")
        y += size * 2
        items = [(i, it) for i, it in enumerate(menu["items"])
                 if it["text"].strip()]
        bw = min(r.w // max(1, len(items)) - size, int(260 * scale))
        bh = int(size * 2.2)
        total = len(items) * bw + (len(items) - 1) * size
        x = r.centerx - total // 2
        for i, it in items:
            b = pygame.Rect(x, min(y, r.bottom - bh), bw, bh)
            hud.small_button(surface, b, scale,
                             "normal" if it["enabled"] else "disabled",
                             it["text"].strip(), style_renderer=style)
            if it["enabled"]:
                rects.append((b, i))
            x += bw + size
    else:
        _line(surface, style, "Click to continue", _size(scale, 0.8),
              dim_rgb, pygame.Rect(r.x, r.bottom - size * 2, r.w, size * 2),
              "center")
    return rects
