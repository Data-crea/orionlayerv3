"""The colony screen's production rows as the original draws them — work
order 326 (Data's numbers_mockup.png: "draw the original's symbols, as
many and grouped as the original draws them, and put the number giving
the row's value at the end of the row").

TRANSCRIPTION `prod_symbols`: `COLDRAW::Draw_Colony_Prod_Both_` at frame
0 (coldraw.cpp:36-181), called for BC, food, industry and research in
that order (`Draw_Colony_Info_Production_`, colony.cpp:706-734: x 128,
right edge 301, spacing 20) — the BC row is drawn by the same function,
so it is drawn here too. Per row, left to right, one symbol per unit:

  the net         tens as the type's tens symbol, then the ones
                  (`Prod_Anims_(type, 1)` / `(type, 0)`, COLONY2.LBX
                  type + tens * 4, colony.cpp:325-333); the net is
                  `colonyfacts.drawn_production`, the four branches
  the second      food: the industry imports as pickaxes
                  (`Prod_Anims_(1, ..)`); industry: the pollution as
                  `Import_Anims_(1, ..)` (COLONY2.LBX 8 + ..,
                  colony.cpp:2161-2166); then one empty slot
  one empty slot  always
  the imports     exported (imports < 0) or the industry row: the type's
                  own symbols for |imports|; otherwise the import symbols
                  for the imports, then the SHORTAGE (maintenance - imports
                  - production, from 1) as the import symbols outlined in
                  colour 0xED (`Short_Anims_`, colony.cpp:2168-2176;
                  `colart.outlined`)

The step is `Calculate_Squish_Step_` (coldraw.cpp:12-34) over every
symbol and slot the original counts, at the spacing of 20 native px times
the sprite's own step, so a squeezed row squeezes as the original's
does; at a step of one pixel or less it becomes 2 and the row is clipped
to its room (coldraw.cpp:111-115). C's arithmetic is kept: tens and ones
of a negative count are negative and draw nothing (a net below zero shows
no symbol, as in the original).

The room is HD's: the row's ruled cell (`row_cells`), less `row_end_number`
— the row's value as a number at the cell's right end (Data's mockup; the
original only counts). The symbols are centred on the cell's height where
the original stands them 0 or 2 px under its row's top (colony.cpp:722-724),
the cell being HD's. Those three are HD's own and marked where the screen
draws (`coldraw._production`, `coldraw._cells`), in layout.json's marks and
the state; this module holds the transcription.

WITHOUT THE EXTRACTION (`tools/colony_art_extract.py`, decision 40) — or
an older one without these drawings — the row is as before work order
326 (`label_number`): Data's icon and the number beside it (`coldraw`).

Worked once per snapshot and size, not per frame: the plan is kept by its
inputs and the stepped drawings by their name and step.
"""
import logging

import pygame

from core import nativedraw as nd
from core.hud import text as hudtext
from core import colonyfacts
from screens.colony_summary import colonyicons

from . import colart

log = logging.getLogger("colony")

ECON_FOOD, ECON_INDUSTRY, ECON_RESEARCH, ECON_BC = 0, 1, 2, 3
#: `Draw_Colony_Info_Production_For_`'s spacing (colony.cpp:727-733).
SPACING = 20
#: The plain drawing of every symbol a row can need, to know the
#: extraction has them before a row is drawn the new way.
STEMS = tuple(f"{kind}_{t}_{tens}" for kind in ("prod", "import")
              for t in range(4) for tens in (0, 1))


def _cdiv(a, b):
    """C's `/` and `%` on ints: truncation toward zero."""
    q = abs(a) // b * (1 if a >= 0 else -1)
    return q, a - q * b


def plan(col, econ):
    """([(slot, stem, short)], counted): what one row draws, in the
    original's order — `slot` the drawn_count it is drawn at, `short` a
    shortage symbol — and the count `Calculate_Squish_Step_` divides by.
    A transcription of coldraw.cpp:36-181, branch for branch."""
    imports = [int(v) for v in col.imports]
    prod = int(col.production[econ])
    maint = [int(v) for v in col.maintenance]
    imp_t = imp_u = sec_t = sec_u = 0
    if econ != ECON_INDUSTRY:
        imp_t, imp_u = _cdiv(abs(imports[econ]), 10)
    if econ == ECON_FOOD:
        sec_t, sec_u = _cdiv(abs(imports[ECON_INDUSTRY]), 10)
    elif econ == ECON_INDUSTRY:
        sec_t, sec_u = _cdiv(int(col.pollution), 10)
    shortage = maint[econ] - imports[econ] - prod
    sh_t, sh_u = _cdiv(abs(shortage if shortage >= 1 else 0), 10)
    net_t, net_u = _cdiv(colonyfacts.drawn_production(col, econ), 10)
    counted = imp_t + sec_t + net_t + sh_t + imp_u + sec_u + net_u + sh_u
    if imports[econ] != 0 and econ != ECON_INDUSTRY:
        counted += 1
    if sec_t or sec_u:
        counted += 1
    out, n = [], 0

    def run(count, stem, short=False):
        nonlocal n
        for _i in range(count):
            out.append((n, stem, short))
            n += 1

    run(net_t, f"prod_{econ}_1")
    run(net_u, f"prod_{econ}_0")
    if sec_t or sec_u:
        if econ == ECON_INDUSTRY:
            run(sec_t, "import_1_1")
            run(sec_u, "import_1_0")
        elif econ == ECON_FOOD:
            run(sec_t, "prod_1_1")
            run(sec_u, "prod_1_0")
        n += 1
    n += 1
    if imports[econ] < 0 or econ == ECON_INDUSTRY:
        run(imp_t, f"prod_{econ}_1")
        run(imp_u, f"prod_{econ}_0")
    else:
        run(imp_t, f"import_{econ}_1")
        run(imp_u, f"import_{econ}_0")
        run(sh_t, f"import_{econ}_1", True)
        run(sh_u, f"import_{econ}_0", True)
    return out, counted


