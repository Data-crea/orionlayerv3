"""The tactical battle — wire id 65 (open fix 52), work order 197 C.

HD STATE: **BUILT, NOT ACCEPTED** until work order 197's live acceptance is
recorded (`dev:doc/briefs/197-progress.md`, Part C).

It claims 65 while the battle's state is on the wire (open fix 53's CMBT)
and draws the whole field (`cbview`), the units, the planet and the ordnance
in the original's own pictures (`cbart`, `cbdraw`), and the acting unit's
panel (`cbpanel`); every event of open fix 56 is PLAYED before the state
after it is shown (`cbplay`), and nothing is sent while one plays — Data's
condition of 30 September 2026 for letting the engine run ahead.

WHAT IT SENDS, each on the player's own unit's turn only, one command per
action (decision 47) through open fix 58's MSG_COMBAT_COMMAND, the next only
after the engine has answered the last (CMEV's event 18):

    a legal cell              MOVE (open fix 65 keeps the original's view)
    an enemy unit             FIRE with the switched weapon rows as the mask
    an enemy unit, BOARD lit  BOARD (the board popup is answered CAPTURE)
    an own unit               SELECT
    an enemy missile          FIRE_MISSILE
    a right click             FACE toward the cell
    AUTO, WAIT, DONE, RETREAT the original's own fields, by activation

and nothing of the camera: zoom and pan are HD's (`cbview`).
"""
import logging
import time

import pygame

from core import combatblocks as cb
from core.screen_base import ScreenBase
from core.kentext import ArcWords
from core.shipparts import ShipPartNames
from . import cbart, cbdraw, cbhelp, cbopts, cbpanel, cbplay, cbpopups, cbview

log = logging.getLogger("combat")

GAME_SCREEN_ID = 65
GRID_TYPE, MAP_RECT = 12, (0, 0, 639, 359)
FOOT = {0: 1, 1: 2, 2: 2, 3: 3, 4: 3, 5: 3}
ANSWER_WAIT = 3.0                  # s: a command the engine never answers
DRAG_SLOP = 6                      # px before a press is a pan


def battle_list(fields):
    """The battle's own list: its map is one grid field (combat1.cpp:111)."""
    return any(getattr(f, "field_type", -1) == GRID_TYPE and
               (f.x, f.y, f.x_end, f.y_end) == MAP_RECT
               for f in fields or [])


def field_by_hotkey(fields, hotkey, types=(0, 1)):
    return next((f for f in fields or [] if f.index and f.hotkey == hotkey
                 and f.field_type in types), None)


