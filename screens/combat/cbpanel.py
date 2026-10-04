"""The acting unit's panel — work orders 197 C, 199 C3.

WHAT THE ORIGINAL SHOWS in its bottom panel (COMBAT.LBX 0 at (0, 351),
cmbtdrw1.cpp:446-448, `dev:doc/combat_drawing_reading.md` §6): the acting
unit's name (:517-521), its picture with the shield rings (:2057-2344), its
weapons — or, by the WEAPONS / SPECIALS toggle, its special systems
(:543-591) — its systems box (drive, shields, computer, structure, armour,
speed and "Remaining", :360-425), and the buttons AUTO, SCAN, BOARD,
RETREAT, WAIT, DONE (:1268-1305) and OPTIONS under them (combat1.cpp:178,
the panel itself is `cbopts`, work order 200). SCAN and BOARD are modes HD
holds itself until a unit is clicked (`cbpopups`, work order 199).

TRANSCRIPTION `weapon_rows` (199 C3): each weapon row as
`Draw_Weapon_Status_Display_` writes it (:2765-2933) — the shots left (the
mount count when none are left and its status is 1), "Heavy " or "PD "
from the modifications' plurals, the weapon's name for one shot and its
plural otherwise, then by its type: " x<ammo>" for missiles, bombs,
fighters and the anti-missile rocket, " <n>t" for a torpedo recharging
(KENTEXT 85, the "t" read off the player's file and written here), and the
arc word in brackets for a beam (KENTEXT 3-6, "360" a literal, :2898-2921);
an exhausted row dims (:2840-2846). The special systems list names every
system the unit carries, a damaged one dimmed (:543-591).

DEVIATION `hud_panel`: HD draws all of it as HUD blocks along the bottom
of the window, in OrionLayer's words where the original uses its own
pictures and labels, not COMBAT.LBX 0. The reduced map sits at the right
end as the original's (`cbmap`, work order 209 B1). DEVIATION
`shield_rings`: the shields round the unit's picture are HD's rings, one
per ten points left in each of the four arcs (front, right, back, left
as `Facing_Shield_` counts them, cmbtfire.cpp:226-237), not the original's
COMBAT.LBX ring masks.
TRANSCRIPTION `weapon_switch` (work order 200): each weapon row IS the
original's own switch — a hidden field over the row (combat1.cpp:180-183)
that cycles the slot's `active` 1 -> 0 -> -1 -> 1 (:594-613): 1 fires on
the next FIRE, 0 sits out that one shot (the fire puts it back to 1), -1
is off for good — and only -1 keeps a weapon out of the defensive fire at
an enemy moving past (`Defensive_Fire_Check_`, cmbtfir2.cpp:868-930).
HD clicks that field, the next only once the last one's change is on the
wire, and shows each row as the battle holds it (`row_colours` below);
FIRE sends the rows that are at 1 (open fix 58), one command per shot
(decision 47). Work order 199 had kept the switch in HD alone, so a weapon
could not be taken out of the defensive fire.
TRANSCRIPTION `row_colours` (work order 209 B2, Data's decision 2; the
blue bars of work order 203 are gone): every row's count and words in the
colour `Draw_Weapon_Status_Display_` picks (cmbtdrw1.cpp:2765-2846), from
the battle palette (FONTS.LBX 4) — `row_mode`:
  green 0x53   switched on (`active` 1); and every row of a unit the
               computer controls (`Ship_Controlled_By_Computer_`,
               combat1.cpp:217-227)
  bright 0x56  switched on and able to hit the unit or missile under the
               pointer — arc, range, legality (:2789-2823; HD reads the
               engine's verdict, CTGT, open fix 54)
  yellow 0xDC  switched off for the next shot (`active` 0) — or unable to
               fire: no ammunition, a torpedo recharging, no shots left
               (:2829-2835), whatever its switch
  red 0x4A     switched off (`active` -1); exhaustion does not change it
The SPECIALS tab (`Draw_Special_Status_Display_`, :543-589): a damaged
system red 0x4A, a working one green 0x53 while its `weapon_ready_flags`
entry is 1, else yellow 0xDC — nothing in the engine ever clears that
flag (combinit.cpp:99, 329, 1372, 2066 set it to 1), so yellow is not
reached there.
"""
import math
import time

import pygame

from core import lang
from core.hud import blocks as hud
from core.hud import style as hudstyle
from core.hud import text as hudtext
from . import cbart, cbmap

