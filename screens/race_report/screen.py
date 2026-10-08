"""The race report — `RACERPRT::Race_Report_Screen_` (racerprt.cpp:9-155).
Work order 223 Part 8 (Data's decision 6: "REPORT on the Races screen does
not work yet; it is to work").

HD STATE: **BUILT, NOT ACCEPTED.** Decision 61, and a smoke check fails if
this sentence leaves this docstring.

What it is, read in `dev:doc/race_report_reading.md`: the left column
(the race's portrait in its banner colours, its leader's name, personality
and objective, their spies in our empire, its alliances and wars) and, on
the right, Info's Tech Review of THAT race — the same subscreen at the
same places (`INFO::_Tech_Review_Subscreen_`, :140), so this screen is
Info's with another record and another left side.

**NO ID OF ITS OWN.** The game shows the report under Races' 6; the
dispatcher asks this screen first (`SHARES_GAME_SCREEN_ID`) and it takes
the snapshot only when the list is the report's (`rrgeom.is_report`) and
HD knows whose report it is.

**HD STATE `report_player`.** `player_idx` never crosses the wire. Races
remembers the race HD picked after REPORT (`races.report_player`); a report
opened some other way (a hotkey on F12) is not claimed, and the F12 notice
stands as before.

**WHAT HD MAY SEND**: RETURN / ESC — the report's own exit field. The tabs
and the list are local, as on Info (HD STATE `local_navigation`): the
report changes nothing in the game.
"""
import logging

from core.billtext import BillText
from core.estrings import EStrings
from screens.info import infodraw, infoview
from screens.info.screen import InfoScreen, TECH
from screens.info import infogeom as igeom
from screens.leaders import ldrdraw as nd
from screens.races import racesart

from . import rrdraw, rrgeom as geom

log = logging.getLogger("race_report")


class Words:
    """The game's words the column prints (BILLTEXT, ESTRINGS)."""

    def __init__(self, language):
        self._b, self._e = BillText(language), EStrings(language)

    def b(self, index):
        return self._b.message(index) or ""

    def e(self, index):
        return self._e.string(index) or ""


class RaceReportScreen(InfoScreen):
    SCREEN_NAME = "race_report"
    GAME_SCREEN_ID = None
    SHARES_GAME_SCREEN_ID = geom.SHARED_SCREEN_ID
    USE_FRAME = False

    def __init__(self, app):
        super().__init__(app)
        self._player = None
        self._words = None
        self._race_art = racesart.load()

    # ── Which report ──────────────────────────────────────

    def _picked(self):
        races = self.app.dispatcher.screens.get("races") \
            if getattr(self.app, "dispatcher", None) else None
        return getattr(races, "report_player", None)

    def claims(self, game_state):
        if getattr(game_state, "current_screen", None) != \
                geom.SHARED_SCREEN_ID:
            return False
        if not geom.is_report(getattr(game_state, "fields", None)):
            return False
        idx = self._picked()
        raws = getattr(game_state, "player_raw", None) or []
        return idx is not None and 0 <= idx < len(raws)

    def enter(self, game_state=None):
        super().enter(game_state)
        lang = (getattr(self.app, "settings", {}) or {}).get("language", "en")
        self._words = Words(lang)
        self.page, self.tech_tab, self.tech_app = TECH, 0, None
        self._entered = True

    def update(self, game_state=None):
        if game_state is None:
            return
        self._entered = True            # Info's saved tab is not the report's
        super().update(game_state)
        live = [f for f in (getattr(game_state, "fields", None) or [])
                if f.index != 0]
        self._exit = next((f for f in live if (f.x, f.y, f.x_end, f.y_end)
                           == geom.EXIT and f.field_type == geom.TYPE_BUTTON),
                          None)
        self._waited = 0
        picked = self._picked()
        if picked is not None:
            self._player = picked
        self.page = TECH

    def _me(self):
        """The record the Tech Review shows: the report's race."""
        p = self._player
        return self._players[p] if p is not None and \
            0 <= p < len(self._players) else None

    def wants_original(self):
        return False

    def view(self):
        """What the left column draws, from the snapshot alone."""
        me_idx = int(getattr(self._state, "player_num", 0) or 0)
        them = self._me()
        if them is None:
            return None
        n = int(getattr(self._state, "num_players", 0) or 0) or len(
            self._players)
        allies, wars = [], []
        for k in range(min(n, len(self._players))):
            if k == self._player:
                continue
            t = int(them.treaty[k])
            if t == geom.TREATY_ALLIANCE:
                allies.append(self._players[k].race_name)
            elif t >= geom.TREATY_WAR:
                wars.append(self._players[k].race_name)
        spies = int(them.spies[me_idx]) & 0x3F if \
            0 <= me_idx < len(them.spies) else 0
        return {"player": them, "spies": spies, "allies": allies,
                "wars": wars}

    # ── Drawing ───────────────────────────────────────────

    def render(self, surface):
        self._render_background(surface)
        self._boxes, self._hits, self._drawn = {}, {}, []
        layout = self.layout
        from core.hud import blocks as hud
        hud.panel(surface, nd.rect(layout, geom.CONTENT), layout.scale)
        view = self.view()
        if view is not None and self._words is not None:
            rrdraw.draw_column(surface, self, view, self._words,
                               self._race_art)
            title = infodraw.T("info.title.tech", "") or ""
            if title:
                infodraw.infobox.line(surface, self, title,
                                      infodraw.R(self, igeom.TITLE_BOX),
                                      infodraw.px(self, "name"),
                                      infodraw.HIGH, "center")
            infoview.tech(self, surface, view["player"])
        r = infodraw.R(self, igeom.EXIT)
        hud.small_button(surface, r, layout.scale, "normal")
        infodraw.infobox.line(surface, self, infodraw.T("info.exit", "RETURN"),
                              r.inflate(-8, 0), infodraw.px(self, "button"),
                              infodraw.hudtext.colour("button"), "center")
        self.render_help(surface)

    # ── Input ─────────────────────────────────────────────

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        p = self._native(screen_x, screen_y)
        if self._in(p, geom.EXIT) or self._in(p, igeom.EXIT):
            self._send_exit("RETURN")
            return None
        for k in range(4):
            if self._in(p, igeom.tech_tab_rect(k)):
                self.tech_tab, self.tech_app = k, None
                return None
        hit = self._hit(screen_x, screen_y)
        if isinstance(hit, int):
            self.tech_app = hit
        return None

    def open_help_at(self, screen_x, screen_y):
        """`_report_help_list`: entry 263 over the whole screen
        (billhelp.cpp:85-87)."""
        entry = self.helptext.entry(geom.HELP_ID) or \
            self.helptext.missing_entry(geom.HELP_ID)
        self.help.open(geom.HELP_ID, *entry)
        return True

    def _send_exit(self, why):
        if self._exit is None or not self.app.connected:
            return
        log.info("race report: %s -> field %d", why, self._exit.index)
        self.app.client.activate_field(self._exit.index)
