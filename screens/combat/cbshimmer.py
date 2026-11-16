"""A fighter group's shimmer — work order 398 (gap 13 of work order 397's
engine-against-overlay list).

TRANSCRIPTION `fighter_shimmer` (`CMBTMIS::Draw_Fighter_`, cmbtmis.cpp:
1482-1535): on every pass whose `_ship_frame % 3` is 0 each fighter picture
of a group gets its own offset, `Random_(3) - 2` for x and then for y — the
game's `Random_` returns 1 to n (random.cpp:25-39), so -1 .. +1 px, not
-2 .. 0 — drawn from a seed of its own, `clock() + i + missile_idx`
(:1517-1523), the game's seed put back after; on the other two passes the
offsets are 0 (`rand_x`, `rand_y` start at 0 in each call and are set only on
the third pass). Only the main view draws it (`combat_view_type == 0`; the
fighter beam's own draw, type 1, does not).

HD STATE `shimmer_clock`: the original's `clock()` is the process's CPU time
in microseconds, which no state carries; HD seeds with its `_ship_frame` (the
counter the pass test reads), so the offsets are the same at the same frame
and a check can assert the rule. `Random_`'s own generator is transcribed.
HD draws a group as one picture (the `ordnance_stack` deviation of
[combat.field], see `cbdraw`), so only the first fighter's (`i` = 0) offset
is drawn here; `offsets` gives any `i`.
UNVERIFIED `fighter_shimmer_live`: not seen in a running battle.
"""

#: `Random_`'s generator (random.cpp:25-39)
MULTIPLIER, INCREMENT = 0x41C64E6D, 0x3039
MASK = 0xFFFFFFFF
#: the shimmer is drawn on every third pass
EVERY = 3


def random_n(seed, n):
    """`game_random::Random(n)` from `seed`: (1..n, the seed after). A draw
    at or above `n * (0xFFFFFFFF / n)` is thrown away, so every value is
    equally likely."""
    quotient = MASK // n
    limit = n * quotient
    while True:
        seed = (seed * MULTIPLIER + INCREMENT) & MASK
        if seed < limit:
            return seed // quotient + 1, seed


def offsets(ship_frame, index, i=0):
    """The (x, y) offset in px of fighter `i` of group `index` on the pass
    `ship_frame`: 0, 0 except on every third pass."""
    if int(ship_frame) % EVERY:
        return 0, 0
    seed = (int(ship_frame) + int(i) + int(index)) & MASK
    x, seed = random_n(seed, 3)
    y, _seed = random_n(seed, 3)
    return x - 2, y - 2
