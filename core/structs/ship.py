"""s_ship_data — VERIFIED spec (129 bytes), partial field set.

Verification (policy method 2, see core/structs/__init__.py):
orion2re's own `src/game/orion2.h` was compiled with its
`#pragma pack(push, 1)` intact and MAX_STARS = 1024 from consts.h,
then queried with offsetof/sizeof:

    sizeof(s_ship_data) = 129 == ORION2RE_STATIC_SIZE_ASSERT(
                                     s_ship_data, 0x81)  [sizes.h:27]
    owner    99   status 100   location 101   x 103   y 105

The struct opens with `struct s_ship_design d;` — 99 bytes of design
data that nothing on the galaxy map needs. Only the five fields after
it are declared here; adding more means re-running the same probe,
not eyeballing orion2.h.

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

SPEC = Spec("s_ship_data", SIZE, [
    ("owner",    99, "i8"),
    ("status",  100, "i8"),
    ("location", 101, "i16"),
    ("x",       103, "i16"),
    ("y",       105, "i16"),
], verified=True)


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
