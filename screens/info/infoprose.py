"""The "How to?" article, set as a reading text — HD EXTENSION `howto_prose`.

The original prints a how-to's HELP.LBX body as one block of 7 pt words
across the whole box (info.cpp:1893-1906). At HD the box is wide and tall,
and one long paragraph in small type is hard to read (Data's mockup
"Sci-Fi Colonist Transfer Reference UI", 24 Nov 2026). HD sets the same
words as prose:

  * type a little over the page's reading size and a looser line, on a
    column no wider than a line can comfortably be (`COLUMN_EM`), centred
    in the box; the type steps down, never below the reading size, until the
    text fits above the picture's room (the caller shortens the box), and a
    text that still does not fit scrolls; the picture never moves for it;
  * from four sentences on the first is the lead-in, in a light tone; every
    other sentence is a step with a gold square before it; three sentences
    are steps only, one or two are one paragraph;
  * the game's own controls — the words the original writes in capitals
    (REFIT, COLONY SHIP, ACCEPT) — in gold.

Not one word of the game's is added, dropped or changed: `sentences` only
decides where a step ends (`check_words` is what the smoke check holds); the
words stay the engine's (`lang.verbatim` at the caller). A language without
capitals gets no gold, only the steps.

**INVENTION `howto_structure`.** A topic the original writes in two ways
and a closing remark — "Move Colonists" (HELP.LBX 214) — gets what Data's
mockup draws: a band with a symbol before each way, and a framed note for
the closing sentence. The band words and the note's label are HD's own
(`info.reference.band.<n>.<k>`, `info.reference.note`, "own" texts, in the
German table); the sentences stay the game's. `STRUCTURE` names the topic,
the sentence count it holds for, the sentence each band stands before and
the note's sentence: a text with another count (another language's split, a
mod's text) is set as every other, without bands.

`ProseBox` is `infobox.Box` for coloured words: it registers itself in
`screen._boxes` and its lines in `screen._drawn` as a `Box` does, so the wheel,
the scroll bar and the smoke check's "every line inside its box" hold; an item
that does not lie wholly inside the box is not drawn (the wheel brings it in).
"""
import re

import pygame

from core import fontscale
from core.hud import blocks as hud

from . import infobox

GOLD = (240, 176, 64)
LEAD = (125, 210, 235)
WHITE = (235, 240, 245)
#: type size over the page's reading size; leading
SIZE_UP = 1.15
LINE_GAP = 1.4
#: the longest line, in ems of the type size
COLUMN_EM = 66
#: three sentences or more are set as steps
SPLIT_FROM = 3
#: a lead-in is told from four sentences on
LEAD_FROM = 4

#: topic record -> {"sentences": the count it holds for, "bands": {sentence
#: the band stands before: (text key, default words, icon name)}, "note":
#: the closing sentence}. HD's own words are "own" texts (infotexts).
STRUCTURE = {
    214: {"sentences": 8,
          "bands": {1: ("info.reference.band.214.1",
                        "Method 1 – Transfer Colonists", "people"),
                    5: ("info.reference.band.214.2",
                        "Method 2 – Via Galaxy Map", "galaxy")},
          "note": 7},
}
NOTE_KEY = ("info.reference.note", "Note:")

_END = re.compile(r"(?<=[.!?])\s+")
_PUNCT = ".,;:!?()\"'"


def sentences(body):
    """The body's sentences, in order. A piece that starts with a lowercase
    letter ("e.g. ...") belongs to the sentence before it."""
    flat = " ".join((body or "").split())
    out = []
    for piece in _END.split(flat):
        if not piece:
            continue
        if out and piece[0].islower():
            out[-1] += " " + piece
        else:
            out.append(piece)
    return out


def structure(record, T):
    """The topic's bands and note with their words resolved through `T`
    (outside `lang.verbatim`: the words are HD's), or None."""
    spec = STRUCTURE.get(record)
    if spec is None:
        return None
    bands = {}
    for idx, (key, default, icon) in spec["bands"].items():
        words_ = T(key, default)
        if not words_:
            return None
        bands[idx] = (words_, icon)
    label = T(NOTE_KEY[0], NOTE_KEY[1])
    return {"sentences": spec["sentences"], "bands": bands,
            "note": (spec["note"], label or NOTE_KEY[1])}


def items(body, struct=None):
    """The body as items: (kind, text, extra) — kind "plain", "lead",
    "step", "band" (text = the band's words, extra = icon) or "note"
    (extra = the label)."""
    parts = [p for p in re.split(r"\n\s*\n", body or "") if p.strip()]
    if len(parts) > 1:
        return [("plain", " ".join(p.split()), None) for p in parts]
    found = sentences(body)
    if not found:
        return []
    if len(found) < SPLIT_FROM:
        return [("plain", " ".join(found), None)]
    out = []
    use = struct if struct and struct["sentences"] == len(found) else None
    for i, s in enumerate(found):
        if use and i in use["bands"]:
            out.append(("band",) + use["bands"][i])
        if use and i == use["note"][0]:
            out.append(("note", s, use["note"][1]))
        elif i == 0 and len(found) >= LEAD_FROM:
            out.append(("lead", s, None))
        else:
            out.append(("step", s, None))
    return out


