"""The gas giant in the star system window — work order 236.

  DEVIATION      `gas_giant_painted`: the original draws a gas giant as
                 BUFFER0.LBX 0x5C + 50, a 31 x 31 picture turning in 40
                 frames (`Get_Rotating_Planet_Segment_`, sys.cpp:199-227);
                 HD draws Data's painted gas giant (delivered 11 October
                 2026, cut by `tools/gas_giant_cut.py`), still, as HD's
                 other planets in the window are still. Until work order
                 236 HD drew a grey ring there (no picture).

The picture is `screens/galaxy_map/assets/gas_giant.png`, read through the
resource roots, so a mod's file of that name replaces it. It is cut at
the size 3840x2160 draws it (the tool's docstring), so 4K draws it 1:1 and
every smaller window scales it down — smoothly: it is painted, not pixel
art, and decision 28's nearest-neighbour rule is about the sprites cut
from the original's pixels. One scaled copy per pixel size is kept.
Missing or unreadable, `picture` answers None and the window draws the
ring, as before.
"""
import logging

import pygame

log = logging.getLogger("galaxy_map.gas_giant")

PICTURE = "screens/galaxy_map/assets/gas_giant.png"
_cache = {}
_master = {}


def picture_path():
    from core import resources
    return resources.res.resolve(PICTURE)


def master():
    """The picture as delivered, loaded once per path; None without it."""
    path = picture_path()
    if path not in _master:
        img = None
        if path:
            try:
                img = pygame.image.load(path)
                if pygame.display.get_surface() is not None:
                    img = img.convert_alpha()
            except pygame.error as err:
                log.warning("gas giant: %s will not load (%s)", path, err)
        else:
            log.info("gas giant: no %s — the ring is drawn", PICTURE)
        _master[path] = img
    return _master[path]


def picture(side):
    """The gas giant on a `side` x `side` square, or None."""
    img = master()
    if img is None:
        return None
    side = max(1, int(side))
    key = (id(img), side)
    hit = _cache.get(key)
    if hit is None:
        hit = img if img.get_width() == side else \
            pygame.transform.smoothscale(img, (side, side))
        if len(_cache) > 8:
            _cache.clear()
        _cache[key] = hit
    return hit
