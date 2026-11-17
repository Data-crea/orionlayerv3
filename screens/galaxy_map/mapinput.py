"""Galaxy map input — clicks, keys, the right button, the wheel, motion.

Split out of `screens/galaxy_map/screen.py` on 17 September 2026 (work order
126 F), along the seam the file already had: everything here answers "the
player did something, what goes to the game", and `screen.py` keeps loading,
geometry and drawing. Brief 110 part C's click reactions land here. Moves
only: the bodies are the methods they were, with `self` renamed `screen`,
and the screen's `handle_*` hooks call them. A function that consumed the
input returns True where the method used to return early, so the hook can
still fall through to `ScreenBase` exactly where it did.
"""
import logging

import pygame

from core import mapcoords as mc
from core import rightinfo
from core.screen_base import ScreenBase
from core.structs import star as star_struct
from screens.galaxy_map import boxdraw
from screens.galaxy_map import boxmodel
from screens.galaxy_map import boxpaint
from screens.galaxy_map import mapboxes
from screens.galaxy_map import mapclick
from screens.galaxy_map import mapeta
from screens.galaxy_map import mapmodal
from screens.galaxy_map import terrpanel
from screens.galaxy_map import ships as ship_icons

log = logging.getLogger("galaxy_map")


def mouse_motion(screen, screen_x, screen_y):
    if getattr(screen, "_territory_drag", False):
        terrpanel.drag(screen, screen_x, screen_y)
        return
    if screen._pan_from is not None:
        view = screen._map_view()
        if view is not None:
            dx = screen_x - screen._pan_from[0]
            dy = screen_y - screen._pan_from[1]
            if dx or dy:
                screen._viewctl.pan(view, screen._state, dx, dy)
                screen._pan_from = (screen_x, screen_y)
        return
    # the held button paints the fleet box's cells (`boxpaint`, 310)
    boxpaint.motion(screen, screen_x, screen_y)
    if boxdraw.system_open(screen):
        screen._hover_star = None        # the window covers the map (226 F)
        return
    screen._hover_star = screen._star_at(screen_x, screen_y)


def left_release(screen):
    """The left button's release, or its gesture cancelled: the fleet
    box's paint ends (mainscr_main.cpp:893-897)."""
    boxpaint.end(screen)
    terrpanel.release(screen)


#: The sidebar's windows: row key -> (layout.json field key, log name) and
#: the help id whose region is the row's band (help.json, evanhelp.cpp:4).
SIDEBAR_WINDOWS = {
    "treasury": ("treasury_window_field", "treasury window"),
    "command": ("command_window_field", "command window"),
    "food": (None, "food window"),
    "freighters": ("freighters_window_field", "freighters window"),
    "research": ("research_window_field", "research window"),
}
SIDEBAR_WINDOW_HELP = {"treasury": 286, "command": 288, "food": 290,
                       "freighters": 291, "research": 292}


def sidebar_window_band(screen, row):
    """The screen rect of one sidebar window: the row's help region (its
    boxes grown by `pad_y`, so neighbours touch) across the panel's full
    width, as the original's fields span the column (mainscr.cpp:1559-1568).
    None when the layout has neither."""
    spec = next((r for r in getattr(screen, "_help_regions", [])
                 if r.get("help_id") == SIDEBAR_WINDOW_HELP[row]), None)
    rect = screen.help_region_rect(spec) if spec else None
    if rect is None:
        return None
    panel = screen.box_rect("sidebar")
    if panel:
        panel = pygame.Rect(*screen.layout.rect(panel))
        rect = pygame.Rect(panel.x, rect.y, panel.w, rect.h)
    return rect


def sidebar_window_at(screen, x, y):
    """The row key of the sidebar window under (x, y), or None."""
    for row in SIDEBAR_WINDOW_HELP:
        band = sidebar_window_band(screen, row)
        if band is not None and band.collidepoint(x, y):
            return row
    return None


