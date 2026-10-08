"""Main Menu Screen — Logo + Credit Scrolling + Buttons."""
import re
import time
import pygame
from core import palette
from core.config import ORION2RE_VERSION
from core.hud import shell
from core.screen_base import ScreenBase

# A credit line is "role <dots> name". The dot run is a separator, not
# a length: the source file keeps the original's fixed-width columns,
# so a long role leaves room for a single dot ("Compatibility Lead .")
# while a short one gets a dozen. What makes it a separator is the
# whitespace on both sides — that is why "1.50" is not split at its
# own dot. Indented lines are continuation names and are never split.
SEPARATOR = re.compile(r"^(.+?)\s+\.+\s*(.+)$")


def parse_credits(text):
    """Text -> [(kind, string)] with kind in role / name / blank."""
    out = []
    for line in text.splitlines():
        line = line.rstrip("\n")
        if not line.strip():
            out.append(("blank", ""))
        elif line.startswith(" "):
            out.append(("name", line.strip()))
        else:
            m = SEPARATOR.match(line)
            if m:
                out.append(("role", m.group(1).strip()))
                out.append(("name", m.group(2).strip()))
            else:
                out.append(("role", line.strip()))
    return out

# Skin-overridable colors (colors.json section "main_menu")
COLOR_ROLE = palette.col("main_menu", "credit_role", (220, 180, 60))
COLOR_NAME = palette.col("main_menu", "credit_name", (180, 210, 240))

# The original draws the version dimmer than the credits, and that
# difference is deliberate: measured off a native screenshot, the
# version glyphs are RGB (104, 56, 20) against the credits' (164,
# 100, 40) — palette index 0xD7 (mainmenu.cpp:290), 59 % of their
# luma. The default below is credit_role at that same ratio, so the
# HD screen keeps the relationship rather than the raw colour of a
# palette OrionLayer does not use.
COLOR_VERSION = palette.col("main_menu", "version", (130, 106, 36))

#: Box that carries the version string, filled at runtime.
VERSION_BOX = "version_text"


