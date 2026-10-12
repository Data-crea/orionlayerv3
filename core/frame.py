"""The skin frame's GEOMETRY — its 9slice.json.

Until decision 71 this composited nine tile images into the pre-game
screens' cockpit frame. Nothing draws them since work order 169; work
order 189 removed the compositing and work order 190 the tiles. What is
read is the metadata: the source size and the content inset (Custom
Race's fallback rect). The two button bars it also read went in work
order 228: nothing asked for them — the frame buttons and their help
regions are the screen shell's (`core/hud/screenframe.py`,
`core/screenhelp.py`). `available` — the answer those readers ask first — means
"this skin's frame has its 9slice.json" since 190; until then it meant
"all nine tiles are there", which for the shipped skin is the same answer.

A skin may replace the frame directory with its own 9slice.json.
"""
import json
import os
import logging

log = logging.getLogger("frame")

class FrameRenderer:
    """The skin frame's 9slice.json: source size and content inset."""

    def __init__(self, frame_dir):
        self.content_inset = (0, 0, 0, 0)  # l, r, t, b in source px
        self.source_w = 0
        self.source_h = 0
        self._loaded = False

        if os.path.isdir(frame_dir):
            self._load(frame_dir)

    def _load(self, frame_dir):
        """Load the metadata from the frame directory."""
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
            self._loaded = True
            log.info("Frame geometry loaded: %s", meta_path)

    @property
    def available(self):
        return self._loaded
