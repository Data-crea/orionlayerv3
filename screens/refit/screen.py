"""Refit — `COLREFIT::Colony_Refit_Popup_` and `Colony_Refit2_Popup_`
(colrefit.cpp). Work order 223 Part 8 (Data's decision 5: "Refit is built
in HD").

HD STATE: **BUILT, NOT ACCEPTED.** Decision 61, and a smoke check fails if
this sentence leaves this docstring.

What it is, read in `dev:doc/refit_reading.md`: the build popup's REFIT
opens the list of the player's combat ships at the colony's star; a ship
picked opens the list of designs of its size to refit it to, or the Ship
Designer (`screens/ship_design`, HD's since work order 185) for a new one.

**NO ID OF ITS OWN.** Both lists stand under the build popup's 25; the
dispatcher asks this screen first (`SHARES_GAME_SCREEN_ID`) and it takes the
snapshot when the list is one of the two (`refgeom.kind`) and the colony's
COLS block names the star.

**WHAT HD MAY SEND**, each a field of the list read at that moment, behind
`core/colony_guard` (never a full-screen field, CRUNCH or TOGGLE — both
lists end with a full-screen catch field, colrefit.cpp:388-390,
:632-635): a ship's cell, up, down and Cancel in the ship list; a design's
row, the last row and Cancel in the design list. The game answers: a help
box (a ship it refuses), the officer's question, the next list, the
designer, or the build popup.

**HD STATE `first_row`.** Which five-ship row the ship list starts at is a
static of the original (`_first_ship`); HD counts the pages it sent itself
and starts at the top on entry. The arrows' hotkeys (E_Strings 0x89 and
0xB, colrefit.cpp:357-371; "+" and "-" in the English game) therefore go
through the same sends, never to the game as keys: a page the game turned
alone would put HD's cells on other ships than the game's.
"""
import logging

import pygame

from core import colony_guard, hestrings
from core.estrings import EStrings
from core.screen_base import ScreenBase
from core.shipparts import ShipPartNames
from core.structs import player as player_struct
from core.structs import ship as ship_struct
from core import researchnative as nat
from screens.fleets import fltart, fltrows
from screens.leaders import ldrdraw as nd

from . import refart, refdraw, refgeom as geom, refwords

log = logging.getLogger("refit")

