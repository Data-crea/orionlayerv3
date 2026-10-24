"""The planet pictures: one per climate, at the size asked for.

**WORK ORDER 331: A PLANET IS A TURNING SPHERE.** Where a climate has a map
(`assets/shared/planets/<type>_surface.png`) `PlanetSet.get` returns the
sphere as it is NOW (`core.planetsphere`), and what follows describes the
STATIC pictures that remain: a mod's old-style full picture for a type it
gives no map (`uses_sphere`), which draws exactly as it always did.

**THE OLD STILLS.** Ten 54 x 54 RGBA sprites under `assets/planets/`, one
per `PLANET_CLIMATE` (orion2_consts.h:362-374), Data's art cut by a tool
that went out with the pictures (work order 331); only a mod can supply
them now.

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

**DEVIATION `painted_planets` (Data, 16 Oct 2026): DATA'S BATTLE PLANETS
FIRST.** Where the player's mod folder holds Data's painted battle
planets (`files/screens/combat/assets/gamedata/cmbtplnt/<n>_0.png`, n =
climate * 6 + size, the combat screen's own slot, decision 81), every
place that draws a planet draws THAT picture, for the planet's climate
and size (`painted`): the discs here, the galaxy map's system window,
the Leaders screen's system display, the Planets list, the colony
screen's system display and the invasion popup. A painted picture is
many times the size it is drawn at, so it is cut to its ink and SMOOTHLY
scaled down (decision 28 is about magnifying the game's pixel art, which
these are not). Without them the discs stand as before; a list, which
knows no size, takes LIST_PLANET_SIZE.

**HD EXTENSION `planet_pictures` (Data, work order 326 F): THE PLANET
CHART FIRST.** "Wherever the game shows a planet, these replace it": a
picture per climate in the mod folder's own slot
(`files/screens/colony_summary/assets/planet_pictures/<climate>.png`,
`PICTURE`, the names of `NAMES`) wins over the painted battle planets in
every place above, at every size — the chart has one picture per climate
and no sizes, so the size is the place's own, as for the battle planets.
The same rules hold (PAINTED_MIN, cut to its ink, smoothly scaled). The
battle itself does not come through here (`screens/combat/cbart.py` reads
its own slot), so the painted battle planets stay the battle's until Data
decides (work order 326, parked).
"""
import logging
import os
from core import planetsphere
from . import setcache

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

#: Data's painted battle planets, resolved like every file (the mod
#: folder first); in the project tree this slot holds no PNG, so a hit
#: is a painting. Smaller than PAINTED_MIN is not one (the stored
#: drawings are 56..150 px) and is left to the discs.
PAINTED = "screens/combat/assets/gamedata/cmbtplnt/{}_0.png"
PAINTED_MIN = 200
#: The planet chart's slot (`planet_pictures`), by climate name; asked
#: before PAINTED. A slot of `core.usermod.SLOTS`: nothing of ours is there.
PICTURE = "screens/colony_summary/assets/planet_pictures/{}.png"
#: The size a place that knows none draws (the lists): large.
LIST_PLANET_SIZE = 3
_painted_src = {}
_painted_drawn = {}

#: How many sets are kept, by pixel size. Two are live at once on this
#: screen — the row icon and the big disc in `planet_info` — and a
#: resize makes two more; four is that with one window's worth of
#: history, and each set is ten sprites. Since `painted_planets` a
#: place that draws planets by size (the galaxy map's system window,
#: five sizes at once) keeps a set per size, so twelve.
SET_CACHE = 12


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


def _painted_source(path):
    import pygame
    try:
        stamp = os.stat(path).st_mtime_ns
    except OSError:
        return None
    hit = _painted_src.get(path)
    if hit is not None and hit[0] == stamp:
        return hit[1]
    img = None
    try:
        img = pygame.image.load(path)
        img = img.convert_alpha() if pygame.display.get_surface() else img
        if max(img.get_size()) < PAINTED_MIN:
            img = None
        else:
            ink = img.get_bounding_rect(min_alpha=8)
            # a picture with no visible pixel (a placeholder) is no picture:
            # a 0 x 0 surface would divide by zero where it is fitted
            img = img.subsurface(ink).copy() if ink.w and ink.h else None
    except (pygame.error, OSError, ValueError) as err:
        log.warning("planets: %s will not load (%s)", path, err)
        img = None
    _painted_src[path] = (stamp, img)
    return img


