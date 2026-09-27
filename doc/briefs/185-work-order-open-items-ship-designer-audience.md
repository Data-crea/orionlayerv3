# Work order — open items after 184, Ship Designer, Audience screen

**Number:** next free work-order number in the tree (check doc/briefs/ and the git log before filing; the last one Data knows of is 184). Use that number everywhere this order says <n>.

## How this run works

Unattended run, no questions. Anything that needs Data goes into doc/briefs/<n>-parked-for-data.md, each item with the default you took and why. Keep doc/briefs/<n>-progress.md current after every part, so the run can be picked up at any part boundary.
One commit per part. Parts that produce nothing for the repo (marked below) are recorded in the progress file only.
Start: read the index doc/v3_fundament.md, then the fundament parts the task needs, always all principles- parts. Check the tree before proposing anything it may already contain.
Baseline Data expects: main = origin/main = af4d354, suite 386 checks green; orion2re orionlayer-local = 4bf152e4 with fixes 34–41 applied. If the tree says otherwise, record the actual state in the progress file and work from it.
Division of labour: you own every detail (field indices, offsets, values, line numbers). This order names where things live and what counts as done; it does not claim what the code contains.

## Rules that apply to every part

orion2re is not changed in this run. No commit on orionlayer-local, no new applied fix. Every engine change is prepared as an open-fix entry: entry in doc/orion2re_open_fixes.md, patch file under doc/, proof (applies cleanly on 4bf152e4 without offset, compiles, counter-test with a misspelled constant fails). Data approves; a later order applies.
Scratch engine builds (needed for proofs and for Part 1) go into a separate worktree and a separate build directory. The build play.py starts must stay untouched.
Live tests: tools/liveguard.py before and after every live session. Xvfb only; the real desktop only with --real-desktop REASON, and there should be no reason in this run. Scratch slots SAVE4/SAVE5 only, never SAVE8. Hash rules as before (SAVE1–9 and SAVE11 identical before/after, SAVE10 only logged). Do not touch engines or clients in Data's session. Use ORIONLAYER_INPUT_LOG where clicks matter. Each live step names its slot/fixture.
Colony screen: never trigger CRUNCH, TOGGLE or field [0].
Every new screen goes through the handover gate core/handover.py (last HD frame stays, input discarded while waiting) and is covered by the flash check and by the double-scaling check 090t. Style as all current screens: HUD style, glass fill with the transparency setting, universal background with mod override, global frame colour. Original graphics are adopted where the original has them. Visible text comes from the extracted strings, not from hand-typed lists.
No silent deviation: any difference from the original gets its marker (HD EXTENSION / DEVIATION) in module, status document and smoke test, with the reason.
Evidence under ~/orionlayer-fixtures/evidence/work_order_<n>/.
References to earlier briefs, entries or decisions name the number AND the first line.

## Part 1 — Open Fix 42: are clicks lost in the gap? (evidence only)

Open Fix 42 lets the engine send screen data during its input delay (Research roughly 0.6 s → 0.1 s, 42 screens affected). Before Data can approve it he needs one answer: with the fix, can a click land in the gap where the HD screen is already visible but the engine does not yet accept input — and is it lost?

Scratch build with the Fix 42 patch (see rules above).
On Xvfb, SAVE4/SAVE5: open Research and at least two other affected screens of different kinds (your choice, named in the report). Inject clicks at stepped offsets from the moment the HD screen becomes visible until well after the engine accepts input. After each click, read state back (framebuffer and/or field list) to decide: taken, lost, or taken twice.
Same procedure on the current unpatched build as the baseline.
Result table (screen × offset × patched/unpatched × outcome) in the evidence folder and summarised in the open-fix 42 entry. Entry status stays OPEN.
If clicks are lost: describe the addition the fix needs (for example HD holds inputs during the gap and sends them once the engine accepts; say which signal tells HD that the engine accepts, and where it comes from) inside the Fix 42 entry. Do not implement it. Park the approval decision with your recommendation.

Commit: the updated Fix 42 entry plus any measurement tool you wrote.

## Part 2 — Fix 41, the proper version (prepared, not applied)

Fix 41 hides the engine window from the start, always. Consequences Data has accepted for now: the original without OrionLayer starts invisible, and F12 to the original does not work. The proper version:

The window is hidden only when OrionLayer starts the engine. Started on its own, orion2re behaves as before Fix 41.
F12 can show the original window (and return to HD, as F12 did before; check the tree for how F12 worked).

