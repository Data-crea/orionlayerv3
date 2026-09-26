"""Drawing the Info screen, in the HUD style — every piece at the HD image
of its native rectangle (`infogeom`, through the Leaders screen's
`ldrdraw` helpers), every text through `core/modtexts` and `infobox`.

  OMISSION     `outer_frame` — INFO.LBX 0 (the frame with the tabs, the
               drop areas and the chart painted in) and the interlaced
               fill are not drawn: glass HUD panels stand where they are
  OMISSION     `app_pictures` — APP_PICS.LBX's 212 application pictures
               (info.cpp:893-896) are not extracted by this order; the
               picture box stays an empty panel
  DEVIATION    `button_words` — the tabs, the tech categories, the metric
               toggles, BACK and RETURN are words the original bakes into
               INFO.LBX; HD writes OrionLayer's words (moddable, `own`)
  DEVIATION    `chart_colours` — the chart's bars in the HUD's colours, not
               INFO.LBX 22-25 recoloured by `_maintenance_bar_colors`
  HD EXTENSION `wrap_and_scroll` — `infobox`
"""
import pygame

from core import modtexts
from core.hud import blocks as hud
from core.hud import text as hudtext
from screens.leaders import ldrdraw as nd

from . import infobox, infogeom as geom, infopages as pages

T = modtexts.text
#: The Info screen's text colours, `_info_normal_color` / `_high_color`
#: body indices (info.cpp:111-113) as HUD tones — INFO.LBX's palette is
#: not extracted (DEVIATION `chart_colours` covers the text too).
NORMAL, HIGH, RED = (150, 190, 215), (235, 240, 245), (225, 70, 60)
BAR_COLOURS = ((210, 190, 90), (120, 170, 230), (110, 200, 150),
               (220, 140, 80), (190, 110, 200), (200, 90, 90),
               (150, 150, 160))


def R(screen, native):
    return nd.rect(screen.layout, native)


def px(screen, key):
    return nd.font_px(screen.layout, key)


def draw_frame(surface, screen, page):
    for box in (geom.LEFT_PANEL, geom.CONTENT):
        nd.draw_box(surface, screen, box)
    layout = screen.layout
    for k, name in enumerate(pages_names()):
        r = R(screen, geom.tab_rect(k))
        hud.small_button(surface, r, layout.scale,
                         "active" if k == page else "normal")
        infobox.line(surface, screen, T(f"info.tab.{name}", name), r.inflate(
            -8, 0), px(screen, "button"), hudtext.colour("button"), "center")
    r = R(screen, geom.EXIT)
    hud.small_button(surface, r, layout.scale, "normal")
    infobox.line(surface, screen, T("info.exit", "RETURN"), r.inflate(-8, 0),
                 px(screen, "button"), hudtext.colour("button"), "center")
    title = T(f"info.title.{pages_names()[page]}", "") or ""
    if title:
        infobox.line(surface, screen, title, R(screen, geom.TITLE_BOX),
                     px(screen, "name"), HIGH, "center")


def pages_names():
    from .infotexts import PAGES
    return PAGES


def draw_stardate(surface, screen, stardate):
    x, y = geom.STARDATE_AT
    r = R(screen, (x - 60, y - 9, x + 60, y + 9))
    text = f"{stardate // 10}.{stardate % 10}"
    infobox.line(surface, screen, text, r, px(screen, "name"), HIGH, "center")


