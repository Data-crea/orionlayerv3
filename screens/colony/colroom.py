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

_cache = {}


def available():
    return colart.load().available and \
        colart.load()._indices("build_art") is not None


def lut(climate, bg):
    """The popup's palette: the colony's with the popup art's over it."""
    art = colart.load()
    pal = dict(art.palette(climate, bg))
    got = art._indices("build_art")
    if got is not None:
        from core import lbx
        blob, head, _px = got
        pal.update(lbx.read_palette(blob, head.frame_count))
    out = np.zeros((256, 3), np.uint8)
    for i, rgb in pal.items():
        if 0 <= i < 256:
            out[i] = rgb[:3]
    return out


def _put(canvas, idx, x0, y0, mask_from=256):
    """Indices `idx` at native (x0, y0) into the window's index canvas;
    0 is transparent, and so is every index >= mask_from."""
    h, w = idx.shape
    ox, oy = x0 - WINDOW[0], y0 - WINDOW[1]
    sx0, sy0 = max(0, -ox), max(0, -oy)
    sx1, sy1 = min(w, SIZE[0] - ox), min(h, SIZE[1] - oy)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    src = idx[sy0:sy1, sx0:sx1]
    dst = canvas[oy + sy0:oy + sy1, ox + sx0:ox + sx1]
    keep = (src != 0) & (src < mask_from)
    dst[keep] = src[keep]


def _building(canvas, art, building):
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
    _put(canvas, cut, BUILDING_FOOT[0] - int(w / 2) - int(xs.min()),
         BUILDING_FOOT[1] - h - int(ys.min()))
    return True


def _centred(canvas, art, stem, at=CENTRE):
    got = art._indices(stem)
    if got is None:
        return False
    px = got[2]
    _put(canvas, px, at[0] - px.shape[1] // 2, at[1] - px.shape[0] // 2)
    return True


def tile(spec, climate, bg):
    """The window with the room and `spec`'s picture, native size, as an
    RGB surface — or None without the extraction. `spec`: ("building",
    id) — a satellite's own picture where it is one —, ("ground", id) —
    the ground drawing whatever the building —, ("trade_goods",), ("android",),
    ("spy", race), ("ship", picture_num), ("room",)."""
    key = (tuple(spec), int(climate), int(bg))
    if key in _cache:
        return _cache[key]
    out = None
    art = colart.load()
    room = art._indices("build_art") if art.available else None
    if room is not None:
        x0, y0, x1, y1 = WINDOW
        canvas = room[2][y0:y1 + 1, x0:x1 + 1].copy()
        kind = spec[0]
        if kind == "ground":
            _building(canvas, art, spec[1])
        elif kind == "building":
            if int(spec[1]) in SATELLITES:
                _centred(canvas, art, f"satellite_{SATELLITES[int(spec[1])]}")
            else:
                _building(canvas, art, spec[1])
        elif kind == "trade_goods":
            got = art._indices("trade_goods")
            if got is not None:
                _put(canvas, got[2], *TRADE_GOODS_AT)
        elif kind == "android":
            _centred(canvas, art, "android")
        elif kind == "spy":
            _centred(canvas, art, f"spy_{int(spec[1])}")
        rgb = lut(climate, bg)[canvas]
        out = pygame.surfarray.make_surface(rgb.transpose(1, 0, 2))
        if kind == "ship":
            from screens.refit import refart
            pic = refart.picture(int(spec[1]), int(spec[2]) if len(spec) > 2
                                 else 0, climate, bg)
            if pic is not None:
                out.blit(pic, (CENTRE[0] - WINDOW[0] - pic.get_width() // 2,
                               CENTRE[1] - WINDOW[1] - pic.get_height() // 2))
    _cache[key] = out
    return out


def step(tile_size, box):
    """The whole-number step (decision 28) the tile stands at in `box`: the
    largest that fits, at least 1."""
    return max(1, min(box[0] // tile_size[0], box[1] // tile_size[1]))


def draw(surface, rect, spec, climate, bg):
    """The tile stepped up by a whole number and centred in `rect`; True if
    drawn. The box keeps its room even when the product has no picture."""
    t = tile(spec, climate, bg)
    if t is None:
        return False
    rect = pygame.Rect(rect)
    k = step(t.get_size(), rect.size)
    big = pygame.transform.scale(t, (t.get_width() * k, t.get_height() * k))
    clip = surface.get_clip()
    surface.set_clip(rect)
    surface.blit(big, big.get_rect(center=rect.center))
    surface.set_clip(clip)
    return True
