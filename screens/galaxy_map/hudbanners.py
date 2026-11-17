"""What the main screen prints at the map's top edge from the wire: the
two event banners, the auto-turn banner and the multiplayer lights, and
the stop of the auto-turn chain — work order 403 (open fixes 114, 118, 119;
`core/mapbannerblocks.py` reads the blocks).

TRANSCRIPTION `warp_beast_banner` (mainscr_main.cpp:28-43): while
`EVENTS::Event_Check_Warp_Beast` holds, ESTR_BEAST (198) at the top left,
two lines above it and two below, pulsed.
TRANSCRIPTION `hyperspace_flux_banner` (:45-59): the same at the right with
H 0xE0, right-aligned. Both strings are the player's own (ESTRINGS, HESTRNGS), read
through the one loaders; a missing table draws no banner (decision 38).
TRANSCRIPTION `banner_pulse`: the word's colour is lifted by
`red_color_pulse_value * 5 / 9` (:31, :46), the counter the sidebar's red
numbers use (`sidebar.pulse_value`, DEVIATION `red_pulse_rate`: HD steps it
by elapsed time). HD EXTENSION `banner_colour`: the original's font colours
are palette ranges ('I'..'L' of font 3), HD lifts a fixed warm colour
(`sidebar.pulse_colour`). UNVERIFIED live: the colours against a native
screenshot.

TRANSCRIPTION `auto_turn_banner` (mainscr2.cpp:566-590): while the turns run
by themselves, the engine's own words "<race> stardate X.Y" in a darkened
box in the middle of the map. DEVIATION `auto_banner_box`: the box is HD's
size (the text plus a margin), centred in the map as the original centres
its own in the native map window; the colours are the HUD's, the original's
border takes the player's font colour.

TRANSCRIPTION `auto_turn_stop` (mainscr.cpp:2937-2947, fields.cpp
`Interpret_Mouse_Input`): the chain ends when `Get_Input` returns anything:
a click on the whole-screen hidden field that `Do_Next_Turn` adds while
"end of turn wait" is off (hotkey ESC), or the ESC key. A click reaches the
engine only if HD sends it, so a click activates that field (found in the
live list by its rectangle, never by a remembered index) and falls back to
ESC (the original has a third path HD does not copy: a mouse button held
while `Draw_Mini_Main_Screen` runs sets `auto_turn_exit`, mainscr.cpp:561-568). DEVIATION `auto_turn_any_key`: any other key stops it too (the
original's stops only on ESC). UNVERIFIED live.

TRANSCRIPTION `player_done_lights` (mainscr.cpp:2958-3005): in a hotseat or
network game, a coloured light per player who has pressed TURN, in player
order from the left; dimmed until every other human is done.
TRANSCRIPTION `diplomacy_lights` (:1067-1100): in a network game, one per
bit of the request mask, in player order from the right.
DEVIATION `lights_place`: the original draws at native x = 0x49 + n w and
0x1FA - n w, y 5 (above the map); HD draws them in the map's top edge,
round, in the owner colours.
INVENTION `lights_look`: the original's lights are animation frames
(`player_lights_seg`); HD draws discs, the diplomacy ones pulsing.
TRANSCRIPTION `multiplayer_help`: the help (302, 303) is the original's
list (evanhelp.cpp:229-237): 303 over the done lights in a hotseat and a
network game, 302 over the diplomacy lights in a game of type 2 only.
OMISSION `diplomacy_reply_popup`: the reply to a human's request
(mainscr.cpp:2475-2540, help 677-680) is not built.
"""
import logging

import pygame

from core import estrings, hestrings
from screens.galaxy_map import renderer
from screens.galaxy_map import sidebar as sb

log = logging.getLogger("galaxy_map.banners")

#: ESTR_BEAST (orion2_str.h:191) and the flux's HESTR message
#: (mainscr_main.cpp:52).
ESTR_BEAST = 198
HSTR_FLUX = 0xE0
ESC = 0x1B
#: Sizes in reference pixels (the layout scales them).
BANNER_FONT, BANNER_INSET, BANNER_TOP, BANNER_LINE = 26, 16, 58, 2
LIGHT_DIAMETER, LIGHT_GAP, LIGHT_INSET, LIGHT_TOP = 30, 10, 14, 6
LIGHT_SLOTS = 6                    # MAX_PLAYERS: the help band's width
PULSE_LEN = sb.PULSE_TOP
WARM = (214, 70, 54)
#: Seconds between two presses that stop the chain (a key held down).
STOP_GAP_S = 0.4
_stopped_at = {}


