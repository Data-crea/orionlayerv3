"""Drawing the single-colony screen in the HUD style (decision 71).

Everything sits at the HD image of its native rectangle (`colgeom`,
through `core/researchnative` as `screens/leaders/ldrdraw` wraps it), so
the drawing, the hit test and a native screenshot speak the original's
coordinates. Panels are the HUD's glass panels, buttons its slanted
buttons, over the universal background.

WHAT IS TRANSCRIPTION AND WHAT IS OURS — each marked where it happens,
and each in `layout.json` `marks`, the status document and check 090p:

  TRANSCRIPTION  every position, every string (`colwords`), the values
                 (`colonyrows`: the net production, morale, the icon walk);
                 `scene` and `system_pictures` — the original's sky and
                 ground of the world and the system display's planets,
                 extracted by the player (`colart`, work order 223)
  HD EXTENSION   `surface_picture` — Data's picture of the colony's world,
                 by climate (decision 58), only where the original's
                 pictures are not extracted
  DEVIATION      `label_number` — a production row is an icon and a number,
                 a job row the figures of its pops; the original COUNTS
                 with sprites (decision 56's deviation, the Colonies
                 screen's)
  DEVIATION      `building_list` — the colony's buildings are a list of
                 names; UNVERIFIED `building_placement` — open fix 36's
                 grid is read and not placed (see `_buildings`)
  TRANSCRIPTION  `unit_figures`, `product_room` (work order 226 G, Data's
                 decision 6): the units at the screen's foot as the
                 original's figures, and the build box's grid room with the
                 product in it (`colroom`, the build popup's code)
  DEVIATION      `row_cells` (226 G): the band's cells — the production
                 rows, morale and the three job rows — ruled with the
                 shell's outline where the original's art rules them; a
                 job row's ruled cell is its field, the drop target
                 (decision 5)
  DEVIATION      `one_top` (226 G): the four boxes of the band share one
                 top and one height, the band's (17..158), where the
                 original's art boxes start at 17, 24 and 29
  OMISSION       `officer_portrait`, `hover_strip`, `roads`,
                 `planet_description` (the box `_drawing_display` 2 shows,
                 colony.cpp:1861-1866) — original art this project does
                 not extract, and the hover strip of the original's own
                 pointer; each named where it would be drawn
"""
import pygame

from core.hestrings import printf
from core.hud import blocks as hud
from core.hud import hover as hud_hover
from core.hud import text as hudtext
from core.structs import colony as colony_struct
from screens.colony_summary import colonyfigures, colonyoutputicons
from screens.colony_summary import colonyrows, colonysurfaces
from screens.colony_summary.colonyplanets import set_for as planet_set_for
from screens.leaders import ldrdraw as nd

from . import colart
from . import colgeom as geom
from . import colwire

#: `PLANET_TYPE` (orion2_consts.h:400-405).
ASTEROID, GAS_GIANT, PLANET = 1, 2, 3

#: DEVIATION `hd_font` (the Leaders screen's): text heights in native
#: pixels, from the line pitch each text sits on — the title's font 4
#: band (0..15), the system display's 7 px lines (colsysdi.cpp: two lines
#: in a 24 px row), the build window's name paragraph.
NATIVE_TEXT = {"title": 12, "line": 7, "value": 9, "button": 9, "small": 7}
#: Output icon master size — the Colonies screen's `output.icon_size`.
ICON_MASTER = 31
def font(layout, key):
    return max(nd.MIN_FONT,
               int(round(NATIVE_TEXT[key] * nd.native_scale(layout))))


def text(surface, screen, words, native_x, native_y, native_w, key, role,
         align="left", colour=None):
    """One line at a native anchor, fitted to a native width."""
    if not words:
        return None
    x, y = nd.point(screen.layout, native_x, native_y)
    w = nd.rect(screen.layout, (0, 0, native_w, 1)).w
    return nd.blit_text(surface, screen.style, words, x, y, w,
                        font(screen.layout, key),
                        colour or hudtext.colour(role), align=align)


