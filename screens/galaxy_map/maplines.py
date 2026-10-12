"""Lines on the galaxy map, and the ONE routine that draws every one of them.

HD EXTENSION — B1 (Data, brief 111): every line on the HD map is
antialiased, through `stroke` and nothing else. MOO2 is palette-indexed and
cannot antialias: `line::Line_` and `line::Multi_Colored_Line_` (line.cpp)
plot hard one-pixel lines. The wormhole link was antialiased before this
rule existed, and unmarked (brief 110 Stop 1); it goes through `stroke`
now, and the smoke test holds `aaline` to this module among the galaxy
map's.

SHIP DESTINATION LINES — TRANSCRIBED from SHIPS::Do_Ship_Destination_Lines_
(ships.cpp:423-480):
  * an icon gets a line when its ship is the local player's and not bound
    for Antares (`Absolute_Location_ != _NUM_STARS`); or is foreign, not
    parked (status != 0) and bound for a star where the local player has a
    colony (`has_colony` bit) or where ANY outpost stands —
    `HAROLD::Player_Has_Outpost_` ignores its player argument
    (harold.cpp:990), and so does this; or is the head node of the stack
    the open fleet box shows (`Node_Ptr_From_Ship_Stack_`, the FSEL chain's
    first node);
  * and only while its location is encoded, 10000 <= location < 30000, and
    bound for a real star — so from the turn of the order (20000 + star)
    on, not a turn later as the map's "eta N" (run 114), which is
    `mapeta` (work order 122, item 2.1);
  * green table for the local player's ship, red for any other
    (`_ship_direction_line_green/red_colors`, mainscr.cpp:105-106);
  * from the icon's corner plus half the header size of BUFFER0.LBX entry
    205 + (3 - zoom) (`Draw_Ship_Destination_Line_`, ships.cpp:535-566;
    `zoomtables.SHIP_ICON_HEADER_DIM`) to the star's centre.
  The RGB of both tables is the main palette's, read from two sources in
  brief 121 and identical: live off VISUAL_FRAME and from FONTS.LBX entry 1.

THE COLOUR WAVE — TRANSCRIBED. `line::Multi_Colored_Line_` (line.cpp:5ff)
clips, puts the endpoint with the smaller y first, and plots one table
colour per pixel along the major axis, counting up from `offset`.
`SHIPS::Draw_Directional_Multi_Colored_Line_` (ships.cpp:258-287) picks the
table order and the offset (phase or 7 - phase) from the direction. The
main loop advances the phase by one per pass (mainscr_main.cpp:1036-1037),
and a pass lasts at least one 55 ms tick (`Mark_Time_` :394,
`Release_Time_(1)` :906, timer.cpp:14-15).

HD EXTENSION — B2 (Data, brief 112, option 1): one table step is `ctx.px`
HD pixels — a period of 8 native pixels times ctx.px, following the
continuous zoom like all map geometry — and never less than one HD pixel,
so a far zoom does not dissolve the wave into flicker. The phase runs on a
fixed 55 ms clock, the original's lower bound per pass, not on HD's frame
rate.

DELIBERATE DEVIATION — the HD ship icon is NOT the size this module
positions with. Data's decision of 15 September 2026, work order 122 item
2.2. The line starts from the icon corner plus half of the game's sprite
HEADER, `zoomtables.SHIP_ICON_HEADER_DIM` = ((11, 11), (12, 11), (12, 10), (16, 12))
(entry 205 + (3 - zoom), measured in brief 121), while the HD icon is drawn
and hit-tested at `zoomtables.SHIP_ICON_DIM` = ((11, 10), (10, 9), (9, 8), (8, 7)),
indexed by zoom: 9 x 8 at zoom 2 against a 12 x 11 header. The two tables
answer different questions — where the game anchors its sprite, and how
large HD draws its own artwork — and the icon's click area at 9 x 8 is
live-confirmed, so neither is corrected towards the other. The smoke test
fails if the tables become equal, or if either changes while this note and
the comment on the other table still quote the old values.

THE PREVIEW LINE ON HOVER — TRANSCRIBED since work order 188 (it was an
OMISSION: its colour is the move result, which was not on the wire; open
fix 48's FMOV puts the engine's own verdict for every star there).
`MAINSCR::Draw_ETA_Destination_Line_` (mainscr.cpp:535-568): with the fleet
box's ships selected and the pointer on a star, the same colour wave from
the box's head icon (its corner plus half the header, as above) to the
star, under the stars; green when `moving != 0 && turns_left != 0`, red
when `blackhole_blocks || hyperspace_flux || (out_of_range && !immobile)`
(:558-567). The verdict is FMOV's, never recomputed here.
HD EXTENSION `hover_line` (Data's decision, 28 Sep — work order 188 Part 3,
"The dashed line appears as soon as the mouse hovers over a star/planet
... and disappears when the mouse leaves. Green: the ship can reach it.
Red: it cannot."), where it differs from the original:
  * the line LEAVES with the pointer — the original keeps `_eta_star_id` on
    the last star hovered until another star or a ship icon is hovered, the
    selection is emptied or an order given (mainscr_main.cpp:504, 539, 542,
    593, 902, 917);
  * RED also where the original draws NO line although the ship cannot go
    there: an immobile fleet (`immobile`, speed 0) and a black hole as the
    target (the original sets `_eta_star_id` to -1 there,
    mainscr_main.cpp:538-540). The one star with no line is the one the
    fleet already stands at (`moving` with `turns_left` 0).

OMISSION, each with its reason:
  * relocation lines (`Draw_Relocation_Links_`, mainscr.cpp:682-703):
    **HALF OF THIS REASON IS SPENT, and the omission stands on the
    other half.** It read "the setting and `relocate_ship_to` (star
    offset 205) are not verified". Work order 144 verified offset 205
    by the header route with twelve agreeing offsets and the struct
    size — `core/structs/star.RELOCATE_OFFSET` carries the derivation —
    and the Fleets minimap now draws these lines from it
    (`fltdraw.draw_relocation_lines`), sharing this module's
    `relocation_pairs`, `directional`, `wave_pieces` and `stroke`.

    What still blocks THIS screen is the other half:
    `_settings.show_relocation_lines` gates the galaxy map's loop
    (mainscr.cpp:690) and does not gate the minimap's at all
    (flt1.cpp:1480). The byte is at offset 8 of `s_settings` — nine
    leading `uint8_t`, unambiguous — and `settings_raw` is on the wire,
    but nothing has confirmed that the option is reachable in this
    build's options screen, so drawing the galaxy map's lines would
    mean guessing at whether a player can turn them off. Parked as
    question 4 in `dev:doc/briefs/144-parked-for-data.md`.

    Not deleted and not quietly satisfied: the data is shared, the look
    is not, and this screen's own gate has still not been read.
"""
import math

