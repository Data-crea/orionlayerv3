"""The credits (wire id 44, orion2re v2) — work order 316 E.

`MAINMENU::Credits_Screen_` (mainmenu.cpp:504-561): reached only from the
main menu while it shows the mod list instead of its own credit scroll
(`mod_list_active`, mainmenu.cpp:376-381, the field at :761). It draws the
title art (MAINMENU.LBX 1, :509-531), loads the credit lines
(`Load_Credits_`, :789-833) and scrolls them in a window until the player
leaves; the engine reports 44 with one field, which is all HD needs, so
this view needs no engine change.

TRANSCRIPTION `credits_scroll`: the window (66, 179)-(354, 422), rows 14
px, the first at y 422, moved up 2 px a frame after 10 frames' delay; a
frame is `Release_Time_(3)`, 3 ticks of 55 ms (mainmenu.cpp:538-549,
:563-623; timer.cpp:10); once every row has passed the top the scroll
starts again from the bottom (:615-622). A row is the left column, dots up
to column one, the right column 4 px after it (`Copy_Credit_String_To_
Bitmap_`, :467-492; column one 0x7C in the English game, :874-878).
TRANSCRIPTION `credits_exit`: a click anywhere or ESC activates the one
full-screen field (hotkey ESC, :541-552); nothing else is sent.

DEVIATION `credits_text`: the original reads the session language's
CREDITS.LBX (GERCRDTS.LBX, ..., `Init_Credits_`, :844-879); HD scrolls
the HD main menu's own credits (`screens/main_menu/assets/credits.txt`,
English), the text the main menu scrolls.
DEVIATION `credits_window`: the window is a HUD panel filling the shell's
content rectangle, rows scaled by its height (decision 71), on the
universal background as every screen without its own picture (work order
173) — the original's stands on the title art, MAINMENU.LBX 1.
DEVIATION `credits_fade`: the rows entering and leaving step their font
palette in the original (`Fade_Credit_Colors_`, :494-498, :578-596); HD
draws them at the share of them inside the window.
HD EXTENSION `credits_close`: a CLOSE button bottom right.
"""
import logging
import re
import time

import pygame

from core.hud import blocks as hud
from core.hud import shell
from core.hud import text as hudtext
from core.screen_base import ScreenBase

log = logging.getLogger("credits")

#: The native window the rows are clipped to (mainmenu.cpp:605).
WIN_X0, WIN_Y0, WIN_X1, WIN_Y1 = 66, 179, 354, 422
#: A row's height and the first row's y (mainmenu.cpp:545, :610).
ROW_H, START_Y = 14, 422
#: 2 px a frame, a frame 3 ticks of 55 ms, 10 frames before the first move
#: (mainmenu.cpp:546, :573, :556; timer.cpp:10) — at v2's default speed:
#: `Release_Time` takes the player's `animation_speedup` off each wait
#: (timer.cpp:61), which is not on the wire, so HD keeps the original's.
STEP_PX, FRAME_S, DELAY_FRAMES = 2, 3 * 0.055, 10
#: Column one (English, mainmenu.cpp:874-878) from the row's left edge, and
#: the right column 4 px after it (:491).
COLUMN_ONE, COLUMN_GAP = 0x7C, 4
#: The HD main menu's credits: the text this view scrolls (DEVIATION
#: `credits_text`).
TEXT_FILE = ("main_menu", "assets/credits.txt")
#: "role <dots> name", as the main menu reads it (`screens/main_menu`).
SEPARATOR = re.compile(r"^(.+?)\s+\.+\s*(.+)$")


def pairs(text):
    """The credit rows as the original holds them: (left, right) each —
    a role and its first name, ("", name) for a further name, ("", "")
    for a blank line (`Load_Credits_`'s two strings a row)."""
    out = []
    for line in (text or "").splitlines():
        if not line.strip():
            out.append(("", ""))
        elif line.startswith(" "):
            out.append(("", line.strip()))
        else:
            m = SEPARATOR.match(line)
            out.append((m.group(1).strip(), m.group(2).strip()) if m
                       else (line.strip(), ""))
    return out


def scroll_y(frame, count):
    """The first row's native y at `frame` frames after the screen opened:
    the delay, then 2 px a frame, from the bottom again once the last row
    has passed the top (`abs(y - 179) > count * 14`, mainmenu.cpp:616)."""
    # the delay's frames draw at 422; the n-th moving frame at 422 - 2n,
    # the last one the first that passes the test, after which it resets
    steps = (WIN_Y1 - WIN_Y0 + ROW_H * count) // STEP_PX + 1
    f = frame % (DELAY_FRAMES + steps)
    return START_Y - STEP_PX * max(0, f - DELAY_FRAMES + 1)


