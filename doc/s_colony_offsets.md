# s_colony — offsets from the header, Phase A

## Result, up front

Measured, by compiling orion2re's own header (see "What was done"):

```
sizeof(s_colony) = 361
```

Asserted, in orion2re's own tree:

```cpp
// src/game/sizes.h:24
ORION2RE_STATIC_SIZE_ASSERT(s_colony, 0x169);
```

`0x169` = 361. **The two agree**, so the offsets in the table below
are fixed by the header and the rest of this file is worth reading.
Had they disagreed, that disagreement would have been the whole
report: a mismatch means the packing or the header version is not
what it appears to be, and every offset taken under it would be
worthless.

### Provenance of the measurement

| | |
|---|---|
| orion2re commit | `cf4d9617` (2026-08-12) |
| `src/game/orion2.h` | `git status --short` clean — not locally modified |
| `src/game/sizes.h` | `git status --short` clean — not locally modified |

Both measurement sources are at their committed state, so the commit
hash describes the measurement completely. This is checked rather
than assumed: the orion2re working tree *does* carry local changes
(the `ORION2RE_EXT` work in `CMakeLists.txt`, `fields.cpp`,
`mox2.cpp`, `platform.cpp`, `racescrn.cpp`, `racesel.cpp` and
`src/ext/`), and had either of the two files above been among them,
the hash alone would have named a header that was not the one
compiled.

`python tools/version_check.py` — OK, all three agree at 1.60.0
(`core/config.ORION2RE_VERSION`, `src/version.h ENGINE_VERSION`,
`src/game/consts.h VERSION_LABEL`). `python tools/smoke_test.py` —
50 checks green. Neither is affected by this file, which touches no
production path; both were run because a measurement taken against a
tree nobody checked is a measurement of an unknown tree.

---

`core/structs/unverified.py` carries `COLONY` with a **deliberately
empty field list**: the size (361 bytes) was known, the field order
was known from `orion2.h`, and no offset had been checked. This file
is the first of the two sources decision 23 requires. It is **not**
permission to fill that list.

## What was done

`struct s_colony` was transcribed from `src/game/orion2.h:487-537`,
50 members. A throwaway translation unit was written in a scratch
directory outside the orion2re tree, including orion2re's own headers
(`compat.h`, `types.h`, `settler.h`, `consts.h`, `orion2_consts.h`,
`orion2.h`) so that the packing in effect is `orion2.h`'s own
`#pragma pack(push, 1)` at line 1 and nothing of ours. It prints
`offsetof` and `sizeof` per member. **Nothing was written into the
orion2re tree**; the only include paths were `-I.../src/game` and
`-I.../src`.

Two details worth recording, because both were first attempted the
wrong way. `orion2.h` is not self-contained — it needs `MAX_PLANETS`,
`MAX_STARS`, `MAX_PLAYERS` and the `undefined` typedefs, and it uses
`__cdecl`, which is MSVC-only. The fix is orion2re's own `compat.h`
(`#define __cdecl` at compat.h:19), not a `-D__cdecl=` of ours, and
`compat.h` also supplies `GUID`; a hand-written GUID stub was written
first and then deleted as redundant. Using the project's own compat
layer is what makes this a measurement of orion2re's headers rather
than of our reconstruction of them.

## No padding anywhere

The 50 members are **contiguous**: every offset
equals the previous offset plus the previous size, and the last
member ends at exactly 361, so the packing left no padding anywhere
and every offset below is fixed by the header alone.

`ECON_COUNT` is 4 and `BUILDING_COUNT` is 49 (orion2_consts.h:123,
:62), which is what makes `production`, `maintenance`, `imports` and
`buildings` the sizes they are.

## The table

★ marks the fields the colony screen's bar design actually consumes.

