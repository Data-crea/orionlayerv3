"""The Ship Designer's three pickers (wire ids 54, 55, 56) — work order 185,
part 7.

`DESBOX::Generic_Replacement_Box_` (shield or computer, 54),
`Weapons_Replacement_Box_` (55) and `Special_Systems_Box_` (56) as HUD
popups over the designer's page (an overlay whose parent is
`ship_design`); the reading is `dev:doc/ship_designer_reading.md` section 3.

**IT CLAIMS THE IDS ONLY WITH OPEN FIX 45's "DSBX" BLOCK ON THE WIRE**
(`dbwire.claims`) — applied by work order 186 (orion2re `4af9fefa`) and
walked live on that engine. Without it the ids never reach the wire at all:
a picker reports 3 and the page hands its list to the game's picture.

One screen answers three ids (`EXTRA_SCREEN_IDS`, which the dispatcher
maps and keeps the overlay for), because the three are one box drawn three
ways and share every input.

**WHAT IT SENDS** — ACTIVATE_FIELD, each field found in the list on the
wire when the byte goes out (decision 20), nothing the player did not
choose (decision 65):

    a row, a filter, an arc, a rack, a modification, Cancel, Accept, a
    scroll arrow                   the field under the click
    ESC, A, B, M, O, S, - , +      the field carrying that hotkey (the
                                   original's own: Cancel ESC, Accept A,
                                   the filters B M O S)
    a click outside the box        the full-screen field — the original
                                   closes the box there (kept item / no
                                   change, desbox.cpp:1270, :1403, :244)

Refused before it goes out (decision 33): Accept while the list offers it
only as a hidden field (the original's "not a valid choice" state), a
click on a row the list has no field for (a shield or computer not
researched). A click inside the box on no field sends nothing — the
original's catch-all swallows it.
"""
import logging

import pygame

from core.screen_base import ScreenBase
from screens.leaders import ldrdraw as nd
from screens.ship_design import sdart
from screens.ship_design.screen import Names

from . import dbdraw, dbgeom as geom, dbright, dbwire

log = logging.getLogger("ship_design")


