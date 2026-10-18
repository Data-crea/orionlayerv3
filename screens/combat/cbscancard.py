"""The scan's card — work order 297 part B (Data, 18 Oct 2026).

HD EXTENSION `scan_breakdown` (its rules: `cbscanparts`): in the scan
(one view since work order 298) a combat value under the pointer shows its
parts in a card — this
ship's systems one by one, the fixed bonuses as one Base line with its
sources under it in grey, what other units give in their own tint and
named, a total at the end; a value whose parts do not make the engine's
sum shows the sum and "Breakdown not available" alone. The same card
shows a cell's whole text where the cell rule cut it, and what a "+n more"
stands for. Each row with a card wears an info sign (drawn: the font need
not have the glyph); no hint text.

Placement (Data, work order 298, replacing 297's rule 13 for these
cards): a combat value's card stands right of COMBAT VALUES, a small gap
off it, its top on the box's top — ONE rectangle for all four rows, so
moving from row to row does not move the card; only the notch on its left
edge follows the hovered row's centre. It may cover the right column and
part of WEAPONS: it is there only while hovered and says the state of
every system it names. Inside the scan window. A cut cell's card keeps
rule 13 (297): beside its cell, inside the window, never over COMBAT
VALUES, SPECIAL SYSTEMS or HULL AND SYSTEMS.

The look (work order 298): lying on top — the frame colour's lit edge,
stronger than a box's, with a soft glow round it; a ground darker than the
boxes (the fill family's header, opaque: the transparency slider never
reaches it); the title in the HUD's accent word colour (`text.title`), the total large on the
right, a separator under the head; the total line a size larger, a
separator over it.

Geometry in reference px, scaled by the window's `k` as the scan.
"""
import pygame

from core.hud import blocks as hud
from core.hud import text as hudtext
from . import cbscan, cbscanparts as cp

ROW, SUB, PAD = 28, 22, 16
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
NOT_AVAILABLE = "Breakdown not available"


def signed(v):
    return f"{int(v):+d}"


class Rows:
    """A card's content: a title, its total, (kind, left, right, colour,
    size) lines."""

    def __init__(self, title, total=None):
        self.title, self.total, self.lines = title, total, []

    def add(self, kind, left, right=None, rgb=None, size=20, state=None):
        self.lines.append((kind, left, right, rgb, size, state))

    def height(self):
        h = HEAD + 8
        for kind, *_r in self.lines:
            h += {"sub": SUB, "note": SUB, "rule": 12}.get(kind, ROW)
        return h + PAD // 2


def value_rows(title, card, rgb, percent=False):
    """The rows of a combat value's card (`cbscanparts.Card`)."""
    tot = f"{card.total}%" if percent else signed(card.total)
    rows = Rows(title, tot)
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
        if p.sources:
            rows.add("sub", " · ".join(f"{n} {signed(v)}"
                                       for n, v in p.sources), rgb=GREY)
        if p.note and p.value is not None:
            rows.add("note", p.note, rgb=rgb["state"][cbscan.DESTROYED]
                     if p.note.startswith("counts") else GREY)
    rows.add("rule", "")
    rows.add("line", "Total", tot, (rgb["label"], rgb["value"]), 22)
    return rows


def speed_rows(title, card, top, rgb):
    rows = Rows(title, f"{card.total} / {top}")
    if not card.ok:
        rows.add("note", NOT_AVAILABLE, rgb=GREY)
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


def value_rect(window, values, height, k):
    """The value card's one rectangle (Data, work order 298): right of
    COMBAT VALUES by the gap, its top on the box's top, as high as its rows
    and never lower than the box (the notch always meets a row), inside
    the window with its glow. Its top moves up only for a card too tall for
    the room below the box's top, and a card taller than the window is cut
    to it — never centred out of it (`Rect.clamp_ip` would)."""
    inner = window.inflate(-2 * margin(k), -2 * margin(k))
    w = min(round(VALUE_W * k), inner.w)
    h = min(max(height, values.h), inner.h)
    x = min(values.right + round(GAP * k), inner.right - w)
    y = max(inner.y, min(values.y, inner.bottom - h))
    return pygame.Rect(max(inner.x, x), y, w, h)


def notch(rect, row, k):
    """The notch's three points: its tip in the gap, toward the hovered
    row's vertical centre, held to the card's edge."""
    h = max(3, round(NOTCH_H * k))
    cy = max(rect.y + h + 2, min(rect.bottom - h - 2, row.centery))
    return ((rect.x + 1, cy - h), (rect.x - max(3, round(NOTCH * k)), cy),
            (rect.x + 1, cy + h))


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
        elif kind == "wrap":
            for line in wrap(style, left, px(20), right - x):
                put(line, (x, y), 20, rgb["value"])
                y += px(ROW)
        elif kind in ("sub", "note"):
            put(fit(style, left, px(18), right - x - px(8)),
                (x + px(8), y), 18, ink)
            y += px(SUB)
        else:
            lab_ink, val_ink = ink
            vr = put(right_t or "", (right, y), size, val_ink, "topright")
            if state is not None:
                s = max(1, round(12 * k))
                box = pygame.Rect(vr.x - s - px(6) // 2, vr.centery - s // 2,
                                  s, s)
                mark(surface, box, rgb["state"][state], state, k)
                vr = vr.union(box)
            put(fit(style, left, px(size), vr.x - px(10) - x), (x, y), size,
                lab_ink)
            y += px(ROW)


def mark(surface, box, rgb, state, k):
    # LOOK EXCEPTION marking: the state's sign beside a number (297)
    if state == cbscan.DAMAGED:
        pygame.draw.polygon(surface, rgb, (box.midtop, box.bottomright,
                                           box.bottomleft))
    else:
        wd = max(1, round(3 * k))
        pygame.draw.line(surface, rgb, box.topleft, box.bottomright, wd)
        pygame.draw.line(surface, rgb, box.topright, box.bottomleft, wd)


def fit(style, t, size, room):
    from .cbscanview import fitted
    return fitted(style, t, size, room)


def wrap(style, text, size, room):
    """Words onto lines of `room` device px (a cut cell's whole text): a
    list cut after its commas, anything else between words."""
    text = str(text)
    sep = ", " if ", " in text else " "
    words = text.split(sep)
    out, line = [], ""
    for n, word in enumerate(words):
        word += sep.rstrip() if sep == ", " and n + 1 < len(words) else ""
        cand = f"{line} {word}" if line else word
        if line and style.render_text(cand, size, (255, 255, 255)
                                      ).get_width() > room:
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
    return speed_rows(title, card, m.speed_max, rgb) if key == "speed" \
        else value_rows(title, card, rgb, percent=key == "evasion")


def show(view, surface, style, scale, k, m, pointer, rgb, column):
    """The card of what is under the pointer (HD EXTENSION
    `scan_breakdown`): a value's at its one place right of COMBAT VALUES
    (work order 298), a cut cell's by rule 13 (297)."""
    values = view.rects.get("values") or {}
    for key, r in values.items():
        if not (m.cards and r.collidepoint(pointer)):
            continue
        cards = {kk: value_card(m, kk, rgb) for kk in values}
        # one rectangle for every row: as high as the highest card
        at = value_rect(view.window, view.boxes["values"],
                        int(max(c.height() for c in cards.values()) * k), k)
        tip = notch(at, r, k)
        draw(surface, style, scale, k, at, cards[key], rgb, tip,
             bounds=view.window)
        view.card = (key, at, tip)
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
