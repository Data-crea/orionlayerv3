"""Colony Summary — orion2re SCREEN_COLONY_SUMMARY (id 20).

The original's "Colonies" list: every colony in a row with its
population split into farmers, workers and scientists, sortable by
seven keys, with the empire totals on the right (colsum.cpp).

Layout: one cockpit frame PNG (assets/frame.png) with transparent
cutouts, stretched over the 1920x1080 reference area and drawn above
everything else — the same construction as the galaxy map. The
boxes in boxes.json ARE the cutouts, derived by tools/frame_holes.py:
  list_area       the colony rows (population bars: next step)
  sidebar         the six empire readouts
  output_panel    production breakdown of the selected colony (later)
  galaxy_inset    the original's small galaxy map (later)
  spare_panel     reserved
  return          RETURN
  sort_*          the seven sort buttons
The title cutout is not a box; it lives in layout.json ("frame").

Input goes to the original by coordinates, not by field id: each sort
button and RETURN has a `native_click` in layout.json, a point inside
the original's button (colsum.cpp:265-273), and the screen injects a
click there. Nothing here needs the field list.

Data: the sidebar is transcribed from COLSUM::Draw_Empire_Info_, six
lines, each one s_player field — all six are in the verified spec.
The list itself waits on s_colony, which is not verified yet.
"""
import logging

import pygame

from core import mouse as mouse_input
from core import palette
from core.config import REF_W, REF_H
from core.screen_base import ScreenBase
from core.structs import player as player_struct

from . import colonylist

log = logging.getLogger("colony_summary")

PANEL_BG = palette.col("colony_summary", "panel_background", (8, 11, 20))
NAV_BG = palette.col("colony_summary", "nav_background", (10, 14, 26))
NAV_HOVER_BG = palette.col("colony_summary", "nav_hover", (22, 34, 60))
NAV_ACTIVE_BG = palette.col("colony_summary", "nav_active", (30, 48, 88))
NAV_TEXT = palette.col("colony_summary", "nav_text", (196, 208, 236))
TITLE_COLOR = palette.col("colony_summary", "title", (200, 210, 238))
LABEL_COLOR = palette.col("colony_summary", "label", (140, 155, 190))
VALUE_COLOR = palette.col("colony_summary", "value", (220, 228, 245))
WARN_COLOR = palette.col("colony_summary", "warn", (235, 90, 80))

#: Native screen the original draws under this one (640x480).
NATIVE_W, NATIVE_H = 640, 480


def format_value(value, signed=False):
    """'+12' / '-3' with signed, else plain — the original's %+d / %d."""
    if signed and value >= 0:
        return f"+{value}"
    return str(value)


