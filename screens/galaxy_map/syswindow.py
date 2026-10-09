"""The star system window's drawing — ONE implementation for the galaxy
map's window and the combat target window (work order 228 B).

The original draws both with one function, `SYS::Draw_System_Display_
Popup_` (sys.cpp:679-857): the galaxy map's window when a star is clicked
(`Wrapper_For_Normal_System_Popup_`, :1696-1720) and the window a player
picks a combat target in ("%s select combat at %s",
`MAINPUPS::Draw_Defense_Selection_Popup_`, mainpups.cpp:2121-2150). Their
fields are one builder's too (`Add_System_Display_Popup_Fields_`,
sys.cpp:1746-1940). So HD draws both here: `boxdraw` for the map, from the
map's own field list; `combattarget` for the popup, from open fix 49's TPOP
block. What each window adds is the caller's.

What is drawn, and from where:

  TRANSCRIPTION  the sun in the rings' centre (`Draw_Sun_Seg_`,
                 sys.cpp:562-578), the orbits and each planet where the
                 engine put it (`sysorbits`, work order 223)
  TRANSCRIPTION  the colony markers (work order 228): beside every planet
                 that carries a colony a pennant in its owner's colour —
                 filled for a colony (`Draw_Colony_Marker_`, BUFFER0.LBX
                 0x23 + colour, its right edge on the planet's left), an
                 outline for an outpost (`Draw_Outpost_Marker_`, 0x2B +
                 colour, 2 px further left), its top 2 px above the
                 planet's (sys.cpp:329-343, :800-822; `_sys_disp` is the
                 orbit place less half the planet, :128-129)
  DEVIATION      `marker_drawn`: the pennants are drawn in code in the
                 measured shape (8 x 7 native px, a right-pointing
                 triangle), not the pictures, which are not extracted
  OMISSION       `asteroid_marker`: an asteroid belt's colony has no field,
                 so HD does not know where the original draws its marker
  TRANSCRIPTION  the planet under the pointer: its highlight and its
                 information in a darkened box at the view's corner
                 (sys.cpp:824-844; `sysinfo`, work order 226 F)
  DEVIATION      `planet_highlight_drawn`: the highlight is BUFFER0.LBX 0x4B
                 recoloured to the owner (grey without one, sys.cpp:599-
                 633); HD draws its measured shape in code — a 35 native px
                 square centred on the planet, four corner brackets 2 px
                 thick and 8 long — in the owner's colour
"""
import pygame

from core import hestrings
from core import palette
from core import textfit
from core.hud import blocks as hud
from core.hud import glyphs
from screens.colony_summary import colonyplanets
from screens.galaxy_map import renderer as rnd
from screens.galaxy_map import sysorbits

PANEL_BG = palette.col("galaxy_map", "panel_background", (8, 11, 20))
TITLE_COLOR = palette.col("galaxy_map", "title", (200, 210, 238))
TEXT_COLOR = palette.col("galaxy_map", "nav_text", (196, 208, 236))
GAS_GIANT = palette.col("galaxy_map", "status", (140, 155, 190))

#: The marker pennant (BUFFER0.LBX 0x23 / 0x2B, measured): 8 x 7 native px.
MARKER_W, MARKER_H = 8, 7
#: Where it stands off the planet's top-left, native px (sys.cpp:803-822):
#: a colony's right edge on the planet's left (`x - width + 2` from a
#: point 2 left of the planet), an outpost's 2 px further left; both from
#: 2 px above the planet's top.
COLONY_MARKER_DX, OUTPOST_MARKER_DX, MARKER_DY = -8, -10, -2
#: The highlight (BUFFER0.LBX 0x4B, measured): its square, the brackets'
#: thickness and arm, native px.
HIGHLIGHT, BRACKET_LINE, BRACKET_ARM = 35, 2, 8
#: `Draw_Darkened_Box_(…, 0x3F)` under an information box (sys.cpp:841).
INFO_SHADE = 170


def font(screen, name, default):
    style = next((b.style for b in screen.boxes if b.name == name), {})
    return screen.layout.font_size(style.get("font_size", default))


