"""The Race Statistics cards — HD EXTENSION `race_cards`.

The original prints a race as plain words in a box: its name, "(ELIMINATED)"
and the specials one per line (info.cpp:1683-1751). HD (Data's mockup "Neon
Sci-Fi Race Statistics HUD", 24 Nov 2026) draws a card: the race's symbol
and its name in its colour over a gold rule, a red ELIMINATED tag at the
head's right end for a race that is out, the specials each with the icon
Select Race draws for it and its value in green (a bonus) or red (a
penalty), and the race's portrait at the card's right, faded into the card
at its left edge — grey and darker for a race that is out.

THE PICTURES are the player's own: the portraits and icons are Select Race's
(`screens/select_race/assets/portraits|icons`, found through the mod folder,
the tree and the base pack like every picture); the symbol is
`screens/info/assets/icons/race_<name>.png` beside the Reference's icons, and
a race without one wears the flag symbol. A missing picture is left out, the
card keeps its words.

The words stay the engine's (`lang.verbatim` at the caller, the race's name)
or the game's translated trait names; ELIMINATED is HD's own ("own" text
`info.races.eliminated_tag`, in the German table). Which line carries which
help (right click) is `Card.rows`, read by `InfoScreen.trait_help_at`.
"""
import json
import os

import pygame

from . import inforef

GOLD = (240, 176, 64)
GREEN = (120, 225, 110)
RED = (240, 85, 70)
TAG_RED = (210, 60, 50)
OUT_DIM = 0.5                 # a race that is out: its portrait's brightness
PORTRAIT_SHARE = 0.58         # of the card's width, from its right edge
FADE = 0.7                    # of the portrait's width: transparent -> solid

_cache = {}
_names = None
#: Pictures kept; a portrait is a whole card, one per size the window passes
#: through (WO 426).
_CACHE_KEEP = 96


def _find(rel):
    from core import resources
    parts = rel.split("/")
    # every root the resolver knows, in its order and with its switches (the
    # mod folder off, `mods/<name>/`): decision 16, WO 426
    for root in tuple(resources.res.roots()):
        if root:
            path = os.path.join(root, *parts)
            if os.path.isfile(path):
                return path
    return None


def _load(rel):
    if rel not in _cache:
        path = _find(rel)
        try:
            _cache[rel] = pygame.image.load(path).convert_alpha() \
                if path else None
        except (pygame.error, OSError):
            _cache[rel] = None
    return _cache[rel]


def race_names():
    """Select Race's race table, by race index: [(file name, crop x, y)]."""
    global _names
    if _names is None:
        path = _find("screens/select_race/races.json")
        try:
            with open(path, encoding="utf-8") as fh:
                _names = [(r["name"].lower(),
                           tuple(r.get("portrait_crop", (0.5, 0.35))))
                          for r in json.load(fh)]
        except (OSError, TypeError, ValueError, KeyError):
            _names = []
    return _names


def icon(folder, key, px):
    """A trait's or government's icon at `px` high, or None (cached)."""
    if not key:
        return None
    k = (folder, key, px)
    if k not in _cache:
        raw = _load(f"screens/select_race/assets/icons/{folder}/{key}.png")
        _cache[k] = None if raw is None else pygame.transform.smoothscale(
            raw, (max(1, round(raw.get_width() * px / raw.get_height())), px))
    return _cache[k]


def emblem(race, px):
    """The race's symbol at `px` high: its own picture, else the flag."""
    names = race_names()
    name = names[race][0] if 0 <= race < len(names) else None
    raw = inforef.picture(f"race_{name}") if name else None
    raw = raw or inforef.picture("flag")
    if raw is None:
        return None
    k = ("emblem", id(raw), px)
    if k not in _cache:
        _cache[k] = pygame.transform.smoothscale(
            raw, (max(1, round(raw.get_width() * px / raw.get_height())), px))
    return _cache[k]


def portrait(race, size, out):
    """The race's portrait cut to `size` (cover, cropped by the race's own
    crop), its left edge fading into the card; grey and darker when `out`."""
    names = race_names()
    if not 0 <= race < len(names):
        return None
    key = ("portrait", race, tuple(size), bool(out))
    if key in _cache:
        return _cache[key]
    if len(_cache) >= _CACHE_KEEP:        # a window dragged through many sizes
        _cache.clear()
    raw = _load(f"screens/select_race/assets/portraits/{names[race][0]}.png")
    if raw is None:
        _cache[key] = None
        return None
    import numpy as np
    k = max(size[0] / raw.get_width(), size[1] / raw.get_height())
    big = pygame.transform.smoothscale(
        raw.convert(), (max(size[0], round(raw.get_width() * k)),
                        max(size[1], round(raw.get_height() * k))))
    cx, cy = names[race][1]
    cut = pygame.Surface(size)
    cut.blit(big, (0, 0), pygame.Rect(
        round((big.get_width() - size[0]) * cx),
        round((big.get_height() - size[1]) * cy), *size))
    a = pygame.surfarray.array3d(cut).astype(np.float32)
    if out:
        a = a.mean(axis=2, keepdims=True).repeat(3, axis=2) * OUT_DIM
    ramp = np.clip(np.linspace(0, 1, size[0]) / FADE, 0, 1)
    ramp = ramp * ramp * (3 - 2 * ramp)              # smoothstep
    alpha = np.repeat(ramp[:, None], size[1], axis=1)
    img = pygame.Surface(size, pygame.SRCALPHA)
    pygame.surfarray.pixels3d(img)[...] = np.clip(a, 0, 255).astype(np.uint8)
    pygame.surfarray.pixels_alpha(img)[...] = (alpha * 255).astype(np.uint8)
    _cache[key] = img
    return img


