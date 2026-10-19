"""The scan's card — work order 297 part B (Data, 18 Oct 2026).

HD EXTENSION `scan_breakdown` (its rules: `cbscanparts`): in the scan
(one view since work order 298) a combat value under the pointer shows its
parts in a card — this
ship's systems one by one, the fixed bonuses as one Base line with its
sources as indented child lines under it — each with its own value,
smaller, dimmer, on a thin tree line (Data, work order 301; one grey line
before) —, what other units give in their own tint and
named, a total at the end; a value whose parts do not make the engine's
sum shows the sum and "Breakdown not available" alone. The same card
shows a cell's whole text where the cell rule cut it, and what a "+n more"
stands for. Each row with a card wears an info sign (drawn: the font need
not have the glyph); no hint text.

Placement (Data, work order 298, replacing 297's rule 13 for these
cards): a combat value's card stands right of COMBAT VALUES, a small gap
off it, its top on the box's top — its top and left edge the same for all
four rows, so moving from row to row does not move the card sideways or up;
its height follows its own rows (Data, work order 299, P3 of 298: no empty
half under a short card) and reaches at least the hovered row, and the
notch on its left edge follows that row's centre. It may cover the right column and
part of WEAPONS: it is there only while hovered and says the state of
every system it names. Inside the scan window. A cut cell's card keeps
rule 13 (297): beside its cell, inside the window, never over COMBAT
VALUES, SPECIAL SYSTEMS or HULL AND SYSTEMS.

The look (work order 298): lying on top — the frame colour's lit edge,
stronger than a box's, with a soft glow round it; a ground darker than the
boxes (the fill family's header, opaque: the transparency slider never
reaches it). A combat value's card has no head (work order 308, Data on
ACGIFT's word: the value stood in its row, the head and the total line):
it opens with its parts under the head-less card's top margin and ends
with the total line, a size larger, a separator over it. A card with no
total line keeps its head — the title in the HUD's accent word colour
(`text.title`), the value large on the right, a separator under it: a
HULL AND SYSTEMS card, and a value's card that says "Breakdown not
available". A damaged or destroyed system of this ship says its
state in the state's colour between its name and its number (Data, work
order 299: "Damaged", "Destroyed", the scan's own state words); an
operational one says none.

Geometry in reference px, scaled by the window's `k` as the scan.
"""
import pygame

from core import lang
from core.hud import blocks as hud
from core.hud import text as hudtext
from . import cbscan, cbscanparts as cp

ROW, SUB, PAD = 28, 22, 16
#: the space between two sentences of a HULL AND SYSTEMS card (302)
GAP_LINE = 6
#: the value card, reference px: its width, its gap off COMBAT VALUES and
#: the notch's depth into that gap and half its height (work order 298)
VALUE_W, GAP, NOTCH, NOTCH_H = 600, 16, 14, 14
#: the head: the title's and the total's size, and its height
TITLE, TOTAL, HEAD = 22, 34, 54
#: the glow's reach round a card, reference px, and its strongest alpha
GLOW, GLOW_ALPHA = 14, 90
#: what another unit gives, in its own tint (Data: "a distinct tint")
FLEET_TINT = (120, 190, 235)
GREY = (130, 136, 150)
#: the tree line of a Base's child lines: dimmer than their words
TREE = (88, 94, 108)
NOT_AVAILABLE = "Breakdown not available"


def signed(v):
    """A card's number as the scan's own rows print theirs: the original's
    Build_Signed_Bonus_String, "+n" above 0, "0" at 0 (cmbtdrw1.cpp:
    3098-3104; v2 :3174-3180). A card's total stands for its row's number,
    so both say the same (audit 26, work order 305: the card said "+0"
    where the row said "0")."""
    return cbscan.signed(v)


