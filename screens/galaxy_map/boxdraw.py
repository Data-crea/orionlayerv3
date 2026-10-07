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

TRANSCRIPTION `box_right` (work order 200 B) — a RIGHT click: on a planet
disc it is a right click on that planet's own field (`core/rightinfo`), which
the engine answers with `SYS::Potential_Colony_Info_Popup_`'s text box
(mainscr.cpp:2104-2110; nothing for a gas giant), shown as HD's message box;
on the fleet box's status line and close button it is the help the original
appends for the box (310, 304; `help_at`). A ship cell's right click (the
original's ship view, `Detailed_View_Ship_`) is not offered: HD has no view
for it (parked, work order 200).

DEVIATION — the layout is HD's. The boxes are boxes.json's, F5-movable;
the words are the original's (boxmodel). Two things follow the original
on purpose: a box sits on the same SIDE of the map as the game's window
(left or right, top or bottom, read from the window's own rect), so it
does not cover the star or fleet it belongs to; and a stack shows at most
nine ships in rows of three — past nine, the three rows the engine shows
(open fix 59, FBSC) with the bar's thumb where the engine has it and its
two arrows sending the bar's own "-" / "+" buttons (fleetpop.cpp:189-216,
mainscr.cpp:3404-3408; work order 197 A2). Two things do not: the planets stand in a
row by orbit instead of on ellipses, and a ship is drawn as its map icon
(the fleet box's own ship pictures are not extracted).

OMISSION (decision 61), each a field HD leaves alone: the system window's
ship buttons, gate icons and planet hover line; the fleet box's ALL,
the bar's thumb drag (a scroll field that reads the POINTER, fleetpop.cpp:
213-216 — a click on the track steps one row toward it instead, DEVIATION
`fleet_scroll_track`) and the Outpost / Colonize / Engage / Transport / Attack buttons;
the space-monster branch of the system window. And three things drawn
without a field, seen beside the original's window on 15 September 2026
(evidence 71): the orbit rings, the asteroid belts, and the colony
markers beside owned planets.

