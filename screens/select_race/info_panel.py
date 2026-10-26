"""Select Race info panel — name, description, traits.

Split out of renderer.py: everything right of the portrait grid.
Colors and font sizes are shared with renderer.py so the skin's
"select_race" colors.json section covers both files.
"""
import re
import pygame

from core import lang
from core.hud import tables
from screens.select_race import racepanel

from screens.select_race.renderer import (
    COL_HEADING, COL_DESC, COL_RACE_TEXT, COL_HIGHLIGHT, COL_KEYWORD,
    TITLE_FONT, SUBTITLE_FONT,
)


#: The subtitle over a picture: lighter than `COL_SUBTITLE`, which was
#: chosen for the plain box.
SUBTITLE_ON_PICTURE = (214, 202, 250)


def render_race_name(surface, L, style, race, rect, fs_scale=1.0):
    """Render race name + subtitle in its own box."""
    rx, ry, rw, rh = rect

    # Race name
    tfs = L.font_size(int(TITLE_FONT * fs_scale))
    tfont = style.get_font(tfs)
    tx, ty = L.pos(rx, ry)
    t_surf = tfont.render(race["name"].upper(), True, COL_HEADING)
    # the name stands over the race's picture: a dark shadow keeps it
    # readable (HD EXTENSION `race_panel_pictures`, racepanel)
    shade = tfont.render(race["name"].upper(), True, (0, 0, 0))
    for dx, dy in ((2, 2), (-1, 2), (2, -1)):
        surface.blit(shade, (tx + dx, ty + dy))
    surface.blit(t_surf, (tx, ty))

    # Subtitle below name
    sub = race.get("subtitle", "")
    if sub:
        sfs = L.font_size(int(SUBTITLE_FONT * fs_scale))
        sfont = style.get_font(sfs)
        sx, sy = L.pos(rx, ry + 42)
        s_surf = sfont.render(sub.upper(), True, SUBTITLE_ON_PICTURE)
        s_shade = sfont.render(sub.upper(), True, (0, 0, 0))
        for dx, dy in ((2, 2), (-1, 2), (2, -1)):
            surface.blit(s_shade, (sx + dx, sy + dy))
        surface.blit(s_surf, (sx, sy))


def render_race_description(surface, L, style, race, rect,
                            scroll_offset=0, fs_scale=1.0):
    """Render scrollable description with markup in its own box."""
    rx, ry, rw, rh = rect
    # OrionLayer's own text ([select_race.screen]): translated
    # whole, before the markup is cut into words (work order 210 B2, Data's
    # decision 1; the German in assets/shared/lang/de.json)
    desc = lang.tr(race.get("description", ""))
    if not desc:
        return
    _render_description(surface, L, style, desc,
                        rx, ry, rw, rh, scroll_offset, fs_scale)


def render_race_traits(surface, L, style, race, rect, cache, find=None,
                       fs_scale=1.0, mouse=None):
    """Render RACE TRAITS section in its own box (racepanel: icons).
    Returns the card under `mouse`, if any (for the tooltip)."""
    return racepanel.render_traits(surface, L, style, race, rect, cache,
                                   find, fs_scale, mouse)


#: The description text, HD EXTENSION `race_panel_pictures`: a size up,
#: the light body colour and a tighter line (Data's mockup of 25 Oct 2026).
DESC_FONT = 20
DESC_LINE = 1.45
SCROLLBAR_W = 5           # reference px


def markup_lines(font, text, max_w, colour):
    """`text` with *highlight* and ~keyword~ markup cut into lines. A line
    is a list of words, a word a list of (fragment, colour): the full
    stop after a marked word stays on it ("*grow*." is one word, green
    "grow" and a plain "."). `colour(kind)` gives "plain", "highlight"
    and "keyword" their colour. One wrap for the description and the
    tooltip."""
    words, cur = [], []
    for p in re.split(r'(\*[^*]+\*|~[^~]+~)', text):
        if not p:
            continue
        if p.startswith('*') and p.endswith('*'):
            kind, body = "highlight", p[1:-1]
        elif p.startswith('~') and p.endswith('~'):
            kind, body = "keyword", p[1:-1]
        else:
            kind, body = "plain", p
        for i, chunk in enumerate(body.split(" ")):
            if i and cur:                 # a space ended the word
                words.append(cur)
                cur = []
            if chunk:
                cur.append((chunk, colour(kind)))
    if cur:
        words.append(cur)

    def width(word):
        return font.size("".join(f for f, _ in word))[0]

    lines, line, line_w = [], [], 0
    space = font.size(" ")[0]
    for word in words:
        w = width(word)
        if line and line_w + space + w > max_w:
            lines.append(line)
            line, line_w = [], 0
        line_w += (space if line else 0) + w
        line.append(word)
    if line:
        lines.append(line)
    return lines


