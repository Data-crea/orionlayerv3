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

## second source still missing: live probe

Everything above comes from **one** source: orion2re's headers,
compiled. Decision 23 and the "two independent sources" principle
both want a second, independent one — numeric agreement with live
data via `tools/struct_probe.py` against a known colony. Until that
exists:

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
