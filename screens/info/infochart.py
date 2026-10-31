"""The planet transformation chart — Reference page, work order 358.

HD EXTENSION `planet_chart` (Data, 31 October 2026: a picture of the steps
as they are in the game — "find a fitting place and rebuild it"): one more
row at the foot of the Reference's how-to list opens a page with the ten
climates as discs and the ways between them:

  Radiation Shield   Radiated -> Barren (`Colony_Calculation_` rewrites the
                     colony's climate while a Radiation Shield stands,
                     colcalc.cpp:682)
  Terraforming       Barren <-> Tundra, Barren -> Desert, Tundra -> Swamp,
                     Desert -> Arid, Swamp / Arid / Ocean -> Terran
  Gaia Transformation  Terran -> Gaia

and the population maximum growing from the top row to the bottom. The
discs are the climates' pictures wherever the game shows a planet
(`colonyplanets.set_for`, the mod's own first); the names are the game's,
the four own words are moddable (`info.chart.*`).

UNVERIFIED `planet_chart_steps`: the steps are as Data's picture draws them;
the engine's transform tables (`ericnet.cpp` terraform, Gaia) were not read
for this page.
"""
import pygame

from core import lang, modtexts
from core.hud import blocks as hud
from screens.colony_summary import colonyplanets as planets

from . import infobox, infodraw

T = modtexts.text
#: the row's payload in the how-to list (`("howto", CHART)`)
CHART = "planet_chart"

#: the chart's own coordinate system (the picture it rebuilds)
W, H = 911.0, 694.0
DISC = 64.0
#: climate -> centre
CENTRE = {"toxic": (55, 120), "radiated": (186, 118), "tundra": (381, 118),
          "barren": (512, 118), "desert": (641, 118), "ocean": (772, 118),
          "swamp": (381, 250), "arid": (641, 380), "terran": (641, 512),
          "gaia": (641, 640)}
#: climate -> (anchor, dx, dy) of its name from the centre
LABEL = {"toxic": ("below", 0, 0), "radiated": ("below", 0, 0),
         "tundra": ("left", 0, 0), "barren": ("below", 0, 0),
         "desert": ("above", 0, 0), "ocean": ("above", 0, 0),
         "swamp": ("left", 0, 0), "arid": ("right", 0, 0),
         "terran": ("right", 0, 0), "gaia": ("right", 0, 0)}
BLUE, ORANGE, GREEN, GREY = (96, 120, 215), (205, 100, 55), (50, 175, 60), \
    (150, 150, 150)
#: (colour, [points], head at the start, head at the end)
ARROWS = (
    (BLUE, [(418, 118), (476, 118)], True, True),
    (BLUE, [(550, 118), (604, 118)], False, True),
    (BLUE, [(381, 156), (381, 212)], False, True),
    (BLUE, [(641, 156), (641, 344)], False, True),
    (BLUE, [(641, 418), (641, 474)], False, True),
    (BLUE, [(381, 290), (381, 332), (606, 492)], False, True),
    (BLUE, [(772, 156), (772, 424), (676, 490)], False, True),
    (GREEN, [(641, 552), (641, 602)], False, True),
    (ORANGE, [(300, 62), (212, 94)], False, True),
    (ORANGE, [(400, 62), (480, 94)], False, True),
    (GREY, [(28, 342), (28, 500)], False, True),
)
#: key, default, centre, colour
TAGS = (("info.chart.shield", "Radiation Shield", (350, 42), ORANGE),
        ("info.chart.terraforming", "Terraforming", (535, 282), BLUE),
        ("info.chart.gaia", "Gaia Transformation", (517, 576), GREEN))
GROWTH = ("info.chart.growth", "Increase of population maximum", (44, 420))


def words():
    """Rows for the how-to list: the chart's row."""
    return T("info.chart.row", "Planet Transformation") or ""


def title():
    return lang.tr(T("info.chart.row", "Planet Transformation") or "")


def _arrow(surface, colour, pts, k, head_start, head_end):
    w = max(2, int(2.2 * k))
    pygame.draw.lines(surface, colour, False, pts, w)

    def head(tip, frm):
        dx, dy = tip[0] - frm[0], tip[1] - frm[1]
        n = max(1.0, (dx * dx + dy * dy) ** 0.5)
        ux, uy = dx / n, dy / n
        s = 11 * k
        base = (tip[0] - ux * s, tip[1] - uy * s)
        # LOOK EXCEPTION marking: the chart's arrow heads in the way's colour
        pygame.draw.polygon(surface, colour, [
            tip, (base[0] - uy * s * 0.5, base[1] + ux * s * 0.5),
            (base[0] + uy * s * 0.5, base[1] - ux * s * 0.5)])
    if head_end:
        head(pts[-1], pts[-2])
    if head_start:
        head(pts[0], pts[1])


def draw(surface, screen, native):
    """The chart inside the how-to page's box `native`."""
    box = infodraw.field(surface, screen, native)
    inner = hud.panel_inner(box, screen.layout.scale).inflate(-6, -6)
    k = min(inner.w / W, inner.h / H)
    ox = inner.x + (inner.w - W * k) / 2.0
    oy = inner.y + (inner.h - H * k) / 2.0

    def P(x, y):
        return (ox + x * k, oy + y * k)
    size = infodraw.px(screen, "skill")
    disc = max(8, int(DISC * k))
    pset = planets.set_for(screen, disc)
    for colour, pts, a, b in ARROWS:
        _arrow(surface, colour, [P(*p) for p in pts], k, a, b)
    for name, (cx, cy) in CENTRE.items():
        pic = pset.get(planets.NAMES.index(name)) if pset else None
        x, y = P(cx, cy)
        if pic is not None:
            surface.blit(pic, pic.get_rect(center=(int(x), int(y))))
        word = name.capitalize()
        anchor = LABEL[name][0]
        h = int(size * 1.6)
        w = int(150 * k)
        if anchor == "below":
            r = pygame.Rect(int(x - w / 2), int(y + disc / 2 + 2), w, h)
            align = "center"
        elif anchor == "above":
            r = pygame.Rect(int(x - w / 2), int(y - disc / 2 - h), w, h)
            align = "center"
        elif anchor == "left":
            r = pygame.Rect(int(x - disc / 2 - w - 4), int(y - h / 2), w, h)
            align = "right"
        else:
            r = pygame.Rect(int(x + disc / 2 + 6), int(y - h / 2), w, h)
            align = "left"
        infobox.line(surface, screen, word, r, size, infodraw.NORMAL, align)
    for key, default, (cx, cy), colour in TAGS:
        text = T(key, default) or default
        x, y = P(cx, cy)
        tw = max(int(len(text) * size * 0.62), int(110 * k))
        r = pygame.Rect(0, 0, tw + int(14 * k), int(size * 1.9))
        r.center = (int(x), int(y))
        # LOOK EXCEPTION marking: a way's name tag in the way's colour
        pygame.draw.rect(surface, colour, r, border_radius=max(3, int(5 * k)))
        infobox.line(surface, screen, text, r.inflate(-8, 0), size,
                     infodraw.HIGH, "center")
    key, default, (gx, gy) = GROWTH
    text = lang.tr(T(key, default) or default)
    x, y = P(gx, gy)
    mid = text.find(" ", len(text) // 2 - 3)
    lines = (text[:mid], text[mid + 1:]) if mid > 0 else (text, "")
    for i, part in enumerate(lines):
        if part:
            infobox.line(surface, screen, part,
                         pygame.Rect(int(x), int(y + i * size * 1.5),
                                     int(260 * k), int(size * 1.5)),
                         size, infodraw.NORMAL)
