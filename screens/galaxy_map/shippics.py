"""The strongest ship as a player stack's map icon — work order 311.

HD EXTENSION `strongest_ship_icon` (Data, 19 October 2026): the original
draws every player stack with one icon per owner colour, whatever the
ships are (BUFFER0.LBX 205 + colour * 4 + zoom, `Get_Ship_Icon_Pict_Seg_`,
ships.cpp:336-397). HD draws the battle picture of the stack's
representative ship instead, facing right, cropped to its visible pixels
and fitted into the icon box `ships.icon_box` already gives — the box,
the slot, the place and the hit test of `[galaxy_map.ships]` do not
change. Registered in `layout.json` `_markings`.

WHICH SHIP. The original sorts each stack descending by
`size * 50 + picture_num` for a combat ship, colony -1, transport -2,
outpost -3 (`Build_Ship_Type_Array_`, shipstak.cpp:283-316) and the icon's
`node_idx` is that sort's head (ships.cpp:653-680). Data's rule for the
player's OWN stacks: the Avenger first, always (Loknar's ship, picture 44
on a player owner, the original's own test colrefit.cpp:196, :458), then
the largest hull, then the higher design cost — DEVIATION
`strongest_tie_by_cost`: the original breaks a size tie by picture_num.
An own stack is rebuilt from `ships_raw` by the original's key — the same
location, x, y and owner, status below 3 (`Find_Ship_Stacks_`,
shipstak.cpp:56-80). Non-combat ships keep the original's order among
themselves (colony, transport, outpost).

A FOREIGN stack is not rebuilt: `ships_raw` holds every ship, the
undetected ones too, and FSEL has no `next_node`, so a rebuilt foreign
stack could show a ship the player has not detected
(`Remove_Non_Detected_Ships_`). It shows the head the original resolves —
DEVIATION `foreign_stack_head`: the original's order is the hull, then
picture_num, so a foreign Avenger (huge, 3 * 50 + 44) beside a Titan or a
Doom Star (5 * 50 + 43) shows the Doom Star, and a size tie goes by
picture_num, not cost. Data's rule for them needs the stack's chain on the
wire (open fix 20 rev 3, `next_node`), not built.

WHICH PICTURE, in this order — the shape is always the builder's
(`previous_owner`'s colour set, the battle's `unit_picture`), the colour the
owner's (as the Fleets screen draws a captured ship, flt1.cpp:561):
1. the map's own slot, `screens/galaxy_map/assets/ship_pictures/`: the
   builder colour's file `<colour>_<picture>.png` drawn as painted (an
   uncaptured ship's builder is its owner), else the colour-free
   `all_<picture>.png` with its neutral grey in the owner's colour (the
   battle's rule, `cbpaint.recoloured`); a captured ship never takes its
   owner's own file — that is the owner's shape. Keyed by picture_num, any
   ship: 45 colony ship, 46 outpost ship and 47 transport have no battle
   picture, so this slot is theirs alone (Data: "bei den Transportschiffen
   ... fehlt noch ein HD-Bild"). The player's mod folder before the base
   pack (`core.usermod.SLOTS`, `core.resources`), per file.
2. a combat ship's battle picture (`cbart.CombatArt`, the precedent is the
   livery window's preview): the Avenger as the battle draws it for every
   owner (MONSTER.LBX 25); the builder's own painted file as painted; the
   colour-free painted picture in the owner's colour — on the map in the
   owner's colour at FULL strength, the Full pattern, the livery's core
   kept (`map_livery`, HD EXTENSION `strongest_ship_icon`: the livery's
   strength and zones are a battle's look, at 20 px they leave every owner
   the metal's grey — owner 4 measured (96, 101, 103) beside the player's
   (104, 94, 89) under strength 0.33); the stored drawing of the builder's
   set with its ship ramp replaced by the owner's, under a colour preset
   that ramp moved to the preset's colour, so a stored drawing matches the
   painted ones and the tinted master.
3. none: `ships.render` draws the tinted master as before — no extraction,
   no painted file, a non-combat ship without its slot file, or the
   setting `map_ship_pictures` off (the OrionLayer window's GAMEPLAY tab,
   applied at once).

HELD ONCE, SCALED PER BOX: a picture is made once per (ship, colours,
detail, preset, map livery) — the detail the smallest whole factor at which
the ship reaches its box, never above the player's `painted_detail`
(`core.paintdetail.cap`, as `core.shippicture` holds it) — and scaled from
it for each box size, so HD's continuous zoom rescales and does not rebuild;
both caches are bounded and dropped, with the map's own battle art, when the
map leaves or the window changes size (`ships.TintCache.clear`).
"""
import logging

