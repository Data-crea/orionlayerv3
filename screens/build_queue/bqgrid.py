"""The picture box's grid — HD EXTENSION `build_grid_room` (Data,
1 November 2026: "replace the grid picture above, a new one is in
Downloads").

The original's room (COLBLDG.LBX 0) is a 640x480-era drawing that HD stepped
up by whole numbers. Data's own picture, a neon grid tunnel on
transparency, takes its place from the mod folder (`popups/build_grid.png`,
`core.usermod.SLOTS`); the product is stood in it as before, only its own
pixels (`colroom.product_only`). Without the file the box shows the
original's room, as it always did.
"""
import logging
import os

import pygame

log = logging.getLogger("build_queue")

#: The tree path of the slot (mod folder name: `popups/build_grid.png`).
SLOT = "assets/shared/turnpopup/build_grid.png"

_loaded = {}
_scaled = {}
_ink = {}


def picture(res):
    """Data's grid as a surface, or None where the mod folder has none."""
    path = res.resolve(SLOT)
    if not path or not os.path.isfile(path):
        return None
    stamp = (path, os.path.getmtime(path))
    if stamp not in _loaded:
        _loaded.clear()
        _scaled.clear()
        _ink.clear()
        try:
            _loaded[stamp] = pygame.image.load(path).convert_alpha()
        except (pygame.error, OSError) as err:
            log.warning("build list: %s cannot be read (%s) — the "
                        "original's room is drawn", SLOT, err)
            _loaded[stamp] = None
    return _loaded[stamp]


def _cover(pic, rect):
    """The picture scaled to cover `rect` in its own proportion, and the
    window of it that `rect` shows (the middle)."""
    key = rect.size
    big = _scaled.get(key)
    if big is None:
        k = max(rect.w / pic.get_width(), rect.h / pic.get_height())
        w, h = (max(rect.w, int(round(pic.get_width() * k))),
                max(rect.h, int(round(pic.get_height() * k))))
        big = pygame.transform.smoothscale(pic, (w, h))
        _scaled.clear()
        _ink.clear()
        _scaled[key] = big
    return big, pygame.Rect((big.get_width() - rect.w) // 2,
                            (big.get_height() - rect.h) // 2,
                            rect.w, rect.h)


def draw(surface, res, rect):
    """The grid, covering `rect` in its own proportion and cut to it at
    the middle (never stretched); True if drawn."""
    pic = picture(res)
    if pic is None:
        return False
    rect = pygame.Rect(rect)
    big, window = _cover(pic, rect)
    surface.blit(big, rect.topleft, window)
    return True


def ink_rect(res, rect):
    """Where the grid's own lines reach inside `rect` as `draw` shows it,
    in window pixels, or None without the picture. HD EXTENSION
    `build_grid_room` (Data, 2 November 2026): the colony screen's turns
    bar stands on the grid's bottom and outer edge."""
    pic = picture(res)
    if pic is None:
        return None
    rect = pygame.Rect(rect)
    hit = _ink.get(rect.size)
    if hit is None:
        big, window = _cover(pic, rect)
        hit = big.subsurface(window).get_bounding_rect(min_alpha=48)
        _ink[rect.size] = hit
    return hit.move(rect.topleft)
