"""The row's geometry: where every box in a colony row is.

Split out of `colonylist` on 6 September 2026, when that file stood
at exactly 300 code lines against the ~300 guideline (decision 6) and
the row's box arithmetic had to go somewhere. The seam is real
rather than a
place to cut: this tree already separates the NUMBERS
(`colonyrows`) from the DRAWING (`colonylist`), and what sat between
them unnamed was the ARITHMETIC — how many rows fit, where the track
starts, which slot a pixel is in, which job a click names.

**IT IS ALSO DECISION 5'S HOME.** "One function produces the rect;
drawing and clicking both call it" is only enforceable if there is
one place the rect comes from. The drop targets were two copies of a
thirds calculation that agreed with each other and disagreed with the
cells until 5 September; that could happen because the geometry was
scattered through a drawing module. Everything here is a pure
function of (area, cfg, scale, row) and nothing here draws.

Nothing in this module imports pygame for rendering — `Rect` is used
as a value type and that is all.
"""
import collections

import pygame

from core import zoomtables

from .colonyrows import POP_LIMIT_CAP


#: What is left of the row's own measurements once the columns are
#: boxes and the band is the window divided by the row count: the
#: gutter between two cells, and nothing else. **NINE VALUES DIED
#: HERE on 8 September 2026** — `row_height`, `pad_x`, `pad_y`,
#: `name_width`, `name_gap`, `bar_height`, `tail_width`,
#: `building_width` and `growth_gap`. Every one of them answered a
#: question a box or the row count now answers, and a tuned number
#: that agrees with a derived one is the second copy decision 5 is
#: about.
Track = collections.namedtuple("Track", "gap band_h")


def track_metrics(area, cfg, scale):
    """The row's two remaining measurements.

    `band_h` is the window divided by `list.row_count` — TEN, the
    original's own window (`_list_col[10]`, colsum.cpp:348) — and it
    is what the figure step, the cell, the plate and the drop rect
    are all derived from. `gap` is the gutter a crowded column gives
    up first (see `_column_boxes`).
    """
    return Track(gap=max(1, int(cfg.get("square_gap", 2) * scale)),
                 band_h=band_height(area, cfg))


