"""The science room's race picture — work order 360.

**HD EXTENSION `science_room_picture`** (replaces the OMISSION
`science_room_animation`, see `screen.py`). In the original the research
breakthrough (SELECT NEW RESEARCH) shows the science room of the player's
race on the strip left of the panel: `SR_R<race>_SC.LBX`, drawn at (0, 0)
before the panel covers all but its left 160 px (tech.cpp:271-290). The
player may put one picture per race in the mod folder,

    <mod folder>/files/screens/research_select/assets/science_room/<race>.png

(`race` is the lower-case race name of `screens.audience.auvideo.RACES`, the
order of MOO2's race numbers). Without it the strip stays an empty box, as
before. The picture is a still (the original's animation is not played).

A picture is wide and the strip is not: the picture is scaled to the strip's
height and the part of it that holds the scientist is shown, centred on
`FOCUS` of its width from the left, never stretched. The scientist stands in
the left third of every room (the widest reach about 35 % of the picture's
width, read off a contact sheet of the thirteen, not measured), so the strip is wide enough for that part
(`screen.SCIENCE_ROOM_SPLIT`), starting at the picture's left edge.
"""
import os

import pygame

REL = "screens/research_select/assets/science_room"
#: where the scientist stands, as a fraction of a wide picture's width
FOCUS = 0.18

_cache = {}


def _path(race):
    from core import basepack, usermod
    from core.config import BASE_DIR
    from screens.audience import auvideo
    if race is None or not 0 <= race < len(auvideo.RACES):
        return None
    rel = f"{REL}/{auvideo.RACES[race]}.png"
    for root in (os.path.join(usermod.mod_dir(), usermod.FILES), BASE_DIR,
                 basepack.base_dir()):
        if root:
            path = os.path.join(root, *rel.split("/"))
            if os.path.isfile(path):
                return path
    return None


def picture(race):
    """The race's picture (convert()ed), or None."""
    path = _path(race)
    if path is None:
        return None
    try:
        key = (path, os.stat(path).st_mtime_ns)
    except OSError:
        return None
    if key not in _cache:
        # keyed by the file's time: a picture replaced while the game runs
        # is read again, and a bad one is not read again every frame
        for old in [k for k in _cache if k[0] == path]:
            del _cache[old]
        try:
            _cache[key] = pygame.image.load(path).convert()
        except (pygame.error, OSError):
            _cache[key] = None
    return _cache[key]


def crop(size, box):
    """The part of a picture of `size` that fills `box` (w, h) at the
    picture's full height, centred on `FOCUS`: a Rect of the picture."""
    w, h = size
    cw = min(w, max(1, round(h * box[0] / box[1])))
    x = round(w * FOCUS - cw / 2)
    if x < w * 0.01:      # a sliver of the left edge: start at the edge
        x = 0
    return pygame.Rect(max(0, min(w - cw, x)), 0, cw, h)


def draw(surface, rect, race):
    """Draw the race's picture into `rect`; False when there is none."""
    pic = picture(race)
    if pic is None or rect.w < 4 or rect.h < 4:
        return False
    part = pic.subsurface(crop(pic.get_size(), rect.size))
    surface.blit(pygame.transform.smoothscale(part, rect.size), rect.topleft)
    return True
