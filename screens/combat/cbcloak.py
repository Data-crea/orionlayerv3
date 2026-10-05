"""Cloaked and phased units — work order 210 C1.

TRANSCRIPTION `cloak`: a unit whose `special_status_flag` is 1 or 5 (a
Cloaking Device holding, combinit.cpp:416, combat1.cpp:1113) is drawn
through `Plasma_Darken_(bitmap, (_ship_frame + unit * 2) % 16, 3)`
(`Draw_Ship_`, cmbtdrw1.cpp:2627-2630): each pixel of its picture is
remapped through `_ship_darken_map[pixel][v]` (`Create_Ship_Darken_Map_`,
:2671-2742) with `v = min(plasma + 2, 15)`, the plasma map COMBAT.LBX 0x31
(60 x 60, fifteen raw frames, the frame `progress % 16` held at 14 by
`Set_Animation_Frame_`) laid over the picture's top-left (:2935-3006). The
map takes a ship pixel down its colour ramp and to 0 — transparent — past
the ramp's start, so the unit shimmers dark and partly not at all. The same
for every viewer: the original has no owner test here.

TRANSCRIPTION `phasing`: a unit whose flag is 4 (a Phasing Cloak engaged,
combinit.cpp:420, combat1.cpp:1122) is only its outline — palette index 5
on every empty pixel beside the picture, the picture itself masked out
(`Outline_Bitmap_` and `Mask_Out_Bitmap_With_Bitmap_`, bitmap.cpp:167-189,
shear.cpp:131-213) — while the acting unit is the local player's
(cmbtdrw1.cpp:2617-2625), and NOTHING otherwise: no picture, no absorber,
no stasis ball, web or hole. The original's test reads the ACTING unit's
owner, so during the player's own turn every phased unit is outlined,
during the computer's none is drawn.

TRANSCRIPTION `cloak_fades`: `Draw_Cloak_` (cmbtspec.cpp:59-121) plays
the change — type 1 cloaking (24 steps, darkness `p / 4` up to 6), 2
uncloaking (24, `6 - p / 4`), 4 phasing (60, `p / 3` up to 20), 5
unphasing (36, `12 - p / 3`) — one step a 55 ms tick, two under FAST
ANIMATIONS, on the facing's glow-0 frame (`Draw_Ship_To_Bitmap_(i, 0,
type, progress)`, :2023-2048).
HD STATE `cloak_fade_time`: no event says when a fade plays, so HD plays it
when the state it adopts changes the flag (`Fades`); the original plays an
uncloak before the shot that breaks the cloak (cmbtfire.cpp:1262-1273).
UNVERIFIED `darken_glass`: a picture's pixels at 0x80 and above lie outside
the original's 128-row map (it reads past it); HD leaves them as they are.
A painted picture (a mod's PNG, no palette indices) is drawn at a quarter of
its alpha when cloaked and not at all when phased.

TRANSCRIPTION `teleport` (work order 210 C4): a Phase Shifter's or Sub
Space Teleporter's move (`CEV_MOVE` with teleport 1) dissolves the unit out
of its cell and into the new one in the same ten frames (five under FAST):
its glow-0 picture through `Vanish_Bitmap_` at 0, 10 .. 90 % where it was
and 100, 90 .. 10 % where it goes (`Draw_Teleporting_Ship_`,
cmbtmov1.cpp:816-886; `Vanish_Bitmap_Pixels_`, shear.cpp:540-588: a pixel
is dropped where `_noise_table` is below the percentage, four pixels to a
table word, the walk jumping by the dword count squared at each row's end
and after a pixel of 0x80 or more; 100 % draws nothing).
DEVIATION `untimed_pace` (decision 80): the original's loop has no wait
(each frame as fast as it is presented); HD gives a frame 15 ms
(`cbplay.UNTIMED_S`). HD STATE `teleport_noise`: the table's start index
comes from the game's random numbers there, from HD's own here.
"""
import numpy as np
import pygame

from core import lbx

from . import cbdraw