def text(screen, surface, rect, words, size, colour, align="center"):
    if not words:
        return
    surf = screen.style.render_text(words, size, tuple(colour[:3]))
    x = {"left": rect.x, "right": rect.right - surf.get_width()}.get(
        align, rect.x + (rect.w - surf.get_width()) // 2)
    surface.blit(surf, (x, rect.y + (rect.h - surf.get_height()) // 2))


def frame(screen, surface, rect):
    """The window's body: the HUD popup block (decision 71) — a dialog over
    the map, opaque."""
    hud.popup(surface, rect, screen.layout.scale)


def close_button(screen, surface, rect, label):
    """CLOSE: the HUD's small button, its word in code."""
    hud.small_button(surface, rect, screen.layout.scale, "normal", label,
                     style_renderer=screen.style,
                     icon=glyphs.for_button("galaxy_map", "close"))


def close_label(screen):
    return (screen._data.get("movable_boxes") or {}).get("close", "")


def owner_colour(owner):
    """A player's colour as the map draws it; the box's text without one."""
    return palette.col("galaxy_map", f"owner_{owner}", TEXT_COLOR) \
        if owner is not None else TEXT_COLOR


def draw_view(screen, surface, view, model, state=None):
    """The window's view: the unviewable system's text, or the sun, the
    orbits, the planets and their markers. Returns [(planet, rect)] of the
    planets drawn, back to front. `state`: the snapshot the window shows
    (the screen's own by default)."""
    if not model["viewable"]:
        size = font(screen, "system_view", 16)
        lines = textfit.wrap_text(screen.style, model["body"], size, view.w)
        y = view.y
        for line in lines:
            surf = screen.style.render_text(line, size, TEXT_COLOR[:3])
            surface.blit(surf, (view.x, y))
            y += surf.get_height()
        return []
    stars = getattr(screen, "_stars", None) or []
    star = stars[model["star"]] if 0 <= model["star"] < len(stars) else None
    ctx = screen._map_context()
    name = rnd.star_icon_name(star, ctx) \
        if ctx is not None and star is not None else None
    s, cx, cy = sysorbits.frame(view)
    # The sun in the rings' centre (`Draw_Sun_Seg_`, sys.cpp:562-578; its
    # BUFFER0.LBX 0x53 + class picture is 32 x 34 native px).
    sun = max(8, int(34 * s))
    if name and screen._cache.has(name):
        img = screen._cache.scaled(name, sun)
        if img is not None:
            surface.blit(img, (cx - img.get_width() // 2,
                               cy - img.get_height() // 2))

    def planet(p, centre, side):
        rect = pygame.Rect(0, 0, side, side)
        rect.center = centre
        disc = None
        if p["type"] != 2:
            discs = colonyplanets.set_for(screen, side)
            disc = discs.get(p["climate"]) if discs is not None else None
        if disc is not None:
            surface.blit(disc, rect.topleft)
        else:
            pygame.draw.circle(surface, GAS_GIANT[:3], rect.center,
                               side // 2, 2)
        return rect

    drawn = sysorbits.draw(surface, view, model, planet)
    markers(surface, state if state is not None else
            getattr(screen, "_state", None), drawn, s)
    return drawn


def marker_polygon(x, y, s):
    """The pennant's three corners, device px, its top-left at (x, y)."""
    return [(x, y), (x + MARKER_W * s, y + MARKER_H * s / 2.0),
            (x, y + MARKER_H * s)]


def colony_mark(state, planet_index):
    """(owner's colour index, outpost?) for a planet with a colony, else
    None (sys.cpp:803-822)."""
    from core.structs import colony as colony_struct
    from core.structs import planet as planet_struct
    from screens.galaxy_map import sysinfo
    colour = sysinfo.owner_colour(state, planet_index)
    if colour is None:
        return None
    ci = int(planet_struct.parse(state.planets_raw[planet_index]).colony_index)
    return colour, bool(colony_struct.parse(state.colonies_raw[ci]).outpost_flag)


def markers(surface, state, drawn, s):
    """A pennant beside each planet with a colony (`markers` in the module
    docstring): filled for a colony, an outline for an outpost."""
    if state is None:
        return
    for p, rect in drawn:
        mark = colony_mark(state, p["planet"])
        if mark is None:
            continue
        owner, outpost = mark
        dx = OUTPOST_MARKER_DX if outpost else COLONY_MARKER_DX
        pts = marker_polygon(rect.x + dx * s, rect.y + MARKER_DY * s, s)
        colour = tuple(owner_colour(owner))[:3]
        line = max(1, int(round(s)))
        # LOOK EXCEPTION data: the colony owner's colour, as the original's marker (sys.cpp:329-343)
        if not outpost:
            pygame.draw.polygon(surface, colour, pts)
            pygame.draw.polygon(surface, tuple(v // 2 for v in colour), pts,
                                line)
        else:
            pygame.draw.polygon(surface, colour, pts, line)


def highlight(surface, centre, s, colour):
    """DEVIATION `planet_highlight_drawn`: the original's corner brackets,
    35 native px square centred on the planet."""
    side = HIGHLIGHT * s
    box = pygame.Rect(0, 0, int(side), int(side))
    box.center = centre
    t = max(1, int(round(BRACKET_LINE * s)))
    a = max(t + 1, int(round(BRACKET_ARM * s)))
    for x, y, sx, sy in ((box.left, box.top, 1, 1),
                         (box.right - 1, box.top, -1, 1),
                         (box.left, box.bottom - 1, 1, -1),
                         (box.right - 1, box.bottom - 1, -1, -1)):
        # LOOK EXCEPTION data: the planet owner's colour, as the original's highlight (sys.cpp:599-633)
        surface.fill(colour, pygame.Rect(min(x, x + sx * a), min(y, y + sy * t),
                                         a, t))
        surface.fill(colour, pygame.Rect(min(x, x + sx * t), min(y, y + sy * a),
                                         t, a))


def info_box(screen, surface, view, lines, colour=TEXT_COLOR):
    """Lines `[(text, gap_before)]` in the darkened box at the view's corner
    (`MISC::Draw_Darkened_Box_` at the content corner, sys.cpp:841, :1035)."""
    size = font(screen, "system_text", 16)
    gap = max(2, size // 3)
    surfs = [(screen.style.render_text(t, size, tuple(colour)[:3]), g)
             for t, g in lines if t]
    if not surfs:
        return
    pad = max(3, size // 3)
    w = max(sf.get_width() for sf, _g in surfs) + 2 * pad
    h = sum(sf.get_height() + (gap if g else 0) for sf, g in surfs) + 2 * pad
    box = pygame.Rect(view.x + pad, view.y + pad, w, h)
    shade = pygame.Surface(box.size, pygame.SRCALPHA)
    # LOOK EXCEPTION transcription: the original's darkened box under the lines (`Draw_Darkened_Box_`, sys.cpp:841)
    shade.fill((0, 0, 0, INFO_SHADE))
    surface.blit(shade, box.topleft)
    y = box.y + pad
    for sf, g in surfs:
        y += gap if g else 0
        surface.blit(sf, (box.x + pad, y))
        y += sf.get_height()


def planet_under(drawn, pointer):
    """The frontmost drawn planet under `pointer`, as (planet, rect)."""
    return next(((p, r) for p, r in reversed(drawn)
                 if r.collidepoint(pointer)), None)


def planet_info(screen, surface, view, drawn, pointer, state=None):
    """The planet under the pointer: its highlight and its lines
    (`sysinfo`, work order 226 F; sys.cpp:824-844). True if one was."""
    state = state if state is not None else getattr(screen, "_state", None)
    from core.buildnames import BuildingNames
    from core.estrings import EStrings
    from screens.galaxy_map import sysinfo
    from screens.planets import planetwords
    over = planet_under(drawn, pointer)
    if over is None or state is None:
        return False
    p, rect = over
    if getattr(screen, "_sysinfo_words", None) is None:
        lang = (getattr(screen.app, "settings", None) or {}).get(
            "language", "en")
        screen._sysinfo_words = (
            planetwords.Words(EStrings(lang), hestrings.for_app(screen.app)),
            BuildingNames(lang))
    words, names = screen._sysinfo_words
    s = sysorbits.frame(view)[0]
    highlight(surface, rect.center, s,
              tuple(owner_colour(sysinfo.owner_colour(state,
                                                      p["planet"])))[:3])
    info_box(screen, surface, view,
             sysinfo.lines(state, p["planet"], words, names))
    return True
