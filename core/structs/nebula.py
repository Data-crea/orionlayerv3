"""s_nebula — VERIFIED spec (5 bytes).

Evidence (26 August 2026), two independent sources:

1. orion2re header `src/game/orion2.h`, struct s_nebula:
       int16_t x; int16_t y; int8_t type;
   The whole header sits inside `#pragma pack(push, 1)`, and
   `sizes.h` asserts sizeof(s_nebula) == 0x5 — so there is no
   alignment padding and the offsets are 0, 2, 4.

2. Live STATE_SNAPSHOT: nebula[0] = 76 01 aa 00 01 -> x=374,
   y=170, type=1. Both coordinates land inside the star field of
   the running galaxy; the one-byte-shifted reading gives -22015,
   which does not.

`type` is confirmed as 0..11 by orion2re itself: savegame.cpp and
netmox.cpp both reject a savegame where `type < 0 || type >= 12`,
and mainscr.cpp's Draw_Nebulae_() indexes its sprite table with
`type % 12`. There are exactly twelve nebula shapes.

Screen mapping is identical to the one used for stars — see
core/mapcoords.py.
"""
from core.structs import Spec

SIZE = 5

#: Number of distinct nebula shapes in the game (orion2re: type % 12).
TYPE_COUNT = 12

SPEC = Spec("s_nebula", SIZE, [
    ("x",    0, "i16"),
    ("y",    2, "i16"),
    ("type", 4, "i8"),
], verified=True)


def parse(raw):
    return SPEC.parse(raw)


def parse_all(raw_list):
    return SPEC.parse_all(raw_list)
