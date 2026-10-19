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
appends for the box (310, 304; `help_at`). OMISSION `box_cell_detail`: the
right click on any cell of an own stack (the original's ship view,
`Detailed_View_Ship_`, mainscr.cpp:3428-3434), offered or not, does nothing:
HD has no view for it (parked, work order 200 P-B1; `mapinput.right_button`,
the cells `_box_own_cells`).

TRANSCRIPTION `drag_select` (work order 310): a press in the fleet box
paints — the held button gives every offered cell it crosses the press's
value, one MSG_SELECT_SHIP each (`boxpaint`). TRANSCRIPTION `belt_hit` (work
order 310): an asteroid belt in the system window is hovered and clicked
through the window's grid field, as the original's scan finds it
(`sysorbits.belt_point`, `belt_at`, `_inside`).

DEVIATION — the layout is HD's. The boxes are boxes.json's, F3-movable;
the words are the original's (boxmodel). Two things follow the original
on purpose: a box sits on the same SIDE of the map as the game's window
(left or right, top or bottom, read from the window's own rect), so it
does not cover the star or fleet it belongs to; and a stack shows at most
nine ships in rows of three — past nine, the three rows the engine shows
(open fix 59, FBSC) with the bar's thumb where the engine has it and its
two arrows sending the bar's own "-" / "+" buttons (fleetpop.cpp:189-216,
mainscr.cpp:3404-3408; work order 197 A2). Since work
order 223 the planets stand where the engine puts them, on their orbits
(`sysorbits`).

