"""Drawing for the Planets screen: list, side column, bottom windows.

The list goes through `core.listgrid` — the colony list's bands, columns,
heading plates, row fills and cell outlines (brief 101, Data: extract and
share, do not copy). Everything positional is a box; everything coloured
is `colors.json` (decision 14).
"""
import logging

import pygame

from core.hud import blocks as hud

from core import listgrid, palette
from screens.colony_summary import colonyinset, colonyplanets
from screens.galaxy_map.renderer import OWNER_COLORS

log = logging.getLogger("planets")

NEUTRAL = palette.require("planets", "neutral")
NEUTRAL_HOVER = palette.require("planets", "neutral_hover")
OWNER_HOVER = {n: palette.require("planets", f"owner_hover_{n}")
               for n in range(8)}
STATUS_COLORS = {"red": palette.require("planets", "status_red"),
                 "green": palette.require("planets", "status_green"),
                 "neutral": palette.require("planets", "status_neutral")}
CONTROL_TEXT = palette.require("planets", "control_text")
CONTROL_ACTIVE = palette.require("planets", "control_active")
CONTROL_HOVER = palette.require("planets", "control_hover")
CONTROL_DISABLED = palette.require("planets", "control_disabled_text")
HEADING_TEXT = palette.require("planets", "heading_text")
#: The HUD panel's fill since decision 71 (work order 169): every window
#: of this screen is a HUD panel, and the research boxes share it.
from core.hud import style as _hudstyle
PANEL_BG = _hudstyle.get().colour("panel.fill")
INSET_FILL = palette.require("colony_summary", "galaxy_inset_fill")
OUTLINE = palette.col("panel", "thin_border", (55, 65, 85))

#: The frame's five cutouts, filled before the frame goes over them.
PANELS = ("list_area", "side_panel", "planet_panel", "picture_panel",
          "button_panel")
COLUMN_KEYS = ("planet", "climate", "gravity", "minerals", "size")


def row_color(row, hover):
    """`Colony_Owner_Colors_` (plntsum.cpp:2204): the owner's player colour
    or the neutral ramp, the hover shade for highlight type 1."""
    colour = row.get("owner_color")
    if colour is None or colour not in OWNER_COLORS:
        return NEUTRAL_HOVER if hover else NEUTRAL
    return OWNER_HOVER[colour] if hover else OWNER_COLORS[colour]


def _text(style, text, size, colour, width):
    """Render, stepping the size down until it fits `width`; the
    original fits the name the same way (Set_Fitted_Font_Style_,
    plntsum.cpp:85)."""
    while True:
        surf = style.render_text(text, size, tuple(colour)[:3])
        if surf.get_width() <= width or size <= 8:
            return surf
        size -= 1