Choose the mechanism (e.g. launch flag, environment variable, extension-API message) and record the choice with the alternatives in the parked file. Prepare it as the next free open-fix number (amendment to or replacement of 41 — say which, and what the revert path is), with the full proof set. Describe the HD side (play.py, F12 handler) in the entry; do not commit HD code that only works with the unapplied patch.

Commit: entry plus patch file.

## Part 3 — Decision drafts (Data assigns the numbers)

Draft two decision texts in the style of the existing decisions, each with the fundament part you would file it in:

The flash rule from 180: the player never sees an original frame before or between HD screens; every screen goes through the handover gate; the flash check replays all transitions and fails on any native frame.
From 183: players skip the intro and land in the HD main menu without intro sound; the engine window is hidden (with the Fix 41 consequences as they stand, and a pointer to the prepared proper version from Part 2).

File them in doc/briefs/<n>-decision-drafts.md with <number: Data> as placeholder. Do not write them into doc/fundament/.

Commit: the drafts file.

## Part 4 — Handover package for Joes (not committed)

Assemble in ~/orionlayer-fixtures/handover_joes_<date>/ (outside the repo, English): Fix 31, entry 33 (jump from the Turn Summary lands on the galaxy instead of the colony, and this also blocks one way into the colony view — include a repro), fixes 34–41, and the note that _screen_data stays at 2 after ESC in the load dialog. For each: what it does, why OrionLayer needs it, the patch file, and whether it is applied locally. No copy of the orion2re tree or bundles. Data sends it himself.

Progress file only.

## Part 5 — Credits roll

Check whether the credits roll still names Darza specifically. If it does, remove that mention. Commit message neutral ("Credits: update roll"); no reason in the commit, the docs or the progress file — the progress file says only "credits roll: changed" or "credits roll: already clean".

## Part 6 — Ship Designer: reading report and brief

Reading report from the orion2re source and the original: what the Ship Designer shows and does, including every sub-dialog it opens (component selection, specials, weapons and their options, hull choice, name entry, and anything else you find), every way into it and out of it, and what happens to a finished design.
For each piece: is it on the wire today, yes or no. For each "no": prepare an open fix (next free numbers, full proof set, not applied).
Write doc/brief_ship_designer.md (no line numbers) before building: screen layout in the current HUD style, which original graphics are adopted, which markers are needed and why.

Commit: report, brief, prepared fix entries and patches.

## Part 7 — Ship Designer: HD screen

Build the screen from the brief as far as today's wire allows. Where a piece depends on an unapplied fix, build the layout and the input path, leave the data path clearly stubbed and marked UNVERIFIED with the fix number — never invented values. Handover gate, flash check, 090t, mod override for text and graphics. Checks in the smoke suite for everything that can be checked offline.

Commit: the screen and its checks.

## Part 8 — Ship Designer: live test

On Xvfb with SAVE4/SAVE5: open it by every way in, change components, name a design, save it, cancel, leave. Put each HD state beside the matching native screenshot and phrase every difference as a question in the report, not a finding. Anything that could not be reached with the scratch saves goes into the parked file with what save would be needed.

Commit: live-test report and any fixes it forced.

## Part 9 — Audience screen: reading report and brief

Same structure as Part 6, for the diplomacy audience: every proposal and sub-menu, the AI replies and where their text comes from, the leader graphics, every way in — including the audience the computer player requests at turn start, not only the one the player opens. Note: the reading report of work order 163 (doc/ai_behaviour_reading.md) parked one line about the player record and objectives already being on the wire until the diplomacy screen — pick that up here.

Brief: doc/brief_audience.md. Missing wire data → prepared open fixes, not applied.

Commit: report, brief, prepared fix entries and patches.

## Part 10 — Audience screen: HD screen

As Part 7.

Commit: the screen and its checks.

## Part 11 — Audience screen: live test

As Part 8. Diplomatic actions change the game: scratch saves only. If no scratch save gets a computer player to request an audience, park it with the save that would be needed.

Commit: live-test report and any fixes it forced.

## Part 12 — Gates and push

Push only if all four are green: full suite, fresh clone, liveguard, flash check. No force-push. If a gate is red, you may repair it and re-run; if it stays red, do not push and say why in the progress file.

## Carried over unchanged (do not act, list them in the parked file with the existing defaults)

- Extra slot message after ESC in the load dialog (default: leave it).
- Narrow buttons with the word only.
- Buildings as a list instead of the grid (Fix 36 unused, UNVERIFIED).
- Plague and population boom not yet seen live.
- Research query at turn start not measured (would write SAVE10).

## End of run

The progress file ends with: what is done, what is parked, and a list of every open fix waiting for Data's approval (number + first line + one sentence on what it unlocks).
