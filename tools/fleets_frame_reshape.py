#!/usr/bin/env python3
"""The Fleets frame's new proportions — work order 153, Part A.

**WHAT MOVES AND WHY.** The ship panel could not hold the original's
readout even after font scaling (work order 152, item 7), so Data
accepted a new layout: the map gives up 195 px of height to the panel,
the left column gives up the width the map loses to keep its aspect,
and the right column takes that width back. In 4K source pixels:

    map hole      1812 x 1101  ->  1491 x  906   (aspect 1.6458 kept)
    ship panel    1801 x  382  ->  1480 x  577
    left column   321 px narrower, top and bottom edges unmoved
    right column  321 px wider, right edge unmoved

**THE METHOD IS THE 3-SLICE OF WORK ORDER 151, GENERALISED.** There it
rebuilt one button; here it rebuilds the whole frame, so it is written
as a piecewise-linear remap of each axis: a list of segments, each
either an ANCHOR copied pixel for pixel or an ELASTIC run resampled to
a new length. Every corner, chamfer, rivet, bracket and V-notch sits
in an anchor; every elastic run is a straight run, chosen against a
MEASUREMENT of the artwork and not by eye — `_measure.py` prints the
same profile these numbers came off (see `SEGMENT_PROVENANCE`).

**WHY THREE BANDS ON THE RIGHT AND ONE ON THE LEFT.** A band is a range
of rows sharing one x-remap. The left column needs only one: an elastic
run in [500, 1770) lies inside the map, the status strip AND the ship
panel at once, so all three lose 321 px while PREV and NEXT, which lie
outside it, keep their size and NEXT simply slides left. The right
column cannot: the four cells, the three buttons of the first row and
the four of the second divide the same width differently, and one
profile would have to grow ALL of a button and a cell by the same
amount. So the grid, button row 1 and button row 2 each get their own
profile, cut at rows 1560 and 1778 — measured flat to 4.3 and 3.7 grey
levels across the whole column, which is what keeps the two rails that
cross the cut from shearing.

**THE OUTER RING IS NOT TOUCHED**, which the row band states: rows
outside [153, 1987) are copied. The frame canvas stays 3840x2160
(decision 70).

Not a command-line tool: `tools/fleets_frame_build.py` calls `reshape`
between the unlit rebuild and the cut.
"""

from PIL import Image

#: The rows the transform touches at all. Outside them is the outer
#: ring and the full-width bars just inside it, which Data's order
#: leaves alone. Measured: across x 500..3615 the largest one-pixel
#: horizontal step is 8.3 grey levels at row 152 and 3.3 or less at
#: 153..169, and 3.3 or less at 1975..1987 against 9.3 at 1988 — so the
#: band ends where the ring's own edge begins and no ring pixel moves.
Y_BAND = (153, 1987)

#: The columns the VERTICAL remap applies to: the left column and the
#: plain chassis right of it. It stops before the right column, whose
#: height does not change. 2080 and not the rail's own edge at 2064
#: because the strip 2068..2130 is featureless chassis — its brightest
#: pixel over the whole band is 26 of 255 — so the seam has nothing to
#: break; 175 sits in the same kind of strip between the ring's arm and
#: the map window, where the largest horizontal step over the band is
#: 34 and that one is row 1987, outside it.
Y_REMAP_X = (175, 2080)

#: What the map gives and the panel takes, and what the left column
#: gives the right one. Both are Data's numbers, and both are checked
#: against the holes that come out (`targets`).
MAP_LOSS = 195
COLUMN_SHIFT = 321

