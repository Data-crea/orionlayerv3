"""The shield's flare when a beam strikes it — work order 200 A2. Work order
199 had left it out (its omission, now gone, carried the same name).

TRANSCRIPTION `shield_flare`, from beams.cpp:

  when      every frame of the shot loop (`Beam_SFX_`, :1340-1712): the
            flag `_shield_hit_now_flag` is set while the bolt's head is
            inside the target's shield square — the shot's result says the
            shield was struck (fire result bit 0) and the head lies within
            half the shield's diameter on both axes (`Fire_Weapon_`,
            :2466-2470; `XY_In_Shield_Radius_`, :2639-2648). Frame 0 draws
            only the muzzle and leaves the flag as it was (:2297-2300); once
            the last shot has run out it is cleared (:1573-1575)
  its state `Adjust_Shield_Display_Status_` (:437-478), once a frame: off
            -> ramp-in on the flag (counter 0), counter 0..3 ramps in, 4..6
            loops while the flag holds, then plays out to the picture's last
            frame and goes off; the shot loop does not end before it is off
            (:1578-1585)
  picture   `Shield_Anims_` (:181-198): BEAMS.LBX 67 + size * 5 + rotation;
            109 + ... when the shot pierced (result bit 1, or a shot of the
            same volley went through, `_g_pierced_shield_flag`); 129 + size
            for an enveloping weapon; a planet's 113 + size * 5 + rotation
            with sizes 4-7 by the planet's size (:808-819); frame = counter
            modulo the picture's frames
  rotation  the angle from the shooter to the target, /22 (`Get_SFX_Draw_
            Shield_Facing2_`, :2180-2196), folded to five stored drawings and
            a flip (`Rot_To_Base_Rot_` / `Rot_To_Rot_Method_`, :781-806):
            mirrored, turned half round, upside down (bitmap.cpp:125-150)
  where     its square's corner at the target's centre less half the
            diameter (:1590-1625); diameters 25, 46, 63, 76 for ships by
            size, 117, 155, 193, 215 for planets (:19)
  drawn     the target's own picture again, brightened under the flare's
            glass pixels — index 0xF0 + j lifts the colour's lightness by
            30 + 4 j per cent and takes the battle palette's nearest colour
            (`Mask_Brighten_Bitmap_`, bitmap.cpp:571-620, shear.cpp:362-381;
            the tables of `Load_Shield_Hit_`, beams.cpp:200-222, built by
            `Create_Brighten_Bitmap_Palettes_`, bitmap.cpp:512-560) — then
            the flare over it, glassed (:700-702)
  its glass the battle's SHIELD glass table, which the shot loop puts in
            place (`Restore_Glass_Remap_Block_(_shield_remap_colors)`,
            beams.cpp:1296), built at the battle's start
            (combinit.cpp:854-866): glass pixel 0xF0 + j blends the colour
            under it with (2j + 13, 2j + 30, 63) (6-bit VGA) at 23 + 3 (j - 1)
            per cent, j = 0 with black at 50 (`Update_Glass_Remap_Colors_`,
            remap.cpp:153-187) — a table of palette INDICES, snapped against
            the palette as it stood then, slots 144-175 black
            (`Set_Palette_Gradient_(144, 32, 0...)`, :861), and shown with
            the palette of the moment: the ship ramps the battle loads at
            0x20 (the attacker's colour) and 0x60 (the defender's,
            cmbtdrw1.cpp:2550-2553) are what most of the shield's blends
            land on, so the flare wears the attacker's colours, as it does
            in the original's frame (measured beside it, work order 200)

The brightening and the glass blend are done on the colours HD drew, not on
palette indices (HD draws ship pictures in RGB), and the glass blend is not
snapped to the palette's nearest colour. The flare's sound is not played
(HD plays no battle sounds).
"""
import colorsys

import pygame

from core import lbx

#: beams.cpp:19 — ships by Ship_Size_To_Shield_Size_, planets 4-7
DIAMETERS = (25, 46, 63, 76, 117, 155, 193, 215)
SHIP_SIZE = {0: 0, 1: 1, 2: 1, 3: 2, 4: 3, 5: 3}
#: beams.cpp:23 — the reflection field's, by the same size index
REFLECTION_DIAMETERS = (29, 52, 71, 86)
PLANET_SIZE = {0: 4, 1: 5, 2: 6, 3: 7, 4: 7}
BASE_ROT = (0, 1, 2, 3, 4, 3, 2, 1, 0, 1, 2, 3, 4, 3, 2, 1)
ROT_METHOD = (0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 3)
#: (mirror left-right, upside down) per rotation method — Flip_Bitmap_'s
#: mode 0 reverses each row, mode 3 the order of the rows
FLIPS = {0: (False, False), 1: (True, False), 2: (True, True),
         3: (False, True)}