class MainMenuScreen(ScreenBase):
    SCREEN_NAME = "main_menu"
    GAME_SCREEN_ID = 10     # SCREEN_MAIN_MENU
    SHELL_WORN = True       # work order 225: the rectangle, no plate

    # Credit scroll config (all in reference pixels / seconds)
    SCROLL_SPEED = 45
    PAUSE_DURATION = 4.0
    FADE_TOP = 380         # above this y: invisible (under logo)
    FADE_TOP_DIST = 200    # fade-in distance below FADE_TOP
    FADE_BOT_DIST = 100    # fade-out distance from bottom
    CREDIT_X = 80          # left margin
    CREDIT_INDENT = 280    # name indent from role
    LINE_H = 32
    FONT_ROLE = 22
    FONT_NAME = 20

    def __init__(self, app):
        super().__init__(app)
        self._logo_orig = None
        self._logo_scaled = None
        self._credits = []
        self._scroll_y = 0.0
        self._total_h = 0
        self._paused = False
        self._pause_timer = 0.0
        self._last_time = 0.0

    def enter(self, game_state=None):
        super().enter(game_state)
        self._load_logo()
        self._load_credits()
        self._apply_version()
        self._reset_scroll()
        self._last_time = time.monotonic()

    def _apply_version(self):
        """Fill the version box — wording from JSON, number from code.

        The template lives in boxes.json so a translation replaces
        the word "Version" without touching this file; the number
        lives in core/config.ORION2RE_VERSION because it belongs to
        orion2re, not to this screen. Substitution is a plain replace
        rather than str.format, so a stray brace in a translated
        label cannot raise in the render path.
        """
        for box in self.boxes:
            if box.name == VERSION_BOX:
                template = box.style.get("label", "{version}")
                box.text = template.replace("{version}",
                                            ORION2RE_VERSION)
                box.text_color = COLOR_VERSION
                return

    def _load_logo(self):
        path = self.asset_path("assets", "logo.png")
        if path:
            self._logo_orig = pygame.image.load(path).convert_alpha()
            self._scale_logo()

    def _scale_logo(self):
        if not self._logo_orig:
            return
        ref_w = 700
        ow, oh = self._logo_orig.get_size()
        ref_h = int(ref_w * oh / ow)
        L = self.layout
        self._logo_scaled = pygame.transform.smoothscale(
            self._logo_orig, (int(ref_w * L.scale), int(ref_h * L.scale)))

    def _load_credits(self):
        path = self.asset_path("assets", "credits.txt")
        if not path:
            return
        with open(path, encoding="utf-8") as f:
            self._credits = parse_credits(f.read())
        self._credits += [("blank", ""), ("blank", "")]
        self._total_h = len(self._credits) * self.LINE_H

    def _reset_scroll(self):
        self._scroll_y = float(1080)  # start below reference screen
        self._paused = False
        self._pause_timer = 0.0

    # ── The Load dialog and the safety net (work order 177) ──

    def _load_dialog(self, game_state):
        """The main menu's LOAD GAME (mainmenu.cpp:132, :187-189) is the
        GAME popup's Load dialog, centred. With its save slots on the wire
        (open fix 34) the GAME menu overlay draws it, as in the GAME menu;
        without them the net shows the game's own picture of it — the
        rows' names are only there (DEVIATION `modal_fallback`)."""
        from screens.game_menu import nodes
        d = self.app.dispatcher
        is_load = nodes.classify(getattr(game_state, "fields", None)) in (
            nodes.LOAD, nodes.CONFIRM, nodes.WARNING)
        slots = getattr(game_state, "save_slots", None)
        if is_load and slots and d.overlay_name != "game_menu":
            d.open_overlay("game_menu", game_state)
        elif d.overlay_name == "game_menu" and not is_load:
            d.close_overlay()

    def _own_list(self, fields):
        """NEW GAME's hidden field, which the menu always builds
        (`Add_Hidden_Field_(0x19F, 0xD9, 0x237, 0xEE, "N")`,
        mainmenu.cpp:137)."""
        return any(f.hotkey == ord("N") and (f.x, f.y, f.x_end, f.y_end) ==
                   (0x19F, 0xD9, 0x237, 0xEE) for f in fields)

    #: Each menu button's own field, by hotkey and rectangle
    #: (`MAINMENU::Add_Main_Menu_Fields_`, mainmenu.cpp:110-140). The
    #: boxes' `field_id`s (1-6) are the list's indices ONLY when both
    #: CONTINUE and LOAD exist: without a continue save the engine adds no
    #: CONTINUE field and every index after it moves up by one — HALL OF
    #: FAME's 5 would then be QUIT (found by work order 188's reading).
    #: So a click resolves its button in the live list, and a button the
    #: game did not build sends nothing.
    BUTTON_FIELDS = {
        "continue": (ord("C"), (0x19F, 0xAC, 0x237, 0xC1)),
        "load_game": (ord("L"), (0x19F, 0xC3, 0x237, 0xD7)),
        "new_game": (ord("N"), (0x19F, 0xD9, 0x237, 0xEE)),
        "multiplayer": (ord("M"), (0x19F, 0xF0, 0x237, 0x104)),
        "hall_of_fame": (ord("H"), (0x19F, 0x106, 0x237, 0x11B)),
        "quit": (ord("Q"), (0x19F, 0x11D, 0x237, 0x132)),
    }

    def button_field(self, name, fields):
        """The live field of menu button `name`, or None."""
        hotkey, rect = self.BUTTON_FIELDS[name]
        return next((f for f in fields or [] if getattr(f, "index", 0) > 0
                     and f.hotkey == hotkey and
                     (f.x, f.y, f.x_end, f.y_end) == rect), None)

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        for box in self.boxes:
            if box.name in self.BUTTON_FIELDS and \
                    box.contains(screen_x, screen_y):
                state = getattr(self.app.client, "state", None)
                f = self.button_field(box.name,
                                      getattr(state, "fields", None))
                if f is not None and self.app.connected:
                    if box.name == "quit":
                        self._quitting()
                    self.app.client.activate_field(f.index)
                return box
        return super().handle_click(screen_x, screen_y)

    def handle_key(self, key):
        """Q is QUIT here too (`last_input_scan == 0x51`, mainmenu.cpp:521),
        while the menu's own list is up."""
        if key in (ord("q"), ord("Q")) and self.app.connected and \
                not self.help_consumes_key(key) and self.button_field(
                    "quit", getattr(getattr(self.app.client, "state", None),
                                    "fields", None)) is not None:
            self._quitting()
            self.app.client.inject_key(key)
            return
        super().handle_key(key)

    def _quitting(self):
        """QUIT ends the game at once, no question (mainmenu.cpp:521-523,
        SCREEN_EXIT): the client is told first, so the engine's going is
        the game's end and OrionLayer closes with it — as the GAME menu's
        QUIT does. Without it the silence read as a dead link: OrionLayer
        stayed open, reconnecting (work order 214, Data's report)."""
        self.app.client.expect_shutdown()

    def wants_original(self):
        return bool(getattr(self, "_net_on", False))

    def handover_is_modal(self):
        return True          # the net is this screen's only hand-over

    def update(self, game_state=None):
        if game_state is not None and getattr(self.app, "connected", False):
            if getattr(self, "_net", None) is None:
                from core import modalnet
                self._net = modalnet.Net(
                    "main menu", self._own_list,
                    known=(("load_with_slots",
                            lambda f: bool(self._slots_now)),))
            # The CURRENT snapshot's slots: a lambda over `game_state`
            # would hold the first snapshot's for ever.
            self._slots_now = getattr(game_state, "save_slots", None)
            self._load_dialog(game_state)
            self._net_on = self._net.check(game_state, self.GAME_SCREEN_ID)
        if not self._credits:
            return
        now = time.monotonic()
        dt = now - self._last_time
        self._last_time = now

        if self._paused:
            self._pause_timer -= dt
            if self._pause_timer <= 0:
                self._reset_scroll()
            return

        self._scroll_y -= self.SCROLL_SPEED * dt
        if self._scroll_y < -self._total_h:
            self._paused = True
            self._pause_timer = self.PAUSE_DURATION

    def render(self, surface):
        self._render_background(surface)
        self._render_credits(surface)

        # Logo (top-left of the CONTENT area, as the buttons are placed in
        # it: on a window wider than 16:9 both move in by the pillar band,
        # work order 224, D4)
        # The logo at the shell's content rectangle's top-left corner (work
        # order 225): the main menu has no title in the game, so it wears
        # no plate and takes only the rectangle (decision 89).
        if self._logo_scaled:
            x, y, _w, _h = shell.content_ref()
            surface.blit(self._logo_scaled, self.layout.pos(x, y))

        for box in self.boxes:
            box.render(surface, self.layout, self.style)

        # Last, so the popup covers the logo and the credit scroll.
        self.render_help(surface)

    def _render_credits(self, surface):
        if not self._credits:
            return
        L = self.layout
        ref_h = 1080

        for i, (typ, text) in enumerate(self._credits):
            if typ == "blank":
                continue
            ref_y = self._scroll_y + i * self.LINE_H

            # Skip if off-screen in reference space
            if ref_y < -self.LINE_H or ref_y > ref_h + self.LINE_H:
                continue

            # Fade factor (0.0 = invisible, 1.0 = fully visible)
            fade = 1.0
            if ref_y < self.FADE_TOP:
                fade = 0.0
            elif ref_y < self.FADE_TOP + self.FADE_TOP_DIST:
                fade = (ref_y - self.FADE_TOP) / self.FADE_TOP_DIST
            if ref_y > ref_h - self.FADE_BOT_DIST:
                fade = min(fade, (ref_h - ref_y) / self.FADE_BOT_DIST)
            if fade <= 0.01:
                continue

            # Color with fade
            base = COLOR_ROLE if typ == "role" else COLOR_NAME
            col = (int(base[0] * fade), int(base[1] * fade),
                   int(base[2] * fade))

            # Font and position
            fs = self.FONT_ROLE if typ == "role" else self.FONT_NAME
            text_surf = self.style.render_text(text, L.font_size(fs), col)

            x = self.CREDIT_X
            if typ == "name":
                x += self.CREDIT_INDENT

            # Reference to window, in the content area as the logo
            surface.blit(text_surf, L.pos(x, ref_y))

    def on_resize(self):
        super().on_resize()
        # on_resize reloads boxes.json for the new resolution, which
        # throws away the runtime text with it.
        self._apply_version()
        self._scale_logo()