def _blit_centered(surface, surf, cx, y):
    surface.blit(surf, (cx - surf.get_width() // 2, y))


def window(screen, name):
    ref = screen.box_rect(name)
    return pygame.Rect(*screen.layout.rect(ref)) if ref else None


def fill_panels(screen, surface):
    """Every window is a HUD panel since decision 71 (work order 169) —
    the frame image that framed them is not drawn."""
    for name in PANELS:
        rect = window(screen, name)
        if rect:
            hud.panel(surface, rect, screen.layout.scale)
    inset = window(screen, "galaxy_inset")
    if inset:
        # BLACK, and here that is a transcription: this screen leaves
        # _using_colony_screen_palette at 0, so Draw_Galaxy_Map_Box_ fills
        # its box with 0 (movebox.cpp:36-38, plntsum.cpp:1954).
        surface.fill(tuple(INSET_FILL)[:3], inset)


def columns(screen, cfg):
    """{key: (x, width)} window px, from the header box and the shares."""
    ref = screen.box_rect("header")
    if not ref:
        return {}
    rects = listgrid.column_rects(ref, cfg.get("columns", {}))
    out = {}
    for key in COLUMN_KEYS:
        rect = rects.get("col_" + key)
        if rect:
            x, _y, w, _h = screen.layout.rect(rect)
            out[key] = (x, w)
    return out


def row_bands(screen):
    """(top, height) of every row band in the `rows` window, or [].

    The ONE place the list's bands come from: `render_list` draws in them
    and the hover finds its row in them (`listgrid.band_at`), decision 5.
    """
    area = window(screen, "rows")
    if not area:
        return []
    return listgrid.all_bands(area, screen.visible)


def render_list(screen, surface, rows, cells, first, hover_index,
                selected_planet):
    cfg = screen._data.get("list", {})
    area = window(screen, "rows")
    header = window(screen, "header")
    if not area or not header:
        return
    cols = columns(screen, cfg)
    scale = screen.layout.scale
    row_a, row_b, row_sel, plate, _hbg, htext = listgrid.row_palette()
    bands = row_bands(screen)
    listgrid.draw_row_fills(
        surface, bands, cols, (), first,
        lambda li: (li < len(rows) and rows[li]["index"] == selected_planet),
        row_a, row_b, row_sel)
    listgrid.draw_cell_plates(surface, bands, cols, (), screen.style, scale,
                              plate)
    hud.table_header(surface, header, scale)
    listgrid.draw_headings(surface, header, cols,
                           screen._data.get("headings", {}), screen.style,
                           screen.layout.font_size(cfg.get("upper_font", 22)),
                           plate, htext, scale)
    upper = screen.layout.font_size(cfg.get("upper_font", 22))
    lower = screen.layout.font_size(cfg.get("lower_font", 16))
    discs = None
    for band, (by, bh) in enumerate(bands):
        li = first + band
        if li >= len(rows):
            break
        row = rows[li]
        colour = row_color(row, li == hover_index)
        words = cells[li]
        size = max(1, int(bh * float(cfg.get("disc_share", 0.72))))
        if discs is None:
            discs = colonyplanets.set_for(screen, size)
        _render_planet_cell(screen, surface, cols.get("planet"), by, bh,
                            words["planet"], row, colour, discs, size,
                            upper, lower)
        for key in COLUMN_KEYS[1:]:
            if key in cols:
                _render_pair(screen.style, surface, cols[key], by, bh,
                             words[key], colour, upper, lower)


def _render_planet_cell(screen, surface, col, by, bh, words, row, colour,
                        discs, size, upper, lower):
    if not col:
        return
    x, w = col
    pad = max(4, bh // 8)
    disc = discs.get(row["climate"]) if discs is not None else None
    if disc is not None:
        surface.blit(disc, (x + pad, by + (bh - size) // 2))
    tx = x + 2 * pad + size
    width = max(1, x + w - tx - pad)
    lines = [(words["special"], lower), (words["name"], upper),
             (words["owner"], lower)]
    surfs = [_text(screen.style, t, s, colour, width) for t, s in lines if t]
    total = sum(s.get_height() for s in surfs)
    y = by + (bh - total) // 2
    for surf in surfs:
        surface.blit(surf, (tx, y))
        y += surf.get_height()


def _render_pair(style, surface, col, by, bh, pair, colour, upper, lower):
    x, w = col
    top, bottom = pair
    first = _text(style, top, upper, colour, w - 8) if top else None
    second = _text(style, bottom, lower, colour, w - 8) if bottom else None
    uh = first.get_height() if first else style.render_text(
        "X", upper, (0, 0, 0)).get_height()
    lh = style.render_text("X", lower, (0, 0, 0)).get_height()
    y0 = by + (bh - uh - lh) // 2
    cx = x + w // 2
    if second is None:
        # One line: half a line down (plntsum.cpp:171-179).
        if first:
            _blit_centered(surface, first, cx, y0 + lh // 2)
        return
    if first:
        _blit_centered(surface, first, cx, y0)
    _blit_centered(surface, second, cx, y0 + uh)


def render_scroll(screen, surface, total, first, visible):
    rect = window(screen, "scroll")
    if not rect:
        return
    arrow = rect.width
    # The track and thumb are the HUD scrollbar (decision 71); the two
    # arrow squares stay the original's controls, drawn as before.
    hud.scrollbar(surface, rect.inflate(0, -2 * arrow), screen.layout.scale,
                  first, visible, total)
    for top, rect_y in ((True, rect.y), (False, rect.bottom - arrow)):
        cx, h = rect.centerx, arrow // 3
        cy = rect_y + arrow // 2
        pts = ([(cx, cy - h), (cx - h, cy + h), (cx + h, cy + h)] if top
               else [(cx, cy + h), (cx - h, cy - h), (cx + h, cy - h)])
        pygame.draw.polygon(surface, tuple(CONTROL_TEXT)[:3], pts)


def scroll_arrows(screen):
    """(up, down) window rects of the two arrow squares, or (None, None)."""
    rect = window(screen, "scroll")
    if not rect:
        return None, None
    a = rect.width
    return (pygame.Rect(rect.x, rect.y, a, a),
            pygame.Rect(rect.x, rect.bottom - a, a, a))


def render_control(screen, surface, name, label, active=False, enabled=True,
                   mouse=None):
    rect = window(screen, name)
    if not rect or not label:
        return
    # The HUD's small button (decision 71): active, hover, disabled and
    # normal are the block's four states; the word is drawn below as
    # before, in its enabled or disabled colour.
    if active:
        state = "active"
    elif not enabled:
        state = "disabled"
    elif mouse is not None and rect.collidepoint(mouse):
        state = "hover"
    else:
        state = "normal"
    hud.small_button(surface, rect, screen.layout.scale, state)
    size = screen.layout.font_size(_font(screen, name, 19))
    surf = _text(screen.style, label, size,
                 CONTROL_TEXT if enabled else CONTROL_DISABLED,
                 rect.width - 8)
    surface.blit(surf, surf.get_rect(center=rect.center))


def render_heading(screen, surface, name, label):
    rect = window(screen, name)
    if not rect or not label:
        return
    surf = _text(screen.style, label.upper(),
                 screen.layout.font_size(_font(screen, name, 22)),
                 HEADING_TEXT, rect.width - 8)
    surface.blit(surf, surf.get_rect(center=rect.center))


def render_status(screen, surface, status):
    rect = window(screen, "status_line")
    if not rect:
        return
    screen.style.draw_plate(surface, rect, screen.layout.scale, OUTLINE)
    if not status or not status[0]:
        return
    surf = _text(screen.style, status[0],
                 screen.layout.font_size(_font(screen, "status_line", 22)),
                 STATUS_COLORS[status[1]], rect.width - 8)
    surface.blit(surf, surf.get_rect(center=rect.center))


def render_inset(screen, surface, stars, marker):
    rect = window(screen, "galaxy_inset")
    if not rect or not stars:
        return
    cfg = screen._data.get("inset", {})
    colonyinset.render(surface, stars, "", rect, cfg, screen.layout,
                       screen.style, native=tuple(cfg.get("native", (180, 116))),
                       marker=marker)


def inset_star_at(screen, stars, x, y):
    """The star index under (x, y) in the inset, or None — the nearest
    drawn dot within its 5x5 native field (plntsum.cpp:1256-1259)."""
    rect = window(screen, "galaxy_inset")
    if not rect or not stars or not rect.collidepoint(x, y):
        return None
    native = tuple(screen._data.get("inset", {}).get("native", (180, 116)))
    mrect = colonyinset.map_rect(rect, native)
    best, best_d = None, None
    for index, (sx, sy, _c, cw, ch) in enumerate(
            colonyinset.star_points(stars, mrect, native)):
        dx, dy = abs(sx - x), abs(sy - y)
        if dx <= 3 * cw and dy <= 3 * ch:
            d = dx * dx + dy * dy
            if best_d is None or d < best_d:
                best, best_d = index, d
    return best


def render_planet_panel(screen, surface, row, words):
    """HD EXTENSION: panel — the scanned row's disc, name and special line,
    larger (layout.json panel._hd_extension_panel)."""
    if row is None:
        return
    disc_rect = window(screen, "planet_disc")
    if disc_rect:
        size = min(disc_rect.width, disc_rect.height)
        disc = colonyplanets.set_for(screen, size)
        image = disc.get(row["climate"]) if disc is not None else None
        if image is not None:
            surface.blit(image, image.get_rect(center=disc_rect.center))
    colour = row_color(row, False)
    for name, text in (("planet_name", words["name"]),
                       ("planet_special", words["special"])):
        rect = window(screen, name)
        if rect and text:
            surf = _text(screen.style, text,
                         screen.layout.font_size(_font(screen, name, 22)),
                         colour, rect.width)
            surface.blit(surf, (rect.x, rect.y + (rect.height
                                                  - surf.get_height()) // 2))


def _font(screen, name, default):
    return screen.box_style(name).get("font_size", default)
