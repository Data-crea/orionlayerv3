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
from screens.galaxy_map import ships as ship_icons

log = logging.getLogger("galaxy_map")


def mouse_motion(screen, screen_x, screen_y):
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


def click(screen, screen_x, screen_y):
    if screen.help_consumes_click(screen_x, screen_y):
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

    # THE RESEARCH WINDOW OPENS CHANGE MODE — work order 165 part B.
    # The sidebar's last window is the one whose handler does
    # something: it switches the game to SCREEN_TECH_CHANGE
    # (mainscr_main.cpp:697-713) and `screens/research_change/` is the
    # HD screen for it. The field is found in the LIVE list by shape,
    # never by a remembered index (decision 20) — the same rule
    # parking follows, and for the same reason: the turn-start research
    # prompt also reports screen 0, and its fields are choice rows.
    for _rw_box in ("sb_research_text", "sb_research_icon"):
        box = screen.box_rect(_rw_box)
        if not box or not pygame.Rect(*screen.layout.rect(box)).collidepoint(
                screen_x, screen_y):
            continue
        field = mapboxes.live_field(
            getattr(screen._state, "fields", None),
            screen._data.get("research_window_field"))
        if field is not None and screen.app.connected:
            activate(screen, field.index, "research window")
        return True

    # THE TREASURY WINDOW OPENS THE TAX RATE POPUP — work order 230 D
    # (mainscr_main.cpp:733-748): the sidebar's first window, found in the
    # live list by shape as the research window is; the popup is HD's
    # (`taxrate`, through the map's modal).
    for _tw_box in ("sb_treasury_text", "sb_treasury_icon"):
        box = screen.box_rect(_tw_box)
        if not box or not pygame.Rect(*screen.layout.rect(box)).collidepoint(
                screen_x, screen_y):
            continue
        field = mapboxes.live_field(
            getattr(screen._state, "fields", None),
            screen._data.get("treasury_window_field"))
        if field is not None and screen.app.connected:
            activate(screen, field.index, "treasury window")
        return True

    # THE COMMAND AND FREIGHTERS WINDOWS — work order 310 (309's finding 2),
    # TRANSCRIPTION sidebar_windows: the second and fourth windows
    # (mainscr.cpp:1566, :1568) compare the id as the others do
    # (mainscr_main.cpp:724-739): Command sets SCREEN_SHOW_COMMAND_POINTS
    # (43, under the guard `_skip_fields == 0`), Freighters
    # SCREEN_SCRAP_FREIGHTERS (35), or with no freighter the box HESTR 0xDF
    # (:726), which comes as MSGB. 35's `Scrap_Freighters_`
    # (mainscr2.cpp:253-300) opens HESTR 0xEC when none can be scrapped
    # (:259), the slider popup (0xED, :274), the confirmation 0xEE (:282)
    # and the result 0xEF (:288). Neither screen has an HD view: the F12 notice
    # names it (`core/screen_names.py`, decision 22). The food window has
    # no handler in the original, so a click there is swallowed below.
    for _sw_boxes, _sw_key, _sw_what in (
            (("sb_command_text", "sb_command_icon"),
             "command_window_field", "command window"),
            (("sb_freighters_text", "sb_freighters_icon"),
             "freighters_window_field", "freighters window")):
        if not any(screen.box_rect(b) and pygame.Rect(*screen.layout.rect(
                screen.box_rect(b))).collidepoint(screen_x, screen_y)
                for b in _sw_boxes):
            continue
        field = mapboxes.live_field(
            getattr(screen._state, "fields", None),
            screen._data.get(_sw_key))
        if field is not None and screen.app.connected:
            activate(screen, field.index, _sw_what)
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
        # OMISSION `box_cell_detail`: the original opens the ship's
        # detailed view on a right click on ANY cell of an own stack,
        # offered for selection or not (`Can_Select_Fleet_Box_Ship_`, the
        # owner only, mainscr.cpp:3526-3536; `Detailed_View_Ship_`,
        # :3638-3643; cmbtdrw1.cpp:227-324, v2); HD has no view and no wire
        # block for it (parked, work order 200 P-B1), so the right click on
        # such a cell does nothing — no pan.
        log.info("Right click on a fleet box cell: no ship view in HD")
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
    if not pygame.Rect(*view.box).collidepoint(mx, my):
        return
    if boxdraw.system_open(screen):
        return                           # the window covers the map (226 F)
    screen._viewctl.zoom_at(view, screen._state, mx, my, direction)
