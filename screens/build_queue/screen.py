"""The build popup (wire id 25) — work order 180 C.

`COLBLDG::Build_Queue_Popup_` in the HUD style; see `bqwire` for when it
claims its id (open fixes 35, 39, 40 — none applied on the engine this
order leaves behind) and `bqdraw` for what it draws.

**SELECTING AN ITEM IS AN ORDER** (the order's words), so nothing goes out
but what the player clicks or types, each field found in the list on the
wire at that moment (decision 20) and through `core.colony_guard`:

    a building row      its `_building_fields[i]` — toggles it in the queue
    a ship/other row    its `_military_fields[i]` — adds it (a separator
                        row sends nothing)
    a queue row         its `_queue_fields[i]` — select / move / delete
    OK, Cancel, Refit, Design, Repeat Build   their buttons
    Auto Build          INJECT_CLICK inside its rect: a radio takes no
                        activation (decision 20; fields.cpp:1292-1298)
    ESC  <  >  B  Q 1-9 0   their hot-key fields

The summary follows HD's own pointer — the original's follows ITS
pointer (`_scanned_prod`, colbldg.cpp:825), which an HD window cannot
move — so hovering sends nothing — HD EXTENSION `summary_follows_hd_pointer`.
"""
import logging

import pygame

from core import colony_guard, prodname
from core.buildnames import BuildingNames
from core.estrings import EStrings
from core.screen_base import ScreenBase
from screens.colony_summary import colonyrows
from screens.leaders import ldrdraw as nd

from . import bqdraw, bqwire as w

log = logging.getLogger("build_queue")

KEYS = {pygame.K_ESCAPE: "\x1b", pygame.K_LESS: "<", pygame.K_GREATER: ">",
        pygame.K_b: "B", pygame.K_q: "Q"}
KEYS.update({getattr(pygame, f"K_{d}"): str(d) for d in range(10)})


class Names:
    def __init__(self, state, buildings, strings):
        self._state = state
        self._buildings, self._strings = buildings, strings
        self._ships = prodname.ShipNames(state, getattr(state, "player_num", 0))

    def product(self, pid, state):
        name, st = prodname.production_name(pid, self._buildings,
                                            self._strings, self._ships)
        return name or "", st

    def planet_name(self, colony):
        return colonyrows.planet_name(
            colony, getattr(self._state, "planets_raw", None) or [],
            getattr(self._state, "stars", None) or [])


class BuildQueueScreen(ScreenBase):
    SCREEN_NAME = "build_queue"
    GAME_SCREEN_ID = w.GAME_SCREEN_ID
    USE_FRAME = False

    def __init__(self, app):
        super().__init__(app)
        self._state = self._view = None
        self._hover = None
        lang = (getattr(app, "settings", None) or {}).get("language", "en")
        self._strings = EStrings(lang)
        self._buildings = BuildingNames(lang)
        self._data = self.app.res.load_json(
            "screens/build_queue/layout.json", {}) or {}

    def claims(self, game_state):
        return w.claims(game_state)

    def wants_original(self):
        return self._view is not None and not self._view.draws

    def handover_is_modal(self):
        return self._view is not None and self._view.state == w.GAME_BOX

    def fallback_reason(self):
        return self._view.reason if self._view is not None else ""

    def e(self, index):
        return self._strings.string(index)

    def word(self, key):
        return (self._data.get("words") or {}).get(key, key.upper())

    def turns_left(self, state, view, product):
        """E 544 only for what the colony is producing now
        (colbldg.cpp:1154-1164), from open fix 38; else None."""
        p = getattr(state, "colony_product", None)
        if p is None or view.colony.producing[0] != product or \
                p["producing"] != product:
            return None
        return p["turns"]

    def update(self, game_state=None):
        if game_state is not None and game_state is not self._state:
            self._state = game_state
            self._view = w.View(game_state)

    def render(self, surface):
        self._render_background(surface)
        if self._view is not None and self._view.draws:
            names = Names(self._state, self._buildings, self._strings)
            bqdraw.draw(surface, self, self._view, self._state, names,
                        self._hover)
        self.render_help(surface)

    # ── Input ────────────────────────────────────────────────────────

    def _live(self):
        return getattr(self.app.client.state, "fields", None) or []

    def send(self, field, label):
        if field is None or not self.app.connected:
            return False
        state = self.app.client.state
        try:
            colony_guard.check(field, getattr(state, "current_screen", -1))
        except colony_guard.Refused as err:
            log.warning("build queue: %s — %s", label, err)
            return False
        log.info("build queue: %s -> field %d", label, field.index)
        self.app.client.activate_field(field.index)
        return True

    def _row_under(self, x, y):
        """(kind, index, field, product) of the row under an HD point."""
        v = self._view
        for kind, entries, rows in (("building", v.buildings,
                                     v.building_rows),
                                    ("other", v.others, v.other_rows)):
            for i, (e, f) in enumerate(zip(entries, rows)):
                if self._hit(f, x, y):
                    return kind, i, f, e["id"]
        for i, f in enumerate(v.queue):
            if self._hit(f, x, y):
                return "queue", i, f, v.items[i] if i < len(v.items) else -1
        return None

    def _hit(self, f, x, y):
        return nd.rect(self.layout, (f.x, f.y, f.x_end, f.y_end)) \
            .collidepoint(x, y)

    def handle_mouse_motion(self, screen_x, screen_y):
        super().handle_mouse_motion(screen_x, screen_y)
        self._hover = None
        if self._view is not None and self._view.draws:
            hit = self._row_under(screen_x, screen_y)
            if hit is not None and hit[0] != "queue" and \
                    hit[3] != w.SEPARATOR:
                self._hover = hit[3]

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        v = self._view
        if v is None or not v.draws:
            return None
        fields = self._live()
        for key, ident in (("OK", w.OK), ("Cancel", w.CANCEL),
                           ("Refit", w.REFIT), ("Design", w.DESIGN),
                           ("Repeat", w.REPEAT)):
            f = w.live_field(fields, ident)
            if f is not None and self._hit(f, screen_x, screen_y):
                self.send(f, key)
                return None
        radio = w.live_field(fields, w.AUTO_BUILD)
        if radio is not None and self._hit(radio, screen_x, screen_y) \
                and self.app.connected:
            x, y = (radio.x + radio.x_end) // 2, (radio.y + radio.y_end) // 2
            log.info("build queue: Auto Build -> INJECT_CLICK (%d, %d)", x, y)
            self.app.client.inject_click(x, y)
            return None
        hit = self._row_under(screen_x, screen_y)
        if hit is None:
            return None
        kind, i, f, product = hit
        if product == w.SEPARATOR:
            return None           # the handler ignores it (:1681-1718)
        live = next((g for g in fields if (g.x, g.y, g.x_end, g.y_end) ==
                     (f.x, f.y, f.x_end, f.y_end)), None)
        self.send(live, f"{kind} row {i}")
        return None

    def handle_key(self, key):
        if self.help_consumes_key(key) or not (self._view and
                                               self._view.draws):
            return
        ch = KEYS.get(key)
        if ch is None:
            return
        field = next((f for f in self._live() if f.index != 0 and
                      f.hotkey == ord(ch)), None)
        self.send(field, f"key {ch!r}")
