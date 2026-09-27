# Work order 185 — progress

Unattended run, 27 September 2026. Evidence root:
`~/orionlayer-fixtures/evidence/work_order_185/`.

## Before part 1

- **Baseline as expected**: main = origin/main = `af4d354`, suite 386 green
  (184's push gate); orion2re `orionlayer-local` `4bf152e4` (fixes 34-41
  applied), its three untracked files (`mox.set`,
  `racesel_custom_screen_id.patch`, `src.zip`) left alone. Number 185: no
  `185-*` brief, no "Work order 185" commit.
- Read: `doc/v3_fundament.md`, all three `principles-` parts (06, 07, 08),
  part 09 (live runs, the virtual display, the files a run writes) and part
  02 (the boundary) in this session; parts 01 and 04 before the two screens.
- **Data's session**: at the first look a `python play.py` (PID 109569), its
  engine 109587 and OrionLayer 109601 were running — Data playing; not
  touched. A minute later all three had ended by themselves. Before every
  live session below the run checks for his processes and does not start
  while he plays (the port and the game folder are shared).

## Part 1 — open fix 42: are clicks lost in the gap? — **DONE: none lost, none taken twice**

1. **The tool**: `tools/gap_clicks.py` (new). One trial = open the screen
   the player's way, t0 = the moment its FIRST HD frame was presented
   (flipped — the frame trace stamps a frame before it is drawn, and a
   cold first frame takes ~0.3 s to draw; the first debug run showed it),
   the player's input posted into the HD window at t0 + offset, the wire
   read back for 2.5 s, the input log saying what HD did with it. Screens:
   the research panel (HD click on the exit → `ACTIVATE_FIELD`; and, added
   when the first run showed the colony screen and popup have no gap, the
   same gap through SDL's queues — `INJECT_KEY` ESC and `INJECT_CLICK` on
   the exit, what HD's safety net forwards), the colony screen (HD ESC →
   `ACTIVATE_FIELD` on its ESC field; never CRUNCH, TOGGLE or field [0]),
   the build popup (HD click on Auto Build → `INJECT_CLICK`, read off open
   fix 39's `auto_building`: flipped once / never / and back = taken /
   lost / TAKEN TWICE, flipped back after each trial, left with Cancel).
   13 offsets 0-1000 ms, two repetitions.
2. **Patched** (scratch engine `21a37ffb` from 184, its own clone and build
   directory in the scratchpad, never `~/orion2re`; engine 112705, guard
   `185_P1_patched`, SAVE4): **130 of 130 taken**. **Unpatched** (the
   applied build `4bf152e4`, engine 113660, guard `185_P1_unpatched`):
   **130 of 130 taken**. Table: `evidence/work_order_185/gap_table.md`;
   every trial in `P1_*/gap.json`.