import numpy as np
import pygame

from core import palette
from core.structs import ship as ship_struct

log = logging.getLogger("galaxy_map.shippics")

#: The user setting and its values (`core.usersettings.DEFAULTS`).
SETTING = "map_ship_pictures"
STEPS = ("on", "off")
#: The map's own picture slot, a tree path the mod folder's `files/` and the
#: base pack fill (`core.usermod.SLOTS`).
SLOT = "screens/galaxy_map/assets/ship_pictures"
#: picture_num of Loknar's Avenger (ship_config.cpp:68; colrefit.cpp:196).
AVENGER = 44
#: The original's order of the non-combat types (shipstak.cpp:300-308).
_NON_COMBAT_RANK = {ship_struct.SHIP_TYPE_COLONY: -1,
                    ship_struct.SHIP_TYPE_TRANSPORT: -2,
                    ship_struct.SHIP_TYPE_OUTPOST: -3}
#: A ramp entry this far from grey (max - min channel, 0-255) is the
#: colour's; the stored ramp's second half is a neutral grey every colour
#: shares (measured: CMBTSHP 44 + colour * 45, chroma 0-16 there).
_RAMP_CHROMA = 24


def strength(ship):
    """Data's order, highest first: a combat ship before any other, the
    Avenger before every combat ship, then the hull size, then the design
    cost; the non-combat types in the original's order."""
    if int(ship.ship_type) == ship_struct.SHIP_TYPE_COMBAT:
        avenger = int(ship.picture_num) == AVENGER and 0 <= int(ship.owner) < 8
        return (1, int(avenger), int(ship.size), int(ship.cost))
    return (0, 0, _NON_COMBAT_RANK.get(int(ship.ship_type), -4), 0)


def stack_key(ship):
    """The original's stack: location, x, y, owner (shipstak.cpp:72-75)."""
    return (int(ship.location), int(ship.x), int(ship.y), int(ship.owner))


def strongest_by_stack(ships):
    """{stack key: its strongest ship} of every ship with status < 3; on a
    full tie the first in the array, the original's own build order."""
    out = {}
    for s in ships:
        if int(s.status) >= ship_struct.STATUS_STACK_SKIP:
            continue
        k = stack_key(s)
        if k not in out or strength(s) > strength(out[k]):
            out[k] = s
    return out


def owner_rgb(colour):
    from screens.combat import cbpaint
    return cbpaint.owner_rgb(colour)


#: Pictures held unscaled (a map's own and foreign stacks, a few per
#: detail), and fitted ones (a zoom sweep makes one per box size).
KEEP_PICTURES = 64
KEEP_FITTED = 256


def map_livery(liv, own=None):
    """The livery a map picture is coloured in: the owner's colour at full
    strength over the whole plating (Full), the livery's core kept — the
    battle's strength and zones make every owner the metal's grey at map
    size (HD EXTENSION `strongest_ship_icon`)."""
    from core import livery
    liv = liv or livery.DEFAULT
    return livery.Livery("full", liv.core, None, 1.0,
                         own if liv.own is None else liv.own)


