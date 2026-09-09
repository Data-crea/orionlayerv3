Colony summary — finishing brief

Written 5 September 2026 after a review of colsum_design_analysis.md against the repo at ccf7e0c. Read doc/v3_fundament.md (repo copy, decisions through 47) before anything below. Every line number cited in the analysis was read against cf4d9617 and a4dbee0; re-anchor against the working tree before it becomes a permanent citation.

Tasks run in this order. Each has a reporting stop; do not start the next one before the stop is answered.

0. Housekeeping (no code)
Move colsum_design_analysis.md into doc/ and commit it. Nothing below may cite a document that exists only in an upload.
The analysis and the HD-track chat design disagree on three points and the chat design is written down nowhere. Record that in the status document as an open design question, not as a decision.

Stop: confirm the file is in doc/ and the status entry exists.

1. Cross-tree diff — the precondition for every Level-2 item

Diff Data's orion2re against a fresh clone of Joes' at cf4d9617. Categorise every deviation: ifdef-guarded / documented patch / Extension API (src/ext/) / unexplained.

Acceptance:

A table in doc/ with one row per deviating file and its category.
The claim "src/ext/ is untracked in Joes' tree" is either confirmed by the diff or struck from the analysis. State which.
The list of hunks in files Joes owns. The analysis says exactly one (platform.cpp); verify the count.
Zero rows in "unexplained", or each one named as an open item.

Stop: report the table. H1 (task 5) does not start on an unverified boundary.

2. Phase 3b acceptance — close it before building on it

Acceptance (per the existing protocol): full colony diff before and after one move; abort path sends nothing on the wire; PNG render beside a native screenshot; colony index bound to name in the protocol; python tools/smoke_test.py green under SDL_VIDEODRIVER=dummy.

Carry-over items to clear here: RETURN-guidance message in layout.json under move for the held-cluster edge case; zoom_probe / park_game citations in Fundament section 3.

Stop: report pass/fail per criterion. No Phase 4 code on a red item.

3. Cell and context design — decide by picture, not by argument

Render both variants of each pair, side by side, next to a native screenshot, at 1920x1080 and one 4K resolution:

identity mark: glyph/letter in the cell (analysis §8) vs border/shading treatment (chat design)
context: hover-driven inspector in spare_panel (analysis §10) vs tooltip below the row — and state whether the tooltip variant overlays or reflows the list. If it reflows, it is out under decision 46 and need not be rendered.
confirm whether the analysis's "job band" is the same object as the chat design's blocker cell (one permanent cell per job group, acting as separator, drop target and icon carrier). If not, render both.

Test cells at the real cell size with a dashed free slot adjacent, so the collision the analysis predicts is visible or not.

Stop: PNGs only, no opinion. Data decides.

4. Phase 4 — Level-1 items (OrionLayer only)

After task 3 is decided. Everything here reads the snapshot and injects nothing new:

identity marks, four classes per Colony_Pop_Anim_; the android / native nibble assignment stays marked UNVERIFIED in the module and in the status document until a mixed-population save exists
inspector or tooltip, as decided in task 3; shows what a click would take (the preview cluster), nothing sent
warnings on the row from fields already present: food deficit, pollution, negative morale, No Farming, unassigned pops; on the left
HD-only filters (starving / idle / growing); filters never change the binding to the game's list
transit display from s_player.settlers[], marked HD EXTENSION

Not in this task: track width from empire maximum, row_height change. Both alter the horizontal click targets and wait for task 6.

Acceptance: each mark/warning has a smoke check that asserts the rule, not the instance (fundament §2); every HD extension is marked in module, status document and a check; PNG beside native; smoke green.

Stop: before writing code, report the file list and which checks will be added.

5. H1 — five screen-state values in the snapshot

Only after task 1 confirmed the boundary. _first, _g_sort_index, _list_col[10], _g_colony_n, _cluster_colony_n, additive in src/ext/, protocol version bumped. Nothing else from H2–H6 in the same change.

Acceptance:

colonyfirst.py (pixel reading of _first) is retired or demoted to a second source; state which and why.
The held cluster is read, not inferred.
_list_col is trusted only while current_screen == 20; a check asserts that.
Two independent sources for every offset (decision 23).
If any line outside src/ext/ is touched, stop and write it into doc/orion2re_open_fixes.md instead.

Stop: report the diff before build; Data pushes.

6. Track width and row count — after H1
Track width from the largest reachable max_pop in the empire. Define when it is recomputed; it must not change while an HD selection is held. Write the rule down and check it.
row_height 58 → 46 for thirteen rows. Confirm with a live move to a row outside the game's ten-slot window that window planning walks _first there first (decision 46 corollary).

Acceptance: move to row 12 succeeds with the correct colony (name bound in the protocol); smoke green; PNG beside native.

7. Status document — the honest end state

Write, verbatim in sense: the HD list screen manages pops fully; build selection, colony-to-colony transfer and the colony detail view hand off to the original framebuffer; OrionLayer requires the locally built orion2re with the platform.cpp hunk; building names appear only after the user runs the techname.lbx extractor; android/native identity is unverified until a mixed save exists.

Phase 5 candidates, listed, not started: transfer via H3, building column via H5, techname.lbx extractor.