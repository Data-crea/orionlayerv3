"""The colony's buildings as sprites on the ground, and its satellites in
the sky — work order 326 (Data's decision, 23 October 2026: "the colony
screen must draw the buildings as the original does").

TRANSCRIPTION, what the original draws (the engine's own source):

  the cells      `Draw_Colony_Bldgs_` (colony_main.cpp:79-99) walks the 36
                 cells back to front (`Bldg_Back_To_Front_`, colony.cpp:
                 484-491: `BACK_TO_FRONT`); the building of cell (col, row)
                 is `_colony_bldgs[col].buildings[row]` — open fix 36's
                 grid, `grid[col][row]`
  the sprite     `Cache_Load_Bldg_` (colbcach.cpp:4-19): BLDG<n>.LBX entry
                 frame + ((id - 1) % 10) * 36, n = (id - 1) / 10, frame by
                 the cell (`Bldg_Coords_To_Effective_Frame_`, colony_main.
                 cpp:229-236; `colart.bldg_stem`). Every entry is a whole
                 640 x 480 picture with the building ALREADY where its
                 cell is, drawn at (0, 0) (`Draw_Colony_Bldg_`, colony_main.
                 cpp:47-77), so no cell is projected anywhere
  the layers     a cell's vegetation first (`Draw_Veggie_CR_`, coldraw.cpp:
                 718) — OMISSION `veggies`, COLVEGGI is not extracted — then
                 its building; a later cell is over an earlier one
  the glass      the pictures are glassed (flag 0x08): pixels 0xF0..0xFF
                 blend with what is under them (animate.cpp:252-292), the
                 shadows (`colart.glass`)
  the satellites `Draw_Colony_Satellites_` (colony.cpp:608-632): slot i of
                 ten, a picture at (295 + (i even ? i : -i) * 50, 162),
                 corner first (`animate::Draw`), COLONY.LBX 9 + the building's
                 picture (`Satellite_Anim_Pic_`, colony.cpp:196-211; the
                 slots' order is `Make_Bldg_Array_For_Colony_`'s). Neither a
                 building's nor a satellite's picture has a second frame
                 (`frame_count` is 1 in every entry), so nothing here moves

HD EXTENSION `building_sprites`: the picture is laid in the surface panel
at an INTEGER step (decision 28: sharp pixels, never a smooth scale) —
the original's 640-wide scene block from its satellites' row down to its
foot, as large a whole step as the panel holds, centred across the panel
and standing on its foot, so the city keeps the original's arrangement
and proportions and sits in the lower part of the picture, on the ground
(`block_rect`). The sprites are placed from the wire's grid and
satellites (open fix 36); `placement.py` of the work order's scratch is
only for offline renders. Without the extracted pictures nothing is drawn
and `coldraw` keeps the building list (DEVIATION `building_list`).

HD EXTENSION `satellite_lift` (Data, 26 October 2026: the Star Base stood
on the mountains and did not read as being in the air): the satellites
— Star Base, Battlestation, Star Fortress, Artemis System Net, Dimensional
Portal, all in the one row — are drawn higher than the original's row 162
wherever the panel is taller than the block it holds, so that their top
edge stands `SAT_TOP_SHARE` of the panel's height under its top at the
latest; never lower than the original puts them, and not at all where the
panel holds the block exactly (1920x1080, 3840x2160: they already stand at
the panel's top). Only the drawing moves: the wire's fields (`colright`)
keep the engine's own coordinates.

UNVERIFIED `building_grid_live`: the grid was compared with a native frame
of a live colony only through the offline transcription of the engine's
placement (work order 326's check); a live engine's CBLD block was not
read for this.
"""
import pygame

from core import nativedraw as nd
from core import nativeview as nat

from . import colart
from . import colgeom as geom

