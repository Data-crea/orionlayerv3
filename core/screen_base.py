"""Base class for all HD screens.

Every screen inherits from ScreenBase and implements:
  enter()   — called when the screen becomes active
  update()  — per-frame data update (no rendering)
  render()  — draw to surface
  exit()    — cleanup when leaving

Background images are loaded automatically from
screens/<n>/assets/background.png if the file exists.
"""
import os
import time
import pygame
from core.box import load_boxes
from core.screenhelp import HelpMixin

# Frame button click feedback
BTN_FLASH_DURATION = 0.30     # total flash time in seconds
BTN_PRESS_DURATION = 0.15     # text stays offset for this long
BTN_PRESS_OFFSET = 2          # pixels down+right while pressed
BTN_FLASH_COLOR = (160, 200, 255)  # light blue-white
BTN_FLASH_MAX_ALPHA = 130     # starting opacity of flash overlay
BTN_PRESSED_TEXT_COLOR = (230, 240, 255)  # bright white while pressed


class ScreenBase(HelpMixin):
    """Base class for all OrionLayer screens.

    Right-click context help comes from `core.screenhelp.HelpMixin`:
    every screen has the behaviour, and a screen opts in by shipping
    a `help.json`.
    """

    SCREEN_NAME = ""
    GAME_SCREEN_ID = None   # orion2re screen ID for auto-switching,
                            # None for sub-screens (manual switch_to)
    IS_OVERLAY = False      # True → renders ABOVE the active screen
                            # (popups: build queue, colonization, ...)
    OVERLAY_DIM = 120       # 0-255 darkening under the overlay
    BOXES_FILE = "boxes.json"
    USE_FRAME = False       # True → draw 9-slice frame overlay
    FRAME_TITLE = ""        # Text rendered in the frame's title bar
    FRAME_BTN_LEFT = None   # ("CANCEL", field_id) or None
    FRAME_BTN_RIGHT = None  # ("ACCEPT", field_id) or None
    FRAME_VARIANT = None    # Subdirectory name in frame/ (e.g. "select_race")

    def __init__(self, app):
        self.app = app
        self._init_help()
        self.boxes = []
        self.active = False
        self._screen_dir = ""
        self._bg = None          # original background surface
        self._bg_scaled = None   # scaled to current window size
        self._bg_pos = (0, 0)
        self._btn_flash = None   # ("left"|"right", start_time)

    @property
    def layout(self):
        return self.app.layout

    @property
    def colors(self):
        return self.app.colors

    @property
    def style(self):
        return self.app.style

    def enter(self, game_state=None):
        """Screen becomes active. Load boxes, background, assets."""
        self.active = True
        # Base project dir — editor saves ALWAYS go here, never to mods
        self._screen_dir = os.path.join(
            self.app.screens_dir, self.SCREEN_NAME
        )
        self._reload_boxes()
        self._update_box_layout()
        self._load_background()
        self._load_help_regions()

    def asset_path(self, *parts):
        """Resolve a file in this screen's folder (mods first).

        Example: self.asset_path("assets", "logo.png")
        Returns an absolute path or None.
        """
        return self.app.res.screen_file(self.SCREEN_NAME, *parts)

    def _reload_boxes(self):
        """Load boxes.json through mod resolution."""
        path = self.asset_path(self.BOXES_FILE)
        self.boxes = load_boxes(path, self.app.win_w,
                                self.app.win_h) if path else []

    def exit(self):
        """Screen deactivated. Clean up."""
        self.active = False
        self.boxes = []
        self.help.close()
        self._bg = None
        self._bg_scaled = None

    def update(self, game_state=None):
        """Per-frame data update. No rendering here."""
        pass

    def render(self, surface):
        """Draw the screen. Background first, then boxes, then frame."""
        self._render_background(surface)
        for box in self.boxes:
            box.render(surface, self.layout, self.style)
        if self.USE_FRAME:
            self._render_frame(surface)
        self.render_help(surface)

    def handle_click(self, screen_x, screen_y):
        """Handle click in screen coordinates.

        Checks frame Cancel/Accept buttons first, then boxes with
        field_ids. Returns the clicked box or None.
        """
        if self.help_consumes_click(screen_x, screen_y):
            return None
        side = self._frame_button_side(screen_x, screen_y)
        if side:
            self._btn_flash = (side, time.monotonic())
        fid = self._frame_button_hit(screen_x, screen_y)
        if fid is not None:
            if self.app.connected:
                self.app.client.activate_field(fid)
            return None
        for box in self.boxes:
            if box.contains(screen_x, screen_y) and box.field_id is not None:
                if self.app.connected:
                    self.app.client.activate_field(box.field_id)
                return box
        return None

    def handle_key_event(self, event):
        """Full pygame KEYDOWN event. Default: forward the keycode.

        Screens with text input override this to access
        event.unicode (see core/widgets/text_input.py).
        """
        self.handle_key(event.key)

    def handle_key(self, key):
        """Handle keypress. Default: forward to orion2re."""
        if self.help_consumes_key(key):
            return
        if self.app.connected:
            self.app.client.inject_key(key)

    def handle_mouse_motion(self, screen_x, screen_y):
        """Update hover state for all boxes."""
        for box in self.boxes:
            box.hover = box.contains(screen_x, screen_y)

    def handle_mousewheel(self, direction, mx, my):
        """Wheel. Default: only an open help popup takes it.

        Defined here rather than only on the screens that scroll
        something, because the main loop routes the wheel by
        `hasattr` — without this, a long help entry would be
        unscrollable on Main Menu and New Game.
        """
        return self.help_consumes_wheel(direction)

    def on_resize(self):
        """Window resized. Reload boxes for new resolution, rescale bg."""
        if self._screen_dir:
            self._reload_boxes()
        self._update_box_layout()
        self._scale_background()
        self.help.clear_cache()

    # --- Background (automatic for all screens) ---

    def _load_background(self):
        """Load background.png from the screen's assets folder.

        Resolution order: mods → screen assets → shared cockpit
        texture (assets/shared/background_cockpit.png).
        """
        path = (self.asset_path("assets", "background.png")
                or self.app.res.shared("background_cockpit.png"))
        if path:
            self._bg = pygame.image.load(path).convert_alpha()
            self._scale_background()
        else:
            self._bg = None
            self._bg_scaled = None

    def _scale_background(self):
        """Scale background to cover the entire window."""
        if self._bg is None:
            return

        win_w = self.app.win_w
        win_h = self.app.win_h
        img_w = self._bg.get_width()
        img_h = self._bg.get_height()

        # Scale to cover (crop edges if aspect ratio differs)
        scale = max(win_w / img_w, win_h / img_h)
        new_w = max(win_w, int(img_w * scale))
        new_h = max(win_h, int(img_h * scale))

        scaled = pygame.transform.smoothscale(self._bg, (new_w, new_h))

        # Center crop
        x = (new_w - win_w) // 2
        y = (new_h - win_h) // 2
        self._bg_scaled = scaled.subsurface((x, y, win_w, win_h)).copy()
        self._bg_pos = (0, 0)

    def _render_background(self, surface):
        """Draw background image or solid color fallback."""
        if self._bg_scaled:
            surface.blit(self._bg_scaled, self._bg_pos)
        else:
            bg = self.colors.get("background", [6, 8, 16])
            surface.fill(bg[:3])

    # --- Box helpers ---

    def box_rect(self, name):
        """Get ref rect [x, y, w, h] from a named box.

        Applies content_offset from the box style so all content
        rendering is shifted without touching individual renderers.
        """
        for box in self.boxes:
            if box.name == name:
                x, y, w, h = box.ref_rect
                co = box.style.get("content_offset")
                if co:
                    return (x + co[0], y + co[1], w, h)
                return box.ref_rect
        return None

    def box_font_scale(self, name):
        """Get font_scale from a named box, auto-adjusted for resolution.

        The stored value is relative to 1080p. At higher resolutions
        an auto-factor is applied so text stays proportional.
        """
        base = 1.0
        for box in self.boxes:
            if box.name == name:
                base = box.style.get("font_scale", 1.0)
                break
        auto = self.app.win_h / 1080.0
        return base * auto

    # --- Internal ---

    def _update_box_layout(self):
        """Set window rects for all boxes. Once on enter/resize."""
        for box in self.boxes:
            box.update_layout(self.layout)

    def _render_frame(self, surface):
        """Draw the 9-slice frame overlay and optional title/buttons."""
        self.style.draw_frame(surface, variant=self.FRAME_VARIANT)
        if self.FRAME_TITLE:
            self._render_frame_title(surface)
        if self.FRAME_BTN_LEFT:
            self._render_frame_button(surface, "left", self.FRAME_BTN_LEFT[0])
        if self.FRAME_BTN_RIGHT:
            self._render_frame_button(surface, "right", self.FRAME_BTN_RIGHT[0])

    def _get_active_frame(self):
        """Return the active frame renderer (variant or default)."""
        if self.FRAME_VARIANT:
            v = self.style.get_frame_variant(self.FRAME_VARIANT)
            if v and v.available:
                return v
        return self.style.frame

    def _render_frame_title(self, surface):
        """Render screen title in the frame's title bar area."""
        frame = self._get_active_frame()
        if not frame or not frame.available:
            return
        tr = frame.title_rect(self.app.win_w, self.app.win_h)
        if not tr:
            return
        tx, ty, tw, th = tr
        fs = max(8, int(th * 0.65))
        col = self.colors.get("text", {}).get(
            "primary", [190, 200, 230])
        text = self.style.render_text(self.FRAME_TITLE.upper(), fs,
                                      tuple(col[:3]))
        cx = tx + (tw - text.get_width()) // 2
        cy = ty + (th - text.get_height()) // 2
        surface.blit(text, (cx, cy))

    def _render_frame_button(self, surface, side, label):
        """Render a text label in the frame's bottom button bar.

        Shows a pressed effect (text offset + flash overlay) for
        BTN_FLASH_DURATION seconds after a click.
        """
        frame = self._get_active_frame()
        if not frame or not frame.available:
            return
        ww, wh = self.app.win_w, self.app.win_h
        if side == "left":
            r = frame.button_rect_left(ww, wh)
        else:
            r = frame.button_rect_right(ww, wh)
        if not r:
            return
        bx, by, bw, bh = r

        # Check flash state
        pressed = False
        flash_alpha = 0
        if self._btn_flash and self._btn_flash[0] == side:
            elapsed = time.monotonic() - self._btn_flash[1]
            if elapsed < BTN_FLASH_DURATION:
                pressed = elapsed < BTN_PRESS_DURATION
                # Flash: bright at start, fade to zero
                t = elapsed / BTN_FLASH_DURATION
                flash_alpha = int(BTN_FLASH_MAX_ALPHA * (1.0 - t))
            else:
                self._btn_flash = None

        fs = max(8, int(bh * frame.button_font_scale))
        if pressed:
            col = BTN_PRESSED_TEXT_COLOR
        else:
            col = self.colors.get("text", {}).get(
                "primary", [190, 200, 230])
        text = self.style.render_text(label.upper(), fs, tuple(col[:3]))
        cx = bx + (bw - text.get_width()) // 2
        cy = by + (bh - text.get_height()) // 2
        if pressed:
            cx += BTN_PRESS_OFFSET
            cy += BTN_PRESS_OFFSET
        surface.blit(text, (cx, cy))

        # Flash overlay
        if flash_alpha > 0:
            flash = pygame.Surface((bw, bh), pygame.SRCALPHA)
            flash.fill((*BTN_FLASH_COLOR, flash_alpha))
            surface.blit(flash, (bx, by))

    def _frame_button_side(self, screen_x, screen_y):
        """Which frame button was hit: 'left', 'right' or None.

        Use this when a button has no field_id yet (unwired) but
        should still trigger local behaviour.
        """
        frame = self._get_active_frame()
        if not frame or not frame.available:
            return None
        ww, wh = self.app.win_w, self.app.win_h
        if self.FRAME_BTN_LEFT:
            r = frame.button_rect_left(ww, wh)
            if r and pygame.Rect(*r).collidepoint(screen_x, screen_y):
                return "left"
        if self.FRAME_BTN_RIGHT:
            r = frame.button_rect_right(ww, wh)
            if r and pygame.Rect(*r).collidepoint(screen_x, screen_y):
                return "right"
        return None

    def _frame_button_hit(self, screen_x, screen_y):
        """Check if a click hit a frame button. Returns field_id or None."""
        frame = self._get_active_frame()
        if not frame or not frame.available:
            return None
        ww, wh = self.app.win_w, self.app.win_h
        if self.FRAME_BTN_LEFT:
            r = frame.button_rect_left(ww, wh)
            if r:
                rect = pygame.Rect(*r)
                if rect.collidepoint(screen_x, screen_y):
                    return self.FRAME_BTN_LEFT[1]
        if self.FRAME_BTN_RIGHT:
            r = frame.button_rect_right(ww, wh)
            if r:
                rect = pygame.Rect(*r)
                if rect.collidepoint(screen_x, screen_y):
                    return self.FRAME_BTN_RIGHT[1]
        return None
