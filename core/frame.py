"""The skin frame's GEOMETRY — 9slice.json and its nine tiles.

Until decision 71 this composited the nine tiles into the pre-game
screens' cockpit frame. Nothing draws them since work order 169, and
work order 189 removed the compositing (`render`, `title_rect`,
`content_rect`, the per-size cache). What is still read is the
metadata: the two button bars (`button_rect_left/right`, the help
regions of kind `frame_button`) and the content inset (Custom Race's
fallback rect). The tiles are still loaded because `available` — the
answer those readers ask first — has always meant "all nine are
there"; see work order 189's parked file.

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
        self.content_inset = (0, 0, 0, 0)  # l, r, t, b in source px
        self.source_w = 0
        self.source_h = 0
        self.btn_left = None   # (x, y, w, h) in source px
        self.btn_right = None  # (x, y, w, h) in source px
        self._loaded = False

        if os.path.isdir(frame_dir):
            self._load(frame_dir)

    def _load(self, frame_dir):
        """Load tiles and metadata from frame directory."""
        meta_path = os.path.join(frame_dir, "9slice.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                meta = json.load(f)
            ci = meta.get("content_inset", {})
            self.content_inset = (
                ci.get("left", 0), ci.get("right", 0),
                ci.get("top", 0), ci.get("bottom", 0),
            )
            # `slice_margins_px`, `title_bar` and `button_font_scale`
            # were read for the drawing and went with it (work order 189).
            sz = meta.get("source_size", [0, 0])
            self.source_w, self.source_h = sz
            bl = meta.get("button_bar_left", {})
            if bl:
                self.btn_left = (bl["x"], bl["y"], bl["width"], bl["height"])
            br_cfg = meta.get("button_bar_right", {})
            if br_cfg:
                rx = self.source_w - br_cfg["x_from_right"] - br_cfg["width"]
                self.btn_right = (rx, br_cfg["y"], br_cfg["width"], br_cfg["height"])

        count = 0
        for name in TILE_NAMES:
            path = os.path.join(frame_dir, f"{name}.png")
            if os.path.exists(path):
                self.tiles[name] = pygame.image.load(path).convert_alpha()
                count += 1

        self._loaded = count == 9
        if self._loaded:
            log.info("Frame loaded: %d tiles", count)
        elif count > 0:
            log.warning("Frame incomplete: %d/9 tiles", count)

    @property
    def available(self):
        return self._loaded

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
