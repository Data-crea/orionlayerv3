"""The Turn Summary's panel, ranked by importance — work order 384.

HD EXTENSION `summary_importance` (Data's mockup of 10 November 2026): the
messages the game reports (`core.turnsummary` groups and ranks them) stand
in a framed list under a header per category — the category's picture, its
name, and on the right how many it holds. A row has the same columns
everywhere: a warning triangle (red, yellow, green), the PLACE (a colony
message's planet), a rule, the SUMMARY and on the right the DETAIL (what
starvation costs, the building scrapped and its refund). A message that
names no colony keeps the game's own sentence over the place and summary
columns, wrapped to two lines when it is long. The list SCROLLS
(HD EXTENSION `summary_scroll`): the rows keep Data's height whatever the
count, the wheel or a click on the track moves the page. The buttons are the
popup's own (`core.turnpopup`), with the mockup's golden rules either side
of them. Every row keeps the action the plain list gave it (a colony message
jumps to its colony).

The pictures are Data's and ship in no tree: `ICONS` are slots of the
player's mod folder (`core.usermod.SLOTS`), and a row without its picture
is drawn without it, a header the same.
"""
import contextlib
import os
import time

import pygame

from core import lang
from core import mouse as mouse_input
from core import turnsummary as ts
from core.hud import blocks as hud
from core.hud import tables as hudtables
from core.hud import text as hudtext

FOLDER = "assets/shared/turnpopup/"
#: The mod folder's pictures (`popups/<name>.png`), by what they show.
ICONS = {ts.RED: "summary_warning_red.png",
         ts.YELLOW: "summary_warning_yellow.png",
         ts.GREEN: "summary_warning_green.png",
         ts.COLONY: "summary_colony_events.png",
         "rule_left": "summary_divider_left.png",
         "rule_right": "summary_divider_right.png"}
SLOTS = tuple(FOLDER + n for n in ICONS.values())

#: The text colour of a severity's detail, read off the pictures' own
#: red, gold and green.
SIGNAL = {ts.RED: (255, 112, 84), ts.YELLOW: (240, 196, 72),
          ts.GREEN: (118, 214, 96)}

REF_W, REF_PAD, REF_FONT, REF_TITLE_FONT = 1100, 30, 27, 38
REF_ROW, REF_HEAD, REF_BAR = 40, 46, 16
_cache = {}


_stamps = {}                    # key -> (checked at, path, mtime)


def _stamp(key):
    """The picture's resolved path and mtime, looked at once a second (the
    player may swap the file; a stat per row per frame is too much)."""
    now = time.monotonic()
    got = _stamps.get(key)
    if got is not None and now - got[0] < 1.0:
        return got[1], got[2]
    from core import resources
    path = resources.res.resolve(FOLDER + ICONS[key])
    try:
        stamp = os.stat(path).st_mtime_ns if path else None
    except OSError:
        path, stamp = None, None
    _stamps[key] = (now, path, stamp)
    return path, stamp


def icon(key, h, w=None):
    """The mod folder's picture for `key` smoothly scaled to `h` high, its
    proportion kept (or to `w` wide when given), or None (absent or
    unreadable)."""
    path, stamp = _stamp(key)
    if not path or h <= 0:
        return None
    cached = _cache.get((path, stamp, h, w))
    if cached is not None:
        return cached or None
    try:
        src = pygame.image.load(path)
        src = src.convert_alpha() if pygame.display.get_surface() else src
        out = pygame.transform.smoothscale(
            src, (w or max(1, round(src.get_width() * h / src.get_height())),
                  h))
    except (pygame.error, OSError, ValueError):
        out = None
    if len(_cache) > 48:
        _cache.clear()
    _cache[(path, stamp, h, w)] = out if out is not None else False
    return out


def _distinct(rows, cat):
    """How many the header counts: colonies for the colony group (a colony
    with two messages is one colony), messages for the others."""
    if cat != ts.COLONY:
        return len(rows)
    return len({r["name"] or r["order"] for r in rows})


def _count_words(cat, n, words):
    if cat == ts.COLONY:
        return words["sum_colony_one"] if n == 1 else \
            words["sum_colonies"].format(n=n)
    return words["sum_event_one"] if n == 1 else \
        words["sum_events"].format(n=n)


