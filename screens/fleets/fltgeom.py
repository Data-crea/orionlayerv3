"""The Fleets screen's geometry: the native rectangles, and the one seat.

**Decision 5 lives here.** This module is the only place that turns the
original's native constants into reference pixels, and the only place
that splits a region into its parts. `tools/fleet_boxes.py` seeds
`boxes.json` through `seat_regions`; the smoke test measures the file
against the same function; the screen draws and hit-tests the boxes the
file then holds. Nothing computes a rectangle twice.

**EVERY NUMBER BELOW WAS READ OFF THE TREE, NOT OFF THE REPORT.**
`doc/fleet_screen_reading.md` was written by a sub-session in work order
126 G and says so; CLAUDE.md's "you own every detail" makes that a claim
to check, not a source to build on. Checked 18 September 2026 against
the tree `core/config.py` names the engine version of, file and line
beside each entry — the reading was right in every one, which is worth
recording because it is what makes the rest of it usable.

**THE ORIGINAL HAS NO BOXES.** Every rectangle here is an absolute
constant in a 640x480 screen, and the artwork behind it (FLEET.LBX 0) is
a full-screen picture, not a frame with holes. So HD cannot derive these
from the frame the way decision 3 derives a cutout screen's: it SEATS
them, as one group, into the one opening of `assets/frame.png`, keeping
the original's proportions exactly (`seat_regions`). The seated
rectangles are then written into `boxes.json`, where F5 can move any of
them — the seat is a starting point, not a cage.

The transform is ONE uniform factor for both axes, which is what keeps
the inset galaxy map at its native 305:182. That aspect is not a
preference: `Box_Fleet_Screen_Scanned_Star_` hardcodes 1659 and 2197,
which are 506000/305 and 400000/182 (movebox.cpp:193-199), so a map box
of another shape puts the star boxes off the stars.
"""

#: The original's screen, and the reference space HD lays out in.
NATIVE_W, NATIVE_H = 640, 480

#: `SCREEN_FLEET = 4`, orion2_consts.h:465.
GAME_SCREEN_ID = 4

#: Reference px each side that content is allowed to slide UNDER the
#: frame's metal, so no seam shows where the two meet. The cutout
#: screens' own number (`tools/frame_holes.py` BLEED, which already grew
#: the opening in `layout.json` by it) and the GAME menu's
#: (`screens/game_menu/gmframe.py`). The seat gives it back: the regions
#: are fitted into the opening LESS the bleed, so nothing this screen
#: draws ends up beneath the ring. The cost is 4 reference px of height.
BLEED = 2


def _r(x1, y1, x2, y2):
    """An INCLUSIVE native rectangle, as the engine's tables write them,
    as (x, y, w, h). `s_help_box` is {x1, y1, x2, y2} (orion2.h:993) and
    `fields.cpp:364-365` ends a field at `x + width - 1`, so both count
    the last pixel; a width of `x2 - x1` would lose it."""
    return (x1, y1, x2 - x1 + 1, y2 - y1 + 1)


#: THE FIVE REGIONS, in native pixels. The screen's four natural
#: sub-panels as the artwork divides them (the reading's §7), with the
#: status band split off the map because the original's own help list
#: does: 363/364/365 are three entries under one strip.
#:
#: `button_band` and `icon_area` are unions of what is inside them and
#: are not themselves drawn by the original; they exist so F5 can move a
#: group without dragging seven buttons one at a time.
REGIONS = {
    # MOVEBOX::Draw_Galaxy_Map_Box_(nullptr, nullptr, 15, 52, 305, 182,
    # 0, 0, 0, 0, 1, -1) — flt1.cpp:411, and the same four numbers to
    # Set_Fltscrn_Small_Ship_Icon_XYs_ (:531) and
    # Add_Galaxy_Map_Fields_2_ (:1254). Given as x/y/w/h, not inclusive.
    "inset_map": (15, 52, 305, 182),
    # help 363 status text, 364 PREV, 365 NEXT (evanhelp.cpp:154-157)
    "status_band": _r(19, 248, 313, 268),
    # help 366 (evanhelp.cpp:158). The DRAW clip is one pixel in on
    # three sides — Set_Window_(15, 282, 320, 465), flt1.cpp:402 — so
    # the help rectangle is the region and the clip is what fits in it.
    "ship_panel": _r(13, 280, 319, 465),
    # the big-icon grid and the scroll column beside it, together:
    # grid origin (0x15B, 0x35) = (347, 53) (flt1.cpp:512-513), 4 across
    # and 5 down (:506-507), step 62 x 60 (flt2.cpp:122, :126), cell
    # 0x3a x 0x39 = 58 x 57 (flt2.cpp:288-290) -> (347, 53)-(590, 349);
    # scroll column help 361 (605, 59)-(619, 349) (evanhelp.cpp:154).
    "icon_area": _r(347, 53, 619, 349),
    # the seven controls at the bottom right, as their help rectangles
    # bound them (evanhelp.cpp:159-165)
    "button_band": _r(342, 380, 628, 456),
}