PLASMA_CANNON = 12              # its natural mods carry ENVELOPING (techdata)
ENVELOPING = 0x100
GLASS = 0xF0
TOTAL_ENTRY = 67                # Shield_Anims_(0, 0, 0, 0): its frame count


def entry(base_rot, size, special, heavy):
    """`Shield_Anims_` — the BEAMS.LBX entry."""
    if size >= 4:
        return 113 + size * 5 + base_rot
    if heavy:
        return 129 + size
    if not special:
        return 67 + size * 5 + base_rot
    return 109 + size * 5 + base_rot


def hit_facing(src, dst, get_angle):
    """`Get_SFX_Draw_Shield_Facing2_(attacker, target)`: 0..15."""
    a = get_angle(src[0] - dst[0], dst[1] - src[1])
    return (a // 22) % 16


def in_shield(x, y, tx, ty, size):
    """`XY_In_Shield_Radius_` for a shield size index."""
    r = DIAMETERS[size] >> 1
    return abs(x - tx) <= r and abs(y - ty) <= r


def step(state, flag, total):
    """`Adjust_Shield_Display_Status_`: (status, counter) -> next."""
    status, n = state
    if status == 0:
        if flag:
            return 1, 0
        return 0, n
    n += 1
    if status == 1:
        return (2 if n >= 4 else 1), n
    if status == 2:
        if flag:
            return 2, (4 if n >= 7 else n)
        return (3 if n >= 7 else 2), n
    return (0 if n >= total else 3), n


def run(flags, total, start=(0, 0), play_out=True):
    """The state after each frame of the shot loop, for the per-frame flag
    `flags` (None: frame 0's 'as it was'), then — with `play_out` — frames
    with the flag cleared until it is off. [(status, counter)], and the
    flag the loop ends on (the next shot of a volley starts from it)."""
    out, state, flag = [], start, False
    for f in flags:
        flag = flag if f is None else f
        state = step(state, flag, total)
        out.append(state)
    if play_out:
        flag = False
        while state[0] != 0:
            state = step(state, flag, total)
            out.append(state)
    return out, flag


def reflection_run(frames=4):
    """`Adjust_Reflection_Field_Display_Status_` (:1797-1837) for a
    reflected beam (state 2): on at once, ramp in 0..3, then out — the
    hit flag is the state-1 test's and stays clear — until the counter
    passes the picture's frames."""
    out, status, n = [], 0, 0
    while True:
        if status == 0:
            if out:
                return out
            status, n = 1, 0
        else:
            n += 1
            if status == 1 and n >= 4:
                status = 2
            elif status == 2 and n >= 7:
                status = 3
            elif status == 3 and n >= frames:
                status = 0
        out.append((status, n))


# ── drawing ───────────────────────────────────────────────────────────
def _indices(art, e, frame, mirror, flip):
    """The flare's palette indices, flipped: (w, h, bytes) or None."""
    b = art.blob("beams", e)
    if not b:
        return None
    try:
        h = lbx.parse_header(b)
        px = lbx.decode_composed(b, h, frame % max(1, h.frame_count))
    except lbx.LbxError:
        return None
    if px is None:
        return None
    rows = [list(px[y * h.width:(y + 1) * h.width]) for y in range(h.height)]
    if mirror:
        rows = [r[::-1] for r in rows]
    if flip:
        rows = rows[::-1]
    return h.width, h.height, rows


def _nearest(rgb, palette, memo):
    if rgb not in memo:
        memo[rgb] = min(palette.values(), key=lambda c: (
            (c[0] - rgb[0]) ** 2 + (c[1] - rgb[1]) ** 2 + (c[2] - rgb[2]) ** 2))
    return memo[rgb]


def brighten(rgb, level, palette, memo):
    """`Create_Brighten_Bitmap_Palettes_`' one entry: lightness lifted by
    `level` per cent (at most full), the palette's nearest colour."""
    h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in rgb))
    l = min(1.0, l + l * level / 100)
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return _nearest((round(r * 255), round(g * 255), round(b * 255)),
                    palette, memo)


