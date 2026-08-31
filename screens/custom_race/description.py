"""Custom Race description panel.

Shows the trait the player last clicked: its name as a heading
plus a wrapped body text. Uses the same markup convention as the
Select Race descriptions:

    *text*   highlight (green)
    ~text~   keyword (blue)

Trait texts live in traits.json (mod-overridable), so this file
contains no game content — only layout.
"""
import re
import pygame
from screens.custom_race.renderer import _c

COL_HEADING  = _c("desc_heading",  (198, 124, 246))
COL_BODY     = _c("desc_body",     (206, 212, 226))
COL_HINT     = _c("desc_hint",     (120, 132, 160))
COL_HIGHLIGHT = _c("highlight",    (100, 210, 140))
COL_KEYWORD  = _c("keyword",       (140, 185, 240))

HEAD_FONT = 26
BODY_FONT = 17
LINE_GAP = 7
PANEL_INSET = 22
HEAD_GAP = 16
BULLET_INDENT = 18

_TOKEN = re.compile(r"(\*[^*]+\*|~[^~]+~)")


def _words(text):
    """Split text into words, each a list of (fragment, color).

    A word can span several markup runs so that punctuation
    directly after a marked-up run stays attached: "*grow*."
    renders as one word, green "grow" plus a normal ".".
    """
    words = []
    current = []
    for part in _TOKEN.split(text):
        if not part:
            continue
        if part.startswith("*") and part.endswith("*"):
            color, body = COL_HIGHLIGHT, part[1:-1]
        elif part.startswith("~") and part.endswith("~"):
            color, body = COL_KEYWORD, part[1:-1]
        else:
            color, body = COL_BODY, part
        # Split on spaces but keep word continuity across runs
        chunks = body.split(" ")
        for i, chunk in enumerate(chunks):
            if i > 0:                 # a space ended the previous word
                if current:
                    words.append(current)
                    current = []
            if chunk:
                current.append((chunk, color))
    if current:
        words.append(current)
    return words


def render_description_panel(surface, L, style, entry, rect,
                             fs=1.0, scroll=0):
    """Draw heading + wrapped body for the selected trait.

    entry: dict with "name" and "description" (or None).
    """
    rx, ry, rw, rh = rect
    ix = rx + PANEL_INSET
    iw = rw - 2 * PANEL_INSET
    body_font = style.get_prop_font(L.font_size(int(BODY_FONT * fs)))

    if not entry:
        hx, hy = L.pos(ix, ry)
        hint = body_font.render("Select a trait to see its details.",
                                True, COL_HINT)
        surface.blit(hint, (hx, hy))
        return

    clip_x, clip_y = L.pos(rx, ry)
    clip_w, clip_h = L.size(rw, rh)
    prev_clip = surface.get_clip()
    surface.set_clip(pygame.Rect(clip_x, clip_y, clip_w, clip_h))

    y = ry - scroll
    head_font = style.get_font(L.font_size(int(HEAD_FONT * fs)))
    hx, hy = L.pos(ix, y)
    head = head_font.render(entry.get("name", "").upper(), True,
                            COL_HEADING)
    surface.blit(head, (hx, hy))
    y += HEAD_FONT * fs + HEAD_GAP

    max_w = int(iw * L.scale)
    space_w = body_font.size(" ")[0]
    line_h = (BODY_FONT + LINE_GAP) * fs

    for para in entry.get("description", "").split("\n"):
        if not para.strip():
            y += line_h * 0.6
            continue
        bullet = para.lstrip().startswith("- ")
        indent = BULLET_INDENT if bullet else 0
        if bullet:
            para = para.lstrip()[2:]
            bx, by = L.pos(ix + 4, y)
            surface.blit(body_font.render("\u2022", True, COL_BODY),
                         (bx, by))
        px, py = L.pos(ix + indent, y)
        cursor = 0
        for word in _words(para):
            surfs = [body_font.render(frag, True, col)
                     for frag, col in word]
            word_w = sum(s.get_width() for s in surfs)
            if cursor and cursor + word_w > max_w - indent * L.scale:
                y += line_h
                px, py = L.pos(ix + indent, y)
                cursor = 0
            for s in surfs:
                surface.blit(s, (px + cursor, py))
                cursor += s.get_width()
            cursor += space_w
        y += line_h

    surface.set_clip(prev_clip)


def description_height(entry, L, style, rect, fs=1.0):
    """Total content height in reference units (for scrolling)."""
    if not entry:
        return 0
    rx, ry, rw, rh = rect
    iw = rw - 2 * PANEL_INSET
    body_font = style.get_prop_font(L.font_size(int(BODY_FONT * fs)))
    max_w = int(iw * L.scale)
    space_w = body_font.size(" ")[0]
    line_h = (BODY_FONT + LINE_GAP) * fs
    h = HEAD_FONT * fs + HEAD_GAP
    for para in entry.get("description", "").split("\n"):
        if not para.strip():
            h += line_h * 0.6
            continue
        indent = BULLET_INDENT if para.lstrip().startswith("- ") else 0
        if indent:
            para = para.lstrip()[2:]
        cursor = 0
        lines = 1
        for word in _words(para):
            w = sum(body_font.size(frag)[0] for frag, _ in word)
            if cursor and cursor + w > max_w - indent * L.scale:
                lines += 1
                cursor = 0
            cursor += w + space_w
        h += lines * line_h
    return h
