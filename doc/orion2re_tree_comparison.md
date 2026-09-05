# Three orion2re trees, compared

Read 5 September 2026. This document reports and decides nothing.
It changed no file in `~/orion2re` and copied nothing between trees;
every comparison below was made against a read-only export.

**One home.** Everything else that needs these facts points here
(fundament, "a name table copied into three files"). If this file is
re-run, replace it rather than writing a second one.

| | Tree | Where |
|---|---|---|
| **A** | Data's working tree, our patches applied | `~/orion2re` |
| **B** | Joes' base the patches were applied to | **exists** — see below |
| **C** | the new download | `~/orion2re-main-neu` |

---

## Step 0 — what these trees are

### B exists, and in the strongest possible form

`~/orion2re` is a real git working tree. Its HEAD is **`cf4d9617`**
("1.50 Backport: mixed race penalty"), `origin` is
`https://github.com/mrjoes/orion2re.git`, the stash is empty and
there is no second branch. Our patches are UNCOMMITTED working-tree
modifications on top of that commit.

So B is not a zip to be hunted for: it is `git archive cf4d9617`
inside A, byte-exact, and that is how it was produced for this
comparison (624 files, exported read-only to a scratch directory).
Nothing had to be reconstructed by subtracting known patches from A,
which the brief rightly forbids.

### C is a newer upstream state, and the version literals cannot say so

- **No `.git` directory.** No hash, no history.
- `src/version.h`: `ENGINE_VERSION[] = "1.60.0"`
- `src/game/consts.h`: `GAME_VERSION_LABEL[] = "Version 1.60.0"`

Both literals are **identical to B's**. On those two numbers alone, C
and B are indistinguishable — which is exactly the failure mode
decision 36 and `tools/version_check.py` were built against, arriving
from the other side: the check reads both literals and would report
this update as "no change".

The discriminator is one line further down the same file:

    GAME_BUILD_DATE[] = "May 31 2026"   (B)
    GAME_BUILD_DATE[] = "Aug 15 2026"   (C)

and step 2 settles it beyond doubt: 474 files differ, 243 exist only
in C, and whole subsystems are new (`src/crypto/`, `src/lua/`,
`documentation/`, `src/config/config_snapshot.*`,
`src/game/aidata_config.cpp`). **C is later than B by a wide margin.**

> **Open item for `tools/version_check.py`:** it reads
> `ENGINE_VERSION` and `GAME_VERSION_LABEL` and nothing else, so it
> cannot see this update. `GAME_BUILD_DATE` is the third literal and
> is the one that moved. Not fixed here — this document reports.

---

## Step 1 — A against C, and how it is honestly presented

A raw `diff -rq A C` yields 474 changed files. Presenting that as
"one row per deviation" would be a table in which about 469 rows are
Joes' work and five are ours, with nothing distinguishing them. The
categorisation the brief asks for only means anything against B, so
it is given there — and the A-against-C question that actually
matters is answered as a merge test, below.

### Our divergence: A against B, categorised — the complete list

| File | Hunks | Category |
|---|---|---|
| `CMakeLists.txt` | 1 | ifdef-guarded — `option(ORION2RE_EXT …)`, adds `src/ext/*.cpp` only when ON. Documented in `doc/ext_api_dokumentation_v3.md` |
| `src/game/fields.cpp` | 2 | ifdef-guarded — `ext::Tick()` and the `g_pending_field` early exit |
| `src/game/mox2.cpp` | 3 | ifdef-guarded — `ext::Tick()`, `ext::Init()`, `ext::Shutdown()` |
| `src/game/platform.cpp` | 4 | ifdef-guarded — the include, the `g_hide_window` guard on `SDL_ShowWindow`, **and two from `doc/ext_inject_click.patch`** (suppress the mouse sync while injected input is unconsumed; clear the flag when the queue is pumped) |
| `src/game/racesel.cpp` | 4 | 3 ifdef-guarded (synthetic screen ID 50 for Custom Race) + **1 UNGUARDED: `_old_race = static_cast<int16_t>(i);`** — documented patch, `doc/orion2re_open_fixes.md` item 5, a crash fix (`racesel.lbx [entry 138]`). Unguarded on purpose: guarding it would leave the crash in a plain build |

**85 inserted lines, 14 hunks, 5 files. Nothing deleted, nothing
moved.**

Untracked in A, and none of it ours except the first:

| Path | What |
|---|---|
| `src/ext/` | the Extension API — ours |
| `mox.set` | 553 bytes, 13 August — the game's own settings file, written at runtime |
| `src.zip` | 1.6 MB, 5 September — a snapshot somebody took |
| `racesel_custom_screen_id.patch` | the racesel hunks as a patch file, lying loose in the tree |

