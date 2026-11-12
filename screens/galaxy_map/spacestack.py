"""Fleets in space stacked beneath what stands at their star — work order 391.

DEVIATION `space_stack` (Data, 12 November 2026: at Altair the original
draws the fleet at the star and the fleet on its way in one beneath the
other; HD drew them on top of each other): the icon of a player's fleet
(owner below 8) in space near a star that would overlap an icon at that
star, or an earlier fleet in space, is moved below it, one pixel clear. The gap is in sprite
px, so it holds at every zoom. The icon box, the click, the destination
line and the ETA label all take the same shift (`shift`).
"""
from core.structs import ship as ship_struct
from screens.galaxy_map import ships as sh

#: How far from a star, native px at HD's rung, a fleet is "at" it.
REACH_PX = 36
#: The most icons stacked beneath one another.
MAX_PUSHES = 6


def size(owner, ctx, cfg=None):
    """The icon's (width, height) in HD px, as `ships.icon_box` gives it."""
    kind = sh.kind_for_owner(owner)
    _, scale = sh.kind_config(cfg, kind or sh.PLAYER_KIND)
    nw, nh = sh.native_size(kind, ctx.zoom)
    return (max(2, int(round(nw * ctx.px * scale))),
            max(2, int(round(nh * ctx.px * scale))))


def _star_of(ship, ctx, anchor):
    """Index of the star the fleet is at (within REACH_PX), or None."""
    from core import zoomtables as zt
    rung = zt.hd_rung(ctx.map_scale, ctx.max_zoom, ctx.num_stars,
                      ctx.max_map_scale)
    if not rung or not anchor.stars:
        return None
    reach = REACH_PX * rung / 10.0                 # galaxy units
    best, found = reach * reach, None
    for i, star in enumerate(anchor.stars):
        d2 = (star.x - ship.x) ** 2 + (star.y - ship.y) ** 2
        if d2 < best:
            best, found = d2, i
    return found


def shift(icon, ctx, anchor, base_top, base_left, box_w, box_h):
    """The HD pixels (down) a fleet in space is moved to clear what stands
    at its star; 0 when nothing overlaps it."""
    # one shift per icon per anchor (an anchor is one frame's): an icon's
    # shift asks the boxes of the earlier ones, which would else recurse
    # through every earlier fleet again (2 ** n for n fleets at one star)
    memo = anchor.__dict__.setdefault("_stack_memo", {})
    if id(icon) not in memo:
        memo[id(icon)] = _shift(icon, ctx, anchor, base_top, base_left,
                                box_w, box_h)
    return memo[id(icon)]


def _shift(icon, ctx, anchor, base_top, base_left, box_w, box_h):
    cfg = getattr(anchor, "cfg", None)
    icons = getattr(anchor.game_state, "ship_icons", None) or []
    mine = next((i for i, o in enumerate(icons) if o is icon), None)
    _, _, ship, _ = anchor.resolve(icon)
    # the head ship's owner, as the line and the label take it
    if mine is None or ship is None or int(ship.owner) >= 8:
        return 0.0
    star = _star_of(ship, ctx, anchor)
    if star is None:
        return 0.0
    others = []
    for j, other in enumerate(icons):
        if j == mine or other.x < 0 or other.y < 0:
            continue
        _, _, oship, _ = anchor.resolve(other)
        if oship is None:
            continue
        if sh._in_space(other, oship):
            # an earlier fleet in space at the same star
            if j > mine or oship.owner >= 8 or \
                    _star_of(oship, ctx, anchor) != star:
                continue
        elif ship_struct.absolute_location(other.star_idx) != star:
            continue                        # an orbit slot at another star
        others.append(sh.icon_box(other, oship.owner, ctx, anchor, cfg))
    top, gap = base_top, max(1.0, ctx.px)
    for _ in range(MAX_PUSHES):
        hit = next((b for b in others
                    if b[0] < base_left + box_w and base_left < b[0] + b[2]
                    and b[1] < top + box_h and top < b[1] + b[3]), None)
        if hit is None:
            break
        top = hit[1] + hit[3] + gap
    return top - base_top
