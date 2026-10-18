"""The ship scan's window — work order 290 (`cbscan` says what it shows).

DEVIATION `scan_view`: a HUD window in the shell's look over the dimmed
battle (decision 71), laid out as Data's sketch and mockup of 17 October
2026 — ship, officer, crew on the left; the shields round the unit's own
picture and the combat values in the middle; hull and systems, the special
systems on the right; the weapons across the foot — not COMBAT.LBX 5 with
the game's own lines (cmbtdrw1.cpp:3223-4007). No weapon or special icons
(Data: the game has none).

HD EXTENSION `scan_transparency`: a slider in the foot lets the battle's
space — stars and nebula, no unit, no panel — through the window's and
the boxes' fills, 0 to 85 %, the edges and the
words stay whole; the player's setting `scan_transparency` (Data, work
order 292).
DEVIATION `scan_one_view` (Data, work order 298): one view that shows more
than the original's — what its scan prints and HD's additions (`cbscan`)
in one window, with the click rule of `scan_card_click`; the Normal /
Detailed switch of work orders 290-297 is gone: Normal was a subset and
every layout had to hold twice.
INVENTION `scan_turn`: the battle's turn (CMBT `turn` + 1) in the head —
the original shows it nowhere.

Geometry in 1920 x 1080 reference pixels, scaled by the window's `k` as
the battle's other popups (`cbpopups._k`); nothing is held across frames
but the click rects of the frame drawn last.
"""
import math

import pygame

from core import lang
from core.hud import blocks as hud
from core.hud import text as hudtext
from . import cbart, cbscan, cbscancard

#: The window and its boxes, reference px. Work order 297 (Data, from the
#: analysis of 18 Oct 2026): each box as high as what it holds needs —
#: SHIELDS gives up height, WEAPONS (8 rows of 22 px text), OFFICER (every
#: combat skill) and COMBAT VALUES gain; measured by check 090znb at three
#: window sizes, every text inside its box.
WINDOW = (60, 30, 1800, 1020)
BOXES = {
    "ship": (80, 114, 520, 200), "officer": (80, 328, 520, 250),
    "crew": (80, 592, 520, 126),
    "shields": (614, 114, 600, 350), "values": (614, 478, 600, 240),
    # a designed ship has 8 special systems at most (the designer's
    # `special_devices[8]`, design.cpp:94-101): 8 rows in one column; 9-16
    # in two, beyond 16 the 16th cell says how many more (work order 297)
    "hull": (1228, 114, 612, 250), "specials": (1228, 378, 612, 340),
    "weapons": (80, 732, 1760, 248),
}
TITLES = {"ship": "SHIP", "officer": "OFFICER", "crew": "CREW",
          "shields": "SHIELDS", "values": "COMBAT VALUES",
          "hull": "HULL AND SYSTEMS", "specials": "SPECIAL SYSTEMS",
          "weapons": "WEAPONS"}
#: HD EXTENSION `scan_states`: a part's state by colour — operational,
#: damaged, destroyed (the original colours only a destroyed special).
STATE_RGB = {cbscan.OK: (80, 210, 110), cbscan.DAMAGED: (240, 170, 60),
             cbscan.DESTROYED: (230, 70, 60)}
#: The foot's transparency slider, reference px, and its range: 0 is the
#: boxes as every HD window has them, at most 85 % of the battle through.
SLIDER = (1260, 1010, 420, 16)
MAX_TRANSPARENCY = 0.85
BAR_BACK = (40, 46, 60)
#: The facing at which a unit's nose points up the screen, so the shield
#: ring's Front stands at its nose: 0 is nose right, 4 nose up, 12 nose
#: down (`cbart.stored_facing`; rendered, work order 296 — 12 had stood
#: here since work order 290 and drew the engines under "Front").
NOSE_UP = 4
#: The weapons table, (column, left edge from the box's left, width),
#: reference px (work order 297): what a weapon is and how well it is —
#: Count, HP, State side by side — then how it fires, the mods last and
#: widest.
WEAPON_COLUMNS = (("#", 176, 30), ("Weapon", 210, 300), ("Count", 520, 90),
                  ("HP", 620, 90), ("State", 720, 160), ("Arc", 890, 60),
                  ("Ammo", 960, 110), ("Mods", 1080, 664))