#: THE VERTICAL SEGMENTS, `(start, stop, out_length)`.
#: An out_length equal to `stop - start` is an anchor.
#:
#:   153..330   the map window's top border and its two top brackets
#:   330..1190  ELASTIC — inside the map, between the brackets: the two
#:              side rails and the starfield, which is inside the hole
#:              and is cut away. 860 -> 665 loses the 195.
#:   1190..1658 the map's bottom brackets, the three small boxes, the
#:              chassis between them and the ship panel's top brackets,
#:              all sliding up 195 as one piece
#:   1658..1815 ELASTIC — inside the ship panel, between ITS brackets
#:              (which end at 1652 and begin at 1822 on the left rail).
#:              157 -> 352 gives the 195 back.
#:   1815..2160 the panel's bottom brackets, its border and the chassis
#:              below, unmoved
Y_SEGMENTS = [
    (0, 153, 153),
    (153, 330, 177),
    (330, 1190, 665),
    (1190, 1658, 468),
    (1658, 1815, 352),
    (1815, 2160, 345),
]

#: THE LEFT HALF OF EVERY x PROFILE, shared by all three bands — which
#: is what keeps the left column from shearing at a band cut.
#:
#:   0..500       the ring's left arm, the chassis, the map's and the
#:                panel's left borders and brackets, PREV in full
#:   500..1770    ELASTIC. Inside the map (228..2039), the status strip
#:                (480..1783) and the ship panel (234..2034) at the same
#:                time, and flat to 5 grey levels over the whole height.
#:                1270 -> 949 takes the 321 off all three at once.
#:   1770..2134   NEXT, the map's right bracket, the panel's right
#:                border and the chassis up to the right column's own
#:                frame line — translated 321 px left as one piece
X_LEFT = [(0, 500, 500), (500, 1770, 949), (1770, 2134, 364)]

#: BAND G — the grid. One elastic run inside each cell's straight top
#: and bottom edge, 80 px each, and the odd pixel in the gap between
#: the last cell and the scroll bar's housing so that all twenty cells
#: stay ONE size: `frame_holes.name_holes_fleets` finds the grid by
#: looking for twenty holes that share a width and a height, and 321/4
#: is not a whole number.
#:
#: The scroll bar keeps its width and its place: everything from 3440
#: on is an anchor at offset 0, and `fltgeom.SCROLL_SRC_COLUMN` needs
#: no new measurement.
X_BAND_GRID = [
    (2134, 2250, 116), (2250, 2420, 250),      # cell column 0  +80
    (2420, 2570, 150), (2570, 2730, 240),      # cell column 1  +80
    (2730, 2870, 140), (2870, 3030, 240),      # cell column 2  +80
    (3030, 3180, 150), (3180, 3330, 230),      # cell column 3  +80
    (3330, 3400, 70), (3400, 3440, 41),        # the odd pixel   +1
    (3440, 3840, 400),                          # scroll bar, frame, ring
]

#: BAND B1 — ALL, RELOCATE, SCRAP. The 321 is split in proportion to
#: the three plates' present widths (398:451:445 -> 99:112:110), so the
#: row keeps its rhythm; the two V-notches between the plates are
#: anchors and keep their pixel size.
X_BAND_ROW1 = [
    (2134, 2200, 66), (2200, 2550, 449),       # ALL       +99
    (2550, 2640, 90), (2640, 3050, 522),       # RELOCATE  +112
    (3050, 3140, 90), (3140, 3550, 520),       # SCRAP     +110
    (3550, 3840, 290),
]

#: BAND B2 — LEADERS, SUPPORT, COMBAT, RETURN, in proportion to
#: 330:285:288:353 -> 84:73:74:90. SUPPORT and COMBAT have already been
#: rebuilt unlit by `fleets_frame_build._unlit` when this runs, at the
#: widths the source painted them; widening them here is the same
#: 3-slice a second time and their corners are anchors in both.
X_BAND_ROW2 = [
    (2134, 2200, 66), (2200, 2480, 364),       # LEADERS   +84
    (2480, 2570, 90), (2570, 2810, 313),       # SUPPORT   +73
    (2810, 2900, 90), (2900, 3150, 324),       # COMBAT    +74
    (3150, 3240, 90), (3240, 3550, 400),       # RETURN    +90
    (3550, 3840, 290),
]

