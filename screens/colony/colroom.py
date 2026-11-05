"""The grid room a product stands in — work order 226 Parts D and G.

ONE implementation for the build screen's picture box and the colony
screen's build box (Data's decisions 3 and 6 of 9 October 2026).

**THE ROOM IS GAME DATA, NOT A DRAWING OF OURS.** It is the picture box of
the build popup's own art, COLBLDG.LBX 0, drawn at (0, 0)
(`Draw_Build_Queue_Popup_`, colbldg.cpp:1011); the products are drawn into
its window (203, 9)-(285, 103) (`Draw_Building_Centered_In_Window_`,
:1108-1113). So it is cut out of the player's own file
(`tools/colony_art_extract.py`, format 2), never rebuilt in code, and is
absent where the extraction is (decision 38: the state is said, no
stand-in).

TRANSCRIPTION, each product's picture, in the palette the popup draws in
(the colony's — FONTS.LBX 2 with the world's ground — and the popup art's
own laid over it, `animate::Draw_Palette_`, :1006):

  a building     its drawing at the ground's cell (5, 5) cut 120 x 120
                 round (318, 303) (`_building_cr_xy`, colony.cpp:108),
                 colours 240-255 masked out, standing with its bottom
                 centred at (244, 93) (colony_main.cpp:421-442)
  a satellite    COLONY.LBX 9 + `Satellite_Anim_Pic_` centred at (244, 56)
                 (`Draw_Icon_`, colbldg.cpp:1853)
  Trade Goods    COLONY2.LBX 7 at (235, 54) (colbldg.cpp:956-963)
  Housing        building 14's drawing (colbldg.cpp:947-955)
  farmer, worker, scientist   the android, RACEICON 0xA9 (`People_Anim_(0,
                 4, race)`: pop state 4 is the android's, colony_main.cpp:
                 444-462), centred at (244, 56)
  spy            the player's race's spy, RACEICON race * 13 + 11
  a ship         its picture recoloured into the screen's grey ramp
                 (`screens/refit/refart`, `Remap_Draw_Ship_*_Centered_`),
                 centred at (244, 56)

The tile is the window at native size; a caller steps it up by a whole
number (decision 28) and never stretches it.
"""
import numpy as np
import pygame

from screens.colony import colart

#: The window the products are clipped to, inclusive (colbldg.cpp:1109).
WINDOW = (203, 9, 285, 103)
SIZE = (WINDOW[2] - WINDOW[0] + 1, WINDOW[3] - WINDOW[1] + 1)
#: Where things stand in it, native (colbldg.cpp: `Draw_Icon_` :1853-1855,
#: `Draw_Building_Centered_In_Window_` :1111, TRADE_GOODS :960).
CENTRE, BUILDING_FOOT, TRADE_GOODS_AT = (244, 56), (244, 93), (235, 54)
#: `_building_cr_xy[5][5]` (colony.cpp:108): the ground point of cell (5, 5).
CELL_XY = (318, 303)
#: `Satellite_Anim_Pic_` (colony.cpp:213-228), by building id.
SATELLITES = {3: 7, 8: 1, 14: 3, 40: 2, 41: 0}
HOUSING_BUILDING = 14

#: THE TWO PLACES the room stands in — one implementation (work order 226
#: G). The colony screen's build box has its own, larger room in its band
#: (COLPUPS.LBX 5; its inside measured off the art, the metal rim left out)
#: and its own points (`Draw_Info_Build_`, colony_main.cpp:899-945;
#: `Draw_Current_Building2_`, :877-896): a building's foot at (579, 106), a
#: satellite at (578, 78), people, a spy, freighters and a ship at
#: (578, 77), a colony ship or transport at (578, 57); Trade Goods and
#: Refit draw nothing there. Its palette is the colony's alone.
#: THE RAISED PLACE BELONGS TO TWO PRODUCTS, NOT TO TWO PICTURES (work
#: order 227 B): only the special products COLONY SHIP (-12) and TRANSPORT
#: (-11) are drawn at (578, 57) (colony_main.cpp:908-913); a ship from the
#: queue is `Draw_Current_Ship_`'s (578, 77) whatever its picture
#: (colony.cpp:778-783) — a queued colony ship has picture 45 too, and
#: keyed by the picture it stood 20 native px high, under the product's
#: name (226 G's finding; measured: the original's frame matches the
#: picture at (578, 77), correlation 0.78, and not at (578, 57)). So
#: `high_ships` is keyed by the product a ship spec carries (`spec[3]`).
PLACES = {
    "popup": {"art": "build_art", "window": WINDOW, "centre": CENTRE,
              "foot": BUILDING_FOOT, "satellite": CENTRE,
              "trade_goods": TRADE_GOODS_AT, "high_ships": {},
              "overlay": True},
    "colony": {"art": "band", "window": (525, 26, 630, 113),
               "centre": (578, 77), "foot": (579, 106),
               "satellite": (578, 78), "trade_goods": None,
               "high_ships": {-12: (578, 57), -11: (578, 57)},
               "overlay": False},
}

