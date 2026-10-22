"""The battle's gestures — the combat screen's input, a mixin of
`screen.CombatScreen` (moved out of `screen.py` by work order 202 for the
300-line guideline; WHAT EACH GESTURE SENDS is that module's docstring).

Nothing here sends while the battle's end is playing (`_tail`, work order
202 D): a click, a right click, a key or a release is not a choice on a
battle that has ended. The camera (wheel, drag) is HD's own and stays.
"""
import logging

import pygame

from core import combatblocks as cb
from . import cbdraw, cbhelp, cbmap, cbpanel, cbtarget

log = logging.getLogger("combat")

FOOT = cbdraw.FOOT
#: TRANSCRIPTION `move_target` (work order 304, Data's P1 of 303): how far
#: the original takes the pointer's point back before it picks the cell a
#: ship's corner goes to, by size class — its frame's `ship_draw_size`
#: (v2 cmbtdrw1.cpp:706-717) and its click's arithmetic (v2 combat1.cpp:
#: 850-862; combat1.cpp:724-733)
SHIFT = {0: 0, 1: 10, 2: 10, 3: 20, 4: 20, 5: 20}
DRAG_SLOP = 6                      # px before a press is a pan
#: TRANSCRIPTION `planet_footprint` (work order 305): the planet's cells a
#: side by its size, tiny 3 .. huge 8, and 6 for a battle without a colony
#: or a size the switch does not name (`Assign_Combat_Grids_`,
#: combat1.cpp:1970-1990; v2 :2451-2468). HD reads the size where the
#: planet's picture is read (`cbart.planet_picture`): the colony record
#: CMBT names and its planet record; neither on the wire is the original's
#: no-colony case, 6.
PLANET_SIDE = {0: 3, 1: 4, 2: 6, 3: 7, 4: 8}
NO_COLONY_SIDE = 6
#: the battle's buttons by the key that presses them (combat1.cpp:126-131,
#: :178): HD's own path for each, the click's (`CombatInput._button`)
KEY_BUTTON = {ord(chr(hk).lower()): k for k, _w, hk in cbpanel.BUTTONS}
#: the missile warning's hidden field, in the reduced map's place while the
#: warning is up (combat1.cpp:116-118)
WARNING_FIELD = (505, 370, 622, 464)


def planet_side(state, c):
    """The battle planet's footprint side in cells (`planet_footprint`)."""
    col = c.get("colony", -1)
    if col is None or col < 0:
        return NO_COLONY_SIDE
    try:
        from core.structs import colony as colony_struct
        from core.structs import planet as planet_struct
        colony = colony_struct.SPEC.parse(state.colonies_raw[col])
        size = int(planet_struct.parse(state.planets_raw[colony.planet]).size)
    except (IndexError, TypeError, AttributeError, ValueError):
        return NO_COLONY_SIDE
    return PLANET_SIDE.get(size, NO_COLONY_SIDE)


def missile_warning(fields):
    """True while the battle's list holds the missile warning's field in
    the reduced map's place — the one place HD learns the warning is up
    (the flag itself is not on the wire)."""
    return any((f.x, f.y, f.x_end, f.y_end) == WARNING_FIELD and f.index
               for f in fields or [])


#: The one field AUTO leaves: `Clear_Fields_` and a hidden field over the
#: whole screen as `_auto_button` (combat1.cpp:569-570).
FULL_SCREEN = (0, 0, 639, 479)


