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

    def vertical(self, ref_y, ref_h, anchor=None):
        """(window y, window height) of a reference band, by anchor.

        HD EXTENSION, work order 170 (decision 71's HUD). The content
        area is 16:9 and centred, so on a window taller than 16:9 it
        leaves letterbox above and below — and a bar that should sit
        on the window's bottom edge would sit on the content area's.
        An anchor keeps a box's distance from the WINDOW's edge instead:

          None       the content area, as every box always was
          "top"      its distance from the window's top edge
          "bottom"   its distance from the window's bottom edge
          "stretch"  top edge as "top", bottom edge as "bottom": the
                     box grows with the window between the two

        Every distance is the reference distance times `scale`, so at
        16:9 and at every wider window all four give the same rect."""
        top = ref_y * self.scale
        bottom = (self.ref_h - ref_y - ref_h) * self.scale
        if anchor == "top":
            return int(top), int(ref_h * self.scale)
        if anchor == "bottom":
            h = int(ref_h * self.scale)
            return int(self.window_h - bottom) - h, h
        if anchor == "stretch":
            y = int(top)
            return y, int(self.window_h - bottom) - y
        return (int(ref_y * self.scale + self.offset_y),
                int(ref_h * self.scale))

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
