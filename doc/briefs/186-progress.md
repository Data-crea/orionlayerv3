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

## Part 2 — HD side — **DONE**

1. **The data is there, seen live first** (the engine `play.py` starts,
   `230a0638`; engine 183602, guard `P2_live/guard_design`, Xvfb, SAVE4,
   nothing saved; `evidence/work_order_186/P2_*`):
   `tools/design_walk.py 1920 1080` — colony → popup → designer → computer
   (54), weapon (55, offered mods 10, 11, 12), special (56) pickers and
   back → popup → colony → map: DSGN on every designer stop, DSBX on each
   picker, **13 transitions, 0 native frames**; `tools/audience_walk.py
   1920 1080` — Races → refusal (57) → Races, Races → greeting → menu →
   Good Bye → Races → map, the HD audience drawing from DIPL: **7
   transitions, 0 native frames**. SAVE1-9 and SAVE11 identical, SAVE10
   unchanged; MOX.SET rewritten by the load → restored from the guard taken
   before the engine existed, verify clean; against the order's first
   guard every game file identical.
2. **Markers removed where the data is now there**: UNVERIFIED `fix44`
   (page), `fix45` (pickers), `fix46`, `fix47` (audience) — from the
   layouts, the modules' docstrings, `core/designblocks.py`,
   `core/diplblocks.py`, the status document and both briefs; the two walk
   tools no longer say "only against a scratch engine". **Kept**: UNVERIFIED
   `name_entry` — the name is shown, not edited, and the reason is now the
   data: DSGN carries the name as committed, the text being typed is the
   engine's `_continuous_string`, on no block (fields.cpp:1048-1100,
   :2181); F12 shows the original's own field. Part 3 measures what
   injected keys do there. Every OMISSION / DEVIATION stays (they are about
   drawing, not about the data path). No stubs were found beyond the marks
   (`grep` for stub / NOT APPLIED / scratch engine in the three screens and
   the two block readers).
3. **Fix 43's HD side**, as entry 43 described it: `ORION2RE_HIDE_WINDOW=1`
   in `tools/vdisplay.engine_env` (the tools' starts and `play.py`'s),
   `MSG_SHOW_WINDOW` in `core/wire_protocol.py`, `GameClient.show_window`,
   F12 in `main.App._cycle_render_mode` (main.py 371 → 373 code lines, its
   over-300 entry extended). Live (engine 183602): started hidden
   (IsUnMapped), F12 → the original's picture and the engine's window
   **IsViewable**, F12 → HD and **IsUnMapped**. Part 1 measured the other
   half: started without the variable the window is viewable.
   README's quick start (play.py hidden because it asks; F12; by hand the
   window shows again), `play.py`'s docstring, part 09's virtual-display
   paragraph and entry 43's HD-side paragraph say so.
4. **Checks 405 → 406** (fast 395 → 396): 090v #2 (new) — the variable on
   both displays, `show_window`'s bytes, F12 on a stand-in App both ways
   and silent without a connection; shown red with the variable removed
   from `engine_env` (`python -B`, caches cleared after the restore), green
   again. 090x / 090y / 090z now assert 44-47 required and their fix marks
   gone, and `name_entry`'s reason. Full suite **406 green**.

## Part 3 — verification on the engine `play.py` starts — **DONE (one fault found and fixed; the AI audience parked)**

Engine `230a0638` (the binary `play.py` starts), every session on Xvfb through
`tools/engine_start.py` with its own guard, SAVE4 or SAVE5, nothing saved
(evidence `work_order_186/P3_*`).

1. **Suite and clone**: full suite **407 green** before this part's commit.
   The fresh clone runs on the committed tree — Part 5.
