"""Drawing the battle — work order 197 C. Every rule is the original's, with
its source (`dev:doc/combat_drawing_reading.md` — the reading, checked where
noted); what HD does otherwise is marked.

  background  black (outside a nebula `Fill_(0)`, cmbtdrw1.cpp:431-433), then
              the star layers COMBAT.LBX 46 (35 in a nebula) / 47 / 48,
              tiled — DEVIATION `star_parallax`: the original's two scroll
              paths disagree (edge scroll 80/40/10 px per step, snap
              +160/+80/+20 per cell, combinit.cpp:2458-2482, 2266-2276);
              HD moves the layers at 1, 1/2 and 1/8 of the camera
  legal cells the acting human unit's legal cells filled with palette 0x81,
              box 20 / 40 / 60 px by size (cmbtdrw1.cpp:249-299)
  a unit      its picture at the cell's centre offset (10 / 20 / 30 by size,
              combinit.cpp:3019-3075) less 28 px, the facing's quadrant
              tweak and (2, 3) (`Get_Draw_Ship_Offsets_`,
              cmbtdrw1.cpp:1909-1976); the planet at its own offsets
  the cursor  COMBAT.LBX 0x20 + {0, 1, 2} by size at (-3,-3) / (-5,-4) /
              (-8,-8), frame (glow / 2) % 4 (cmbtdrw1.cpp:816-853)
  ordnance    CMBTMISL[type * 16 + facing] at its world pixel less 12 (23 for
              a torpedo); fighters CMBTFGTR[type * 16 + facing]
              (cmbtmis.cpp:1044-1168) — HD draws one picture per stack
              with its count, DEVIATION `ordnance_stack` (the original's
              stack patterns are not transcribed yet)
"""
import pygame

from . import cbart, cbview

CELL = cbview.CELL
LEGAL_INDEX = 0x81
CENTRE = {0: 10, 1: 20, 2: 20, 3: 30, 4: 30, 5: 30}
BASE_OFF = {0: -16, 1: -6, 2: 4}          # by (size + 1) // 2
PLANET_CENTRE = {0: 30, 1: 40, 2: 60, 3: 70, 4: 80}
PLANET_OFF = {0: (2, 2), 1: (0, 1), 2: (7, 7), 3: (4, 4), 4: (6, 6)}
CURSOR = {0: (0x20, -3, -3), 1: (0x21, -5, -4), 2: (0x22, -8, -8)}
MISSILE_TYPE = {14: 0, 15: 1, 16: 2, 17: 3, 18: 4, 19: 5, 20: 6, 40: 6}
TORPEDOES = {18, 19, 20, 40}
FIGHTER_TYPE = {31: 0, 29: 1, 30: 2, 28: 3}
STAR_LAYERS = ((46, 0.125), (47, 0.5), (48, 1.0))


