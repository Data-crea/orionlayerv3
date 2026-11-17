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
original does not print. TRANSCRIPTION `score_title`: the original's title is in
its picture (SCORE.LBX); the word is typed in `layout.json` (decision 15).
TRANSCRIPTION/OMISSION `score_pop_pictures`: the rows of population and
captured-colonist figures and the eliminated players' portraits are drawn
from the numbers and snapshot the screen holds (`popicons.py`: the rule of
`Draw_Pop`, score.cpp:1282-1345, and `Draw_Eliminated_Race_Pictures`); what
the block does not carry (the original's random pick of figures, the
contacts that weight the captured portraits) is named there as DEVIATION and
UNVERIFIED, and a row whose pictures are not extracted (`python
tools/raceicon_extract.py`, `python tools/score_art_extract.py`) is omitted.
UNVERIFIED live: the screen has not
been seen against a real game's end (Data's decision of 20 October 2026).
"""
import logging

import pygame

from core import scoreblock
from core.hud import blocks as hud
from core.hud import shell
from core.hud import text as hudtext
from core.screen_base import ScreenBase
from screens.colony_summary import colonyfigures
from screens.score import popicons

log = logging.getLogger("score")

#: The words' size in reference pixels (the shell's layout scales it) and
#: the largest share of a row the text may fill.
REF_FONT, MAX_FILL = 30, 0.62
#: How tall the rows of people are, in text rows (HD's layout, not the
#: original's pixels): the figures' row and the portraits' row.
ICON_UNITS, PORTRAIT_UNITS = 1.5, 2.2
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

    def exit(self):
        # leaving the tally ends the one-snapshot grace: a later id 87
        # without a block is not this game's (review of WO 404)
        self._kept = None
        super().exit()

    def claims(self, game_state):
        # The engine keeps id 87 for one more snapshot after the tally's
        # loop ended (`g_score_live` is already false, the block gone; review
        # of WO 403). The last block carries that snapshot, so the screen
        # does not flash the F12 notice before the Hall of Fame.
        block = getattr(game_state, "score", None)
        if block is not None:
            self._kept = block
            return True
        kept = getattr(self, "_kept", None)
        if kept is not None:
            try:
                game_state.score = kept
            except AttributeError:
                return False
            return True
        return False

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
        extras = self._extras(score)
        units = len(rows) + 2 + sum(
            PORTRAIT_UNITS if k == "portraits" else ICON_UNITS
            for k in extras.values())
        row_h = int(inner.h // units)
        # the figures are the game's 28 px sprites, never smaller
        sprite = int(row_h * ICON_UNITS)
        if extras and (sprite < colonyfigures.MASTER_SIZE
                       or not self._figures_ok(sprite)):
            extras = {k: v for k, v in extras.items() if v == "portraits"}
            units = len(rows) + 2 + sum(PORTRAIT_UNITS for _ in extras)
            row_h = int(inner.h // units)
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
            if kind in extras:
                y += self._draw_pictures(surface, kind, extras[kind], y,
                                         row_h, inner, sprite, score)
        self.render_shell(surface)

    # ── the rows of people (work order 406) ────────────────────────────
    def _extras(self, score):
        """{row key: picture kind} for the rows that have pictures to draw
        now: the names are worked out once here and kept for the draw."""
        self._pics = {}
        pops = popicons.pop_icons(score, self._state)
        if pops:
            self._pics["population"] = ("pop", pops)
        cap = popicons.captured_icons(score)
        if cap:
            self._pics["captured_colonies"] = ("captured", cap)
        shown = [d for d in score["defeated"]
                 if popicons.portrait(d["race"])[0] is not None]
        if shown:
            self._pics["elimination"] = ("portraits", shown)
        return {k: v[0] for k, v in self._pics.items()}

    def _figures_ok(self, sprite):
        """The population figures at this size, or False (not extracted)."""
        return self._figure_set(sprite).state != "missing"

    def _figure_set(self, sprite):
        cache = self.__dict__.setdefault("_fig_sets", {})
        if sprite not in cache:
            cache.clear()
            cache[sprite] = colonyfigures.FigureSet(self.app.res, sprite)
        return cache[sprite]

    def _draw_pictures(self, surface, row, kind, y, row_h, inner, sprite,
                       score):
        """One row of pictures under line `row` at `y`; returns its height.
        Figures stand on `Draw_Pop`'s grid: 22 px steps for 28 px sprites."""
        names = self._pics[row][1]
        if kind == "portraits":
            return self._draw_portraits(surface, names, y, row_h, inner)
        figs = self._figure_set(sprite)
        step = max(1, round(sprite * popicons.STEP / popicons.SPRITE))
        for n, (dx, _dy) in enumerate(popicons.positions(
                popicons.REG_MAX_POP if kind == "pop"
                else popicons.CAP_MAX_POP, len(names))[0]):
            pic = figs.get(names[n])
            if pic is not None:
                surface.blit(pic, (inner.x + dx * step // popicons.STEP, y))
        return int(row_h * ICON_UNITS)

    def _draw_portraits(self, surface, shown, y, row_h, inner):
        """The eliminated players' portraits side by side, the defeat's
        figure at the top of each and the name at its bottom
        (`Draw_Eliminated_Race_Pictures`, score.cpp:725-790)."""
        height = int(row_h * PORTRAIT_UNITS)
        label = hudtext.colour("value")[:3]
        x = inner.x
        for d in shown:
            pic, frame = popicons.portrait(d["race"])
            if pic is None:
                continue
            k = max(1, height // (pic.get_height() + 2 * 1))
            pic = pygame.transform.scale(pic, (pic.get_width() * k,
                                               pic.get_height() * k))
            surface.blit(pic, (x, y))
            if frame is not None:
                frame = pygame.transform.scale(frame, (frame.get_width() * k,
                                                       frame.get_height() * k))
                surface.blit(frame, (x - k, y - k))
            fsz = max(10, int(row_h * 0.45))
            fig = self.style.render_text("%d.%d" % divmod(d["figure"], 10),
                                         fsz, label)
            surface.blit(fig, (x + (pic.get_width() - fig.get_width()) // 2,
                               y + k))
            nm = self.style.render_text(d["name"], fsz, label)
            surface.blit(nm, (x + max(0, (pic.get_width() - nm.get_width())
                                      // 2), y + pic.get_height() - nm.get_height() - k))
            x += pic.get_width() + popicons.BOX_GAP * k
        return height

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
