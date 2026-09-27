"""Drawing the single-colony screen in the HUD style (decision 71).

Everything sits at the HD image of its native rectangle (`colgeom`,
through `core/researchnative` as `screens/leaders/ldrdraw` wraps it), so
the drawing, the hit test and a native screenshot speak the original's
coordinates. Panels are the HUD's glass panels, buttons its slanted
buttons, over the universal background.

WHAT IS TRANSCRIPTION AND WHAT IS OURS — each marked where it happens,
and each in `layout.json` `marks`, the status document and check 090p:

  TRANSCRIPTION  every position, every string (`colwords`), the values
                 (`colonyrows`: the net production, morale, the icon walk)
  HD EXTENSION   `surface_picture` — Data's picture of the colony's world,
                 by climate (decision 58), where the original draws its
                 own landscape art
  DEVIATION      `label_number` — a production row is an icon and a number,
                 a job row the figures of its pops; the original COUNTS
                 with sprites (decision 56's deviation, the Colonies
                 screen's)
  DEVIATION      `building_list` — the colony's buildings are a list of
                 names; UNVERIFIED `building_placement` — open fix 36's
                 grid is read and not placed (see `_buildings`)
  HD STATE       `status_word`, `production_bar`, `turns` — drawn as
                 nothing while fixes 37 and 38 are absent
  OMISSION       `unit_sprites`, `officer_portrait`, `product_picture`,
                 `hover_strip`, `roads`, `planet_description` (the box
                 `_drawing_display` 2 shows, colony.cpp:1861-1866) — original art this project does
                 not extract, and the hover strip of the original's own
                 pointer; each named where it would be drawn
"""
import pygame

from core.hud import blocks as hud
from core.hud import text as hudtext
from screens.colony_summary import colonyfigures, colonyoutputicons
from screens.colony_summary import colonyrows, colonysurfaces
from screens.colony_summary.colonyplanets import set_for as planet_set_for
from screens.leaders import ldrdraw as nd

from . import colgeom as geom
from . import colwire

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
    for native in (geom.SYS_DISP, (124, 29, 304, 152),
                   (307, 29, 512, 152), geom.BUILD_WINDOW):
        nd.draw_box(surface, screen, native)
    _title_line(surface, screen, view, state, words, names)
    _system(surface, screen, view, state, words)
    _production(surface, screen, view)
    _jobs(surface, screen, view, state)
    _build(surface, screen, view, state, words, names)
    _buildings(surface, screen, view, state, names)
    _units(surface, screen, view, words)
    _officer(surface, screen, view, state, words)
    _buttons(surface, screen, state)
    return layout


def _scene(surface, screen, view):
    """HD EXTENSION `surface_picture` — decision 58's picture of the world,
    by the colony's climate, under the band; nothing where it is absent."""
    pics = colonysurfaces.set_for(screen)
    pic = pics.get(view.colony.climate) if pics is not None else None
    if pic is None:
        return
    r = nd.rect(screen.layout, geom.SCENE)
    scaled = pygame.transform.smoothscale(pic, r.size)
    surface.blit(scaled, r.topleft)


def _title_line(surface, screen, view, state, words, names):
    name = colonyrows.planet_name(view.colony, names.planets, names.stars)
    text(surface, screen, words.title(view, name), *geom.TITLE_CENTRE, 380,
         "title", "title", align="center")
    status = words.status(view, getattr(state, "player_num", 0), state)
    # HD STATE `status_word`: None is "open fix 37 absent" — nothing drawn.
    text(surface, screen, status, *geom.STATUS_AT, 120, "value",
         "negative")
    text(surface, screen, words.pop(view), *geom.POP_RIGHT, 128, "value",
         "value", align="right")


def _system(surface, screen, view, state, words):
    size = max(1, int(20 * nd.native_scale(screen.layout)))
    planets = planet_set_for(screen, size)
    for i, planet in enumerate(view.system):
        if planet is None:
            continue
        (cx, cy), (tx, ty) = geom.sys_row(i)
        pic = planets.get(planet.climate) if planets is not None and \
            planet.planet_type == 3 else None
        if pic is not None:
            x, y = nd.point(screen.layout, cx, cy)
            surface.blit(pic, (x - pic.get_width() // 2,
                               y - pic.get_height() // 2))
        lines(surface, screen, words.summary(planet, state), tx, ty,
              geom.SYS_TEXT_W, "line", "label", 8)


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
    got = view.product(state)
    if got is None:
        return layout        # HD STATE `production_bar`, `turns`
    cost, turns = got
    spent = cost if view.colony.bought_outright else \
        view.colony.production_spent
    # DEVIATION `production_bar`: the original draws two frames of its art
    # (C_Anims_ 34/35, frames 0..50) whose column runs 64 native px down
    # from y + 10 (coldraw.cpp:249-280); the art's width is not in the
    # source. HD draws the 64 px column, filled current / total, 12 px wide.
    bx, by = geom.BUILD_BAR_AT
    bar = nd.rect(layout, (bx, by + 10, bx + 11, by + 10 + 63))
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


def _units(surface, screen, view, words):
    """The unit counts, `":%d"` as the original prints them beside its
    sprites (colony_main.cpp:1241); OMISSION `unit_sprites`."""
    marines, armour = view.units()
    x1, y1, x2, y2 = geom.UNITS
    parts = [p for p in (
        f"{screen.word('marines')} :{marines}" if marines else "",
        f"{screen.word('armour')} :{armour}" if armour else "") if p]
    text(surface, screen, "   ".join(parts), x1 + 4, y2 - 12, x2 - x1,
         "value", "value")


def _officer(surface, screen, view, state, words):
    """`Draw_Colony_Info_Officer_` (colony.cpp:706-734): the star's slot for
    the player, then the name or `E 285` with the ETA. OMISSION
    `officer_portrait`."""
    got = view.officer(state)
    if got is None:
        return                 # no frame either (colony.cpp:709)
    nd.draw_box(surface, screen, geom.OFFICER_FRAME)
    name, eta = got
    line = (words.e(285) or "%d") % eta if eta > 0 else name
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
                         "disabled" if dim else screen.button_state(key, r),
                         screen.word(key), style_renderer=screen.style)
