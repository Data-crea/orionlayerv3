"""The colony list — one allocation track per row, drawn two ways.

Its own module rather than the end of `screen.py`, which is at 258
lines against a ~300 guideline (decision 6), and because none of this
is about being a screen. The numbers are in `colonyrows.py`: this
half is handed plain dicts (name, pops, jobs, no_farming, max_pop)
and never touches a struct, so the seam is a data shape rather than a
call graph.

**The bar is an INVENTION.** The original draws three columns of pop
sprites per row, one icon per colonist, squished together when a
colony outgrows its column (`COLDRAW::Do_Colony_Info_Pop_Stuff_For_
Pop_`, coldraw.cpp:282; `Calculate_Squish_Step_`, coldraw.cpp:12).
This draws one bar per row instead, one square per colonist, in three
zones, on a track as long as the engine's population ceiling. Marked
here, in `layout.json` under `list._invention`, in
`v3_projektstatus.md`, and in a smoke check that fails if the marking
disappears.

A FIGURE MODE stood beside this for a day — a sprite per colonist,
the zone colour as a rule beneath — and lost the comparison it was
built for: at a 22 px slot the silhouettes collapse into a stipple
one step down in scale, and the rule ended up carrying the profession
the figures were meant to carry. Deleted rather than switched off,
because a branch nobody renders is a branch nobody checks. The
comparison is in `v3_projektstatus.md`.

**The per-row detail line is an HD EXTENSION.** The original prints
it ONCE, for the selected colony, into the bottom-left scan box at
native (13, 354, 80, 88) — `COLSUM::Draw_Colony_Scan_Info_`
(colsum.cpp:1155) formats `ESTRINGS::E_Strings_(74)` and squeezes it
into that rect, guarded by `_g_colony_n != -1`. The rows themselves
carry a name and nothing else. Putting it on every row makes
comparable what the original could only show one at a time, which is
the same family as the allocation bar: not something MOO2 chose
against, something its screen had no room for. Marked here, in
`layout.json` under `list._hd_extension`, in `doc/v3_fundament.md`,
in `v3_projektstatus.md`, and in a smoke check.

**NOT DRAWN — the original's SLIDER.** The list scrolls (mouse
wheel, see `screen.handle_mousewheel`) and the only thing on screen
saying so is the overflow line. The original draws a real indicator:
`Draw_Bar_Indicator_` (colsum.cpp:747-753) fills a bar at native x
621..626 whose ends are `271 * _first / n` and `271 * (_first + 10)
/ n`, offset 40 — a proportional thumb, so its LENGTH reports how
much of the list the window covers, which a text count does not.
Above and below it sit `_x_fields[1]` and `_x_fields[2]`, the two
step buttons (colsum.cpp:790-800).

Not drawn because nothing has been built for it, not because the
data is missing: `first`, the row count and `list_area` are all
here, and the frame artwork has no hole for it — a slider would be
an artwork decision as well as a code one (decision 3). Recorded
rather than left to be noticed, in the same form as the blockade and
the colony event in `colonyrows`: an omission nobody has written
down is indistinguishable from an omission nobody saw.

**It is a SUBSET, and the omission is deliberate.** That one call
substitutes SEVEN values, in order: planet size, climate, gravity
class, mineral class, `n_pops`, the computed maximum, and population
growth (colsum.cpp:1196-1205). The row draws three — climate,
`n_pops`, `max_pop` — and leaves four: size, gravity, mineral class
and growth.

They are left out because a row is 58 px and the second line is one
short string; seven values there would be a table, not a caption, and
the row exists to carry the allocation track. The four have a home
already, and it is the original's own: `output_panel` is the HD
equivalent of that bottom-left box, and the whole seven belong in it.
If the hover band from the design ever lands, the row keeps its three
and the panel answers for the rest — which is what the original does,
one colony at a time.

TRANSCRIBED here, with its source:
  the zone order     food, industry, research — ECON_FOOD=0,
                     ECON_INDUSTRY=1, ECON_RESEARCH=2
                     (orion2_consts.h:119) and the same left-to-right
                     order the original's columns use
                     (colsum.cpp:318-329)

Everything else transcribed for this screen — the row set, the job
split, the "No Farming" condition, the planet name, the bar length
and the track length — is in `colonyrows.py` and marked there.
"""
import collections

import pygame

from core import palette