def lines(surface, screen, words, native_x, native_y, native_w, key, role,
          pitch):
    """A paragraph whose `\\n` the original's `_Print_Paragraph_` breaks."""
    for i, line in enumerate((words or "").split("\n")):
        text(surface, screen, line, native_x, native_y + i * pitch,
             native_w, key, role)


# ── The whole picture ────────────────────────────────────────────────

def draw(surface, screen, view, state, words, names):
    layout = screen.layout
    _scene(surface, screen, view)
    # DEVIATION `one_top`: the band's four boxes share its top and height.
    top = min(b[1] for b in BAND_BOXES)
    bottom = max(b[3] for b in BAND_BOXES)
    for x0, _y0, x1, _y1 in BAND_BOXES:
        nd.draw_box(surface, screen, (x0, top, x1, bottom))
    _cells(surface, screen)
    _room(surface, screen, view, state)
    _title_line(surface, screen, view, state, words, names)
    _system(surface, screen, view, state, words)
    _production(surface, screen, view)
    _jobs(surface, screen, view, state)
    _no_farming(surface, screen, view, words)
    _build(surface, screen, view, state, words, names)
    _buildings(surface, screen, view, state, names)
    _units(surface, screen, view, words, state)
    _officer(surface, screen, view, state, words)
    _buttons(surface, screen, state)
    return layout


#: The band's four boxes, the original art's (COLPUPS.LBX 5): the system
#: display, production, population, the build window.
BAND_BOXES = (geom.SYS_DISP, (124, 29, 304, 152), (307, 29, 512, 152),
              geom.BUILD_WINDOW)


def _cells(surface, screen):
    """DEVIATION `row_cells`: each production row, the morale row and each
    job row in a ruled cell, the shell's outline — the original's band art
    rules them. A job row's cell IS its drop target (`colgeom.JOB_CELLS`,
    which `screen._job_click` hits), so the drawn cell is the hit cell
    (decision 5)."""
    for native in list(geom.PROD_ROWS.values()) + [geom.MORALE] + \
            list(geom.JOB_CELLS):
        hud.outline(surface, nd.rect(screen.layout, native),
                    screen.layout.scale)


def _room(surface, screen, view, state):
    """TRANSCRIPTION `product_room`: the build window's grid room with the
    product standing in it, where the original draws it (`Draw_Info_Build_`,
    colony_main.cpp:899-945) — `colroom`'s colony place, the build popup's
    code; stepped up as the screen's sprites are (`nd.magnified`)."""
    from screens.build_queue import bqproduct
    from . import colroom
    pid = view.colony.producing[0]
    race = _race(state, int(view.colony.owner))
    ship = None
    from core import prodname
    from core.structs import ship as ship_struct
    if prodname.kind(pid) == prodname.KIND_QUEUED_SHIP:
        ships = getattr(state, "ships_raw", None) or []
        i = prodname.QUEUED_SHIP_BASE - pid
        if 0 <= i < len(ships):
            ship = ship_struct.parse(ships[i])
    spec = bqproduct.picture(pid, race, None, ship) or ("room",)
    t = colroom.tile(spec, view.colony.climate, _bg_type(view), "colony")
    if t is None:
        return
    win = colroom.PLACES["colony"]["window"]
    r = nd.rect(screen.layout, win)
    big = nd.magnified(t, screen.layout)
    clip = surface.get_clip()
    surface.set_clip(r)
    surface.blit(big, big.get_rect(center=r.center))
    surface.set_clip(clip)


def _race(state, owner):
    from core.structs import player as player_struct
    raws = getattr(state, "player_raw", None) or []
    return int(player_struct.parse(raws[owner]).race) \
        if 0 <= owner < len(raws) else 0


