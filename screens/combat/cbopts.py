"""The battle's OPTIONS panel in HD, and what its options draw — work order
200 A2 (open fix 68's COPT, `core/combatoptions.py`). Work order 199 had
left the panel out (its omission, now gone, carried the same name).

TRANSCRIPTION `combat_options` — THE PANEL. OPTIONS (the panel's info
button, hotkey O, combat1.cpp:178) flips `_order_info_flag` and slides
COMBAT.LBX 9 up over the buttons (`Move_Options_Background_`,
cmbtdrw1.cpp:1463-1544); while it is up the battle's buttons are gone from
the list and the panel holds: its title — the same button, now at (298, 301)
with ESC — SELF DESTRUCT (283, 348; its confirmation is the game's box,
combat1.cpp:509-546), and five lights, each a hidden field over its row
(combat1.cpp:160-164): MISSILE WARNING, FAST ANIMATIONS, SHOW LEGAL MOVES,
SHOW SHIELD ARCS, DISPLAY GRID. HD shows the panel while COPT says it is up,
each light as COPT holds it, and every click is the original's own field —
HD keeps no option of its own. The words are the panel picture's.

TRANSCRIPTION `option_drawing` — WHAT THE OPTIONS DRAW, over the field:
DISPLAY GRID, a line every 20 px both ways in colour 4 (cmbtdrw1.cpp:
528-535, 1813-1820); SHOW SHIELD ARCS, the acting unit's four arc borders
in colour 0x54 from its centre and the arcs' letters in font 0, colour
0x81 — F R B L; A D I S only in the Italian game (language 4,
cmbtdrw1.cpp:27; the German game, language 1, keeps F R B L) — at the
size's distance
(`Draw_Shield_Arcs_`, cmbtdrw1.cpp:21-152); SHOW LEGAL MOVES, the legal
cells (`cbdraw.draw_legal`). FAST ANIMATIONS sets the playback's steps
(`cbplay`). MISSILE WARNING changes what a move does in the engine; the
original shows its warning picture in the reduced map's place, which HD
does not (`cbmap`'s OMISSION `missile_warning_picture`).

DEVIATION `hud_panel` (the panel's): the panel is HUD blocks over the
buttons, not COMBAT.LBX 9 sliding up; the lights are HUD checkboxes.
"""
import time

import pygame

from core import combatoptions
from core.hud import blocks as hud
from core.hud import text as hudtext
from core.structs import settings as settings_struct

OPEN_KEY = ord("O")
ESC = 27
TITLE = (298, 301)               # the info button while the panel is up
SELF_DESTRUCT = (283, 348)
#: the five hidden fields (combat1.cpp:160-164), the lights' order
LIGHTS = ((264, 383, 407, 396), (264, 399, 407, 412), (264, 415, 407, 428),
          (264, 431, 407, 444), (264, 447, 407, 460))
WORDS = ("MISSILE WARNING", "FAST ANIMATIONS", "SHOW LEGAL MOVES",
         "SHOW SHIELD ARCS", "DISPLAY GRID")
#: COMBAT.LBX 9 is 170 x 180 at (248, 298); its parts relative to it
PANEL = (170, 180)
GRID_INDEX, ARC_INDEX, LETTER_INDEX = 4, 0x54, 0x81
ARC_RADIUS = {0: 15, 1: 22, 2: 25, 3: 30, 4: 33, 5: 33}
LETTERS = {"en": "FRBL", "it": "ADIS"}        # language 4 is Italian
WAIT = 1.0                       # s: a light whose change never arrives


def options(state):
    """COPT of the battle on the wire, or None."""
    o = getattr(state, "combat_options", None)
    c = getattr(state, "combat", None)
    return o if o is not None and c is not None and \
        o["serial"] == c["serial"] else None


def flag(state, name):
    """An option as the battle holds it; without COPT the settings record
    (legal moves only, as before open fix 68) or off."""
    o = options(state)
    if o is not None:
        return o[name]
    if name != "legal_moves":
        return False
    raw = getattr(state, "settings_raw", b"") or b""
    return len(raw) >= settings_struct.SIZE and \
        settings_struct.SPEC.parse(raw).combat_legal_moves_flag == 1


def _field(fields, at=None, rect=None):
    for f in fields or []:
        if not f.index:
            continue
        if rect is not None and (f.x, f.y, f.x_end, f.y_end) == rect:
            return f
        if at is not None and (f.x, f.y) == at and f.field_type == 0:
            return f
    return None