def painted(resources, climate, planet_size, side):
    """Data's painted planet for `climate` and `planet_size` on a `side`
    px square (centred, its proportion kept), or None when the mod folder
    has none (`painted_planets`)."""
    import pygame
    side = int(side)
    if climate is None or planet_size is None or side <= 0:
        return None
    climate, planet_size = int(climate), int(planet_size)
    if not (0 <= climate < len(NAMES) and 0 <= planet_size <= 4):
        return None
    src = None
    # the chart's picture of the climate first, then the battle planet
    # of climate and size (`planet_pictures`, `painted_planets`)
    for slot in (PICTURE.format(NAMES[climate]),
                 PAINTED.format(climate * 6 + planet_size)):
        path = resources.resolve(slot)
        if path and path.lower().endswith(".png"):
            src = _painted_source(path)
        if src is not None:
            break
    if src is None:
        return None
    key = (path, _painted_src[path][0], side)
    hit = _painted_drawn.get(key)
    if hit is not None:
        return hit
    w, h = src.get_size()
    k = side / max(w, h)
    pic = pygame.transform.smoothscale(
        src, (max(1, round(w * k)), max(1, round(h * k))))
    out = pygame.Surface((side, side), pygame.SRCALPHA)
    out.blit(pic, pic.get_rect(center=(side // 2, side // 2)))
    if len(_painted_drawn) > 256:
        _painted_drawn.clear()
    _painted_drawn[key] = out
    return out


def uses_sphere(resources, name, painted_found):
    """WO 331: a type is a turning sphere wherever it has a map — except a
    type a mod still supplies an old-style full picture for (the chart's,
    a painted battle planet, or a 54 px disc in a mod's own `planets/`)
    and no map of its own: that stays the static picture, no rotation, no
    error (`painted_found` says the first two were found)."""
    if not planetsphere.surface_path(resources, name):
        return False
    old = painted_found or any(
        os.path.exists(os.path.join(base, "screens", "colony_summary",
                                    PLANET_DIR, f"{name}.png"))
        for base in resources.roots() if not planetsphere.in_base(base))
    return not old or planetsphere.mod_map(resources, name)


def turning(resources, climate, side, seed=None, planet_size=None):
    """The turning sphere of `climate` on a `side` px square NOW, or None
    where the type is a static picture or has no map — for the places with
    no screen to ask a set from (the popups, the battle)."""
    name = name_for(climate)
    if name is None or side < 4:
        return None
    found = planet_size is not None and painted(
        resources, int(climate), planet_size, side) is not None
    if not uses_sphere(resources, name, found):
        return None
    return planetsphere.frame(resources, name, int(side), seed, int(climate))


class PlanetSet:
    """The ten discs at one pixel size, or a stated absence.

    `state` is "ok", "partial" or "missing", the same three words the
    figure loader uses. An absent set draws no icon and the rows are
    what they were before the artwork existed — a state of the
    feature, not an error.
    """

    def __init__(self, resources, size, root=None, planet_size=None):
        size = int(size)
        assert size > 0, f"a planet set needs a pixel size, got {size}"
        self.size = size
        self.state = "missing"
        self.planets = {}
        #: Climates drawn as a turning sphere (`core.planetsphere`); they
        #: have no entry in `planets`. The static picture stays for a type
        #: whose map is missing or whose mod supplies an old-style picture.
        self.spheres = set()
        self.res = resources
        self.refused = []
        self.planet_size = LIST_PLANET_SIZE if planet_size is None \
            else int(planet_size)
        self._load(resources, root)

    def _load(self, resources, root):
        import pygame
        for climate, name in enumerate(NAMES):
            pic = None if root else painted(resources, climate,
                                            self.planet_size, self.size)
            if not root and uses_sphere(resources, name, pic is not None):
                self.spheres.add(name)
                continue
            if pic is not None:
                self.planets[name] = pic
                continue
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
        if not self.planets and not self.spheres:
            log.info("planets: none of %d found under %s — run "
                     "`python tools/planet_extract.py`",
                     len(NAMES), PLANET_DIR)
            return
        self.state = "ok" if len(self.planets) + len(self.spheres) \
            == len(NAMES) else "partial"

    def get(self, climate, seed=None):
        """The picture for a climate id, or None: the turning sphere as it
        is NOW where the type has one (`seed` names the planet, so it keeps
        its own start and speed on every screen), else the static disc."""
        name = name_for(climate)
        if name is None:
            return None
        if name in self.spheres:
            return planetsphere.frame(self.res, name, self.size, seed,
                                      int(climate))
        return self.planets.get(name)


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


def set_for(screen, size, planet_size=None):
    """The planet set at `size` px, cached per App with an LRU; with
    Data's painted planets, those of `planet_size` (LIST_PLANET_SIZE when
    the place knows none).

    Keyed by pixel size for the same reason `colonyfigures.set_for`
    is: the row icon's size comes from the band and the panel's from
    the panel, so a window serves two sizes at once and a resize can
    ask for two more.
    """
    size = int(size)
    if size <= 0:
        return None
    key = size if planet_size is None else (size, int(planet_size))
    args = (screen.app.res, size) if planet_size is None else \
        (screen.app.res, size, None, int(planet_size))
    return setcache.lru(screen.app, "planet_sets", key,
                        lambda: PlanetSet(*args), SET_CACHE)
