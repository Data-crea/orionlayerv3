"""The painted scenes of the build list and the Ship Designer — HD EXTENSION
`build_list_scene` (work order 432) and `designer_mockup` (work order 433),
Data's mockups of 25 November 2026.

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
    return _load_file(f"build_{name}")


def _load_file(stem):
    from core import resources
    path = resources.res.resolve(f"{FOLDER}/{stem}.png")
    if not path or not os.path.isfile(path):
        return None
    stamp = (path, os.path.getmtime(path))
    hit = _raw.get(stem)
    if hit is not None and hit[0] == stamp:
        return hit[1]
    try:
        loaded = pygame.image.load(path)
        surf = pygame.Surface(loaded.get_size(), pygame.SRCALPHA)
        surf.blit(loaded, (0, 0))
    except (pygame.error, OSError) as err:
        log.warning("scene: %s cannot be read (%s) — not drawn",
                    f"{FOLDER}/{stem}.png", err)
        surf = None
    _raw[stem] = (stamp, surf)
    return surf


def art():
    """The scene under a help text, or None."""
    return _load(ART)


def named(stem):
    """The painted scene `popups/<stem>.png` — the Ship Designer's two
    (`design_scene_drive`, `design_scene_special`, WO 433) — or None."""
    return _load_file(stem)


def forget():
    _raw.clear()
