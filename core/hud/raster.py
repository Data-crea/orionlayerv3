"""Shapes for the HUD blocks, rasterised once at the device size.

Decision 71 asks for a style that is sharp at every resolution. That is
what drawing a shape at the size it is shown buys, and it is spent here:

- **the outline is a polygon**, drawn at `supersample` times the device
  size and smoothscaled down once — that is the antialiasing of a slant
  or a chamfer at any size, and it keeps edges sub-pixel exact;
- **the edge line is the polygon minus its inset**, so its width is one
  number from style.json and it is the same width at every corner;
- **a glow is that edge line blurred**, by three box passes over numpy
  cumulative sums at the DEVICE size (pygame 2.6 has no blur), and split
  into what falls inside the shape — the soft band along the inside of
  every HUD edge — and what falls outside it.

Nothing here knows what a panel or a button is; `blocks` does.
"""
import numpy as np
import pygame


def chamfered(w, h, c):
    """A w x h rectangle with all four corners cut by `c`."""
    c = max(0.0, min(c, w / 2, h / 2))
    return [(c, 0), (w - c, 0), (w, c), (w, h - c), (w - c, h), (c, h),
            (0, h - c), (0, c)]


def slanted(w, h, s):
    """A parallelogram leaning right like the HUD's nav buttons ("/"):
    its top is shifted `s * h` right of its bottom."""
    d = max(0.0, min(s * h, w / 2))
    return [(d, 0), (w, 0), (w - d, h), (0, h)]


def inset(poly, e):
    """A convex polygon moved `e` inward along every edge normal.

    Each edge is shifted and adjacent shifted edges are intersected, so
    the band between `poly` and `inset(poly, e)` is `e` wide on every
    side and at every corner — which is the edge line's whole promise.
    The polygons here are clockwise in screen coordinates (y down)."""
    n = len(poly)
    lines = []
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        ln = (dx * dx + dy * dy) ** 0.5 or 1.0
        nx, ny = -dy / ln, dx / ln          # inward for clockwise, y down
        lines.append(((x0 + nx * e, y0 + ny * e), (dx, dy)))
    out = []
    for i in range(n):
        (px, py), (dx, dy) = lines[i - 1]
        (qx, qy), (ex, ey) = lines[i]
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            out.append((qx, qy))
            continue
        t = ((qx - px) * ey - (qy - py) * ex) / den
        out.append((px + t * dx, py + t * dy))
    return out


def _mask(poly, size, ss, pad):
    """Coverage 0..1 of `poly` (device px, origin at the pad) as floats
    at the device size, via a `ss`-times polygon smoothscaled down."""
    w, h = size
    big = pygame.Surface((w * ss, h * ss))
    big.fill((0, 0, 0))
    pts = [((x + pad) * ss, (y + pad) * ss) for x, y in poly]
    pygame.draw.polygon(big, (255, 255, 255), pts)
    small = pygame.transform.smoothscale(big, (w, h))
    m = pygame.surfarray.array_red(small).astype(np.float32).T / 255.0
    # FULL COVERAGE IS EXACTLY 1. smoothscale tops out a level or two
    # below 255 inside a filled shape, which made a popup's body 99.6 %
    # opaque — invisible, and enough to blend what was under it through
    # by one or two levels (found by the research screen's "popup drawn
    # last" check, work order 169).
    m[m > 0.985] = 1.0
    m[m < 0.015] = 0.0
    return m


def blur(a, radius, passes=3):
    """A box blur of `a` (2-D float), `passes` times: near a gaussian of
    sigma ~ radius / 1.7. Exact at the borders by edge padding."""
    r = int(round(radius))
    if r < 1:
        return a
    out = a
    for _ in range(passes):
        for axis in (0, 1):
            p = np.pad(out, [(r + 1, r) if ax == axis else (0, 0)
                             for ax in (0, 1)], mode="edge")
            c = np.cumsum(p, axis=axis, dtype=np.float64)
            if axis == 0:
                out = (c[2 * r + 1:] - c[:-2 * r - 1]) / (2 * r + 1)
            else:
                out = (c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)
    return out.astype(np.float32)


def shape(poly_fn, w, h, *, fill, edge, edge_w, glow=None, glow_w=0.0,
          inner=None, inner_w=0.0, fill_alpha=1.0, ss=3, glass=None):
    """One HUD shape as an RGBA surface, and the pad it was drawn with.

    `poly_fn(w, h)` gives the outline in device px. `fill`, `edge`,
    `glow`, `inner` are RGB; `edge_w`, `glow_w`, `inner_w` device px.
    `glass`, when given, is a float (h, w, 3) fill in place of `fill`.
    The surface is the shape's box plus `pad` on every side, so a glow
    has room; blit it at (x - pad, y - pad)."""
    pad = int(np.ceil(glow_w * 2.2)) + 2 if glow else 1
    size = (w + 2 * pad, h + 2 * pad)
    poly = poly_fn(w, h)
    outer = _mask(poly, size, ss, pad)
    inner_m = _mask(inset(poly, edge_w), size, ss, pad)
    line = np.clip(outer - inner_m, 0.0, 1.0)
    rgb = np.empty(size[::-1] + (3,), np.float32)
    rgb[...] = fill
    if glass is not None:
        # The panel GLASS (work order 174): a per-pixel fill for the
        # shape's own box, `core.hud.glass`; the edge, the inner band and
        # the glow go over it as over a flat fill.
        rgb[pad:pad + h, pad:pad + w] = glass
    if inner is not None and inner_w > 0:
        g = blur(line, inner_w / 2.0)
        g = np.clip(g / max(float(g.max()), 1e-6) * 1.6, 0.0, 1.0)
        g *= inner_m
        rgb += (np.array(inner, np.float32) - rgb) * g[..., None]
    rgb += (np.array(edge, np.float32) - rgb) * line[..., None]
    alpha = outer * fill_alpha + line * (1.0 - fill_alpha)
    if fill_alpha == 0.0 and inner is not None and inner_w > 0:
        # An OUTLINE keeps the soft band along the inside of its edge, as
        # a translucent wash over whatever the box holds.
        alpha = np.maximum(alpha, g * 0.55)
    if glow is not None and glow_w > 0:
        g = blur(line, glow_w)
        g = np.clip(g / max(float(g.max()), 1e-6) * 1.4, 0.0, 1.0)
        g *= (1.0 - outer)
        rgb += (np.array(glow, np.float32) - rgb) * g[..., None]
        alpha = np.maximum(alpha, g * 0.85)
    surf = pygame.Surface(size, pygame.SRCALPHA)
    px = pygame.surfarray.pixels3d(surf)
    px[...] = np.clip(rgb, 0, 255).astype(np.uint8).transpose(1, 0, 2)
    del px
    pa = pygame.surfarray.pixels_alpha(surf)
    pa[...] = np.clip(alpha * 255.0, 0, 255).astype(np.uint8).T
    del pa
    return surf, pad
