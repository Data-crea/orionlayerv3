"""UNVERIFIED starting-point specs — DO NOT use in production paths.

Specs live here until their offsets are confirmed. Confirmation
means one of:
  - numeric agreement with live data via tools/struct_probe.py, or
  - orion2re's own header compiled with its `#pragma pack(1)` and
    the resulting sizeof matching the assert in sizes.h.

Once confirmed, a spec moves into its own module with
verified=True and the evidence written into the docstring.

Already promoted out of this file:
  s_nebula      -> core/structs/nebula.py   (26 Aug 2026)
  s_planet_data -> core/structs/planet.py   (26 Aug 2026)
  s_player      -> core/structs/player.py   (26 Aug 2026, partial)

The old s_planet_data guess that used to sit here had `star_index`
at offset 0 and an invented `position` at 2. Both were wrong: the
real first member is `colony_index`. Kept as a note because it is
exactly the kind of plausible-looking guess this file exists to
quarantine.

Still needed, still unverified:
  s_colony      (361 B) — colony screen. Field list now FILLED from
                          the header (see doc/s_colony_offsets.md),
                          still one source, still quarantined.
  s_leader_data (59 B)  — officers screen
"""
from core.structs import Spec

# s_colony: 361 bytes, 50 members.
#
# The field list is no longer empty. It is not a guess either: every
# offset below was measured by compiling orion2re's own headers with
# their `#pragma pack(push, 1)` and printing offsetof per member, and
# the resulting sizeof matched ORION2RE_STATIC_SIZE_ASSERT(s_colony,
# 0x169) at sizes.h:24. The full write-up, including provenance of
# the headers that were compiled, is doc/s_colony_offsets.md.
#
# That is ONE source. verified=False, and this spec stays in the
# quarantine, because decision 23 wants two and the second — numeric
# agreement with live data through tools/struct_probe.py --spec — has
# not been taken yet. Filling the list is what this file is for: a
# documented starting point that production code does not touch.
#
# Source: orion2.h:487-537 (member order and types),
#         offsetof/sizeof from a throwaway TU, see the doc.
COLONY = Spec("s_colony", 361, [
    ("owner",                              0, "i8"),
    ("allocated_to",                       1, "i8"),
    ("planet",                             2, "i16"),
    ("officer",                            4, "i16"),
    ("outpost_flag",                       6, "u8"),
    ("morale",                             7, "i8"),
    ("pollution",                          8, "i16"),
    ("n_pops",                            10, "u8"),
    ("specialty",                         11, "i8"),
    ("pop",                               12, "u32[42]"),
    ("pop_roundoff",                     180, "i16[10]"),
    ("pop_growth",                       200, "i16[10]"),
    ("n_turns_existed",                  220, "i8"),
    ("food2_per_farmer",                 221, "i8"),
    ("industry_per_worker",              222, "i8"),
    ("research_per_scientist",           223, "i8"),
    ("max_farms",                        224, "u8"),
    ("max_population",                   225, "i8"),
    ("climate",                          226, "u8"),
    ("ground_strength",                  227, "i16"),
    ("space_strength",                   229, "i16"),
    ("production",                       231, "i16[4]"),
    ("maintenance",                      239, "u8[4]"),
    ("imports",                          243, "i16[4]"),
    ("n_industry_recyclers",             251, "i8"),
    ("food2_needed_for_our_empire",      252, "u8"),
    ("food2_needed_for_assimilated",     253, "u8"),
    ("food2_needed_for_conquered",       254, "u8"),
    ("food2_needed_for_natives",         255, "u8"),
    ("industry2_needed_for_our_empire",  256, "u8"),
    ("industry2_needed_for_androids",    257, "u8"),
    ("industry2_needed_for_assimilated", 258, "u8"),
    ("industry2_needed_for_conquered",   259, "u8"),
    ("food2_needed_for_empire",          260, "i8[8]"),
    ("industry2_needed_for_empire",      268, "i8[8]"),
    ("n_food_replicated",                276, "i8"),
    ("producing",                        277, "i16[7]"),
    ("just_produced",                    291, "i16"),
    ("production_spent",                 293, "i16"),
    ("n_industry_taxed",                 295, "i16"),
    ("auto_building",                    297, "u8"),
    ("production_surplus",               298, "i16"),
    ("bought_outright",                  300, "i16"),
    ("occupation_points",                302, "i8"),
    ("occupation_policy",                303, "i8"),
    ("military",                         304, "i16[2]"),
    ("tank_roundoff",                    308, "i8"),
    ("infantry_roundoff",                309, "i8"),
    ("buildings",                        310, "u8[49]"),
    ("last_turn_building_destroyed",     359, "u16"),
], verified=False,
   note="offsets from the header and its own size assert; second "
        "source (live probe against a known colony) still missing")

# Bit layout inside one pop[] word. NOT part of the byte layout, and
# not reachable by offsetof: the word's offset and width are fixed by
# the header, its contents are orion2re's own reading of what the
# original packs in there. Transcribed from src/game/pop.h:8-12,
# which carries getters AND setters, so this is the writing side
# rather than an inference from call sites. See the addition to
# decision 23 in doc/v3_fundament.md for why this needs its own
# confirmation even though the enclosing struct's offsets are solid.
#
# These are explicit masks on a uint32_t, not C bitfields.
POP_MASK_RACE = 0x0000000F           # pop.h:8   8 = android, 9 = native
POP_MASK_ORIGINAL_OWNER = 0x00000070  # pop.h:9   >> 4
POP_MASK_PROF = 0x00000180           # pop.h:10  >> 7, 0..2
POP_MASK_ASSIGNED = 0x00000200       # pop.h:11
POP_MASK_CONQUERED = 0x00000400      # pop.h:12

# pop.h:18-20. There is no fourth profession; 3 is not a valid value.
POP_PROF_FARMER = 0
POP_PROF_WORKER = 1
POP_PROF_SCIENTIST = 2
POP_PROF_MAX = 2

POP_RACE_ANDROID = 8                 # pop.h:14
POP_RACE_NATIVE = 9                  # pop.h:15


def pop_race(word):
    """POP::Get_Race (pop.h:23). UNVERIFIED against live data."""
    return word & POP_MASK_RACE


def pop_prof(word):
    """POP::Get_Prof (pop.h:39). UNVERIFIED against live data."""
    return (word & POP_MASK_PROF) >> 7


def pop_original_owner(word):
    """POP::Get_Original_Owner (pop.h:31). UNVERIFIED."""
    return (word & POP_MASK_ORIGINAL_OWNER) >> 4


def pop_is_assigned(word):
    """POP::Is_Assigned (pop.h:59). UNVERIFIED."""
    return bool(word & POP_MASK_ASSIGNED)


def pop_is_conquered(word):
    """POP::Is_Conquered (pop.h:71). UNVERIFIED."""
    return bool(word & POP_MASK_CONQUERED)

# s_leader_data: 59 bytes. Same situation.
LEADER = Spec("s_leader_data", 59, [], verified=False,
              note="confirm name string offset first, it is the "
                   "cheapest ground truth")
