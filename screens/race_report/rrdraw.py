"""Drawing the race report's left column (racerprt.cpp:96-133) — the right
half is Info's Tech Review page (`screens/info/infoview.tech`) for the
race the report is about.

  TRANSCRIPTION  the portrait in its banner-colour frame, the name, the
                 personality and objective, their spies and the count
                 line, the alliances and wars — every word the game's own
                 (BILLTEXT, ESTRINGS), every place the source's
  DEVIATION      `hud_parts`: RACERPRT.LBX 0's painted boxes are the
                 shared field (work order 223, decision 71 as amended);
                 the font is the HD font (`hd_font`, the Races screen's)
"""
from core.hud import blocks as hud
from screens.info import infodraw
from screens.info import infopages as pages
from screens.leaders import ldrdraw as nd
from screens.races import racesdraw

from . import rrgeom as geom


def lines(view, words):
    """What the column says, as data: (name, text lines, spy count, spy
    line, treaty lines)."""
    p = view["player"]
    pers = words.e(geom.E_PERSONALITY + int(p.personality)) or ""
    text = [pers]
    if int(p.objectives) != geom.OBJECTIVE_HUMAN:
        text.append(words.e(geom.E_OBJECTIVE + int(p.objectives)) or "")
    spies = view["spies"]
    if spies == 0:
        spy_line = words.b(geom.B_NO_SPIES)
    elif spies == 1:
        spy_line = words.b(geom.B_ONE_SPY)
    else:
        spy_line = pages.stat(words.b(geom.B_SPIES), spies)
    treaty = [words.b(geom.B_ALLIES)] + (view["allies"] or
                                         [words.b(geom.B_NO_ALLIES)])
    treaty += [""] + [words.b(geom.B_WARS)] + (view["wars"] or
                                               [words.b(geom.B_NO_WARS)])
    return p.name, text, spies, spy_line, treaty


def draw_column(surface, screen, view, words, art):
    layout = screen.layout
    hud.panel(surface, nd.rect(layout, geom.LEFT_PANEL), layout.scale)
    for box in geom.FIELDS:
        hud.field(surface, nd.rect(layout, box), layout.scale)
    p = view["player"]
    px, py = geom.PORTRAIT
    w, h = geom.PORTRAIT_SIZE
    cell = nd.rect(layout, (px, py, px + w - 1, py + h - 1))
    hud.field(surface, cell, layout.scale)
    pic = art.portrait(int(p.race)) if art is not None else None
    if pic is not None:
        big = nd.magnified(pic, layout)
        surface.blit(big, big.get_rect(center=cell.center))
    racesdraw.banner_frame(surface, layout, cell, int(p.color), art)
    name, text, spies, spy_line, treaty = lines(view, words)
    x, y, bw, bh = geom.NAME
    _centred(surface, screen, [name], (x, y, bw, bh), "name",
             infodraw.HIGH)
    _centred(surface, screen, text, geom.TEXT, "skill", infodraw.NORMAL)
    if spies:
        racesdraw.draw_icons(surface, screen, geom.SPY_GROUP, spies,
                             int(p.race), art)
    sx, sy, sw = geom.SPY_LINE
    _centred(surface, screen, [spy_line], (sx, sy, sw, 12), "status",
             infodraw.NORMAL)
    _centred(surface, screen, treaty, geom.TREATIES, "skill",
             infodraw.NORMAL, top=True)


def _centred(surface, screen, rows, box, key, colour, top=False):
    """`Squeeze_Paragraph_Centered_`: each row centred in the box's width,
    the block centred in its height (or from its top)."""
    layout = screen.layout
    x, y, w, h = box
    r = nd.rect(layout, (x, y, x + w - 1, y + h - 1))
    size = nd.font_px(layout, key)
    step = max(1, int(size * 1.15))
    rows = [t for t in rows if t is not None]
    total = step * len(rows)
    ty = r.y if top else r.y + max(0, (r.h - total) // 2)
    for t in rows:
        if t:
            nd.blit_text(surface, screen.style, t, r.centerx, ty, r.w, size,
                         colour, "center")
        ty += step
