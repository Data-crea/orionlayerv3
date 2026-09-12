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

**THE SLIDER IS DRAWN — since 9 September 2026**, and the marker
that stood here saying it was not is gone with it.
`COLSUM::Draw_Bar_Indicator_` (colsum.cpp:747-771) fills a bar at
native x 621..626 whose ends are `271 * _first / n + 40` and
`271 * (_first + 10) / n + 40` — a proportional thumb, so its LENGTH
reports how much of the list the window covers, which a text count
does not. Above and below it sit `_x_fields[1]` and `_x_fields[2]`,
the two step buttons (colsum.cpp:790-800). It is
`colonyscroll.slider`, and the track it runs in is
`colonyscroll.track` — one channel where this column used to draw ten
stacked plates.

WHAT IS STILL NOT DRAWN, and stays a recorded omission at three
homes: the per-row BUY button the original adds at native x 599
(`_list_buy_fields`, colsum.cpp:302). See `layout.json`'s
`list._buy_note`.

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

import pygame

from core import palette

from core import textfit
from core import zoomtables

from . import colonybuild
from . import colonyfigures
from . import colonyscroll
from . import colonytrack
from .colonyrows import POP_LIMIT_CAP
#: THE GEOMETRY LIVES IN `colonytrack`, and is re-exported here.
#: Split out on 6 September 2026 (decision 6); the names stay
#: importable from this module because every caller in the tree and
#: in the checks reaches for them here, and moving a seam is not a
#: reason to move a hundred call sites on the same day.
from .colonytrack import (            # noqa: F401  (re-export)
    RowBoxes, track_metrics, figure_step,
    row_boxes, cell_at_x, drop_targets, drop_band,
    row_regions, rows_drawn, row_bands, row_at)

#: One colour per profession, in ECON order. Palette so a skin or mod
#: can restyle the whole list without touching this file.
ZONE_COLORS = (
    palette.col("colony_summary", "zone_food", (86, 150, 96)),
    palette.col("colony_summary", "zone_industry", (176, 128, 60)),
    palette.col("colony_summary", "zone_research", (86, 122, 190)),
)
#: The scroll arrows. The label colour, because they are the
#: list's own furniture and not a value.
SCROLL_ARROW = palette.col("colony_summary", "label",
                           (150, 168, 200))
#: The SCANNED colony's name — bright. See `ROW_NAME_DIM`.
ROW_NAME = palette.col("colony_summary", "row_name", (206, 216, 238))

#: Every OTHER colony's name — dimmed. **TRANSCRIBED, and the driver
#: is the scanned colony rather than a hover of ours.**
#: `Draw_Colony_Summary_For_Colony_` calls
#: `COLONY::Set_Colony_Font_To_Blue_(2, colony_idx ==
#: COLONY::_g_colony_n)` (colsum.cpp:554), which picks
#: `_font_bright_color_array` when that flag is set and
#: `_font_color_array` when it is not (colony.cpp:533-546).
#:
#: `_g_colony_n` IS the state that fills the description panel
#: (`Draw_Colony_Scan_Info_`, colsum.cpp:1155), so the two read one
#: source here as well — `colonyselect.Selection.colony`, whose
#: `row()` the panel already takes. A smoke check asserts they cannot
#: disagree.
#:
#: A COLOUR AND NOTHING ELSE: no rectangle and no frame. The only
#: `Fill_`/`Line_` calls in `colsum.cpp` are the scroll thumb
#: (:759-765).
#:
#: The two values and why the RELATIONSHIP is transcribed rather than
#: the RGB are in `colors.json` under `_row_name_note`.
ROW_NAME_DIM = palette.col("colony_summary", "row_name_dim",
                           (147, 154, 169))
#: The climate/population line under the name. Quieter than the
#: name: it is context for the row, not its identity.
DETAIL_COLOR = palette.col("colony_summary", "row_detail",
                           (132, 148, 180))
NO_FARM_COLOR = palette.col("colony_summary", "no_farming", (150, 120, 110))
#: The cell plate's line. The same key the header plates use, because
#: they are one plate in two rows of the same table — see
#: `colonyheader.render` and decision 51.
PLATE_COLOR = palette.col("colony_summary", "plate_outline", (55, 65, 85))

