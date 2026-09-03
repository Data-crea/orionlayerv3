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

**`outpost_flag` (offset 6) is VERIFIED — 3 September 2026.** It was
the header alone until then, which fixes where the byte sits and how
wide it is and cannot say the byte MEANS outpost (decision 23). The
first thing that wanted to read it was a FILTER, and a filter is a
claim about the meaning: the original builds its colony list on two
conditions, the colony's `owner` and a zero `outpost_flag`
(`Build_Global_Colony_List_`, colxport.cpp:91-99, and `N_Colonies_`
counts with the same pair at colxport.cpp:67).

**Source two, the game's own screen, and it is discriminating rather
than merely consistent.** A save at stardate 3502.4 with 55 colonies:
colony 54 sits on planet 239, the game itself labels that planet
"Yian I (Elerian Outpost)" and shows 0/4 population, and the Colonies
screen does not list it. Twelve colony records carry the local
player as owner; the screen lists **eleven**. The one record the two
counts differ by is the one with the flag set, and it is the one the
game calls an outpost.

That is the query the earlier save could not answer. Its 21 colonies
all carried 0, so the filter removed nothing and the count agreed
with "offset 6 is the outpost flag" and with "offset 6 is a byte that
is zero everywhere" equally well — consistent, and not a second
source. `tools/struct_probe.py colonies --outposts` prints either
verdict and says which it is; against this save it reports
ANSWERABLE and 12 against 11.

**One write site, which is what makes the flag mean one thing.**
`COLONIZE::Make_New_Colony_Or_Outpost_` sets it, in the branch that
runs when the new colony is not a colony: `outpost_flag = 1` with
`n_pops = 0` beside it (colonize.cpp:381-382), which is also where
the observed 0 population comes from. Nothing else in the tree
assigns it — every other mention is a read — except
`savegame.cpp:309`, which restores it from disk. So a set flag has
exactly one origin and the byte cannot be carrying a second meaning
somewhere else.

**`pop_growth` (offset 200) is VERIFIED — 3 September 2026.** The
colony summary sums all ten words (colsum.cpp:1179-1182) and prints
the total; for Sadak I the original's own scan box read **+63k** and
the same sum off the wire is 63. The "k" is a unit, not a label —
MOO2 counts population in thousands — so the number, its sign and its
scale all agree with the original's own print of the same colony.
Read in the second `--live --native` side-by-side, with both halves
on the same sort key and the same ten rows.

**`morale` (offset 7) is NOT verified, and the obstacle is an input
capability rather than the data.** The comparison needs the original's
scan box pointed at a colony with non-zero morale. In that save
exactly one of the local player's listed colonies has one — Draconis
I at -4 — and `_g_colony_n` moves on HOVER (colsum.cpp:880-890),
which the Extension API cannot inject. Every click that lands on that
row does something else: the name field leaves for SCREEN_COLONY, the
producing text opens the build popup, a job column moves population.
The game window is hidden while the API is on (platform.cpp:1379), so
it cannot be hovered by hand either. What would settle it is a save in
which the colony the original is already scanning has non-zero morale.

WHAT IS NOT VERIFIED: the bit layout inside a `pop[]` word. The
header fixes the word's offset and width and can say nothing about
its contents, which is the distinction decision 23 carries. Of the
five masks below, only `MASK_PROF` has a second source — Sol II
decodes 2 farmers and shows two symbols in the screen's FARMERS
column, while Ixion II and Sol I decode none and show that column
empty. The rest are a transcription of `src/game/pop.h:8-12`, which
carries getters and setters and is therefore the writing side, but a
transcription all the same.

**The low nibble is NOT a race, and pop.h's name for it is wrong.**
`COLONY::Get_Effective_Pop_Player_` (colony.cpp:1257) reads
`pop & 0x0F` and returns it as a PLAYER index; only 8 and 9 are
special, and those resolve to the colony's own `owner`. The race is a
SECOND lookup on top of that: `Colony_Pop_Anim_` (colony.cpp:1268)
takes the player index and reads `MOX::_player[idx].race` at
colony.cpp:1275 to pick the sprite. So `POP::MASK_RACE` names the
mask after the thing two steps away from it, and that name must not
be carried into this spec — a field called `race` here would be read
as a race index by the next person, and it would be wrong for every
multi-player colony.