#: `(first row, last row + 1, profile)`. The two cuts are the flattest
#: rows between the grid and the buttons and between the two button
#: rows: across x 2200..3560 the largest one-pixel horizontal step is
#: 4.3 at 1550..1567 and 3.7 at 1772..1785.
X_BANDS = [
    (153, 1560, X_LEFT + X_BAND_GRID),
    (1560, 1778, X_LEFT + X_BAND_ROW1),
    (1778, 1987, X_LEFT + X_BAND_ROW2),
]

#: Where the numbers above were read off, so a later session can
#: re-measure rather than trust them. `tools/fleets_frame_measure.py`
#: prints all three profiles from the source.
SEGMENT_PROVENANCE = "tools/fleets_frame_measure.py"


def _check(segments, total, delta, what):
    """Segments must tile the axis and move it by exactly `delta`."""
    pos = 0
    for lo, hi, out in segments:
        if lo != pos:
            raise ValueError(f"{what}: gap or overlap at {lo}, expected {pos}")
        if out < 1 or hi <= lo:
            raise ValueError(f"{what}: empty segment {(lo, hi, out)}")
        pos = hi
    if pos != total:
        raise ValueError(f"{what}: segments end at {pos}, not {total}")
    got = sum(out - (hi - lo) for lo, hi, out in segments)
    if got != delta:
        raise ValueError(f"{what}: moves the axis by {got}, not {delta}")


def _apply(im, segments, axis):
    """One axis remapped. `axis` 0 is x, 1 is y. Anchors are copied."""
    w, h = im.size
    out_len = sum(s[2] for s in segments)
    size = (out_len, h) if axis == 0 else (w, out_len)
    out = Image.new(im.mode, size)
    at = 0
    for lo, hi, n in segments:
        if axis == 0:
            piece = im.crop((lo, 0, hi, h))
            if n != hi - lo:
                piece = piece.resize((n, h), Image.LANCZOS)
            out.paste(piece, (at, 0))
        else:
            piece = im.crop((0, lo, w, hi))
            if n != hi - lo:
                piece = piece.resize((w, n), Image.LANCZOS)
            out.paste(piece, (0, at))
        at += n
    return out


def _validate():
    _check(Y_SEGMENTS, 2160, 0, "Y_SEGMENTS")
    for y0, y1, segs in X_BANDS:
        _check(segs, 3840, 0, f"x band {y0}..{y1}")
        elastic = [s for s in segs if s[2] != s[1] - s[0]]
        # the left column loses exactly what the right column gains
        left = sum(s[2] - (s[1] - s[0]) for s in elastic if s[1] <= 2134)
        if left != -COLUMN_SHIFT:
            raise ValueError(f"x band {y0}..{y1}: left column moves {left}")
    # and the vertical halves match the order's one number
    lost = sum(s[2] - (s[1] - s[0])
               for s in Y_SEGMENTS if s[1] <= 1190)
    if lost != -MAP_LOSS:
        raise ValueError(f"the map loses {lost}, not {MAP_LOSS}")


def reshape(im):
    """Data's new proportions, from the source's own pixels.

    Vertical first, on the left column only; then horizontal, one
    profile per band. Both leave the canvas 3840x2160.
    """
    _validate()
    if im.size != (3840, 2160):
        raise ValueError(f"the source is {im.size}, not 3840x2160")

    xa, xb = Y_REMAP_X
    out = im.copy()
    out.paste(_apply(im.crop((xa, 0, xb, 2160)), Y_SEGMENTS, 1), (xa, 0))

    y0b, y1b = Y_BAND
    final = out.copy()
    for y0, y1, segs in X_BANDS:
        if y0 < y0b or y1 > y1b:
            raise ValueError(f"band {y0}..{y1} leaves the row band {Y_BAND}")
        final.paste(_apply(out.crop((0, y0, 3840, y1)), segs, 0), (0, y0))
    return final