def move_target(cam, x, y, size_class):
    """TRANSCRIPTION `move_target`: the cell a click at window point (x, y)
    moves the acting ship's corner to, the same cell its frame is drawn on
    — the ship's middle under the pointer. The original's frame takes
    `(pointer - s + 12) / 20` (12: the pointer picture's point,
    v2 cmbtdrw1.cpp:716-717) and its click with an arrow pointer
    `xpos / 2 - 1` or `(xpos + 1) / 2 - 1` of the 10 px grid's `xpos`
    (v2 combat1.cpp:851-861, v2 fields.cpp:2813): both floor((point - s) /
    20) with s 0, 10 or 20 px by size class. So a ship of size class 3-5
    goes one cell up and left of the pointer's cell, one of 1-2 only
    while the point is in its cell's left or top half; the arrow areas are
    shifted to match (`Assign_Mouse_Images`, v2 combat1.cpp:2321-2373). HD's
    point is the window pointer mapped into the world, the same number.
    DEVIATION `footprint_view_edge`: the original clamps its frame's cell
    to its 32 x 18 cell view while its click goes one cell further (at
    the view's left or top edge with s > 0); HD's view is no grid of
    cells, so frame and click take the same cell everywhere (at the
    right and bottom edge the original's two agree; its frame is also cut
    at y 350, v2 cmbtdrw1.cpp:702-703).
    DEVIATION `footprint_arrow_areas`: the original moves its arrow areas
    by s px and, for size class 1-2, empties the neighbours that hold no
    arrow (v2 combat1.cpp:2321-2373); in the few pixels left with no area its
    pointer has no shape and offset 0, and its click takes the unshifted
    cell (a rim cell of the reachable area, or a reachable cell beside an
    enemy). HD takes `move_target`'s cell for every point, so the frame
    and the click never part. None off the field or outside the world's
    cells."""
    if not cam.on_field(x, y):
        return None
    wx, wy = cam.to_world(x, y)
    s = SHIFT.get(int(size_class), 20)
    cx, cy = int((wx - s) // cbdraw.CELL), int((wy - s) // cbdraw.CELL)
    if not (0 <= cx < cb.GRID_W and 0 <= cy < cb.GRID_H):
        return None
    return cx, cy


def auto_off_field(state, me):
    """TRANSCRIPTION `auto_off` (work order 229 F): while the player's side
    plays under AUTO the engine's list is that one full-screen field, and
    the computer's turn polls it (cmbtai.cpp:598, :616, :740): ANY click
    switches AUTO off. Its index, or None when AUTO is not the player's or
    the list is not that shape. Until 229 HD looked AUTO up by its hotkey
    and waited for the player's turn, so AUTO, once on, could not be
    switched off in HD (seen live: the flag stayed on to the battle's end)."""
    c = getattr(state, "combat", None)
    if not c:
        return None
    mine = c.get("auto_attacker") if c["attacker"] == me else \
        c.get("auto_defender")
    live = [f for f in (getattr(state, "fields", None) or []) if f.index]
    if not mine or len(live) != 1:
        return None
    f = live[0]
    return f.index if (f.x, f.y, f.x_end, f.y_end) == FULL_SCREEN else None


def field_by_hotkey(fields, hotkey, types=(0, 1)):
    return next((f for f in fields or [] if f.index and f.hotkey == hotkey
                 and f.field_type in types), None)


class CombatInput:
    _pointer = None
    _held = None                # (`_moment`, time) of a field just activated
    _round = None               # (serial, turn) the modes were lit in
    _engine_board = False       # the engine's BOARD flag as last seen

    def _hover(self, c):
        """The CTGT mask of the unit or missile under the pointer — what
        `Draw_Weapon_Status_Display_` is handed while the pointer is over
        another unit or a missile (cmbtdrw1.cpp:690-724; the pointer
        pictures 12 and 1, combat1.cpp:1818-1834) — or None. CTGT is the
        engine's own arc, range and legality verdict for the acting unit
        (open fix 54), the original's three tests. A missile is the one
        hit area of `cbtarget.missile_under` (TRANSCRIPTION
        `missile_field`), any owner's."""
        targets = getattr(self._state, "targets", None)
        if cb.acting_index(c) is None:
            return None             # no acting unit, no verdict for it
        if self._pointer is None or self._cam is None or not targets or \
                targets.get("unit") != c["cur_ship"] or \
                not self._cam.on_field(*self._pointer):
            return None
        missile = cbtarget.missile_under(self._play.ordnance, self._cam,
                                         *self._pointer)
        if missile is not None:
            return targets["missiles"].get(missile["index"], 0)
        cell = self._cam.cell_at(*self._pointer)
        unit = self._unit_at(cell) if cell is not None else None
        if unit is None or unit == c["cur_ship"]:
            return None
        masks = targets["units"]
        return masks[unit] if unit < len(masks) else 0

    def _target(self, c):
        """What the systems window shows instead of the systems
        (`cbtarget`, TRANSCRIPTION `target_box`, work order 259): a missile
        under its hidden field, else a unit other than the acting one —
        only in the player's own orders and outside BOARD mode, the
        pointer pictures 1 and 12 (combat1.cpp:1730-1834) — or None.
        HD EXTENSION `scan_hover`: in SCAN mode too, the unit only — the
        original's scan pointer (13, :1785-1790) shows nothing there, HD
        shows the unit the click would scan (Data, 17 Oct 2026)."""
        if self._pointer is None or self._cam is None or self._board or \
                not self._own_turn() or \
                not self._cam.on_field(*self._pointer):
            return None
        m = None if self._pops.scan_mode else cbtarget.missile_under(
            self._play.ordnance, self._cam, *self._pointer)
        if m is not None:
            return ("missile", m, c,
                    (self._play.ordnance or {}).get("missiles", []),
                    self._cache)
        cell = self._cam.cell_at(*self._pointer)
        unit = self._unit_at(cell) if cell is not None else None
        if unit is None or unit == c["cur_ship"]:
            return None
        u = c["units"][unit]
        return ("unit", u, self._status_of(dict(c, cur_ship=unit), u),
                cbdraw.unit_picture(self._art, self._play.colours, u, 0))

    def _frame_cell(self, point=None):
        """TRANSCRIPTION `footprint_frame` (work order 304): the cell the
        red frame stands on — `move_target` of the pointer when the engine
        marks it legal (2000), outside SCAN, on the player's own turn with
        the orders up, not the OPTIONS panel (v2 cmbtdrw1.cpp:699, :702,
        :730-733). Not gated, as the original's is not: BOARD, a missile
        under the pointer, a command in flight, SHOW LEGAL MOVES.
        Nothing over the field either — a popup, the log, the help — where
        the original's field is not its input.
        TRANSCRIPTION `board_own_cells` (work order 305): in BOARD the
        acting ship's own footprint holds its index, not -1, so
        `Set_Legal_Moves_` marks none of those cells 2000
        (`Assign_Combat_Grids_`, combat1.cpp:1970 and :1991-2005,
        `Set_Legal_Moves_` :2329; v2 :2451). HD's bitmap is the engine's,
        which never sees HD's local BOARD: the frame leaves those cells.
        DEVIATION `footprint_playback`: none while HD plays the battle's
        events, nor under AUTO (its own turn, `_own_turn`, as the reachable
        cells and the arrow: AUTO's list is one full-screen field, not the
        battle's); the original draws it in its animation loops from the
        cells it had before the move, HD's snapshot already holds the next
        ones, and under AUTO from the cells of the ship the computer moves
        (v2 cmbtai.cpp:896). None once the pointer has left the window
        (`handle_pointer_leave`)."""
        point = point or self._pointer
        if point is None or self._cam is None or self._pops.scan_mode or \
                self._logwin.open or self.help.visible or \
                not self._own_turn():
            return None
        if self._opts.up(self._state) or self._pops.showing(self._state):
            return None
        c = self._shown()
        u = cb.acting_unit(c)
        if u is None:
            return None
        cell = move_target(self._cam, point[0], point[1], u["size_class"])
        if cell is None or not cb.legal(c["legal"], *cell):
            return None
        n = FOOT.get(int(u["size_class"]), 1)
        if self._board and u["x"] <= cell[0] < u["x"] + n and \
                u["y"] <= cell[1] < u["y"] + n:
            return None
        return cell

    def _move_cell(self, point=None):
        """The cell a click moves the acting ship's corner to while the
        move pointer shows (TRANSCRIPTION `move_pointer`, `cbcursor`;
        TRANSCRIPTION `move_target`): the frame's cell (`_frame_cell`), in
        the player's orders (the original's arrows are only there,
        v2 combat1.cpp:2213-2296), outside BOARD (v2 :2275-2283, and its
        click moves nothing, v2 :872), no missile under the pointer — any
        owner's, its field comes first (`missile_field`) — and no command
        in flight. The footprint of a legal cell is free but for the ship
        itself (`Set_Legal_Moves`, v2 combat1.cpp:2877, :2890), so over a
        short move the pointer may stand on the acting ship and still move
        it."""
        point = point or self._pointer
        cell = self._frame_cell(point)
        if cell is None or self._board:
            return None
        if self._computer(self._shown()) or not self._ready() or \
                cbtarget.missile_under(self._play.ordnance, self._cam,
                                       *point) is not None:
            return None             # a click there fires, or is not sent
        return cell

    def _computer(self, c):
        """`Ship_Controlled_By_Computer_` (combat1.cpp:217-227): another
        player's unit, a monster's, or the side under AUTO (`_auto_combat`
        is the acting side's flag, :1564-1566). HD runs single-player
        battles, so the human is this client's player."""
        unit = cb.acting_unit(c)
        if unit is None:
            # UNVERIFIED: nobody acts, so no human's orders — the
            # computer's side of every question asked here
            return True
        side = "auto_attacker" if unit["owner"] == c["attacker"] else \
            "auto_defender"
        return unit["owner"] != self._me() or bool(c.get(side))

    def _unit_at(self, cell):
        """The live unit whose footprint holds `cell`: a ship's by its size
        class, the planet's by its size (TRANSCRIPTION `planet_footprint`)."""
        c = self._shown()
        for i, u in enumerate(c["units"]):
            if u["unit_status"] != 0 or (i and u["structure_max"] <= 0):
                continue
            n = FOOT.get(int(u["size_class"]), 1) if i else \
                planet_side(self._state, c)
            if u["x"] <= cell[0] < u["x"] + n and u["y"] <= cell[1] < u["y"] + n:
                return i
        return None

    def handle_click(self, screen_x, screen_y):
        # the battle log (`cblog`, work order 267): its window takes every
        # click while it is up; LOG opens it at any moment, AUTO included
        if self._logwin.click(screen_x, screen_y):
            return None
        r = self._panel.rects.get("log")
        if r is not None and r.collidepoint(screen_x, screen_y) and \
                not self._opts.up(self._state):
            self._logwin.toggle()
            return None
        if self._tail:                       # its end playing: no input
            return None
        if self.help_consumes_click(screen_x, screen_y):
            return None
        off = auto_off_field(self._state, self._me())
        if off is not None:                  # any click ends AUTO (229 F)
            log.info("combat: AUTO off -> field %d", off)
            if self.app.connected:
                self.app.client.activate_field(off)
            return None
        if self._state is None or getattr(self._state, "combat", None) is None \
                or self._pops.click(screen_x, screen_y, self._state,
                                    self.app.client, self._scan) or \
                self._opts.click(screen_x, screen_y, self._state,
                                 self.app.client):
            return None
        key = self._panel.button_at(screen_x, screen_y)
        if key is not None:
            return self._button(key)
        at = cbmap.cell_at(self._panel.map, screen_x, screen_y) \
            if self._panel.map is not None else None
        if at is not None:                   # the map's grid field: the view
            if self._cam is not None:        # there, nothing sent (`cbmap`)
                self._cam.centre_on(at[0] * cbmap.CELL, at[1] * cbmap.CELL)
            return None
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
        me, cur = self._me(), cb.acting_index(c)
        if cur is None:
            return None
        missile = cbtarget.missile_under(self._play.ordnance, self._cam,
                                         screen_x, screen_y)
        move = self._move_cell((screen_x, screen_y))
        target = self._unit_at(cell)
        if missile is not None:
            # TRANSCRIPTION `missile_field` (work order 305): a missile's
            # hidden field comes before the map's in the list, in every
            # mode, and fires only at another owner's; a click on the
            # player's own missile is taken and does nothing — no move, no
            # fire (combat1.cpp:442-465, `Add_Missile_Fields_` :1658-1677;
            # v2 :557-582, :2150-2156)
            if int(missile.get("owner", -1)) != c["units"][cur]["owner"]:
                self._send("fire_missile", missile["index"])
            return None
        if self._pops.scan_mode:             # SCAN, then a unit: HD's own view
            # TRANSCRIPTION `scan_mode_kept` (work order 306): the original's
            # click scans any live unit and leaves `skan_flag` on
            # (combat1.cpp:823-824), so SCAN stays lit and the next unit
            # clicked is scanned too; only the round's start, BOARD and the
            # SCAN button put it out (:384, :670, combinit.cpp:1013). A
            # click on no unit scans nothing and leaves SCAN on (:743, :823)
            if target is not None:
                self._pops.local_unit = target
            return None
        if move is not None:                 # TRANSCRIPTION `move_target`
            self._send("move", *move)
        elif self._board:
            # BOARD, then any live unit: the original boards whatever it is
            # (`Initiate_Boarding_Action_`, combat1.cpp:825-826); the light
            # stays on until a boarding is carried out (:2149). An enemy
            # (the planet too) is open fix 58's BOARD.
            # TRANSCRIPTION `board_own_unit_box` (work order 306): on one of
            # the player's own units too — the original refuses it in its
            # box, KENTEXT 0x40, or 0x41 for a captured one, the own planet
            # 0x3F (:2032-2037, `Warning_Box_` :2086-2090); open fix 101
            # lets that BOARD through to the original's handler and its box
            # reaches HD as every box does (MSGB, open fix 29). Not on the
            # acting unit itself, which the engine still refuses
            if target is not None and target != cur:
                self._send("board", target)
        elif target is not None and target != cur and \
                c["units"][target]["owner"] != me:
            if cbdraw.unit_ref(c["units"][target],
                               "stasis_source_idx") is not None:
                # TRANSCRIPTION `release_stasis` (work order 214): a click
                # on an enemy held in a stasis field asks to release it
                # (KENTEXT 61) and releases it on YES, as the original's
                # click does (combat1.cpp:782-796, `Ship_Is_In_Stasis_`
                # cmbtmov1.cpp:53-58); open fix 58's REMOVE_STASIS runs
                # that branch, its box HD's. A FIRE there is refused.
                self._send("remove_stasis", target)
            else:
                # a phased enemy (`special_status_flag` 4) too: the
                # original's click says why not in its box (KENTEXT 80,
                # combat1.cpp:797-802), which open fix 101's FIRE runs and
                # HD shows as every box (MSGB, open fix 29); no shot, the
                # rows unchanged
                self._send("fire", target, self._mask(cur, c["units"][cur]))
        elif target is not None and target != cur:
            self._send("select", target)
        return None

    def _button(self, key):
        """A battle button, clicked or by its key (`KEY_BUTTON`): one path,
        one set of guards. SCAN and BOARD are modes HD holds locally, lit
        only in the player's own orders (the original's radio fields are
        only there, combat1.cpp:127-128) and each putting the other out
        (:627-628, :670); the rest are the original's own fields by
        activation, on the player's own turn with no command in flight
        (`_ready`) — a field activated under a pending command could be
        swallowed by it — and the next only once the engine has moved on
        (`_hold_input`)."""
        if key in ("board", "scan"):
            if not self._own_turn():
                return None
            if key == "board" and not self._board:
                self._board, self._pops.scan_mode = True, False
            elif key == "board":
                self._board_off()
            else:
                if not self._pops.scan_mode:
                    self._board_off()
                self._pops.scan_mode = not self._pops.scan_mode
            return None
        hotkey = dict((k, hk) for k, _w, hk in cbpanel.BUTTONS)[key]
        f = field_by_hotkey(getattr(self._state, "fields", None), hotkey)
        if f is not None and self._ready() and self.app.connected:
            log.info("combat: %s -> field %d", key, f.index)
            self.app.client.activate_field(f.index)
            self._hold_input()
        return None

    def _moment(self):
        """What a battle field's effect changes on the wire: the round, the
        acting unit and its place in the order, the AUTO and super-fast
        flags, the engine's BOARD flag, and whether the battle's own list
        stands (a box or the OPTIONS panel replaces it)."""
        live = getattr(self._state, "combat", None)
        if live is None:
            return None
        return (live["serial"], live["turn"], live["cur_ship"],
                live["cur_ptr"], live.get("auto_attacker"),
                live.get("auto_defender"), live.get("super_fast"),
                live.get("board_flag"),
                tuple((f.index, f.field_type, f.x, f.y, f.hotkey) for f in
                      getattr(self._state, "fields", None) or []))

    def _board_off(self):
        """BOARD out. The engine's own flag is set by a BOARD command and
        stays on when the boarding is refused or cancelled (combat1.cpp:
        2084-2091, :2149); while it is on the engine refuses every MOVE,
        FIRE and SELECT (ext_api.cpp v2 :3216). So HD puts it out the
        original's way, its radio key B (fields.cpp:1033-1039), once,
        only where the battle's list has that field. While the key cannot
        be sent (a command in flight, a field held) BOARD stays lit: an
        HD light off over the engine's flag on is the silent lock-up
        itself (the audit's item 1)."""
        live = getattr(self._state, "combat", None)
        if not (live and live.get("board_flag")):
            self._board = False
        elif self._ready() and self.app.connected and field_by_hotkey(
                getattr(self._state, "fields", None), ord("B")):
            log.info("combat: the engine's BOARD off (its key)")
            self.app.client.inject_key(ord("b"))
            self._board = False
            self._hold_input()

    def _follow_modes(self, combat):
        """TRANSCRIPTION `modes_per_round` (work order 305): SCAN and BOARD
        go out at each new round (`Do_Combat_Turn_`, combat1.cpp:384-385;
        v2 :499-500). TRANSCRIPTION `board_mode_kept`: BOARD is lit while
        the engine's flag is — a BOARD command sets it, a carried-out
        boarding clears it (:2149), a refused or cancelled one leaves it
        on, as the original's light (:2084-2091): HD follows each change
        of the engine's flag."""
        rnd = (combat["serial"], combat["turn"])
        if rnd != getattr(self, "_round", None):
            self._round = rnd
            self._board = self._pops.scan_mode = False
        flag = bool(combat.get("board_flag"))
        if flag != getattr(self, "_engine_board", False):
            self._engine_board = self._board = flag

    def _right_owner(self):
        """Who a right press belongs to instead of the battle (work order
        298, Data): the scan view (HD's or the engine's, 'local' / 'scan'),
        the board popup ('board'), the battle log ('log'), an open help
        panel ('help') — or None, the battle's.

        TRANSCRIPTION `modal_right_click`: the original's scan and its
        board popup are their own input loops
        (`Detailed_View_Ship_` cmbtdrw1.cpp:156-247, `Board_Popup_`
        :1581-1666). `Get_Input_`'s cancel is off since the main screen
        (`Disable_Cancel_`, fields.cpp:112-114, mainscr_main.cpp:281), so
        a right click returns the field under it negative (fields.cpp:1375,
        :1526-1528), which neither loop answers — both compare positive
        ids — and the battle under them never turns a ship.
        DEVIATION `scan_right_click`: both keep the battle's help list —
        the scan saves it and does not clear it (`Save_Help_List_`,
        evanhelp.cpp:356-360), the board popup never touches it
        (`Clear_Fields_` fields.cpp:212-223 leaves it) — and
        `Check_Help_List_` runs before the fields (fields.cpp:1255, :1379),
        so by the source a right click over a battle help region opens
        that help over either (read, not seen live); HD's scan and board
        popup consume every right click and right drag — no help, no FACE,
        no pan, no pin (Data, 298, P1 of 297). The camera drag is HD's own
        (HD EXTENSION `free_camera`); a window over the battle stops it
        the same way."""
        kind = self._pops.showing(self._state)
        if kind is not None:
            return kind
        if self._logwin.open:
            return "log"
        if self.help.visible:
            return "help"
        return None

    def handle_right_button(self, down, screen_x, screen_y):
        """A right DRAG pans (the galaxy map's gesture, HD EXTENSION
        `free_camera`); a right CLICK is FACE toward the cell, as the
        original's right click on its map (combat1.cpp:696-710). A press
        that starts or ends while a window is over the battle is that
        window's (`_right_owner`): the press, its motion and its release."""
        if down:
            # [start, last, moved, owner]: an owner keeps it off the battle
            # to its release, even when the window closes on the way
            self._press = [(screen_x, screen_y), (screen_x, screen_y), False,
                           self._right_owner()]
            return
        press, self._press = self._press, None
        owner = (press[3] if press is not None else None) or \
            self._right_owner()
        if self._tail or press is None or press[2]:
            return
        if owner == "help":
            cbhelp.right(self, screen_x, screen_y)   # a click closes it
            return
        if owner is not None or cbhelp.right(self, screen_x, screen_y):
            return
        if self._opts.up(self._state):
            # TRANSCRIPTION `options_right_click` (work order 299, Data's P1
            # of 298): while OPTIONS is up the original adds no space field
            # (`_space_field = -100`, combat1.cpp:155, against :111-114), so
            # its right click never reaches Turn_To_Face_ (:702); HD sends
            # no FACE. Under the panel's own list `_ready` is False already
            # (no space field, `battle_list`); COPT and the list are two
            # messages, and this holds the moment between them. The drag
            # stays HD's camera (`free_camera`).
            return
        if self._ready() and self._cam is not None:
            cell = self._cam.cell_at(screen_x, screen_y)
            if cell is not None:
                self._send("face", *cell)

    def handle_left_release(self, screen_x, screen_y):
        if not self._tail:
            self._pops.release(self._state, self.app.client)

    def handle_left_cancel(self):
        self._pops.cancel()

    def handle_right_cancel(self):
        """The right press ends without its effect (work order 299, Data's
        P2 of 298): its release went to a game box or a turn popup over the
        battle (`main.App`'s right gate, as `handle_left_cancel` for the left
        button), so no later motion pans with no button held and no FACE
        follows."""
        self._press = None

    def handle_mouse_motion(self, screen_x, screen_y):
        self._pointer = (screen_x, screen_y)    # the rows' hover (`_hover`)
        self._pops.motion(screen_x)
        if self._press is not None and self._cam is not None:
            (x0, y0), (lx, ly), moved, owner = self._press
            # a window opened under a held drag takes the rest of it
            owner = owner or self._right_owner()
            if moved or abs(screen_x - x0) + abs(screen_y - y0) > DRAG_SLOP:
                if owner is None:
                    self._cam.pan(screen_x - lx, screen_y - ly)
                self._press = [(x0, y0), (screen_x, screen_y), True, owner]
        return super().handle_mouse_motion(screen_x, screen_y)

    def handle_pointer_leave(self):
        """The pointer left the window (`main.App`, pygame's WINDOWLEAVE):
        nothing is under it, so no frame, no move arrow, no target box —
        HD drew the last ones until the pointer came back (work order
        305)."""
        self._pointer = None

    def handle_mousewheel(self, dy, screen_x, screen_y):
        if self.help_consumes_wheel(dy) or self._logwin.wheel(dy):
            return                  # an open help entry scrolls first
        if self._pops.showing(self._state) in ("local", "scan", "board"):
            # TRANSCRIPTION `scan_wheel` (work order 299, Data's P7 of 298):
            # the original's scan is its own input loop with no zoom
            # (`Detailed_View_Ship_` cmbtdrw1.cpp:156-247); the wheel is the
            # scan's while it is up and never zooms the battle under it —
            # nor under the board popup, its own loop as well
            # (`Board_Popup_` cmbtdrw1.cpp:1581-1666; work order 305)
            return
        if self._cam is not None:
            self._cam.zoom(dy, (screen_x, screen_y))

    def handle_key(self, key):
        # an open help closes first, ESC included, as on every screen
        # (`ScreenHelp.help_consumes_key`; work order 305); the log is
        # modal for keys as for clicks (`cblog`): ESC closes it, the rest
        # never reach the battle under it
        if self.help_consumes_key(key) or self._logwin.key(key) or \
                self._logwin.open:
            return
        if self._tail:
            return
        if self._pops.key(key, self._state, self.app.client) or \
                self._opts.key(key, self._state, self.app.client):
            return
        ev = getattr(self, "_key_event", None)     # Alt+letter: the game's
        alt = ev is not None and getattr(ev, "key", None) == key and \
            getattr(ev, "mod", 0) & pygame.KMOD_ALT
        if key == pygame.K_c and self._cam is not None and self._shown():
            u = self._acting()
            if u is not None:
                self._cam.centre_on(*cbdraw.centre(u))    # the original's C
        elif key == pygame.K_ESCAPE:
            self._board_off()
            self._pops.scan_mode = False
        elif key in KEY_BUTTON and not alt:
            # A S B R W D O press the button they name, its own path and
            # guards (combat1.cpp:126-131, :178): S and B light HD's own
            # SCAN and BOARD, never the engine's flags behind them
            self._button(KEY_BUTTON[key])
        elif self._ready():
            # T Z [ and the rest — the one rule every screen shares (work
            # order 230 E), under the buttons' guards: the player's own
            # orders, nothing playing, no command in flight
            super().handle_key(key)
            # held only where `_moment` sees the effect: T ends the turn
            # (`_end_of_turn_button`, combat1.cpp:132), Z the super-fast
            # flag (:145); '[' (:113) has no handler and changes nothing
            if key in (pygame.K_t, pygame.K_z) and field_by_hotkey(
                    getattr(self._state, "fields", None),
                    ord(chr(key).upper()), types=range(256)):
                self._hold_input()
