"""Base class for all HD screens.

Every screen inherits from ScreenBase and implements:
  enter()   — called when the screen becomes active
  update()  — per-frame data update (no rendering)
  render()  — draw to surface
  exit()    — cleanup when leaving

Every screen stands on the background `core.backgrounds` resolves
for it (work order 173): its own picture, else the universal one.
"""
import os
import time
import pygame

from core.pressfeedback import Pressed
from core.box import load_boxes
from core.config import REF_W, REF_H
from core.screenhelp import HelpMixin
from core import backgrounds
from core.hud import screenframe

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
        self._frame = None         # a screen's own fixed frame image
        self._frame_scaled = None  # scaled to the reference area
        self._frame_pos = (0, 0)
        self._btn_flash = None   # ("left"|"right", start_time)
        self.pressed = Pressed()  # a held press on a word (pressfeedback)

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

    def wants_original(self):
        """True when this screen cannot vouch for what it would draw.

        Decision 22 promises the game stays playable on a screen HD
        does not know. This is the same promise one step in: a screen
        that DOES know the id but cannot trust its own picture — an
        extractor file absent, a reconstruction the game's field list
        contradicts — hands over to the original view rather than draw
        a list it cannot vouch for.

        `App._showing_original` asks this, so such a screen gets the
        game's own picture AND the click forwarding that came with it
        in work order 130 A. False here: a screen says so for itself.
        """
        return False

    def exit(self):
        """Screen deactivated. Clean up."""
        self.active = False
        self.boxes = []
        self.help.close()

    def update(self, game_state=None):
        """Per-frame data update. No rendering here."""
        pass

    def render(self, surface):
        """Draw the screen. Background, boxes, frame, content, help."""
        if not self.draws_this_frame():
            return
        self._render_background(surface)
        for box in self.boxes:
            box.render(surface, self.layout, self.style)
        if self.USE_FRAME:
            self._render_frame(surface)
        self.render_content(surface)
        self.render_help(surface)

    def draws_this_frame(self):
        """False when the screen has nothing it may draw AT ALL.

        Not the same question as `wants_original`: that one asks for
        the GAME's picture; this one asks for nothing, so whatever is
        already on the surface stands — for an OVERLAY that is the
        parent screen underneath it.

        Work order 166 part A: the research panel says False while the
        game has not built its field list, so change mode shows the HD
        galaxy map it is a panel over, rather than an empty frame that
        fills in a third of a second later. A screen that is not an
        overlay has nothing underneath and draws its own empty self
        instead — the Fleets screen's answer to the same moment (work
        order 142 A).
        """
        return True

    def render_content(self, surface):
        """What the screen draws OVER its boxes. The base draws nothing.

        **THE HELP POPUP HAS TO BE LAST**, and this hook is what makes
        that true for a screen that draws content of its own. A screen
        that calls `super().render(surface)` and then draws is drawing
        over a popup that has already been painted — found on the two
        research screens while work order 165 part C built the
        description box, which is the same popup: right-click help
        opened there and the panel's own text was painted across it.
        """
        return None

    def editor_note(self, box):
        """One line about `box` for the F5 editor's info bar, or None.

        **The screen owns what a box MEANS; the editor owns the
        chrome.** A geometry value that is derived — a row band, a
        sprite step, a lower bound the editor must report and never
        clamp — has no rect for the editor to show, so without this
        the person dragging is dragging blind.

        It replaces a `hasattr(scr, "_race_by_id")` in
        `core.editor.overlay.draw_info`: generic editor code that
        named ONE screen and reached into it. A hook is the same
        information with the knowledge on the side that has it.

        Plain text. The overlay appends it to the box's own line and
        does not parse it.
        """
        return None

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

    def handle_left_release(self, screen_x, screen_y):
        """The press ends (core.pressfeedback)."""
        self.pressed.release()

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
        """The screen's BACKGROUND SLOT — decision 71, filled by work
        order 173: `core.backgrounds` resolves the picture (the screen's
        own, else Data's universal one, else the placeholder; the mod
        folder's file of the same name first, decision 72) and keeps one
        cover-scaled copy per window size for every screen that shares
        it. Nothing is held here that a resize could leave stale.

        The shared cockpit texture used to be the fallback here. It was
        part of the cockpit look decision 71 replaces, so it is no longer
        drawn behind a screen; the file stays in the tree.
        """

    def _scale_background(self):
        """Nothing to do: `core.backgrounds` scales per window size."""

    @property
    def _bg_scaled(self):
        """The background at the window's size (a popup's `backdrop`)."""
        return backgrounds.scaled(self.SCREEN_NAME, self.app.win_w,
                                  self.app.win_h)

    def _render_background(self, surface):
        """The background slot's picture, or the dark placeholder."""
        backgrounds.draw(surface, self.SCREEN_NAME)

    # --- Fixed frame image (screens that wear one PNG over their content) ---
    #
    # Extracted 17 September 2026 (work order 126 I): the colony summary,
    # the galaxy map and planets each carried this load, scale and blit,
    # identical but for spelling — and every screen still to be built with
    # a fixed frame would have pasted it a fourth time. Opt-in: a screen
    # calls `_load_frame` from `enter`, `_scale_frame` from `on_resize` and
    # `_render_frame_image` where the frame goes in its draw order.

    def _load_frame(self, image="frame.png"):
        """The frame; stretched over the reference area so its holes
        coincide with the boxes measured out of them."""
        path = self.asset_path("assets", image)
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

    def _render_frame_image(self, surface):
        """NOTHING IS DRAWN HERE SINCE DECISION 71 (work order 169).

        The fixed frame images are replaced by the HUD blocks, which each
        screen draws in its own `render`. This method, `_load_frame` and
        `_scale_frame` stay, as the order that recorded 71 asks — a later
        order removes them with the images — but no screen's picture
        goes through them any more. `USE_FRAME` screens get the HUD's
        title plate and buttons from `_render_frame` below."""
        if self.USE_FRAME:
            self._render_frame(surface)

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

    def box_screen_rect(self, name):
        """A named box's WINDOW rect as `Box.update_layout` placed it —
        anchors included (work order 170) — or None. Where a box may be
        anchored to the window's edge, this is the rect to draw and hit
        with; `layout.rect(box_rect(name))` is the content-area rect."""
        for box in self.boxes:
            if box.name == name and box.screen_rect is not None:
                return pygame.Rect(box.screen_rect)
        return None

    def box_style(self, name):
        """A named box's style dict, or {} when there is no such box.

        Extracted 17 September 2026 (work order 126 I): colony summary,
        galaxy map, empire identity (`_box_style`) and planets
        (`planetdraw._style`) each carried this loop, identical but for
        the name — the fourth copy of a lookup whose siblings live here.
        """
        for box in self.boxes:
            if box.name == name:
                return box.style
        return {}

    def box_font_scale_stored(self, name):
        """A box's `font_scale` as boxes.json holds it. No auto-factor.

        **USE THIS WHEREVER `Layout.font_size` IS APPLIED AFTERWARDS.**
        `box_font_scale` multiplies by `win_h / 1080` and `font_size`
        multiplies by the window scale as well, so the two together
        square the resolution factor: 1.0 at 1080p, 1.78 at 1440p and
        **4.0 at 2160p against an intended 2.0**. Where a box carries
        a value that was tuned by eye with both in place, that is what
        makes the tuning land; where it carries none — every box on
        the colony summary — there is nothing to cancel it and the
        text comes out twice the size at 4K.

        Extracted 7 September 2026 from `screenhelp._help_font_scale`,
        which had worked this out for the help popup and solved it
        privately. The colony summary's empire readouts were the
        second case, and a second private copy is how the third one
        gets written too.
        """
        for box in self.boxes:
            if box.name == name:
                return box.style.get("font_scale", 1.0)
        return 1.0

    def box_font_scale(self, name):
        """A box's font_scale times the resolution auto-factor.

        For a caller that sizes text DIRECTLY. A caller that then goes
        through `Layout.font_size` wants `box_font_scale_stored` —
        see there for what taking both does.
        """
        return self.box_font_scale_stored(name) * (self.app.win_h / 1080.0)

    # --- Internal ---

    def _update_box_layout(self):
        """Set window rects for all boxes. Once on enter/resize."""
        for box in self.boxes:
            box.update_layout(self.layout)

    def _render_frame(self, surface):
        """The HUD's title plate and the two frame buttons — decision 71.
        See `core.hud.screenframe`."""
        screenframe.render(self, surface)

    def hud_frame_button_rect(self, side):
        """Where frame button `side` is drawn AND hit (decision 5); the
        click is still handled here, in `handle_click` (decision 13)."""
        return screenframe.button_rect(self, side)

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
        should still trigger local behaviour. Since decision 71 it asks
        the HUD buttons, through the rect they are drawn in."""
        return screenframe.side_at(self, screen_x, screen_y)

    def _frame_button_hit(self, screen_x, screen_y):
        """Check if a click hit a frame button. Returns field_id or None."""
        side = self._frame_button_side(screen_x, screen_y)
        if side == "left":
            return self.FRAME_BTN_LEFT[1]
        if side == "right":
            return self.FRAME_BTN_RIGHT[1]
        return None
