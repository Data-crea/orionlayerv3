"""What a left click on the map is about, in the original's order.

TRANSCRIBED. `MAINSCR::Main_Screen_` resolves a click on the map grid
through two tests and picks their order by one condition
(mainscr_main.cpp:425-438): while the fleet box (box 2) is open, STARS
first and ships only if no star answered; otherwise SHIPS first and
stars only if no icon answered.

  * `Check_Ships_XY_` (mainscr.cpp:1750-1780) walks `_ship_icon[]` in
    ARRAY order and takes the first icon whose rectangle — top-left
    x/y, the sprite's width and height, bounds inclusive — contains the
    pointer.
  * `Check_Stars_XY_` (mainscr.cpp:1697-1740) walks the stars in index
    order and takes the first whose draw centre lies within
    `Scaled_Star_Map_Dimension_({12, 10, 8}[star.size])` pixels.

HD asks the same two questions in HD pixels — the icon rectangle is the
one `ships.render` draws in (`ships.icon_box`, decision 5), the star test
is `GalaxyMapScreen._star_at` — and then sends ONE click at a native
point the game resolves to the same object: an icon's own rectangle,
clear of every earlier icon, or the star's centre (decision 35: the
native point is the game's, never the HD view's).

DECISION 65 (fundament): the guard. While the fleet box is open, a
click the game would resolve to a star is a move order for the selected
ships (mainscr_main.cpp:480-535), and opening the box of a stack you own
selects its ships by itself (fleetpop.cpp:683-686). HD does not draw
that box yet and the player cannot have chosen a target in it, so such a
click is NOT SENT. DEVIATION: the original moves the fleet. It is tested
with the game's own star test on the native point — including clicks on
empty space and on icons that sit within a star's radius — and a black
hole is exempt, because the original never orders a move to one (:481).
"""
from dataclasses import dataclass

from core import mapcoords as mc
from core import zoomtables as zt
from core.structs import star as star_struct
from screens.galaxy_map import ships as ship_icons

#: `Check_Stars_XY_`'s thresholds by star.size, mainscr.cpp:1698.
STAR_CLICK_RADIUS = (12, 10, 8)


def icon_at(ctx, icons, owners, anchor, cfg, sx, sy):
    """Index of the first placed icon whose HD rectangle holds (sx, sy)."""
    if ctx is None:
        return None
    for i, (icon, owner) in enumerate(zip(icons, owners)):
        if icon.x < 0 or icon.y < 0:
            continue
        left, top, w, h = ship_icons.icon_box(icon, owner, ctx, anchor, cfg)
        if left <= sx <= left + w and top <= sy <= top + h:
            return i
    return None


def native_icon_rect(icon, owner, game_zoom):
    """Inclusive native rectangle, as Check_Ships_XY_ tests it."""
    w, h = ship_icons.native_size(ship_icons.kind_for_owner(owner), game_zoom)
    return icon.x, icon.y, icon.x + w, icon.y + h


def _inside(r, x, y):
    return r[0] <= x <= r[2] and r[1] <= y <= r[3]


def icon_click_point(icons, owners, index, game_zoom):
    """A native point the game resolves to icon `index`, or None.

    The centre when no earlier icon covers it — Check_Ships_XY_ stops at
    the first hit in array order, so a point under an earlier icon would
    open that stack instead — otherwise the first point of the rectangle
    that is clear of every earlier one.
    """
    icon, owner = icons[index], owners[index]
    target = native_icon_rect(icon, owner, game_zoom)
    earlier = [native_icon_rect(icons[j], owners[j], game_zoom)
               for j in range(index)
               if icons[j].x >= 0 and icons[j].y >= 0]
    cx = (target[0] + target[2]) // 2
    cy = (target[1] + target[3]) // 2
    points = [(cx, cy)] + [(x, y) for y in range(target[1], target[3] + 1)
                           for x in range(target[0], target[2] + 1)]
    for x, y in points:
        if mc.on_screen(x, y) and not any(_inside(r, x, y) for r in earlier):
            return x, y
    return None


def star_at_native(stars, state, nx, ny):
    """Check_Stars_XY_ on a native point: the first star in range, or None."""
    percent = zt.star_scale_percent(len(stars),
                                    getattr(state, "map_scale", 10) or 10)
    for idx, star in enumerate(stars):
        cx, cy = mc.galaxy_to_native(star.x, star.y, state)
        size = max(0, min(len(STAR_CLICK_RADIUS) - 1, int(star.size)))
        radius = zt.scale_star_dimension(STAR_CLICK_RADIUS[size], percent)
        if (cx - nx) ** 2 + (cy - ny) ** 2 <= radius * radius:
            return idx
    return None


@dataclass
class Plan:
    what: str                 # "icon", "star", "empty", "refused", "none"
    send: tuple = None        # native (x, y) to INJECT_CLICK, or None
    detail: str = ""


def plan(boxes, star, icon_index, icons, owners, stars, state, game_zoom,
         pointer):
    """Decide one left click on the map. Sends nothing itself.

    `star` is the HD star under the pointer or None, `icon_index` the HD
    icon or None, `pointer` the native point under the pointer.
    """
    fleet_open = boxes is not None and boxes.fleet is not None
    order = ("star", "icon") if fleet_open else ("icon", "star")
    chosen = None
    for kind in order:
        if kind == "icon" and icon_index is not None:
            point = icon_click_point(icons, owners, icon_index, game_zoom)
            chosen = Plan("icon", point, f"icon {icon_index}")
            break
        if kind == "star" and star is not None:
            point = mc.galaxy_to_native(star.x, star.y, state)
            chosen = Plan("star", point, star.name)
            break
    if chosen is None:
        chosen = Plan("empty", pointer, "empty map")
    if chosen.send is None or not mc.on_screen(*chosen.send):
        return Plan("none", None, f"{chosen.detail}: no native point")
    if fleet_open:
        hit = star_at_native(stars, state, *chosen.send)
        if hit is not None and not star_struct.is_black_hole(stars[hit]):
            return Plan("refused", None,
                        f"{chosen.detail}: the game would read star "
                        f"{stars[hit].name} as a move order while the fleet "
                        f"box is open (decision 65)")
    return chosen
