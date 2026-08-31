"""ListView — scrollable table widget.

The workhorse for Colony Summary, Planet Summary, Reports,
Officers, Load/Save: a header row, scrollable data rows, hover
and selection, and an optional scrollbar.

The widget draws INSIDE a rect the screen provides (typically a
box with skin=inner_panel — the panel background is the box's
job, not the widget's). All fonts are rasterized at target pixel
size via style.get_font(layout.font_size(...)).

Colors come from the skin's colors.json "widgets" section with
code defaults (see core/palette.py).

Usage in a screen:
    self.list = ListView(
        columns=[("NAME", 0.4), ("POP", 0.2), ("PROD", 0.2),
                 ("FOOD", 0.2)],
        on_select=self._on_row)
    self.list.set_rows([("Sol III", "8", "12", "5"), ...])
    # render():  self.list.render(surface, rect, style, layout)
    # input:     self.list.handle_click(x, y)
    #            self.list.handle_mousewheel(dy, x, y)
    #            self.list.handle_mouse_motion(x, y)
"""
import pygame
from core import palette

_c = palette.for_section("widgets")

COL_HEADER     = _c("list_header",     (138, 180, 232))
COL_ROW        = _c("list_row",        (200, 202, 212))
COL_ROW_DIM    = _c("list_row_dim",    (144, 152, 176))
COL_HOVER_BG   = _c("list_hover_bg",   (40, 55, 90, 120))
COL_SELECT_BG  = _c("list_select_bg",  (50, 75, 130, 170))
COL_SELECT_TX  = _c("list_select_text", (220, 235, 255))
COL_SEPARATOR  = _c("list_separator",  (60, 80, 120))
COL_SCROLLBAR  = _c("list_scrollbar",  (70, 95, 150))
COL_SCROLL_BG  = _c("list_scroll_bg",  (25, 32, 55))

HEADER_FONT = 15    # reference sizes (1080p)
ROW_FONT = 16
ROW_HEIGHT = 26
PAD_X = 10
SCROLLBAR_W = 8


class ListView:
    def __init__(self, columns, on_select=None, row_height=ROW_HEIGHT):
        """columns: list of (title, width_fraction); fractions
        should sum to <= 1.0."""
        self.columns = columns
        self.on_select = on_select
        self.row_height_ref = row_height
        self.rows = []
        self.selected = -1
        self.hover = -1
        self.scroll = 0          # first visible row index
        self._rect = pygame.Rect(0, 0, 0, 0)
        self._visible = 0

    # ── Data ────────────────────────────────────────────

    def set_rows(self, rows, keep_selection=False):
        self.rows = list(rows)
        if not keep_selection:
            self.selected = -1
        self.selected = min(self.selected, len(self.rows) - 1)
        self.scroll = max(0, min(self.scroll,
                                 max(0, len(self.rows) - 1)))

    # ── Geometry ────────────────────────────────────────

    def _row_h(self, layout):
        return max(14, int(self.row_height_ref * layout.scale))

    def _rows_area(self, layout):
        """Rect of the data rows (below the header)."""
        h = self._row_h(layout)
        return pygame.Rect(self._rect.x, self._rect.y + h,
                           self._rect.w, self._rect.h - h)

    def row_at(self, x, y):
        """Row index under screen point, or -1."""
        area = self._rows_area(self._layout)
        if not area.collidepoint(x, y):
            return -1
        idx = self.scroll + (y - area.y) // self._row_h(self._layout)
        return idx if 0 <= idx < len(self.rows) else -1

    # ── Input ───────────────────────────────────────────

    def handle_click(self, x, y):
        """Select row under point. Returns row index or -1."""
        idx = self.row_at(x, y)
        if idx >= 0:
            self.selected = idx
            if self.on_select:
                self.on_select(idx, self.rows[idx])
        return idx

    def handle_mouse_motion(self, x, y):
        self.hover = self.row_at(x, y)

    def handle_mousewheel(self, dy, x, y):
        """Scroll if the pointer is inside the widget."""
        if not self._rect.collidepoint(x, y):
            return False
        max_scroll = max(0, len(self.rows) - self._visible)
        self.scroll = max(0, min(max_scroll, self.scroll - dy * 3))
        return True

    def handle_key(self, key):
        """Optional arrow-key navigation. Returns True if consumed."""
        if key == pygame.K_UP and self.selected > 0:
            self.selected -= 1
        elif key == pygame.K_DOWN and self.selected < len(self.rows) - 1:
            self.selected += 1
        else:
            return False
        if self.selected < self.scroll:
            self.scroll = self.selected
        elif self.selected >= self.scroll + self._visible:
            self.scroll = self.selected - self._visible + 1
        if self.on_select and 0 <= self.selected < len(self.rows):
            self.on_select(self.selected, self.rows[self.selected])
        return True

    # ── Render ──────────────────────────────────────────

    def render(self, surface, rect, style, layout):
        self._rect = pygame.Rect(rect)
        self._layout = layout
        row_h = self._row_h(layout)
        hfont = style.get_font(layout.font_size(HEADER_FONT))
        rfont = style.get_prop_font(layout.font_size(ROW_FONT))

        # Column x positions
        xs = []
        x = rect.x + int(PAD_X * layout.scale)
        usable = rect.w - int(2 * PAD_X * layout.scale) - SCROLLBAR_W
        for title, frac in self.columns:
            xs.append(x)
            x += int(usable * frac)

        # Header
        for (title, _), cx in zip(self.columns, xs):
            surface.blit(hfont.render(title.upper(), True, COL_HEADER),
                         (cx, rect.y + 2))
        pygame.draw.line(surface, COL_SEPARATOR,
                         (rect.x + 4, rect.y + row_h - 2),
                         (rect.right - 4, rect.y + row_h - 2))

        # Rows
        area = self._rows_area(layout)
        self._visible = max(1, area.h // row_h)
        end = min(len(self.rows), self.scroll + self._visible)
        for i in range(self.scroll, end):
            ry = area.y + (i - self.scroll) * row_h
            row_rect = pygame.Rect(area.x + 2, ry, area.w - 4, row_h)
            if i == self.selected:
                shade = pygame.Surface(row_rect.size, pygame.SRCALPHA)
                shade.fill(COL_SELECT_BG)
                surface.blit(shade, row_rect.topleft)
            elif i == self.hover:
                shade = pygame.Surface(row_rect.size, pygame.SRCALPHA)
                shade.fill(COL_HOVER_BG)
                surface.blit(shade, row_rect.topleft)
            color = COL_SELECT_TX if i == self.selected else COL_ROW
            for value, cx in zip(self.rows[i], xs):
                surface.blit(rfont.render(str(value), True, color),
                             (cx, ry + (row_h - rfont.get_height()) // 2))

        # Scrollbar
        if len(self.rows) > self._visible:
            track = pygame.Rect(rect.right - SCROLLBAR_W - 2,
                                area.y, SCROLLBAR_W, area.h)
            pygame.draw.rect(surface, COL_SCROLL_BG, track,
                             border_radius=3)
            frac_h = self._visible / len(self.rows)
            frac_y = self.scroll / len(self.rows)
            thumb = pygame.Rect(track.x,
                                track.y + int(track.h * frac_y),
                                SCROLLBAR_W,
                                max(16, int(track.h * frac_h)))
            pygame.draw.rect(surface, COL_SCROLLBAR, thumb,
                             border_radius=3)
