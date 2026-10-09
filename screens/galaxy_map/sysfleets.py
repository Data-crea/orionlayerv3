"""The star system window's fleets: the bar at its bottom and what a fleet
under the pointer says — work order 228 B (the combat target window).

TRANSCRIPTION of the original's bar (`SYS::Build_System_Popup_Ships_`,
sys.cpp:2160-2190, and `Draw_System_Ship_Icons_`, :1018-1049): one icon per
owner with ships at the star (`location` the star, `status` below 3), in
slot = owner (:2172-2173), laid out left to right in the order the engine
met them (`Get_System_Display_Ship_Icon_XY_`, :2130-2158) — HD reads that
order off the icons' own fields, never recomputes it. A click on an icon is
the original's (the engine answers it; in the combat target window
`Check_System_Display_Fields_Defense_Selection_`, mainpups.cpp:3006-3036).

TRANSCRIPTION of the information under the pointer (`Do_Print_System_Ship_
Data_`, sys.cpp:1108-1324, in the darkened box at the view's corner,
:1033-1036): a monster's own name; for a player H 0x163 with the race's name
in the player's colour, then one line per hull size "%2d %s" (the hull's
name, its plural past one; `TECHDATA::_hull_data`, read as `shipparts`'
hulls and hull_plurals), then the colony ships (H 0x164 / 0x165), outposts
(0x166 / 0x167) and transports (0x168 / 0x169) by `N_Ships_By_Type_In_
Stack_` (:859-895).

DEVIATION `fleet_icon_drawn`: the original's bar pictures (BUFFER0.LBX 0x111
+ colour for a player, 0x119 and on for monsters, :988-1009) are not
extracted; HD draws the owner's map icon, as the fleet box does.
DEVIATION `fleet_stack`: the original counts the chain of the icon's own
stack (`_system_display_ships[owner].ship_idx`); HD counts the owner's ships
at the star by `Build_System_Popup_Ships_`'s condition — the same ships
while they form one stack, which ships at a star do.
OMISSION `fleet_line_indent`: the lines after the first stand 3 native px
in (:1238); HD prints them flush.
"""
import pygame

from core import hestrings
from core.structs import player as player_struct
from core.structs import ship as ship_struct
from screens.galaxy_map import ships as ship_icons

MAX_PLAYERS = 8
H_RACE_FLEET = 0x163
#: (one, more) for colony ships, outposts, transports (sys.cpp:1255-1316),
#: by `N_Ships_By_Type_In_Stack_`'s groups a, b, c (:859-895).
H_GROUPS = ((ship_struct.SHIP_TYPE_COLONY, 0x164, 0x165),
            (ship_struct.SHIP_TYPE_OUTPOST, 0x166, 0x167),
            (ship_struct.SHIP_TYPE_TRANSPORT, 0x168, 0x169))
HULLS = 9                       # SHIP_SIZE_DOOM_STAR + 1
#: `layout_state + width + 3`: the gap between two icons, native px.
ICON_GAP = 3


def entries(ships, fields):
    """[(owner, field)] of the bar: every slot with a field in the live
    list, in the engine's left-to-right order (the fields' x)."""
    by_index = {getattr(f, "index", None): f for f in fields or []}
    out = []
    for owner, slot in enumerate(ships or []):
        f = by_index.get(slot.get("field")) if slot.get("field", 0) > 0 \
            else None
        if f is not None and slot.get("ship", -1) > -1:
            out.append((owner, f))
    return sorted(out, key=lambda e: (e[1].x, e[0]))


def stack(state, star, owner):
    """The owner's ships at the star (`fleet_stack`)."""
    out = []
    for raw in getattr(state, "ships_raw", None) or []:
        if len(raw) < ship_struct.SIZE:
            continue
        s = ship_struct.parse(raw)
        if int(s.owner) == owner and int(s.location) == star and \
                int(s.status) < 3:
            out.append(s)
    return out


def lines(state, star, owner, text, parts):
    """[(text, gap_before)] the box prints for the owner's fleet. `text`:
    HESTRNGS (`core.hestrings`), `parts`: `ShipPartNames`."""
    ships = stack(state, star, owner)
    if not ships:
        return []
    if owner >= MAX_PLAYERS:
        return [(ships[0].name, False)]
    players = getattr(state, "player_raw", None) or []
    race = player_struct.parse(players[owner]).race_name \
        if 0 <= owner < len(players) else ""
    head = text.message(H_RACE_FLEET) if text is not None else None
    out = [(hestrings.printf(head, race) if head else race, False)]
    hulls = [0] * HULLS
    for s in ships:
        if s.ship_type == ship_struct.SHIP_TYPE_COMBAT:
            hulls[min(max(0, int(s.size)), HULLS - 1)] += 1
    for size, n in enumerate(hulls):
        if n > 0:
            name = parts.name("hulls" if n == 1 else "hull_plurals", size) \
                if parts is not None else None
            out.append(("%2d %s" % (n, name or ""), False))
    for kind, one, more in H_GROUPS:
        n = sum(1 for s in ships if s.ship_type == kind)
        if n > 0:
            fmt = text.message(one if n == 1 else more) \
                if text is not None else None
            out.append((hestrings.printf(fmt, n) if fmt else str(n), False))
    return out


def player_colour_index(state, owner):
    """The palette colour of a player's fleet (`_main_palette_player_
    colors[player.color]`, sys.cpp:1183-1186), None for a monster."""
    players = getattr(state, "player_raw", None) or []
    if not 0 <= owner < min(MAX_PLAYERS, len(players)):
        return None
    return int(player_struct.parse(players[owner]).color)


def icon(screen, owner, side):
    """The owner's map icon at `side` device px, tinted for a player — the
    fleet box's ship picture and the bar's (DEVIATION `fleet_icon_drawn`)."""
    kind = ship_icons.kind_for_owner(owner) or ship_icons.PLAYER_KIND
    key = ship_icons._resolve_sprite(screen._cache, kind, 0)
    if key is None:
        return None
    base = screen._cache.base(key)
    img = screen._cache.scaled(key, max(1, side * base.get_width()
                                        // max(base.get_width(),
                                               base.get_height())))
    if img is not None and kind == ship_icons.PLAYER_KIND:
        colour = ship_icons._player_color(screen._players, owner)
        if colour is not None:
            img = screen._tints.get(img, key, colour)
    return img


def draw_bar(screen, surface, bar, bar_entries, s):
    """The icons left to right in `bar`; returns [(rect, owner, field)]."""
    hits = []
    side = max(4, bar.h)
    x = bar.x
    gap = max(1, int(round(ICON_GAP * s)))
    for owner, field in bar_entries:
        cell = pygame.Rect(x, bar.y, side, side)
        if cell.right > bar.right:
            break
        img = icon(screen, owner, side * 8 // 10)
        if img is not None:
            surface.blit(img, img.get_rect(center=cell.center))
        hits.append((cell, owner, field))
        x += side + gap
    return hits