#: WHAT SITS INSIDE WHICH REGION. Also F5-editable boxes, because each
#: one is a control the player aims at and the report's own warning is
#: that fields "that look identical" are not: the three bottom-row
#: rectangles differ in height from the three above them.
#:
#: Every rectangle is the control's HELP rectangle, which is the only
#: place the original states an extent — a type 0 button's size comes
#: from its LBX artwork at runtime (`fields.cpp:364-365`), not from the
#: source. RETURN is the one exception and is derived below.
CONTROLS = {
    "prev_fleet": ("status_band", _r(19, 249, 50, 267)),      # help 364
    "status_text": ("status_band", _r(66, 248, 267, 268)),    # help 363
    "next_fleet": ("status_band", _r(283, 249, 313, 267)),    # help 365
    "scroll_column": ("icon_area", _r(605, 59, 619, 349)),    # help 361
    "btn_all": ("button_band", _r(348, 380, 421, 407)),       # help 368
    "btn_relocate": ("button_band", _r(441, 380, 529, 407)),  # help 369
    "btn_scrap": ("button_band", _r(549, 380, 621, 407)),     # help 370
    "btn_leaders": ("button_band", _r(342, 430, 414, 456)),   # help 371
    "btn_support": ("button_band", _r(425, 435, 485, 453)),   # help 372
    "btn_combat": ("button_band", _r(487, 435, 546, 453)),    # help 373
    # RETURN IS THE ONE DERIVED RECTANGLE, and it is derived because its
    # help entry is not its button. Help 374 is (456, 430)-(628, 456)
    # (evanhelp.cpp:165) — a strip that reaches left across the two
    # filter radios, which have their own entries 372 and 373 earlier in
    # the table and therefore win the first-match test
    # (fields.cpp:2924-2932). The BUTTON is added at (556, 430)
    # (flt1.cpp:1201-1204). So: left and top from the field, right and
    # bottom from the help strip. Drawing it at the help rectangle would
    # put RETURN on top of SUPPORT and COMBAT.
    "btn_return": ("button_band", _r(556, 430, 628, 456)),
}

#: The scroll column's three parts, as fractions of the column itself —
#: the colony summary's argument in `colonyscroll` one step on: there
#: the arrows are not boxes because a column table already fixes them;
#: here the COLUMN is the box and its three parts are fixed relative to
#: it, so moving the box in F5 moves all three and no number is stored
#: twice.
#:
#: Native, inside the column (605, 59, 15, 291):
#:   up arrow    y  59..85   — field at (606, 59) (flt1.cpp:1214) down to
#:                             where the track begins
#:   track       y  86..319  — Fill_FltScrn_Scroll_Bar_ x 0x25E = 606,
#:                             y 0x56 = 86, width 0xC = 12
#:                             (flt1.cpp:273-278); length 0xea = 234
#:                             (Initialize_Scroll_Bar_, flt1.cpp:35, and
#:                             Fleet_Screen_Big_Icon_Fields_(…, 605, 86,
#:                             14, 234), flt1.cpp:1246)
#:   down arrow  y 325..349  — field at (605, 325) (flt1.cpp:1215) down
#:                             to the help rectangle's bottom edge
SCROLL_PARTS = {
    "up": (0, 0, 15, 27),
    "track": (1, 27, 12, 234),
    "down": (0, 266, 15, 25),
}

#: The grid the big icons sit in — flt1.cpp:506-513, flt2.cpp:116-127,
#: :288-290. `_big_icon_display_max_icons = 20` (flt1.cpp:511).
GRID_COLUMNS, GRID_ROWS = 4, 5
GRID_STEP_X, GRID_STEP_Y = 62, 60
GRID_CELL_W, GRID_CELL_H = 58, 57
GRID_ORIGIN = (347, 53)
GRID_MAX_ICONS = GRID_COLUMNS * GRID_ROWS

#: Rows the original's scroll bar counts as one page — `visible_rows = 5`
#: (flt1.cpp:34), i.e. the grid's five rows.
SCROLL_VISIBLE_ROWS = 5


def native_union():
    """The smallest native rectangle holding every region, (x, y, w, h).

    (13, 52)-(628, 465), 616 x 414 — the reading's §7 union, recomputed
    here so it can never disagree with the table above it."""
    x1 = min(r[0] for r in REGIONS.values())
    y1 = min(r[1] for r in REGIONS.values())
    x2 = max(r[0] + r[2] for r in REGIONS.values())
    y2 = max(r[1] + r[3] for r in REGIONS.values())
    return (x1, y1, x2 - x1, y2 - y1)