PLASMA_ENTRY = 0x31
OUTLINE_INDEX = 5
#: `Draw_Cloak_`'s length by type, in steps (cmbtspec.cpp:74-89).
FADE_STEPS = {1: 24, 2: 24, 4: 60, 5: 36}
TICK = 0.055
CLOAKED = (1, 5)
PHASED = 4
_CACHE_MAX = 512
#: `_noise_table[258]` (shear.cpp:24-42).
NOISE = bytes((
    42, 68, 35, 1, 70, 25, 79, 59, 63, 65, 6, 46, 82, 28, 62, 92,
    96, 43, 28, 37, 92, 5, 3, 54, 93, 83, 22, 17, 19, 96, 48, 27,
    72, 39, 70, 13, 68, 100, 36, 95, 4, 12, 23, 34, 74, 65, 42, 12,
    54, 69, 48, 45, 63, 58, 38, 60, 24, 42, 30, 79, 17, 36, 91, 43,
    89, 7, 41, 43, 65, 49, 47, 6, 91, 30, 71, 51, 7, 2, 94, 49,
    30, 24, 85, 55, 57, 41, 67, 77, 32, 9, 45, 40, 27, 24, 38, 39,
    19, 83, 30, 42, 34, 16, 40, 59, 5, 31, 78, 7, 74, 87, 22, 46,
    25, 73, 71, 30, 78, 74, 98, 13, 87, 91, 62, 37, 56, 68, 56, 75,
    32, 53, 51, 51, 42, 25, 67, 31, 8, 92, 8, 38, 58, 88, 54, 84,
    46, 10, 10, 59, 22, 89, 23, 47, 7, 31, 14, 69, 1, 92, 63, 56,
    11, 60, 25, 38, 49, 84, 96, 42, 3, 51, 92, 37, 75, 21, 97, 22,
    49, 100, 69, 85, 82, 35, 54, 100, 19, 39, 1, 89, 28, 68, 29, 94,
    49, 84, 8, 22, 11, 18, 14, 15, 10, 17, 36, 52, 1, 50, 20, 57,
    99, 4, 25, 9, 45, 10, 90, 3, 96, 86, 94, 44, 24, 88, 15, 4,
    49, 1, 59, 19, 81, 97, 99, 82, 90, 99, 10, 58, 73, 23, 39, 93,
    39, 80, 91, 58, 59, 92, 16, 89, 57, 12, 3, 35, 73, 56, 29, 47,
    28, 79,
))