class CombatScreen(ScreenBase):
    SCREEN_NAME = "combat"
    GAME_SCREEN_ID = GAME_SCREEN_ID
    EXTRA_SCREEN_IDS = (66, 67)          # scan view, board popup (199 C1)
    USE_FRAME = False

    def __init__(self, app):
        super().__init__(app)
        self._state = None
        self._art = cbart.CombatArt()
        self._names = None
        self._cam = None
        self._serial = None
        self._panel = cbpanel.Panel()
        self._play = cbplay.Player()
        self._pops = cbpopups.Popups()
        self._opts = cbopts.Options()         # the OPTIONS panel (work order 200)
        self._specials = False               # the panel's SPECIALS view
        self._language = "en"
        self._ken = None
        self._board = False
        # (op, time) awaiting event 18; (pos, button, dragged) of a press
        self._sent = self._press = None
        self._clock0 = time.monotonic()
        self._cache = cbdraw.SpriteCache()     # bounded by bytes (202 B)
        self._turn_seen, self._home = None, False

    # ── state ──────────────────────────────────────────────────────
    def claims(self, game_state):
        """65 with CMBT; 66 and 67 only with open fix 66's CPOP as well."""
        return getattr(game_state, "combat", None) is not None and (
            getattr(game_state, "current_screen", 65) == GAME_SCREEN_ID or
            cbpopups.engine_popup(game_state) is not None)

    def wants_original(self):
        return False

    def enter(self, game_state=None):
        super().enter(game_state)
        language = (getattr(self.app, "settings", {}) or {}).get(
            "language", "en")
        self._names, self._language = ShipPartNames(language), language
        self._ken = ArcWords(language)
        self.update(game_state)

    def update(self, game_state=None):
        if game_state is None:
            return
        self._state = game_state
        combat = getattr(game_state, "combat", None)
        events = (getattr(game_state, "combat_events", None) or {}).get(
            "events", [])
        if combat is None:
            return
        if combat["serial"] != self._serial:
            self._serial = combat["serial"]
            self._cam, self._board = None, False
            self._play.reset()
            self._pops.reset()
        self._pops.update(game_state)
        self._play.fast = cbopts.flag(game_state, "fast")
        self._play.feed(combat, events, getattr(game_state, "ordnance", None))
        for e in events:
            if e["kind"] == "command" and self._sent and \
                    e["op"] == self._sent[0]:
                if e["result"]:
                    log.info("combat: %s refused — %s", self._sent[0],
                             cb.REFUSALS.get(e["result"], e["result"]))
                self._sent = None

    def _me(self):
        return getattr(self._state, "player_num", 0) or 0

    def _shown(self):
        """The battle as HD shows it: the played state (`cbplay`)."""
        return self._play.shown

    def _acting(self):
        c = self._shown()
        return c["units"][c["cur_ship"]] if c else None

    def _own_turn(self):
        c = self._shown()
        live = getattr(self._state, "combat", None)
        return (c is not None and live is not None and not self._play.busy()
                and live["units"][live["cur_ship"]]["owner"] == self._me()
                and self._state.current_screen == GAME_SCREEN_ID
                and battle_list(getattr(self._state, "fields", None)))

    def _ready(self):
        if self._sent and time.monotonic() - self._sent[1] > ANSWER_WAIT:
            self._sent = None
        return self._own_turn() and self._sent is None

    def _mask(self, unit_idx, unit):
        """The rows at 1 as the battle holds them (`cbpanel.on_mask`)."""
        live = getattr(self._state, "combat", None)
        return cbpanel.on_mask(live["units"][unit_idx] if live and unit_idx <
                               len(live["units"]) else unit)

    # ── drawing ────────────────────────────────────────────────────
    def render(self, surface):
        # OrionLayer's background under the panel's glass, as on every
        # screen (`ScreenBase._render_background`); the field covers the rest
        self._render_background(surface)
        win_w, win_h = surface.get_size()
        c = self._shown()
        band = cbpanel.Panel.area(win_w, win_h)
        area = (0, 0, win_w, band.y)
        if self._cam is None or tuple(self._cam.area) != area:
            old = self._cam
            self._cam = cbview.Camera(area)
            if old is None and c is not None:
                u = c["units"][c["cur_ship"]]
                self._cam.frame_original(u["x"], u["y"])
            elif old is not None:
                self._cam.scale, self._cam.ox, self._cam.oy = \
                    old.scale, old.ox, old.oy
                self._cam.clamp()
        cam, art = self._cam, self._art
        self._cache.begin(cam.scale)
        if c is not None:
            self._follow(c)
        clock = int((time.monotonic() - self._clock0) / 0.11)   # 110 ms
        cbdraw.draw_background(surface, cam, art,
                               bool(c and c.get("in_nebula")), self._cache)
        if c is None:
            return
        clip = surface.get_clip()
        surface.set_clip(pygame.Rect(area))
        unit = c["units"][c["cur_ship"]]
        if self._own_turn() and unit["movement_left"] > 0 and \
                cbopts.flag(self._state, "legal_moves"):
            cbdraw.draw_legal(surface, cam, art, c, unit)
        if cbopts.flag(self._state, "grid"):
            cbopts.draw_grid(surface, cam, art)
        if cbopts.flag(self._state, "shield_arcs") and c["cur_ship"]:
            cbopts.draw_shield_arcs(surface, cam, art, unit, cbdraw.centre(
                unit), self.style, self._language)
        self._play.colours = cbdraw.player_colours(self._state)
        self._play.planet = self._planet_picture(c)
        cbdraw.draw_units(surface, cam, art, c, self._play.colours, clock,
                          self._cache, self._play.planet)
        if unit["owner"] == self._me():
            cbdraw.draw_cursor(surface, cam, art, unit, clock, self._cache)
        cbdraw.draw_ordnance(surface, cam, art, self._play.ordnance,
                             max(10, int(18 * self.layout.scale)),
                             self.style, self._cache)
        self._play.draw(surface, cam, art, self.style, self.layout.scale,
                        self._cache)
        surface.set_clip(clip)
        live = {k for k, _w, hk in cbpanel.BUTTONS
                if self._own_turn() and (k != "options" or cbopts.options(
                    self._state)) and (k in ("board", "scan") or field_by_hotkey(
                    getattr(self._state, "fields", None), hk))}
        pic = cbdraw.unit_picture(self._art, self._play.colours, unit, 0)
        self._panel_unit = unit
        self._panel.draw(surface, self.style, unit, self._names, self._ken,
                         [w["active"] for w in (self._state.combat["units"][
                             c["cur_ship"]] if self._state.combat else unit)[
                             "weapons"]],
                         self._board or self._pops.scan_mode and "scan", live,
                         self.layout.scale, pic, self._specials)
        self._opts.draw(surface, self.style, self.layout.scale, self._state,
                        band, self._panel.buttons)
        self._pops.draw(surface, self.style, self.layout.scale, self._state,
                        c, self._weapon_name)
        self.render_help(surface)               # `cbhelp`, work order 200

    def _follow(self, c):
        """The original centres its view on each acting unit at its turn
        (`Snap_Center_Combat_Screen_`, combinit.cpp:2240) and keeps what a
        unit does in view; HD keeps the player's zoom and moves only when
        the acting unit, or the event being played, would be off the area
        or at its edge."""
        turn = (c["serial"], c["turn"], c["cur_ship"])
        at = None
        if turn != self._turn_seen:
            self._turn_seen = turn
            at = cbdraw.centre(c["units"][c["cur_ship"]])
        focus, busy = self._play.focus(), self._play.busy()
        self._home = self._home or busy
        if focus is not None:
            at = focus
        elif self._home and self._own_turn():
            # back to the player's own unit once a playback has ended and
            # its turn is ready (the original snaps to the acting unit,
            # combinit.cpp:2240)
            self._home = False
            at = cbdraw.centre(c["units"][c["cur_ship"]])
        if at is not None and not self._cam.shows(*at):
            self._cam.centre_on(*at)

    def _weapon_name(self, wid):
        return self._names.name("weapons", wid) if self._names else None

    def _planet_picture(self, c):
        key = ("planet", c.get("colony", -1))
        if key not in self._cache:
            self._cache[key] = cbart.planet_picture(self._art, self._state, c)
        return self._cache[key]

    # ── input ──────────────────────────────────────────────────────
    def _send(self, op, a=0, b=0, c=0):
        combat = self._state.combat
        log.info("combat: %s %s %s %s (unit %d)", op, a, b, c,
                 combat["cur_ship"])
        self.app.client.combat_command(combat["serial"], combat["cur_ship"],
                                       cb.COMMANDS[op], a, b, c)
        self._sent = (cb.COMMANDS[op], time.monotonic())

    def _unit_at(self, cell):
        c = self._shown()
        for i, u in enumerate(c["units"]):
            if u["unit_status"] != 0 or (i and u["structure_max"] <= 0):
                continue
            n = FOOT.get(int(u["size_class"]), 1) if i else 5
            if u["x"] <= cell[0] < u["x"] + n and u["y"] <= cell[1] < u["y"] + n:
                return i
        return None

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        if self._state is None or getattr(self._state, "combat", None) is None \
                or self._pops.click(screen_x, screen_y, self._state,
                                    self.app.client) or \
                self._opts.click(screen_x, screen_y, self._state,
                                 self.app.client):
            return None
        key = self._panel.button_at(screen_x, screen_y)
        if key is not None:
            return self._button(key)
        tab = self._panel.tab_at(screen_x, screen_y)
        if tab is not None:                  # a view only, as the original's
            self._specials = tab == "specials"
            return None
        row = self._panel.row_at(screen_x, screen_y)
        if row is not None:
            if self._own_turn() and self.app.connected:
                self._panel.switch(row, self._state, self.app.client)
            return None
        if not self._ready() or self._cam is None:
            return None
        cell = self._cam.cell_at(screen_x, screen_y)
        if cell is None:
            return None
        c = self._shown()
        me, cur = self._me(), c["cur_ship"]
        missile = cbdraw.missile_at(self._play.ordnance, self._cam, screen_x,
                                    screen_y, me)
        target = self._unit_at(cell)
        if self._pops.scan_mode:             # SCAN, then a unit: HD's own view
            self._pops.scan_mode, self._pops.local_unit = False, target
            return None
        if missile is not None:
            self._send("fire_missile", missile)
        elif target is not None and target != cur and \
                c["units"][target]["owner"] != me:
            if self._board:
                self._board = False
                self._send("board", target)
            else:
                self._send("fire", target, self._mask(cur, c["units"][cur]))
        elif target is not None and target != cur:
            self._send("select", target)
        elif cb.legal(c["legal"], *cell):
            self._send("move", *cell)
        return None

    def _button(self, key):
        if key in ("board", "scan"):         # modes HD holds locally
            self._board = key == "board" and not self._board
            self._pops.scan_mode = key == "scan" and not self._pops.scan_mode
            return None
        hotkey = dict((k, hk) for k, _w, hk in cbpanel.BUTTONS)[key]
        f = field_by_hotkey(getattr(self._state, "fields", None), hotkey)
        if f is not None and self._own_turn() and self.app.connected:
            log.info("combat: %s -> field %d", key, f.index)
            self.app.client.activate_field(f.index)
        return None

    def handle_right_button(self, down, screen_x, screen_y):
        """A right DRAG pans (the galaxy map's gesture, HD EXTENSION
        `free_camera`); a right CLICK is FACE toward the cell, as the
        original's right click on its map (combat1.cpp:696-710)."""
        if down:
            self._press = [(screen_x, screen_y), (screen_x, screen_y), False]
            return
        press, self._press = self._press, None
        if press is None or press[2] or cbhelp.right(self, screen_x,
                                                     screen_y):
            return
        if self._ready() and self._cam is not None:
            cell = self._cam.cell_at(screen_x, screen_y)
            if cell is not None:
                self._send("face", *cell)

    def handle_left_release(self, screen_x, screen_y):
        self._pops.release(self._state, self.app.client)

    def handle_mouse_motion(self, screen_x, screen_y):
        self._pops.motion(screen_x)
        if self._press is not None and self._cam is not None:
            (x0, y0), (lx, ly), moved = self._press
            if moved or abs(screen_x - x0) + abs(screen_y - y0) > DRAG_SLOP:
                self._cam.pan(screen_x - lx, screen_y - ly)
                self._press = [(x0, y0), (screen_x, screen_y), True]
        return super().handle_mouse_motion(screen_x, screen_y)

    def handle_mousewheel(self, dy, screen_x, screen_y):
        if self._cam is not None:
            self._cam.zoom(dy, (screen_x, screen_y))

    def handle_key(self, key):
        if self._pops.key(key, self._state, self.app.client) or \
                self._opts.key(key, self._state, self.app.client):
            return
        if key == pygame.K_c and self._cam is not None and self._shown():
            u = self._acting()
            self._cam.centre_on(*cbdraw.centre(u))    # the original's C
        elif key == pygame.K_ESCAPE:
            self._board = self._pops.scan_mode = False
