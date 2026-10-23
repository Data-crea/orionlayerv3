"""The picture of a ship for a list or a preview — work order 239 Part C.

HD EXTENSION `painted_lists` (Data, 238 P3): where a list shows a ship's
picture — the Leaders ship view, the Fleets grid, the Ship Designer — HD
draws the painted ship from the player's mod folder (`cmbtshp/all_<n>_0.png`,
work orders 215-222) when "Load mods" is on and a painted picture for that
ship exists; otherwise the original's SHIPS.LBX sprite, as before, ship by
ship. The original has one sprite per ship there (SHIPS.LBX, a 3/4 icon);
the painted pictures are the battle's, seen from above.

ONE WAY FOR EVERY PLACE: the battle's own `CombatArt` and its colour-free
recolour (`screens/combat/cbpaint`) make the picture — the owner's colour,
the player's livery and second colour on his own ships (`core/livery`,
decision 8), held at the detail the player chose (`core/paintdetail`) —
at facing 0 (nose right, as the sprites face) and glow frame 1 (at rest,
the livery window's choice), held at the smallest whole factor at which
the ship itself reaches its box, within the player's detail setting, and
never enlarged. It is cropped to its pixels and scaled smoothly,
proportions kept, into the box the caller gives: the original sprite's
own drawn pixels as the place draws them (`footprint`), so every
hull keeps the size the original gives it there, and cells, names and
click areas do not move.

Made once per (ship, colour, box size, livery, detail) and kept
(`_FITTED`); a frame only looks it up. With the mod folder off
`livery.offered()` is empty and nothing is looked up at all.
"""
import math

import pygame

#: `SHIP_SIZE_DOOM_STAR` (orion2_consts.h:515): the battle draws every Doom
#: Star as picture 43, whatever its design's picture (combinit.cpp:132-137,
#: :359-363), so its list picture is that one too.
SHIP_SIZE_DOOM_STAR = 5
DOOM_STAR = 43
#: The glow frame of a ship at rest (frame 0 has its engines off since work
#: order 222; the livery window shows frame 1).
AT_REST = 1
#: The colony, outpost and transport ship pictures: no battle picture
#: (CMBTSHP holds 45 per colour, 0-44; `initship.cpp`'s templates).
NON_COMBAT = (45, 46, 47)
#: Player colours 0..7; anything else is the monster set (`fltrows`).
COLOURS = 8
#: How many fitted pictures are kept (a full Fleets grid at one size is 25).
KEEP = 256

_ARTS = {}
_FITTED = {}


def number(picture, size=None):
    """The painted picture's number for a ship of `picture` and hull
    `size`: the battle's (a Doom Star is 43)."""
    if size is not None and int(size) == SHIP_SIZE_DOOM_STAR:
        return DOOM_STAR
    return int(picture)


def painted(picture, size=None):
    """True when the mod folder is on and holds a painted picture for this
    ship (`core.livery.offered`, {} with the folder off)."""
    from core import livery
    return number(picture, size) in livery.offered()


def footprint(sprite, at, step):
    """The window rect of `sprite`'s drawn pixels, blitted at `at` after
    magnifying by `step`: the box the painted ship is fitted into."""
    r = sprite.get_bounding_rect(min_alpha=1)
    return pygame.Rect(at[0] + r.x * step, at[1] + r.y * step,
                       max(1, r.w * step), max(1, r.h * step))


_OWN = [None, None]


def own_colour(game_state):
    """The local player's colour index (`_player[player_num].color`), or
    None. Read once per snapshot: a list asks for every cell each frame."""
    if _OWN[0] is game_state:
        return _OWN[1]
    colour = None
    try:
        from core.structs import player as player_struct
        raws = getattr(game_state, "player_raw", None) or []
        me = int(getattr(game_state, "player_num", 0) or 0)
        if 0 <= me < len(raws) and raws[me] is not None:
            colour = int(player_struct.parse(raws[me]).color)
    except (AttributeError, IndexError, TypeError, ValueError):
        colour = None
    _OWN[0], _OWN[1] = game_state, colour
    return colour


