"""The row's geometry: where every box in a colony row is.

Split out of `colonylist` on 6 September 2026, when that file stood
at exactly 300 code lines against the ~300 guideline (decision 6) and
the job markers had to go somewhere. The seam is real rather than a
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

from .colonyrows import POP_LIMIT_CAP

#: One marker per job, always, in ECON order. **HD EXTENSION** — see
#: `row_boxes`, which is where the reason is written down.
MARKER_COUNT = 3
#: How wide a marker is, in slots. One, decided at the real render at
#: 1920x1080 and 3840x2160 rather than from the mockup: a letter is
#: legible in a single slot at both, and two would cost six slots of
#: track in every row for nothing. `layout.json` may override it.
MARKER_SLOTS_DEFAULT = 1



#: `unit` is one slot's ink, `gap` the space after it, `step` the two
#: together — the pitch from one slot to the next. `width` is the
#: whole POP_LIMIT_CAP-slot track. A sprite may be at most `unit`
#: wide, which is the step minus the gap: ink that ate its gap would
#: touch its neighbour and the count would stop being legible.
#:
#: `slack` is what `list_area` has left after the building column,
#: the two `pad_x` and the whole track have been paid for — the
#: pixels the slot's floor division drops. It is added to the name
#: column's DRAWN width and to nothing else, so the row ends flush at
#: every resolution. See `track_metrics`.
Track = collections.namedtuple(
    "Track",
    "unit gap step width slack growth_gap bar_h row_h build_w build_gap")

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


def track_metrics(area, cfg, scale):
    """The one geometry both modes measure from.

    The slot is measured from POP_LIMIT_CAP and from nothing on
    screen, which is what makes counting mean anything — see the
    constant in `colonyrows.py`. `tail_width` is reserved BESIDE the
    track, not taken out of it: a full-length track ends where the
    panel does, and "No Farming" needs a column no slot reaches.

    **`slack`, and why the name column gets it.** `unit` is a floor
    division, so the six columns almost never spend `list_area`
    exactly: at scale 1.0 the shipped values divide evenly, and at
    every fractional scale the six independent `int()` calls each
    drop a fraction. Those pixels used to land at the right edge as
    dead air — 30 px at 1280x720, 15 at 2560x1440 — where nothing
    claimed them and the row simply stopped short of the panel.

    They go to the name column's DRAWN width instead, which is the
    only column that can take a variable amount without lying: the
    slot must stay `POP_LIMIT_CAP`-derived or counting stops meaning
    anything, `building_width` is a hard transcription, and `pad_x`
    and `square_gap` are the fixed costs.

    It is drawn width and NOT text budget. The name still clips and
    ellipsises at `name_width * scale`, so the threshold is the same
    244 reference px everywhere; the slack becomes gutter between the
    name and the first slot. Letting it into the text budget would
    make the ellipsis resolution-dependent — 244 ref px at 1080p
    against 288 at 720p, so the same name cuts on one monitor and not
    on another. See `_draw_name_block` and `_name_width_note`.
    """
    gap = max(1, int(cfg.get("square_gap", 2) * scale))
    pad_x = int(cfg.get("pad_x", 22) * scale)
    tail_w = int(cfg.get("tail_width", 0) * scale)
    build_gap = int(cfg.get("building_gap", 16) * scale)
    growth_gap = int(cfg.get("growth_gap", 18) * scale)
    cols = columns(area, cfg)
    name_w = cols["name"][1] - 2 * pad_x if cols else int(
        cfg.get("name_width", 236) * scale)
    build_w = cols["building"][1] if cols else int(
        cfg.get("building_width", 0) * scale)
    if build_w and not cols:
        build_w += build_gap
    bar_space = area.w - name_w - tail_w - build_w - 2 * pad_x
    # THE TRACK HOLDS POP_LIMIT_CAP SLOTS PLUS THREE MARKERS PLUS THE
    # GAP, and that is the price of the markers stated in arithmetic
    # rather than in prose: a row can hold 42 pops, every one of them
    # is a slot, the three job markers are three more, and the growth
    # boxes sit past a fixed gap. The slot therefore shrinks by about
    # a fifteenth against the pre-marker row. What does NOT change is
    # that one slot is the same width in every row, which is the
    # property the whole track is measured from — see the note in
    # `colonyrows.POP_LIMIT_CAP`.
    slots = POP_LIMIT_CAP + MARKER_COUNT
    unit = max(2, (bar_space - growth_gap - (slots - 1) * gap) // slots)
    width = slots * unit + (slots - 1) * gap + growth_gap
    # Clamped at 0: `unit` has a floor of 2, so a `list_area` too
    # narrow for the columns configured would compute a NEGATIVE
    # remainder, and adding that to the name column would drag the
    # track left over the names. The row then overruns the panel on
    # the right, which is the visible failure and the honest one.
    slack = max(0, area.w - (name_w + tail_w + build_w
                             + 2 * pad_x + width))
    return Track(unit=unit, gap=gap, step=unit + gap,
                 width=width, slack=slack, growth_gap=growth_gap,
                 # NO DEFAULT, deliberately, for these three and for
                 # `pad_y` in `row_bands`: they carry the ten-row
                 # arithmetic, and the number that used to stand here
                 # was 60, which `layout.json._row_height_note`
                 # records as REJECTED — 10 x 60 = 600 leaves 5 px
                 # and clamps the "{count} more not shown" line back
                 # over the last row it exists to account for. A
                 # missing key must raise, not silently draw nine
                 # rows: an absence shaped like a result is the one
                 # thing the fundament refuses.
                 bar_h=int(cfg["bar_height"] * scale),
                 row_h=int(cfg["row_height"] * scale),
                 build_w=int(cfg.get("building_width", 0) * scale),
                 build_gap=build_gap)


#: The key `cfg` carries the column table under. The screen merges
#: `layout_reference.list_columns` into its `list` block on load, so
#: the table travels with every other row number and there is no
#: module state to leak between one caller and the next — which a
#: global would do the moment one check rendered the real screen and
#: the next used a synthetic fixture.
COLUMNS_KEY = "columns"


def columns(area, cfg):
    """{key: (x, width)} in SCREEN px, tiling `area` exactly, or {}.

    Empty when `cfg` carries no table, and the single-track
    arithmetic runs then — which is what the synthetic fixtures in
    the checks exercise, and what the row was before Stage 4.

    The last column takes what integer division left, so the row can
    never end short of the panel — the same rule
    `colonyheader.plate_rects` uses for the headings above, which is
    why the two line up at every resolution without either knowing
    about the other.
    """
    table = cfg.get(COLUMNS_KEY) or ()
    if not table:
        return {}
    total = sum(w for _k, w in table)
    out, x = {}, area.x
    for i, (key, ref_w) in enumerate(table):
        w = (area.right - x if i == len(table) - 1
             else round(area.w * ref_w / total))
        out[key] = (x, w)
        x += w
    return out


#: The three job columns, in ECON order, as they are keyed above.
JOB_KEYS = ("farmers", "workers", "scientists")


def track_x(area, cfg, scale):
    """Where the 42-slot track starts on screen.

    Decision 5, one scroll offset further in than `row_bands`: the
    drawing and the two hit tests below have to agree about the
    track's left edge, and the expression is `pad_x + name_width +
    slack` — the slack included, because those are the pixels the six
    floor divisions dropped and `track_metrics` gives them to the
    name column's DRAWN width. A hit test that forgot the slack would
    be one gutter to the left of the squares at every fractional
    scale and exactly right at 1.0, which is the resolution anybody
    checks.
    """
    track = track_metrics(area, cfg, scale)
    return (area.x + int(cfg.get("pad_x", 22) * scale)
            + int(cfg.get("name_width", 236) * scale) + track.slack)


def row_regions(row):
    """The three job groups of one row, in CELL counts.

    `runs` is (zone, first_cell_index, count) for the jobs that hold
    pops, `spans` the same for all three including the empty ones,
    `filled` the pops drawn and `reach` how many the colony could
    hold. **None of these are slots any more** — the markers moved
    the slots apart, so `row_boxes` is what turns a cell index into
    a rectangle and this counts.

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
#: `markers` and `cells` are what is drawn; `targets` is what a click
#: is tested against, and it is built from the same two. `growth` are
#: the dashed capacity boxes after the gap, `beyond` the faint line
#: for the track a colony cannot reach yet, or None.
RowBoxes = collections.namedtuple(
    "RowBoxes", "markers cells targets growth beyond run_right")


def row_boxes(area, cfg, scale, row, band=None):
    """THE row geometry. Everything that draws or hits calls this.

    `band` is the (top, height) `row_bands` gave for this row; without
    it the rects carry x and width only and their y is 0, which is
    what a hit test wants and what the layout checks read.

    **THREE JOB MARKERS, ALWAYS — HD EXTENSION.** Every row carries a
    marker per job in ECON order, each introducing its own cells, the
    two forming one unbroken run:

        F [food cells] W [worker cells] S [scientist cells]   gap  · · ·

    The original does not have them and does not need them: it draws
    three FIXED columns under three headings — FARMERS, WORKERS,
    SCIENTISTS (colsum.cpp:1006-1024 for the columns) — so an empty
    job is a visible empty column. **A row without columns cannot
    carry a heading.** Before the markers, a colony with everyone
    farming drew a run of squares and then nothing, and nothing on
    screen said the other two jobs existed; the drop placeholder
    appeared only once a pop was held, which is one click too late.
    Marked here, in `layout.json` under `list._hd_extension_markers`,
    in `v3_projektstatus.md`, and in a check.

    **FLUSH, NO GAPS INSIDE THE RUN.** A marker whose job holds
    nothing is followed immediately by the next marker. Short
    colonies make short rows, so the length of a row goes on meaning
    something.

    **AND IT COLLAPSES THE EMPTY-GROUP CASE.** `drop_targets` used to
    invent a placeholder for a job with no cells, positioned by a
    seam rule with two bounds. No job is ever empty now — the marker
    is that placeholder, made permanent and visible — so the rule is
    gone rather than bypassed. One layout path.

    **The growth boxes belong to the COLONY, not to a job**, so they
    follow all three groups after a fixed gap (`list.growth_gap`,
    a layout value and not a side effect of some other number).
    """
    track = track_metrics(area, cfg, scale)
    origin = track_x(area, cfg, scale)
    marker_slots = int(cfg.get("marker_slots", MARKER_SLOTS_DEFAULT))
    top, height = band if band else (0, 0)
    y = top + (height - track.bar_h) // 2 if band else 0
    h = track.bar_h if band else 0
    cols = columns(area, cfg)
    if cols:
        return _column_boxes(cols, cfg, scale, row, y, h, track,
                             marker_slots)

    def box(slot, count):
        return pygame.Rect(origin + slot * track.step, y,
                           count * track.step - track.gap, h)

    regions = row_regions(row)
    markers, cells, targets = [], [], []
    slot = 0
    for job, (_start, count) in enumerate(regions.spans):
        m = box(slot, marker_slots)
        markers.append((job, m))
        first_cell = slot + marker_slots
        for k in range(count):
            cells.append((job, k, box(first_cell + k, 1)))
        # the target is marker AND cells, one contiguous rect
        targets.append((job, pygame.Rect(
            m.x, y, (marker_slots + count) * track.step - track.gap, h)))
        slot = first_cell + count

    run_right = origin + slot * track.step - track.gap
    grow_n = max(0, regions.reach - regions.filled)
    gx = run_right + track.growth_gap
    growth = [pygame.Rect(gx + i * track.step, y,
                          track.unit, h) for i in range(grow_n)]
    beyond_x = gx + grow_n * track.step
    right = origin + track.width
    beyond = (pygame.Rect(beyond_x, y, right - beyond_x, h)
              if band and beyond_x < right else None)
    return RowBoxes(tuple(markers), tuple(cells), tuple(targets),
                    tuple(growth), beyond, run_right)


def _column_boxes(cols, cfg, scale, row, y, h, track, marker_slots):
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

    The markers keep their place at the head of each column
    (`row_boxes`' HD EXTENSION). Their original reason — a row without
    columns cannot carry a heading — is answered by the headings above
    as of Stage 4, and whether they stay is Stage 5's call; they are
    not removed here because a marking is re-targeted in the commit
    that deletes what it marks, not before.

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
    from core import zoomtables
    from . import colonyfigures
    from . import colonyicons
    regions = row_regions(row)
    markers, cells, targets = [], [], []
    for job, key in enumerate(JOB_KEYS):
        cx, cw = cols[key]
        n_left, n_right = colonyicons.COLUMNS[job]
        count = regions.spans[job][1]
        # THE MARKER COMES OUT OF THE COLUMN, NOT ON TOP OF IT. A
        # square the height of the bar, at the column's left edge;
        # the cells then get what is left, and the scale below is
        # computed from THAT so the last cell lands inside the
        # column instead of one marker's width past it.
        # `track.bar_h` AND NOT `h`: the caller may pass no band, in
        # which case `h` is 0 and the rects carry x and width only —
        # which is what `cell_at_x` asks for. A marker width taken
        # from `h` was 2 px there and a full square when drawn, so
        # every cell in the row sat at a different x in the hit test
        # than on screen. Caught by the check that samples each drawn
        # cell's own pixels, which is the one that exists because
        # "they call the same function" is not the same as "they get
        # the same answer".
        m_w = max(2, min(track.bar_h, cw // 8))
        m = pygame.Rect(cx, y, m_w, h)
        markers.append((job, m))
        start = cx + m_w + track.gap
        room = max(1, cx + cw - start)
        # THE FACTOR IS THE SPRITE STEP, NOT THE COLUMN RATIO.
        # `zoomtables.FIGURE_STEP` (decision 26) is the integer 2/3/4
        # a 28 px native figure is drawn at, and the stacking decision
        # is that HD's extra width goes into the column RESERVATION
        # and never into figure spacing. Scaling the pitch by the
        # column ratio instead — 342 : 125, about 2.7 at 1080p —
        # spends that reservation on spacing, and every cell and every
        # drop target would move again the day Stage 3 draws sprites
        # at the step. Corrected 7 September 2026; it was the ratio
        # for one stop.
        # ONE HOME for the step: `colonyfigures.figure_step` also
        # loads the sprites at it, and a pitch and a sprite that
        # disagree are a picture nothing would report.
        step = colonyfigures.figure_step(scale)
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
        if count and start + count * pitch > cx + cw:
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
    return RowBoxes(tuple(markers), tuple(cells), tuple(targets),
                    (), None, cols[JOB_KEYS[-1]][0] + cols[JOB_KEYS[-1]][1])


def drop_targets(area, cfg, scale, row):
    """(job, Rect) per job — marker plus that job's cells.

    One rect per job and never two boxes that look alike and behave
    differently, which is the trap decision 5 is about: the marker is
    part of its group's target, so a click on the letter is a drop on
    that job.
    """
    return row_boxes(area, cfg, scale, row).targets


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
    `colonyrows` builds the row that way. A marker is not a cell and
    answers None: there is nothing to pick up on it.
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
    # No defaults here either — see `track_metrics`.
    row_h = int(cfg["row_height"] * scale)
    y = area.y + int(cfg["pad_y"] * scale)
    bands = []
    for _ in range(count):
        if y + row_h > area.bottom:
            break
        bands.append((y, row_h))
        y += row_h
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


