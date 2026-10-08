"""A ship's picture as the colony screens draw it — work order 223.

`COLONY::Remap_Draw_Ship_Centered_` (colony.cpp:459-482): the picture of
the ship's builder (`Get_Ship_Picture_Seg_(previous_owner, picture)`) is
copied and recoloured into the colony screen's grey ramp — indices 1-31 to
0x51-0x6F, the ship ramps 0xC0-0xCF and 0xD0-0xDF each to every second of
those — and drawn in the colony screen's palette (FONTS.LBX 2 with the
world's ground palette, `screens/colony/colart`). So a refit list shows
every ship in the same silver whoever owns it — measured on the native
picture of g223_refit_many, where the player's red Invincibles are grey.

Without the colony pictures (the palette) the Fleets picture in its
owner's colours stands in.
"""
import numpy as np
import pygame

from screens.colony import colart
from screens.fleets import fltart

_cache = {}


def remap_table():
    """`Replace_Color_Range_(bitm, 0x51.., 1, 31)` then the two ramps."""
    table = np.arange(256, dtype=np.uint8)
    for k in range(1, 32):
        table[k] = 0x51 + (k - 1)
    for i in range(16):
        table[0xC0 + i] = table[0xD0 + i] = 0x51 + 2 * i
    return table


def picture(picture_num, built, climate, bg):
    key = (picture_num, built, climate, bg)
    if key in _cache:
        return _cache[key]
    art, col = fltart.load(), colart.load()
    out = None
    got = art.ship_indices(int(picture_num), int(built)) \
        if art.available and col.available else None
    if got is not None:
        w, h, px = got
        idx = remap_table()[np.frombuffer(px, np.uint8).reshape(h, w)]
        lut = np.zeros((256, 3), np.uint8)
        for i, rgb in col.palette(climate, bg).items():
            if 0 <= i < 256:
                lut[i] = rgb[:3]
        out = pygame.Surface((w, h), pygame.SRCALPHA)
        view = pygame.surfarray.pixels3d(out)
        view[...] = lut[idx].transpose(1, 0, 2)
        del view
        alpha = pygame.surfarray.pixels_alpha(out)
        alpha[...] = np.where(np.frombuffer(px, np.uint8).reshape(h, w) != 0,
                              255, 0).T
        del alpha
    _cache[key] = out
    return out
