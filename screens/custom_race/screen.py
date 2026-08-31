"""Custom Race Screen — three-panel layout matching MOO2 reference.

Layout (three inner panels + bottom bars):
  Left:   "RACE PICKS" — categories in 2 sub-columns (5 each)
  Center: "SPECIAL ABILITIES" — single column checkbox list
  Right:  "DESCRIPTION" — name + text of the selected trait
  Bottom: combined Race Picks / Score bar (one movable box)
  Frame:  default frame (same as New Game) with CLEAR / ACCEPT
          in the button bars
"""
import logging
import time
import pygame
from core.screen_base import ScreenBase
from screens.custom_race.renderer import (
    render_race_picks_panel, render_specials_panel,
    picks_hit_test, specials_hit_test, specials_content_height, _c,
)
from screens.custom_race.description import (
    render_description_panel, description_height,
)
from screens.custom_race.popup import (
    MessagePopup, FALLBACK_PANEL, fallback_text_rect,
)

log = logging.getLogger("custom_race")

COL_PANEL_HEADER = _c("panel_header", (120, 170, 255))

# Fallback wording; the shipped string lives in traits.json under
# "messages" so a mod or a translation can replace it.
MSG_PICKS_NEGATIVE = ("Picks remaining must be greater than or "
                      "equal to zero.")