#: `Bldg_Back_To_Front_`'s table (colony.cpp:484-491): 36 (col, row).
BACK_TO_FRONT = tuple(zip(*[iter((
    5, 5, 5, 4, 4, 5, 5, 3, 3, 5, 4, 4, 5, 2, 2, 5, 4, 3, 3, 4, 5, 1, 1, 5,
    4, 2, 2, 4, 3, 3, 5, 0, 0, 5, 4, 1, 1, 4, 2, 3, 3, 2, 4, 0, 0, 4, 3, 1,
    1, 3, 2, 2, 3, 0, 0, 3, 2, 1, 1, 2, 2, 0, 0, 2, 1, 1, 1, 0, 0, 1, 0, 0
))] * 2))
#: `Satellite_Anim_Pic_` (colony.cpp:196-211): building id -> COLONY.LBX
#: picture 9 + p; the other ids are not satellites.
SATELLITE_PIC = {3: 7, 8: 1, 14: 3, 40: 2, 41: 0}
#: `Draw_Colony_Satellites_` (colony.cpp:608-632).
SAT_Y, SAT_SLOTS, SAT_CENTRE, SAT_STEP = 162, 10, 295, 50
#: The original's scene: 640 wide, its foot at 480 (colony_main.cpp:111-115).
NATIVE_W, NATIVE_H = nat.NATIVE_W, nat.NATIVE_H
#: The block laid in the panel runs from the satellites' row to the foot.
BLOCK_TOP = SAT_Y + 1
#: `satellite_lift`: the share of the panel's height under its top at which
#: the satellites' top edge stands at the latest. At 2560x1440 the original's
#: row put the Star Base at 25 % of the panel, on the ridge of the HD sky's
#: mountains (about 30 %); 10 % leaves it clear of them.
SAT_TOP_SHARE = 0.10


def sat_xy(slot):
    """Slot i's corner (colony.cpp:621-624)."""
    return (1 if slot % 2 == 0 else -1) * slot * SAT_STEP + SAT_CENTRE, SAT_Y


def sprites(art, placement, climate, bg, lift=0):
    """[(surface, (x, y))] in the original's 640 x 480 coordinates, in
    drawing order: the city back to front, then the satellites, `lift`
    native rows higher than the original's (`sat_lift`; 0 is the original's
    own place). Only what the pictures hold: a cell or a satellite the
    extraction lacks is skipped. `placement` is open fix 36's {"grid",
    "satellites"}."""
    out = []
    grid = placement["grid"]
    for col, row in BACK_TO_FRONT:
        stem = art_stem(grid[col][row], col, row)
        got = art.picture(stem, climate, bg) if stem else None
        if got is not None:
            out.append((got[0], got[1]))
    for slot, bid in enumerate(placement["satellites"][:SAT_SLOTS]):
        pic = SATELLITE_PIC.get(bid)
        got = art.picture(f"satellite_{pic}", climate, bg, glassed=False) \
            if pic is not None else None
        if got is not None:
            x, y = sat_xy(slot)
            out.append((got[0], (x + got[1][0], y - lift + got[1][1])))
    return out


def art_stem(bid, col, row):
    return colart.bldg_stem(bid, col, row)


def native_layer(art, placement, climate, bg, lift=0):
    """The whole scene's buildings and satellites at the original's size,
    over nothing (alpha): 640 x 480 — what the check lays over the original's
    own frame (`lift` 0), and what `layer` scales."""
    surf = pygame.Surface((NATIVE_W, NATIVE_H), pygame.SRCALPHA)
    for pic, at in sprites(art, placement, climate, bg, lift):
        surf.blit(pic, at)
    return surf


