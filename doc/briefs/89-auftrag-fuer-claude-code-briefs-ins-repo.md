Auftrag für Claude Code — Briefs ins Repo

Datum: 9. September 2026, abends. Entscheidung Datas: Übergabe-Empfehlung angenommen.

Ziel

Alle Briefs und Aufträge dieses Projekts aus ~/.claude/paste-cache/ nach doc/briefs/ überführen und den Zeiger-Commit 9a85c74 darauf richten. Ein Commit, kein Push.

Regeln
Inhalte byte für byte übernehmen, nichts umformulieren, nichts kürzen.
Dateinamen sprechend vergeben; ein Datum nur, wenn es aus dem Brief selbst oder aus der Git-Historie belegbar ist (erster Commit, der den Brief umsetzt). Unbelegbares Datum weglassen, nicht schätzen.
doc/briefs/README.md als Index: Dateiname, Datum oder „undatiert", ein Satz Inhalt, und welche Quelle (Cache-Datei oder Anhang dieses Auftrags).
Die zwei Anhänge unten (A: Pop-Move-Brief, B: Workorder Run A / Run B) kommen mit hinein. Beide existierten bisher nur als Chat-Nachricht. Anhang A ist am Anfang unvollständig — er setzt mitten in Abschnitt 1 ein, Titel und Kopf fehlen. Genau so ablegen, im Index als „Anfang fehlt" markieren, nichts nachdichten.
Die zwei Stellen, die brief_pop_sprites_assets.md als „retired" führen (Fundament Entscheidung 50, Status ~:3831), auf die tatsächliche Datei zeigen lassen — oder, falls es die Datei nie gab, die Formulierung so ändern, dass sie nichts Nichtexistentes zitiert.
Der Workorder (Anhang B) verweist auf Abschnitte 3b/3c des Pop-Move-Briefs (Anhang A). Nach dem Import prüfen, ob dieser Verweis jetzt auf eine Datei zeigt, und im Bericht sagen, welche.
Anhang A wird in Session 2 Ziel von Pointern („pointer back to this brief" in open_fixes, Akzeptanzpunkt „this brief agree"). Im Bericht den endgültigen Pfad nennen, damit diese Pointer später einen festen Pfad haben.
9a85c74 amenden, nicht neu draufsetzen: der Zeiger im Status soll auf doc/briefs/ zeigen.
Auftrag „Pop-Verschiebung" vom 4.9. (Cache e13c3084, Parts 0–4) ist ein drittes, eigenes Dokument und kommt aus dem Cache.
Stopp und Bericht, bevor Data pusht
Anzahl übernommener Dateien
Liste der Cache-Dateien, die nicht zu diesem Projekt gehörten
Welche in den Dokumenten zitierten Briefs weiterhin fehlen
Pfad von Anhang A und Anhang B im Baum
Smoke-Test muss grün sein

Danach, nach Datas Push: Part 3 des Pop-Move-Auftrags bis zum Editor-Stopp.

Anhang A — Pop-Move-Brief (9.9.2026, Anfang fehlt)

A second problem the chain carries and the fix removes: the chain must answer "which icon in the game's window", and the HD row does not lay figures out the way the original does. Get_Cluster_ also does not pick up "the N under the cursor" — it takes every identical pop from the clicked one to the array end (transcribed in colonymove.py, verify in colmove.cpp). The HD selection has never been the game's cluster (decision 47).

The decision (draft of fundament entry 52)

A pop move reaches the game as one command, addressed by colony index, pop index and job — never as a click sequence into the game's window.

Implemented as a local patch to orion2re under the same rule as open fix #3: patch file under doc/, entry in doc/orion2re_open_fixes.md, reported to Data before it is applied. tools/version_check.py must additionally verify the patch is present in the local tree, so an unpatched engine fails a check instead of silently ignoring the command. The click chain (RESORT / ESTABLISH / PICK / DROP) is deleted, not kept as a fallback. Two paths for one action is the duplicate the project keeps paying for. Decision 46 and the sort rationale in colonysend.py lose their occasion on this screen; say so where they are cited, do not let them vanish. The five refusal rules in colonymove.py stay. Decision 33 is unchanged: HD refuses before sending, because a refused command is still a silent failure in the framebuffer. Extends decision 36's line: a client that rebuilds a click choreography to trigger one function call is already behaving per-engine, and then the patch is the honest route.

Pop index means storage order in s_colony.pop[], which HD and the game read from the same snapshot. Drawing order is a separate question and no longer on the wire.

52 is the next free number as of this brief's date — check again before writing; two same-day sessions once took the same number. The final wording is written after section 3 is answered, not before.

Session 1 — read and measure, no code

Reporting stop after this section. Do not write the patch yet.

3a. Timing of the current chain. Log timestamps per chain state for a move on the first row and on the last row of the reference save (Sterndatum 3502.4, player 0 Greywind). Report seconds per step and the observed state/s, visual/s from GameClient.stats. This is the before-value the acceptance test compares against.

3b. Source questions, answered from the function that builds the thing:

What context does Give_Colonist_New_Job_ read besides its arguments? Specifically whether it depends on cluster_colony_n, the current screen, or any global the colony summary screen sets. If it needs screen state, name what and where it is set. Can the recalculation (Col_Calc_Wrapper → Colony_Calculation_ → Pass_Out_Imports_, per the notes in colonymove.py) run once after several job changes, or does Give_Colonist_New_Job_ itself trigger it per pop? This decides whether the command moves one pop or a list. Where in ProcessInput() (ext_api.cpp) does a new command byte go, and confirm the handler can write immediately in the drain loop rather than through g_pending_field. Five commands in one tick must all land. Does the game's own colony screen redraw from pop[] on the next frame without a cluster state, or does anything cache the row? Read coldraw.cpp, not the screenshot.

3c. Report the four answers with file and line, and a proposed command shape (one pop per command vs. list) with the reason.

Session 2 — patch, verify, rewire

Only after Data has read the section 3 report.

Write doc/ext_move_pop.patch (name it what it does). Report the diff before applying. Extend tools/version_check.py to detect the patch. Add the entry to doc/orion2re_open_fixes.md as a request, with a pointer back to this brief. Live verification with the existing tools before any HD change: predict_pops, move_diff_verdict and tools/colony_move_probe.py were built for the click chain and measure the new command the same way. A move must change exactly the predicted pop words in exactly one colony and nothing else except the fields move_diff_verdict already allows. Rewire colonysend.Send to one send and one wait on the predicted pops. Delete the four chain states and the window-stepping code. Retarget every marker and smoke-test assertion that named them in the same commit. Missing test cases from the open acceptance list still apply: a save with Native/Android pops and one with max_farms == 0. 5. Acceptance Smoke test passes headless. Version check fails on an unpatched tree and passes on the patched one. Live: a five-pop move on the last row of the reference save lands in one snapshot round after the send; report the measured time beside the section 3a value. Live: a move refused by rule 1 (native to research) sends nothing and shows the layout.json message. grep finds no reference to RESORT, ESTABLISH, PICK, DROP, STEP_UP_XY or STEP_DOWN_XY outside the git history. Fundament entry 52 written, status document updated, both orion2re_open_fixes.md and this brief agree on what was asked. 6. Out of scope

Distribution (build script vs. binary) is an open item for the status document, not for this work. The patch is the same whichever way it ships. Primary user is Data; that is enough for a build script.

Anhang B — Workorder: colony runs and doc audit

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