def row_step(x, right, count, spacing, px=1):
    """(step, clip): `Calculate_Squish_Step_` — its one home,
    `colonyicons.squish_step` (coldraw.cpp:12-34) — and this caller's
    floor (:111-117): a step of one native pixel or less becomes 2 and
    the row is clipped to its room. `px`: device px per native px (the
    sprite step), so the floor scales as the spacing does."""
    step = colonyicons.squish_step(x, right, count, spacing)
    if step <= px:
        return 2 * px, True
    return step, False


def available(art):
    """Every drawing a row can need is extracted: the new rows can be
    drawn. An extraction from before work order 326 has none of them,
    which is said once. Asked once per loaded set, not per frame."""
    got = _AVAILABLE.get(id(art))
    if got is None or got[0] is not art:
        missing = [s for s in STEMS if not art.has(s)] \
            if art.available else list(STEMS)
        if art.available and missing:
            log.info("colony production symbols: %d of %d not extracted "
                     "(an extraction before work order 326) - the rows "
                     "show an icon and a number. Run: %s", len(missing),
                     len(STEMS), colart.HOW)
        got = _AVAILABLE[id(art)] = (art, not missing)
    return got[1]


#: {id(art): (art, bool)} — the art object kept so its id is not reused.
_AVAILABLE = {}


def draw_rows(surface, screen, view, ground, rows, number_size):
    """Each production row (`rows`: {econ: native rect}) as the original
    draws it with the row's value at its end, in the palette of the world
    shown (`ground`: the planet's ground type, `coldraw._bg_type`). False
    when the drawings are not there (the caller draws its fallback)."""
    art = colart.load()
    if not available(art):
        return False
    layout = screen.layout
    step = _sprite_step(art, layout)
    climate = view.colony.climate
    cache = getattr(screen, "_prod_cache", None)
    if cache is None or cache["key"] != (layout.size, step, climate, ground):
        cache = {"key": (layout.size, step, climate, ground), "pics": {},
                 "rows": {}}
        screen._prod_cache = cache
    for econ, native in rows.items():
        value = colonyfacts.drawn_production(view.colony, econ)
        r = nd.rect(layout, native)
        got = _row(cache, screen, view.colony, econ, r, value, number_size,
                   step)
        clip = surface.get_clip()
        if got["clip"] is not None:
            surface.set_clip(got["clip"].clip(clip))
        for stem, short, x, y in got["symbols"]:
            surface.blit(_pic(cache, art, stem, short, climate, ground,
                              layout), (x, y))
        surface.set_clip(clip)
        # `row_end_number` (coldraw's mark): the row's value at its end
        colour = hudtext.colour("negative" if value < 0 else "value")
        text = screen.style.render_text(str(value), number_size, colour)
        surface.blit(text, (got["number_right"] - text.get_width(),
                            r.centery - text.get_height() // 2))
    return True


def _row(cache, screen, col, econ, r, value, number_size, step):
    """The placed symbols of one row, kept while its inputs are the same:
    one snapshot draws every frame from this."""
    key = (econ, tuple(r), value, number_size, int(col.production[econ]),
           tuple(int(v) for v in col.imports),
           tuple(int(v) for v in col.maintenance), int(col.pollution))
    got = cache["rows"].get(econ)
    if got is not None and got["key"] == key:
        return got
    pad = max(2, r.h // 8)
    field = max(screen.style.text_width(str(value), number_size),
                screen.style.text_width("888", number_size))
    number_right = r.right - pad
    left, right = r.x + pad, number_right - field - pad
    symbols, counted = plan(col, econ)
    pitch, clipped = row_step(left, right, counted, SPACING * step, step)
    h = 23 * step
    y = r.y + (r.h - h) // 2
    got = {"key": key, "number_right": number_right,
           "clip": pygame.Rect(left, r.y, max(0, right - left), r.h)
           if clipped else None,
           # a shortage's bitmap is one px larger all round (the sprite sits
           # at (1, 1) inside it, as `Short_Anims` makes it) and is drawn at
           # the same point, so the outline surrounds the symbol
           "symbols": [(stem, short, left + pitch * slot, y)
                       for slot, stem, short in symbols]}
    cache["rows"][econ] = got
    return got


def _pic(cache, art, stem, short, climate, ground, layout):
    """A drawing at the screen's sprite step (`nd.magnified`), kept."""
    k = (stem, short)
    if k not in cache["pics"]:
        pic = art.outlined(stem, climate, ground) if short else \
            art.sprite(stem, climate, ground)
        cache["pics"][k] = nd.magnified(pic, layout)
    return cache["pics"][k]


def _sprite_step(art, layout):
    """The integer step `nd.magnified` gives the screen's sprites."""
    pic = art.sprite(STEMS[0], 0, 0)
    return max(1, nd.magnified(pic, layout).get_width() // pic.get_width())