import pygame

from core import palette
from core import zoomtables as zt
from core.structs import colony as colony_struct
from core.structs import planet as planet_struct
from core.structs import ship as ship_struct
from core.structs import star as star_struct
from screens.galaxy_map import ships as ship_icons

#: mainscr.cpp:105-106, indices 6E 6F 72 74 74 72 6F 6E and 49 4A 4D 4F
#: 4F 4D 4A 49 — their RGB lives in the skin (decision 14), measured.
GREEN = tuple(tuple(c) for c in palette.require("galaxy_map",
                                                 "travel_line_green"))
RED = tuple(tuple(c) for c in palette.require("galaxy_map",
                                               "travel_line_red"))
#: One colour per step, eight per period (line.cpp, `color_index & 7`).
PERIOD = 8
#: The phase clock: one step per 55 ms (HD EXTENSION B2, see above).
PHASE_MS = 55
#: SHIP_LOCATION_MOVING_OFFSET and SHIP_LOCATION_LIMIT (ships.cpp:454).
LOCATION_ENCODED = ship_struct.LOCATION_MOVING_OFFSET
LOCATION_LIMIT = ship_struct.LOCATION_LIMIT


def stroke(surface, colour, a, b):
    """THE line primitive of the HD map — HD EXTENSION B1, antialiased."""
    pygame.draw.aaline(surface, tuple(colour[:3]), a, b)