def _rule(surface, x, y, w, colour):
    """The gold rule under a card's head, fading to the right."""
    strip = pygame.Surface((w, 2), pygame.SRCALPHA)
    for i in range(w):
        a = int(200 * (1 - i / w) ** 0.8)
        # LOOK EXCEPTION marking: the card head's gold rule, Data's mockup (24 Nov)
        strip.fill(colour + (a,), (i, 0, 1, 2))
    surface.blit(strip, (x, y))


def _tag(surface, style, rect, words, size):
    """The red ELIMINATED tag at the head's right end."""
    box = pygame.Surface(rect.size, pygame.SRCALPHA)
    # LOOK EXCEPTION marking: the ELIMINATED tag's red frame, Data's mockup (24 Nov)
    pygame.draw.rect(box, TAG_RED + (45,), box.get_rect(), border_radius=5)
    # LOOK EXCEPTION marking: the ELIMINATED tag's red frame, Data's mockup (24 Nov)
    pygame.draw.rect(box, TAG_RED + (230,), box.get_rect(), 2,
                     border_radius=5)
    surface.blit(box, rect.topleft)
    img = style.render_text(words, size, RED)
    surface.blit(img, (rect.centerx - img.get_width() // 2,
                       rect.centery - img.get_height() // 2))


def card(surface, screen, key, rect, player, colour, out, words, tag, unit,
         name_size, helps, most=0):
    """Draw one race's card in `rect`; returns [(row rect, help id)].
    `words` are the trait rows' (folder, key, name, value) with the names
    translated, `tag` the ELIMINATED word, `unit` the page's reading size,
    `helps` the help id of each row (`infopages.trait_help`), `most` the
    most rows any card of the page has (every card's rows share one pitch
    and size, whichever race it is)."""
    style = screen.style
    clip = surface.get_clip()
    surface.set_clip(rect.clip(clip))
    race = int(getattr(player, "race", -1))
    share = max(40, int(rect.w * PORTRAIT_SHARE))
    pic = portrait(race, (share, rect.h - 4), out)
    if pic is not None:
        surface.blit(pic, (rect.right - 2 - share, rect.y + 2))
    pad = max(10, unit)
    # the head: symbol, name, tag, rule
    head_h = int(name_size * 1.9)
    sym = emblem(race, int(name_size * 1.5))
    x = rect.x + pad
    if sym is not None:
        surface.blit(sym, (x, rect.y + pad // 2 + (head_h - sym.get_height()) // 2))
        x += sym.get_width() + pad // 2
    shade = tuple(int(c * (0.82 if out else 1.0)) for c in colour)
    tr = None
    if out and tag:
        ts = max(10, int(unit * 0.95))
        timg = style.render_text(tag, ts, RED)
        tr = pygame.Rect(0, 0, timg.get_width() + 2 * ts, int(ts * 2.0))
        tr.topright = (rect.right - pad, rect.y + pad // 2
                       + (head_h - tr.h) // 2)
    label = player.race_name.upper().replace("^", "")
    name = style.render_text(label, name_size, shade)
    if tr is not None and x + name.get_width() > tr.left - pad // 2:
        # a long name on an eliminated card stands left of the tag, not
        # under it (WO 427: 72 px of overlap at 15 wide letters)
        room_w = max(1, tr.left - pad // 2 - x)
        name = style.render_text(
            label, max(8, int(name_size * room_w / max(1, name.get_width()))),
            shade)
    surface.blit(name, (x, rect.y + pad // 2 + (head_h - name.get_height()) // 2))
    if tr is not None:
        _tag(surface, style, tr, tag, ts)
    _rule(surface, rect.x + pad, rect.y + pad // 2 + head_h, rect.w // 2 + pad,
          GOLD)
    # the specials
    top = rect.y + pad // 2 + head_h + pad // 2
    room = rect.bottom - pad - top
    n = max(1, len(words), most)
    pitch = min(int(unit * 2.3), room // n)
    ipx = max(10, int(pitch * 0.82))
    size = max(9, min(int(unit * 1.15), int(pitch * 0.62)))
    rows = []
    for i, (folder, ikey, name_, value) in enumerate(words):
        y = top + i * pitch
        pic_i = icon(folder, ikey, ipx)
        if pic_i is not None:
            surface.blit(pic_i, (rect.x + pad, y + (pitch - pic_i.get_height()) // 2))
        tx = rect.x + pad + ipx + pad // 2
        text = style.render_text(name_.rstrip(": "), size, (232, 236, 242))
        surface.blit(text, (tx, y + (pitch - text.get_height()) // 2))
        if value:
            vimg = style.render_text(
                value, size, RED if value.startswith("-") else GREEN)
            surface.blit(vimg, (tx + text.get_width() + max(4, size // 3),
                                y + (pitch - vimg.get_height()) // 2))
        r = pygame.Rect(rect.x + pad, y, int(rect.w * 0.6), pitch)
        screen._drawn.append((pygame.Rect(tx, y + (pitch - text.get_height()) // 2,
                                          text.get_width(), text.get_height()),
                              rect, True))
        rows.append((r, helps[i] if 0 <= i < len(helps) else None))
    surface.set_clip(clip)
    return rows
