"""The planet surface pictures: one landscape per climate.

**HD EXTENSION, decision 58.** The original shows no landscape on the Colonies
screen: `Draw_Colony_Scan_Info_` (colsum.cpp:1155) draws production
sprites, morale sprites and one paragraph, and nothing else. The
picture is Data's design (brief 97, `doc/briefs/97-mockup.png`), drawn
in `colony_panel` for the scanned colony.

**DEVIATION IN KIND, AND THE ARTWORK IS AI-GENERATED.** Data made the
sheet with ChatGPT (13 September 2026); it carries no copyright claim
and is the project's own, listed in LICENSE's artwork scope. The ten
tiles are DERIVED from the committed sheet by
`tools/make_surface_tiles.py`, rebuilt by `tools/setup.py` and ignored
by git (decision 40).

**THE CLIMATE ID IS THE WHOLE MAPPING**, the same field and the same
names as the disc: `colonyplanets.NAMES` is `PLANET_CLIMATE`'s order
(orion2_consts.h:362-373) and a file is that name lowercased. Resolved
through the resource roots, so a mod that ships `surfaces/` replaces
them file by file (decisions 16 and 17). No path is ever stored in a
box: the image box says where and how big, this module says which
picture.

**NOT SCALED HERE.** A tile is kept at sheet resolution and the image
box scales it once, where it is drawn — so a 1440p window is fed the
411 px original and not a crop somebody already shrank for 1080p.

**A MISSING TILE IS A STATE, NOT AN ERROR** — the rule decision 38
set for the help texts. A clone that has not run `tools/setup.py` has
no tiles; the set says so once, in the log, naming the command, and the
panel draws what it drew before: no picture.
"""
import logging
import os

from .colonyplanets import NAMES, name_for

log = logging.getLogger("surfaces")

#: Where the tool writes and a mod overrides. Per screen, like the discs.
SURFACE_DIR = os.path.join("assets", "surfaces")


class SurfaceSet:
    """The ten surface pictures at sheet resolution, or a stated absence.

    `state` is "ok", "partial" or "missing" — the figure loader's words.
    """

    def __init__(self, resources, root=None):
        self.state = "missing"
        self.surfaces = {}
        self.refused = []
        self._load(resources, root)

    def _load(self, resources, root):
        import pygame
        for name in NAMES:
            for base in ([root] if root else resources.roots()):
                path = os.path.join(base, "screens", "colony_summary",
                                    SURFACE_DIR, f"{name}.png")
                if not os.path.exists(path):
                    continue
                try:
                    image = pygame.image.load(path)
                except pygame.error as err:
                    log.warning("surfaces: %s will not load (%s)", path, err)
                    self.refused.append(path)
                    break
                self.surfaces[name] = (image.convert()
                                       if pygame.display.get_init()
                                       and pygame.display.get_surface()
                                       else image)
                break
        if not self.surfaces:
            log.info("surfaces: none of %d found under %s — run "
                     "`python tools/setup.py` (it runs "
                     "tools/make_surface_tiles.py); the panel draws no "
                     "picture until then", len(NAMES), SURFACE_DIR)
            return
        self.state = "ok" if len(self.surfaces) == len(NAMES) else "partial"

    def get(self, climate):
        """The picture for a climate id, or None."""
        name = name_for(climate)
        return None if name is None else self.surfaces.get(name)


def set_for(screen):
    """The one set, cached per App — it has one size, the sheet's."""
    cached = getattr(screen.app, "surface_set", None)
    if cached is None:
        cached = SurfaceSet(screen.app.res)
        screen.app.surface_set = cached
    return cached
