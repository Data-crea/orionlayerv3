"""The score screen's rows of people: `Draw_Pop` and the eliminated players'
portraits — work order 406 (the fix 120 screen's OMISSION `score_pop_pictures`).

WHAT THE ORIGINAL DRAWS. Under "N Population" a row of up to 16 figures, under
"N Captured Colonists" a row of up to 16 portraits (`Draw_Reg_Pop`,
`Draw_Cap_Pop`: `Draw_Pop(0, 4, reg_pop)` and `Draw_Pop(1, 2, raw_captured_
population)`, score.cpp:640-645, :700-705), under "Players Eliminated" one
portrait box of each defeated player (`Draw_Eliminated_Race_Pictures`,
:725-790).

TRANSCRIPTION `score_pop_rule`: the geometry of `Draw_Pop` (score.cpp:1290-
1345). The list is at most 16 long, so `current_pop > max_pop * 27` (108 or
54) never holds and the figures stand on the grid branch: figure n at
x = (n % 25) * 22, y = (n / 25) * 22 from x = 140, one row of 22 pixel steps
for 28 pixel sprites (RACEICON's 28 x 28); the rows after it start 28 pixels
lower (`next_draw_y = y_start + y_offset + 28`). `positions` carries both
branches of the function.

TRANSCRIPTION `score_pop_count`: how many figures of which race and job, as
`Set_Hi_Score_Pop_Icon_Ids` counts them (score.cpp:1103-1190): the pops of
the player's colonies in colony order, each race's share
`(count * 160 / total + 5) / 10` (a rounding of 16 * count / total), cut to
16 in all, races in index order, race 14 and above left out; each figure is
the sprite `Colony_Pop_Anim` gives that pop (`colonyfigures.figure_for`).
DEVIATION `score_pop_pick`: the original shuffles the pops and takes the next
unused of a race at random; HD takes a race's pops evenly spread over its
list, so the picture does not change between two looks at it. The wire does
not carry `pop_units` (open fix 120 sends the raw figures only); the colonies
the snapshot holds are the source, and a snapshot that no longer holds the
player's colonies draws no row.

TRANSCRIPTION `score_captured_rule`: the captured colonists are
`min(captured colonies, 16)` portraits (`Build_Captured_Colonists_Array`,
score.cpp:1198-1235), sorted by race (`qsort` ascending), each a
`Colony_Pop_Icon` (RACEICON entry race * 13 + 12, `Draw_Pop`). 
UNVERIFIED `score_captured_races`: the original draws each portrait's race at random,
weight 5 for a player the tally's player defeated and 2 for one he had first
contact with; HD apportions the portraits over the DEFEATED players' races
by that weight alone and draws none when nobody was defeated, because the
contact list at the game's end is not carried.

TRANSCRIPTION `score_portrait_boxes`: each defeated player's portrait
(SCORE.LBX entry 2 + race, 40 x 46) side by side with a 4 pixel gap from
x = 142 (`Draw_Eliminated_Race_Pictures`: `current_x += width + 4`), the
defeat's figure "d.d" at its top and the name at its bottom. 
DEVIATION `score_portrait_frame`: the original lays SCORE.LBX's frame picture and two
`Box` lines (colours 0x4b, 0x0f) round it; HD draws the frame picture
extracted as entry 1 where it exists and no boxes. 
HD EXTENSION `score_portrait_pieces`: the figure and the name are drawn in HD's own font.

The pictures are the player's own (RACEICON.LBX through `tools/raceicon_
extract.py`, SCORE.LBX through `tools/score_art_extract.py`); without them a
row is not drawn and the figures and names of the tally stand as before.
"""
import logging
import struct

from core import blobart, lbx
from core.structs import colony as colony_struct
from core.structs import player as player_struct
from screens.colony_summary import colonyfigures

log = logging.getLogger("scorepop")

REL = "assets/shared/score/gamedata"
HOW = "python tools/score_art_extract.py"
#: Draw_Pop's constants (score.cpp:1290-1345).
MAX_ICONS = 16
GRID_X0, STEP, SPRITE = 140, 22, 28
ROW_BELOW = 28
REG_MAX_POP, CAP_MAX_POP = 4, 2
#: Draw_Eliminated_Race_Pictures: the first box's x and the gap.
BOX_X0, BOX_GAP = 0x8E, 4
STOCK_RACES = 13
DEFEATED_WEIGHT = 5
PORTRAIT_FIRST, FRAME_ENTRY, PALETTE_ENTRY = 2, 1, 0


