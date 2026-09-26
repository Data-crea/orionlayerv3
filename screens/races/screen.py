"""Races — orion2re SCREEN_RACE (6), `RACESCRN::Race_Screen_`
(racescrn.cpp:677-1093). Work order 175 C.

HD STATE: **BUILT, NOT ACCEPTED.** The live part of work order 175 C is
parked in `doc/briefs/175-parked-for-data.md` with its exact steps.
Decision 61, and a smoke check fails if this sentence leaves this
docstring.

Entered from the galaxy map's RACES button. Up to seven other races —
portrait, name, treaty paragraph, relation bar and slider, IGNORED, their
spies and the mission row — the agents' pool, the SPY / AGENT bonus and
the five buttons; the inventory is `doc/briefs/175-progress.md` part C.

THE MODULES, one topic each:

  racesgeom   the native geometry, sourced, and the two field shapes
  raceswire   what one snapshot lets HD believe and send
  racesrows   what a slot says: treaties, relation, spies, the bonuses
  racesdraw   the drawing, in the HUD style
  racesart    the original's portraits and spy icons, extracted

**WHAT HD MAY SEND** is `raceswire.View.sendable`'s answer: RETURN (and
ESC), the four actions, and in WHO mode a race or the catcher — each
answers in the list HD reads back (the mode, a box, a dialog). The race
report and diplomacy are the game's own screens under the same id: the
list is neither of this screen's shapes and the fallback shows them.
"""
import logging

from core.billtext import BillText
from core.estrings import EStrings
from core.screen_base import ScreenBase
from core import researchnative as nat
from screens.leaders import ldrdraw as nd

from . import racesart, racesdraw, racesgeom, racesrows, raceswire

log = logging.getLogger("races")


class RacesScreen(ScreenBase):
    SCREEN_NAME = "races"
    GAME_SCREEN_ID = racesgeom.GAME_SCREEN_ID
    USE_FRAME = False

    def __init__(self, app):
        super().__init__(app)
        self._state = None
        self._view = None
        self._waited = 0
        self._slots = []
        self._hover = None          # native point of the pointer
        self._armed = None          # HD STATE `armed_action`: what HD sent
        self._words = None
        self._art = racesart.load()
        self.words_no_contact = self.words_ignored = ""
        self.words_spy = self.words_agent = ""
        self.my_race = 0

    def enter(self, game_state=None):
        super().enter(game_state)
        language = (getattr(self.app, "settings", {}) or {}).get(
            "language", "en")
        self._billtext = BillText(language)
        self._estrings = EStrings(language)
        self._waited, self._hover, self._armed = 0, None, None
        self.update(game_state)

    def update(self, game_state=None):
        if game_state is None:
            return
        self._state = game_state
        self._view = raceswire.View(game_state, self._waited)
        own = self._view.state in (raceswire.MAIN, raceswire.WHO)
        self._waited = 0 if own else self._waited + 1
        if self._view.state == raceswire.MAIN:
            self._armed = None
        if not self._view.draws or not self._view.players:
            self._slots = []
            return
        words = racesrows.Words(self._billtext, self._estrings,
                                self._view.me)
        self._words = words
        clean = racesrows.clean
        self.words_no_contact = clean(words.billtext(racesrows.B_NO_CONTACT))
        self.words_ignored = clean(words.billtext(racesrows.B_IGNORED))
        self.words_spy = words.billtext(racesrows.B_SPY) or ""
        self.words_agent = words.billtext(racesrows.B_AGENT) or ""
        self.my_race = int(self._view.players[self._view.me].race)
        self._slots = racesrows.slots(self._view, words)

    def wants_original(self):
        return self._view is not None and not self._view.draws

    def fallback_reason(self):
        return self._view.reason if self._view else ""

    @property
    def problems(self):
        return [self._view.reason] if self.wants_original() else []

    # ── Drawing ───────────────────────────────────────────

    def render(self, surface):
        self._render_background(surface)
        art, view = self._art, self._view
        racesdraw.draw_frame(surface, self)
        who = view is not None and view.state == raceswire.WHO
        lit = self._slot_at(self._hover) if who else None
        bar = None if who else self._bar_at(self._hover)
        for slot in self._slots:
            racesdraw.draw_slot(surface, self, slot, art,
                                lit=lit == slot.index)
        for i in range(len(self._slots), racesgeom.SLOTS):
            racesdraw.draw_empty(surface, self, i, art)
        if bar is not None:
            racesdraw.relation_word(surface, self, self._slots[bar], art)
        if view is not None and view.players:
            racesdraw.draw_icons(surface, self, racesgeom.AGENT_GROUP,
                                 racesrows.agents(view), self.my_race, art)
            racesdraw.draw_bonuses(surface, self, racesrows.spy_bonuses(
                view, getattr(self._state, "leaders_raw", None)), art)
        racesdraw.draw_buttons(surface, self,
                               view.buttons if view is not None else {},
                               self._armed if who else None)
        if view is not None and view.state == raceswire.IN_BOX:
            from screens.fleets import fltbox
            fltbox.draw(surface, self, self._state)
        self.render_help(surface)

    def help_extra_rect(self, spec):
        native = spec.get("native")
        return nd.rect(self.layout, tuple(native)) if native else None

    # ── Input ─────────────────────────────────────────────

    def _native(self, x, y):
        return nat.from_hd_point(self.layout.to_ref(x, y), self.layout)

    @staticmethod
    def _inside(p, r):
        return p is not None and r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3]

    def _slot_at(self, p):
        return next((i for i in range(len(self._view.active
                                          if self._view else []))
                     if self._inside(p, racesgeom.who_field(i))), None)

    def _bar_at(self, p):
        return next((s.index for s in self._slots if s.active
                     and self._inside(p, racesgeom.bar_field(s.index))), None)

    def _send(self, field, why):
        if field is None or not self.app.connected:
            return
        log.info("races: %s -> field %d", why, field.index)
        self.app.client.activate_field(field.index)

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        view = self._view
        if view is None:
            return None
        if view.state == raceswire.IN_BOX:
            from screens.fleets import fltbox
            for key, field, rect in fltbox.button_rects(self):
                if rect.collidepoint(screen_x, screen_y):
                    self._send(field, f"box {key}")
            return None
        p = self._native(screen_x, screen_y)
        if p is None or view.state not in (raceswire.MAIN, raceswire.WHO):
            return None
        for name in racesgeom.BUTTONS:
            if self._inside(p, racesgeom.button_rect(name)) and \
                    view.sendable(name):
                self._send(view.buttons[name], name)
                if name in racesgeom.ACTIONS:
                    self._armed = name
                return None
        if view.state == raceswire.WHO:
            i = self._slot_at(p)
            if i is not None:
                self._send(view.field(racesgeom.who_field(i)), f"race {i}")
            else:
                self._send(view.field(racesgeom.CATCHER), "cancel")
        return None

    def handle_mouse_motion(self, screen_x, screen_y):
        self._hover = self._native(screen_x, screen_y)
        return super().handle_mouse_motion(screen_x, screen_y)

    def handle_key(self, key):
        if self.help_consumes_key(key):
            return
        view = self._view
        if key == racesgeom.ESC and view is not None and \
                view.sendable("exit"):
            self._send(view.buttons["exit"], "ESC")
