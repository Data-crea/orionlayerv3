"""The destination lines on the Fleets inset — work order 403 A (gap 9 of
work order 401's comparison, its part that needs no engine change).

TRANSCRIPTION `destination_lines`: `FLT1::Draw_Fltscrn_Ship_Destination_
Lines_` (flt1.cpp:121-217) walks every small ship icon of the screen and
draws a line from the icon to the star it heads for:

  * the local player's own icon whose ship is in transit
    (`Absolute_Location != NUM_STARS`, location inside the moving / wormhole
    range, flt1.cpp:179-185) — green;
  * any other owner's icon whose ship is not orbiting and heads for a star
    the player holds a colony or an outpost at
    (`SHIPS::Enemy_Ship_Heading_Toward_Our_Colony_`, ships.cpp:401-420;
    flt1.cpp:186-192) — red. Unlike the galaxy map the Fleets screen does
    NOT consult the options screen's "enemy moves" setting: the function
    is not called here at all.

The line ends are the star's point and the icon's top-left `+4, +4`
(`Draw_Ship_Destination_Line_`, ships.cpp:552-553, the branch for every
screen but the galaxy map). The star's end is `out_x + 3` (flt1.cpp:161-173,
:207-210) of `Get_Galaxy_Map_Star_XY` called with marker mode 1, which has
ALREADY taken 3 off (`star_center_offset`, movebox.cpp:343-366): the two
cancel and the line ends ON the star's own point, the one the dot is drawn
at. HD took only the `+3` and ended every line 3 native px (about 10 HD px)
right of and below its star (Data, 19 November 2026: "es zeigt immer
etwas daneben an"). The line is drawn from the icon to the star
(ships.cpp:558-563), the wave through `maplines`' one routine (decision
68), clipped to the inset box like the relocation lines beside it
(`fltdraw.draw_relocation_lines`).

TRANSCRIPTION `preview_line` (open fix 121, work order 406). The marking
OMISSION `omission_preview_line` stands only against an engine without that
fix. The loop's first line — the selected stack's icon
to the star under the pointer, green while the move is possible and red for
a black hole or a refusal (flt1.cpp:130-170) — reads `_g_ship_move_info.
moving`, the verdict for the SELECTED SHIPS, which the engine now sends on
this screen as FMOV (`fltpreview.preview_line`). It is drawn FIRST, before
the other icons' lines, as the original's order is (:130-170, then :172).
Against an engine without the fix no line is drawn (no verdict, no guess).

UNVERIFIED live: the lines, the preview line included, in a running game
(headless renders only).
"""
from core.structs import planet as planet_struct
from core.structs import colony as colony_struct
from core.structs import ship as ship_struct
from core.structs import star as star_struct

from . import fltgeom

#: At the star `Get_Galaxy_Map_Star_XY`'s `-3` (marker mode 1) and the
#: caller's `+3` cancel; at the icon `x2 + 4` (see the header).
STAR_NUDGE = 3 - 3
ICON_NUDGE = 4


def ends(rect, native, icon_xy, star_xy):
    """The line's two ends in window pixels: `rect` the inset's box,
    `native` its native `(x, y, w, h)`, `icon_xy` the stack icon's
    absolute native top-left, `star_xy` the star's box-local native point
    (`colonyfacts.galaxy_inset_stars`). One place, so a check can hold the
    star's end to where the dot is drawn (`fltdraw.draw_inset`)."""
    bx, by, nw, nh = native
    fx, fy = rect.width / float(nw), rect.height / float(nh)
    a = (rect.x + (int(icon_xy[0]) - bx + ICON_NUDGE) * fx,
         rect.y + (int(icon_xy[1]) - by + ICON_NUDGE) * fy)
    b = (rect.x + (star_xy[0] + STAR_NUDGE) * fx,
         rect.y + (star_xy[1] + STAR_NUDGE) * fy)
    return a, b


def _ours(state, star):
    """`Player_Has_Colony_` or `Player_Has_Outpost_` at the star
    (ships.cpp:411-415; harold.cpp:423) — the galaxy map's own rule,
    copied with its source because another screen's private name is not
    this screen's to import."""
    me = int(getattr(state, "player_num", 0) or 0)
    if (int(star.has_colony) >> (me & 0x1F)) & 1:
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


def lines(state):
    """`[{"icon": i, "star": s, "colour": "green"|"red"}]` for the icons
    that get a line; empty without the node table (open fix 20: no ship
    behind an icon)."""
    sel = getattr(state, "fleet_selection", None)
    raws = getattr(state, "ships_raw", None) or []
    stars = getattr(state, "stars", None) or []
    if not sel or not raws or not stars:
        return []
    me = int(getattr(state, "player_num", 0) or 0)
    out = []
    for i, icon in enumerate(getattr(state, "ship_icons", None) or []):
        node = int(icon.node_idx)
        if not 0 <= node < len(sel["ships"]):
            continue
        ship_idx = sel["ships"][node]
        if not 0 <= ship_idx < len(raws):
            continue
        ship = ship_struct.parse(raws[ship_idx])
        dest = ship_struct.absolute_location(ship.location)
        if not 0 <= dest < len(stars):
            continue                     # NUM_STARS: Antares, no star
        if ship.owner == me:
            moving = ship_struct.LOCATION_MOVING_OFFSET <= ship.location \
                < ship_struct.LOCATION_LIMIT
            colour = "green" if moving else None
        else:
            colour = "red" if ship.status != 0 and _ours(state, stars[dest]) \
                else None
        # The moving-range test belongs to the OWN branch only
        # (flt1.cpp:186); a foreign ship is tested by `status != 0` and the
        # colony alone (ships.cpp:401-420).
        if colour is not None:
            out.append({"icon": i, "star": dest, "colour": colour})
    return out


def draw(surface, screen, state, stars, ms, preview=None):
    """The lines on the inset, over the black and under the stars' next
    paint. `stars` is `_inset_stars()` — box-local native points. `preview`
    is `fltpreview.preview_line`'s entry, drawn first."""
    from screens.galaxy_map import maplines
    from . import fltdraw
    rect = fltdraw._rect(screen, "inset_map")
    if rect is None or not stars or state is None:
        return []
    todo = ([preview] if preview else []) + lines(state)
    if not todo:
        return []
    bx, by, nw, nh = fltgeom.REGIONS["inset_map"]
    fx, fy = rect.width / float(nw), rect.height / float(nh)
    phase = maplines.phase_at(ms)
    step = max(1.0, min(fx, fy))
    icons = state.ship_icons
    previous = surface.get_clip()
    surface.set_clip(rect)
    drawn = []
    for line in todo:
        if not 0 <= line["star"] < len(stars):
            continue
        icon = icons[line["icon"]]
        if int(icon.x) < 0 or int(icon.y) < 0:
            continue                     # not placed (the -1 sentinel)
        sx, sy, _c = stars[line["star"]]
        a, b = ends(rect, (bx, by, nw, nh), (icon.x, icon.y), (sx, sy))
        table, offset = maplines.directional(
            a[0], a[1], b[0], b[1],
            maplines.RED if line["colour"] == "red" else maplines.GREEN,
            phase)
        seg = maplines.clip(a, b, (rect.x, rect.y, rect.width, rect.height))
        if seg is None:
            continue
        for colour, p, q in maplines.wave_pieces(seg[0], seg[1], table,
                                                 offset, step):
            maplines.stroke(surface, colour, p, q)
        drawn.append((line["icon"], line["star"], line["colour"]))
    surface.set_clip(previous)
    return drawn
