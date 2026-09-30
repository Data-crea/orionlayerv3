"""The Ship Designer (wire id 3) — work order 185, part 7.

The original's `DESIGN::Design_Screen_` in the HUD style; the reading is
`dev:doc/ship_designer_reading.md`, the brief `dev:doc/brief_ship_designer.md`.

**IT CLAIMS ITS ID ONLY WITH OPEN FIX 44's "DSGN" BLOCK ON THE WIRE**
(`sdwire.claims`). 44 and 45 are applied since work order 186 (orion2re
`70d31b10`, `4af9fefa`) and the page was walked live on that engine; on an
engine without them id 3 stays the game's own picture through the safety
net, exactly as before this screen existed. With the block, a
list that is not the page's (a warning box, or a picker on an engine
without fix 45) is a modal HD has no view for, and the screen hands over.

**WHAT IT SENDS** — nothing the player did not choose (decision 65), each
field found in the list on the wire when the byte goes out (decision 20):

    Cancel / ESC, Clear / L, Build / B      ACTIVATE_FIELD on the button
    the icon arrows, the shield and computer panels, a weapon or special
    row, plus / minus                       ACTIVATE_FIELD on its field
    a hull button                           INJECT_CLICK at its centre —
                                            a multi-button (type 3) is
                                            resolved in the mouse path an
                                            activation skips (fundament 09)

Refused before it goes out (decision 33): a hull without its button field,
plus / minus without their button, Build without its button (the original
removes it when the design does not fit). THE NAME (work order 187): a
click on it opens HD's own text field; Enter sends an injected click on
the original's field, 15 Backspaces to clear it, the keys one per tick
and Enter —
the save dialog's path (`sdname.py`, DEVIATION `name_field`); ESC cancels
in HD. The typed text is HD's until the engine commits it (DSGN carries
only the committed name).
"""
import logging

import pygame

from core import hestrings, kentext, techdesc
from core.screen_base import ScreenBase
from core.shipparts import ShipPartNames
from screens.leaders import ldrdraw as nd

from . import sddraw, sdgeom as geom, sdname, sdwire

log = logging.getLogger("ship_design")

KEYS = {pygame.K_ESCAPE: geom.CANCEL, pygame.K_l: geom.CLEAR,
        pygame.K_b: geom.BUILD}


class Names:
    """Every word the page draws, each from the player's extracted files."""

    def __init__(self, app, language, root=None):
        # `root`: another tree of derived files — the smoke suite's
        # committed stand-ins (`dev:tools/make_derived_fixtures.py`). HESTRNGS
        # is the App's one table (D17); a harness sets `app.hstrings`.
        self._h = hestrings.for_app(app)
        self._parts = ShipPartNames(language, root=root)
        self._arcs = kentext.ArcWords(language, root=root)
        self._desc = techdesc.TechDesc(language, root=root)

    @property
    def state(self):
        if self._h.state != "ok":
            return "hestrings missing — run tools/hestrings_extract.py"
        if self._parts.state != "ok" or not self._parts.has_design_names():
            return ("ship part names missing or from before work order 185 "
                    "— run tools/techname_extract.py")
        if self._desc.state != "ok":
            return "ship design descriptions missing — run " \
                "tools/techdesc_extract.py"
        return "ok"

    def h(self, index):
        return self._h.message(index)

    def part(self, table, index):
        return self._parts.name(table, index)

    def arc(self, flags):
        return self._arcs.arc(flags)

    def description(self, special):
        return self._desc.special(special)

    def weapon_note(self, weapon):
        return self._desc.weapon_note(weapon)


