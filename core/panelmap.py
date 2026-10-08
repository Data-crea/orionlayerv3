"""A transcribed screen's native regions, fitted into its shell panels —
work order 225 (decisions 86-92, "How the transcribed screens are handled").

A transcribed screen draws and hits everything at the HD image of its
native 640x480 rectangle: `core.researchnative.to_hd` puts the 640x480
picture into the 4:3 island of the reference area, and `Layout.rect` takes
it to the window. The shell wants the screen's panels in ONE content
rectangle instead (`core.hud.shell`), so each transcribed screen names its
panels as boxes of its own (`boxes.json`, F5-editable, the Fleets pattern:
reference boxes to draw and hit, the original rectangles only to know what
the engine's fields are) and says which NATIVE REGION each one carries.

`PanelMap` is the screen's layout for everything native. It is a `Layout`
— the same scale, so a font, a line and a sprite's integer step are what
they always were (decision 28) — whose `rect`, `pos` and `to_ref` carry a
point of a native region into that region's panel and back:

    window = panel.x + (native - region.x) * panel.w / region.w   (and y)

So the drawing code and the hit test, which only ever ask the layout,
place and hit every native rectangle in its panel, through ONE function
each way (decision 5); nothing in the shared native helpers
(`researchnative`, `ldrdraw`) changes, and a screen that has no map is
drawn exactly as before. A click resolves to the native pixel the drawing
put there, so it reaches the same field as before (decision 35: the wire
coordinates are still the game's own rectangles).

A point outside every panel has no native pixel (`to_ref` gives a point
`from_hd_point` refuses), as a point outside the 4:3 island had none.

DEVIATION `panel_fit`: the original's regions keep their proportion; a
panel of another shape spreads its region's positions (the words and
sprites keep their size).
"""
import math

import pygame

from core.config import REF_H, REF_W
from core.layout import Layout

NATIVE_W, NATIVE_H = 640, 480

#: A reference point no native pixel answers to (left of the island).
NOWHERE = (-1.0e6, -1.0e6)


def _island():
    """`researchnative._scale`'s numbers, for the reference area: the
    native picture's scale and offset inside 1920x1080."""
    k = min(REF_W / NATIVE_W, REF_H / NATIVE_H)
    return k, (REF_W - NATIVE_W * k) / 2.0, (REF_H - NATIVE_H * k) / 2.0


class Region:
    """One native rectangle (inclusive, as the source writes it) and the
    window rect it is fitted into."""

    def __init__(self, name, native, window, hit=True):
        x1, y1, x2, y2 = native
        self.name = name
        #: False: drawn into its window, never hit — a region whose native
        #: rectangle overlaps fields that live elsewhere now (the shell's
        #: button row), so a click there must resolve to no native pixel.
        self.hit = hit
        self.native = (x1, y1, x2, y2)
        self.nx, self.ny = float(x1), float(y1)
        self.nw, self.nh = float(x2 - x1 + 1), float(y2 - y1 + 1)
        self.window = pygame.Rect(window)
        self.sx = self.window.w / self.nw
        self.sy = self.window.h / self.nh

    def holds(self, nx, ny):
        return (self.nx <= nx < self.nx + self.nw
                and self.ny <= ny < self.ny + self.nh)

    def distance(self, nx, ny):
        dx = max(self.nx - nx, 0.0, nx - (self.nx + self.nw))
        dy = max(self.ny - ny, 0.0, ny - (self.ny + self.nh))
        return dx * dx + dy * dy

    def to_window(self, nx, ny):
        return (self.window.x + (nx - self.nx) * self.sx,
                self.window.y + (ny - self.ny) * self.sy)

    def to_native(self, wx, wy):
        # A hair inward: a pixel centre exactly on a cell's left edge must
        # not fall a float's width short of it.
        return (self.nx + (wx - self.window.x) / self.sx + 1e-7,
                self.ny + (wy - self.window.y) / self.sy + 1e-7)


def _edge(v):
    """A device edge: the first pixel whose CENTRE is at or past `v`.
    Both edges of a drawn rectangle use it, so the pixels drawn are
    exactly those whose centre lies in [left, right) — the ones `to_ref`
    sends back inside the rectangle (decision 5)."""
    return int(math.ceil(v - 0.5))


class PanelMap(Layout):
    """The base layout, with native positions carried region by region.

    `regions` is [(name, native rect, window rect[, hit])]; the FIRST region that
    holds a point wins, and a point no region holds goes to the nearest
    one (a native rectangle that straddles two regions is placed by its
    centre, so it moves as a whole)."""

    def __init__(self, base, regions):
        super().__init__(base.window_w, base.window_h)
        self.base = base
        self.regions = [Region(*r) for r in regions]

    @property
    def sprite_scale(self):
        """Window px per native px a SPRITE may take here: the tightest
        scale of any hit region, either axis. A panel that squeezes its
        region (the shell's banner and row leave less height than the
        4:3 island had) must not keep the island's integer step, or a
        portrait outgrows its row (decision 28: steps, never stretches)."""
        return min(min(r.sx, r.sy) for r in self.regions if r.hit)

    # The native picture's reference coordinates (what `to_hd` returns)
    # and back — exact inverses of `researchnative`'s arithmetic.
    @staticmethod
    def _native_of(ref_x, ref_y):
        """Back to the native picture. `to_hd` rounded each edge to a
        whole reference px (at most 0.5 / 2.25 of a native px off), and
        every native coordinate the screens pass is whole: so the nearest
        whole native px is the one that was meant."""
        k, ox, oy = _island()
        return round((ref_x - ox) / k), round((ref_y - oy) / k)

    @staticmethod
    def _ref_of(nx, ny):
        k, ox, oy = _island()
        return ox + nx * k, oy + ny * k

    def region_of(self, nx, ny):
        for reg in self.regions:
            if reg.holds(nx, ny):
                return reg
        return min(self.regions, key=lambda r: r.distance(nx, ny))

    def rect(self, ref_rect):
        x, y, w, h = ref_rect
        nx, ny = self._native_of(x, y)
        k = _island()[0]
        nw, nh = round(w / k), round(h / k)
        reg = self.region_of(nx + nw / 2.0, ny + nh / 2.0)
        x0, y0 = reg.to_window(nx, ny)
        x1, y1 = reg.to_window(nx + nw, ny + nh)
        left, top = _edge(x0), _edge(y0)
        return (left, top, _edge(x1) - left, _edge(y1) - top)

    def pos(self, ref_x, ref_y):
        nx, ny = self._native_of(ref_x, ref_y)
        x, y = self.region_of(nx, ny).to_window(nx, ny)
        return _edge(x), _edge(y)

    def region_at(self, screen_x, screen_y):
        """The region whose panel holds this window point, or None."""
        for reg in self.regions:
            if reg.hit and reg.window.collidepoint(screen_x, screen_y):
                return reg
        return None

    def to_ref(self, screen_x, screen_y):
        """A window point to the native picture's reference coordinates,
        UNROUNDED: `from_hd_point` truncates once, to the native pixel the
        drawing put under this point. Outside every panel: `NOWHERE`."""
        reg = self.region_at(screen_x, screen_y)
        if reg is None:
            return NOWHERE
        # The pixel's centre, nudged in, so a truncation never lands one
        # native pixel short of the cell that drew it.
        nx, ny = reg.to_native(screen_x + 0.5, screen_y + 0.5)
        return self._ref_of(nx, ny)

    def update(self, window_w, window_h):
        raise RuntimeError("a PanelMap is rebuilt from its screen's boxes, "
                           "never resized in place")