def step_for(rect_size):
    """The largest whole step the native block (640 wide, from
    `BLOCK_TOP` to the foot) fits `rect_size` at — `BLOCK_TOP` is 163, one
    row under the satellites' corner row: the Battlestation's and the Star
    Base's drawings ink that row, and a panel that holds the block exactly
    cuts it (`draw` clips) rather than halve the city; 1 when it fits at none
    (a window too small for the original's own size: the block then reaches
    past the panel and `draw` cuts it at the panel)."""
    w, h = rect_size
    return max(1, min(w // NATIVE_W, h // (NATIVE_H - BLOCK_TOP)))


def block_rect(rect):
    """(step, destination rect of the whole 640 x 480 canvas) for a panel
    `rect`: centred across it, the canvas's foot on the panel's foot."""
    k = step_for(rect.size)
    w, h = NATIVE_W * k, NATIVE_H * k
    return k, pygame.Rect(rect.x + (rect.w - w) // 2, rect.bottom - h, w, h)


def sat_lift(rect, step):
    """HD EXTENSION `satellite_lift`: how many native rows higher than the
    original's row the satellites are drawn in a panel `rect` at `step`: the
    rows that bring their top edge to `SAT_TOP_SHARE` of the panel's height
    under its top, 0 when the original's row is already that high."""
    natural_top = rect.bottom - (NATIVE_H - SAT_Y) * step
    want_top = rect.y + round(SAT_TOP_SHARE * rect.h)
    return max(0, (natural_top - want_top) // step)


_cache = {}


def layer(art, placement, climate, bg, step, lift=0):
    """The native layer scaled by a whole `step`, kept per what it shows
    (grid, satellites, world, step, lift) — one scale per snapshot and
    size, not one a frame (check 090zzzzzp)."""
    key = (tuple(map(tuple, placement["grid"])),
           tuple(placement["satellites"]), climate, bg, step, lift)
    got = _cache.get(key)
    if got is None:
        if len(_cache) >= 4:
            _cache.clear()
        got = pygame.transform.scale(
            native_layer(art, placement, climate, bg, lift),
            (NATIVE_W * step, NATIVE_H * step))
        _cache[key] = got
    return got


def draw(surface, rect, art, placement, climate, bg):
    """Lay the city and the satellites in `rect` (the surface panel's
    inside); False, and nothing drawn, without the pictures or the grid."""
    if rect is None or placement is None or not art.available or \
            art.glass() is None or not art.has("bldgcell_1_0"):
        return False
    k, dest = block_rect(rect)
    pic = layer(art, placement, climate, bg, k, sat_lift(rect, k))
    prev = surface.get_clip()
    surface.set_clip(rect.clip(prev))
    surface.blit(pic, dest.topleft)
    surface.set_clip(prev)
    return True


def shown(state):
    """Open fix 36's placement when the sprites can be drawn from it — the
    pictures are extracted, the glass table is there, and the wire has the
    grid — else None, and the building list is the colony's buildings."""
    placement = getattr(state, "colony_placement", None)
    art = colart.load()
    if placement is None or not art.available or art.glass() is None \
            or not art.has("bldgcell_1_0"):
        return None
    return placement


def panel_rect(screen):
    from . import coldraw
    return coldraw.scene_rect(screen)


def list_geometry(screen, n, placement):
    """DEVIATION `building_list`, ONE geometry for its drawing and its
    clicks (`coldraw._buildings`, `colright.row_at`): (box, [row rects]) in
    window pixels, recomputed from the layout each time (P809).

    Without sprites (`placement` None) the original's own native rows
    (`colgeom.building_row`). With them the list stands in the panel's
    left margin — the space the centred city leaves — from the panel's
    top, its rows squeezed to the panel's height when 37 of them would run
    past it, so it neither covers the city nor leaves the panel; its
    function (the right click's description, the demolish) is the same."""
    layout = screen.layout
    r = panel_rect(screen) if placement is not None else None
    if r is not None:
        k, dest = block_rect(r)
        margin = dest.x - r.x
        pad = max(2, nd.rect(layout, (0, 0, 2, 0)).w)
        if margin >= 40 * pad // 4 and n > 0:
            nat = nd.rect(layout, geom.building_row(0)).h
            # above the units' strip, which stands at the panel's foot
            foot = nd.rect(layout, geom.UNITS).h
            pitch = max(1, min(nat, (r.h - 2 * pad - foot) // n))
            x0, w = r.x + pad, margin - 2 * pad
            rows = [pygame.Rect(x0, r.y + pad + i * pitch, w, pitch)
                    for i in range(n)]
            return pygame.Rect(r.x, r.y, margin, n * pitch + 2 * pad), rows
    rows = [nd.rect(layout, geom.building_row(i)) for i in range(n)]
    return nd.rect(layout, geom.building_box(n)), rows
