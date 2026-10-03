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
from . import cbdraw, cbhelp, cbmap, cbpanel

log = logging.getLogger("combat")

FOOT = {0: 1, 1: 2, 2: 2, 3: 3, 4: 3, 5: 3}
DRAG_SLOP = 6                      # px before a press is a pan


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
                not pygame.Rect(self._cam.area).collidepoint(self._pointer):
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
        if self._tail:                       # its end playing: no input
            return None
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
        if self._tail:
            return
        if press is None or press[2] or cbhelp.right(self, screen_x,
                                                     screen_y):
            return
        if self._ready() and self._cam is not None:
            cell = self._cam.cell_at(screen_x, screen_y)
            if cell is not None:
                self._send("face", *cell)

    def handle_left_release(self, screen_x, screen_y):
        if not self._tail:
            self._pops.release(self._state, self.app.client)

    def handle_mouse_motion(self, screen_x, screen_y):
        self._pointer = (screen_x, screen_y)    # the rows' hover (`_hover`)
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