#: **THE LOWER BOUND OF THE NAME COLUMN, and the editor REPORTS it
#: rather than clamping.** Two sources, both required, and neither
#: is a character count on its own:
#:
#:   the TABLE — `STARNAME.LBX` entry 1, 829 records of `char[15]`
#:   (`MAPGEN::Get_Star_Name_`, mapgen.cpp:1371-1386, count at :34,
#:   loaded at :1428). Longest by rendering is "Commoriom IV";
#:
#:   what a PLAYER can type — `NAMESTAR::Do_Change_Star_Name_`
#:   (namestar.cpp:236-274) passes `sizeof(_star[].name)` = 15 as the
#:   buffer AND caps the field's pixel width at
#:   `min(Max_Pixel_Width_Star_Name_Can_Be_,
#:   Get_String_Width_("WWWWWWW"), 0xCD)`. So the hard bound is SEVEN
#:   W's wide, not fourteen arbitrary characters.
#:
#: **THE CAP IS MEASURED IN FONTS.LBX STYLE 3, WHICH THIS PROJECT
#: CANNOT READ** — the same gap the "No Farming" size sits in (see
#: `NO_FARM_FONT_REF`), and the font extractor is owed twice now. So
#: the translation into this font is close and not exact, and that is
#: exactly why the editor reports the number and never clamps on it.
NAME_BOUND_STAR = "WWWWWWW IV"
NAME_BOUND_DETAIL = "Radiated 42/100"
NAME_BOUND_NOTE = "namestar.cpp:246-256, in FONTS.LBX style 3"
#: The original's own numbers for the "No Farming" label, in NATIVE
#: px, kept as a proportion of the row rather than as HD pixels
#: (fundament, Evidence: a percentage carries across a resolution
#: change and a pixel count does not).
#:
#:   31   the row pitch, `top_y = 31*i + 34` (colsum.cpp:311)
#:    5   `top_y + 5`, the label's y (coldraw.cpp:320)
#:   28   the squeeze box's height, same call
NATIVE_ROW_PITCH = 31
NATIVE_LABEL_Y_OFFSET = 5
NATIVE_LABEL_BOX_H = 28
#: The cap height of the label's capital "N", MEASURED off
#: `colony_summary_native_split.png`. See `NO_FARM_FONT_REF`.
NATIVE_LABEL_CAP = 10
#: **MEASURED, SINGLE SOURCE — and the source is a picture.** The
#: original's size is font style 3, whose pixel height lives in the
#: player's own FONTS.LBX and is in no source file this project can
#: read. The capital "N" of "No Farming" measures 10 px of cap height
#: on `orionlayer-fixtures/evidence/colony_summary_native_split.png`
#: (1:1 native, row pitch 31 confirmed on it).
#:
#: 10 of a 31 px row is 18.4 of this screen's **57 reference px band**
#: — the band is the list window divided by `list.row_count` since
#: 8 September 2026, not a tuned `row_height` — and Aldrich's cap is
#: 0.70 of its nominal size (measured by rendering, decision 30), so
#: 18.4 / 0.70 = 26.3 -> **26**, whose cap renders 18 against the
#: wanted 18.4. 25 renders 18 as well and 26 is the larger of the
#: two, which is the side to err on for a label that has to read.
#:
#: **RE-DERIVED 12 September 2026, and the arithmetic is the one that
#: matters rather than the number.** It was 28 against a 63 px band;
#: the static frame's list hole is shorter, the band with it, and the
#: measurement follows the band by construction. It was 26 once
#: before, against the old 58 px row, which is the same size arrived
#: at from the same proportion — the value tracks the list and always
#: has.
#: `layout.json list.no_farming_font` may override it.
#:
#: **THE ONE THING THIS DOES NOT REPRODUCE, stated rather than
#: discovered later:** the label is 57 % of the original's column
#: (77 of 135 native px) and about 45 % of ours, because the HD job
#: column is 2.53x its native column while the row — and therefore
#: the font — is 1.87x its native row. Three magnifications live on
#: this screen (see `zoomtables.CLUSTER_FIGURE_OFFSET`), and this
#: value is anchored on the one the label is made of.
NO_FARM_FONT_REF = 26
#: The "n not shown" line. Deliberately NOT `ROW_NAME`: it is not a
#: colony and must not read as one, and the name-overflow check scans
#: for row-name ink outside the name column.
OVERFLOW_COLOR = palette.col("colony_summary", "row_overflow",
                             (150, 120, 110))