def _fit(style, text, size, width, colour):
    """One line of `text`, shrunk to `width` when it is longer (never cut,
    never past its column: the text-fit rule for a one-line label)."""
    img = style.render_text(text, size, colour)
    if img.get_width() > width > 0:
        img = pygame.transform.smoothscale(
            img, (width, max(1, img.get_height() * width // img.get_width())))
    return img


def _text(style, text, size, width, colour, row_h):
    """The summary column's text as one surface: one line when it fits, else
    two lines in a smaller size, else shrunk to fit — it always stands in
    its own row."""
    img = style.render_text(text, size, colour)
    if img.get_width() <= width:
        return img
    from core.textfit import wrap_rendered
    lines = wrap_rendered(style, text, max(9, int(size * 0.8)), width, colour)
    if len(lines) == 2 and lines[0].get_height() * 2 <= row_h:
        out = pygame.Surface((width, lines[0].get_height() * 2),
                             pygame.SRCALPHA)
        for n, line in enumerate(lines):
            out.blit(line, (0, n * line.get_height()))
        return out
    return _fit(style, text, size, width, colour)


def draw(surface, style, c, words, buttons_row):
    """The panel for `c` (the popup's content with its `summary` rows);
    `buttons_row(surface, panel, s, pad)` draws the buttons and returns
    their `[(rect, action)]`. Returns `(rects, button_actions)` like
    `turnpopup.draw`. The list's scroll state goes in and out through `c`:
    `c["scroll"]` is the offset in px, `c["scroll_info"]` is set to
    `{"max", "track", "row", "page", "total", "view"}` (None when the list
    fits) for the view and the overlay."""
    win_w, win_h = surface.get_size()
    s = win_h / 1080
    pad = int(REF_PAD * s)
    w = min(int(REF_W * s), win_w - 2 * pad)
    inner = w - 2 * pad
    size = max(10, int(REF_FONT * s))
    colour = tuple(hudtext.colour("value")[:3])
    label_colour = tuple(hudtext.colour("label")[:3])
    groups = ts.groups(c["summary"])
    title = style.render_text(c["title"], max(12, int(REF_TITLE_FONT * s)),
                              tuple(hudtext.colour("title")[:3]))
    bh = int(58 * s)
    head_h, row_h = int(REF_HEAD * s), int(REF_ROW * s)
    frame = pad // 2
    content_h = sum(head_h + len(g[1]) * row_h for g in groups)
    empty = None
    if not groups:               # everything switched off, or nothing came
        hid = c.get("summary_hidden", 0)
        empty = style.render_text(
            words["sum_hidden"].format(n=hid) if hid else words["sum_empty"],
            size, label_colour)
        content_h = head_h * 2
    # the list takes what the content needs, the window's height at most
    room = win_h - 2 * pad - (pad + title.get_height() + pad // 2 + pad +
                              bh + pad)
    list_h = min(room, content_h + frame)
    h = pad + title.get_height() + pad // 2 + list_h + pad + bh + pad
    panel = pygame.Rect((win_w - w) // 2, (win_h - h) // 2, w, h)
    hud.popup(surface, panel, s)
    y = panel.y + pad
    surface.blit(title, title.get_rect(midtop=(panel.centerx, y)))
    y += title.get_height() + pad // 2
    box = pygame.Rect(panel.x + pad, y, inner, list_h)
    hud.panel(surface, box, s, lit=False, dense=True)
    view = box.inflate(-pad, -frame)             # where rows may show
    max_scroll = max(0, content_h - view.h)
    scroll = min(max(0, int(c.get("scroll", 0))), max_scroll)
    bar_w = max(6, int(REF_BAR * s)) if max_scroll else 0
    track = None
    if max_scroll:
        track = pygame.Rect(view.right - bar_w, view.y, bar_w, view.h)
        hudtables.scrollbar(surface, track, s, first=scroll,
                            visible=view.h, total=content_h)
    c["scroll_info"] = {"max": max_scroll, "track": track, "row": row_h,
                        "page": view.h, "total": content_h,
                        "view": view} if max_scroll else None
    rects = []
    mouse = mouse_input.pos()
    rule = tuple(int(v * 0.35) for v in label_colour)
    left, right = view.x, view.right - (bar_w + pad // 4 if bar_w else 0)
    name_w = int((right - left) * 0.22)
    sep_x = left + int(row_h * 1.1) + name_w
    clip = surface.get_clip()
    surface.set_clip(view.clip(clip))
    y = view.y - scroll
    if empty is not None:
        surface.blit(empty, empty.get_rect(center=(view.centerx,
                                                   view.y + head_h)))
    for cat, rows in groups:
        if y + head_h > view.y and y < view.bottom:
            label = words.get("sum_" + cat)
            if len(groups) == 1 and rows[0]["severity"] is None:
                label = words["sum_messages"]
            pic = icon(cat, int(head_h * 0.8)) if cat in ICONS else None
            x = left
            if pic is not None:
                surface.blit(pic, pic.get_rect(midleft=(x, y + head_h // 2)))
                x += pic.get_width() + pad // 2
            head = style.render_text(label.upper(), size,
                                     tuple(hudtext.colour("title")[:3]))
            surface.blit(head, head.get_rect(midleft=(x, y + head_h // 2)))
            count = _fit(style, _count_words(cat, _distinct(rows, cat),
                                             words), size,
                         (right - left) // 3, label_colour)
            surface.blit(count, count.get_rect(midright=(right,
                                                         y + head_h // 2)))
        y += head_h
        for r in rows:
            if y + row_h <= view.y or y >= view.bottom:
                y += row_h
                continue
            rect = pygame.Rect(left, y, right - left, row_h)
            if r["action"] is not None and rect.collidepoint(mouse) and \
                    view.collidepoint(mouse):
                hud.panel(surface, rect, s, lit=True, dense=True)
            mid = y + row_h // 2
            pic = icon(r["severity"], int(row_h * 0.74)) \
                if r["severity"] is not None else None
            x = left + pad // 4
            if pic is not None:
                surface.blit(pic, pic.get_rect(midleft=(x, mid)))
            x = left + int(row_h * 1.1)
            if r["name"]:
                with lang.verbatim():       # a planet's name is the game's
                    nm = _fit(style, r["name"], size, name_w - pad // 2,
                              colour)
                surface.blit(nm, nm.get_rect(midleft=(x, mid)))
                pygame.draw.line(surface, label_colour,
                                 (sep_x, y + row_h // 5),
                                 (sep_x, y + row_h - row_h // 5))
                x = sep_x + pad // 2
            detail = None
            if r.get("detail"):
                with (lang.verbatim() if r["detail"][2]
                      else contextlib.nullcontext()):
                    detail = _fit(
                        style, r["detail"][0], size, (right - x) // 2,
                        SIGNAL[r["detail"][1]] if r["detail"][1] is not None
                        else colour)
            room_w = right - x - (detail.get_width() + pad if detail else 0)
            # the kind's label is OrionLayer's word; the game's sentence is
            # not translated (`lang.verbatim`)
            with (lang.verbatim() if r.get("verbatim", True)
                  else contextlib.nullcontext()):
                body = _text(style, r["text"], size, room_w, colour, row_h)
            surface.blit(body, body.get_rect(midleft=(x, mid)))
            if detail is not None:
                surface.blit(detail, detail.get_rect(midright=(right, mid)))
            pygame.draw.line(surface, rule, (left, y + row_h - 1),
                             (right, y + row_h - 1))
            visible = rect.clip(view)
            if visible.h > 0:
                rects.append((visible, r["action"]))
            y += row_h
    surface.set_clip(clip)
    out, acts = buttons_row(surface, panel, s, pad)
    for key, side in (("rule_left", "l"), ("rule_right", "r")):
        pic = icon(key, int(bh * 0.5))
        if pic is None or not out:
            continue
        first_btn, last_btn = out[0][0], out[-1][0]
        gap = (first_btn.x - box.x if side == "l"
               else box.right - last_btn.right) - pad
        if gap > pad:
            pic = icon(key, pic.get_height(), min(gap, pic.get_width()))
            at = (first_btn.x - pad - pic.get_width() if side == "l"
                  else last_btn.right + pad)
            surface.blit(pic, (at, first_btn.centery - pic.get_height() // 2))
    return rects + out, acts
