"""The engine's placement of a colony's buildings, replayed — and the roads
that follow it. Work order 339 (Data, 28 October 2026: "in the original all
buildings are cleanly placed and coherent; in HD it looks randomly placed").

Why a replay: the roads are not on the wire (open fix 36 sends the grid and
the satellites, not `COLDRAW::road_list`), and they are drawn from the SAME
random stream the placement ends on — `Make_Bldg_Array_For_Colony_` seeds
`game_random` with the colony's index, places every building with `Random_`
draws, jitters the houses, and only then calls
`Build_Road_List_Based_On_Bldg_List_` (colony_main.cpp:527-617). So the
roads are a function of (colony index, buildings, pops) and nothing else,
and a client can only get them by running the placement again.

TRANSCRIPTION (is_ui_view 0, which is the colony screen's own call:
colony_main.cpp:286, colony.cpp:1651, colbldg.cpp:594):

  the stream       `Random` (random.cpp:25-39): an LCG, seed * 0x41C64E6D +
                   0x3039, rejected above `max * (0xFFFFFFFF / max)`
  the buildings    `Insert_Bldg_Into_Array_` (colony_main.cpp:619-676), the
                   replacement slot (`Find_Replacement_Slot_For_Building_`,
                   colony.cpp:263-293), the housing (`N_Houses_In_Bldg_
                   Array_`, colony.cpp:465-482), the satellites
                   (`Insert_Satellite_Into_Array_`, `Sat_Should_Be_Replaced_`,
                   colony.cpp:229-254), the sort (`Sort_Bldg_Array_Columns_`,
                   colony_main.cpp:677-720), the house jitter and the
                   Capitol's move to (1, 1) (colony_main.cpp:559-600,
                   `Get_Bldg_CR_`, colony.cpp:358-388)
  the roads        `Build_Road_List_Based_On_Bldg_List_` (coldraw.cpp:515-
                   562) with `N_Roads_Around_CR_` (:603) and
                   `Pick_Random_Road_At_And_Around_CR_` (:564). `Link_
                   Buildings_` (:495) only calls `Draw_Simplest_Path_`, an
                   empty function in orion2re (:436) — it draws no road and
                   takes no random number
  the table        `TECHDATA::buildings` cost and group (techdata.cpp:41-90,
                   `s_tech_building_data`: name, id, tech_app, cost, 0,
                   upkeep, group, 0; group 7 is a satellite)

The replay proves itself: `replay` returns the grid and the satellites, and
`roads_for` draws roads only when they equal the engine's own (the wire's),
so a drift in this transcription shows as no roads, never as wrong ones.

UNVERIFIED `roads_live`: `Remove_Satellite_From_Array_` (colony.cpp:1651) rebuilds the placement WITHOUT
zeroing the road list (only `Load_Road_List_Anims_`, colony_main.cpp:386, does), so after a scrapped satellite the
engine's roads may differ from this replay, which starts from zero; the wire's grid cannot show that. The replay was compared with the wire's grid in
the suite's fixtures and with a native frame of the all-buildings save
(work order 339); a live engine's CBLD block was not read against it (no
live runs).
"""

#: (cost, group) per building id 0..48 — techdata.cpp:41-90.
TECH = {0: (0, 6), 1: (60, 4), 2: (150, 0), 3: (1000, 7), 4: (200, 1),
        5: (150, 2), 6: (200, 1), 7: (60, 3), 8: (1000, 7), 9: (200, 1),
        10: (100, 0), 11: (200, 0), 12: (250, 0), 13: (200, 0),
        14: (500, 7), 15: (60, 3), 16: (200, 1), 17: (500, 1),
        18: (250, 5), 19: (250, 5), 20: (120, 3), 21: (60, 0),
        22: (60, 0), 23: (500, 2), 24: (200, 1), 25: (120, 1),
        26: (120, 2), 27: (200, 2), 28: (80, 0), 29: (150, 1),
        30: (150, 2), 31: (250, 0), 32: (80, 0), 33: (200, 1),
        34: (200, 1), 35: (60, 0), 36: (150, 3), 37: (120, 0),
        38: (100, 1), 39: (80, 0), 40: (400, 7), 41: (2500, 7),
        42: (1000, 0), 43: (150, 0), 44: (250, 0), 45: (300, 0),
        46: (200, 0), 47: (150, 0), 48: (800, 0)}
