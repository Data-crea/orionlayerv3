"""The colony list — rows, allocation bars, and the numbers behind them.

Its own module rather than the end of `screen.py`, which is at 258
lines against a ~300 guideline (decision 6), and because none of this
is about being a screen.

**The bar is an INVENTION.** The original draws three columns of pop
sprites per row, one icon per colonist, squished together when a
colony outgrows its column (`COLDRAW::Do_Colony_Info_Pop_Stuff_For_
Pop_`, coldraw.cpp:282; `Calculate_Squish_Step_`, coldraw.cpp:12).
This draws one bar per row instead, one square per colonist, in three
zones. Marked here, in `layout.json` under `list._invention`, in
`v3_projektstatus.md`, and in a smoke check that fails if the marking
disappears.

TRANSCRIBED, and each with its source:
  the row set        colonies whose `owner` is the local player
  "No Farming"       drawn in place of the food column exactly when
                     `max_farms == 0` (coldraw.cpp:315, ESTR_NO_FARMING
                     387). The wording lives in layout.json.
  the zone order     food, industry, research — ECON_FOOD=0,
                     ECON_INDUSTRY=1, ECON_RESEARCH=2
                     (orion2_consts.h:119) and the same left-to-right
                     order the original's columns use
                     (colsum.cpp:318-329)
  the planet name    colony -> planet -> star, with the numeral from
                     `HAROLD::Planet_Number_` (harold.cpp): it counts
                     the OCCUPIED slots of `star->planet_index[5]`
                     before the planet, NOT the orbit. An empty slot
                     earlier in a system shifts every numeral after it.
  the bar length     `COLCALC::Planet_Max_Population_For_Player_`
                     (colcalc.cpp:896) — see max_population() below

NOT DRAWN, deliberately: race groups as shades, and androids and
natives as locked. Those need `pop_race`, whose mask has no second
source (see `core/structs/colony.py`). Nothing here reads it, so
nothing on screen depends on an unverified claim; the zone split is
built as a list of runs so the shading can be added inside a run
later without moving anything else.
"""
import pygame

from core import palette
from core.structs import colony as colony_struct
from core.structs import planet as planet_struct
from core.structs import player as player_struct
from core.structs import star as star_struct

ROMAN = ("I", "II", "III", "IV", "V")

#: One colour per profession, in ECON order. Palette so a skin or mod
#: can restyle the whole list without touching this file.
ZONE_COLORS = (
    palette.col("colony_summary", "zone_food", (86, 150, 96)),
    palette.col("colony_summary", "zone_industry", (176, 128, 60)),
    palette.col("colony_summary", "zone_research", (86, 122, 190)),
)
BAR_EMPTY = palette.col("colony_summary", "bar_empty", (26, 32, 48))
BAR_EDGE = palette.col("colony_summary", "bar_edge", (54, 66, 92))
ROW_NAME = palette.col("colony_summary", "row_name", (206, 216, 238))
NO_FARM_COLOR = palette.col("colony_summary", "no_farming", (150, 120, 110))

# ── The numbers ───────────────────────────────────────────────────

#: colcalc.cpp:57, _size_climate_max_pop_lookup, indexed by climate.
CLIMATE_FACTOR = (25, 25, 25, 25, 25, 25, 40, 60, 80, 100)
#: mox.cpp:796, _planet_max_population, indexed by PLANET_SIZE. This
#: is the BASE of a computation and never an answer on its own — see
#: the fundament, section 3.
SIZE_BASE = (5, 10, 15, 20, 25)

TRAIT_AQUATIC = 12            # orion2_consts.h:961
TRAIT_SUBTERRANEAN = 13       # orion2_consts.h:962
TRAIT_ENVIRONMENT_IMMUNE = 23  # orion2_consts.h:972
BUILDING_BIOSPHERES = 15      # orion2_consts.h:28
POP_BONUS_BIOSPHERES = 2      # colcalc_config.cpp:40
POP_LIMIT_CAP = 42            # colcalc.cpp:930, and pop[42] is why

CLIMATE_TUNDRA, CLIMATE_OCEAN, CLIMATE_SWAMP = 4, 5, 6
CLIMATE_TERRAN, CLIMATE_GAIA = 8, 9