class ColonySummaryScreen(ScreenBase):
    SCREEN_NAME = "colony_summary"
    GAME_SCREEN_ID = 20         # SCREEN_COLONY_SUMMARY
    USE_FRAME = False           # own frame PNG, see _render_frame_image
    FRAME_TITLE = "Colonies"

    def __init__(self, app):
        super().__init__(app)
        self._data = {}
        self._frame = None
        self._frame_scaled = None
        self._frame_pos = (0, 0)
        self._local = None          # parsed s_player of the local player
        self._sort_key = "name"     # what the original starts on
        self._state = None          # last snapshot, for the list

    # ── Lifecycle ─────────────────────────────────────────

    def enter(self, game_state=None):
        super().enter(game_state)
        self._data = self.app.res.load_json(
            "screens/colony_summary/layout.json", {}) or {}
        self._sort_key = self._data.get("sort", {}).get("default", "name")
        self._load_frame()
        self.update(game_state)

    def update(self, game_state=None):
        if game_state is None:
            return
        # Kept whole for the list, which needs colonies, planets and
        # stars together; the sidebar only ever wanted the local
        # player's record.
        self._state = game_state
        raws = getattr(game_state, "player_raw", None) or []
        players = [player_struct.parse(r) for r in raws
                   if len(r) >= player_struct.SIZE]
        idx = getattr(game_state, "player_num", 0)
        self._local = players[idx] if 0 <= idx < len(players) else None

    def on_resize(self):
        super().on_resize()
        self._scale_frame()

    # ── Frame ─────────────────────────────────────────────

    def _load_frame(self):
        """The cutout frame; stretched over the reference area so the
        cutouts coincide with the boxes derived from them."""
        cfg = self._data.get("frame", {})
        path = self.asset_path("assets", cfg.get("image", "frame.png"))
        self._frame = (pygame.image.load(path).convert_alpha()
                       if path else None)
        self._scale_frame()

    def _scale_frame(self):
        if self._frame is None:
            self._frame_scaled = None
            return
        x, y, w, h = self.layout.rect((0, 0, REF_W, REF_H))
        self._frame_scaled = pygame.transform.smoothscale(self._frame, (w, h))
        self._frame_pos = (x, y)

    # ── Rendering ─────────────────────────────────────────

    def render(self, surface):
        self._render_background(surface)
        self._render_panels(surface)
        self._render_list(surface)
        self._render_sidebar(surface)
        self._render_buttons(surface)
        self._render_frame_image(surface)
        self._render_title(surface)

    def _render_frame_image(self, surface):
        if self._frame_scaled is not None:
            surface.blit(self._frame_scaled, self._frame_pos)
        elif self.USE_FRAME:
            self._render_frame(surface)

    def _render_title(self, surface):
        cfg = self._data.get("frame", {})
        rect = cfg.get("title_rect")
        title = cfg.get("title", self.FRAME_TITLE)
        if not rect or not title:
            return
        x, y, w, h = self.layout.rect(rect)
        font = self.style.get_font(self.layout.font_size(
            cfg.get("title_font", 30)))
        text = font.render(title.upper(), True, TITLE_COLOR[:3])
        surface.blit(text, (x + (w - text.get_width()) // 2,
                            y + (h - text.get_height()) // 2))

    def _render_panels(self, surface):
        """Every cutout that shows content gets the panel fill, so the
        frame never sits over raw background."""
        for name in self._data.get("panels", {}):
            if name.startswith("_"):
                continue
            box = self.box_rect(name)
            if box:
                surface.fill(PANEL_BG[:3], pygame.Rect(*self.layout.rect(box)))

    def _render_list(self, surface):
        """The colony list. The bar is an INVENTION — see colonylist.

        Read-only: the rows come out of the snapshot and nothing here
        sends anything to the game. Static for now, by design; the
        hover band and the draggable dividers belong on a picture
        somebody already believes.
        """
        box = self.box_rect("list_area")
        if not box:
            return
        cfg = self._data.get("list", {})
        rows = colonylist.build_rows(self._state, self._sort_key)
        colonylist.render(surface, rows,
                          pygame.Rect(*self.layout.rect(box)),
                          cfg, self.layout, self.style)

    def _render_sidebar(self, surface):
        """Six empire lines, label over value, evenly stacked in the
        sidebar cutout — COLSUM::Draw_Empire_Info_ transcribed."""
        box = self.box_rect("sidebar")
        cfg = self._data.get("empire", {})
        rows = cfg.get("rows", [])
        if not box or not rows:
            return
        rect = pygame.Rect(*self.layout.rect(box))
        surface.fill(PANEL_BG[:3], rect)
        fs = self.box_font_scale("sidebar")
        label_size = self.layout.font_size(int(cfg.get("label_font", 18) * fs))
        value_size = self.layout.font_size(int(cfg.get("value_font", 26) * fs))
        pad = int(rect.h * cfg.get("row_pad", 0.10))
        row_h = (rect.h - 2 * pad) / len(rows)
        for i, row in enumerate(rows):
            top = rect.y + pad + int(i * row_h)
            label = self.style.render_text(row["label"].upper(), label_size,
                                           LABEL_COLOR[:3])
            value, warn = self._empire_value(row)
            # render_text, not font.render: the sign characters are on
            # Bank Gothic DEMO's watermark list and get substituted.
            vt = self.style.render_text(
                value, value_size, (WARN_COLOR if warn else VALUE_COLOR)[:3])
            block_h = label.get_height() + vt.get_height()
            y = top + (int(row_h) - block_h) // 2
            surface.blit(label, (rect.centerx - label.get_width() // 2, y))
            surface.blit(vt, (rect.centerx - vt.get_width() // 2,
                              y + label.get_height()))

    def _empire_value(self, row):
        """(text, warn). '--' while disconnected, never a fake zero."""
        if self._local is None:
            return "--", False
        value = getattr(self._local, row["field"], None)
        if value is None:
            return "--", False
        warn = bool(row.get("warn_negative")) and value < 0
        return format_value(value, row.get("signed", False)), warn

    def _render_buttons(self, surface):
        """Sort buttons and RETURN: the frame provides the bezel, so
        each box gets a fill plus its label; hover brightens it and
        the active sort key stays lit."""
        mouse = mouse_input.pos()
        specs = [(f"sort_{b['key']}", b["label"], b["key"] == self._sort_key)
                 for b in self._data.get("sort", {}).get("buttons", [])]
        specs.append(("return",
                      self._data.get("return", {}).get("label", "Return"),
                      False))
        for name, label, active in specs:
            box = self.box_rect(name)
            if not box:
                continue
            rect = pygame.Rect(*self.layout.rect(box))
            hovered = rect.collidepoint(mouse)
            fill = NAV_HOVER_BG if hovered else (
                NAV_ACTIVE_BG if active else NAV_BG)
            surface.fill(fill[:3], rect)
            font = self.style.get_font(self.layout.font_size(
                self.box_style(name).get("font_size", 18)))
            text = font.render(label.upper(), True, NAV_TEXT[:3])
            surface.blit(text, (rect.x + (rect.w - text.get_width()) // 2,
                                rect.y + (rect.h - text.get_height()) // 2))

    def box_style(self, name):
        for box in self.boxes:
            if box.name == name:
                return box.style
        return {}

    # ── Input ─────────────────────────────────────────────

    def handle_click(self, screen_x, screen_y):
        for spec in self._data.get("sort", {}).get("buttons", []):
            if self._hit(f"sort_{spec['key']}", screen_x, screen_y):
                self._sort_key = spec["key"]
                self._inject(spec.get("native_click"), f"sort {spec['key']}")
                return None
        if self._hit("return", screen_x, screen_y):
            self._inject(self._data.get("return", {}).get("native_click"),
                         "return")
            return None
        return super().handle_click(screen_x, screen_y)

    def _hit(self, name, x, y):
        box = self.box_rect(name)
        return bool(box) and pygame.Rect(*self.layout.rect(box)).collidepoint(x, y)

    def _inject(self, point, what):
        """Click the original at a point inside one of its buttons."""
        if not point:
            log.warning("No native click point for %s", what)
            return
        nx, ny = point
        if not (0 <= nx < NATIVE_W and 0 <= ny < NATIVE_H):
            log.warning("Native point off screen for %s: %s", what, point)
            return
        log.info("Action: %s -> native click (%d, %d)", what, nx, ny)
        if self.app.connected:
            self.app.client.inject_click(nx, ny)