TABS = (("weapons", "WEAPONS"), ("specials", "SPECIALS"))
BUTTONS = (("auto", "AUTO", ord("A")), ("scan", "SCAN", ord("S")),
           ("board", "BOARD", ord("B")), ("retreat", "RETREAT", ord("R")),
           ("wait", "WAIT", ord("W")), ("done", "DONE", ord("D")),
           ("options", "OPTIONS", ord("O")))
#: `TECHDATA::_weapons[i].type` (techdata.cpp:481-527, the struct's last
#: field): 0 beam, 1 missile, 2 torpedo, 3 bomb, 4 fighter, 5 special.
WEAPON_TYPE = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 1, 1, 1, 1, 2, 2, 2,
               3, 3, 3, 3, 3, 3, 0, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 2, 0,
               0, 0, 5, 5)
ANTI_MISSILE = 33
ALL_SECTORS = 0x0F
HEAVY, POINT_DEFENSE = 0x02, 0x04
#: WEAPON_MOD_HEAVY_MOUNT / _POINT_DEFENSE (orion2_consts.h) in the
#: modification tables
MOD_HEAVY, MOD_PD = 1, 2
TURNS = "t"                       # KENTEXT 85 (English)
ROW_WAIT = 3.0                    # s: a switch whose change never arrives
#: `row_mode` -> the font's body colour (`s_colors` entry 1 — a glyph pixel
#: n takes entry n - 1, fonts.cpp:62, and entry 0 is the edge) in the
#: battle palette, FONTS.LBX entry 4 (cmbtdrw1.cpp:2766-2769).
ON, IN_REACH, PAUSED, OFF = 0, 1, 2, 3
ROW_COLOUR = {ON: (56, 132, 40),          # 0x53
              IN_REACH: (108, 220, 76),   # 0x56
              PAUSED: (212, 208, 44),     # 0xDC
              OFF: (148, 0, 0)}           # 0x4A
#: The weapon list's columns (`row_columns`): the count's right edge and the
#: name's left edge in the original's list, 114..263 (cmbtdrw1.cpp:2775,
#: :2858, :2929), as fractions of its width.
COUNT_RIGHT = (127 - 114) / (263 - 114)
NAME_LEFT = (131 - 114) / (263 - 114)


def row_field(fields, k):
    """The original's hidden field over weapon row `k` (combat1.cpp:180-183:
    (120, y - 10) to (255, y), y = 389 + 11 k)."""
    rect = (120, 389 + 11 * k - 10, 255, 389 + 11 * k)
    return next((f for f in fields or [] if f.index and
                 (f.x, f.y, f.x_end, f.y_end) == rect), None)


def row_mode(active, exhausted, computer=False, hover_bit=None):
    """The original's `display_color_mode` for one weapon row
    (cmbtdrw1.cpp:2784-2835). `hover_bit` is None with no unit or missile
    under the pointer, else whether this slot can hit it."""
    if computer:
        mode = ON
    elif active != 1:
        mode = PAUSED if active == 0 else OFF
    else:
        mode = IN_REACH if hover_bit else ON
    if mode != OFF and exhausted:
        mode = PAUSED
    return mode


def special_mode(ready, damaged):
    """`Draw_Special_Status_Display_`'s colour (cmbtdrw1.cpp:562-570)."""
    return OFF if damaged else ON if ready == 1 else PAUSED


def on_mask(unit):
    """The rows that fire on the next FIRE: `active` 1 (`Weapon_Is_On_`,
    cmbtdrw1.cpp:2592-2594)."""
    return sum(1 << k for k, w in enumerate(unit["weapons"])
               if w["count"] > 0 and w["active"] == 1)


def weapon_row(w, names, ken):
    """(count, label, exhausted) of one weapon slot (cmbtdrw1.cpp:2829-2930)."""
    wid = int(w["weapon_id"])
    kind = WEAPON_TYPE[wid] if 0 <= wid < len(WEAPON_TYPE) else 0
    shots, ammo = w["shots_left"], w["ammo"]
    count = w["count"] if shots == 0 and w["status"] == 1 else shots
    label = ""
    if w["specials"] & HEAVY:
        label = (names.name("weapon_mod_plurals", MOD_HEAVY) or "Heavy") + " "
    elif w["specials"] & POINT_DEFENSE:
        label = (names.name("weapon_mod_plurals", MOD_PD) or "PD") + " "
    single = names.name("weapons", wid) or f"weapon {wid}"
    label += single if shots == 1 else \
        (names.name("weapon_plurals", wid) or single)
    if kind in (1, 3, 4) or wid == ANTI_MISSILE:
        label += f" x{ammo}"
    elif kind == 2:
        if ammo > 0:
            label += f" {ammo}{TURNS}"
    elif kind == 0:
        arc = int(w["arc"])
        # the panel's own switch (:2902-2924): ALL_SECTORS is 0x0F
        # (orion2_consts.h:1084) — work order 199 had 0x10, which is the
        # designer's `Weapon_Arc_String_` test, not this one
        word = "360" if arc == ALL_SECTORS else \
            (ken.arc(arc) if ken is not None and arc in (1, 2, 4, 8) else "")
        label += f" ({word or ''})"
    exhausted = (kind in (1, 3, 4) and ammo == 0) or \
        (kind == 2 and ammo > 0) or (shots == 0 and w["status"] != 1)
    return count, label, exhausted