class ShipPictures:
    """The pictures made so far, cleared with the tinted sprites
    (`ships.TintCache.clear`). `art` a stand-in used at every detail (the
    checks); else one `CombatArt` per detail, made when first asked and
    dropped with the caches."""

    def __init__(self, art=None):
        self._given = art
        self._arts = {}
        self._pictures = {}
        self._made = {}
        self._stacks = (None, {})

    def clear(self):
        self._made.clear()
        self._pictures.clear()
        self._arts.clear()
        self._stacks = (None, {})

    # ── which ship ─────────────────────────────────────────────────
    def representative(self, head, ships, me):
        """The ship whose picture stands for the head's stack: rebuilt for
        the player's own stack, the head itself for a foreign one."""
        if head is None:
            return None
        if me is None or int(head.owner) != int(me) or not ships:
            return head
        if self._stacks[0] is not ships:
            self._stacks = (ships, strongest_by_stack(ships))
        return self._stacks[1].get(stack_key(head), head)

    # ── which picture ──────────────────────────────────────────────
    def art(self, cap=1):
        """The battle art holding painted pictures at `cap` x at most."""
        if self._given is not None:
            return self._given
        if cap not in self._arts:
            from screens.combat import cbart
            art = cbart.CombatArt()
            art.set_detail(cap)
            self._arts[cap] = art
        return self._arts[cap]

    def icon(self, ship, colour, shape, box_w, box_h, settings=None,
             own=None):
        """`ship`'s picture in the owner colour `colour` (0-7), drawn in the
        builder colour `shape`'s set, fitted into box_w x box_h; None for
        the tinted master. `own` is the player's colour."""
        if ship is None or colour is None:
            return None
        if settings is not None and settings.get(SETTING) == "off":
            return None
        liv = map_livery(self._livery(settings, own), own)
        key = (int(colour), int(shape), int(ship.picture_num),
               int(ship.ship_type), palette.active_preset(), liv.key())
        pic, painted = self._unscaled(ship, key, liv, 1)
        cap = 1
        if pic is not None and painted:
            cap = detail_for(pic, box_w, box_h, settings)
            if cap > 1:
                pic = self._unscaled(ship, key, liv, cap)[0] or pic
        fk = (key, cap, int(box_w), int(box_h))
        if fk not in self._made:
            if len(self._made) >= KEEP_FITTED:
                self._made.clear()
            self._made[fk] = fitted(pic, box_w, box_h)
        return self._made[fk]

    def _unscaled(self, ship, key, liv, cap):
        """(picture cut to its pixels or None, from the battle art) for the
        picture key at detail `cap`, made once."""
        k = key + (cap,)
        if k not in self._pictures:
            if len(self._pictures) >= KEEP_PICTURES:
                self.clear()
            pic, painted = self._picture(ship, key[0], key[1], liv, cap)
            # a copy: the cut must not hold the art's whole canvas
            pic = visible(pic)
            self._pictures[k] = (None if pic is None else pic.copy(),
                                 painted)
        return self._pictures[k]

    @staticmethod
    def _livery(settings, own):
        if settings is None:
            return None
        from core import livery
        return livery.from_settings(settings, own)

    def _picture(self, ship, colour, shape, liv, cap):
        p = int(ship.picture_num)
        own = slot_picture(p, colour, shape)
        if own is not None:
            return own, False
        if int(ship.ship_type) != ship_struct.SHIP_TYPE_COMBAT or \
                not 0 <= p < 45:
            return None, False
        try:
            art = self.art(cap)
            art.set_livery(liv)
            # a stored drawing has one size: no other detail to ask for
            painted = art.ship_indices(shape, p, 0, 0) is None
            return battle_picture(art, shape, colour, p), painted
        except (pygame.error, OSError, ValueError) as err:
            log.warning("galaxy map: no picture for ship picture %d (%s)",
                        p, err)
            return None, False


def detail_for(pic, box_w, box_h, settings):
    """The detail a painted picture is held at for a box: the smallest
    whole factor at which `pic` (its pixels at 1 x) reaches the box, never
    above the player's `painted_detail` (`core.paintdetail.cap`)."""
    import math
    from core import paintdetail
    w, h = pic.get_size()
    framing = min(box_w / max(1, w), box_h / max(1, h))
    choice = settings.get("painted_detail") if settings is not None else None
    return max(1, min(paintdetail.cap(choice, framing),
                      math.ceil(framing - 1e-9)))


