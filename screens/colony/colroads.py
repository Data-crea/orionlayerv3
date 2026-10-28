"""The roads of the colony's ground — work order 339.

TRANSCRIPTION `roads`: `Draw_Colony_Screen_` draws the ground, then
`COLDRAW::Draw_Road_List_` (colony_main.cpp:117-119), then the buildings
(`Draw_Colony_Bldgs_`) — so a road is under every building and under every
shadow. `Draw_Road_List_` (coldraw.cpp:452-473) walks the 7 x 7 road list
back to front (`Road_Back_To_Front_`, :444-450) and in every cell the four
directions in the order 3, 2, 0, 1; each connection that is set is the
cell's COLROADS.LBX picture, a whole 640 x 480 glassed picture drawn at
(0, 0), like a building's. Which connections are set is the engine's
random stream after the placement (`colplace`).

HD EXTENSION `roads` (the same whole step as the buildings,
`colbuildings.block_rect`): the pictures are laid in the buildings' layer,
under them, so they stand where the buildings stand at every size.

Without the extracted pictures (`tools/colony_art_extract.py`, an older
extraction has none) no road is drawn, as before, and nothing is said but
once in the log.
"""
import logging

from . import colplace

log = logging.getLogger("colony")

#: `Road_Back_To_Front_`'s table (coldraw.cpp:444-450): 49 (row, col). The
#: original's table lists (4, 3) twice and (4, 5) not at all (its fourth
#: diagonal reads 4,3 where 4,5 belongs); kept as written — the native
#: frame matches with it (work order 339).
BACK_TO_FRONT = tuple(zip(*[iter((
    6, 6, 5, 6, 6, 5, 4, 6, 5, 5, 6, 4, 3, 6, 4, 3, 5, 4, 6, 3, 2, 6, 3, 5,
    4, 4, 5, 3, 6, 2, 1, 6, 2, 5, 3, 4, 4, 3, 5, 2, 6, 1, 0, 6, 1, 5, 2, 4,
    3, 3, 4, 2, 5, 1, 6, 0, 0, 5, 1, 4, 2, 3, 3, 2, 4, 1, 5, 0, 0, 4, 1, 3,
    2, 2, 3, 1, 4, 0, 0, 3, 1, 2, 2, 1, 3, 0, 0, 2, 1, 1, 2, 0, 0, 1, 1, 0,
    0, 0
))] * 2))
#: the directions' order in a cell (coldraw.cpp:454).
DIRECTION_ORDER = (3, 2, 0, 1)
#: entries in COLROADS.LBX (42 + 42 + 36 + 36, `colplace.new_road_list`).
COUNT = 156


def stem(index):
    return f"road_{int(index)}"


def draw_list(conn):
    """The COLROADS entries to draw, in drawing order, for a connection table
    (`colplace.build_roads`)."""
    _conn, anim = colplace.new_road_list()
    out = []
    for row, col in BACK_TO_FRONT:
        for d in DIRECTION_ORDER:
            if conn[row][col][d] != 0:
                out.append(anim[row][col][d])
    return out


def roads_for(view, placement):
    """The roads of the colony `view` shows, as a tuple of COLROADS entry
    numbers in drawing order — or () when the replay of the placement does
    not end in the engine's own grid (the wire's): then the stream the
    roads come from is not the engine's, and a road from it would be
    invented."""
    colony = getattr(view, "colony", None)
    if placement is None or colony is None or view.index < 0:
        return ()
    have = list(colony.buildings)
    if len(have) < 49:
        return ()
    grid, sats, conn = colplace.replay(view.index, have, colony.n_pops)
    wire = [list(map(int, r)) for r in placement["grid"]]
    if grid != wire or list(sats) != [int(s) for s in
                                      placement["satellites"][:10]]:
        log.info("roads: the replay of the placement is not the engine's "
                 "grid for colony %d — no roads", view.index)
        return ()
    return tuple(draw_list(conn))
