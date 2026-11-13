"""An owner's mark beside a stack's icon — HD EXTENSION `owner_marks`
(Data, 13 November 2026).

The galaxy map tells the empires apart by the hull's colour alone, and for
a player who cannot tell some of them (red-green blind: the nearest two of
eight owners 0.2 apart in Delta E under Okabe-Ito, measured offline) that
is not enough. Under the colour-blind palette (`playercolors.COLOUR_BLIND`,
Okabe-Ito) every player stack carries a small white mark with a dark rim on
the icon's upper right, a shape that belongs to the owner's colour and not
to its hue: 0 circle, 1 square, 2 triangle up, 3 diamond, 4 plus, 5 cross,
6 ring, 7 triangle down. Tied to the palette, no switch of its own (Data:
"ich würde es koppeln"). Drawn inside `ships.render` after the icon, so
the box, the slot, the click and the lines are the icon's own, unchanged.
Registered in `layout.json` `_markings`.
"""
import pygame

#: The mark's size against the icon's height, and its least size in px.
SHARE, LEAST = 0.55, 10
#: Supersampling of the shape before it is brought to size.
_K = 6
WHITE, RIM = (245, 245, 245), (0, 0, 8)
SHAPES = ("circle", "square", "triangle_up", "diamond", "plus", "cross",
          "ring", "triangle_down")
_MADE = {}
_KEEP = 64


def shape_for(colour):
    """The shape name of an owner colour (0..7)."""
    return SHAPES[int(colour) % len(SHAPES)]


def _draw(surf, name, c, r, col):
    """`name`'s shape centred on (c, c), half-extent `r`, in `col`."""
    t = max(2, int(r * 0.42))
    if name == "circle":
        pygame.draw.circle(surf, col, (c, c), r)
    elif name == "ring":
        pygame.draw.circle(surf, col, (c, c), r, t)
    elif name == "square":
        d = int(r * 0.86)
        # LOOK EXCEPTION data: the owner mark's shape, one per owner colour
        pygame.draw.rect(surf, col, (c - d, c - d, 2 * d, 2 * d))
    elif name == "triangle_up":
        # LOOK EXCEPTION data: the owner mark's shape, one per owner colour
        pygame.draw.polygon(surf, col, ((c, c - r), (c + r, c + int(r * .8)),
                                        (c - r, c + int(r * .8))))
    elif name == "triangle_down":
        # LOOK EXCEPTION data: the owner mark's shape, one per owner colour
        pygame.draw.polygon(surf, col, ((c, c + r), (c + r, c - int(r * .8)),
                                        (c - r, c - int(r * .8))))
    elif name == "diamond":
        # LOOK EXCEPTION data: the owner mark's shape, one per owner colour
        pygame.draw.polygon(surf, col, ((c, c - r), (c + r, c), (c, c + r),
                                        (c - r, c)))
    elif name == "plus":
        # LOOK EXCEPTION data: the owner mark's shape, one per owner colour
        pygame.draw.rect(surf, col, (c - r, c - t // 2, 2 * r, t))
        # LOOK EXCEPTION data: the owner mark's shape, one per owner colour
        pygame.draw.rect(surf, col, (c - t // 2, c - r, t, 2 * r))
    elif name == "cross":
        d = int(r * 0.8)
        h = max(1.0, t * 0.7071)
        # LOOK EXCEPTION data: the owner mark's shape, one per owner colour
        for (x0, y0), (x1, y1) in (((c - d, c - d), (c + d, c + d)),
                                   ((c - d, c + d), (c + d, c - d))):
            nx, ny = (y1 - y0), -(x1 - x0)
            n = (nx * nx + ny * ny) ** 0.5 or 1.0
            ox, oy = nx / n * h, ny / n * h
            pygame.draw.polygon(surf, col, ((x0 + ox, y0 + oy),
                                            (x1 + ox, y1 + oy),
                                            (x1 - ox, y1 - oy),
                                            (x0 - ox, y0 - oy)))


def mark(colour, size):
    """The mark of owner colour `colour` as a `size` x `size` picture with
    its rim, made once per (colour, size)."""
    key = (int(colour) % len(SHAPES), int(size))
    hit = _MADE.get(key)
    if hit is not None:
        return hit
    k = _K
    side = size * k
    rim = max(k, int(side * 0.14))
    big = pygame.Surface((side, side), pygame.SRCALPHA, 32)
    c = side // 2
    r = c - rim - 1
    sil = pygame.Surface((side, side), pygame.SRCALPHA, 32)
    _draw(sil, SHAPES[key[0]], c, r, (255, 255, 255, 255))
    dark = pygame.mask.from_surface(sil, 40).to_surface(
        setcolor=RIM + (255,), unsetcolor=(0, 0, 0, 0))
    steps = ((-rim, 0), (rim, 0), (0, -rim), (0, rim), (-rim, -rim),
             (rim, -rim), (-rim, rim), (rim, rim),
             (-rim // 2, -rim), (rim // 2, -rim), (-rim // 2, rim),
             (rim // 2, rim), (-rim, -rim // 2), (-rim, rim // 2),
             (rim, -rim // 2), (rim, rim // 2))
    for dx, dy in steps:
        big.blit(dark, (dx, dy))
    big.blit(dark, (0, 0))
    _draw(big, SHAPES[key[0]], c, r, WHITE + (255,))
    out = pygame.transform.smoothscale(big, (size, size))
    if len(_MADE) >= _KEEP:
        _MADE.clear()
    _MADE[key] = out
    return out


def size_for(box_h):
    return max(LEAST, int(round(box_h * SHARE)))


def draw(surface, left, top, box_w, box_h, colour):
    """The mark on the upper right of the icon box at (left, top); none
    for a stack without a colour (None)."""
    if colour is None:
        return
    s = size_for(box_h)
    picture = mark(colour, s)
    surface.blit(picture, (int(round(left + box_w - s * 0.55)),
                           int(round(top - s * 0.45))))
