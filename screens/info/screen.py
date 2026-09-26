"""Info — orion2re SCREEN_INFO (9), `INFO::Info_Screen_` (info.cpp:510-642).
Work order 175 D.

HD STATE: **BUILT, NOT ACCEPTED.** The live part of work order 175 D is
parked in `doc/briefs/175-parked-for-data.md` with its exact steps.
Decision 61, and a smoke check fails if this sentence leaves this
docstring.

The left panel (stardate, income and maintenance chart) and five pages —
History Graph, Tech Review, Race Statistics, Turn Summary, Reference; the
inventory is `doc/briefs/175-progress.md` part D. EVERY TEXT is looked up
by a stable key through `core/modtexts` (decision 73, HD EXTENSION
`moddable_texts`), so a mod replaces
it with a file; long texts wrap and scroll (`infobox`).

  infogeom    the native geometry, sourced
  infotexts   every text by its key, with its default and its source
  infopages   what each page says, as data
  infobox     wrapping, scrolling, the no-clipping record
  infodraw    the drawing parts, in the HUD style
  infoview    the five pages, drawn

**HD STATE `local_navigation`.** The tabs are multi-buttons bound to a
LOCAL of `Info_Screen_` (`current_tab`, info.cpp:563-574) that changes only
on a real click inside `Draw_Field_`, and the pages' own state (the tech
category, the race page, the reference page, the selection) lives in file
statics the wire never carries — so HD navigates the pages itself, starting
on the tab the game saved (`history_btns` bits 4-6, bill.cpp:379-382), and
sends only RETURN / ESC. What the original writes back on exit
(`Set_Plyr_Info_Btns_`) is then the tab the game had, not HD's.

**Open fix 32** (`doc/ext_info_screen_state.patch`, APPLIED by work order
176) brings the History Graph's divisors and the Turn Summary's rendered
messages; on an engine without it (HD STATE `engine_without_fix_32`) those
two pages say so in their own moddable words and draw what they have. The
metric toggles are HD's own too (`history_btns` bits 0-3 at entry).
"""
import logging

from core import modtexts
from core.billtext import BillText
from core.estrings import EStrings
from core.infotext import InfoText
from core.screen_base import ScreenBase
from core.technames import TechNames
from core import researchnative as nat

from . import infobox, infodraw, infogeom as geom, infopages as pages
from . import infotexts, infoview
from .infotexts import PAGES

log = logging.getLogger("info")
T = modtexts.text
WAIT_BOUND = 66
HISTORY, TECH, RACES, TURNS, REFERENCE = range(5)


