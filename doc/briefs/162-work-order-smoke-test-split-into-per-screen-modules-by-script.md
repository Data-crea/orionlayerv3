Work Order 162 — Smoke test split into per-screen modules, by script

First line for references: "Work Order 162 — Smoke test split into per-screen modules, by script"

Filed as 162 because the highest number in doc/briefs/ was 161 when this was written. Check that before filing (session startup rule); if 162 is taken, take the next free number and change the title line.

Read doc/v3_fundament.md first, then doc/briefs/157-suite-profile.md and doc/briefs/158-work-order-two-tier-gate-fast-on-commit-full-on-push.md. This order builds on 158's two-tier gate and must not undo any of it.

Why (Data)

tools/smoke_test.py is about 22,000 lines and about 1.2 MB, almost all of it inside one function, main(). That is several times larger than any context window and roughly fifteen times the 80 KB reading budget of work order 127. Every new screen therefore costs more than the one before: a new check has to be placed inside a file nobody can see whole, next to fixtures that have to be found by grep, and every development run executes checks that have nothing to do with the screen being built. Many screens are still to come before 22 November.

The goal: while working on a screen, only that screen's checks and the shared core run and have to be read. Before handoff and before push, everything runs, exactly as today.

How this run works

Unattended, no reporting stops. Data has decided the direction and the constraints below; every technical decision inside them is Claude Code's, and where a decision would need judgement Data cannot give, this order replaces it with a rule. Questions go into doc/briefs/162-parked-for-data.md and do not stop the run. Progress into doc/briefs/162-progress.md. Evidence under ~/orionlayer-fixtures/evidence/work_order_162/.

This run will be long, and it may outlive a session. Write 162-progress.md so that a fresh session can resume from it alone: what is done, what is committed, what the next step is, where the evidence is. Parts 1 and 2 are tools that change nothing in the suite and may be committed as they are finished; that is what makes the run resumable. The cut itself (Part 3) is one commit.

The rule that governs the whole run

tools/smoke_test.py is never read as a whole. Inventory and cut are done by scripts whose output is small. A session that starts "reading itself in" to the file has already left this order. Moving code by reading blocks into context and writing them out again is how a check disappears silently; it is not allowed here.

Hard constraints
No check is deleted, weakened, thinned, fixed or added. Every existing check still runs, unchanged, in the full suite. A fault found while moving is parked, not repaired.
No restructuring beyond the move, even where it would make sense. Merging checks, rewriting fixtures, removing duplication: each changes the ok(...) list for a good reason, and then the list can no longer tell a good change from a lost check. Every such idea goes into a section "Later, per module" in 162-parked-for-data.md, naming the module, so it can be done when that screen is next worked on and the module is small enough to test on its own. Layout, file names, grouping and the core's organisation are free — they do not touch the proof.
The move is mechanical. A check's code lands in its module unchanged apart from what the move itself requires: indentation, imports, and rewriting access to names bound earlier in main() so they reach the shared state. Every such change is produced by the cutting script, never by hand.
The gates stay exactly as 158 left them. Pre-commit runs the fast tier, pre-push runs the full suite, both block on any non-zero exit, both installed by tools/setup.py. python tools/smoke_test.py with no flag remains the full suite. The entry point keeps its path.
The full run keeps the original order. A check that depends on state set up earlier still sees it.
157's rejection of Option B stands. The new selector (Part 4) is a development convenience, never used by a hook, and it can only make a run larger than the named screen, never skip a check the screen needs. Checks that sweep directories or police files that do not exist yet belong to the core, which always runs.
Part 1 — The baseline, and proof the baseline is stable

Before anything else, capture what "nothing was lost" will be compared against.