def band_height(area, cfg):
    """The row band — `list_area` height divided by the row count.

    One expression, one home. TEN rows at every resolution because
    that is the original's window and not a number that looked right:
    `COLSUM::_list_col[10]` and `Update_Col_List_` fills exactly that
    many (colsum.cpp:348). The remainder goes to the LAST band, the
    same rule the columns and the header plates use, so the rows tile
    the window exactly instead of leaving a strip nothing owns.
    """
    return max(1, area.h // max(1, int(cfg.get("row_count", 10))))


def figure_step(area, cfg):
    """The largest sprite step whose figure fits one band.

    **DERIVED, never declared** — the hand-written per-resolution
    table is gone. A master is 28 px (decision 50) and a step is an
    integer swap (decision 28), so the step is the largest whose
    `28 * step` fits the band under the plate's own top line.

    THE `+ PLATE_LINE` IS MEASURED, NOT ASSUMED. The cell plate is a
    1 px line and 46 of the 54 masters carry ink on canvas row 0, so
    a figure blitted at the band's top would paint over it. The
    BOTTOM line needs nothing: every master has at least 3
    transparent rows below its ink, which is the same measurement the
    row clip rests on.
    """
    band = band_height(area, cfg)
    fits = [s for s in zoomtables.FIGURE_STEPS
            if 28 * s + PLATE_LINE <= band]
    return max(fits) if fits else min(zoomtables.FIGURE_STEPS)


#: The cell plate's line, in device px — `StyleRenderer.draw_plate`
#: draws width 1 at every resolution. The figure clears it at the top
#: and the masters' own bottom margin clears it at the bottom.
PLATE_LINE = 1


#: `runs` is (zone, start_slot, count) per profession — the squares
#: fill them. `filled`..`reach` is the free region, `reach`..
#: POP_LIMIT_CAP the unreachable one.
#:
#: `spans` is the same thing for ALL THREE zones including the empty
#: ones, as (start_slot, count) in ECON order. `runs` drops the
#: empties because nothing draws them; `drop_targets` needs to know
#: WHERE an empty group would have been, and computing that a second
#: time is how the drawing and the hit test start to disagree.
Regions = collections.namedtuple("Regions", "runs filled reach spans")


#: The key `cfg` carries the column table under. The screen binds the
#: six column BOXES into its `list` block on load
#: (`colonyheader.install_columns`), so the table travels with every
#: other row value and there is no module state to leak between one
#: caller and the next — which a global would do the moment one check
#: rendered the real screen and the next used a synthetic fixture.
COLUMNS_KEY = "columns"

#: The key `cfg` carries `list_area`'s own REFERENCE rect under, as
#: `(ref_x, ref_width)`. Bound beside the table by the same call, so
#: the cutout a column is a fraction of travels with the columns and
#: cannot be a second lookup that misses.
COLUMNS_SPAN_KEY = "columns_span"


def columns(area, cfg):
    """{key: (x, width)} in SCREEN px, from the six column BOXES.

    Empty when `cfg` carries no column table, and the single-track
    arithmetic runs then — which is what the synthetic fixtures in
    the checks exercise, and what the row was before Stage 4.

    **THE BOXES ARE THE COLUMNS — 8 September 2026.** `cfg[COLUMNS_KEY]`
    holds `[(key, Box)]`, live objects, so a column dragged in the F5
    editor moves the cells, the plates, the drop rects and the
    heading above it on the same frame. It used to hold
    `[(key, ref_width)]` baked out of `layout_reference.json` at
    screen load, tiled here, and tiled a SECOND time in
    `plate_rects` — two arithmetics that agreed by construction and
    could not be edited.

    **THE COLUMN IS A FRACTION OF THE CUTOUT, NOT A POSITION IN THE
    WINDOW — 9 September 2026.** What is read off a box is its
    REFERENCE left edge, and it is mapped into `area`, which is
    `list_area` resolved through the same `Layout.rect` call the
    frame image goes through (`screen._scale_frame`). Both edges of
    every column therefore come out of one rect that is recomputed
    every frame.

    Until this date the left edge came from `Box.screen_rect`, which
    `Box.update_layout` writes ONCE per layout change. That is a
    device coordinate with a lifetime, and it outlived the window:
    `ScreenBase.on_resize` calls `_reload_boxes`, which REPLACES
    `screen.boxes` with new objects, while the table bound at
    `enter()` went on pointing at the discarded ones. Measured on
    8 September 2026 at all four F9 sizes — after any resize away
    from the start size the six columns kept the start size's device
    x (105, 408, 751, 1112, 1452, 1767) while `list_area` and the
    frame followed the new one. At 2560x1440 the frame's left rail
    was then drawn over the NAME text; at 3440x1440 the columns sat
    on the letterbox bar outside the frame entirely; and `col_scroll`,
    being the remainder, swelled from 35 px to 635, 1075 and 1837.
    Every value on the screen stayed correct, which is why it lived
    a day.

    **ONLY THE LEFT EDGE IS READ, and the width is the distance to
    the next column.** A box carries four numbers and three of them
    would be a second answer: the y and height are `list_area`'s
    because a column is a strip of the list, and the WIDTH is the
    gap to its neighbour because the six have to tile the window
    exactly. Reading the stored width instead opened a one-pixel seam
    at 1280x720 and 2048x1152 — `Box.update_layout` truncates x and
    width independently, so `int(x*s) + int(w*s)` and
    `int((x+w)*s)` disagree wherever the fractions add up. Mapping
    both edges through `area` with one expression makes the tiling
    true by construction rather than by two roundings agreeing: the
    first column starts at `area.x` because its offset into the
    cutout is zero, and the last ends at `area.right` because the
    span's end is the cutout's end.

    What that means at the editor: dragging a column moves a
    BOUNDARY, and its neighbour follows.
    `colonyheader.sync_columns` writes the derived width and the
    window's y and height back into the boxes, so the outline shows
    what the geometry did rather than what was dragged.
    """
    table = cfg.get(COLUMNS_KEY) or ()
    span = cfg.get(COLUMNS_SPAN_KEY)
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


#: The three job columns, in ECON order, as they are keyed above.
JOB_KEYS = ("farmers", "workers", "scientists")


def row_regions(row):
    """The three job groups of one row, in CELL counts.

    `runs` is (zone, first_cell_index, count) for the jobs that hold
    pops, `spans` the same for all three including the empty ones,
    `filled` the pops drawn and `reach` how many the colony could
    hold. **None of these are slots any more** — the column layout
    lays each job's cells inside its own column, so `row_boxes` is
    what turns a cell index into a rectangle and this counts.

    Zones are laid down in ECON order and clipped at POP_LIMIT_CAP,
    which the engine cannot pass either. Cells past `max_pop` are
    kept, not clipped: a pop is a fact, `max_pop` a computation with
    two documented deviations (`colonyrows.max_population`), so they
    stay visible and the disagreement stays visible with them.

    The count is `row["cells"]` where the row carries it — one entry
    per ICON, in the original's own draw order (decision 48) — and
    falls back to `row["jobs"]` for a row built without it, which is
    every synthetic fixture in the checks.
    """
    cells = row.get("cells")
    runs, spans = [], []
    used = 0
    for zone in range(3):
        count = (len(cells[zone]) if cells is not None
                 else row["jobs"][zone])
        n = max(0, min(count, POP_LIMIT_CAP - used))
        spans.append((used, n))
        if n:
            runs.append((zone, used, n))
        used += n
    return Regions(runs=tuple(runs), filled=used,
                   reach=max(0, min(row["max_pop"], POP_LIMIT_CAP)),
                   spans=tuple(spans))


#: One row's boxes, all of them, in screen pixels.
#:
#: `cells` is what is drawn; `targets` is the three job rects a drop
#: is tested against, and `name` is the fourth target — the colony
#: name's own column, which the original accepts a drop on as "put
#: them back" (`Send_Cluster_(colony, -1)`, colsum.cpp:909). `growth`
#: are the dashed capacity boxes after the gap, `beyond` the faint
#: line for the track a colony cannot reach yet, or None.
#:
#: **THE `markers` FIELD IS GONE — 8 September 2026.** It carried the
#: three F/W/S squares, which were an HD EXTENSION standing in for
#: headings a column-less row could not have. Stage 4 gave the row
#: five real columns with the original's own headings above them, so
#: the stand-in had nothing left to stand in for, and its own marking
#: said as much: "whether they stay is Stage 5's call". Removed with
#: the marking, in this commit, and the drop target did not move with
#: them — it was already the whole column (see `_column_boxes`).
RowBoxes = collections.namedtuple(
    "RowBoxes", "name cells targets growth beyond run_right")


def row_boxes(area, cfg, scale, row, band=None):
    """THE row geometry. Everything that draws or hits calls this.

    `band` is the (top, height) `row_bands` gave for this row; without
    it the rects carry x and width only and their y is 0, which is
    what a hit test wants and what the layout checks read.

    **NO JOB MARKERS — REMOVED 8 September 2026.** Three grey F/W/S
    squares used to head each group. They were an HD EXTENSION with
    one argument behind them: a row without columns cannot carry a
    heading, so a colony with everyone farming drew a run of squares
    and nothing said the other two jobs existed. Stage 4's five
    columns and the headings above them answer that, and the marking
    itself named this as Stage 5's call. The cells now start at their
    column's own left edge, which is where the original starts its
    icons — `(30 - squish) * i + left_x` with `left_x` the column
    (coldraw.cpp:349).

    **THE EMPTY-COLUMN DROP DID NOT DEPEND ON THEM.** In the column
    layout the target has always been the whole column rect, which is
    what the original's own per-row job field is (`Add_Scroll_Field_(
    left_x, top_y, …, right_x - left_x + 8, 30, …)`,
    coldraw.cpp:409, added in mode 1 whether or not the column holds
    an icon). This path — the single-track fallback, which only the
    synthetic fixtures reach — cannot say that: with no marker and no
    cells a job's target is empty, and `drop_band` answers None.
    Stated rather than papered over, because an invisible placeholder
    is exactly what this removal was for.

    **The growth boxes belong to the COLONY, not to a job**, so they
    follow all three groups after a fixed gap (`list.growth_gap`,
    a layout value and not a side effect of some other number).
    """
    track = track_metrics(area, cfg, scale)
    top, height = band if band else (0, 0)
    cols = columns(area, cfg)
    if not cols:
        # NO COLUMNS, NO ROW. The single-track geometry is gone with
        # the nine tuned values it was measured from (see `Track`);
        # a caller without the column boxes gets nothing rather than
        # a second layout that looks almost right.
        return RowBoxes(None, (), (), (), None, area.x)
    return _column_boxes(cols, cfg, scale, row, top,
                         height or track.band_h, track,
                         figure_step(area, cfg))


def _column_boxes(cols, cfg, scale, row, y, h, track, step):
    """One row laid out in the five columns — the Stage 4 geometry.

    **THE PITCH IS THE ORIGINAL'S OWN, SCALED.** Each job column's
    cells are laid at `colonyicons.column_pitch(job, count)`, which is
    `COLDRAW::Calculate_Squish_Step_` (coldraw.cpp:12-33) transcribed,
    multiplied by this column's HD width over its NATIVE width. So a
    column that squeezes in the original squeezes here, by the same
    amount, and a column that does not is drawn at the full 30-unit
    pitch. The HD row is the original's walk under a scale factor
    rather than a second layout that happens to look like it.

    **IDENTITY IS BY INDEX, NOT BY POSITION, and that is what makes
    the drawing free** (decision 48). Cell k of job j is slot k of the
    game's own column j: `colonysend` injects
    `colonyicons.slot_click_x(j, k, count)`, a NATIVE x computed from
    the same `column_pitch`. Nothing here is transferred into that
    call — the two share the index and the count, and the pixel each
    works in is its own. A cell drawn anywhere in its column would
    still click correctly; drawn at the original's pitch it also
    LOOKS like the thing it clicks.

    **THE CELLS START AT THE COLUMN'S OWN LEFT EDGE.** They used to
    start one marker's width in; the markers are gone (see
    `RowBoxes`) and the first cell moved left with them, which is
    also where the original puts its first icon — `left_x` is the
    column, `(30 - squish) * i + left_x` the slot (coldraw.cpp:349).

    **THE DROP TARGET IS THE WHOLE COLUMN AND ALWAYS WAS**, which is
    why removing the markers cost no click target and no invisible
    button was kept in their place. It is the original's own field:
    mode 1 adds `Add_Scroll_Field_(left_x, top_y, left_x, right_x + 8,
    left_x, right_x, right_x - left_x + 8, 30, …)` (coldraw.cpp:409)
    for every row and every job, unconditionally — the walk before it
    may have emitted nothing, and the field is added anyway, so an
    EMPTY column accepts a drop in the original exactly as it does
    here.

    **THE DEVIATION IN HEIGHT IS CLOSED — 8 September 2026.** The
    drop rect was `bar_h`, 30 reference px of a 58 px row, 52 % of
    the band, where the original's field is 30 px of a 31 px row
    pitch (`top_y = 31*i + 34`, colsum.cpp:311, height 30) — 97 %.
    A click in the outer 14 reference px of a row discarded the
    selection where the original would have dropped. **The target is
    the whole band now**, because the plate rect is the drop rect is
    the cell rect and all three are `column x band` (decision 5).
    Recorded as closed here, in `layout.json` under
    `move._drop_target_note`, and in `v3_projektstatus.md`.

    **NO GROWTH BOXES IN THIS LAYOUT.** They belong to the COLONY and
    not to a job, so in a row that is three job columns there is no
    place for them that is not a lie — a dashed box inside the
    scientists column says "scientists", which is what the colony's
    spare capacity is not. The headroom is already on screen, in the
    scan box the original puts it in (`Population (13/22)`,
    colsum.cpp:1196-1205). The code and its marking stay; Stage 5
    decides whether they come back somewhere honest.
    """
    from core import box
    from . import colonyicons
    regions = row_regions(row)
    cells, targets = [], []
    for job, key in enumerate(JOB_KEYS):
        cx, cw = cols[key]
        n_left, n_right = colonyicons.COLUMNS[job]
        count = regions.spans[job][1]
        # ONE PIXEL INSIDE THE PLATE'S LINE, and it is transcribed.
        # The original's icons start at `left_x` — 101 / 236 / 378 —
        # and its drawn cell boxes start at 100 / 235 / 377, measured
        # on `colony_summary_native_split.png`. So the first icon sits
        # exactly one pixel inside the box's own line, which is what
        # keeps the line visible with a full column. The same `+1` at
        # the top is what `figure_step` reserves.
        start = cx + PLATE_LINE
        room = max(1, cw - 2 * PLATE_LINE)
        # THE FACTOR IS THE SPRITE STEP, NOT THE COLUMN RATIO.
        # The step is the integer a 28 px native figure is drawn at
        # (decision 26), derived from the band, and the stacking decision
        # is that HD's extra width goes into the column RESERVATION
        # and never into figure spacing. Scaling the pitch by the
        # column ratio instead — 342 : 125, about 2.7 at 1080p —
        # spends that reservation on spacing, and every cell and every
        # drop target would move again the day Stage 3 draws sprites
        # at the step. Corrected 7 September 2026; it was the ratio
        # for one stop.
        # ONE HOME for the step: `figure_step` above answers it from
        # the band, `colonyfigures.FigureSet` loads the sprites at
        # what it says, and a pitch and a sprite that disagree are a
        # picture nothing would report. It was a hand-written table
        # per resolution until 8 September 2026, which could agree
        # with the band or not and nothing checked.
        pitch = min(colonyicons.column_pitch(job, max(count, 1)),
                    colonyicons.ICON_SPACING) * step
        # AND A CLAMP THAT CAN EXPIRE, decision 44's shape. The
        # original's own run is at most `right_x - left_x - 10` native
        # px (the `spacing / -3` term in Calculate_Squish_Step_), so at
        # the step it needs that times the step. Every supported
        # window reserves more than that except 1280x720, where the
        # reservation is 229 device px against 230 needed — see the
        # status document for the table. Written as a min so the
        # deviation ends the day the reservation is wide enough,
        # rather than as a special case for one window.
        if count and start + count * pitch > cx + cw - PLATE_LINE:
            pitch = room / float(count)
        # CELLS MAY NOT OVERLAP, and the arithmetic has to guarantee
        # it rather than the numbers happening to. `int((k+1)*p) -
        # int(k*p)` is either floor(p) or floor(p)+1, so a width of
        # floor(p) can never reach the next cell. The gap is given up
        # before the width is, because a cell narrower than a pixel is
        # not a cell — at a small window a crowded column draws its
        # squares touching, which is what the original's own squish
        # does with its icons.
        step_i = max(1, int(pitch))
        gap = track.gap if step_i > track.gap + 1 else 0
        cell_w = max(1, step_i - gap)
        for k in range(count):
            cells.append((job, k, pygame.Rect(
                start + int(k * pitch), y, cell_w, h)))
        targets.append((job, pygame.Rect(cx, y, cw, h)))
    name = None
    if "name" in cols:
        nx, nw = cols["name"]
        name = pygame.Rect(nx, y, nw, h)
    return RowBoxes(name, tuple(cells), tuple(targets),
                    (), None, cols[JOB_KEYS[-1]][0] + cols[JOB_KEYS[-1]][1])


def drop_targets(area, cfg, scale, row):
    """(job, Rect) per job — the whole column cell.

    One rect per job and never two boxes that look alike and behave
    differently, which is the trap decision 5 is about. It is the
    original's own field: `Add_Scroll_Field_(left_x, top_y, …,
    right_x - left_x + 8, 30, …)` (coldraw.cpp:409), added per row
    and per job whether or not the column drew an icon, which is why
    an empty column is a target here too.
    """
    return row_boxes(area, cfg, scale, row).targets


def name_rect(area, cfg, scale, row):
    """The colony name's own column — the FOURTH drop target, or None.

    TRANSCRIBED. A drop on the name field is `Send_Cluster_(colony,
    -1)` (colsum.cpp:909), and on the colony the cluster came from
    that is the re-flag branch: `requested_job == -1` sets `0x200`
    back and consults no rule (colmove.cpp:161-165), so the array
    ends exactly as it started. It is the original's "put them back",
    and it is the nearest thing this screen has to a cancel that is
    not a leave-the-screen path.
    """
    return row_boxes(area, cfg, scale, row).name


def on_name(area, cfg, scale, row, x):
    """Is `x` over the colony name's column?"""
    rect = name_rect(area, cfg, scale, row)
    # `rect is None`, NOT `not rect`: a pygame.Rect of zero HEIGHT is
    # falsy, and `row_boxes` is called without a band for every hit
    # test — that is the whole point of the no-band form, and it
    # would make this answer False for every click on the name.
    if rect is None or not rect.width:
        return False
    return rect.x <= x < rect.x + rect.width


def drop_band(area, cfg, scale, row, x):
    """Which job `x` names while a pick is held, or None.

    Outside all three is None, and None is a state: it discards the
    selection rather than dropping. The growth boxes are outside —
    they belong to the colony, not to a job.
    """
    for job, rect in drop_targets(area, cfg, scale, row):
        if rect.width and rect.x <= x < rect.x + rect.width:
            return job
    return None


def cell_at_x(area, cfg, scale, row, x):
    """(job, index) of the pop cell under `x`, or None.

    Index is within that job's cells, in the order they are drawn —
    which is the original's icon order (decision 48), because
    `colonyrows` builds the row that way. Bare column past the last
    cell answers None: there is nothing to pick up there. A pop in a
    HELD cluster has no cell either — `build_rows` clears its `0x200`
    exactly as `Get_Cluster_` does — so it cannot be picked twice.
    """
    for job, index, rect in row_boxes(area, cfg, scale, row).cells:
        if rect.x <= x < rect.x + rect.width:
            return job, index
    return None


def rows_drawn(area, cfg, scale, count):
    """How many of `count` rows `render` would actually draw.

    Exported so a caller — and the smoke test — can ask the question
    without re-deriving the pitch. The whole fault this answers was
    that nothing could ask it.
    """
    return len(row_bands(area, cfg, scale, count))


def row_bands(area, cfg, scale, count):
    """(top, height) for each row that FITS, in draw order.

    Decision 5: one function makes the rect and both the drawing and
    the hit-test call it. The hover selection reads the same bands
    `render` lays out, so a row that is hovered is by construction a
    row that is on screen — the last row is dropped rather than
    clipped, which is exactly the case a second copy of this
    arithmetic would get wrong.

    **`count` is the length of the WINDOW, not of the list.** Since
    the list scrolls, both callers pass `len(rows) - first`, and the
    band index this returns is a position on screen. Turning that
    back into an index into the rows is the screen's job, in
    `screen._row_at`, because the screen is where the offset lives —
    a band number used as a row number is the fault decision 5 exists
    for, one scroll offset removed.

    Fewer bands than `count` therefore means the tail of the window
    is not drawn. That is still the honest shape: nothing below the
    last band can be selected because nothing below it is there.
    """
    band = band_height(area, cfg)
    want = int(cfg.get("row_count", 10))
    bands, y = [], area.y
    for i in range(min(count, want)):
        # THE LAST BAND TAKES THE REMAINDER, the rule the columns and
        # the header plates already use, so the rows tile the window
        # exactly instead of leaving a strip that belongs to nobody.
        h = (area.bottom - y) if i == want - 1 else band
        if h <= 0:
            break
        bands.append((y, h))
        y += h
    return bands


def row_at(area, cfg, scale, count, point):
    """Index of the drawn row under `point`, or None.

    None also covers a point inside `area` but past the last drawn
    row — the pad and the tail the bands do not reach. The original
    has the same dead strip: its rows are fields, and the space below
    them belongs to no field at all.
    """
    px, py = point
    if not (area.x <= px < area.right):
        return None
    for i, (top, height) in enumerate(row_bands(area, cfg, scale, count)):
        if top <= py < top + height:
            return i
    return None


