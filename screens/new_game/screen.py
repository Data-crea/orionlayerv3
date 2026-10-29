"""New Game Screen — the five game settings, the three switches, Cancel
and Accept, in the screen shell (work order 225).

No status line: the original prints none, and the one HD drew ("New Game
| Click settings to cycle | ESC -> Main Menu") was a leftover that Data
found on the multiplayer New Game (work order 196 B1).

Every rect is the shell's (`_shell_slot`, `_shell_toggle`), read by the
drawing, the click and the help (decision 5). The v2 drawing before the
shell — positions in 3440x1440 space mapped through the cut-out
background's cover scale — is gone (work order 272, the redundancy
audit's N20); layout.json keeps the value maps, the fields and each
slot's proportion, mod-overridable like every other data file.

Input routing:
  Settings (type=7 click-through) -> ACTIVATE_FIELD
  Toggles (type=1 radio buttons)  -> INJECT_CLICK (only exception)
  Accept/Cancel (type=0 buttons)  -> ACTIVATE_FIELD via frame bars
  ESC                             -> inject_key
"""
import logging
import pygame

from core.hud import blocks as hud
from core import backgrounds, palette
from core.screen_base import ScreenBase

log = logging.getLogger("new_game")

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



def _values(info):
    """A category's values for the connected engine: orion2re v2 orders the
    civilisation levels anew and adds two values (`values_v2`, work order
    243; `core.structs.layout.generation`)."""
    from core.structs import layout
    if layout.generation() >= 2 and "values_v2" in info:
        return info["values_v2"]
    return info.get("values", {})

