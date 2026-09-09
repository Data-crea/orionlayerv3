Task 1 — cross-tree comparison

Read doc/v3_fundament.md first. This task reads and reports; it changes nothing in ~/orion2re and copies nothing between trees. The update itself is a separate decision after this report.

Data has downloaded a new upstream tree to ~/orion2re-main-neu. Three trees are involved:

A — ~/orion2re, Data's working tree with our patches
B — Joes' base our patches were applied to (cf4d9617), if an unmodified copy exists anywhere: the original clone, a previous zip, or git stash/branch state inside A
C — ~/orion2re-main-neu, the new download
Step 0 — identify C

A zip has no history. Establish what C is before diffing:

is there a .git directory? If yes, git log -1 gives the hash.
read src/version.h (ENGINE_VERSION) and src/game/consts.h (GAME_VERSION_LABEL). Report both literals; they can disagree.
if there is no hash and both literals still say 1.60.0, C's relation to cf4d9617 is unknown until step 2 answers it. Say so; do not assume C == B.

Also report whether B exists at all and where. If it does not, step 2 is impossible and must be reported as impossible — not reconstructed by subtracting known patches from A.

Step 1 — A against C (the original Task 1)

Diff the full trees, ignoring build output. One row per deviating file, category from the brief: ifdef-guarded / documented patch / Extension API (src/ext/) / unexplained.

The one line that decides the analysis's boundary section: does src/ext/ exist in C? If not, "untracked in Joes' tree" is confirmed. If it does, report what is in it and whether it matches ours — either answer changes doc/colsum_design_analysis.md §3.

Verify the count of hunks in files Joes owns. The analysis claims exactly one (platform.cpp, doc/ext_inject_click.patch); there is also doc/ext_ship_icon_owner.patch in the tree. Reconcile.

Step 2 — B against C (what Joes changed)

Only if B exists. Diff the full trees, list every changed file. This is upstream progress, not our concern to categorise — but note any file that doc/v3_orion2re_index.md, doc/s_colony_offsets.md or core/structs/ cites by line number, because those citations may have moved.

Check specifically: src/version.h, src/game/consts.h, src/ext/ (if present), src/game/platform.cpp, orion2.h, sizes.h, pop.h, and every file in the colony chain (colsum.cpp, coldraw.cpp, colmove.cpp, colcalc*.cpp, settler.cpp).

Step 3 — the intersection

Every file that appears in BOTH step 1 and step 2 is a file Joes changed that we also patched. That list is the merge risk and the point of this task. For each: the hunk on our side, the hunk on Joes' side, and whether they touch the same lines.

Report

A table in doc/ — one file, and every other document points at it (fundament §2, "a name table copied into three files"):

what C is, and how that is known (hash / literals / unknown)
whether B exists and where
step 1 table, with the src/ext/ answer as its own line
step 2 file list, with the citation-affected files marked
step 3 intersection, or "empty"
zero rows in "unexplained", or each one named as an open item

Then stop. No merge, no copy, no push. Data decides the update after reading the intersection.

Housekeeping before starting: the five review files in the working directory (diff*.txt and the two from the less redirect) go into .gitignore or out of the tree — a diff log committed is a derived file under decision 40.