#: **THE POP MOVE DRAWS NO MARKS ON THE ROW — 8 September 2026.**
#: `PICK_COLOR` outlined the cells a pick would take and `BAND_COLOR`
#: framed the three drop targets while one was held. Both are gone,
#: and the reason is the source rather than taste: the ONLY drawing
#: `colsum.cpp` does outside its fields and its paragraphs is the
#: scroll thumb (`Fill_`/`Line_`, colsum.cpp:759-765). The original
#: marks neither the picked pops nor the row they came from — a held
#: pop simply stops being an icon (`0x200`, coldraw.cpp:336) and
#: hangs on the pointer instead (`Draw_Cluster_`, colmove.cpp:7-37),
#: which says both things at once and is what `draw_held_cluster`
#: below transcribes. The one per-pop state the original does draw is
#: the HOVERED icon blinking dark (coldraw.cpp:342-343), which is a
#: hover and not a selection; it is not built here either.
#:
#: **AND THE THREE JOB MARKERS ARE GONE WITH THEM** — see
#: `colonytrack.RowBoxes`. The colours went with the drawings; a
#: palette key nothing reads is a marking that has stopped marking.
#: The identity letter inside a pop cell. One colour for every class:
#: WHICH class is the letter's job, and a second axis of colour here
#: would fight the fill, which is the profession.
CELL_MARK = palette.col("colony_summary", "cell_mark", (16, 18, 24))


# ── Geometry: computed once, drawn by either mode ──────────────────
def render(surface, rows, area, cfg, layout, style, first=0,
           frame_inset=0, figures=None, scanned=None, planets=None):
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
    cols = colonytrack.columns(area, cfg)
    # No `row_h` here: the loop takes it from `row_bands`, which is
    # the one place the row pitch is computed (decision 5). A local
    # copy of that expression is how the drawing and the hit-test
    # start to disagree.
    name_px = layout.font_size(cfg.get("name_font", 20))
    small_px = layout.font_size(cfg.get("small_font", 15))

    # ── ONE PLATE PER CELL OF EVERY BAND, COLONIES OR NOT ───────
    # **A DEVIATION IN KIND, and the original has no drawing call at
    # all.** `Draw_Colony_Summary_Screen_` blits ONE bitmap —
    # `animate::Draw_(0, 0, _anims[0])`, COLSUM.LBX entry 0
    # (colsum.cpp:461, loaded at :404-408) — and the cell plates are
    # painted into it. That is why every cell has one including the
    # empty rows: they are part of the picture, not a per-row
    # decision. HD cannot ship that bitmap (decision 42), so it draws
    # them, and the plate is `StyleRenderer.draw_plate` (decision 51)
    # rather than a rect this module invents.
    #
    # **AND IT IS DRAWN HERE, NOT IN THE ROW — 9 September 2026.**
    # This loop used to sit inside `_render_bar`, which runs once per
    # COLONY, so a player with seven colonies got seven plated bands
    # and bare panel below them. Every document said otherwise: the
    # comment above, decision 51 and the status document all claimed
    # a plate on every band including the empty ones, and the
    # drawing was the only one of the four that disagreed. The
    # original plates ten with eight colonies — counted on its own
    # framebuffer, `evidence/colony_summary_native_split.png`.
    #
    # FIVE COLUMNS, NOT SIX — corrected 9 September 2026. The
    # original's bitmap has a plate behind the name and behind the
    # producing text as well as behind the three job columns, so all
    # five of those are plated. The SCROLL column is not one of them:
    # what the original has there is a single continuous track with a
    # slider in it (`Draw_Bar_Indicator_`, colsum.cpp:747-771), and
    # ten stacked cells was this screen treating the scroll slot as a
    # sixth column of the row. `colonyscroll.track` draws it now.
    #
    # For the three JOB columns the plate rect IS the drop rect and
    # the cell rect — `column x band`, one expression, three readers
    # (decision 5) — which is also what closed the pick round's
    # drop-height DEVIATION: the target was `bar_h`, 52 % of the band,
    # and it is the whole band now.
    for _by, _bh in colonytrack.all_bands(area, cfg):
        for _key, (_cx, _cw) in cols.items():
            if _key == colonyscroll.COLUMN:
                continue
            style.draw_plate(surface, pygame.Rect(_cx, _by, _cw, _bh),
                             scale, PLATE_COLOR)

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
        # THE NAME CELL IS ITS OWN COLUMN BOX, and the block fills it.
        _nx, _nw = cols["name"] if cols else (area.x, 0)
        # THE SCANNED COLONY'S NAME IS THE BRIGHT ONE. `scanned` is a
        # COLONY INDEX and never a row position — the same distinction
        # `colonyselect` is built on, one sort away from being wrong.
        _draw_name_block(surface, row, _nx, y, _nw, row_h,
                         cfg, name_px, small_px, style, frame_inset,
                         scanned=(scanned is not None
                                  and row["index"] == scanned),
                         planets=planets,
                         icon_gap=int(cfg.get("planet_icon_gap", 6)
                                      * scale))
        _render_bar(surface, row, area, cfg, scale, (y, row_h), track,
                    small_px, style, layout, figures)
        # THE PRODUCING TEXT SITS IN ITS OWN COLUMN, which is its own
        # box — one rect source, like every other column.
        _cols = colonytrack.columns(area, cfg)
        if _cols:
            _bx, _bw = _cols["building"]
            colonybuild.draw(surface, row, _bx, y, _bw, row_h, cfg,
                             style, layout)

    # THE ARROWS REPLACE THE OVERFLOW LINE. "N more not shown" was
    # text where the original has two buttons, and it said what was
    # off screen without offering a way to reach it. The arrows say
    # both — a live one IS the statement that there is more — so the
    # sentence goes rather than being drawn beside them.
    colonyscroll.render(surface, area, cfg, scale, SCROLL_ARROW, first,
                        colonytrack.rows_drawn(area, cfg, scale,
                                               max(0, len(rows) - first)),
                        len(rows))


