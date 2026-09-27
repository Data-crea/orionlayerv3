"""The single-colony screen (wire id 1) — work order 180 B.

The original's `COLONY::Colony_Screen_` (colony_main.cpp:238-378) in the
HUD style. Inventory: `doc/briefs/180-colony-inventory.md`.

**IT CLAIMS ITS ID ONLY WHEN THE GAME SAYS WHICH COLONY IT SHOWS**
(`claims`, open fix 35's "COLS" block, NOT APPLIED on the engine this
order leaves behind). Without the block the dispatcher does not give id 1
to this screen, and the game's own picture stands, exactly as before —
"HD must not guess the colony". With it, the first tick at id 1 still
carries the previous colony's handle, so the screen WAITS until the
star/orbit pair and the handle agree, and the hand-over gate (180 A2)
holds the last HD frame meanwhile.

**WHAT IT SENDS** — nothing the player did not choose (decision 65), each
field found in the list on the wire when the byte goes out (decision 20),
and every one through `core.colony_guard`, which refuses CRUNCH, TOGGLE
and the full-screen field [0] (work order 126's safety rule):

    ESC / RETURN      the ESC field [2], the RETURN button as fallback
    < / >             [6] / [7], the original's own keys (index +1 / -1)
    L / LEADERS       [17]      A  the autobuild field [18]
    B / BUY           [3]       CHANGE — the FIELD [4], never the key: a C
                                 reaches [5] (recalculate) first
                                 (fields.cpp:2608-2613) — DEVIATION
                                 `change_by_field` from decision 39's
                                 key-first order, for that reason
    a production row, morale   [13]..[16], [12] — the game's text box
    a planet of the system     its `_sys_disp_planet_fields` entry
    a pop move        one MSG_SET_JOBS (decision 52), picked locally and
                      sent on the drop (decision 47), the Colonies
                      screen's rules and sender unchanged

A pop picked in HD stays HD's until the drop (decision 47): ESC, a right
click or a click outside every job row releases it and sends nothing —
HD EXTENSION `pick_cancel`, as on the Colonies screen. The galaxy-map
inset is unreachable in this engine and not built (OMISSION
`galaxy_inset`).

Everything else is not sent: the buildings (their handler reads the real
pointer — OMISSION `building_actions`), recalculation ([5] is a cheat
with `_cheats`), and any key not listed.
"""
import logging

import pygame

from core import colony_guard
from core.buildnames import BuildingNames
from core.estrings import EStrings
from core import prodname
from core.screen_base import ScreenBase
from screens.colony_summary import colonymove, colonypick, colonysend
from screens.leaders import ldrdraw as nd

from . import coldraw, colgeom as geom, colwire, colwords

log = logging.getLogger("colony")

KEYS = {pygame.K_ESCAPE: "esc", pygame.K_LESS: "<", pygame.K_GREATER: ">",
        pygame.K_l: "L", pygame.K_a: "A", pygame.K_b: "B"}


class Names:
    """The names the screen draws: planets, stars, buildings, products."""

    def __init__(self, state, buildings, strings):
        # RAW records: `colonyrows.planet_name` parses them itself.
        self.planets = getattr(state, "planets_raw", None) or []
        self.stars = getattr(state, "stars", None) or []
        self._buildings, self._strings = buildings, strings

    def building(self, bid):
        name, _st = prodname.production_name(bid, self._buildings)
        return name or ""

    def product(self, pid, state):
        ships = prodname.ShipNames(state, getattr(state, "player_num", 0))
        return prodname.production_name(pid, self._buildings, self._strings,
                                        ships)