#: WHAT THE HOLES MUST COME OUT AS, in source pixels — the order's own
#: figures, restated as an assertion rather than as prose. The build
#: raises if the cut does not produce exactly these, so a segment
#: edited by hand cannot quietly move a box.
TARGET_HOLES = {
    "inset_map": (228, 211, 1491, 906),
    "ship_panel": (234, 1350, 1480, 577),
    "prev_fleet": (233, 1180, 183, 113),
    "status_band": (480, 1175, 983, 119),
    "next_fleet": (1522, 1179, 191, 114),
    "btn_all": (1851, 1607, 497, 126),
    "btn_relocate": (2400, 1606, 563, 126),
    "btn_scrap": (3015, 1607, 555, 125),
    "btn_leaders": (1852, 1807, 414, 125),
    "btn_support": (2313, 1807, 358, 125),
    "btn_combat": (2719, 1807, 362, 125),
    "btn_return": (3127, 1806, 443, 126),
}
#: The grid: four columns 341 wide (261 + 80), the three gutters 44, 44
#: and 40 as the source painted them, and five rows that do not move —
#: the right column changes in x only.
#:
#: **THE CELLS COME OUT 221 TALL WHERE THEY WERE 219, AND THAT IS THE
#: DETECTOR CATCHING UP, NOT THE RESHAPE.** `_openings` grows an edge
#: while the next line is 80 % dark; at the cell's lower bevel that
#: line is dark everywhere except under the two corner brackets, so
#: the fraction depends on how WIDE the cell is. At 261 px the
#: brackets were 24 % of rows 444 and 445 and the walk stopped at 443;
#: at 341 px they are 19 % and it reaches 445. The paint says 445 is
#: right: a column through the middle of a cell reads 8.7 at row 445
#: and 29.0 at 446, so the interior always ended there and the old cut
#: was three rows short of it. Recorded rather than tuned away —
#: nothing about the threshold changed.
TARGET_CELL_SIZE = (341, 221)
TARGET_CELL_X = (1892, 2277, 2662, 3043)
TARGET_CELL_Y = (225, 488, 751, 1014, 1277)


def _anchor_offsets(segments):
    """`[(lo, hi, delta)]` for the segments copied 1:1."""
    out, at = [], 0
    for lo, hi, n in segments:
        if n == hi - lo:
            out.append((lo, hi, at - lo))
        at += n
    return out


def anchor_pairs():
    """Every region the reshape TRANSLATES and does not resample.

    `[(sx, sy, w, h, dx, dy)]` in source pixels: the rectangle at
    `(sx, sy)` in the unlit source appears unchanged at
    `(sx + dx, sy + dy)` in the result. Every corner, chamfer, rivet,
    bracket and V-notch of the frame is inside one of them, which is
    what makes "no stretched corners" a measurement instead of a
    claim — the smoke test compares the two, pixel for pixel.

    Only whole rectangles are listed. An x anchor that straddles the
    vertical remap's own edge is split at it, so a pair is either
    entirely inside the columns the y remap touches, where the y
    anchors decide its rows, or entirely outside, where every row of
    the band is at the same offset.
    """
    _validate()
    xa, xb = Y_REMAP_X
    yanch = _anchor_offsets(Y_SEGMENTS)
    pairs = []
    for by0, by1, segs in X_BANDS:
        for lo, hi, dx in _anchor_offsets(segs):
            for x0, x1 in ((lo, min(hi, xa)), (max(lo, xa), min(hi, xb)),
                           (max(lo, xb), hi)):
                if x1 <= x0:
                    continue
                if xa <= x0 and x1 <= xb:            # the y remap applies
                    for ly0, ly1, dy in yanch:
                        y0, y1 = max(by0, ly0), min(by1, ly1)
                        if y1 > y0:
                            pairs.append((x0, y0, x1 - x0, y1 - y0, dx, dy))
                else:                                 # rows are untouched
                    pairs.append((x0, by0, x1 - x0, by1 - by0, dx, 0))
    return pairs


#: THE MAP HOLE BEFORE THIS WORK ORDER, so "the stretch did not
#: change" is something a check can measure rather than a sentence.
#: `aspect / (INSET_SCALE_X / INSET_SCALE_Y)` is the factor the galaxy
#: is stretched by when it is drawn into the box, and the galaxy's own
#: 1.265 is the same for every galaxy size (work order 151).
SOURCE_MAP_HOLE = (1812, 1101)