HD EXTENSION `box_ship_picture` (work order 312, Data: the popup showed no
picture of the new designs): the original draws in every cell that cell's
OWN ship, `Get_Ship_Id_Picture_Seg_(ship)` — SHIPS.LBX picture_num + colour *
50, the builder's colour (fleetpop.cpp:723-746, ken.cpp:451-468). HD draws
each cell's own ship by the map's picture rule (`ships.ship_picture`,
`shippics`: the map slot, else the battle picture, the builder's shape in
the owner's colour, the setting `map_ship_pictures`), so a cell shows what
the map shows for that ship, fitted into 8/10 of the cell. Until then every
cell drew the owner's tinted map master, one picture for every ship. A ship
with no picture there (setting off, no extraction, a colony, outpost or
transport ship without its slot file) keeps the tinted master (DEVIATION
`fleet_icon_drawn`, `sysfleets.icon`), as on the map.

TRANSCRIPTION `box_scanned_name` and TRANSCRIPTION `box_damage_bars` (work
order 313, `boxcells`): the cell under the pointer puts its ship's text in
the info line before the move line (fleetpop.cpp:1028-1031, :1368-1392), and
every own combat ship that is damaged gets the original's bar over its
picture (fleetpop.cpp:41-84, :748-762).

THE SYSTEM WINDOW'S DRAWING IS `syswindow`'s (work order 228 B): one
implementation for this window and the combat target window
(`combattarget`), as the original draws both with one function; this
module places the map's window and keeps its hits.

OMISSION (decision 61), each a field HD leaves alone: the system window's
gate icons (its planet information under the pointer is drawn since work
order 226 F, `sysinfo`; its fleet bar since work order 231 C, `sysfleets`,
from open fix 90's SYSW); the bar's thumb drag (a scroll
field that reads the POINTER, fleetpop.cpp:213-216 — a click on the track
steps one row toward it instead, DEVIATION `fleet_scroll_track`); the
space-monster branch of the system window. The fleet box's ALL and its
Outpost / Colonize / Engage / Transport / Attack buttons are drawn since
work order 229 (`fleetorders`, open fix 86). (The orbit rings and the
asteroid belts are drawn since work order 223, `sysorbits`; the colony
markers beside owned planets since work order 228, `syswindow`.)

A fleet box is drawn only from open fix 20's wire data (boxmodel): its
cells follow the engine's chain, their colour is each node's selected
byte, and while it is drawn a star click is a move order for exactly the
blue ships (decision 65's amendment, `orders_ok`).
"""
import logging

import pygame

from core.hud import blocks as hud

from core import hestrings
from core import mouse
from core import palette
from screens.galaxy_map import (boxcells, boxmodel, boxpaint, fleetorders,
                                mapboxes, sysfleets, sysorbits, syswindow)
from screens.galaxy_map import ships as ship_icons
from screens.galaxy_map.syswindow import TEXT_COLOR

log = logging.getLogger("galaxy_map.boxes")

SYSTEM_BOXES = ("system_box", "system_title", "system_view",
                "system_text", "system_close")
FLEET_BOXES = ("fleet_box", "fleet_title", "fleet_grid",
               "fleet_status", "fleet_close")
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
    clicked = getattr(screen, "_box_identity", None)
    out = []
    for box in boxes.boxes:
        # THE WIRE NAMES THE BOX (work order 231 D, `boxmodel.wire_identity`)
        # — whoever opened it; HD's own last click only on an older engine
        ident = boxmodel.wire_identity(state, box.kind) or clicked
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


def _draw_system(screen, surface, r, model, hits):
    """The window's view through `syswindow`; the planets' hit areas; the
    fleet bar through `sysfleets`, the combat target window's drawing
    (work order 231 C)."""
    view = r["system_view"]
    drawn = syswindow.draw_view(screen, surface, view, model)
    for p, rect in drawn:
        hits.append((rect, p["field"]))
        screen._box_planets.append((rect, p["field"]))
    bar = sysfleets.bar_rect(view, r["system_close"])
    s = sysorbits.frame(view)[0]
    if model["viewable"]:
        fleets = sysfleets.draw_bar(screen, surface, bar, model["fleets"], s)
    else:
        # TRANSCRIPTION `hidden_ship_fields`: an unviewable window draws no
        # bar (sys.cpp:692-731) but keeps its ship fields (:1845-1870), so a
        # click where an icon would stand opens that fleet's box, as there.
        fleets = sysfleets.bar_cells(bar, model["fleets"], s)
    for rect, _owner, f in fleets:
        hits.append((rect, ("fleet", f.index, model["nodes"][f.index])))
    pointer = mouse.pos()
    if model["viewable"] and model.get("asteroids"):
        screen._box_belts = (view, model)
    if not (model["viewable"] and sysfleets.hover(
            screen, surface, view, screen._state, model["star"], fleets,
            pointer, _texts(screen))):
        if not syswindow.planet_info(screen, surface, view, drawn, pointer):
            # TRANSCRIPTION `belt_hit`: no ship, no planet under the
            # pointer — then the grid scan's belt (mainscr.cpp:2141-2163)
            belt = belt_at(screen, *pointer)
            if belt is not None:
                syswindow.belt_info(screen, surface, view,
                                    belt[1]["planet"])


def belt_at(screen, x, y):
    """(native point, belt) of the asteroid belt the system window's grid
    scan finds under (x, y) (`sysorbits.belt_point`), or None."""
    drawn = getattr(screen, "_box_belts", None)
    if drawn is None or not drawn[0].collidepoint(x, y):
        return None
    return sysorbits.belt_point(drawn[1], (x, y))


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
    # where a press starts the painted selection (`boxpaint`): the box
    # below its title, the original's drag strip (fleetpop.cpp:142)
    box, head = r["fleet_box"], r["fleet_title"]
    screen._box_paint_area = pygame.Rect(box.x, head.bottom, box.w,
                                         max(0, box.bottom - head.bottom))
    cw, ch = grid.w // 3, grid.h // 3
    if model.get("scroll"):
        _draw_scroll(screen, surface, r["fleet_box"], grid, model["scroll"],
                     hits)
    records = model.get("records") or [None] * len(model["stack"])
    me = getattr(screen._state, "player_num", 0)
    cells = []
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
        cells.append(cell)
        if model["owners"][0] == me:
            # an own stack's cell, offered or not (`boxpaint.own_cell_at`)
            screen._box_own_cells.append(cell)
        if model["selectable"][i]:
            hits.append((cell, ("select", ship, not chosen)))
        img = cell_picture(screen, records[i], owner, cell)
        if img is not None:
            surface.blit(img, img.get_rect(center=cell.center))
        # TRANSCRIPTION `box_damage_bars`: over the picture (fleetpop.cpp:
        # 748-762)
        boxcells.draw_bar(surface, cell, boxcells.bar_for(
            records[i], model["owners"][0], me))
    # TRANSCRIPTION `box_scanned_name`: a cell under the pointer is the
    # scanned ship, and its text wins over the move line (fleetpop.cpp:
    # 1028-1031, mainscr.cpp:3422-3428)
    at = boxcells.scanned_index(cells, mouse.pos())
    scanned = None if at is None else boxcells.scanned_name(
        records[at], me, sysfleets.part_names(screen))
    screen._box_scanned = None if at is None else model["stack"][at]
    status, refused = boxcells.info_line(
        scanned, hover_status(screen) if at is None else None,
        model["status"])
    colour = REFUSED if refused else TEXT_COLOR
    syswindow.text(screen, surface, r["fleet_status"], status,
                   syswindow.font(screen, "fleet_status", 16), colour)


def cell_picture(screen, ship, owner, cell):
    """A fleet box cell's picture: its own ship's (HD EXTENSION
    `box_ship_picture`) fitted into 8/10 of the cell, else the owner's
    tinted map master at 7/10, as before (`sysfleets.icon`)."""
    side = min(cell.w, cell.h)
    if ship is not None and \
            ship_icons.kind_for_owner(owner) == ship_icons.PLAYER_KIND:
        state = getattr(screen, "_state", None)
        pic = ship_icons.ship_picture(
            getattr(screen, "_tints", None), ship, owner,
            getattr(screen, "_players", None),
            getattr(state, "player_num", None),
            getattr(getattr(screen, "app", None), "user_settings", None),
            side * 8 // 10, side * 8 // 10)
        if pic is not None:
            return pic
    return sysfleets.icon(screen, owner, side * 7 // 10)


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
    screen._box_belts = None
    screen._box_paint_area = None
    screen._box_own_cells = []
    screen._box_scanned = None
    screen._order_rects = {}
    screen._system_drawn = False
    for names, box, model in drawable(screen):
        r = _placed(screen, names, box)
        if r is None:
            continue
        offer = None
        if model["kind"] == "fleet":
            # the order buttons under CLOSE grow the box (work order 229 C)
            offer = fleetorders.offered(screen._state, model)
            r = fleetorders.place(r, names, offer["orders"],
                                  pygame.Rect(*screen._map_view().box))
        corners = None
        if model["kind"] == "system":
            # Data's decision 3 (work order 230 C): black with stars, the
            # blue frame and title panel — `syswindow.system_frame`
            panel, corners = syswindow.system_frame(screen, surface,
                                                    r[names[0]], r[names[1]])
            syswindow.title(screen, surface, panel, model["title"],
                            syswindow.font(screen, names[1], 20),
                            syswindow.native_scale(r[names[0]]))
        else:
            syswindow.frame(screen, surface, r[names[0]])
            syswindow.text(screen, surface, r[names[1]], model["title"],
                           syswindow.font(screen, names[1], 20),
                           syswindow.TITLE_COLOR)
        hits.append((r[names[0]], None))
        if model["kind"] == "system":
            screen._system_drawn = True
            screen._hover_star = None    # no map hover under it (226 F)
            _draw_system(screen, surface, r, model, hits)
            syswindow.text(screen, surface, r["system_text"],
                           model["wormhole"],
                           syswindow.font(screen, "system_text", 16),
                           TEXT_COLOR, "left")
        else:
            _draw_fleet(screen, surface, r, model, hits)
            # the fleet box's help, as `Set_Main_Screen_Help_List_`
            # appends it (evanhelp.cpp:239-273): 310 the band above the
            # buttons — HD's status line stands there — then 304 the
            # close button, and the order buttons' 305-309 (`fleetorders`).
            screen._box_help = [(r["fleet_status"], 310),
                                (r[names[-1]], 304)]
        close = r[names[-1]]
        syswindow.close_button(screen, surface, close,
                               syswindow.close_label(screen))
        hits.append((close, model["close"]))
        if corners is not None:
            # the rounded corners last, over all of it (work order 235);
            # the hit area stays the whole rectangle, so a click on a corner
            # the map now shows through is still the window's and swallowed
            syswindow.finish(screen, surface, corners)
        if offer is not None:
            fleetorders.draw(screen, surface, r, names, offer, hits,
                             screen._box_help)


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


def _fleet(screen, field, node):
    """A ship in the system window's bar: the original opens that stack's
    fleet box in the window's place (`Scan_System_Display_Fields_`,
    mainscr.cpp:2076-2083; `Do_Fleet_Popup_(icon, 0)`, mainscr_main.cpp:
    580-581, mainscr.cpp:1782-1860). The field goes out by index — the ship
    branch compares the field, never the pointer — and HD's click names the
    box that follows: the stack's head ship and the map icon whose node it
    is, where `Set_Popup_Draw_XY_` places the box (decision 65's identity)."""
    state = getattr(screen, "_state", None)
    icons = getattr(state, "ship_icons", None) or []
    nodes = ship_icons.wire_nodes(state) or []
    icon = next((i for i in icons if i.node_idx == node), None)
    if icon is not None and 0 <= node < len(nodes):
        screen._box_identity = boxmodel.Identity(
            "fleet", ship=nodes[node], icon=(icon.x, icon.y))
    _activate(screen, field, f"fleet of node {node}")


def handle_click(screen, x, y):
    """True when (x, y) is inside a drawn box. Fields go out by index; a
    ship cell sends MSG_SELECT_SHIP (open fix 21) with the opposite of the
    state the FSEL block showed; a ship in the system window's bar its
    field (`_fleet`)."""
    for rect, action in reversed(getattr(screen, "_box_hits", [])):
        if rect.collidepoint(x, y):
            if isinstance(action, tuple) and action[0] == "fleet":
                _fleet(screen, action[1], action[2])
            elif isinstance(action, tuple):
                _select(screen, action[1], action[2])
                # the press paints its cell first (`boxpaint`)
                boxpaint.start(screen, action[2], action[1])
            elif action is None:
                _inside(screen, x, y)
            else:
                _activate(screen, action, "field")
            return True
    return False


def _inside(screen, x, y):
    """A press on a box where it has no field of HD's own: an asteroid
    belt in the system window — the original's grid field takes the click
    at the point it scans (TRANSCRIPTION `belt_hit`: the engine opens the
    colony screen for an own colony there and box 217 for an own outpost,
    mainscr_main.cpp:567-577, mainscr.cpp:1567-1582; decision 35, the
    native point off the live list's fields); the fleet box beside its
    cells — the press starts a paint that selects (`boxpaint`)."""
    belt = belt_at(screen, x, y)
    if belt is not None:
        log.info("Box: asteroid belt, planet %s (grid click at %s)",
                 belt[1]["planet"], belt[0])
        if screen.app.connected:
            screen.app.client.inject_click(*belt[0])
        return
    area = getattr(screen, "_box_paint_area", None)
    if area is not None and area.collidepoint(x, y):
        boxpaint.start(screen, True)


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


def system_open(screen):
    """True while HD draws the star system window (the frame before): then
    the map under it takes nothing from the pointer — no hover name, no
    click, no wheel, no pan (work order 226 F, Data's decision 5; beside
    decision 66 and D13). The fleet box is not such a window: with it open
    a star click is the original's move order (decision 65 amended).

    DEVIATION system_window_blocks_map: the original's window is moveable
    box 0, whose fields Add_Map_Fields_ adds BESIDE the map's own: the
    map's grid field, through which a star or a ship is hit
    (mainscr_main.cpp:421-438), stays live around it
    (Add_Moveable_Box_Fields_ then Add_Grid_Field_, mainscr.cpp:1406,
    :1426; the window's fields mainscr.cpp:4391-4404). HD blocks the whole
    map while it is open, by Data's decision 5 of work order 226 F.
    Registered in `layout.json` `_markings`."""
    return bool(getattr(screen, "_system_drawn", False))