> **Open item:** `src.zip` and `racesel_custom_screen_id.patch` sit
> in a source tree and are neither Joes' nor a build product. Not
> ours to delete — reported so the next reader does not mistake them
> for upstream.

### The line that decides the analysis's boundary section

**`src/ext/` does not exist in C.** `diff -rq` reports `Nur in
orion2re: ext`, and A's own git reports it as untracked at
`cf4d9617`. So the claim in `doc/colsum_design_analysis.md` §3 —
*"`src/ext/` is our own directory, untracked in Joes' tree"* — is
**CONFIRMED**, against B and against C independently.

### The hunk count in files Joes owns — the analysis was WRONG

The analysis says, in §13 and §16, that Joes' tree "stays at the one
`platform.cpp` hunk". That is not true as written, and the table
above is the correction: **five files, fourteen hunks.**

Where the wrong number came from is worth keeping, because the
sentence it was derived from is correct. `doc/ext_inject_click.patch`
says that OF THE THREE FILES THAT PATCH TOUCHES, only `platform.cpp`
is Joes' — the other two are `src/ext/`. That is a statement about
one patch, and it was read as a statement about the whole tree. The
four other files diverged earlier, when the Extension API was first
integrated, and they are documented in
`doc/ext_api_dokumentation_v3.md` — the analysis simply did not count
them.

The claim that survives, and it is the one that matters, is
different and stronger: **thirteen of the fourteen hunks are inside
`#ifdef ORION2RE_EXT`**, so a build without the flag is Joes' code.
The fourteenth is the documented crash fix.

`doc/ext_ship_icon_owner.patch` is reconciled: it is marked OPTIONAL
in its own header, it is **not applied** (`git diff` shows no change
to `mainscr.cpp` or the ship-icon path), and it therefore contributes
zero hunks.

### Does our patch still apply to C? — measured, dry run only

    cd ~/orion2re-main-neu && patch -p1 --dry-run < our_patches.diff

| File | Result |
|---|---|
| `CMakeLists.txt` | applies (offset +314) |
| `src/game/fields.cpp` | applies (offset +12) |
| `src/game/mox2.cpp` | applies (offset +2, +26) |
| `src/game/platform.cpp` | **2 of 4 hunks FAIL** |
| `src/game/racesel.cpp` | **4 of 4 hunks FAIL** |

---

## Step 2 — B against C: what Joes changed

**474 files differ, 243 exist only in C, 59 only in B.** This is
upstream progress and is not ours to categorise. What is ours is the
effect on things this tree cites.

### The struct layer — the serious part

| Header | Change |
|---|---|
| `pop.h` | a closing-brace comment. **No semantic change**; every mask and sentinel is identical |
| `version.h` | indentation and a namespace comment. Literals unchanged |
| `consts.h` | `GAME_BUILD_DATE` May 31 -> Aug 15; new `MAX_COLONY_POPULATION 42`, `MAX_FREIGHTED_SETTLERS 1000`, `ORIGINAL_MAX_FREIGHTED_SETTLERS 25`, `GAME_SETTINGS_FILENAME` |
| `orion2.h` | 136 lines. In `s_colony`: `pop[42]` -> `pop[MAX_COLONY_POPULATION]` (same 42), and **`food2_per_farmer` and `industry_per_worker` change `int8_t` -> `uint8_t`** |
| `sizes.h` | **`s_ship_data` 0x81 -> 0x87**, **`s_antaran` 0x42 -> 0x44**, and `s_player` becomes CONFIGURABLE: `0xf0e` or `0x2d86` depending on `MAX_FREIGHTED_SETTLERS` |

**`s_colony` keeps its size (0x169 = 361) and every offset.** Our
spec's offsets survive; two of its FIELD KINDS do not. `i8` against
`u8` is the `imports` sign trap (open fix 7) in a second place, and
it is invisible until a value reaches 128.

**And the wire format breaks.** `core/game_state.py` walks the
snapshot with hardcoded record sizes (`SHIP_SIZE = 0x81`,
`ANTARAN_SIZE = 0x42`, lines 16-25). Both are wrong for C, both sit
BEFORE the ship icons in the stream, and the parser is sequential —
so against a binary built from C, everything after the ships block
is read at the wrong offset: colonies, planets, nebulas, leaders,
antarans, icons. `PROTO_VERSION` stays 1 and announces nothing.

> **This is a hard blocker on updating to C**, and it is not a
> merge conflict — it is a client change. Two constants and two
> struct specs (`core/structs/ship.py`, and `player.py` if the
> configurable build is used) must move in the same step.

### Files this tree cites by line number — all of them moved

