"""9-slice frame renderer for screen borders.

Loads 9 pre-sliced tile images from a frame directory and
composites them at any window size. Corners stay fixed,
edges stretch 1D, center stretches 2D.

The frame is drawn as an overlay (last) so content renders
underneath the transparent center area.

Modders can replace individual tiles or swap the whole
frame directory in their skin.
"""
import json
import os
import logging
import pygame

log = logging.getLogger("frame")

TILE_NAMES = [
    "top_left", "top", "top_right",
    "left", "center", "right",
    "bottom_left", "bottom", "bottom_right",
]


class FrameRenderer:
    """Renders a 9-slice frame at any size."""

    def __init__(self, frame_dir):
        self.tiles = {}
        self.margins = (0, 0, 0, 0)  # left, right, top, bottom
        self.content_inset = (0, 0, 0, 0)  # l, r, t, b in source px
        self.source_w = 0
        self.source_h = 0
        self.title_bar_y = 0
        self.title_bar_h = 0
        self.btn_left = None   # (x, y, w, h) in source px
        self.btn_right = None  # (x, y, w, h) in source px
        self.button_font_scale = 0.35  # fraction of button height
        self._cache = {}
        self._loaded = False

        if os.path.isdir(frame_dir):
            self._load(frame_dir)

    def _load(self, frame_dir):
        """Load tiles and metadata from frame directory."""
        meta_path = os.path.join(frame_dir, "9slice.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                meta = json.load(f)
            m = meta.get("slice_margins_px", {})
            self.margins = (
                m.get("left", 0), m.get("right", 0),
                m.get("top", 0), m.get("bottom", 0),
            )
            ci = meta.get("content_inset", {})
            self.content_inset = (
                ci.get("left", 0), ci.get("right", 0),
                ci.get("top", 0), ci.get("bottom", 0),
            )
            sz = meta.get("source_size", [0, 0])
            self.source_w, self.source_h = sz
            tb = meta.get("title_bar", {})
            self.title_bar_y = tb.get("y", 0)
            self.title_bar_h = tb.get("height", 0)
            bl = meta.get("button_bar_left", {})
            if bl:
                self.btn_left = (bl["x"], bl["y"], bl["width"], bl["height"])
            br_cfg = meta.get("button_bar_right", {})
            if br_cfg:
                rx = self.source_w - br_cfg["x_from_right"] - br_cfg["width"]
                self.btn_right = (rx, br_cfg["y"], br_cfg["width"], br_cfg["height"])
            self.button_font_scale = meta.get("button_font_scale", 0.35)

        count = 0
        for name in TILE_NAMES:
            path = os.path.join(frame_dir, f"{name}.png")
            if os.path.exists(path):
                self.tiles[name] = pygame.image.load(path).convert_alpha()
                count += 1

        self._loaded = count == 9
        if self._loaded:
            log.info("Frame loaded: %d tiles, margins %s",
                     count, self.margins)
        elif count > 0:
            log.warning("Frame incomplete: %d/9 tiles", count)

    @property
    def available(self):
        return self._loaded

    def render(self, width, height):
        """Get a frame surface at (width, height). Cached per size.

        Buttonless frames are separate tile sets loaded as frame
        variants (subdirectories), not runtime tile swaps.
        """
        key = (width, height)
        if key in self._cache:
            return self._cache[key]

        if not self._loaded:
            return None

        ml, mr, mt, mb = self.margins
        t = self.tiles

        # Scale margins proportionally to window vs source
        sx = width / self.source_w if self.source_w else 1.0
        sy = height / self.source_h if self.source_h else 1.0
        cl = int(ml * sx)
        cr = int(mr * sx)
        ct = int(mt * sy)
        cb = int(mb * sy)

        # Center stretch dimensions
        cx_w = width - cl - cr
        cy_h = height - ct - cb

        if cx_w < 1 or cy_h < 1:
            return None

        result = pygame.Surface((width, height), pygame.SRCALPHA)

        # Corners (scaled proportionally)
        result.blit(pygame.transform.smoothscale(
            t["top_left"], (cl, ct)), (0, 0))
        result.blit(pygame.transform.smoothscale(
            t["top_right"], (cr, ct)), (width - cr, 0))
        result.blit(pygame.transform.smoothscale(
            t["bottom_left"], (cl, cb)), (0, height - cb))
        result.blit(pygame.transform.smoothscale(
            t["bottom_right"], (cr, cb)), (width - cr, height - cb))

        # Edges
        result.blit(pygame.transform.smoothscale(
            t["top"], (cx_w, ct)), (cl, 0))
        result.blit(pygame.transform.smoothscale(
            t["bottom"], (cx_w, cb)), (cl, height - cb))
        result.blit(pygame.transform.smoothscale(
            t["left"], (cl, cy_h)), (0, ct))
        result.blit(pygame.transform.smoothscale(
            t["right"], (cr, cy_h)), (width - cr, ct))

        # Center (usually mostly transparent)
        result.blit(pygame.transform.smoothscale(
            t["center"], (cx_w, cy_h)), (cl, ct))

        self._cache[key] = result
        return result

    def content_rect(self, win_w, win_h):
        """Inner content area rect after border insets.

        Returns (x, y, w, h) in window pixels. Screens should
        place their outermost elements inside this rect.
        """
        if not self.source_w or not self.source_h:
            return (0, 0, win_w, win_h)
        sx = win_w / self.source_w
        sy = win_h / self.source_h
        il, ir, it, ib = self.content_inset
        x = int(il * sx)
        y = int(it * sy)
        w = win_w - int((il + ir) * sx)
        h = win_h - int((it + ib) * sy)
        return (x, y, w, h)

    def title_rect(self, win_w, win_h):
        """Title bar rect in window pixels (dark panel in top center).

        Returns (x, y, w, h) or None if no title bar defined.
        """
        if not self.title_bar_h or not self.source_w:
            return None
        sx = win_w / self.source_w
        sy = win_h / self.source_h
        ml, mr, mt, mb = self.margins
        cl = int(ml * sx)
        cr = int(mr * sx)
        ty = int(self.title_bar_y * sy)
        th = int(self.title_bar_h * sy)
        return (cl, ty, win_w - cl - cr, th)

    def clear_cache(self):
        self._cache.clear()

    def button_rect_left(self, win_w, win_h):
        """Left button bar rect in window pixels, or None."""
        if not self.btn_left or not self.source_w:
            return None
        sx = win_w / self.source_w
        sy = win_h / self.source_h
        bx, by, bw, bh = self.btn_left
        return (int(bx * sx), int(by * sy), int(bw * sx), int(bh * sy))

    def button_rect_right(self, win_w, win_h):
        """Right button bar rect in window pixels, or None."""
        if not self.btn_right or not self.source_w:
            return None
        sx = win_w / self.source_w
        sy = win_h / self.source_h
        bx, by, bw, bh = self.btn_right
        return (int(bx * sx), int(by * sy), int(bw * sx), int(bh * sy))
