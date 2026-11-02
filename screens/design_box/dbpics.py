"""The designer pickers' pictures from the player's mod folder.

HD EXTENSION `designer_pictures` (Data, 2 November 2026, "Sci-Fi Arsenal
Button and Compass UI Sheet": four filter buttons and a compass).

The original paints the weapon picker's four filter buttons (Beam, Missile,
Bomb, Special) and its arc dial from DESIGN.LBX (`screens/ship_design/
sdart`). A mod folder may replace them, by exact name under `design_box/`:

  filter_beam.png, filter_missile.png, filter_bomb.png, filter_special.png
  compass.png

A filter picture is the button switched ON (the original's frame 1); the
button OFF is the same picture darkened (the original's frame 0 is the
same button, dark navy with a grey word). The compass is the dial with all
four quarters lit; the original's five arcs (Forward, Forward Extended,
Back Extended, Back, 360) are made by greying the glass in the quarters the
arc does not cover. Each picture is fitted into the place the original's
own stood, never stretched. A missing picture answers False and the
original's art is drawn, as it always was.
"""
import os

import numpy as np
import pygame

TREE = "screens/design_box/assets/{}.png"
KINDS = ("beam", "missile", "bomb", "special")
NAMES = tuple(f"filter_{k}" for k in KINDS) + ("compass",)
#: How much of the lit button's light the OFF button keeps.
OFF_LIGHT = 0.35
#: The arcs the dial lights: the quarters it covers, by picture number
#: (the original's own five pictures, read off them): 0 the front quarter,
#: 1 all but the rear, 2 all but the front, 3 the rear quarter, 4 all.
FRONT, REAR = "front", "rear"
COVERS = {0: (FRONT,), 1: (FRONT, "sides"), 2: ("sides", REAR),
          3: (REAR,), 4: (FRONT, "sides", REAR)}

_raw = {}
_scaled = {}


def _load(res, name):
    path = res.resolve(TREE.format(name))
    if not path or not os.path.isfile(path):
        return None
    stamp = (path, os.path.getmtime(path))
    hit = _raw.get(name)
    if hit is None or hit[0] != stamp:
        try:
            img = pygame.image.load(path).convert_alpha()
        except (pygame.error, OSError):
            img = None
        _raw[name] = hit = (stamp, img)
        _scaled.clear()
    return hit[1]


def _fit(img, size):
    """`img` scaled to the largest size inside `size`, proportion kept."""
    k = min(size[0] / img.get_width(), size[1] / img.get_height())
    return pygame.transform.smoothscale(
        img, (max(1, int(img.get_width() * k)),
              max(1, int(img.get_height() * k))))


def _blit_centred(surface, pic, rect):
    surface.blit(pic, pic.get_rect(center=rect.center))


def draw_filter(surface, res, rect, index, on):
    """Filter button `index` (0..3) in `rect`, lit or dark; True if drawn."""
    img = _load(res, NAMES[index]) if 0 <= index < len(KINDS) else None
    rect = pygame.Rect(rect)
    if img is None or rect.w < 4 or rect.h < 4:
        return False
    key = (index, bool(on), rect.size)
    pic = _scaled.get(key)
    if pic is None:
        pic = _fit(img, rect.size)
        if not on:
            rgb = pygame.surfarray.pixels3d(pic)
            rgb[:] = (rgb * OFF_LIGHT).astype(np.uint8)
            del rgb
        _scaled[key] = pic
    _blit_centred(surface, pic, rect)
    return True


def draw_compass(surface, res, rect, arc):
    """The dial lit for arc picture `arc` (0..4) in `rect`; True if drawn."""
    img = _load(res, "compass")
    rect = pygame.Rect(rect)
    if img is None or arc not in COVERS or rect.w < 8 or rect.h < 8:
        return False
    key = ("compass", arc, rect.size)
    pic = _scaled.get(key)
    if pic is None:
        pic = _fit(img, rect.size)
        w, h = pic.get_size()
        rgb = pygame.surfarray.pixels3d(pic)          # [x, y, channel]
        px = rgb.astype(np.int32)
        glass = (px[..., 2] - np.maximum(px[..., 0], px[..., 1])) > 40
        xs, ys = np.meshgrid(np.arange(w) - w / 2 + 0.5,
                             np.arange(h) - h / 2 + 0.5, indexing="ij")
        ang = np.degrees(np.arctan2(xs, -ys))
        lit = _lit_mask(ang, arc)
        grey = glass & ~lit
        lum = (0.299 * px[..., 0] + 0.587 * px[..., 1] + 0.114 * px[..., 2])
        g = np.clip(lum * 1.6 + 50, 0, 255)
        rgb[..., 0][grey] = g[grey]
        rgb[..., 1][grey] = g[grey]
        rgb[..., 2][grey] = np.clip(g[grey] + 6, 0, 255)
        del rgb
        _scaled[key] = pic
    _blit_centred(surface, pic, rect)
    return True


def _lit_mask(ang, arc):
    a = np.abs(ang)
    front, rear = a <= 45, a >= 135
    side = ~front & ~rear
    cover = COVERS[arc]
    return ((front & (FRONT in cover)) | (rear & (REAR in cover))
            | (side & ("sides" in cover)))