def _scene(surface, screen, view):
    """TRANSCRIPTION `scene` (work order 223): the original's own picture
    of the world — COLONY2.LBX's sky with PLANETS.LBX's ground of the
    colony's climate and the planet's ground type over it, in the screen's
    palette (`colart`; colony_main.cpp:111-115, :475-479) — the part under
    the band, each native pixel to its exact HD rectangle. Without the
    extracted pictures, HD EXTENSION `surface_picture`: decision 58's
    painting of the world by climate; nothing where that is absent too."""
    r = nd.rect(screen.layout, geom.SCENE)
    art = colart.load()
    pic = art.scene(view.colony.climate, _bg_type(view)) \
        if art.available else None
    if pic is not None:
        x0, y0, x1, y1 = geom.SCENE
        crop = pic.subsurface(pygame.Rect(x0, y0, x1 - x0 + 1, y1 - y0 + 1))
        surface.blit(nd.stretched(crop, r), r.topleft)
        return
    pics = colonysurfaces.set_for(screen)
    pic = pics.get(view.colony.climate) if pics is not None else None
    if pic is None:
        return
    scaled = pygame.transform.smoothscale(pic, r.size)
    surface.blit(scaled, r.topleft)


def _first_planet_word(screen):
    """H_Message 0xA0, the first planet's word ("Prime"); None without the
    game's table, and the numeral stays."""
    from core import hestrings
    table = hestrings.for_app(screen.app)
    return table.message(0xA0) if table is not None else None


def _bg_type(view):
    planet = getattr(view, "planet", None)
    return int(getattr(planet, "climate_bg_type", 0) or 0) if planet else 0


def system_picture(art, planet, state, view):
    """The system display's drawing of one orbit's planet: COLSYSDI by the
    COLONY'S climate where the planet has one (a terraformed world shows
    its new climate) and its size; a gas giant, an asteroid belt
    (colsysdi.cpp:15-33). In the palette of the world shown."""
    climate = planet.climate
    ci = getattr(planet, "colony_index", -1)
    raws = getattr(state, "colonies_raw", None) or []
    if ci is not None and 0 <= ci < len(raws):
        climate = colony_struct.parse(raws[ci]).climate
    stem = {GAS_GIANT: "gas_giant", ASTEROID: "asteroids"}.get(
        planet.planet_type) or colart.planet_stem(climate, planet.size)
    return None if stem is None else art.sprite(
        stem, view.colony.climate, _bg_type(view))


def title_words(screen, view, words, names):
    """The colony's title: `Get_Planet_Name_` with the "Prime" word
    (colony.cpp:1019-1039; haccess.cpp:216-221), not the lists' No_Prime
    form (work order 223). On the shell's plate since work order 225."""
    name = colonyrows.planet_name(view.colony, names.planets, names.stars,
                                  first=_first_planet_word(screen))
    return words.title(view, name)


def _title_line(surface, screen, view, state, words, names):
    # The title stands on the shell's plate (work order 225,
    # `screen._shell_title`); the original's place is `geom.TITLE_CENTRE`.
    # Blockaded, Plague or Pop Boom (open fix 37), or nothing at all.
    status = words.status(view, getattr(state, "player_num", 0), state)
    text(surface, screen, status, *geom.STATUS_AT, 120, "value",
         "negative")
    text(surface, screen, words.pop(view), *geom.POP_RIGHT, 128, "value",
         "value", align="right")