def _is_control(word):
    core = word.strip(_PUNCT)
    letters = [c for c in core if c.isalpha()]
    return len(letters) >= 2 and core.upper() == core and any(
        c.isupper() for c in core)


def words(text):
    """(word, gold) pairs: the capitalised words are controls; a lone
    capital letter or a number is not."""
    return [(w, _is_control(w)) for w in text.split()]


def check_words(body, struct=None):
    """The body's words with nothing added or lost — what its sentences
    carry, for the smoke check."""
    got = " ".join(w for kind, t, _x in items(body, struct)
                   if kind != "band" for w, _g in words(t))
    return " ".join(body.split()) == got


_widths = {}
_cache_style = None


def paint_band(surface, area):
    """The gold band under a heading or a chosen row: gold fading to the
    right between two thin gold rules (Data's mockup, 24 Nov)."""
    band = pygame.Surface(area.size, pygame.SRCALPHA)
    for x in range(area.w):                   # gold fading to the right
        a = int(120 * (1 - x / area.w) ** 0.6)
        # LOOK EXCEPTION marking: the band's gold gradient and rules, Data's mockup (24 Nov)
        band.fill((150, 100, 25, a), (x, 0, 1, area.h))
    # LOOK EXCEPTION marking: the band's gold rules, Data's mockup (24 Nov)
    pygame.draw.line(band, GOLD + (150,), (0, 0), (area.w, 0))
    # LOOK EXCEPTION marking: the band's gold rules, Data's mockup (24 Nov)
    pygame.draw.line(band, GOLD + (150,), (0, area.h - 1),
                     (area.w, area.h - 1))
    surface.blit(band, area.topleft)


def article_items(title, body, icon=None):
    """A category article as items: the topic's title as a band (with the
    category's symbol) and the body's paragraphs, plain. A body with blank
    lines keeps its paragraphs, else it is one."""
    lines = infobox.paragraphs(body or "")
    paras, cur = [], []
    for line in lines:
        if line.strip():
            cur.append(line.strip())
        elif cur:
            paras.append(" ".join(cur))
            cur = []
    if cur:
        paras.append(" ".join(cur))
    out = [("band", title, icon)] if title else []
    return out + [("plain", p, None) for p in paras]


