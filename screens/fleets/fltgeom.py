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
    # RETURN COMES FROM ITS FIELD AND FROM NOTHING ELSE — corrected by
    # work order 137 E4, and the correction is in where the numbers come
    # from rather than in the numbers.
    #
    # Help 374 is (456, 430)-(628, 456) (evanhelp.cpp:165), a strip that
    # reaches left across the two filter radios; they have their own
    # entries 372 and 373 earlier in the table and win the first-match
    # test (fields.cpp:2924-2932), so the strip is not RETURN's extent
    # and never was. Drawing it there would put RETURN over SUPPORT and
    # COMBAT.
    #
    # The button is added at (556, 430) (flt1.cpp:1201-1204) and its
    # SIZE is FLEET.LBX 12 at runtime, in no source — so the size is
    # taken from LEADERS, the other button of the same row, added the
    # same way from the same artwork family (:1234). That is 73 x 27.
    #
    # THE TRAP THIS REPLACES: the entry used to say "right and bottom
    # from the help strip", and 556 + 73 - 1 IS 628. The two agree, so
    # the wrong derivation produced the right rectangle and would have
    # gone on producing it until the strip moved. Decision 38 keeps the
    # help rectangle in `help.json` and lets it decide no box edge.
    "btn_return": ("button_band", (556, 430) + _r(342, 430, 414, 456)[2:]),
}

#: THE TWO AREAS HD LEAVES EMPTY, and the box that says so in each.
#:
#: A `text` box draws the string and nothing else — no panel, no border
#: (decision 37) — and the wording is `layout.json`'s `words`
#: (decision 15). Both areas are marked OMISSION in `layout.json`'s
#: `marks`, beside the four `fltwire` already carries, and a smoke
#: check holds all six.
#:
#: The rectangles are INSIDE their region, not the region itself: a
#: text box on the region's own edge would sit on its `thin_border`
#: line, which is the fault 137 E3 is about. Each is the region's
#: native rect inset by `HINT_INSET` native px on every side, so the
#: two follow their region if F5 or a new opening moves it.
HINT_INSET = 6

#: hint box -> (the region it sits in, the `words` key it draws)
HINTS = {
    "inset_hint": ("inset_map", "inset_hint"),
    "status_hint": ("status_band", "status_hint"),
}


#: How tall the inset's hint strip is, in native px. The inset is a
#: MAP and the hint is not allowed to sit on it — see `hint_rect`.
HINT_BAND = 13


def hint_rect(region):
    """A hint box's native rect: its region, inset on every side.

    **THE INSET'S IS A STRIP ALONG THE BOTTOM EDGE, NOT THE WHOLE BOX.**
    It used to be the region inset on all four sides, which centres the
    words in the middle of the galaxy — across the stars the screen
    exists to show, and over the exact area a player reads positions
    off. The strip is `HINT_BAND` native px at the bottom edge; whether
    it is DRAWN at all is decided per frame against the star positions
    (`screen._fill_hints`), because an edge with a star on it is still
    a star underneath words.
    """
    x, y, w, h = REGIONS[region]
    if region == "inset_map":
        return (x + HINT_INSET, y + h - HINT_INSET - HINT_BAND,
                w - 2 * HINT_INSET, HINT_BAND)
    return (x + HINT_INSET, y + HINT_INSET,
            w - 2 * HINT_INSET, h - 2 * HINT_INSET)


def hint_collides(stars, region="inset_map"):
    """True when any star falls inside that region's hint strip.

    The star list is `colonyrows.galaxy_inset_stars`, in the same
    native space `REGIONS` is in, and a star is drawn as a 5x5 sprite
    offset `-2, -2` (movebox.cpp:85) — so the sprite's own extent is
    tested, not its centre point. `REGIONS[region]` is the box and the
    star coordinates are relative to it, which is why the box origin is
    added before the comparison.
    """
    bx, by, _bw, _bh = REGIONS[region]
    hx, hy, hw, hh = hint_rect(region)
    for sx, sy, _colour in stars or []:
        x, y = bx + sx - 2, by + sy - 2
        if x + 5 > hx and x < hx + hw and y + 5 > hy and y < hy + hh:
            return True
    return False


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
#: **MEASURED OFF THE v4 FRAME, because the scroll bar is PAINTED and
#: not a hole** (work order 146). Everything else on this screen gets
#: its rect from a transparent cutout; this one has none, so the hit
#: rects and the thumb have to be put on the art by measurement or
#: they will sit beside it. Source pixels in
#: `screens/fleets/assets/frame.png` (1445x811):
#:
#:   housing      x 1275..1308, the two rails at 1275-1280 and
#:                1302-1308 with the dark track channel between them
#:   up arrow     y  76..123    (block, chamfered, triangle at 98..112)
#:   track        y 124..512    (luma ~22 inside the channel)
#:   down arrow   y 513..564    (block, triangle at 532..550)
#:
#: "An asset is not a measurement" cuts the other way here: these ARE
#: measurements OF the asset, because the asset is where the bar is.
#: What they must never become is a source for anything else's
#: geometry.
#: **THE CHAMFER, MEASURED FROM THE FRAME.** Every v4 hole has
#: rounded/chamfered corners, so the largest axis-aligned rectangle
#: fully inside a hole is the hole inset by this many SOURCE pixels on
#: every side. Content drawn outside it is not clipped — it is drawn
#: and then covered, because the frame image renders last
#: (`_render_frame_image`), which is how the ship panel's first line
#: disappeared under the corner the first time v4 was rendered.
#:
#: A HAND-COPIED VALUE WITH A CHECKER (decision 36): the smoke test
#: re-derives every number here from `assets/frame.png` and fails if
#: the frame and this table stop agreeing.
#: **THE v4 FRAME IS AN HD INVENTION.** The native Fleets screen has
#: nothing like it: FLEET.LBX entry 0 (`Draw_Fleet_Screen_`,
#: flt1.cpp:385) is flat blue plates with thin bevels, and every
#: measurement in this module that cites a `flt1.cpp` line describes
#: THAT screen, not this frame. The frame's holes are Data's layout,
#: not the original's geometry, and nothing in the original can be
#: cited for where they are. Marked here, in `layout.json`'s
#: `frame._note`, in `v3_projektstatus.md`, and held by a smoke check.
CONTENT_INSET_SRC = {
    "inset_map": 14, "ship_panel": 13, "status_band": 6,
    "prev_fleet": 5, "next_fleet": 5,
    "btn_all": 7, "btn_relocate": 6, "btn_scrap": 6,
    "btn_leaders": 6, "btn_support": 6, "btn_combat": 7,
    "btn_return": 6,
}
#: every cell is the same hole, so one number covers all twenty
CONTENT_INSET_SRC.update({f"cell_{i:02d}": 6 for i in range(20)})