def brightened(picture, mask, ox, oy, palette, memo, k=1):
    """A copy of `picture` lifted where `mask` (the flare's indices, its
    top-left at (ox, oy) in the drawing's pixels) holds a glass pixel
    0xF0 + j: by 30 + 4 j per cent (`Load_Shield_Hit_`'s sixteen levels). A
    painted picture at k times the drawing (HD EXTENSION `hd_painted`) is
    lifted k x k pixels for each of the mask's, and the copy keeps its
    factor (`cbart.derived`; work order 219: without it the ship under the
    flare was drawn k times too large). Each (colour, level) is lifted and
    snapped once, through `brighten` — the same arithmetic, so the pixels
    are those the per-pixel walk gave; the walk took 54-164 ms for an 8 x
    picture (work order 219)."""
    import numpy as np
    from . import cbart
    w, h, rows = mask
    out = picture.copy()
    pw, ph = out.get_size()
    m = np.array(rows, dtype=np.int32)
    lvl = np.where(m >= GLASS, (m - GLASS) * 4 + 30, 0)
    if k > 1:
        lvl = np.repeat(np.repeat(lvl, k, 0), k, 1)
    big = np.zeros((ph, pw), dtype=np.int32)
    y0, x0 = oy * k, ox * k
    sy0, sx0 = max(0, y0), max(0, x0)
    sy1, sx1 = min(ph, y0 + lvl.shape[0]), min(pw, x0 + lvl.shape[1])
    if sy1 > sy0 and sx1 > sx0:
        big[sy0:sy1, sx0:sx1] = lvl[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0]
    rgb = pygame.surfarray.pixels3d(out)
    alpha = pygame.surfarray.pixels_alpha(out)
    try:
        hit = (big.T > 0) & (alpha > 0)
        if hit.any():
            c = rgb[hit].astype(np.int64)
            pct = big.T[hit].astype(np.int64)
            key = (c[:, 0] << 24) | (c[:, 1] << 16) | (c[:, 2] << 8) | pct
            uniq, inv = np.unique(key, return_inverse=True)
            rgb[hit] = _brighten_many(uniq, palette, memo)[inv.ravel()]
    finally:
        del rgb, alpha
    return cbart.derived(out, picture)


def _v(m1, m2, hue):
    """`colorsys._v` on arrays, operation for operation."""
    import numpy as np
    hue = np.mod(hue, 1.0)
    return np.where(hue < colorsys.ONE_SIXTH, m1 + (m2 - m1) * hue * 6.0,
                    np.where(hue < 0.5, m2,
                             np.where(hue < colorsys.TWO_THIRD,
                                      m1 + (m2 - m1) * (colorsys.TWO_THIRD
                                                        - hue) * 6.0, m1)))


def _lift(rgb, level):
    """`brighten`'s lift for many colours (n x 3, 0..255) and levels (n):
    `colorsys.rgb_to_hls`, the lightness raised, `hls_to_rgb`, rounded as
    `round` rounds — the same float operations in the same order, so the
    same results (work order 219: 252 flare pictures byte-equal)."""
    import numpy as np
    r, g, b = (rgb[:, i].astype(np.float64) / 255 for i in range(3))
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    sumc, rangec = maxc + minc, maxc - minc
    l = sumc / 2.0
    grey = minc == maxc
    rng = np.where(grey, 1.0, rangec)
    s = np.where(l <= 0.5, rangec / np.where(grey, 1.0, sumc),
                 rangec / np.where(grey, 1.0, 2.0 - maxc - minc))
    rc, gc, bc = (maxc - r) / rng, (maxc - g) / rng, (maxc - b) / rng
    h = np.where(r == maxc, bc - gc,
                 np.where(g == maxc, 2.0 + rc - bc, 4.0 + gc - rc))
    h = np.mod(h / 6.0, 1.0)
    h, s = np.where(grey, 0.0, h), np.where(grey, 0.0, s)
    l = np.minimum(1.0, l + l * level / 100)
    m2 = np.where(l <= 0.5, l * (1.0 + s), l + s - (l * s))
    m1 = 2.0 * l - m2
    out = [np.where(s == 0.0, l, _v(m1, m2, hh))
           for hh in (h + colorsys.ONE_THIRD, h, h - colorsys.ONE_THIRD)]
    return np.rint(np.stack(out, 1) * 255).astype(np.int64)