_cache = {}
_targets = {}


def available(place="popup"):
    return colart.load().available and \
        colart.load()._indices(PLACES[place]["art"]) is not None


def lut(climate, bg, place="popup"):
    """The place's palette: the colony's, with the popup art's over it in
    the build popup."""
    art = colart.load()
    pal = dict(art.palette(climate, bg))
    got = art._indices("build_art") if PLACES[place]["overlay"] else None
    if got is not None:
        from core import lbx
        blob, head, _px = got
        pal.update(lbx.read_palette(blob, head.frame_count))
    out = np.zeros((256, 3), np.uint8)
    for i, rgb in pal.items():
        if 0 <= i < 256:
            out[i] = rgb[:3]
    return out


def _put(canvas, idx, x0, y0, window, mask_from=256):
    """Indices `idx` at native (x0, y0) into the window's index canvas;
    0 is transparent, and so is every index >= mask_from."""
    h, w = idx.shape
    ox, oy = x0 - window[0], y0 - window[1]
    ch, cw = canvas.shape
    sx0, sy0 = max(0, -ox), max(0, -oy)
    sx1, sy1 = min(w, cw - ox), min(h, ch - oy)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    src = idx[sy0:sy1, sx0:sx1]
    dst = canvas[oy + sy0:oy + sy1, ox + sx0:ox + sx1]
    keep = (src != 0) & (src < mask_from)
    dst[keep] = src[keep]


def _building(canvas, art, building, foot, window):
    got = art._indices(f"bldg_{int(building)}")
    if got is None:
        return False
    px = got[2]
    x, y = CELL_XY
    cut = px[max(0, y - 120):y, max(0, x - 60):x + 60].copy()
    cut[cut >= 240] = 0                     # Mask_Out_Colors_(bitm, 240, 255)
    ys, xs = np.nonzero(cut)
    if not len(xs):
        return False
    w = int(xs.max() - xs.min() + 1)
    h = int(ys.max() - ys.min() + 1)
    # The content's left is x - w / 2 (C: truncated), its bottom at y.
    _put(canvas, cut, foot[0] - int(w / 2) - int(xs.min()),
         foot[1] - h - int(ys.min()), window)
    return True


def _centred(canvas, art, stem, at, window):
    got = art._indices(stem)
    if got is None:
        return False
    px = got[2]
    _put(canvas, px, at[0] - px.shape[1] // 2, at[1] - px.shape[0] // 2,
         window)
    return True


def ship_centre(spec, place):
    """Where a ("ship", picture, owner[, product[, hull size]]) spec's
    picture is centred in `place`, native px: a special product's raised
    point, else the place's centre — the one answer for the drawing and the
    check."""
    pl = PLACES[place]
    product = int(spec[3]) if len(spec) > 3 and spec[3] is not None else None
    return pl["high_ships"].get(product, pl["centre"])


def hd_target(spec, place="popup"):
    """HD EXTENSION `building_pictures`: (building id, (x, y, w, h)) when
    `spec` is a building the player painted (`core.buildingart`) — the ink
    of the original's drawing in the window's native coordinates, which the
    painted one is fitted into — else None. Housing's ground drawing
    ("ground") is the original's own, whatever building 14's picture is."""
    from core import buildingart
    if spec[0] != "building" or buildingart.picture(spec[1]) is None:
        return None
    key = (int(spec[1]), place, buildingart.present())
    if key not in _targets:
        _targets[key] = _hd_target(int(spec[1]), place)
    return _targets[key]


