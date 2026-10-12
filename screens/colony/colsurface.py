"""The colony screen's surface picture in the screen's own format — work
order 232 (Data's decisions 2 and 3, 11 October 2026).

Since 232 the surface panel runs from under the band to the content
rectangle's bottom edge, and its shape is the screen's surface format: at a
16:9 window or a wider one 1880 x 651 reference px, about 2.89 : 1 — far
flatter than the original's 640 x 328 picture, which is therefore cut to
cover it (`coldraw.cover`). Data's decision 3: a new picture is made for
the format. This is where it goes and how it is found.

THE PLACE: `screens/colony/assets/surfaces/<climate>.png`, one per
climate, the climate's name as the Colonies screen's discs and surfaces
spell it (`colonyplanets.NAMES`, `PLANET_CLIMATE`'s order,
orion2_consts.h:362-373). The original has three grounds per climate
(PLANETS.LBX `climate * 3 + climate_bg_type`, the planet's own type;
`colart`), so `<climate>_<ground>.png` (ground 0, 1 or 2) wins over
`<climate>.png` for that ground — a painter may make one per climate or
three. Resolved through the resource roots (decision 72): the player's
folder (`files/screens/colony/assets/surfaces/…`, a `core.usermod` slot,
since the tree ships none yet), a developer mod, the tree.

ORDER: a picture found here wins over the original's extracted picture,
which wins over decision 58's painting (`coldraw._scene`). It is drawn by
the same `cover` as the original's: at the format it fills the panel
whole; at another shape it is cut, never stretched.

HD EXTENSION `surface_format_picture`: the original has one picture per
climate and ground at 640 x 328 under its band and no route to replace it.

A MISSING PICTURE IS A STATE, NOT AN ERROR (decision 38's rule): nothing
here, and the original's picture is drawn as before. A file that will not
load is said once in the log and skipped.
"""
import logging

import pygame

from screens.colony_summary.colonyplanets import name_for

log = logging.getLogger("colony")

#: The folder, a tree path (resolved, never joined to the tree's root).
FOLDER = "screens/colony/assets/surfaces"
#: The original's grounds per climate (`colart.BG_TYPES`).
GROUNDS = 3

_cache = {}
_refused = set()


def format_size(layout):
    """(w, h) device px the picture fills in this window: the surface
    panel less the shell's inset — `coldraw.scene_rect` of the shell's own
    cut (a box moved in the layout editor moves it with it). The size a
    painter makes the picture at; its ratio is the format."""
    from core.hud import shell
    from . import colgeom
    panel = pygame.Rect(colgeom.shell_boxes(layout)
                        [colgeom.SURFACE_REGION[0]])
    return shell.inner(panel, layout).size


def names(climate, ground):
    """The file names that answer for this world, the first that exists
    wins: the climate's ground of its own, then the climate's."""
    name = name_for(climate)
    if name is None:
        return []
    out = []
    if 0 <= int(ground) < GROUNDS:
        out.append(f"{name}_{int(ground)}.png")
    out.append(f"{name}.png")
    return out


def picture(climate, ground, resources=None):
    """The surface picture for a world in the screen's format, or None.
    Kept per resolved path: a mod that replaces a picture is a new path."""
    if resources is None:
        from core import resources as res_mod
        resources = res_mod.res
    for fname in names(climate, ground):
        path = resources.resolve(f"{FOLDER}/{fname}")
        if path is None or path in _refused:
            continue
        if path not in _cache:
            try:
                img = pygame.image.load(path)
            except (pygame.error, OSError) as err:
                log.warning("colony surface %s will not load (%s) — the "
                            "original's picture is drawn", path, err)
                _refused.add(path)
                continue
            _cache[path] = (img.convert() if pygame.display.get_init()
                            and pygame.display.get_surface() else img)
        return _cache[path]
    return None