`doc/v3_orion2re_index.md`, `doc/s_colony_offsets.md`,
`doc/pop_order_reading.md`, `doc/colsum_design_analysis.md` and every
docstring in `screens/colony_summary/` cite these:

| File | B lines | C lines | differing |
|---|---|---|---|
| `colsum.cpp` | 1264 | 1445 | 361 |
| `coldraw.cpp` | 849 | 829 | 1274 |
| `colmove.cpp` | 587 | 586 | 171 |
| `colcalc.cpp` | 3900 | 3956 | 1060 |
| `colcalc_main.cpp` | 1602 | 1613 | 525 |
| `colcalc_base.cpp` | 186 | 184 | 88 |
| `settler.cpp` | 352 | 351 | 67 |
| `colony.cpp` | 2374 | 2319 | 227 |
| `colony_main.cpp` | 1295 | 1251 | 300 |
| `colonize.cpp` | 398 | 405 | 41 |
| `invasion.cpp` | 938 | 957 | 1445 |
| `aidudes.cpp` | 1600 | 1616 | 160 |
| `fields.cpp` | 3211 | 3154 | 557 |
| `textbox.cpp` | 492 | 484 | 72 |
| `bomb.cpp` | 326 | 326 | 2 |
| `gendraw.cpp` | 265 | 265 | 2 |

**Every citation in this tree is anchored to `cf4d9617` and would
have to be re-anchored on an update.** They are not wrong today —
they are correct against the binary that is running — which is why
each document names the version it was read against. `coldraw.cpp`
and `invasion.cpp` are the two to distrust most: more differing lines
than the file has, i.e. wholesale rewriting or reformatting.

---

## Step 3 — the intersection: files Joes changed that we also patched

**All five. The intersection is complete, and it is the point of
this task.**

| File | Our hunks | Upstream | Same lines? |
|---|---|---|---|
| `CMakeLists.txt` | 1, appended at the end | file grew by ~314 lines | **No** — ours applies cleanly |
| `src/game/fields.cpp` | 2 | 557 lines differ | **No** — applies at +12 |
| `src/game/mox2.cpp` | 3 | changed | **No** — applies at +2 / +26 |
| `src/game/platform.cpp` | 4 | changed | **YES, on two of four** |
| `src/game/racesel.cpp` | 4 | 165 lines differ ignoring indentation | **YES, on all four** |

### `platform.cpp` — the collision is semantic, not cosmetic

Our pointer fix works by returning early from
`Sync_Mouse_State_From_SDL_`, so its `Enqueue_Mouse_Input_Event_`
cannot coalesce over the injected button-up. In C that tail has been
rewritten:

    B:  Enqueue_Mouse_Input_Event_(mapped_x, mapped_y, mapped_buttons);

    C:  const bool overlay_captures_mouse =
            debug_overlay::Handle_Mouse_Position_(mapped_x, mapped_y);
        Forward_Game_Mouse_State_(mapped_x, mapped_y, mapped_buttons,
                                  overlay_captures_mouse);

The enqueue moved behind a new wrapper and a new consumer of the
mouse position appeared (`debug_overlay`). **The fix's reasoning has
to be re-derived against the new function, not just re-anchored**,
and the symptom of getting it wrong is the one the patch file already
names: the population move goes quiet again. The second failing hunk
is the `g_hide_window` guard, where `SDL_ShowWindow` simply moved.

### `racesel.cpp` — mechanical failure, semantic change underneath

All four hunks fail because the file was re-indented into a namespace
block (`int16_t _old_race;` at column 0 in B, indented in C), so no
context line matches. Underneath that, 165 lines really did change:
a new `#include "raceopt.h"`, a `LAST_RACE_FILENAME` constant, and
`_race_specials[14]` is now statically initialised instead of filled
at runtime.

**The crash fix is still needed.** C's `_old_race` sites are the same
as B's, shifted — Joes has not fixed `racesel.lbx [entry 138]`
upstream, so `doc/orion2re_open_fixes.md` item 5 stays open and its
one line has to be re-applied by hand at the new location.

---

## Unexplained

**Zero rows.** Every deviation of A from B is ifdef-guarded and
documented, or is the documented crash fix. The two loose files in
A's root (`src.zip`, `racesel_custom_screen_id.patch`) and the
`version_check.py` blind spot are named above as open items rather
than left in this category, because none of them is an unexplained
code change.

---

## What this does NOT say

No merge was performed, nothing was copied, and no recommendation
about updating is made here. The three facts Data needs for that
decision are: the intersection is complete (all five files);
`platform.cpp` needs its fix re-derived rather than re-anchored; and
the update is blocked on the client side until
`core/game_state.py`'s record sizes and `core/structs/ship.py` follow
`s_ship_data` from 0x81 to 0x87.
