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
    if bid not in _pictures:
        surf = None
        path = tree_path(bid)
        if path is not None:
            import pygame
            from core import resources
            found = resources.res.resolve(path)
            if found:
                try:
                    raw = pygame.image.load(found)
                    # always 32 bit with alpha: smoothscale refuses an
                    # 8-bit picture, and there may be no display yet
                    surf = pygame.Surface(raw.get_size(), pygame.SRCALPHA)
                    surf.blit(raw, (0, 0))
                except (pygame.error, OSError) as err:
                    log.warning("building picture %s cannot be read (%s) — "
                                "the original's drawing is used", path, err)
        _pictures[bid] = surf
    return _pictures[bid]


def present():
    """The ids that have a picture, as a tuple (a cache key), kept until
    `forget` — asked every frame."""
    if "present" not in _fitted:
        _fitted["present"] = tuple(
            b for b in range(1, COUNT + 1) if picture(b) is not None)
    return _fitted["present"]


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


def forget():
    """Drop what was read (a check changes the mod folder under it)."""
    _pictures.clear()
    _fitted.clear()
