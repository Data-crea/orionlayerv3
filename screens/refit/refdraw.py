"""Drawing Refit's two lists in the HUD style — work order 223.

Everything at the HD image of its native rectangle (`refgeom`, through
`screens/leaders/ldrdraw`), every panel, field and button the shared look
(decision 71 as amended): no colour of this screen's own.

  TRANSCRIPTION  the ship list: the cells, each ship's picture in its
                 builder's colours under its holder's ramp (`Draw_Ship2_`,
                 colrefit.cpp:435-438; the Fleets art), the refusal words
                 in the cell (:440-462), the bar's thumb (:414-433), the
                 hovered ship's paragraph (`refwords`); the design list:
                 the title, the five rows — name, ":" and the hull, bright
                 where the size is the ship's (:485-526) — the last row,
                 the hovered design's paragraph or the last row's (:276-298)
  DEVIATION      `hud_parts`: REFITPUP.LBX 0 / 4 and the buttons 1-3 are
                 the HUD's panel, fields and buttons; the words baked into
                 the art (the ship list's title, Cancel) are OrionLayer's
                 words (`button_words`)
  DEVIATION      `alone`: the original draws its window over the build
                 popup; HD shows it alone over the background — the popup
                 is under it, unchanged, and comes back with Cancel
"""
from core.hud import blocks as hud
from core.hud import hover as hud_hover
from core.hud import text as hudtext
from screens.colony.coldraw import font, text
from screens.leaders import ldrdraw as nd

from . import refgeom as geom


def draw_frame(surface, screen, title):
    """The stage: the shell's panel (work order 225) — the title stands on
    the shell's plate, so `title` is not drawn here. The original's popup
    and title rects (`geom.POPUP`, `geom.TITLE`) stay as its record."""
    hud.panel(surface, screen.box_screen_rect("stage"), screen.layout.scale)


def draw_ships(surface, screen, cells, hover, first, total):
    """`cells`: [(index in cell order, ship view or None, picture,
    refusal word)] for the cells on show."""
    layout = screen.layout
    hud.field(surface, nd.rect(layout, geom.GRID), layout.scale)
    for i in range(geom.CELLS):
        r = nd.rect(layout, geom.cell(i))
        hud.field(surface, r, layout.scale, on=(i == hover and
                                                 cells[i][1] is not None))
        _k, view, pic, refusal = cells[i]
        if view is None:
            continue
        if pic is not None:
            big = nd.magnified(pic, layout)
            surface.blit(big, big.get_rect(center=r.center))
        if refusal:
            text(surface, screen, refusal, (geom.cell(i)[0] + geom.cell(i)[2]) // 2,
                 geom.cell(i)[1] + 22, 55, "line", "negative", align="center")
    hud.field(surface, nd.rect(layout, geom.INFO_BOX), layout.scale)
    track = nd.rect(layout, geom.TRACK)
    if total >= geom.CELLS:
        # `Draw_Bar_Indicator_` (:414-433): rows of five, three on show.
        rows = (total + 5) // 5
        hud.scrollbar(surface, track, layout.scale, first // 5, 3, rows)
    else:
        hud.field(surface, track, layout.scale)


def draw_designs(surface, screen, rows, hover):
    """`rows`: [(row index, name, hull, matches)] for the five slots that
    hold a design, then the last row's word as (6, word, "", True)."""
    layout = screen.layout
    hud.field(surface, nd.rect(layout, geom.DESIGN_BOX), layout.scale)
    for k, name, hull, matches in rows:
        r = nd.rect(layout, geom.design_row(k))
        if k == hover:
            hud.field(surface, r, layout.scale, on=True)
        role = "value" if matches else "sub"
        y = geom.design_row(k)[1] + 2
        if k == geom.GOTO_ROW:
            text(surface, screen, name, 320, y, 300, "value", role,
                 align="center")
            continue
        text(surface, screen, name, geom.DESIGN_NAME_X, y, 130, "value", role)
        text(surface, screen, ":", geom.DESIGN_COLON_X, y, 10, "value", role,
             align="center")
        text(surface, screen, hull, geom.DESIGN_HULL_RIGHT, y, 130, "value",
             role, align="right")
    hud.field(surface, nd.rect(layout, geom.INFO_BOX), layout.scale)


def draw_paragraph(surface, screen, lines, box):
    """The hovered ship's or design's lines in the info box: a heading, a
    label and its value, or two items side by side."""
    if not lines:
        return
    layout = screen.layout
    x, y, w, h = box
    size = font(layout, "line")
    step = max(1, int(size * 1.2))
    r = nd.rect(layout, (x, y, x + w - 1, y + h - 1))
    ty = r.y
    for row in lines:
        if ty + step > r.bottom:
            break
        if len(row) == 1:
            nd.blit_text(surface, screen.style, row[0], r.x, ty, r.w, size,
                         hudtext.colour("label"))
        elif row[0] == "":
            nd.blit_text(surface, screen.style, row[1], r.x, ty, r.w, size,
                         hudtext.colour("value"))
        else:
            a, b = row
            nd.blit_text(surface, screen.style, a, r.x, ty, r.w // 2 - 4,
                         size, hudtext.colour("label"))
            nd.blit_text(surface, screen.style, b, r.x + r.w // 2, ty,
                         r.w // 2, size, hudtext.colour("value"))
        ty += step


def draw_buttons(surface, screen, kind):
    layout = screen.layout
    names = (("cancel", geom.CANCEL),) if kind == "designs" else (
        ("up", geom.UP), ("down", geom.DOWN), ("cancel", geom.CANCEL))
    # Cancel is the shell's closing action (work order 225).
    names = tuple(n for n in names if n[0] != "cancel")
    for key, rect in names:
        r = nd.rect(layout, rect)
        hud.small_button(surface, r, layout.scale,
                         hud_hover.pointer_state(r), screen.word(key),
                         style_renderer=screen.style)