def positions(max_pop, current):
    """`Draw_Pop`'s figure positions: [(x, y)] relative to the row's top left
    (x counted from 140), and the extra rows the call adds to `y_start`.
    Both branches of score.cpp:1290-1345."""
    space = 12 if current < max_pop * 48 else 10 if current < max_pop * 58 \
        else 8 if current < max_pop * 72 else 6 if current < max_pop * 97 \
        else 4
    out, x_off, row_n, drawn, y_start = [], 0, 0, 0, 0
    for i in range(max(0, current)):
        if i >= max_pop * 97:
            continue
        if current > max_pop * 27:
            y = y_start if row_n % 2 == 0 else y_start + space
            out.append((x_off, y))
            x_off += space
            drawn += 1
            if x_off + 24 > 360:
                y_start += 30
                x_off = row_n = 0
        else:
            out.append(((drawn % 25) * STEP, (drawn // 25) * STEP))
            drawn += 1
        row_n += 1
    return out, y_start


def pop_icons(score, game_state):
    """The figure names of the population row, in drawing order ([] when the
    snapshot cannot say): see `score_pop_count` above."""
    total = int(score["raw"].get("raw_population", 0))
    raw = getattr(game_state, "player_raw", None) or []
    colonies = getattr(game_state, "colonies_raw", None) or []
    player = score["player"]
    if total <= 0 or not 0 <= player < len(raw):
        return []
    try:
        races = {i: int(player_struct.parse(r).race)
                 for i, r in enumerate(raw)}
        by_race, taken = {}, 0
        for blob in colonies:
            col = colony_struct.parse(blob)
            if col.owner != player:
                continue
            owner_race = races.get(col.owner)
            for word in list(col.pop)[:col.n_pops]:
                name = colonyfigures.figure_for(word, owner_race, races)
                eff = colony_struct.pop_effective_player(word, col.owner)
                race = races.get(eff)
                if name is None or race is None or race >= 14:
                    continue
                if taken >= total:
                    break
                taken += 1
                by_race.setdefault(race, []).append(name)
    except (AttributeError, ValueError, TypeError, IndexError,
            struct.error):
        return []
    out = []
    for race in sorted(by_race):
        want = ((len(by_race[race]) * 160) // total + 5) // 10
        if len(out) + want > MAX_ICONS and want > 1:
            want = MAX_ICONS - len(out)
        pool = by_race[race]
        for j in range(max(0, want)):
            if len(out) >= MAX_ICONS:
                break
            out.append(pool[(j * len(pool)) // want])
    return out


def captured_icons(score):
    """The portrait names of the captured-colonists row, race-sorted
    (`score_captured_rule`)."""
    n = min(int(score["raw"].get("raw_captured_colonies", 0)), MAX_ICONS)
    races = [d["race"] for d in score.get("defeated", [])
             if 0 <= d["race"] < len(colonyfigures.RACE_KEYS)]
    if n <= 0 or not races:
        return []
    # weight DEFEATED_WEIGHT for each, shared evenly: the n portraits go
    # round the defeated races in order, then sorted like the qsort
    picks = sorted(races[i % len(races)] for i in range(n))
    return [colonyfigures.master_name(race=r, portrait=True) for r in picks]


# -- portraits of the eliminated players (SCORE.LBX) -------------------------
_cache = {}


def _decode(blob, palette):
    import numpy as np
    import pygame
    head = lbx.parse_header(blob, "score picture")
    pix = lbx.decode_frame(blob, head, 0)
    if pix is None:           # an undecodable frame or draw mode
        raise lbx.LbxError("score picture: frame will not decode")
    pal = np.zeros((256, 4), np.uint8)
    for i, (r, g, b) in palette.items():
        if 0 <= i < 256:
            pal[i] = (r, g, b, 255)
    pal[0] = (0, 0, 0, 0)
    arr = pal[np.frombuffer(bytes(pix), np.uint8)]
    surf = pygame.image.frombuffer(arr.tobytes(),
                                   (head.width, head.height), "RGBA")
    return surf.convert_alpha() if pygame.display.get_surface() else surf


def portrait(race, folder=None):
    """(portrait, frame) of race `race` as surfaces, either None when the
    extraction is absent or will not decode."""
    key = (folder, race)
    if key in _cache:
        return _cache[key]
    out = (None, None)
    if 0 <= race < STOCK_RACES:
        src = blobart.Source(REL, folder)
        try:
            pal_blob = src.read(f"score_{PALETTE_ENTRY}.bin")
            head = lbx.parse_header(pal_blob, "score palette")
            pal = lbx.read_palette(pal_blob, head.frame_count)
            pic = _decode(src.read(f"score_{PORTRAIT_FIRST + race}.bin"), pal)
            try:
                frame = _decode(src.read(f"score_{FRAME_ENTRY}.bin"), pal)
            except (OSError, lbx.LbxError, ValueError, struct.error,
                    TypeError):
                frame = None
            out = (pic, frame)
        except (OSError, lbx.LbxError, ValueError, struct.error,
                TypeError) as err:
            log.info("score portrait %d absent (%s) - run `%s`",
                     race, err, HOW)
    _cache[key] = out
    return out