def draw_chart(surface, screen, player):
    """`Draw_Maint_Income_Chart_` (info.cpp:732-776) in HUD parts."""
    nd.draw_box(surface, screen, geom.CHART_BOX)
    income, maint, pct, net = pages.chart(player)
    h = geom.BAR_BOTTOM - geom.BAR_TOP
    visible = [k for k in range(1, 7) if pct[k]]
    x_of = {0: geom.INCOME_BAR_X}
    x = (len(visible) * 18 - 42) // 2 + 120
    for k in range(6, 0, -1):
        if pct[k]:
            x_of[k] = x
            x -= 18
    for k, bx in x_of.items():
        top = geom.BAR_BOTTOM - h * pct[k] // 100
        r = R(screen, (bx, top, bx + geom.BAR_W - 1, geom.BAR_BOTTOM))
        if r.h > 0:
            pygame.draw.rect(surface, BAR_COLOURS[k], r)
    net_text = pages.stat(T("info.chart.net_income", ""), net)
    x, y = geom.NET_AT
    infobox.line(surface, screen, net_text, R(screen, (x - 90, y - 7, x + 90,
                                                       y + 7)),
                 px(screen, "status"), RED if net < 0 else NORMAL, "center")
    for (x, y), key in ((geom.INCOME_HEAD_AT, "info.chart.income"),
                        (geom.MAINT_HEAD_AT, "info.chart.maintenance")):
        infobox.line(surface, screen, T(key, "") or "",
                     R(screen, (x - 40, y - 5, x + 40, y + 5)),
                     px(screen, "note"), NORMAL, "center")
    x0, y0 = geom.LABEL_AT
    w, hh = geom.LABEL_SIZE
    names = ("income", "buildings", "freighters", "ships", "spies",
             "tribute", "leaders")
    for k, name in enumerate(names):
        y = y0 + k * geom.LABEL_STEP
        label = T(f"info.chart.label.{name}", "") or ""
        text = f"{income}{label}" if k == 0 else f"{pct[k]:3d}%  {label}"
        r = R(screen, (x0, y, x0 + w - 1, y + hh - 2))
        pygame.draw.rect(surface, BAR_COLOURS[k], r.inflate(-r.w + 6, -4)
                         .move(-(r.w // 2) + 4, 0))
        infobox.line(surface, screen, text, r.inflate(-12, 0).move(6, 0),
                     px(screen, "status"), NORMAL,
                     "center" if k == 0 else "left")


def rows(surface, screen, key, native, items, selected=None, lit=None):
    """A scrolling list of one-line rows — `(text, payload, header)` — each
    shrunk to its width. Returns nothing; its hit rects go to
    `screen._hits[key]` as (rect, payload)."""
    box = R(screen, native)
    nd.draw_box(surface, screen, native)
    inner = hud.panel_inner(box, screen.layout.scale).inflate(-4, -4)
    step = int(px(screen, "skill") * 1.35)
    total = step * len(items)
    overflow = max(0, total - inner.h)
    if overflow:
        inner.w -= max(6, step // 3) + 2
    offset = max(0, min(screen._scroll.get(key, 0), overflow))
    screen._scroll[key] = offset
    hits = []
    y = inner.y - offset
    previous = surface.get_clip()
    surface.set_clip(inner)
    for text, payload, header in items:
        r = pygame.Rect(inner.x, y, inner.w, step)
        if inner.contains(r):
            colour = HIGH if header or payload in (selected, lit) else NORMAL
            if payload is not None and payload == selected:
                pygame.draw.rect(surface, (40, 70, 110), r)
            infobox.line(surface, screen, text,
                         r.inflate(-4, 0) if header else r.inflate(-16, 0)
                         .move(8, 0), px(screen, "skill"), colour)
            if payload is not None:
                hits.append((r, payload))
        y += step
    surface.set_clip(previous)
    if overflow:
        hud.scrollbar(surface, pygame.Rect(inner.right + 2, inner.y,
                                           max(6, step // 3), inner.h),
                      screen.layout.scale, offset, inner.h, total)
    screen._hits[key] = hits
    screen._boxes[key] = _ListBox(box, overflow, step)


class _ListBox:
    def __init__(self, rect, overflow, step):
        self.rect, self.overflow, self.step = rect, overflow, step


def text(surface, screen, key, native, body, size_key="skill", colour=NORMAL,
         align="left", panel=True):
    rect = R(screen, native)
    if panel:
        nd.draw_box(surface, screen, native)
        # Clear of the panel's edge and its glow (`blocks.panel_inner`).
        rect = hud.panel_inner(rect, screen.layout.scale).inflate(-4, -4)
    infobox.Box(key, rect, body or "", px(screen, size_key),
                colour, align).draw(surface, screen)


def button(surface, screen, native, words, active=False):
    r = R(screen, native)
    hud.small_button(surface, r, screen.layout.scale,
                     "active" if active else "normal")
    infobox.line(surface, screen, words, r.inflate(-6, 0), px(screen, "cost"),
                 hudtext.colour("button"), "center")
