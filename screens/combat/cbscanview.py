"""The ship scan's window — work order 290 (`cbscan` says what it shows).

DEVIATION `scan_view`: a HUD window in the shell's look over the dimmed
battle (decision 71), laid out as Data's sketch and mockup of 17 October
2026 — ship, officer, crew on the left; the shields round the unit's own
picture and the combat values in the middle; hull and systems, the special
systems on the right; the weapons across the foot — not COMBAT.LBX 5 with
the game's own lines (cmbtdrw1.cpp:3223-4007). No weapon or special icons
(Data: the game has none).

HD EXTENSION `scan_modes`: NORMAL shows what the original's scan shows;
DETAILED, the default (Data), adds the four arcs, the weapons' and the
special systems' hits, a weapon's original count and the crew's experience.
The choice is the player's setting `scan_view` (`core.usersettings`).
INVENTION `scan_turn`: the battle's turn (CMBT `turn` + 1) in the head —
the original shows it nowhere.

Geometry in 1920 x 1080 reference pixels, scaled by the window's `k` as
the battle's other popups (`cbpopups._k`); nothing is held across frames
but the click rects of the frame drawn last.
"""
import math

import pygame

from core.hud import blocks as hud
from core.hud import text as hudtext
from . import cbart, cbscan

#: The window and its boxes, reference px (the sketch's).
WINDOW = (60, 30, 1800, 1020)
BOXES = {
    "ship": (80, 114, 520, 220), "officer": (80, 348, 520, 250),
    "crew": (80, 612, 520, 150),
    "shields": (614, 114, 600, 420), "values": (614, 548, 600, 214),
    "hull": (1228, 114, 612, 230), "specials": (1228, 358, 612, 404),
    "weapons": (80, 774, 1760, 206),
}
TITLES = {"ship": "SHIP", "officer": "OFFICER", "crew": "CREW",
          "shields": "SHIELDS", "values": "COMBAT VALUES",
          "hull": "HULL AND SYSTEMS", "specials": "SPECIAL SYSTEMS",
          "weapons": "WEAPONS"}
#: HD EXTENSION `scan_states`: a part's state by colour — operational,
#: damaged, destroyed (the original colours only a destroyed special).
STATE_RGB = {cbscan.OK: (80, 210, 110), cbscan.DAMAGED: (240, 170, 60),
             cbscan.DESTROYED: (230, 70, 60)}
DETAIL_TAG = (200, 120, 255)
BAR_BACK = (40, 46, 60)
#: The facing at which a unit's nose points up the screen (`cbart.
#: stored_facing`: 0 is nose right, the quarter turn is 4 or 12).
NOSE_UP = 12
#: The weapons table's columns, reference px from the box's left.
WEAPON_COLUMNS = (("#", 176), ("Weapon", 210), ("Count", 560),
                  ("Arc", 700), ("Ammo", 820), ("Mods", 950),
                  ("HP", 1260), ("State", 1560))


def k_of(surface):
    w, h = surface.get_size()
    return min(w / 1920, h / 1080)