def special_bits(flags):
    """The special systems set in a 5-byte field (`Test_Bit_Field_`)."""
    return [b for b in range(40) if flags[b >> 3] >> (b & 7) & 1]


#: `SPECIAL_REGENERATION` (orion2_consts.h:578), the last special bit.
REGENERATION = 39


def listed_specials(flags):
    """The systems the SPECIALS tab lists: TRANSCRIPTION `specials_list`
    (work order 213) — `Draw_Special_Status_Display_` walks the bits below
    `SPECIAL_REGENERATION` unless `COMBINIT::_amoeba_regeneration` is set
    (cmbtdrw1.cpp:557-558), and nothing in the engine sets it (combinit.h:11
    is its only assignment), so Regeneration is never listed."""
    return [b for b in special_bits(flags) if b < REGENERATION]


def draw_shields(surface, rect, unit, picture):
    """The unit's picture with HD's shield rings (DEVIATION `shield_rings`):
    four arcs round it, one ring per ten points left in each."""
    cx, cy = rect.center
    if picture is not None:
        k = min(rect.w, rect.h) * 0.62 / max(cbart.native_size(picture))
        size = (max(1, int(picture.get_width() * k / cbart.hd_factor(picture))),
                max(1, int(picture.get_height() * k / cbart.hd_factor(picture))))
        # a painted picture at k times the drawing shrinks smoothly; the
        # game's drawings keep their pixels (HD EXTENSION `hd_painted`)
        img = (pygame.transform.smoothscale if cbart.hd_factor(picture) > 1
               and size[0] < picture.get_width() else
               pygame.transform.scale)(picture, size)
        surface.blit(img, img.get_rect(center=(cx, cy)))
    face = (int(unit["facing_dir"]) & 15) * 22.5
    base = min(rect.w, rect.h) * 0.36
    gap = max(2, int(base * 0.06))
    for arc, centre in enumerate((0, -90, 180, 90)):    # front right back left
        rings = min(8, (max(0, unit["shield_arc_current"][arc]) + 9) // 10)
        a0 = math.radians(face + centre - 40)
        a1 = math.radians(face + centre + 40)
        for r in range(rings):
            rad = base + r * gap
            box = pygame.Rect(0, 0, int(2 * rad), int(2 * rad))
            box.center = (cx, cy)
            pygame.draw.arc(surface, (40, 200, 90), box, a0, a1, 2)


class Panel:
    def __init__(self):
        self.all_buttons, self.help_rows = {}, []
        self.left = self.mid = self.facts = None
        self.map = None           # the reduced map's rect (`cbmap`)
        self.rects = {}           # button key -> window rect
        self.rows = []            # (window rect, slot) of the weapon rows
        self.tabs = {}            # "weapons" / "specials" -> window rect
        self.buttons = None       # the button block (the OPTIONS panel's place)
        self._row_wait = None     # (row, active before, time) after a switch

    def switch(self, row, state, client):
        """A click on weapon row `row`: the original's own field, once the
        last switch's change is on the wire. True when it was sent."""
        live = state.combat["units"][state.combat["cur_ship"]]
        w = self._row_wait
        if w and (live["weapons"][w[0]]["active"] != w[1] or
                  time.monotonic() - w[2] > ROW_WAIT):
            self._row_wait = w = None
        f = row_field(getattr(state, "fields", None), row)
        if w is not None or f is None:
            return False
        client.activate_field(f.index)
        self._row_wait = (row, live["weapons"][row]["active"],
                          time.monotonic())
        return True

    @staticmethod
    def area(win_w, win_h):
        """The panel's band: the original's 129 of 480 rows, at the bottom."""
        h = int(win_h * 129 / 480 * 0.75)
        return pygame.Rect(0, win_h - h, win_w, h)

    def draw(self, surface, style, unit, names, ken, actives, board_mode, live,
             scale, picture=None, specials=False, computer=False, hover=None):
        """`hover` is the CTGT mask of the unit or missile under the pointer
        (bit k: slot k can hit it), None when the pointer is over neither;
        `computer` whether the acting unit is the computer's."""
        band = self.area(*surface.get_size())
        hud.panel(surface, band.inflate(-8, -8), scale, dense=True)
        pad = int(16 * scale)
        inner = band.inflate(-2 * pad, -2 * pad)
        size = max(10, int(22 * scale))
        small = max(9, int(18 * scale))
        self.rects, self.rows, self.tabs = {}, [], {}
        self.all_buttons, self.help_rows = {}, []     # `cbhelp`'s
        self.left = self.mid = self.facts = self.map = None
        if unit is None:
            return
        # the name, the systems and the picture with its shields (left)
        left = pygame.Rect(inner.x, inner.y, int(inner.w * 0.30), inner.h)
        hudtext.blit(surface, style.render_text(unit["name"], size,
                                                hudtext.colour("value")[:3]),
                     pygame.Rect(left.x, left.y, left.w, size + 4),
                     align="left")
        facts = (("Structure", unit["structure_max"] - unit["structure_damage"],
                  unit["structure_max"]),
                 ("Armor", unit["armor_remaining"], None),
                 # TRANSCRIPTION (work order 208 A3): the SHIELD SYSTEM's
                 # hits, as `Draw_Internals_Display_` prints them
                 # (cmbtdrw1.cpp:387-395) — "No Shields" for shield_type 0
                 # — not the arcs' strength, which the rings show.
                 (("Shields", unit["shield_current_hits"],
                   unit["shield_max_hits"]) if unit["shield_type"] else
                  ("No Shields", "", None)),
                 ("Drive", unit["drive_current_hits"], unit["drive_max_hits"]),
                 ("Computer", unit["computer_current_hits"],
                  unit["computer_max_hits"]),
                 ("Remaining", unit["movement_left"], unit["current_speed"]))
        y = left.y + size + 8
        for label, value, top in facts:
            text = (f"{lang.tr(label)}  {value}" + (f" / {top}" if top else
                                                     "")).rstrip()
            hudtext.blit(surface, style.render_text(
                text, small, hudtext.colour("label")[:3]),
                pygame.Rect(left.x, y, left.w // 2, small + 2), align="left")
            y += small + 3
        draw_shields(surface, pygame.Rect(left.centerx, left.y, left.w // 2,
                                          left.h), unit, picture)
        # the reduced map at the right end, as the original's (work order
        # 209 B1, `cbmap`); the room is taken from the weapons column, so the
        # buttons keep their size and move left by the map's width
        self.map = cbmap.rect_for(inner)
        # the weapons — or the special systems — (middle): the toggle above
        mid = pygame.Rect(left.right + pad, inner.y,
                          int(inner.w * 0.40) - self.map.w - pad, inner.h)
        self.left, self.mid = left, mid
        self.facts = pygame.Rect(left.x, left.y, left.w // 2, left.h)
        right = pygame.Rect(mid.right + pad, inner.y,
                            self.map.x - mid.right - 2 * pad, inner.h)
        rows = (len(BUTTONS) + 1) // 2
        bw = (right.w - pad) // 2
        bh = max(small + 8, (right.h - (rows - 1) * (pad // 2)) // rows)
        # TRANSCRIPTION `tab_words` (work order 200): the original's WEAPONS
        # and SPECIALS pictures (COMBAT.LBX 7 and 8, combinit.cpp:688, :697)
        # carry their word at the same 7-row cap height as the AUTO ... DONE
        # pictures (COMBAT.LBX 0x32-0x36) — 7 of a 14-row picture against 7
        # of a 20-row one. So HD draws the two words at the size it gives the
        # buttons' words, in a tab twice the word's cap tall as the picture
        # is; sized by the tab's own height they came out half as tall
        # (199 C3's open item).
        word_px = hudtext.size_for(style, "button", bh)
        cap = word_px * hudtext.cap_ratio(style)
        tab_h = max(small + 6, int(math.ceil(2 * cap)))
        for n, (key, word) in enumerate(TABS):
            r = pygame.Rect(mid.x + n * (mid.w // 2), mid.y, mid.w // 2 - 4,
                            tab_h)
            hud.small_button(surface, r, scale, "active" if
                             (key == "specials") == bool(specials) else
                             "normal")
            hudtext.blit(surface, style.render_text(
                word, word_px, hudtext.colour("button")), r)
            self.tabs[key] = r
        body = pygame.Rect(mid.x, mid.y + tab_h + 4, mid.w,
                           mid.h - tab_h - 4)
        row_h = max(small + 2, body.h // 8)
        if specials:
            have = listed_specials(unit.get("special_device_flags")
                                   or [0] * 5)
            damaged = set(special_bits(unit.get("special_device_damage_flags")
                                       or [0] * 5))
            ready = list(unit.get("weapon_ready_flags") or [1] * 8)
            # TRANSCRIPTION `specials_list` (work order 213): no cap — the
            # original prints row after row 11 px apart from y 0x17C
            # (cmbtdrw1.cpp:557-582), so a ninth runs on past its 88 px
            # list as here past the list's eight rows
            for k, bit in enumerate(have):
                r = pygame.Rect(body.x, body.y + k * row_h, body.w, row_h - 2)
                word = names.name("specials", bit) or f"special {bit}"
                self.help_rows.append((r, k))
                # the k-th system shown reads ready flag k (`Special_Is_On_
                # (ship, visible_special_count)`, cmbtdrw1.cpp:566)
                hudtext.blit(surface, style.render_text(
                    word, small, ROW_COLOUR[special_mode(
                        ready[k] if k < len(ready) else 0, bit in damaged)]),
                    r.inflate(-pad, 0), align="left")
            if not have:
                hudtext.blit(surface, style.render_text(
                    "No special systems", small, hudtext.colour("label")[:3]),
                    body, align="center")
        else:
            for k, wpn in enumerate(unit["weapons"]):
                if wpn["count"] <= 0 or wpn["weapon_id"] <= 0:
                    continue
                r = pygame.Rect(body.x, body.y + k * row_h, body.w, row_h - 2)
                state = actives[k] if k < len(actives) else 1
                count, label, exhausted = weapon_row(wpn, names, ken)
                # the row's frame says only that it is a switch (the
                # original's hidden field has no picture); its state is the
                # colour of its words, `row_colours`
                hud.small_button(surface, r, scale, "normal")
                mode = row_mode(state, exhausted, computer, None if hover
                                is None else bool(hover >> k & 1))
                # TRANSCRIPTION `row_columns` (work order 210 B4): the count
                # right-aligned at x 127 and the name from x 131 of the list's
                # 114..263 (`Print_Integer_Right_(127, …)`, `Print_(131, …)`,
                # cmbtdrw1.cpp:2858, :2929): as fractions of the row, so the
                # count stands clear of the row's frame at every size
                col = r.x + int(r.w * COUNT_RIGHT)
                name_x = r.x + int(r.w * NAME_LEFT)
                hudtext.blit(surface, style.render_text(
                    str(count), small, ROW_COLOUR[mode]),
                    pygame.Rect(r.x, r.y, col - r.x, r.h), align="right")
                hudtext.blit(surface, style.render_text(
                    label, small, ROW_COLOUR[mode]),
                    pygame.Rect(name_x, r.y, r.right - pad // 2 - name_x,
                                r.h), align="left")
                self.rows.append((r, k))
                self.help_rows.append((r, k))
        # the buttons (right), each only while the live list carries it
        self.buttons = right
        for n, (key, word, hotkey) in enumerate(BUTTONS):
            r = pygame.Rect(right.x + (n % 2) * (bw + pad),
                            right.y + (n // 2) * (bh + pad // 2), bw, bh)
            if n == len(BUTTONS) - 1 and n % 2 == 0:    # OPTIONS, centred
                r.x = right.x + (right.w - bw) // 2
            state = "active" if board_mode == {"board": True,
                                               "scan": "scan"}.get(key) else \
                "normal" if key in live else "disabled"
            hud.small_button(surface, r, scale, state, word,
                             style_renderer=style)
            self.all_buttons[key] = r
            if key in live:
                self.rects[key] = r
        return band

    def button_at(self, x, y):
        return next((k for k, r in self.rects.items()
                     if r.collidepoint(x, y)), None)

    def row_at(self, x, y):
        return next((k for r, k in self.rows if r.collidepoint(x, y)), None)

    def tab_at(self, x, y):
        return next((k for k, r in self.tabs.items()
                     if r.collidepoint(x, y)), None)