class ShipDesignScreen(ScreenBase):
    SCREEN_NAME = "ship_design"
    # Literal, as every screen's is (the id check reads them off the
    # source); `sdgeom` names the same, and the smoke group holds the two.
    GAME_SCREEN_ID = 3
    USE_FRAME = False

    def __init__(self, app):
        super().__init__(app)
        self._state = None
        self._view = None
        self._page_fields = None
        self._names = None
        self.name_edit = sdname.NameEditor(self)
        self._data = self.app.res.load_json(
            "screens/ship_design/layout.json", {}) or {}

    def names(self):
        if self._names is None:
            lang = (getattr(self.app, "settings", None) or {}).get(
                "language", "en")
            self._names = Names(self.app, lang)
        return self._names

    def exit(self):
        # A list remembered for drawing under a picker is this visit's.
        self._page_fields = None
        self.name_edit = sdname.NameEditor(self)
        super().exit()

    # ── The dispatcher's and the gate's questions ────────────────────

    def claims(self, game_state):
        return sdwire.claims(game_state)

    def wants_original(self):
        if self._view is None:
            return False
        return not self._view.draws or self.names().state != "ok"

    def handover_is_modal(self):
        return self._view is not None and self._view.state == sdwire.GAME_BOX

    def modal_is_box(self):
        # GAME_BOX with DSGN on the wire: a box over the page, nothing late.
        return self.handover_is_modal() and self._view.design is not None

    def fallback_reason(self):
        if self._view is not None and not self._view.draws:
            return self._view.reason
        state = self.names().state
        return "" if state == "ok" else state

    # ── Per frame ─────────────────────────────────────────────────────

    def update(self, game_state=None):
        if game_state is not None and game_state is not self._state:
            self._state = game_state
            self._view = sdwire.View(game_state, self._page_fields)
            if self._view.state == sdwire.READY:
                self._page_fields = self._view.fields
            self.name_edit.update(game_state)
            self.name_edit.settled(
                (self._view.design or {}).get("name"),
                (getattr(self.app.client, "stats", None) or {}).get("state", 0))

    def word(self, key):
        """OrionLayer's own words, through decision 73's resolver (the
        player's mod folder first), `layout.json`'s as the default."""
        from core import modtexts
        default = (self._data.get("words") or {}).get(key, key.upper())
        name = "ship_design.title" if key == "title" else \
            f"ship_design.button.{key}"
        return modtexts.text(name, default) or default

    def button_state(self, key, rect):
        from core.hud import hover
        return hover.pointer_state(rect)

    def render(self, surface):
        self._render_background(surface)
        view = self._view
        if view is not None and view.draws and self.names().state == "ok":
            sddraw.draw(surface, self, view, self.names())
            if self.name_edit.input is not None:
                self.name_edit.input.render(
                    surface, nd.rect(self.layout, geom.NAME_RECT),
                    self.style, self.layout)
        self.render_help(surface)

    # ── Right-click help, `_static_design_screen_help_list` ───────────

    def help_list(self):
        """`[(help id, native rect)]`: help.json's regions, with the two
        table regions' top moved below the loaded rows as
        `Set_Design_Screen_Help_List_` moves them (`+ n*14 + 15`, capped
        at the bottom), so a right click on a loaded row is not the
        table's general entry. DEVIATION `row_help`: on a loaded row the
        original opens that item's description, whose record is not on
        the wire — HD opens nothing there."""
        out = []
        view = self._view
        counts = {"weapons": len(view.weapon_rows()) if view and view.draws
                  else 0,
                  "specials": len(view.specials()) if view and view.draws
                  else 0}
        for spec in self._help_regions:
            x1, y1, x2, y2 = spec["native"]
            n = counts.get(spec.get("rows"), 0)
            if n > 0:
                y1 = min(y1 + n * 14 + 15, y2)
            out.append((int(spec["help_id"]), (x1, y1, x2, y2)))
        return out

    def open_help_at(self, screen_x, screen_y):
        for help_id, native in self.help_list():
            if nd.rect(self.layout, native).collidepoint(screen_x, screen_y):
                entry = self.helptext.entry(help_id) or \
                    self.helptext.missing_entry(help_id)
                self.help.open(help_id, *entry)
                return True
        return False

    # ── Sending ──────────────────────────────────────────────────────

    def _live(self):
        return getattr(self.app.client.state, "fields", None) or []

    def send(self, field, label):
        """ACTIVATE_FIELD into the live list."""
        if field is None or not self.app.connected:
            return False
        log.info("ship design: %s -> field %d", label, field.index)
        self.app.client.activate_field(field.index)
        return True

    def click_field(self, field, label):
        """INJECT_CLICK at a field's centre (a multi-button)."""
        if field is None or not self.app.connected:
            return False
        x, y = (field.x + field.x_end) // 2, (field.y + field.y_end) // 2
        log.info("ship design: %s -> INJECT_CLICK (%d, %d)", label, x, y)
        self.app.client.inject_click(x, y)
        return True

    def _hit(self, f, x, y):
        return nd.rect(self.layout, (f.x, f.y, f.x_end, f.y_end)) \
            .collidepoint(x, y)

    # ── Input ────────────────────────────────────────────────────────

    def ready(self):
        return self._view is not None and \
            self._view.state == sdwire.READY and self.names().state == "ok"

    def handle_key_event(self, event):
        # The name field, while open or while its keys go out, takes every
        # key (the TextInput needs `event.unicode`); otherwise the page's.
        if self.name_edit.handle_key_event(event):
            return
        self.handle_key(event.key)

    def handle_key(self, key):
        if self.help_consumes_key(key) or not self.ready():
            return
        ident = KEYS.get(key)
        if ident is not None:
            self.send(sdwire.live_field(self._live(), ident),
                      f"key {pygame.key.name(key)}")

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y) or not self.ready():
            return None
        if self.name_edit.busy:
            return None               # the name's keys are going out
        name_hit = nd.rect(self.layout, geom.NAME_RECT).collidepoint(
            screen_x, screen_y)
        if self.name_edit.editing:
            # As in the original, a click away from the open field commits
            # it (fields.cpp copies the string on another field); the click
            # itself is not passed on — DEVIATION `name_field`.
            if not name_hit:
                self.name_edit.commit()
            return None
        live = self._live()
        if name_hit and sdwire.live_field(live, geom.NAME) is not None:
            self.name_edit.start((self._view.design or {}).get("name"))
            return None
        for label, ident in (("Cancel", geom.CANCEL), ("Clear", geom.CLEAR),
                             ("Build", geom.BUILD),
                             ("picture <", geom.PICTURE_LEFT),
                             ("picture >", geom.PICTURE_RIGHT),
                             ("shield", geom.SHIELD),
                             ("computer", geom.COMPUTER)):
            f = sdwire.live_field(live, ident)
            if f is not None and self._hit(f, screen_x, screen_y):
                self.send(f, label)
                return None
        for size, (y1, _y2) in enumerate(geom.HULL_ROWS):
            f = sdwire.at_origin(live, geom.HULL_X[0], y1)
            if f is not None and self._hit(f, screen_x, screen_y):
                if f.field_type == geom.TYPE_MULTI:
                    self.click_field(f, f"hull {size}")
                return None           # a hidden hull field: not offered
        for i in range(8):
            y = geom.WEAPON_ROW_Y0 + i * geom.ROW_STEP
            for x, label in ((geom.MINUS_X, "minus"), (geom.PLUS_X, "plus")):
                f = sdwire.at_origin(live, x, y)
                if f is not None and self._hit(f, screen_x, screen_y):
                    if f.field_type == geom.TYPE_BUTTON:
                        self.send(f, f"{label} {i}")
                    return None       # a hidden field there: refused
        for f in live:
            if f.index == 0 or f.field_type != geom.TYPE_HIDDEN or \
                    not self._hit(f, screen_x, screen_y):
                continue
            weapon = (f.x, f.x_end) in ((0x4D, 0x22C), (0x10, 0x26F)) and \
                geom.WEAPON_ROW_Y0 <= f.y < geom.WEAPON_ROW_Y0 + 8 * \
                geom.ROW_STEP
            special = (f.x, f.x_end) == (0x11, 0x26F) and \
                geom.SPECIAL_ROW_Y0 <= f.y < geom.SPECIAL_ROW_Y0 + 8 * \
                geom.ROW_STEP
            if weapon or special:
                self.send(f, "weapon row" if weapon else "special row")
                return None
        return None