#: Artemis System Net, Dimensional Portal, Star Base, Star Fortress: the
#: houses' ids (`Insert_Bldg_Into_Array_`'s switch, colony_main.cpp:658-670).
HOUSES = (3, 14, 40, 41)
HOUSING = -3
CAPITOL = 9
SATELLITE_GROUP = 7


class Rng:
    """`game_random::Random` (random.cpp:25-39)."""

    def __init__(self, seed):
        self.seed = seed & 0xFFFFFFFF

    def random(self, top):
        if top == 0:
            return 1
        quotient = 0xFFFFFFFF // top
        limit = top * quotient
        seed = self.seed
        while True:
            seed = (seed * 0x41C64E6D + 0x3039) & 0xFFFFFFFF
            if not limit <= seed:
                break
        self.seed = seed
        return seed // quotient + 1


def _bldg_cr(grid, rng, bid):
    """`Get_Bldg_CR_` (colony.cpp:358-388): (found, row, col); it draws a
    random number for every empty cell it passes."""
    row = col = empty = 0
    for i in range(6):
        for j in range(6):
            cur = grid[i][j]
            if cur == bid:
                return True, i, j
            if cur == 0:
                empty += 1
                if rng.random(empty) == 1:
                    row, col = i, j
    return bid == -1, row, col


def _replacement(grid, bid):
    """`Find_Replacement_Slot_For_Building_` (colony.cpp:263-293)."""
    if bid < 0:
        return -1, -1
    least, row, col = 1000, 0, 0
    for i in range(6):
        for j in range(6):
            cur = grid[i][j]
            if cur in HOUSES:
                least, row, col = 0, i, j
            elif TECH[cur][0] < least:
                row, col, least = i, j, TECH[cur][0]
    return row, col


def _insert(grid, rng, delta, bid, kind):
    """`Insert_Bldg_Into_Array_` (colony_main.cpp:619-676), not back to
    front (that is the Colonies list's thumbnail, `is_ui_view` 1)."""
    row = col = -1
    houses = sum(1 for i in range(6) for j in range(6)
                 if grid[i][j] in HOUSES)
    house_mod = (houses + delta) % 4
    if kind < 36:
        empty = 0
        for i in range(6):
            for j in range(6):
                if grid[i][j] == 0:
                    empty += 1
                    if rng.random(empty) == 1:
                        row, col = i, j
        if row == -1 or (col == -1 and bid != HOUSING):
            row, col = _replacement(grid, bid)
    else:
        row, col = _replacement(grid, bid)
    if row == -1 or col == -1:
        return
    if bid >= 0:
        grid[row][col] = bid
    elif bid == HOUSING:
        grid[row][col] = HOUSES[(house_mod + 1) % 4]
    elif bid == -1:
        grid[row][col] = 8


def _sort(grid):
    """`Sort_Bldg_Array_Columns_` (colony_main.cpp:677-720)."""
    done = 0
    while True:
        swapped = 0
        for row in range(5):
            for col in range(5):
                for r2, c2 in ((row + 1, col + 1), (row + 1, col),
                               (row, col + 1)):
                    b1, b2 = grid[row][col], grid[r2][c2]
                    if b1 != 0 and b2 != 0 and TECH[b2][1] < TECH[b1][1]:
                        swapped = b1
                        grid[row][col], grid[r2][c2] = b2, b1
        done += 1
        if not (swapped != 0 and done < 6):
            return


def _satellite_replaced(bid, have):
    """`Sat_Should_Be_Replaced_` (colony.cpp:229-246)."""
    if bid == 40:
        return bool(have[8] or have[41])
    if bid == 8:
        return bool(have[41])
    return False


def _jitter(grid, rng):
    """colony_main.cpp:559-600: each house id, twice round, is swapped with
    the diagonal cell (tr, tr) — `tc = tr` is in the source as written —
    then the Capitol goes to (1, 1) if that is taken."""
    for k in range(8):
        found, row, col = _bldg_cr(grid, rng, HOUSES[k % 4])
        if not found:
            continue
        done = False
        for si in (1, 0, -1):
            for _di in (1, 0, -1):
                if done:
                    break
                tr = min(5, max(0, row - si))
                if grid[tr][tr] == 0:
                    swap = rng.random(3) == 1
                else:
                    swap = rng.random(3) == 1 or rng.random(3) == 1
                if swap:
                    grid[tr][tr], grid[row][col] = grid[row][col], \
                        grid[tr][tr]
                    done = True
    found, row, col = _bldg_cr(grid, rng, CAPITOL)
    if found and grid[1][1] != 0:
        grid[1][1], grid[row][col] = grid[row][col], grid[1][1]