def player_climate(climate, traits):
    """COLCALC::Calc_Player_Climate_ (colcalc.cpp). Aquatic only."""
    if traits and traits[TRAIT_AQUATIC]:
        if climate in (CLIMATE_TUNDRA, CLIMATE_SWAMP):
            return CLIMATE_TERRAN
        if climate in (CLIMATE_OCEAN, CLIMATE_TERRAN):
            return CLIMATE_GAIA
    return climate


def max_population(colony, planet, traits):
    """The maximum the original prints, for the colony's OWNER.

    `COLCALC::Colony_Race_Pop_Limit_` (colcalc.cpp) over
    `Size_And_Climate_Race_Pop_Limit_` and
    `Size_And_Climate_Max_Population_` (colcalc.cpp:1271).

    Two details that are easy to get wrong and were both read out of
    the source rather than assumed. The climate is the COLONY's
    (offset 226), not the planet's: `Colony_Calculation_` rewrites it
    when a shield turns a Radiated world Barren (colcalc.cpp:682).
    And `SIZE_BASE[size]` is only the base — the climate factor and
    the immunity bonus scale it, which is the difference between 10
    and the 5 the game prints for a Small Ocean planet.

    TWO DEVIATIONS, both stated rather than hidden:

    1. Advanced City Planning adds a flat +5 and is NOT applied,
       because it lives in `s_player.tech_applications`, which
       `core/structs/player.py` does not expose and which has no
       verified offset. Adding an unverified one to make a bar
       longer is exactly the trade decision 23 forbids.
    2. The original returns the best limit over the RACES PRESENT in
       the colony; this returns the limit for the owner's race. The
       two agree for a single-race colony and the walk needs
       `pop_race`, whose mask has no second source yet.

    Both make the bar too SHORT rather than too long, which shows as
    a bar that cannot hold its own squares — visible, not silent.
    """
    climate = player_climate(colony.climate, traits)
    immune = bool(traits[TRAIT_ENVIRONMENT_IMMUNE]) if traits else False
    factor = min(100, (25 if immune else 0) + CLIMATE_FACTOR[climate])
    size = max(0, min(len(SIZE_BASE) - 1, planet.size))
    limit = (factor * SIZE_BASE[size] + 50) // 100
    if traits and traits[TRAIT_SUBTERRANEAN]:
        limit += 2 * size + 2          # COLCALC::Double_Add_Two_
    if colony.buildings[BUILDING_BIOSPHERES]:
        limit += POP_BONUS_BIOSPHERES
    return min(limit, POP_LIMIT_CAP)


def planet_name(colony, planets, stars):
    """'Sol III' — HAROLD::Planet_Number_ counts occupied slots."""
    if not 0 <= colony.planet < len(planets):
        return "?"
    planet = planet_struct.parse(planets[colony.planet])
    if not 0 <= planet.star_index < len(stars):
        return "?"
    star = stars[planet.star_index]
    number = 0
    for slot in star_struct.planet_indices(star):
        if slot == colony.planet:
            break
        if slot > -1:
            number += 1
    numeral = ROMAN[number] if number < len(ROMAN) else str(number + 1)
    return f"{star.name} {numeral}"


def build_rows(game_state, sort_key="name"):
    """One dict per colony of the local player, sorted.

    Only `owner`, `planet`, `n_pops`, `max_farms`, `climate` and
    `buildings` are read, plus `pop_prof` — every one of them backed
    by two sources. `pop_race` is not touched.
    """
    if game_state is None or not getattr(game_state, "colonies_raw", None):
        return []
    planets = game_state.planets_raw
    stars = game_state.stars
    me = game_state.player_num
    traits = None
    if 0 <= me < len(game_state.player_raw):
        traits = player_struct.traits(
            player_struct.parse(game_state.player_raw[me]))

    rows = []
    for raw in game_state.colonies_raw:
        col = colony_struct.parse(raw)
        if col.owner != me or not 0 <= col.planet < len(planets):
            continue
        planet = planet_struct.parse(planets[col.planet])
        jobs = [0, 0, 0]
        for i in range(min(col.n_pops, len(col.pop))):
            prof = colony_struct.pop_prof(col.pop[i])
            if 0 <= prof < len(jobs):
                jobs[prof] += 1
        rows.append({
            "name": planet_name(col, planets, stars),
            "pops": col.n_pops,
            "jobs": jobs,
            "no_farming": col.max_farms == 0,
            "max_pop": max_population(col, planet, traits),
        })

    keys = {"name": lambda r: r["name"],
            "population": lambda r: (-r["pops"], r["name"])}
    rows.sort(key=keys.get(sort_key, keys["name"]))
    return rows


