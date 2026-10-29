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
    an enemy unit, BOARD lit  BOARD; the board popup that follows is the
                              game's own, drawn and answered in HD (RAID,
                              CAPTURE, ESC — `cbpopups`)
    an own unit               SELECT (in BOARD nothing, `cbinput`)
    an enemy missile          FIRE_MISSILE (the player's own: nothing)
    a right click             FACE toward the cell
    AUTO, WAIT, DONE, RETREAT the original's own fields, by activation, as
    OPTIONS and their keys    their keys; S and B light HD's own SCAN and
                              BOARD, as their buttons do

and nothing of the camera: zoom and pan are HD's (`cbview`).
"""
import logging
import time

import pygame

from core import combatblocks as cb
from core.screen_base import ScreenBase
from core.kentext import ArcWords
from core.shipparts import ShipPartNames
from . import (cbart, cbcloak, cbcursor, cbdraw, cbfeed, cblog, cbmap,
               cbopts, cbpanel, cbplay, cbpopups, cbscansources, cbview)
# the gestures, moved out by work order 202 (decision 6's guideline); FOOT and
# field_by_hotkey are read here and by tools under this module's name
from .cbinput import FOOT, CombatInput, field_by_hotkey  # noqa: F401

log = logging.getLogger("combat")

GAME_SCREEN_ID = 65
#: SPECIAL_SUB_SPACE_TELEPORTER, SPECIAL_PHASE_SHIFTER (orion2_consts.h)
TELEPORTER, PHASE_SHIFTER = 33, 22
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
    #: The player watches a battle without input: no idle rate here
    #: (`framerate.loop_cap`, work order 263).
    FULL_RATE = True
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
        self._scan = cbscansources.Sources(self)   # work order 290
        self._move_ptr = cbcursor.Pointer()         # work order 303
        self._opts = cbopts.Options()         # the OPTIONS panel (work order 200)
        self._log = cblog.BattleLog()         # LOG and its window (267)
        self._logwin = cblog.LogWindow()
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
        self._next = cbfeed.NextBattle()     # the next one meanwhile (305)

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
        self._log.add(events, combat if combat is not None and not self._tail
                      else self._play.shown, self._weapon_name,
                      lambda i: self._names.name("specials", i)
                      if self._names else None)
        if self._tail:
            # the battle's last events, played on the battle as it stood;
            # the state after it (no CMBT, another battle, another screen)
            # is not taken — the screen draws its own last state meanwhile
            self._play.feed(None, [e for e in events
                                   if e.get("serial") == self._serial], None)
            # the next battle's snapshots meanwhile are kept (`cbfeed`)
            self._next.keep(self._serial, combat, events,
                            getattr(game_state, "ordnance", None))
            self._play.tick()
            return
        self._state = game_state
        if combat is None:
            return
        if combat["serial"] != self._serial:
            self._serial = combat["serial"]
            self._cam, self._board, self._held = None, False, None
            self._press = None       # a right press held over a battle change
            self._logwin.open = False
            self._play.reset()
            self._fades.reset()
            self._pops.reset()
            self._scan.reset()
            # what it brought while the last battle's tail played (`cbfeed`)
            events = self._next.start(self._play, combat, events) + events
        self._pops.update(game_state)
        self._follow_modes(combat)
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
        return cb.acting_unit(self._shown())

    def _human_acting(self):
        """The battle on its own screen, nothing playing, the live acting
        unit the player's — whatever list stands (the orders, OPTIONS,
        AUTO's one field)."""
        c = self._shown()
        live = getattr(self._state, "combat", None)
        return (c is not None and live is not None and not self._tail and
                not self._play.busy()
                and (cb.acting_unit(live) or {}).get("owner") == self._me()
                and self._state.current_screen == GAME_SCREEN_ID)

    def _own_turn(self):
        """The player's own orders: `_human_acting` with the battle's own
        list up (its map's grid field, `battle_list`)."""
        return self._human_acting() and \
            battle_list(getattr(self._state, "fields", None))

    def _legal_shown(self, c, unit):
        """The reachable cells are drawn while the battle's SHOW LEGAL
        MOVES is on and the acting unit is the human player's
        (cmbtdrw1.cpp:477-482; v2 :553-559) — the OPTIONS panel up too:
        TRANSCRIPTION `legal_options` (work order 305), the original's
        gate asks nothing of its orders, and with the panel up its grid
        holds no unit, so every cell in reach is 2000 (`Move_Options_
        Background_` cmbtdrw1.cpp:1543-1544, `Assign_Combat_Grids_`
        combat1.cpp:1962); the engine's bitmap on the wire is that grid.
        DEVIATION `legal_cells_auto`: none under AUTO — the original draws
        them from the cells of the ship the computer moves, between its
        moves; HD plays those moves from the events, and its snapshot
        already holds the cells after them (as `footprint_playback`).
        TRANSCRIPTION `legal_gate` (work order 303, Data's P3 of 302):
        `Draw_Legal_Boxes`' own gate (v2 cmbtdrw1.cpp:327-343;
        cmbtdrw1.cpp:249-268) — never for the planet (unit 0); with moves
        left, or with none while a working Sub-Space Teleporter or Phase
        Shifter is unused this turn (`Used_Teleporter`, bit 0 of
        `combat_status_flags`, v2 cmbtfir2.cpp:399-401): then the engine's
        bitmap holds the teleporter's range (v2 combat1.cpp:2835-2843,
        :2908-2921) — empty with a Phase Shifter, alone or beside the
        teleporter, so the gate opens and nothing is drawn, as in the
        original."""
        live = getattr(self._state, "combat", None)
        if not (unit is not None and self._human_acting() and
                not self._computer(live) and c["cur_ship"] != 0 and
                cbopts.flag(self._state, "legal_moves")):
            return False
        if unit["movement_left"] > 0:
            return True

        fitted = unit.get("special_device_flags") or [0] * 5
        damaged = unit.get("special_device_damage_flags") or [0] * 5

        def works(bit):
            mask, byte = 1 << (bit & 7), bit >> 3
            return bool(fitted[byte] & mask) and not damaged[byte] & mask
        return (works(TELEPORTER) or works(PHASE_SHIFTER)) and \
            not int(unit.get("combat_status_flags") or 0) & 1

    def _ready(self):
        """The player's own orders with no command in flight and no field
        just activated whose effect is not on the wire yet
        (`_hold_input`)."""
        now = time.monotonic()
        if self._sent and now - self._sent[1] > ANSWER_WAIT:
            self._sent = None
        if self._held and (now - self._held[1] > ANSWER_WAIT or
                           self._held[0] != self._moment()):
            self._held = None
        return self._own_turn() and self._sent is None and self._held is None

    def _hold_input(self):
        """TRANSCRIPTION `done_delay` (work order 305): after DONE the
        original drops the input of its next three calls and clears the
        pointer's buffer (`Set_Input_Delay_(3)`, combat1.cpp:859,
        fields.cpp:143-147, :167-170), so a double click ends one ship, not
        two. HD holds every battle field it activates, a key's too, until
        the engine's state has moved on (`_moment`) or `ANSWER_WAIT` has
        passed; what comes in meanwhile is dropped, not queued."""
        self._held = (self._moment(), time.monotonic())

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
        area = cbview.fit_area((0, 0, win_w, band.y))
        if self._cam is None or tuple(self._cam.area) != area:
            old = self._cam
            self._cam = cbview.Camera(area)
            if old is None:
                self._hold_painted()
            if old is None and c is not None:
                u = cb.acting_unit(c)
                if u is not None:
                    self._cam.frame_original(u["x"], u["y"])
                else:
                    # TRANSCRIPTION `no_acting_view` (work order 324,
                    # UNVERIFIED live): no unit to snap to
                    # (`Snap_Center_Combat_Screen_` is the acting unit's,
                    # combinit.cpp:2240), so the engine's own window
                    # (`cur_combat_x/y`, the grid offset of
                    # cmbtdrw1.cpp:733) is framed
                    vw, vh = cbview.VIEW_CELLS
                    self._cam.frame_original(
                        int(c.get("view_x", 0)) + vw // 2,
                        int(c.get("view_y", 0)) + vh // 2)
            elif old is not None:
                self._cam.scale, self._cam.ox, self._cam.oy = \
                    old.scale, old.ox, old.oy
                self._cam.clamp()
        cam, art = self._cam, self._art
        self._cache.begin(cam.scale)
        if c is not None:
            self._follow(c)
        clock = ship_frame(time.monotonic() - self._clock0)
        # None while no unit acts (`cb.acting_index`): no cursor, no
        # acting-unit panel, no orders, as the original's guards
        # (cmbtdrw1.cpp:608, :713)
        unit = cb.acting_unit(c)
        cbdraw.draw_background(surface, cam, art,
                               bool(c and c.get("in_nebula")), self._cache)
        if c is None:
            self._move_ptr.clear()
            return
        clip = surface.get_clip()
        surface.set_clip(pygame.Rect(area))
        if self._legal_shown(c, unit):
            # over the space, under the units (DEVIATION
            # `legal_cells_readable`, work order 303)
            cbdraw.draw_legal(surface, cam, art, c, unit)
        # the tractor beams before the grid and the frame, as the original's
        # back page (v2 cmbtdrw1.cpp:583-591, :605) under the frame
        # `Draw_Main_Combat_Screen` draws on it
        cbdraw.draw_tractors(surface, cam, art, c, self._cache)
        if cbopts.flag(self._state, "grid"):
            cbopts.draw_grid(surface, cam, art)
        frame = self._frame_cell()
        if frame is not None and unit is not None:
            # TRANSCRIPTION `footprint_frame`
            cbdraw.draw_footprint(surface, cam, art, frame,
                                  unit["size_class"])
        if cbopts.flag(self._state, "shield_arcs") and c["cur_ship"] and \
                unit is not None:
            cbopts.draw_shield_arcs(surface, cam, art, unit, cbdraw.centre(
                unit), self.style, self._language)
        self._play.colours = cbdraw.player_colours(self._state)
        self._play.planet = self._planet_picture(c)
        now = time.monotonic()
        self._fades.update(c["units"], now)
        cbdraw.draw_units(surface, cam, art, c, self._play.colours, clock,
                          self._cache, self._play.planet,
                          phased_shown=unit is not None and
                          unit["owner"] == self._me(),
                          fades=self._fades, now=now, fast=self._play.fast)
        # TRANSCRIPTION `cursor_hidden` (work order 222): not while the
        # acting unit is moved, turned, teleported or fades (cloak), the
        # original's `_dont_draw_ship` (cmbtdrw1.cpp:815-819; Draw_Cloak_,
        # cmbtspec.cpp:95) — HD drew it on the cell the move left
        cur = c["cur_ship"]
        # TRANSCRIPTION `no_cursor` (work order 324): none with no acting
        # unit (cmbtdrw1.cpp:713 draws the cursor's box only for
        # `cur_ship >= 0`)
        if unit is not None and not self._computer(c) and \
                self._play.dont_draw() != cur and \
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
                    self._state)) and (k == "board" or field_by_hotkey(
                    getattr(self._state, "fields", None), hk))}
        pic = cbdraw.unit_picture(self._art, self._play.colours, unit, 0) \
            if unit is not None else None
        self._panel_unit = unit
        self._panel.log_open = self._logwin.open
        self._panel.draw(surface, self.style, unit, self._names, self._ken,
                         [w["active"] for w in (
                             cb.acting_unit(self._state.combat) or unit
                             or {}).get("weapons", ())],
                         self._board or self._pops.scan_mode and "scan", live,
                         self.layout.scale, pic, self._specials,
                         self._computer(self._state.combat or c),
                         self._hover(c), self._status_of(c, unit),
                         self._target(c))
        if self._panel.map is not None:              # work order 209 B1
            cbmap.draw(surface, self._panel.map, c, self._play.ordnance,
                       self._cam, self._art, self._play.colours,
                       self._play.planet, clock, self.layout.scale)
        self._opts.draw(surface, self.style, self.layout.scale, self._state,
                        band, self._panel.buttons)
        self._pops.draw(surface, self.style, self.layout.scale, self._state,
                        c, self._scan)
        self._logwin.draw(surface, self.style, self.layout.scale, area,
                          self._log, self._play.colours)
        self.render_help(surface)               # `cbhelp`, work order 200
        # TRANSCRIPTION `move_pointer` (work order 303): the arrow over a
        # reachable cell, the HD pointer elsewhere — each frame, as the
        # cells change with every move
        self._move_ptr.update(self._art, unit, self._move_cell(), win_h)

    def exit(self):
        self._move_ptr.clear()          # the HD pointer back off the battle
        super().exit()

    def _follow(self, c):
        """The original centres its view on each acting unit at its turn
        (`Snap_Center_Combat_Screen_`, combinit.cpp:2240) and keeps what a
        unit does in view; HD keeps the player's zoom and moves only when
        the acting unit, or the event being played, would be off the area
        or at its edge."""
        turn = (c["serial"], c["turn"], c["cur_ship"])
        at = None
        acting = cb.acting_unit(c)
        if turn != self._turn_seen:
            self._turn_seen = turn
            if acting is not None:      # nothing to snap to otherwise
                at = cbdraw.centre(acting)
        focus, busy = self._play.focus(), self._play.busy()
        self._home = self._home or busy
        if focus is not None:
            at = focus
        elif self._home and self._own_turn():
            # back to the player's own unit once a playback has ended and
            # its turn is ready (the original snaps to the acting unit,
            # combinit.cpp:2240)
            self._home = False
            at = cbdraw.centre(acting) if acting is not None else None
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

    def _status_of(self, c, unit):
        """What the panel's status picture needs (`cbstatus`), None for
        the planet (unit 0, OMISSION `status_planet`)."""
        if not c["cur_ship"] or unit is None:
            return None
        owner = unit["previous_owner"] if unit["previous_owner"] <= 7 \
            else unit["owner"]
        return (self._art, self._play.colours.get(owner, 0), unit,
                cbdraw.from_monster_file(unit))

    # ── input ──────────────────────────────────────────────────────
    def _send(self, op, a=0, b=0, c=0):
        combat = self._state.combat
        log.info("combat: %s %s %s %s (unit %d)", op, a, b, c,
                 combat["cur_ship"])
        self.app.client.combat_command(combat["serial"], combat["cur_ship"],
                                       cb.COMMANDS[op], a, b, c)
        self._sent = (cb.COMMANDS[op], time.monotonic())
