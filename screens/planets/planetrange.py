"""Planets In Range — the fifth toggle of the Planets list, work order 322 A3.

TRANSCRIPTION `range_filter` of `PLNTSUM::Planet_In_Range_Of_A_Colony_` (plntsum.cpp:387-392,
v2 :388-393), which asks `SHIPMOVE::Star_In_Extended_Range_Of_Player_` for
the planet's STAR (shipmove.cpp, orion2re 1.60 / v2):

    Star_In_Extended_Range_Of_Player_   :327-331  / v2 :363-367
        ext = (ship_range * 3 + 1) / 2              150 %, rounded
    Star_In_Range_Of_Player_            :340-355  / v2 :376-392
        the player, then every ALLY (treaty 2) by the same test
    Star_In_Range_Of_Player_Aux2_       :286-310  / v2 :322-347
        a colony at the star; or Aux1; or through the star's wormhole,
        when the player has visited the far end, Aux1 from there
    Star_In_Range_Of_Player_Aux1_       :249-277  / v2 :285-311
        any star S with a colony of the player, whose black-hole bitmap
        does not block the TARGET's index, within dist * 30 px

Every value it reads is on the wire: `s_player.ship_range` and `treaty`
(`core/structs/player.py`), each star's `x`, `y`, `has_colony`, `visited`,
`wormhole_star_id` and its black-hole bitmap (`core/structs/star.py`,
`black_hole_blocks`). Two details the shape of the code hides, both kept:
the bitmap is the COLONY star's, indexed by the TARGET star; and the
wormhole branch measures from the far end, and only when that end is
visited.

UNVERIFIED `range_filter_live`: the list with the toggle on, held against the
game's own rows (PLSM carries them), was never seen live — no live runs
(Data, 20 October 2026).
"""
from core.structs import player as player_struct
from core.structs import star as star_struct

#: "dist is scaled by 30 pixels per unit (30^2 = 900)" (shipmove.cpp:256-257,
#: v2 :292-293).
PIXELS_PER_PARSEC_SQ = 900
#: `treaty[i] == 2`, an alliance (shipmove.cpp:347, v2 :383).
TREATY_ALLIANCE = 2


def _bit(mask, player):
    """`(mask >> (player & 0x1F)) & 1`, as every helper here tests it."""
    return (int(mask) >> (int(player) & 0x1F)) & 1


def extended_range(ship_range):
    """`(ship_range * 3 + 1) / 2` in C's int16 arithmetic: the division
    truncates toward zero, so a negative range is not floored."""
    value = int(ship_range) * 3 + 1
    return int(value / 2) if value < 0 else value // 2


def aux1(stars, target, player, dist):
    """`Star_In_Range_Of_Player_Aux1_`: a colony star of `player` that
    sees `target` past every black hole, within `dist` parsecs."""
    if not stars or not 0 <= target < len(stars):
        return False
    limit = int(dist) * int(dist) * PIXELS_PER_PARSEC_SQ
    to = stars[target]
    for star in stars:
        if not _bit(star.has_colony, player):
            continue
        if star_struct.black_hole_blocks(star, target):
            continue
        dx, dy = int(to.x) - int(star.x), int(to.y) - int(star.y)
        if dx * dx + dy * dy <= limit:
            return True
    return False


def aux2(stars, target, player, dist):
    """`Star_In_Range_Of_Player_Aux2_`: a colony here, in range, or in
    range of the far end of this star's wormhole once it is visited."""
    star = stars[target]
    if _bit(star.has_colony, player):
        return True
    if aux1(stars, target, player, dist):
        return True
    far = int(star.wormhole_star_id)
    if far != -1 and 0 <= far < len(stars) and \
            _bit(stars[far].visited, player):
        return aux1(stars, far, player, dist)
    return False


def in_range(view, target, player, dist):
    """`Star_In_Range_Of_Player_`: the player, then each ally."""
    stars = view.stars
    if not 0 <= target < len(stars):
        return False
    if aux2(stars, target, player, dist):
        return True
    record = view.player(player)
    treaty = list(getattr(record, "treaty", None) or []) if record else []
    for other in range(min(len(view.players), player_struct.MAX_PLAYERS)):
        if other != player and other < len(treaty) and \
                treaty[other] == TREATY_ALLIANCE and \
                aux2(stars, target, other, dist):
            return True
    return False


def in_extended_range(view, target, player):
    """`Star_In_Extended_Range_Of_Player_` for star `target`. A player
    record the snapshot does not carry, or one without `ship_range`, is
    out of range of nothing it cannot prove: False."""
    record = view.player(player)
    ship_range = getattr(record, "ship_range", None) if record else None
    if ship_range is None:
        return False
    return in_range(view, target, player, extended_range(ship_range))


def star_in_range(view, target, player):
    """`in_extended_range`, once per star and player per snapshot: the
    answer is kept on `view`, which the screen builds once per snapshot
    (`planetrows.View`), so the frames between two snapshots — the list is
    refreshed every frame — never walk stars x colonies x allies again."""
    cache = view.__dict__.setdefault("_in_range", {})
    key = (int(target), int(player))
    if key not in cache:
        cache[key] = in_extended_range(view, int(target), int(player))
    return cache[key]
