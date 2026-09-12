"""The planet discs: one sprite per climate, at the size asked for.

**DATA'S ARTWORK, CUT BY `tools/planet_extract.py`.** Ten 54 x 54 RGBA
sprites under `assets/planets/`, one per `PLANET_CLIMATE`
(orion2_consts.h:362-374). They are committed, like `assets/frame.png`
and unlike the population figures: those come out of the player's own
RACEICON.LBX and these are the project's own art.

**THE CLIMATE ID IS THE WHOLE MAPPING.** `colonyrows` puts
`s_colony.climate` in every row (`colonyrows`'s own docstring carries
why it is the COLONY's field and not the planet's), the sheet is drawn
in the enum's order, and `NAMES` below is that order written once. So
the icon on a row and the word in "Terran 13/22" under it are the same
number read twice, and there is nothing to keep in step.

**SCALED LIKE A FIGURE, NEVER SMOOTHED.** Nearest neighbour to
whatever the layout asks for, one cached set per pixel size, no
`smoothscale` anywhere — the same rule the population figures follow
(decision 28 and its marked exception). The master is 54 px because
that is the row icon's height at 1920x1080, so the reference
resolution draws this art at 1:1 and every other size steps from it.
"""
import collections
import logging
import os

log = logging.getLogger("planets")

#: Where the extractor writes and a mod overrides. PER SCREEN, not
#: shared: the galaxy map draws no planets, and a shared folder would
#: say it does.
PLANET_DIR = os.path.join("assets", "planets")

#: The extractor's own output size. One number, two readers — the
#: tool writes it and a smoke check asserts the files are it.
MASTER_SIZE = 54

#: `PLANET_CLIMATE` (orion2_consts.h:362-374) in the enum's own order,
#: ids 0 to 9. The file name is the enum's name lowercased, which is
#: what makes a mod's replacement obvious to find.
NAMES = ("toxic", "radiated", "barren", "desert", "tundra",
         "ocean", "swamp", "arid", "terran", "gaia")

#: How many sets are kept, by pixel size. Two are live at once on this
#: screen — the row icon and the big disc in `planet_info` — and a
#: resize makes two more; four is that with one window's worth of
#: history, and each set is ten sprites.
SET_CACHE = 4


def name_for(climate):
    """The file's name for a climate id, or None if it is not one.

    None rather than a guess: a climate this build has never heard of
    draws no disc and the row keeps its text, which is the same shape
    `colonyfigures.figure_for` takes for a race it cannot name.
    """
    if climate is None:
        return None
    climate = int(climate)
    return NAMES[climate] if 0 <= climate < len(NAMES) else None


class PlanetSet:
    """The ten discs at one pixel size, or a stated absence.

    `state` is "ok", "partial" or "missing", the same three words the
    figure loader uses. An absent set draws no icon and the rows are
    what they were before the artwork existed — a state of the
    feature, not an error.
    """

    def __init__(self, resources, size, root=None):
        size = int(size)
        assert size > 0, f"a planet set needs a pixel size, got {size}"
        self.size = size
        self.state = "missing"
        self.planets = {}
        self.refused = []
        self._load(resources, root)

    def _load(self, resources, root):
        import pygame
        for name in NAMES:
            for base in ([root] if root else resources.roots()):
                path = os.path.join(base, "screens", "colony_summary",
                                    PLANET_DIR, f"{name}.png")
                if not os.path.exists(path):
                    continue
                try:
                    image = pygame.image.load(path)
                except pygame.error as err:
                    log.warning("planets: %s will not load (%s)", path, err)
                    self.refused.append(path)
                    break
                if image.get_size() != (MASTER_SIZE, MASTER_SIZE):
                    log.warning(
                        "planets: %s is %dx%d and must be %dx%d — "
                        "refused, the disc is left out",
                        path, image.get_size()[0], image.get_size()[1],
                        MASTER_SIZE, MASTER_SIZE)
                    self.refused.append(path)
                    break
                image = image.convert_alpha() if pygame.display.get_init() \
                    else image
                # NEAREST IN BOTH DIRECTIONS. Up at every window from
                # 1920x1080 and the big disc everywhere; DOWN at
                # 1280x720 and 1366x768, where the row band leaves
                # less than the master. `smoothscale` would blend the
                # sheet's colours into ones it does not contain, which
                # is the thing decision 28 is about.
                self.planets[name] = image if self.size == MASTER_SIZE \
                    else pygame.transform.scale(image,
                                                (self.size, self.size))
                break
        if not self.planets:
            log.info("planets: none of %d found under %s — run "
                     "`python tools/planet_extract.py`",
                     len(NAMES), PLANET_DIR)
            return
        self.state = "ok" if len(self.planets) == len(NAMES) else "partial"

    def get(self, climate):
        """The disc for a climate id, or None."""
        name = name_for(climate)
        return None if name is None else self.planets.get(name)


def icon_size(area, cfg):
    """The row icon's side in device px — square, and the band's.

    `band - 2 * figure_step` is the clearance the population figures
    already keep from the cell plate's line, top and bottom, so the
    disc cannot touch it either. At 1920x1080 that is 54, which is
    `MASTER_SIZE`, so the reference resolution draws Data's sheet at
    1:1 (`tools/planet_extract.py` picks the master's size from this
    end).

    Here rather than on the screen because it is planet geometry and
    this module is where a planet's size is decided — the screen asks
    for a set and blits what it gets.
    """
    from . import colonytrack
    return max(1, colonytrack.band_height(area, cfg)
               - 2 * colonytrack.figure_step(area, cfg))


def set_for(screen, size):
    """The planet set at `size` px, cached per App with an LRU.

    Keyed by pixel size for the same reason `colonyfigures.set_for`
    is: the row icon's size comes from the band and the panel's from
    the panel, so a window serves two sizes at once and a resize can
    ask for two more.
    """
    size = int(size)
    if size <= 0:
        return None
    cache = getattr(screen.app, "planet_sets", None)
    if cache is None:
        cache = collections.OrderedDict()
        screen.app.planet_sets = cache
    if size in cache:
        cache.move_to_end(size)
    else:
        cache[size] = PlanetSet(screen.app.res, size)
        while len(cache) > SET_CACHE:
            cache.popitem(last=False)
    return cache[size]
