Run A — pop-move brief, sections 3b/3c only

Section 3a is answered: the corrected ten-drop table from Part I is the before-value. Do not re-measure. Instead, state from that table what a direct command can and cannot remove: which states are the click chain's own and go away with it, and which part is the game's recalculation and the snapshot cadence that no command can shorten. One paragraph, numbers from the table, filed beside the table in the status document. That is the sentence Data needs before agreeing to a patch in Joes' tree.

Then 3b, each answer from the function that builds the thing, with file and line:

what Give_Colonist_New_Job_ reads besides its arguments (_cluster_colony_n, screen state, any COLSUM/COLMOVE global); whether the recalculation can run once after several job changes or is triggered per pop — this decides one-pop-per-command versus a list; where in ProcessInput() a new command byte goes, and whether the handler can write inside the drain loop rather than through g_pending_field; whether the game's own colony screen redraws from pop[] on the next frame without cluster state (coldraw.cpp, not a screenshot).

3c: proposed command shape with the reason. No patch, no HD code. Reporting stop. Fundament entry 52 is written after Data has read this, and its number is checked again at that moment.

Run B — documentation audit

Sequenced after Stage 5. An audit before the old modules are deleted documents a tree that the next commit removes. Its own commit, nothing else in it.

Scope

README.md, MODDING.md, CLAUDE.md, v3_projektstatus.md, every file under doc/, comments in screens/colony_summary/layout*.json if any, module docstrings in screens/colony_summary/, docstrings of the tools/*.py the colony work touched.

Known stale points to start from v3_projektstatus.md says "Updated: 5 September 2026" at the top while carrying entries dated 9 September. Either the header is wrong or the document's own convention is; say which and fix it. Any document that still describes row_height, pad_x, FIGURE_STEP as a table, the frame bezel, the yellow pick outline, the F/W/S labels, "1 moved", per-band scroll plates, or SAVE10.GAM as the natives fixture path is describing a tree that no longer exists. Part F's first table (7ca487e) is wrong in its attribution; make sure no document quotes it without the correction in bf35bf0. The - 1t item: extraction plus checker per decision 36, not a Joes wish. If doc/orion2re_open_fixes.md or the status still list it as a request, that is a copy pointing outward. The pop-move direction may be mentioned as planned and labelled as such, never as built. What "redundant" means — and what it does not

Remove a passage only when the same content has a better home and the removal leaves a pointer. The rules are in the fundament; apply them:

One home per list: orion2re requests in doc/orion2re_open_fixes.md only; the screen-ID map in one place; save identities in tools/fixtures.py. Every other mention becomes a pointer. Rule in the fundament, state in the status. A rule restated in the status is a copy — delete, cite the decision number. A state snapshot in the fundament is the copy the other way — move it out. Evidence is not redundancy. Measurements, threshold sweeps, before/after tables stay even where their conclusion is repeated. Decision numbers are identities. Nothing renumbered, no decision text reworded. A decision the tree has reversed is a report item, not an edit. CLAUDE.md's division-of-labour section also lives in Data's memory. If you touch it, say so in bold at the top of the report; if not, say that too. (The check count 105→111 is not that section.) Markers need three homes: module, status, smoke test. The audit removes none of the three; it reports any marker with fewer. Method Inventory before editing: one line per file in scope — what it claims to be, when it was last true, what it duplicates. Report, then edit. Grep for the dead vocabulary above and for references to files no longer in the tree. Each deletion names its new home in the commit message. Smoke test green — some checks grep documents for markers. Report

Inventory table, deletions with their new home, contradictions found but not resolved (rule vs. tree, doc vs. doc), the CLAUDE.md statement. The contradictions are the valuable part.

Acceptance Run A: the can/cannot-remove paragraph filed beside the Part I table; four 3b answers with file:line; 3c proposal; no code. Run B: inventory before edits; every removal has a named home; no decision renumbered or reworded; marker triples intact; header date resolved; CLAUDE.md statement present; one commit; smoke test green. git push is Data's, after reading the diff.
