"""HD ships and monsters on the Fleets minimap — the stack icons.

HD EXTENSION `minimap_hd_icons` (Data: the HD monsters' and ships' icons
belong on the Fleets screen's small map, reduced to the right size). The
original draws one 5 to 15 px sprite per stack (FLEET.LBX 19-33,
flt1.cpp:216-235); HD draws the picture the galaxy map draws for the same
stack — `shippics.ShipPictures`, the representative ship in the owner's
colour and the player's livery (HD EXTENSION `strongest_ship_icon`), a
monster's master from `screens/galaxy_map/assets/ships/<kind>/0.png`.

THE SIZE IS THE ORIGINAL SPRITE'S OWN DRAWN PIXELS (`shippicture.footprint`,
the rule `painted_lists` uses in the grid): the picture is cut to its pixels
and fitted into that box, aspect kept, never over it — so every stack keeps
the size the original gives it there, and a stack stays as easy to hit.

Nothing HD to draw (the mod folder and masters absent, the map's
`map_ship_pictures` setting off, a monster without a master — the Antaran,
the amoeba — or no original sprite to measure) answers None and the
caller draws the original's sprite, as before. Sends nothing.
"""
import pygame

from core import shippicture, shipstacks
from core.structs import ship as ship_struct
from screens.galaxy_map import shippics
from screens.galaxy_map import ships as map_ships

_TINTS = None
_PARSED = [None, []]
_MASTERS = {}
_SCALED = {}
KEEP = 128


def _tints():
    global _TINTS
    if _TINTS is None:
        _TINTS = map_ships.TintCache()
    _TINTS.follow()
    return _TINTS


def _ships(game_state):
    """Every ship parsed, once per snapshot (the icons ask each frame)."""
    raws = getattr(game_state, "ships_raw", None)
    if _PARSED[0] is not raws:
        _PARSED[0] = raws
        _PARSED[1] = [ship_struct.parse(r) for r in (raws or [])]
    return _PARSED[1]


def _head(game_state, icon):
    sel = getattr(game_state, "fleet_selection", None)
    ships = _ships(game_state)
    node = int(icon.node_idx)
    if not sel or not 0 <= node < len(sel["ships"]):
        return None
    head = sel["ships"][node]
    return ships[head] if 0 <= head < len(ships) else None


def _master(app, kind):
    """A monster's master picture cut to its pixels, or None."""
    path = app.res.screen_file("galaxy_map", "assets", "ships", kind,
                               "0.png")
    if not path:
        return None
    if path not in _MASTERS:
        try:
            surf = pygame.image.load(path)
            surf = surf.convert_alpha() if pygame.display.get_surface() \
                else surf.convert_alpha(pygame.Surface((1, 1),
                                                       pygame.SRCALPHA))
            vis = shippics.visible(surf)
            _MASTERS[path] = vis.copy() if vis is not None else None
        except (pygame.error, OSError):
            _MASTERS[path] = None
    return _MASTERS[path]


def _fit(master, path_key, box):
    key = (path_key, box.w, box.h)
    if key not in _SCALED:
        if len(_SCALED) >= KEEP:
            _SCALED.clear()
        _SCALED[key] = shippics.fitted(master, box.w, box.h)
    return _SCALED[key]


def picture(app, game_state, icon, sprite, at):
    """(surface, topleft) for one stack icon, or None for the original's
    sprite. `sprite` is the original's small picture, blitted at `at`
    after magnifying by `step`; its drawn pixels are the box."""
    if sprite is None or app is None:
        return None
    settings = getattr(app, "user_settings", None)
    if settings is not None and settings.get(shippics.SETTING) == "off":
        return None
    box = shippicture.footprint(sprite, at, 1)
    owner = int(icon.owner)
    kind = map_ships.kind_for_owner(owner)
    if kind is None:
        return None
    if kind != map_ships.PLAYER_KIND:
        master = _master(app, kind)
        pic = _fit(master, kind, box) if master is not None else None
    else:
        head = _head(game_state, icon)
        colour = shipstacks.colour_of(game_state, owner)
        if head is None or colour is None:
            return None
        tints = _tints()
        ship = tints.pictures.representative(
            head, _ships(game_state), getattr(game_state, "player_num", None))
        built = int(ship.previous_owner)
        shape = shipstacks.colour_of(game_state, built) \
            if 0 <= built < shipstacks.MAX_PLAYERS else None
        pic = tints.pictures.icon(
            ship, colour, colour if shape is None else shape, box.w, box.h,
            settings, shippicture.own_colour(game_state))
    if pic is None:
        return None
    return pic, (box.x + (box.w - pic.get_width()) // 2,
                 box.y + (box.h - pic.get_height()) // 2)
