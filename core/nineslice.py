"""NineSlice — scalable texture rendering.

NineSlice splits one image into a 3x3 grid; corners stay fixed,
edges stretch 1D, center stretches 2D. Cached per size. Its one
user since decision 71 is `core/researchframe.py`.

`load_tile_directory()`, which assembled the skin's inner panel
tiles into one NineSlice, went with those tiles (work order 189):
nothing drew them since the HUD blocks of decision 71.
"""
import logging
import pygame

log = logging.getLogger("nineslice")


class NineSlice:
    """Scalable texture renderer using 9-slice technique.

    Splits an image into a 3x3 grid. Corners stay fixed,
    edges stretch 1D, center stretches 2D. Cached per size.
    """

    def __init__(self, image, left, right, top, bottom):
        self.image = image
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self._cache = {}

    def render(self, width, height):
        key = (width, height)
        if key in self._cache:
            return self._cache[key]

        src = self.image
        sw, sh = src.get_width(), src.get_height()
        l, r, t, b = self.left, self.right, self.top, self.bottom

        if width < l + r + 2 or height < t + b + 2:
            result = pygame.transform.smoothscale(src, (width, height))
            self._cache[key] = result
            return result

        result = pygame.Surface((width, height), pygame.SRCALPHA)
        dst_cx = width - l - r
        dst_cy = height - t - b
        src_cx = sw - l - r
        src_cy = sh - t - b

        # 4 corners (unchanged)
        result.blit(src, (0, 0), (0, 0, l, t))
        result.blit(src, (width - r, 0), (sw - r, 0, r, t))
        result.blit(src, (0, height - b), (0, sh - b, l, b))
        result.blit(src, (width - r, height - b), (sw - r, sh - b, r, b))

        # 4 edges (1D scaling)
        if dst_cx > 0 and t > 0:
            edge = src.subsurface((l, 0, src_cx, t))
            result.blit(pygame.transform.smoothscale(
                edge, (dst_cx, t)), (l, 0))
        if dst_cx > 0 and b > 0:
            edge = src.subsurface((l, sh - b, src_cx, b))
            result.blit(pygame.transform.smoothscale(
                edge, (dst_cx, b)), (l, height - b))
        if dst_cy > 0 and l > 0:
            edge = src.subsurface((0, t, l, src_cy))
            result.blit(pygame.transform.smoothscale(
                edge, (l, dst_cy)), (0, t))
        if dst_cy > 0 and r > 0:
            edge = src.subsurface((sw - r, t, r, src_cy))
            result.blit(pygame.transform.smoothscale(
                edge, (r, dst_cy)), (width - r, t))

        # Center (2D scaling)
        if dst_cx > 0 and dst_cy > 0:
            center = src.subsurface((l, t, src_cx, src_cy))
            result.blit(pygame.transform.smoothscale(
                center, (dst_cx, dst_cy)), (l, t))

        self._cache[key] = result
        return result

    def clear_cache(self):
        self._cache.clear()
