"""Territories, the drawing half: glass, borders and tinted nebulas.

the territory view (`terrfield`) (see `terrfield` for what a territory is).
Three layers, each switched by the left panel (`terrpanel`):

  * the GLASS fill — the territory's colour, strongest along the border
    and a third of it inside, scaled by the player's opacity slider. The
    picture is built once per state at the field's grid and scaled
    (bilinear) for the part of the map in view, so the slider and the
    zoom cost a scale, not a rebuild;
  * the BORDERS — the field's contour, a soft glow, a body and a bright
    core, in the empire's colour. **For colour blindness the colour is
    never the only sign:** while a colour-blind preset is the player's
    palette (`palette.active_preset() != "original"`) each of the eight
    colours also gets its own line pattern (`PATTERNS`), shown in the
    legend beside the swatch. Colour comes from the same table the star
    names use, so the player's choice in the GAME menu reaches this view
    without a setting of its own;
  * the NEBULAS take the colour of the territory they lie in, so gas
    over two empires is the mix of both (`tint_nebula`).
"""
import math

import numpy as np
import pygame

from core import palette
from screens.galaxy_map import maplines

#: Player settings and their defaults (`core/usersettings.py` carries the
#: same values; a tool with no settings gets these).
SHOW, BORDERS, NEBULAE, OPACITY = ("territory_show", "territory_borders",
                                   "territory_nebulae", "territory_opacity")
DEFAULT_OPACITY = 40

#: How much of a nebula's own colour a full territory replaces.
NEBULA_TINT = 0.80
#: At most this many tinted nebula pictures are kept (one per nebula and
#: size); a zoom sweep would otherwise keep every size it passed through.
TINT_KEEP = 24

#: A line's on/off lengths in layout px, one per colour index. Eight that
#: differ by length AND rhythm, so two read apart at a glance and in a
#: dash that is cut short by the screen's edge.
PATTERNS = (None, (22, 9), (3, 8), (16, 7, 3, 7), (8, 8),
            (16, 6, 3, 6, 3, 6), (3, 4, 3, 4, 3, 14), (34, 10))


def setting(app, key):
    us = getattr(app, "user_settings", None)
    if us is None:
        return {SHOW: "on", BORDERS: "on", NEBULAE: "on",
                OPACITY: DEFAULT_OPACITY}[key]
    return us.get(key)


def is_on(app, key):
    return setting(app, key) != "off"


def opacity(app):
    v = setting(app, OPACITY)
    try:
        return min(1.0, max(0.0, float(v) / 100.0))
    except (TypeError, ValueError):
        return DEFAULT_OPACITY / 100.0


def patterned():
    """Patterns on while the player's palette is a colour-blind one."""
    return palette.active_preset() != "original"


def pattern_for(colour):
    return PATTERNS[colour % len(PATTERNS)] if patterned() else None


def affine(view):
    """(ox, oy, kx, ky): screen = o + k * world, measured over a long
    baseline. `MapView.to_screen` truncates to whole native pixels, as
    the original does, so one world unit alone reads as 0 or a step; a
    territory is a smooth area and takes the line the stars follow."""
    span = 6000.0
    ox, oy = view.to_screen(0.0, 0.0)
    ex, ey = view.to_screen(span, span)
    return ox, oy, (ex - ox) / span, (ey - oy) / span


def _surface(terr):
    surf = getattr(terr, "_surf", None)
    if surf is None:
        surf = pygame.Surface((terr.w, terr.h), pygame.SRCALPHA, 32)
        pygame.surfarray.pixels3d(surf)[:] = terr.fill[..., :3].swapaxes(0, 1)
        pygame.surfarray.pixels_alpha(surf)[:] = terr.fill[..., 3].T
        terr._surf = surf
    return surf


def render_fill(surface, view, terr, opacity_):
    """The glass, for the part of the territory that is in view."""
    from screens.galaxy_map import terrfield as tf
    box = pygame.Rect(view.box)
    ox, oy, kx, ky = affine(view)
    wx0, wy0 = (box.left - ox) / kx, (box.top - oy) / ky
    wx1, wy1 = (box.right - ox) / kx, (box.bottom - oy) / ky
    c = tf.CELL
    i0 = max(0, int(math.floor((min(wx0, wx1) - terr.x0) / c)) - 1)
    j0 = max(0, int(math.floor((min(wy0, wy1) - terr.y0) / c)) - 1)
    i1 = min(terr.w, int(math.ceil((max(wx0, wx1) - terr.x0) / c)) + 2)
    j1 = min(terr.h, int(math.ceil((max(wy0, wy1) - terr.y0) / c)) + 2)
    if i1 - i0 < 2 or j1 - j0 < 2:
        return
    sub = _surface(terr).subsurface(pygame.Rect(i0, j0, i1 - i0, j1 - j0))
    ax, ay = (ox + (terr.x0 + (i0 - 0.5) * c) * kx,
              oy + (terr.y0 + (j0 - 0.5) * c) * ky)
    bx, by = (ox + (terr.x0 + (i1 - 0.5) * c) * kx,
              oy + (terr.y0 + (j1 - 0.5) * c) * ky)
    size = (max(1, int(round(bx - ax))), max(1, int(round(by - ay))))
    img = pygame.transform.smoothscale(sub, size)
    img.set_alpha(int(255 * opacity_))
    surface.blit(img, (int(round(ax)), int(round(ay))))