| Offset | Size | Type | Name | Source |
|---:|---:|---|---|---|
| 0 | 1 | `int8_t` | `owner` ★ | orion2.h:488 |
| 1 | 1 | `int8_t` | `allocated_to` | orion2.h:489 |
| 2 | 2 | `int16_t` | `planet` ★ | orion2.h:490 |
| 4 | 2 | `int16_t` | `officer` | orion2.h:491 |
| 6 | 1 | `uint8_t` | `outpost_flag` | orion2.h:492 |
| 7 | 1 | `int8_t` | `morale` | orion2.h:493 |
| 8 | 2 | `int16_t` | `pollution` | orion2.h:494 |
| 10 | 1 | `uint8_t` | `n_pops` ★ | orion2.h:495 |
| 11 | 1 | `int8_t` | `specialty` | orion2.h:496 |
| 12 | 168 | `uint32_t[42]` | `pop` ★ | orion2.h:497 |
| 180 | 20 | `int16_t[10]` | `pop_roundoff` | orion2.h:498 |
| 200 | 20 | `int16_t[10]` | `pop_growth` | orion2.h:499 |
| 220 | 1 | `int8_t` | `n_turns_existed` | orion2.h:500 |
| 221 | 1 | `int8_t` | `food2_per_farmer` | orion2.h:501 |
| 222 | 1 | `int8_t` | `industry_per_worker` | orion2.h:502 |
| 223 | 1 | `int8_t` | `research_per_scientist` | orion2.h:503 |
| 224 | 1 | `uint8_t` | `max_farms` ★ | orion2.h:504 |
| 225 | 1 | `int8_t` | `max_population` | orion2.h:505 |
| 226 | 1 | `uint8_t` | `climate` | orion2.h:506 |
| 227 | 2 | `int16_t` | `ground_strength` | orion2.h:507 |
| 229 | 2 | `int16_t` | `space_strength` | orion2.h:508 |
| 231 | 8 | `int16_t[ECON_COUNT]` | `production` | orion2.h:509 |
| 239 | 4 | `uint8_t[ECON_COUNT]` | `maintenance` | orion2.h:510 |
| 243 | 8 | `int16_t[ECON_COUNT]` | `imports` | orion2.h:511 |
| 251 | 1 | `int8_t` | `n_industry_recyclers` | orion2.h:512 |
| 252 | 1 | `uint8_t` | `food2_needed_for_our_empire` | orion2.h:513 |
| 253 | 1 | `uint8_t` | `food2_needed_for_assimilated` | orion2.h:514 |
| 254 | 1 | `uint8_t` | `food2_needed_for_conquered` | orion2.h:515 |
| 255 | 1 | `uint8_t` | `food2_needed_for_natives` | orion2.h:516 |
| 256 | 1 | `uint8_t` | `industry2_needed_for_our_empire` | orion2.h:517 |
| 257 | 1 | `uint8_t` | `industry2_needed_for_androids` | orion2.h:518 |
| 258 | 1 | `uint8_t` | `industry2_needed_for_assimilated` | orion2.h:519 |
| 259 | 1 | `uint8_t` | `industry2_needed_for_conquered` | orion2.h:520 |
| 260 | 8 | `int8_t[8]` | `food2_needed_for_empire` | orion2.h:521 |
| 268 | 8 | `int8_t[8]` | `industry2_needed_for_empire` | orion2.h:522 |
| 276 | 1 | `int8_t` | `n_food_replicated` | orion2.h:523 |
| 277 | 14 | `int16_t[7]` | `producing` | orion2.h:524 |
| 291 | 2 | `int16_t` | `just_produced` | orion2.h:525 |
| 293 | 2 | `int16_t` | `production_spent` | orion2.h:526 |
| 295 | 2 | `int16_t` | `n_industry_taxed` | orion2.h:527 |
| 297 | 1 | `uint8_t` | `auto_building` | orion2.h:528 |
| 298 | 2 | `int16_t` | `production_surplus` | orion2.h:529 |
| 300 | 2 | `int16_t` | `bought_outright` | orion2.h:530 |
| 302 | 1 | `int8_t` | `occupation_points` | orion2.h:531 |
| 303 | 1 | `int8_t` | `occupation_policy` | orion2.h:532 |
| 304 | 4 | `int16_t[2]` | `military` | orion2.h:533 |
| 308 | 1 | `int8_t` | `tank_roundoff` | orion2.h:534 |
| 309 | 1 | `int8_t` | `infantry_roundoff` | orion2.h:535 |
| 310 | 49 | `uint8_t[BUILDING_COUNT]` | `buildings` | orion2.h:536 |
| 359 | 2 | `uint16_t` | `last_turn_building_destroyed` | orion2.h:537 |

