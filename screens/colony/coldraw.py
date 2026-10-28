"""Drawing the single-colony screen in the HUD style (decision 71).

Everything sits at the HD image of its native rectangle (`colgeom`,
through `core/nativeview` as `core/nativedraw` wraps it), so
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
  TRANSCRIPTION  `prod_symbols` (work order 326): the four production rows
                 count with the original's symbols (`colprod`)
  HD EXTENSION   `row_end_number` (326): the row's value at its end
  DEVIATION      `label_number` — without the extracted symbols a
                 production row is an icon and a number; morale its mask
                 and its value; a job row the figures of its pops; the
                 original COUNTS with sprites (decision 56's deviation,
                 the Colonies screen's)
  DEVIATION      `figure_on_line` (326): a figure's ink stands on its
                 cell's line, the original's canvas hangs from the row top
  TRANSCRIPTION  `building_sprites` (work order 326, `colbuildings`): the
                 colony's buildings drawn as the original's sprites from open
                 fix 36's grid, its satellites in the sky; HD EXTENSION: at
                 a whole step in the surface panel's lower part
  DEVIATION      `building_list` — the colony's buildings are also a list of
                 names (the right click and the demolish ask through it),
                 beside the city; UNVERIFIED `building_placement` — see
                 `_buildings`
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
  OMISSION       `veggies` (326): COLVEGGI's plants between the buildings
  OMISSION       `officer_portrait`, `hover_strip`, `roads` — original
                 art this project does not extract, and the hover strip
                 of the original's own pointer; each named where it would
                 be drawn
  TRANSCRIPTION  `planet_description` (work order 315, seen live): the box
                 `_drawing_display` 2 shows (colony.cpp:1861-1866) is the
                 game's own and comes back as HD's message box
"""
import pygame

from core.hestrings import printf
from core.hud import blocks as hud
from core.hud import hover as hud_hover
from core.hud import text as hudtext
from core.structs import colony as colony_struct
from screens.colony_summary import colonyfigures, colonyoutputicons
from core import colonyfacts
from screens.colony_summary import colonysurfaces, colonytrack
from screens.colony_summary.colonyplanets import painted as painted_planet
from screens.colony_summary.colonyplanets import set_for as planet_set_for
from core import nativedraw as nd

from . import colart
from . import colbuildings
from . import colroads
from . import colprod
from . import colsurface
from . import colgeom as geom
from . import colwire

#: `PLANET_TYPE` (orion2_consts.h:400-405).
ASTEROID, GAS_GIANT, PLANET = 1, 2, 3

#: DEVIATION `hd_font` (the Leaders screen's): text heights in native
#: pixels, from the line pitch each text sits on — the title's font 4
#: band (0..15), the system display's 7 px lines (colsysdi.cpp: two lines
#: in a 24 px row), the build window's name paragraph.
NATIVE_TEXT = {"title": 12, "line": 7, "value": 9, "button": 9, "small": 7,
               "number": 17}
#: "number": HD EXTENSION `row_end_number`'s size, measured off Data's
#: numbers_mockup.png (work order 326): its digits are 26 px in a 65 px
#: row, 0.4 of it; the HD font's digits are 0.7 of its size (21 px at
#: 30, measured), so 0.4 / 0.7 of the 30 native px row: 17.
#: Output icon master size — the Colonies screen's `output.icon_size`.
ICON_MASTER = 31
def font(layout, key):
    return max(nd.MIN_FONT,
               int(round(NATIVE_TEXT[key] * nd.native_scale(layout))))