def relocation_pairs(state, player_num):
    """`(star_index, target_index)` for every relocation `player_num` has.

    **THE SHARED FACT BEHIND TWO DRAWINGS.** The Fleets minimap and the
    galaxy map draw relocation lines from the SAME data —
    `HACCESS::Star_Has_Relocation_` is `relocate_ship_to[player] != -1`
    and `HACCESS::Relocation_` returns the value (haccess.cpp:113-119),
    and both `FLT1::Draw_Fltscrn_Relocation_Lines_` (flt1.cpp:1480-1487)
    and `MAINSCR::Draw_Relocation_Links_` (mainscr.cpp:691-697) walk
    every star testing exactly that. So the fact lives here, once, and
    each screen supplies its own transform — which is decision 68 for
    the part of a line that is not the stroke.

    What the two screens do NOT share is the look, and that is the
    original's doing, not ours:

      * colours — the minimap's table is palette 6,7,7,8,8,9,9,10
        (flt1.cpp:1460-1467), a GREY ramp in FONTS.LBX 9; the galaxy
        map's is 0x6E,0x6F,0x70,0x70,... (mainscr.cpp:684), the green
        of the travel lines
      * direction — the minimap draws star -> target
        (flt1.cpp:1486 through ships.cpp:558-566), the galaxy map draws
        star -> target as well (mainscr.cpp:697); the minimap's ends
        are nudged +4 at the star and +3 at the target
      * gating — the galaxy map is inside
        `if (_settings.show_relocation_lines != 0)` (mainscr.cpp:690);
        **the minimap is not gated at all**

    Underneath, both end in `SHIPS::Draw_Directional_Multi_Colored_Line_`
    with `_multi_colored_line_start`, which `directional`, `phase_at`
    and `wave_pieces` above already transcribe. One routine, two
    tables.
    """
    out = []
    for index, star in enumerate(state.stars or []):
        target = star_struct.relocation_target(star, player_num)
        if target is not None and 0 <= target < len(state.stars):
            out.append((index, target))
    return out


def phase_at(ms):
    """`_multi_colored_line_start` on HD's fixed 55 ms clock."""
    return int(ms // PHASE_MS) % PERIOD


def directional(x1, y1, x2, y2, table, phase):
    """(table, offset) as `Draw_Directional_Multi_Colored_Line_` picks them
    for a line from (x1, y1) to (x2, y2)."""
    inverse = max(0, 7 - phase)
    reverse = tuple(reversed(table))
    if x1 < x2:
        return (table, inverse) if y1 <= y2 else (reverse, phase)
    return (table, inverse) if y1 < y2 else (reverse, phase)


def clip(a, b, box):
    """The part of segment a-b inside `box` (x, y, w, h), or None —
    Liang-Barsky; `Clip_Line_` clips before the wave is counted."""
    x0, y0 = box[0], box[1]
    x1, y1 = box[0] + box[2], box[1] + box[3]
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay)):
        if p == 0:
            if q < 0:
                return None
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return None
    return ((ax + dx * t0, ay + dy * t0), (ax + dx * t1, ay + dy * t1))


def wave_pieces(a, b, table, offset, step):
    """[(colour, p, q)] along a-b: `Multi_Colored_Line_` with one table
    step of `step` HD pixels along the major axis (at least 1)."""
    (ax, ay), (bx, by) = a, b
    if by < ay:
        ax, ay, bx, by = bx, by, ax, ay
    major = max(abs(bx - ax), abs(by - ay))
    if major == 0:
        return [(table[offset % PERIOD], (ax, ay), (bx, by))]
    step = max(1.0, step)
    pieces = []
    for k in range(max(1, math.ceil(major / step))):
        t0, t1 = k * step / major, min(1.0, (k + 1) * step / major)
        pieces.append((table[(offset + k) % PERIOD],
                       (ax + (bx - ax) * t0, ay + (by - ay) * t0),
                       (ax + (bx - ax) * t1, ay + (by - ay) * t1)))
    return pieces


