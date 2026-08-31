"""Empire Identity Screen — ruler name, banner colour, home system.

Merges MOO2's three small dialogs (Enter Ruler Name, Select Banner,
Enter Home Star Name) into one HD screen. Reached on both paths:
  - Custom Race → Accept (custom_race/screen.py, lock_ids 50+6)
  - Stock race portrait click in Select Race (lock_ids 6)
The dialogs are detected by field SHAPE (core/injection.py), so the
same chain serves both flows unchanged:

  Top panel:     RULER NAME input | BANNER grid (4x2) | HOME SYSTEM input
  Bottom panel:  EMPIRE PREVIEW — banner on a stand, empire name,
                 ruler + home system, and the homeworld artwork
  Frame:         default frame with CANCEL / ACCEPT

All rects come from boxes.json (F5). The homeworld artwork sits in
the "preview_image" box, whose style carries zoom/crop/fade_left —
pan and zoom it in the editor (scroll = zoom, Shift/Alt+scroll or
right-drag = pan) and save with Ctrl+S.

Wiring: Accept starts an InjectionChain (core/injection.py) that
feeds the three original dialogs — ruler name, banner tile, home star
name — while this screen stays on top and shows progress. The lock is
held via keep_lock() until the chain is done; the game then sits on
the Galaxy Map (ID 0) and the dispatcher releases.
"""
import logging
import time
import pygame
from core import banner as bn
from core.screen_base import ScreenBase
from core.widgets.text_input import TextInput
from core.injection import (InjectionChain, is_name_dialog,
                            is_banner_dialog, type_name, click_banner,
                            LONG_STEP_TIMEOUT_S)
from screens.empire_identity import renderer
from screens.empire_identity.renderer import (
    draw_thin_box, draw_title_hint, draw_centered,
    render_banner_grid, banner_hit_test, render_image_box,
    draw_icon_ruler, draw_icon_star, render_preview_text,
    COL_HEADER,
)

log = logging.getLogger("empire_identity")


