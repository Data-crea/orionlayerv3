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

TWO MODES, and the label differs between them. FIGURE MODE draws a
sprite per colonist, which is what the original does — so the
figures are closer to MOO2 than the squares are, and what stays
invented is the rest: the fixed 42-slot track, the free and
unreachable regions, and the zone colour as a rule beneath the
figures instead of three columns. Neither mode is a transcription of
the original's LAYOUT. It is off by default and cannot come on by
itself; see `colonyfigures.load_figures`.

ONE GEOMETRY, TWO RENDERINGS. `track_metrics` and `row_regions` are
computed once and handed to whichever mode draws. If each mode
worked out its own unit, zone edges and free region, a comparison
between the two would be comparing two LAYOUTS rather than two
drawings of one layout, and the drift would be a slot wide — big
enough to change which figure sits under a divider, small enough
that no screenshot names it.

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
NO_FARM_COLOR = palette.col("colony_summary", "no_farming", (150, 120, 110))


# ── Geometry: computed once, drawn by either mode ──────────────────

#: `unit` is one slot's ink, `gap` the space after it, `step` the two
#: together — the pitch from one slot to the next. `width` is the
#: whole POP_LIMIT_CAP-slot track. A sprite may be at most `unit`
#: wide, which is the step minus the gap: a figure that ate its gap
#: would touch its neighbour and the count would stop being legible.
Track = collections.namedtuple("Track", "unit gap step width bar_h")

#: `runs` is (zone, start_slot, count) per profession — the squares
#: fill them, the figures stand in them and the zone rule underlines
#: them. `filled`..`reach` is the free region, `reach`..POP_LIMIT_CAP
#: the unreachable one.
Regions = collections.namedtuple("Regions", "runs filled reach")


def track_metrics(area, cfg, scale):
    """The one geometry both modes measure from.

    The slot is measured from POP_LIMIT_CAP and from nothing on
    screen, which is what makes counting mean anything — see the
    constant in `colonyrows.py`. `tail_width` is reserved BESIDE the
    track, not taken out of it: a full-length track ends where the
    panel does, and "No Farming" needs a column no slot reaches.
    """
    gap = max(1, int(cfg.get("square_gap", 2) * scale))
    name_w = int(cfg.get("name_width", 320) * scale)
    pad_x = int(cfg.get("pad_x", 18) * scale)
    tail_w = int(cfg.get("tail_width", 150) * scale)
    bar_space = area.w - name_w - tail_w - 2 * pad_x
    unit = max(2, (bar_space - (POP_LIMIT_CAP - 1) * gap) // POP_LIMIT_CAP)
    return Track(unit=unit, gap=gap, step=unit + gap,
                 width=POP_LIMIT_CAP * unit + (POP_LIMIT_CAP - 1) * gap,
                 bar_h=int(cfg.get("bar_height", 30) * scale))


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

def render(surface, rows, area, cfg, layout, style, figures=None):
    """Draw the rows into `area`. Everything sized from `cfg`.

    `area` is the `list_area` box in screen coordinates, `cfg` the
    `list` block of layout.json. No geometry constant lives here —
    `POP_LIMIT_CAP` is a population count the engine enforces, not a
    tuned size, and it is the one number the track is measured from.

    `figures` is a `colonyfigures.FigureSet` or None. None draws
    squares, which is the default and the only mode a clone of the
    repository can reach; the caller loads the set once rather than
    per frame.

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
    rule_h = max(1, int((cfg.get("figures") or {}).get("rule_height", 3)
                        * scale))

    y = area.y + int(cfg.get("pad_y", 12) * scale)
    for row in rows:
        if y + row_h > area.bottom:
            break
        label = style.render_text(row["name"], name_px, ROW_NAME)
        surface.blit(label, (area.x + pad_x,
                             y + (row_h - label.get_height()) // 2))
        bar_x = area.x + pad_x + name_w
        bar_y = y + (row_h - track.bar_h) // 2
        _render_bar(surface, row, bar_x, bar_y, track, cfg, small_px,
                    style, figures, rule_h)
        y += row_h


def _render_bar(surface, row, x, y, track, cfg, text_px, style,
                figures, rule_h):
    """One POP_LIMIT_CAP-slot track, in three regions with three states.

      filled       0..pops, one per assigned pop — a square in its
                   zone's colour, or a figure standing on a zone rule.
      free         pops..max_pop, a dashed outline and no fill: a
                   slot this colony can be grown into TODAY.
      unreachable  max_pop..POP_LIMIT_CAP, no square at all, only a
                   faint baseline.

    The third region is NOT padding, and a square there — even a dim
    one — would say the wrong thing twice, being neither filled nor
    free. It is room the colony does not have YET: Advanced City
    Planning adds a flat +5, Biospheres +2, Subterranean scales with
    size, terraforming moves the climate factor itself.

    Only the FILLED region changes between the modes; the free and
    unreachable ones are drawn by the same code from the same
    `Regions`, so comparing the modes compares one thing.

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
    if figures is None:
        _draw_squares(surface, regions, track, x, y)
    else:
        _draw_figures(surface, regions, track, x, y, figures, rule_h)

    if row["no_farming"]:
        label = cfg.get("no_farming", "")
        if label:
            surf = style.render_text(label, text_px, NO_FARM_COLOR)
            surface.blit(surf, (x + track.width + track.gap * 4,
                                y + (track.bar_h - surf.get_height()) // 2))


def _draw_squares(surface, regions, track, x, y):
    """One filled square per pop, the zone colour as the fill."""
    for zone, start, count in regions.runs:
        for i in range(count):
            pygame.draw.rect(surface, ZONE_COLORS[zone], pygame.Rect(
                x + (start + i) * track.step, y + 1,
                track.unit, track.bar_h - 2))


def _draw_figures(surface, regions, track, x, y, figures, rule_h):
    """One sprite per pop, the zone colour as a rule beneath them.

    The colour stops being a fill because a filled block behind a
    figure fights it for the same pixels — the silhouette carries
    the profession and needs a quiet ground — while the rule still
    shows the zone as a run, which is what the fill was doing.
    Sprites are centred in their slot and stand ON the rule, so all
    three professions share one line however their widths differ.
    """
    common, sprites = figures.sized(track.unit, track.bar_h - rule_h)
    base = y + track.bar_h
    for zone, start, count in regions.runs:
        x0 = x + start * track.step
        x1 = x + (start + count - 1) * track.step + track.unit
        pygame.draw.rect(surface, ZONE_COLORS[zone],
                         pygame.Rect(x0, base - rule_h, x1 - x0, rule_h))
        sprite = sprites[zone]
        offset = (track.unit - sprite.get_width()) // 2
        for i in range(count):
            surface.blit(sprite, (x + (start + i) * track.step + offset,
                                  base - rule_h - common))


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
