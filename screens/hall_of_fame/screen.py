"""The Hall of Fame (wire id 14) — work order 188, Part 6.

`SCORE::Hall_Of_Fame_Screen_` (score.cpp:291-356): ten entries, score
descending, numbered 1-10 (the numbers are the picture's), four columns —
the player's name, the race's name, the difficulty's word, the score — drawn
from HOF.M2 as the engine loaded it; no header row (the picture has none).
Reached from the main menu's HALL OF FAME (its field resolved by hotkey,
`screens/main_menu`) and at the end of a game (the new entry flashes).
There is no empty state in the original: a missing or bad file is replaced
by the engine with ten default entries (score.cpp:304-306), so HD never
draws an empty table either — without HOFM it does not claim the id.

**IT CLAIMS 14 ONLY WITH OPEN FIX 50's "HOFM" BLOCK** (`core/hofblocks.py`):
the entries are the engine's, never read from a file of ours (decision 60's
reasoning — the engine may rewrite HOF.M2 on entry).

**WHAT IT SENDS**: one ACTIVATE_FIELD — the screen's full-screen field with
ESC as its hotkey (score.cpp:549), the original's only way out — on a click
anywhere or ESC. Nothing else: the original's "C" re-creates the default
file ON DISK (score.cpp:329-334), and no key but ESC reaches the game from
here (OMISSION `reset_key`).

Marks (`layout.json`): DEVIATION `hud_table`, DEVIATION `flash`, HD
EXTENSION `exit_button`, OMISSION `reset_key`.
"""
import logging

import pygame

from core.hud import blocks as hud
from core.hud import text as hudtext
from core.screen_base import ScreenBase

log = logging.getLogger("hall_of_fame")

#: The columns' native extents (score.cpp:407-437): name 164..281, race
#: 292..354, difficulty 364..449, score right-aligned at 500; the row's own
#: field starts at 139 (:542-547). HD keeps the proportions inside its
#: table: each column is a fraction of 139..500.
COLUMNS = (("name", 164, 281, "left"), ("race", 292, 354, "left"),
           ("difficulty", 364, 449, "left"), ("score", 458, 500, "right"))
TABLE_X0, TABLE_X1 = 139, 500
#: The flash's pace: one step every 6 draw ticks of 55 ms (score.cpp:
#: 397-405) — the lit row blinks at twice that period.
FLASH_MS = 6 * 55
REF_W, REF_ROW, REF_PAD, REF_FONT = 1180, 62, 28, 30


def exit_field(fields):
    """The full-screen field with ESC as its hotkey (score.cpp:549)."""
    return next((f for f in fields or [] if getattr(f, "index", 0) > 0
                 and f.hotkey == 0x1B and (f.x, f.y, f.x_end, f.y_end) ==
                 (0, 0, 639, 479)), None)


class HallOfFameScreen(ScreenBase):
    SCREEN_NAME = "hall_of_fame"
    GAME_SCREEN_ID = 14
    USE_FRAME = False

    def __init__(self, app):
        super().__init__(app)
        self._state = None
        self._data = {}
        self._close = None

    def enter(self, game_state=None):
        super().enter(game_state)
        self._data = self.app.res.load_json(
            "screens/hall_of_fame/layout.json", {}) or {}

    def claims(self, game_state):
        return getattr(game_state, "hall_of_fame", None) is not None

    def wants_original(self):
        return False

    def update(self, game_state=None):
        if game_state is not None:
            self._state = game_state

    def words(self, key):
        return ((self._data.get("words") or {}).get(key) or key.upper())

    # ── drawing ───────────────────────────────────────────────────────
    def render(self, surface):
        self._render_background(surface)
        hof = getattr(self._state, "hall_of_fame", None)
        if hof is None:
            return
        win_w, win_h = surface.get_size()
        s = win_h / 1080
        pad = int(REF_PAD * s)
        w = int(REF_W * s)
        row_h = int(REF_ROW * s)
        size = max(10, int(REF_FONT * s))
        rows = hof["rows"]
        top = hud.title_plate(surface, win_w // 2, int(40 * s), s,
                              self.words("title"), self.style).bottom
        panel = pygame.Rect((win_w - w) // 2, top + pad, w,
                            row_h * len(rows) + 2 * pad)
        hud.panel(surface, panel, s, dense=True)
        inner = panel.inflate(-2 * pad, -2 * pad)

        def column_rect(x0, x1, y):
            span = TABLE_X1 - TABLE_X0
            a = inner.x + (x0 - TABLE_X0) * inner.w // span
            b = inner.x + (x1 - TABLE_X0) * inner.w // span
            return pygame.Rect(a, y, b - a, row_h)
        # NO HEADER ROW: the original has none (its picture carries the
        # title and the rank numbers only — the native frame, work order
        # 188). The rank numbers 1-10 stand at the rows' own fields
        # (x 139-155, score.cpp:542-547).
        label = hudtext.colour("label")
        y = inner.y
        flash_on = (pygame.time.get_ticks() // FLASH_MS) % 2 == 0
        ink = hudtext.colour("value")
        for row in rows:
            if row["record"] == hof["flash"] and hof["flash"] >= 0 and \
                    flash_on:
                hud.panel(surface, pygame.Rect(inner.x, y, inner.w, row_h),
                          s, lit=True, dense=True)
            rank = self.style.render_text(str(rows.index(row) + 1), size,
                                          label[:3])
            hudtext.blit(surface, rank, column_rect(TABLE_X0, 157, y),
                         align="right")
            values = {"name": row["name"], "race": row["race"],
                      "difficulty": row["difficulty_word"],
                      "score": str(row["score"])}
            for key, x0, x1, align in COLUMNS:
                r = column_rect(x0, x1, y)
                t = self.style.render_text(values[key], size, ink[:3])
                if t.get_width() > r.w + int(40 * s) and align == "left":
                    # the original fits race and difficulty to their
                    # windows (score.cpp:363-385); HD lets a long word run
                    # into the gap and no further
                    t = t.subsurface(pygame.Rect(0, 0, r.w + int(40 * s),
                                                 t.get_height()))
                hudtext.blit(surface, t, r, align=align)
            y += row_h
        self._close = pygame.Rect(0, 0, int(220 * s), int(58 * s))
        self._close.midtop = (win_w // 2, panel.bottom + pad)
        hud.action_button(surface, self._close, s, "normal",
                          self.words("close"), style_renderer=self.style)

    # ── input: the one way out ─────────────────────────────────────────
    def _leave(self, why):
        state = getattr(self.app.client, "state", None)
        f = exit_field(getattr(state, "fields", None))
        if f is not None and self.app.connected:
            log.info("hall of fame: %s -> field %d", why, f.index)
            self.app.client.activate_field(f.index)

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        self._leave("click")          # a click anywhere, as the original
        return None

    def handle_key_event(self, event):
        if event.key == pygame.K_ESCAPE:
            self._leave("ESC")
        return True                   # no other key reaches the game

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            self._leave("ESC")
