"""s_colony — VERIFIED spec (361 bytes, 50 members).

Two sources, as decision 23 requires, and they are independent of
each other.

**Source one, the header.** `struct s_colony` transcribed from
orion2re's `src/game/orion2.h:487-537` and measured by compiling that
header with its own `#pragma pack(push, 1)`: `offsetof` per member,
and a `sizeof` of exactly 361 matching
`ORION2RE_STATIC_SIZE_ASSERT(s_colony, 0x169)` at sizes.h:24. The 50
members are contiguous — every offset is the previous offset plus the
previous size, and the last ends on 361 — so the packing left no
padding and no offset is free to move. Full write-up, including the
provenance of the headers compiled, in `doc/s_colony_offsets.md`.

**Source two, the original's own screen.** Checked 31 August 2026
against a screenshot of the colony summary from a savegame at 85
turns (stardate 3508.5, 21 colonies, local player 0, seven of them
his):

  owner       7/7. Exactly seven colonies carry player 0, and their
              names — Ixion II, Kif II, Malus I, Sol I, Sol II,
              Sol III, Sol IV — are the seven the screen lists.
  planet      7/7, implied by the above: the name is only reachable
              as colony -> planet -> star, so a wrong `planet` would
              have produced wrong names.
  n_pops      39 against the empire sidebar's Population, which comes
              from a different field in a different struct
              (`s_player`); and 3 against Ixion II's "Population
              (3/5)", which `sys.cpp:1444` prints as `colony->n_pops`
              directly.
  max_farms   7/7 against "No Farming": 0 for Kif II, Malus I,
              Sol III and Sol IV, 255 for Ixion II, Sol I and Sol II.

`max_farms` is NOT a farm capacity despite the name. `Colony_
Calculation_` writes -1 into a `uint8_t` when the planet can farm and
0 when it cannot (colcalc.cpp:691-695), and `coldraw.cpp:393` reads
0xff as "no cap". The real per-planet number is
`s_planet_data.max_farms`. `max_population` (225) is vestigial in
this struct and in `s_planet_data`; see `core/structs/planet.py` for
what the game actually computes.

WHAT IS NOT VERIFIED: the bit layout inside a `pop[]` word. The
header fixes the word's offset and width and can say nothing about
its contents, which is the distinction decision 23 carries. Of the
five masks below, only `MASK_PROF` has a second source — Sol II
decodes 2 farmers and shows two symbols in the screen's FARMERS
column, while Ixion II and Sol I decode none and show that column
empty. The rest are a transcription of `src/game/pop.h:8-12`, which
carries getters and setters and is therefore the writing side, but a
transcription all the same.

`MASK_RACE` in particular is neither confirmed nor refuted: every
colonist in that savegame is race 0 with `original_owner` 0, so no
data there could decide it. What settles it is a different savegame
holding androids, natives or a conquered population — not another
turn, since the race mix does not change across one.
"""
from core.structs import Spec

SIZE = 361

SPEC = Spec("s_colony", SIZE, [
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
], verified=True)

# ── Bit layout inside one pop[] word ──────────────────────────────
# Transcribed from src/game/pop.h:8-12. These are explicit masks on a
# uint32_t, not C bitfields. Only MASK_PROF has a second source; see
# the docstring above before relying on any of the others.
POP_MASK_RACE = 0x0000000F            # pop.h:8   8 = android, 9 = native
POP_MASK_ORIGINAL_OWNER = 0x00000070  # pop.h:9   >> 4
POP_MASK_PROF = 0x00000180            # pop.h:10  >> 7, 0..2. VERIFIED
POP_MASK_ASSIGNED = 0x00000200        # pop.h:11
POP_MASK_CONQUERED = 0x00000400       # pop.h:12

# pop.h:18-20. There is no fourth profession; 3 is not a valid value.
# The numbering is shared with ECON_FOOD/INDUSTRY/RESEARCH by
# construction: Give_Colonist_New_Job_ casts an ECON_* value straight
# to e_prof (colmove.cpp:550).
POP_PROF_FARMER = 0
POP_PROF_WORKER = 1
POP_PROF_SCIENTIST = 2
POP_PROF_MAX = 2

POP_RACE_ANDROID = 8                  # pop.h:14
POP_RACE_NATIVE = 9                   # pop.h:15


def pop_race(word):
    """POP::Get_Race (pop.h:23). Mask NOT confirmed live."""
    return word & POP_MASK_RACE


def pop_prof(word):
    """POP::Get_Prof (pop.h:39). Confirmed live, see docstring."""
    return (word & POP_MASK_PROF) >> 7


def pop_original_owner(word):
    """POP::Get_Original_Owner (pop.h:31). Mask NOT confirmed live."""
    return (word & POP_MASK_ORIGINAL_OWNER) >> 4


def pop_is_assigned(word):
    """POP::Is_Assigned (pop.h:59). Mask NOT confirmed live."""
    return bool(word & POP_MASK_ASSIGNED)


def pop_is_conquered(word):
    """POP::Is_Conquered (pop.h:71). Mask NOT confirmed live."""
    return bool(word & POP_MASK_CONQUERED)


def parse(raw):
    return SPEC.parse(raw)


def parse_all(raw_list):
    return SPEC.parse_all(raw_list)
