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

The window's look (work order 230 C, Data's decision 3, both windows):

  DATA'S DECISION `system_window_look`: the window is black with stars
                 (`sysstars`, the original's view), not filled with the
                 box fill — an exception to decisions 93 and 94; its frame
                 is a line in the blue of the original's lettering, and a
                 title panel across the top carries "Star System <name>"
                 in that blue. Lines drawn in code, no frame picture
                 (decision 71).
  TRANSCRIPTION  the blue: the title's colours `Font_Colors2_(4, 0x3C,
                 0x41)` (sys.cpp:944, :975) — its letters 0x41 (80, 108,
                 144), the shadow one native px down in 0x3D (32, 40, 76)
                 (`_Print_Centered_Shadow_Down_`, sys.cpp:986); FONTS.LBX
                 1's palette, and the most frequent title colour in Data's
                 picture of the original
  TRANSCRIPTION  the title panel: 0x49's panel colour, (24, 24, 32),
                 measured on the picture
  DEVIATION      `title_word_floor`: on that panel the original's 0x41
                 stands at 3.3:1; the title's letters are the same blue
                 raised until they keep decision 94's word floor (4.5:1
                 with its margin) — (98, 133, 177) on the shipped panel.
                 The frame keeps 0x41 exactly
  TRANSCRIPTION  the information box (planet and fleet): its edge the
                 original's `Draw_Highlight_Box_` (misc.cpp:396-438) in
                 0x3F-0x42 — outer top and right 0x42, inner 0x41, outer
                 left and bottom 0x3F, inner 0x40, one native px each —
                 round `Draw_Darkened_Box_(…, 0x3F)` (sys.cpp:841,
                 :1033); a planet's lines in `Font_Colors2_(2, 0x3C,
                 0x43)`'s letters 0x43 (104, 140, 176) (sys.cpp:1359)
  TRANSCRIPTION  the sun: BUFFER0.LBX 0x53 + class (sys.cpp:562-578), one
                 fixed picture whatever the map's zoom — HD's step-0 star
                 with as much light as it (`SUN_CANVAS_NATIVE`; until work
                 order 230 it took the map's zoom step, and shrank with it)
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
#: The window's look (work order 230 C): the original's palette, FONTS.LBX 1
#: indices 0x3D, 0x3F-0x43 (see the module docstring); moddable in the
#: skin's colors.json.
BLUE = palette.col("galaxy_map", "system_blue", (80, 108, 144))
TITLE_SHADOW = palette.col("galaxy_map", "system_title_shadow", (32, 40, 76))
TITLE_PANEL = palette.col("galaxy_map", "system_title_panel", (24, 24, 32))
INFO_TEXT = palette.col("galaxy_map", "system_info_text", (104, 140, 176))
#: `Draw_Highlight_Box_`'s four edges: outer top/right, inner top/right,
#: outer left/bottom, inner left/bottom (0x42, 0x41, 0x3F, 0x40).
INFO_EDGE = (palette.col("galaxy_map", "system_info_edge_outer_lit",
                         (92, 124, 160)),
             palette.col("galaxy_map", "system_info_edge_inner_lit",
                         (80, 108, 144)),
             palette.col("galaxy_map", "system_info_edge_outer_dim",
                         (56, 76, 108)),
             palette.col("galaxy_map", "system_info_edge_inner_dim",
                         (68, 92, 128)))
#: BUFFER0.LBX 0x49, native px: the whole picture, and the title panel's
#: band (its inner dark run, rows 12..37 of the picture, measured).
WINDOW_PICTURE = (347, 273)
TITLE_BAND = (12, 37)
#: HD's step-0 star canvas, native px, whose LIGHT covers as much as the
#: original's sun picture's (BUFFER0.LBX 0x53-0x58, 32-35 px pictures):
#: equal area above luminance 100, the median over the six classes
#: (42.6-58.7). Not stable under its threshold — a sweep 60 / 100 / 160
#: gives medians 55 / 52 / 40 (work order 230, P607): the middle is taken
#: and the spread said, since HD's star is not the original's drawing.
SUN_CANVAS_NATIVE = 52
#: Decision 94's word floor with its margin, for the title's letters.
WORD_FLOOR = 4.6


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


def native_scale(rect):
    """Device px per native px of a window drawn into `rect`."""
    return min(rect.w / WINDOW_PICTURE[0], rect.h / WINDOW_PICTURE[1])


def line_width(screen):
    return max(1, int(round(2 * screen.layout.scale)))


def title_panel(box, title):
    """The title panel: across the window, the title's band, inset from
    the frame as far as the title box is."""
    inset = max(0, title.x - box.x)
    return pygame.Rect(box.x + inset, title.y, box.w - 2 * inset, title.h)


def system_frame(screen, surface, box, title):
    """DATA'S DECISION `system_window_look` (work order 230 C): the window
    black with the original's stars, its frame a line in the lettering's
    blue, the title panel across the top — not the box fill (an exception
    to decisions 93 and 94)."""
    from screens.galaxy_map import sysstars
    s = native_scale(box)
    panel = title_panel(box, title)
    # LOOK EXCEPTION transcription: the original's window ground, Data's decision 3 (decision 94's exception)
    surface.fill(sysstars.GROUND[:3], box)
    below = pygame.Rect(box.x, panel.bottom, box.w, box.bottom - panel.bottom)
    sysstars.draw(screen, surface, below, s)
    lw = line_width(screen)
    # LOOK EXCEPTION transcription: 0x49's title panel colour, Data's decision 3
    pygame.draw.rect(surface, TITLE_PANEL[:3], panel)
    # LOOK EXCEPTION transcription: the frame in the title's blue, palette 0x41 (sys.cpp:944), Data's decision 3
    pygame.draw.rect(surface, BLUE[:3], panel, lw)
    # LOOK EXCEPTION transcription: the frame in the title's blue, palette 0x41 (sys.cpp:944), Data's decision 3
    pygame.draw.rect(surface, BLUE[:3], box, lw)
    return panel


def at_floor(colour, ground, floor=WORD_FLOOR):
    """DEVIATION `title_word_floor`: `colour` raised in brightness, its hue
    kept, until it stands at `floor` on `ground` (as it was if it does)."""
    import numpy as np
    from core.hud.glass import lum

    def ratio(c):
        a, b = float(lum(np.array(c, float))), float(lum(np.array(ground,
                                                                    float)))
        return (max(a, b) + 0.05) / (min(a, b) + 0.05)
    c = tuple(int(v) for v in colour[:3])
    k = 1.0
    while ratio(c) < floor and k < 4.0:
        k += 0.01
        c = tuple(min(255, int(round(v * k))) for v in colour[:3])
    return c


def title_colour():
    return at_floor(BLUE, TITLE_PANEL)


def title(screen, surface, rect, words, size, s):
    """The title in the blue with its shadow one native px down
    (`_Print_Centered_Shadow_Down_(…, 0x3D, …)`, sys.cpp:986); `s` device
    px per native px."""
    if not words:
        return
    drop = max(1, int(round(s)))
    shadow = screen.style.render_text(words, size, tuple(TITLE_SHADOW[:3]))
    face = screen.style.render_text(words, size, title_colour())
    x = rect.x + (rect.w - face.get_width()) // 2
    y = rect.y + (rect.h - face.get_height()) // 2
    surface.blit(shadow, (x, y + drop))
    surface.blit(face, (x, y))


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
        # The star's description, as `Print_Empty_System_Data_` sets it
        # (sys.cpp:1536-1593): a paragraph centred across and down the
        # view, in the window's blue (measured 0x41 on the original's
        # frame) — raised to the word floor on the ground, as the title
        from screens.galaxy_map import sysstars
        size = font(screen, "system_view", 16)
        lines = textfit.wrap_text(screen.style, model["body"], size,
                                  int(view.w * 0.9))
        colour = at_floor(BLUE, sysstars.GROUND)
        surfs = [screen.style.render_text(line, size, colour)
                 for line in lines]
        y = view.y + (view.h - sum(sf.get_height() for sf in surfs)) // 2
        for sf in surfs:
            surface.blit(sf, (view.x + (view.w - sf.get_width()) // 2, y))
            y += sf.get_height()
        return []
    stars = getattr(screen, "_stars", None) or []
    star = stars[model["star"]] if 0 <= model["star"] < len(stars) else None
    name = sun_icon_name(star)
    s, cx, cy = sysorbits.frame(view)
    # The sun in the rings' centre (`Draw_Sun_Seg_`, sys.cpp:562-578): the
    # original's fixed picture, ~32 native px of light, at every map zoom.
    sun = max(8, int(round(SUN_CANVAS_NATIVE * s)))
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


def sun_icon_name(star):
    """HD's star at its largest step — the window's sun is one fixed
    picture (BUFFER0.LBX 0x53 + class), not the map's zoom step."""
    if star is None:
        return None
    folder = rnd.CLASS_DIRS.get(star.spectral_class)
    return f"stars/{folder}/0" if folder else None


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


def info_box(screen, surface, view, lines, colour=INFO_TEXT):
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
    info_edge(surface, box, sysorbits.frame(view)[0])
    y = box.y + pad
    for sf, g in surfs:
        y += gap if g else 0
        surface.blit(sf, (box.x + pad, y))
        y += sf.get_height()


def info_edge(surface, box, s):
    """`Draw_Highlight_Box_` (misc.cpp:396-438) round the box: two lines a
    side, each one native px, lit top and right, dim left and bottom."""
    t = max(1, int(round(s)))
    outer_lit, inner_lit, outer_dim, inner_dim = (c[:3] for c in INFO_EDGE)
    for k, (lit, dim) in enumerate(((outer_lit, outer_dim),
                                    (inner_lit, inner_dim))):
        r = box.inflate(-2 * k * t, -2 * k * t)
        # LOOK EXCEPTION transcription: Draw_Highlight_Box_'s edges, palette 0x3F-0x42 (misc.cpp:396-438)
        surface.fill(lit, (r.x, r.y, r.w, t))
        # LOOK EXCEPTION transcription: Draw_Highlight_Box_'s edges, palette 0x3F-0x42 (misc.cpp:396-438)
        surface.fill(lit, (r.right - t, r.y, t, r.h))
        # LOOK EXCEPTION transcription: Draw_Highlight_Box_'s edges, palette 0x3F-0x42 (misc.cpp:396-438)
        surface.fill(dim, (r.x, r.y + t, t, r.h - t))
        # LOOK EXCEPTION transcription: Draw_Highlight_Box_'s edges, palette 0x3F-0x42 (misc.cpp:396-438)
        surface.fill(dim, (r.x, r.bottom - t, r.w, t))


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