def exit_field(fields):
    """The full-screen field with ESC as its hotkey (mainmenu.cpp:541)."""
    return next((f for f in fields or [] if getattr(f, "index", 0) > 0
                 and f.hotkey == 0x1B and (f.x, f.y, f.x_end, f.y_end) ==
                 (0, 0, 639, 479)), None)


class CreditsScreen(ScreenBase):
    SCREEN_NAME = "credits"
    GAME_SCREEN_ID = 44
    USE_FRAME = False
    SHELL_WORN = True

    def __init__(self, app):
        super().__init__(app)
        self._state = None
        self._data = {}
        self._rows = []
        self._t0 = time.monotonic()
        # THE SHELL (decision 89): the original's screen has no title, so
        # no plate; CLOSE the closing action (HD EXTENSION `credits_close`).
        self.shell = shell.Shell(title=None, buttons=[(
            "close", lambda: self.words("close"), "action")], row=True)

    def enter(self, game_state=None):
        super().enter(game_state)
        self._data = self.app.res.load_json(
            "screens/credits/layout.json", {}) or {}
        self._rows = self._load_rows()
        self._t0 = time.monotonic()

    def _load_rows(self):
        path = self.app.res.screen_file(*TEXT_FILE)
        try:
            with open(path, encoding="utf-8") as handle:
                return pairs(handle.read())
        except (OSError, TypeError):
            log.warning("credits: %s not found, nothing to scroll", path)
            return []

    def wants_original(self):
        return False

    def update(self, game_state=None):
        if game_state is not None:
            self._state = game_state

    def words(self, key):
        return (self._data.get("words") or {}).get(key) or key.upper()

    # ── drawing ───────────────────────────────────────────────────────
    def frame(self, now=None):
        now = time.monotonic() if now is None else now
        return int((now - self._t0) / FRAME_S)

    def render(self, surface, now=None):
        self._render_background(surface)
        L = self.ref_layout
        s = L.scale
        panel = self.box_screen_rect("credits") or self.shell.panels(L)
        hud.panel(surface, panel, s, dense=True)
        inner = shell.inner(panel, L)
        # the native window, scaled by the panel's height and centred
        k = inner.h / (WIN_Y1 - WIN_Y0)
        win_w = min(inner.w, int((WIN_X1 - WIN_X0) * k))
        win = pygame.Rect(inner.centerx - win_w // 2, inner.y, win_w, inner.h)
        size = max(10, int(ROW_H * k * 0.72))
        label, ink = hudtext.colour("label")[:3], hudtext.colour("value")[:3]
        dot = self.style.render_text(".", size, label)
        y0 = scroll_y(self.frame(now), len(self._rows))
        clip = surface.get_clip()
        surface.set_clip(win)
        try:
            for i, (left, right) in enumerate(self._rows):
                ny = y0 + i * ROW_H
                if ny + ROW_H <= WIN_Y0 or ny >= WIN_Y1 or not (left or right):
                    continue
                inside = (min(ny + ROW_H, WIN_Y1) - max(ny, WIN_Y0)) / ROW_H
                row = pygame.Surface((win.w, max(1, int(ROW_H * k))),
                                     pygame.SRCALPHA)
                x = 0
                if left:
                    t = self.style.render_text(left, size, label)
                    row.blit(t, (0, 0))
                    x = t.get_width() + int(4 * k)
                col = int(COLUMN_ONE * k)
                if left and right:
                    while x < col and dot.get_width() > 0:
                        row.blit(dot, (x, 0))
                        x += dot.get_width()
                if right:
                    row.blit(self.style.render_text(right, size, ink),
                             (int((COLUMN_ONE + COLUMN_GAP) * k), 0))
                if inside < 1:
                    row.set_alpha(int(255 * inside))
                surface.blit(row, (win.x, win.y + int((ny - WIN_Y0) * k)))
        finally:
            surface.set_clip(clip)
        self.render_shell(surface)
        self.render_help(surface)

    # ── input: the one way out ─────────────────────────────────────────
    def _leave(self, why):
        state = getattr(self.app.client, "state", None)
        f = exit_field(getattr(state, "fields", None))
        if f is not None and self.app.connected:
            log.info("credits: %s -> field %d", why, f.index)
            self.app.client.activate_field(f.index)

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        # a click anywhere, as the original; CLOSE only lends its look
        self.shell_click(screen_x, screen_y)
        self._leave("click")
        return None

    def handle_key_event(self, event):
        if event.key == pygame.K_ESCAPE:
            self._leave("ESC")
        return True

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            self._leave("ESC")
