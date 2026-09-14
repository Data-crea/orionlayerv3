"""s_ship_data — VERIFIED spec (129 bytes), partial field set.

Verification (policy method 2, see core/structs/__init__.py):
orion2re's own `src/game/orion2.h` was compiled with its
`#pragma pack(push, 1)` intact and MAX_STARS = 1024 from consts.h,
then queried with offsetof/sizeof:

    sizeof(s_ship_data) = 129 == ORION2RE_STATIC_SIZE_ASSERT(
                                     s_ship_data, 0x81)  [sizes.h:27]
    owner    99   status 100   location 101   x 103   y 105

THE DESIGN BLOCK `d` (99 bytes) IS VERIFIED TOO, since 14 September
2026 (brief "Galaxy-map click reactions and space monsters", Stop 1),
by BOTH sources decision 23 asks for:

  1. the header compile: `pch.h` with `-fsyntax-only` and 48
     static_asserts on every member of `s_ship_design` and
     `s_ship_weapons` (orion2.h:1723-1750) — rc 0 — plus a copy with
     one offset deliberately wrong (`armor_damage` 124, and in a second
     run `s_ship_weapons.specials` 6) that failed as it must;
  2. a live probe on the `natives` fixture: all five monster records
     (Amoeba x2, Eel, Hydra, Guardian) decoded field for field and
     compared against `SHIP_CONFIG`'s templates (ship_config.cpp:51-139)
     — size, shield, drive, computer, armour, the five special bytes,
     every weapon's type, count, arc and mods, and `picture_num` all
     agree. The same records sit at offset 68828 of the fixture file,
     byte for byte.

    name 0 (16)  size 16  ship_type 17  shield_type 18  ftl_type 19
    speed 20  computer_type 21  armor_type 22  special_device_flags 23
    (5)  ship_weapon 28 (8 x 8)  picture_num 92  previous_owner 93
    cost 94  combat_speed 96  date_of_design 97

**THE DAMAGE FIELDS ARE NOT DECLARED, ON PURPOSE.** `armor_damage`
123, `structural_damage` 125 and the shield/drive/computer percentages
compiled where the header says, but every monster the probe could see
carried zero there — monsters are repaired in full every turn — and a
zero confirms no offset. Nothing reads them (Data's decision: the panel
shows maximum values), so they stay UNVERIFIED and absent from this
spec rather than present and unproven.

LOCATION IS ENCODED, not a plain star index. consts.h:22-25 and
HAROLD::Absolute_Location_ (harold.cpp:815):

    0             .. 9999   at star `location`
    10000         .. 19999  moving toward (location - 10000)
    20000         .. 29999  in a wormhole toward (location - 20000)

Use absolute_location() rather than the raw value.
"""
from core.structs import Spec

SIZE = 0x81                       # 129

#: consts.h:22-25
LOCATION_STEP = 10000
LOCATION_MOVING_OFFSET = LOCATION_STEP
LOCATION_WORMHOLE_OFFSET = LOCATION_STEP * 2
LOCATION_LIMIT = LOCATION_STEP * 3

#: s_ship_data.owner values above the player range
#: (orion2_consts.h:528, NONPLAYER_SHIP_TYPE).
OWNER_ANTARAN = 8
OWNER_GUARDIAN = 9
OWNER_AMOEBA = 10
OWNER_CRYSTAL = 11
OWNER_DRAGON = 12
OWNER_EEL = 13
OWNER_HYDRA = 14

#: STATUS values used on the map. 1 is in transit, which is what puts
#: a ship icon into stack_slot 5 (SHIPS::Build_Ship_Icons_).
STATUS_IN_TRANSIT = 1
STATUS_DESTROYED = 5

#: SHIPSTAK::Find_Ship_Stacks_ (shipstak.cpp:56) sets the skip flag for
#: every ship with status >= 3, and those ships get no node. The exact
#: meaning of 3 and 4 is not documented in the source; the threshold is
#: transcribed literally rather than interpreted.
STATUS_STACK_SKIP = 3

#: The monster owners, HAROLD::Race_Name_'s `owner + 5` range
#: (haccess.cpp:683). Antaran ships (8) are not monsters.
MONSTER_OWNERS = range(OWNER_GUARDIAN, OWNER_HYDRA + 1)

#: s_ship_design.ship_weapon: eight `s_ship_weapons` of 8 bytes from 28.
WEAPONS_OFFSET = 28
WEAPON_SLOTS = 8
WEAPON_SIZE = 8

#: special_device_flags is five bytes, read bit by bit LSB first
#: (struct_::Test_Bit_Field_, struct.cpp:20-26) — SPECIAL_COUNT 40 bits.
SPECIAL_BITS = 40

SPEC = Spec("s_ship_data", SIZE, [
    ("name",                  0, "str16"),
    ("size",                 16, "i8"),
    ("ship_type",            17, "i8"),
    ("shield_type",          18, "i8"),
    ("ftl_type",             19, "i8"),
    ("speed",                20, "i8"),
    ("computer_type",        21, "i8"),
    ("armor_type",           22, "i8"),
    ("special_device_flags", 23, "u8[5]"),
    ("picture_num",          92, "i8"),
    ("previous_owner",       93, "u8"),
    ("cost",                 94, "i16"),
    ("combat_speed",         96, "u8"),
    ("date_of_design",       97, "u16"),
    ("owner",    99, "i8"),
    ("status",  100, "i8"),
    ("location", 101, "i16"),
    ("x",       103, "i16"),
    ("y",       105, "i16"),
], verified=True)

#: s_ship_weapons (orion2.h:1723), the same two sources as the design.
WEAPON_SPEC = Spec("s_ship_weapons", WEAPON_SIZE, [
    ("type",          0, "i16"),
    ("count",         2, "i8"),
    ("current_count", 3, "i8"),
    ("firing_arc",    4, "i8"),
    ("specials",      5, "u16"),
    ("ammo",          7, "i8"),
], verified=True)


def is_monster(owner):
    return owner is not None and int(owner) in MONSTER_OWNERS


def weapons(view):
    """The mounted weapon slots, in slot order: those with a count.

    An empty slot is all zero (the templates initialise only the slots
    they name, ship_config.cpp:86-139), so `count` is what says a slot
    is used — the same test the fleet screen's weapon list makes
    before it prints a line (flt2.cpp, `count > 0`)."""
    out = []
    for slot in range(WEAPON_SLOTS):
        start = WEAPONS_OFFSET + slot * WEAPON_SIZE
        weapon = WEAPON_SPEC.parse(view.raw[start:start + WEAPON_SIZE])
        if weapon.count > 0:
            out.append(weapon)
    return out


def special_bits(view):
    """Indices of the set special-device bits, `Test_Bit_Field_` order."""
    flags = view.special_device_flags
    return [i for i in range(SPECIAL_BITS)
            if (flags[i >> 3] >> (i & 7)) & 1]


def absolute_location(location):
    """HAROLD::Absolute_Location_ — strip the moving/wormhole offset."""
    if LOCATION_MOVING_OFFSET <= location < LOCATION_WORMHOLE_OFFSET:
        return location - LOCATION_MOVING_OFFSET
    if LOCATION_WORMHOLE_OFFSET <= location < LOCATION_LIMIT:
        return location - LOCATION_WORMHOLE_OFFSET
    return location


def parse(raw):
    return SPEC.parse(raw)


def parse_all(raw_list):
    return SPEC.parse_all(raw_list)
