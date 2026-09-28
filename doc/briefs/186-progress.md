# Work order 186 — progress

Unattended run, 28 September 2026. Evidence root:
`~/orionlayer-fixtures/evidence/work_order_186/`. The order:
`doc/briefs/186-work-order-apply-fixes-44-47-ship-designer-audience-live-modal-hold.md`.

## Before part 1

- **Number 186**: the last brief in `doc/briefs/` is 185, no "Work order
  186" commit.
- **Baseline as expected**: main = origin/main = `5d791a9` (185, "Work order
  185: gates and the end of the order (part 12)"), suite 405 green by 185's
  push gate; orion2re `orionlayer-local` = `4bf152e4` (fixes 34-41), its
  three untracked files (`mox.set`, `racesel_custom_screen_id.patch`,
  `src.zip`) left alone.
- Read: `doc/v3_fundament.md`, the three `principles-` parts (06, 07, 08),
  part 09 (live runs, the virtual display, the files a run writes, the
  engine line), CLAUDE.md, 185's progress and parked files, entries 41-47.
- **Data's session**: no orion2re, no `play.py`, no OrionLayer running at
  the start. The order's first guard: `guard_186_start` (16 files).
- "The proper version of Fix 41 prepared in 185 Part 2" is **open fix 43**
  (entry 43, "The engine's window: hidden only when OrionLayer starts it,
  and shown again on request") — 185 wrote it as a separate fix amending 41.

## Part 1 — apply the approved engine fixes — **DONE: 44, 45, 46, 47 and 43 applied**

1. **Per fix, before applying: the proof on the current tip**, in a scratch
   clone (`git clone --no-hardlinks ~/orion2re`, the session's scratchpad),
   never in `~/orion2re` (`P1_proofs/*.json`): reset to the tip, `patch -p1
   --dry-run` and `patch -p1` (any offset, fuzz or reject reported), every
   changed .cpp compiled alone with the build's own command re-pointed at the
   scratch tree (`-fsyntax-only`), a misspelt-constant control that must be
   refused, and the applied diff compared with the file.

   | fix | tip | as 185 wrote it | re-cut | control(s) refused |
   |---|---|---|---|---|
   | 44 | `4bf152e4` | clean, diff equal | — | `_printed_space_avial` |
   | 45 | `70d31b10` | clean, diff equal | — | `_weapon_replacment_rack` (ext_api.cpp), `ext::ScreenOveride` (desbox.cpp) |
   | 46 | `4af9fefa` | ext_api.h hunk offset 4 (45's four lines) | yes | `ext::ScreenOveride` |
   | 47 | `8aea1a25` | ext_api.cpp hunk 2 offset 187 (44/45's blocks), ext_api.h offset 4 | yes | `DIP_SCRN::_respons_message` |
   | 43 | `ba9b6bc6` | ext_api.cpp hunks 3/4 offset 233 (44-47's blocks) | yes | `case MSG_SHOW_WINDW:` (ext_api.cpp), `g_window_shwn` (platform.cpp) |

   **Re-cut** = regenerated from the applied scratch tree; every added,
   removed and context line is 185's, only positions and index lines
   changed (`recut.py` prints the difference); the re-cut file was then
   proved again from the start: clean, compiles, controls refused.
   Two slips of mine on the way, both caught before anything was applied:
   my first desbox.cpp control misspelt a comment (it compiled — a control
   that measured nothing; moved onto the guard line), and my `:`-separated
   argument broke on `::`; and GNU patch's `.orig` backup on an offset was
   swept into the first 46 diff by a `git add -A` — the script now stages
   only the patch's own files.
2. **Applied on `~/orion2re`**, each after checking that no process runs
   from `out/build/Linux/linux-debug/orion2re` (every `/proc/*/exe`, and
   `engine_start --check`: none, OK to start): dry run, apply (no offset),
   `ninja` (no error), `git add` of the fix's files only, one commit, the
   commit's diff equal to the doc patch byte for byte (index lines
   included), a bundle, `git bundle verify` exit 0. Older bundles kept.

   | fix | before | after | bundle |
   |---|---|---|---|
   | 44 | `4bf152e4` | **`70d31b10`** | `~/orion2re_bundle_28sep_70d31b10_fixes34-44.bundle` |
   | 45 | `70d31b10` | **`4af9fefa`** | `~/orion2re_bundle_28sep_4af9fefa_fixes34-45.bundle` |
   | 46 | `4af9fefa` | **`8aea1a25`** | `~/orion2re_bundle_28sep_8aea1a25_fixes34-46.bundle` |
   | 47 | `8aea1a25` | **`ba9b6bc6`** | `~/orion2re_bundle_28sep_ba9b6bc6_fixes34-47.bundle` |
   | 43 | `ba9b6bc6` | **`230a0638`** | `~/orion2re_bundle_28sep_230a0638_fixes34-47_43.bundle` |

   Nothing pushed; 1169 commits on the branch.
3. **Revert paths, proved in scratch**: the five files reversed in the
   opposite order return the tree to `4bf152e4` byte for byte; `git revert`
   alone on the tip is clean for 43, 47 and 45; 46 and 44 conflict until
   the fix stacked on them (47, 45) is off. Each entry says so.
4. **Side effects found**:
   - **Fix 43 replaced fix 41's line in `ext_api.cpp`**: `version_check`
     reported 41 `MISSING` on its first run. 41's other half (no VSync
     while hidden, `platform.cpp`) keeps its marker; `LOCAL_PATCHES` reads
     41 there now, entry 41 says it is amended by 43, and check 090r #4
     asserts 0 markers in ext_api.cpp and 1 in platform.cpp.
   - **Live on the virtual display** (engine `230a0638`; guards
     `P1_live/guard_noenv`, `guard_env`, each verified identical; no save
     loaded): started without `ORION2RE_HIDE_WINDOW` the window is
     **IsViewable**, with it **IsUnMapped** and the intro skip arrives;
     `MSG_SHOW_WINDOW` hides and shows both ways, 9 snapshots in each 1.5 s;
     main-menu pacing 6.05/s, gap median 165.1-165.2 ms, CPU 2.4-2.5 % (41's
     6.06 / 164.3). **Until Part 2 sets the variable, every start shows the
     engine's window** — harmless on Xvfb, visible from `play.py`.
5. **Documented**: entries 43-47 APPLIED (status with both hashes, the
   commit's diff, the proof on the tip, the re-cut and why, side effects,
   revert), entry 41 amended, summary rows; the five patch files' headers
   (APPLIED, both proofs, revert); `version_check` (43-47 in
   `LOCAL_PATCHES`, 42 alone in `REPORTED_PATCHES`, 41 read in
   `platform.cpp`) — green on `230a0638`, and on `git archive 4bf152e4`
   exit 1 naming 43, 44, 45, 46, 47 `MISSING`; README row 15 and the
   newest bundle; `setup.py`'s report follows `required_fixes()` by itself
   (it now names 3 … 41, 43, 44, 45, 46, 47 — nothing hard-coded there to
   change); fundament part 09's engine line. Check 090r #6-#8 rewritten
   from "parked" to "applied and documented" (on this disk each commit's
   diff the file's); the count stays 405.
6. **Release clean-up list** created, `doc/release_cleanup.md`: commit
   `6f0570c` holds two short game strings in hex (the order's decision; no
   rewrite, no force-push).
7. **Found by the suite**: check 090c (the Leaders screen's fix 30) takes the
   colony series off a copy of `ext_api.cpp` to reach fix 30's context, and
   fix 40 no longer came off — 44/45 append after its block and 47 puts
   DIPL between INFS and COLS. The helper now takes the `ext_api.cpp` parts
   of 44, 45, 47 and 43 off first, last applied first
   (`STACKED_AFTER_COLONY`); fix 30 then comes off as before. The helper
   moved out of `tools/version_check.py` into `tools/patch_stack.py`
   (re-exported by the same names): with it, version_check had reached 334
   code lines; without it, 284 — so it left the over-300 list rather than
   growing its entry. **Full suite: 405 green.**
