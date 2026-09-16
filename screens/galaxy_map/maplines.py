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

OMISSION, each with its reason:
  * the order preview line (`Draw_ETA_Destination_Line_`,
    mainscr.cpp:535-568): its colour is the move result, which is not on
    the wire.
  * relocation lines (`Draw_Relocation_Links_`, mainscr.cpp:682-703): the
    setting and `relocate_ship_to` (star offset 205) are not verified.
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
