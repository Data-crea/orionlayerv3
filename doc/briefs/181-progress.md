# Work order 181 — progress

Unattended run, 27 September 2026, base `7fa43b4` (= origin/main, 371
checks). orion2re `orionlayer-local` at the start: `9ab84230` (fix 34), with
its three untracked files (`mox.set`, `racesel_custom_screen_id.patch`,
`src.zip`), left alone. Evidence root:
`~/orionlayer-fixtures/evidence/work_order_181/`.

## Before part 1

- Read: `doc/v3_fundament.md` (the index), all three `principles-` parts
  (06, 07, 08), and the parts this order touches: 02 (the orion2re boundary
  — decisions 22, 33, 36, 47, 52), 09 (orion2re facts, the live-run file
  list, MOX.SET's load byte). Then 180's progress, parked file, the six
  patch files and entries 34-40 of `doc/orion2re_open_fixes.md` (34 is the
  model the order names).
- 08:15: no orion2re and no OrionLayer client running (`ps`). The desktop
  had been idle for 46 s (`org.gnome.Mutter.IdleMonitor.GetIdletime`) —
  Data was at the desk minutes before; there was nothing running to leave
  or to close.
- 180's scratch clone of the engine still exists
  (`/tmp/claude-1000/-home-data/d1bec194-…/scratchpad/orion2re_180`, commits
  `3badb08e` … `053fa0d5` on `9ab84230`), so "byte for byte against the
  scratch commits" is checked against the commits themselves, not only
  against the patch files. First: each of the six patch files' diffs at
  `7fa43b4` is byte-identical to `git diff <scratch>~1 <scratch>` (all six
  `cmp` clean).

## Part 1 — apply the series 35 to 40 — **DONE, all six applied**

**Two comment-only corrections, both made to the patch FILE before it was
applied, so file and commit match:**

1. **Fix 39 (the order's correction).** The block's comment DID name the
   fix, but broken over a line — `…and LAST. OrionLayer, open` /
   `fix 39.` — so the string `OrionLayer, open fix 39.` was in no line of
   the file and no grep could find it; that is why `version_check` had
   fallen back to the symbol. Re-wrapped, same line count (so fix 40's
   hunk lines do not move):

   ```diff
   -+    //     ONLY while SCREEN_QUEUE_POPUP is up, and LAST. OrionLayer, open
   -+    //     fix 39.
   ++    //     ONLY while SCREEN_QUEUE_POPUP is up, and LAST.
   ++    //     OrionLayer, open fix 39.
   ```

   `tools/version_check.py`'s marker for it is now `OrionLayer, open fix
   39.` (was `COLBLDG::_colony_auto_building`).
2. **Fix 35's `#include` (found applying Part 2.1 to Part 1).** Fix 35
   changes TWO places: the block, which names the fix, and one added line
   `#include "game/build_queue.h"`, which named nothing. Part 2.1 asks for
   a marker "at every changed place", so the include now carries it on the
   same line (no line added, nothing else moves):

   ```diff
   -+#include "game/build_queue.h"
   ++#include "game/build_queue.h"  // OrionLayer, open fix 35. autobuild_settings, sent in "COLS".
   ```

   This is a second difference from 180's proof that the order did not
   name; **parked** (`181-parked-for-data.md`, "fix 35's include") with this default.

**Method.** The corrected series was first built as commits in a scratch
clone of `orionlayer-local` (scratchpad `o181`) and each patch file's diff
section replaced by that commit's `git diff`; then the FILES were applied
to `~/orion2re`. For each fix, in order: `patch -p1 --dry-run` (output
checked for offset / fuzz / reject — none), `patch -p1` (the same), `ninja
-C out/build/Linux/linux-debug` (ext_api.cpp compiled and the binary linked,
0 warnings), one commit, then `git diff HEAD~1 HEAD` compared with the patch
file's diff section: **byte for byte, all six.**

| fix | block | orionlayer-local commit |
|---|---|---|
| 35 | COLS | `c5d4dacd` OrionLayer Open Fix 35: send which colony the colony screen and the build popup show ("COLS") |
| 36 | CBLD | `01bafd9c` OrionLayer Open Fix 36: send where the colony screen puts its buildings ("CBLD") |
| 37 | CEVT | `a10e20ba` OrionLayer Open Fix 37: send the colony screen's Plague and Pop Boom answers ("CEVT") |
| 38 | CPRD | `8a6acc08` OrionLayer Open Fix 38: send the shown colony's product cost and turns ("CPRD") |
| 39 | BLDQ | `2be953d4` OrionLayer Open Fix 39: send the build popup's queue under edit and its modes ("BLDQ") |
| 40 | BLDL | `2097b0c6` OrionLayer Open Fix 40: send the build popup's two lists and its queue with their numbers ("BLDL") |

**Against 180's scratch commits, verified:** the finished `ext_api.cpp`
against `053fa0d5`'s differs in exactly the two comment lines above (`diff`
prints lines 9 and 542-543, nothing else). Commit by commit, the diffs
against `3badb08e` … `053fa0d5` are identical in every `+`, `-`, context
and `@@` line except (a) the two corrections, in 35 and 39, and (b) the
`index <blob>..<blob>` line of every fix from 35 on — git's hash of the
whole file, which any changed byte earlier in the series changes (fix 40's
would have changed from the order's own fix 39 correction alone). Before
the first fix the binary at `9ab84230` was kept in the scratchpad
(`sha256 15831519…`).

**Markers, checked by grep** (`OrionLayer, open fix N.`), each in the
comment directly above its block: 35 at 9 (the include) and 444 (block
`if` at 459), 36 at 473 (482), 37 at 498 (506), 38 at 519 (529), 39 at 543
(552), 40 at 569 (581). `python tools/version_check.py`: all six "applied"
(still under REPORTED until Part 2 moves them).

**Two existing checks adjusted, not weakened.** 090c (fix 30) and 090f
(fix 32) prove their patch comes back off a COPY of the live
`ext_api.cpp` with `patch -R`; 35-40 append after 32's block, onto the
trailing context both use, so the first commit attempt was refused by the
fast gate ("Unreversed patch detected" in 090c). Both now take the series
off the copy first, last one first, as the stack was applied —
`version_check.COLONY_SERIES` and `take_off_colony_series` (a tree without
the series passes through; a fix that will not come off fails the check
by name). Fast tier then green, 361 of 371.

## Part 2 — document every engine change — **DONE** (`87119b8`)

1. **Comments in the engine source.** Every changed place carries
   `OrionLayer, open fix <N>.` (Part 1 above, the grep): 35 on its include
   line and over its block, 36-40 over theirs, each on ONE line.
2. **Entries 35-40 in `doc/orion2re_open_fixes.md`**: status APPLIED, 27
   September 2026, the orion2re commit, the OrionLayer commit (`87119b8`,
   added by the next commit as 179 did), the change (file, function
   `SerializeState`, the line ranges), the full diff, "against 180's
   proof" (35: the include's comment; 39: the marker re-wrap, with the
   patch file's diff; the rest: only the `index` line), the live wire
   (`doc/briefs/181-fixes35-40-wire.txt`), side effects, the revert. The
   summary rows say Applied. Entry 36 keeps "HD does not place buildings
   yet" and UNVERIFIED `building_placement`, with the reason.
   - **The live wire** (engine PID 94595 started by this session with
     `tools/engine_start.py`, guard `181_p2_record`; SAVE4 loaded as
     scratch, nothing saved; `tools/colony_record.py 4 4` → evidence
     `P2_record`): all six blocks on every stop of their screens and none
     elsewhere; field layout and sizes equal the fixture on all 12 colony
     and popup stops, and **on the nine stops 180 recorded, every byte**
     (`cmp` of the tails) — no fixture or parser correction. The HD colony
     screen and build popup claimed ids 1 and 25 by themselves; the gate
     held one snapshot per colony entry. Engine closed with SIGTERM.
     Guard verify: `game/MOX.SET` changed — restored with `--restore`
     BEFORE its bytes were compared, so this run did not itself confirm it
     was the known offset-21 load byte (every later guard does); and the
     tree's own uncommitted edits. SAVE1-11 identical (SAVE8
     `ab70cc9a…`).
   - **Side effects** read in the source: every function the blocks call
     (`Event_Check_Plague_`, `Event_Check_Population_Boom_`,
     `Colony_Product_Cost_` with `Ship_Type_Cost_For_Player_` and
     `Cost_Reduction_For_Govt_Type_`, `Colony_N_Turns_To_Produce_`,
     `Calculate_Colony_Turn_Count_From_Scrap_For_Prod_`) only reads.
   - **The reverts, run** in a scratch clone: `git revert 2097b0c6 …
     c5d4dacd` (reverse order) returns `ext_api.cpp` to `9ab84230` exactly;
     so does the `patch -R -p1` chain of the six files, no offset or fuzz.
3. **version_check**: the six moved from REPORTED_PATCHES (empty again) to
   LOCAL_PATCHES. **A build without one is reported**: for each fix, a
   scratch copy of the tree with exactly that commit's added lines removed
   — exit 1, and the MISSING line names that patch and no other (git
   revert of a single middle commit conflicts, the blocks being adjacent;
   removing its lines is the same tree). 090r #2 holds it offline with a
   stand-in tree per patch.
4. **Every place that tells a clone which fixes it needs:** README's
   orion2re table (row 13, and the bundle name); `tools/setup.py` now
   prints "The orion2re build it needs … open fixes 3, 12, 14, 20, 21, 22,
   24, 25, 27, 28, 30, 31, 32, 34, 35, 36, 37, 38, 39, 40" and whether the
   tree here has them (`engine_report`); a line in fundament part 09
   (there was no such line — the rule set had only pointed at
   `version_check`). The numbers live in `version_check.FIX_NUMBERS`, keyed
   like the two lists; 090r #1 holds README, setup and the fundament to it.
   CLAUDE.md's colony-screen sentence no longer says "parked".
5. **Docs against the commits, fix by fix:** each entry's diff equals
   `git diff <hash>~1 <hash>` byte for byte after fix 34's convention (no
   `diff --git`/`index` lines, nothing after `@@`): 35 2143 bytes, 36
   1449, 37 1309, 38 1743, 39 1541, 40 3362 — all equal. Each patch
   file's diff section equals its commit's `git diff` byte for byte. 090r
   #3 holds entry = patch file offline, and commit = patch file where the
   tree is on the disk.
