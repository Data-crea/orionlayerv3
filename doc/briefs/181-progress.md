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