class NewGameScreen(ScreenBase):
    SCREEN_NAME = "new_game"
    #: Its picture moves only with input, the game and the window: a frame
    #: that would draw it again is not drawn (work order 273, `core/drawgate`).
    STILL = True
    GAME_SCREEN_ID = 13     # SCREEN_NEW_GAME
    USE_FRAME = True
    FRAME_TITLE = "New Game"
    FRAME_BTN_LEFT = ("Cancel", 14)
    FRAME_BTN_RIGHT = ("Accept", 15)
    #: THE SCREEN SHELL (work order 225): six panels, three by two, fill
    #: the content rectangle above the button row — the five settings
    #: (title, picture, value) and the three switches; the title on the
    #: plate, CANCEL and ACCEPT the shell's buttons (`screenframe`). Every
    #: rect comes from `_shell_slot` / `_shell_toggle`, which the drawing,
    #: the click and the help all read (decision 5).
    SHELL_WORN = True
    #: The panels in reading order; the last holds the switches.
    SHELL_PANELS = ("difficulty", "galaxy_size", "galaxy_age", "players",
                    "tech_level", "toggles")
    #: Word sizes in reference px — what the v2 sizes (36, 38, 32) came
    #: to at 1920x1080 through the cover scale.
    TITLE_PX, LABEL_PX, TOGGLE_PX = 26, 28, 23
    #: The switch's box, likewise (the v2 icon_size 80 at 1920x1080).
    TOGGLE_BOX_PX = 60

    def __init__(self, app):
        super().__init__(app)
        self._cfg = {}           # layout.json contents
        self._setting_imgs = {}
        self._current = {}       # category -> image filename
        self._labels = {}        # category -> display label
        self._toggle_states = {}
        self._scaled_cache = {}

    def enter(self, game_state=None):
        self._load_layout_cfg()
        super().enter(game_state)   # boxes, layout, background override
        self._preload_setting_images()
        self._current = {}
        self._labels = {}
        self._toggle_states = {}
        self._scaled_cache.clear()

    def exit(self):
        super().exit()
        self._setting_imgs.clear()
        self._scaled_cache.clear()

    # ── Config / loading ─────────────────────────────────────

    def _load_layout_cfg(self):
        self._cfg = self.app.res.load_json(
            "screens/new_game/layout.json", {})

    def picture_rect(self, category):
        """Where `category`'s picture is drawn: the shell's picture rect
        (work order 225)."""
        return self._shell_slot(category)[1]

    def setting_picture(self, category):
        """The picture for `category`'s current setting, scaled to
        `picture_rect`, or None. One function for the drawing and the
        check that holds the picture to its source (work order 172)."""
        filename = self._current.get(category)
        img = self._get_setting_image(category, filename) if filename else None
        if img is None:
            return None
        inner = self.picture_rect(category)
        return self._get_scaled(img, inner.w, inner.h)

    def _preload_setting_images(self):
        """Load ALL setting images up front so render never blocks on disk I/O."""
        cats = self._cfg.get("categories", {})
        for cat, info in cats.items():
            for val_key, entry in _values(info).items():
                filename = entry.get("image")
                if filename:
                    self._get_setting_image(cat, filename)

    def _get_setting_image(self, category, filename):
        key = f"{category}/{filename}"
        if key not in self._setting_imgs:
            path = self.asset_path("assets", category, f"{filename}.png")
            img = None
            if path:
                try:
                    img = pygame.image.load(path).convert()
                except pygame.error as err:  # a corrupt mod file (audit pass 2)
                    log.warning("%s not loaded: %s", path, err)
            self._setting_imgs[key] = img
        return self._setting_imgs[key]

    def _get_scaled(self, surf, w, h):
        key = (id(surf), w, h)
        if key not in self._scaled_cache:
            self._scaled_cache[key] = (
                pygame.transform.smoothscale(surf, (w, h)))
        return self._scaled_cache[key]

    # ── The shell's geometry (work order 225) ────────────────

    def _shell_panel(self, name):
        from core.hud import shell
        L = self.ref_layout
        area = shell.panels(L, row=True)
        cols = shell.split(area, L, [1.0, 1.0, 1.0])
        rows = shell.split(area, L, [1.0, 1.0], vertical=True)
        i = self.SHELL_PANELS.index(name)
        c, r = cols[i % 3], rows[i // 3]
        return pygame.Rect(c.x, r.y, c.w, r.h)

    def _shell_slot(self, cat):
        """(panel, picture rect, title y, label y) of setting `cat`: the
        title at the inner top, the value at the inner bottom, the
        picture between them in its slot's own proportion, centred."""
        from core.hud import shell
        L = self.ref_layout
        panel = self._shell_panel(cat)
        inner = shell.inner(panel, L)
        g = shell.element_gap(L)
        th = L.font_size(self.TITLE_PX) + g
        lh = L.font_size(self.LABEL_PX) + g
        slot = self._cfg.get("setting_slots", {}).get(cat, {})
        sw, sh = (slot.get("rect") or (0, 0, 600, 306))[2:]
        room = pygame.Rect(inner.x, inner.y + th, inner.w,
                           inner.h - th - lh)
        k = min(room.w / sw, room.h / sh)
        pic = pygame.Rect(0, 0, int(sw * k), int(sh * k))
        pic.center = room.center
        return panel, pic, inner.y, inner.bottom - lh + g

    def _shell_toggle(self, i):
        """(row rect, box rect) of switch `i`: the rows share the panel's
        inner height, the box a square at the row's left."""
        from core.hud import shell
        L = self.ref_layout
        inner = shell.inner(self._shell_panel("toggles"), L)
        n = max(1, len(self._cfg.get("toggles", {}).get("order", [])))
        h = inner.h // n
        row = pygame.Rect(inner.x, inner.y + i * h, inner.w, h)
        size = int(self.TOGGLE_BOX_PX * L.scale)
        box = pygame.Rect(row.x + shell.element_gap(L) * 2, 0, size, size)
        box.centery = row.centery
        return row, box

    # ── Update ───────────────────────────────────────────────

    def update(self, game_state=None):
        if not game_state:
            return
        cats = self._cfg.get("categories", {})
        self._current = {}
        self._labels = {}
        for cat, attr in STATE_ATTRS.items():
            value = getattr(game_state, attr, None)
            entry = _values(cats.get(cat, {})).get(str(value))
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
        # THE HUD STYLE, decision 71 (work order 169): the universal
        # background (work order 173), the shell's panels with each
        # picture on its own, the plate and the buttons, the help.
        backgrounds.draw(surface, self.SCREEN_NAME)
        self._render_shell_panels(surface)
        self._render_frame(surface)     # the plate and the buttons
        self.render_help(surface)

    def _render_shell_panels(self, surface):
        """The six panels, the settings' words and pictures, the switches."""
        L = self.ref_layout
        cats = self._cfg.get("categories", {})
        for name in self.SHELL_PANELS:
            hud.panel(surface, self._shell_panel(name), L.scale)
        tfont = self.style.get_font(L.font_size(self.TITLE_PX))
        lfont = self.style.get_font(L.font_size(self.LABEL_PX))
        for cat in self._cfg.get("setting_slots", {}):
            panel, pic, ty, ly = self._shell_slot(cat)
            # The outline UNDER the picture, just outside it: the picture
            # stays its source pixel for pixel (172's rule, check 006f).
            hud.outline(surface, pic.inflate(4, 4), L.scale)
            img = self.setting_picture(cat)
            if img is not None:
                surface.blit(img, pic)
            title = cats.get(cat, {}).get("title", "")
            if title:
                t = tfont.render(title.upper(), True, TITLE_COLOR)
                surface.blit(t, (panel.centerx - t.get_width() // 2, ty))
            label = self._labels.get(cat, "")
            if label:
                t = lfont.render(label, True, LABEL_COLOR)
                surface.blit(t, (panel.centerx - t.get_width() // 2, ly))
        t = self._cfg.get("toggles", {})
        font = self.style.get_font(L.font_size(self.TOGGLE_PX))
        for i, name in enumerate(t.get("order", [])):
            row, box = self._shell_toggle(i)
            hud.checkbox(surface, box, L.scale,
                         self._toggle_states.get(name, False))
            w = font.render(t.get("labels", {}).get(name, name).upper(),
                            True, TOGGLE_LABEL_COLOR)
            surface.blit(w, (box.right + box.w // 2,
                             row.centery - w.get_height() // 2))

    # ── Input ────────────────────────────────────────────────

    def help_extra_rect(self, spec):
        """Region kinds only this screen has.

        `slot` and `toggle` are the shell's panel and switch row — the
        same rects the drawing and the click use (decision 5).
        """
        cat = spec.get("slot")
        if cat:
            slot = self._cfg.get("setting_slots", {}).get(cat)
            return self._shell_slot(cat)[0] if slot else None

        name = spec.get("toggle")
        if name:
            t = self._cfg.get("toggles", {})
            order = t.get("order", [])
            if name not in order:
                return None
            return self._shell_toggle(order.index(name))[0]
        return None

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return
        if not self.app.connected:
            return
        # Settings: ACTIVATE_FIELD
        for cat, slot in self._cfg.get("setting_slots", {}).items():
            # The whole panel answers under the shell, as the slot did.
            if self._shell_slot(cat)[0].collidepoint(screen_x, screen_y):
                self.app.client.activate_field(slot["field_id"])
                return
        # Toggles: type=1 radio buttons — must use INJECT_CLICK.
        # INJECT_CLICK pushes SDL mouse events; orion2re must also
        # push SDL_MOUSEMOTION before the button events so
        # Interpret_Mouse_Input_() reads the correct position.
        # Use field rects from FIELD_LIST when available (dynamic)
        # rather than hardcoded click_640 coordinates (static).
        t = self._cfg.get("toggles", {})
        for i, name in enumerate(t.get("order", [])):
            if self._shell_toggle(i)[0].collidepoint(screen_x, screen_y):
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