def _brighten_many(keys, palette, memo):
    """`brighten` for many (colour << 8 | level) keys at once: the lift
    (`_lift`, `colorsys`' arithmetic on arrays), then the palette's nearest
    colour for each distinct lifted colour, first of equals as `_nearest`'s
    `min` takes it: |c - p|^2 less the constant |c|^2 is |p|^2 - 2 c.p, a
    sum of whole numbers well inside a float's exact range, so the same
    order and the same ties. `memo` is kept for the signature; one array
    pass is cheaper than a dictionary of tuples (work order 219)."""
    import numpy as np
    keys = np.asarray(keys, dtype=np.int64)
    rgb = np.stack([(keys >> 24) & 255, (keys >> 16) & 255,
                    (keys >> 8) & 255], 1)
    lifted = _lift(rgb, (keys & 255).astype(np.float64))
    packed = (lifted[:, 0] << 16) | (lifted[:, 1] << 8) | lifted[:, 2]
    uniq, inv = np.unique(packed, return_inverse=True)
    t = np.stack([uniq >> 16, (uniq >> 8) & 255, uniq & 255], 1) \
        .astype(np.float64)
    pal = np.array(list(palette.values()), dtype=np.float64)
    best = np.empty(len(t), dtype=np.int64)
    for i in range(0, len(t), 65536):
        d = (pal * pal).sum(1)[None, :] - 2.0 * (t[i:i + 65536] @ pal.T)
        best[i:i + 65536] = d.argmin(1)
    return pal.astype(np.uint8)[best][inv.ravel()]


#: the shield glass: (r, g, b, per cent) per glass index (combinit.cpp:856-859)
SHIELD_GLASS = [(0, 0, 0, 50)] + [((2 * j + 13) * 4, (2 * j + 30) * 4, 252,
                                   23 + 3 * (j - 1)) for j in range(1, 16)]


def build_palette(art):
    """The palette the shield glass table was snapped against."""
    pal = art.palette_with()
    pal.update({i: (0, 0, 0) for i in range(144, 176)})
    return pal


def show_palette(art, attacker, defender):
    """The palette of the shot loop: the battle's, with the attacker's ship
    ramp at 0x20 and the defender's at 0x60."""
    pal = art.palette_with()
    pal.update({k: v for k, v in art.ramp(attacker).items() if k < 0x40})
    pal.update({k: v for k, v in art.ramp(defender).items() if k >= 0x60})
    return pal


def draw_glassed(surface, rows, at, scale, palette, memo, show=None):
    """The flare's frame `rows` (palette indices) drawn with its top-left at
    window point `at`, `scale` window px per native px, as the shot loop
    draws a glassed picture (animate.cpp:279-288): its own pixels in the
    battle palette, a glass pixel 0xF0 + j replaced by the colour under it
    blended with the shield glass and snapped to the palette's nearest
    colour (`Update_Glass_Remap_Colors_`, remap.cpp:153-187)."""
    import numpy as np
    a = np.array(rows, dtype=np.int32)
    h, w = a.shape
    sh, sw = max(1, round(h * scale)), max(1, round(w * scale))
    a = a[np.minimum((np.arange(sh) / scale).astype(int), h - 1)][
        :, np.minimum((np.arange(sw) / scale).astype(int), w - 1)]
    x0, y0 = int(at[0]), int(at[1])
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1 = min(surface.get_width(), x0 + sw)
    sy1 = min(surface.get_height(), y0 + sh)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    a = a[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0].T          # x-major, as pixels3d
    pal = np.array([palette.get(i, (i, i, i)) for i in range(256)],
                   dtype=np.int32)
    out = pal if show is None else np.array(
        [show.get(i, (i, i, i)) for i in range(256)], dtype=np.int32)
    view = pygame.surfarray.pixels3d(surface)
    try:
        sub = view[sx0:sx1, sy0:sy1]
        own = (a > 0) & (a < GLASS)
        sub[own] = out[a[own]]
        glass = a >= GLASS
        if glass.any():
            g = np.array([c[:3] for c in SHIELD_GLASS], dtype=np.int32)
            pct = np.array([c[3] for c in SHIELD_GLASS], dtype=np.int32)
            j = a[glass] - GLASS
            bg = sub[glass].astype(np.int32)
            tgt = (bg * (100 - pct[j])[:, None] + g[j] * pct[j][:, None]) // 100
            key = (tgt[:, 0] << 16) | (tgt[:, 1] << 8) | tgt[:, 2]
            uniq, inv = np.unique(key, return_inverse=True)
            todo = [k for k in uniq.tolist() if k not in memo]
            if todo:
                t = np.array(todo, dtype=np.int64)
                rgb = np.stack([t >> 16, (t >> 8) & 255, t & 255], 1)
                d = ((rgb[:, None, :] - pal[None, :, :]) ** 2).sum(2)
                for k, best in zip(todo, d.argmin(1).tolist()):
                    memo[k] = best
            near = np.array([memo[k] for k in uniq.tolist()])[inv.ravel()]
            sub[glass] = out[near]
    finally:
        del view


def mask(art, e, frame, rot):
    mirror, flip = FLIPS[ROT_METHOD[rot & 15]]
    return _indices(art, e, frame, mirror, flip)
