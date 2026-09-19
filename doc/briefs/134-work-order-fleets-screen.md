Work order (next free number) — Fleets screen in one run: outer frame + screen

Read doc/v3_fundament.md and CLAUDE.md first, as always. Check the next free work-order, decision and Open Fix numbers before filing anything.

Goal

Build the Fleets screen in HD in one run, including its frame. There is no reporting stop. Anything that needs Data goes to doc/briefs/<n>-parked-for-data.md, and progress goes to doc/briefs/<n>-progress.md. Nothing is pushed.

Background from work order 134: the Planets frame does not fit Fleets as a whole. Data's decision: take only the outer ring. The Fleets regions are drawn inside it by the screen, with box skins.

Required reading before writing any code: doc/fleet_screen_reading.md (the fleet reading report from work order 126, part G) and the 134 results. Do not redo what they already settled.

Part A — Outer frame
Build a variant of the Planets frame artwork with the inner struts removed, so that exactly one opening remains (decision 12, frame variant, no runtime tile swapping). Cut from geometry, the way the galaxy frame v3 was done, not from a threshold.
Where the struts meet the outer ring there may be joint artwork. If removing it leaves a stub or a hole in the ring, do not paint in code. Instead, fill the spot from the ring's own artwork next to it, and report which spots you touched.
The single opening must hold the union of the Fleets regions at every resolution, and the inset map must keep its 1.676 aspect ratio. Report the margins in numbers.
Record provenance the same way as for the other frames.
Part B — Screen structure
Create screens/fleets/, with the screen ID taken from the source and auto-discovery (decision 7).
Inner regions (inset map, status line with PREV/NEXT, ship panel, large icon grid with scroll column, button band) are boxes in boxes.json and F5-editable. They are drawn with thin_border unless the panel-skin rule of decision 34 calls for inner_panel. Say which regions use which skin, and why.
The scroll column goes inside the grid region, and HD draws the scroll bar itself.
Draw and hit-test from one shared geometry (decision 5).
Wording comes from JSON or extractors, not from renderers (decision 15).
Part C — Data and input
First establish, from what is already on the wire, what the screen can show. Reconstruct derived state where the data provides a validation (decision 25). Check whether the existing ship-selection path (Open Fixes 20/21, MSG_SELECT_SHIP) already covers selection on this screen before designing anything new.
orion2re changes are allowed in this work order, but only for what the Fleets screen cannot get any other way, and only under the usual protocol:
one Open Fix entry for each change;
a patch file under doc/;
one commit per change on orionlayer-local;
a git bundle after every commit.
The hard rule stands without exception: orion2re is never uploaded anywhere. Before applying a patch, compare it with the reading report. If it grows beyond a read block plus the smallest necessary write commands, park it instead of building it.
Input rules: use ACTIVATE_FIELD where the target compares field IDs. Refuse input the game would refuse (decision 33). Never send into fields the reading report marks as dangerous.
The fallback must be loud: if required wire data is missing, the screen hands over to the original view (decision 22) and says why. It never shows guessed contents.
Part D — Checks and live acceptance
Add smoke checks on a real GameState, not a hand-built dummy (lesson from 130). Cover: frame opening versus regions, draw and hit-test agreement, the loud fallback, and the presence of the orion2re patches in version_check.py if any patches were made.
Live acceptance on scratch saves only, following the live protocol:
exactly one client;
hash SAVE1–SAVE9 and SAVE11 before and after (they must be identical), SAVE10 is only logged;
never use SAVE8;
livesend reads the field list before every send.
Acceptance means opening Fleets, PREV/NEXT across at least three fleets, selecting a ship, and each button once, all compared against the original.
If Data's own orion2re or OrionLayer is running, do not connect a second client. Park the live part with the exact steps instead.
Put headless renders at 1080p, 1440p, ultrawide and 2160p, next to the native screen, into ~/orionlayer-fixtures/evidence/work_order_<n>/.
Delivery
Use one commit per part, and the pre-commit hook must pass.
Update the status document. The screen stays marked "built, NOT accepted" until the live acceptance has passed.
File a new fundament entry only for a decision that is actually new.
Final report: commits, smoke count before and after, orion2re commits and bundles, evidence path, parked items.