A small tool records, for one full run, the ordered list of every ok(...) message, the check count, and the fast tier's skipped set.
Normalise the list: anything in a message that varies from run to run (timings, measured values, paths, counts of things on the user's disk) is replaced by a placeholder. The normalisation rules live in the tool, each with a comment saying which message needed it.
Run the full suite twice and compare the two normalised lists. They must be identical before the cut starts. If they are not, the normalisation is not finished — fix the tool, not the suite.
Store the baseline and both runs as evidence. Record the runtimes of both tiers.
Part 2 — Inventory tool

A tool (for example tools/smoke_inventory.py) that parses tools/smoke_test.py with ast and writes a compact table, one row per check section: line range, the screen or area it belongs to and how that was determined, the names it reads that were bound earlier in main(), the names it binds that later sections read, whether it sits behind a slow(...) guard, and its runtime from a measured run.

The table is what goes into context, not the code. From it, Claude Code decides the cut: one group of modules per screen (a folder or a name prefix — a screen whose checks exceed the size limit of Part 5 is split into several modules, by topic, never by line count), plus a shared core, itself split the same way, for fixtures, helpers and cross-cutting rules (unique decision numbers, the single-literal checks, directory sweeps, marker inventories). Sections whose home is ambiguous go to the core. The cut and the reason for each ambiguous case are written into the progress file.

Part 3 — The cut

A cutting script produces the new layout from the inventory in one run. Layout and file names are Claude Code's choice. tools/smoke_test.py stays the entry point and runs the core, then every module, in the original order.

Proof that nothing was lost, all required before the commit:

the normalised ok(...) list of a full run after the cut is identical to the baseline;
the check count and the fast tier's skipped set are identical;
full suite and fast tier green on a fresh clone (verify against a pristine tree, not the working one).
Abort rules — these replace a decision by Data
If the normalised list differs and the cause cannot be fixed in the cutting script, discard the cut entirely. Nothing of it is committed.
If the inventory shows the sections so entangled that the cut would need changes beyond the mechanical ones allowed above — logic rewritten, checks reordered, state split in a way a script cannot do safely — do not attempt the full cut.

In either case, build the fallback instead: tools/smoke_test.py stays one file, and main() is divided into named section functions in the original order, which the selector in Part 4 can pick from. The same proof applies to the fallback. Say in the report which of the two was built and why.

Part 4 — The development selector

A flag such as --screen <name> runs the core plus all of that screen's modules, nothing else. It prints on its first and last line that it is not a gate run, for example SMOKE TEST PASSED (SCREEN research_select ONLY — NOT A GATE).

The selector widens itself; it never trusts the session to remember. Before narrowing, it looks at what has changed in the working tree and the index against HEAD. If anything outside that screen's own territory has changed — core/, assets/shared/, main.py, another screen's folder, tools/, the test core, another screen's tests — it runs the fast tier instead and says so on its first and last line, naming the files that caused it, for example WIDENED TO FAST TIER: core/box.py changed outside screens/research_select/. Each screen's territory is listed in one place, not inferred per run.

The working rule goes into CLAUDE.md and the Process section of doc/v3_fundament.md, written by Claude Code: during screen work iterate with --screen; before every handoff run the full suite (decision 31 unchanged); the push gate stays mechanical.

Part 5 — The rule that keeps it from growing back

Size limit: no test module and not the core may exceed half of the reading budget, 40 KB. This is a setting, not a measurement, and Data may change it later. A check in the core fails when a module goes over it. Exceptions only if listed with a reason, the way decision 6 handles files over ~300 lines. A screen that outgrows the limit gets another module in its own group, split by topic. A new screen gets its own group; screen-specific checks never go into another screen's group or the core.

If the fallback was built, the same limit applies to each section function's source, measured the same way.

References from outside

Documents and comments that cite smoke_test.py:<line> will break. Find them with a grep, point each one at its new location, and list what was changed in the progress file. CLAUDE.md, tools/setup.py, both hooks and any tool that names the file are checked the same way.

Acceptance
Normalised baseline stable across two runs, and identical after the cut; count and skipped set identical; evidence stored.
Full suite and fast tier green on a fresh clone; both hooks proved by running them, as in 158.
--screen works for at least two screens. In a throwaway change, a change inside the screen's folder runs the narrow selection and a change in core/ with the same flag widens to the fast tier and names the file. Both reverted.
The size-limit check exists and fails on a deliberately oversized module in a throwaway test. Reverted.
Runtimes before and after, per tier and for one --screen run, in the progress file.
Push is Data's decision, after the fresh-clone verification.
Final report for Data — in German, short, no code

Data will read this and nothing else, so write it for someone who does not read the code. Answer only these, in plain sentences:

Built or rolled back? Full split, fallback, or nothing — and in one or two sentences why.
Was any check lost? Yes or no, and what proves it.
How long does a run take now? While working on one screen, and the full suite before a push — each before and after.
How much test output does a run produce? Bytes of output written by one run during screen work, before (full suite) and after (--screen), measured, not estimated. Every run's output lands in the session's context, so this is the direct measure of what the change saves in tokens.
What changes for the next screen? In one or two sentences.
Which places in CLAUDE.md and doc/v3_fundament.md were changed? Name each section and quote the new rule. Several rules deliberately live in both files; say for each that it now reads the same in both.
Is anything parked for Data? If so, what, in plain words.