def draw_held_cluster(surface, pointer, figures, cells, scale, y=None):
    """The held pops, hanging on the pointer. Drawn LAST, over
    everything, like the original's own `Draw_Cluster_`.

    **THE OFFSET IS TRANSCRIBED, THE VERTICAL ANCHOR IS A DEVIATION**
    since 12 September 2026 — see `colonytrack.held_figure_y`, which
    computes `y` and carries the measurement. Inside a row the cluster
    sits on that row's own figure line; outside one it is the
    original's pointer offset, unchanged.

    **TRANSCRIBED** — `COLMOVE::Draw_Cluster_` (colmove.cpp:7-37),
    called with the raw pointer at the end of the screen's draw
    (`COLMOVE::Draw_Cluster_(mouse::Pointer_X_(), mouse::Pointer_Y_())`,
    colsum.cpp:509-511, after `Draw_Visible_Fields_`). The three
    numbers — +5 x, -10 y, +20 per further pop — and the reason they
    are multiplied by the sprite step live in `core/zoomtables.py`
    (decision 26), which is also where the DEVIATION that produces is
    marked. Nothing is chosen here.

    **THE ORIGINAL DOES NOT HIDE A POINTER AND NEITHER DOES THIS,
    ANSWERED FROM SOURCE.** `Clear_Mouse_Picture_` (colony.cpp:360)
    swaps the mouse list for the variable one and `Draw_Cluster_`
    then draws `C_Anims_(15)` at the pointer itself — the pointer
    picture is REPLACED, not removed, and the figures sit beside the
    replacement. HD's pointer is already its own artwork at the
    original's own proportion of the screen (`core/cursor.py`, 4.38 %
    of window height, hotspot at the top-left tip), so there is
    nothing left to swap and nothing to hide: the figures go at the
    transcribed offset from the hotspot, which is the position pygame
    reports.

    `cells` are the held pops' `colonyrows.Cell`s in the order the
    original would draw them — `Draw_Cluster_` walks `pop[]` from 0
    and takes every pop whose `0x200` is clear (colmove.cpp:24-29),
    which is ARRAY order and not the icon walk's. The caller builds
    them that way; drawing them in any other order would be a second
    ordering rule (decision 48).

    Draws nothing when the figures are not extracted. The row falls
    back to coloured cells in that state (decision 50) and a coloured
    square on the pointer would be a shape the original never has —
    the pops leaving the row is already the whole statement.
    """
    if not cells or figures is None:
        return
    # **THE SCALE, NOT THE STEP, SINCE 12 September 2026.** These are
    # NATIVE constants — `(5, -10)` and 20 — and what multiplies them
    # is however many device px a master row is drawn at
    # (`colonytrack.figure_scale`). Where that is an integer, which is
    # every window the step table used to serve alone, it is the
    # number it always was; where it is not, the cluster grows with
    # the sprite instead of hanging beside a figure a third larger.
    off_x, off_y = zoomtables.CLUSTER_FIGURE_OFFSET
    pitch = zoomtables.CLUSTER_FIGURE_PITCH * scale
    x = pointer[0] + off_x * scale
    # `y` is `colonytrack.held_figure_y`'s answer — the row's own
    # figure line when the pointer is in a row, the transcribed
    # pointer offset when it is not. None means nobody asked, and the
    # transcription is what a caller that does not know gets.
    for cell in cells:
        name = getattr(cell, "figure", None)
        surf = None if name is None else figures.get(name)
        if surf is not None:
            # PER SPRITE, because the anchor is the INK and a cluster
            # can hold two races whose ink ends on different rows —
            # see `colonytrack.figure_origin_y`. `y` is a callable
            # taking that sprite's own last inked row; None means
            # nobody asked, and the transcription is what a caller
            # that does not know gets.
            surface.blit(surf, (x, pointer[1] + off_y * scale if y is None
                                else y(figures.ink_bottom(name))))
        x += pitch


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
    surface.blit(surf, (area.x, max(area.y, y)))


