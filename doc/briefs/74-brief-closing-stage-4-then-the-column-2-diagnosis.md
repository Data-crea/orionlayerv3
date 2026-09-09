Brief — Closing Stage 4, then the column-2 diagnosis

Read doc/v3_fundament.md before touching anything. This brief sets direction and acceptance criteria; every number, line and offset is yours to establish and report. Tree state: d0abd07 pushed; Stage 4 Stops 2 and 3 sit uncommitted on top (14 modified, 2 new). Stop 3 is accepted with one open item (column 2) that blocks Stage 3.

Two parts. Part A closes Stage 4 in one commit, which Data pushes. Part B is a reading task that reports before it changes anything.

Part A — close Stage 4
A1. Pitch scale — verify, and change if it is the excluded case

The stacking decision: the squish is transcribed in native units, with the same integer step as the sprites (2×/3×/4×); HD extra width goes into the column reservation, never into figure spacing. Stop 3 says the cell pitch is "scaled by HD-over-native column width".

State which factor colonyicons.column_pitch applies: the sprite step, or the ratio of the HD column to the native one (342 : 135). If the ratio: that is the excluded case, and Stage 3's sprites would move every cell and every drop target again. Change it to the sprite step. Either way: name the step at each of the three resolutions, the table it comes from (zoomtables.py, decision 26), and confirm the click path reads the same value — one function (decision 5). Evidence: Blucher II's farmers beside the native at the same scale.

If the step-based pitch overflows a column at some count, that is a finding for the report, not a reason to fall back to the ratio: say at which count and which resolution, and what the original does at that count (the original's column is also fixed and also fills).

A2. 2160p empire stats — fix if confirmed

At 3840×2160 the six values in empire_stats render at roughly twice the intended size and collide with their labels; 1080p and 1440p are correct. Does that box's text read the scale twice — box_font_scale and Layout.font_size both applied? This is the help-popup class of fault (fundament: "scaling twice looks correct at the resolution you tested").

If confirmed: fix, plus a check that renders the box at all three resolutions and asserts the value glyphs stay inside the box and clear of the label — same shape as the help-popup check. Then grep for the same double read in every other box that must work at an untuned resolution; report what you found, fix what you found.

A3. Three verifications from the Stop 3 images

List window. Ours shows Blucher II…Wolf II with one more not shown; the native ×3 shows Blucher III…Woz III. Does our first row come from the game's _first or from our own scroll state? If both images are from one game state they must agree; if they are not, the manifest names the moment each was taken. If ours ignores _first, say so and whether it is a Stage 3 or a Stage 5 item.

Empire values. Income +45 / +42, Food -1 / -3, Research 25 / 27 between ours and the native. Different moments (after the PICK/DROP runs would explain all three), or our own computation (colonyempire, decision 44)? State which, and the second source for each of the three values. If any value is ours by computation and has no second source, it goes to the status document as unverified, not into the screen as fact.

Scroll. The header's 36 px slot is empty and "1 more not shown" is text at the list's bottom-left; the original has arrows. Marked interim or missing? Status entry either way, and if interim, the stage that replaces it.

A4. Fundament and status
Fundament, section 2, Evidence: the wrong-game runs. A tool that reads a save identifies it before it reports; a proof that does not say what it is about is not a proof. Three acceptance runs, every line true, none of it evidence. Check whether it is a sibling of "a test that reads the user's disk" or its own line — say which.
Status document: the column-2 entry with the exact lines from both tools (colony_move_hd.py, colony_move_probe.py), marked as blocking Stage 3.
Status document: planet_info open item and the plate-height table as already reported; scroll and empire-value entries from A3.
Fundament and status agree with each other; CLAUDE.md count only.
A5. Commit

One commit for Stage 4, with A1–A4 in it. Smoke green, count reported. Reference save preserved; hashes reported. Evidence images under ~/Bilder/rahmen/ with hash in the name, manifest updated for anything A1–A3 changed. Report the diff summary and stop. Data pushes.

Part B — the column-2 diagnosis (after the push)

Column 2 (scientists) fails the "exactly one colony changed" rule on the reference save: a second colony's bytes change, always the next index, reproducibly, and the native-click probe shows the same shape — so it is the game's behaviour or the rule's, not HD geometry. Not diagnosed, not loosened, not assumed benign.

Read the function that writes, not the ones that read.

Which bytes of colony 12 changed — by field, through core/structs specs, not by offset. Pop word, or something else (a research-derived field, morale, anything empire-wide a scientist move touches)? If it is not the pop word, the rule in both tools is measuring the wrong thing.
Is it column 2, or is it the neighbour? The same move as a farmer and as a worker at the same colony on the reference save. Say what separates the cases.
The write path. Decision 48 names Enforce_Population_Limits_At_Colony_. What does a pop move touch beyond the moved colony, under what condition, file and line. If a second function is involved, name it the same way.
The rule becomes a rule with a source. Either "exactly one colony" with the reason the game guarantees it, or "the moved colony plus the fields X the game rewrites" with the file:line that rewrites them. Not a widened tolerance, not a special case for one save.

Report before changing either tool. Then, with the go: both tools carry the sourced rule, the column-2 PICK and DROP are re-run on the reference save, and the status entry closes with the output. No orion2re changes expected; if one is needed, the conditional permission from the Stage B/C brief applies and it is reported before, not after. Reference save preserved; hashes reported. No push.

Standing rules
Two independent sources before any production value.
No number in a doc that a check does not read.
Nothing deleted from the old modules; marker re-targeting is Stage 5, in the same commit as deletion.
Screenshot questions answered with a crop beside the native at the same scale.