#: A table row, reference px, and the smallest text a crowded box may draw
#: (the analysis' floor: 18 reference px, 12 device px at 1280 x 720).
ROW, WEAPON_TEXT, FLOOR = 26, 22, 18
SPECIAL_ROW, SPECIAL_ROWS = 30, 8
#: The combat values' number column ends this far from the box's right
#: edge: the state marker and the breakdown's info sign stand right of it.
VALUE_PAD = 64
SKILL_ROW = 26
#: a table's column head under a box's title: its top from the box's top,
#: its text size and the gap to the first row — SPECIAL SYSTEMS' and, since
#: work order 301, HULL AND SYSTEMS' "HP" alike
HEAD_Y, HEAD_TEXT, HEAD_GAP = 44, 18, 28
#: HULL AND SYSTEMS: a row's height (its hover band) and how far its hits
#: end from the box's right edge — the ⓘ stands right of them (work order
#: 302)
HULL_ROW, HULL_PAD = 44, 40
#: COMBAT VALUES' four rows share the box under its title: from this far
#: below the box's top to this far above its foot (work order 301)
VALUES_TOP, VALUES_FOOT = 40, 6
#: the state marker's square and stroke, reference px (work orders 297, 301)
MARKER, MARKER_STROKE = 12, 3
ELLIPSIS = "…"
_FITTED = {}


def k_of(surface):
    w, h = surface.get_size()
    return min(w / 1920, h / 1080)


def fitted(style, text, size, room):
    """THE CELL RULE (work order 297): a text wider than its cell is cut
    with an ellipsis, never drawn past it. Kept per (text, size, room)."""
    # cut what is drawn: OrionLayer's own words in the player's language,
    # then kept from being translated again (`core.lang.Stored`)
    text = lang.tr(text)
    key = (text, size, room, id(style))
    hit = _FITTED.get(key)
    if hit is None:
        if len(_FITTED) > 2048:
            _FITTED.clear()
        width = lambda t: style.render_text(t, size, (255, 255, 255)).get_width()
        hit = lang.Stored(text)
        if room > 0 and width(text) > room:
            cut = text
            while cut and width(cut.rstrip(", ·") + ELLIPSIS) > room:
                cut = cut[:-1]
            hit = lang.Stored(cut.rstrip(", ·") + ELLIPSIS)
        _FITTED[key] = hit
    return hit


def value_bands(box, k):
    """COMBAT VALUES' four hover bands, top down: the box under its title
    in four equal parts that meet (work order 301)."""
    x, w = box.x + max(1, round(4 * k)), box.w - 2 * max(1, round(4 * k))
    top = box.y + max(9, int(VALUES_TOP * k))
    step = (box.bottom - max(1, round(VALUES_FOOT * k)) - top) / 4
    edges = [top + round(n * step) for n in range(5)]
    return [pygame.Rect(x, a, w, b - a) for a, b in zip(edges, edges[1:])]


