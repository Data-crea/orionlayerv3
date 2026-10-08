"""Races — orion2re SCREEN_RACE (6), `RACESCRN::Race_Screen_`
(racescrn.cpp:677-1093). Work order 175 C.

HD STATE: **BUILT, NOT ACCEPTED.** The live part of work order 175 C is
parked in `dev:doc/briefs/175-parked-for-data.md` with its exact steps.
Decision 61, and a smoke check fails if this sentence leaves this
docstring.

Entered from the galaxy map's RACES button. Up to seven other races —
portrait, name, treaty paragraph, relation bar and slider, IGNORED, their
spies and the mission row — the agents' pool, the SPY / AGENT bonus and
the five buttons; the inventory is `dev:doc/briefs/175-progress.md` part C.

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
from core.hud import shell
from core.screen_base import ScreenBase
from core import researchnative as nat
from screens.leaders import ldrdraw as nd

from . import racesart, racesdraw, racesgeom, racesrows, racesspies, raceswire

log = logging.getLogger("races")


class RacesScreen(ScreenBase):
    SCREEN_NAME = "races"
    GAME_SCREEN_ID = racesgeom.GAME_SCREEN_ID
    USE_FRAME = False
    SHELL_WORN = True
    #: THE SCREEN SHELL (work order 225): the original's two columns of race
    #: slots — the right one with the agents' strip, the bonuses and the
    #: buttons under its three slots — each a panel of the content
    #: rectangle (boxes.json), carried through `core.panelmap` — `fill`: the
    #: original's own boxes (the slots, the bonuses, the buttons' box) reach
    #: the panel's edges and are the panels a frame would lie round.
    REGIONS = (("left_panel", (16, 45, 312, 464), True, True),
               ("right_panel", (328, 45, 624, 464), True, True))
    #: Where EXIT stands, natively: the buttons' box right of the four
    #: actions, both rows high (racescrn.cpp:338-373 puts EXIT there).
    EXIT_AREA = (522, 423, 616, 460)

    def __init__(self, app):
        super().__init__(app)
        self._state = None
        self._view = None
        self._waited = 0
        self._slots = []
        self._hover = None          # native point of the pointer
        self._armed = None          # HD STATE `armed_action`: what HD sent
        # HD STATE `report_player` (work order 223): the race HD picked for
        # the race report — the game's `player_idx` is never on the wire,
        # so the report screen (screens/race_report) can draw only a
        # report HD itself asked for.
        self.report_player = None
        self._last_sent = None      # the last action button HD sent
        self._hand = None           # racesspies.Hand: spies picked, not sent
        self._spy_sent = None       # (expected groups, frames waited)
        self._words = None
        self._art = racesart.load()
        self.words_no_contact = self.words_ignored = ""
        self.words_spy = self.words_agent = ""
        self.my_race = 0
        self.shell = shell.Shell(title=lambda: racesdraw.WORDS["title"])

    def exit_rect(self):
        """EXIT (RETURN), the closing action: the slanted shell button in
        the buttons' box right of the four actions (decision 90: where the
        original has it), at the bottom right of the content rectangle.
        Drawn and hit here (decision 5)."""
        return nd.rect(self.layout, self.EXIT_AREA)

    def enter(self, game_state=None):
        super().enter(game_state)
        language = (getattr(self.app, "settings", {}) or {}).get(
            "language", "en")
        self._billtext = BillText(language)
        self._estrings = EStrings(language)
        self._waited, self._hover, self._armed = 0, None, None
        # Back from a report (or in for the first time): no race is picked.
        self.report_player, self._last_sent = None, None
        self._hand = self._spy_sent = None
        self.update(game_state)

    def update(self, game_state=None):
        if game_state is None:
            return
        self._state = game_state
        self._view = raceswire.View(game_state, self._waited)
        own = self._view.state in (raceswire.MAIN, raceswire.WHO)
        self._waited = 0 if own else \
            self._waited + self.new_snapshot(game_state)
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
        if self._spy_sent is not None:
            want, waited = self._spy_sent
            now = racesspies.groups(self._slots, racesrows.agents(self._view))
            # the command's effect is on the wire, or it was refused
            self._spy_sent = None if now == want or waited > 20 else \
                (want, waited + 1)

    def wants_original(self):
        return self._view is not None and not self._view.draws

    def fallback_reason(self):
        return self._view.reason if self._view else ""

    def no_view_reason(self, game_state):
        """The race report stands under id 6 (REPORT, then a race). Since
        work order 223 it is HD's (`screens/race_report`) when HD asked for
        it; a report HD did not ask for (opened on F12) names no race on
        the wire, so it stays on F12 ([races.report])."""
        if self._view is not None and self._view.state == raceswire.DIALOG:
            return "This race report was not opened in HD"
        return None

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
        racesdraw.draw_spy_hand(surface, self, self._hand, self._hover)
        racesdraw.draw_buttons(surface, self,
                               view.buttons if view is not None else {},
                               self._armed if who else None)
        self.render_shell(surface)
        if view is not None and view.state == raceswire.IN_BOX:
            from screens.fleets import fltbox
            with self.island():          # the engine's box keeps its place
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

    # ── Spies and missions (open fix 64, `racesspies`) ─────

    def _group_at(self, p):
        """(key, box) of the spy group under native p: a movable race's
        strip or the agent pool."""
        for s in self._slots:
            if racesspies.movable(s) and self._inside(
                    p, racesgeom.SPY_GROUP[s.index]):
                return s.index, racesgeom.SPY_GROUP[s.index]
        if self._inside(p, racesgeom.AGENT_GROUP):
            return racesspies.AGENTS, racesgeom.AGENT_GROUP
        return None, None

    def _spy_click(self, p):
        """True if the click was the spies' or a mission's."""
        if self._spy_sent is not None or not self.app.connected:
            return False
        counts = racesspies.groups(self._slots, racesrows.agents(self._view))
        for s in self._slots:
            for k in range(3):
                if racesspies.movable(s) and self._inside(
                        p, racesgeom.mission_rect(s.index, k)):
                    self._send_spies(counts, {s.index: k + 1},
                                     f"mission {k} for race {s.index}")
                    return True
        key, box = self._group_at(p)
        if key is None:
            return False
        if self._hand is None:
            icon = self._art.spy(self.my_race) if self._art else None
            n = racesspies.pick_count(counts[key], box, icon.get_width()
                                      if icon else 28, p[0])
            self._hand = racesspies.Hand(key, n) if n else None
            return True
        hand, self._hand = self._hand, None
        if key != hand.source:
            new, _rest = racesspies.drop(counts, hand, key)
            self._send_spies(new, {}, f"{hand.count} spies {hand.source} "
                             f"-> {key}")
        return True

    def _send_spies(self, counts, missions, why):
        races = racesspies.races_list(self._slots, counts, missions)
        log.info("races: %s -> MSG_SET_SPIES %s agents %d", why, races,
                 counts[racesspies.AGENTS])
        self.app.client.set_spies(races, counts[racesspies.AGENTS])
        self._spy_sent = (counts, 0)

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        view = self._view
        if view is None:
            return None
        if view.state == raceswire.IN_BOX:
            from screens.fleets import fltbox
            with self.island():
                answers = fltbox.button_rects(self)
            for key, field, rect in answers:
                if rect.collidepoint(screen_x, screen_y):
                    self._send(field, f"box {key}")
            return None
        if view.state in (raceswire.MAIN, raceswire.WHO) and shell.hit(
                self.exit_rect(), screen_x, screen_y):
            if view.sendable("exit"):
                self._send(view.buttons["exit"], "exit")
            return None
        p = self._native(screen_x, screen_y)
        if p is None or view.state not in (raceswire.MAIN, raceswire.WHO):
            return None
        for name in racesgeom.BUTTONS:
            if name == "exit":
                continue                 # the slanted button, above
            if self._inside(p, racesgeom.button_rect(name)) and \
                    view.sendable(name):
                self._send(view.buttons[name], name)
                if name in racesgeom.ACTIONS:
                    self._armed = self._last_sent = name
                return None
        if view.state == raceswire.MAIN and self._spy_click(p):
            return None
        if view.state == raceswire.WHO:
            i = self._slot_at(p)
            if i is not None:
                # Not `_armed`: a main-mode snapshot between REPORT and the
                # game's WHO list clears that (seen live, work order 223).
                if self._last_sent == "report" and i < len(view.active):
                    self.report_player = view.active[i]
                self._last_sent = None
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
        if key == racesgeom.ESC and self._hand is not None:
            self._hand = None           # back where it came from; nothing sent
            return
        if key == racesgeom.ESC and view is not None and \
                view.sendable("exit"):
            self._send(view.buttons["exit"], "ESC")
