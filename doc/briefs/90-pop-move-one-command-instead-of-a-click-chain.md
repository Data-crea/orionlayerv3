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