def draw_line(surface, font, line, x, y):
    """One wrapped line, fragment by fragment."""
    space = font.size(" ")[0]
    for word in line:
        for frag, col in word:
            f = font.render(frag, True, col)
            surface.blit(f, (x, y))
            x += f.get_width()
        x += space


def _desc_colour(kind):
    return {"highlight": COL_HIGHLIGHT, "keyword": COL_KEYWORD}.get(
        kind, COL_DESC)


#: The race description's own look (Data's order of 25 Oct 2026; the
#: tooltip keeps DESC_LINE and `_desc_colour`): a line a fifth taller,
#: soft grey for plain text, 12 reference px of room inside the box, and
#: a half line between paragraphs.
RACE_LINE = 1.74
RACE_PAD = 12
PARA_GAP = 0.5
PARA_CHARS = 240
_SENTENCE_END = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9*~])')


def paragraphs(text):
    """`text` cut into paragraphs at its own sentence ends — the words
    are not touched, only where a paragraph begins. About one paragraph
    to `PARA_CHARS` characters, the sentences shared out evenly, so no
    paragraph is left with a single short sentence; a cut never falls
    inside a *marked* or ~marked~ run."""
    if "\n" in text:                      # paragraphs the text sets itself
        return [q for part in text.split("\n") if part.strip()
                for q in paragraphs(part)]
    n = max(1, round(len(text) / PARA_CHARS))
    sents = _SENTENCE_END.split(text)
    if n == 1 or len(sents) < 2:
        return [text]
    target = len(text) / n
    out, cur = [], ""
    for sent in sents:
        if cur and len(out) < n - 1 \
                and abs(len(cur) + 1 + len(sent) - target) > \
                abs(len(cur) - target) \
                and cur.count('*') % 2 == 0 and cur.count('~') % 2 == 0:
            out.append(cur)
            cur = sent
        else:
            cur = f"{cur} {sent}" if cur else sent
    out.append(cur)
    return out


def _race_colour(kind):
    return {"highlight": COL_HIGHLIGHT, "keyword": COL_KEYWORD}.get(
        kind, COL_RACE_TEXT)


def _description_layout(L, style, text, rect, fs_scale):
    """[(line, y offset)] from the text area's top, the content height,
    the view height, the font — all device px, all one computation for
    the drawing and for the wheel's limit."""
    fs = L.font_size(int(DESC_FONT * fs_scale))
    font = style.get_prop_font(fs)
    pad = int(RACE_PAD * L.scale)
    width = int(rect[2] * L.scale) - 2 * pad
    line_h = int(fs * RACE_LINE)
    out, y = [], 0
    for i, para in enumerate(paragraphs(text)):
        if i:
            y += int(line_h * PARA_GAP)
        for line in markup_lines(font, para, width, _race_colour):
            out.append((line, y))
            y += line_h
    return out, y, int(rect[3] * L.scale) - 2 * pad, font


def description_extent(L, style, race, rect, fs_scale=1.0):
    """(content height, view height) of a race's description in device
    px — what the wheel may scroll by."""
    text = lang.tr(race.get("description", ""))
    _lines, content, view, _font = _description_layout(L, style, text,
                                                       rect, fs_scale)
    return content, view


def _render_description(surface, L, style, text, rx, ry, rw, rh,
                        scroll_offset, fs_scale):
    """Scrollable description with *highlight* and ~keyword~ markup."""
    lines, content, view, font = _description_layout(
        L, style, text, (rx, ry, rw, rh), fs_scale)
    pad = int(RACE_PAD * L.scale)
    sx, sy = L.pos(rx, ry)
    tx, ty = sx + pad, sy + pad
    width = int(rw * L.scale) - 2 * pad
    line_h = font.get_height()

    old_clip = surface.get_clip()
    surface.set_clip(pygame.Rect(tx, ty, width, view))
    for line_words, y in lines:
        y = ty + y - scroll_offset
        if y + line_h > ty - line_h and y < ty + view + line_h:
            draw_line(surface, font, line_words, tx, y)
    surface.set_clip(old_clip)

    # A text that does not fit says so: the HUD's scroll bar at the box's
    # right edge
    if content > view:
        bw = max(6, int(SCROLLBAR_W * L.scale))
        tables.scrollbar(surface, (sx + int(rw * L.scale) - bw, ty, bw, view),
                         L.scale, first=scroll_offset, visible=view,
                         total=content)