def click(screen, screen_x, screen_y):
    if screen.help_consumes_click(screen_x, screen_y):
        return True
    # The territory panel (HD EXTENSION `territory_view`) is HD's own and
    # sends nothing to the game; a click on it is never the map's.
    if terrpanel.click(screen, screen_x, screen_y):
        return True
    # The HUD title plate = the original's GAME button (top centre).
    # `title_rect` is the one function the drawing and the help use too.
    title = screen.title_rect()
    if title.collidepoint(screen_x, screen_y):
        screen.pressed.press("title", title)
        activate_spec(screen, screen._data.get("game_menu_field"),
                      "game menu")
        return True

    # Navigation buttons next — the HUD draws them over the map's floor,
    # so they are asked before the map is. Each is hit as the shape it
    # is drawn as (`nav_hit`, decision 5).
    for spec in screen._data.get("buttons", []):
        if screen.nav_hit(spec["key"], screen_x, screen_y):
            screen.pressed.press(spec["key"], screen.nav_rect(spec["key"]))
            activate_spec(screen, spec, spec["key"])
            return True

    # THE SIDEBAR'S FIVE WINDOWS — the whole row band, not the readout inside
    # it (TRANSCRIPTION `sidebar_window_bands`, mainscr.cpp:1559-1568: each
    # `Add_Hidden_Field` spans x 545-613 and a band of 70 native rows with
    # 2-3 between neighbours, so a click between two rows opens a window; work
    # order 402). `sidebar_window_at` is the one hit-test, the band the help
    # regions use. Each window keeps its own rule, found in the LIVE list by
    # shape, never by a remembered index (decision 20):
    #   Treasury   opens HD's tax rate popup (work order 230 D,
    #              mainscr_main.cpp:733-748; `taxrate`, through the map's modal)
    #   Research   switches to SCREEN_TECH_CHANGE (work order 165 B,
    #              mainscr_main.cpp:697-713; `screens/research_change/`) — the
    #              turn-start research prompt also reports screen 0, and its
    #              fields are choice rows, which is why the shape matters
    #   Command    SCREEN_SHOW_COMMAND_POINTS 43 under `_skip_fields == 0`;
    #   Freighters SCREEN_SCRAP_FREIGHTERS 35, or with no freighter the box
    #              HESTR 0xDF (:726), which comes as MSGB (work order 310,
    #              TRANSCRIPTION `sidebar_windows`, mainscr.cpp:1566, :1568,
    #              mainscr_main.cpp:724-739). 35's slider is HD's turn popup
    #              since open fix 104 (TPOP kind 20, id 80, work order 316),
    #              its boxes HD's message box; 43's Command Summary is HD's
    #              message box too (live work orders 310 and 378).
    #   Food       has no handler in the original: the click is swallowed.
    window = sidebar_window_at(screen, screen_x, screen_y)
    if window is not None:
        key, what = SIDEBAR_WINDOWS.get(window, (None, None))
        field = mapboxes.live_field(
            getattr(screen._state, "fields", None),
            screen._data.get(key)) if key else None
        if field is not None and screen.app.connected:
            activate(screen, field.index, what)
        return True

    # The info panel is not map: a click on it that no window took is
    # swallowed, never sent through to a star under the panel.
    side = screen.box_rect("sidebar")
    if side and pygame.Rect(*screen.layout.rect(side)).collidepoint(
            screen_x, screen_y):
        return True

    if boxdraw.handle_click(screen, screen_x, screen_y):
        return True
    view = screen._map_view()
    if view is not None and pygame.Rect(*view.box).collidepoint(
            screen_x, screen_y):
        if boxdraw.system_open(screen):
            # THE SYSTEM WINDOW IS OPEN: nothing reaches the map under it
            # (work order 226 F) — closed through its own CLOSE (decision 66).
            log.info("Map click ignored: the star system window is open")
            return True
        map_click(screen, view, screen_x, screen_y)
        return True

    return False


def map_click(screen, view, sx, sy):
    """One left click on the map: `mapclick.plan` decides, this sends.

    Icon or star first by the original's order, the native point the
    game resolves to the same object, and the decision-65 guard while
    the fleet box is open. An empty-map pixel goes HD -> galaxy through
    WHATEVER view is on screen, then galaxy -> native through the
    game's view, which is the one the click has to land in.
    """
    if screen._state is None:
        return
    # NOTHING GOES OUT WHILE THE GAME IS NOT ON THIS SCREEN. Decision 33:
    # refuse what the game would refuse — and it would refuse all of it,
    # because the native point this computes belongs to the map's field
    # space and another screen's list is a different space entirely
    # (decision 20, work order 128 C).
    #
    # It was already true and it was true BY ACCIDENT: the dispatcher
    # routes input to the top screen, so the map has no clicks to send
    # while the game is elsewhere. That is an exclusion that happens to
    # hold, not a rule — and the gate above (ships.ScreenStateGate) made
    # it worth saying out loud, because while the id is not 0 the state
    # this reads is the last screen-0 one and a click computed from it
    # would look perfectly reasonable. Work order 137 B.
    if getattr(screen._state, "current_screen",
               screen.GAME_SCREEN_ID) != screen.GAME_SCREEN_ID:
        log.info("Map click ignored: the game reports screen %s",
                 getattr(screen._state, "current_screen", None))
        return
    icons = getattr(screen._state, "ship_icons", None) or []
    owners = ship_icons.resolve_owners(
        icons, screen._ships, ship_icons.wire_nodes(screen._state))
    gx, gy = view.to_galaxy(sx, sy)
    orders_ok = boxdraw.orders_ok(screen)
    result = mapclick.plan(
        mapboxes.classify(getattr(screen._state, "fields", None)),
        screen._star_at(sx, sy),
        mapclick.icon_at(screen._map_context(), icons, owners,
                         screen._icon_anchor(),
                         screen._data.get("ship_icons") or {}, sx, sy),
        icons, owners, screen._stars, screen._state, screen._game_zoom(),
        mc.galaxy_to_native(gx, gy, screen._state),
        orders_ok=orders_ok)
    log.info("Map click: %s (%s)", result.what, result.detail)
    if result.send is not None and screen.app.connected:
        screen.app.client.inject_click(*result.send)
        boxmodel.remember(screen, result, icons, order=orders_ok)
        if orders_ok and result.what == "star" and \
                is_move_order(screen._state, screen._stars, result.target):
            screen._eta_lock = mapeta.hold(screen._state, screen._ships)


