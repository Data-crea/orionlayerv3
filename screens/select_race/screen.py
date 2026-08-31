"""Select Race Screen — Portrait grid layout with info panel.

Normal mode (select_race):
  Left:   5x3 portrait grid (13 races + Custom Race as 14th cell)
  Right:  Race name, subtitle, description, Race Traits

Picture mode (select_picture):
  Full:   5x3 portrait grid only (no info panel)
  Bottom: Back / Accept buttons

Custom Race is the 14th grid entry (id=13) with its own portrait.
All positions come from boxes.json (editable with F5).
"""
import json
import os
import logging
import time
import pygame
from core.screen_base import ScreenBase

log = logging.getLogger("select_race")
from screens.select_race.renderer import render_race_grid, grid_cell_rect
from screens.select_race.info_panel import (
    render_race_name, render_race_description, render_race_traits,
)


class SelectRaceScreen(ScreenBase):
    SCREEN_NAME = "select_race"
    GAME_SCREEN_ID = 6      # SCREEN_RACE
    USE_FRAME = True
    FRAME_TITLE = "Select Race"
    FRAME_BTN_LEFT = None
    FRAME_BTN_RIGHT = None
    FRAME_VARIANT = "select_race"

    MODE_SELECT_RACE = "select_race"
    MODE_SELECT_PICTURE = "select_picture"

    def __init__(self, app):
        super().__init__(app)
        self._races = []
        self._selected_id = 9   # default: Psilon
        self._portraits = {}
        self._desc_scroll = 0
        self._mode = self.MODE_SELECT_RACE
        self._thumb_cache = {}
        self._custom_portrait_id = 0  # portrait index for custom race
        self._picture_mode_time = 0   # when picture mode was entered
        self._pending_picture_mode = False  # deferred picture mode entry

    def enter(self, game_state=None):
        super().enter(game_state)
        self._load_races()
        self._load_portraits()
        self._thumb_cache.clear()
        self._mode = self.MODE_SELECT_RACE  # always start in normal mode
        self._pending_picture_mode = False
        self._apply_mode()

    def _load_races(self):
        """Race data, mod-overridable (screens/select_race/races.json)."""
        data = self.app.res.load_json("screens/select_race/races.json")
        if data:
            self._races = data

    def _load_portraits(self):
        """Load portrait images. Uses 'key' field or lowercase name."""
        self._portraits.clear()
        for race in self._races:
            key = race.get("key", race["name"].lower())
            for ext in (".png", ".jpg", ".webp"):
                # Per-file mod resolution: a mod can replace a
                # single portrait without copying the others.
                path = self.asset_path("assets", "portraits", key + ext)
                if path:
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        self._portraits[race["id"]] = img
                    except Exception:
                        pass
                    break

    def set_mode(self, mode):
        self._mode = mode
        if mode == self.MODE_SELECT_PICTURE:
            self._picture_mode_time = time.monotonic()
        self._apply_mode()

    def _apply_mode(self):
        if self._mode == self.MODE_SELECT_PICTURE:
            self.FRAME_TITLE = "Select Race Picture"
        else:
            self.FRAME_TITLE = "Select Race"

    @property
    def is_picture_mode(self):
        return self._mode == self.MODE_SELECT_PICTURE

    def update(self, game_state=None):
        """Handle deferred picture mode and timeout.

        Picture mode is NOT entered immediately on Custom Race click.
        Instead, _pending_picture_mode is set. On the next frame:
        - If the game is still on screen 6 → enter picture mode
          (game stayed in picture-select, case A)
        - If the game moved to screen 50 → dispatcher handles switch,
          pending flag is cleared in enter() on re-entry (case B)

        No timeout here: picture mode is only left via portrait
        click (game moves to 50) or ESC.
        """
        if self._pending_picture_mode:
            screen = game_state.current_screen if game_state else -1
            if screen == 6:
                # Game stayed on race selection → picture mode confirmed
                self._pending_picture_mode = False
                self.set_mode(self.MODE_SELECT_PICTURE)
            elif screen == 50:
                # Game already entered Custom Race → dispatcher will switch
                self._pending_picture_mode = False


    def _race_by_id(self, rid):
        for r in self._races:
            if r["id"] == rid:
                return r
        return None

    def on_resize(self):
        super().on_resize()
        self._thumb_cache.clear()

    # ── Rendering ─────────────────────────────────────────

    def render(self, surface):
        self._render_background(surface)
        L = self.layout
        race = self._race_by_id(self._selected_id)
        pic = self.is_picture_mode

        # Panel skins. Picture mode hides the info panel and its three
        # content boxes; the grid stays and keeps its own frame.
        _skip_picture = {"info_panel", "race_name",
                         "race_description", "race_traits"}
        for box in self.boxes:
            if box.style.get("skin") in ("inner_panel", "thin_border"):
                if pic and box.name in _skip_picture:
                    continue
                box.render(surface, self.layout, self.style)

        # Portrait grid (14 entries: 13 races + Custom Race)
        gr = self.box_rect("race_grid")
        if gr:
            render_race_grid(surface, L, self.style, self._races,
                             self._selected_id, gr,
                             self._portraits, self._thumb_cache,
                             self.box_font_scale("race_grid"),
                             picture_mode=pic)

        # Info panel content (normal mode only)
        if not pic and race:
            nr = self.box_rect("race_name")
            if nr:
                render_race_name(surface, L, self.style, race, nr,
                                 self.box_font_scale("race_name"))

            dr = self.box_rect("race_description")
            if dr:
                render_race_description(surface, L, self.style, race,
                                        dr, self._desc_scroll,
                                        self.box_font_scale("race_description"))

            tr = self.box_rect("race_traits")
            if tr:
                render_race_traits(surface, L, self.style, race, tr,
                                   self.box_font_scale("race_traits"))

        # Frame overlay
        if self.USE_FRAME:
            self._render_frame(surface)

    # ── Input ─────────────────────────────────────────────

    def _race_at_screen_pos(self, screen_x, screen_y):
        """Return race id under cursor in the grid, or None."""
        L = self.layout
        gr = self.box_rect("race_grid")
        if not gr:
            return None
        for i, race in enumerate(self._races):
            cell = grid_cell_rect(gr, i)
            if cell is None:
                continue
            cx, cy, cw, ch = cell
            sx, sy = L.pos(cx, cy)
            sw, sh = L.size(cw, ch)
            if pygame.Rect(sx, sy, sw, sh).collidepoint(screen_x, screen_y):
                return race["id"]
        return None

    def handle_mouse_motion(self, screen_x, screen_y):
        super().handle_mouse_motion(screen_x, screen_y)
        rid = self._race_at_screen_pos(screen_x, screen_y)
        if rid is not None and rid != self._selected_id:
            self._selected_id = rid
            self._desc_scroll = 0

    def handle_click(self, screen_x, screen_y):
        rid = self._race_at_screen_pos(screen_x, screen_y)
        if rid is None:
            return
        self._activate_race(rid)

    def _activate_race(self, rid):
        """Select + confirm a race. Shared by mouse click and ENTER
        so both paths keep the HD side in sync with the game."""
        self._selected_id = rid
        self._desc_scroll = 0

        if not self.app.connected:
            return

        if self.is_picture_mode:
            # Picture mode: only stock race portraits (0-12) are valid
            if rid == 13 or rid > 12:
                return
            self._custom_portrait_id = rid
            log.info("Custom portrait selected: %d (%s)",
                     rid, self._race_by_id(rid)["name"])
            # The game is in ITS picture-select state (we sent the
            # Custom click on entering this mode). Clicking the
            # chosen portrait's radio confirms the picture and
            # opens Racial_Option_Screen_. The _current_screen patch
            # (screen 50) triggers auto-routing via the dispatcher.
            self._inject_race_click(rid)
            return

        if rid == 13:
            # Custom Race: send click on the Custom radio button.
            # Two outcomes depending on game state:
            # A) _custom_flag was 0 → game enters picture-select mode
            #    (stays on screen 6) → we enter picture mode next frame
            # B) _custom_flag was 1 → game enters Racial_Option_Screen_
            #    directly (screen 50) → dispatcher handles the switch
            # We defer picture mode to update() so we don't desync.
            self._inject_race_click(13)
            self._pending_picture_mode = True
            self._selected_id = 0
            return

        # Stock race: single click → inject click on radio button.
        # orion2re goes directly to Enter Ruler Name and keeps
        # reporting screen 6 through all three dialogs. Show the
        # merged HD screen on top (same as after Custom Race Accept);
        # its Accept runs the injection chain (ruler → banner → home
        # star), then the game lands on the Galaxy Map (ID 0) and
        # the lock releases. Cancel sends ESC → back to screen 6 →
        # dispatcher returns here.
        log.info("Race selected: %d (%s)",
                 rid, self._race_by_id(rid)["name"])
        self._inject_race_click(rid)
        self.app.dispatcher.switch_to("empire_identity", lock_ids=(6,))

    def _inject_race_click(self, race_id):
        """Send INJECT_CLICK on the 640x480 radio button for a race."""
        if race_id < 7:
            col_x = (351 + 473) // 2
            row = race_id
        else:
            col_x = (477 + 599) // 2
            row = race_id - 7
        y = 90 + row * 48 + 24
        self.app.client.inject_click(col_x, y)

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            if self.is_picture_mode:
                # Bring the GAME back out of its picture-select
                # state as well, then mirror in HD.
                # NOTE: inject_key(ESC) can cascade across
                # sub-screens (documented learning) — needs a live
                # test here; if it also exits race selection, we
                # need a different back mechanism.
                if self.app.connected:
                    self.app.client.inject_key(pygame.K_ESCAPE)
                self.set_mode(self.MODE_SELECT_RACE)
            elif self.app.connected:
                self.app.client.inject_click(162, 445)
        elif key == pygame.K_RETURN:
            # Same path as a click: keeps HD and game in sync
            # (stock race → empire_identity, Custom → deferred
            # picture mode, picture mode → confirm portrait).
            self._activate_race(self._selected_id)
        else:
            super().handle_key(key)

    def handle_mousewheel(self, direction, mx, my):
        """Scroll description text."""
        if self.is_picture_mode:
            return
        dr = self.box_rect("race_description")
        if not dr:
            return
        L = self.layout
        dx, dy = L.pos(dr[0], dr[1])
        dw, dh = L.size(dr[2], dr[3])
        if pygame.Rect(dx, dy, dw, dh).collidepoint(mx, my):
            scroll_step = int(24 * L.scale)
            self._desc_scroll -= direction * scroll_step
            self._desc_scroll = max(0, self._desc_scroll)

    def _invalidate_thumb(self, race_id):
        """Remove cached thumbnails for a race so they regenerate."""
        keys = [k for k in self._thumb_cache if k[0] == race_id]
        for k in keys:
            del self._thumb_cache[k]

    def save_races(self):
        path = os.path.join(self._screen_dir, "races.json")
        with open(path, "w") as f:
            json.dump(self._races, f, indent=2)
