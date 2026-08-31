"""
Reference-to-window coordinate scaling.

All UI coordinates live in the reference space (1920x1080).
This class converts them to the actual window size.
Called once on load/resize, not per frame.
"""
from core.config import REF_W, REF_H


class Layout:
    """Scales reference coordinates to window coordinates."""

    def __init__(self, window_w, window_h):
        self.window_w = window_w
        self.window_h = window_h
        self.ref_w = REF_W
        self.ref_h = REF_H

        # Uniform scale: use smaller factor so nothing is clipped.
        # Letterboxing on aspect ratio mismatch.
        self.scale_x = window_w / self.ref_w
        self.scale_y = window_h / self.ref_h
        self.scale = min(self.scale_x, self.scale_y)

        # Center offset for letterbox bars
        scaled_w = self.ref_w * self.scale
        scaled_h = self.ref_h * self.scale
        self.offset_x = (window_w - scaled_w) / 2
        self.offset_y = (window_h - scaled_h) / 2

    def rect(self, ref_rect):
        """Reference rect [x,y,w,h] -> window rect (int tuple)."""
        x, y, w, h = ref_rect
        return (
            int(x * self.scale + self.offset_x),
            int(y * self.scale + self.offset_y),
            int(w * self.scale),
            int(h * self.scale),
        )

    def pos(self, ref_x, ref_y):
        """Reference position -> window position (int tuple)."""
        return (
            int(ref_x * self.scale + self.offset_x),
            int(ref_y * self.scale + self.offset_y),
        )

    def size(self, ref_w, ref_h):
        """Reference size -> window size (int tuple)."""
        return (int(ref_w * self.scale), int(ref_h * self.scale))

    def to_ref(self, screen_x, screen_y):
        """Window coordinate -> reference coordinate (for input)."""
        rx = (screen_x - self.offset_x) / self.scale
        ry = (screen_y - self.offset_y) / self.scale
        return (int(rx), int(ry))

    def font_size(self, ref_size):
        """Reference font size -> scaled size (int, min 8)."""
        return max(8, int(ref_size * self.scale))

    def update(self, window_w, window_h):
        """Recalculate after window resize."""
        self.__init__(window_w, window_h)
