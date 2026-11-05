"""The galaxy map's territory view: what the screen asks, in one place.

the territory view (`terrfield`). `terrfield` computes, `terrdraw` draws,
`terrpanel` is the left panel; this module is the screen's one seam to
them, so `screen.py` only names three calls: `territory` (built again only
when an owner, a known star or a player colour changed), `render_under`
(glass and borders, before the wormholes and stars) and `nebula_tint`.
"""
import pygame

from core.hud import blocks as hud
from screens.galaxy_map import renderer as rnd
from screens.galaxy_map import terrdraw
from screens.galaxy_map import terrfield


def colours():
    return [tuple(rnd.OWNER_COLORS[i][:3]) for i in range(8)]


def territory(screen):
    """The current Territory, or None; kept on the screen by its key."""
    state = screen._state
    if state is None:
        return None
    player_num = getattr(state, "player_num", 0)
    omni = screen._omniscient
    players = screen._players
    emps = terrfield.empires(
        screen._stars, players, player_num, omni,
        lambda s: rnd.star_label(s, player_num, players, omni))
    cols = colours()
    key = terrfield.state_key(emps, cols)
    cur = getattr(screen, "_territory", None)
    if cur is not None and cur[0] == key:
        return cur[1]
    terr = terrfield.build(emps, cols)
    screen._territory = (key, terr)
    return terr


def legend(screen):
    """[(colour index, race name, rgb)] of the empires on the map."""
    terr = territory(screen)
    if terr is None:
        return []
    cols = colours()
    return [(c, terr.names.get(c) or "", cols[c % len(cols)])
            for c in sorted(terr.names)]


def render_gas(screen, surface, ctx):
    """The nebulas (switchable, tinted by their territory), then the
    glass and the borders over them — what `_render_map` draws first."""
    if terrdraw.is_on(screen.app, terrdraw.NEBULAE):
        rnd.render_nebulas(surface, ctx, screen._nebulas, screen._cache,
                           screen._data.get("nebula_forms", []),
                           tint=nebula_tint(screen, ctx))
    render_under(screen, surface, ctx)


def render_under(screen, surface, ctx):
    app = screen.app
    terr = territory(screen)
    if terr is None:
        return
    view = ctx.view
    op = terrdraw.opacity(app)
    # Kept off the rim of the map box by a panel's glow width: the panels
    # and the bar glow a few px past their rects, and nothing the map
    # draws may lie under a HUD block (011a)
    clip = surface.get_clip()
    pad = hud.glow_pad(screen.layout.scale)
    surface.set_clip(clip.clip(pygame.Rect(view.box).inflate(-2 * pad,
                                                             -2 * pad)))
    try:
        _draw_under(screen, surface, view, terr, op)
    finally:
        surface.set_clip(clip)


def _draw_under(screen, surface, view, terr, op):
    app = screen.app
    if terrdraw.is_on(app, terrdraw.SHOW):
        terrdraw.render_fill(surface, view, terr, op)
    if terrdraw.is_on(app, terrdraw.BORDERS):
        layer = getattr(screen, "_border_layer", None)
        if layer is None:
            layer = screen._border_layer = terrdraw.BorderLayer()
        terrdraw.render_borders(surface, view, terr, colours(),
                                screen.layout.scale, op, layer)


def nebula_tint(screen, ctx):
    """The tint callable `render_nebulas` takes, or None when territories
    are not shown (the gas is then the picture as it was)."""
    app = screen.app
    if not terrdraw.is_on(app, terrdraw.SHOW):
        return None
    terr = territory(screen)
    if terr is None:
        return None
    view = ctx.view
    return lambda img, n, xy: terrdraw.tint_nebula(img, n, view, xy, terr)