class Options:
    def __init__(self):
        self.rects = {}
        self._pending = None             # (key, flags before, time)

    def up(self, state):
        o = options(state)
        return o is not None and o["panel_up"]

    @staticmethod
    def box(band, buttons):
        """The panel over the buttons (`buttons`, the panel's button block),
        standing up out of the band as the original's 180 rows stand over
        its 129-row panel."""
        h = int(band.h * PANEL[1] / 129)
        r = pygame.Rect(0, 0, buttons.w + buttons.w // 12, h)
        r.midbottom = (buttons.centerx, band.bottom - 4)
        return r

    def draw(self, surface, style, scale, state, band, buttons):
        self.rects = {}
        if not self.up(state) or buttons is None:
            return
        o = options(state)
        box = self.box(band, buttons)
        hud.panel(surface, box, scale)
        k = box.h / PANEL[1]
        pad = int(10 * k)
        row = lambda y, h: pygame.Rect(box.x + pad, box.y + int(y * k),
                                       box.w - 2 * pad, int(h * k))
        self.rects["title"] = row(3, 19).inflate(-box.w // 4, 0)
        self.rects["self_destruct"] = row(50, 20).inflate(-box.w // 8, 0)
        # the picture's words stand 7-8 rows tall (COMBAT.LBX 3, 9, 10),
        # the buttons' as the rows'
        size = max(9, int(round(8 * k / hudtext.cap_ratio(style))))
        for key, word, look in (("title", "OPTIONS", "active"),
                                ("self_destruct", "SELF DESTRUCT", "normal")):
            hud.small_button(surface, self.rects[key], scale, look)
            hudtext.blit(surface, style.render_text(
                word, size, hudtext.colour("button")), self.rects[key])
        for i, (name, word) in enumerate(zip(combatoptions.FLAGS, WORDS)):
            r = row(85 + 16 * i, 14)
            light = pygame.Rect(r.x, r.y, r.h, r.h)
            hud.checkbox(surface, light, scale, o[name])
            hudtext.blit(surface, style.render_text(
                word, size, hudtext.colour("button")),
                pygame.Rect(light.right + pad, r.y, r.right - light.right
                            - pad, r.h), align="left")
            self.rects[name] = r

    def click(self, x, y, state, client):
        """True when the panel took the click."""
        if not self.up(state):
            return False
        key = next((k for k, r in self.rects.items() if r.collidepoint(x, y)),
                   None)
        fields = getattr(state, "fields", None)
        o = options(state)
        if self._pending and (time.monotonic() - self._pending[2] > WAIT or
                              o[self._pending[0]] != self._pending[1]):
            self._pending = None
        if key is None or self._pending:
            return True
        if key == "title":
            f = _field(fields, at=TITLE)
        elif key == "self_destruct":
            f = _field(fields, at=SELF_DESTRUCT)
        else:
            f = _field(fields, rect=LIGHTS[combatoptions.FLAGS.index(key)])
            if f is not None:
                self._pending = (key, o[key], time.monotonic())
        if f is not None:
            client.activate_field(f.index)
        return True

    def key(self, key, state, client):
        """ESC closes the panel through its own hotkey."""
        if not self.up(state) or key != pygame.K_ESCAPE:
            return False
        f = next((f for f in getattr(state, "fields", None) or []
                  if f.index and f.hotkey == ESC), None)
        if f is not None:
            client.activate_field(f.index)
        return True


# ── what the options draw ─────────────────────────────────────────────
def draw_grid(surface, cam, art):
    """DISPLAY GRID: a line on every cell border, colour 4."""
    col = art.palette_with().get(GRID_INDEX, (0, 0, 120))
    x0, y0, w, h = cam.area
    left, top = cam.to_world(x0, y0)
    right, bottom = cam.to_world(x0 + w, y0 + h)
    step = 20
    lw = max(1, round(cam.scale))         # one native pixel, scaled
    for gx in range(int(left // step) * step, int(right) + step, step):
        x = int(cam.to_window(gx, 0)[0])
        pygame.draw.line(surface, col, (x, y0), (x, y0 + h - 1), lw)
    for gy in range(int(top // step) * step, int(bottom) + step, step):
        y = int(cam.to_window(0, gy)[1])
        pygame.draw.line(surface, col, (x0, y), (x0 + w - 1, y), lw)


#: Draw_Shield_Arcs_' borders by facing % 4 (far points, native px), and
#: its letter offsets (as fractions of the size's distance)
_FAR = {0: ((2000, 2000), (-2000, -2000), (2000, -2000), (-2000, 2000)),
        1: ((3827, -9239), (-9239, -3827), (-3827, 9239), (9239, 3827)),
        2: ((0, 2000), (-2000, 0), (0, -2000), (2000, 0)),
        3: ((9239, -3827), (-3827, -9239), (-9239, 3827), (3827, 9239))}


def _offsets(facing, sz):
    """The four letters' (dx, dy), indexed from the facing's quarter."""
    q = facing % 4
    v23, v19 = sz * 23 // 25, sz * 19 // 50
    base = {0: ((sz, 0), (0, sz), (-sz, 0), (0, -sz)),
            1: ((v23, -v19), (v19, v23), (-v23, v19), (-v19, -v23)),
            2: ((sz, -sz), (sz, sz), (-sz, sz), (-sz, -sz)),
            3: ((v19, -v23), (v23, v19), (-v19, v23), (-v23, -v19))}[q]
    i0 = (facing // 4) % 4
    out = [None] * 4
    for j in range(4):
        out[(i0 + j) % 4] = base[j]
    return out


def draw_shield_arcs(surface, cam, art, unit, centre, style, language="en"):
    """SHOW SHIELD ARCS (`Draw_Shield_Arcs_`): the acting unit only, not the
    planet (cmbtdrw1.cpp:22-24)."""
    pal = art.palette_with()
    line_col = pal.get(ARC_INDEX, (90, 90, 90))
    text_col = pal.get(LETTER_INDEX, (60, 200, 60))
    facing = int(unit["facing_dir"]) & 15
    sz = ARC_RADIUS.get(int(unit["size_class"]), 22)
    cx, cy = centre
    start = cam.to_window(cx, cy)
    letters = LETTERS.get(language, LETTERS["en"])
    px = max(8, int(round(7 * cam.scale)))       # font 0: about 7 px a line
    for i, ((fx, fy), (dx, dy)) in enumerate(zip(_FAR[facing % 4],
                                                 _offsets(facing, sz))):
        pygame.draw.line(surface, line_col, start,
                         cam.to_window(cx + fx, cy + fy),
                         max(1, round(cam.scale)))
        img = style.render_text(letters[i], px, text_col)
        surface.blit(img, cam.to_window(cx + dx - 2, cy + dy - 3))
