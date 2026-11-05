"""The player's HD building pictures — HD EXTENSION `building_pictures`.

The original draws every building as a 640 x 480 indexed picture per cell
of the colony's 6 x 6 ground (BLDG<n>.LBX) and a satellite as a small
COLONY.LBX picture. A painter may replace a building with ONE picture with
transparency, `files/screens/colony/assets/buildings/<NN>_<name>.png` in the
player's mod folder (`core.usermod`, a slot; the tree and the base pack ship
none): NN is the building's id (1..48, techdata.cpp:25-74), the name is the
building's, from `NAMES`. The picture is the whole building, tight to its
ink, any size — it is fitted into the footprint of the original's drawing
(`fit`), never stretched, and drawn at the size the window asks for, so a
4K window shows it at about the original's drawing times four.

Used by the colony's ground and sky (`screens/colony/colbuildings`), the
colony's build box and the build popup's picture box
(`screens/colony/colroom`). A building without a picture of its own is
drawn as the original's, and a file that will not load is said once in the
log and skipped.
"""
import logging
import threading

log = logging.getLogger("buildingart")

FOLDER = "screens/colony/assets/buildings"
#: building id 1..48 -> the name its file carries (`buildnames` spells them
#: for the player; these are file names, so they stay put).
NAMES = (
    "alien_control_center", "armor_barracks", "artemis_system_net",
    "astro_university", "atmosphere_renewer", "autolab", "automated_factory",
    "battlestation", "capitol", "cloning_center", "colony_base",
    "deep_core_mine", "core_waste_dump", "dimensional_portal", "biospheres",
    "food_replicators", "gaia_transformation", "currency_exchange",
    "galactic_cybernet", "holo_simulator", "hydroponic_farm",
    "marine_barracks", "barrier_shield", "flux_shield", "gravity_generator",
    "missile_base", "ground_batteries", "radiation_shield", "stock_exchange",
    "supercomputer", "pleasure_dome", "pollution_processor", "recyclotron",
    "robotic_factory", "research_lab", "robo_miner_plant", "soil_enrichment",
    "space_academy", "spaceport", "star_base", "star_fortress",
    "stellar_converter", "subterranean_farms", "terraforming",
    "warp_interdictor", "weather_controller", "fighter_garrison",
    "artificial_planet")
COUNT = len(NAMES)

_pictures = {}
_fitted = {}
#: Bumped by `forget`: a load that began before it must not store its
#: picture after it (the background warm-up, `prewarm`, is such a load).
_gen = [0]
_lock = threading.RLock()


def tree_path(bid):
    """The tree path of building `bid`'s picture, or None for a bad id."""
    if not 1 <= int(bid) <= COUNT:
        return None
    return f"{FOLDER}/{int(bid):02d}_{NAMES[int(bid) - 1]}.png"


def slots():
    """Every name a mod may fill (`core.usermod.SLOTS`)."""
    return tuple(tree_path(b) for b in range(1, COUNT + 1))


def picture(bid):
    """The building's picture (RGBA), or None — absent or unreadable."""
    bid = int(bid)
    with _lock:
        if bid in _pictures:
            return _pictures[bid]
        gen = _gen[0]
        surf = _load(bid)
        if gen == _gen[0]:
            _pictures[bid] = surf
        return surf


def _load(bid):
    path = tree_path(bid)
    if path is None:
        return None
    import pygame
    from core import resources
    found = resources.res.resolve(path)
    if not found:
        return None
    try:
        raw = pygame.image.load(found)
        # always 32 bit with alpha: smoothscale refuses an 8-bit
        # picture, and there may be no display yet
        surf = pygame.Surface(raw.get_size(), pygame.SRCALPHA)
        surf.blit(raw, (0, 0))
        return surf
    except (pygame.error, OSError) as err:
        log.warning("building picture %s cannot be read (%s) — "
                    "the original's drawing is used", path, err)
        return None


def present():
    """The ids the mod folder holds a picture for, as a tuple (a cache
    key), kept until `forget` — asked every frame.

    FROM THE FOLDER'S INDEX, NOT FROM THE PICTURES: this used to read all
    48 files on the first frame (about a second at 4K, the colony
    screen's first opening) to learn which exist, while the screen needs
    only the few buildings on show. A file that will not load is still
    listed here and answers None from `picture`, which every caller
    already handles."""
    if "present" not in _fitted:
        from core import usermod
        index = usermod._state.get("index") or {}
        _fitted["present"] = tuple(
            b for b in range(1, COUNT + 1) if tree_path(b) in index)
    return _fitted["present"]


def prewarm():
    """Read the pictures in the background, so the colony screen's first
    frame finds them in memory. Returns the thread (None when there is
    nothing to read). Cosmetic: it answers nothing and `picture` stays
    correct without it; a `forget` meanwhile drops what it read."""
    ids = present()
    if not ids:
        return None

    def work():
        for b in ids:
            picture(b)
    thread = threading.Thread(target=work, name="buildingart-prewarm",
                              daemon=True)
    thread.start()
    return thread


def fit(bid, w, h):
    """The building's picture scaled, aspect kept, to the largest size that
    fits `w` x `h` — or None without a picture. Smooth: it is a painting,
    not the original's indexed pixels (decision 28 is about those)."""
    pic = picture(bid)
    if pic is None or w < 1 or h < 1:
        return None
    key = (int(bid), int(w), int(h))
    if key not in _fitted:
        import pygame
        if len(_fitted) > 200:
            _fitted.clear()                    # (and `present` with it)
        s = min(w / pic.get_width(), h / pic.get_height())
        size = (max(1, round(pic.get_width() * s)),
                max(1, round(pic.get_height() * s)))
        _fitted[key] = pygame.transform.smoothscale(pic, size)
    return _fitted[key]


def fit_height(bid, h):
    """The building's picture scaled, aspect kept, to exactly `h` tall (its
    width follows) — or None without a picture. A satellite's painting
    stands as tall as the original's sprite (`colbuildings`,
    `satellite_height`). Smooth, like `fit`."""
    pic = picture(bid)
    if pic is None or h < 1:
        return None
    key = (int(bid), 0, int(h))
    if key not in _fitted:
        import pygame
        if len(_fitted) > 200:
            _fitted.clear()
        w = max(1, round(pic.get_width() * h / pic.get_height()))
        _fitted[key] = pygame.transform.smoothscale(pic, (w, int(h)))
    return _fitted[key]


def forget():
    """Drop what was read (a check changes the mod folder under it)."""
    with _lock:
        _gen[0] += 1
        _pictures.clear()
        _fitted.clear()