from . import colonybuild
from . import colonyscroll
from . import colonytrack
from .colonyrows import POP_LIMIT_CAP
#: THE GEOMETRY LIVES IN `colonytrack`, and is re-exported here.
#: Split out on 6 September 2026 (decision 6); the names stay
#: importable from this module because every caller in the tree and
#: in the checks reaches for them here, and moving a seam is not a
#: reason to move a hundred call sites on the same day.
from .colonytrack import (            # noqa: F401  (re-export)
    Track, Regions, RowBoxes, track_metrics, track_x, row_boxes,
    cell_at_x, drop_targets, drop_band, row_regions, rows_drawn,
    row_bands, row_at)

#: One colour per profession, in ECON order. Palette so a skin or mod
#: can restyle the whole list without touching this file.
ZONE_COLORS = (
    palette.col("colony_summary", "zone_food", (86, 150, 96)),
    palette.col("colony_summary", "zone_industry", (176, 128, 60)),
    palette.col("colony_summary", "zone_research", (86, 122, 190)),
)
#: A free slot's dashed outline, and the faint baseline under the
#: part of the track no colony can reach yet. Two colours because
#: they say two different things; the old single `bar_empty` fill
#: could only say "not filled" for both.
BAR_FREE = palette.col("colony_summary", "bar_free", (72, 88, 120))
#: The scroll arrows. The label colour, because they are the
#: list's own furniture and not a value.
SCROLL_ARROW = palette.col("colony_summary", "label",
                           (150, 168, 200))
BAR_BEYOND = palette.col("colony_summary", "bar_beyond", (34, 42, 60))
ROW_NAME = palette.col("colony_summary", "row_name", (206, 216, 238))
#: The climate/population line under the name. Quieter than the
#: name: it is context for the row, not its identity.
DETAIL_COLOR = palette.col("colony_summary", "row_detail",
                           (132, 148, 180))
NO_FARM_COLOR = palette.col("colony_summary", "no_farming", (150, 120, 110))
#: The "n not shown" line. Deliberately NOT `ROW_NAME`: it is not a
#: colony and must not read as one, and the name-overflow check scans
#: for row-name ink outside the name column.
OVERFLOW_COLOR = palette.col("colony_summary", "row_overflow",
                             (150, 120, 110))
#: The pop move's two marks: the squares a pick would take, and the
#: three drop bands the track reads as while one is held. Both are
#: only ever drawn during a move — see `draw_pick` for why the second
#: one exists at all.
PICK_COLOR = palette.col("colony_summary", "pick_outline",
                         (238, 232, 180))
BAND_COLOR = palette.col("colony_summary", "drop_band",
                         (120, 140, 180))
#: The job markers. GREY on purpose and not a fourth accent: an
#: amber marker in the first mockup read as a fourth job class, which
#: is the one thing a marker must never do. The letter is light
#: enough to carry at one slot's width; `_render_bar` centres it.
MARKER_BG = palette.col("colony_summary", "marker_bg", (86, 92, 104))
MARKER_EDGE = palette.col("colony_summary", "marker_edge",
                          (196, 204, 216))
MARKER_TEXT = palette.col("colony_summary", "marker_text",
                          (232, 238, 246))
#: The identity letter inside a pop cell. One colour for every class:
#: WHICH class is the letter's job, and a second axis of colour here
#: would fight the fill, which is the profession.
CELL_MARK = palette.col("colony_summary", "cell_mark", (16, 18, 24))


