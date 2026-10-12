"""The star system window's rounded corners — work order 235 (Data's
decision, 11 October 2026: "the outer frame is far too hard").

  DEVIATION      `system_window_rounded`: the window's outer frame — the
                 map's window and the combat target window, one drawing
                 (`syswindow.system_frame`) — has rounded corners, drawn
                 with antialiasing; the ground, the stars and everything
                 drawn inside are clipped to the rounded shape, and the
                 map shows through outside it. The frame's colour and line
                 width are unchanged (0x41, decided in 230 P1). The
                 original's window is BUFFER0.LBX 0x49, a picture; HD
                 draws a line (decision 71), and its corners are Data's
                 choice, not a measurement.

THE RADIUS LIVES HERE, ONCE, in native px of the window picture (P604:
the proportion carries across window sizes, a pixel count does not). It
is chosen to fit what stands in the corners: the title panel's corner is
10.5 x 6.3 native px in from the window's, CLOSE's 10.5 x 7.0, so with 16
the arc passes about 5 native px outside either corner — clearly round,
and nothing it holds is cut. Measured on the boxes at 1920x1080,
3440x1440 and 3840x2160, all three the same in native px. The title panel
is rounded the same way, smaller (`PANEL_CORNER_NATIVE`) — not asked for;
the session's call by eye, shown beside the square panel in the
evidence.

HOW: the four corner squares of the backdrop are kept before the window
is drawn (`Corners`), and after the last thing inside is drawn
`Corners.finish` lays each square back together: the backdrop outside the
arc, the frame's line on it, the window's own pixels inside, each pixel
weighted by how much of it the shape covers (the distance to the arc,
clamped to one pixel's width — the antialiasing). Everything inside is
clipped because the window is finished last, whoever drew in it.
"""
import math

import numpy as np
import pygame

#: The window's corner radius, native px — both windows (work order 235).
CORNER_NATIVE = 16
#: The title panel's corner radius, native px (0 keeps it square): the
#: outer radius less the panel's inset, so the two arcs run alongside —
#: a square panel in a round corner read hard again (work order 235's
#: comparison shows both).
PANEL_CORNER_NATIVE = 6


def coverage(radius, inset, side):
    """How much of each pixel of a `side` x `side` top-left corner square
    lies inside a rounded rectangle of corner `radius` shrunk by `inset`
    (device px), as an (x, y) array of 0..1. The arc's centre is at
    (radius, radius); a pixel past it on either axis is measured to the
    straight edge, so the square joins the window's sides seamlessly."""
    c = (np.arange(side, dtype=float) + 0.5)
    dx = np.maximum(radius - c, 0.0)[:, None]
    dy = np.maximum(radius - c, 0.0)[None, :]
    d = np.hypot(dx, dy)
    return np.clip(radius - inset - d + 0.5, 0.0, 1.0)


class Corners:
    """The four corner squares of `box`'s backdrop on `surface`, kept
    before the window is drawn over them."""

    def __init__(self, surface, box, radius, line):
        self.box = pygame.Rect(box)
        self.radius = float(radius)
        self.line = int(line)
        self.side = int(math.ceil(self.radius))
        self.saved = {}
        if self.side < 2:
            return
        bounds = surface.get_rect()
        for name, rect in self.squares().items():
            if bounds.contains(rect):
                self.saved[name] = pygame.surfarray.array3d(
                    surface.subsurface(rect)).astype(float)

    def squares(self):
        n, b = self.side, self.box
        return {"tl": pygame.Rect(b.x, b.y, n, n),
                "tr": pygame.Rect(b.right - n, b.y, n, n),
                "bl": pygame.Rect(b.x, b.bottom - n, n, n),
                "br": pygame.Rect(b.right - n, b.bottom - n, n, n)}

    def finish(self, surface, colour):
        """Lay the corners back together: backdrop outside the arc, the
        frame's line in `colour`, the window inside (module docstring)."""
        if not self.saved:
            return
        outer = coverage(self.radius, 0, self.side)
        inner = coverage(self.radius, self.line, self.side)
        line = np.array(colour[:3], dtype=float)
        squares = self.squares()
        for name, backdrop in self.saved.items():
            o, i = outer, inner
            if name[1] == "r":
                o, i = o[::-1, :], i[::-1, :]
            if name[0] == "b":
                o, i = o[:, ::-1], i[:, ::-1]
            o, i = o[..., None], i[..., None]
            rect = squares[name]
            inside = pygame.surfarray.array3d(
                surface.subsurface(rect)).astype(float)
            out = backdrop * (1 - o) + line * (o - i) + inside * i
            surface.blit(pygame.surfarray.make_surface(
                np.rint(out).astype(np.uint8)), rect)
