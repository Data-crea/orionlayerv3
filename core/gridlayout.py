"""Generic "N items in a rect" grid layout.

Used by any screen that lays cells into a panel and needs the exact
same rects for rendering and hit-testing (select_race's portrait
grid, empire_identity's banner grid). Previously each screen carried
its own copy of this arithmetic; this module is the one place it is
computed, so render and hit-test can never drift and a third
grid-based screen doesn't need a third copy.

Two shapes are supported:

  fixed grid    cols and rows are both given (e.g. a 5x3 portrait
                grid with a reserved header strip) — cell size is
                whatever divides the content area evenly, cells need
                not be square.

  packed grid   only cols is given; rows is derived from item count
                (ceil(n / cols)) and the whole grid is centered in
                the rect with square cells (e.g. banner swatches).
"""


def grid_cell_rect(rect, index, cols, rows, pad=0, gap=0, header=0):
    """Cell rect for `index` in a fixed cols x rows grid.

    `header` reserves a strip at the top of the content area (e.g.
    for a panel title) before the grid starts. Returns (x, y, w, h)
    in the same coordinate space as `rect`, or None if `index` is
    out of range.
    """
    if index < 0 or index >= cols * rows:
        return None
    rx, ry, rw, rh = rect
    col, row = index % cols, index // cols

    content_x = rx + pad
    content_y = ry + pad + header
    content_w = rw - pad * 2
    content_h = rh - pad * 2 - header

    cell_w = (content_w - (cols - 1) * gap) / cols
    cell_h = (content_h - (rows - 1) * gap) / rows

    cx = content_x + col * (cell_w + gap)
    cy = content_y + row * (cell_h + gap)
    return (cx, cy, cell_w, cell_h)


def packed_grid(items, rect, cols, pad=0, gap=0):
    """Square cells for `items`, packed into `cols` columns and
    centered in `rect`. Rows are derived from len(items).

    Returns [(item, (x, y, w, h)), ...] in the same coordinate
    space as `rect`.
    """
    rx, ry, rw, rh = rect
    n = len(items)
    rows = max(1, (n + cols - 1) // cols)
    inner_w = rw - 2 * pad
    inner_h = rh - 2 * pad
    cell = min((inner_w - (cols - 1) * gap) / cols,
               (inner_h - (rows - 1) * gap) / rows)
    grid_w = cols * cell + (cols - 1) * gap
    grid_h = rows * cell + (rows - 1) * gap
    ox = rx + (rw - grid_w) / 2
    oy = ry + (rh - grid_h) / 2

    out = []
    for i, item in enumerate(items):
        c, r = i % cols, i // cols
        out.append((item, (ox + c * (cell + gap),
                           oy + r * (cell + gap), cell, cell)))
    return out