class Rows:
    """A card's content: a title, its total, (kind, left, right, colour,
    size) lines."""

    def __init__(self, title, total=None):
        self.title, self.total, self.lines = title, total, []

    def add(self, kind, left, right=None, rgb=None, size=20, state=None):
        self.lines.append((kind, left, right, rgb, size, state))

    def height(self):
        h = HEAD + 8 if self.title else 12
        for kind, *_r in self.lines:
            h += {"note": SUB, "child": SUB, "rule": 12,
                  "gap": GAP_LINE}.get(kind, ROW)
        return h + PAD // 2

    def drawn_height(self, k):
        """The height `draw` takes in device px, step by step as it steps:
        each step at least 9 px (its `px`), so at 1280 x 720 more than
        `height() * k` (work order 302's review: a card's last lines ran
        past its edge)."""
        px = lambda n: max(9, int(n * k))
        h = px(HEAD) + px(8) if self.title else px(12)
        for kind, *_r in self.lines:
            h += px({"sub": SUB, "note": SUB, "child": SUB, "rule": 12,
                     "gap": GAP_LINE}.get(kind, ROW))
        return h + px(PAD // 2)


def value_rows(title, card, rgb, percent=False):
    """The rows of a combat value's card (`cbscanparts.Card`)."""
    tot = f"{card.total}%" if percent else signed(card.total)
    # no head over a breakdown: its total line says the value (308); the
    # head stays where no total line follows
    rows = Rows(None if card.ok else title, tot)
    if not card.ok:
        rows.add("note", NOT_AVAILABLE, rgb=GREY)
        return rows
    for p in card.parts:
        st = p.state if p.kind == cp.SYSTEM else cbscan.OK
        fleet = p.kind == cp.FLEET
        ink = rgb["state"][st] if st != cbscan.OK else \
            FLEET_TINT if fleet else rgb["value"]
        right = signed(p.value) if p.value is not None else (p.note or "")
        rows.add("line", p.label, right,
                 (FLEET_TINT if fleet else rgb["label"], ink), 20,
                 st if st != cbscan.OK else None)
        for n, (name, v) in enumerate(p.sources):
            # the last child closes the tree line (`state` carries it)
            rows.add("child", name, signed(v), GREY, 18,
                     n == len(p.sources) - 1)
        if p.note and p.value is not None:
            rows.add("note", p.note, rgb=rgb["state"][cbscan.DESTROYED]
                     if p.note.startswith("counts") else GREY)
    rows.add("rule", "")
    rows.add("line", "Total", tot, (rgb["label"], rgb["value"]), 22)
    return rows


def speed_rows(title, card, top, rgb, galaxy=None):
    """Combat speed's card; `galaxy` the drive's parsecs a turn, its last
    line under its own separator — not part of the speed.
    DEVIATION `scan_galaxy_speed` (Data, work order 302): the original
    printed it under the drive's hits, above the combat speed, always in
    view (v2 cmbtdrw1.cpp:3548-3567)."""
    rows = Rows(None if card.ok else title, f"{card.total} / {top}")
    if not card.ok:
        rows.add("note", NOT_AVAILABLE, rgb=GREY)
        if galaxy:
            rows.add("rule", "")
            rows.add("line", "Galaxy speed", galaxy,
                     (rgb["label"], rgb["label"]), 20)
        return rows
    for p in card.parts:
        st = p.state if p.kind == cp.SYSTEM and p.state != cbscan.OK \
            else None
        right = p.note if p.value is None else (
            str(p.value) if p.label == "Design speed" else signed(p.value))
        ink = rgb["state"][st] if st else FLEET_TINT \
            if p.kind == cp.FLEET else rgb["value"]
        rows.add("line", p.label, right, (rgb["label"], ink), 20, st)
    rows.add("rule", "")
    rows.add("line", "Current speed", str(card.total),
             (rgb["label"], rgb["value"]), 22)
    rows.add("line", "Maximum", str(top), (rgb["label"], rgb["value"]), 22)
    if galaxy:
        rows.add("rule", "")
        rows.add("line", "Galaxy speed", galaxy,
                 (rgb["label"], rgb["label"]), 20)
    return rows


def text_rows(whole):
    rows = Rows(None)
    rows.add("wrap", whole)
    return rows


def info_sign(surface, centre, r, rgb):
    """ⓘ, drawn: a ring, a dot and a stem."""
    lw = max(1, round(r / 5))
    # LOOK EXCEPTION marking: the info sign of a row with a card (297)
    pygame.draw.circle(surface, rgb, centre, r, lw)
    pygame.draw.circle(surface, rgb, (centre[0], centre[1] - r * 0.45),
                       max(1, lw))
    pygame.draw.line(surface, rgb, (centre[0], centre[1] - r * 0.1),
                     (centre[0], centre[1] + r * 0.5), lw + 1)


def place(size, row, window, avoid, column=None):
    """Where a card of `size` stands for `row`: in `column` (the left
    column's x span) beside the row when given, else under or over the
    row; inside `window`; never over a rect of `avoid`. None when nowhere
    fits."""
    w, h = size
    inner = window.inflate(-8, -8)
    tries = []
    if column is not None:
        tries.append((column[0], row.y))
        tries.append((column[0], row.bottom - h))
    tries += [(row.x, row.bottom + 4), (row.x, row.y - h - 4),
              (row.right - w, row.bottom + 4), (row.right - w, row.y - h - 4)]
    for x, y in tries:
        r = pygame.Rect(x, y, w, h)
        r.clamp_ip(inner)
        if not r.colliderect(row) and not any(r.colliderect(a)
                                              for a in avoid):
            return r
    return None


def margin(k):
    """How far a card keeps off the window's edge: its glow and a hair."""
    return max(1, round(GLOW * k)) + max(1, round(4 * k))


def value_rect(window, values, height, k, tallest=None, row=None):
    """The value card's rectangle (Data, work orders 298 and 299): right of
    COMBAT VALUES by the gap, its top on the box's top, as high as its own
    rows (`height`) and at least down to the hovered `row`'s foot, so the
    notch always meets it; inside the window with its glow. The top and
    the left edge are the same for every row: the top moves up only when
    the `tallest` of the four cards is too tall for the room below the
    box's top, and then for all four alike; a card taller than the window
    is cut to it — never centred out of it (`Rect.clamp_ip` would)."""
    inner = window.inflate(-2 * margin(k), -2 * margin(k))
    w = min(round(VALUE_W * k), inner.w)
    top = min(max(height if tallest is None else tallest, height), inner.h)
    x = min(values.right + round(GAP * k), inner.right - w)
    y = max(inner.y, min(values.y, inner.bottom - top))
    reach = row.bottom - y if row is not None else 0
    h = min(max(height, reach), inner.bottom - y)
    return pygame.Rect(max(inner.x, x), y, w, h)


def notch(rect, row, k, right=False):
    """The notch's three points: its tip in the gap, toward the hovered
    row's vertical centre, held to the card's edge — the left edge for a
    value's card, the right for a HULL AND SYSTEMS row's (302)."""
    h = max(3, round(NOTCH_H * k))
    cy = max(rect.y + h + 2, min(rect.bottom - h - 2, row.centery))
    if right:
        return ((rect.right - 2, cy - h),
                (rect.right - 1 + max(3, round(NOTCH * k)), cy),
                (rect.right - 2, cy + h))
    return ((rect.x + 1, cy - h), (rect.x - max(3, round(NOTCH * k)), cy),
            (rect.x + 1, cy + h))


def hull_rows(style, k, card):
    """A HULL AND SYSTEMS row's card (HD EXTENSION `scan_hull_cards`, work
    order 302): its title, the row's hits large on the right, each sentence
    word-wrapped to the card's width, a small gap between sentences."""
    title, total, sentences = card
    rows = Rows(str(title).upper(), total)
    size = max(9, int(20 * k))
    room = round(VALUE_W * k) - 2 * max(9, int(PAD * k))
    # a name the head would cut stands whole as the first line: the card is
    # also what a cut name in the row shows (rule 13, work order 297)
    width = lambda t, n: style.render_text(t, n, (255, 255, 255)).get_width()
    head = room - width(total, max(9, int(TOTAL * k))) - max(9, int(12 * k))
    if width(rows.title, max(9, int(TITLE * k))) > head:
        for line in wrap(style, str(title), size, room):
            rows.add("wrap", line)
        rows.add("gap", "")
    for n, sentence in enumerate(sentences):
        if n:
            rows.add("gap", "")
        # the sentence translated whole, then cut into lines
        for line in wrap(style, lang.tr(sentence), size, room):
            rows.add("wrap", line)
    return rows


def hull_rect(window, hull, height, k, row):
    """The card of a HULL AND SYSTEMS row (Data, work order 302): left of
    the box by the gap, so it never covers the row it explains; its top on
    the box's top, at least down to the row; inside the window with its
    glow, moved up when too tall, never centred out of it."""
    inner = window.inflate(-2 * margin(k), -2 * margin(k))
    w = min(round(VALUE_W * k), inner.w)
    x = max(inner.x, hull.x - round(GAP * k) - w)
    h = min(max(height, row.bottom - hull.y), inner.h)
    y = max(inner.y, min(hull.y, inner.bottom - h))
    return pygame.Rect(x, y, w, h)


def ground():
    """The card's ground: the fill family's darkest box member, opaque."""
    from core.hud import fill
    return fill.member("header")


def glow(rect, edge, k, scale):
    """The soft glow round `rect`: one ring a device px, each on the
    panel's chamfered outline grown by its distance, its alpha falling off
    outward — rings that meet, never overwrite one another."""
    pad = max(1, round(GLOW * k))
    surf = pygame.Surface((rect.w + 2 * pad, rect.h + 2 * pad),
                          pygame.SRCALPHA)
    for d in range(pad, 0, -1):
        a = round(GLOW_ALPHA * (1 - (d - 1) / pad) ** 2)
        pts = [(pad - d + x, pad - d + y) for x, y in
               hud.panel_polygon(rect.w - 1 + 2 * d, rect.h - 1 + 2 * d,
                                 scale)]
        # LOOK EXCEPTION marking: the card's soft outer glow in the frame
        # colour, so it reads as lying on top (Data, work order 298)
        pygame.draw.polygon(surf, (*edge, a), pts, 2)
    return surf, pad


def draw(surface, style, scale, k, rect, rows, rgb, tip=None, bounds=None):
    """The card in `rect`, lying on top (work order 298), its rows top
    down; `tip` the notch's points (a value card's); `bounds` the scan
    window, which the glow never passes."""
    from core.hud import style as hudstyle
    px = lambda n: max(9, int(n * k))
    thin = lambda n: max(1, round(n * k))
    edge = hudstyle.get().colour("popup.edge")[:3]
    halo, pad = glow(rect, edge, k, scale)
    keep = surface.get_clip()
    if bounds is not None:
        surface.set_clip(pygame.Rect(bounds).clip(keep))
    surface.blit(halo, (rect.x - pad, rect.y - pad))
    surface.set_clip(keep)
    # LOOK EXCEPTION marking: the card's own ground, opaque and darker than
    # the boxes — the glass (work order 253) and the scan's transparency
    # slider never reach it, so it reads over stars and nebula; filled to
    # the panel's own chamfered outline, so no corner shows past the edge
    shape = [(rect.x + x, rect.y + y) for x, y in
             hud.panel_polygon(rect.w - 1, rect.h - 1, scale)]
    pygame.draw.polygon(surface, ground(), shape)
    if tip is not None:
        pygame.draw.polygon(surface, ground(), tip)
    hud.panel(surface, rect, scale, lit=True, filled=False)
    # LOOK EXCEPTION marking: the card's edge, the frame colour lit and
    # stronger than a box's (Data, work order 298), on the panel's own
    # chamfered outline
    pygame.draw.polygon(surface, edge, shape, thin(2))
    if tip is not None:
        pygame.draw.lines(surface, edge, False, tip, thin(2))
    x, y = rect.x + px(PAD), rect.y + px(12)
    right = rect.right - px(PAD)

    def put(t, at, size, ink, anchor="topleft", heavy=False):
        img = style.render_text(str(t), px(size), ink[:3])
        r = img.get_rect(**{anchor: at})
        surface.blit(img, r)
        if heavy:                   # the font has no bold: struck twice
            surface.blit(img, r.move(thin(1), 0))
            r = r.inflate(thin(1), 0)
        return r

    if rows.title:
        room = right - x
        if rows.total is not None:
            tr = put(rows.total, (right, rect.y + px(6)), TOTAL,
                     rgb["value"], "topright", heavy=True)
            room = tr.x - px(12) - x
        # the title in the HUD's accent word colour (`text.title`: it follows
        # the frame's hue, `style.WORDS_THAT_FOLLOW`), the edge the frame's
        put(fit(style, rows.title, px(TITLE), room), (x, y + px(4)), TITLE,
            hudtext.colour("title"))
        y = rect.y + px(HEAD)
        hud.separator(surface, x, right, y, scale)
        y += px(8)
    for kind, left, right_t, ink, size, state in rows.lines:
        if kind == "rule":
            hud.separator(surface, x, right, y + px(4), scale)
            y += px(12)
        elif kind == "gap":
            y += px(GAP_LINE)
        elif kind == "wrap":
            for line in wrap(style, left, px(20), right - x):
                put(line, (x, y), 20, rgb["value"])
                y += px(ROW)
        elif kind == "child":
            # ├ / └ drawn, so no font need have the glyphs: the stem from
            # the line above to this row's middle, on through a middle
            # child, and the tick to the words
            tx, cy, lw = x + px(10), y + px(SUB) // 2, thin(1)
            pygame.draw.line(surface, TREE, (tx, y - px(4)),
                             (tx, cy if state else y + px(SUB)), lw)
            pygame.draw.line(surface, TREE, (tx, cy), (tx + px(12), cy), lw)
            vr = put(right_t, (right, y), size, ink, "topright")
            put(fit(style, left, px(size), vr.x - px(10) - (tx + px(18))),
                (tx + px(18), y), size, ink)
            y += px(SUB)
        elif kind == "note":
            put(fit(style, left, px(18), right - x - px(8)),
                (x + px(8), y), 18, ink)
            y += px(SUB)
        else:
            lab_ink, val_ink = ink
            vr = put(right_t or "", (right, y), size, val_ink, "topright")
            if state is not None:
                # the state word, the scan's own, in the state's colour
                # (work order 299); the label gives way to it
                gap = px(12) if right_t else 0
                vr = vr.union(put(state, (vr.x - gap, y), size,
                                  rgb["state"][state], "topright"))
            put(fit(style, left, px(size), vr.x - px(10) - x), (x, y), size,
                lab_ink)
            y += px(ROW)


def fit(style, t, size, room):
    from .cbscanview import fitted
    return fitted(style, t, size, room)


def wrap(style, text, size, room):
    """Words onto lines of `room` device px. A list (a cut cell's whole
    text: ", " between its items, no full stop) breaks after its commas
    where it can; anything else, and a list item wider than the room,
    breaks at its spaces (work order 302: a card's sentences)."""
    text = str(text)
    width = lambda t: style.render_text(t, size, (255, 255, 255)).get_width()
    listed = ", " in text and not text.rstrip().endswith(".")
    words = []
    if listed:
        items = text.split(", ")
        for n, item in enumerate(items):
            item += "," if n + 1 < len(items) else ""
            # an item that fits stays whole: one word to the breaking
            words.append(item if width(item) <= room else None)
            if words[-1] is None:
                words[-1:] = item.split(" ")
    else:
        words = text.split(" ")
    out, line = [], ""
    for word in words:
        cand = f"{line} {word}" if line else word
        if line and width(cand) > room:
            out.append(line)
            cand = word
        line = cand
    if line:
        out.append(line)
    return out


def value_card(m, key, rgb):
    """The rows of the card of combat value `key` of the model `m`."""
    title = {"attack": m.words["beam_attack"],
             "defense": m.words["beam_defense"],
             "evasion": m.words["missile_evasion"],
             "speed": "Combat speed"}[key].upper()
    card = m.cards[key]
    galaxy = f"{m.parsecs}{m.words['parsecs']}" if m.drive is not None \
        else None
    return speed_rows(title, card, m.speed_max, rgb, galaxy) \
        if key == "speed" else value_rows(title, card, rgb,
                                          percent=key == "evasion")


def show(view, surface, style, scale, k, m, pointer, rgb, column):
    """The card of what is under the pointer (HD EXTENSION
    `scan_breakdown`): a value's at its one place right of COMBAT VALUES
    (work order 298), a cut cell's by rule 13 (297)."""
    values = view.rects.get("values") or {}
    for key, r in values.items():
        if not (m.cards and r.collidepoint(pointer)):
            continue
        cards = {kk: value_card(m, kk, rgb) for kk in values}
        # one top and one left edge for every row, the height the card's
        # own (work order 299)
        # the height as `draw` steps it (each step at least 9 px), so a
        # short card at 1280 x 720 does not end under its last line
        at = value_rect(view.window, view.boxes["values"],
                        cards[key].drawn_height(k), k,
                        max(c.drawn_height(k) for c in cards.values()), r)
        tip = notch(at, r, k)
        draw(surface, style, scale, k, at, cards[key], rgb, tip,
             bounds=view.window)
        view.card = (key, at, tip)
        return
    for key, r in (view.rects.get("hull") or {}).items():
        cards = getattr(m, "hull_cards", None) or {}
        if key not in cards or not r.collidepoint(pointer):
            continue
        rows = hull_rows(style, k, cards[key])
        at = hull_rect(view.window, view.boxes["hull"],
                       rows.drawn_height(k), k, r)
        tip = notch(at, r, k, right=True)
        draw(surface, style, scale, k, at, rows, rgb, tip,
             bounds=view.window)
        view.card = ("hull", at, r, tip)
        return
    avoid = [view.boxes[b] for b in ("values", "specials", "hull")]
    for r, whole in view.cut:
        if not r.collidepoint(pointer):
            continue
        # as wide as the left column at most, so it can stand there, clear
        # of the boxes that list the systems (rule 13)
        room = column.w - 2 * int(PAD * k)
        lines = wrap(style, whole, max(9, int(20 * k)), room)
        if not lines:
            return
        rows = text_rows(whole)
        wide = max(style.render_text(t, max(9, int(20 * k)),
                                     (255, 255, 255)).get_width()
                   for t in lines)
        size = (min(column.w, wide + 2 * int(PAD * k)),
                int((24 + len(lines) * ROW) * k))
        at = place(size, r, view.window, avoid,
                   column=(column.x, column.right))
        if at is not None:
            draw(surface, style, scale, k, at, rows, rgb,
                 bounds=view.window)
            view.card = ("cell", at, r)
        return