def _our_colony_or_any_outpost(state, star, player_num):
    """`Player_Has_Colony_` (harold.cpp:423) or `Player_Has_Outpost_`."""
    if (int(star.has_colony) >> (player_num & 0x1F)) & 1:
        return True
    planets = getattr(state, "planets_raw", None) or []
    colonies = getattr(state, "colonies_raw", None) or []
    for index in star_struct.planet_indices(star):
        if not 0 <= index < len(planets):
            continue
        colony = planet_struct.parse(planets[index]).colony_index
        if 0 <= colony < len(colonies) and \
                colony_struct.parse(colonies[colony]).outpost_flag != 0:
            return True
    return False


def destination_lines(state, ships, stars, game_zoom):
    """The icons that get a destination line, as dicts: `icon`, `ship`,
    `star`, `colour` ("green"/"red") and `start`, the native point at the
    icon. Empty without open fix 20's node table (no ship per icon)."""
    nodes = ship_icons.wire_nodes(state)
    if nodes is None:
        return []
    me = getattr(state, "player_num", 0)
    sel = getattr(state, "fleet_selection", None)
    head = (sel["chain"][0] if sel and sel["stack"] >= 0 and sel["chain"]
            else None)
    hw, hh = zt.ship_icon_header_dimension(3 - game_zoom)
    out = []
    for i, icon in enumerate(getattr(state, "ship_icons", None) or []):
        node = icon.node_idx
        if not 0 <= node < len(nodes) or not 0 <= nodes[node] < len(ships):
            continue
        ship = ships[nodes[node]]
        dest = ship_struct.absolute_location(ship.location)
        own = ship.owner == me
        moving = own and dest != len(stars)
        enemy = (not own and ship.status != 0 and 0 <= dest < len(stars)
                 and _our_colony_or_any_outpost(state, stars[dest], me))
        if not (moving or enemy or node == head):
            continue
        if not LOCATION_ENCODED <= ship.location < LOCATION_LIMIT \
                or not 0 <= dest < len(stars):
            continue
        out.append({"icon": i, "ship": nodes[node], "star": dest,
                    "colour": "red" if enemy or not own else "green",
                    "start": (icon.x + (hw >> 1), icon.y + (hh >> 1))})
    return out


def render_destination_lines(surface, ctx, state, ships, stars, game_zoom,
                             anchor, ms):
    """Draw every destination line, under the stars (mainscr_main.cpp:965)."""
    from core import mapcoords as mc
    lines = destination_lines(state, ships, stars, game_zoom)
    if not lines:
        return
    phase = phase_at(ms)
    view = ctx.view
    icons = state.ship_icons
    for line in lines:
        star = stars[line["star"]]
        nx, ny = line["start"]
        sx, sy = mc.galaxy_to_native(star.x, star.y, state)
        table, offset = directional(nx, ny, sx, sy,
                                    RED if line["colour"] == "red" else GREEN,
                                    phase)
        a = ship_icons.anchored_point(icons[line["icon"]], nx, ny, ctx,
                                      anchor)
        seg = clip(a, view.to_screen(star.x, star.y), view.box)
        if seg is None:
            continue
        for colour, p, q in wave_pieces(seg[0], seg[1], table, offset,
                                        ctx.px):
            stroke(surface, colour, p, q)