2. **Flash walk over every transition, and the colony screens**:

   | walk | 1920x1080 | 2576x1432 |
   |---|---|---|
   | `flash_walk` (pre-game, the SAVE4 load, every in-game screen, the system window) | 29, 0 native | 29, 0 native |
   | `design_walk` (popup → designer → the three pickers → back) | 11, 0 | 11, 0 |
   | `audience_walk` (Races → refusal; greeting → menu → Good Bye) | 7, 0 | 7, 0 |
   | `colony_accept` (colony screen and build popup, every way in and out; fix 47 puts DIPL between INFS and COLS) | 17, 0 — 276 colony frames agreeing with the engine's handle, 0 disagreeing | — |

   **Every recorded transition of this order — 164 in 16 runs — 0 native
   frames** (summed from each run's `transitions.json`).
3. **The Ship Designer live, beside 185's native frames**
   (`P3_designer_1920x1080`, strips HD 186 | native 185 | native 186 in
   `P3_side_by_side/`): 185's 16 states in 185's order. **HD 186 is pixel
   for pixel HD 185** on 13 of them; 08 and 09 differ by 185's own later fix
   (a modification that is on drawn lit); 02 is the game's picture in both
   (the warning box, the modal net); in 03 185's native frame was taken
   before the box had closed — 186's shows the page, as HD does. Native 186
   vs native 185: 0-0.23 % except 03 (that timing). New in 186: out by the
   HD **Cancel button** (185 left by ESC), a **second way in**, **name
   entry**, **Build** (save design, in memory — nothing on disk). Every way
   in the save offers was walked; Refit is not offered (parked, as in 185).
4. **Name entry — a fault in the safety net, found and fixed.** Through F12
   (the player's route to the original's own field) the name did not
   change: the forwarded click went out as an ACTIVATE_FIELD, which never
   opens a continuous string field; the five keys went nowhere; **Enter
   then pressed the field under the engine's pointer** — the Cruiser hull,
   where the last injected click had left it (fields.cpp `Scan_Field_`) —
   and the design became a Cruiser "Interceptor", which Build then wrote
   into slot 1 in memory. A probe measured the right path: an injected
   click opens the field, keys append, Enter commits (`Corvette` →
   `CorvetteAbc`). The first fix (skip string fields like radio buttons)
   was not enough — the next field under the point, the page's full-screen
   hidden field, was activated instead (and Enter opened the weapon picker
   under the real pointer); a control with the engine's window hidden
   again gave the same, so the shown window was not the cause. **The
   fix**: `original_view.find_field_at` takes the FIRST field covering the
   point, as the engine's hit test does (fields.cpp:710-715), and a radio
   button or a string field there goes as INJECT_CLICK. Live again through
   F12: click sent as 130, keys appended, Enter committed — `Corvette` →
   `CorvetteQzxvk`, the HD page shows it — and **Build** returned to the
   popup with slot 2's new cost (82). **Check 090g #3** (new) holds the
   rule on a list shaped like the designer's; shown red with the old rule
   (the exact live failure: field 42 activated), green again. The name is
   now OMISSION `name_entry` (measured; HD's page itself does not edit
   it — parked 1c), part 09 has the fact.
5. **The audience live** (`P3_audience_states_1920x1080`): refusal (race
   slot 0), greeting, the menu "How may I serve you:" (Peace Treaty
   disabled, as the list's flag says), **Declare War → "REALLY DECLARE
   WAR?!" answered Cancel** (the Yes item never sent) → back to the menu,
   Good Bye, 7 transitions, 0 native. Beside 185's frames: HD within
   0.5-0.9 % of 185's (the statement is a random variant — HD shows the
   engine's current one, as its native frame does); the native frames
   differ by the ambassador's animation. Differences, as questions: parked
   2a.
6. **The AI's turn-start audience (58) — not reachable by ending one turn**:
   SAVE4's TURN stops at "Select planet for Colony Base in Malus system"
   (work order 122's dialog — a game decision, place or scrap), SAVE5's at
   "CyberToller select combat at peren" (a battle). The probe only
   observed (nothing sent to either); SAVE10, rewritten by the TURN press,
   and MOX.SET restored from the guards taken before those engines.
   Parked 1d with the save it needs.
7. **Fix 43 live**: the binary started by hand on Xvfb without OrionLayer's
   variable — window **IsViewable** at 2, 4 and 8 s; OrionLayer's start —
   **IsUnMapped**; F12 → **IsViewable**, F12 → **IsUnMapped** (Part 2).
8. **Guards**: every session verified after its engine stopped; MOX.SET
   (every load) and SAVE10 (the two TURN presses) restored from the guard
   taken before that engine existed; against the order's first guard every
   game file identical — only the tree's own uncommitted edits differ.
   SAVE1-9 and SAVE11 identical in every run.
9. Checks **406 → 407** (fast 396 → 397).

### Data's acceptance on his desktop (one screen)

Start with `python play.py` (use a save you can throw away — Build and
the diplomacy menu act on the loaded game).

1. **No engine window appears**; the HD main menu, no intro sound.
2. Load the save → map → your colony → **CHANGE → Design → a design row**:
   the **HD Ship Designer** (glass panels, the design's numbers), no flash
   of the old picture on the way in.
3. Click the **computer panel**, a **weapon row**, a **special row**: each
   an HD picker; in the weapon picker choose a weapon, an arc, a
   modification; **ESC** back each time. Try **+ / −** and a **hull**.
4. **F12**: OrionLayer shows the original's picture AND the **original's
   own window opens**. Click the name, type, **Enter**, **F12**: the HD
   page shows the new name; the original's window is gone.
5. **Cancel** → the build popup (or **Build** to keep the design).
6. **RACES → AUDIENCE → a race**: the HD audience (room, ambassador); click
   the greeting → the menu; **Declare War → "REALLY DECLARE WAR?!" →
   Cancel**; **Good Bye** → Races.
7. Close OrionLayer → the engine stops too. Start the orion2re binary by
   hand → **its window appears**, as before fix 41.

What you should NOT see: the old 640x480 picture flashing before an HD
screen; the original's window at any time except while F12 is on.

