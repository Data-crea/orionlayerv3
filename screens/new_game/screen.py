"""New Game Screen — Settings display with transparent background cutouts.

Rendering order:
  1. Black fill
  2. Setting images at their cutout slots
  3. Background PNG on top (transparent cutouts reveal settings)
  4. Category titles above each cutout
  5. Dynamic value labels below each cutout
  6. Toggle buttons (blue=on, dark=off) with labels
  7. Frame overlay
  8. Status line

All positions live in layout.json (v2 hd-space, 3440x1440) and are
converted to screen coordinates via the background's cover-scale
transform — mod-overridable like every other data file.

Input routing:
  Settings (type=7 click-through) -> ACTIVATE_FIELD
  Toggles (type=1 radio buttons)  -> INJECT_CLICK (only exception)
  Accept/Cancel (type=0 buttons)  -> ACTIVATE_FIELD via frame bars
  ESC                             -> inject_key
"""
import pygame
from core import palette
from core.screen_base import ScreenBase

TOGGLE_LABEL_COLOR = palette.col("new_game", "toggle_label", (160, 180, 210))
TITLE_COLOR = palette.col("new_game", "category_title", (160, 180, 210))
LABEL_COLOR = palette.col("new_game", "value_label", (100, 210, 210))

# GameState attribute per category / toggle
STATE_ATTRS = {
    "difficulty": "ng_difficulty", "galaxy_size": "ng_galaxy_size",
    "galaxy_age": "ng_galaxy_age", "players": "ng_opponents",
    "tech_level": "ng_tech_level",
}
TOGGLE_ATTRS = {
    "tactical_combat": "ng_tactical_combat",
    "random_events": "ng_random_events",
    "antarans_attack": "ng_antarans",
}


