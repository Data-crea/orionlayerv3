"""A screen-sized list of rows in columns: bands, columns, heading
plates, row fills and cell outlines — shared by every list screen.

**EXTRACTED 13 September 2026 (brief 101)** from `colonytrack`,
`colonyheader`, `colonyplates` and `colonylist`, when the Planets
screen became the second screen with this list. The colony modules
keep their own names for these functions and delegate here; they keep
everything that is not a list of rows — figures, the allocation track,
pop moves. One home for the arithmetic, so a column, the heading above
it and the cells inside it cannot land in different places on two
screens (decision 5), and a copy that diverges is the failure the
fundament records under "A name table copied into three files".

Nothing here reads a snapshot, a box file or a layout file. Callers
hand in rects, counts and colours; the geometry is pure and the drawing
takes a surface.

**THE LIST PALETTE HAS ONE HOME**, `colors.json` under
`colony_summary` (`row_a`, `row_b`, `row_selected`, `plate_outline`,
`header_background`, `header_text`), and `row_palette()` is how a
second screen reads it rather than carrying a copy of the values.
The row fills are an HD EXTENSION (decision 57); the original's lists
have no row backgrounds.
"""
import pygame

#: Reference px of heading window left above and below each plate,
#: and the gap between two neighbouring plates. `colonyheader` carries
#: the measurements these came from.
PLATE_INSET_REF = 2
PLATE_DIVIDER_REF = 6