class InfoScreen(ScreenBase):
    SCREEN_NAME = "info"
    GAME_SCREEN_ID = geom.GAME_SCREEN_ID
    USE_FRAME = False

    def __init__(self, app):
        super().__init__(app)
        self._state, self._players, self._waited = None, [], 0
        self._exit = None
        self.page, self.tech_tab, self.race_page = REFERENCE, 0, 0
        self.ref_mode, self.ref_ix, self.topic = "index", 0, None
        self.tech_app = None
        self.hist_bits = 0xF
        self._scroll, self._boxes, self._hits, self._drawn = {}, {}, {}, []
        self._info = None

    def enter(self, game_state=None):
        super().enter(game_state)
        lang = (getattr(self.app, "settings", {}) or {}).get("language", "en")
        self._info = InfoText(lang)
        infotexts.bind(BillText(lang), EStrings(lang), self.helptext,
                       self._info, TechNames(lang))
        self._waited, self._scroll = 0, {}
        self.ref_mode, self.topic, self.tech_app = "index", None, None
        self._entered = False
        self.update(game_state)

    def update(self, game_state=None):
        if game_state is None:
            return
        self._state = game_state
        self._players = pages.players_of(game_state)
        live = [f for f in (getattr(game_state, "fields", None) or [])
                if f.index != 0]
        self._exit = next((f for f in live if (f.x, f.y, f.x_end, f.y_end)
                           == geom.EXIT and f.field_type == geom.TYPE_BUTTON),
                          None)
        self._waited = 0 if self._exit is not None else self._waited + 1
        me = self._me()
        if not self._entered and me is not None:
            # The tab the game saved (`Get_Plyr_Info_Btns_`, info.cpp:500).
            tab = (int(me.history_btns) >> 4) & 7
            self.hist_bits = int(me.history_btns) & 0xF
            self.page = tab if 0 <= tab < len(PAGES) else REFERENCE
            self._entered = True

    def _me(self):
        n = int(getattr(self._state, "player_num", 0) or 0)
        return self._players[n] if 0 <= n < len(self._players) else None

    def wants_original(self):
        return self._state is not None and (
            self._me() is None or (self._exit is None
                                   and self._waited >= WAIT_BOUND))

    def fallback_reason(self):
        if self._me() is None:
            return "The snapshot carries no player records."
        return "The game reports the Info screen and its list never came."

    # ── Drawing ───────────────────────────────────────────

    def render(self, surface):
        self._render_background(surface)
        self._boxes, self._hits, self._drawn = {}, {}, []
        infodraw.draw_frame(surface, self, self.page)
        me = self._me()
        if self._state is not None:
            infodraw.draw_stardate(surface, self,
                                   int(getattr(self._state, "stardate", 0)))
        if me is not None:
            infodraw.draw_chart(surface, self, me)
            getattr(infoview, PAGES[self.page])(self, surface, me)
        self.render_help(surface)

    # ── Right-click help (billhelp.cpp:3-40, info.cpp:1936-1947) ──

    #: `_info_help_list`: the tabs and the chart; then the page's own
    #: entry over (206, 0)-(639, 479). The category and how-to lists'
    #: installers are named the other way round in the source, and their
    #: call sites compensate — category 245, how-to 246.
    HELP_LEFT = ((242, (0, 40, 205, 197)), (243, (0, 198, 205, 479)))
    HELP_PAGE = {HISTORY: 250, TECH: 249, RACES: 248, TURNS: 247}
    HELP_REFERENCE = {"index": 244, "category": 245, "howto": 246}

    def open_help_at(self, screen_x, screen_y):
        p = self._native(screen_x, screen_y)
        if p is None:
            return False
        help_id = next((h for h, r in self.HELP_LEFT if self._in(p, r)), None)
        if help_id is None and self._in(p, (206, 0, 639, 479)):
            help_id = (self.HELP_REFERENCE[self.ref_mode]
                       if self.page == REFERENCE else self.HELP_PAGE[self.page])
        if help_id is None:
            return False
        entry = self.helptext.entry(help_id) or \
            self.helptext.missing_entry(help_id)
        self.help.open(help_id, *entry)
        return True

    # ── Input ─────────────────────────────────────────────

    def _native(self, x, y):
        return nat.from_hd_point(self.layout.to_ref(x, y), self.layout)

    @staticmethod
    def _in(p, r):
        return p is not None and r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3]

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        p = self._native(screen_x, screen_y)
        if self._in(p, geom.EXIT):
            self._send_exit("RETURN")
            return None
        for k in range(len(PAGES)):
            if self._in(p, geom.tab_rect(k)):
                self.page = k
                return None
        hit = self._hit(screen_x, screen_y)
        if self.page == TECH:
            for k in range(4):
                if self._in(p, geom.tech_tab_rect(k)):
                    self.tech_tab, self.tech_app = k, None
                    return None
            if hit is not None:
                self.tech_app = hit
        elif self.page == HISTORY:
            for k in range(4):
                if self._in(p, geom.history_button_rect(k)):
                    self.hist_bits ^= 1 << k
        elif self.page == RACES and self._in(p, geom.RACE_PAGE_BUTTON):
            self.race_page = 1 - self.race_page
        elif self.page == REFERENCE:
            if self.ref_mode != "index" and self._in(p, geom.BACK_BUTTON):
                self.ref_mode, self.topic = "index", None
            elif self.ref_mode == "index" and hit is not None:
                self.ref_mode, self.ref_ix = {"cat": "category",
                                              "howto": "howto"}[hit[0]], hit[1]
                self.topic = None
            elif self.ref_mode == "category" and hit is not None:
                self.topic = hit
        return None

    def _hit(self, x, y):
        for hits in self._hits.values():
            for rect, payload in hits:
                if rect.collidepoint(x, y):
                    return payload
        return None

    def handle_mouse_motion(self, screen_x, screen_y):
        """A row under the pointer is selected, as the original's lists do
        on the mouse alone (info.cpp:1541, :1116)."""
        hit = self._hit(screen_x, screen_y)
        if hit is not None and self.page == TECH and isinstance(hit, int):
            self.tech_app = hit
        elif hit is not None and self.page == REFERENCE and \
                self.ref_mode == "category":
            self.topic = hit
        return super().handle_mouse_motion(screen_x, screen_y)

    def handle_mousewheel(self, direction, mx, my):
        if infobox.scroll(self, (mx, my), direction):
            return True
        return super().handle_mousewheel(direction, mx, my)

    def handle_key(self, key):
        if self.help_consumes_key(key):
            return
        if key == geom.ESC:
            self._send_exit("ESC")

    def _send_exit(self, why):
        if self._exit is None or not self.app.connected:
            return
        log.info("info: %s -> field %d", why, self._exit.index)
        self.app.client.activate_field(self._exit.index)