class NewGameScreen(ScreenBase):
    SCREEN_NAME = "new_game"
    GAME_SCREEN_ID = 13     # SCREEN_NEW_GAME
    USE_FRAME = True
    FRAME_TITLE = "New Game"
    FRAME_BTN_LEFT = ("Cancel", 14)
    FRAME_BTN_RIGHT = ("Accept", 15)

    def __init__(self, app):
        super().__init__(app)
        self._cfg = {}           # layout.json contents
        self._bg_orig = None
        self._bg_screen = None
        self._bg_scale = 1.0
        self._bg_crop_x = 0.0
        self._bg_crop_y = 0.0
        self._hd2i_x = 1.0       # hd (3440x1440) -> bg image factors
        self._hd2i_y = 1.0
        self._setting_imgs = {}
        self._current = {}       # category -> image filename
        self._labels = {}        # category -> display label
        self._toggle_on = None
        self._toggle_off = None
        self._toggle_states = {}
        self._scaled_cache = {}

    def enter(self, game_state=None):
        self._load_layout_cfg()
        super().enter(game_state)   # boxes, layout, background override
        self._load_toggle_buttons()
        self._preload_setting_images()
        self._current = {}
        self._labels = {}
        self._toggle_states = {}
        self._scaled_cache.clear()

    def exit(self):
        super().exit()
        self._bg_orig = None
        self._bg_screen = None
        self._setting_imgs.clear()
        self._scaled_cache.clear()
        self._toggle_on = None
        self._toggle_off = None

    # ── Config / loading ─────────────────────────────────────

    def _load_layout_cfg(self):
        self._cfg = self.app.res.load_json(
            "screens/new_game/layout.json", {})
        img_w, img_h = self._cfg.get("background_image_size",
                                     [1937, 812])
        self._hd2i_x = img_w / 3440
        self._hd2i_y = img_h / 1440

    def _load_background(self):
        """Override ScreenBase: cutout background needs its own
        cover-scale that keeps scale/crop factors for _hd_to_screen."""
        path = self.asset_path("assets", "background.png")
        if path:
            self._bg_orig = pygame.image.load(path).convert_alpha()
            self._scale_background()

    def _scale_background(self):
        if not self._bg_orig:
            return
        win_w, win_h = self.app.win_w, self.app.win_h
        img_w, img_h = self._bg_orig.get_size()
        self._bg_scale = max(win_w / img_w, win_h / img_h)
        sw = int(img_w * self._bg_scale)
        sh = int(img_h * self._bg_scale)
        self._bg_crop_x = (sw - win_w) / 2
        self._bg_crop_y = (sh - win_h) / 2
        scaled = pygame.transform.smoothscale(self._bg_orig, (sw, sh))
        cx, cy = int(self._bg_crop_x), int(self._bg_crop_y)
        self._bg_screen = scaled.subsurface(
            (cx, cy, win_w, win_h)).copy()
        self._scaled_cache.clear()

    def _load_toggle_buttons(self):
        on_path = self.asset_path("assets", "toggle_on.png")
        off_path = self.asset_path("assets", "toggle_off.png")
        if on_path:
            self._toggle_on = pygame.image.load(on_path).convert_alpha()
        if off_path:
            self._toggle_off = pygame.image.load(off_path).convert_alpha()

    def _preload_setting_images(self):
        """Load ALL setting images up front so render never blocks on disk I/O."""
        cats = self._cfg.get("categories", {})
        for cat, info in cats.items():
            for val_key, entry in info.get("values", {}).items():
                filename = entry.get("image")
                if filename:
                    self._get_setting_image(cat, filename)

    def _get_setting_image(self, category, filename):
        key = f"{category}/{filename}"
        if key not in self._setting_imgs:
            path = self.asset_path("assets", category, f"{filename}.png")
            self._setting_imgs[key] = (
                pygame.image.load(path).convert() if path else None)
        return self._setting_imgs[key]

    def _get_scaled(self, surf, w, h):
        key = (id(surf), w, h)
        if key not in self._scaled_cache:
            self._scaled_cache[key] = (
                pygame.transform.smoothscale(surf, (w, h)))
        return self._scaled_cache[key]

    # ── Coordinate transform ─────────────────────────────────

    def _hd_to_screen(self, hd_x, hd_y, hd_w=0, hd_h=0):
        """Convert v2 hd coords (3440x1440) -> screen pixels."""
        s = self._bg_scale
        cx, cy = self._bg_crop_x, self._bg_crop_y
        ix, iy = hd_x * self._hd2i_x, hd_y * self._hd2i_y
        iw, ih = hd_w * self._hd2i_x, hd_h * self._hd2i_y
        return (int(ix * s - cx), int(iy * s - cy),
                int(iw * s), int(ih * s))

    def _hd_rect(self, hd_tuple):
        return pygame.Rect(*self._hd_to_screen(*hd_tuple))

    def _hd_font_size(self, hd_size):
        return max(8, int(hd_size * self._hd2i_y * self._bg_scale))

    def _toggle_icon_rect(self, index):
        """hd rect of toggle icon number `index` (from layout.json)."""
        t = self._cfg.get("toggles", {})
        size = t.get("icon_size", 80)
        return (t.get("x", 2186),
                t.get("y0", 830) + index * t.get("dy", 105),
                size, size)

    # ── Update ───────────────────────────────────────────────

    def update(self, game_state=None):
        if not game_state:
            return
        cats = self._cfg.get("categories", {})
        self._current = {}
        self._labels = {}
        for cat, attr in STATE_ATTRS.items():
            value = getattr(game_state, attr, None)
            entry = cats.get(cat, {}).get("values", {}).get(str(value))
            if entry:
                self._current[cat] = entry.get("image")
                self._labels[cat] = entry.get("label", "")
        # Toggle states: non-zero = ON (blue), 0 = OFF (dark).
        # Polarity verified by live test 24 Aug 2026 (previous
        # assumption "0 = ON" was inverted).
        self._toggle_states = {
            name: getattr(game_state, attr, 0) != 0
            for name, attr in TOGGLE_ATTRS.items()
        }

    # ── Render ───────────────────────────────────────────────

    def render(self, surface):
        surface.fill((6, 8, 16))
        if not self._bg_screen:
            return
        slots = self._cfg.get("setting_slots", {})
        cats = self._cfg.get("categories", {})
        text_cfg = self._cfg.get("text", {})

        # 1. Setting images (under background cutouts)
        for cat, slot in slots.items():
            filename = self._current.get(cat)
            img = (self._get_setting_image(cat, filename)
                   if filename else None)
            if not img:
                continue
            sx, sy, sw, sh = self._hd_to_screen(*slot["rect"])
            if sw > 0 and sh > 0:
                surface.blit(self._get_scaled(img, sw, sh), (sx, sy))

        # 2. Background with transparent cutouts
        surface.blit(self._bg_screen, (0, 0))

        # 3. Boxes (inner panels etc. from editor)
        for box in self.boxes:
            box.render(surface, self.layout, self.style)

        # 4. + 5. Category titles / dynamic value labels
        tfont = self.style.get_font(self._hd_font_size(
            text_cfg.get("title_font_size", 36)))
        lfont = self.style.get_font(self._hd_font_size(
            text_cfg.get("label_font_size", 38)))
        title_dy = text_cfg.get("title_dy", 55)
        label_dy = text_cfg.get("label_dy", 30)
        for cat, slot in slots.items():
            rect = slot["rect"]
            center_x = rect[0] + rect[2] // 2
            title = cats.get(cat, {}).get("title", "")
            if title:
                tx, ty, _, _ = self._hd_to_screen(
                    center_x, rect[1] - title_dy)
                surf = tfont.render(title.upper(), True, TITLE_COLOR)
                surface.blit(surf, (tx - surf.get_width() // 2, ty))
            label = self._labels.get(cat, "")
            if label:
                lx, ly, _, _ = self._hd_to_screen(
                    center_x, rect[1] + rect[3] + label_dy)
                surf = lfont.render(label, True, LABEL_COLOR)
                surface.blit(surf, (lx - surf.get_width() // 2, ly))

        # 6. Toggle buttons
        self._render_toggles(surface)

        # 7. Frame overlay
        if self.USE_FRAME:
            self._render_frame(surface)

        # 8. Status line (after frame so it's not covered)
        font = self.style.get_font(
            max(8, int(14 * self.app.win_h / 1080)))
        col = self.colors.get("text", {}).get(
            "secondary", [120, 135, 170])
        info = ("New Game  |  Click settings to cycle"
                "  |  ESC \u2192 Main Menu")
        text = font.render(info, True, tuple(col[:3]))
        surface.blit(text, (10, self.app.win_h - 24))

        # 9. Right-click help, above everything including the frame.
        self.render_help(surface)

    def _render_toggles(self, surface):
        t = self._cfg.get("toggles", {})
        lfont = self.style.get_font(self._hd_font_size(
            t.get("label_font_size", 32)))
        labels = t.get("labels", {})
        for i, name in enumerate(t.get("order", [])):
            is_on = self._toggle_states.get(name, False)
            btn_img = self._toggle_on if is_on else self._toggle_off
            if not btn_img:
                continue
            icon_hd = self._toggle_icon_rect(i)
            ix, iy, iw, ih = self._hd_to_screen(*icon_hd)
            if iw > 0 and ih > 0:
                surface.blit(self._get_scaled(btn_img, iw, ih), (ix, iy))
            lx_hd = icon_hd[0] + t.get("label_offset_x", 100)
            ly_hd = icon_hd[1] + icon_hd[3] // 2
            lx, ly, _, _ = self._hd_to_screen(lx_hd, ly_hd)
            surf = lfont.render(labels.get(name, name).upper(), True,
                                TOGGLE_LABEL_COLOR)
            surface.blit(surf, (lx, ly - surf.get_height() // 2))

    # ── Input ────────────────────────────────────────────────

    def help_extra_rect(self, spec):
        """Region kinds only this screen has.

        `slot` and `toggle` both live in the cover-scaled background
        space, not in the 1080p reference space the base class knows,
        so they resolve through the same `_hd_rect` the click path
        uses — decision 5, one function for drawing, clicking and now
        for the help region as well.
        """
        cat = spec.get("slot")
        if cat:
            slot = self._cfg.get("setting_slots", {}).get(cat)
            return self._hd_rect(slot["rect"]) if slot else None

        name = spec.get("toggle")
        if name:
            t = self._cfg.get("toggles", {})
            order = t.get("order", [])
            if name not in order:
                return None
            icon = self._toggle_icon_rect(order.index(name))
            return self._hd_rect((icon[0], icon[1] - 5,
                                  t.get("click_width", 600),
                                  t.get("dy", 105)))
        return None

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return
        if not self.app.connected:
            return
        # Settings: ACTIVATE_FIELD
        for cat, slot in self._cfg.get("setting_slots", {}).items():
            if self._hd_rect(slot["rect"]).collidepoint(
                    screen_x, screen_y):
                self.app.client.activate_field(slot["field_id"])
                return
        # Toggles: type=1 radio buttons — must use INJECT_CLICK.
        # INJECT_CLICK pushes SDL mouse events; orion2re must also
        # push SDL_MOUSEMOTION before the button events so
        # Interpret_Mouse_Input_() reads the correct position.
        # Use field rects from FIELD_LIST when available (dynamic)
        # rather than hardcoded click_640 coordinates (static).
        t = self._cfg.get("toggles", {})
        cw = t.get("click_width", 600)
        dy = t.get("dy", 105)
        for i, name in enumerate(t.get("order", [])):
            icon = self._toggle_icon_rect(i)
            region = (icon[0], icon[1] - 5, cw, dy)
            if self._hd_rect(region).collidepoint(screen_x, screen_y):
                fid = t.get("field_ids", {}).get(name)
                cx, cy = self._toggle_click_pos(name, fid)
                if cx:
                    self.app.client.inject_click(cx, cy)
                return
        # Accept/Cancel via frame button bars + boxes
        super().handle_click(screen_x, screen_y)

    def _toggle_click_pos(self, name, field_id):
        """Get 640x480 click position for a toggle button.

        Prefers live field rects from FIELD_LIST (adapts to game
        changes). Falls back to hardcoded click_640 from layout.json.
        """
        if field_id and self.app.client.state:
            for f in self.app.client.state.fields:
                if f.index == field_id and f.x >= 0:
                    cx = (f.x + f.x_end) // 2
                    cy = (f.y + f.y_end) // 2
                    return (cx, cy)
        t = self._cfg.get("toggles", {})
        return t.get("click_640", {}).get(name, (0, 0))

    def handle_key(self, key):
        if self.help_consumes_key(key):
            return
        if key == pygame.K_ESCAPE:
            if self.app.connected:
                self.app.client.inject_key(pygame.K_ESCAPE)
            else:
                self.app.dispatcher.switch_to("main_menu")
        else:
            super().handle_key(key)

    def on_resize(self):
        super().on_resize()
        self._scaled_cache.clear()
