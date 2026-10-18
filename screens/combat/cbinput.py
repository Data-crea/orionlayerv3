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

FOOT = {0: 1, 1: 2, 2: 2, 3: 3, 4: 3, 5: 3}
DRAG_SLOP = 6                      # px before a press is a pan


#: The one field AUTO leaves: `Clear_Fields_` and a hidden field over the
#: whole screen as `_auto_button` (combat1.cpp:569-570).
FULL_SCREEN = (0, 0, 639, 479)


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

    def _hover(self, c):
        """The CTGT mask of the unit or missile under the pointer — what
        `Draw_Weapon_Status_Display_` is handed while the pointer is over
        another unit or a missile (cmbtdrw1.cpp:690-724; the pointer
        pictures 12 and 1, combat1.cpp:1818-1834) — or None. CTGT is the
        engine's own arc, range and legality verdict for the acting unit
        (open fix 54), the original's three tests."""
        targets = getattr(self._state, "targets", None)
        if self._pointer is None or self._cam is None or not targets or \
                targets.get("unit") != c["cur_ship"] or \
                not self._cam.on_field(*self._pointer):
            return None
        missile = cbdraw.missile_at(self._play.ordnance, self._cam,
                                    *self._pointer, self._me())
        if missile is not None:
            return targets["missiles"].get(missile, 0)
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

    def _move_cell(self):
        """The reachable cell under the pointer while the move pointer
        shows (TRANSCRIPTION `move_pointer`, `cbcursor`): the player's own
        turn and orders (the original's arrows are only there,
        combat1.cpp:2213-2296), outside BOARD and SCAN, nothing over the
        field — the OPTIONS panel, a popup, the log, the help —, a cell the
        engine marks legal that HD's click moves to (`handle_click`)."""
        if self._pointer is None or self._cam is None or self._board or \
                self._pops.scan_mode or self._tail or self._logwin.open or \
                self.help.visible or not self._own_turn() or \
                not self._cam.on_field(*self._pointer):
            return None
        if self._opts.up(self._state) or self._pops.showing(self._state):
            return None
        c = self._shown()
        if self._computer(c) or not self._ready() or cbdraw.missile_at(
                self._play.ordnance, self._cam, *self._pointer,
                self._me()) is not None:
            return None             # a click there fires, or is not sent
        cell = self._cam.cell_at(*self._pointer)
        if cell is None or not cb.legal(c["legal"], *cell) or \
                self._unit_at(cell) is not None:
            return None
        return cell

    def _computer(self, c):
        """`Ship_Controlled_By_Computer_` (combat1.cpp:217-227): another
        player's unit, a monster's, or the side under AUTO (`_auto_combat`
        is the acting side's flag, :1564-1566). HD runs single-player
        battles, so the human is this client's player."""
        unit = c["units"][c["cur_ship"]]
        side = "auto_attacker" if unit["owner"] == c["attacker"] else \
            "auto_defender"
        return unit["owner"] != self._me() or bool(c.get(side))

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
            elif cbdraw.unit_ref(c["units"][target],
                                   "stasis_source_idx") is not None:
                # TRANSCRIPTION `release_stasis` (work order 214): a click
                # on an enemy held in a stasis field asks to release it
                # (KENTEXT 61) and releases it on YES, as the original's
                # click does (combat1.cpp:782-796, `Ship_Is_In_Stasis_`
                # cmbtmov1.cpp:53-58); open fix 58's REMOVE_STASIS runs
                # that branch, its box HD's. A FIRE there is refused.
                self._send("remove_stasis", target)
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

    def handle_mousewheel(self, dy, screen_x, screen_y):
        if self._logwin.wheel(dy):
            return
        if self._pops.showing(self._state) in ("local", "scan"):
            # TRANSCRIPTION `scan_wheel` (work order 299, Data's P7 of 298):
            # the original's scan is its own input loop with no zoom
            # (`Detailed_View_Ship_` cmbtdrw1.cpp:156-247); the wheel is the
            # scan's while it is up and never zooms the battle under it
            return
        if self._cam is not None:
            self._cam.zoom(dy, (screen_x, screen_y))

    def handle_key(self, key):
        if self._logwin.key(key):
            return
        if self._tail:
            return
        if self._pops.key(key, self._state, self.app.client) or \
                self._opts.key(key, self._state, self.app.client):
            return
        if key == pygame.K_c and self._cam is not None and self._shown():
            u = self._acting()
            self._cam.centre_on(*cbdraw.centre(u))    # the original's C
        elif key == pygame.K_ESCAPE:
            self._board = self._pops.scan_mode = False
        else:
            # A S B R W D T Z O — the battle's buttons' hotkeys (combat1.cpp:
            # 109-187): the one rule every screen shares (work order 230 E)
            super().handle_key(key)
