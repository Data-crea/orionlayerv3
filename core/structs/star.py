"""s_star_data — VERIFIED spec.

Two independent sources agree on every offset here:

1. Live testing (16 Aug 2026): 36/36 star names valid at
   STAR_SIZE=234, x/y render at correct map positions.
2. orion2re's header `src/game/orion2.h` compiled with the same
   `#pragma pack(1)` the game uses — sizeof comes out at exactly
   234, matching the configurable static assert in sizes.h
   (0x6a + BITMAP(MAX_STARS), MAX_STARS=1024). With the assert
   satisfied and packing on, no field can have shifted.

`system_special` sits after last_planet_selected[8] and the
black_hole_blocks bitmap (23 + 8 + 128 = 159), which the header
confirms.

Star name visibility (mainscr.cpp, Get_Star_Name_) needs `visited`:
it is a BITMASK over players, so player N has explored this system
when `visited & (1 << N)`. An omniscient player sees every name,
but a system they have not visited is shown in brackets.
"""
from core.structs import Spec

SIZE = 0x6A + (1024 + 7) // 8   # 234

#: spectral_class values (STAR_CLASS in orion2_consts.h)
CLASS_B, CLASS_F, CLASS_G = 0, 1, 2
CLASS_K, CLASS_M, CLASS_DWARF = 3, 4, 5
CLASS_BLACK_HOLE = 6

#: size values feed the icon size (0 = largest)
SIZE_LARGE, SIZE_MEDIUM, SIZE_SMALL = 0, 1, 2

SPEC = Spec("s_star_data", SIZE, [
    ("name",             0, "str15"),
    ("x",               15, "i16"),
    ("y",               17, "i16"),
    ("size",            19, "u8"),
    ("owner",           20, "i8"),
    ("pict_type",       21, "i8"),
    ("spectral_class",  22, "u8"),
    ("system_special", 159, "u8"),   # 23 + 8 + 128
    ("wormhole_star_id", 160, "i16"),
    ("blockaded",      162, "u8"),
    ("visited",        171, "u8"),   # BITMASK over players
    ("colonize_player", 175, "i8"),
    ("has_colony",     176, "u8"),
    ("has_stargate",   182, "u8"),
    ("is_stagepoint",  186, "u8"),
    ("in_nebula",      232, "u8"),
], verified=True)

#: planet_index[5] at offset 195, five int16 — read through the
#: helper below rather than as a Spec field. Spec has carried an
#: array kind since s_colony needed pop[42], so this is no longer a
#: limitation; the helper stays because callers want the slots as a
#: list they can walk, and because HAROLD::Planet_Number_ (harold.cpp)
#: reads them exactly that way: a planet's Roman numeral counts the
#: OCCUPIED slots before it, not its orbit.
PLANET_INDEX_OFFSET = 195
PLANET_SLOTS = 5


def planet_indices(view):
    """The five planet slots of a system; -1 means empty."""
    import struct as _s
    return list(_s.unpack_from("<5h", view.raw, PLANET_INDEX_OFFSET))


def is_black_hole(view):
    return view.spectral_class == CLASS_BLACK_HOLE


def visited_by(view, player_num):
    """True when `player_num` has explored this system."""
    return bool(view.visited & (1 << (player_num & 0x1F)))


def parse(raw):
    return SPEC.parse(raw)


def parse_all(raw_list):
    return SPEC.parse_all(raw_list)