Both steps are reachable on the wire: this nibble, and
`s_player.race` at offset 37 in the verified `player.py` spec.

**VERIFIED for 0..7 on 1 September 2026** — second source, live,
and it does not merely support the player reading, it REFUTES the
race one. `tools/struct_probe.py colonies --pop-nibble` against the
reference save (stardate 3508.5, 21 colonies, 131 live colonists):

  owner 0: nibble 0 x39     owner 3: nibble 3 x28
  owner 1: nibble 1 x22     owner 4: nibble 4 x17
  owner 2: nibble 2 x25     no value outside 0..9; 751 unused
                            slots past n_pops all zero

Five distinct owners, every colonist carrying its own colony's, zero
mismatches. What makes it decisive rather than suggestive is the
second query: `s_player.race` for those five players is 5, 2, 3, 4, 0
(CyberToller, Darlok, Elerian, Gnolam, Alkari) — **not one player's
race equals its own index.** Player 0 plays race 5, so under the
"race" reading his colonists would carry nibble 5; they carry 0.
Player 4 plays race 0 and carries 4. The two readings predict
different numbers for every player in this save, and the data picks
the player one every time.

The earlier pass had already recorded the weaker half — 598 colonists
across two samples, nibble never above 9 (`doc/s_colony_offsets.md`).
That is consistent with both readings. The owner match is what
separates them, and it was never checked until now.

**Still NOT verified: the sentinels.** 8, 9 and anything >= 14 are
absent from this save, so `Get_Effective_Pop_Player_`'s branch at
colony.cpp:1261 remains transcription only. That needs a savegame
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

#: pop.h:8 calls this MASK_RACE. It is a PLAYER INDEX, and the name
#: is not carried over — see the docstring. Three meanings share the
#: nibble, all read straight out of the C++:
#:   0..7   a player index. MAX_PLAYERS is 8 (consts.h:7), and
#:          `Get_Effective_Pop_Player_` returns the value unchanged
#:          (colony.cpp:1265).
#:   8, 9   android and native. NOT player indices: both resolve to
#:          the colony's own owner (colony.cpp:1261-1263).
#:   >= 14  compared DIRECTLY against a race in `Sum_Colonists_`
#:          (colony.cpp:2129), on a branch that bypasses the player
#:          lookup entirely. What those values index was not
#:          established here; what matters for a reader of this file
#:          is that the nibble is not bounded by 9, so a value of 14
#:          or 15 in live data is a fourth state and not corruption.
POP_MASK_PLAYER_INDEX = 0x0000000F
#: consts.h:7, MAX_PLAYERS. The highest value that is a player index.
POP_PLAYER_INDEX_MAX = 7
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

#: The two nibble values that are not player indices (pop.h:14-15).
#: Named without "RACE" on purpose: they are sentinels inside the
#: player-index nibble, and both resolve to the colony's owner.
POP_ANDROID = 8
POP_NATIVE = 9
#: colony.cpp:2129. At or above this the nibble is matched against a
#: race index directly, without the player lookup.
POP_DIRECT_RACE_MIN = 14


def pop_player_index(word):
    """POP::Get_Race (pop.h:23) — misnamed there; a player index.

    Raw nibble, not the effective player: 8 and 9 come back as 8 and
    9. `COLONY::Get_Effective_Pop_Player_` (colony.cpp:1257) is what
    maps those two to the colony's owner, and it needs the colony,
    which this function does not have. Mask NOT confirmed live.
    """
    return word & POP_MASK_PLAYER_INDEX


def pop_effective_player(word, colony_owner):
    """COLONY::Get_Effective_Pop_Player_ (colony.cpp:1257), transcribed.

    The whole of the first step: the nibble, except that android (8)
    and native (9) belong to the colony's owner. Feed the result to
    `s_player.race` for the second step, which is what
    `Colony_Pop_Anim_` does at colony.cpp:1275.
    """
    index = pop_player_index(word)
    if index in (POP_ANDROID, POP_NATIVE):
        return colony_owner
    return index


def pop_prof(word):
    """POP::Get_Prof (pop.h:39). Confirmed live, see docstring."""
    return (word & POP_MASK_PROF) >> 7


def pop_original_owner(word):
    """POP::Get_Original_Owner (pop.h:31). A player index too — the
    setter masks it to 0x07 (pop.h:36). Mask NOT confirmed live."""
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
