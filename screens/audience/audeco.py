"""The gold diplomacy look over the ambassador's film — work order 359.

**HD EXTENSION `audience_gold_menu`.** Data's mockup ("Elerian Empire
Diplomacy Interface"): while the ambassador's clip plays the menu is a
gold-framed panel with the title, a divider, one dark card per row — an
icon, the words, the hovered row lit in gold — and the statement bar has
the race's symbol at its left. Only the LOOK changes: the rows stand
exactly where the engine's fields put them (`augeom`), so a click lands
where it is drawn, and every word is still the game's (`lang.verbatim`).
Without the clip the audience keeps the HUD panels of `audraw`.

The icons are cut from the player's icon sheet by
`tools/audience_icons_install.py` into the mod folder; the symbol is the
race's emblem, the one the flag choice shows (`assets/shared/banner/
emblems/<race>.png`). A missing icon or emblem is simply not drawn.

**INVENTION `menu_icons_by_row`.** The icon of a row is its index in the
main menu (eight rows: Propose Treaty, Break Treaty, Demand, Offer Gift,
Exchange Tech, Declare War, Surrender, Good Bye); a menu of any other
length has no icons — the words differ per language, so they cannot name
the row.
"""
import os

import pygame

ICONS = ("propose", "break", "demand", "gift", "exchange", "war",
         "surrender", "bye")
ICON_REL = "screens/audience/assets/icons"
EMBLEM_REL = "assets/shared/banner/emblems"

#: The gold the mockup is drawn in; `pal()` turns it with the player's
#: frame colour (Game Settings), as every component of the HUD turns.
GOLD = (236, 190, 96)
GOLD_DIM = (150, 112, 52)
GOLD_LIT = (255, 214, 120)
OFF_LINE, OFF_TEXT = (70, 56, 36), (110, 100, 86)
CARD = (14, 12, 12, 215)
PANEL = (10, 8, 8, 225)

_cache = {}
_tone = {"key": None, "pal": None, "emblem": {}, "divider": None}


#: The hue of the mockup's gold, degrees (236, 190, 96 -> 41).
GOLD_HUE = 41


class Pal:
    pass


def _delta():
    """How far the gold turns for the player's frame colour. The HUD's
    hue setting is the hue its accent is DRAWN in (196, a blue, measured);
    the menu's accent is this gold, so the setting names the menu's hue
    directly: a setting of 30 gives an orange-gold, 196 a blue. The first
    cut turned the gold by the HUD's own offset from blue (setting - 196),
    and a setting of 30 made the menu blue (Data, 1 November)."""
    from core.hud import tint
    return 0.0 if tint.hue() is None else float(tint.hue()) - GOLD_HUE


def pal():
    """The gold colours at the player's frame colour (`core.hud.tint`:
    hue, saturation, brightness — the default leaves the gold as drawn).

    **HD EXTENSION `audience_gold_follows_frame_colour`.** The panels'
    lines, the title, the header, the ring and the divider turn exactly as
    the HUD's own components do (`tint.transform`, by component, work
    order 172); the icons and the race's symbol are pictures and keep
    their own colours — the symbol only takes the gold its ring has."""
    from core.hud import tint
    key = (tint.hue(), tint.sat(), tint.bright())
    if _tone["key"] != key:
        out = Pal()
        for name, rgb in (("gold", GOLD), ("dim", GOLD_DIM),
                          ("lit", GOLD_LIT), ("off_line", OFF_LINE),
                          ("off_text", OFF_TEXT)):
            setattr(out, name, tint.transform(rgb, d=_delta()))
        _tone.update(key=key, pal=out, emblem={}, divider=None)
    return _tone["pal"]


def turned(pic, cache_key):
    """`pic` (a gold piece of the frame) turned with the frame colour."""
    from core.hud import tint
    if tint.is_default():
        return pic
    import numpy as np
    pal()                                   # drops caches on a change
    held = _tone["emblem"]
    if cache_key not in held:
        out = pic.copy()
        px = pygame.surfarray.pixels3d(out)
        px[:] = tint.transform_array(np.array(px), _delta(),
                                     tint.sat(), tint.bright(), False, True)
        del px
        held[cache_key] = out
    return held[cache_key]


def _find(rel):
    from core import basepack, usermod
    from core.config import BASE_DIR
    for root in (os.path.join(usermod.mod_dir(), usermod.FILES), BASE_DIR,
                 basepack.base_dir()):
        if root:
            path = os.path.join(root, *rel.split("/"))
            if os.path.isfile(path):
                return path
    return None


def picture(rel):
    """The file's convert_alpha picture, or None (cached)."""
    if rel not in _cache:
        path = _find(rel)
        try:
            _cache[rel] = pygame.image.load(path).convert_alpha() \
                if path else None
        except (pygame.error, OSError):
            _cache[rel] = None
    return _cache[rel]


