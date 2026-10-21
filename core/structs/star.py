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
from core.structs import layout as _layout

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
    # work order 322 D: the system window's gate icons. BITMASKS over
    # players. `has_jumpgate` (set per owner, colcalc.cpp:358-360) has no
    # icon in the window — only the two after it are drawn — (`Player_Has_Artemis_Net_` / `_Dimensional_Portal_`,
    # harold.cpp:524-536), between has_stargate and is_stagepoint in the
    # header (orion2.h:2997-3001) and named in the engine's layout table
    # (ext_layout_table.inc:599-601), which places them on the wire
    ("has_jumpgate",   183, "u8"),
    ("has_artemis_net", 184, "u8"),
    ("has_dimensional_portal", 185, "u8"),
    ("is_stagepoint",  186, "u8"),
    # `int8_t officer_index[MAX_PLAYERS]` (orion2.h:3005): the colony
    # leader each player keeps at this star, -1 for none. Work order
    # 167. The header route asserts 187 (dev:tools/struct_header_check.py);
    # the second source is the leader records: every status-1 colony
    # leader on SAVE4 and the natives fixture sits at a star whose slot
    # FOR ITS OWN PLAYER names it back, and no other slot names anyone
    # (dev:tools/leader_check.py).
    ("officer_index",  187, "i8[8]"),
    # the two arrays below were read through helpers at fixed offsets
    # until work order 243; as spec fields the engine's layout finds them
    ("planet_index",   195, "i16[5]"),
    ("relocate_ship_to", 205, "i16[8]"),
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
    return list(view.planet_index)


#: `relocate_ship_to[MAX_PLAYERS]`, orion2.h:3007 — one int16 per
#: player, -1 for "no relocation". Immediately after `planet_index[5]`
#: at 195, which this file already carried as verified: 195 + 10 = 205.
#:
#: **VERIFIED BY THE HEADER ROUTE** (decision 23's second route), not
#: by a hand count. The whole struct was laid out from
#: `src/game/orion2.h`'s field order with `MAX_PLAYERS 8` and
#: `BITMAP(MAX_STARS 1024)`, and the result reproduces every offset
#: this spec already held as verified — name 0, x 15, y 17, size 19,
#: owner 20, pict_type 21, spectral_class 22, system_special 159,
#: wormhole_star_id 160, blockaded 162, visited 171, colonize_player
#: 175, planet_index 195 — and the total size 234. Twelve agreements
#: and the size; the thirteenth value is this one.
#:
#: `screens/galaxy_map/maplines.py` recorded this offset as "not
#: verified" and omitted the relocation lines because of it. That
#: reason is now spent.
RELOCATE_OFFSET = 205
RELOCATE_SLOTS = 8


def relocation_target(view, player_num):
    """The star this system's ships are relocated to, or None.

    `HACCESS::Star_Has_Relocation_` is `relocate_ship_to[player] != -1`
    and `HACCESS::Relocation_` returns the value (haccess.cpp:113-119),
    so the two are one lookup here and None carries "no relocation"
    rather than a magic -1 the caller has to remember.
    """
    slots = view.relocate_ship_to
    if not 0 <= int(player_num) < len(slots):
        return None
    target = slots[int(player_num)]
    return None if target < 0 else target


def is_black_hole(view):
    return view.spectral_class == CLASS_BLACK_HOLE


def visited_by(view, player_num):
    """True when `player_num` has explored this system."""
    return bool(view.visited & (1 << (player_num & 0x1F)))


def parse(raw):
    return SPEC.parse(raw)


def parse_all(raw_list):
    return SPEC.parse_all(raw_list)


#: `int8_t black_hole_blocks[BITMAP(MAX_STARS)]` (orion2.h:2985, v2 :2982):
#: bit n set means a black hole lies between this star and star n.
#: Work order 322 A3 (`screens/planets/planetrange.py`). NOT a spec field:
#: parsed with every record it would unpack 128 bytes per star on every
#: snapshot for a test only the Planets list's range toggle makes. TWO
#: SOURCES: offsetof 31, 128 bytes, over the 1.60 headers (the compile of
#: work order 322), and this spec's own verified `system_special` at
#: 159 = 23 + 8 + 128, which a bitmap of another place or width would
#: have moved. An engine with the LAYOUT says its own place and width
#: (decision 97).
BLACK_HOLE_BLOCKS_OFFSET = 31
BLACK_HOLE_BLOCKS_SIZE = 128


def black_hole_blocks(view, star_index):
    """`struct_::Test_Bit_Field_(star->black_hole_blocks, star_index)`
    (struct.cpp v2 :20-25: byte index >> 3, bit index & 7): True when a
    black hole blocks the line from this star to `star_index`."""
    if _layout.current() is None:
        # no LAYOUT: the engine the offset was read against (1.60)
        at, size = BLACK_HOLE_BLOCKS_OFFSET, BLACK_HOLE_BLOCKS_SIZE
    else:
        member = _layout.member("s_star_data", "black_hole_blocks")
        if member is None:
            return False        # a layout without the member: unknown,
            #                     read as "not blocked", as a spec field
            #                     the engine lacks reads None
        at, size = member.offset, member.size
    index = int(star_index)
    if not 0 <= index < size * 8:
        return False
    raw = view.raw
    byte = at + (index >> 3)
    return byte < len(raw) and bool((raw[byte] >> (index & 7)) & 1)
