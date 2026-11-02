"""The build list stands over the colony's landscape — work order 361.

**HD EXTENSION `build_scene_background`** (Data, 1 November 2026: the build
screen's background is the colony screen's, not space). The original's
build list is drawn over the colony's own picture of the world, darkened
(Data's screenshot of the original: the landscape behind the three
lists, colbldg.cpp drawing over `Colony_Screen_`); HD gave it the universal
space background like every other screen. Here it wears the picture the
colony screen shows as its surface — `screens/colony/colsurface` (the
player's picture in the screen's format) or the original's (`colart`, the
climate's ground under COLONY2's sky) — over the whole window, cut to
cover it, never stretched, and darkened to `KEEP` of its light so the words
on the panels keep their contrast. The panels are glass over it
(`core.hud.glass`: what is drawn under a box shows through).

Without a picture (no player's file and the original's art not extracted)
`draw` says so and the screen draws its background as before.
"""
import pygame

from screens.colony import colart, colgeom, colsurface
from screens.colony.coldraw import cover

#: How much of the picture's light stays (a 0..255 grey the picture is
#: multiplied by): the landscape is dark in the original, and every HUD word
#: must keep 4.5 : 1 on the glass over it.
KEEP = 105
#: Where a flatter window cuts the picture: its middle.
ANCHOR = 0.5

_made = {}


def picture(view, res):
    """The colony's surface picture for the view's colony and planet, or
    None: the screen's own format first, then the original's."""
    climate = view.colony.climate
    ground = int(getattr(view.planet, "climate_bg_type", 0) or 0)
    pic = colsurface.picture(climate, ground, res)
    if pic is not None:
        return pic, ("format", id(pic))
    art = colart.load()
    if art.available:
        pic = art.scene(climate, ground)
        if pic is not None:
            x0, y0, x1, y1 = colgeom.SCENE
            return (pic.subsurface(pygame.Rect(x0, y0, x1 - x0 + 1,
                                               y1 - y0 + 1)),
                    ("original", climate, ground))
    return None


def draw(surface, screen, view):
    """Draw the landscape over the whole `surface`; False when the colony
    has none (the caller draws the background instead)."""
    if view is None or not view.draws:
        return False
    got = picture(view, screen.app.res)
    if got is None:
        return False
    pic, name = got
    size = surface.get_size()
    key = (name, size)
    ready = _made.get(key)
    if ready is None:
        if len(_made) >= 3:      # a window size, a resize, the next colony
            _made.clear()
        ready = cover(pic, pygame.Rect(0, 0, *size), ANCHOR).copy()
        ready.fill((KEEP, KEEP, KEEP, 255),
                   special_flags=pygame.BLEND_RGBA_MULT)
        _made[key] = ready
    surface.blit(ready, (0, 0))
    return True
