"""The galaxy map's movable boxes, drawn by HD (Data's decision A1, brief 111).

`boxmodel` decides WHAT a box shows and whether HD may show it; this
module decides where and how, and what a click inside one sends.

WHAT A CLICK SENDS. Only fields, by index from the live list (decision
20): CLOSE is the box's ESC-hotkey button (`MOVEBOX`'s close field,
sys.cpp:1781, fleetpop.cpp:477), and the ESC key sends the same field —
never a positional right click (decision 66). A planet disc sends that
planet's field, which the engine answers as the original does: the colony
screen for an own colony, "%s is an outpost planet" for an own outpost,
nothing otherwise (mainscr_main.cpp:570-577). A click anywhere else inside
a drawn box is swallowed, because the box covers the map there.

DEVIATION — the layout is HD's. The boxes are boxes.json's, F5-movable;
the words are the original's (boxmodel). Two things follow the original
on purpose: a box sits on the same SIDE of the map as the game's window
(left or right, top or bottom, read from the window's own rect), so it
does not cover the star or fleet it belongs to; and a stack shows at most
nine ships in rows of three. Two things do not: the planets stand in a
row by orbit instead of on ellipses, and a ship is drawn as its map icon
(the fleet box's own ship pictures are not extracted).

OMISSION (decision 61), each a field HD leaves alone: the system window's
ship buttons, gate icons and planet hover line; the fleet box's ALL,
scroll and the Outpost / Colonize / Engage / Transport / Attack buttons;
the space-monster branch of the system window. And three things drawn
without a field, seen beside the original's window on 15 September 2026
(evidence 71): the orbit rings, the asteroid belts, and the colony
markers beside owned planets. Moving a fleet from the HD box is not
built: decision 65 still refuses the destination click.
"""
import logging

import pygame

from core import hestrings
from core import palette
from core import textfit
from screens.colony_summary import colonyplanets
from screens.galaxy_map import boxmodel, mapboxes
from screens.galaxy_map import renderer as rnd
from screens.galaxy_map import ships as ship_icons

log = logging.getLogger("galaxy_map.boxes")

SYSTEM_BOXES = ("system_box", "system_title", "system_view",
                "system_text", "system_close")
FLEET_BOXES = ("fleet_box", "fleet_title", "fleet_grid",
               "fleet_status", "fleet_close")
PANEL_BG = palette.col("galaxy_map", "panel_background", (8, 11, 20))
TITLE_COLOR = palette.col("galaxy_map", "title", (200, 210, 238))
TEXT_COLOR = palette.col("galaxy_map", "nav_text", (196, 208, 236))
BUTTON_BG = palette.col("galaxy_map", "nav_background", (10, 14, 26))
GAS_GIANT = palette.col("galaxy_map", "status", (140, 155, 190))
#: The original's map window centre, native: a box whose own centre lies
#: left of it sits on the left, and so on (mainscr.cpp:1060-1082).
MAP_MID = ((22 + 527) / 2, (22 + 421) / 2)


def _texts(screen):
    text = getattr(screen, "_hstrings", None)
    if text is None:
        lang = (getattr(screen.app, "settings", {}) or {}).get("language",
                                                               "en")
        text = hestrings.HStrings(lang)
        screen._hstrings = text
    return text if text.state == "ok" else None


def drawable(screen):
    """[(names, box, model)] for every box HD may draw this frame."""
    state = getattr(screen, "_state", None)
    if state is None:
        return []
    boxes = mapboxes.classify(getattr(state, "fields", None))
    ident = getattr(screen, "_box_identity", None)
    out = []
    for box in boxes.boxes:
        if box.kind == "system":
            model, why = boxmodel.system_model(
                state, ident, box, _texts(screen), screen._omniscient)
            names = SYSTEM_BOXES
        else:
            model, why = boxmodel.fleet_model(state, ident, box,
                                              _texts(screen))
            names = FLEET_BOXES
        if model is None:
            if getattr(screen, "_box_refusal", None) != why:
                log.info("%s box not drawn: %s", box.kind, why)
                screen._box_refusal = why
            continue
        out.append((names, box, model))
    return out


def _placed(screen, names, box):
    """HD rects for a box group, moved to the original's side of the map."""
    rects = {}
    for name in names:
        ref = screen.box_rect(name)
        if not ref:
            return None
        rects[name] = pygame.Rect(*screen.layout.rect(ref))
    view = screen._map_view()
    if view is None:
        return None
    area = pygame.Rect(*view.box)
    panel = rects[names[0]]
    x0, y0, x1, y1 = box.rect
    dx = dy = 0
    if (x0 + x1) / 2 < MAP_MID[0]:
        dx = (area.x + (area.right - panel.right)) - panel.x
    if (y0 + y1) / 2 < MAP_MID[1]:
        dy = (area.y + (area.bottom - panel.bottom)) - panel.y
    return {n: r.move(dx, dy) for n, r in rects.items()}


def _font(screen, name, default):
    style = next((b.style for b in screen.boxes if b.name == name), {})
    return screen.layout.font_size(style.get("font_size", default))


