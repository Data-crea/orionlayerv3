"""NineSlice — scalable texture rendering.

Two building blocks used across the UI:
  - NineSlice: splits one image into a 3x3 grid; corners stay
    fixed, edges stretch 1D, center stretches 2D. Cached per size.
  - load_tile_directory(): assembles nine separate tile images
    (top_left.png ... bottom_right.png) into one NineSlice.

The cockpit frame (core/frame.py) intentionally does NOT use
this class: it scales its corners proportionally with the
window, while NineSlice keeps corners at native pixel size.
"""
import os
import logging
import pygame

log = logging.getLogger("nineslice")

TILE_NAMES = ["top_left", "top", "top_right", "left", "center",
              "right", "bottom_left", "bottom", "bottom_right"]


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


def load_tile_directory(panel_dir):
    """Assemble nine tile PNGs from a directory into one NineSlice.

    Returns None if the directory is missing tiles. Corner size is
    taken from top_left.png (tiles are expected to be square-cornered).
    """
    parts = {}
    for name in TILE_NAMES:
        path = os.path.join(panel_dir, f"{name}.png")
        if os.path.exists(path):
            parts[name] = pygame.image.load(path).convert_alpha()
    if len(parts) < 9:
        return None

    corner = parts["top_left"].get_width()
    full_w = (corner + parts["top"].get_width()
              + parts["top_right"].get_width())
    full_h = (corner + parts["left"].get_height()
              + parts["bottom_left"].get_height())
    assembled = pygame.Surface((full_w, full_h), pygame.SRCALPHA)
    assembled.blit(parts["top_left"], (0, 0))
    assembled.blit(parts["top"], (corner, 0))
    assembled.blit(parts["top_right"], (full_w - corner, 0))
    assembled.blit(parts["left"], (0, corner))
    assembled.blit(parts["center"], (corner, corner))
    assembled.blit(parts["right"], (full_w - corner, corner))
    bl_h = parts["bottom_left"].get_height()
    assembled.blit(parts["bottom_left"], (0, full_h - bl_h))
    assembled.blit(parts["bottom"], (corner, full_h - bl_h))
    assembled.blit(parts["bottom_right"], (full_w - corner, full_h - bl_h))
    log.debug("Assembled tiles from %s: %dx%d corner=%d",
              panel_dir, full_w, full_h, corner)
    return NineSlice(assembled, corner, corner, corner, corner)
