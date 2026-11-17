"""The dark glow round a galaxy-map ship or monster icon.

One job: `haloed` builds (and caches) the ring that is drawn round a
sprite's silhouette, `blit_haloed` draws the sprite with it. Split out of
ships.py (decision 6) at the seam between the icons' placement and
picking and their one drawing effect; it needs nothing from ships.py.
"""
import pygame


#: Haloed copies made so far, keyed by the sprite they came from (held, so
#: its id cannot be reused); bounded.
_HALOED = {}
HALO_KEEP = 256
#: A ship's dark glow (a light rim looked wrong on black, Data).
GLOW_COLOR = (0, 0, 8)


def haloed(sprite):
    """`sprite` with a dark glow round its silhouette,
    on a canvas grown by the glow (HD EXTENSION `map_icon_halo`, Data: ships
    and monsters must stand out from the background)."""
    hit = _HALOED.get(id(sprite))
    if hit is not None and hit[0] is sprite:
        return hit[1]
    w, h = sprite.get_size()
    g = max(2, min(4, round(min(w, h) / 10)))
    pad = g + 1
    mask = pygame.mask.from_surface(sprite, 40)
    sil = mask.to_surface(setcolor=(255, 255, 255, 255),
                          unsetcolor=(0, 0, 0, 0))

    def tinted(colour, alpha):
        t = sil.copy()
        t.fill(colour + (255,), special_flags=pygame.BLEND_RGBA_MULT)
        t.set_alpha(alpha)
        return t

    out = pygame.Surface((w + 2 * pad, h + 2 * pad), pygame.SRCALPHA, 32)
    glow = tinted(GLOW_COLOR, 80)
    for d in range(2, g + 1):
        for dx, dy in ((-d, 0), (d, 0), (0, -d), (0, d),
                       (-d, -d), (d, -d), (-d, d), (d, d)):
            out.blit(glow, (pad + dx, pad + dy))
    # only the ring: the silhouette itself is cut out, the sprite is blitted
    # on its own, first, and the ring over its edge (see `blit_haloed`)
    out.blit(sil, (pad, pad), special_flags=pygame.BLEND_RGBA_SUB)
    if len(_HALOED) >= HALO_KEEP:
        _HALOED.clear()
    _HALOED[id(sprite)] = (sprite, out)
    return out


def blit_haloed(surface, sprite, cx, cy):
    x = int(round(cx - sprite.get_width() / 2.0))
    y = int(round(cy - sprite.get_height() / 2.0))
    ring = haloed(sprite)
    pad = (ring.get_width() - sprite.get_width()) // 2
    # the ring is the outline round the picture, so it goes over the
    # picture's own edge pixels only where the picture is transparent
    surface.blit(sprite, (x, y))
    surface.blit(ring, (x - pad, y - pad))