## The pop word — the ★ field that is not a plain integer

`pop[42]` is 42 `uint32_t`, one per colonist, and the fields the HD
drag needs are bits inside it, not members of `s_colony`. The layout
is **not** inferred from the call sites that read it: `src/game/pop.h`
carries getters *and setters* for every field, which is the writing
side.

| Bits | Mask | Meaning | Source |
|---|---|---|---|
| 0-3 | `0x0000000F` | race index; 8 = android, 9 = native | pop.h:7, :14-15 |
| 4-6 | `0x00000070` | original owner | pop.h:8, :31 |
| 7-8 | `0x00000180` | profession: 0 farmer, 1 worker, 2 scientist | pop.h:9, :17-21 |
| 9 | `0x00000200` | assigned to a job | pop.h:10, :60 |
| 10 | `0x00000400` | conquered | pop.h:11, :72 |

`COLMOVE::Pops_Identical_` (colmove.cpp:106) groups on
`(pop1 ^ pop2) & 0x180` — the profession bits — plus
`COLONY::Pop_To_Pop_State_` (colony.cpp:1240), which reads the race
nibble and maps 9 to 3, 8 to 4 and everything else to 2. That is the
grouping an HD drag has to reproduce to translate into native clicks.

The `MASK_ORIGINAL_OWNER` field at bits 4-6 does not appear in any of
the call sites read for this pass; it was found only by reading
`pop.h` itself. Recorded because it is there, not because its use is
understood.

## Unwelcome findings

**There is no star index in `s_colony`.** The priority list asked for
"star/planet index"; the struct has `planet` (offset 2) and nothing
else. The star is reached indirectly, `MOX::_planet[colony->planet]
.star_index` — the pattern used at aileader.cpp:93, aibuild.cpp:549
and aidata.cpp:298. A colony screen that wants the system name needs
`s_planet_data` as well, which is already verified in
`core/structs/planet.py`.

**Population is not one number.** `n_pops` (offset 10, `uint8_t`) is
the count of entries in `pop[]`. MOO2 displays fractional population,
and `pop_roundoff[10]` and `pop_growth[10]` at offsets 180 and 200
are per-race arrays, not per-colonist ones — 10 entries against
`pop[]`'s 42. What they index was not established in this pass and is
not guessed here.

**`morale` is `int8_t`, `climate` is `uint8_t`.** Signedness varies
member by member through the whole struct and is transcribed
verbatim above. Reading `morale` as unsigned would turn a penalty
into a large bonus, silently.

## Phase B, first pass — bit positions checked, meanings not

A live decode was run through the new `tools/struct_probe.py --spec`
mode. **It is not the second source.** It checks that the bits sit
where `pop.h` says, and it cannot check what they mean, because
nothing here was compared against a value a human read off the
screen.

### Provenance of the live measurement

A measurement without the state it was taken in is the unknown-tree
problem again, so: two different games were sampled, and the state
changed underneath the run.

| | |
|---|---|
| First sample | stardate 3500.0, 99 stars, 50 colonies, 467 pops |
| | freshly generated galaxy, **before the first turn** |
| Second sample | stardate 3508.5, 54 stars, 21 colonies, 131 pops |
| | a *different* galaxy, with turns played |