def marker_box(right, cy, k):
    """The marker's square, its right edge at `right`, centred on `cy`."""
    s = max(1, round(MARKER * k))
    return pygame.Rect(right - s, cy - s // 2, s, s)


def marker_shapes(box, state, k):
    """The marker as filled polygons inside `box`, one stroke width for
    both: the "!" a stem and a square dot centred upright, the cross two
    bars corner to corner — their ends cut so neither leaves the box, so
    the drawn signs are the box's height alike."""
    wd = max(1, round(MARKER_STROKE * k))
    if state == cbscan.DAMAGED:
        x0 = box.centerx - wd // 2
        gap = max(1, round(wd * 0.6))
        return ([(x0, box.y), (x0 + wd - 1, box.y),
                 (x0 + wd - 1, box.bottom - 1 - wd - gap),
                 (x0, box.bottom - 1 - wd - gap)],
                [(x0, box.bottom - wd), (x0 + wd - 1, box.bottom - wd),
                 (x0 + wd - 1, box.bottom - 1), (x0, box.bottom - 1)])
    # a bar of perpendicular width `wd`: the fill takes both edges' pixels,
    # so the outline is one px narrower and the drawn bar is as heavy as the
    # stem; its ends inset by half that width along each axis, so its
    # corners touch the box's edges and never pass them
    h = (wd - 1) / 2 / math.sqrt(2)
    l, t = box.x, box.y
    r, b = box.right - 1, box.bottom - 1
    # one bar's corners rounded, the other its mirror about the box's
    # middle: the fill truncates fractional corners, which drew the two
    # bars' ends unlike
    c = math.ceil(2 * h)            # whole px, up: the stem's weight
    one = [(l + c, t), (r, b - c), (r - c, b), (l, t + c)]
    return one, [(l + r - x, y) for x, y in one]


class View:
    def __init__(self):
        self.rects = {}
        self.ring = self.window = None
        self.boxes = {}
        #: the cells drawn cut this frame: [(rect, the whole text)] — what
        #: the card shows under the pointer (work order 297 part B)
        self.cut = []

    def draw(self, surface, style, scale, model, turn, pics,
             transparency=0.0, under=None, pointer=None):
        """One frame of the scan of `model` (`cbscan.Model`); `pics` hands
        in the pictures (`ship`, `upright`, `portrait`, `skill_icon`).
        `transparency` 0..`MAX_TRANSPARENCY` lets `under` — the battle's
        space, `Sources.backdrop` — through the window's and the boxes'
        fills, never through their edges or words (HD EXTENSION
        `scan_transparency`). `pointer`: where the pointer is — the card of
        what is under it (HD EXTENSION `scan_breakdown`) and the value row
        under it in the selected look."""
        self.rects, self.cut = {}, []
        self.card = None
        k = k_of(surface)
        w, h = surface.get_size()
        ox = (w - WINDOW[2] * k) / 2 - WINDOW[0] * k
        oy = (h - WINDOW[3] * k) / 2 - WINDOW[1] * k

        def R(x, y, rw, rh):
            return pygame.Rect(round(ox + x * k), round(oy + y * k),
                               round(rw * k), round(rh * k))

        def px(n):
            return max(9, int(n * k))

        def thin(n):
            """A line's width or a gap below `px`'s 9 device px."""
            return max(1, round(n * k))

        def width(t, size):
            return style.render_text(str(t), px(size), value[:3]).get_width()

        def text(t, at, size, rgb, anchor="topleft", room=None):
            """`room` (device px): the cell's width — cut to fit it."""
            t = str(t)
            whole = lang.tr(t)          # what is drawn when nothing is cut
            if room is not None:
                t = fitted(style, t, px(size), room)
            img = style.render_text(t, px(size), rgb[:3])
            r = img.get_rect(**{anchor: at})
            surface.blit(img, r)
            if t != whole:
                self.cut.append((r, whole))
            return r

        def button(rect, word):
            """A HUD small button whose word reaches the tables' floor
            (Data, work order 299, P8 of 298): the HUD sizes a button's word
            by its height (9-10 device px at 1280 x 720 against the floor's
            12); the word, its colour and its centring stay the HUD's."""
            hud.small_button(surface, rect, scale, "normal")
            size = max(hudtext.size_for(style, "button", rect.h), px(FLOOR))
            img = style.render_text(word.upper(), size,
                                    hudtext.colour("button")[:3])
            hudtext.blit(surface, img, rect)

        label, value = hudtext.colour("label"), hudtext.colour("value")
        head = hudtext.colour("sub")
        hud.popup(surface, R(*WINDOW), scale)
        for key, box in BOXES.items():
            hud.panel(surface, R(*box), scale, dense=True)
        if transparency > 0 and under is not None:
            win = R(*WINDOW).clip(surface.get_rect())
            see = under.subsurface(win).copy()
            see.set_alpha(int(255 * min(MAX_TRANSPARENCY, transparency)))
            surface.blit(see, win)
            # only the fills let the battle through: the edges again
            hud.panel(surface, R(*WINDOW), scale, lit=True, filled=False)
            for box in BOXES.values():
                hud.panel(surface, R(*box), scale, dense=True, filled=False)
        text("SHIP SCAN", R(960, 40, 0, 0).topleft, 40, value, "midtop")
        if turn is not None:
            text(f"Combat turn  {turn}", R(1790, 52, 0, 0).topleft, 28,
                 value, "topright")
        x = R(1804, 44, 40, 40)
        button(x, "X")
        self.rects["close_x"] = x
        for key, box in BOXES.items():
            r = R(*box)
            text(TITLES[key], (r.x + px(14), r.y + px(8)), 24, head)

        def marker(right, cy, state):
            """The state beside a coloured number, so it never rests on the
            colour alone (work order 297): an "!" for damaged, a cross for
            destroyed. Drawn, so no font need have the glyph — and both as
            filled shapes on one square box with one stroke width, so the
            "!" stands upright and straight with the cross's height and
            weight (Data, work orders 300 and 301). Returns its left
            edge."""
            if state not in (cbscan.DAMAGED, cbscan.DESTROYED):
                return right
            box = marker_box(right, cy, k)
            rgb = STATE_RGB[state]
            # LOOK EXCEPTION marking: the state's sign beside a number (297)
            for shape in marker_shapes(box, state, k):
                pygame.draw.polygon(surface, rgb, shape)
            return box.x

        def bar(r, frac, rgb):
            # LOOK EXCEPTION data: a part's hits as a bar (work order 290)
            pygame.draw.rect(surface, BAR_BACK, r)
            if frac > 0:
                # LOOK EXCEPTION data: the hits left, in the part's state colour
                pygame.draw.rect(surface, rgb, (r.x, r.y, int(r.w * min(1, frac)),
                                                r.h))

        def fit_img(img, box):
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
        ink = lambda state: STATE_RGB[state] if state in (
            cbscan.DAMAGED, cbscan.DESTROYED) else value
        # ── A the ship ─────────────────────────────────────────
        r = R(*BOXES["ship"])
        pic_box = R(BOXES["ship"][0] + 16, BOXES["ship"][1] + 40, 140, 140)
        img = fit_img(pics.ship, pic_box)
        if img is not None:
            surface.blit(img, img.get_rect(center=pic_box.center))
        tx = r.x + px(172)
        room = r.right - px(16) - tx
        y = r.y + px(42)
        text(m.name, (tx, y), 32, value, room=room)
        y += px(40)
        for line, size, rgb in ((m.hull, 24, value), (m.owner_name, 24, label),
                                (m.design_date and
                                 f"Design date {m.design_date}", 22, label),
                                (m.captured and m.words["captured"], 22,
                                 STATE_RGB[cbscan.DESTROYED])):
            if line:
                text(line, (tx, y), size, rgb, room=room)
                y += px(28)
        # ── B the officer ──────────────────────────────────────
        r = R(*BOXES["officer"])
        o = m.officer
        if o is None:
            text("No officer", (r.x + px(16), r.y + px(48)), 24, label)
        else:
            # the whole figure, as every place draws it (`leaderportraits`)
            port = R(BOXES["officer"][0] + 12, BOXES["officer"][1] + 38,
                     150, 200)
            pic = pics.portrait(o, port.size)
            if pic is not None:
                surface.blit(pic, pic.get_rect(center=port.center))
            else:
                hud.field(surface, port, scale)
            tx = port.right + px(16)
            room = r.right - px(16) - tx
            text(o["name"], (tx, r.y + px(42)), 30, value, room=room)
            # the level on the title's line (work order 297)
            lw = o["level_word"] or f"Level {o['level']}"
            # the level first: a long title is what the cell rule cuts
            what = " · ".join(p for p in (f"{lw} {m.officer_mark}",
                                          o["title"]) if p)
            text(what, (tx, r.y + px(78)), 20, label, room=room)
            y = r.y + px(110)
            fit = (r.bottom - px(6) - y) // px(SKILL_ROW)
            skills = o["skills"]
            shown = skills if len(skills) <= fit else skills[:fit - 1]
            for sid, name, val in shown:
                icon = pics.skill_icon(sid, px(22))
                if icon is not None:
                    surface.blit(icon, (tx, y))
                vr = text(val, (r.right - px(16), y), 22,
                          STATE_RGB[cbscan.OK], "topright")
                text(name, (tx + px(30), y), 22, label,
                     room=vr.x - px(8) - (tx + px(30)))
                y += px(SKILL_ROW)
            if len(shown) < len(skills):
                more = text(f"+{len(skills) - len(shown)} more",
                            (tx + px(30), y), 20, label)
                self.cut.append((more, ", ".join(
                    f"{n} {v}" for _s, n, v in skills[len(shown):])))
            if not skills:
                text("no skill that acts in battle", (tx, y), 20, label,
                     room=room)
        # ── C the crew: the stars on the level's line, experience and
        # marines on one (work order 297) ───────────────────────
        r = R(*BOXES["crew"])
        y = r.y + px(44)
        if m.crew is not None:
            stars = max(0, min(5, m.crew_quality))
            left = r.right - px(16 + 5 * 26)
            for n in range(5):
                c = (left + px(13 + n * 26), y + px(12))
                rgb = (240, 170, 60) if n < stars else (60, 66, 80)
                pts = [(c[0] + px(11) * math.sin(a * math.pi / 5) *
                        (1 if a % 2 == 0 else 0.45),
                        c[1] - px(11) * math.cos(a * math.pi / 5) *
                        (1 if a % 2 == 0 else 0.45)) for a in range(10)]
                # LOOK EXCEPTION data: the crew stars, one a level (cmbtdrw1.cpp:1222-1245)
                pygame.draw.polygon(surface, rgb, pts)
            cr = text(m.crew, (left - px(12), y), 22, value, "topright")
            text("Crew level", (r.x + px(16), y), 22, label,
                 room=cr.x - px(12) - (r.x + px(16)))
        y2 = y + px(36)
        mx = r.x + px(16)
        if m.experience is not None:
            er = text("Experience", (mx, y2), 22, label)
            text(str(m.experience), (er.right + px(10), y2), 22, value)
        if m.marines is not None:
            vr = text(str(m.marines), (r.right - px(16), y2), 22, value,
                      "topright")
            text(m.words["marines"], (vr.x - px(10), y2), 22, label,
                 "topright")
        # ── D the shields ──────────────────────────────────────
        r = R(*BOXES["shields"])
        # the generator and its state in the title's line, the upgrades
        # and a damper field under it (work order 297, ACGIFT)
        hx = r.right - px(16)
        if m.shield_system is not None:
            cur, most = m.shield_system
            st = cbscan.part_state(cur, most)
            vr = text(f"{cur} / {most}", (hx, r.y + px(10)), 22, ink(st),
                      "topright")
            mx = marker(vr.x - px(6), vr.centery, st)
            text(m.shield_name or "Shield", (mx - px(10), r.y + px(10)),
                 22, label, "topright")
        elif m.damper is not None:
            name, st = m.damper
            vr = text(st, (hx, r.y + px(10)), 22, STATE_RGB[st],
                      "topright")
            text(name, (vr.x - px(10), r.y + px(10)), 22, label,
                 "topright")
        elif m.shield_name:
            text(m.shield_name, (hx, r.y + px(10)), 22, label, "topright")
        x0, ty = r.x + px(16), r.y + px(40)
        tags = m.shield_tags
        for n, (name, st) in enumerate(tags):
            sep = px(26) if n else 0
            need = width(name, 20) + (px(18) if st != cbscan.OK else 0)
            rest = len(tags) - n - 1
            end = r.right - px(16) - (px(48) if rest else 0)
            if x0 + sep + need > end:
                # the rest by number; the card names them
                more = text(f"+{len(tags) - n}", (x0 + sep, ty), 20,
                            label)
                self.cut.append((more, ", ".join(t for t, _s in
                                                 tags[n:])))
                break
            if n:
                text("·", (x0 + px(9), ty), 20, label)
            tr = text(name, (x0 + sep, ty), 20,
                      ink(st) if st != cbscan.OK else label)
            x0 = tr.right
            if st != cbscan.OK:
                x0 = tr.right + px(18)
                marker(x0, tr.centery, st)
        # the ring and its four arcs below the head
        c = (r.centerx, r.y + px(198))
        img = fit_img(pics.upright, pygame.Rect(0, 0, px(104), px(104)))
        if img is not None:
            surface.blit(img, img.get_rect(center=c))
        most = max(1, m.shield_max)
        rad = px(80)
        box = pygame.Rect(0, 0, 2 * rad, 2 * rad)
        box.center = c
        self.ring = box.copy()                  # held by check 090znb
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
            at = {0: (c[0], c[1] - rad - px(54)),
                  2: (c[0], c[1] + rad + px(8)),
                  3: (c[0] - rad - px(80), c[1] - px(24)),
                  1: (c[0] + rad + px(80), c[1] - px(24))}[arc]
            lr = text(names[arc], at, 22, label, "midtop")
            text(f"{m.arcs[arc]} / {m.shield_max}",
                 (lr.centerx, lr.bottom), 24, rgb, "midtop")
        # ── E the combat values: four rows spread evenly over the box,
        # nothing under them (Data, work order 301: the card shows every
        # part; the computer's sub-line of 297 showed one as the only one);
        # the number coloured by THIS ship's systems behind it, the label
        # never
        r = R(*BOXES["values"])
        self.rects["values"] = {}
        vs = m.value_states
        rows = ((m.words["beam_attack"], cbscan.signed(m.attack), "attack"),
                (m.words["beam_defense"], cbscan.signed(m.defense),
                 "defense"),
                (m.words["missile_evasion"], f"{m.evasion}%", "evasion"),
                ("Combat speed", f"{m.speed[0]} / {m.speed_max}", "speed"))
        for band in value_bands(r, k):
            lab, val, key = rows[len(self.rects["values"])]
            st = vs.get(key, cbscan.OK)
            vx, cy = r.right - px(VALUE_PAD), band.centery
            # the bands tile the box under its title: no gap where the card
            # would go away for a frame or a click would close the scan
            lit = bool(m.cards) and pointer is not None and \
                band.collidepoint(pointer)
            if lit:
                # the row under the pointer: the one "selected" look of
                # decision 92 (Data, work order 298), no colour of its own
                hud.table_row(surface, band, scale, 0, selected=True)
            if key == "speed":
                # the current speed follows the drive, the maximum not
                mr = text(f" / {m.speed_max}", (vx, cy), 24, value,
                          "midright")
                vr = text(f"{m.speed[0]}", (mr.x, cy), 24, ink(st),
                          "midright").union(mr)
            else:
                vr = text(val, (vx, cy), 24, ink(st), "midright")
            marker(r.right - px(40), vr.centery, st)
            if m.cards:
                cbscancard.info_sign(surface, (r.right - px(25),
                                               vr.centery), thin(8),
                                     value if lit else head)
            text(lab, (r.x + px(16), cy), 24, label, "midleft",
                 room=vr.x - px(12) - (r.x + px(16)))
            self.rects["values"][key] = band
        # ── F hull and systems: a card for each row (HD EXTENSION
        # `scan_hull_cards`, Data, work order 302) — its ⓘ right of the
        # hits, the row under the pointer in the selected look ──────
        r = R(*BOXES["hull"])
        # the hits' column head, as SPECIAL SYSTEMS' "System · HP · State"
        # head: its size, colour and place under the title, so both boxes
        # look alike; no State — the bar's colour says it (Data, work
        # orders 301 and 302)
        head_y = r.y + px(HEAD_Y)
        nx = r.right - px(HULL_PAD)
        text("HP", (nx, head_y), HEAD_TEXT, label, "topright")
        y = head_y + px(HEAD_GAP)
        wd = m.words
        cards = getattr(m, "hull_cards", None) or {}
        # the part's own name ("Xentronium Armor") stands for the word; the
        # drive's galaxy speed is in Combat speed's card (Data, work order
        # 302, P1 of 301: nothing in a battle reads it)
        lines = [("structure", wd["structure"], m.structure),
                 ("armor", m.armour_name or wd["armor"], m.armour)]
        if m.drive is not None:
            lines.append(("drive", wd["drive"], m.drive))
        lines.append(("computer", m.computer_name or wd["computer"],
                      m.computer))
        # the computer's longest name (299 px at 22) keeps its room
        bar_x = r.right - px(HULL_PAD + 242)
        self.rects["hull"] = {}
        for key, lab, pair in lines:
            cur, most = pair
            band = pygame.Rect(r.x + px(4), y - px(10), r.w - px(8),
                               px(HULL_ROW))
            lit = key in cards and pointer is not None and \
                band.collidepoint(pointer)
            if lit:
                hud.table_row(surface, band, scale, 0, selected=True)
            frac = cur / most if most else 0
            rgb = STATE_RGB[cbscan.OK] if most and cur >= most else \
                STATE_RGB[cbscan.DAMAGED] if cur > 0 else \
                STATE_RGB[cbscan.DESTROYED]
            text(lab, (r.x + px(16), y), 22, label,
                 room=bar_x - px(10) - (r.x + px(16)))
            bar(pygame.Rect(bar_x, y + px(4), px(100), px(16)), frac, rgb)
            # a part at 0 HP says so in its number, the empty bar stays
            # (Data, work order 303, P5 of 302)
            nr = text(f"{cur} / {most}" if most is not None else str(cur),
                      (nx, y), 22, STATE_RGB[cbscan.DESTROYED]
                      if most and cur <= 0 else value, "topright")
            if key in cards:
                cbscancard.info_sign(surface, (r.right - px(25),
                                               nr.centery), thin(8),
                                     value if lit else head)
                self.rects["hull"][key] = band
            y += px(HULL_ROW)
        # ── G the special systems: 8 rows; 9-16 in two columns; beyond
        # 16 the last cell says how many more (work order 297) ───────
        r = R(*BOXES["specials"])
        rows = m.specials
        if not rows:
            text(m.words["no_specials"], (r.x + px(16), r.y + px(48)), 22,
                 label)
        else:
            head_y = r.y + px(HEAD_Y)
            two = len(rows) > SPECIAL_ROWS
            cols = 2 if two else 1
            cw = (r.w - px(32)) // cols
            cells = rows if len(rows) <= 2 * SPECIAL_ROWS else \
                rows[:2 * SPECIAL_ROWS - 1]
            size = 22 if not two else 20
            for col in range(cols):
                x0 = r.x + px(16) + col * cw
                x1 = x0 + cw - (px(28) if two and col == 0 else 0)
                text("System", (x0, head_y), HEAD_TEXT, label)
                text("HP", (x1 - (px(154) if not two else 0), head_y),
                     HEAD_TEXT, label, "topright")
                if not two:
                    text("State", (x1, head_y), HEAD_TEXT, label, "topright")
            y0 = head_y + px(HEAD_GAP)
            for n, (_b, name, cur, most, state) in enumerate(cells):
                col, line = divmod(n, SPECIAL_ROWS)
                x0 = r.x + px(16) + col * cw
                x1 = x0 + cw - (px(28) if two and col == 0 else 0)
                y = y0 + line * px(SPECIAL_ROW)
                rgb = STATE_RGB[state] if state != cbscan.OK else value
                hp = "—" if most is None else f"{cur} / {most}"
                if two:
                    mk = marker(x1, y + px(11), state)
                    hr = text(hp, (mk - px(6), y), size, value, "topright")
                    right = hr.x
                else:
                    sr = text(state, (x1, y), size, STATE_RGB[state],
                              "topright")
                    hr = text(hp, (x1 - px(154), y), size, value,
                              "topright")
                    right = min(hr.x, sr.x)
                text(name, (x0, y), size, rgb, room=right - px(10) - x0)
            if len(cells) < len(rows):
                col, line = divmod(len(cells), SPECIAL_ROWS)
                at = (r.x + px(16) + col * cw,
                      y0 + line * px(SPECIAL_ROW))
                more = text(f"+{len(rows) - len(cells)} more", at, size,
                            label)
                self.cut.append((more, ", ".join(
                    name for _b, name, _c, _m, _s in rows[len(cells):])))
        # ── W the weapons ──────────────────────────────────────
        r = R(*BOXES["weapons"])
        cols = WEAPON_COLUMNS
        for name, x, _w in cols:
            text(name, (r.x + px(x), r.y + px(10)), 18, label)
        rows = m.weapons
        room = r.h - px(40)
        step = max(px(FLOOR + 2), min(px(ROW), room // max(1, len(rows))))
        size = max(FLOOR, min(WEAPON_TEXT, int(step / k * 0.85)))
        y = r.y + px(38)
        for n, wr in enumerate(rows):
            rgb = STATE_RGB[wr["state"]] if wr["state"] != cbscan.OK \
                else value
            # "count/original" and the HP of the weapon in front, HP and
            # State in the state's colour (work order 294)
            cells = {"#": str(n + 1), "Weapon": wr["name"],
                     "Count": wr["count_of"],
                     "Arc": wr["arc"], "Ammo": wr["ammo"],
                     "Mods": wr["mods"], "HP": wr["hp"],
                     "State": wr["state"]}
            for name, x, cw in cols:
                tint = STATE_RGB[wr["state"]] if name in ("HP", "State") \
                    else rgb if name == "Count" else value
                text(cells[name], (r.x + px(x), y), size, tint,
                     room=px(cw) - px(8))
            y += step
        if not rows:
            text(m.words["none"], (r.x + px(210), r.y + px(40)), 22, label)
        # ── the foot ───────────────────────────────────────────
        cr = R(840, 996, 240, 42)
        button(cr, "CLOSE")
        self.rects["close"] = cr
        x0 = R(100, 1004, 0, 0)
        for n, (state, rgb) in enumerate(STATE_RGB.items()):
            at = (x0.x + px(n * 170), x0.y)
            pygame.draw.circle(surface, rgb, (at[0] + px(6), at[1] + px(11)),
                               px(6))
            text(state, (at[0] + px(22), at[1]), 18, label)
        # the transparency slider (HD EXTENSION `scan_transparency`)
        text("Transparency", R(1110, 1004, 0, 0).topleft, 18, label)
        bar = R(*SLIDER)
        hud.field(surface, bar, scale)
        t = max(0.0, min(MAX_TRANSPARENCY, transparency))
        knob = pygame.Rect(0, 0, max(4, px(10)), bar.h + px(8))
        knob.center = (bar.x + int(bar.w * t / MAX_TRANSPARENCY), bar.centery)
        # LOOK EXCEPTION marking: the slider's knob, in the value colour
        pygame.draw.rect(surface, value[:3], knob, border_radius=px(3))
        text(f"{round(t * 100)}%", (bar.right + px(14), R(0, 1004, 0, 0).y),
             18, value)
        self.rects["transparency"] = bar.inflate(0, px(16))
        self.boxes = {key: R(*b) for key, b in BOXES.items()}
        self.window = R(*WINDOW)
        if pointer is not None:
            cbscancard.show(self, surface, style, scale, k, model, pointer,
                            {"label": label, "value": value,
                             "state": STATE_RGB}, R(80, 0, 520, 0))

    def card_at(self, x, y):
        """A card drawn in the frame drawn last for what is at (x, y): a
        value row, a HULL AND SYSTEMS row (work order 302) or a cut cell (the click rule, DEVIATION
        `scan_card_click`) — never a row whose card found no place."""
        if self.card is None:
            return False
        rows = self.rects.get("values") or {}
        hit = self.card[2] if self.card[0] in ("cell", "hull") else \
            rows.get(self.card[0])
        return hit is not None and hit.collidepoint(x, y)