def is_move_order(state, stars, star_index):
    """True when a star click with HD's fleet box drawn is a move order the
    ETA lock is for (309's finding 16): the order's branch wants a ship of
    the box selected (`icon_selected_flag`, FSEL here) and a star that is no
    black hole (mainscr_main.cpp:479-482), and the merge-relocation mode's
    branch takes the click before it (:455-463; MREL, open fix 102).
    Otherwise the click gives no order and nothing is locked."""
    sel = getattr(state, "fleet_selection", None) or {}
    chain, flags = sel.get("chain") or [], sel.get("selected") or []
    if not any(flags[n] for n in chain if 0 <= n < len(flags)):
        return False
    if getattr(state, "merging_relocations", None):
        return False
    if star_index is None or not 0 <= star_index < len(stars):
        return False
    return not star_struct.is_black_hole(stars[star_index])


def activate_spec(screen, spec, what):
    """Activate the field `spec` names (type and native rect) in the LIVE
    list (decision 20, `core/livefields.py`), or send nothing.

    Until work order 243 the bottom bar, TURN and the GAME plate sent the
    index the old engine gave each (6, 7, 10-15). orion2re v2 adds five
    cheat hot keys before them (mainscr.cpp `Add_Cheats`), so every index
    moved by five and COLONIES opened the score: an index is a different
    field in every other list."""
    f = mapboxes.live_field(getattr(screen._state, "fields", None), spec)
    if f is None or not screen.app.connected:
        log.info("Action: %s — not in the live field list, nothing sent",
                 what)
        return
    activate(screen, f.index, what)


def activate(screen, field_id, what=""):
    log.info("Action: %s (field %s)", what or field_id, field_id)
    if screen.app.connected and field_id is not None:
        screen.app.client.activate_field(field_id)


def key_down(screen, key):
    if screen.help_consumes_key(key):
        return True
    if boxdraw.handle_key(screen, key):
        return True
    ping_key = screen._ping_key()
    if ping_key is not None and key == ping_key:
        # Consumed here on purpose: forwarding it would hand
        # orion2re a key it has no binding for.
        screen.ping_home()
        return True
    if terrpanel.key(screen, key):
        return True
    if key == pygame.K_g:
        activate_spec(screen, screen._data.get("game_menu_field"),
                      "game menu")
        return True
    if key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS,
               pygame.K_MINUS, pygame.K_KP_MINUS):
        view = screen._map_view()
        if view is not None:
            bx, by, bw, bh = view.box
            direction = (1 if key in (pygame.K_PLUS, pygame.K_EQUALS,
                                      pygame.K_KP_PLUS) else -1)
            screen._viewctl.zoom_at(view, screen._state,
                                    bx + bw // 2, by + bh // 2,
                                    direction)
        return True
    if key in (pygame.K_0, pygame.K_KP0):
        # Back to the full-galaxy view (mirror the parked game).
        screen._viewctl.reset()
        return True
    for spec in screen._data.get("buttons", []):
        hotkey = spec.get("hotkey")
        if hotkey and key == ord(hotkey):
            activate_spec(screen, spec, spec["key"])
            return True
    return False