def preview_colour(verdict, black_hole=False):
    """"green", "red" or None for one star's FMOV verdict.

    Transcribed (mainscr.cpp:558-567): green when the move is legal and
    takes a turn; red on a black hole in the way, flux, or out of range.
    HD EXTENSION `hover_line` (Data's decision, 28 Sep): red too for an
    immobile fleet and a black hole as the target, where the original
    draws nothing; None only at the star the fleet already stands at."""
    if verdict is None:
        return None
    if black_hole:
        return "red"                 # HD EXTENSION: never a destination
    if verdict["moving"] and verdict["turns_left"]:
        return "green"
    if verdict["moving"] and not verdict["turns_left"]:
        return None                  # already there: nothing to preview
    if verdict["blackhole_blocks"] or verdict["hyperspace_flux"] or \
            (verdict["out_of_range"] and not verdict["immobile"]):
        return "red"
    return "red"                     # HD EXTENSION: immobile, black hole


def preview_line(state, star_index, game_zoom, black_hole=False):
    """`{"icon", "star", "colour", "start"}` for the hovered star, or None:
    FMOV's verdict (open fix 48) for the fleet box's selection, from the
    box's head icon (the FSEL chain's first node, `Node_Ptr_From_Ship_Stack_`,
    mainscr.cpp:545-553)."""
    move = getattr(state, "fleet_move", None)
    sel = getattr(state, "fleet_selection", None)
    if not move or not sel or sel["stack"] < 0 or not sel["chain"]:
        return None
    if not any(sel["selected"][n] for n in sel["chain"]
               if 0 <= n < len(sel["selected"])):
        return None
    verdicts = move["verdicts"]
    if star_index is None or not 0 <= star_index < len(verdicts):
        return None
    colour = preview_colour(verdicts[star_index], black_hole)
    if colour is None:
        return None
    head = sel["chain"][0]
    icons = getattr(state, "ship_icons", None) or []
    icon = next((i for i, ic in enumerate(icons) if ic.node_idx == head),
                None)
    if icon is None:
        return None
    hw, hh = zt.ship_icon_header_dimension(3 - game_zoom)
    ic = icons[icon]
    return {"icon": icon, "star": star_index, "colour": colour,
            "start": (ic.x + (hw >> 1), ic.y + (hh >> 1))}


def render_preview_line(surface, ctx, state, stars, star_index, game_zoom,
                        anchor, ms, black_hole=False):
    """Draw the hover preview (`Draw_ETA_Destination_Line_`), or nothing.
    Returns the line's dict when it drew one."""
    from core import mapcoords as mc
    line = preview_line(state, star_index, game_zoom, black_hole)
    if line is None:
        return None
    star = stars[star_index]
    nx, ny = line["start"]
    sx, sy = mc.galaxy_to_native(star.x, star.y, state)
    table, offset = directional(nx, ny, sx, sy,
                                RED if line["colour"] == "red" else GREEN,
                                phase_at(ms))
    a = ship_icons.anchored_point(state.ship_icons[line["icon"]], nx, ny,
                                  ctx, anchor)
    seg = clip(a, ctx.view.to_screen(star.x, star.y), ctx.view.box)
    if seg is None:
        return None
    for colour, p, q in wave_pieces(seg[0], seg[1], table, offset, ctx.px):
        stroke(surface, colour, p, q)
    return line


def render_hover_preview(screen, surface, ctx):
    """The galaxy map's call: the preview to the star under the pointer
    (`screen._hover_star`, local to HD — the engine's pointer never moves),
    or nothing. The line goes with the pointer (HD EXTENSION `hover_line`)."""
    hover = getattr(screen, "_hover_star", None)
    if hover is None or getattr(screen, "_state", None) is None:
        return None
    stars = screen._stars
    # BY POSITION, not identity: `_hover_star` is the object the last mouse
    # motion found, and every snapshot builds `_stars` anew (found live, work
    # order 188: an identity lookup never matched after the first update).
    index = next((i for i, s in enumerate(stars)
                  if (s.x, s.y) == (hover.x, hover.y)), None)
    return render_preview_line(
        surface, ctx, screen._state, stars, index, screen._game_zoom(),
        screen._icon_anchor(), pygame.time.get_ticks(),
        black_hole=star_struct.is_black_hole(hover))
