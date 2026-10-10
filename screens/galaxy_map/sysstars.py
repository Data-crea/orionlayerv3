"""The star system window's background: black with stars — work order 230 C
(Data's decision 3: "black background with stars", as the original's
window has it, instead of the box fill).

Where the original's window gets it: `Draw_System_Display_Border_` draws
BUFFER0.LBX 0x49 (sys.cpp:322-327), one 347 x 273 picture that carries the
metal frame, the title panel and, in the view (12..333, 45..227 of the
picture), a field of single-pixel stars on one colour. HD carries no
frame picture (decision 71), so the field is drawn here, in code:

  TRANSCRIPTION  the ground: (0, 12, 0), the view's own colour in 0x49
                 (FONTS.LBX 1's palette; Data's picture of the original
                 shows the same value round the planets)
  TRANSCRIPTION  the stars: 1487 points in the view's 322 x 183 native px,
                 one per 39.6 native px, at the picture's own colours and
                 in their measured shares (`STARS`), each one native px —
                 measured on 0x49 decoded with FONTS.LBX 1 (work order 230,
                 `~/claude/scratch/wo230/C/buffer0_49.png`)
  DEVIATION      `system_stars_drawn`: the points are laid out by a seeded
                 RNG at those shares, not at the picture's own places — the
                 picture is the player's file and is not extracted

A MODDER REPLACES THEM two ways, both through the resource roots
(decision 16): a picture `screens/galaxy_map/assets/system_stars.png`
(stretched over the window below its title panel, the ground under it),
or the numbers — `layout.json` `system_stars` (`native_px_per_star`,
`seed`) and the ground `galaxy_map.system_window_bg` in the skin's
`colors.json`.
"""
import random

import pygame

from core import palette

#: The view's ground in BUFFER0.LBX 0x49.
GROUND = palette.col("galaxy_map", "system_window_bg", (0, 12, 0))
#: The picture's points: (colour, count) in the view's 322 x 183 native
#: px, measured (work order 230).
STARS = (
    ((36, 36, 40), 513), ((24, 24, 32), 314), ((16, 16, 24), 159),
    ((44, 44, 52), 150), ((56, 72, 88), 105), ((72, 72, 80), 64),
    ((96, 96, 104), 44), ((0, 12, 16), 26), ((60, 60, 68), 26),
    ((52, 52, 60), 23), ((88, 100, 120), 23), ((80, 80, 88), 7),
    ((108, 108, 116), 5), ((88, 88, 96), 5), ((156, 164, 180), 5),
    ((12, 12, 40), 4), ((220, 220, 228), 4), ((124, 124, 132), 4),
    ((136, 136, 144), 2), ((40, 60, 76), 1), ((164, 164, 172), 1),
    ((80, 108, 144), 1), ((196, 204, 212), 1))
#: 322 * 183 / 1487: one point per this many native px.
NATIVE_PX_PER_STAR = 39.6
SEED = 230
#: The modder's picture, if one is shipped.
PICTURE = "screens/galaxy_map/assets/system_stars.png"

_cache = {}


def settings(screen):
    """`layout.json` `system_stars`, over the measured defaults."""
    data = (getattr(screen, "_data", None) or {}).get("system_stars") or {}
    return (float(data.get("native_px_per_star", NATIVE_PX_PER_STAR)),
            int(data.get("seed", SEED)))


def picture_path():
    from core import resources
    return resources.res.resolve(PICTURE)


def field(size, s, per_star=NATIVE_PX_PER_STAR, seed=SEED, picture=None):
    """The background for a `size` area at `s` device px per native px:
    the ground and the points, or the modder's picture over the ground.
    Built once per size and kept (P809: recomputed for a new size)."""
    w, h = max(1, int(size[0])), max(1, int(size[1]))
    key = (w, h, round(s, 3), per_star, seed, picture)
    hit = _cache.get(key)
    if hit is not None:
        return hit
    surf = pygame.Surface((w, h))
    # LOOK EXCEPTION transcription: the original's window ground (BUFFER0.LBX 0x49), Data's decision 3
    surf.fill(GROUND[:3])
    if picture:
        try:
            img = pygame.image.load(picture)
            surf.blit(pygame.transform.smoothscale(img, (w, h)), (0, 0))
        except (pygame.error, OSError):
            picture = None
    if not picture:
        rng = random.Random(seed)
        total = sum(n for _c, n in STARS)
        count = int(round((w / s) * (h / s) / max(1.0, per_star)))
        dot = max(1, int(round(s)))
        for _ in range(count):
            roll, acc = rng.uniform(0, total), 0
            colour = STARS[-1][0]
            for c, n in STARS:
                acc += n
                if roll <= acc:
                    colour = c
                    break
            x, y = rng.randrange(w), rng.randrange(h)
            # LOOK EXCEPTION picture: a point of the original's star field (BUFFER0.LBX 0x49)
            surf.fill(colour, (x, y, dot, dot))
    if len(_cache) > 16:
        _cache.clear()
    _cache[key] = surf
    return surf


def draw(screen, surface, rect, s):
    """The field over `rect` (device px), `s` device px per native px."""
    per, seed = settings(screen)
    surface.blit(field(rect.size, s, per, seed, picture_path()), rect.topleft)