# ── Geometry: computed once, drawn by either mode ──────────────────
def render(surface, rows, area, cfg, layout, style, first=0,
           frame_inset=0):
    """Draw the rows into `area`. Everything sized from `cfg`.

    `area` is the `list_area` box in screen coordinates, `cfg` the
    `list` block of layout.json. No geometry constant lives here —
    `POP_LIMIT_CAP` is a population count the engine enforces, not a
    tuned size, and it is the one number the track is measured from.

    `first` is the index of the topmost row to draw. THIS MODULE DOES
    NOT OWN IT and does not clamp it: it is handed plain dicts and an
    integer, the same way it is handed rows, and where the offset
    lives, what bounds it and whether the game agrees with it are
    `colonyselect.Window`'s business (decision 46). Out of range
    simply draws nothing, which is what slicing already does.

    Text goes through `Style.render_text`, which takes a pixel size
    and returns a surface — it can mix two fonts inside one string,
    so height comes from the rendered surface and never from one
    font's metrics (decision 30).
    """
    if not rows:
        _blit_centered(surface, area, cfg.get("empty", ""),
                       layout.font_size(cfg.get("name_font", 20)),
                       ROW_NAME, style)
        return

    scale = layout.scale
    track = track_metrics(area, cfg, scale)
    # No `row_h` here: the loop takes it from `row_bands`, which is
    # the one place the row pitch is computed (decision 5). A local
    # copy of that expression is how the drawing and the hit-test
    # start to disagree.
    pad_x = int(cfg.get("pad_x", 22) * scale)
    name_w = int(cfg.get("name_width", 236) * scale)
    name_px = layout.font_size(cfg.get("name_font", 20))
    small_px = layout.font_size(cfg.get("small_font", 15))

    window = rows[first:]
    for row, (y, row_h) in zip(window,
                               row_bands(area, cfg, scale, len(window))):
        # The name block is handed `name_w`, the TEXT BUDGET, and is
        # unaware of `slack`: it right-aligns, clips and ellipsises
        # against that and nothing else, so the threshold does not
        # move with the resolution. The bar starts past the slack, so
        # the leftover pixels read as a wider gutter — which is the
        # one thing that column can absorb without saying anything
        # untrue.
        _draw_name_block(surface, row, area.x + pad_x, y, name_w, row_h,
                         cfg, name_px, small_px, style, frame_inset)
        _render_bar(surface, row, area, cfg, scale, (y, row_h), track,
                    small_px, style)
        # THE PRODUCING TEXT SITS IN ITS OWN COLUMN when there is a
        # column table, and after the track when there is not. Same
        # call, same width, one place that decides where — a second
        # `colonybuild.draw` for the column case would be the second
        # copy of a position (decision 5).
        _cols = colonytrack.columns(area, cfg)
        if _cols:
            _bx, _bw = _cols["building"]
            colonybuild.draw(surface, row, _bx, y, _bw, row_h, cfg,
                             style, layout)
        elif track.build_w:
            colonybuild.draw(
                surface, row, track_x(area, cfg, scale) + track.width
                + track.build_gap, y, track.build_w, row_h, cfg, style,
                layout)

    # THE ARROWS REPLACE THE OVERFLOW LINE. "N more not shown" was
    # text where the original has two buttons, and it said what was
    # off screen without offering a way to reach it. The arrows say
    # both — a live one IS the statement that there is more — so the
    # sentence goes rather than being drawn beside them.
    colonyscroll.render(surface, area, cfg, scale, SCROLL_ARROW, first,
                        colonytrack.rows_drawn(area, cfg, scale,
                                               max(0, len(rows) - first)),
                        len(rows))


def draw_pick(surface, area, cfg, scale, band, row, job, slots):
    """Outline the squares a held pick would take.

    **The simplest drawing that can be SEEN, which is the whole
    requirement for this phase** — the visualisation is phase 4. It
    is an outline rather than a fill because a fill would sit on the
    same axis as the zone colours and say "these are a fourth
    profession"; an outline is off that axis, the same reasoning the
    free slots' dashes rest on.

    `slots` are icon slots WITHIN ONE JOB's column — that is what
    `Pick.slots()` counts, because the original's icon walk is
    per-column (coldraw.cpp:352) — so the job and the row are needed
    to turn one into a rectangle. It takes them and asks
    `row_boxes`, which is the same call `_render_bar` draws the cells
    with (decision 5).

    **AND THAT IS THE WHOLE OF THE FIX OF 6 SEPTEMBER 2026.** This
    function used to compute `track_x + slot * step` for itself, on
    the assumption that an icon slot is a track slot. It never was:
    job 1's cells start after job 0's, so the outline sat as many
    cells to the left as the earlier jobs held, and the three job
    markers added one more per group. Reported live on Horus IV as
    "one cell to the left" because food is job 0 and the F marker is
    its only error — industry was off six and research ten, and had
    been since this function was written (343d9ba). The docstring
    above already claimed the mark was placed by the function that
    placed the squares; it was not, and a comment cannot enforce
    that. The check does, by reading both back off the render.

    `band` is the (top, height) of the row as `row_bands` gave it.
    """
    if not slots:
        return
    wanted = set(slots)
    for cell_job, index, rect in row_boxes(
            area, cfg, scale, row, band).cells:
        if cell_job == job and index in wanted:
            pygame.draw.rect(surface, PICK_COLOR, rect, 2)