def slot_picture(picture, colour, shape=None):
    """The map slot's picture for `picture` in owner colour `colour`, or
    None: the builder colour `shape`'s own file as painted (the owner's for
    an uncaptured ship), else the colour-free one in the owner's colour."""
    from core import resources
    res = resources.res
    shape = colour if shape is None else shape
    path = res.resolve(f"{SLOT}/{int(shape)}_{int(picture)}.png")
    recolour = False
    if not path:
        path = res.resolve(f"{SLOT}/all_{int(picture)}.png")
        recolour = True
    if not path:
        return None
    try:
        surf = pygame.image.load(path)
    except (pygame.error, OSError) as err:
        log.warning("galaxy map: %s cannot be read (%s)", path, err)
        return None
    if surf.get_bitsize() != 32 or not surf.get_flags() & pygame.SRCALPHA:
        rgba = pygame.Surface(surf.get_size(), pygame.SRCALPHA, 32)
        rgba.blit(surf, (0, 0))
        surf = rgba
    if recolour:
        from screens.combat import cbpaint
        surf = cbpaint.recoloured(surf, owner_rgb(colour))
    return surf


def battle_picture(art, shape, colour, picture):
    """A combat ship's battle picture, facing right, engines off (frame 0):
    the builder colour `shape`'s drawing in the owner colour `colour`."""
    if picture == AVENGER:
        # one drawing for every owner (MONSTER.LBX 25, `cbart._unit_entry`)
        return art.ship(shape, picture, 0, 0)
    stored = art.ship_indices(shape, picture, 0, 0)
    if stored is not None:
        pixels, pal = stored
        pal = dict(pal)
        pal.update(ramp(art, colour))
        return art.from_indices(pixels, pal)
    if shape == colour:
        return art.ship(colour, picture, 0, 0)
    from screens.combat import cbpaint
    if cbpaint.has_own(art, shape, picture, 0, 0):
        # a captured ship whose builder has a painted file of his own: that
        # file as painted, the shape before the colour
        return art.ship(shape, picture, 0, 0)
    # the colour-free picture in the owner's colour, even where the owner
    # has a file of his own: that file is the owner's shape
    free = cbpaint.ship(art, colour, picture, 0, 0, own_first=False)
    return free if free is not None else art.ship(shape, picture, 0, 0)


def ramp(art, colour):
    """The owner colour's stored ship ramp; under a colour preset its
    coloured half moved to the preset's colour, each entry's lightness kept
    (the battle's own blend, `cbpaint.color_blend`), the grey half as it
    is."""
    base = art.ramp(colour)
    from core import playercolors
    if palette.active_preset() == playercolors.ORIGINAL or not base:
        return base
    from screens.combat import cbpaint
    keys = [k for k, rgb in base.items()
            if max(rgb[:3]) - min(rgb[:3]) > _RAMP_CHROMA]
    if not keys:
        return base
    rgb = np.array([base[k][:3] for k in keys], float) / 255
    out = np.clip(cbpaint.color_blend(rgb, owner_rgb(colour)) * 255 + 0.5,
                  0, 255).astype(int)
    moved = dict(base)
    for k, c in zip(keys, out):
        moved[k] = tuple(int(v) for v in c)
    return moved


def visible(surf):
    """`surf` cut to its visible pixels (alpha above 0)."""
    if surf is None:
        return None
    r = surf.get_bounding_rect(min_alpha=1)
    if r.w <= 0 or r.h <= 0:
        return None
    return surf.subsurface(r)


def fitted(surf, box_w, box_h):
    """`surf`'s visible pixels inside box_w x box_h, aspect kept, never
    over the box (the slots sit 11 - zoom native px apart)."""
    surf = visible(surf)
    if surf is None:
        return None
    w, h = surf.get_size()
    f = min(box_w / w, box_h / h)
    size = (max(1, int(round(w * f))), max(1, int(round(h * f))))
    if size == (w, h):
        return surf.copy()
    if surf.get_bitsize() != 32:
        rgba = pygame.Surface((w, h), pygame.SRCALPHA, 32)
        rgba.blit(surf, (0, 0))
        surf = rgba
    return pygame.transform.smoothscale(surf, size)
