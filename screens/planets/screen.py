"""Planets Screen — orion2re SCREEN_PLANET_SUMMARY (id 32).

`PLNTSUM::Planet_Summary_Screen_` (plntsum.cpp:1931). Brief 101, built
from Data's frame3 and mockup3, 13 September 2026.

What drives the game from here, and how (decision 20):
  RETURN        ACTIVATE_FIELD on the esc button, found in the live field
                list by its 0x1B hotkey (plntsum.cpp:724-731)
  sort keys     INJECT_CLICK at `native_click` — multi-button fields are
                type 3, which ACTIVATE_FIELD does not take
  restrictions  INJECT_KEY "1".."5", the radio fields' own hotkeys, with
                `native_click` as the fallback

What is local and sends nothing: the list, its scroll window (decision
46), the hover, the star click in the inset, the bottom windows. The two
send buttons are DISPLAY ONLY — sending ships is its own brief (decision
21). The Planets In Range toggle drives the game and the HD list does not
filter on it: a marked gap (`planetrows.FILTER_GAPS`).

The rows, the order and the words are `planetrows` and `planetwords`; the
drawing is `planetdraw`; this file owns the boxes, the input and the wire.
"""
import logging

import pygame

from core import mouse as mouse_input
from core.config import REF_W, REF_H
from core.screen_base import ScreenBase
from core.shipparts import ShipPartNames
from screens.colony_summary import colonyrows

from . import monsterpanel, planetdraw, planetrows, planetwords

log = logging.getLogger("planets")

NATIVE_W, NATIVE_H = 640, 480
#: The native box the inset stars are computed for (plntsum.cpp:1351).
INSET_NATIVE = (443, 17, 180, 116)
KEY_ESC = 27