6. **Bundle:** `~/orion2re_bundle_27sep_2097b0c6_fixes34-40.bundle` (`git
   bundle create --all`, beside 179's `…26sep_9ab84230.bundle`), 21 refs,
   `git bundle verify`: "ist in Ordnung", complete history; a clone of it
   shows 2097b0c6 … 9ab84230 on orionlayer-local. sha256 `e9956e89…`.

**Checks: 371 → 374** — 090r (three): the one list and its three readers;
a tree missing any one fix is reported by name; 35-40 applied and
documented. Each shown red by a mutation (the fundament line without 40;
fix 39's marker broken over two lines again; a marker in version_check
that no longer matches) and green restored, run with `python -B`.

## Part 3 — activate and accept both screens live — **DONE**

**No flag.** With the blocks on the wire both screens claimed their ids by
themselves from the first recording on (Part 2's `P2_record`).

**Wire against the fixtures:** Part 2 — layout, sizes and (on the nine
shared stops) every byte equal `tools/fixtures/colony_blocks_180.json`;
nothing to correct in the fixture or `core/colonyblocks.py`.

**The driver:** `tools/colony_accept.py` (new; `colony_live.Live` with a
per-frame agreement count), evidence `~/orionlayer-fixtures/evidence/
work_order_181/`. Engines, each started by this session with
`tools/engine_start.py` and closed with SIGTERM: 100458 (guard `181_p3_a`,
runs `P3_try1_1920x1080` and a first `--orders` try that crashed in its own
report — its pictures kept apart in `P3_orders_1920x1080/
first_try_crashed_0858/`), 102128 (`181_p3_b`, `P3_orders_1920x1080`, and a
2576 run kept as `P3_orders_2576x1432_second_on_engine_102128` because the
system window was still open from the 1920 run), 103384 (`181_p3_c`, the
clean `P3_orders_2576x1432`), 103561 (`181_p3_d`,
`P3_pictures_3840x2160_cancel_lost`, below), 105528 (`181_p3_e`,
`P3_pictures_3840x2160`). SAVE4 loaded as scratch in every one, nothing
saved. **Every guard:** MOX.SET's offset 21, 10 → 3 (`cmp -l`: `22 12 3`,
the load's slot byte), restored, then identical; SAVE1-11 identical in
every run (SAVE8 `ab70cc9a…`). The desktop was in active use during these
runs (idle 89 ms at 08:56); nothing foreign was running.

**Colony screen (1), every way the scratch save offers:**

| way in / out | result |
|---|---|
| galaxy map: home star → system window → the colony's planet (HD's own disc click), ESC back | Sol IV, HD and native the same colony |
| Colonies screen: row name (the game's field through `livesend` — the HD Colonies screen offers no such click), ESC back | Ixion II |
| `<` and `>`, twice each way | 17 → 15 → 17 → 19 → 17 (Ixion II, Kif II, …); HD follows every switch |
| L → Leaders (29), ESC back | both HD, back on the same colony |
| Info screen / Turn Summary jump | **not reachable**: open fix 33 (the engine goes to the map; `info.cpp` unchanged since 176 measured it — the series touched only `ext_api.cpp`) |
| turn-start reports, turn summary, colony landing | **not reachable** without TURN, which writes SAVE10 |

**The handle/pair agreement, at every frame HD drew the colony screen:**
406 frames at 1920, 395 at 2576, 267 at 3840 — the colony HD drew was the
engine's handle in every one, 0 disagreeing, including the frames right
after each switch (the gate holds 1-3 snapshots per entry until the pair
and the handle agree).

**Elements against the native screen** (side-by-sides below): title, pop
line, system display, production rows, morale, job rows, the production
window (name, **bar and turns — fix 38**: Housing 1 turn, Colony Base 6
turns, as native), the building LIST (DEVIATION `building_list`), units,
buttons. **Status word:** Blockaded none; CEVT answered plague 0 / pop boom
0 on every colony walked (six) — **Plague and Pop Boom are not reachable
in SAVE4**, so the two words were seen only in the smoke check's forced
states. **Found and fixed:** the original prints **"No Farming"** centred
in the farmers' row when `max_farms` is 0 on this screen too
(`Draw_Colony_Info_Pop_For_` → mode 0 of `coldraw.cpp:315-321`); 180's
colony screen did not. Now drawn (`coldraw._no_farming`, `colwords.
no_farming`), seen on Kif II beside the native at 3840.

**Pop move** (Ixion II, colony 17): a worker to scientists through the HD
job rows, on the wire; moved back; `pop[]` restored word for word — at
1920 and at 2576.

**Build popup (25):** both lists against the native popup — order and
names identical (Trade Goods, Housing, Research Lab, Soil Enrichment, Star
Base; Freighter Fleet … Spy with its separators), the summary's numbers the
native print (Colony Base 200 / 0 / 10, Turn(s) Left 5), the queue
identical, queued buildings bright as in the native. Corsair and Paladin
are dim natively and bright in HD — DEVIATION `ship_row_dim`, as marked.
**Auto Build:** BLDQ 0, COLS `autobuild_enabled` 0, HD's radio unlit, the
native radio unlit. **The queue under edit (fix 39):** Soil Enrichment (37)
selected — in BLDQ and drawn in HD's queue while the colony's `producing[]`
on the wire was still the old one; a ship (Colony Base -15) selected — the
queue moved; **Cancel — `producing[]` exactly as before.** **One real
order:** 37 added and **OK** — `producing[]` `[11, 11, 35, 40, 37, -1, -1]`
on the wire, and the game's own popup reopened shows Soil Enrichment
queued; then taken back the same way (the row toggles, colbldg.cpp:
1654-1672) and OK — `producing[]` as before and **the colony record
byte-identical** to before the add. Both sizes. The save file was never
written (guards).

**Flash — every transition into and out of 1 and 25, at 1920 and 2576:
0 native frames** (trace and pixels agreeing), all settled, 0 fallbacks —
19 transitions at 1920, 21 at 2576 (plus the 3840 walk, 0 as well). **Added
to 180's replay set:** `tools/fixtures/transitions_180.json` regenerated
from 180's six run folders plus `P3_orders_{1920x1080,2576x1432}` — all
158 old transitions reproduced byte for byte, 40 added (198). 090p #7
holds the twelve ways at both sizes in that set.

**Comparison images:** `compare/` — 35 live side-by-sides (native | HD,
one frame) at 1920, 2576 and 3840 (Sol IV from the map, Kif II, Ixion II
and the other switch targets, the pop move, the popup, the queue under
edit, after OK, taken back), and 39 offline side-by-sides of the live
recording `P2_record` (four colonies, their `<` neighbours, three popups)
at all three sizes.

**A click lost once, at 3840** (`P3_pictures_3840x2160_cancel_lost`): the
popup's Cancel did nothing for 30 s and the walk then ran one step behind.
The trace shows the client's field list EMPTY for exactly that frame (snap
1663: 45 fields → 0 → 45) — a one-frame FIELD_LIST of 0 from the engine
while the popup rebuilt its fields; the activation most likely landed in
that rebuild. **Not reproduced** on a fresh engine (every transition
settled). Cause not established; parked with the evidence.

**Markings.** HD STATE `status_word`, `production_bar` and `turns` are
gone — from `coldraw`, `colwire`, `colwords`, `layout.json` (18 → 16
marks), the status document and entries 37/38 — with the state itself:
the colony screen now claims id 1 only with all four blocks the engine
writes there (`colwire.BLOCKS`: COLS, CBLD, CEVT, CPRD), the popup only
with its four (`bqwire.BLOCKS`: COLS, CPRD, BLDQ, BLDL; 38 joined for
"Turn(s) Left"), and a CEVT or CPRD that does not describe the shown
colony is waited for, never drawn. **Recorded as required:** 090p #5
asserted "without open fix 37 the status word is an HD STATE: nothing" —
that state no longer exists, so the assertion was replaced (the word for
each of CEVT's answers, none included) and the claim check (#3) now
proves each of the four blocks is required on its own; 090q #1 the same
for the popup's four. No check was removed. DEVIATION `building_list`,
`production_bar`, `ship_row_dim`, `label_number`, … and UNVERIFIED
`building_placement` stay.

**Checks: 374 → 375** (090p #7).