def _hd_target(bid, place):
    art = colart.load()
    pl = PLACES[place]
    if bid in SATELLITES:
        # HD EXTENSION: the original's satellite drawing is a few pixels
        # across (77 x 44 at most); a painted one fills 80 % of the window's
        # width instead, centred where the original's stands
        win = pl["window"]
        w = (win[2] - win[0] + 1) * 8 // 10
        h = (win[3] - win[1] + 1) // 2
        cx, cy = pl["satellite"]
        return bid, (cx - w // 2, cy - h // 2, w, h)
    got = art._indices(f"bldg_{bid}")
    if got is None:
        return None
    x, y = CELL_XY
    cut = got[2][max(0, y - 120):y, max(0, x - 60):x + 60].copy()
    cut[cut >= 240] = 0
    ys, xs = np.nonzero(cut)
    if not len(xs):
        return None
    w = int(xs.max() - xs.min() + 1)
    h = int(ys.max() - ys.min() + 1)
    return bid, (pl["foot"][0] - w // 2, pl["foot"][1] - h, w, h)


def hull_size(spec):
    """The ship spec's hull size (the Doom Star rule of `shippicture`), or
    None where the spec carries none."""
    return int(spec[4]) if len(spec) > 4 and spec[4] is not None else None


def painted(spec, colour, place="popup"):
    """True when `spec` is a ship the player's mod folder paints — a colony,
    outpost or transport ship (45-47) in the galaxy map's slot, any other
    in the battle's painted picture (`core.shippicture`, the one route of
    every place): the tile is then taken without the sprite and `overlay`
    draws the painted picture. HD EXTENSION `slot_ship_pictures` (work
    order 326 P7) and `painted_lists` (the build box, Data, 4 November
    2026: it was parked since work order 239)."""
    from core import shippicture
    if colour is None or spec[0] != "ship":
        return False
    size = hull_size(spec)
    if int(spec[1]) in shippicture.NON_COMBAT:
        win = PLACES[place]["window"]
        return shippicture.fitted(None, colour, int(spec[1]), (
            0, 0, win[2] - win[0], win[3] - win[1]), size=size) is not None
    # a battle picture is asked for by whether the folder holds one: making
    # it here, at the window's size, would build a picture the footprint's
    # size then builds again
    return 0 <= int(colour) < shippicture.COLOURS and \
        shippicture.painted(int(spec[1]), size)


def overlay(surface, spec, colour, climate, bg, place, origin, k, app=None):
    """Draw the painted picture of ship `spec` for owner `colour` over a
    tile stood at `origin` (window px) magnified `k` times; True if drawn.
    It is fitted into the drawn pixels of the sprite the original draws
    there (`shippicture.footprint`) and never enlarged, so it is sharp and
    stands where the sprite stood. The original draws the colony screen's
    grey remap of SHIPS.LBX here (`Remap_Draw_Ship_Seg_N_Centered`,
    colony_main.cpp:878/:881, colbldg.cpp:916/:950/:959; a queued ship
    `Remap_Draw_Ship_Centered`, colony.cpp:435-450, :750). `app` brings the
    player's livery and detail setting (`shippicture.fitted`); DEVIATION
    `painted_build_colour`: the painted ship is in its builder's own colour,
    where the original draws every ship grey here."""
    from core import buildingart
    target = hd_target(spec, place)
    if target is not None:
        win = PLACES[place]["window"]
        bid, (x, y, w, h) = target
        pic = buildingart.fit(bid, w * k, h * k)
        if pic is not None:
            surface.blit(pic, (origin[0] + (x - win[0]) * k
                               + (w * k - pic.get_width()) // 2,
                               origin[1] + (y + h - win[1]) * k
                               - pic.get_height()))
            return True
    from core import shippicture
    from screens.refit import refart
    if not painted(spec, colour, place):
        return False
    sprite = refart.picture(int(spec[1]), int(spec[2]) if len(spec) > 2
                            else 0, climate, bg)
    if sprite is None:
        return False
    at = ship_centre(spec, place)
    win = PLACES[place]["window"]
    pos = (origin[0] + (at[0] - win[0] - sprite.get_width() // 2) * k,
           origin[1] + (at[1] - win[1] - sprite.get_height() // 2) * k)
    # these ships are the player's own (the build list, the queue): his
    # livery's second colour goes on them
    got = shippicture.fitted(app, colour, int(spec[1]),
                             shippicture.footprint(sprite, pos, k),
                             own=colour, size=hull_size(spec))
    if got is None:
        return False
    surface.blit(got[0], got[1])
    return True


def owner_colour(state, owner):
    """Player `owner`'s colour index (`_player[owner].color`), or None."""
    from core.structs import player as player_struct
    raws = getattr(state, "player_raw", None) or []
    try:
        return int(player_struct.parse(raws[int(owner)]).color) \
            if 0 <= int(owner) < len(raws) and raws[int(owner)] else None
    except (IndexError, TypeError, ValueError, AttributeError):
        return None


def tile(spec, climate, bg, place="popup", colour=None):
    """The place's window with the room and `spec`'s picture, native size,
    as an RGB surface — or None without the extraction. `spec`:
    ("building", id) — a satellite's own picture where it is one —,
    ("ground", id) — the ground drawing whatever the building —,
    ("trade_goods",), ("android",), ("spy", race), ("ship", picture_num,
    owner[, special product]), ("room",)."""
    bare = painted(spec, colour, place)
    from core import shippicture
    hd = hd_target(spec, place) is not None
    key = (tuple(spec), int(climate), int(bg), place, bare, hd,
           shippicture.usermod_generation() if bare else 0)
    if key in _cache:
        return _cache[key]
    out = None
    pl = PLACES[place]
    win = pl["window"]
    art = colart.load()
    room = art._indices(pl["art"]) if art.available else None
    if room is not None:
        x0, y0, x1, y1 = win
        canvas = room[2][y0:y1 + 1, x0:x1 + 1].copy()
        kind = spec[0]
        if kind == "ground":
            _building(canvas, art, spec[1], pl["foot"], win)
        elif kind == "building" and hd:
            pass                    # `overlay` stands the painted one here
        elif kind == "building":
            if int(spec[1]) in SATELLITES:
                _centred(canvas, art, f"satellite_{SATELLITES[int(spec[1])]}",
                         pl["satellite"], win)
            else:
                _building(canvas, art, spec[1], pl["foot"], win)
        elif kind == "trade_goods" and pl["trade_goods"] is not None:
            got = art._indices("trade_goods")
            if got is not None:
                _put(canvas, got[2], *pl["trade_goods"], win)
        elif kind == "android":
            _centred(canvas, art, "android", pl["centre"], win)
        elif kind == "spy":
            _centred(canvas, art, f"spy_{int(spec[1])}", pl["centre"], win)
        rgb = lut(climate, bg, place)[canvas]
        out = pygame.surfarray.make_surface(rgb.transpose(1, 0, 2))
        if kind == "ship" and not bare:
            from screens.refit import refart
            pic = refart.picture(int(spec[1]), int(spec[2]) if len(spec) > 2
                                 else 0, climate, bg)
            at = ship_centre(spec, place)
            if pic is not None:
                out.blit(pic, (at[0] - win[0] - pic.get_width() // 2,
                               at[1] - win[1] - pic.get_height() // 2))
    _cache[key] = out
    return out


def step(tile_size, box):
    """The whole-number step (decision 28) the tile stands at in `box`: the
    largest that fits, at least 1."""
    return max(1, min(box[0] // tile_size[0], box[1] // tile_size[1]))


def draw(surface, rect, spec, climate, bg, place="popup", colour=None,
         app=None):
    """The tile stepped up by a whole number and centred in `rect`; True if
    drawn. The box keeps its room even when the product has no picture."""
    t = tile(spec, climate, bg, place, colour)
    if t is None:
        return False
    rect = pygame.Rect(rect)
    k = step(t.get_size(), rect.size)
    big = pygame.transform.scale(t, (t.get_width() * k, t.get_height() * k))
    clip = surface.get_clip()
    surface.set_clip(rect)
    at = big.get_rect(center=rect.center)
    surface.blit(big, at)
    overlay(surface, spec, colour, climate, bg, place, at.topleft, k, app)
    surface.set_clip(clip)
    return True


_only = {}


def product_only(spec, climate, bg, place="popup", colour=None):
    """The tile with the ROOM left out: the product's own pixels on
    transparency, or None without the extraction. The room is the tile of
    `("room",)`; a pixel that differs from it belongs to the product (the
    palette is exact, so no halo of room colour stays but where a ship's
    soft edge blended into it). HD EXTENSION `build_grid_room`: the build
    list stands its product in a picture of Data's instead of the room."""
    t = tile(spec, climate, bg, place, colour)
    room = tile(("room",), climate, bg, place, colour)
    if t is None or room is None:
        return None
    key = (id(t), id(room))
    hit = _only.get(key)
    if hit is not None:
        return hit[0]
    differs = (pygame.surfarray.array3d(t) !=
               pygame.surfarray.array3d(room)).any(axis=2)
    out = pygame.Surface(t.get_size(), pygame.SRCALPHA, 32)
    out.blit(t, (0, 0))
    alpha = pygame.surfarray.pixels_alpha(out)
    alpha[:] = np.where(differs, 255, 0)
    del alpha
    if len(_only) > 64:
        _only.clear()
    # `t` and `room` are held too: their ids stay theirs while cached
    _only[key] = (out, t, room)
    return out


#: HD EXTENSION `product_fill` (Data, 4 November 2026: the pictures in the
#: blue grid "are too small"): the share of the grid's box a product's own
#: pixels fill, in the limiting direction. The whole-number step used to
#: come from the room's window (106 x 88 or 83 x 95 native), which holds the
#: biggest product with air round it, so the typical one (43 x 36 native,
#: measured over all 96 buildings and ships) stood at 38 % of the box. Fitted
#: to the product's ink it stands at up to this share; the step stays a whole
#: number (decision 28: the original's pixels are never smoothed), and never
#: goes below what the window gave. 0.8 leaves the colony box's name line
#: (its top sixth) and the turns bar (its bottom edge) free.
PRODUCT_FILL = 0.8
#: A product's step never exceeds this many times the window's (plus one):
#: a 15 px scout is not stood as large as a colony base — the biggest and
#: the smallest keep some of the order the original shows them in.
PRODUCT_STEP_CAP = 2
_fit_k = {}


def _ink_of(t, spec, climate, bg, place, colour):
    """The bounding box of the product as it is laid at step 1 (its
    painted picture included), measured on a scratch three tiles wide —
    the overlay may reach past the tile."""
    tw, th = t.get_size()
    scratch = pygame.Surface((tw * 3, th * 3), pygame.SRCALPHA, 32)
    scratch.blit(t, (tw, th))
    overlay(scratch, spec, colour, climate, bg, place, (tw, th), 1)
    return scratch.get_bounding_rect()


def product_step(t, spec, climate, bg, place, colour, rect_size):
    """The whole-number step the product stands at in a box of
    `rect_size`: the window's own step at least, else the largest at which
    its ink (the original's pixels and a painted picture alike) fills
    `PRODUCT_FILL` of the box — measured once per product, size and art."""
    from core import buildingart, shippicture
    base = step(t.get_size(), rect_size)
    key = (tuple(spec), int(climate), int(bg), place, colour,
           tuple(rect_size), buildingart.present(),
           shippicture.usermod_generation())
    got = _fit_k.get(key)
    if got is None:
        if len(_fit_k) > 256:
            _fit_k.clear()
        ink = _ink_of(t, spec, climate, bg, place, colour)
        if ink.w == 0 or ink.h == 0:
            got = base
        else:
            fit = int(min(PRODUCT_FILL * rect_size[0] / ink.w,
                          PRODUCT_FILL * rect_size[1] / ink.h))
            got = max(base, min(fit, PRODUCT_STEP_CAP * base + 1))
        _fit_k[key] = got
    return got


def draw_product(surface, rect, spec, climate, bg, place="popup",
                 colour=None, app=None):
    """`draw`, the room left out (`product_only`) and the product CENTRED by
    what is drawn: a building stands on the original's floor (its foot at
    y 93 of a window 9 to 103) and a ship or satellite at the middle, so
    their ink sat low or aside in Data's grid. The product and its painted
    overlay are drawn on a scratch twice the box, the ink's bounding box is
    measured, and the scratch is laid so that box's middle is the box's
    middle (HD EXTENSION `build_grid_room`). The step fits the product to
    the box (`product_step`, HD EXTENSION `product_fill`). True if drawn."""
    t = product_only(spec, climate, bg, place, colour)
    if t is None:
        return False
    rect = pygame.Rect(rect)
    k = product_step(t, spec, climate, bg, place, colour, rect.size)
    big = pygame.transform.scale(t, (t.get_width() * k, t.get_height() * k))
    side = max(rect.w, big.get_width()) * 2, max(rect.h, big.get_height()) * 2
    scratch = pygame.Surface(side, pygame.SRCALPHA, 32)
    mid = pygame.Rect(side[0] // 4, side[1] // 4, side[0] // 2, side[1] // 2)
    at = big.get_rect(center=mid.center)
    scratch.blit(big, at)
    overlay(scratch, spec, colour, climate, bg, place, at.topleft, k, app)
    ink = scratch.get_bounding_rect()
    if ink.w == 0 or ink.h == 0:
        return True
    clip = surface.get_clip()
    surface.set_clip(rect.clip(clip) if clip else rect)
    surface.blit(scratch, (rect.centerx - ink.centerx,
                           rect.centery - ink.centery))
    surface.set_clip(clip)
    return True