def _text(screen, surface, rect, text, size, colour, align="center"):
    if not text:
        return
    surf = screen.style.render_text(text, size, tuple(colour[:3]))
    x = {"left": rect.x, "right": rect.right - surf.get_width()}.get(
        align, rect.x + (rect.w - surf.get_width()) // 2)
    surface.blit(surf, (x, rect.y + (rect.h - surf.get_height()) // 2))


def _frame(screen, surface, rect):
    surface.fill(PANEL_BG[:3], rect)
    screen.style.draw_thin_border(surface, rect, screen.layout.scale)


def _button(screen, surface, rect, label, size):
    surface.fill(BUTTON_BG[:3], rect)
    screen.style.draw_thin_border(surface, rect, screen.layout.scale)
    _text(screen, surface, rect, label, size, TEXT_COLOR)


def _close_label(screen):
    return (screen._data.get("movable_boxes") or {}).get("close", "")


def _draw_system(screen, surface, r, model, hits):
    view = r["system_view"]
    if not model["viewable"]:
        size = _font(screen, "system_view", 16)
        lines = textfit.wrap_text(screen.style, model["body"], size, view.w)
        y = view.y
        for line in lines:
            surf = screen.style.render_text(line, size, TEXT_COLOR[:3])
            surface.blit(surf, (view.x, y))
            y += surf.get_height()
        return
    stars = screen._stars
    star = stars[model["star"]]
    ctx = screen._map_context()
    name = rnd.star_icon_name(star, ctx) if ctx is not None else None
    sun = min(view.h, view.w // 5)
    if name and screen._cache.has(name):
        img = screen._cache.scaled(name, sun)
        if img is not None:
            surface.blit(img, (view.x, view.centery - img.get_height() // 2))
    planets = model["planets"]
    if not planets:
        return
    cell = (view.w - sun) // len(planets)
    disc_max = min(cell, view.h) * 8 // 10
    for i, p in enumerate(planets):
        side = max(4, disc_max * (6 + min(4, p["size"])) // 10)
        cx = view.x + sun + cell * i + cell // 2
        rect = pygame.Rect(0, 0, side, side)
        rect.center = (cx, view.centery)
        disc = None
        if p["type"] != 2:
            discs = colonyplanets.set_for(screen, side)
            disc = discs.get(p["climate"]) if discs is not None else None
        if disc is not None:
            surface.blit(disc, rect.topleft)
        else:
            pygame.draw.circle(surface, GAS_GIANT[:3], rect.center, side // 2, 2)
        hits.append((rect, p["field"]))


def _draw_fleet(screen, surface, r, model, hits):
    grid = r["fleet_grid"]
    cw, ch = grid.w // 3, grid.h // 3
    for i, (ship, owner) in enumerate(zip(model["stack"], model["owners"])):
        cell = pygame.Rect(grid.x + cw * (i % 3), grid.y + ch * (i // 3),
                           cw, ch)
        kind = ship_icons.kind_for_owner(owner) or ship_icons.PLAYER_KIND
        key = ship_icons._resolve_sprite(screen._cache, kind, 0)
        if key is None:
            continue
        side = min(cell.w, cell.h) * 7 // 10
        base = screen._cache.base(key)
        img = screen._cache.scaled(key, max(1, side * base.get_width()
                                            // max(base.get_width(),
                                                   base.get_height())))
        if img is None:
            continue
        if kind == ship_icons.PLAYER_KIND:
            colour = ship_icons._player_color(screen._players, owner)
            if colour is not None:
                img = screen._tints.get(img, key, colour)
        surface.blit(img, img.get_rect(center=cell.center))
    _text(screen, surface, r["fleet_status"], model["status"],
          _font(screen, "fleet_status", 16), TEXT_COLOR)


def render(screen, surface):
    """Draw every box HD may draw; remember the hit areas for clicks."""
    hits = []
    screen._box_hits = hits
    for names, box, model in drawable(screen):
        r = _placed(screen, names, box)
        if r is None:
            continue
        _frame(screen, surface, r[names[0]])
        hits.append((r[names[0]], None))
        _text(screen, surface, r[names[1]], model["title"],
              _font(screen, names[1], 20), TITLE_COLOR)
        if model["kind"] == "system":
            _draw_system(screen, surface, r, model, hits)
            _text(screen, surface, r["system_text"], model["wormhole"],
                  _font(screen, "system_text", 16), TEXT_COLOR, "left")
        else:
            _draw_fleet(screen, surface, r, model, hits)
        close = r[names[-1]]
        _button(screen, surface, close, _close_label(screen),
                _font(screen, names[-1], 18))
        hits.append((close, model["close"]))


def _activate(screen, index, what):
    if index is None:
        return
    log.info("Box: %s (field %s)", what, index)
    if screen.app.connected:
        screen.app.client.activate_field(index)


def handle_click(screen, x, y):
    """True when (x, y) is inside a drawn box; fields go out by index."""
    for rect, index in reversed(getattr(screen, "_box_hits", [])):
        if rect.collidepoint(x, y):
            _activate(screen, index, "field")
            return True
    return False


def handle_key(screen, key):
    """ESC closes a drawn box through its own CLOSE field (decision 66)."""
    if key != pygame.K_ESCAPE:
        return False
    for _, _, model in drawable(screen):
        if model["close"] is not None:
            _activate(screen, model["close"], "close")
            return True
    return False
