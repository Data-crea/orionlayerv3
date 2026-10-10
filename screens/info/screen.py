"""Info — orion2re SCREEN_INFO (9), `INFO::Info_Screen_` (info.cpp:510-642).
Work order 175 D.

HD STATE: **BUILT, NOT ACCEPTED.** The live part of work order 175 D is
parked in `dev:doc/briefs/175-parked-for-data.md` with its exact steps.
Decision 61, and a smoke check fails if this sentence leaves this
docstring.

The left panel (stardate, income and maintenance chart) and five pages —
History Graph, Tech Review, Race Statistics, Turn Summary, Reference; the
inventory is `dev:doc/briefs/175-progress.md` part D. EVERY TEXT is looked up
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
from core.hud import shell
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
#: snapshots without the screen's EXIT before the list is called another
#: screen's: the research screens' measured bound (work order 166), in
#: snapshots since work order 212 (`researchstate.EMPTY_LIST_GRACE`)
WAIT_BOUND = 20
HISTORY, TECH, RACES, TURNS, REFERENCE = range(5)


class InfoScreen(ScreenBase):
    SCREEN_NAME = "info"
    GAME_SCREEN_ID = geom.GAME_SCREEN_ID
    USE_FRAME = False
    SHELL_WORN = True
    #: THE SCREEN SHELL (work order 225): the original's left panel
    #: (stardate, tabs, chart) IS the left panel (`fill`); the content area
    #: below the page title fills the content panel, the title standing on
    #: the plate — both fitted into the content rectangle (boxes.json,
    #: `core.panelmap`). A subclass not in the shell yet says None.
    REGIONS = (("left_panel", geom.LEFT_PANEL, True, True),
               ("content_panel", geom.CONTENT_BELOW_TITLE, True))

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
        from . import infoart
        self._art = infoart.load()      # the Tech Review pictures (196 F)
        self.shell = shell.Shell(title=self._title) if self.REGIONS else None

    def _title(self):
        """The page's title, from where the screen took it before the
        shell (`info.title.<page>`, drawn over the content area)."""
        return infodraw.T(f"info.title.{PAGES[self.page]}", "") or ""

    def exit_rect(self):
        """EXIT (RETURN), the screen's closing action, as the slanted shell
        button at the content panel's inner bottom-right corner, at the size
        its native rectangle maps to — where the original puts it, inside
        the panel's edge (decision 90). Drawn and hit here (decision 5)."""
        r = infodraw.R(self, geom.EXIT)
        panel = self.box_screen_rect("content_panel")
        if panel is None:
            return r
        inner = shell.inner(panel, self.app.layout)
        r.bottomright = inner.bottomright
        return r

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
        self._waited = 0 if self._exit is not None else \
            self._waited + self.new_snapshot(game_state)
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
        self.render_shell(surface)
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
        help_id = self.trait_help_at(screen_x, screen_y) \
            if self.page == RACES else None
        if help_id is None:
            help_id = next((h for h, r in self.HELP_LEFT if self._in(p, r)),
                           None)
        if help_id is None and self._in(p, (206, 0, 639, 479)):
            help_id = (self.HELP_REFERENCE[self.ref_mode]
                       if self.page == REFERENCE else self.HELP_PAGE[self.page])
        if help_id is None:
            return False
        entry = self.helptext.entry(help_id) or \
            self.helptext.missing_entry(help_id)
        self.help.open(help_id, *entry)
        return True

    def trait_help_at(self, x, y):
        """A race's special under a window point: its help id, as the race
        page's own list puts them first (info.cpp:1719-1751). HD wraps the
        panel's text, so the line under the point is found among the
        wrapped lines of each paragraph (`infobox.wrap`)."""
        for k, (skip, ids) in getattr(self, "_race_shown", {}).items():
            box = self._boxes.get(f"races.{k}")
            if box is None or not box.inner.collidepoint(x, y):
                continue
            row = (y - box.inner.y + self._scroll.get(box.key, 0)) // \
                box.step
            n = 0
            for i, para in enumerate(box.text.split("\n")):
                n += max(1, len(infobox.wrap(self.style, para, box.size,
                                             box.inner.w)))
                if row < n:
                    return ids[i - skip] if 0 <= i - skip < len(ids) \
                        else None
        return None

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
        if shell.hit(self.exit_rect(), screen_x, screen_y):
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
        else:
            super().handle_key(key)     # work order 230 E: the shared rule

    def _send_exit(self, why):
        if self._exit is None or not self.app.connected:
            return
        log.info("info: %s -> field %d", why, self._exit.index)
        self.app.client.activate_field(self._exit.index)