class View:
    def __init__(self):
        self.rects = {}

    def draw(self, surface, style, scale, model, detailed, turn, pics):
        """One frame of the scan of `model` (`cbscan.Model`); `pics` hands
        in the pictures (`ship`, `upright`, `portrait`, `skill_icon`)."""
        self.rects = {}
        k = k_of(surface)
        w, h = surface.get_size()
        ox = (w - WINDOW[2] * k) / 2 - WINDOW[0] * k
        oy = (h - WINDOW[3] * k) / 2 - WINDOW[1] * k

        def R(x, y, rw, rh):
            return pygame.Rect(round(ox + x * k), round(oy + y * k),
                               round(rw * k), round(rh * k))

        def px(n):
            return max(9, int(n * k))

        def text(t, at, size, rgb, anchor="topleft"):
            img = style.render_text(str(t), px(size), rgb[:3])
            r = img.get_rect(**{anchor: at})
            surface.blit(img, r)
            return r

        label, value = hudtext.colour("label"), hudtext.colour("value")
        head = hudtext.colour("sub")
        hud.popup(surface, R(*WINDOW), scale)
        text("SHIP SCAN", R(960, 40, 0, 0).topleft, 40, value, "midtop")
        for n, (key, word) in enumerate((("normal", "Normal"),
                                         ("detailed", "Detailed"))):
            r = R(80 + n * 140, 44, 130, 40)
            on = detailed == (key == "detailed")
            hud.small_button(surface, r, scale, "active" if on else "normal",
                             word, style_renderer=style)
            self.rects[key] = r
        if turn is not None:
            text(f"Combat turn  {turn}", R(1790, 52, 0, 0).topleft, 28,
                 value, "topright")
        x = R(1804, 44, 40, 40)
        hud.small_button(surface, x, scale, "normal", "X",
                         style_renderer=style)
        self.rects["close_x"] = x
        for key, box in BOXES.items():
            r = R(*box)
            hud.panel(surface, r, scale, dense=True)
            text(TITLES[key], (r.x + px(14), r.y + px(8)), 24, head)

        def tag(at):
            """The lilac D: a value shown only in the Detailed mode."""
            img = style.render_text("D", px(16), (12, 12, 12))
            r = img.get_rect(midleft=at).inflate(px(8), px(2))
            # LOOK EXCEPTION marking: the Detailed mode's D (work order 290)
            pygame.draw.rect(surface, DETAIL_TAG, r, border_radius=px(3))
            surface.blit(img, img.get_rect(center=r.center))

        def row(r, y, lab, val, rgb=value, size=24):
            text(lab, (r.x + px(16), y), size, label)
            text(val, (r.right - px(16), y), size, rgb, "topright")

        def bar(r, frac, rgb):
            # LOOK EXCEPTION data: a part's hits as a bar (work order 290)
            pygame.draw.rect(surface, BAR_BACK, r)
            if frac > 0:
                # LOOK EXCEPTION data: the hits left, in the part's state colour
                pygame.draw.rect(surface, rgb, (r.x, r.y, int(r.w * min(1, frac)),
                                                r.h))

        def fit(img, box):
            if img is None:
                return None
            # the drawing's own pixels, not its canvas
            img = img.subsurface(img.get_bounding_rect(min_alpha=8)) \
                if img.get_bounding_rect(min_alpha=8).w else img
            iw, ih = img.get_size()
            s = min(box.w / iw, box.h / ih)
            size = (max(1, int(iw * s)), max(1, int(ih * s)))
            how = cbart.smooth if cbart.hd_factor(img) > 1 or s < 1 \
                else pygame.transform.scale
            return how(img, size)

        m = model
        # ── A the ship ─────────────────────────────────────────
        r = R(*BOXES["ship"])
        pic_box = R(BOXES["ship"][0] + 16, BOXES["ship"][1] + 44, 150, 150)
        img = fit(pics.ship, pic_box)
        if img is not None:
            surface.blit(img, img.get_rect(center=pic_box.center))
        y = r.y + px(44)
        tx = r.x + px(184)
        text(m.name, (tx, y), 32, value)
        y += px(42)
        if m.hull:
            text(m.hull, (tx, y), 24, value)
            y += px(32)
        if m.owner_name:
            text(m.owner_name, (tx, y), 24, label)
            y += px(32)
        if m.design_date:
            text(f"Design date {m.design_date}", (tx, y), 22, label)
            y += px(30)
        if m.captured:
            text(m.words["captured"], (tx, y), 24, STATE_RGB[cbscan.DESTROYED])
        # ── B the officer ──────────────────────────────────────
        r = R(*BOXES["officer"])
        o = m.officer
        if o is None:
            text("No officer", (r.x + px(16), r.y + px(48)), 24, label)
        else:
            # the whole figure, as every place draws it (`leaderportraits`)
            port = R(BOXES["officer"][0] + 12, BOXES["officer"][1] + 38,
                     150, 206)
            pic = pics.portrait(o, port.size)
            if pic is not None:
                surface.blit(pic, pic.get_rect(center=port.center))
            else:
                hud.field(surface, port, scale)
            tx = port.right + px(16)
            text(o["name"], (tx, r.y + px(42)), 30, value)
            if o["title"]:
                text(o["title"], (tx, r.y + px(78)), 22, label)
            lw = o["level_word"] or f"Level {o['level']}"
            text(f"{lw}  {m.officer_mark}", (tx, r.y + px(104)), 22, value)
            y = r.y + px(136)
            for sid, name, val in o["skills"][:4]:
                icon = pics.skill_icon(sid, px(22))
                if icon is not None:
                    surface.blit(icon, (tx, y))
                text(name, (tx + px(30), y), 22, label)
                text(val, (r.right - px(16), y), 22, STATE_RGB[cbscan.OK],
                     "topright")
                y += px(26)
            if not o["skills"]:
                text("no skill that acts in battle", (tx, y), 20, label)
        # ── C the crew ─────────────────────────────────────────
        r = R(*BOXES["crew"])
        y = r.y + px(44)
        if m.crew is not None:
            row(r, y, "Crew level", m.crew)
            stars = max(0, min(5, m.crew_quality))
            for n in range(5):
                c = (r.right - px(27 + (4 - n) * 26), y + px(44))
                rgb = (240, 170, 60) if n < stars else (60, 66, 80)
                pts = [(c[0] + px(11) * math.sin(a * math.pi / 5) *
                        (1 if a % 2 == 0 else 0.45),
                        c[1] - px(11) * math.cos(a * math.pi / 5) *
                        (1 if a % 2 == 0 else 0.45)) for a in range(10)]
                # LOOK EXCEPTION data: the crew stars, one a level (cmbtdrw1.cpp:1222-1245)
                pygame.draw.polygon(surface, rgb, pts)
            if detailed and m.experience is not None:
                er = text(f"Experience {m.experience}",
                          (r.x + px(16), y + px(32)), 22, label)
                tag((er.right + px(10), er.centery))
        if m.marines is not None:
            row(r, y + px(68), m.words["marines"], str(m.marines))
        # ── D the shields ──────────────────────────────────────
        r = R(*BOXES["shields"])
        c = (r.centerx, r.y + px(186))
        img = fit(pics.upright, pygame.Rect(0, 0, px(130), px(130)))
        if img is not None:
            surface.blit(img, img.get_rect(center=c))
        most = max(1, m.shield_max)
        rad = px(100)
        box = pygame.Rect(0, 0, 2 * rad, 2 * rad)
        box.center = c
        names = ("Front", "Right", "Rear", "Left")
        # arc centres on the screen, counter-clockwise from right (pygame):
        # front up, right right, rear down, left left
        centres = (90, 0, 270, 180)
        for arc in range(4):
            frac = m.arcs[arc] / most if m.shield_max > 0 else 0
            rgb = STATE_RGB[cbscan.OK] if frac >= 0.75 else \
                STATE_RGB[cbscan.DAMAGED] if frac > 0 else (70, 76, 90)
            a0 = math.radians(centres[arc] - 38)
            a1 = math.radians(centres[arc] + 38)
            pygame.draw.arc(surface, rgb, box, a0, a1, max(3, px(10)))
            if detailed:
                at = {0: (c[0], c[1] - rad - px(54)),
                      2: (c[0], c[1] + rad + px(8)),
                      3: (c[0] - rad - px(78), c[1] - px(24)),
                      1: (c[0] + rad + px(78), c[1] - px(24))}[arc]
                lr = text(names[arc], at, 22, label, "midtop")
                text(f"{m.arcs[arc]} / {m.shield_max}",
                     (lr.centerx, lr.bottom), 24, rgb, "midtop")
        if detailed:
            tag((c[0] + px(64), c[1] - rad - px(42)))
            if m.shield_max > 0:
                text("All arcs share one maximum",
                     (r.right - px(16), r.y + px(14)), 16, label, "topright")
        y = r.bottom - px(68)
        row(r, y, "Weakest arc", m.shield_line, size=22)
        if m.shield_name:
            row(r, y + px(30), "Shield", m.shield_name, size=22)
        # ── E the combat values ────────────────────────────────
        r = R(*BOXES["values"])
        y = r.y + px(44)
        evade = f"{m.evasion}%"
        for lab, val in ((m.words["beam_attack"], cbscan.signed(m.attack)),
                         (m.words["beam_defense"], cbscan.signed(m.defense)),
                         (m.words["missile_evasion"], evade),
                         ("Combat speed", f"{m.speed[0]} / {m.speed[1]}"),
                         (m.words["computer"], m.computer_line)):
            row(r, y, lab, val)
            y += px(32)
        # ── F hull and systems ─────────────────────────────────
        r = R(*BOXES["hull"])
        y = r.y + px(44)
        wd = m.words
        # the part's own name ("Xentronium Armor") stands for the word
        lines = [(wd["structure"], None, m.structure),
                 (m.armour_name or wd["armor"], None, m.armour)]
        if m.drive is not None:
            lines.append((wd["drive"], f"{m.parsecs}{wd['parsecs']}",
                          m.drive))
        lines.append((m.computer_name or wd["computer"], None, m.computer))
        if m.shield_system is not None:
            lines.append((m.shield_name or "Shield", None, m.shield_system))
        for lab, small, pair in lines:
            cur, most = pair
            frac = cur / most if most else 0
            rgb = STATE_RGB[cbscan.OK] if most and cur >= most else \
                STATE_RGB[cbscan.DAMAGED] if cur > 0 else \
                STATE_RGB[cbscan.DESTROYED]
            lr = text(lab, (r.x + px(16), y), 22, label)
            if small:
                text(small, (lr.right + px(10), y + px(3)), 18, value)
            bar(pygame.Rect(r.right - px(270), y + px(4), px(110), px(16)),
                frac, rgb)
            text(f"{cur} / {most}" if most is not None else str(cur),
                 (r.right - px(16), y), 22, value, "topright")
            y += px(34)
        # ── G the special systems ──────────────────────────────
        r = R(*BOXES["specials"])
        rows = m.specials
        if not rows:
            text(m.words["no_specials"], (r.x + px(16), r.y + px(48)), 22,
                 label)
        else:
            head_y = r.y + px(44)
            text("System", (r.x + px(16), head_y), 18, label)
            if detailed:
                text("HP", (r.right - px(170), head_y), 18, label, "topright")
                tag((r.right - px(160), head_y + px(10)))
                text("State", (r.right - px(16), head_y), 18, label,
                     "topright")
            room = r.bottom - px(10) - (head_y + px(28))
            step = max(px(16), min(px(30), room // max(1, len(rows))))
            size = max(14, min(22, int(step / k * 0.75)))
            y = head_y + px(28)
            for _b, name, cur, most, state in rows:
                rgb = STATE_RGB[state] if state != cbscan.OK else value
                text(name, (r.x + px(16), y), size, rgb)
                if detailed:
                    text("—" if most is None else f"{cur} / {most}",
                         (r.right - px(170), y), size, value, "topright")
                    text(state, (r.right - px(16), y), size,
                         STATE_RGB[state], "topright")
                y += step
        # ── W the weapons ──────────────────────────────────────
        r = R(*BOXES["weapons"])
        cols = [(name, x) for name, x in WEAPON_COLUMNS
                if detailed or name not in ("HP", "State")]
        for name, x in cols:
            text(name, (r.x + px(x), r.y + px(10)), 18, label)
        if detailed:
            tag((r.x + px(1300), r.y + px(20)))
        rows = m.weapons
        step = max(px(16), min(px(23), (r.h - px(40)) // max(1, len(rows))))
        size = max(14, min(22, int(step / k * 0.9)))
        y = r.y + px(36)
        for n, wr in enumerate(rows):
            rgb = STATE_RGB[wr["state"]] if wr["state"] != cbscan.OK \
                else value
            count = str(wr["count"]) if not detailed or not wr["lost"] \
                else f"{wr['count']} of {wr['whole']}"
            cells = {"#": str(n + 1), "Weapon": wr["name"], "Count": count,
                     "Arc": wr["arc"], "Ammo": wr["ammo"],
                     "Mods": wr["mods"], "HP": wr["hp"],
                     "State": wr["state"] if wr["state"] != cbscan.DAMAGED
                     or not wr["lost"] else f"{wr['lost']} destroyed"}
            for name, x in cols:
                ink = rgb if name in ("Count", "State") else value
                text(cells[name], (r.x + px(x), y), size, ink)
            y += step
        if not rows:
            text(m.words["none"], (r.x + px(190), r.y + px(40)), 22, label)
        # ── the foot ───────────────────────────────────────────
        cr = R(840, 996, 240, 42)
        hud.small_button(surface, cr, scale, "normal", "CLOSE",
                         style_renderer=style)
        self.rects["close"] = cr
        if detailed:
            tag((R(84, 1016, 0, 0).x, R(84, 1016, 0, 0).y))
            text("= only in Detailed", R(108, 1004, 0, 0).topleft, 18, label)
        x0 = R(320, 1004, 0, 0)
        for n, (state, rgb) in enumerate(STATE_RGB.items()):
            at = (x0.x + px(n * 170), x0.y)
            pygame.draw.circle(surface, rgb, (at[0] + px(6), at[1] + px(11)),
                               px(6))
            text(state, (at[0] + px(22), at[1]), 18, label)


#: The player's setting (`core.usersettings.DEFAULTS["scan_view"]`).
SETTING, DETAILED, NORMAL = "scan_view", "detailed", "normal"


class Pictures:
    """The pictures of one scan: the unit as the battle draws it, the same
    unit nose up for the shields' ring, the officer's portrait (the Leaders
    screen's: `core.leaderportraits`, else OFFICER.LBX's) and his skills'
    icons (OFFICER.LBX `0x58 + id / 2`, `ldrart.skill_icon`)."""

    def __init__(self, art, colours, unit, leader_art):
        from . import cbdraw
        self.ship = cbdraw.unit_picture(art, colours, unit, 0)
        self.upright = cbdraw.unit_picture(
            art, colours, {**unit, "facing_dir": NOSE_UP}, 0)
        self._leader_art = leader_art

    def portrait(self, officer, size):
        from core import leaderportraits
        rec = officer["rec"]
        hd = leaderportraits.picture(rec, size)
        if hd is not None:
            return hd
        la = self._leader_art
        sprite = la.portrait(rec.pict_num) if la is not None and \
            la.available else None
        return leaderportraits.fit(sprite, size) if sprite is not None \
            else None

    def skill_icon(self, sid, size):
        la = self._leader_art
        icon = la.skill_icon(sid) if la is not None and la.available \
            else None
        if icon is None:
            return None
        from screens.leaders import ldrdraw
        return ldrdraw.skill_icon(icon, size)


class Sources:
    """What the scan reads besides the battle: the screen's tables, its
    art and colours, the player's setting. Built by the combat screen."""

    def __init__(self, screen):
        self._screen = screen
        self._words = None
        self._leader_art = None
        self._pictures = {}

    def words(self):
        s = self._screen
        key = (id(s._names), id(s._ken), s._language)
        if self._words is None or self._words[0] != key:
            from core import estrings, hestrings
            from screens.leaders import ldrrows
            unit = ldrrows.UNIT.get(s._language, ldrrows.UNIT_DEFAULT)
            self._words = (key, cbscan.Words(
                s._ken, s._names, estrings.EStrings(s._language),
                hestrings.for_app(s.app), unit))
        return self._words[1]

    def _settings(self):
        return getattr(self._screen.app, "user_settings", None)

    def detailed(self):
        us = self._settings()
        return (us.get(SETTING) if us is not None else DETAILED) != NORMAL

    def set_detailed(self, on):
        us = self._settings()
        if us is None:
            return
        us.set(SETTING, DETAILED if on else NORMAL)
        # kept at once: a battle may end with the window still open
        import os
        from core import usersettings
        if us.path != os.devnull:          # a tool's or a check's settings
            usersettings.save(us)

    def pictures(self, unit):
        """Made once per unit, picture and colours (P828: kept with what
        they were made from)."""
        s = self._screen
        if self._leader_art is None:
            from screens.leaders import ldrart
            self._leader_art = ldrart.load()
        key = (unit["name"], int(unit["picture_num"]),
               int(unit["facing_dir"]), int(unit["owner"]),
               int(unit["previous_owner"]), id(s._art),
               tuple(sorted(s._play.colours.items())))
        hit = self._pictures.get(key)
        if hit is None:
            if len(self._pictures) > 32:
                self._pictures.clear()
            hit = self._pictures[key] = Pictures(
                s._art, s._play.colours, unit, self._leader_art)
        return hit