def darken_map():
    """`_ship_darken_map[128][16]` as `Create_Ship_Darken_Map_` fills it
    (cmbtdrw1.cpp:2671-2742); rows 0x50-0x5F are never written (0)."""
    m = np.zeros((128, 16), dtype=np.uint8)
    for i in range(0x20):
        for j in range(16):
            v = (i - 2 * j) & 0xFF
            m[i, j] = 0 if v > 0x20 else v
    for lo, hi, floor, div in ((0x20, 0x30, 0x20, 1), (0x30, 0x40, 0x30, 1),
                               (0x40, 0x48, 0x40, 2), (0x48, 0x50, 0x48, 2),
                               (0x60, 0x70, 0x60, 1), (0x70, 0x80, 0x70, 1)):
        for i in range(lo, hi):
            for j in range(16):
                v = (i - (j // div if div > 1 else j)) & 0xFF
                m[i, j] = 0 if v < floor else v
    return m


DARKEN = darken_map()


def darkness(mode, progress):
    """`Plasma_Darken_`'s darkness by mode (cmbtdrw1.cpp:2946-2972)."""
    p = int(progress)
    if mode == 1:
        return min(p // 4, 6)
    if mode == 2:
        return max(6 - p // 4, 0)
    if mode == 3:
        return 6
    if mode == 4:
        return min(p // 3, 20)
    if mode == 5:
        return max(12 - p // 3, 0)
    return 0


def plasma(art):
    """COMBAT.LBX 0x31's frames as a (frames, h, w) array, or None."""
    key = ("plasma",)
    cache = _cache(art)
    if key not in cache:
        b = art.blob("combat", PLASMA_ENTRY)
        out = None
        try:
            h = lbx.parse_header(b)
            offs = np.frombuffer(b, dtype="<u4", count=h.frame_count + 1,
                                 offset=12)
            out = np.stack([np.frombuffer(
                b[offs[k]:offs[k] + h.width * h.height], dtype=np.uint8
            ).reshape(h.height, h.width) for k in range(h.frame_count)])
        except (lbx.LbxError, TypeError, ValueError):
            out = None
        cache[key] = out
    return cache[key]


def darken(pixels, progress, mode, frames):
    """`Plasma_Darken_(bitmap, progress, mode)` on an index array."""
    d = darkness(mode, progress)
    if d == 0 or frames is None:
        return pixels
    f = frames[min(int(progress) % 16, len(frames) - 1)]
    out = pixels.copy()
    h, w = min(out.shape[0], f.shape[0]), min(out.shape[1], f.shape[1])
    p = f[:h, :w].astype(np.int32)
    v = (p * d) >> 2 if d < 5 else p + d - 4
    v = np.minimum(v, 15)
    sub = out[:h, :w]
    inside = sub < 0x80
    sub[inside] = DARKEN[sub[inside], v[inside]]
    return out


def outline(pixels):
    """The ring `Outline_Bitmap_` then `Mask_Out_Bitmap_With_Bitmap_` leave:
    every pixel that is 0 or 5 with a solid 4-neighbour becomes 5, every
    pixel of the picture becomes 0. The original walks width x width
    pixels (shear.cpp:135); HD's pictures are square, so the walk is the
    picture."""
    solid = (pixels != 0) & (pixels != OUTLINE_INDEX)
    near = np.zeros_like(solid)
    near[:, 1:] |= solid[:, :-1]
    near[:, :-1] |= solid[:, 1:]
    near[1:, :] |= solid[:-1, :]
    near[:-1, :] |= solid[1:, :]
    out = np.zeros_like(pixels)
    out[near & ~solid & (pixels == 0) | near & (pixels == OUTLINE_INDEX)] = \
        OUTLINE_INDEX
    out[pixels != 0] = 0
    return out


def vanish(pixels, intensity, start=0):
    """`Vanish_Bitmap_(…, intensity)` on an index array (bitmap.cpp:742-768,
    shear.cpp:540-588); `start` the even table index the game draws at
    random."""
    if intensity <= 0:
        return pixels
    if intensity >= 100:
        return np.zeros_like(pixels)
    h, w = pixels.shape
    flat = np.zeros(((h * w + 3) // 4) * 4, dtype=np.uint8)
    flat[:h * w] = pixels.reshape(-1)
    row_dwords = w >> 2
    counter = row_dwords
    idx = int(start) & 0xFE
    n = len(flat) // 4
    for k in range(n):
        ecx = n - k
        for b in range(4):
            if NOISE[idx + b] < intensity:
                flat[4 * k + b] = 0
        idx = (idx + 4) & 0xFF
        counter -= 1
        if flat[4 * k + 3] >= 0x80 or counter == 0:
            counter = row_dwords
            idx = (idx + ecx * ecx) & 0xFE
    return flat[:h * w].reshape(h, w)


def vanished(art, colours, u, intensity, start=0):
    """The unit's glow-0 picture through `vanish`, or None (a painted
    picture is drawn at the alpha left)."""
    owner = u["previous_owner"] if u["previous_owner"] <= 7 else u["owner"]
    colour = colours.get(owner, 0)
    key = ("vanish", colour, u["picture_num"], u["facing_dir"],
           int(intensity), int(start))
    cache = _cache(art)
    if key in cache:
        return cache[key]
    idx = art.ship_indices(colour, u["picture_num"], u["facing_dir"], 0,
                           monster=cbdraw.from_monster_file(u))
    if idx is None:
        surf = art.ship(colour, u["picture_num"], u["facing_dir"], 0,
                        monster=cbdraw.from_monster_file(u))
        if surf is not None:
            surf = surf.copy()
            surf.set_alpha(int(255 * (100 - min(100, intensity)) / 100))
        cache[key] = surf
        return surf
    pixels, palette = idx
    out = vanish(pixels, intensity, start)
    cache[key] = art.from_indices(out, palette) if out.any() else None
    return cache[key]


def _cache(art):
    c = getattr(art, "_cloak_cache", None)
    if c is None:
        c = {}
        try:
            art._cloak_cache = c
        except AttributeError:
            pass
    if len(c) > _CACHE_MAX:
        keep = c.get(("plasma",))
        c.clear()
        c[("plasma",)] = keep
    return c


def picture(art, colours, u, glow, how, progress=0, mode=3):
    """The unit's picture drawn `how` ("cloak": darkened at `progress` in
    `mode`, "outline": its phasing ring), or None to draw nothing."""
    owner = u["previous_owner"] if u["previous_owner"] <= 7 else u["owner"]
    colour = colours.get(owner, 0)
    key = (how, colour, u["picture_num"], u["facing_dir"], int(glow),
           int(progress) % 16 if how == "cloak" else 0,
           darkness(mode, progress) if how == "cloak" else 0)
    cache = _cache(art)
    if key in cache:
        return cache[key]
    idx = art.ship_indices(colour, u["picture_num"], u["facing_dir"], glow,
                           monster=cbdraw.from_monster_file(u))
    if idx is None:                     # a painted picture: no indices
        surf = art.ship(colour, u["picture_num"], u["facing_dir"], glow,
                        monster=cbdraw.from_monster_file(u))
        if surf is not None and how == "cloak":
            surf = surf.copy()
            surf.set_alpha(64)
        elif how != "cloak":
            surf = None
        cache[key] = surf
        return surf
    pixels, palette = idx
    pixels = darken(pixels, progress, mode, plasma(art)) if how == "cloak" \
        else outline(pixels)
    cache[key] = art.from_indices(pixels, palette)
    return cache[key]


class Fades:
    """The cloak fades HD plays when the state it shows changes a unit's
    flag (HD STATE `cloak_fade_time`): {unit: (type, start time)}."""

    def __init__(self):
        self._seen = {}
        self._on = {}

    def reset(self):
        self._seen, self._on = {}, {}

    def update(self, units, now):
        for i, u in enumerate(units):
            flag = int(u.get("special_status_flag", 0))
            was = self._seen.get(i)
            self._seen[i] = flag
            if was is None or was == flag:
                continue
            kind = fade_type(was, flag)
            if kind:
                self._on[i] = (kind, now)

    def step(self, i, now, fast=False):
        """(type, progress) of unit `i`'s fade now, or None."""
        f = self._on.get(i)
        if f is None:
            return None
        kind, t0 = f
        progress = int((now - t0) / TICK) * (2 if fast else 1)
        if progress >= FADE_STEPS[kind]:
            del self._on[i]
            return None
        return kind, progress


def fade_type(was, now):
    """The `Draw_Cloak_` type a flag change plays (combat1.cpp:1107-1123,
    1185-1188; cmbtfire.cpp:1262-1273), or 0."""
    if now in CLOAKED and was not in CLOAKED:
        return 5 if was == PHASED else 1
    if was in CLOAKED and now not in CLOAKED:
        return 2
    if now == PHASED and was != PHASED:
        return 4
    if was == PHASED:
        return 5
    return 0