# ── The drawing ───────────────────────────────────────────────────

def render(surface, rows, area, cfg, layout, style):
    """Draw the rows into `area`. Everything sized from `cfg`.

    `area` is the `list_area` box in screen coordinates, `cfg` the
    `list` block of layout.json. No geometry constant lives here.

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
    row_h = int(cfg.get("row_height", 60) * scale)
    pad_x = int(cfg.get("pad_x", 18) * scale)
    name_w = int(cfg.get("name_width", 320) * scale)
    bar_h = int(cfg.get("bar_height", 30) * scale)
    gap = max(1, int(cfg.get("square_gap", 2) * scale))
    name_px = layout.font_size(cfg.get("name_font", 20))
    small_px = layout.font_size(cfg.get("small_font", 15))

    # One square is the same size in EVERY row — that is the whole
    # point of the design: counting squares counts pops. So the
    # widest row's maximum sets the scale and every other bar is
    # shorter in proportion.
    widest = max(r["max_pop"] for r in rows) or 1
    bar_space = area.w - name_w - 2 * pad_x
    unit = max(2, (bar_space - (widest - 1) * gap) // widest)

    y = area.y + int(cfg.get("pad_y", 12) * scale)
    for row in rows:
        if y + row_h > area.bottom:
            break
        label = style.render_text(row["name"], name_px, ROW_NAME)
        surface.blit(label, (area.x + pad_x,
                             y + (row_h - label.get_height()) // 2))
        bar_x = area.x + pad_x + name_w
        bar_y = y + (row_h - bar_h) // 2
        _render_bar(surface, row, bar_x, bar_y, bar_h, unit, gap,
                    cfg, small_px, style)
        y += row_h


def _render_bar(surface, row, x, y, h, unit, gap, cfg, text_px, style):
    """The bar: `max_pop` slots wide, `pops` of them filled.

    The "No Farming" label sits AFTER the bar, not inside it. The
    design brief calls it a collapsed food zone, and a collapsed zone
    is what it is — but a zone of zero width has nowhere to put a
    label, and the bar's empty tail is not a reliable home either:
    Sol IV has one free slot in this savegame, about 50 reference
    pixels, and the words do not fit. Drawing it inside the bar is
    what the first version did, and the worker squares painted over
    it — correct in every number and invisible on screen.
    """
    slots = row["max_pop"]
    width = slots * unit + max(0, slots - 1) * gap
    pygame.draw.rect(surface, BAR_EMPTY, pygame.Rect(x, y, width, h))
    pygame.draw.rect(surface, BAR_EDGE, pygame.Rect(x, y, width, h), 1)

    # Zones left to right in ECON order: food, industry, research.
    slot = 0
    for zone, count in enumerate(row["jobs"]):
        for _ in range(count):
            if slot >= slots:
                break          # deviation made visible, see max_population
            sx = x + slot * (unit + gap)
            pygame.draw.rect(surface, ZONE_COLORS[zone],
                             pygame.Rect(sx, y + 1, unit, h - 2))
            slot += 1

    if row["no_farming"]:
        label = cfg.get("no_farming", "")
        if label:
            surf = style.render_text(label, text_px, NO_FARM_COLOR)
            surface.blit(surf, (x + width + gap * 4,
                                y + (h - surf.get_height()) // 2))


def _blit_centered(surface, area, text, px, color, style):
    if not text:
        return
    surf = style.render_text(text, px, color)
    surface.blit(surf, (area.x + (area.w - surf.get_width()) // 2,
                        area.y + (area.h - surf.get_height()) // 2))