def _system(surface, screen, view, state, words):
    """`Draw_Col_Sys_Disp_` (colsysdi.cpp:8-48): each orbit's marker and
    its planet's own drawing, magnified to the window (decision 28)
    (TRANSCRIPTION `system_pictures`, work order 223). Without the
    extracted pictures, decision 58's climate disc for a planet."""
    art = colart.load()
    size = max(1, int(20 * nd.native_scale(screen.layout)))
    planets = None if art.available else planet_set_for(screen, size)
    for i, planet in enumerate(view.system):
        (cx, cy), (tx, ty) = geom.sys_row(i)
        if art.available:
            mark = art.sprite("marker", view.colony.climate, _bg_type(view))
            if mark is not None:
                _centred(surface, screen, nd.magnified(mark, screen.layout),
                         geom.SYS_X + 2, geom.SYS_Y + i * geom.SYS_ROW + 12)
        if planet is None:
            continue
        if art.available:
            pic = system_picture(art, planet, state, view)
            pic = nd.magnified(pic, screen.layout) if pic is not None \
                else None
        else:
            pic = planets.get(planet.climate) if planets is not None and \
                planet.planet_type == PLANET else None
        if pic is not None:
            x, y = nd.point(screen.layout, cx, cy)
            surface.blit(pic, (x - pic.get_width() // 2,
                               y - pic.get_height() // 2))
        lines(surface, screen, words.summary(planet, state), tx, ty,
              geom.SYS_TEXT_W, "line", "label", 8)


def _centred(surface, screen, pic, native_x, native_y):
    """`ERIC::Draw_Centered_` at a native point."""
    x, y = nd.point(screen.layout, native_x, native_y)
    surface.blit(pic, (x - pic.get_width() // 2, y - pic.get_height() // 2))


def _production(surface, screen, view):
    """DEVIATION `label_number`: the original's own net, as a number
    beside its icon (`colonyrows.drawn_production`, coldraw.cpp:36-181)."""
    layout = screen.layout
    icons = _icons(screen)
    for econ, native in geom.PROD_ROWS.items():
        value = colonyrows.drawn_production(view.colony, econ)
        name = colonyoutputicons.RESOURCE_NAMES[econ]
        _icon_value(surface, screen, icons, name, native, value)
    # Under Unification the original draws no marks at all, which is not
    # a morale of 0 — so nothing is drawn (`colony_morale`'s `applies`).
    morale, applies = colonyrows.colony_morale(view.colony,
                                               view.owner_traits)
    if applies:
        _icon_value(surface, screen, icons, colonyrows.morale_icon(morale),
                    geom.MORALE, morale)
    return layout


def _icon_value(surface, screen, icons, name, native, value):
    r = nd.rect(screen.layout, native)
    icon = icons.icons.get(name) if icons is not None else None
    x = r.x + max(2, r.h // 8)
    if icon is not None:
        surface.blit(icon, (x, r.centery - icon.get_height() // 2))
        x += icon.get_width() + max(2, r.h // 6)
    colour = hudtext.colour("negative" if value < 0 else "value")
    size = font(screen.layout, "value")
    surf = screen.style.render_text(str(value), size, colour)
    surface.blit(surf, (x, r.centery - surf.get_height() // 2))


def _icons(screen):
    size = max(1, int(round(ICON_MASTER / 32 * nd.rect(
        screen.layout, geom.PROD_ROWS[0]).h * 0.8)))
    cache = getattr(screen, "_icon_cache", None)
    if cache is None or cache[0] != size:
        cache = (size, colonyoutputicons.IconSet(screen.app.res, ICON_MASTER,
                                                 size))
        screen._icon_cache = cache
    return cache[1]


def figure_size(screen):
    return max(4, int(nd.rect(screen.layout, geom.JOB_ROWS[0]).h * 0.9))


def job_cells(screen, view):
    """Every drawn pop cell: (job, k, window rect, cell) — ONE function for
    the drawing and the click (decision 5). The figures of a job in the
    original's icon order (`row["cells"]`, decision 48), squeezed into the
    row as `Calculate_Squish_Step_` squeezes (coldraw.cpp:12-34): the full
    pitch while they fit, the room divided evenly when they do not."""
    row = view.row
    if row is None:
        return []
    size = figure_size(screen)
    span = nd.rect(screen.layout, (geom.JOB_ICON_X[0], 0,
                                   geom.JOB_ICON_X[1], 1)).w
    out = []
    for job, native in enumerate(geom.JOB_ROWS):
        r = nd.rect(screen.layout, native)
        cells = row["cells"][job] if job < len(row["cells"]) else ()
        n = len(cells)
        pitch = size if n < 2 else min(size, max(1, (span - size) // (n - 1)))
        for k, cell in enumerate(cells):
            out.append((job, k, pygame.Rect(r.x + k * pitch, r.y,
                                            pitch, r.h), cell))
    return out


def _jobs(surface, screen, view, state):
    """DEVIATION `label_number`'s pop half: each job's figures (see
    `job_cells`); the HD pick is outlined, and nothing was sent for it."""
    size = figure_size(screen)
    if getattr(screen, "_fig_size", None) != size:
        screen._figures = colonyfigures.FigureSet(screen.app.res, size)
        screen._fig_size = size
    figures = screen._figures
    held = screen.pick_cells()
    for job, k, rect, cell in job_cells(screen, view):
        pic = figures.get(cell.figure) if figures.state != "missing" \
            else None
        if pic is not None:
            surface.blit(pic, (rect.x, rect.bottom - pic.get_height()))
        else:
            pygame.draw.rect(surface, hudtext.colour("label"),
                             rect.inflate(-2, -4), 1)
        if (job, k) in held:
            hud.outline(surface, rect, screen.layout.scale)


def _no_farming(surface, screen, view, words):
    """"No Farming", centred in the farmers' row: `Squeeze_Print_Paragraph_(
    left_x, top_y + 5, right_x - left_x, 28, E 387, 2)` with the row's
    (310, 62)-(510) (colony.cpp:1332-1345, coldraw.cpp:315-321) — 2 is the
    centred mode. Found missing by work order 181's side-by-side."""
    x1, y1, x2, _y2 = geom.JOB_ROWS[0]
    text(surface, screen, words.no_farming(view), (x1 + 510) // 2, y1 + 5,
         510 - x1, "value", "label", align="center")


def _build(surface, screen, view, state, words, names):
    """The production window: name, bar, turns, the autobuild label."""
    layout = screen.layout
    pid = view.colony.producing[0]
    name, _st = names.product(pid, state)
    x1, y1, x2, y2 = geom.BUILD_NAME
    text(surface, screen, name, (x1 + x2) // 2, y1, x2 - x1, "value",
         "value", align="center")
    text(surface, screen, words.autobuild(view), *geom.AUTOBUILD_CENTRE,
         110, "small", "label", align="center")
    cost, turns = view.product(state)        # open fix 38
    spent = cost if view.colony.bought_outright else \
        view.colony.production_spent
    # DEVIATION `production_bar`: the original draws two frames of its art
    # (C_Anims_ 34/35, frames 0..50, coldraw.cpp:249-280) — a box whose
    # size is not in the source. HD draws a bar filled current / total in
    # the box the art covers, measured off the native frame (work order 208
    # B2): it ends above the turns line at y 103 (colony.cpp:993), which
    # the 64 px column HD drew before ran through.
    bar = nd.rect(layout, geom.BUILD_BAR_BOX)
    pygame.draw.rect(surface, hudtext.colour("label"), bar, 1)
    if cost > 0:
        filled = max(0, min(bar.h - 2, (bar.h - 2) * spent // cost))
        pygame.draw.rect(surface, hudtext.colour("button"),
                         (bar.x + 1, bar.bottom - 1 - filled,
                          bar.w - 2, filled))
    text(surface, screen, words.turns(turns), *geom.BUILD_TURNS_RIGHT, 80,
         "small", "value", align="right")
    return layout


def _buildings(surface, screen, view, state, names):
    """DEVIATION `building_list`: the colony's buildings as a list.

    UNVERIFIED `building_placement`: open fix 36's grid is parsed, and its
    OCCUPIED CELLS are verified — every one lands on a live building field
    (`colgeom.building_field`, check 090p). What a cell's id MEANS for the
    scene is not: `Make_Bldg_Array_For_Colony_` also puts housing (-3) in
    the grid and jitters satellites into it (colony_main.cpp:559-600), and
    the recorded grids name Star Base and Star Fortress twice where the
    native scene shows each once. So nothing is placed from it."""
    ids = view.buildings()
    if not ids:
        return
    box = (8, 160, 150, min(430, 166 + 10 * len(ids)))
    nd.draw_box(surface, screen, box)
    for i, bid in enumerate(ids):
        text(surface, screen, names.building(bid), 14, 164 + 10 * i, 132,
             "small", "label")


#: `Military_Anim_` (colony.cpp:1308-1328): marines (0) are figure 1, or 2
#: with Powered Armor (application 144); armour (1) is 3, or 4 with
#: Battleoids (24); a figure is RACEICON race * 13 + figure + 6.
MILITARY_FIGURES = {0: (1, 2, 144), 1: (3, 4, 24)}
RESEARCHED = 3


def unit_layout(counts):
    """`Do_Colony_Info_Military_Stuff_For_` (colony_main.cpp:1193-1290),
    both kinds in order: [(kind, slot, count)] — a figure at native
    x = slot * 30 on the screen's foot (:1222, :1239), and `count` printed
    at x = (slot + 1) * step beside it (or None, :1248). Eight units or
    fewer are drawn one figure each; more, and each kind is one figure and
    its count (`E 0x7C`), the next kind three slots on. Returns (figures,
    step)."""
    total = max(1, sum(counts))
    step = max(1, 260 // total)
    squish = 30 - step if step < 30 else 0
    out, start = [], 0
    for kind, n in enumerate(counts):
        if n <= 0:
            continue
        if squish == 0:
            for k in range(n):
                out.append((kind, start + k, None))
            start += n
        else:
            out.append((kind, start, n))
            start += 3
    return out, (30 - squish)


def _units(surface, screen, view, words, state=None):
    """TRANSCRIPTION `unit_figures` (work order 226 G, Data's decision 6):
    the units at the screen's foot as the original draws them — the
    owner's race's figures (`Military_Anim_`), on the bottom edge, the
    count `E 0x7C` beside a lone figure (`unit_layout`)."""
    from . import colart
    counts = view.units()
    figures, step = unit_layout(counts)
    if not figures:
        return
    art = colart.load()
    owner = int(view.colony.owner)
    race = _race(state, owner) if state is not None else 0
    apps = _tech_apps(state, int(getattr(state, "player_num", 0) or 0)) \
        if state is not None else ()
    for kind, slot, count in figures:
        plain, better, app = MILITARY_FIGURES[kind]
        fig = better if len(apps) > app and apps[app] == RESEARCHED else plain
        pic = art.sprite(f"military_{race}_{fig}", view.colony.climate,
                         _bg_type(view)) if art.available else None
        x_native = slot * 30
        height = pic.get_height() if pic is not None else 12
        if pic is not None:
            big = nd.magnified(pic, screen.layout)
            surface.blit(big, nd.point(screen.layout, x_native,
                                       479 - height))
        if count is not None:
            fmt = words.e(0x7C) or "x %d"
            text(surface, screen, printf(fmt, count),
                 (slot + 1) * step, 479 - height, 60, "value", "value")


def _tech_apps(state, player):
    from core.structs import player as player_struct
    raws = getattr(state, "player_raw", None) or []
    if not 0 <= player < len(raws):
        return ()
    return list(player_struct.parse(raws[player]).tech_applications)


def _officer(surface, screen, view, state, words):
    """`Draw_Colony_Info_Officer_` (colony.cpp:706-734): the star's slot for
    the player, then the name or `E 285` with the ETA. OMISSION
    `officer_portrait`."""
    got = view.officer(state)
    if got is None:
        return                 # no frame either (colony.cpp:709)
    nd.draw_box(surface, screen, geom.OFFICER_FRAME)
    name, eta = got
    line = printf(words.e(285) or "%d", eta) if eta > 0 else name
    text(surface, screen, line, *geom.OFFICER_NAME_CENTRE, 80, "small",
         "value", align="center")


def _buttons(surface, screen, state):
    """CHANGE, BUY, LEADERS, RETURN — where the live list has them."""
    fields = getattr(state, "fields", None)
    for key, ident in (("change", geom.CHANGE), ("buy", geom.BUY),
                       ("leaders", geom.LEADERS), ("return", geom.RETURN)):
        f = colwire.live_field(fields, ident)
        if f is None:
            continue
        r = nd.rect(screen.layout, (f.x, f.y, f.x_end, f.y_end))
        dim = key == "buy" and f.field_type != geom.TYPE_BUTTON
        hud.slant_button(surface, r, screen.layout.scale,
                         "disabled" if dim else hud_hover.pointer_state(r),
                         screen.word(key), style_renderer=screen.style)