3. **The gap**: only the research panel has one with the fix. Inputs sent
   0-400 ms after its first HD frame took effect 560-610 ms after that
   frame, whenever sent — held until the delay ended; from 500 ms on the
   normal latency. The colony screen and the popup: the same latency at
   every offset (their three-pass delays end before HD's first frame).
   Unpatched: no gap anywhere. **Entry 42 updated** (section "Clicks in the
   gap", row 42); status stays NOT APPLIED / open; **no addition needed**;
   approval parked with the recommendation to approve (parked 1a).
4. **Cites corrected** (found while writing this part, fixed in all seven
   copies): the research panel's delay is `tech.cpp:286` (184 wrote
   `:306`), its idle pass `:351-353` (184: `:349-351`); the consumption
   block after the delay `fields.cpp:173-183` (184: `:167-183`) — in entry
   42, the patch file's header, `184-research-timing.md`,
   `184-parked-for-data.md`, fundament part 09 and
   `core/researchprepare.py`'s docstring.
5. Guards `185_P1_patched` (MOX.SET's load byte restored, then identical)
   and `185_P1_unpatched` (MOX.SET restored; otherwise only this order's
   own files). SAVE1-9 identical, SAVE10/11 unchanged in every run.

## Part 4 — handover package for Joes — **DONE (not committed)**

`~/orionlayer-fixtures/handover_joes_2026-09-27/`, English: `README.md`
(what each fix does, why OrionLayer needs it, the patch with its sha256,
its local status), `patches/` (fixes 31, 34-41, the files from `doc/`),
`entries/` (entries 31, 33, 34-41 in full), `notes/33-turn-summary-colony-
jump.md` (with a reproduction; the jump also removes one way into the
colony view) and `notes/load-dialog-screen-data-after-esc.md`. Every cite
in the two notes re-read on `4bf152e4` (loadsave.cpp:382-383 and :388-391,
info.cpp:641, msg.cpp:653-672, info.cpp:2087). No tree, no bundle.
**Measured before writing the base paragraph**: the patches do NOT apply to
upstream `cf4d9617` on their own (fix 31's third hunk fails; the later ones
depend on earlier local changes), and the whole local series in number
order does not reproduce `4bf152e4` either (fix 25 fails; other local
commits are not patch files) — the README says so, and reads the patches
as exact descriptions of each change. Data sends it himself.

## Part 5 — credits roll — credits roll: already clean

## Part 2 — fix 41, the proper version — **DONE: open fix 43 written, proved, parked**

1. **How F12 works, measured first** (the applied build, engine 113660 after
   part 1's baseline, SAVE4, `evidence/work_order_185/P2_f12_applied/`):
   F12 switches OrionLayer's own window to the engine's picture (381
   colours sampled, frame source `net`/`f12`), a forwarded click on the
   native COLONIES button opened the colony summary, ESC came back, F12
   returned to HD. **It works with fix 41**; what cannot happen is the
   engine's own window appearing (parked 2b).
2. **Open fix 43** (entry 43, `doc/ext_engine_window_on_request.patch`,
   reported by `version_check`, **check 090r #6** new): `ORION2RE_HIDE_WINDOW`
   decides the hidden start (replacing 41's `true`), `ext::Init` no longer
   forces it, `MSG_SHOW_WINDOW` (0x86) sets the atomic flag, the main thread
   applies a change once (show/hide, VSync again). Amends 41; revert =
   `patch -R`, back to 41. Mechanism and alternatives: parked 2a.
3. **Scratch**: worktree `wt43` of the scratch clone at `4bf152e4`
   (commit `f110592e`), its own build directory `build43`, vendors copied,
   the preset's variables; built exit 0. Proof: the patch FILE applied to a
   fresh worktree at `4bf152e4` (`patch -p1 --dry-run`, then `patch -p1`,
   no offset, no fuzz), byte for byte the scratch commit's five files;
   `ext_api.cpp`, `ext_server.cpp`, `platform.cpp` compile alone with the
   build's own command; the control `MSG_SHOW_WINDW` refused.
4. **Live on Xvfb** (every start `engine_start.py --engine`, guards
   `185_P2_noenv`, `185_P2_env`, `185_P2_control`, each verified identical):
   without the variable IsViewable, hide → IsUnMapped, show → IsViewable;
   with it IsUnMapped from the start, the skip arrives, show/hide work;
   pacing 6.05/s, 165.0 ms; control: the applied build ignores the message.
   (The first probe read "no window" — it lacked the private Xvfb's cookie;
   with `XAUTHORITY` set it saw the window.)
5. **The new check caught the author**: its first run failed on
   `+#include <atomic>` in `ext_api.h`, a changed place without the marker.
   The marker was added there (a comment), the scratch commit amended
   (`884c727e` → `f110592e`), rebuilt, the patch regenerated, and the
   apply, compile and control proofs run again on the new file — all as
   before. The live results above were measured on `884c727e`; the two
   differ in that one comment.
6. HD side described in entry 43, not committed. **Checks 386 → 387.**

## Part 3 — decision drafts — **DONE**

`doc/briefs/185-decision-drafts.md`: draft 1, the flash rule of 180 (for
part 02, after decision 22 "Graceful fallback."), from 180's proposed text
with the snapshot rates measured since (36 snapshots ≈ 2 s on the map, ≈ 6
s at the main menu), 166 A's waiting overlay, `claims`, the replay check
and the live walk; draft 2, the player's start of 183 (for part 02, after
decision 39), from 183's proposed text with the fix 41 consequences as
they stand — F12 stated as measured in part 2 — and the pointer to open
fix 43. Placeholders `<number: Data>`; nothing written into
`doc/fundament/`.

## Part 6 — Ship Designer: reading report and brief — **DONE**

1. **The reading**: `doc/ship_designer_reading.md` — drafted by a read-only
   agent over `design_main.cpp`, `design.cpp`, `desbox.cpp`,
   `design_config.cpp`, then checked at the tree before use: the way in
   (only the build popup: Design + a design row, Refit + the custom row),
   Cancel / Build back to it, the save (`Update_Player_Design_`), the one
   input delay (20 passes, before the weapon picker), the in-progress
   struct (corrected to orion2.h:702-743), no design data on the wire, no
   other writer of SCREEN_DESIGN, what the page prints and computes, what
   each picker prints. Every sub-dialog: the shield/computer picker, the
   weapon picker (filters, arcs, racks, modifications, Accept), the special
   picker, the hull buttons, the name field, the warning boxes; what a
   finished design becomes (the slot is overwritten; no list-full case).
   The table says, piece by piece, what is on the wire today.
2. **Open fixes 44 and 45** (entries, patches, rows, `version_check`
   REPORTED, **check 090r #7** new): "DSGN" — the edit, slot, refit flag,
   printed numbers, computed stats, engine-formatted weapon strings; ids
   54/55/56 for the three pickers and "DSBX" — their state and rows by the
   same calls as their drawing. Scratch worktree `wt44` at `4bf152e4`, its
   own build directory `build44`, commits `ef021842` (44) and `cc0becc9`
   (45), built exit 0 after each; both patch files applied cleanly (44 on
   `4bf152e4`, 45 on top of it), byte for byte the scratch commits, each
   changed .cpp compiling alone, both misspelt-constant controls refused.
3. **Recorded live** (scratch engine 132355, guard `185_P6_record`, SAVE4;
   a scratch recorder, every send decided from the list read then):
   DSGN on the designer agrees with the native page value for value (slot 0
   "Scout"); the shield field with nothing researched gives the warning box
   under 3 (the first run left it open — its script escaped only on an id
   change; the second dismissed it through the box's full-screen field and
   edited slot 1 "Rafale"); 54 / 55 / 56 with DSBX, the weapon picker's rows
   equal to the native picker's. Reader: `core/designblocks.py` (new,
   `game_state` calls it after the colony blocks; inert without the blocks).
4. **The brief**: `doc/brief_ship_designer.md` (no line numbers) — the
   claim rule (no DSGN, no claim: the safety net as today), the HUD layout
   area by area with each value's source, the original graphics adopted
   (SHIPS.LBX pictures through the Fleets extraction, DESIGN.LBX's arc
   pictures) and not (its chrome — decision 71), the input path (hull
   buttons by injected click, everything else by activation found in the
   live list, the name UNVERIFIED), the markers, the texts.
5. **No engine fix for texts or pictures**: every name is in TECHNAME.LBX,
   descriptions and notes in TECHDESC.LBX, pictures in SHIPS.LBX /
   DESIGN.LBX — HD extractions (part 7).
6. Checks 387 → 388.

## Part 7 — Ship Designer HD screen — **DONE (built against the recorded blocks; fixes 44/45 NOT applied)**

1. **`screens/ship_design/`** (id 3) and **`screens/design_box/`** (54, 55,
   56 — one overlay over the page; the dispatcher maps and keeps it through
   `EXTRA_SCREEN_IDS`, new). Both claim only with open fix 44's DSGN (and 45's
   DSBX): on the engine `play.py` starts nothing changes — id 3 stays the
   game's picture. The page draws every value from DSGN, the pickers every
   row and number from DSBX; each picker is laid from the base its catch-all
   field gives. Under a picker the page draws from the design and its own
   last list (nothing is sent from it). Inputs: activation of the field found
   in the list now; a hull by injected click; refusals for a hidden hull, a
   hidden plus, Build without its button, Accept only hidden; a click outside
   a picker sends its full-screen field (the original closes there).
2. **Texts and art**: TECHNAME's designer tables (`core/shipparts.py`),
   TECHDESC (`core/techdesc.py`, `tools/techdesc_extract.py`), DESIGN.LBX's
   arc pictures, arc and rack words and filter buttons
   (`tools/design_art_extract.py`, format 2), the ship pictures through the
   Fleets extraction. OrionLayer's own words (titles, button words) in
   `screens/ship_design/sdtexts.py`, moddable (decision 73). Stand-ins for
   the suite (`tools/make_derived_fixtures.py`: designer tables, TECHDESC).
3. **Open fix 45 amended** by one word — which modifications the weapon
   picker offers (the field list alone cannot say which mod a field is).
   Scratch commit `cc0becc9` → `ce56babd`; every proof again: applied on
   `4bf152e4` + fix 44 with no offset and no fuzz, equal to the commit, the
   engine rebuilt, `ext_api.cpp` compiled alone exit 0, the misspelt
   `_weapon_replacment_rack` control refused exit 1. Entry 45 and the patch
   file updated; `core/designblocks.py` reads the word.
4. **Live, scratch engine** (`build44`, PID 136228, guard `185_P7_walk`,
   Xvfb, SAVE4, nothing saved; `tools/design_walk.py`, new, input log on):
   build popup → designer → computer / weapon / special picker and back
   (ESC) → popup → colony → map at **1920x1080 (13 transitions) and
   2576x1432 (11), 0 native frames**. The weapon picker offered mods
   10, 11, 12 (ECCM, Heavily Armored, Fast), as the native picker shows.
   SAVE1-9 and SAVE11 identical, SAVE10 unchanged; `liveguard verify`:
   MOX.SET changed (the game rewrites it on load) → restored from the guard
   taken before the engine existed; verify then clean. Evidence
   `work_order_185/P7_design_*`.
5. **Fixtures**: `tools/fixtures/design_blocks_185.json` (cut by
   `tools/design_fixture.py` from the 1920 walk); `transitions_180.json`
   rebuilt from 180/181's folders plus the two walks (198 → 220; the old
   set reproduced byte for byte first).
6. **Checks 388 → 398** (fast 378 → 388, modules 141 → 143): **090x**
   (ship_design, 6) and **090y** (design_box, 4); 004 now also reads
   `EXTRA_SCREEN_IDS`; 017's marked-file inventory, 062's absent-ok list
   and 055's help note gained the new files. 090t stages both screens
   (the special picker over the page) from the committed stand-in, with the
   text stand-ins where the player's files are absent. Full suite green.
7. **Marks** (module, status document, check): page — DEVIATION
   `hud_frameless`, `button_words`, `row_help`; HD EXTENSION `title`;
   OMISSION `hover_messages`, `flashing_hover`; UNVERIFIED `name_entry`,
   `fix44`. Pickers — DEVIATION `hud_frameless`, `button_words`,
   `filter_art`, `centring_swap`; HD EXTENSION `box_titles`; INVENTION
   `chosen_fill`; OMISSION `no_weapon_damage`, `fit_colour`,
   `flashing_hover`, `picker_help`; UNVERIFIED `fix45`.

## Part 8 — Ship Designer live test — **DONE (3 differences: 1 fixed, 2 questions; unreachable states parked)**

Scratch engine `build44` (PID 139760, Xvfb, guard `185_P8_live`, SAVE4,
nothing saved; scratch driver, every input through the HD window, input log
on). 16 states, each HD beside the game's frame of the same moment
(`work_order_185/P8_live_1920x1080/pairs/`): the page; the shield panel's
warning box (held, then the game's picture, answered by a click in HD's
window); the page after it; the computer picker; the weapon picker; Laser
Cannon chosen (arc box, Forward lit, Heavy Mount / Point Defense offered);
Fwd Ext chosen (1-6, 12, 25); a modification on; the MISSILE filter off
(the missile row gone, the button dim); ESC back; the special picker;
Augmented Engines added (cost 89, space 32, 19 combat speed); plus on the
first weapon row ("Nuclear Missiles (3)" ×2); Cruiser (293, 120);
Clear; Cancel back to the popup. **Every number, word, arc, filter state
and row agrees with the native frame.** Differences (parked 2c): the
warning box shows after 3.76 s (the gate's modal hold — question); the
chosen hull is faintly marked and its word small (question); a
modification that is on was drawn as off — **fixed** (lit fill, INVENTION
`chosen_fill` widened, 090y asserts it). 0 native frames on every
transition. SAVE1-9 and SAVE11 identical, SAVE10 unchanged; MOX.SET
rewritten by the game → restored from the pre-engine guard, verify clean.
States the save does not reach, and the save each needs: parked, section 3.