**Why the state changed:** the maintainer loaded a savegame roughly
50 turns old while the first pass was running. Different galaxy, no
mystery — recorded here because a reader who finds two incompatible
sets of numbers in one document deserves the reason and not just the
fact. The second was confirmed stable across three consecutive
snapshots before anything was read from it. Numbers from the two
samples are not comparable and are never compared below. The first
galaxy no longer exists and cannot be re-examined.

That the loader ran is itself checkable rather than assumed:
`n_turns_existed` reads 85, 85, 85, 85, 85, 79, 73, 70, 69, 68, 67,
54, 54, 49, 28, 24, 0, 17, 14, 11, 5 across the 21 colonies — a
founding order no freshly generated galaxy produces.

### What held

Across both samples, every colonist word decoded within range:
professions 0..2 without exception, race nibble never above 9,
`original_owner` never above 7, `pop[]` entries beyond `n_pops`
uniformly zero, and the per-profession counts summing exactly to
`n_pops`. That is consistent with `MASK_PROF` and `MASK_RACE` sitting
where `pop.h` puts them — a wrong shift would scatter values across
the whole range, and 598 colonists did not produce one.

**`planet` at offset 2 is confirmed independently.** For every
colony, `MOX::_planet[colony.planet].colony_index` points back at
that colony's own index — 50/50 in the first sample, 20/21 in the
second. The check runs against `core/structs/planet.py`, which is
verified, so this is agreement between two specs on live data rather
than a spec agreeing with itself.

### The profession mapping is NOT swapped

Raised as the likeliest suspicion, because summing to `n_pops` and
staying inside 0..2 both survive any permutation of the three jobs.
Settled from the source instead, and it took five places that agree:

1. `orion2_consts.h:119-121` — `ECON_FOOD=0`, `ECON_INDUSTRY=1`,
   `ECON_RESEARCH=2`.
2. `colmove.cpp:550` — `Give_Colonist_New_Job_` writes the job with
   `POP::Set_Prof(pop, (POP::e_prof)new_job)`, a direct cast from an
   `ECON_*` value. The two enumerations therefore share their
   numbering by construction, not by coincidence.
3. `colony.cpp:878-887` — `Job_String_(0)` returns FARMER, `(1)`
   WORKER, anything else SCIENTIST.
4. `colony.cpp:929` — that function is called with
   `(pop_data >> 7) & 3`, the same shift as `POP::Get_Prof`.
5. `colsum.cpp:313-329` — `Add_Fields_Pop_For_` walks `i = 0,1,2`
   into columns at x 101, 236 and 378, passing `i` as `job_filter`;
   `coldraw.cpp:392` then tests `job_filter == ECON_FOOD` for the
   farm shadows. The leftmost column is food.

`pop.h`'s `PROF_FARMER=0, PROF_WORKER=1, PROF_SCIENTIST=2` agrees
with all five. **No swap.** This was derived from the mapping to
columns and labels, not from the order the enum happens to be
written in.

### max_farms is real, and its name is misleading

The Phase A table offered two explanations for `max_farms` reading
255 or 0 and never anything else: an unpopulated field, or a
mislabelled offset. **Both were wrong**, and so was a third
(computed during turn processing) — the second sample has turns
played and the values are unchanged.

`COLCALC::Colony_Calculation_` (colcalc.cpp:691-695):

```cpp
int16_t food_per_farmer = Colony_Food2_Per_Farmer_(colony, colony->owner, nullptr);
if (food_per_farmer != 0) {
    colony->max_farms = -1;
} else {
    colony->max_farms = 0;
}
```