class PlanetsScreen(ScreenBase):
    SCREEN_NAME = "planets"
    GAME_SCREEN_ID = 32         # SCREEN_PLANET_SUMMARY, orion2_consts.h:487
    USE_FRAME = False

    def __init__(self, app):
        super().__init__(app)
        self._data = {}
        self._frame = None
        self._frame_scaled = None
        self._frame_pos = (0, 0)
        self._state = None
        self._view = None
        self._list = planetrows.PlanetList()
        self._filters = {key: False for key in planetrows.FILTERS}
        self._words = None
        self._first = 0
        self._hover = None          # list index under the pointer, or None
        self._selected = None       # planet index of the scanned row
        self._scanned = None        # star index + 1000, MOX::_scanned_field
        self._parts = None          # ship part names, core.shipparts
        self._monster_sprites = {}  # owner -> panel sprite or None
        self._monster_scaled = {}   # the one scaled copy on screen

    # ── Lifecycle ─────────────────────────────────────────

    def enter(self, game_state=None):
        super().enter(game_state)
        self._data = self.app.res.load_json(
            "screens/planets/layout.json", {}) or {}
        language = (getattr(self.app, "settings", {}) or {}).get(
            "language", "en")
        self._words = planetwords.Words.load(
            language, self._data.get("words", {}).get("food", "%s Food"))
        self._parts = ShipPartNames(language)
        self._list = planetrows.PlanetList(
            self._data.get("sort", {}).get("default", "climate"))
        # MOX::_scanned_field = -1 on entry (plntsum.cpp:1945).
        self._first, self._hover = 0, None
        self._selected = self._scanned = None
        self._load_frame()
        self.update(game_state)
        self._push_sort_key()

    def update(self, game_state=None):
        if game_state is None:
            return
        self._state = game_state
        self._view = planetrows.View(game_state)
        if self._list.refresh(self._view, self._filters):
            self._clear_scanned()
        self._clamp_after_filter()

    def on_resize(self):
        super().on_resize()
        self._scale_frame()

    def _push_sort_key(self):
        """Impose the HD sort key on the game once, on entry — the colony
        summary's trade; a click on the key the game already holds changes
        nothing (plntsum.cpp:2013-2018)."""
        for spec in self._data.get("sort", {}).get("buttons", []):
            if spec["key"] == self._list.sort_key:
                self._inject(spec, f"entry sort {spec['key']}")

    # ── State helpers ─────────────────────────────────────

    @property
    def visible(self):
        return int(self._data.get("list", {}).get("row_count", 8))

    def _clear_scanned(self):
        self._scanned = None
        self._selected = None

    def _clamp_after_filter(self):
        """plntsum.cpp:2022-2028, after a filter click."""
        total = len(self._list.rows)
        if total < self.visible:
            self._first = 0
        elif total < self._first + self.visible:
            self._first = total - self.visible

    def _cells(self):
        if self._view is None or self._words is None:
            return []
        return [planetwords.cells(self._view, row, self._words)
                for row in self._list.rows]

    def _selected_row(self):
        for row in self._list.rows:
            if row["index"] == self._selected:
                return row
        return None

    def _inset_stars(self):
        if self._state is None:
            return []
        return colonyrows.galaxy_inset_stars(self._state, INSET_NATIVE)

    def _send_available(self, hotkey):
        """A send button is available exactly when the game added its
        hidden field (plntsum.cpp:703-713)."""
        fields = getattr(self._state, "fields", None) or []
        return any(f.hotkey in (ord(hotkey.upper()), ord(hotkey.lower()))
                   for f in fields)

    # ── Frame ─────────────────────────────────────────────

    def _load_frame(self):
        path = self.asset_path("assets", self._data.get("frame", {}).get(
            "image", "frame.png"))
        self._frame = pygame.image.load(path).convert_alpha() if path else None
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
        planetdraw.fill_panels(self, surface)
        cells = self._cells()
        rows = self._list.rows
        planetdraw.render_list(self, surface, rows, cells, self._first,
                               self._hover, self._selected)
        planetdraw.render_scroll(self, surface, len(rows), self._first,
                                 self.visible)
        stars = self._inset_stars()
        planetdraw.render_inset(self, surface, stars, self._marker())
        planetdraw.render_status(self, surface, planetwords.status_line(
            self._view, self._scanned, self._words)
            if self._view is not None else None)
        self._render_controls(surface)
        row = self._selected_row()
        if row is not None:
            planetdraw.render_planet_panel(
                self, surface, row,
                planetwords.cells(self._view, row, self._words)["planet"])
        monsterpanel.render(self, surface, row)
        if self._frame_scaled is not None:
            surface.blit(self._frame_scaled, self._frame_pos)
        self.render_help(surface)

    def _marker(self):
        if self._scanned is None or self._view is None:
            return None
        index = self._scanned - 1000
        if not 0 <= index < len(self._view.stars):
            return None
        owner = int(self._view.stars[index].owner)
        player = self._view.player(owner) if 0 <= owner < 8 else None
        return index, planetdraw.row_color(
            {"owner_color": player.color if player is not None else None},
            False)

    def _render_controls(self, surface):
        mouse = mouse_input.pos()
        words = self._data.get("words", {})
        planetdraw.render_heading(self, surface, "sort_heading",
                                  words.get("sort_heading"))
        planetdraw.render_heading(self, surface, "restrict_heading",
                                  words.get("restrict_heading"))
        for spec in self._data.get("sort", {}).get("buttons", []):
            planetdraw.render_control(self, surface, "sort_" + spec["key"],
                                      spec["label"],
                                      active=spec["key"] == self._list.sort_key,
                                      mouse=mouse)
        for spec in self._data.get("restrictions", {}).get("buttons", []):
            planetdraw.render_control(self, surface, "restrict_" + spec["key"],
                                      spec["label"],
                                      active=self._filters[spec["key"]],
                                      mouse=mouse)
        send = self._data.get("send", {})
        for key in ("colony", "outpost"):
            spec = send.get(key, {})
            planetdraw.render_control(
                self, surface, "send_" + key, spec.get("label"),
                enabled=self._send_available(spec.get("hotkey", "?")),
                mouse=mouse)
        planetdraw.render_control(self, surface, "return",
                                  self._data.get("return", {}).get("label"),
                                  mouse=mouse)

    # ── Input ─────────────────────────────────────────────

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        pos = (screen_x, screen_y)
        up, down = planetdraw.scroll_arrows(self)
        if up and up.collidepoint(pos):
            return self._scroll(-1)
        if down and down.collidepoint(pos):
            return self._scroll(1)
        for spec in self._data.get("sort", {}).get("buttons", []):
            if self._hit("sort_" + spec["key"], pos):
                if spec["key"] != self._list.sort_key:
                    self._list.sort(spec["key"])
                    self._clear_scanned()       # plntsum.cpp:2016
                self._inject(spec, f"sort {spec['key']}")
                return None
        for spec in self._data.get("restrictions", {}).get("buttons", []):
            if self._hit("restrict_" + spec["key"], pos):
                self._filters[spec["key"]] = not self._filters[spec["key"]]
                if self._view is not None and self._list.refresh(
                        self._view, self._filters):
                    self._clear_scanned()
                self._clamp_after_filter()
                self._inject(spec, f"restriction {spec['key']}")
                return None
        for key in ("colony", "outpost"):
            if self._hit("send_" + key, pos):
                log.info("Send %s ship: not built in brief 101 — the send "
                         "chain is its own brief (decision 21)", key)
                return None
        if self._hit("return", pos):
            self._return()
            return None
        star = planetdraw.inset_star_at(self, self._inset_stars(), *pos)
        if star is not None:
            self._star_click(star)
            return None
        # A row click is swallowed: with no armed send the original does
        # nothing with it (Scan_Summary_Box_Fields_, plntsum.cpp:1284-1295).
        return None

    def _star_click(self, star):
        """plntsum.cpp:2052-2064: only with more than eight rows."""
        if len(self._list.rows) <= self.visible:
            return
        row = self._list.first_row_of_star(star)
        if row <= -1:
            log.info("Star %d has no planet in the list; the original's "
                     "warning box (H 0x14F) is not built", star)
            return
        self._first = row

    def _scroll(self, step):
        """The up/down buttons move one row when there are more than eight
        (plntsum.cpp:2030-2038), clamped at both ends."""
        total = len(self._list.rows)
        if total > self.visible:
            self._first = max(0, min(total - self.visible, self._first + step))
        return None

    def _return(self):
        fields = getattr(self._state, "fields", None) or []
        field = next((f for f in fields if f.hotkey == KEY_ESC), None)
        if field is not None:
            log.info("Action: return (field %s)", field.index)
            if self.app.connected:
                self.app.client.activate_field(field.index)
            return
        log.warning("No esc field in the field list; sending the key")
        if self.app.connected:
            self.app.client.inject_key(KEY_ESC)

    def handle_mouse_motion(self, screen_x, screen_y):
        super().handle_mouse_motion(screen_x, screen_y)
        pos = (screen_x, screen_y)
        area = planetdraw.window(self, "rows")
        self._hover = None
        if area and area.collidepoint(pos):
            band = (screen_y - area.y) * self.visible // max(1, area.height)
            index = self._first + band
            if 0 <= index < len(self._list.rows):
                row = self._list.rows[index]
                self._hover = index
                self._selected = row["index"]
                self._scanned = row["star"] + 1000   # plntsum.cpp:1314
            return
        star = planetdraw.inset_star_at(self, self._inset_stars(), *pos)
        if star is not None:
            self._scanned = star + 1000               # plntsum.cpp:2066-2068

    def handle_mousewheel(self, direction, mx, my):
        """HD EXTENSION (layout.json list._hd_extension_wheel): one row per
        notch over the list or its scroll column. Sends nothing."""
        if super().handle_mousewheel(direction, mx, my):
            return True
        if not (self._hit("rows", (mx, my)) or self._hit("scroll", (mx, my))):
            return False
        self._scroll(-direction)
        return True

    def _hit(self, name, pos):
        rect = planetdraw.window(self, name)
        return bool(rect) and rect.collidepoint(pos)

    def _inject(self, spec, what):
        """Hotkey first, native click as the fallback (colony_summary's
        `_inject`, whose docstring carries the live verification)."""
        hotkey = (spec or {}).get("hotkey")
        if isinstance(hotkey, str) and len(hotkey) == 1:
            log.info("Action: %s -> hotkey %r", what, hotkey)
            if self.app.connected:
                self.app.client.inject_key(ord(hotkey))
            return
        point = (spec or {}).get("native_click")
        if not point or not (0 <= point[0] < NATIVE_W
                             and 0 <= point[1] < NATIVE_H):
            log.warning("No usable native click for %s: %s", what, point)
            return
        log.info("Action: %s -> native click %s", what, point)
        if self.app.connected:
            self.app.client.inject_click(*point)
