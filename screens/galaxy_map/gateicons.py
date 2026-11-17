"""The galaxy map's gate icons and its visited-star dots — work order 402
(package 1), two small decorations the original draws with the stars.

THE GATE ICONS (`Draw_A_Gate_Icon_`, mainscr.cpp:916-1010, called for every
star by `Draw_Gate_Icons_`: in the live frame after the black holes and
BEFORE `Draw_Stars_` (mainscr_main.cpp:968, :988), in the overview redraw
after the stars, mainscr.cpp:746-751): beside the name of a system the
local player has VISITED, the Dimensional Portal's icon (BUFFER0.LBX
19 + zoom_offset) and the Artemis Net's (31 + zoom_offset) for the player's
own bit of `star.has_dimensional_portal` / `has_artemis_net`
(`Player_Has_Dimensional_Portal_`, harold.cpp:524-536).

  TRANSCRIPTION  `map_gate_icons`: with one icon it stands left of the star
                 (its right edge 4 native px from the star's centre), with
                 two the portal left and the net right (4 px from the
                 centre); an icon's bottom is the star's bottom edge, the
                 portal's 2 px lower (mainscr.cpp:962-993). The star gate
                 and the jump gate are asked and ignored (:924-926), so
                 only these two icons exist, and the original's cases of 3
                 and 4 icons (a 75 x 20 composite, :995-1010) can never be
                 reached: not built.
  DEVIATION      `gate_over_stars`: HD draws the icons over the stars (the
                 overview redraw's order, mainscr.cpp:746-751), the live
                 loop draws the stars over them (mainscr_main.cpp:968,
                 :988); the star sprites are drawn earlier by the map
                 renderer and an icon stands beside the star, so the
                 overlap is a few pixels at most. UNVERIFIED live.
  DEVIATION `map_gate_icon_drawn`: the pictures are the player's files
                 (not extracted), so HD draws what the system window draws
                 (`sysextras._picture` / `_drawn`, its `gate_icon_drawn`),
                 one 11 native px square at every zoom: the original's
                 picture is the zoom's (zoom_offset 2 at the nearest zoom,
                 3 elsewhere), whose sizes are UNVERIFIED (not measured;
                 no live run, Data's decision of 20 October 2026).

THE VISITED DOT (`Draw_A_Star_`, mainscr.cpp:588-628 and :113-131,
`MAP_SCALE::Uses_Visited_Uncolonized_Overview_Marker_`, map_scale.h:134):

  TRANSCRIPTION  `visited_dot`: on an extended galaxy at its widest zoom,
                 where no names are printed, a visited star nobody owns
                 (`owner == -1`, not a black hole) gets a 2 x 2 native px
                 dot at (x - 1, y + star height / 2 + 1) in the local
                 player's colour.
  DEVIATION      `visited_dot_colour`: the original's colour is the
                 player's palette base + 5 (22 for base 32); HD uses the
                 player's colour from the skin.
  UNVERIFIED     `overview_markers`: `Use_Main_Map_Overview_Markers_`
                 (mainscr.cpp:74-111, :628-640) swaps the sprites for
                 coloured dots on a Maximum galaxy when `main_map_overview_
                 markers` is set; it is false in the engine's config
                 (mainscr_config.cpp:6) and nothing on the wire says the
                 player changed it. Not built.
"""
import pygame

from core.structs import star as star_struct
from screens.galaxy_map import renderer as rnd
from screens.galaxy_map import sysextras

#: Native px: an icon's side (the system window's 12 px step less its
#: gap), its distance from the star's centre, the portal's drop.
SIDE, GAP, PORTAL_DROP = 11, 4, 2
#: The dot: its side and its place under the star (native px).
DOT_SIDE, DOT_DROP = 2, 1

_PICTURES = {}
PICTURE_KEEP = 16


def _picture(kind, side):
    """A mod's picture of the icon at `side` px, or None (drawn in code).
    Cached: `sysextras._picture` reads the file every call."""
    key = (kind, side)
    if key not in _PICTURES:
        if len(_PICTURES) >= PICTURE_KEEP:
            _PICTURES.clear()
        _PICTURES[key] = sysextras._picture(None, kind, side)
    return _PICTURES[key]


def icons(star, player_num):
    """["portal", "artemis"] the local player has at `star`, in the
    original's order (portal first)."""
    bit = 1 << (player_num & 0x1F)
    out = []
    if int(getattr(star, "has_dimensional_portal", 0) or 0) & bit:
        out.append("portal")
    if int(getattr(star, "has_artemis_net", 0) or 0) & bit:
        out.append("artemis")
    return out


def places(star_icons, sx, sy, ih, px):
    """[(kind, Rect)] of the icons of one star (TRANSCRIPTION
    `map_gate_icons`) for a star centred at (sx, sy), `ih` px high."""
    side = max(4, int(round(SIDE * px)))
    gap = int(round(GAP * px))
    bottom = sy + ih / 2.0
    out = []
    for n, kind in enumerate(star_icons):
        # the first icon is on the left, a second one on the right
        x = sx - side - gap if n == 0 else sx + gap
        drop = PORTAL_DROP * px if kind == "portal" else 0
        out.append((kind, pygame.Rect(int(round(x)),
                                      int(round(bottom - side + drop)),
                                      side, side)))
    return out


def render_gates(surface, ctx, stars, heights, player_num):
    """Every visited star's gate icons, over the stars and under the
    names."""
    view = ctx.view
    for s in stars:
        if not star_struct.visited_by(s, player_num):
            continue
        have = icons(s, player_num)
        if not have:
            continue
        sx, sy = view.to_screen(s.x, s.y)
        for kind, rect in places(have, sx, sy, heights.get(s.index, 0),
                                 ctx.px):
            img = _picture(kind, rect.w)
            if img is not None:
                surface.blit(img, rect.topleft)
            else:
                sysextras._drawn(surface, rect, kind)


def dot_wanted(ctx, s, player_num):
    """TRANSCRIPTION `visited_dot`: `Uses_Visited_Uncolonized_Overview_
    Marker_` — an extended galaxy at its widest zoom, not a black hole,
    owner -1, visited."""
    return (ctx.names_hidden and not star_struct.is_black_hole(s)
            and int(s.owner) == -1
            and star_struct.visited_by(s, player_num))


def render_dots(surface, ctx, stars, heights, player_num, players):
    """The visited-uncolonized dots (see the module doc)."""
    if not ctx.names_hidden:
        return
    local = players[player_num] if 0 <= player_num < len(players) else None
    colour = rnd.OWNER_COLORS.get(getattr(local, "color", None))
    if colour is None:
        return          # the original draws none for a colour past 7
    side = max(1, int(round(DOT_SIDE * ctx.px)))
    for s in stars:
        if not dot_wanted(ctx, s, player_num):
            continue
        sx, sy = ctx.view.to_screen(s.x, s.y)
        y = sy + heights.get(s.index, 0) / 2.0 + DOT_DROP * ctx.px
        # LOOK EXCEPTION transcription: the original's 2 x 2 dot of the
        # player's colour (`Draw_Visited_Uncolonized_Star_Marker`)
        surface.fill(colour[:3], (int(round(sx - ctx.px)), int(round(y)),
                                  side, side))
