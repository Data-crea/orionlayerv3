"""The end-of-game score screen (wire id 87) — work order 403, open fix 120.

`SCORE::Hi_Score_Screen` (score.cpp:490-545) shows the tally of a finished
game before the Hall of Fame (HD's `screens/hall_of_fame`, id 14): nine
components, each a line "words ..... figure" (`Print_Score_String`,
score.cpp:904-950: the label, a run of dots in a dimmer colour, the figure
right-aligned), in this order — the time, the population, the players
eliminated (with a small portrait and the defeat's figure of each), the
captured colonies, the technology, the capture of Orion, the capture of
Antares, the council vote (only when its score is above 0) — and the total
(`Draw_Total_Score`, :847-): the raw subtotal, the difficulty's modifier and
the final score, "(S x M) F". The screen ends on a click anywhere or ESC, its
own whole-screen field (:985-987, :522-526).

THE ENGINE'S WORDS AND FIGURES (`core/scoreblock.py`): every line is the
engine's own formatted message, so the player's language is the game's. The
screen claims 87 only with open fix 120's "SCOR" block; without it the
engine reports the caller's id and the F12 notice stays.

TRANSCRIPTION `score_order`: the lines and their order are
`Draw_Hi_Score_Screen`'s (score.cpp:86-120). TRANSCRIPTION `score_leaders`:
label, dots, figure (:904-950). TRANSCRIPTION `score_out`: a click or ESC
activates the whole-screen field the block names (:985-987).
DEVIATION `hud_table`: HUD panels on the universal background where the
original draws SCORE.LBX's picture and cursor. HD EXTENSION `score_header`:
the player the tally is for ("<name>, <race>") above the lines, which the
original does not print. INVENTION `score_title`: the original's title is in
its picture (SCORE.LBX); the word is typed in `layout.json` (decision 15).
OMISSION `score_pop_pictures`: the rows of population and captured-colonist
icons (`Draw_Pop`, score.cpp:1282-1345) and the race portraits of the
eliminated players are not drawn; the figures and the names are. The block
does not carry them (open fix 120). UNVERIFIED live: the screen has not
been seen against a real game's end (Data's decision of 20 October 2026).
"""
import logging

import pygame

from core import scoreblock
from core.hud import blocks as hud
from core.hud import shell
from core.hud import text as hudtext
from core.screen_base import ScreenBase

log = logging.getLogger("score")

#: The words' size in reference pixels (the shell's layout scales it) and
#: the largest share of a row the text may fill.
REF_FONT, MAX_FILL = 30, 0.62
#: The dim run of the leaders' dots (`Print_Score_String`: palette 0xD0..0xD1).
DOT_DIM = 0.55


def exit_field(fields, wanted=None):
    """The whole-screen field that ends the tally: the block's index while
    that field still has the rectangle, else the first ESC field of
    0,0-639,479 (score.cpp:985-987); None when the list has none."""
    whole = [f for f in fields or [] if getattr(f, "index", 0) > 0
             and (f.x, f.y, f.x_end, f.y_end) == (0, 0, 639, 479)]
    return next((f for f in whole if f.index == wanted), None) or next(
        (f for f in whole if f.hotkey == 0x1B), None)


def rows_of(score):
    """The screen's rows: (kind, left words, right words) in order — the
    components, a line under the eliminated ones for each player defeated,
    the total last (kind "total")."""
    out = []
    for key, words, figure in scoreblock.total_rows(score)[:-1]:
        out.append((key, words, figure))
        if key == "elimination":
            for d in score["defeated"]:
                out.append(("defeated", f"    {d['name']}",
                            "%d.%d" % divmod(d["figure"], 10)))
    key, words, figure = scoreblock.total_rows(score)[-1]
    out.append(("total", words, figure))
    return out


class ScoreScreen(ScreenBase):
    SCREEN_NAME = "score"
    GAME_SCREEN_ID = 87
    USE_FRAME = False
    SHELL_WORN = True

    def __init__(self, app):
        super().__init__(app)
        self._state = None
        self._data = {}
        # THE SHELL (decision 87-92): the title plate and the table in the
        # content rectangle; no button, the original has none.
        self.shell = shell.Shell(title=lambda: self.words("title"))

    def enter(self, game_state=None):
        super().enter(game_state)
        self._data = self.app.res.load_json(
            "screens/score/layout.json", {}) or {}

    def claims(self, game_state):
        return getattr(game_state, "score", None) is not None

    def wants_original(self):
        return False

    def update(self, game_state=None):
        if game_state is not None:
            self._state = game_state

    def words(self, key):
        return (self._data.get("words") or {}).get(key) or key.upper()

    def score(self):
        return scoreblock.for_state(self._state)

    # ── drawing ───────────────────────────────────────────────────────
    def render(self, surface):
        self._render_background(surface)
        score = self.score()
        if score is None:
            return
        L = self.ref_layout
        s = L.scale
        panel = self.box_screen_rect("table") or self.shell.panels(L)
        hud.panel(surface, panel, s, dense=True)
        inner = shell.inner(panel, L).inflate(-2 * int(28 * s), 0)
        header = f"{score['name']}, {score['race_name']}".strip(", ")
        rows = rows_of(score)
        row_h = inner.h // (len(rows) + 2)
        size = max(10, min(int(REF_FONT * s), int(row_h * MAX_FILL)))
        label = hudtext.colour("label")[:3]
        ink = hudtext.colour("value")[:3]
        dim = tuple(int(c * DOT_DIM) for c in label)
        y = inner.y
        if header:
            hudtext.blit(surface, self.style.render_text(header, size, label),
                         pygame.Rect(inner.x, y, inner.w, row_h),
                         align="center")
        y += row_h
        for kind, words, figure in rows:
            if kind == "total":
                y += row_h // 2               # the line above the total
                pygame.draw.line(surface, dim, (inner.x, y - row_h // 4),
                                 (inner.right, y - row_h // 4),
                                 max(1, int(2 * s)))
            small = kind == "defeated"
            f_size = max(10, int(size * (0.8 if small else 1.0)))
            left = self.style.render_text(words, f_size, label if small
                                          else ink)
            right = self.style.render_text(figure, f_size, ink)
            r = pygame.Rect(inner.x, y, inner.w, row_h)
            hudtext.blit(surface, left, r, align="left")
            hudtext.blit(surface, right, r, align="right")
            self._dots(surface, left, right, r, f_size, dim)
            y += row_h
        self.render_shell(surface)

    def _dots(self, surface, left, right, r, size, colour):
        """The leaders: a run of dots from the label to the figure
        (`Print_Score_String`, score.cpp:904-950)."""
        dot = self.style.render_text(".", size, colour)
        gap = r.w - left.get_width() - right.get_width() - 2 * dot.get_width()
        if dot.get_width() <= 0 or gap <= 0:
            return
        base = r.y + (r.h - left.get_height()) // 2
        x = r.x + left.get_width() + dot.get_width()
        for _ in range(gap // dot.get_width()):
            surface.blit(dot, (x, base))
            x += dot.get_width()

    # ── input: the one way out ─────────────────────────────────────────
    def _leave(self, why):
        score = self.score() or {}
        client = self.app.client
        f = exit_field(getattr(getattr(client, "state", None), "fields",
                               None), score.get("exit_field"))
        if f is not None and self.app.connected:
            log.info("score: %s -> field %d", why, f.index)
            client.activate_field(f.index)

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        self._leave("click")                  # anywhere (score.cpp:985-987)
        return None

    def handle_key_event(self, event):
        if event.key == pygame.K_ESCAPE:
            self._leave("ESC")
        return True

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            self._leave("ESC")