def sprite_origin(unit):
    """World px of the unit's picture's top-left (`Get_Draw_Ship_Offsets_`)."""
    size = max(0, min(5, int(unit["size_class"])))
    x = unit["x"] * CELL + BASE_OFF[min(2, (size + 1) // 2)]
    y = unit["y"] * CELL + BASE_OFF[min(2, (size + 1) // 2)]
    q = max(0, (int(unit["facing_dir"]) - 1) // 4)
    if q in (1, 2):
        x -= 2
    if q in (2, 3):
        y -= 1
    return x - 2, y - 3


def centre(unit):
    size = max(0, min(5, int(unit["size_class"])))
    return (unit["x"] * CELL + CENTRE[size], unit["y"] * CELL + CENTRE[size])


def scaled(surf, scale, cache):
    key = (id(surf), round(scale, 3))
    if key not in cache:
        w = max(1, round(surf.get_width() * scale))
        h = max(1, round(surf.get_height() * scale))
        cache[key] = pygame.transform.scale(surf, (w, h))
        if len(cache) > 4000:
            cache.clear()
    return cache[key]


def draw_background(surface, cam, art, nebula, cache):
    surface.fill((0, 0, 0), cam.area)
    if not art.available:
        return
    clip = surface.get_clip()
    surface.set_clip(pygame.Rect(cam.area))
    for entry, factor in STAR_LAYERS:
        if nebula and entry == 46:
            entry = 35
        layer = art.surface("combat", entry)
        if layer is None:
            continue
        img = scaled(layer, cam.scale, cache)
        w, h = img.get_size()
        sx = -(cam.ox * factor * cam.scale) % w
        sy = -(cam.oy * factor * cam.scale) % h
        x = cam.area[0] + sx - w
        while x < cam.area[0] + cam.area[2]:
            y = cam.area[1] + sy - h
            while y < cam.area[1] + cam.area[3]:
                surface.blit(img, (x, y))
                y += h
            x += w
    surface.set_clip(clip)


def draw_legal(surface, cam, art, combat, unit):
    size = max(0, min(5, int(unit["size_class"])))
    box = {0: 20, 1: 40, 2: 40}.get(size, 60)
    rgb = (art.palette_with().get(LEGAL_INDEX, (40, 40, 90))
           if art.available else (40, 40, 90))
    from core import combatblocks as cb
    shade = pygame.Surface((max(1, round(box * cam.scale)),) * 2,
                           pygame.SRCALPHA)
    shade.fill((*rgb, 150))
    for x in range(cb.GRID_W):
        for y in range(cb.GRID_H):
            if cb.legal(combat["legal"], x, y):
                surface.blit(shade, cam.to_window(x * CELL, y * CELL))


def draw_units(surface, cam, art, combat, colours, glow_clock, cache,
               planet_pic=None):
    for i, u in enumerate(combat["units"]):
        if u["unit_status"] != 0 or (i and u["structure_max"] <= 0):
            continue
        if i == 0:
            if planet_pic is not None:
                size = planet_pic[1]
                ox, oy = PLANET_OFF.get(size, (7, 7))
                surface.blit(scaled(planet_pic[0], cam.scale, cache),
                             cam.to_window(u["x"] * CELL + ox,
                                           u["y"] * CELL + oy))
            continue
        owner = u["previous_owner"] if u["previous_owner"] <= 7 else u["owner"]
        monster = u["previous_owner"] > 9
        # the glow cycle {1,2,3,2}, phased by the unit (cmbtdrw1.cpp:2499-2508)
        glow = (1, 2, 3, 2)[((glow_clock // 2) + i) % 4]
        pic = art.ship(colours.get(owner, 0), u["picture_num"],
                       u["facing_dir"], glow, monster=monster)
        if pic is None:
            wx, wy = centre(u)
            pygame.draw.circle(surface, (160, 170, 200),
                               [int(v) for v in cam.to_window(wx, wy)],
                               max(3, int(8 * cam.scale)), 1)
            continue
        ox, oy = sprite_origin(u)
        dx, dy = u.get("_off", (0, 0))      # a move being played (cbplay)
        surface.blit(scaled(pic, cam.scale, cache),
                     cam.to_window(ox + dx, oy + dy))


def draw_cursor(surface, cam, art, unit, glow_clock, cache):
    size = max(0, min(5, int(unit["size_class"])))
    entry, dx, dy = CURSOR[0 if size == 0 else 1 if size <= 2 else 2]
    frames = art.frame_count("combat", entry)
    pic = art.surface("combat", entry, (glow_clock // 2) % max(1, frames))
    if pic is None:
        return
    surface.blit(scaled(pic, cam.scale, cache),
                 cam.to_window(unit["x"] * CELL + dx, unit["y"] * CELL + dy))


def draw_ordnance(surface, cam, art, ordnance, font_px, style, cache):
    for m in (ordnance or {}).get("missiles", []):
        kind = int(m["type"])
        facing = int(m["facing_dir"]) & 15
        if kind in FIGHTER_TYPE:
            pic = art.surface("cmbtfgtr", FIGHTER_TYPE[kind] * 16 + facing)
            off = 12
            count = max(1, min(9, int(m["quantity"]) // 4))
        elif kind in MISSILE_TYPE:
            pic = art.surface("cmbtmisl", MISSILE_TYPE[kind] * 16 + facing)
            off = 23 if kind in TORPEDOES else 12
            count = int(m["quantity"])
        else:
            continue
        x, y = cam.to_window(m["x"] - off, m["y"] - off)
        if pic is not None:
            surface.blit(scaled(pic, cam.scale, cache), (x, y))
        if count > 1 and style is not None:
            from screens.leaders import ldrdraw as nd
            nd.blit_text(surface, style, f"{count}", int(x), int(y),
                         200, font_px, (230, 230, 120))
