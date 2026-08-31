"""s_planet_data — VERIFIED spec (18 bytes).

Offsets taken from orion2re's own header (`src/game/orion2.h`,
struct s_planet_data) and confirmed by compiling that header with
`#pragma pack(1)`: sizeof comes out at exactly 18, matching the
`ORION2RE_STATIC_SIZE_ASSERT(s_planet_data, 0x12)` in sizes.h.
With packing on and the assert satisfied there is no room for
padding, so every field offset is fixed.

CORRECTION to the earlier guess in unverified.py, which had
`star_index` at offset 0 and an invented `position` at 2. The real
first field is `colony_index`; `star_index` is second. Anything
built on the old guess read the colony index as a star index.

Field meanings worth knowing:
  colony_index   -1 when the planet is uncolonised
  star_index     which system the planet belongs to
  orbit          slot 0..4 within the system
  planet_type    see PLANET_TYPE in orion2_consts.h (asteroids,
                 gas giant, normal planet ...)
  size           PLANET_SIZE: Tiny=0 .. Huge=4
  gravity_class  PLANET_GRAVITY: LowG=0, Normal=1, HeavyG=2
  climate        PLANET_CLIMATE: Toxic=0 .. Gaia=9
  mineral_class  MINERAL_RESOURCE: UltraPoor=0 .. UltraRich=4
"""
from core.structs import Spec

SIZE = 18

SPEC = Spec("s_planet_data", SIZE, [
    ("colony_index",              0, "i16"),
    ("star_index",                2, "i16"),
    ("orbit",                     4, "i8"),
    ("planet_type",               5, "i8"),
    ("size",                      6, "i8"),
    ("gravity_class",             7, "i8"),
    ("group",                     8, "i8"),
    ("climate",                   9, "i8"),
    ("climate_bg_type",          10, "i8"),
    ("mineral_class",            11, "i8"),
    ("food_per_farmer",          12, "i8"),
    ("n_terraforms",             13, "i8"),
    ("max_farms",                14, "u8"),
    ("max_population",           15, "i8"),
    ("planet_special",           16, "i8"),
    ("environmental_alterations", 17, "i8"),
], verified=True)


def parse(raw):
    return SPEC.parse(raw)


def parse_all(raw_list):
    return SPEC.parse_all(raw_list)