class RefitScreen(ScreenBase):
    SCREEN_NAME = "refit"
    GAME_SCREEN_ID = None
    SHARES_GAME_SCREEN_ID = geom.SHARED_SCREEN_ID
    USE_FRAME = False
    SHELL_WORN = True
    #: THE SCREEN SHELL (work order 225): the popup's content — the grid,
    #: the arrows and the scroll, the info box (native 159..479 x 46..425)
    #: — is one picture stage of the rectangle's full height, centred, in
    #: its native proportion (`core.panelmap`), standing at the shell's
    #: inset inside the stage's panel; the title stands on the
    #: plate and Cancel is the shell's closing action. REFITPUP's window
    #: (`POPUP`) is not drawn: the stage is the panel.
    REGIONS = (("stage", (159, 46, 479, 425), True),)   # at the inset
    SHELL_STAGE = "stage"

    def __init__(self, app):
        super().__init__(app)
        from core.hud import shell
        self.shell = shell.Shell(
            title=self.title_text,
            buttons=[("cancel", lambda: self.word("cancel"), "action")],
            visible=lambda key: self.kind is not None)
        self._state = None
        self.kind = None
        self.first = 0              # HD STATE `first_row`
        self._ships = []            # ship indices in the original's order
        self._hover = None          # a cell (ships) or a row (designs)
        self._estrings = None
        self._parts = None
        self._picked = None         # the ship HD picked (`_g_ship_n`)
        self._data = self.app.res.load_json(
            "screens/refit/layout.json", {}) or {}

    # ── Which list ────────────────────────────────────────

    def claims(self, game_state):
        return (getattr(game_state, "current_screen", None) ==
                geom.SHARED_SCREEN_ID and
                geom.kind(getattr(game_state, "fields", None)) is not None and
                getattr(game_state, "colony_screen", None) is not None)

    def enter(self, game_state=None):
        super().enter(game_state)
        lang = (getattr(self.app, "settings", {}) or {}).get("language", "en")
        self._estrings = EStrings(lang)
        self._parts = ShipPartNames(lang)
        self.first, self._hover, self.kind = 0, None, None
        self.update(game_state)

    def update(self, game_state=None):
        if game_state is None:
            return
        kind = geom.kind(getattr(game_state, "fields", None))
        if kind != self.kind:
            self._hover = None
            if kind == "ships" and self.kind is None:
                self.first = 0
        self.kind = kind
        self._state = game_state
        self._ships = self.ship_list(game_state)

    def wants_original(self):
        return False

    def word(self, key):
        """DEVIATION `button_words`: the words REFITPUP.LBX has baked into
        its art (the list's title, Cancel, the arrows) — OrionLayer's, in
        `layout.json`'s `words`, as the build popup's are."""
        return (self._data.get("words") or {}).get(key, key.upper())

    # ── What it shows ─────────────────────────────────────

    def e(self, index):
        return self._estrings.string(index) if self._estrings else ""

    def h(self, index):
        table = hestrings.for_app(self.app)
        return table.message(index) if table is not None else ""

    def _me(self):
        n = int(getattr(self._state, "player_num", 0) or 0)
        raws = getattr(self._state, "player_raw", None) or []
        return player_struct.parse(raws[n]) if 0 <= n < len(raws) else None

    @staticmethod
    def ship_list(state):
        """`Build_Ship_List_` (colrefit.cpp:38-58): the player's ships
        with status < 3 at the colony's star, combat type, in ship order."""
        me = int(getattr(state, "player_num", 0) or 0)
        star = (getattr(state, "colony_screen", None) or {}).get("star")
        out = []
        for i, raw in enumerate(getattr(state, "ships_raw", None) or []):
            if len(raw) < ship_struct.SIZE:
                continue
            s = ship_struct.parse(raw)
            if (int(s.owner) == me and int(s.status) < 3 and
                    int(s.location) == star and
                    int(s.ship_type) == ship_struct.SHIP_TYPE_COMBAT):
                out.append(i)
        return out

    def ship_view(self, index):
        raws = getattr(self._state, "ships_raw", None) or []
        return ship_struct.parse(raws[index]) if 0 <= index < len(raws) \
            else None

    def refusal(self, view):
        """The cell's red word (colrefit.cpp:440-462), in its order: the
        colony cannot build it, it was captured, it is Loknar's. The first
        is the build popup's rule (`bqdraw.design_needs_base`, DEVIATION
        `ship_row_dim` narrowed): large or bigger needs a base."""
        me = int(getattr(self._state, "player_num", 0) or 0)
        if int(view.size) >= geom.SHIP_SIZE_LARGE and not self._has_base():
            return self.e(geom.E_NO_BASE)
        if int(view.previous_owner) != me:
            return self.e(geom.E_CAPTURED)
        if int(view.picture_num) == geom.LOKNAR_PICTURE:
            return self.e(geom.E_LOKNAR)
        return ""

    def _has_base(self):
        from core.structs import colony as colony_struct
        from screens.build_queue import bqdraw
        block = getattr(self._state, "colony_screen", None) or {}
        raws = getattr(self._state, "colonies_raw", None) or []
        c = block.get("colony", -1)
        if not 0 <= c < len(raws):
            return False
        built = list(colony_struct.parse(raws[c]).buildings)
        return any(0 <= b < len(built) and built[b] for b in bqdraw.BASES)

    def cells(self):
        art = fltart.load()
        out = []
        for i in range(geom.CELLS):
            k = self.first + i
            if k >= len(self._ships):
                out.append((i, None, None, ""))
                continue
            view = self.ship_view(self._ships[k])
            built = fltrows.player_colour(self._state, view.previous_owner)
            held = fltrows.player_colour(self._state, view.owner)
            pic = None
            if built is not None:
                pic = refart.picture(view.picture_num, built, *self._world())
                if pic is None and art.available:
                    pic = art.ship(int(view.picture_num), built, owner=held)
            out.append((i, view, pic, self.refusal(view)))
        return out

    def _world(self):
        """(climate, ground type) of the colony the popup belongs to — the
        palette its screen runs in (`colart`)."""
        from core.structs import colony as colony_struct
        from core.structs import planet as planet_struct
        block = getattr(self._state, "colony_screen", None) or {}
        cols = getattr(self._state, "colonies_raw", None) or []
        pls = getattr(self._state, "planets_raw", None) or []
        c = block.get("colony", -1)
        if not 0 <= c < len(cols):
            return 0, 0
        col = colony_struct.parse(cols[c])
        bg = planet_struct.parse(pls[col.planet]).climate_bg_type \
            if 0 <= col.planet < len(pls) else 0
        return int(col.climate), int(bg)

    def design_rows(self):
        me = self._me()
        ship = self._picked_ship()
        if me is None:
            return []
        rows = []
        for k in range(5):
            name = player_struct.design_name(me, k)
            if not name:
                continue
            size = player_struct.design_size(me, k)
            matches = ship is not None and size == int(ship.size)
            rows.append((k, name, self._parts.name("hulls", int(size)) or "",
                         matches))
        rows.append((geom.GOTO_ROW, self.e(geom.E_GOTO_DESIGN), "", True))
        return rows

    def _picked_ship(self):
        """HD STATE `picked_ship`: the ship being refitted is the one HD
        picked last (the list does not say which; `_g_ship_n` is a
        static)."""
        idx = getattr(self, "_picked", None)
        return self.ship_view(idx) if idx is not None else None

    # ── Drawing ───────────────────────────────────────────

    def title_text(self):
        """The list's title: the ships' word, or the design list's "%s"
        with the picked ship's name."""
        if self.kind == "designs":
            ship = self._picked_ship()
            return (self.e(geom.E_PICK_DESIGN) or "%s").replace(
                "%s", ship.name if ship is not None else "")
        return self.word("title") if self.kind == "ships" else ""

    def render(self, surface):
        self._render_background(surface)
        if self.kind == "ships":
            refdraw.draw_frame(surface, self, self.word("title"))
            refdraw.draw_ships(surface, self, self.cells(), self._hover,
                               self.first, len(self._ships))
            if self._hover is not None and \
                    self.first + self._hover < len(self._ships):
                k = self._ships[self.first + self._hover]
                refdraw.draw_paragraph(surface, self, refwords.ship_lines(
                    self.ship_view(k), k, self._state, self.e, self.h,
                    self._parts), geom.SHIP_TEXT)
        elif self.kind == "designs":
            ship = self._picked_ship()
            title = (self.e(geom.E_PICK_DESIGN) or "%s").replace(
                "%s", ship.name if ship is not None else "")
            refdraw.draw_frame(surface, self, title)
            refdraw.draw_designs(surface, self, self.design_rows(),
                                 self._hover)
            if self._hover == geom.GOTO_ROW:
                refdraw.draw_paragraph(surface, self, [(
                    "", self.e(geom.E_GOTO_TEXT))], geom.DESIGN_TEXT)
            elif self._hover is not None and self._me() is not None:
                refdraw.draw_paragraph(surface, self, refwords.design_lines(
                    refwords.design_view(self._me(), self._hover), self.e,
                    self._parts), geom.DESIGN_TEXT)
        if self.kind is not None:
            refdraw.draw_buttons(surface, self, self.kind)
        self.render_shell(surface)
        self.render_help(surface)

    def button_state(self, key, rect):
        from core.hud import hover
        return hover.pointer_state(rect)

    def help_extra_rect(self, spec):
        native = spec.get("native")
        return nd.rect(self.layout, tuple(native)) if native else None

    # ── Input ─────────────────────────────────────────────

    def _native(self, x, y):
        return nat.from_hd_point(self.layout.to_ref(x, y), self.layout)

    @staticmethod
    def _in(p, r):
        return p is not None and r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3]

    def _field(self, rect, ftype):
        return next((f for f in getattr(self._state, "fields", None) or ()
                     if f.index != 0 and (f.x, f.y, f.x_end, f.y_end) == rect
                     and f.field_type == ftype), None)

    def send(self, field, label):
        """A field of the live list, behind the colony rules."""
        if field is None or not self.app.connected:
            return False
        colony_guard.check(field, self._state.current_screen)
        log.info("refit: %s -> field %d", label, field.index)
        self.app.client.activate_field(field.index)
        return True

    def handle_mouse_motion(self, screen_x, screen_y):
        p = self._native(screen_x, screen_y)
        self._hover = None
        if self.kind == "ships":
            self._hover = next((i for i in range(geom.CELLS)
                                if self._in(p, geom.cell(i))), None)
        elif self.kind == "designs":
            self._hover = next((k for k in list(range(5)) + [geom.GOTO_ROW]
                                if self._in(p, geom.design_row(k))), None)
        return super().handle_mouse_motion(screen_x, screen_y)

    def _page(self, step):
        """One row of five up (-1) or down (+1), by the arrow's own field;
        down only while a ship stands past the view (colrefit.cpp:241-245)."""
        if step < 0:
            if self.send(self._field(geom.UP, geom.TYPE_BUTTON), "up"):
                self.first = max(0, self.first - 5)
        elif self.first + geom.CELLS < len(self._ships) and \
                self.send(self._field(geom.DOWN, geom.TYPE_BUTTON), "down"):
            self.first += 5

    def handle_key(self, key):
        """The arrows' hotkeys page through `_page` (HD STATE
        `first_row`); every other key goes to the game as before."""
        if self.help_consumes_key(key):
            return
        if self.kind == "ships":
            ch = chr(key) if 0 < key < 0x110000 else ""
            if key in (pygame.K_KP_PLUS, pygame.K_KP_MINUS):
                ch = "+" if key == pygame.K_KP_PLUS else "-"
            for rect, step in ((geom.DOWN, +1), (geom.UP, -1)):
                f = self._field(rect, geom.TYPE_BUTTON)
                if f is not None and f.hotkey and ch and \
                        ord(ch.lower()) in (f.hotkey, ord(chr(f.hotkey).lower())):
                    self._page(step)
                    return
        super().handle_key(key)

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        if self.kind is not None and \
                self.shell_click(screen_x, screen_y) == "cancel":
            self.send(self._field(geom.CANCEL, geom.TYPE_BUTTON), "Cancel")
            return None
        p = self._native(screen_x, screen_y)
        if p is None or self.kind is None:
            return None
        if self._in(p, geom.CANCEL) and not self.SHELL_WORN:
            self.send(self._field(geom.CANCEL, geom.TYPE_BUTTON), "Cancel")
            return None
        if self.kind == "ships":
            if self._in(p, geom.UP):
                self._page(-1)
                return None
            if self._in(p, geom.DOWN):
                self._page(+1)
                return None
            for i in range(geom.CELLS):
                if self._in(p, geom.cell(i)) and \
                        self.first + i < len(self._ships):
                    if self.send(self._field(geom.cell(i), geom.TYPE_HIDDEN),
                                 f"ship {self._ships[self.first + i]}"):
                        self._picked = self._ships[self.first + i]
                    return None
        else:
            for k in list(range(5)) + [geom.GOTO_ROW]:
                if self._in(p, geom.design_row(k)):
                    self.send(self._field(geom.design_row(k),
                                          geom.TYPE_HIDDEN), f"row {k}")
                    return None
        return None
