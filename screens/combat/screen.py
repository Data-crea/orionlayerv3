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
from . import (cbart, cbcloak, cbdraw, cbmap, cbopts, cbpanel, cbplay,
               cbpopups, cbview)
# the gestures, moved out by work order 202 (decision 6's guideline); FOOT and
# field_by_hotkey are read here and by tools under this module's name
from .cbinput import FOOT, CombatInput, field_by_hotkey  # noqa: F401

log = logging.getLogger("combat")

GAME_SCREEN_ID = 65
GRID_TYPE, MAP_RECT = 12, (0, 0, 639, 359)
ANSWER_WAIT = 3.0                  # s: a command the engine never answers
TICK = 0.055                       # s: `Release_Time_(1)`, timer.cpp:14-24


def ship_frame(seconds):
    """The original's `_ship_frame` after `seconds` of an idle battle —
    TRANSCRIPTION `pace`, corrected by work order 202 G. The glow
    (cmbtdrw1.cpp:2499-2508), the selection cursor (:816-853) and the
    Energy Absorber (cmbtfire.cpp:944) all read `_ship_frame / 2`, and
    `_ship_frame` grows by one per `Draw_Main_Combat_Screen_` (:931). The
    idle turn draws it TWICE per 55 ms tick — combat1.cpp:865 after the
    input step and :1071 at the loop's end, one `Release_Time_(1)` at :1079
    from the mark at :404 (measured in a scratch build: 612 + 612 draws,
    two in the same millisecond, every 55 ms) — so each steps every 55 ms,
    as orion2re's own window shows (201: 88 steps in 4.8 s). The reading
    had taken the auto-function's 110 ms (`Assign_Auto_Function_(…, 2)`,
    combat1.cpp:383) for the idle redraw: 220 ms a step, 4x too slow."""
    return 2 * int(seconds / TICK)


def sound_level(game_state):
    """The game's Sound Fx level, 0..100 (`_settings.sound_fx_level`, the
    MENU's bar, loadsave.cpp:200-201): the master volume the engine plays
    its sounds at (harold.cpp:364), so HD's battle sounds follow the same
    slider. 100 when the settings are not on the wire."""
    from core.structs import settings as spec
    raw = getattr(game_state, "settings_raw", b"") or b""
    if len(raw) < spec.SIZE:
        return 100
    return max(0, min(100, int(spec.parse(raw).sound_fx_level)))


def battle_list(fields):
    """The battle's own list: its map is one grid field (combat1.cpp:111)."""
    return any(getattr(f, "field_type", -1) == GRID_TYPE and
               (f.x, f.y, f.x_end, f.y_end) == MAP_RECT
               for f in fields or [])