class ColonyScreen(ScreenBase):
    SCREEN_NAME = "colony"
    GAME_SCREEN_ID = geom.GAME_SCREEN_ID
    USE_FRAME = False

    def __init__(self, app):
        super().__init__(app)
        self._state = None
        self._view = None
        self.pick = None
        self.send_ = None
        self.message = ""
        lang = (getattr(app, "settings", None) or {}).get("language", "en")
        self._strings = EStrings(lang)
        self._buildings = BuildingNames(lang)
        self._words = colwords.Words(self._strings)
        self._data = self.app.res.load_json("screens/colony/layout.json",
                                            {}) or {}
        self._move_words = (self.app.res.load_json(
            "screens/colony_summary/layout.json", {}) or {}).get("move", {})

    # ── The dispatcher's and the gate's questions ────────────────────

    def claims(self, game_state):
        return colwire.claims(game_state)

    def wants_original(self):
        return self._view is not None and not self._view.draws

    def handover_is_modal(self):
        return self._view is not None and self._view.state == colwire.GAME_BOX

    def fallback_reason(self):
        return self._view.reason if self._view is not None else ""

    # ── Per frame ─────────────────────────────────────────────────────

    def update(self, game_state=None):
        if game_state is None:
            return
        if game_state is not self._state:
            self._state = game_state
            self._view = colwire.View(game_state)
            if self.pick is not None and (not self._view.draws or
                                          self._view.index != self.pick.colony):
                self.pick = None      # the colony changed under the pick
        if self.send_ is not None:
            self.send_.update(game_state)
            if self.send_.finished:
                if self.send_.state != colonysend.DONE:
                    self.message = self._move_words.get(
                        self.send_.reason, self.send_.reason or "")
                self.send_ = None
                self.pick = None

    def word(self, key):
        return (self._data.get("words") or {}).get(key, key.upper())

    def button_state(self, key, rect):
        from core import mouse as mouse_input
        return "hover" if rect.collidepoint(*mouse_input.pos()) else "normal"

    def pick_cells(self):
        if self.pick is None:
            return set()
        return {(self.pick.job, self.pick.slot)}

    def render(self, surface):
        self._render_background(surface)
        view = self._view
        if view is not None and view.draws:
            names = Names(self._state, self._buildings, self._strings)
            coldraw.draw(surface, self, view, self._state, self._words, names)
            if self.message:
                coldraw.text(surface, self, self.message,
                             *geom.HOVER_CENTRE, 600, "value", "negative",
                             align="center")
        self.render_help(surface)

    # ── Sending ──────────────────────────────────────────────────────

    def _live(self):
        return getattr(self.app.client.state, "fields", None) or []

    def send(self, field, label):
        """ACTIVATE_FIELD, through the one guard, into the live list."""
        if field is None or not self.app.connected:
            return False
        state = self.app.client.state
        try:
            colony_guard.check(field, getattr(state, "current_screen", -1))
        except colony_guard.Refused as err:
            log.warning("colony: %s — %s", label, err)
            return False
        log.info("colony: %s -> field %d", label, field.index)
        self.app.client.activate_field(field.index)
        return True

    def _hot(self, key, ftype=None):
        return colwire.hotkey_field(self._live(), key, ftype)

    def _field(self, ident):
        return colwire.live_field(self._live(), ident)

    # ── Input ────────────────────────────────────────────────────────

    def handle_key(self, key):
        if self.help_consumes_key(key) or not (self._view and
                                               self._view.draws):
            return
        what = KEYS.get(key)
        if what is None:
            return                    # nothing else is sent (docstring)
        if what == "esc":
            if self.pick is not None:
                self.pick = None      # decision 47: the preview is ours
                return
            self.send(colwire.hotkey_field(self._live(), "\x1b")
                      or self._field(geom.RETURN), "RETURN")
        else:
            self.send(self._hot(what), f"key {what}")

    def handle_right_button(self, down, mx, my):
        if down and self.pick is not None:
            self.pick = None          # decision 47
            return True
        return False

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        view = self._view
        if view is None or not view.draws or self.send_ is not None:
            return None
        self.message = ""
        if self._job_click(screen_x, screen_y):
            return None
        if self.pick is not None:
            self.pick = None          # a drop outside every job: nothing
            return None
        for key, ident in (("CHANGE", geom.CHANGE), ("BUY", geom.BUY),
                           ("LEADERS", geom.LEADERS),
                           ("RETURN", geom.RETURN)):
            f = self._field(ident)
            if f is not None and self._hit(f, screen_x, screen_y):
                self.send(f, key)
                return None
        for native in list(geom.PROD_ROWS.values()) + [geom.MORALE]:
            if nd.rect(self.layout, native).collidepoint(screen_x, screen_y):
                self.send(self._field((geom.TYPE_HIDDEN,) + native[:2]),
                          "info box")
                return None
        x1, y1, x2, y2 = geom.SYS_DISP
        for f in self._live():
            if f.field_type == geom.TYPE_HIDDEN and x1 <= f.x and \
                    f.x_end <= x2 and y1 <= f.y and f.y_end <= y2 + 8 \
                    and self._hit(f, screen_x, screen_y):
                self.send(f, "system display")
                return None
        return None

    def _hit(self, f, x, y):
        return nd.rect(self.layout, (f.x, f.y, f.x_end, f.y_end)) \
            .collidepoint(x, y)

    def _job_click(self, x, y):
        """The pop move: first click picks (locally), second drops (one
        command). The Colonies screen's rules and sender, unchanged."""
        view = self._view
        rows = [(j, nd.rect(self.layout, r)) for j, r in
                enumerate(geom.JOB_ROWS)]
        job = next((j for j, r in rows if r.collidepoint(x, y)), None)
        if job is None:
            return False
        loaded = colonypick.pops_of(self._state, view.index)
        if loaded is None:
            return True
        pops, n_pops, max_farms = loaded
        if self.pick is None:
            hit = next(((j, k) for j, k, rect, _c in
                        coldraw.job_cells(self, view)
                        if rect.collidepoint(x, y)), None)
            if hit is None:
                return True
            outcome = colonypick.pick_at(pops, n_pops, hit[0], hit[1],
                                         view.index, 0, "name")
            if isinstance(outcome, colonypick.Refusal):
                self.message = colonypick.message(self._move_words, outcome)
            else:
                self.pick = outcome
            return True
        if job == self.pick.job:
            self.pick = None          # its own group: nothing is sent
            return True
        outcome = colonypick.plan_move(self.pick, pops, n_pops, max_farms,
                                       view.index, job)
        if isinstance(outcome, colonypick.Refusal):
            self.message = colonypick.message(self._move_words, outcome)
            self.pick = None
            return True
        if not self.app.connected:
            return True
        predicted = colonymove.predict_pops(pops, n_pops, max_farms,
                                            self.pick.cluster, job)
        self.send_ = colonysend.Send(self.app.client, colony=view.index,
                                     target_job=job,
                                     cluster=self.pick.cluster,
                                     predicted=predicted)
        return True