# ── borders ──────────────────────────────────────────────

def _dashes(pts, pattern):
    """The 'on' pieces of a closed polyline cut by `pattern` (lengths in
    px, on, off, on, ...): points arrays, each one dash."""
    seg = np.hypot(*np.diff(pts, axis=0).T)
    along = np.concatenate([[0.0], np.cumsum(seg)])
    total = along[-1]
    out, pos, k = [], 0.0, 0
    while pos < total:
        step = pattern[k % len(pattern)]
        if k % 2 == 0:
            ts = np.arange(pos, min(pos + step, total), 1.0)
            ts = np.append(ts, min(pos + step, total))
            out.append(np.column_stack([np.interp(ts, along, pts[:, 0]),
                                        np.interp(ts, along, pts[:, 1])]))
        pos += step
        k += 1
    return out


class BorderLayer:
    """The borders' transparent layer, kept between frames of one size."""

    def __init__(self):
        self.layer = None

    def get(self, size):
        if self.layer is None or self.layer.get_size() != size:
            self.layer = pygame.Surface(size, pygame.SRCALPHA, 32)
        self.layer.fill((0, 0, 0, 0))
        return self.layer


def render_borders(surface, view, terr, colours, scale, opacity_, cache):
    box = pygame.Rect(view.box)
    layer = cache.get(box.size)
    ox, oy, kx, ky = affine(view)
    strength = min(1.0, 0.60 + 0.40 * opacity_)
    core_w = max(2, int(round(1.6 * scale)))
    drawn = False
    for colour, loops in terr.loops.items():
        rgb = tuple(colours[colour % len(colours)][:3])
        bright = tuple(min(255, int(c + (255 - c) * 0.35)) for c in rgb)
        pattern = pattern_for(colour)
        for loop in loops:
            pts = np.column_stack([loop[:, 0] * kx + ox - box.x,
                                   loop[:, 1] * ky + oy - box.y])
            if (pts[:, 0].max() < 0 or pts[:, 1].max() < 0
                    or pts[:, 0].min() > box.w or pts[:, 1].min() > box.h):
                continue
            pts = np.vstack([pts, pts[:1]])
            pieces = (_dashes(pts, [p * scale for p in pattern])
                      if pattern else [pts])
            for piece in pieces:
                path = [(float(x), float(y)) for x, y in piece]
                # glow, body, core: written over each other, widest first
                maplines.stroke_path(layer, rgb + (int(46 * strength),),
                                     path, core_w * 5)
                maplines.stroke_path(layer, rgb + (int(120 * strength),),
                                     path, core_w * 2 + 1)
                maplines.stroke_path(layer, bright + (int(255 * strength),),
                                     path, core_w)
            drawn = True
    if drawn:
        surface.blit(layer, box.topleft)


# ── nebulas ──────────────────────────────────────────────

def tint_nebula(img, neb_key, view, neb_xy, terr):
    """`img` (a nebula's additive picture) recoloured by the territory it
    lies in: its brightness kept, its hue moved towards the territory's
    colour by the territory's cover. Cached on `terr`, so a new state
    drops it; None-safe (no territory: the picture as it is)."""
    if terr is None or img is None:
        return img
    from screens.galaxy_map import terrfield as tf
    w, h = img.get_size()
    key = (neb_key, w, h)
    cache = terr.__dict__.setdefault("_tints", {})
    hit = cache.get(key)
    if hit is not None:
        return hit
    _ox, _oy, kx, ky = affine(view)
    if not kx or not ky:
        return img
    gx = neb_xy[0] + (np.arange(w) + 0.5) / kx
    gy = neb_xy[1] + (np.arange(h) + 0.5) / ky
    ci = np.clip(np.rint((gx - terr.x0) / tf.CELL).astype(int), 0, terr.w - 1)
    rj = np.clip(np.rint((gy - terr.y0) / tf.CELL).astype(int), 0, terr.h - 1)
    cover = terr.cover[np.ix_(rj, ci)].T                    # (w, h)
    if cover.max() <= 0.001:
        out = img
    else:
        tint = terr.tint[np.ix_(rj, ci)].transpose(1, 0, 2)  # (w, h, 3)
        direction = tint / np.maximum(tint.max(axis=2, keepdims=True), 1.0)
        src = pygame.surfarray.array3d(img).astype(np.float32)
        lum = src.max(axis=2, keepdims=True)
        m = (cover * NEBULA_TINT)[..., None]
        mixed = src * (1.0 - m) + lum * direction * m
        out = pygame.surfarray.make_surface(
            np.clip(mixed, 0, 255).astype(np.uint8))
    if len(cache) >= TINT_KEEP:
        cache.clear()
    cache[key] = out
    return out
