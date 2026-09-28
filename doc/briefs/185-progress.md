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

## Part 9 — the diplomacy audience: reading, brief, open fixes — **DONE**

1. **The reading** `doc/audience_reading.md` (read-only, every citation
   `file:line` at `4bf152e4`; 30 of them re-checked before filing, all
   agreed): there is no audience screen id — it is a nested call under its
   caller's id (6 Races, 0 a turn-start report, 12 a sneak attack); what it
   shows (DIPLOMAT.LBX room and ambassador, DIPLOMSx statements, JIMTEXT
   menus); every menu the player can open; the AI's replies; every way in
   and out; what each outcome writes; the globals; the input delays; what
   is on the wire.
2. **163's parked line** (open question 3 of `doc/ai_behaviour_reading.md`)
   answered there: the player records are on the wire whole, during an
   audience too, and `objectives`, `relations` and the treaty arrays are
   declared already; what is missing is the audience's own state. Stale
   claims corrected: `doc/pop_order_reading.md` ("nothing on the wire
   reports objectives"), `doc/races_screen_reading.md` (the spec status,
   the ext_api line numbers).
3. **Open fixes 46 and 47** (entries, rows, patches, `version_check`
   REPORTED, **check 090r #8**): 46 — the player's audience reports 57, the
   AI's (turn start and sneak attack) 58, through ScreenOverride; 47 —
   `Get_List_Field_` records its running list, and a "DIPL" block between
   INFS and COLS carries the ambassador, the option, the statement id, the
   reply text as rendered, and the menu with its enable flags. Scratch
   worktree `wt46` at `4bf152e4`, own build directory `build46`; commits
   `453c4c05` (46), `20f5f920` (47), each built exit 0; both files applied
   with no offset and no fuzz (47 on 46), equal to the commits; each
   changed .cpp compiled alone (exit 0); controls refused (exit 1:
   `ScreenOveride`, `_respons_message`). 46's header note first sat on the
   lines fix 45 changes — moved below the struct, so 44+45+46+47 apply
   together on `4bf152e4` (offsets only, no fuzz, no reject). A first
   compile run appended a second `-o` and failed for that reason — its
   numbers were discarded and the run repeated correctly.
4. **Recorded live** (engine `build46`, PID 146097, guard
   `185_P9_audience`, Xvfb, SAVE4, nothing agreed; scratch recorder, input
   log on): race slot 0 → 57, the refusal (option 0, statement 126); race
   slot 1 → 57, the greeting, then the menu (title, four items, Peace
   Treaty disabled), Good Bye by activation → 6. The reply text changed
   between greeting and menu under one statement id. SAVE1-9 and SAVE11
   identical, SAVE10 unchanged; MOX.SET rewritten → restored from the
   pre-engine guard, verify clean. The AI's 58 needs a turn start with a
   diplomacy message: not reachable without TURN — parked (part 11).
5. **Client side**: `core/diplblocks.py` (read between INFS and COLS, whole
   or None), `tools/audience_fixture.py` → `tools/fixtures/
   audience_blocks_185.json`. **Found on the way**: the committed fixtures
   must not carry the game's words — the audience's replies and menus, and
   in part 7's designer fixture the design name and the modification
   words. Both cutters now replace every text with a stand-in (`neutral`);
   the designer fixture is re-cut (part 7's commit `6f0570c` still holds
   the two short strings, hex-encoded; superseded, not rewritten).
6. **The brief** `doc/brief_audience.md`: ids 57/58 on one screen, the
   original's room and ambassador as the stage, HUD reply and menu panels,
   items by activation (measured), disabled items refused, the markers.
7. Checks 398 → 399 (090r #8). The DIPL parse check is written and waits
   for part 10: a check group must name a screen folder, and
   `screens/audience/` is part 10's.

## Part 10 — the audience HD screen — **DONE (built against the recorded blocks; fixes 46/47 NOT applied)**

1. **`screens/audience/`** (ids 57 and 58, one screen via `EXTRA_SCREEN_IDS`;
   `core/screen_names.py` 57/58): claims only with DIPL. The stage is the
   original's own art — the race's room and ambassador out of DIPLOMAT.LBX
   (`tools/audience_art_extract.py`, new, raw blobs, gitignored;
   `screens/audience/auart.py`), no ambassador when refused, black filled
   only under the room (without the art the panels stand on the universal
   background — 006f's glass rule caught the opaque stage). HUD panels:
   the statement as the engine rendered it in the original's column (x 80,
   470 wide, centred on y 440), the menu at the list's own fields with its
   title, disabled items dimmed. States off the live list: MENU,
   STATEMENT, else GAME_BOX (the system picker, a list that disagrees) —
   modal, the game's picture.
2. **Input**: an enabled item's field by activation, a statement's one
   field on any click, a disabled item refused; no keys (the list has no
   hotkeys).
3. **Live walk** (`tools/audience_walk.py`, new; engine `build46`, PID
   148507, guard `185_P10_walk`, Xvfb, SAVE4, input log on): Races →
   refused audience → click → Races; Races → greeting → click → menu → Good
   Bye → Races; ESC to the map — at 1920x1080 (9 transitions) and 2576x1432
   (7), **0 native frames**, every audience input sent by the HD screen.
   SAVE1-9, SAVE11 identical, SAVE10 unchanged; MOX.SET → restored from the
   pre-engine guard, verify clean. `transitions_180.json` 220 → 233.
4. **Checks 399 → 405**: 090z gains 5 (claim and states, sends, draws at
   three sizes and marks, art loader and extractor entries, recorded ways);
   the DIPL parse check held from part 9 lands with it. 090t stages the
   audience from its stand-in (`tools/standins.py`, new — moved out of
   `tools/hud_evidence.py`, which the new staging had pushed over 300 code
   lines).
5. **Marks**: DEVIATION `hud_frameless`; OMISSION `talking_loop`,
   `header_line`, `glass_remap` (the ambassador's glassed pixels drawn as
   their indices — a hatching; the original remaps them against the room),
   `audience_help`; UNVERIFIED `fix46`, `fix47`.

## Part 11 — the audience live test — **DONE (2 fixed, 2 questions; the AI audience parked)**

Engine `build46` (PIDs 148507 for part 10's walk, 150365 here; guards
`185_P10_walk`, `185_P11_live`; Xvfb, SAVE4, nothing saved; input log on).
Every state HD beside the game's frame of the same moment
(`work_order_185/P10_audience_1920x1080/pairs/`, `P11_audience_1920x1080/pairs/`):
the refusal (no ambassador — as the original), the greeting, the menu
"How may I serve you:" (Peace Treaty disabled, as the list's flag says),
Declare War's confirmation "REALLY DECLARE WAR?!" (Yes / Cancel — answered
Cancel through the HD screen; nothing declared), back to the menu, Good
Bye. The room, the ambassador, the words, the flags and the line breaks
agree with the native frames. Differences:
- the statement and the menu were drawn at 9 native px against the
  original's style-4 font — **fixed**: 16 native px, taken from the list's
  own 21-px row pitch (`augeom.TEXT_PX`), the statement centred as FMTPARA
  mode 2 centres it (fmtpara.cpp:1701-1702); the re-render breaks the
  line where the native frame does;
- the fade-in is not played (the native greeting frame is mid-fade) —
  **marked** OMISSION `fade_in`, question (parked 2d);
- the header line is not drawn — question (parked 2d);
- the ambassador's hatching: the native framebuffer shows the same, so
  `glass_remap`'s text now says so.
A first run answered the confirmation with "no" (no such item — nothing
sent); the second answered Cancel. 0 native frames. SAVE1-9, SAVE11
identical, SAVE10 unchanged; MOX.SET → restored from the pre-engine guard,
verify clean. **The AI's audience (58)** needs a turn start — parked with
the save and permission it needs (section 3).

## Part 12 — gates and push — **DONE**

- **The full suite**: exit 0, **405 green** (before the part 11 commit;
  each commit's own fast tier, 395).
- **A fresh clone** (`git clone --no-hardlinks` at `8956d54`,
  `tools/setup.py`): setup **exit 0**, its own verification the full
  suite, **405 green**. (A bare suite run in the clone before setup fails
  on the galaxy map's generated icons, as it always has — setup builds
  them; the gate is setup's run.)
- **The flash check**: 090o replaying 233 recorded transitions, green in
  both runs; live, `tools/flash_walk.py` on the engine `play.py` starts
  (orionlayer-local, fixes 44-47 not applied; guard `185_P12_flash`):
  **29 transitions, 0 native frames**; and 0 native frames in every live
  run of parts 7, 8, 10 and 11 on the scratch engines.
- **liveguard**: every session verified after its engine stopped; MOX.SET,
  rewritten by the game on each load, restored each time from the guard
  taken before that engine existed; final verify against this order's
  first backup (`185_P1_patched`): every game file identical — only the
  tree's recorded `git status` differs, by this order's commits (the tree
  is clean).
- **orion2re unchanged**: no commit on orionlayer-local, no fix applied;
  every engine change lives in scratch worktrees (`wt43`, `wt44`, `wt46`)
  of a scratch clone, with their own build directories; the build
  `play.py` starts was not rebuilt.
- **Push**: `git push` (no force), ten commits, the pre-push hook's full
  suite.

## End of work order 185

**Done**: parts 1-12 — fix 42's gap clicks (none lost), fix 43, the two
decision drafts, the handover package for Joes (outside the repo), the
credits roll (already clean), the Ship Designer read, built, walked and
compared, the diplomacy audience read, built, walked and compared.

**Parked for Data** (`doc/briefs/185-parked-for-data.md`): the open fixes
below; the F12 question (2b); the designer's three differences (2c: the
warning box's 3.8 s hold, the chosen hull's marking); the audience's two
(2d: the header line, the fade-in and talking loop); the states the
scratch save does not reach, each with the save it needs, including the
AI's turn-start audience (58); the carried-over items (section 4).

**Every open fix awaiting approval:**
- **42 — A screen is silent on the wire while its input delay counts
  down.** Ticks during an input delay so a screen's list reaches a client
  when it is built — the research panel's entry 636-686 → 77-103 ms, no
  input lost or taken twice.
- **43 — The engine's window: hidden only when OrionLayer starts it, and
  shown again on request.** Amends 41: an engine started on its own is
  visible again, and a client can show and hide its window (F12).
- **44 — The Ship Designer's design as it is being edited.** Puts the
  design, the slot and the page's printed numbers on the wire ("DSGN"), so
  the designer's page can be HD.
- **45 — The Ship Designer's sub-dialogs: which is open, and what it
  offers.** Ids 54-56 and their rows ("DSBX", amended in part 7 by the
  offered modifications), so the three pickers can be HD.
- **46 — The diplomacy audience has no screen id.** Ids 57 (the player's)
  and 58 (an AI's, turn start and sneak attack), so a client can tell an
  audience is up and whose.
- **47 — The diplomacy audience's state is not on the wire.** "DIPL": who,
  the statement, the reply text as rendered, the menu and which items are
  enabled, so the audience can be HD.
