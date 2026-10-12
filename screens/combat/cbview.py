"""The battle's camera — world pixels (the original's 20 px cells) to window
pixels. Work order 197 C.

HD EXTENSION `free_camera` and `whole_grid`: the original shows 32 x 18
of the 81 x 68 cells (consts.h:35-38) and scrolls by the pointer at the
edges; HD shows the whole field, zoomed by the wheel about the pointer and
panned by dragging, as the galaxy map is (decision 49's free zoom). It
STARTS as the original frames a battle — 32 cells across, centred on the
acting unit (`Snap_Center_Combat_Screen_`, combinit.cpp:2240) — so the first
picture is the original's, larger.
"""
import math
from dataclasses import dataclass

CELL = 20                        # px per cell (cmbtdrw1.cpp:809-810)
GRID_W, GRID_H = 81, 68          # consts.h:35-36
VIEW_CELLS = (32, 18)            # the original's window (consts.h:37-38)
WORLD_W, WORLD_H = GRID_W * CELL, GRID_H * CELL
ZOOM_STEP = 1.15


@dataclass
class Camera:
    area: tuple                  # window rect (x, y, w, h) the field is drawn in
    scale: float = 1.0           # window px per world px
    ox: float = 0.0              # world px at the area's left edge
    oy: float = 0.0              # world px at the area's top edge

    def min_scale(self):
        """The whole field fits."""
        return min(self.area[2] / WORLD_W, self.area[3] / WORLD_H)

    def max_scale(self):
        """Four times the original's framing."""
        return 4 * self.area[2] / (VIEW_CELLS[0] * CELL)

    def framing(self):
        """The original's framing's scale: 32 cells across the area."""
        return self.area[2] / (VIEW_CELLS[0] * CELL)

    def frame_original(self, cell_x, cell_y):
        """The original's framing: 32 cells across, centred on a cell."""
        self.scale = self.framing()
        self.centre_on((cell_x + 0.5) * CELL, (cell_y + 0.5) * CELL)

    def rungs(self):
        """The wheel's levels (work order 202 B): the framing times
        ZOOM_STEP to a whole power, with the smallest and the largest
        scale as the two ends. A step moves one rung, so a step back lands
        on the level it left — before, a step was `scale * 1.15` clamped at
        the ends, and ten steps in from 3.0 (12.14, clamped to 12) and ten
        out came back at 2.97: another level, scaled again, cached again
        (201)."""
        lo, hi, base = self.min_scale(), self.max_scale(), self.framing()
        out = [lo]
        k = math.ceil(math.log(lo / base, ZOOM_STEP))
        while base * ZOOM_STEP ** k < hi * (1 - 1e-6):
            v = base * ZOOM_STEP ** k
            if v > lo * (1 + 1e-6):
                out.append(v)
            k += 1
        out.append(hi)
        return out

    def centre_on(self, wx, wy):
        self.ox = wx - self.area[2] / (2 * self.scale)
        self.oy = wy - self.area[3] / (2 * self.scale)
        self.clamp()

    def clamp(self):
        vw, vh = self.area[2] / self.scale, self.area[3] / self.scale
        # a field smaller than the area is centred; else no black past it
        self.ox = (WORLD_W - vw) / 2 if vw >= WORLD_W else \
            max(0.0, min(self.ox, WORLD_W - vw))
        self.oy = (WORLD_H - vh) / 2 if vh >= WORLD_H else \
            max(0.0, min(self.oy, WORLD_H - vh))

    def to_window(self, wx, wy):
        return (self.area[0] + (wx - self.ox) * self.scale,
                self.area[1] + (wy - self.oy) * self.scale)

    def to_world(self, x, y):
        return (self.ox + (x - self.area[0]) / self.scale,
                self.oy + (y - self.area[1]) / self.scale)

    def on_field(self, x, y):
        """Is the window point on the battlefield — inside the area the
        field is drawn in? The world goes on under the panel band, so a
        point there maps to a cell nobody sees; it is the panel's, never
        the field's. TRANSCRIPTION `field_only`: the original's field is
        one grid field, (0,0)-(639,359) (combat1.cpp:114), and its panel
        below holds other fields or none (work order 224, D1). The one
        test for the click, the right click and the hover (decision 5)."""
        ax, ay, aw, ah = self.area
        return ax <= x < ax + aw and ay <= y < ay + ah

    def cell_at(self, x, y):
        if not self.on_field(x, y):
            return None
        wx, wy = self.to_world(x, y)
        if not (0 <= wx < WORLD_W and 0 <= wy < WORLD_H):
            return None
        return int(wx // CELL), int(wy // CELL)

    def shows(self, wx, wy, margin=0.15):
        """Is the world point inside the area, `margin` of it kept clear?"""
        x, y = self.to_window(wx, wy)
        ax, ay, aw, ah = self.area
        return ax + aw * margin <= x <= ax + aw * (1 - margin) and \
            ay + ah * margin <= y <= ay + ah * (1 - margin)

    def zoom(self, steps, anchor):
        """Wheel steps about a window point: the world point under it
        stays. From a scale between two rungs (a resized window) the step
        starts at the nearest one."""
        wx, wy = self.to_world(*anchor)
        r = self.rungs()
        n = round(steps) or (1 if steps > 0 else -1 if steps < 0 else 0)
        i = min(range(len(r)), key=lambda j: abs(math.log(r[j] / self.scale)))
        self.scale = r[max(0, min(len(r) - 1, i + n))]
        self.ox = wx - (anchor[0] - self.area[0]) / self.scale
        self.oy = wy - (anchor[1] - self.area[1]) / self.scale
        self.clamp()

    def pan(self, dx, dy):
        """A drag of (dx, dy) window px moves the field with the pointer."""
        self.ox -= dx / self.scale
        self.oy -= dy / self.scale
        self.clamp()
