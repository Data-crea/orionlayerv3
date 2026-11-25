"""The Reference page's row icons — work order 423.

**HD EXTENSION `reference_icons`** (Data's mockup "Futuristic Space
Reference Interface", 22 Nov 2026). The original's Reference index is two
lists of words (info.cpp:997-1116). HD puts a gold symbol in front of every
row: the fourteen categories and the how-to topics. The symbols are the
player's own pictures — cut from his two icon sheets by
`tools/reference_icons_install.py` into the mod folder
(`files/screens/info/assets/icons/<name>.png`) — so OrionLayer ships none; a
row whose picture is missing is drawn as before, words only.

**HD EXTENSION `howto_background`**: a picture the player puts at
`howto_background.png` beside the icons is drawn over the whole how-to text
box, cut to the box from its middle (`background`) and drawn as painted — how bright
and how coloured it is the picture's own business, the code changes nothing; OrionLayer ships none and
a missing file leaves the box as before.

**HD EXTENSION `reference_pictures`** (the same mockup): two wide pictures cut
from it — a planet system and a ship's wireframe — stand under the two lists
of the index and at the foot of a category's or a how-to's text
(`infodraw.art_below`, `art_in`); missing, they are not drawn.

**INVENTION `icons_by_row`.** Which symbol stands before which row is HD's:
the original has none. A row is found by what it IS, not by its words (the
words differ per language): a category by its index in HELP.LBX's category
labels (`pages.categories`, 1..14), a how-to topic by its HELP.LBX record
number (212..227) and the planet chart by its payload. A topic this table
does not know has no symbol.
"""
import os

import pygame

from . import infochart

ICON_REL = "screens/info/assets/icons"

#: category index (`_help_category_labels`, ESTRINGS 0x294..) -> icon name
CATEGORY_ICONS = {
    1: "building",        # Governmental
    2: "planet",          # Planetary Systems
    3: "ringed_planet",   # Space Systems
    4: "spaceship",       # Ship Systems/Crew
    5: "gear",            # Ship Drives
    6: "shield",          # Ship Defenses
    7: "crosshair",       # Ship Weapons
    8: "rocket",          # Missiles/Bombs
    9: "burst",           # Ground Combat
    10: "people",         # Population
    11: "factory",        # Production
    12: "plant",          # Ecology
    13: "lock",           # Security
    14: "laurel",         # Achievements
}
#: how-to record number (HELP.LBX 212..227, in the original's order) -> icon
HOWTO_ICONS = {
    212: "plus",          # Create New Colonies
    213: "move",          # Move Ships
    214: "people",        # Move Colonists
    215: "crown",         # Assign Leaders
    216: "star",          # Go to Antares
    217: "swords",        # Invade Planets
    218: "ring_target",   # Capture Ships
    219: "coins",         # Change Tax Rates
    220: "explosion",     # Prevent Supernovas
    221: "flask",         # Cure a Plague
    222: "skull",         # End Pirate Activity
    223: "comet",         # Destroy a Comet
    224: "wrench",        # Refit Ships
    225: "document",      # Design Ships
    226: "question",      # Get More Help
    227: "flag",          # Pick New Colonies
    infochart.CHART: "galaxy",   # Planet Transformation (HD's own row)
}
#: the group rows of the how-to list (HD EXTENSION `reference_groups`)
GROUP_ICONS = {"hazards": "meteor"}
#: the how-to records folded into the group "hazards", in their order
HAZARDS = (220, 223)       # Prevent Supernovas, Destroy a Comet
#: every icon the tables name, once (the install tool cuts exactly these)
ICON_NAMES = tuple(sorted(set(CATEGORY_ICONS.values())
                          | set(HOWTO_ICONS.values())
                          | set(GROUP_ICONS.values())))
ICON_FILES = tuple(f"{n}.png" for n in ICON_NAMES)
#: the two wide pictures under the lists (the mockup's planet system under
#: the technology list, the ship's wireframe under the how-to list): name ->
#: the file beside the icons. HD EXTENSION `reference_pictures`.
ART_FILES = {"technology": "art_technology.png", "guide": "art_guide.png"}

#: the how-to text's background (Data's "Cinematic Blue Nebula Starfield",
#: 24 Nov): the file beside the icons. HD EXTENSION `howto_background`.
BACKGROUND = "howto_background"

_cache = {}


def _find(name):
    from core import resources
    rel = f"{ICON_REL}/{name}.png".split("/")
    # every root the resolver knows, in its order and with its switches (the
    # mod folder off, `mods/<name>/`): decision 16, WO 426
    for root in tuple(resources.res.roots()):
        if root:
            path = os.path.join(root, *rel)
            if os.path.isfile(path):
                return path
    return None


def picture(name):
    """The icon's convert_alpha surface, or None (cached)."""
    if name not in _cache:
        path = _find(name)
        try:
            _cache[name] = pygame.image.load(path).convert_alpha() \
                if path else None
        except (pygame.error, OSError):
            _cache[name] = None
    return _cache[name]


def art(name):
    """A wide picture of the Reference page (`ART_FILES`), or None."""
    return picture(ART_FILES[name][:-4]) if name in ART_FILES else None


def icon_for(payload):
    """The picture for a row payload — `("cat", index)` or
    `("howto", record)` — or None."""
    if not isinstance(payload, tuple) or len(payload) != 2:
        return None
    table = {"cat": CATEGORY_ICONS, "howto": HOWTO_ICONS,
             "group": GROUP_ICONS}.get(payload[0])
    name = table.get(payload[1]) if table else None
    return picture(name) if name else None


def background(size, anchor=(0.5, 0.5)):
    """HD EXTENSION `howto_background`: the player's background picture
    scaled to cover `size` and cut to it round `anchor` (0..1 across, down;
    the middle by default: a narrow box can be cut from a corner where the
    picture has more to show), or None when the
    file is missing. Up to eight sizes are kept (the Reference's boxes)."""
    back = picture(BACKGROUND)
    if back is None:
        return None
    key = ("cover", tuple(size), tuple(anchor))
    if key not in _cache:
        sized = [k for k in _cache if isinstance(k, tuple)]
        if len(sized) >= 8:        # a drag-resize makes a size per step
            for old in sized:
                del _cache[old]
        k = max(size[0] / back.get_width(), size[1] / back.get_height())
        big = pygame.transform.smoothscale(
            back.convert(), (max(size[0], round(back.get_width() * k)),
                             max(size[1], round(back.get_height() * k))))
        cut = pygame.Surface(size)
        cut.blit(big, (0, 0), pygame.Rect(
            round((big.get_width() - size[0]) * anchor[0]),
            round((big.get_height() - size[1]) * anchor[1]), *size))
        _cache[key] = cut
    return _cache[key]