class CombatScreen(CombatInput, ScreenBase):
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
        self._play.sounds._blob = self._art.blob   # SOUND.LBX (open fix 79)
        self._play._art = self._art
        self._fades = cbcloak.Fades()         # work order 210 C1
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
        self._tail = False                   # the battle's end playing (202 D)

    # ── state ──────────────────────────────────────────────────────
    def claims(self, game_state):
        """65 with CMBT; 66 and 67 only with open fix 66's CPOP as well."""
        return getattr(game_state, "combat", None) is not None and (
            getattr(game_state, "current_screen", 65) == GAME_SCREEN_ID or
            cbpopups.engine_popup(game_state) is not None)

    def wants_original(self):
        return False

    def finishing(self, game_state):
        """THE BATTLE IS PLAYED TO ITS END (work order 202 D): it has ended
        — its CMBT gone, or another battle's on the wire, or the game on an
        id other than the battle's own — and its own events are still to
        be played: those queued, and the last ones, which arrive with the
        first snapshot after the battle (open fix 56). Till then this
        screen keeps the window and takes no input; what the game shows
        next waits (`ScreenBase.finishing`)."""
        if self._serial is None or self._play.shown is None:
            return False
        combat = getattr(game_state, "combat", None)
        if combat is not None and combat["serial"] == self._serial and \
                getattr(game_state, "current_screen", GAME_SCREEN_ID) in \
                (GAME_SCREEN_ID, *self.EXTRA_SCREEN_IDS):
            return False
        nxt = self._play._next_seq          # its last ones, not yet fed
        return self._play.busy() or any(
            e.get("serial") == self._serial and e["kind"] != "command" and
            (nxt is None or e["seq"] >= nxt) for e in (getattr(
                game_state, "combat_events", None) or {}).get("events", []))

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
        combat = getattr(game_state, "combat", None)
        events = (getattr(game_state, "combat_events", None) or {}).get(
            "events", [])
        self._tail = self.finishing(game_state)
        if self._tail:
            # the battle's last events, played on the battle as it stood;
            # the state after it (no CMBT, another battle, another screen)
            # is not taken — the screen draws its own last state meanwhile
            self._play.feed(None, [e for e in events
                                   if e.get("serial") == self._serial], None)
            self._play.tick()
            return
        self._state = game_state
        if combat is None:
            return
        if combat["serial"] != self._serial:
            self._serial = combat["serial"]
            self._cam, self._board = None, False
            self._play.reset()
            self._fades.reset()
            self._pops.reset()
        self._pops.update(game_state)
        self._play.fast = cbopts.flag(game_state, "fast")
        self._play.sounds.set_level(sound_level(game_state))
        self._play.feed(combat, events, getattr(game_state, "ordnance", None))
        self._play.tick()
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
        return (c is not None and live is not None and not self._tail and
                not self._play.busy()
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
            if old is None:
                self._hold_painted()
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
        clock = ship_frame(time.monotonic() - self._clock0)
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
        now = time.monotonic()
        self._fades.update(c["units"], now)
        cbdraw.draw_tractors(surface, cam, art, c, self._cache)
        cbdraw.draw_units(surface, cam, art, c, self._play.colours, clock,
                          self._cache, self._play.planet,
                          phased_shown=unit["owner"] == self._me(),
                          fades=self._fades, now=now, fast=self._play.fast)
        # TRANSCRIPTION `cursor_hidden` (work order 222): not while the
        # acting unit is moved, turned, teleported or fades (cloak), the
        # original's `_dont_draw_ship` (cmbtdrw1.cpp:815-819; Draw_Cloak_,
        # cmbtspec.cpp:95) — HD drew it on the cell the move left
        cur = c["cur_ship"]
        if not self._computer(c) and self._play.dont_draw() != cur and \
                self._fades.step(cur, now, self._play.fast) is None:
            cbdraw.draw_cursor(surface, cam, art, unit, clock, self._cache)
        cbdraw.draw_ordnance(surface, cam, art, self._play.ordnance,
                             max(10, int(18 * self.layout.scale)),
                             self.style, self._cache, clock, c["cur_ship"])
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
                         self.layout.scale, pic, self._specials,
                         self._computer(self._state.combat or c),
                         self._hover(c))
        if self._panel.map is not None:              # work order 209 B1
            cbmap.draw(surface, self._panel.map, c, self._play.ordnance,
                       self._cam, self._art, self._play.colours,
                       self._play.planet, clock, self.layout.scale)
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

    def _hold_painted(self):
        """HD EXTENSION `painted_detail` (work order 219, `core/paintdetail`):
        the factor painted pictures are held at, from Game Settings and the
        battle's opening view, asked when a battle's first view is built.
        A change drops the pictures made so far — here too, since the
        scaled ones are keyed by the picture's `id` (P828)."""
        from core import livery, paintdetail
        us = getattr(self.app, "user_settings", None)
        choice = us.get("painted_detail") if us is not None else None
        if self._art.set_detail(paintdetail.cap(choice,
                                                self._cam.framing())):
            self._cache.clear()
            log.info("combat: painted pictures held at %d x at most (%s)",
                     self._art.detail, choice or paintdetail.DEFAULT)
        # HD EXTENSION `livery` (work order 220, `core/livery`): the window's
        # choice from the next battle on, the second colour on the player's
        # own colour only (decision 8); a change drops every picture made in
        # the old one, here too (P828)
        own = cbdraw.player_colours(self._state).get(self._me()) \
            if self._state is not None else None
        if self._art.set_livery(livery.from_settings(us, own)):
            self._cache.clear()
            log.info("combat: painted ships in %r", self._art.livery)

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
