"""The scan's card — work order 297 part B (Data, 18 Oct 2026).

HD EXTENSION `scan_breakdown` (its rules: `cbscanparts`): in the Detailed
scan a combat value under the pointer shows its parts in a card — this
ship's systems one by one, the fixed bonuses as one Base line with its
sources under it in grey, what other units give in their own tint and
named, a total at the end; a value whose parts do not make the engine's
sum shows the sum and "Breakdown not available" alone. The same card
shows a cell's whole text where the cell rule cut it, and what a "+n more"
stands for. Each row with a card wears an info sign (drawn: the font need
not have the glyph); no hint text.

Placement (Data's rule 13): inside the scan window, never over the
COMBAT VALUES box or a box that lists the systems the card names — a
value's card stands in the left column, beside its row.

Geometry in reference px, scaled by the window's `k` as the scan.
"""
import pygame

from core.hud import blocks as hud
from core.hud import text as hudtext
from . import cbscan, cbscanparts as cp

ROW, SUB, PAD = 28, 22, 16
#: what another unit gives, in its own tint (Data: "a distinct tint")
FLEET_TINT = (120, 190, 235)
GREY = (130, 136, 150)
GROUND = (10, 13, 20)
NOT_AVAILABLE = "Breakdown not available"


def signed(v):
    return f"{int(v):+d}"


class Rows:
    """A card's content: (kind, left, right, colour, size) lines."""

    def __init__(self, title):
        self.title, self.lines = title, []

    def add(self, kind, left, right=None, rgb=None, size=20, state=None):
        self.lines.append((kind, left, right, rgb, size, state))

    def height(self):
        h = 50
        for kind, *_r in self.lines:
            h += {"sub": SUB, "note": SUB, "rule": 12}.get(kind, ROW)
        return h + PAD // 2


def value_rows(title, card, rgb, percent=False):
    """The rows of a combat value's card (`cbscanparts.Card`)."""
    tot = f"{card.total}%" if percent else signed(card.total)
    rows = Rows(f"{title}  {tot}")
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
    rows.add("line", "Total", tot, (rgb["label"], rgb["value"]), 20)
    return rows


def speed_rows(title, card, top, rgb):
    rows = Rows(f"{title}  {card.total} / {top}")
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
             (rgb["label"], rgb["value"]), 20)
    rows.add("line", "Maximum", str(top), (rgb["label"], rgb["value"]), 20)
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


def draw(surface, style, scale, k, rect, rows, rgb):
    """The card in `rect`: the HUD popup's look, its rows top down."""
    px = lambda n: max(9, int(n * k))
    # LOOK EXCEPTION marking: the card's own ground, opaque — with the glass
    # on (work order 253) a panel lets what is under it through, and a card
    # over the scan's text must hide that text
    pygame.draw.rect(surface, GROUND, rect.inflate(-2, -2))
    hud.popup(surface, rect, scale)
    x, y = rect.x + px(PAD), rect.y + px(12)
    right = rect.right - px(PAD)

    def put(t, at, size, ink, anchor="topleft"):
        img = style.render_text(str(t), px(size), ink[:3])
        r = img.get_rect(**{anchor: at})
        surface.blit(img, r)
        return r

    if rows.title:
        put(rows.title, (x, y), 22, rgb["value"])
        y += px(38)
    for kind, left, right_t, ink, size, state in rows.lines:
        if kind == "rule":
            pygame.draw.line(surface, GREY, (x, y + px(4)), (right, y + px(4)),
                             max(1, round(k)))
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


def show(view, surface, style, scale, k, m, pointer, rgb, column):
    """The card of what is under the pointer (HD EXTENSION
    `scan_breakdown`), placed by rule 13: inside the window, never over
    COMBAT VALUES, SPECIAL SYSTEMS or HULL AND SYSTEMS."""
    avoid = [view.boxes[b] for b in ("values", "specials", "hull")]
    for key, r in (view.rects.get("values") or {}).items():
        if not (m.cards and r.collidepoint(pointer)):
            continue
        title = {"attack": m.words["beam_attack"],
                 "defense": m.words["beam_defense"],
                 "evasion": m.words["missile_evasion"],
                 "speed": "Combat speed"}[key].upper()
        card = m.cards[key]
        rows = speed_rows(title, card, m.speed_max, rgb) \
            if key == "speed" else value_rows(
                title, card, rgb, percent=key == "evasion")
        size = (column.w, int(rows.height() * k))
        at = place(size, r, view.window, avoid,
                              column=(column.x, column.right))
        if at is not None:
            draw(surface, style, scale, k, at, rows, rgb)
            view.card = (key, at)
        return
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
            draw(surface, style, scale, k, at, rows, rgb)
            view.card = ("cell", at, r)
        return