class CustomRaceScreen(ScreenBase):
    SCREEN_NAME = "custom_race"
    GAME_SCREEN_ID = 50     # Custom Race sub-screen (patched in racesel.cpp)
    USE_FRAME = True
    FRAME_TITLE = "Custom Race"
    FRAME_BTN_LEFT = ("Clear", 4)     # field 4 = Default/Clear (hotkey C)
    FRAME_BTN_RIGHT = ("Accept", 3)   # field 3 = Accept (hotkey A)
    FRAME_VARIANT = None    # default frame (with button bars)

    def __init__(self, app):
        super().__init__(app)
        self._traits_data = {}
        self._categories = []
        self._specials = []
        self._trait_state = {}
        self._starting_picks = 10
        self._bar_img = None      # combined picks/score bar image
        self._icons = {}          # radio/checkbox images
        self._icon_cache = {}     # scaled icons per pixel size
        self._active = None       # entry shown in the description panel
        self._spec_scroll = 0     # specials list scroll (reference units)
        self._desc_scroll = 0     # description scroll (reference units)
        self._panels = {}         # inner content rects (hit tests)
        self._panel_outer = {}    # outer box rects (headers/skins)
        self._panel_fs = {}       # font scale per panel (from boxes)
        self._popup = MessagePopup()   # blocks Accept on negative picks

    def enter(self, game_state=None):
        super().enter(game_state)
        self._load_traits()
        self._load_bar_image()
        self._load_icons()
        self._reset_traits()
        self._active = None
        self._spec_scroll = 0
        self._desc_scroll = 0
        self._popup.close()
        # Sync game to zero: the game loads stock traits on entry,
        # HD starts clean — sending Clear aligns both sides.
        if self.app.connected:
            self.app.client.activate_field(4)

    def _load_traits(self):
        """Trait data, mod-overridable (screens/custom_race/traits.json)."""
        data = self.app.res.load_json("screens/custom_race/traits.json")
        if not data:
            return
        self._traits_data = data
        self._categories = self._traits_data.get("categories", [])
        self._specials = self._traits_data.get("specials", [])
        self._starting_picks = self._traits_data.get("starting_picks", 10)

    def _load_bar_image(self):
        """Combined Race Picks + Score bar (one image, one box)."""
        path = self.asset_path("assets", "picks_score_bar.png")
        if path:
            self._bar_img = pygame.image.load(path).convert_alpha()
            log.info("Loaded picks_score_bar.png")

    def _load_icons(self):
        """Radio and checkbox icons (mod-overridable assets).

        The unselected outline icons ship in a warm metal tone that
        disappears against the dark panels, so their RGB is recolored
        to the skin's "icon_outline" while the original alpha (and
        therefore the shape and antialiasing) is kept. radio_on keeps
        its own colors — it is the glowing selected marker.
        """
        tint = _c("icon_outline", (168, 186, 214))
        for name in ("radio_off", "radio_on", "checkbox_off"):
            path = self.asset_path("assets", f"{name}.png")
            if not path:
                continue
            img = pygame.image.load(path).convert_alpha()
            if name != "radio_on":
                img = self._tint(img, tint)
            self._icons[name] = img
        self._icon_cache.clear()

    @staticmethod
    def _tint(surface, color):
        """Replace RGB with `color`, preserving the alpha channel."""
        out = surface.copy()
        rgb = pygame.surfarray.pixels3d(out)
        rgb[:, :, 0] = color[0]
        rgb[:, :, 1] = color[1]
        rgb[:, :, 2] = color[2]
        del rgb
        return out

    def _reset_traits(self):
        """All traits off; government falls back to its default.

        There is no "Normal" row (the original has none either) —
        0 simply means "nothing selected" for a category.
        """
        self._trait_state = {}
        for cat in self._categories:
            self._trait_state[cat["trait_id"]] = 0
        for spec in self._specials:
            self._trait_state[spec["trait_id"]] = 0
        self._trait_state[0] = self._traits_data.get(
            "default_government", 2)

    @property
    def picks_used(self):
        total = 0
        for cat in self._categories:
            val = self._trait_state.get(cat["trait_id"], 0)
            for opt in cat["options"]:
                if opt["value"] == val:
                    total += opt["picks"]
                    break
        for spec in self._specials:
            if (self._trait_state.get(spec["trait_id"], 0)
                    == spec.get("value", 1)):
                total += spec["picks"]
        return total

    @property
    def picks_remaining(self):
        return self._starting_picks - self.picks_used

    @property
    def blocked_traits(self):
        """Set of (trait_id, value) pairs blocked by exclusive groups.

        A special is blocked when its exclusive partner is active.
        Farming (trait 2) is blocked when Lithovore (trait 18) is on.
        """
        blocked = set()
        # Specials: exclusive groups
        active_groups = {}
        for spec in self._specials:
            group = spec.get("group")
            if not group:
                continue
            val = spec.get("value", 1)
            if self._trait_state.get(spec["trait_id"], 0) == val:
                active_groups[group] = (spec["trait_id"], val)
        for spec in self._specials:
            group = spec.get("group")
            if not group:
                continue
            val = spec.get("value", 1)
            active = active_groups.get(group)
            if active and active != (spec["trait_id"], val):
                blocked.add((spec["trait_id"], val))
        # Lithovore (trait 18) blocks Farming (trait 2)
        if self._trait_state.get(18, 0) == 1:
            blocked.add((2, "all"))
        return blocked

    def _content_rect(self):
        """Content area inside frame in reference coords."""
        frame = self._get_active_frame()
        L = self.layout
        if frame and frame.available:
            ci = frame.content_inset
            ww, wh = self.app.win_w, self.app.win_h
            sx = ci[0] * ww / frame.source_w
            sy = ci[2] * wh / frame.source_h
            sw = ww - (ci[0] + ci[1]) * ww / frame.source_w
            sh = wh - (ci[2] + ci[3]) * wh / frame.source_h
            return (sx / L.scale, sy / L.scale,
                    sw / L.scale, sh / L.scale)
        return (60, 80, 1800, 920)

    def _fallback_rect(self, key):
        """Three-column split of the frame content area.

        Used only when the corresponding box is missing from
        boxes.json, so a broken edit cannot blank the screen.
        """
        rx, ry, rw, rh = self._content_rect()
        gap = 12
        left_w = rw * 0.40 - gap
        mid_w = rw * 0.29 - gap
        right_w = rw * 0.31
        if key == "picks":
            return (rx, ry, left_w, rh)
        if key == "specials":
            return (rx + left_w + gap, ry, mid_w, rh)
        return (rx + left_w + gap + mid_w + gap, ry, right_w, rh)

    # ── Rendering ─────────────────────────────────────────

    def render(self, surface):
        self._render_background(surface)
        L = self.layout
        fs = self.app.win_h / 1080.0

        rx, ry, rw, rh = self._content_rect()

        # Panels come from boxes.json (F5: move, resize, font_scale).
        # Falls back to a computed three-column split if a box is
        # missing, so the screen still renders after a bad edit.
        head_h = 34
        pad = 10
        self._panels = {}
        self._panel_fs = {}

        for key, box_name in (("picks", "race_picks_panel"),
                              ("specials", "specials_panel"),
                              ("description", "description_panel")):
            rect = self.box_rect(box_name) or self._fallback_rect(key)
            self._panels[key] = (rect[0] + pad, rect[1] + head_h,
                                 rect[2] - pad * 2,
                                 rect[3] - head_h - pad)
            self._panel_fs[key] = (self.box_font_scale(box_name)
                                   if self.box_rect(box_name) else fs)
            self._panel_outer = getattr(self, "_panel_outer", {})
            self._panel_outer[key] = rect

        # Panel skins are drawn by the box itself: inner_panel is the
        # NineSlice art, thin_border the rounded outline. Both live in
        # core/style.py, so this screen no longer carries its own copy
        # of the border arithmetic.
        for box in self.boxes:
            if box.style.get("skin") in ("inner_panel", "thin_border"):
                box.render(surface, self.layout, self.style)

        # -- Left panel: RACE PICKS --
        pr = self._panel_outer["picks"]
        self._draw_panel_header(surface, L, "RACE PICKS",
                                "picks_header", pr)
        blocked = self.blocked_traits
        render_race_picks_panel(surface, L, self.style,
            self._categories, self._trait_state,
            self._panels["picks"], self._icons, self._icon_cache,
            self._panel_fs["picks"], self._active, blocked)

        # -- Center panel: SPECIAL ABILITIES --
        sr = self._panel_outer["specials"]
        self._draw_panel_header(surface, L, "SPECIAL ABILITIES",
                                "specials_header", sr)
        render_specials_panel(surface, L, self.style,
            self._specials, self._trait_state,
            self._panels["specials"], self._icons, self._icon_cache,
            self._panel_fs["specials"], self._spec_scroll,
            self._active, blocked)

        # -- Right panel: DESCRIPTION --
        dr = self._panel_outer["description"]
        self._draw_panel_header(surface, L, "DESCRIPTION",
                                "description_header", dr)
        render_description_panel(surface, L, self.style,
            self._active_entry(), self._panels["description"],
            self._panel_fs["description"], self._desc_scroll)

        # Frame overlay
        if self.USE_FRAME:
            self._render_frame(surface)

        # ── Bottom bar (ONE F5-movable box, on top of frame) ──
        self._render_bar(surface, L,
                         self.box_font_scale("picks_score_bar"))

        # ── Message box, above everything it interrupts ──
        self._render_popup(surface, L)

    def _render_popup(self, surface, L):
        """Draw the message box; also previewed while the editor runs.

        The preview is what makes the two boxes tunable at all — an
        empty panel gives no clue whether the font scale fits the
        string it will have to hold.
        """
        editor = getattr(self.app, "editor", None)
        preview = bool(editor and editor.active)
        if not self._popup.visible and not preview:
            return
        panel = self.box_rect("picks_popup") or FALLBACK_PANEL
        text_rect = (self.box_rect("picks_popup_text")
                     or fallback_text_rect(panel))
        message = self._popup.message or self._message(
            "picks_negative", MSG_PICKS_NEGATIVE)
        self._popup.render(surface, L, self.style, panel, text_rect,
                           self.box_font_scale("picks_popup_text"),
                           message, self._bg_scaled)

    def _message(self, key, fallback):
        """Screen text from traits.json (mod- and translation-ready)."""
        return self._traits_data.get("messages", {}).get(key, fallback)

    def _render_bar(self, surface, L, fs):
        """Combined Race Picks + Score bar.

        The image (picks_score_bar.png) holds two empty panels;
        label+value pairs are positioned via F5-movable boxes
        'picks_text' and 'score_text'.
        """
        rect = self.box_rect("picks_score_bar")
        if not rect:
            return
        rx, ry, rw, rh = rect
        sx, sy = L.pos(rx, ry)
        sw, sh = L.size(rw, rh)

        if self._bar_img:
            scaled = pygame.transform.smoothscale(self._bar_img,
                                                  (sw, sh))
            surface.blit(scaled, (sx, sy))

        from screens.custom_race.renderer import (
            COL_LABEL, COL_VALUE_POS, COL_VALUE_NEG)

        picks_ok = self.picks_remaining >= 0
        entries = [
            ("picks_text", "Race Picks",
             str(self.picks_remaining),
             COL_VALUE_POS if picks_ok else COL_VALUE_NEG),
            ("score_text", "Score",
             f"{max(0, 100 + self.picks_remaining * 10)}%",
             COL_VALUE_POS),
        ]
        for box_name, label, value, vcol in entries:
            tr = self.box_rect(box_name)
            tfs = self.box_font_scale(box_name) if tr else fs
            lfont = self.style.get_font(L.font_size(int(14 * tfs)))
            vfont = self.style.get_prop_font(
                L.font_size(int(24 * tfs)))
            lbl = lfont.render(label, True, COL_LABEL)
            val = vfont.render(value, True, vcol)
            if tr:
                bx, by = L.pos(tr[0], tr[1])
                bw, bh = L.size(tr[2], tr[3])
            else:
                # Fallback: centered in bar halves
                bx = sx
                by, bh = sy, sh
                bw = sw
            # Label left, value right, both baseline-aligned
            pair_h = max(lbl.get_height(), val.get_height())
            base_y = by + (bh - pair_h) // 2
            lbl_y = base_y + (pair_h - lbl.get_height())
            val_y = base_y + (pair_h - val.get_height())
            surface.blit(lbl, (bx + int(bw * 0.06), lbl_y))
            surface.blit(val, (bx + int(bw * 0.55), val_y))

    def _draw_panel_header(self, surface, L, text, box_name, panel_rect):
        """Draw a centered header, positioned via its own F5 box."""
        hr = self.box_rect(box_name)
        hfs = self.box_font_scale(box_name) if hr else 1.0
        if hr:
            rx, ry, rw, rh = hr
        else:
            # Fallback: top of the panel
            rx, ry, rw = panel_rect[0], panel_rect[1] + 4, panel_rect[2]
            rh = 30
        font = self.style.get_font(L.font_size(int(15 * hfs)))
        hx, hy = L.pos(rx, ry)
        hw, hh = L.size(rw, rh)
        h_surf = font.render(text, True, COL_PANEL_HEADER)
        surface.blit(h_surf, (hx + (hw - h_surf.get_width()) // 2,
                               hy + (hh - h_surf.get_height()) // 2))

    def _active_entry(self):
        return self._active

    # ── Input ─────────────────────────────────────────────

    def handle_click(self, screen_x, screen_y):
        """Click routing: frame buttons, category radios, specials."""
        # Modal: while the message box is up it swallows every click,
        # including the frame buttons underneath it.
        if self._popup.visible:
            self._popup.close()
            return None

        side = self._frame_button_side(screen_x, screen_y)
        if side == "left":
            self._btn_flash = (side, time.monotonic())
            self._reset_traits()
            self._active = None
            self._spec_scroll = 0
            self._desc_scroll = 0
            if self.app.connected:
                self.app.client.activate_field(self.FRAME_BTN_LEFT[1])
            log.info("Clear: all picks reset")
            return None
        if side == "right":
            self._btn_flash = (side, time.monotonic())
            # The game refuses an overspent race and answers with its
            # own error box. Testing here means orion2re never sees the
            # invalid Accept, so no framebuffer popup has to be
            # dismissed and the HD screen is never left behind.
            if self.picks_remaining < 0:
                self._popup.open(self._message("picks_negative",
                                               MSG_PICKS_NEGATIVE))
                log.info("Accept blocked: %d picks remaining",
                         self.picks_remaining)
                return None
            if self.app.connected:
                self.app.client.activate_field(self.FRAME_BTN_RIGHT[1])
            log.info("Accept")
            # Interim routing (no C++ patch yet): the original banner /
            # name dialogs report no ID of their own, orion2re falls
            # back to 6 (SCREEN_RACE) after Accept. Hold the HD screen
            # for 50 and 6; anything else (13 New Game, 0 Galaxy Map)
            # releases it.
            self.app.dispatcher.switch_to("empire_identity",
                                          lock_ids=(50, 6))
            return None

        L = self.layout

        # Race Picks: select an option within its category
        hit = picks_hit_test(L, self._categories,
                             self._panels.get("picks", (0, 0, 0, 0)),
                             self._panel_fs.get("picks", 1.0),
                             screen_x, screen_y)
        if hit:
            cat, opt = hit
            trait_id, value = cat["trait_id"], opt["value"]
            # No "Normal" row: clicking the active option clears it.
            # Government always keeps a selection (as in the original).
            if self._trait_state.get(trait_id) == value:
                if trait_id != 0:
                    self._trait_state[trait_id] = 0
            else:
                self._trait_state[trait_id] = value
            # Send to the game (all Custom Race fields are type=7,
            # so ACTIVATE_FIELD works — no INJECT_CLICK needed)
            fid = opt.get("field_id")
            if fid is not None and self.app.connected:
                self.app.client.activate_field(fid)
            # Options may carry their own text (governments do);
            # otherwise the category text is shown.
            if opt.get("description"):
                self._set_active({"name": opt["label"],
                                  "description": opt["description"]})
            else:
                self._set_active(cat)
            return None

        # Special Abilities: toggle the checkbox
        spec = specials_hit_test(L, self._specials,
                                self._panels.get("specials", (0, 0, 0, 0)),
                                 self._panel_fs.get("specials", 1.0),
                                 self._spec_scroll,
                                 screen_x, screen_y)
        if spec is not None:
            self._toggle_special(spec)
            self._set_active(spec)
            fid = spec.get("field_id")
            if fid is not None and self.app.connected:
                self.app.client.activate_field(fid)
            return None

        return super().handle_click(screen_x, screen_y)

    def _toggle_special(self, spec):
        """Toggle a special ability, honouring exclusive groups.

        Traits in the same group (Low-G/High-G, Rich/Poor Home
        World, Creative/Uncreative, Repulsive/Charismatic) cannot
        be active at the same time. Rich and Poor Home World share
        one trait_id and differ by their signed value.
        """
        trait_id = spec["trait_id"]
        value = spec.get("value", 1)
        if self._trait_state.get(trait_id, 0) == value:
            self._trait_state[trait_id] = 0
            return
        group = spec.get("group")
        if group:
            for other in self._specials:
                if other.get("group") == group and other is not spec:
                    self._trait_state[other["trait_id"]] = 0
        self._trait_state[trait_id] = value

    def _set_active(self, entry):
        """Show a trait (category or special) in the description."""
        if entry is not self._active:
            self._desc_scroll = 0
        self._active = entry

    def handle_mousewheel(self, direction, mx, my):
        """Scroll the specials list or the description text."""
        if self._popup.visible:
            return
        L = self.layout
        step = 40
        spec_fs = self._panel_fs.get("specials", 1.0)
        desc_fs = self._panel_fs.get("description", 1.0)

        for key, content_h in (
                ("specials",
                 specials_content_height(self._specials, spec_fs)),
                ("description",
                 description_height(self._active_entry(), L, self.style,
                                    self._panels.get("description",
                                                     (0, 0, 0, 0)),
                                    desc_fs))):
            rect = self._panels.get(key)
            if not rect:
                continue
            px, py = L.pos(rect[0], rect[1])
            pw, ph = L.size(rect[2], rect[3])
            if not pygame.Rect(px, py, pw, ph).collidepoint(mx, my):
                continue
            max_scroll = max(0, content_h - rect[3])
            attr = ("_spec_scroll" if key == "specials"
                    else "_desc_scroll")
            value = getattr(self, attr) - direction * step
            setattr(self, attr, max(0, min(max_scroll, value)))
            return

    def handle_key(self, key):
        # Any key dismisses the message box, and none of them reaches
        # the game — ESC would otherwise cancel the whole screen.
        if self._popup.visible:
            self._popup.close()
            return
        if key == pygame.K_ESCAPE:
            if self.app.connected:
                # Field 2 is the ESC hotkey — ACTIVATE_FIELD returns
                # it as _exit_ken which triggers the cancel path in
                # Racial_Option_Screen_().
                self.app.client.activate_field(2)
        else:
            super().handle_key(key)