def text(surface, screen, words, native_x, native_y, native_w, key, role,
         align="left", colour=None, size=None):
    """One line at a native anchor, fitted to a native width (`size`: a
    window size below the key's, for a row the panel squeezes)."""
    if not words:
        return None
    x, y = nd.point(screen.layout, native_x, native_y)
    # THE WIDTH WHERE THE LINE STANDS (work order 231 E): each panel has a
    # scale of its own, and a width measured at (0, 0) is the first
    # panel's; right-aligned and centred lines reach back from the anchor
    x0 = native_x - (native_w if align == "right" else
                     native_w // 2 if align == "center" else 0)
    w = nd.rect(screen.layout, (x0, native_y, x0 + native_w - 1,
                                native_y)).w
    return nd.blit_text(surface, screen.style, words, x, y, w,
                        min(size or 10 ** 6, font(screen.layout, key)),
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
    # THE SHELL'S PANELS (work order 231 E, Data's decision 7): the band's
    # four windows side by side across the content rectangle, the surface
    # under them — each a box of its own (`colgeom.BAND_REGIONS`,
    # `SURFACE_REGION`), the panel drawn where the box is.
    # DEVIATION `one_top`: the band's four boxes share its top and height.
    for name, _native in geom.BAND_REGIONS + (geom.SURFACE_REGION,):
        r = screen.box_screen_rect(name)
        if r is not None:
            hud.panel(surface, r, layout.scale)
    _scene(surface, screen, view)
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
    _buttons(surface, screen, state)
    return layout


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
    # the colour of the ship's builder: the queued ship's previous owner,
    # else the local player (`Remap_Draw_Ship_Seg_N_Centered` takes
    # MOX::PLAYER_NUM, colony.cpp:1186)
    owner = int(ship.previous_owner) if ship is not None else \
        int(getattr(state, "player_num", 0) or 0)
    colour = colroom.owner_colour(state, owner)
    t = colroom.tile(spec, view.colony.climate, _bg_type(view), "colony",
                     colour)
    if t is None:
        return
    win = colroom.PLACES["colony"]["window"]
    r = nd.rect(screen.layout, win)
    big = nd.magnified(t, screen.layout)
    clip = surface.get_clip()
    surface.set_clip(r)
    at = big.get_rect(center=r.center)
    surface.blit(big, at)
    colroom.overlay(surface, spec, colour, view.colony.climate,
                    _bg_type(view), "colony", at.topleft,
                    big.get_width() // t.get_width())
    surface.set_clip(clip)


def _race(state, owner):
    from core.structs import player as player_struct
    raws = getattr(state, "player_raw", None) or []
    return int(player_struct.parse(raws[owner]).race) \
        if 0 <= owner < len(raws) else 0


def scene_rect(screen):
    """Where the surface picture stands: the surface panel less the
    shell's inset — the window `PanelMap` carries the surface region
    into, so what stands on the picture stands where it is drawn."""
    from core.hud import shell
    r = screen.box_screen_rect(geom.SURFACE_REGION[0])
    return shell.inner(r, screen.app.layout) if r is not None else None


#: Where today's picture is cut when its panel is flatter than it: 0.0
#: keeps its top (the sky and the horizon), 1.0 its foot. Data's decision 3
#: (work order 232, answering 231 P2): the panel's format stays, what is
#: cut does not matter — a picture in the format is made for it
#: (`colsurface`), and that one fills the panel whole. HD's choice is the
#: top, as built in 231; the original shows its picture whole.
COVER_ANCHOR = 0.0


def cover(pic, rect, anchor=None):
    """`pic` scaled to cover `rect` in its own proportion and cut to it at
    `COVER_ANCHOR` — a picture, not a box (work order 231 E): never
    stretched to the panel. DEVIATION `surface_cover`: the original's
    picture is whole at 640 x 328; a panel of another shape shows a cut."""
    a = COVER_ANCHOR if anchor is None else anchor
    k = max(rect.w / float(pic.get_width()), rect.h / float(pic.get_height()))
    w, h = max(1, int(round(pic.get_width() * k))), \
        max(1, int(round(pic.get_height() * k)))
    big = pygame.transform.scale(pic, (w, h))
    x = (w - rect.w) // 2
    y = int(round((h - rect.h) * a)) if h > rect.h else 0
    return big.subsurface(pygame.Rect(x, y, min(rect.w, w - x),
                                      min(rect.h, h - y)))


def _scene(surface, screen, view):
    """TRANSCRIPTION `scene` (work order 223): the original's own picture
    of the world — COLONY2.LBX's sky with PLANETS.LBX's ground of the
    colony's climate and the planet's ground type over it, in the screen's
    palette (`colart`; colony_main.cpp:111-115, :475-479) — the part under
    the band. Since work order 231 E it fills the surface panel inside the
    content rectangle and ends there (decision 89: a frame is drawn round
    the rectangle, so nothing of the screen may run past it), in its own
    proportion (`cover`). Without the extracted pictures, HD EXTENSION
    `surface_picture`: decision 58's painting of the world by climate;
    nothing where that is absent too."""
    r = scene_rect(screen)
    if r is None:
        return
    # A picture in the screen's own format (work order 232) wins over the
    # original's: HD EXTENSION `surface_format_picture`.
    climate, ground = view.colony.climate, _bg_type(view)
    pic = colsurface.picture(climate, ground, screen.app.res)
    source = "format"
    art = colart.load()
    if pic is None and art.available:
        source = "original"
        pic = art.scene(climate, ground)
        if pic is not None:
            x0, y0, x1, y1 = geom.SCENE
            pic = pic.subsurface(pygame.Rect(x0, y0, x1 - x0 + 1,
                                             y1 - y0 + 1))
    if pic is None:
        source = "painting"
        pics = colonysurfaces.set_for(screen)
        pic = pics.get(climate) if pics is not None else None
    if pic is None:
        return
    # One scale per world, source and panel size, not one a frame: a
    # picture made in the format can be a 4K one (work order 232). A format
    # picture is named by its object, which `colsurface` keeps for the
    # session (so its id is never reused, P828); the other two are fixed
    # per world.
    key = (source, id(pic) if source == "format" else None, climate,
           ground, r.size, COVER_ANCHOR)
    got = _COVERED.get(key)
    if got is None:
        if len(_COVERED) >= 4:
            _COVERED.clear()
        got = _COVERED[key] = cover(pic, r)
    surface.blit(got, r.topleft)


#: `_scene`'s covered pictures (a window shows one colony at a time; four
#: is that with a resize and the next colony).
_COVERED = {}


def _first_planet_word(screen):
    """H_Message 0xA0, the first planet's word ("Prime"); None without the
    game's table, and the numeral stays."""
    from core import hestrings
    table = hestrings.for_app(screen.app)
    return table.message(0xA0) if table is not None else None


def _bg_type(view):
    planet = getattr(view, "planet", None)
    return int(getattr(planet, "climate_bg_type", 0) or 0) if planet else 0


def _shown_climate(planet, state):
    """The climate the system display shows for a planet: the colony's where
    it has one (a terraformed world shows its new climate)."""
    ci = getattr(planet, "colony_index", -1)
    raws = getattr(state, "colonies_raw", None) or []
    if ci is not None and 0 <= ci < len(raws):
        return colony_struct.parse(raws[ci]).climate
    return planet.climate


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
    name = colonyfacts.planet_name(view.colony, names.planets, names.stars,
                                  first=_first_planet_word(screen))
    return words.title(view, name)


def title_line_rects(screen):
    """(status rect, pop rect) in window px: the original's title line
    (`Draw_Info_Name_And_Pop_`, colony_main.cpp:806-873) prints the status
    word at its left (0, 0), the title centred, "Pop" right-aligned at its
    right (638, 3) — so with the title on the shell's plate (work order
    225) the two stand BESIDE the plate on its text line: the status word
    from the content rectangle's left edge to the plate, "Pop" from the
    plate to the rectangle's right edge (work order 232; until then both
    stood inside the first and the last band panel, under the plate's
    line). The help regions 484 and 486 are these rects (decision 5)."""
    from core.hud import shell
    lay = screen.ref_layout
    c = shell.content(lay)
    plate, line = shell.title_rects(lay)
    return (pygame.Rect(c.x, line.y, max(1, plate.x - c.x), line.h),
            pygame.Rect(plate.right, line.y, max(1, c.right - plate.right),
                        line.h))


def _title_line(surface, screen, view, state, words, names):
    # The title stands on the shell's plate (work order 225,
    # `screen._shell_title`); the original's place is `geom.TITLE_CENTRE`.
    # Blockaded, Plague or Pop Boom (open fix 37), or nothing at all.
    status = words.status(view, getattr(state, "player_num", 0), state)
    size = font(screen.layout, "value")
    left, right = title_line_rects(screen)
    for words_, r, role, align, x in (
            (status, left, "negative", "left", left.x),
            (words.pop(view), right, "value", "right", right.right)):
        if words_:
            nd.blit_text(surface, screen.style, words_, x,
                         r.y + (r.h - size) // 2, r.w, size,
                         hudtext.colour(role), align=align)


def _system(surface, screen, view, state, words):
    """`Draw_Col_Sys_Disp_` (colsysdi.cpp:8-48): each orbit's marker and
    its planet's own drawing, magnified to the window (decision 28)
    (TRANSCRIPTION `system_pictures`, work order 223). Without the
    extracted pictures, decision 58's climate disc for a planet."""
    art = colart.load()
    size = max(1, int(20 * nd.native_scale(screen.layout)))
    # WO 331: a planet is a turning sphere here too, at the sprite's own
    # size, whether or not the original's pictures are extracted
    for i, planet in enumerate(view.system):
        (cx, cy), (tx, ty) = geom.sys_row(i)
        if art.available:
            mark = art.sprite("marker", view.colony.climate, _bg_type(view))
            if mark is not None:
                _centred(surface, screen, nd.magnified(mark, screen.layout),
                         geom.SYS_X + 2, geom.SYS_Y + i * geom.SYS_ROW + 12)
        if planet is None:
            continue
        pic = None
        if art.available:
            pic = system_picture(art, planet, state, view)
            pic = nd.magnified(pic, screen.layout) if pic is not None \
                else None
            # Data's painted planet at the drawing's own size, where the
            # mod folder has one (DEVIATION `painted_planets`).
            if pic is not None and planet.planet_type == PLANET:
                pic = painted_planet(screen.app.res, planet.climate,
                                     getattr(planet, "size", None),
                                     max(pic.get_size())) or pic
        if planet.planet_type == PLANET:
            disc = planet_set_for(screen, max(pic.get_size()) if pic
                                  is not None else size)
            turning = disc.get(_shown_climate(planet, state),
                               view.system_ids[i]) if disc is not None \
                else None
            if turning is not None:
                pic = turning
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
    """TRANSCRIPTION `prod_symbols` (work order 326): the BC, food,
    industry and research rows count with the original's symbols, as many
    and grouped as `Draw_Colony_Prod_Both_` draws them (coldraw.cpp:36-181,
    `colprod`) — centred on the ruled cell (DEVIATION `row_cells`), where
    the original stands them 0 or 2 px under its row's top — and
    HD EXTENSION `row_end_number` puts the row's value at its right end
    (Data's mockup). Without the extracted symbols, DEVIATION
    `label_number`: the original's own net as a number beside Data's icon
    (`colonyfacts.drawn_production`)."""
    layout = screen.layout
    icons = _icons(screen)
    if not colprod.draw_rows(surface, screen, view, _bg_type(view),
                             geom.PROD_ROWS, font(layout, "number")):
        for econ, native in geom.PROD_ROWS.items():
            value = colonyfacts.drawn_production(view.colony, econ)
            name = colonyoutputicons.RESOURCE_NAMES[econ]
            _icon_value(surface, screen, icons, name, native, value)
    # Under Unification the original draws no marks at all, which is not
    # a morale of 0 — so nothing is drawn (`colony_morale`'s `applies`).
    morale, applies = colonyfacts.colony_morale(view.colony,
                                               view.owner_traits)
    if applies:
        _icon_value(surface, screen, icons, colonyfacts.morale_icon(morale),
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
    `job_cells`). Colonists in hand are not in their row — the view was
    built without them (TRANSCRIPTION `carry`) — and nothing marks the
    row they came from, as the original marks nothing.

    DEVIATION `figure_on_line` (work order 326, Data's pictures: the
    Colonies screen's figures stand on their line, these floated): the
    figure's last INKED row stands on the cell's bottom line, the
    Colonies screen's rule (`colonytrack.figure_origin_y`, decision of
    12 September 2026). The original puts the sprite's CANVAS TOP at the
    row's top (`Do_Colony_Info_Pop_Stuff_For_Pop_`, coldraw.cpp:281-440,
    rows `type * 30 + 62`, colony.cpp:1293-1309) and its band art draws
    the rules, so its ink ends some px above the row's end."""
    size = figure_size(screen)
    if getattr(screen, "_fig_size", None) != size:
        screen._figures = colonyfigures.FigureSet(screen.app.res, size)
        screen._fig_size = size
    figures = screen._figures
    # `figure_origin_y` assumes a one-px plate line; this cell's outline
    # is `outline_width` thick (two px at 3840x2160), so the floor rises
    # by the difference or the foot would stand IN the line.
    thicker = hud.outline_width(screen.layout.scale) - \
        colonytrack.PLATE_LINE
    for job, k, rect, cell in job_cells(screen, view):
        pic = figures.get(cell.figure) if figures.state != "missing" \
            else None
        ink = figures.ink_bottom(cell.figure) if pic is not None else None
        if ink is not None:
            surface.blit(pic, (rect.x, colonytrack.figure_origin_y(
                rect.y, rect.h, ink) - thicker))
        elif pic is not None:
            surface.blit(pic, (rect.x, rect.bottom - pic.get_height()))
        else:
            pygame.draw.rect(surface, hudtext.colour("label"),
                             rect.inflate(-2, -4), 1)


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
    # Nothing to build toward (Trade Goods, cost 0): the original's two
    # frames draw nothing visible (`Draw_Colony_PC_Bar_`, coldraw.cpp:249-
    # 279, frame 0 of the empty art — seen live, work order 231 E, Kif IV),
    # so HD draws no bar either: the empty box Data's picture showed was
    # HD's own.
    if cost > 0:
        bar = nd.rect(layout, geom.BUILD_BAR_BOX)
        pygame.draw.rect(surface, hudtext.colour("label"), bar, 1)
        filled = max(0, min(bar.h - 2, (bar.h - 2) * spent // cost))
        pygame.draw.rect(surface, hudtext.colour("button"),
                         (bar.x + 1, bar.bottom - 1 - filled,
                          bar.w - 2, filled))
    text(surface, screen, words.turns(turns), *geom.BUILD_TURNS_RIGHT, 80,
         "small", "value", align="right")
    return layout


def _roads(view, placement):
    """TRANSCRIPTION `roads` (work order 339, `colroads`): the road pictures
    that go under the city; none without their extraction. The replay is
    kept per colony and what it was made from — one a frame would run the
    engine's placement 60 times a second."""
    art = colart.load()
    if not art.has("road_0"):
        return ()
    colony = view.colony
    key = (view.index, tuple(colony.buildings), colony.n_pops,
           tuple(map(tuple, placement["grid"])),
           tuple(placement["satellites"]))
    if _road_memo[0] != key:
        _road_memo[:] = [key, colroads.roads_for(view, placement)]
    return _road_memo[1]


_road_memo = [None, ()]


def _buildings(surface, screen, view, state, names):
    """TRANSCRIPTION `building_sprites` / HD EXTENSION `building_sprites`
    (work order 326, `colbuildings`): the colony's buildings as the
    original's sprites on the ground and its satellites in the sky, from
    open fix 36's grid; and DEVIATION `building_list`: the buildings as a
    list of names, which is how HD asks for a building's description and its
    demolish (`colright`, `coldemolish`) — in the box `col_buildings`, by
    default the panel's left margin beside the city (HD EXTENSION
    `building_list_box`, the F3 editor's), when the sprites are drawn, the
    original's rows when they are not (no extracted pictures).

    UNVERIFIED `building_placement`: the grid's occupied cells are verified
    against the live fields (`colgeom.building_field`, check 090p); that a
    live engine's CBLD block draws the native city was not seen live (work
    order 326: the transcription of the placement was compared with a
    native frame instead)."""
    ids = view.buildings()
    placement = colbuildings.shown(state)
    if placement is not None:
        colbuildings.draw(surface, scene_rect(screen), colart.load(),
                          placement, view.colony.climate, _bg_type(view),
                          roads=_roads(view, placement))
    if not ids:
        return
    box, rows = colbuildings.list_geometry(screen, len(ids), placement)
    if not rows:      # a box too small for one row draws no empty frame
        return
    hud.panel(surface, box, screen.layout.scale)
    colbuildings.draw_list(surface, screen, [names.building(b) for b in ids],
                           rows, hudtext.colour("label"))


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
    # what the drawing covers per kind, the click's rects (decision 5): a
    # click there is the game's military field for that kind, which opens
    # its troop popup (colony.cpp:2007-2013, open fix 98)
    screen.unit_hits = []
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
        # ON THE BOTTOM EDGE, as the original stands them (`479 - h`): the
        # figure keeps the band's sprite step while the surface panel
        # spreads its positions flatter, so the native top mapped down ran
        # the figure over the panel's edge (Data's picture, work order
        # 232). The foot is the anchor: the panel's inner bottom, native
        # 480 mapped (the window `PanelMap` carries the surface into).
        x, foot = nd.point(screen.layout, x_native, 480)
        big = nd.magnified(pic, screen.layout) if pic is not None else None
        top = foot - (big.get_height() if big is not None else
                      int(round(12 * nd.native_scale(screen.layout))))
        if big is not None:
            surface.blit(big, (x, top))
        # a lone figure with its count spans the original's three slots
        # (colony_main.cpp:1208, :1217-1224), a figure of a row one
        span = nd.point(screen.layout, x_native + step * (
            3 if count is not None else 1), 480)[0] - x
        hit = pygame.Rect(x, top, max(span, big.get_width() if big is not None
                                      else 0), foot - top)
        known = next((h for h in screen.unit_hits if h[0] == kind), None)
        if known is None:
            screen.unit_hits.append((kind, hit, slot * step))
        else:
            known[1].union_ip(hit)
        if count is not None:
            fmt = words.e(0x7C) or "x %d"
            cx, _y = nd.point(screen.layout, (slot + 1) * step, 480)
            w = nd.rect(screen.layout, ((slot + 1) * step, 470,
                                        (slot + 1) * step + 59, 470)).w
            nd.blit_text(surface, screen.style, printf(fmt, count), cx, top,
                         w, font(screen.layout, "value"),
                         hudtext.colour("value"))


def _tech_apps(state, player):
    from core.structs import player as player_struct
    raws = getattr(state, "player_raw", None) or []
    if not 0 <= player < len(raws):
        return ()
    return list(player_struct.parse(raws[player]).tech_applications)


def officer_line(view, state, words):
    """`Draw_Colony_Info_Officer_` (colony.cpp:706-734): the star's slot for
    the player, then the name or `E 285` with the ETA — or None, where the
    original draws no frame either (:709). Since work order 232 it is the
    word of the LEADERS slot (`screen._leaders_word`): with an officer the
    original has no LEADERS button, its field [17] is the officer's frame
    (a hidden field over it, colony_main.cpp:994-999), and a click there
    opens the Leaders screen as the button does. OMISSION
    `officer_portrait`."""
    got = view.officer(state)
    if got is None:
        return None
    name, eta = got
    return printf(words.e(285) or "%d", eta) if eta > 0 else name


def _buttons(surface, screen, state):
    """CHANGE and BUY in the build window, where the live list has them.
    LEADERS and RETURN are the screen's own actions, the shell's buttons
    since work order 231 E (decisions 87, 90; `screen.shell`)."""
    fields = getattr(state, "fields", None)
    for key, ident in (("change", geom.CHANGE), ("buy", geom.BUY)):
        f = colwire.live_field(fields, ident)
        if f is None:
            continue
        r = nd.rect(screen.layout, (f.x, f.y, f.x_end, f.y_end))
        dim = key == "buy" and f.field_type != geom.TYPE_BUTTON
        hud.slant_button(surface, r, screen.layout.scale,
                         "disabled" if dim else hud_hover.pointer_state(r),
                         screen.word(key), style_renderer=screen.style)