The member is `uint8_t`, so `-1` stores as **255**, which is exactly
the observed value. The reader confirms the intent
(`coldraw.cpp:393`): `if (max_farms != 0xff)` — draw shadow farmers
up to the cap, and `0xff` means *do not*. So the offset is correct
and the field is written constantly; it is a two-state flag — 255
"no farm cap", 0 "this colony cannot farm" — and **not** a farm
capacity. The real per-planet number is `s_planet_data.max_farms`,
which is a different field in a different struct.

This also explains why the obvious cross-check fails.
`ericnet.cpp:162` does copy the planet's value into the colony's,
but `Colony_Calculation_` runs afterwards and overwrites it, so
`colony.max_farms == planet[colony.planet].max_farms` held 0 out of
50 and 0 out of 21. That was the spec being right and the
expectation being wrong.

**`max_population` (offset 225) is vestigial in both structs.**
Phase B's first pass explained it as "only ever restored from a
save", which the loaded savegame then refuted: it is 0 in all 21
colonies *there too*, and `savegame.cpp:322` demonstrably does read
it. Chasing that down settled it, and the answer clears `orion2.h`
rather than accusing it.

The cap the game actually uses is a table, not a struct member:
`MOX::_planet_max_population[PLANET_SIZE_COUNT] = {5, 10, 15, 20, 25}`
(mox.cpp:796), indexed by planet size and read directly at
colcalc.cpp:1283 and invasion.cpp:318 and :924. The member is written
only to 0 (homegen.cpp:615), restored from a save, or set on the
network path (ericnet.cpp:443). `s_planet_data.max_population` is 0
on all 270 planet slots for the same reason, and that spec is
`verified=True` — a verified offset holding a value nobody uses,
which is exactly the distinction decision 23 gained. Neither member
should be read.

Worth recording as corroboration rather than as the finding:
`savegame.cpp:305-330` restores `s_colony` **field by field in the
header's own order**, with matching widths — a second, hand-written
expression of the same member sequence. It does not confirm any
name, but a loader written against a different order would not
round-trip.

### One finding that belongs to planet.py

Raised in the first pass as unexplained and now settled. Of 270
planet slots, **112 are not planets at all**: the array is always 5
per star, and an unused slot is a record zeroed field by field
(homegen.cpp:598-615), which `PLANET_TYPE_NOT_USED0 = 0`
(orion2_consts.h:401) marks. Every one of those 112 carries
`colony_index == 0` — because 0 is what zeroing writes, and 0 is
also a legal colony index.

Among the 158 real planets the docstring's claim holds exactly: 138
at -1, and 20 carrying a colony index that appears once and points
back at the colony naming that planet. The hazard is the filter:
`colony_index != -1` as a test for "colonised" finds 112 phantom
colonies, all of them apparently colony 0, and nothing about the
result looks wrong. `planet_type != 0` has to come first.

`core/structs/planet.py`'s docstring has been rewritten accordingly —
offsets and `verified=True` untouched, since this was never a layout
question. Each meaning now says whether it was seen live or is header
only, and the four enum directions (climate, size, gravity, minerals)
are marked as ranges confirmed and directions **not** confirmed: an
observed range matching a declared range rules out a wrong offset and
cannot tell Toxic from Gaia.

## Second source: four fields confirmed, one claim still open

Ground truth: a screenshot of the original colony summary, savegame
at 85 turns, stardate 3508.5 — the same state the Phase B pass ran
against. Seven colonies of the local player, named on screen; the
population symbols were deliberately *not* counted, so nothing below
leans on them.

| Check | Result |
|---|---|
| `owner` (0) | **7/7.** Exactly seven colonies carry player 0, and their names are the seven on screen |
| `planet` (2) | **7/7**, implied by the above — the name comes from colony → planet → star |
| `n_pops` (10) | **39 = 39** against the empire sidebar's Population, and **3 = 3** for Ixion II against "Population (3/5)" |
| `max_farms` (224) | **7/7** against "No Farming": 0 for Kif II, Malus I, Sol III, Sol IV; 255 for Ixion II, Sol I, Sol II |
| `MASK_PROF` | **3/3.** Sol II decodes 2 farmers and the screen shows two farmer symbols; Ixion II and Sol I decode 0 and both show an empty farmer column |
| `MASK_RACE` | **not confirmed** — see below |

