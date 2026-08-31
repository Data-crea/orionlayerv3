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

THE OFFSETS ARE VERIFIED; THE MEANINGS BELOW ARE NOT ALL. Decision 23
distinguishes the two: compiling the header fixes where a field sits
and how wide it is, and says nothing about what its values mean. Each
line below therefore says where it comes from. Checked live against a
loaded savegame on 31 August 2026 (54 stars, 270 planet slots, 21
colonies, stardate 3508.5).

  planet_type    LIVE. PLANET_TYPE in orion2_consts.h:400. **0 is
                 PLANET_TYPE_NOT_USED0 and marks an EMPTY SLOT, not a
                 planet.** The array is always 5 per star, so of 270
                 slots only 158 were real: 17 asteroid (1), 31 gas
                 giant (2), 110 planet (3). Filter on this before
                 reading anything else.

  colony_index   LIVE, with a trap. -1 does mean uncolonised, and
                 among the 158 real planets it was exactly that: 138
                 at -1 and 20 carrying a colony index, each appearing
                 once, each pointing back at the colony that names
                 that planet. But **all 112 empty slots hold 0**, not
                 -1, because an unused record is zeroed field by field
                 (homegen.cpp:598-615) and 0 is a legal colony index.
                 Testing `colony_index != -1` to mean "colonised"
                 therefore finds 112 phantom colonies, all of them
                 apparently colony 0. Test `planet_type != 0` first.
                 mapgen.cpp:565 writes a third value, -2, for a planet
                 dropped during generation; none survived into this
                 savegame, but nothing here guarantees that.

  star_index     HEADER ONLY. Not checked against a named system yet.
  orbit          HEADER ONLY. Slot 0..4 within the system.

  size           RANGE seen live (0..4, all five present), direction
                 NOT checked. PLANET_SIZE says Tiny=0 .. Huge=4.
  gravity_class  RANGE seen live (0..2, all three present), direction
                 NOT checked. PLANET_GRAVITY: LowG=0, Normal=1,
                 HeavyG=2.
  climate        RANGE seen live (0..9, all ten present), direction
                 NOT checked. PLANET_CLIMATE: Toxic=0 .. Gaia=9.
  mineral_class  RANGE seen live (0..4, all five present), direction
                 NOT checked. MINERAL_RESOURCE: UltraPoor=0 ..
                 UltraRich=4.

  An observed range agreeing with a declared range is weak evidence:
  it rules out a wrong offset, and it cannot tell Toxic from Gaia,
  because a reversed enum produces the same range. Reading one
  planet's description off the game's own screen would settle all
  four at once, and has not been done.

  max_farms      LIVE, real data (0, 2, 4, 5, 7, 10 across 158
                 planets). This is the genuine per-planet farm cap —
                 NOT to be confused with s_colony.max_farms, which is
                 a 0/255 flag written by Colony_Calculation_.
  max_population VESTIGIAL. 0 on all 270 slots in a loaded savegame.
                 The population cap the game actually uses is the
                 table MOX::_planet_max_population[] = {5,10,15,20,25}
                 indexed by size (mox.cpp:796), read directly at
                 colcalc.cpp:1283 and invasion.cpp:318/924. This
                 member is only ever written to 0 (homegen.cpp:615),
                 restored from a save (savegame.cpp:390) or set on the
                 network path (ericnet.cpp:443). Do not use it.
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
