Screen-id fix, update decision, then push

Read doc/v3_fundament.md first. Four steps, one stop at the end. Nothing else in this task — Task 2 starts after the push.

1. Apply the fix to Race_Selection_Screen_

Same form as the two Custom Race hunks in doc/ext_screen_id.patch: save MOX::_current_screen on entry, restore it before the cancel return 0 (the path reported at racesel.cpp:337-343 — re-anchor against the working tree). Guarded by #ifdef ORION2RE_EXT, comment in the same voice as the existing three, naming why: the caller (newgame.cpp) does not touch the id after a cancel, so the API keeps reporting the screen that is gone.

Accept path is left alone — the report established the original's own assignment at :692 runs first.

2. Regenerate the patch, do not edit it

doc/ext_screen_id.patch is regenerated the same way as before: working copy minus the point-5 line, diffed against git archive cf4d9617, forward-applied to a fresh export, byte-compared. Header updated to four guarded hunks, each named. The point-5 residual line stays documented in the header.

Then the pointers, never copies (fundament §2):

doc/orion2re_open_fixes.md, "Applied" section — the sentence that read as if everything was fine is corrected; the line count matches the patch header.
v3_projektstatus.md, loose ends — the item moves from "found" to "applied, awaiting live confirmation".
doc/orion2re_tree_comparison.md — racesel.cpp row: four guarded plus one unguarded, all to be re-set by hand on a C update.
3. Live confirmation — the acceptance criterion

Rebuild orion2re. Then, with OrionLayer connected: enter the race selection from New Game, cancel, read current_screen from the next snapshot. Expected: New Game's id, not SCREEN_RACE. Log line with timestamp in the report. Also confirm the two Custom Race hunks still behave (enter Custom Race → 50, cancel → back).

If the rebuild or the live test is not possible in this session, the report says so and the status item stays at "awaiting live confirmation" — it does not get promoted on the strength of the source reading.

4. Record the update decision

New entry in v3_projektstatus.md, its own phase number, title along the lines of "Update to upstream (build 15 Aug 2026) — DEFERRED". Decision: not during the colony screen work. Reason: nothing in the colony screen needs C; the update is four pieces, none skippable. Plan = the intersection table in doc/orion2re_tree_comparison.md:

platform.cpp pointer fix re-derived, not re-anchored
racesel.cpp: crash fix (point 5) plus the four screen-id hunks, by hand, file re-indented upstream
core/game_state.py and the struct specs to the new record sizes (s_ship_data, s_antaran, s_player variable); note the signedness change of food2_per_farmer / industry_per_worker in the colony spec
every line number in doc/ and core/structs/ re-anchored; coldraw.cpp and invasion.cpp least trustworthy

Two items that do NOT wait for the update, filed as open items in the same entry, to be scheduled before H1:

tools/version_check.py additionally reads GAME_BUILD_DATE and the record sizes from sizes.h that our specs cite
HELLO_REPLY carries the record sizes or a layout hash, additive in src/ext/; the client refuses on mismatch instead of reading offset
request to Joes in doc/orion2re_open_fixes.md: bump ENGINE_VERSION when record layouts change
Housekeeping

src.zip in the orion2re root is Data's own upload archive — add it to .gitignore there or note it in the comparison table as explained, so the next diff does not raise it again.

Stop

Smoke test green under SDL_VIDEODRIVER=dummy. Report: the four hunks, the live-test result (or why not), the status entry. Show the full diff. Data reads it and pushes.