`n_pops` is the strongest of these, because `sys.cpp:1444` prints the
description as `colony->n_pops` over the computed maximum, so "(3/5)"
is that member rendered directly, and 39 is an independent agreement
with a different field in a different struct (`s_player`).

`max_farms` behaves exactly as the Phase B reading of
`Colony_Calculation_` predicted: 0 where the game refuses farming,
255 where it does not. Seven for seven, with the split falling where
the screen says and not where a coincidence would put it.

### A correction to the naming, found by this check

The first attempt mapped colony → planet → star and appended the
Roman numeral of `planet.orbit`. That produced Kif II and Malus I
correctly and was **off by one** for Ixion and Sol. The rule is not
the orbit: `HAROLD::Planet_Number_` (harold.cpp) walks
`star->planet_index[5]` and counts only the **occupied** slots before
the planet, so an empty slot earlier in the system shifts every
numeral after it. With that fixed, all seven names matched. Two of
the seven `max_farms` comparisons had been failing purely because
they were compared against the wrong colony.

### MASK_PROF confirmed twice; MASK_RACE untouched by this savegame

The ground truth first offered Sol II as "the one colony showing two
races". The maintainer withdrew that on a second look: the two
distinguishable symbols stand in the **FARMERS column**, and Sol II
is the only row with anything in that column at all — the other six
show workers only. The colour difference is the profession, not a
race. Recorded here as what it was: a reading of a screen that
carried an assumption inside it, corrected before it cost anything.

So `MASK_PROF` has two independent confirmations rather than one —
the decode (Sol II 2 farmers, Ixion II and Sol I none) and the column
the symbols sit in.

`MASK_RACE` is untouched. Sol II decodes 19 colonists all of race 0
with `original_owner` 0 throughout, and every colony of the empire is
single-race. There is no android, no native and no conquered
population anywhere in this savegame, so nothing here could confirm
the mask or refute it. The check had no ground to stand on, which is
different from failing.

## Promoted — with the masks kept separate

`COLONY` moved to `core/structs/colony.py` with `verified=True` on
31 August 2026. The evidence is in that module's docstring: which
colony confirmed which field, in which savegame.

**The byte layout and the bit layout were promoted on different
evidence, and the module says so.** The four struct fields have two
independent sources. Of the five masks inside a `pop[]` word, only
`MASK_PROF` does; the rest remain a transcription of `pop.h`, which
is exactly the distinction decision 23 gained.

What `MASK_RACE` still needs is not another turn — the race mix does
not change across one — but **a different savegame**: a colony
holding androids, natives or a conquered population. One such record
settles it the way the farmer column settled `MASK_PROF`.

A second data point across a turn remains worth having for `n_pops`,
which currently agrees twice within one state.

Superseded by the section above: four fields now have their second
source. The list below still stands, because one claim does not.

- `COLONY` in `core/structs/unverified.py` stays empty.
- No `core/structs/colony.py`.
- Nothing in `screens/colony_summary/` reads a field.
- No field is marked verified.

This file is documentation. It is not a spec.

### Note for Phase B

`tools/struct_probe.py` prints its int16 column view only for records
of 64 bytes or less. `s_colony` is 361, so a live probe currently
yields the hex dump and the ASCII runs and nothing aligned to the
table above. That limit needs lifting before the second source can be
taken — deliberately not changed in this pass, which touched no
production path.

The cheapest ground truth to check first, in this order: `owner` at 0
against the known player number; `n_pops` at 10 against the
population the game prints; `max_farms` at 224 against the farm cap;
then the first `pop[]` word at 12, whose low nibble must be a race
index and whose bits 7-8 must be 0, 1 or 2.