A fleet box is drawn only from open fix 20's wire data (boxmodel): its
cells follow the engine's chain, their colour is each node's selected
byte, and while it is drawn a star click is a move order for exactly the
blue ships (decision 65's amendment, `orders_ok`).
"""
import logging

import pygame

from core.hud import blocks as hud
from core.hud import glyphs

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
GAS_GIANT = palette.col("galaxy_map", "status", (140, 155, 190))
#: A hover refusal's line — the original's second colour set
#: (fleetpop.cpp:1122-1150, `use_primary_colors = false`).
REFUSED = palette.col("galaxy_map", "fleet_refused", (226, 96, 72))
#: The original's map window centre, native: a box whose own centre lies
#: left of it sits on the left, and so on (mainscr.cpp:1060-1082).
MAP_MID = ((22 + 527) / 2, (22 + 421) / 2)


def _texts(screen):
    # ONE CONSTRUCTION SITE (D17, work order 159). This cached its own
    # copy on the SCREEN, so the galaxy map and the game menu read
    # HESTRNGS into two objects; `hestrings.for_app` owns the one.
    text = hestrings.for_app(screen.app)
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
    """The window's body: the HUD popup block (decision 71) — the system
    window and the fleet box are dialogs over the map, opaque."""
    hud.popup(surface, rect, screen.layout.scale)


def _button(screen, surface, rect, label, size):
    """CLOSE: the HUD's small button, its word in code."""
    hud.small_button(surface, rect, screen.layout.scale, "normal", label,
                     style_renderer=screen.style,
                     icon=glyphs.for_button("galaxy_map", "close"))


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
        screen._box_planets.append((rect, p["field"]))


def orders_ok(screen):
    """True while HD draws a fleet box — which it does only with the
    chain and the selection read off the wire: then a star click moves
    exactly the ships shown blue, and the decision-65 guard steps aside
    (Data's path 1, brief 117)."""
    return any(m["kind"] == "fleet" for _, _, m in drawable(screen))


def scroll_rects(box, grid):
    """(bar, up, down) window rects of the fleet box's scroll column: the
    strip between the grid and the box's right edge, an arrow square at
    each end — the original's buttons sit above and below its track
    (fleetpop.cpp:197-216)."""
    w = max(8, min(box.right - grid.right - 3, grid.w // 12))
    bar = pygame.Rect(grid.right + 1, grid.y, w, grid.h)
    return (bar, pygame.Rect(bar.x, bar.y, w, w),
            pygame.Rect(bar.x, bar.bottom - w, w, w))


def _draw_scroll(screen, surface, box, grid, scroll, hits):
    """The bar the original shows past nine ships (fleetpop.cpp:189, :782):
    the thumb at the row the engine shows (FBSC), and the two arrows, each
    a hit area for the bar's own button when the live list carries it."""
    bar, up, down = scroll_rects(box, grid)
    hud.scrollbar(surface, bar.inflate(0, -2 * up.h), screen.layout.scale,
                  scroll["first_row"], scroll["visible_rows"], scroll["rows"])
    for rect, field, top in ((up, scroll["up"], True),
                             (down, scroll["down"], False)):
        cx, cy, h = rect.centerx, rect.centery, max(2, rect.w // 3)
        pts = ([(cx, cy - h), (cx - h, cy + h), (cx + h, cy + h)] if top
               else [(cx, cy + h), (cx - h, cy - h), (cx + h, cy - h)])
        # LOOK EXCEPTION marking: a scroll arrow glyph in the box's text colour
        pygame.draw.polygon(surface, TEXT_COLOR[:3], pts)
        if field is not None:
            hits.append((rect, field))
    # DEVIATION `fleet_scroll_track`: the original's track is a scroll field
    # dragged by the POINTER; a click on HD's track steps one row toward it
    # through the same buttons.
    track = pygame.Rect(bar.x, up.bottom, bar.w, down.y - up.bottom)
    mid = track.y + track.h * (scroll["first_row"] + 1.5) / scroll["rows"]
    if scroll["up"] is not None:
        hits.append((pygame.Rect(track.x, track.y, track.w,
                                 max(0, int(mid) - track.y)), scroll["up"]))
    if scroll["down"] is not None:
        hits.append((pygame.Rect(track.x, int(mid), track.w,
                                 max(0, track.bottom - int(mid))),
                     scroll["down"]))


def _draw_fleet(screen, surface, r, model, hits):
    grid = r["fleet_grid"]
    cw, ch = grid.w // 3, grid.h // 3
    if model.get("scroll"):
        _draw_scroll(screen, surface, r["fleet_box"], grid, model["scroll"],
                     hits)
    for i, (ship, owner) in enumerate(zip(model["stack"], model["owners"])):
        cell = pygame.Rect(grid.x + cw * (i % 3), grid.y + ch * (i // 3),
                           cw, ch).inflate(-4, -4)
        # One box per ship, blue selected and black not, as the original
        # draws its cells — the colour is the cell's node byte in the FSEL
        # block, the cell's place its place in the wire's chain.
        # Since work order 223 the shared field, 'on' where chosen
        # (proposal C): the original's blue cell, in the one look.
        chosen = model["selected"][i]
        hud.field(surface, cell, screen.layout.scale, on=chosen)
        if model["selectable"][i]:
            hits.append((cell, ("select", ship, not chosen)))
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
    status, colour = model["status"], TEXT_COLOR
    over = hover_status(screen)
    if over is not None:
        status, colour = over[0], (REFUSED if over[1] else TEXT_COLOR)
    _text(screen, surface, r["fleet_status"], status,
          _font(screen, "fleet_status", 16), colour)


def hover_status(screen):
    """`boxmodel.hover_status` for the star under the pointer (work order
    196 H): the move to it, before it is ordered."""
    hover = getattr(screen, "_hover_star", None)
    stars = getattr(screen, "_stars", None) or []
    if hover is None or getattr(screen, "_state", None) is None:
        return None
    # By position, as the hover line finds it (`maplines.render_hover_preview`).
    index = next((i for i, s in enumerate(stars)
                  if (s.x, s.y) == (hover.x, hover.y)), None)
    return boxmodel.hover_status(screen._state, index, stars,
                                 _texts(screen))


def render(screen, surface):
    """Draw every box HD may draw; remember the hit areas for clicks."""
    hits = []
    screen._box_hits = hits
    screen._box_planets = []
    screen._box_help = []
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
            # the fleet box's help, as `Set_Main_Screen_Help_List_`
            # appends it (evanhelp.cpp:239-273): 310 the band above the
            # buttons — HD's status line stands there — then 304 the
            # close button. The order buttons' 305-309 have no HD element
            # (the box offers no orders).
            screen._box_help = [(r["fleet_status"], 310),
                                (r[names[-1]], 304)]
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


def _select(screen, ship, selected):
    log.info("Box: ship %s selected -> %s", ship, selected)
    if screen.app.connected:
        screen.app.client.select_ship(ship, selected)


def handle_click(screen, x, y):
    """True when (x, y) is inside a drawn box. Fields go out by index; a
    ship cell sends MSG_SELECT_SHIP (open fix 21) with the opposite of the
    state the FSEL block showed."""
    for rect, action in reversed(getattr(screen, "_box_hits", [])):
        if rect.collidepoint(x, y):
            if isinstance(action, tuple):
                _select(screen, action[1], action[2])
            else:
                _activate(screen, action, "field")
            return True
    return False


def help_at(screen, x, y):
    """The open fleet box's help id under (x, y), or None."""
    return next((hid for rect, hid in getattr(screen, "_box_help", [])
                 if rect.collidepoint(x, y)), None)


def planet_field_at(screen, x, y):
    """The system window's planet field under (x, y), or None — where the
    original answers a right click with the planet's colony info
    (`SYS::Potential_Colony_Info_Popup_`, mainscr.cpp:2105-2110; a gas
    giant gets nothing there, as in the original)."""
    return next((f for rect, f in getattr(screen, "_box_planets", [])
                 if rect.collidepoint(x, y)), None)


def handle_key(screen, key):
    """ESC closes a drawn box through its own CLOSE field (decision 66)."""
    if key != pygame.K_ESCAPE:
        return False
    for _, _, model in drawable(screen):
        if model["close"] is not None:
            _activate(screen, model["close"], "close")
            return True
    return False
