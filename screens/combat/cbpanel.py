"""The acting unit's panel — work order 197 C.

WHAT THE ORIGINAL SHOWS in its bottom panel (COMBAT.LBX 0 at (0, 351),
cmbtdrw1.cpp:446-448, `dev:doc/combat_drawing_reading.md` §6): the acting
unit's name (:517-521), its weapons — count right-aligned, name, the arc or
the ammunition (:2765-2933) — its systems box (drive, shields, computer,
structure, armour, speed and "Remaining", :360-425), and the buttons AUTO,
SCAN, BOARD, RETREAT, WAIT, DONE (:1268-1305). SCAN and BOARD are modes HD
holds itself until a unit is clicked (`cbpopups`, work order 199).

DEVIATION `hud_panel`: HD draws them as HUD blocks along the bottom of the
window, in OrionLayer's words, not COMBAT.LBX 0; the shield rings round the
status picture and the reduced map are not drawn (the whole field is on the
screen, HD EXTENSION `whole_grid`). Each weapon row is a SWITCH, as the
original's eight hidden weapon rows are (combat1.cpp:594-613: a click cycles
the slot on and off) — HD keeps the switch itself and sends the mask with
FIRE (open fix 58), one command per shot (decision 47).
"""
import pygame

from core.hud import blocks as hud
from core.hud import text as hudtext

BUTTONS = (("auto", "AUTO", ord("A")), ("scan", "SCAN", ord("S")),
           ("board", "BOARD", ord("B")), ("retreat", "RETREAT", ord("R")),
           ("wait", "WAIT", ord("W")), ("done", "DONE", ord("D")))


class Panel:
    def __init__(self):
        self.rects = {}           # button key -> window rect
        self.rows = []            # (window rect, slot) of the weapon rows

    @staticmethod
    def area(win_w, win_h):
        """The panel's band: the original's 129 of 480 rows, at the bottom."""
        h = int(win_h * 129 / 480 * 0.75)
        return pygame.Rect(0, win_h - h, win_w, h)

    def draw(self, surface, style, unit, names, mask, board_mode, live,
             scale):
        band = self.area(*surface.get_size())
        hud.panel(surface, band.inflate(-8, -8), scale, dense=True)
        pad = int(16 * scale)
        inner = band.inflate(-2 * pad, -2 * pad)
        size = max(10, int(22 * scale))
        small = max(9, int(18 * scale))
        self.rects, self.rows = {}, []
        if unit is None:
            return
        # the name and the systems (left)
        left = pygame.Rect(inner.x, inner.y, int(inner.w * 0.22), inner.h)
        hudtext.blit(surface, style.render_text(unit["name"], size,
                                                hudtext.colour("value")[:3]),
                     pygame.Rect(left.x, left.y, left.w, size + 4),
                     align="left")
        facts = (("Structure", unit["structure_max"] - unit["structure_damage"],
                  unit["structure_max"]),
                 ("Armor", unit["armor_remaining"], None),
                 ("Shields", max(unit["shield_arc_current"]),
                  unit["shield_arc_max"]),
                 ("Drive", unit["drive_current_hits"], unit["drive_max_hits"]),
                 ("Computer", unit["computer_current_hits"],
                  unit["computer_max_hits"]),
                 ("Remaining", unit["movement_left"], unit["current_speed"]))
        y = left.y + size + 8
        for label, value, top in facts:
            text = f"{label}  {value}" + (f" / {top}" if top else "")
            hudtext.blit(surface, style.render_text(
                text, small, hudtext.colour("label")[:3]),
                pygame.Rect(left.x, y, left.w, small + 2), align="left")
            y += small + 3
        # the weapons (middle): each a switch
        mid = pygame.Rect(left.right + pad, inner.y, int(inner.w * 0.45),
                          inner.h)
        row_h = max(small + 4, mid.h // 8)
        for k, wpn in enumerate(unit["weapons"]):
            if wpn["count"] <= 0 or wpn["weapon_id"] <= 0:
                continue
            r = pygame.Rect(mid.x, mid.y + k * row_h, mid.w, row_h - 2)
            on = bool(mask >> k & 1)
            hud.small_button(surface, r, scale, "active" if on else "normal")
            name = names(wpn["weapon_id"]) or f"weapon {wpn['weapon_id']}"
            shots = wpn["shots_left"] if wpn["shots_left"] >= 0 else \
                wpn["count"]
            hudtext.blit(surface, style.render_text(
                f"{shots}  {name}" + (f"  x{wpn['ammo']}" if wpn["ammo"] > 0
                                      else ""), small,
                hudtext.colour("button")[:3]), r.inflate(-pad, 0),
                align="left")
            self.rows.append((r, k))
        # the buttons (right), each only while the live list carries it
        right = pygame.Rect(mid.right + pad, inner.y,
                            inner.right - mid.right - pad, inner.h)
        bw, bh = (right.w - pad) // 2, max(small + 8, right.h // 3 - pad)
        for n, (key, word, hotkey) in enumerate(BUTTONS):
            r = pygame.Rect(right.x + (n % 2) * (bw + pad),
                            right.y + (n // 2) * (bh + pad // 2), bw, bh)
            state = "active" if board_mode == {"board": True,
                                               "scan": "scan"}.get(key) else \
                "normal" if key in live else "disabled"
            hud.small_button(surface, r, scale, state, word,
                             style_renderer=style)
            if key in live:
                self.rects[key] = r
        return band

    def button_at(self, x, y):
        return next((k for k, r in self.rects.items()
                     if r.collidepoint(x, y)), None)

    def row_at(self, x, y):
        return next((k for r, k in self.rows if r.collidepoint(x, y)), None)