#: The frame's own pixel size, which `to_ref` scales from. Not a
#: layout number — the only thing it is allowed to convert is the
#: chamfer above.
FRAME_SRC_SIZE = (1445, 811)

SCROLL_V4_COLUMN = (1275, 76, 34, 489)
SCROLL_PARTS = {
    "up": (0, 0, 34, 48),
    "track": (6, 48, 21, 389),
    "down": (0, 437, 34, 52),
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


#: NATIVE PX A GROUP IS GROWN BY, so no control sits ON its outline.
#:
#: `status_band` and `button_band` are HELP rectangles and so are the
#: controls inside them — 363/364/365 and 368..374, evanhelp.cpp:154-165
#: — and the original's own table gives the group and its first control
#: the same left edge (19, and 342). It could: the original draws no
#: outline there at all, only the artwork. HD draws the group as a
#: `thin_border`, which is a 1 px rounded line (`StyleRenderer.draw_plate`,
#: core/style.py:418-420), and a control whose edge is ON that line
#: doubles it.
#:
#: SO THE GROUP GIVES WAY, NEVER THE CONTROL, which is decision 54's
#: rule for the same collision one level up ("shrink the slot, not the
#: thing that is checked"). Every rectangle in `REGIONS` and `CONTROLS`
#: stays the transcription it is; this pad is applied when the two
#: UNION regions are seated, and it is ours — the unions are not drawn
#: by the original and are named as ours in `REGIONS` already.
#:
#: 2 and not 1: the seat's factor is about 2.9 reference px per native
#: px today, so one native px would be plenty — but the pad is in
#: NATIVE px so that it survives a different opening, and a native 1
#: rounds to a reference gap that a later, smaller opening could round
#: back to 0. 2 native px is 5 reference px at today's seat, which is
#: under half the 10 px corner radius the line is drawn with and
#: therefore changes nothing anyone can see.
GROUP_PAD = 2

#: The regions the pad applies to: the two that are UNIONS of controls.
#: `inset_map`, `ship_panel` and `icon_area` hold no control box, and
#: `icon_area` holds `scroll_column`, which is the one case where the
#: original itself puts a gap (help 361 starts at x 605, the area ends
#: at 619 — the column IS the area's right edge and has 14 px of its
#: own).
PADDED_REGIONS = ("status_band", "button_band")


def _padded(name, rect):
    if name not in PADDED_REGIONS:
        return rect
    x, y, w, h = rect
    return (x - GROUP_PAD, y - GROUP_PAD,
            w + 2 * GROUP_PAD, h + 2 * GROUP_PAD)


def seat_regions(opening, bleed=BLEED):
    """Every region and control, seated, as rounded reference rects.

    The dict `tools/fleet_boxes.py` writes and the smoke test checks.
    """
    out = {}
    for name, rect in REGIONS.items():
        out[name] = [int(round(v))
                     for v in to_ref(_padded(name, rect), opening, bleed)]
    for name, (_parent, rect) in CONTROLS.items():
        out[name] = [int(round(v)) for v in to_ref(rect, opening, bleed)]
    for name, (region, _word) in HINTS.items():
        out[name] = [int(round(v))
                     for v in to_ref(hint_rect(region), opening, bleed)]
    return out


def scroll_parts(column_rect):
    """The column box's three parts in the SAME space it is given in.

    `column_rect` is the `scroll_column` box wherever F5 left it; the
    three parts follow it by the native fractions, so the up arrow, the
    track and the down arrow can never drift apart from each other.
    """
    cx, cy, cw, ch = column_rect
    # v4: scaled against the COLUMN AS MEASURED ON THE FRAME, not
    # against the native control rect — the bar is painted there and
    # the parts have to land on it.
    _, _, nw, nh = SCROLL_V4_COLUMN[2], SCROLL_V4_COLUMN[3], 0, 0
    nw, nh = SCROLL_V4_COLUMN[2], SCROLL_V4_COLUMN[3]
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