class DesignBoxScreen(ScreenBase):
    SCREEN_NAME = "design_box"
    # Literal, as every screen's is (the id check reads them off the
    # source); `dbgeom` names the same, and the smoke group holds the two.
    GAME_SCREEN_ID = 55
    EXTRA_SCREEN_IDS = (54, 56)
    IS_OVERLAY = True
    OVERLAY_PARENT = "ship_design"
    OVERLAY_DIM = 0                 # the original draws the box over the page
    USE_FRAME = False

    def __init__(self, app):
        super().__init__(app)
        self._state = None
        self._box = None
        self._names = None
        self._data = self.app.res.load_json(
            "screens/design_box/layout.json", {}) or {}

    def names(self):
        if self._names is None:
            lang = (getattr(self.app, "settings", None) or {}).get(
                "language", "en")
            self._names = Names(self.app, lang)
        return self._names

    def _art_state(self):
        art = sdart.load()
        if self._box is not None and self._box.kind == "weapon" and \
                (not art.available or art.label("filter", 0) is None):
            return art.reason or ("designer artwork from before work order "
                                  "185 part 7 — run "
                                  "`python tools/design_art_extract.py`")
        return ""

    # ── The dispatcher's and the gate's questions ────────────────────

    def claims(self, game_state):
        return dbwire.claims(game_state)

    def wants_original(self):
        if self._box is None:
            return False
        return not self._box.draws or self.names().state != "ok" or \
            bool(self._art_state())

    def handover_is_modal(self):
        return self._box is not None and self._box.state == dbwire.GAME_BOX

    def modal_is_box(self):
        # GAME_BOX with DSBX on the wire (not "no DSBX block").
        return self.handover_is_modal() and self._box.box is not None

    def fallback_reason(self):
        if self._box is not None and not self._box.draws:
            return self._box.reason
        state = self.names().state
        return (state if state != "ok" else "") or self._art_state()

    # ── Per frame ─────────────────────────────────────────────────────

    def update(self, game_state=None):
        if game_state is not None and game_state is not self._state:
            self._state = game_state
            self._box = dbwire.Box(game_state)

    def word(self, key):
        """OrionLayer's own words through decision 73's resolver, the
        layout's as the default (`screens/ship_design/sdtexts.py`)."""
        from core import modtexts
        default = (self._data.get("words") or {}).get(key, key.upper())
        name = f"ship_design.box.{key[4:]}" if key.startswith("box_") else \
            f"ship_design.button.{key}"
        return modtexts.text(name, default) or default

    def button_state(self, key, rect):
        from core.hud import hover
        return hover.pointer_state(rect)

    def ready(self):
        return self._box is not None and self._box.draws and \
            self.names().state == "ok" and not self._art_state()

    def render(self, surface):
        if self.ready():
            dbdraw.draw(surface, self, self._box, self.names())

    # ── Sending ──────────────────────────────────────────────────────

    def _live_box(self):
        state = getattr(self.app.client, "state", None)
        return dbwire.Box(state) if state is not None else None

    def send(self, field, label):
        if field is None or not self.app.connected:
            return False
        log.info("design box: %s -> field %d", label, field.index)
        self.app.client.activate_field(field.index)
        return True

    def open_help_at(self, screen_x, screen_y):
        """A right click: `dbright` (work order 200)."""
        box = self._live_box()
        return box is not None and box.draws and \
            dbright.answer(self, box, screen_x, screen_y)

    def _hit(self, f, x, y):
        return nd.rect(self.layout, (f.x, f.y, f.x_end, f.y_end)) \
            .collidepoint(x, y)

    # ── Input ────────────────────────────────────────────────────────

    def handle_key(self, key):
        if self.help_consumes_key(key) or not self.ready():
            return
        live = self._live_box()
        if live is None or not live.draws:
            return
        code = geom.ESC if key == pygame.K_ESCAPE else \
            ord(pygame.key.name(key).upper()) \
            if len(pygame.key.name(key)) == 1 else None
        if code is None:
            return
        # The button first: ESC is the Cancel's hotkey and the full-screen
        # field's, and the original's hotkey scan finds the Cancel first.
        hits = sorted((f for f in live.fields if f.hotkey == code),
                      key=lambda f: (f.field_type != geom.TYPE_BUTTON,
                                     f.index))
        if hits and not (hits[0] is live.accept() and
                         hits[0].field_type != geom.TYPE_BUTTON):
            self.send(hits[0], f"key {pygame.key.name(key)}")

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y) or not self.ready():
            return None
        live = self._live_box()
        if live is None or not live.draws:
            return None
        acc = live.accept()
        targets = [(live.cancel, "Cancel")]
        if acc is not None and acc.field_type == geom.TYPE_BUTTON:
            targets.append((acc, "Accept"))
        targets += [(f, "scroll") for f in live.scroll_buttons()]
        if live.kind == "weapon":
            targets += [(f, "filter") for f in live.filter_fields() if f]
            targets += [(f, "rack") for f in live.rack_fields()]
            targets += [(f, "arc") for f in live.arc_fields()]
            targets += [(f, f"mod {i}") for i, f, _on in live.mods()]
        targets += [(f, "row") for _y, _r, f in live.rows() if f is not None]
        for f, label in targets:
            if self._hit(f, screen_x, screen_y):
                self.send(f, label)
                return None
        if acc is not None and self._hit(acc, screen_x, screen_y):
            return None               # Accept not offered: refused
        if live.kind == "weapon":
            box = live.arc_box_field()
            if box is not None and self._hit(box, screen_x, screen_y):
                # The arc box itself: the original answers with a message
                # (no weapon chosen, or built-in 360) — its box, its picture.
                self.send(box, "arc box")
                return None
        if not self._hit(live.base, screen_x, screen_y):
            self.send(live.full_screen, "outside the box")
        return None