def _draw_name_block(surface, row, x, y, name_w, row_h, cfg,
                     name_px, small_px, style, frame_inset=0,
                     scanned=False, planets=None, icon_gap=0):
    """The colony name, and under it climate and population.

    **LEFT-ALIGNED, WHICH IS THE ORIGINAL'S — 8 September 2026, and
    it retires a marked deviation.** `BILL::Squeeze_Formatted_
    Paragraph_Centered_(0x0C, y_pos, paragraph_type, 0x17, buffer, 0)`
    (colsum.cpp:582) passes **0** as the sixth argument, which reaches
    `Print_Formatted_Paragraph_` as JUSTIFY_LEFT (bill.cpp:210); the
    wrapper's `Centered_` is about the vertical axis only, which is
    the trap that marking existed to name (decision 45).

    This was right-aligned for a real reason: a 236 px name column
    could not hold the widest name, and right alignment sent the
    overflow LEFT into `pad_x` where nothing was drawn, instead of
    rightward onto the first slots of the track. **That trade is over
    because the column is a box.** The NAME cell is 303 reference px
    of its own, the widest name a player can produce measures 174
    (see `NAME_BOUND_NOTE`), and there is nothing to absorb because
    there is nothing to overflow.

    **THE SECOND LINE IS AN HD EXTENSION.** The original prints
    climate and n/max for the SELECTED colony only, into the scan box
    at native (13, 354, 80, 88) — `COLSUM::Draw_Colony_Scan_Info_`,
    colsum.cpp:1155, substituting into `E_Strings_(74)`. Drawing it
    per row makes comparable what the original could only show one at
    a time. Marked here, in `layout.json` under `list._hd_extension`,
    in `v3_projektstatus.md`, and in a smoke check.

    The detail line is `cfg["detail"]`, substituted by REPLACE and
    not `str.format` (decision 37): a stray brace in a translated
    string cannot raise inside the render path.
    """
    # THE CELL'S OWN INSET, and it is the frame's. `list_area`'s
    # outer few reference px are under the frame's metal rim (see
    # `_frame_bleed_note`), so the first column's text starts clear
    # of it; every other column starts at its own edge because the
    # rim is not there. One expression, applied to the left edge.
    inset = max(0, int(frame_inset * (name_px / 21.0)))
    left = x + inset
    room = max(1, name_w - 2 * inset)
    # ── THE PLANET DISC, AND THE TEXT MOVES RIGHT FOR IT ────────
    #
    # **DEVIATION — the original starts this text at native x 12 and
    # draws no planet** (`Squeeze_Formatted_Paragraph_Centered_(0x0C,
    # …)`, colsum.cpp:582; 0x0C is the 12). Data's decision of
    # 12 September 2026: the row carries the world it is about, out of
    # his own sheet, and the name and the "Terran 13/22" line under it
    # start past it. THE SHIFT IS DATA AND NOT CODE — `list.
    # planet_icon_gap` in layout.json, reference px, scaled here —
    # because it is a layout decision and the next one may want a
    # different gap without a commit in this file.
    #
    # The disc is SQUARE and as tall as the band leaves it: the icon
    # is `row_h` less the clearance the figures already use, so it
    # cannot touch the cell plate's line above or below. Centred
    # vertically, because it is a disc and a disc sitting on a floor
    # reads as falling.
    icon = planets.get(row.get("climate")) if planets is not None else None
    if icon is not None:
        surface.blit(icon, (left, y + (row_h - icon.get_height()) // 2))
        step = icon.get_width() + icon_gap
        left += step
        room = max(1, room - step)
    colour = ROW_NAME if scanned else ROW_NAME_DIM
    lines = [(style.render_text(
        _fit(row["name"], style, name_px, room, cfg), name_px, colour), 0)]
    detail = _detail_text(row, cfg)
    if detail:
        lines.append((style.render_text(detail, small_px, DETAIL_COLOR),
                      int(cfg.get("detail_gap", 2) * (small_px / 15.0))))

    block_h = sum(s.get_height() + gap for s, gap in lines)
    top = y + (row_h - block_h) // 2
    prev_clip = surface.get_clip()
    surface.set_clip(pygame.Rect(left, y, room, row_h))
    for surf, gap in lines:
        top += gap
        surface.blit(surf, (left, top))
        top += surf.get_height()
    surface.set_clip(prev_clip)


def _fit(text, style, px, room, cfg):
    """`text`, ellipsised only if it outruns even the padding.

    **AND SINCE 8 September 2026 IT SHOULD NEVER FIRE.** The column is
    a box of its own — 303 reference px — and the widest name the
    game can produce is 174 (`NAME_BOUND_NOTE`), so the ellipsis is
    the fallback for a column somebody has narrowed past the bound
    the editor reports. That is the shape it was always meant to
    have; before the columns were boxes it was the mechanism, because
    the name shared a budget with the track.

    What stood here was the old trade: a str15 name renders up to
    336 px, a realistic one 190 to 230, so the column was sized for
    the realistic case and the rest ellipsised. Both numbers were
    measured against a name that could be typed and the game's own
    cap makes it narrower — see `NAME_BOUND_NOTE`.
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
                style, layout, figures=None):
    """One row's run: the three job groups, then the growth.

    Every box comes from `colonytrack.row_boxes`, which is also what
    a click is tested against — one function, two readers
    (decision 5). Nothing here computes a position.

      cells        one per DRAWN icon, in its job's colour, with an
                   identity
                   letter where the pop is not one of the player's
                   own — see `_cell_mark`.
      growth       `max_pop` less the pops, dashed, after the gap.
                   They belong to the COLONY and not to any job,
                   which is why they are past all three groups
                   instead of trailing the last one.
      beyond       the faint line for track the colony cannot reach
                   yet. NOT padding, and not a dim square either: a
                   square there would be neither filled nor free.

    Drawn back to front — beyond, growth, cells — because a later
    draw wins where boxes touch. Not hypothetical: the "No Farming"
    label was painted over by the worker squares once, with every
    number correct and nothing on screen.

    **A HELD CLUSTER IS SIMPLY NOT HERE.** `build_rows` cleared its
    `0x200` (colmove.cpp:70) before the icon walk ran, so those pops
    produced no cell, the column's pitch was computed over what is
    left, and the same shortened list answers a hit test. There is no
    `count - n` on this path and no second pitch to keep in step —
    see `colonymove.held_pops`.
    """
    boxes = colonytrack.row_boxes(area, cfg, scale, row, band)
    top, band_h = band

    cells = row.get("cells")
    # **CLIPPED TO THE ROW, VERTICALLY ONLY.** A stepped figure is
    # 28 x step tall — 56, 84, 112 — against a row of 58, 77 and 116
    # reference-scaled px, so at 2560x1440 alone the figure is seven
    # px taller than its row. That is the integer step's known cost
    # (decision 28): 1440p takes step 3 where proportion wants 2.67,
    # which makes the figure 12.5 % larger there relative to the
    # layout than at the other two resolutions.
    #
    # **THE CLIP IS LOSSLESS, AND THAT IS MEASURED, NOT HOPED.**
    # Every one of the 54 masters carries at least 3 transparent rows
    # below its ink (measured across the whole set; the tallest ink
    # is `alkari_farmer` at 24 of 28 rows), so at step 3 there are at
    # least 9 px of empty canvas to give up and 7 px to find. The
    # figure is TOP-aligned, which is where the original draws it, so
    # what the clip removes is always the empty bottom of the canvas
    # and never a head.
    #
    # Horizontal overflow is NOT clipped: it is the overlap.
    _clip = surface.get_clip()
    if figures is not None:
        surface.set_clip(pygame.Rect(area.x, top, area.width, band_h))
    for job, index, rect in boxes.cells:
        # THE FIGURE IS THE CELL WHEN THERE IS ONE (decision 50).
        # `figures` is a `colonyfigures.FigureSet` or None, and None
        # is the ordinary state of an install that has not run the
        # extractor — the coloured cell is what it falls back to, and
        # the screen names the command elsewhere. It is a state of
        # this feature, not dead code, which is why the cell path
        # stays.
        surf = _figure_for_cell(figures, cells, job, index)
        if surf is not None:
            # **AT THE SLOT'S LEFT AND THE ROW'S TOP — TRANSCRIBED,
            # NOT CENTRED.** `animate::Draw_((30 - _step_squish) *
            # pop_draw_index + left_x, top_y, anim)` (coldraw.cpp:349)
            # places the sprite at the slot's own left edge and at
            # `top_y`, the ROW's top. Centring it in the cell was the
            # obvious-looking thing and it is an invention: the cell
            # is 2:1 here (the pitch is stepped, the bar height is
            # not), so centring pushed a 56 px figure 13 px above and
            # below a 30 px bar and, at 1440p, four px into the rows
            # either side.
            #
            # NEVER SCALED TO THE CELL. Where the cell is narrower
            # than the figure — a squished column — the overflow is
            # the OVERLAP the original has at the same squish, and
            # fitting the sprite to the slot would remove exactly the
            # thing being transcribed (decision 28).
            # THE INK ON THE PLATE'S INNER FLOOR, AND THAT IS A
            # DEVIATION —
            # 12 September 2026, Data's decision. It was `top +
            # 4 * step`, which transcribed the original's own top
            # anchor (icon row `31*i + 38` against a band at
            # `31*i + 35`) and left every pixel the band has over
            # 28 rows as empty space UNDER the figures: 2 px at
            # 1920x1080, where nobody saw it, and 17 at 3440x1371 and
            # 21 at 2560x1440, where the row's colonists floated over
            # their own row. `colonytrack.figure_origin_y` is the one
            # home for the rule and carries the measurements it rests
            # on. Anchoring the CANVAS there was the first attempt
            # and it floated at every size: a master inks to row 23
            # of 28 (24 for the three Bulrathi), so the transparent
            # tail — 8 device px at step 2, 16 at step 4 — sat under
            # every figure. What goes on the floor is the INK.
            #
            # The held cluster reads the same function through
            # `colonytrack.held_figure_y`, so a figure in hand and a
            # figure in the row cannot land on different lines.
            surface.blit(surf, (rect.x, colonytrack.figure_origin_y(
                top, band_h, figures.ink_bottom(
                    cells[job][index].figure))))
            continue
        pygame.draw.rect(surface, ZONE_COLORS[job], rect)
        mark = _cell_mark(cfg, cells, job, index)
        if mark:
            _blit_centered(surface, rect, mark, text_px, CELL_MARK, style)
    surface.set_clip(_clip)

    # LAST, SO IT WINS. The original prints "No Farming" INSIDE the
    # farmers column at `top_y + 5` (coldraw.cpp:314-320), in place of
    # the farmer figures a colony with `max_farms == 0` does not have.
    # Drawing it after the figures is that same order.
    if row["no_farming"]:
        _draw_no_farming(surface, boxes, band, cfg, layout, style)


def _figure_for_cell(figures, cells, job, index):
    """The stepped sprite for one cell, or None.

    None for four different things and the caller treats them alike:
    no figure set, a set that does not hold this name, a cell whose
    race could not be read from the snapshot, and a row built before
    the set existed. All four draw the coloured cell, which is a
    complete picture rather than a gap.
    """
    if figures is None or not cells:
        return None
    if job >= len(cells) or index >= len(cells[job]):
        return None
    name = cells[job][index].figure
    return None if name is None else figures.get(name)


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
    # `.kind`, not the cell itself: a cell carries its identity class
    # AND the figure it draws (`colonyrows.Cell`), because both are
    # branches of the same `Colony_Pop_Anim_` read and must be
    # computed from one word in one place.
    return marks.get(cells[job][index].kind, "")


def _draw_no_farming(surface, boxes, band, cfg, layout, style):
    """The label, CENTRED IN THE FARMERS COLUMN — transcribed.

    `COLDRAW::Do_Colony_Info_Pop_Stuff_For_Pop_` prints it in mode 0
    when `max_farms == 0`, for the food column only
    (coldraw.cpp:315-321):

        Set_Colony_Font_To_(3)
        Squeeze_Print_Paragraph_(left_x, top_y + 5,
                                 right_x - left_x, 28,
                                 E_Strings_(387), 2)

    and the sixth argument, 2, reaches `_Print_String_Bill_` as the
    mode that selects `fonts::Print_Centered_(x + width/2, y, str)`
    (bill.cpp). So: centred across the WHOLE column, in the band the
    farmer figures would occupy, and squeezed into a box of the
    column's width by 28 px.

    **SECOND SOURCE, MEASURED, and it agrees to the pixel.** On
    `orionlayer-fixtures/evidence/colony_summary_native_split.png` —
    the original's own list for the natives fixture, 1:1 native, its
    content origin at (22, 6) and its column separators landing on
    101/236/378/512 — the label's ink centre is 163, which is exactly
    `101 + 125/2`, and its ink TOP is 136, which is exactly
    `top_y + 5` for that row (`top_y = 31*3 + 38`). `Print_Centered_`
    therefore puts the ink top ON `y`, which is why the blit below
    subtracts the surface's own ink offset instead of using its top.

    **THE FONT SIZE IS MEASURED AND SINGLE-SOURCED, and it says so.**
    `Set_Colony_Font_To_(3)` is a STYLE INDEX; the pixel height is
    `_font_header.font_heights[3]`, loaded from the player's own
    FONTS.LBX (fonts.cpp `Set_Font_Style_`), so it is not in the
    orion2re source and this project has no font extractor. What can
    be had is the picture: the label's capital "N" measures **10 px
    of cap height** on that screenshot. `list.no_farming_font`
    carries the derivation from it — the way `SHIP_ICON_DIM` says
    DERIVED rather than pretending to a transcription — and the
    check re-measures the rendered cap against it.

    **THE SQUEEZE IS `core.textfit`'s**, which shrinks until BOTH
    dimensions fit where `_Squeeze_Print_Paragraph_` loops on height
    alone; that difference already has a home in
    `layout.json list._width_condition_note` and is not restated
    here.

    Drawn AFTER the cells, which is the order that matters and the
    one this label was once on the wrong side of — every number right
    and nothing on screen. It cannot collide with a figure anyway:
    `max_farms == 0` is exactly the case in which the food column has
    no farmer to draw.
    """
    label = cfg.get("no_farming", "")
    if not label or not boxes.targets:
        return
    column = boxes.targets[0][1]
    if not column.width:
        return
    top, band_h = band
    # THE BOX IS THE COLUMN BY (28 of 31) OF THE ROW, and the offset
    # is 5 of 31 — the original's numbers against its own row pitch
    # (`top_y = 31*i + 34`, colsum.cpp:311), turned into a proportion
    # so they carry across a resolution change rather than a pixel
    # count that does not (fundament, Evidence).
    box_h = max(1, round(NATIVE_LABEL_BOX_H * band_h / NATIVE_ROW_PITCH))
    y_off = round(NATIVE_LABEL_Y_OFFSET * band_h / NATIVE_ROW_PITCH)
    px = layout.font_size(cfg.get("no_farming_font", NO_FARM_FONT_REF))
    lines, _size = textfit.squeeze_lines(
        style, label, column.width, box_h,
        [px - n for n in range(0, max(1, px - 7))], NO_FARM_COLOR[:3])
    y = top + y_off
    for surf in lines:
        ink = surf.get_bounding_rect()
        if not ink.width:
            continue
        surface.blit(surf, (column.x + (column.width - ink.width) // 2
                            - ink.x, y - ink.y))
        y += surf.get_height()


def _blit_centered(surface, area, text, px, color, style):
    if not text:
        return
    surf = style.render_text(text, px, color)
    surface.blit(surf, (area.x + (area.w - surf.get_width()) // 2,
                        area.y + (area.h - surf.get_height()) // 2))
