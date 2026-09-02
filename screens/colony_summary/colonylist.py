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

**It is a SUBSET, and the omission is deliberate.** That one call
substitutes SEVEN values, in order: planet size, climate, gravity
class, mineral class, `n_pops`, the computed maximum, and population
growth (colsum.cpp:1196-1205). The row draws three — climate,
`n_pops`, `max_pop` — and leaves four: size, gravity, mineral class
and growth.

They are left out because a row is 62 px and the second line is one
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
from .colonyrows import POP_LIMIT_CAP

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
BAR_BEYOND = palette.col("colony_summary", "bar_beyond", (34, 42, 60))
ROW_NAME = palette.col("colony_summary", "row_name", (206, 216, 238))
#: The climate/population line under the name. Quieter than the
#: name: it is context for the row, not its identity.
DETAIL_COLOR = palette.col("colony_summary", "row_detail",
                           (132, 148, 180))
NO_FARM_COLOR = palette.col("colony_summary", "no_farming", (150, 120, 110))


# ── Geometry: computed once, drawn by either mode ──────────────────

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
    "Track", "unit gap step width slack bar_h row_h build_w build_gap")

#: `runs` is (zone, start_slot, count) per profession — the squares
#: fill them. `filled`..`reach` is the free region, `reach`..
#: POP_LIMIT_CAP the unreachable one.
Regions = collections.namedtuple("Regions", "runs filled reach")


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
    name_w = int(cfg.get("name_width", 320) * scale)
    pad_x = int(cfg.get("pad_x", 18) * scale)
    tail_w = int(cfg.get("tail_width", 0) * scale)
    build_w = int(cfg.get("building_width", 0) * scale)
    build_gap = int(cfg.get("building_gap", 16) * scale)
    if build_w:
        build_w += build_gap
    bar_space = area.w - name_w - tail_w - build_w - 2 * pad_x
    unit = max(2, (bar_space - (POP_LIMIT_CAP - 1) * gap) // POP_LIMIT_CAP)
    width = POP_LIMIT_CAP * unit + (POP_LIMIT_CAP - 1) * gap
    # Clamped at 0: `unit` has a floor of 2, so a `list_area` too
    # narrow for the columns configured would compute a NEGATIVE
    # remainder, and adding that to the name column would drag the
    # track left over the names. The row then overruns the panel on
    # the right, which is the visible failure and the honest one.
    slack = max(0, area.w - (name_w + tail_w + build_w
                             + 2 * pad_x + width))
    return Track(unit=unit, gap=gap, step=unit + gap,
                 width=width, slack=slack,
                 bar_h=int(cfg.get("bar_height", 30) * scale),
                 row_h=int(cfg.get("row_height", 60) * scale),
                 build_w=int(cfg.get("building_width", 0) * scale),
                 build_gap=build_gap)


def row_regions(row):
    """The three regions of one row, in slots.

    Zones are laid down left to right in ECON order and clipped at
    POP_LIMIT_CAP, which the engine cannot pass either. Squares past
    `max_pop` are kept, not clipped: a pop is a fact, `max_pop` a
    computation with two documented deviations (see
    `colonyrows.max_population`), so they land in the unreachable
    region where nothing else is drawn and the disagreement stays
    visible.
    """
    runs = []
    slot = 0
    for zone, count in enumerate(row["jobs"]):
        n = max(0, min(count, POP_LIMIT_CAP - slot))
        if n:
            runs.append((zone, slot, n))
        slot += n
    return Regions(runs=tuple(runs), filled=slot,
                   reach=max(0, min(row["max_pop"], POP_LIMIT_CAP)))


# ── The drawing ───────────────────────────────────────────────────

def render(surface, rows, area, cfg, layout, style):
    """Draw the rows into `area`. Everything sized from `cfg`.

    `area` is the `list_area` box in screen coordinates, `cfg` the
    `list` block of layout.json. No geometry constant lives here —
    `POP_LIMIT_CAP` is a population count the engine enforces, not a
    tuned size, and it is the one number the track is measured from.

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
    row_h = int(cfg.get("row_height", 60) * scale)
    pad_x = int(cfg.get("pad_x", 18) * scale)
    name_w = int(cfg.get("name_width", 320) * scale)
    name_px = layout.font_size(cfg.get("name_font", 20))
    small_px = layout.font_size(cfg.get("small_font", 15))

    y = area.y + int(cfg.get("pad_y", 12) * scale)
    for row in rows:
        if y + row_h > area.bottom:
            break
        # The name block is handed `name_w`, the TEXT BUDGET, and is
        # unaware of `slack`: it right-aligns, clips and ellipsises
        # against that and nothing else, so the threshold does not
        # move with the resolution. The bar starts past the slack, so
        # the leftover pixels read as a wider gutter — which is the
        # one thing that column can absorb without saying anything
        # untrue.
        _draw_name_block(surface, row, area.x + pad_x, y, name_w, row_h,
                         cfg, name_px, small_px, style)
        bar_x = area.x + pad_x + name_w + track.slack
        bar_y = y + (row_h - track.bar_h) // 2
        _render_bar(surface, row, bar_x, bar_y, track, cfg, small_px,
                    style)
        if track.build_w:
            colonybuild.draw(
                surface, row, bar_x + track.width + track.build_gap, y,
                track.build_w, row_h, cfg, style, layout)
        y += row_h


def _draw_name_block(surface, row, x, y, name_w, row_h, cfg,
                     name_px, small_px, style):
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
    room = right - (x - _pad_left(x, cfg, name_px))
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
    surface.set_clip(pygame.Rect(0, y, right, row_h))
    for surf, gap in lines:
        top += gap
        surface.blit(surf, (right - surf.get_width(), top))
        top += surf.get_height()
    surface.set_clip(prev_clip)


def _pad_left(x, cfg, name_px):
    """How far left of the column the name may grow: `pad_x`."""
    return int(cfg.get("pad_x", 18) * (name_px / 21.0))


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


def _render_bar(surface, row, x, y, track, cfg, text_px, style):
    """One POP_LIMIT_CAP-slot track, in three regions with three states.

      filled       0..pops, one square per assigned pop, in its
                   zone's colour.
      free         pops..max_pop, a dashed outline and no fill: a
                   slot this colony can be grown into TODAY.
      unreachable  max_pop..POP_LIMIT_CAP, no square at all, only a
                   faint baseline.

    The third region is NOT padding, and a square there — even a dim
    one — would say the wrong thing twice, being neither filled nor
    free. It is room the colony does not have YET: Advanced City
    Planning adds a flat +5, Biospheres +2, Subterranean scales with
    size, terraforming moves the climate factor itself.

    Drawn back to front — baseline, dashed, filled — because a later
    draw wins where regions overlap. Not hypothetical: the "No
    Farming" label was painted over by the worker squares once, every
    number correct and nothing on screen. It sits AFTER the track now,
    in the reserved `tail_width` column, because a collapsed food zone
    has no width to hold a label and the free tail is no home either
    — Sol IV has one free slot, about 50 reference pixels.
    """
    regions = row_regions(row)

    # 3. unreachable: one faint line along the foot of the tail. Not
    #    per slot — a slot tick would read as an empty square, which
    #    is exactly what this region is not.
    if regions.reach < POP_LIMIT_CAP:
        thick = max(1, track.bar_h // 16)
        x0 = x + regions.reach * track.step
        pygame.draw.rect(surface, BAR_BEYOND, pygame.Rect(
            x0, y + track.bar_h - thick, track.width - (x0 - x), thick))

    # 2. free
    for i in range(regions.filled, regions.reach):
        _dashed_rect(surface, BAR_FREE,
                     pygame.Rect(x + i * track.step, y + 1,
                                 track.unit, track.bar_h - 2),
                     max(1, track.unit // 4))

    # 1. filled
    _draw_squares(surface, regions, track, x, y)

    if row["no_farming"]:
        _draw_no_farming(surface, x, y, track, cfg, text_px, style)


def _draw_no_farming(surface, x, y, track, cfg, text_px, style):
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
    if cfg.get("no_farming_placement", "below") == "tail":
        surface.blit(surf, (x + track.width + track.gap * 4,
                            y + (track.bar_h - surf.get_height()) // 2))
        return
    # `y` is the BAR's top; the row extends half the spare height
    # above and below it. Bottom-aligned in the band that leaves, so
    # any rounding slack sits between the label and the bar, where it
    # reads as spacing, rather than under the label, where it reads
    # as a taller row.
    row_bottom = y + track.bar_h + (track.row_h - track.bar_h) // 2
    surface.blit(surf, (x, row_bottom - surf.get_height()))


def _draw_squares(surface, regions, track, x, y):
    """One filled square per pop, the zone colour as the fill."""
    for zone, start, count in regions.runs:
        for i in range(count):
            pygame.draw.rect(surface, ZONE_COLORS[zone], pygame.Rect(
                x + (start + i) * track.step, y + 1,
                track.unit, track.bar_h - 2))


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
