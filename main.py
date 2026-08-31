"""OrionLayer v3 — HD frontend for orion2re."""
import sys
import logging
import pygame
from core.config import load_settings, TARGET_FPS, SCREENS_DIR
from core import resources, palette
from core import cursor as cursor_gfx
from core import mouse as mouse_input
from core.layout import Layout
from core.style import StyleRenderer
from core.dispatcher import Dispatcher
from core.game_client import GameClient
from core.original_view import OriginalView
from core.editor import Editor

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s.%(msecs)03d %(name)s: %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("orionlayer")


class App:
    def __init__(self):
        pygame.init()
        self.settings = load_settings()
        self.screens_dir = SCREENS_DIR

        # Mod-aware resource resolver (must run before anything loads)
        self.res = resources.init(self.settings)

        # Skin colors (per-screen palettes resolve at screen import)
        skin = self.settings.get("skin", "default")
        self.colors = self.res.load_json(
            f"assets/shared/skins/{skin}/colors.json", {})
        palette.init(self.colors)

        # Window
        win = self.settings.get("window", {})
        self.win_w = win.get("width", 1920)
        self.win_h = win.get("height", 1080)
        flags = pygame.RESIZABLE if win.get("resizable", True) else 0
        if win.get("fullscreen", False):
            flags |= pygame.FULLSCREEN
        self.surface = pygame.display.set_mode(
            (self.win_w, self.win_h), flags
        )
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

    def _handle_click(self, screen_x, screen_y):
        if self.editor.active:
            return  # editor handles all clicks
        if self.render_mode == "original" and self.connected:
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
            state = self.client.state

            if state.framebuffer and state.palette:
                self.original_view.update(state.framebuffer, state.palette)

            if state.current_screen >= 0:
                self.dispatcher.update_from_game(state)

        self.dispatcher.update_screens(state)

    def _render(self):
        """Render based on current mode."""
        if self.render_mode == "original" and self.connected:
            self.original_view.render(self.surface, self.layout)
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

    def _apply_resolution(self, w, h, caption=None):
        """Set windowed mode at (w, h) and refresh layout/caches/screens."""
        self.win_w = w
        self.win_h = h
        self.surface = pygame.display.set_mode(
            (w, h), pygame.RESIZABLE
        )
        if caption:
            pygame.display.set_caption(f"OrionLayer v3 — {caption}")
        self._after_resolution_change()

    def _after_resolution_change(self):
        """Common refresh after any resolution/surface change."""
        self.layout.update(self.win_w, self.win_h)
        self.style.clear_caches()
        cursor_gfx.apply(self.res, self.win_h, self.settings)
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
            # Open fullscreen at native resolution
            self._fs_surface = pygame.display.set_mode(
                (native_w, native_h), pygame.FULLSCREEN
            )
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