# ---- the roads -------------------------------------------------------------

def new_road_list():
    """`Load_Road_List_Anims_` (coldraw.cpp:475-493): road_list[7][7], each
    cell four connections (0 = none) and four COLROADS entries, numbered in
    the order the loop hands them out; -1 where the cell has no such road
    (the last row has only direction 0, the last column only 1)."""
    conn = [[[0] * 4 for _ in range(7)] for _ in range(7)]
    anim = [[[-1] * 4 for _ in range(7)] for _ in range(7)]
    n = 0
    for c in range(4):
        for i in range(7):
            for j in range(7):
                if (i == 6 and c != 0) or (j == 6 and c != 1):
                    continue
                anim[i][j][c] = n
                n += 1
    return conn, anim


def _roads_around(conn, row, col):
    """`N_Roads_Around_CR_` (coldraw.cpp:603-622)."""
    return sum(1 for dr, dc, d in ((0, 0, 0), (0, 0, 1), (0, 1, 0),
                                   (1, 0, 1))
               if conn[row + dr][col + dc][d] != 0)


def _pick_random_road(conn, rng, row, col, want):
    """`Pick_Random_Road_At_And_Around_CR_` (coldraw.cpp:564-598), four
    searches. It compares each connection with `want`, which the caller
    leaves at 0 — so it matches the cells WITHOUT a road; kept as written,
    because what it returns only matters for the random numbers it takes."""
    best = (row, col, want)
    matches = 0
    for dr, dc, d in ((0, 0, 0), (0, 0, 1), (0, 1, 0), (1, 0, 1)):
        if conn[row + dr][col + dc][d] == want:
            matches += 1
            if rng.random(matches) == 1:
                best = (row + dr, col + dc, d)
    return matches, best


def build_roads(grid, rng):
    """`Build_Road_List_Based_On_Bldg_List_` (coldraw.cpp:515-562): the
    connection table (7 x 7 x 4) from the final grid, taking numbers from
    `rng` where it left off."""
    conn, _anim = new_road_list()
    for x in range(6):
        for y in range(6):
            if grid[x][y] != 0:
                if rng.random(2) == 1:
                    conn[x][y][0] = 1
                else:
                    conn[x][y][1] = 1
                if rng.random(2) != 1:
                    conn[x + 1][y][0] = 1
                if rng.random(2) != 1:
                    conn[x][y + 1][1] = 1
                conn[x][y + 1][2] = 0
                conn[x][y + 1][3] = 0
            else:
                if conn[x][y + 1][2] != 0 and conn[x][y + 1][3] != 0:
                    if rng.random(2) == 1:
                        conn[x][y + 1][3] = 0
                    else:
                        conn[x][y + 1][2] = 0
                if _roads_around(conn, x, y) == 4 and \
                        (conn[x][y][2] == 1 or conn[x][y][3] == 1):
                    matches, (rx, ry, rd) = _pick_random_road(
                        conn, rng, x, y, 0)
                    if matches:
                        conn[rx][ry][rd] = 0
    return conn


def replay(colony_idx, have, n_pops):
    """(grid, satellites, connections) for a colony: `have` the 49
    building flags, `n_pops` its population. grid[row][col] as the wire's."""
    rng = Rng(colony_idx)
    grid = [[0] * 6 for _ in range(6)]
    sats = [-1] * 10
    n_sat = placed = 0
    for bid in range(49):
        if not have[bid]:
            continue
        if TECH[bid][1] == SATELLITE_GROUP:
            if not _satellite_replaced(bid, have):
                sats[n_sat] = bid
                n_sat += 1
        else:
            _insert(grid, rng, colony_idx, bid, placed)
            placed += 1
    for _h in range((n_pops & 0xFF) // 3 + 1):
        if placed < 36:
            _insert(grid, rng, colony_idx, HOUSING, placed)
            placed += 1
    _sort(grid)
    _jitter(grid, rng)
    return grid, sats, build_roads(grid, rng)