def _words(app):
    """(ESTRINGS, HESTRNGS) of the player's language, cached on the app."""
    held = getattr(app, "_banner_words", None)
    if held is None:
        language = (getattr(app, "settings", {}) or {}).get("language", "en")
        held = (estrings.EStrings(language), hestrings.for_app(app))
        app._banner_words = held
    return held


def banners_on(state):
    """(warp beast, hyperspace flux) as the wire says; both False without
    the block."""
    block = getattr(state, "map_banners", None) or {}
    return bool(block.get("warp_beast")), bool(block.get("hyperspace_flux"))


def left_edge(screen, rect, top, bottom):
    """The x the left-hand items start at: the map's inset edge, or the
    territory panel's right edge while that panel (HD's own, movable by the
    player) stands in the band `top`..`bottom` of the map's top.
    HD EXTENSION `clear_of_territory_panel`."""
    from screens.galaxy_map import terrpanel, terrview
    edge = rect.x + int(BANNER_INSET * screen.layout.scale)
    if terrpanel.shown(screen.app):
        found = terrpanel.rects(screen, len(terrview.legend(screen)))
        panel = found["panel"] if found else None
        if panel is not None and panel.top < bottom and panel.bottom > top:
            edge = max(edge, panel.right + int(BANNER_INSET * screen.layout.scale))
    return edge