class ProseBox(infobox.Box):
    """The article: items of coloured words in one centred column."""

    def __init__(self, key, rect, body, size, colour, floor=None, struct=None,
                 icons=None, given=None):
        super().__init__(key, rect, body, size, colour, "left", LINE_GAP)
        self.floor = floor or size
        self.items = given if given is not None else items(body, struct)
        self.icons = icons or (lambda name: None)

    def _w(self, style, text):
        global _cache_style
        if _cache_style is not style:
            _widths.clear()
            _cache_style = style
        k = (self.size, text)
        if k not in _widths:
            _widths[k] = style.render_text(
                text, self.size, (255, 255, 255)).get_width()
        return _widths[k]

    def _wrap(self, style, pairs, width, space):
        """Lines of (word, gold) pairs of at most `width`; a word wider
        than the line is broken by characters."""
        out, line, used = [], [], 0
        for word, gold in pairs:
            while self._w(style, word) > width and len(word) > 1:
                k = len(word) - 1
                while k > 1 and self._w(style, word[:k]) > width:
                    k -= 1
                if line:
                    out.append(line)
                    line, used = [], 0
                out.append([(word[:k], gold)])
                word = word[k:]
            w = self._w(style, word)
            if line and used + space + w > width:
                out.append(line)
                line, used = [], 0
            used += (space if line else 0) + w
            line.append((word, gold))
        if line:
            out.append(line)
        return out

    def layout(self, style):
        top = self.size
        while True:
            self.size = top
            self._set(style, self.inner_for())
            if self.content_h <= self.inner.h or top <= self.floor:
                break
            top -= 1
        if self.content_h > self.inner.h:      # scrolls: the scroll bar's room
            self.inner.w -= max(6, self.size // 2) + 2
            self._set(style, self.inner)
        self.overflow = max(0, self.content_h - self.inner.h)
        self.text_end = self.inner.y + self.content_h
        return self

    def inner_for(self):
        pad = max(2, self.size // 3)
        return self.rect.inflate(-2 * pad, -2 * pad)

    def _set(self, style, inner):
        """Wrap every item and give it its y (from the inner's top) and
        height; `content_h` is the sum."""
        self.inner = inner
        self.step = int(self.size * fontscale.factor() * self.line_gap)
        self.col = min(self.inner.w, self.size * COLUMN_EM)
        space = max(2, self._w(style, "a a") - self._w(style, "aa"))
        self.space = space
        self.indent = int(self.size * 1.3)
        self.band_h = int(self.step * 1.7)
        self.pad = int(self.step * 0.4)
        step, y, prev, placed = self.step, 0, None, []
        for kind, text, extra in self.items:
            if kind == "band":
                lines, h = [], self.band_h
                before = step * 0.7 if prev else 0
            elif kind == "note":
                label = [(w, True) for w in extra.split()]
                width = self.col - 2 * self.pad - self.band_h
                lines = self._wrap(style, label + words(text), width, space)
                h = len(lines) * step + 2 * self.pad
                before = step * 0.6
            elif kind == "step":
                lines = self._wrap(style, words(text), self.col - self.indent,
                                   space)
                h = len(lines) * step
                before = step * (0.15 if prev in ("step", "band") else 0.5)
            else:                              # lead, plain
                lines = self._wrap(style, words(text), self.col, space)
                h = len(lines) * step
                # an article's paragraphs stand clear of its band and of
                # each other (Data, 24 Nov: not stuck to the heading)
                before = 0 if prev is None else step * (
                    1.0 if prev == "band" else 0.7)
            if kind == "band":
                before = step * 0.7 if prev not in (None, "band") else 0
            y += int(before)
            placed.append((kind, text, extra, lines, y, h))
            y += h
            if kind == "band":
                y += int(step * 0.25)
            prev = kind
        self.placed = placed
        self.content_h = y

    def draw(self, surface, screen):
        style = screen.style
        self.layout(style)
        offset = max(0, min(screen._scroll.get(self.key, 0), self.overflow))
        screen._scroll[self.key] = offset
        previous = surface.get_clip()
        surface.set_clip(self.inner)
        x0 = self.inner.centerx - self.col // 2
        for kind, text, extra, lines, y, h in self.placed:
            area = pygame.Rect(x0, self.inner.y - offset + y, self.col, h)
            whole = self.inner.contains(area)
            if whole:
                self._item(surface, style, kind, text, extra, area)
            tx = x0
            ty = area.y
            if kind == "step":
                tx += self.indent
            elif kind == "note":
                tx += self.pad + self.band_h
                ty += self.pad + (self.step - self.size) // 3
            elif kind == "band":
                continue
            for line in lines:
                x = tx
                for word, gold in line:
                    img = style.render_text(
                        word, self.size, GOLD if gold else (
                            LEAD if kind == "lead" else self.colour))
                    r = pygame.Rect(x, ty, img.get_width(), img.get_height())
                    if whole:
                        surface.blit(img, r.topleft)
                    screen._drawn.append((r, self.inner, whole))
                    x += img.get_width() + self.space
                ty += self.step
        surface.set_clip(previous)
        if self.overflow:
            bar = pygame.Rect(self.inner.right + 2, self.inner.y,
                              max(6, self.size // 2), self.inner.h)
            hud.scrollbar(surface, bar, screen.layout.scale, offset,
                          self.inner.h, self.content_h)
        screen._boxes[self.key] = self

    def _item(self, surface, style, kind, text, extra, area):
        """What an item draws besides its words: a step's square, a
        band, a note's frame and mark."""
        if kind == "step":
            s = max(4, self.size // 3)
            # LOOK EXCEPTION marking: a step's gold square, the controls' gold, Data's mockup (24 Nov)
            pygame.draw.rect(surface, GOLD, (
                area.x + self.indent // 3, area.y + (self.step - s) // 2 - self.size // 8,
                s, s))
        elif kind == "band":
            paint_band(surface, area)
            icon = self.icons(extra)
            left = area.x + 10
            if icon is not None:
                k = (area.h - 8) / icon.get_height()
                size = (max(1, round(icon.get_width() * k)), area.h - 8)
                surface.blit(pygame.transform.smoothscale(icon, size),
                             (area.x + 8, area.y + 4))
                left = area.x + 8 + size[0] + 12
            img = style.render_text(text, self.size, WHITE)
            surface.blit(img, (left, area.centery - img.get_height() // 2))
        elif kind == "note":
            box = pygame.Surface(area.size, pygame.SRCALPHA)
            # LOOK EXCEPTION marking: the note's gold-tinted frame, Data's mockup (24 Nov)
            pygame.draw.rect(box, (120, 80, 20, 60), box.get_rect(),
                             border_radius=6)
            # LOOK EXCEPTION marking: the note's gold-tinted frame, Data's mockup (24 Nov)
            pygame.draw.rect(box, GOLD + (170,), box.get_rect(), 1,
                             border_radius=6)
            surface.blit(box, area.topleft)
            r = self.band_h // 2 - 2
            c = (area.x + self.pad // 2 + self.band_h // 2, area.centery)
            # LOOK EXCEPTION marking: the note's gold ring round the mark, Data's mockup (24 Nov)
            pygame.draw.circle(surface, GOLD, c, r, 2)
            mark = style.render_text("!", self.size, GOLD)
            surface.blit(mark, (c[0] - mark.get_width() // 2,
                                c[1] - mark.get_height() // 2))