def fitted(app, colour, picture, box, state=None, own=None, size=None):
    """(surface, topleft) of the painted ship `picture` (hull `size`) in
    owner colour `colour`, fitted into window rect `box` and centred in it;
    None when there is none — the mod folder off, no painted picture for
    this ship, a colour that is no player's — and the caller draws the
    original's sprite. `own` is the local player's colour (his livery's
    second colour goes on his ships only), else read from `state`."""
    if colour is None or not 0 <= int(colour) < COLOURS or box is None:
        return None
    if int(picture) in NON_COMBAT and not (
            size is not None and int(size) == SHIP_SIZE_DOOM_STAR):
        return _slot(colour, int(picture), box)
    if not painted(picture, size):
        return None
    from core import livery, palette, usermod
    if own is None and state is not None:
        own = own_colour(state)
    box = pygame.Rect(box)
    us = getattr(app, "user_settings", None)
    liv = livery.from_settings(us, own)
    choice = us.get("painted_detail") if us is not None else None
    n = number(picture, size)
    # the colour table's number: a preset applied while the program runs
    # makes the picture again (HD EXTENSION `preset_at_once`)
    key = (int(colour), n, box.w, box.h, liv.key(), choice,
           id(usermod._state["index"]), palette.generation())
    if key not in _FITTED:
        if len(_FITTED) >= KEEP:
            _FITTED.clear()
        _FITTED[key] = _make(int(colour), n, box.size, liv, choice)
    pic = _FITTED[key]
    if pic is None:
        return None
    return pic, (box.x + (box.w - pic.get_width()) // 2,
                 box.y + (box.h - pic.get_height()) // 2)


def _slot(colour, picture, box):
    """(surface, topleft) of the galaxy map's ship-picture slot for a
    colony, outpost or transport ship (`NON_COMBAT`), fitted into `box`,
    or None. The battle has no picture 45-47 (`cmbtshp` holds 45 a colour,
    so entry `colour * 45 + 47` is another colour's ship): the route above
    would alias a wrong ship. The slot is the one place the player's mod
    folder paints these — ONE ROUTE FOR EVERY PLACE, so the transport the
    player painted reaches the Fleets grid, the Leaders ship view and the
    Ship Designer as it reaches the map (HD EXTENSION `slot_ship_pictures`,
    work order 326 C2; the original draws picture 47 on every one of those
    screens, `KEN::Do_Get_Ship_Picture_Seg` ken.cpp:455-465). Never
    enlarged, as the battle's pictures are not. DEVIATION of the map's slot
    rule: a captured ship takes the HOLDER's colour here (`fitted` is given
    the cell's ramp, not the builder's), the map takes the builder's own
    `<colour>_<n>.png` first."""
    from core import palette
    from screens.galaxy_map import shippics
    box = pygame.Rect(box)
    key = ("slot", int(colour), picture, box.w, box.h,
           usermod_generation(), palette.generation())
    if key not in _FITTED:
        if len(_FITTED) >= KEEP:
            _FITTED.clear()
        surf = shippics.slot_picture(picture, int(colour))
        vis = shippics.visible(surf)
        if vis is not None and (vis.get_width() > box.w
                                or vis.get_height() > box.h):
            vis = shippics.fitted(vis, box.w, box.h)
        _FITTED[key] = vis.copy() if vis is not None else None
    pic = _FITTED[key]
    if pic is None:
        return None
    return pic, (box.x + (box.w - pic.get_width()) // 2,
                 box.y + (box.h - pic.get_height()) // 2)


def usermod_generation():
    """How many times the mod folder was read (`usermod.init`): the cache
    key above must not outlive a rescan."""
    from core import usermod
    return usermod._state.get("generation", 0)


def _art(cap):
    """The battle's art, one per detail cap (a cap change in `CombatArt`
    drops every picture made, so each cap keeps its own)."""
    if cap not in _ARTS:
        from screens.combat import cbart
        art = cbart.CombatArt()
        art.set_detail(cap)
        _ARTS[cap] = art
    return _ARTS[cap]


def _make(colour, n, size, liv, choice):
    from core import lbx, paintdetail
    from screens.combat import cbart, cbpaint, cbpulse
    # the detail: the smallest whole factor at which the SHIP — the
    # picture's drawn pixels, which is what is fitted — is not enlarged in
    # this box, never above what the player's setting allows
    # (`paintdetail.cap`: Normal 4 x, High 8 x, Auto as the battle picks).
    # Measured against the whole 59 x 60 canvas (work order 239's first
    # cut) a frigate, which fills a third of it, was held at 2 x and then
    # enlarged 2.1 x into its box: blurred (Data's screenshot, the
    # Corvette beside a sharp Fighter).
    probe = _art(paintdetail.FACTORS["high"])
    blob = probe.blob("cmbtshp", n)
    try:
        h = lbx.parse_header(blob) if blob else None
    except lbx.LbxError:
        h = None
    dw, dh = (h.width, h.height) if h is not None else (59, 60)
    cw, ch = float(dw), float(dh)
    raw = probe.painted_file("cmbtshp", f"all_{n}_0.png", n)
    if raw is not None:
        per = raw.get_width() / dw          # the file's px per drawing px
        bb = raw.get_bounding_rect(min_alpha=8)
        cw, ch = max(1.0, bb.w / per), max(1.0, bb.h / per)
    framing = min(size[0] / cw, size[1] / ch)
    art = _art(min(paintdetail.cap(choice, framing),
                   max(1, math.ceil(framing - 1e-9))))
    art.set_livery(liv)
    pic = cbpaint.ship(art, colour, n, 0, AT_REST)
    if pic is None:
        pic = cbpulse.own(art, "cmbtshp", colour * 45 + n, 0, AT_REST,
                          False, False)
    if pic is None:
        return None
    pic = pic.subsurface(pic.get_bounding_rect(min_alpha=8))
    # never enlarged: where the box wants more px than the painting holds
    # (a frigate at 3840x2160 under High), it stands at its own size,
    # centred, a little smaller than the sprite it replaces, and sharp
    k = min(1.0, size[0] / max(1, pic.get_width()),
            size[1] / max(1, pic.get_height()))
    # rounded, not truncated: k is the box over the picture, and the side
    # that fits must come out at the box's own length (120 / w * w can be
    # 119.99...), never a px short of it nor past it
    out = (min(size[0], max(1, round(pic.get_width() * k))),
           min(size[1], max(1, round(pic.get_height() * k))))
    return cbart.smooth(pic.copy(), out)
