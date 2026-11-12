"""Where a ship in space is drawn next to a star — work order 390.

Split out of `ships.py` (decision 6, 40 KB); `ships.space_point` is this
function, the one every consumer of a ship's place in space calls.
"""
from core import zoomtables as zt


#: How far from a star, in native px at HD's rung, a ship in space still
#: keeps its place relative to the star's orbit slots (`space_point`).
NEAR_STAR_PX = 24


def space_point(ship, ctx, stars):
    """HD point of a ship that is in space (or in slot 5): its own galaxy
    position through the HD view — except next to a star.

    DEVIATION `space_near_star` (work order 390, Data: two fleets at Altair
    stood apart in the original and lay on top of each other in HD, moving
    against each other while zooming): the orbit slots (`orbit_slot_offset`)
    grow with the sprite RUNG, a ship's own place with the continuous zoom,
    so a fleet on its way in drifted through the fleet standing at the star.
    Within NEAR_STAR_PX native px of the nearest star the ship's offset from
    that star is scaled like the slots, by the rung and `ctx.px`, as the
    original does at every rung it can stand on, and blended into the
    continuous place over that distance, so nothing jumps."""
    from core import mapcoords as mc

    sx, sy = ctx.view.to_screen(ship.x, ship.y)
    if not stars:
        return sx, sy
    rung = zt.hd_rung(ctx.map_scale, ctx.max_zoom, ctx.num_stars,
                      ctx.max_map_scale)
    if not rung:
        return sx, sy
    per_unit = mc.SCALE_UNIT / float(rung)       # native px per galaxy unit
    near, best = None, None
    for star in stars:
        d2 = (star.x - ship.x) ** 2 + (star.y - ship.y) ** 2
        if best is None or d2 < best:
            near, best = star, d2
    if near is None or (best ** 0.5) * per_unit >= NEAR_STAR_PX:
        return sx, sy
    w = (best ** 0.5) * per_unit / NEAR_STAR_PX
    px_, py_ = ctx.view.to_screen(near.x, near.y)
    dx = (ship.x - near.x) * per_unit * ctx.px
    dy = (ship.y - near.y) * per_unit * ctx.px
    return (px_ + dx * (1 - w) + (sx - px_) * w,
            py_ + dy * (1 - w) + (sy - py_) * w)