def band_height(area, row_count):
    """The row band: the list's height divided by its row count."""
    return max(1, area.h // max(1, int(row_count)))


def band_at(bands, y):
    """The index of the band holding device row `y`, or None.

    Takes the bands `all_bands` produced — the ones the rows were DRAWN
    in — so a hit test cannot divide the window a second way (decision 5).
    Planets' hover divided `(y - top) * n // height` while its rows were
    drawn as h // n with the remainder on the last band, and the two named
    different rows on single pixel lines (work order 128 D).
    """
    for index, (top, height) in enumerate(bands):
        if top <= y < top + height:
            return index
    return None


def all_bands(area, row_count):
    """(top, height) for every band of the window, the last one taking
    the remainder so the bands tile the window exactly."""
    band = band_height(area, row_count)
    want = int(row_count)
    bands, y = [], area.y
    for i in range(want):
        h = (area.bottom - y) if i == want - 1 else band
        if h <= 0:
            break
        bands.append((y, h))
        y += h
    return bands


def column_rects(list_box, cols):
    """{col_<key>: [x, y, w, h]} — columns laid across `list_box` from
    `cols`, an ordered {key: width} whose LAST entry is an absolute
    width (the scroll slot) and whose others are shares of what is left.
    Each column ends where the next begins, so they tile by
    construction."""
    ax, ay, aw, ah = list_box
    keys = list(cols)
    last = keys[-1]
    fixed = cols[last]
    total = sum(v for k, v in cols.items() if k != last)
    span = aw - fixed
    out, off = {}, 0
    for key in keys:
        if key == last:
            out["col_" + key] = [ax + aw - fixed, ay, fixed, ah]
        else:
            x = ax + round(off * span / total)
            nxt = (ax + aw - fixed if off + cols[key] >= total
                   else ax + round((off + cols[key]) * span / total))
            out["col_" + key] = [x, ay, nxt - x, ah]
        off += cols[key]
    return out


def columns(area, table, span):
    """{key: (x, width)} in screen px from live column boxes.

    `table` is [(key, Box)] and `span` the list box's reference
    (x, width). Only each box's reference LEFT edge is read and mapped
    into `area`; a column's width is the distance to the next one, so
    the columns tile the window at any size and a dragged boundary
    moves its neighbour (`colonytrack.columns` carries the history).
    """
    if not table or not span:
        return {}
    ref_x, ref_w = span
    if ref_w <= 0:
        return {}
    edges = sorted((b.ref_rect[0], key) for key, b in table)
    out = {}
    for i, (rx, key) in enumerate(edges):
        nxt = edges[i + 1][0] if i + 1 < len(edges) else ref_x + ref_w
        x = area.x + (max(0, rx - ref_x) * area.width) // ref_w
        right = area.x + (max(0, nxt - ref_x) * area.width) // ref_w
        out[key] = (x, max(1, right - x))
    return out


def plate_rects(header_box, cols, scale):
    """[(key, rect)] — one heading plate per column, window px. The
    column's own x and width; `header_box` supplies only the vertical."""
    box = pygame.Rect(header_box)
    if not cols:
        return []
    inset = max(1, round(PLATE_INSET_REF * scale))
    half = max(1, round(PLATE_DIVIDER_REF * scale / 2))
    return [(key, pygame.Rect(
        x + half, box.y + inset,
        max(1, w - 2 * half), max(1, box.height - 2 * inset)))
        for key, (x, w) in cols.items()]


def draw_headings(surface, header_box, cols, labels, style, font_size,
                  outline, text_color, scale):
    """The heading plates and their words. A key with no word gets its
    plate and no text; a word wider than its plate is left out rather
    than overdrawn."""
    for key, rect in plate_rects(header_box, cols, scale):
        style.draw_plate(surface, rect, scale, outline)
        word = labels.get(key)
        if not word:
            continue
        text = style.render_text(word.upper(), font_size, text_color[:3])
        if text.get_width() > rect.width - 8:
            continue
        surface.blit(text, (rect.x + (rect.width - text.get_width()) // 2,
                            rect.y + (rect.height - text.get_height()) // 2))


def plated_span(cols, skip):
    """(x, width) across every column not in `skip`, or None."""
    plated = [(x, w) for key, (x, w) in cols.items() if key not in skip]
    if not plated:
        return None
    x0 = min(x for x, _w in plated)
    return x0, max(x + w for x, w in plated) - x0


def band_fill(list_index, selected, row_a, row_b, row_selected):
    """The fill of one band: the selected colour when `selected`,
    otherwise A or B by LIST index, so a scroll or a sort never breaks
    the stripe."""
    if selected:
        return row_selected
    return row_a if list_index % 2 == 0 else row_b


def draw_row_fills(surface, bands, cols, skip, first, is_selected,
                   row_a, row_b, row_selected):
    """Fill every band under the plated columns — HD EXTENSION,
    decision 57. `is_selected(list_index)` answers whether that list
    position holds the selected row."""
    span = plated_span(cols, skip)
    if span is None:
        return
    fx, fw = span
    for band, (by, bh) in enumerate(bands):
        li = first + band
        fill = band_fill(li, is_selected(li), row_a, row_b, row_selected)
        surface.fill(tuple(fill)[:3], pygame.Rect(fx, by, fw, bh))
    # The selected band's RIM, the HUD table's selected row (decision
    # 71): drawn after every fill so a neighbour cannot cover it.
    from core.hud import style as hudstyle
    rim = hudstyle.get().colour("mockup_colony.selected_edge")
    for band, (by, bh) in enumerate(bands):
        if is_selected(first + band):
            # One px INSIDE the band: the band's edge lines stay its
            # fill, which is what shows a hover or a scan reaching the
            # whole band (the Planets hover check reads exactly those).
            pygame.draw.rect(surface, rim,
                             pygame.Rect(fx + 1, by + 1, fw - 2, bh - 2), 1)


def draw_cell_plates(surface, bands, cols, skip, style, scale, color):
    """One outline per cell of every band, for every column not in
    `skip` — `StyleRenderer.draw_plate` (decision 51)."""
    for by, bh in bands:
        for key, (cx, cw) in cols.items():
            if key in skip:
                continue
            style.draw_plate(surface, pygame.Rect(cx, by, cw, bh),
                             scale, color)


def row_palette():
    """(row_a, row_b, row_selected, plate_outline, header_background,
    header_text) — the HUD table's (decision 71, work order 169).

    Until 169 this read the colony list palette of decision 57 out of
    `colors.json`. The HUD's table blocks carry the same six roles,
    measured off Data's colony mockup (`mockup_colony` in the style
    file), and every table on every screen reads them from there: the
    colony list and the Planets list stripe, select and outline with
    one set of colours. The plate outline is the HUD outline's own
    (`panel.edge_dim`), since `draw_plate` draws that and nothing else."""
    from core.hud import style as hudstyle
    st = hudstyle.get()
    return tuple(st.colour(k) for k in (
        "mockup_colony.row_a", "mockup_colony.row_b",
        "mockup_colony.selected", "panel.edge_dim",
        "mockup_colony.header", "mockup_colony.text_header"))