def seat_factor(opening, bleed=BLEED):
    """The one factor that fits the union into `opening` less `bleed`."""
    _, _, ow, oh = opening
    _, _, uw, uh = native_union()
    return min((ow - 2 * bleed) / uw, (oh - 2 * bleed) / uh)


def seat(opening, bleed=BLEED):
    """`(factor, dx, dy)`: native (x, y) -> reference `(dx + x*f, dy + y*f)`.

    The union is centred in the opening on both axes. On this frame it
    is HEIGHT-BOUND — the opening's 1775:921 is 1.927 against the
    union's 616:414 = 1.488 — so the spare room is horizontal and
    nothing is cropped.
    """
    ox, oy, ow, oh = opening
    ux, uy, uw, uh = native_union()
    f = seat_factor(opening, bleed)
    dx = ox + bleed + (ow - 2 * bleed - uw * f) / 2 - ux * f
    dy = oy + bleed + (oh - 2 * bleed - uh * f) / 2 - uy * f
    return f, dx, dy


def to_ref(rect, opening, bleed=BLEED):
    """One native rectangle, seated, as reference px (floats)."""
    f, dx, dy = seat(opening, bleed)
    x, y, w, h = rect
    return (dx + x * f, dy + y * f, w * f, h * f)


def seat_regions(opening, bleed=BLEED):
    """Every region and control, seated, as rounded reference rects.

    The dict `tools/fleet_boxes.py` writes and the smoke test checks.
    """
    out = {}
    for name, rect in REGIONS.items():
        out[name] = [int(round(v)) for v in to_ref(rect, opening, bleed)]
    for name, (_parent, rect) in CONTROLS.items():
        out[name] = [int(round(v)) for v in to_ref(rect, opening, bleed)]
    return out


def scroll_parts(column_rect):
    """The column box's three parts in the SAME space it is given in.

    `column_rect` is the `scroll_column` box wherever F5 left it; the
    three parts follow it by the native fractions, so the up arrow, the
    track and the down arrow can never drift apart from each other.
    """
    cx, cy, cw, ch = column_rect
    _, _, nw, nh = CONTROLS["scroll_column"][1]
    fx, fy = cw / nw, ch / nh
    return {name: (cx + x * fx, cy + y * fy, w * fx, h * fy)
            for name, (x, y, w, h) in SCROLL_PARTS.items()}


def icon_cells(grid_rect):
    """The twenty big-icon cells inside `grid_rect`, in its own space.

    `Get_Fltscrn_Big_Icon_XY_` (flt2.cpp:116-128) in one place: index ->
    `(347 + 62*(i%4), 53 + 60*(i//4))`, cell 58 x 57. The grid rect is
    the part of `icon_area` left of the scroll column, which is what
    `grid_rect` gives. Returns a list of 20 rects in display order.
    """
    gx, gy, gw, gh = grid_rect
    span_w = (GRID_COLUMNS - 1) * GRID_STEP_X + GRID_CELL_W
    span_h = (GRID_ROWS - 1) * GRID_STEP_Y + GRID_CELL_H
    fx, fy = gw / span_w, gh / span_h
    cells = []
    for i in range(GRID_MAX_ICONS):
        x = (i % GRID_COLUMNS) * GRID_STEP_X
        y = (i // GRID_COLUMNS) * GRID_STEP_Y
        cells.append((gx + x * fx, gy + y * fy,
                      GRID_CELL_W * fx, GRID_CELL_H * fy))
    return cells


def native_grid():
    """The grid's own native rectangle, (347, 53, 244, 297)."""
    return (GRID_ORIGIN[0], GRID_ORIGIN[1],
            (GRID_COLUMNS - 1) * GRID_STEP_X + GRID_CELL_W,
            (GRID_ROWS - 1) * GRID_STEP_Y + GRID_CELL_H)


def native_cells():
    """The twenty cells in NATIVE pixels, `(x, y)` top-left each.

    The field list's own coordinates: `Add_Fltscrn_Big_Icon_Fields_`
    builds each big-icon field at `(x, y, x + 58, y + 57)` with x and y
    from `Get_Fltscrn_Big_Icon_XY_(slot)` (flt2.cpp:288-290, :313-320),
    so this is what `fltwire` matches a live field against.
    """
    return [(int(round(x)), int(round(y)))
            for x, y, _w, _h in icon_cells(native_grid())]


def grid_rect(icon_area, scroll_column):
    """The part of `icon_area` the icons use: everything left of the
    scroll column, by the native gap between the two (590 -> 605)."""
    ax, ay, aw, ah = icon_area
    sx = scroll_column[0]
    gap = (CONTROLS["scroll_column"][1][0]
           - (GRID_ORIGIN[0] + (GRID_COLUMNS - 1) * GRID_STEP_X
              + GRID_CELL_W))
    f = aw / REGIONS["icon_area"][2]
    return (ax, ay, max(0.0, sx - gap * f - ax), ah)
