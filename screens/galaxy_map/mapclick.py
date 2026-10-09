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

THE POINT IS CHECKED BEFORE IT IS SENT (work order 226 A, D8 of the GUI
audit; Data's decision 1 of 9 October 2026, decision 35 with 33 as the
tool). HD picks the object in HD pixels; the game picks it again from
the native point with `Check_Stars_XY_`, the FIRST star in index order
within its radius. So every planned point is run through that test
(`star_at_native`): a star's centre an earlier-index neighbour covers is
moved to another point inside the target's own radius that only the
target holds (`star_point`); an icon's point, while the fleet box puts
stars first, to a point of its rectangle no star holds; and an "empty"
click the game would read as a star is not sent. Where no such point
exists nothing is sent and the plan says why.
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


def icon_click_point(icons, owners, index, game_zoom, avoid=None):
    """A native point the game resolves to icon `index`, or None.

    The centre when no earlier icon covers it — Check_Ships_XY_ stops at
    the first hit in array order, so a point under an earlier icon would
    open that stack instead — otherwise the first point of the rectangle
    that is clear of every earlier one. `avoid(x, y)` rules out a point
    the game would resolve to something else first (a star, while the
    fleet box is open; D8).
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
        if mc.on_screen(x, y) and not any(_inside(r, x, y) for r in earlier) \
                and not (avoid is not None and avoid(x, y)):
            return x, y
    return None


def _circle(star, state, percent):
    """(native centre x, y, click radius) as Check_Stars_XY_ tests it."""
    cx, cy = mc.galaxy_to_native(star.x, star.y, state)
    size = max(0, min(len(STAR_CLICK_RADIUS) - 1, int(star.size)))
    return cx, cy, zt.scale_star_dimension(STAR_CLICK_RADIUS[size], percent)


def _percent(stars, state):
    return zt.star_scale_percent(len(stars),
                                 getattr(state, "map_scale", 10) or 10)


def star_at_native(stars, state, nx, ny):
    """Check_Stars_XY_ on a native point: the first star in range, or None."""
    percent = _percent(stars, state)
    for idx, star in enumerate(stars):
        cx, cy, radius = _circle(star, state, percent)
        if (cx - nx) ** 2 + (cy - ny) ** 2 <= radius * radius:
            return idx
    return None


def star_point(stars, state, target):
    """A native point `Check_Stars_XY_` resolves to star `target`, or None.

    The centre when no earlier-index star covers it, else the point of the
    target's own click circle nearest its centre that no earlier star
    covers. Only earlier stars can take a point inside the target's circle
    (the walk stops at the first hit), so only those whose circle meets it
    are asked.
    """
    percent = _percent(stars, state)
    tx, ty, rt = _circle(stars[target], state, percent)
    earlier = []
    for j in range(target):
        cx, cy, r = _circle(stars[j], state, percent)
        if (cx - tx) ** 2 + (cy - ty) ** 2 <= (r + rt) ** 2:
            earlier.append((cx, cy, r))
    offsets = sorted(((dx, dy) for dy in range(-rt, rt + 1)
                      for dx in range(-rt, rt + 1)
                      if dx * dx + dy * dy <= rt * rt),
                     key=lambda d: (d[0] * d[0] + d[1] * d[1], d[1], d[0]))
    for dx, dy in offsets:
        x, y = tx + dx, ty + dy
        if mc.on_screen(x, y) and not any(
                (cx - x) ** 2 + (cy - y) ** 2 <= r * r
                for cx, cy, r in earlier):
            return x, y
    return None


@dataclass
class Plan:
    what: str                 # "icon", "star", "empty", "refused", "none"
    send: tuple = None        # native (x, y) to INJECT_CLICK, or None
    detail: str = ""
    target: int = -1          # the icon index or star index clicked


def plan(boxes, star, icon_index, icons, owners, stars, state, game_zoom,
         pointer, orders_ok=False):
    """Decide one left click on the map. Sends nothing itself.

    `star` is the HD star under the pointer or None, `icon_index` the HD
    icon or None, `pointer` the native point under the pointer.
    `orders_ok` lifts the decision-65 guard: True only while HD draws the
    fleet box with its selection read off the wire (open fix 20), so the
    player sees which ships a star click will move.
    """
    fleet_open = boxes is not None and boxes.fleet is not None
    order = ("star", "icon") if fleet_open else ("icon", "star")
    chosen = None
    # With the box open the game asks stars first, so an icon's point must
    # be one no star holds (D8); with it closed ships come first.
    avoid = ((lambda x, y: star_at_native(stars, state, x, y) is not None)
             if fleet_open else None)
    for kind in order:
        if kind == "icon" and icon_index is not None:
            point = icon_click_point(icons, owners, icon_index, game_zoom,
                                     avoid)
            chosen = Plan("icon", point, f"icon {icon_index}",
                          target=icon_index)
            break
        if kind == "star" and star is not None:
            index = next((i for i, s in enumerate(stars) if s is star), -1)
            point = star_point(stars, state, index) if index >= 0 else None
            detail = star.name
            if point is not None and point != mc.galaxy_to_native(
                    star.x, star.y, state):
                detail += " (off its centre: an earlier star holds it, D8)"
            chosen = Plan("star", point, detail, target=index)
            break
    if chosen is None:
        chosen = Plan("empty", pointer, "empty map")
    if chosen.send is None or not mc.on_screen(*chosen.send):
        return Plan("none", None, f"{chosen.detail}: no native point the "
                    f"game reads as it")
    if fleet_open and not orders_ok:
        hit = star_at_native(stars, state, *chosen.send)
        if hit is not None and not star_struct.is_black_hole(stars[hit]):
            return Plan("refused", None,
                        f"{chosen.detail}: the game would read star "
                        f"{stars[hit].name} as a move order while the fleet "
                        f"box is open (decision 65)")
    if chosen.what == "empty":
        hit = star_at_native(stars, state, *chosen.send)
        if hit is not None:
            return Plan("none", None, f"empty map: the game would read star "
                        f"{stars[hit].name} there (D8)")
    return chosen
