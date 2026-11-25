"""The painted scene under the build list's help text — HD EXTENSION
`build_list_scene` (work order 432, Data's mockup of 25 November 2026).

The mockup lays a painted scene under the description. Neither tree nor base
pack holds one: it is the player's own file in the mod folder
(`popups/build_art.png`, tree `assets/shared/turnpopup/`, one slot), and
without it the large box is as it was. The small pictures in front of the
lists' rows are NOT files: they are the player's building pictures, the
game's own ship, android and spy drawings and the HUD's glyphs in the frame
colour (`screens/build_queue/bqlist`, `bqmiddle`).
"""
# HD EXTENSION `build_list_scene`: see the docstring.
import logging
import os

import pygame

log = logging.getLogger("build_queue")

#: The tree folder (`popups/` in the mod folder) and the slot glob.
FOLDER = "assets/shared/turnpopup"
SLOT = f"{FOLDER}/build_art.png"

ART = "art"

_raw = {}


def tree_path(name):
    return f"{FOLDER}/build_{name}.png"


def _load(name):
    from core import resources
    path = resources.res.resolve(tree_path(name))
    if not path or not os.path.isfile(path):
        return None
    stamp = (path, os.path.getmtime(path))
    hit = _raw.get(name)
    if hit is not None and hit[0] == stamp:
        return hit[1]
    try:
        loaded = pygame.image.load(path)
        surf = pygame.Surface(loaded.get_size(), pygame.SRCALPHA)
        surf.blit(loaded, (0, 0))
    except (pygame.error, OSError) as err:
        log.warning("build list: %s cannot be read (%s) — not drawn",
                    tree_path(name), err)
        surf = None
    _raw[name] = (stamp, surf)
    return surf


def art():
    """The scene under a help text, or None."""
    return _load(ART)


def forget():
    _raw.clear()
