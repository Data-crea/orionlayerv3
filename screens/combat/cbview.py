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

    def frame_original(self, cell_x, cell_y):
        """The original's framing: 32 cells across, centred on a cell."""
        self.scale = self.area[2] / (VIEW_CELLS[0] * CELL)
        self.centre_on((cell_x + 0.5) * CELL, (cell_y + 0.5) * CELL)

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

    def cell_at(self, x, y):
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
        """Wheel steps about a window point: the world point under it stays."""
        wx, wy = self.to_world(*anchor)
        s = self.scale * (ZOOM_STEP ** steps)
        self.scale = max(self.min_scale(), min(self.max_scale(), s))
        self.ox = wx - (anchor[0] - self.area[0]) / self.scale
        self.oy = wy - (anchor[1] - self.area[1]) / self.scale
        self.clamp()

    def pan(self, dx, dy):
        """A drag of (dx, dy) window px moves the field with the pointer."""
        self.ox -= dx / self.scale
        self.oy -= dy / self.scale
        self.clamp()
