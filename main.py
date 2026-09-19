"""OrionLayer v3 — HD frontend for orion2re."""
import sys
import logging
import pygame
from core.config import (load_settings, TARGET_FPS, SCREENS_DIR,
                         build_line)
from core import resources, palette, usersettings
from core import cursor as cursor_gfx
from core import mouse as mouse_input
from core.layout import Layout
from core.style import StyleRenderer
from core.dispatcher import Dispatcher
from core.game_client import GameClient
from core.original_view import OriginalView
from core.editor import Editor
from core import fallbacknote
from core import helppopup

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s.%(msecs)03d %(name)s: %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("orionlayer")




class App:
    def __init__(self):
        pygame.init()
        # FIRST LINE OF EVERY LOG (work order 139 C). 138 could not say
        # which commit Data's run was on, and the answer decided
        # whether a rule that had never run live was even in that
        # build. `build_line` asks git and degrades to "unknown"; it
        # raises nothing, because a diagnostic that takes the program
        # down is worse than no diagnostic.
        log.info("build: %s", build_line())
        self.settings = load_settings()
        self.screens_dir = SCREENS_DIR

        # Mod-aware resource resolver (must run before anything loads)
        self.res = resources.init(self.settings)

        # The player's own OrionLayer settings BEFORE the palette: the
        # colour preset is applied by palette.init, and every screen
        # binds its colours at import (decision 18, fundament 63).
        self.user_settings = usersettings.load()

        # Skin colors (per-screen palettes resolve at screen import)
        skin = self.settings.get("skin", "default")
        self.colors = self.res.load_json(
            f"assets/shared/skins/{skin}/colors.json", {})
        palette.init(self.colors,
                     preset=self.user_settings.get("player_colors"),
                     base=self.user_settings.get("player_color_base"))

        # Window
        win = self.settings.get("window", {})
        self.win_w = win.get("width", 1920)
        self.win_h = win.get("height", 1080)
        flags = pygame.RESIZABLE if win.get("resizable", True) else 0
        if win.get("fullscreen", False):
            flags |= pygame.FULLSCREEN
        self.surface = self._set_mode(self.win_w, self.win_h, flags)
        pygame.display.set_caption("OrionLayer v3")

        # Custom cursor
        self._load_cursor()

        # Layout (reference -> window scaling)
        self.layout = Layout(self.win_w, self.win_h)

        # Style renderer (skins, font, corners) — mod-resolved
        skin_dir = self.res.skin_dir()
        font_path = self.res.font() or ""
        self.style = StyleRenderer(skin_dir, font_path, self.colors)

        # Game client (TCP connection to orion2re)
        self.client = GameClient()
        self.connected = False

        # Original view (framebuffer fallback)
        self.original_view = OriginalView()

        # Render mode: "original", "hd"
        self.render_mode = self.settings.get("render_mode", "hd")

        # Dispatcher + screens + editor
        self.dispatcher = Dispatcher()
        self._register_screens()
        self.dispatcher.switch_to("main_menu")
        self.editor = Editor(self)

        self.clock = pygame.time.Clock()
        self.running = True
        self._fullscreen = False
        self._ignore_resize = False
        self._fs_surface = None
        self._fs_offset = None
        mouse_input.set_offset(None)
        self._fs_native = None
        #: What `_showing_original` last decided and why, so the log
        #: carries a CHANGE and never a frame count (work order 139 A).
        self._reporter = fallbacknote.Reporter()
        #: The sentence to draw over the game's picture while an HD
        #: screen with a known id is handing over, or None (139 D).
        self._fallback_note = None
        #: The cockpit fill the note writes on, and its wording. Same
        #: source as the help popup's, for the reason that entry gives
        #: (work order 139 D).
        self._note_backdrop = helppopup.Backdrop()
        self._note_labels = self.res.load_json(
            "assets/shared/fallback/labels.json", {}) or {}

        # Resolution presets (F9 to cycle)
        self._resolutions = [
            (1920, 1080, "1080p"),
            (2560, 1440, "1440p"),
            (3440, 1440, "Ultrawide"),
            (3840, 2160, "4K"),
        ]
        self._res_index = next(
            (i for i, r in enumerate(self._resolutions)
             if r[0] == self.win_w and r[1] == self.win_h),
            1
        )

        # Try connecting to orion2re
        self._connect()

    def _load_cursor(self):
        """Custom sci-fi cursor (mod-overridable), sized to the window.

        The artwork is 4K-sized; core.cursor scales it to the same
        share of screen height the original's cursor occupies, and is
        called again after every resolution change.
        """
        cursor_gfx.apply(self.res, self.win_h, self.settings)

    def _connect(self):
        """Connect to orion2re Extension API."""
        cfg = self.settings.get("orion2re", {})
        host = cfg.get("host", "localhost")
        port = cfg.get("port", 17362)
        self.connected = self.client.connect(host=host, port=port)
        if self.connected:
            log.info(f"Connected to orion2re at {host}:{port}")
        else:
            log.warning(f"Could not connect to orion2re at {host}:{port}")
            log.info("Running in standalone mode (no game data)")

    def _register_screens(self):
        """Auto-discover screens in screens/ and active mods."""
        from core.screens_loader import register_all
        register_all(self, self.dispatcher, self.res)

    def run(self):
        """Main loop."""
        while self.running:
            self._handle_events()
            self._update()
            self._render()
            self.clock.tick(TARGET_FPS)

        self.client.disconnect()
        pygame.quit()
        sys.exit()
    def _handle_events(self):
        for event in pygame.event.get():
            # Adjust mouse positions for fullscreen offset
            if self._fs_offset and hasattr(event, 'pos'):
                ox, oy = self._fs_offset
                adjusted = (event.pos[0] - ox, event.pos[1] - oy)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    event = pygame.event.Event(event.type,
                        button=event.button, pos=adjusted)
                elif event.type == pygame.MOUSEBUTTONUP:
                    event = pygame.event.Event(event.type,
                        button=event.button, pos=adjusted)
                elif event.type == pygame.MOUSEMOTION:
                    event = pygame.event.Event(event.type,
                        pos=adjusted, rel=event.rel,
                        buttons=event.buttons)

            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                if self._ignore_resize:
                    self._ignore_resize = False
                else:
                    self._on_resize(event.w, event.h)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F5:
                    self.editor.toggle()
                elif event.key == pygame.K_F11:
                    self._toggle_fullscreen()
                elif event.key == pygame.K_F9 and not self._fullscreen:
                    self._cycle_resolution()
                elif event.key == pygame.K_F12:
                    self._cycle_render_mode()
                elif not self.editor.handle_event(event):
                    self.dispatcher.route_key_event(event)
            elif self.editor.handle_event(event):
                pass  # editor consumed it
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(*event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # The end of a held press, duck-typed like the right button:
                # screens with a drag (the GAME menu's volume bars) answer.
                top = self.dispatcher.top
                if top and hasattr(top, "handle_left_release") \
                        and not self.editor.active:
                    top.handle_left_release(*event.pos)
            elif (event.type in (pygame.MOUSEBUTTONDOWN,
                                 pygame.MOUSEBUTTONUP)
                  and event.button == 3):
                # Right button, duck-typed like handle_mousewheel:
                # screens that pan (galaxy map) implement it, all
                # others simply do not answer.
                top = self.dispatcher.top
                if top and hasattr(top, "handle_right_button"):
                    down = event.type == pygame.MOUSEBUTTONDOWN
                    top.handle_right_button(down, *event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self.dispatcher.route_motion(*event.pos)
            elif event.type == pygame.MOUSEWHEEL:
                if not self.editor.handle_event(event):
                    top = self.dispatcher.top
                    if top and hasattr(top, "handle_mousewheel"):
                        mx, my = mouse_input.pos()
                        top.handle_mousewheel(event.y, mx, my)

    def _adjust_mouse(self, x, y):
        """Adjust mouse coordinates for fullscreen offset.

        Kept as a method because callers exist; the arithmetic itself
        lives in core.mouse so hover, wheel and the editor cannot
        drift apart from it.
        """
        return mouse_input.adjust(x, y)

    def _showing_original(self):
        """True when the window shows orion2re's own framebuffer.

        TWO WAYS IN, ONE VIEW. F12's render mode is one; the
        dispatcher's fallback for a screen id no HD screen claims
        (decision 22) is the other. They differ in how they are
        entered and in nothing else, so the renderer and the click
        handler both ask this one question rather than each testing
        for a mode (decision 9 — the framebuffer path has one home).

        Work order 130 A. Until then `use_original` was set by the
        dispatcher and read by nothing: the fallback filled the window
        with a flat colour and swallowed every click, so the two
        turn-start research dialogs (52, 53) were a dead end inside
        OrionLayer's window.
        """
        if not self.connected:
            return self._verdict(False, None)
        if self.render_mode == "original" or self.dispatcher.use_original:
            return self._verdict(True, None)
        # A THIRD WAY IN, work order 130 E: a screen that KNOWS the id
        # but cannot vouch for what it would draw. The research select
        # screen does this when the game's field list contradicts its
        # reconstruction or the extracted names are absent — it hands
        # over rather than draw a list it cannot stand behind, and the
        # player answers the dialog through the picture instead.
        top = self.dispatcher.top
        if top is not None and top.wants_original():
            return self._verdict(True, top)
        return self._verdict(False, top)

    def _verdict(self, shown, top):
        """Return the decision, and report it. Work order 139 A.

        ONE PLACE, because this is the one place the question is
        answered: every screen that hands over passes through
        `_showing_original`, so none of them needs a rule or a log call
        of its own. Until now `fallback_reason()` had exactly one
        caller in the whole tree — `tools/researchphases.py` — and a
        player saw a screen that did not appear with nothing anywhere
        saying why (work order 138).

        The reporting itself lives in `core.fallbacknote`, beside the
        drawing of the same sentence: they are one behaviour and the
        log line and the note must never be able to disagree.
        """
        sid = (getattr(self.client.state, "current_screen", -1)
               if self.connected else -1)
        self._fallback_note = self._reporter.note(
            shown, top, self.dispatcher, sid)
        return shown

    def _handle_click(self, screen_x, screen_y):
        if self.editor.active:
            return  # editor handles all clicks
        if self._showing_original():
            self.original_view.forward_click(
                self.client, screen_x, screen_y,
                self.win_w, self.win_h)
        elif self.dispatcher.active:
            self.dispatcher.route_click(screen_x, screen_y)

    def _update(self):
        """Poll game state and update active screen + overlay."""
        state = None
        if self.connected:
            self.client.poll()
            if self.client.game_ended:
                # QUIT -> YES in the GAME menu: the player asked the
                # game to end, the client stood its watchdog down
                # before sending YES, and OrionLayer ends with it
                # (decision 62). No reconnect, no "game ended" screen.
                log.info("orion2re ended at the player's request; "
                         "OrionLayer exits with it")
                self.running = False
                return
            state = self.client.state

            if state.framebuffer and state.palette:
                self.original_view.update(state.framebuffer, state.palette)

            if state.current_screen >= 0:
                self.dispatcher.update_from_game(state)

        self.dispatcher.update_screens(state)

    def _render(self):
        """Render based on current mode."""
        if self._showing_original():
            picture = self.original_view.render(self.surface, self.layout)
            # WORK ORDER 139 D — the reason, where the player is
            # looking. Drawn AFTER the picture and outside it, and it
            # is drawing only: `_handle_click` above forwards every
            # click to the game whatever this returns.
            fallbacknote.render(self.surface, self.style, self.res,
                                self._note_backdrop, self._fallback_note,
                                self._note_labels, picture)
            if self.render_mode == "original":
                # The status bar belongs to the F12 MODE, not to the
                # picture: it names the mode and the key that leaves it.
                # The fallback is not a mode and has no key, and Data
                # chose the plain forwarding fallback over the one with
                # a visible hint (work order 130, decided; 129 parked
                # point 1, option a over option c). This one line is the
                # only difference between the two entries.
                state = self.client.state
                self.original_view.render_status_bar(
                    self.surface, self.style, self.colors, state,
                    self.dispatcher.screen_name_for(state.current_screen),
                    self.render_mode)
        elif self.dispatcher.active:
            self.surface.fill((4, 6, 14))
            self.dispatcher.render(self.surface)
        else:
            self.surface.fill((6, 8, 16))

        self.editor.render(self.surface)
        if self._fs_surface:
            self._fs_surface.fill((0, 0, 0))
            self._fs_surface.blit(self.surface, self._fs_offset)
        pygame.display.flip()

    def _cycle_render_mode(self):
        """F12: cycle through render modes."""
        modes = ["original", "hd"]
        idx = (modes.index(self.render_mode)
               if self.render_mode in modes else 0)
        self.render_mode = modes[(idx + 1) % len(modes)]
        log.info(f"Render mode: {self.render_mode}")

    def _set_mode(self, w, h, flags):
        """`set_mode`, and ADOPT the size that was actually granted.

        **A REQUESTED SIZE IS NOT A WINDOW SIZE.** The window manager
        may give less than was asked for, and on this project's own
        machine it does: measured 9 September 2026 on a single
        3440x1440 display, a request for 2560x1440 is granted
        2560x1371, 3440x1440 is granted 3440x1371, and 3840x2160 —
        which is one of the four sizes F9 offers — is granted
        3440x1371. **No `VIDEORESIZE` event is delivered for any of
        them**, so nothing downstream can notice on its own, and
        `_ignore_resize` (which exists to swallow the event a
        deliberate resolution change provokes) was never even reached.

        `win_w`/`win_h` used to be the numbers we asked for, and
        `Layout`, every box, the cursor and the frame plate are all
        built from them. At F9 "4K" the whole screen was therefore
        laid out for 3840x2160 inside a 3440x1371 surface: 1.12x too
        wide, 1.58x too tall, everything past the edge simply gone.
        Milder but live at every other size too — 2560x1440 got 69 px
        of height it did not have. That is
        `after_geometry_3840x2160.png` in the fixtures, whose FILE
        NAME is the request and whose pixels are the grant.

        The difference is REPORTED and not merely absorbed, because a
        window that is quietly smaller than the one configured is a
        state somebody has to be able to see in a log rather than
        infer from a screenshot. The formatter carries the timestamp
        (see `basicConfig` above), which is what makes the line
        placeable against a resize the user remembers making.
        """
        surface = pygame.display.set_mode((w, h), flags)
        got_w, got_h = surface.get_size()
        if (got_w, got_h) != (w, h):
            log.warning(
                "window: asked for %dx%d, granted %dx%d — laying out "
                "for what was granted", w, h, got_w, got_h)
        self.win_w, self.win_h = got_w, got_h
        return surface

    def _apply_resolution(self, w, h, caption=None):
        """Set windowed mode at (w, h) and refresh layout/caches/screens."""
        self.surface = self._set_mode(w, h, pygame.RESIZABLE)
        if caption:
            pygame.display.set_caption(f"OrionLayer v3 — {caption}")
        self._after_resolution_change()

    def _after_resolution_change(self):
        """Common refresh after any resolution/surface change."""
        self.layout.update(self.win_w, self.win_h)
        self.style.clear_caches()
        cursor_gfx.apply(self.res, self.win_h, self.settings)
        # DROP THE EDITOR'S SELECTION, because `dispatcher.on_resize`
        # reaches `ScreenBase._reload_boxes`, which REPLACES every Box
        # object — and `Editor.selected` is the one other place in the
        # tree that holds one across frames. A stale selection draws
        # its outline from a device rect computed for the previous
        # window, and worse, `save_boxes` writes `scr.boxes`, so a
        # drag on the discarded object is silently thrown away. Found
        # by the sweep for retained Box references, 9 September 2026;
        # same class as the colony column table one commit back.
        self.editor.selected = None
        self.dispatcher.on_resize()

    def _on_resize(self, new_w, new_h):
        """Window resized."""
        min_w = self.settings.get("window", {}).get("min_width", 1280)
        min_h = self.settings.get("window", {}).get("min_height", 720)
        self._apply_resolution(max(new_w, min_w), max(new_h, min_h))

    def _toggle_fullscreen(self):
        """F11: toggle fullscreen with black bars at current F9 resolution."""
        self._ignore_resize = True
        self._fullscreen = not self._fullscreen
        if self._fullscreen:
            # Get native monitor resolution
            try:
                sizes = pygame.display.get_desktop_sizes()
                native_w, native_h = sizes[0]
            except (AttributeError, IndexError):
                info = pygame.display.Info()
                native_w = info.current_w
                native_h = info.current_h
            # Open fullscreen at native resolution.
            #
            # NOT through `_set_mode`: that adopts the granted size
            # into `win_w`/`win_h`, and here those must stay the F9
            # CONTENT size — the surface below is a plain Surface of
            # exactly that size, blitted into the middle of the
            # display. What is read back is the DISPLAY, because the
            # centring offset and `_fs_native` are about it and a
            # refused native size would put the content off centre
            # by half the difference.
            self._fs_surface = pygame.display.set_mode(
                (native_w, native_h), pygame.FULLSCREEN
            )
            got_w, got_h = self._fs_surface.get_size()
            if (got_w, got_h) != (native_w, native_h):
                log.warning(
                    "fullscreen: asked for %dx%d, granted %dx%d — "
                    "centring on what was granted",
                    native_w, native_h, got_w, got_h)
            native_w, native_h = got_w, got_h
            # Content rendered at F9 resolution, centered
            w, h, label = self._resolutions[self._res_index]
            self.win_w = w
            self.win_h = h
            self.surface = pygame.Surface((w, h))
            # Offset for centering content on native screen
            self._fs_offset = ((native_w - w) // 2, (native_h - h) // 2)
            mouse_input.set_offset(self._fs_offset)
            self._fs_native = (native_w, native_h)
            self._after_resolution_change()
        else:
            self._fs_surface = None
            self._fs_offset = None
            self._fs_native = None
            mouse_input.set_offset(None)
            w, h, label = self._resolutions[self._res_index]
            self._apply_resolution(w, h, caption=label)

    def _cycle_resolution(self):
        """F9: cycle window resolution."""
        self._res_index = (self._res_index + 1) % len(self._resolutions)
        w, h, label = self._resolutions[self._res_index]
        self._ignore_resize = True
        self._apply_resolution(w, h, caption=label)


if __name__ == "__main__":
    app = App()
    app.run()