def fitted(pic, box_w, box_h):
    k = min(box_w / pic.get_width(), box_h / pic.get_height())
    return pygame.transform.smoothscale(
        pic, (max(1, round(pic.get_width() * k)),
              max(1, round(pic.get_height() * k))))


def frame(surface, rect, fill=PANEL, cut=None, line=None, width=2):
    """A chamfered dark panel with a double gold border."""
    c = cut if cut is not None else max(6, rect.h // 7)
    p = pal()
    for grow, colour, w, alpha in ((0, line or p.gold, width, True),
                                   (-4, p.dim, 1, False)):
        r = rect.inflate(2 * grow, 2 * grow)
        pts = [(r.left + c, r.top), (r.right - c, r.top),
               (r.right, r.top + c), (r.right, r.bottom - c),
               (r.right - c, r.bottom), (r.left + c, r.bottom),
               (r.left, r.bottom - c), (r.left, r.top + c)]
        if alpha:
            layer = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.polygon(layer, fill, [(x - rect.x, y - rect.y)
                                              for x, y in pts])
            surface.blit(layer, rect.topleft)
        # LOOK EXCEPTION picture: the gold frame of Data's mockup (HD EXTENSION audience_gold_menu), not a HUD panel: its own gold, turned with the frame colour by pal()
        pygame.draw.polygon(surface, colour, pts, w)


#: Data's mockup, as fractions of the film's picture (1672 x 941): the
#: panel's left, top and width; the title and divider heights; the first
#: row's top, its height and its pitch; the bar's box.
#: **HD EXTENSION `menu_toward_left_edge`** (Data, 1 November): the panel
#: and its rows stand half the mockup's distance from the picture's left
#: edge (95 px -> 47.5 px), their widths as drawn.
LEFT_X = 95 / 1672 / 2
PANEL_X, PANEL_Y, PANEL_W = LEFT_X, 118 / 941, 510 / 1672
ROW_X, ROW_W, ROW_H, ROW_PITCH = (LEFT_X + 23 / 1672, 464 / 1672, 50 / 941,
                                  57 / 941)
TITLE_Y, DIVIDER_Y, ROW_TOP = 154 / 941, 185 / 941, 217 / 941
BAR = (245 / 1672, 776 / 941, 1180 / 1672, 122 / 941)
TITLE_H, ITEM_H, BAR_H = 0.042, 0.033, 0.031     # text heights / picture h
#: **HD EXTENSION `menu_down_from_top`** (Data, 1 November): the menu panel
#: stands up to 65 px lower than the mockup has it (the picture's 941 px;
#: the width and the x stay), but never nearer to the statement bar than
#: 25 px. The 8-row main menu ends 90 px over the bar, so it moves the full
#: 65 and keeps 25; a longer menu moves less (9 rows: 8), one that already
#: touches the bar (10 rows) not at all.
MENU_SHIFT, BAR_GAP = 65 / 941, 25 / 941
MAIN_TITLE = "DIPLOMACY"                          # INVENTION, see below


class Layout:
    """Where the film mode puts the menu and the bar, from the film's
    picture rectangle `box` and the row count `n`."""

    def __init__(self, box, n):
        w, h = box.size
        self.h = h
        r = lambda fx, fy, fw, fh: pygame.Rect(  # noqa: E731
            box.x + round(fx * w), box.y + round(fy * h),
            round(fw * w), round(fh * h))
        bottom = ROW_TOP + n * ROW_PITCH + 0.014
        d = min(MENU_SHIFT, max(0.0, BAR[1] - BAR_GAP - bottom))
        self.panel = r(PANEL_X, PANEL_Y + d, PANEL_W, bottom - PANEL_Y)
        self.title = r(PANEL_X, TITLE_Y + d - 0.03, PANEL_W, 0.06)
        self.divider_y = box.y + round((DIVIDER_Y + d) * h)
        self.rows = [r(ROW_X, ROW_TOP + d + i * ROW_PITCH, ROW_W, ROW_H)
                     for i in range(n)]
        self.bar = r(*BAR)


def gold(pic, key):
    """A grey emblem as gold, the gold at the frame colour; cached."""
    from core.hud import tint
    pal()                                   # drops caches on a change
    held = _tone["emblem"]
    if ("symbol", key) not in held:
        out = pic.copy()
        out.fill(tint.transform((255, 205, 110), d=_delta()) + (255,),
                 special_flags=pygame.BLEND_RGBA_MULT)
        out.fill((40, 22, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
        held[("symbol", key)] = out
    return held[("symbol", key)]


def menu(surface, screen, view, lay, text_at, hovered):
    """The gold menu in `lay`. `text_at(words, x, y, w, colour, px,
    centre)` prints a line; `hovered(rect)` answers the pointer."""
    from core.hud import text as hudtext
    items = view.items()
    frame(surface, lay.panel, cut=max(8, lay.panel.w // 28))
    title = (view.audience["title"] or "").strip()
    main = len(items) == len(ICONS)
    if main:
        title = MAIN_TITLE    # INVENTION `menu_title_mockup`
    if title:
        px = int(lay.h * TITLE_H)
        text_at(title.upper(), lay.title.centerx, lay.title.centery,
                lay.title.w, pal().gold, px, True)
    div = picture(ICON_REL + "/divider.png")
    if div is not None:
        d = fitted(turned(div, "divider"), lay.panel.w - 40,
                   max(8, lay.h // 40))
        surface.blit(d, (lay.panel.centerx - d.get_width() // 2,
                         lay.divider_y - d.get_height() // 2))
    px = int(lay.h * ITEM_H)
    p = pal()
    for n, (item, f) in enumerate(items):
        r = lay.rows[n]
        lit = item["enabled"] and hovered(r)
        frame(surface, r, fill=CARD, cut=max(4, r.h // 6),
              line=p.lit if lit else (p.dim if item["enabled"]
                                      else p.off_line),
              width=3 if lit else 1)
        pad = max(18, r.h // 2)           # the words keep off the card's edge
        pic = picture(f"{ICON_REL}/{ICONS[n]}.png") if main else None
        if pic is not None:
            ic = fitted(pic, int(r.h * 1.1), r.h - 8)
            if not item["enabled"]:
                ic = ic.copy()
                ic.set_alpha(110)
            surface.blit(ic, (r.x + pad, r.centery - ic.get_height() // 2))
        x = r.x + pad + (int(r.h * 1.1) + pad // 2 if main else 0)
        colour = (p.lit if lit else hudtext.colour("value")) \
            if item["enabled"] else p.off_text
        text_at(item["text"].strip(), x, r.centery, r.right - x - pad,
                colour, px, False)


def bar(surface, screen, view, lay, text_at, header):
    """The statement bar: the race's gold symbol in a ring, the header
    line, the statement. `header` is the line over it or ''."""
    from core.textfit import wrap_text
    b = lay.bar
    frame(surface, b, cut=max(8, b.h // 6))
    gap = b.h // 7
    x = b.x + gap + 6
    sym = emblem(screen_race(view))
    ring = b.h - 2 * gap
    if sym is not None:
        c = (x + ring // 2, b.centery)
        pygame.draw.circle(surface, pal().gold, c, ring // 2, 2)
        pygame.draw.circle(surface, pal().dim, c, ring // 2 - 5, 1)
        pic = fitted(gold(sym, view.race), int(ring * 0.62),
                     int(ring * 0.62))
        surface.blit(pic, (c[0] - pic.get_width() // 2,
                           c[1] - pic.get_height() // 2))
        x += ring + gap
    px = int(lay.h * BAR_H)
    hpx = int(px * 0.72)
    x += gap // 2
    width = b.right - x - gap * 2
    lines = wrap_text(screen.style, view.statement, px, width)[:2]
    step = int(px * 1.25)
    rule = 12                         # the rule under the header, with room
    total = len(lines) * step + (int(hpx * 1.25) + rule if header else 0)
    y = b.centery - total // 2
    if header:
        text_at(header.upper(), x, y + int(hpx * 1.25) // 2, width, pal().gold,
                hpx, False)
        y += int(hpx * 1.25) + rule // 2
        pygame.draw.line(surface, pal().dim, (x, y), (b.right - gap * 2, y),
                         1)
        y += rule // 2
    for line in lines:
        text_at(line, x, y + step // 2, width, (236, 232, 220), px, False)
        y += step


def screen_race(view):
    return view.race


def header_line(view):
    """"ELERIAN EMPIRE · ELLOWYN" from the ambassador's record, or ''.
    INVENTION `bar_header`: the race's name and the ruler's, as the game
    keeps them; the word EMPIRE is the mockup's, not the game's."""
    from core.structs import player as player_struct
    raws = getattr(view.game_state, "player_raw", None) or []
    i = view.audience["ambassador"] if view.audience else -1
    if not 0 <= i < len(raws) or raws[i] is None:
        return ""
    try:
        p = player_struct.parse(raws[i])
        race, name = str(p.race_name).strip(), str(p.name).strip()
    except (AttributeError, ValueError, TypeError):
        return ""
    return f"{race} Empire \u00b7 {name}" if race and name else \
        (race or name)


def emblem(race):
    """The race's flag-choice symbol, or None."""
    from . import auvideo
    if race is None or not 0 <= race < len(auvideo.RACES):
        return None
    return picture(f"{EMBLEM_REL}/{auvideo.RACES[race]}.png")
