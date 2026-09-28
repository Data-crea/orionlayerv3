Work order — apply fixes 44–47 (and the proper Fix 41), take Ship Designer and Audience live, measure the modal hold

Number: next free work-order number in the tree (the last one Data knows of is 185). Use it everywhere this order says <n>.

How this run works
Unattended run, no questions. Anything that needs Data goes into doc/briefs/<n>-parked-for-data.md with the default you took and why. Keep doc/briefs/<n>-progress.md current after every part.
One commit per part. For orion2re, one commit per fix (see Part 1).
Start: read the index doc/v3_fundament.md, then the parts the task needs, always all principles- parts; then doc/briefs/185-progress.md and doc/briefs/185-parked-for-data.md.
Baseline Data expects: main = origin/main = 5d791a9, suite 405 green; orion2re orionlayer-local = 4bf152e4, fixes 34–41 applied. If the tree says otherwise, record the actual state and work from it.
Division of labour: you own every detail. This order names what Data approved and what counts as done.
Rules that apply to every part
Live tests: tools/liveguard.py before and after every live session. Xvfb only; the real desktop only with --real-desktop REASON (there should be no reason in this run). Scratch slots SAVE4/SAVE5 only, never SAVE8. Hash rules as before, MOX.SET restored as in 185. Do not touch engines or clients in Data's session.
Colony screen: never trigger CRUNCH, TOGGLE or field [0].
Diplomacy in live tests: never confirm Declare War or any other proposal that changes relations; answer with Cancel, as in 185.
Committed fixtures: every game-written text is replaced by a stand-in, before the first commit.
Evidence under ~/orionlayer-fixtures/evidence/work_order_<n>/.
References to earlier briefs, entries or decisions name the number AND the first line.
Data's decisions for this order
Approved: open fixes 44, 45 (as amended in 185), 46, 47.
Approved on condition: the proper version of Fix 41 prepared in 185 Part 2, only if its proof set is complete (applies cleanly, compiles, counter-test with a misspelled constant fails) on the base it will be applied to. If the proof is incomplete or cannot be completed on that base, do not apply it; park it with what is missing.
Not approved: Fix 42. Do not apply it and do not build on it. Its entry stays OPEN.
Game text in commit 6f0570c: leave it. Add a line to the release clean-up list (create the list under doc/ if none exists) naming the commit and that it holds two short game strings in hex. No history rewrite, no force-push.
Part 1 — Apply the approved engine fixes

Order: 44, 45, 46, 47, then the proper 41.

Before each fix, re-run its proof on the current tip of orionlayer-local (the tip moves with every applied fix): applies cleanly without offset, compiles, counter-test fails. If a fix no longer applies cleanly because an earlier one changed the context, re-cut the patch file, rerun the full proof, and record in the entry that and why the patch changed. If a fix cannot be made to apply, stop applying at that point; the fixes before it stay applied, the rest is parked.

For each applied fix, the full ritual:

One-line comment OrionLayer, open fix N. at every changed place.
One commit per fix on orionlayer-local. Never pushed anywhere.
Entry set to APPLIED with the diff, both hashes (before/after), the revert path and the side effects you found.
tools/version_check.py, README, setup.py and fundament part 09 updated to the new fix set and hash.
A new bundle after each applied fix: ~/orion2re_bundle_<date>_<hash>_fixes34-<last>.bundle. Keep the older bundles.
The doc and the commit byte-identical.

The engine binary play.py starts: rebuild it only after checking with liveguard that no engine from Data's session is running from it. If one is, do not touch it: record it, park, and continue with everything that does not need the rebuilt binary.

Commits: one per fix in orion2re; one commit in orionlayerv3 for entries, version_check, README, setup.py and part 09.

Part 2 — HD side
Ship Designer and Audience: data now arrives through fixes 44–47. Remove the UNVERIFIED markers and stubs where the data is really there now; keep a marker on anything still not covered, with the reason. Checks updated accordingly.
Proper Fix 41 (only if applied in Part 1): the HD side described in its entry: play.py asks for the hidden window; F12 shows the original window and returns to HD as it did before Fix 41. Check that the original started on its own (without OrionLayer) is visible again.

Commit: the HD changes and their checks.

Part 3 — Verification on the engine play.py now starts
Full suite and fresh clone after tools/setup.py.
Flash walk over all transitions, not only the new screens: four engine changes at once can touch old screens. Result: number of transitions, number of native frames (must be 0).
Ship Designer and Audience live on Xvfb, SAVE4/SAVE5: every way in and out, the pickers, name entry, save design, cancel; the audience opened by the player (57) with greeting, refusal, menu and Declare War answered with Cancel. Put each HD state beside the native frame from 185 and phrase every difference as a question.
The AI's turn-start audience (58): if a scratch save can reach it by ending a turn in SAVE4/SAVE5, walk it. If not, it stays parked with the save it would need.
Fix 41 (if applied): original started alone → window visible; OrionLayer start → hidden; F12 → original visible, back to HD.
For Data's own acceptance on his desktop: write a short checklist in the progress file (what to click, what he should see), no more than one screen long.

Commit: the verification report and any fixes it forced.

Part 4 — The 3.8 s hold before modal boxes (measure only)

In 185 the warning box over the designer appeared only after 3.8 s. You reported that this is the handover gate's hold for every modal box. Find out, with measurements and no fix:

What exactly the gate waits for at a modal box, and where the 3.8 s go (timeline: input, engine, wire, gate, first HD frame).
Whether it is the same for every modal box you can reach in the scratch saves (name them).
Whether it depends on the engine's input delay that Fix 42 addresses, or not.

Report in the evidence folder and a summary in the progress file, with the options you see and your recommendation. Park the decision. Change nothing.

Commit: the report and any measurement tool you wrote.

Part 5 — Gates and push

Push only if all four are green: full suite, fresh clone, liveguard, flash check. No force-push. If a gate stays red, do not push and say why.

Carried over unchanged (do not act; list them in the parked file with the existing defaults)
From 185: hull choice only faintly marked; audience header line, fade-in and talking animation not drawn.
Extra slot message after ESC in the load dialog (default: leave it).
Narrow buttons with the word only.
Buildings as a list instead of the grid (Fix 36 unused, UNVERIFIED).
Plague and population boom not yet seen live.
Research query at turn start not measured (would write SAVE10).
End of run

The progress file ends with: which fixes are applied (number, first line, hash after), which are not and why, the flash-walk result, the 3.8 s findings in three sentences, Data's acceptance checklist, and what is parked.