class EmpireIdentityScreen(ScreenBase):
    SCREEN_NAME = "empire_identity"
    GAME_SCREEN_ID = None     # sub-screen; wired later (after Custom Race)
    USE_FRAME = True
    FRAME_TITLE = "Empire Identity"
    FRAME_BTN_LEFT = ("Cancel", None)    # field IDs follow with wiring
    FRAME_BTN_RIGHT = ("Accept", None)
    FRAME_VARIANT = None

    def __init__(self, app):
        super().__init__(app)
        self._data = {}
        self._colors = []
        self._race = "elerian"
        self._color = "green"
        self._hover_color = None
        self._ruler = None            # TextInput
        self._home = None             # TextInput
        self._focus = "ruler"         # which input owns the caret
        self._homeworld = None        # artwork surface
        self._img_cache = {}
        self._tiles = None           # BannerRenderer (grid tiles)
        self._stand = None            # BannerRenderer (preview stand)
        self._chain = None            # InjectionChain while accepting
        self._release = False         # True once the chain finished

    # ── Lifecycle ─────────────────────────────────────────

    def enter(self, game_state=None):
        super().enter(game_state)
        self._data = self.app.res.load_json(
            "screens/empire_identity/layout.json", {}) or {}
        self._colors = self._data.get("banner_colors", [])
        self._color = self._data.get("default_color", "green")
        self._race = self._race_from_selection()
        self._tiles = bn.get_renderer(bn.BANNER_TILE)
        self._stand = bn.get_renderer(bn.BANNER_STAND_HD,
                                      with_background=False)
        self._load_homeworld()
        self._img_cache = {}

        home_default = self._data.get("home_default", {}).get(
            self._race, "")
        self._ruler = TextInput(
            value="", max_len=self._data.get("ruler_max_len", 15),
            placeholder="Ruler name", font_ref=30,
            on_submit=lambda v: self._accept(), on_cancel=self._cancel)
        self._home = TextInput(
            value=home_default, max_len=self._data.get("home_max_len", 12),
            placeholder="Home system", font_ref=30,
            on_submit=lambda v: self._accept(), on_cancel=self._cancel)
        self._focus = "ruler"
        self._set_focus("ruler")
        self._chain = None
        self._release = False

    def _race_from_selection(self):
        """Race key for the emblem: taken from the Select Race screen
        when it holds a stock race, otherwise the layout default.
        (Custom Race → picture choice; to be read from the game later.)"""
        default = self._data.get("default_race", "elerian")
        sel = self.app.dispatcher.screens.get("select_race") \
            if hasattr(self.app, "dispatcher") else None
        rid = getattr(sel, "_selected_id", None)
        return self._data.get("race_by_select_id", {}).get(str(rid), default)

    def set_race(self, race_key):
        """Change the emblem race (hook for later wiring)."""
        if race_key in bn.RACES:
            self._race = race_key

    def _load_homeworld(self):
        path = self.asset_path("assets", "homeworld.png")
        self._homeworld = (pygame.image.load(path).convert_alpha()
                           if path else None)

    def update(self, game_state=None):
        if self._chain:
            self._chain.update(game_state)
            if self._chain.failed:
                self._on_chain_failed(self._chain.failed_step)
            if self._chain.done or self._chain.failed:
                self._release = True
                self._chain = None

    def _on_chain_failed(self, step):
        """A failed chain leaves the game standing in an original
        dialog the HD screen cannot draw — the classic symptom is HD
        back on Custom Race while orion2re waits on "Enter home star
        name". Hand the player the framebuffer so the dialog can be
        finished by hand (F12 switches back)."""
        log.error("Injection chain failed at '%s' — the game is still "
                  "in an original dialog; switching to original view",
                  step or "?")
        if getattr(self.app, "connected", False):
            self.app.render_mode = "original"

    def keep_lock(self, screen_id):
        """Dispatcher hook. True: hold regardless of the game's ID
        (chain running). False: release now (chain done / cancel).
        None: let the dispatcher's lock_ids decide (idle)."""
        if self._chain:
            return True
        if self._release:
            return False
        return None

    @property
    def busy(self):
        return self._chain is not None

    def on_resize(self):
        super().on_resize()
        self._img_cache = {}

    # ── Rendering ─────────────────────────────────────────

    def render(self, surface):
        self._render_background(surface)
        L = self.layout
        labels = self._data.get("labels", {})

        # -- Top panel: identity inputs + banner grid --
        r = self.box_rect("identity_panel")
        if r:
            draw_thin_box(surface, L, r)
        for key in ("ruler", "banner", "home"):
            hr = self.box_rect(f"{key}_header")
            if hr:
                draw_title_hint(surface, L, self.style,
                                labels.get(f"{key}_title", key.title()),
                                labels.get(f"{key}_hint", ""), hr,
                                self.box_font_scale(f"{key}_header"))
        gr = self.box_rect("banner_grid")
        if gr:
            draw_thin_box(surface, L, gr)
            render_banner_grid(surface, L, self._colors, self._race,
                               self._color, self._hover_color, gr,
                               self._tiles)
        for key, widget in (("ruler", self._ruler), ("home", self._home)):
            ir = self.box_rect(f"{key}_input")
            if ir and widget:
                widget.render(surface, pygame.Rect(L.rect(ir)),
                              self.style, L)

        # -- Bottom panel: preview (fill → artwork → border) --
        pr = self.box_rect("preview_panel")
        if pr:
            draw_thin_box(surface, L, pr)
        ir = self.box_rect("preview_image")
        if ir:
            style = self._box_style("preview_image")
            render_image_box(surface, L, self._homeworld, ir, style,
                             self._img_cache)
        if pr:
            draw_thin_box(surface, L, pr, fill=False)
        hr = self.box_rect("preview_header")
        if hr:
            font = self.style.get_font(L.font_size(
                int(19 * self.box_font_scale("preview_header"))))
            draw_centered(surface, font,
                          labels.get("preview_title", "Empire Preview").upper(),
                          COL_HEADER, L.rect(hr))
        br = self.box_rect("preview_banner")
        if br and self._stand:
            px, py = L.pos(br[0], br[1])
            pw, ph = L.size(br[2], br[3])
            img = self._stand.get_scaled(self._color, self._race, ph)
            surface.blit(img, (px + (pw - img.get_width()) // 2, py))
        self._render_preview_text(surface, L, labels)
        if self._chain:
            self._render_busy(surface, L, labels)

        if self.USE_FRAME:
            self._render_frame(surface)

    def _render_busy(self, surface, L, labels):
        """Progress box while the injection chain runs (INVENTION —
        see the note in renderer.py). Wording per step comes from
        layout.json, so a translation never touches this file."""
        panel = self.box_rect("busy_panel") or renderer.FALLBACK_PANEL
        text_rect = (self.box_rect("busy_text")
                     or renderer.busy_text_rect(panel))
        steps = labels.get("busy_steps", {})
        step = self._chain.current
        renderer.render_busy_panel(
            surface, L, self.style, panel, text_rect,
            labels.get("busy", "Setting up your empire"),
            steps.get(step, step.title()),
            self._chain.step_number, self._chain.step_count,
            self._chain.waited,
            labels.get("busy_elapsed", "({s} s)"),
            backdrop=self._bg_scaled)

    def _render_preview_text(self, surface, L, labels):
        tr = self.box_rect("preview_text")
        if not tr:
            return
        empire = self._data.get("empire_name", {}).get(
            self._race, f"{self._race.title()} Empire")
        rows = (
            (draw_icon_ruler, labels.get("preview_ruler", "Ruler:"),
             self._ruler.value if self._ruler else ""),
            (draw_icon_star, labels.get("preview_home", "Home System:"),
             self._home.value if self._home else ""),
        )
        render_preview_text(surface, L, self.style,
                            self.box_font_scale("preview_text"),
                            tr, empire, rows)

    def image_size(self, box_name):
        """Editor hook: source size of the artwork in a pannable box."""
        if box_name == "preview_image" and self._homeworld:
            return self._homeworld.get_size()
        return None

    def _box_style(self, name):
        for box in self.boxes:
            if box.name == name:
                return box.style
        return {}

    # ── Input ─────────────────────────────────────────────

    def handle_click(self, screen_x, screen_y):
        if self.busy:
            return None
        side = self._frame_button_side(screen_x, screen_y)
        if side == "left":
            self._btn_flash = (side, time.monotonic())
            self._cancel()
            return None
        if side == "right":
            self._btn_flash = (side, time.monotonic())
            self._accept()
            return None

        gr = self.box_rect("banner_grid")
        if gr:
            hit = banner_hit_test(self.layout, self._colors, gr,
                                  screen_x, screen_y)
            if hit:
                self._color = hit
                log.info("Banner colour: %s", hit)
                return None

        # Text inputs: focus the one clicked; a click elsewhere keeps
        # the current focus (a caret is always somewhere on this screen)
        if self._ruler and self._home:
            r_hit = self._ruler.handle_click(screen_x, screen_y)
            h_hit = self._home.handle_click(screen_x, screen_y)
            if r_hit or h_hit:
                self._set_focus("home" if h_hit else "ruler")
                return None
            self._set_focus(self._focus)
        return super().handle_click(screen_x, screen_y)

    def _set_focus(self, which):
        self._focus = which
        self._ruler.focused = (which == "ruler")
        self._home.focused = (which == "home")

    def handle_mouse_motion(self, screen_x, screen_y):
        super().handle_mouse_motion(screen_x, screen_y)
        gr = self.box_rect("banner_grid")
        self._hover_color = (banner_hit_test(self.layout, self._colors, gr,
                                             screen_x, screen_y)
                             if gr else None)

    def handle_key_event(self, event):
        if event.type != pygame.KEYDOWN or self.busy:
            return
        if event.key == pygame.K_TAB and self._ruler and self._home:
            self._set_focus("home" if self._focus == "ruler" else "ruler")
            return
        for widget in (self._ruler, self._home):
            if widget and widget.focused and widget.handle_key_event(event):
                return
        self.handle_key(event.key)

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            self._cancel()
        # No forwarding to orion2re: this screen is not wired yet.

    # ── Actions ───────────────────────────────────────────

    def _accept(self):
        r = self.result
        log.info("Accept: ruler='%s' banner=%s home='%s' race=%s",
                 r["ruler"], r["banner"], r["home"], r["race"])
        if not self.app.connected:
            self._release = True
            return
        if self.busy:
            return
        order = list(self._colors)
        ruler, home, color = r["ruler"], r["home"], r["banner"]
        # The home star step gets a long timeout: it is not asked by
        # racesel.cpp at all. Race selection returns first, the game
        # generates the galaxy, and only then does the naming popup
        # appear — silence in between, with no field list published.
        self._chain = InjectionChain(self.app.client, [
            ("ruler name", is_name_dialog,
             lambda c, f: type_name(c, ruler)),
            ("banner", is_banner_dialog,
             lambda c, f: click_banner(c, f, color, order)),
            ("home star", is_name_dialog,
             lambda c, f: type_name(c, home), LONG_STEP_TIMEOUT_S),
        ])

    def _cancel(self):
        """Back out: ESC closes the ruler dialog in the original and
        returns to race selection; release the lock so the dispatcher
        follows whatever ID the game reports next."""
        log.info("Cancel")
        if self.app.connected:
            self.app.client.inject_key(pygame.K_ESCAPE)
        self._chain = None
        self._release = True

    @property
    def result(self):
        """Current choices — consumed by the wiring later."""
        return {"ruler": self._ruler.value if self._ruler else "",
                "home": self._home.value if self._home else "",
                "banner": self._color, "race": self._race}
