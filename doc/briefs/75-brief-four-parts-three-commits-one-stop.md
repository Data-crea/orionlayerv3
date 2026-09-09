Brief — Four parts, three commits, one stop

Read doc/v3_fundament.md before touching anything. This brief sets direction and acceptance criteria; every number, line and offset is yours to establish and report. Tree state: ac5b86f pushed, working tree clean, manifest correction held.

Four parts. A, C and D each end in their own commit; B is a report with no code. Run them in this order, stop once at the end with one report that has a section per part. Data pushes all three commits after reviewing. If a part blocks — a missing file, a decision only Data can take — write down where it stopped and continue with the next; do not wait mid-brief.

Part A — the column-2 rule (commit 1)

The diagnosis stands as reported: the move writes pops only to the moved colony; Pass_Out_Imports_ rewrites imports on every colony of the owner and pop_growth / pop_roundoff / specialty on every needy one. Not column 2, not the neighbour.

The rule as stated in the Part B diagnosis, item 4, in one place both tools read (colony_move_hd.py, colony_move_probe.py), not two copies.

Prove it can fail before it is trusted. Three synthetic diffs against the rule function, each a pasted red line in the report: (a) a second colony whose pop[] changed; (b) a second colony whose production changed; (c) a non-needy colony whose pop_growth changed. If the rule accepts any of these, it is a tolerance.

Then the live proof: column-2 PICK and DROP on the reference save, the pop word diffed against the prediction, output in the report. The status entry closes with it.

Same commit:

Decision 48: Enforce_Population_Limits_At_Colony_ is not on the pop-move write path — say so where it is named, and name Pass_Out_Imports_ / Post_Import_Computing_ as the cross-colony writers with file:line.
doc/v3_orion2re_index.md: the pop-move write path from Send_Cluster_ down to Pass_Out_Imports_, with the needy-colony condition.
Fundament section 3, if not already there in substance: a pop move recalculates the whole player's food distribution; other colonies legitimately change in imports, needy ones additionally in pop_growth, pop_roundoff, specialty.
Fundament section 2, Evidence, if it is not already covered by "read the function that BUILDS the thing": the "always the next index" pattern was five needy colonies walked round-robin — a pattern in three observations is not a rule until the writer says it is. Say whether it is a new line or the existing one.
The held manifest correction.
Part B — Stage 3 Stop 1, the assets stop (report only, no code)

Stage 3 replaces cells with figures. Nothing is drawn before this stop is answered. Standing decisions from Data: the sprite carries the identity, no letter; the squish is transcribed at the sprite step (now FIGURE_STEP), HD width goes to the reservation. New decisions from Data, 7 September:

A user supplies one master per figure; the 2×/3×/4× steps are built from it, as the frame plate is — setup.py step, derived files never committed (decision 49 as the pattern).
A user master that fails the dimension check is not drawn: the original is used and the log names the file and the reason. No silent fallback.
Modding is in from the first figure, not added after: a user who drops assets into the mod folder sees them; the original is only the fallback.

Report, in this order:

Artwork inventory. What figure artwork exists in the tree and in Data's folders, against brief_pop_sprites_assets.md: which race × job combinations are present, which are missing, at what pixel size, and whether each master fits the step rule once the dimension comes from the table (decision 26 — "an asset is not a measurement"). Any master that cannot serve 4× without upscaling is reported as an interim, dated. Also: which of the original's own figure sprites (LBX) can be extracted as the fallback set, by which existing tool or which new one, following the help_extract.py pattern — extracted from the user's installation, never committed, absence a state to explain.

Resolution rule. Does core/resources.py resolve a screen asset per file — a mod supplies three races, the base supplies ten — or does decision 17's whole-directory rule apply to screen assets as it does to skins? File and function. If per-file already exists, name the check that proves it; if not, draft the new decision (next free number, under Data and resources) with the mixed-style consequence named as the accepted price, for Data to confirm.

Identity. race_idx and MASK_CONQUERED for the loader: which field gives the figure's race, what a conquered population's figure should show (the original's behaviour, from coldraw.cpp or wherever it draws them — file and line), and the two sources for the field. Pop nibble sentinels 8 and 9 (Android, Native): Native exists in the reference save (Urna I); what the loader does for Android until a save with one exists.

Loader chain. Master → steps → tinted or not (decision 29 applies only if the original palette-swaps figures; say whether it does) → cache → draw. One function for the figure rect that both drawing and slot_click_x read (decision 5). Where the three homes for the markings will be.

Acceptance criteria you will be held to at Stop 2, written out so Data can strike or add: a test mod with one user master that appears on screen while every other figure is original; the same master at a wrong size, named in the log and not drawn; both asserted in the smoke test without a screenshot; squish visible as overlap as in the original, Blucher II's farmers beside the native; PICK and DROP per column re-proven with the Part A rule.

No code in Part B. If the inventory finds a blocker — no fallback extractor, no artwork at 4× — that is the report's first line.

Part C — the BUILDING column (commit 2)

Every row carries producing='', so the column draws nothing while the original shows "Trade Goods - 1t". The horizon lists techname.lbx extraction as the source for the producing sort key and the building name.

Follow the HELP.LBX pattern exactly (decision 38): an extractor under tools/ that moves bytes untouched, a derived file with a format version, never committed, decoding at load time, absence a state the screen explains — the column shows the "not extracted yet" wording from assets/shared/help/labels.json or its sibling, not nothing.

Two sources for the mapping: the LBX entry index the colony record carries, and the original's own rendering on the reference save (the framebuffer shows the text; the extracted table must agree for every visible row). The "- 1t" suffix: find where the original computes it (turns remaining) and transcribe; if it is a computed value we cannot reproduce from the snapshot, show the name only and mark the suffix as open, not approximate it.

Acceptance: BUILDING filled on the reference save, every visible row matching the native ×3 crop; a smoke check that compares the extracted names against a pinned list from the reference save and reports "absent, run this" when the file is missing; producing sort works on the extracted key; the extractor added to setup.py STEPS. Evidence crop beside the native.

If the LBX is not where the pattern expects or needs a decoder the help extractor does not have, report and stop this part; do not build a second string-format interpreter without saying so.

Part D — scroll arrows (commit 3)

The header's 36 px slot and the list's bottom have no control; the original has arrows there (_x_fields[1]/[2], Decrement_First_/Increment_First_, colsum.cpp:211-226) and colonysend already activates both. "1 more not shown" is text.

Draw the two arrows where the original has them, as boxes in boxes.json if they are cutout-derived and as thin_border or text skin boxes if not (decisions 34/37 — say which and why). Click activates the field the original activates, through colonysend, and the HD list's own Window.top moves with it (decision 46: HD scrolls freely for viewing; _first is re-established before injection — state how the arrow keeps the two in step). The text line goes.

Acceptance: arrows visible at three resolutions beside the native; one click on each arrow live on the reference save, the game's _first on the wire before and after in the report; smoke check that the two arrow rects come from the same geometry function as the list rows' hit-test.

The report

One report, four sections, in order. Per commit: hash, diff summary, smoke count. Per part that blocked: where and why. Reference save preserved; hashes reported. Evidence under ~/Bilder/rahmen/ with hash in the name, manifest updated. No orion2re changes expected; if one is needed, the conditional permission applies and it is reported, not applied silently. No push.

Standing rules
Two independent sources before any production value.
No number in a doc that a check does not read.
Nothing deleted from the old modules; marker re-targeting is Stage 5, in the same commit as deletion.
A derived file needs a regeneration path in setup.py and a check that says "absent, run this" rather than skipping.