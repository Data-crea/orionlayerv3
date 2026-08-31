"""Main Menu Screen — Logo + Credit Scrolling + Buttons."""
import re
import time
import pygame
from core import palette
from core.config import ORION2RE_VERSION
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

    def update(self, game_state=None):
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

        # Logo (top-left)
        if self._logo_scaled:
            L = self.layout
            surface.blit(self._logo_scaled,
                         (int(40 * L.scale), int(80 * L.scale + L.offset_y)))

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

            # Convert to screen coords
            sx = int(x * L.scale)
            sy = int(ref_y * L.scale + L.offset_y)
            surface.blit(text_surf, (sx, sy))

    def on_resize(self):
        super().on_resize()
        # on_resize reloads boxes.json for the new resolution, which
        # throws away the runtime text with it.
        self._apply_version()
        self._scale_logo()