def draw_drop_bands(surface, area, cfg, scale, band, row):
    """The three drop targets, while a pick is held.

    HD EXTENSION — `drop_targets` carries the reason and the shape,
    and this draws exactly the rects it returns. One function, two
    readers (decision 5): the outline a player aims at IS the region
    that will be hit-tested, by construction rather than by two
    copies of an arithmetic agreeing.

    Drawn only during a move, which is what keeps it out of the
    resting row.
    """
    track = track_metrics(area, cfg, scale)
    top, row_h = band
    y = top + (row_h - track.bar_h) // 2
    for _job, rect in drop_targets(area, cfg, scale, row):
        if rect.width:
            pygame.draw.rect(surface, BAND_COLOR, pygame.Rect(
                rect.x, y - 2, rect.width, track.bar_h + 4), 1)


def _draw_overflow(surface, rows, area, cfg, scale, layout, style,
                   first=0):
    """Say how many rows are not on screen, because otherwise nothing
    does.

    **This is the fault it exists for, and it was live.** `render`
    stops at the first row that would cross `area.bottom`, so a list
    longer than the panel simply ended — no ellipsis, no count, no
    scrollbar, and the rows that were drawn were all correct. At
    1920x1080 the panel held NINE rows then — `row_height` was 62 —
    so a twelve-colony empire lost three, and the way it was found
    was somebody noticing a colony they knew they owned was not on a
    screenshot. Every check in the suite was green, because every
    check looked at rows that were drawn. The panel holds ten now
    and the fault is the same one at thirteen colonies.

    **The list scrolls now, and this line counts BOTH directions.**
    It used to say "not a scrollbar and not a step towards one";
    that step has since been taken, and the sentence was rewritten
    rather than left to contradict the code under it. `hidden` is
    the rows above the window plus the rows below it, so the number
    is the honest one at every offset: it is the whole of what the
    panel is not showing, not the tail alone. The layout.json
    template is unchanged — "{count} more not shown" was already
    true of both.

    It counts against the ROW TOTAL and not against the game's ten
    (decision 46's corollary): how many rows fit is derived from
    `list_area` and `row_height` at this resolution and is ten only
    by arithmetic.

    Drawn in the strip the bands could not use, so it cannot cover a
    row: the bands stop when the next one would cross `area.bottom`,
    which leaves at least `row_height` minus one pixel of unused
    height whenever anything was dropped at all. At an offset with a
    full window and nothing below, that strip is where the count of
    the rows ABOVE goes.
    """
    template = cfg.get("overflow", "")
    if not template:
        return
    bands = row_bands(area, cfg, scale, max(0, len(rows) - first))
    # Above plus below, in one subtraction: `first` rows are off the
    # top and `len(rows) - first - len(bands)` are off the bottom.
    hidden = len(rows) - len(bands)
    if hidden <= 0:
        return
    text = template.replace("{count}", str(hidden))
    surf = style.render_text(
        text, layout.font_size(cfg.get("small_font", 15)),
        OVERFLOW_COLOR[:3])
    top = bands[-1][0] + bands[-1][1] if bands else area.y
    # Centred in what is left, and clamped so a panel too short for
    # even one row still shows the line rather than drawing it off
    # the bottom edge.
    y = min(top + max(0, (area.bottom - top - surf.get_height()) // 2),
            area.bottom - surf.get_height())
    surface.blit(surf, (area.x + int(cfg.get("pad_x", 22) * scale),
                        max(area.y, y)))


def _draw_name_block(surface, row, x, y, name_w, row_h, cfg,
                     name_px, small_px, style, frame_inset=0):
    """The colony name, and under it climate and population.

    **HD EXTENSION: the original LEFT-aligns this name.** It draws it
    with `BILL::Squeeze_Formatted_Paragraph_Centered_(0x0C, y_pos,
    paragraph_type, 0x17, buffer, 0)` (colsum.cpp:582), and that
    wrapper's name is about the VERTICAL axis only — it forwards to
    `_Squeeze_Print_Paragraph_(x, y + height/2, …, center_y=true)`
    (bill.cpp:252), where `center_y` does nothing but
    `y = y - height/2` (bill.cpp:205). The sixth parameter is
    `color_or_alignment`, and for a formatted paragraph it goes
    straight into `Print_Formatted_Paragraph_` as the JUSTIFY
    argument (bill.cpp:210). colsum.cpp passes **0**, which is
    JUSTIFY_LEFT.

    The alignment below is therefore ours, and it is KEPT: right
    alignment is what makes a 236 px name column affordable, because
    overflow grows LEFT into `pad_x` where nothing is drawn instead
    of rightward onto the track, and that trade is what bought the
    building column. The marking does not undo the trade. It exists
    because `Centered_` is a trap of a function name — a later reader
    who checks the call site and sees a name agreeing with the word
    will file this as transcribed. Marked here, in
    `doc/v3_fundament.md` (45), and in a smoke check.

    RIGHT-ALIGNED to the column's right edge. Left-aligned, a name
    too long for the column grew RIGHTWARD onto the track's first
    slots — and the squares draw afterwards, so the data won and the
    name was the casualty. Right-aligned it grows LEFT into `pad_x`,
    where nothing is drawn, which turns the clip from the mechanism
    into a fallback. `name_gap` comes out of the column, so the name
    ends at `name_width - name_gap` and grows left across `pad_x`:
    236 - 14 + 22 = 244 px of room, against a realistic maximum of
    230 and a structural one of 336. The clip stays, because that
    room is not infinite either and a column narrowed later must fail
    towards the empty side. It also puts both lines against the bar,
    so the eye crosses one gap rather than a ragged one per row.

    The detail line is `cfg["detail"]`, substituted by REPLACE and
    not `str.format` (decision 37): a stray brace in a translated
    string cannot raise inside the render path.
    """
    # The gutter is taken out of the column, not out of the track:
    # right-aligned to `name_w` exactly, the name ends on the pixel
    # the first square starts on and the two read as a collision.
    right = x + name_w - int(cfg.get("name_gap", 14) * (name_px / 21.0))
    # Everything from the left edge of `list_area` to `right` is
    # available: right-alignment sends overflow into `pad_x`, where
    # nothing is drawn. Only a name that outruns THAT is ellipsised.
    room = right - (x - _pad_left(x, cfg, name_px, frame_inset))
    lines = [(style.render_text(
        _fit(row["name"], style, name_px, room, cfg), name_px, ROW_NAME), 0)]
    detail = _detail_text(row, cfg)
    if detail:
        lines.append((style.render_text(detail, small_px, DETAIL_COLOR),
                      int(cfg.get("detail_gap", 2) * (small_px / 15.0))))

    block_h = sum(s.get_height() + gap for s, gap in lines)
    top = y + (row_h - block_h) // 2
    # Clipped to the column PLUS its left padding — the direction
    # overflow is now allowed to grow. Clipping to the column alone
    # would cut the very overflow this alignment exists to absorb.
    prev_clip = surface.get_clip()
    # Left bound is the same one `room` was computed against, so the
    # clip agrees with the fit instead of letting an unfitted string
    # through to the rim. It used to start at x = 0.
    _left = x - _pad_left(x, cfg, name_px, frame_inset)
    surface.set_clip(pygame.Rect(_left, y, max(1, right - _left), row_h))
    for surf, gap in lines:
        top += gap
        surface.blit(surf, (right - surf.get_width(), top))
        top += surf.get_height()
    surface.set_clip(prev_clip)


def _pad_left(x, cfg, name_px, frame_inset=0):
    """How far left of the column the name may grow.

    `pad_x`, LESS the screen's `frame_inset` — because `pad_x` is not
    empty all the way to the box edge. `list_area`'s outer few
    reference px are under the frame's metal rim (see
    `_frame_bleed_note`, and `_frame_inset_note` for the
    measurement), so a name allowed to run to the box edge runs under
    the frame. It did: one pixel of a fifteen-character name at
    1600x900, which the tree-wide Class A check found and nothing
    else could — the name has to be long enough to use the whole
    gutter before any of it reaches the rim.

    The subtraction is clamped at 0 so a screen declaring an inset
    wider than its own padding loses the overflow rather than
    inverting it.
    """
    return max(0, int((cfg.get("pad_x", 22) - frame_inset)
                      * (name_px / 21.0)))


def _fit(text, style, px, room, cfg):
    """`text`, ellipsised only if it outruns even the padding.

    The reservation is the REALISTIC range, not the structural
    maximum. A star name is str15 and a player can type all fifteen
    (namestar.cpp:262), which renders 336 px — but the widest of the
    54 stars in the reference galaxy is 124 px, and a realistic
    15-character name is 190 to 230. Sizing the column for the
    pathological case spends 100 px of the shared budget on a name
    nobody types; sizing it for the realistic one and ellipsising the
    rest spends nothing and degrades visibly in the one case it
    cannot hold. Right alignment is what makes that trade available:
    overflow grows left into `pad_x`, not right onto the track.
    """
    if style.render_text(text, px, ROW_NAME).get_width() <= room:
        return text
    dots = cfg.get("ellipsis", "…")
    cut = text
    while cut and style.render_text(
            cut + dots, px, ROW_NAME).get_width() > room:
        cut = cut[:-1]
    return (cut + dots) if cut else text


def _detail_text(row, cfg):
    """'Terran 12/14' — climate name plus pops over the maximum.

    HD EXTENSION: per row, where the original has it once for the
    selected colony (colsum.cpp:1155). See the module docstring.
    """
    template = cfg.get("detail", "")
    if not template:
        return ""
    climates = cfg.get("climates") or ()
    index = row.get("climate", -1)
    name = climates[index] if 0 <= index < len(climates) else "?"
    for key, value in (("{climate}", name),
                       ("{pops}", str(row["pops"])),
                       ("{max_pop}", str(row["max_pop"]))):
        template = template.replace(key, value)
    return template


def _render_bar(surface, row, area, cfg, scale, band, track, text_px,
                style):
    """One row's run: three markers, their cells, then the growth.

        F [food cells] W [worker cells] S [scientist cells]  gap  · · ·

    Every box comes from `colonytrack.row_boxes`, which is also what
    a click is tested against — one function, two readers
    (decision 5). Nothing here computes a position.

      markers      grey, light border, the job's letter. ALWAYS all
                   three, whether or not the job holds pops. HD
                   EXTENSION; `row_boxes` carries the reason.
      cells        one per pop, in its job's colour, with an identity
                   letter where the pop is not one of the player's
                   own — see `_cell_mark`.
      growth       `max_pop` less the pops, dashed, after the gap.
                   They belong to the COLONY and not to any job,
                   which is why they are past all three groups
                   instead of trailing the last one.
      beyond       the faint line for track the colony cannot reach
                   yet. NOT padding, and not a dim square either: a
                   square there would be neither filled nor free.

    Drawn back to front — beyond, growth, markers, cells — because a
    later draw wins where boxes touch. Not hypothetical: the "No
    Farming" label was painted over by the worker squares once, with
    every number correct and nothing on screen.
    """
    boxes = colonytrack.row_boxes(area, cfg, scale, row, band)

    if boxes.beyond is not None:
        thick = max(1, track.bar_h // 16)
        pygame.draw.rect(surface, BAR_BEYOND, pygame.Rect(
            boxes.beyond.x, boxes.beyond.y + track.bar_h - thick,
            boxes.beyond.width, thick))

    for rect in boxes.growth:
        _dashed_rect(surface, BAR_FREE,
                     pygame.Rect(rect.x, rect.y + 1, track.unit,
                                 track.bar_h - 2),
                     max(1, track.unit // 4))

    letters = cfg.get("marker_letters", ["F", "W", "S"])
    for job, rect in boxes.markers:
        surface.fill(MARKER_BG[:3], rect)
        pygame.draw.rect(surface, MARKER_EDGE[:3], rect, 1)
        if job < len(letters):
            _blit_centered(surface, rect, str(letters[job]), text_px,
                           MARKER_TEXT, style)

    cells = row.get("cells")
    for job, index, rect in boxes.cells:
        pygame.draw.rect(surface, ZONE_COLORS[job], rect)
        mark = _cell_mark(cfg, cells, job, index)
        if mark:
            _blit_centered(surface, rect, mark, text_px, CELL_MARK, style)

    if row["no_farming"]:
        _draw_no_farming(surface, boxes, track, cfg, text_px, style)


def _cell_mark(cfg, cells, job, index):
    """The identity letter for one cell, or "" for the common case.

    **HD EXTENSION, and the reason is a sprite the original cannot
    reuse.** The original draws a pop as `race * 13 + job * 2 + 1`
    (colony_main.cpp:445) — profession AND race in one figure —
    except for the three classes that get one sprite each: a native
    is entry 0xAA whatever it does, an android 0xA9, a conquered pop
    a static race portrait (colony.cpp:1278). In the original the
    profession is carried by WHICH COLUMN the sprite stands in. The
    HD row has one track and no columns, so a cell has to carry both:
    the FILL carries the profession and the letter carries the
    identity, and the letter may not disturb the fill.

    **The player's own pops carry no letter.** Over ninety per cent
    of cells are that case and they have to stay quiet, or scanning
    twenty rows dies.

    Verification, split and stated (decision 23): **N for a native is
    confirmed** against `fixture_natives_3502.5.GAM` by three
    independent sources — the data, the original's own picture and
    the label the game prints. **A for an android and C for a
    conquered pop are UNVERIFIED**: no save this project holds
    contains either, so those two letters rest on the source alone.

    **A fifth class is deliberately NOT marked and it is a known
    gap.** A pop of another player's race with the conquered bit
    CLEAR — an assimilated one, which `invasion.cpp:672-676` produces
    when the conquering player is Assimilative — draws here exactly
    like one of the player's own, and the original draws it with its
    own race's figure. The mark it wants is a race initial, which
    collides with the marker alphabet (Sakkra begins with the same
    letter as Scientist), and no fixture contains the case to judge
    that collision on. Marking it from a guessed mapping is the thing
    a picture of the wrong thing is made of; it is recorded in
    `v3_projektstatus.md` instead.
    """
    if not cells or job >= len(cells) or index >= len(cells[job]):
        return ""
    marks = cfg.get("cell_marks", {})
    return marks.get(cells[job][index], "")


def _draw_no_farming(surface, boxes, track, cfg, text_px, style):
    """The label, in the tail column or under the track.

    BELOW is the cheaper of the two, and not by a little: the tail
    column costs 150 reference px of the ONE horizontal budget every
    row shares, while the band under the bar is 14 px that
    `row_height` already spends and nothing occupies. At a 42-slot
    track that is the difference between a 19 px slot and a 22 px one
    — and 14 px against 18 px once a building column is added, which
    is the decision this placement exists for. See
    `_horizontal_budget` in layout.json.

    What has to hold either way: the label must not be drawn where
    something else draws later. It was once put at the bar's left
    edge and the worker squares painted straight over it — every
    number right, nothing on screen. Below the bar is outside the
    track's own band by construction (squares occupy `y+1` to
    `y+bar_h-1`), so a full 42-slot row cannot reach it. That is a
    property of the geometry, not of the data, which is why it is
    also a smoke check rather than a look at one screenshot.
    """
    label = cfg.get("no_farming", "")
    if not label:
        return
    surf = style.render_text(label, text_px, NO_FARM_COLOR)
    x = boxes.markers[0][1].x
    y = boxes.markers[0][1].y
    # `y` is the BAR's top; the row extends half the spare height
    # above and below it. Bottom-aligned in the band that leaves, so
    # any rounding slack sits between the label and the bar, where it
    # reads as spacing, rather than under the label, where it reads
    # as a taller row.
    row_bottom = y + track.bar_h + (track.row_h - track.bar_h) // 2
    surface.blit(surf, (x, row_bottom - surf.get_height()))


def _dashed_rect(surface, color, rect, dash):
    """A one-pixel outline drawn as dashes — pygame has no dash mode.

    A free slot must read as a slot that is NOT filled. Any solid
    treatment, however dim, is a second fill and sits on the same
    axis as the zone colours; a broken line is off that axis, which
    is why this is an outline and not a darker square. Dashes start
    at each edge's start, so a corner is always inked and the square
    keeps its shape at small `unit`.
    """
    for x0 in range(rect.left, rect.right, dash * 2):
        w = min(dash, rect.right - x0)
        surface.fill(color, pygame.Rect(x0, rect.top, w, 1))
        surface.fill(color, pygame.Rect(x0, rect.bottom - 1, w, 1))
    for y0 in range(rect.top, rect.bottom, dash * 2):
        hgt = min(dash, rect.bottom - y0)
        surface.fill(color, pygame.Rect(rect.left, y0, 1, hgt))
        surface.fill(color, pygame.Rect(rect.right - 1, y0, 1, hgt))


def _blit_centered(surface, area, text, px, color, style):
    if not text:
        return
    surf = style.render_text(text, px, color)
    surface.blit(surf, (area.x + (area.w - surf.get_width()) // 2,
                        area.y + (area.h - surf.get_height()) // 2))
