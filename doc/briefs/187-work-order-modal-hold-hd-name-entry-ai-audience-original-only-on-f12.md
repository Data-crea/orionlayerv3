Work order — modal hold, HD name entry, AI audience, and "the original only on F12"

Number: next free work-order number in the tree (the last one Data knows of is 186). Use it everywhere this order says <n>.

Data's rule for this order and everything after it

The player never sees any part of the original picture unless he presses F12. This applies without exception: no hand-over to the original for input, no native frame during transitions, no original screen as a fallback. Where HD cannot yet do something, the answer is never "show the original"; it is parked for Data with a proposal.

How this run works
Unattended run, no questions. Anything that needs Data goes into doc/briefs/<n>-parked-for-data.md with the default you took and why. Keep doc/briefs/<n>-progress.md current after every part.
One commit per part.
Start: read the index doc/v3_fundament.md, then the parts the task needs, always all principles- parts; then doc/briefs/186-progress.md, 186-parked-for-data.md and 186-modal-hold.md.
Baseline Data expects: main = origin/main = 557da0f, suite 407 green; orion2re orionlayer-local = 230a0638, fixes 34–41 and 43–47 applied. If the tree says otherwise, record the actual state and work from it.
orion2re is not changed in this run. If something needs the engine, prepare it as an open fix (entry, patch file, full proof), do not apply it. Fix 42 stays OPEN.
Rules that apply to every part
Live tests: tools/liveguard.py before and after every live session. Xvfb only; the real desktop only with --real-desktop REASON. Scratch slots SAVE4/SAVE5 only, never SAVE8. Hash rules as before, MOX.SET restored as in 185/186. Do not touch engines or clients in Data's session.
Colony screen: never trigger CRUNCH, TOGGLE or field [0].
Diplomacy: never confirm Declare War or any proposal that changes relations; answer with Cancel.
Committed fixtures: every game-written text replaced by a stand-in before the first commit.
Evidence under ~/orionlayer-fixtures/evidence/work_order_<n>/.
References to earlier briefs, entries or decisions name the number AND the first line.
Part 1 — Modal hold: option C

Approved: option C from doc/briefs/186-modal-hold.md. A modal box over an HD screen is shown as soon as its list has stood still for SETTLE snapshots, instead of waiting out the gate's full hold.

The early release applies only where no late data can come (modal boxes). Screens keep the existing hold.
Walk every modal box reachable in the scratch saves one by one (name each in the report) and measure the time from input to first HD frame of the box, before and after.
Flash walk over all transitions: native frames must stay 0.

Commit: the change, its checks, the before/after table.

Part 2 — Name entry in the Ship Designer, in HD

The 186 recommendation (hand over to the original picture for input) is rejected: it breaks Data's rule.

Find how the screens that already take text in HD do it (for example Empire Identity, the Custom Race names, the save dialog) and give the designer's name entry the same path. The field, the cursor and the typed text are drawn by HD; keys go to the engine.
Live on Xvfb: enter a name, correct it with Backspace, confirm with Enter, cancel with ESC; the design shows the new name; no native frame at any point.
If it provably cannot be done without an engine change, prepare the open fix and park it. Do not fall back to the original.

Commit: the entry path and its checks (including a check that the name entry produces 0 native frames).

Part 3 — Multi-buttons through F12 (measure, fix only a clear forwarding defect)

186 left multi-buttons forwarded through F12 unmeasured. Measure them the way the text field was measured in 186 (the defect behind check 090g #3): does each click reach the right button and state, taken once, not lost, not doubled?

If you find a clear defect in HD's forwarding of the same kind as in 186, fix it with a check. Anything else: report and park.

Commit: measurement report plus any fix and check.

Part 4 — The light-blue "Peace Treaty" in the audience

The original decides. Compare the disabled "Peace Treaty" item (and every other disabled item you can reach) against the native frame. If the original shows the same colour, leave it and say so; if not, match the original.

Commit: the comparison and any change.

Part 5 — The AI's audience (58)

In SAVE4/SAVE5 only, in memory, never saved: you may take game decisions that stop the turn (colony base choice, combat and similar) with any default choice, and end turns until a computer player asks for an audience. Limit: 30 turns per save. Every decision you took is listed in the report.

If 58 appears: walk it (greeting, statement, reply, menu; any proposal answered so that relations don't change), compare with the native frame, check that the transition into it and out of it shows 0 native frames.
If it doesn't appear within the limit in either save: park it; Data will provide a save of his own.

Commit: the report, and any fix the walk forced.

Part 6 — Where can the original still show? (inventory, no change)

Check the code for every path by which the original picture can become visible without F12. That includes screens that have no HD version yet, fallbacks for unknown screen ids, error paths, timeouts of the gate, and anything that hands over to the original for input.

For each path: where it is, when it triggers, whether a walk has ever seen it trigger, and what HD could show instead (for example keep the last HD frame with a notice). Report in doc/briefs/<n>-original-visibility.md, with your recommendation. Change nothing; Data decides.

Commit: the report.

Part 7 — Gates and push

Push only if all four are green: full suite, fresh clone, liveguard, flash check. No force-push. If a gate stays red, do not push and say why.

Carried over unchanged (do not act; list them in the parked file with the existing defaults)
From 185: hull choice only faintly marked; audience header line, fade-in and talking animation not drawn.
Extra slot message after ESC in the load dialog (default: leave it).
Narrow buttons with the word only.
Buildings as a list instead of the grid (Fix 36 unused, UNVERIFIED).
Plague and population boom not yet seen live.
Research query at turn start not measured (would write SAVE10).
End of run

The progress file ends with: modal-hold times before/after, whether name entry works in HD, the multi-button result, the Peace Treaty result, whether 58 was reached, the number of paths from Part 6 and the ones that need Data's decision first, and what is parked.