def _banner(screen, surface, text, right, rect, now):
    s = screen.layout.scale
    size = screen.layout.font_size(BANNER_FONT)
    colour = sb.pulse_colour(WARM, now)
    img = screen.style.render_text(text, size, colour)
    inset = int(BANNER_INSET * s)
    y = rect.y + int(BANNER_TOP * s)
    x = rect.right - inset - img.get_width() if right else left_edge(
        screen, rect, y, y + img.get_height())
    line = max(1, int(BANNER_LINE * s))
    gap = max(2, int(4 * s))
    # two lines above and two below the word, as the original draws them
    # (mainscr_main.cpp:34-35, :40-41): the outer one in the first colour
    # LOOK EXCEPTION transcription: the banner's four lines in the word's own pulsed colours (mainscr_main.cpp:34-41)
    for k, shade in enumerate((colour, tuple(c * 3 // 4 for c in colour))):
        surface.fill(shade, (x, y - gap - (2 - k) * line, img.get_width(),
                             line))
        surface.fill(shade, (x, y + img.get_height() + gap + k * line,
                             img.get_width(), line))
    surface.blit(img, (x, y))


def render_banners(screen, surface, now=None):
    """The event banners over the map's top edge."""
    state = getattr(screen, "_state", None)
    beast, flux = banners_on(state)
    rect = screen.box_screen_rect("map_area")
    if rect is None or not (beast or flux):
        return
    now = sb._ticks() if now is None else now
    estr, hstr = _words(screen.app)
    if beast:
        text = estr.string(ESTR_BEAST)
        if text:
            _banner(screen, surface, text, False, rect, now)
    if flux:
        text = hstr.message(HSTR_FLUX)
        if text:
            _banner(screen, surface, text, True, rect, now)


def auto_turn(state):
    """The auto-turn block, or None. Only while the engine reports the
    turn's own id (12) or the report phase's (39): the block stays on the
    wire through the whole of `Do_Next_Turn`, so a combat or a popup in the
    chain is not the banner's and must get its input (review of WO 403)."""
    block = getattr(state, "auto_turn", None)
    screen_id = getattr(state, "current_screen", None)
    if block is not None and isinstance(screen_id, int) and \
            screen_id not in (12, 39):
        return None
    return block


def render_auto_banner(screen, surface):
    """The darkened box with the race and the stardate, mid-map."""
    block = auto_turn(getattr(screen, "_state", None))
    rect = screen.box_screen_rect("map_area")
    if block is None or rect is None or not block.get("text"):
        return
    size = screen.layout.font_size(BANNER_FONT)
    img = screen.style.render_text(block["text"], size, (240, 240, 248))
    pad = int(14 * screen.layout.scale)
    box = pygame.Rect(0, 0, img.get_width() + 2 * pad,
                      img.get_height() + 2 * pad)
    box.center = rect.center
    shade = pygame.Surface(box.size, pygame.SRCALPHA)
    shade.fill((0, 0, 0, 170))
    surface.blit(shade, box)
    # LOOK EXCEPTION marking: the auto-turn box's border in the banner's warm colour, as the original's box takes the player's colour
    pygame.draw.rect(surface, WARM, box, max(1, int(2 * screen.layout.scale)))
    surface.blit(img, (box.x + pad, box.y + pad))


def _slot(screen, rect, n, from_right):
    s = screen.layout.scale
    d = int(LIGHT_DIAMETER * s)
    step = d + int(LIGHT_GAP * s)
    inset = int(LIGHT_INSET * s)
    y = rect.y + int(LIGHT_TOP * s)
    x = (rect.right - inset - d - n * step) if from_right \
        else left_edge(screen, rect, y, y + d) + n * step
    return pygame.Rect(x, y, d, d)


def lights_rect(screen, kind):
    """The help band over one row of lights (help.json `lights`): the
    done lights' row from the left, the diplomacy lights' from the right;
    None without the block, and the diplomacy one outside a game of type 2
    (evanhelp.cpp:229-237)."""
    block = getattr(getattr(screen, "_state", None), "player_lights", None)
    rect = screen.box_screen_rect("map_area")
    if block is None or rect is None:
        return None
    if kind == "diplomacy" and block["game_type"] != 2:
        return None
    if kind == "done" and block["game_type"] not in (1, 2):
        return None            # evanhelp.cpp:229-237: types 1 and 2 only
    first = _slot(screen, rect, 0, kind == "diplomacy")
    last = _slot(screen, rect, LIGHT_SLOTS - 1, kind == "diplomacy")
    band = first.union(last)
    return band.inflate(int(LIGHT_GAP * screen.layout.scale),
                        int(LIGHT_TOP * 2 * screen.layout.scale))


def _disc(surface, rect, colour, bright, ring=(12, 12, 16)):
    shade = colour if bright else tuple(c * 2 // 5 for c in colour)
    pygame.draw.ellipse(surface, shade, rect)
    pygame.draw.ellipse(surface, ring, rect, max(1, rect.w // 10))


def render_lights(screen, surface, now=None):
    """The multiplayer lights in the map's top edge."""
    block = getattr(getattr(screen, "_state", None), "player_lights", None)
    rect = screen.box_screen_rect("map_area")
    if block is None or rect is None:
        return
    now = sb._ticks() if now is None else now
    players = block["players"]
    n = 0
    for done, colour in players:                  # Draw_Player_Done_Lights
        if done:
            _disc(surface, _slot(screen, rect, n, False),
                  renderer.OWNER_COLORS.get(colour, renderer.NEUTRAL_COLOR),
                  block["bright"])
            n += 1
    n = 0
    lit = sb.pulse_value(now) >= PULSE_LEN // 2
    for i, (_done, colour) in enumerate(players):  # Draw_Diplomacy_Request_Lights
        if block["game_type"] in (2, 3) and (block["request_mask"] >> i) & 1:
            _disc(surface, _slot(screen, rect, n, True),
                  renderer.OWNER_COLORS.get(colour, renderer.NEUTRAL_COLOR),
                  lit)
            n += 1


def render(screen, surface):
    """Everything this module draws, above the map's HUD."""
    render_banners(screen, surface)
    render_lights(screen, surface)
    render_auto_banner(screen, surface)


# ── stopping the auto-turn chain ─────────────────────────────────────────

def exit_field(state):
    """The whole-screen hidden field that ends the chain, from the LIVE
    list: the block's index when that field still has the rectangle, else
    the first ESC field of 0,0-639,479; None when the list has none."""
    block = auto_turn(state) or {}
    fields = getattr(state, "fields", None) or []
    whole = [f for f in fields if getattr(f, "index", 0) > 0
             and (f.x, f.y, f.x_end, f.y_end) == (0, 0, 639, 479)]
    named = [f for f in whole if f.index == block.get("exit_field")]
    return (named or [f for f in whole if getattr(f, "hotkey", 0) == ESC]
            or [None])[0]


def stop_chain(screen, why, now=None):
    """Stop the turns that run by themselves: a click activates the
    whole-screen field, a key (or a click with no such field) sends ESC.
    True when the input was the chain's (consumed), False when no chain
    runs. Once per STOP_GAP_S, so a held key is not a flood."""
    client = getattr(screen.app, "client", None)
    state = getattr(client, "state", None) or getattr(screen, "_state", None)
    if auto_turn(state) is None:
        return False
    if not getattr(screen.app, "connected", False):
        return True
    import time
    now = time.monotonic() if now is None else now
    if now - _stopped_at.get(id(screen), -1e9) < STOP_GAP_S:
        return True
    _stopped_at[id(screen)] = now
    field = exit_field(state) if why == "click" else None
    if field is not None:
        log.info("auto turn: %s -> field %d", why, field.index)
        client.activate_field(field.index)
    else:
        log.info("auto turn: %s -> ESC", why)
        client.inject_key(ESC)
    return True