def right_button(screen, down, mx, my):
    """Right button: context help first, then the game's cancel, then
    the pan drag.

    The original's help list for this screen covers the sidebar
    readouts, the bottom bar and the title, and pointedly NOT the
    map area (evanhelp.cpp:4). A right click on the map is not help
    but a CANCEL — it ends the relocation-merge mode and leaves zoom
    mode, and on a zoomed-in map scrolls it to the point clicked
    (layout.json `map_cancel`, DEVIATION map_cancel_scroll: HD's cancel
    lands at the grid's centre, so it scrolls nothing). So a press over
    the map sends that first, and the drag starts after.
    """
    if ScreenBase.handle_right_button(screen, down, mx, my):
        screen._pan_from = None
        return True
    if not down:
        screen._pan_from = None
        return False
    # The fleet box's help (work order 200 B) and a planet in the system
    # window: the game's colony info (`core/rightinfo`) — its field, not a
    # point on the map.
    hid = boxdraw.help_at(screen, mx, my)
    if hid is not None:
        entry = screen.helptext.entry(hid) or \
            screen.helptext.missing_entry(hid)
        screen.help.open(hid, *entry)
        return True
    planet = boxdraw.planet_field_at(screen, mx, my)
    if planet is not None:
        rightinfo.send(screen.app, rightinfo.field_at_index(screen.app, planet),
                       "planet colony info", rightinfo.opener(screen))
        return True
    if boxpaint.cell_at(screen, mx, my) is not None or \
            boxpaint.own_cell_at(screen, mx, my):
        # TRANSCRIPTION `box_cell_detail` (work order 317): the original
        # opens the ship's detail view on a right click on ANY cell of an
        # own stack, offered for selection or not — its field answered
        # negative is `Scan_Fleet_Movement_Box_Fields`' result 1
        # (`Can_Select_Fleet_Box_Ship_`, the owner only, mainscr.cpp:
        # 3526-3536; `Detailed_View_Ship`, :3637-3643; cmbtdrw1.cpp:227).
        # HD right-clicks that cell's own field (`core/rightinfo`); the view
        # is HD's with open fix 106 (`core/shipview.py`), the F12 notice
        # names it without (`ScreenBase.no_view_reason`). Never a pan.
        index = next((f for r, f in getattr(screen, "_box_cell_fields",
                                            None) or []
                      if r.collidepoint(mx, my)), None)
        field = None if index is None else \
            rightinfo.field_at_index(screen.app, index)
        # P816: the live list must still hold that cell's field — hidden,
        # 0x35 square (fleetpop.cpp:161-162) — at the moment of sending
        if field is None or field.field_type != 7 or \
                field.x_end - field.x != boxmodel.FLEET_ICON_SPAN or \
                field.y_end - field.y != boxmodel.FLEET_ICON_SPAN:
            log.info("Right click on a fleet box cell: its field is not in "
                     "the live list")
            return True
        rightinfo.send(screen.app, field, "ship detail view",
                       rightinfo.opener(screen))
        return True
    view = screen._map_view()
    if view is not None and boxdraw.system_open(screen):
        return False                     # no cancel, no pan (226 F)
    if view is not None and pygame.Rect(*view.box).collidepoint(
            mx, my):
        # DECISION 66: no positional right click while a box is open.
        # CANCEL_FIELD lands at the grid's CENTRE (ext_api.cpp:427-455),
        # which an open box may cover; a box is closed by its own
        # CLOSE field instead, never by a right click aimed at it.
        if not mapboxes.classify(getattr(screen._state, "fields",
                                         None)).open:
            send_map_cancel(screen)
        screen._pan_from = (mx, my)
    return False


def send_map_cancel(screen):
    """CANCEL_FIELD on the map's grid field, found in the live list.

    TRANSCRIBED (layout.json `map_cancel`). Returns the field index
    sent, or None when there was nothing to send to: no connection,
    or no field of that type and rect in the list at this moment —
    refused rather than aimed at a remembered index (decision 20).

    TRANSCRIPTION zoom_mode_exit: in the engine's own zoom mode the list
    has no grid field (`mapmodal.is_zoom_mode`); the original leaves the
    mode on any right click, a negative input (`Exit_Zooming_Mode_`,
    mainscr_main.cpp:396-403), so the cancel goes to the whole-screen
    field (`zoom_mode_field`), whose centre no '+' or '-' covers.
    """
    fields = getattr(screen._state, "fields", None)
    field = mapboxes.live_field(fields, screen._data.get("map_cancel"))
    if field is None and mapmodal.is_zoom_mode(screen, fields):
        field = mapboxes.live_field(fields,
                                    screen._data.get("zoom_mode_field"))
    if field is None or not screen.app.connected:
        log.debug("map cancel: no grid field in the list, nothing sent")
        return None
    screen.app.client.cancel_field(field.index)
    return field.index


def mousewheel(screen, direction, mx, my):
    """Wheel over the map zooms the HD viewport, at the pointer.

    The game is not told: the snapshot carries every star's
    galaxy coordinate, so the HD view scales and pans on its
    own. The first tick decouples from the game's slice;
    park_game then walks the game to maximum zoom-out so every
    click keeps resolving (see viewctl).
    """
    view = screen._map_view()
    if view is None:
        return
    if screen.help_consumes_wheel(direction):
        return
    if boxdraw.wheel(screen, mx, my, direction):
        return                           # the fleet box's own bar
    if not pygame.Rect(*view.box).collidepoint(mx, my):
        return
    if boxdraw.system_open(screen):
        return                           # the window covers the map (226 F)
    screen._viewctl.zoom_at(view, screen._state, mx, my, direction)
