# Work Order 157 — Close 156, repair T3, profile the suite — unattended

First line for references: "Work Order 157 — Close 156, repair T3, profile the suite — unattended"

Filed as 157: the highest number in `doc/briefs/` was 156 when this was
filed (work order 156, the Stage 5 / redundancy cleanup).

Read `doc/v3_fundament.md` first.

## How this run works

This is an **unattended run**. There are no reporting stops.

- Questions that need Data go into `doc/briefs/157-parked-for-data.md`
  and the run carries on with the next part. A parked question never
  blocks a later part unless that part depends on the answer; then the
  dependent part is parked too, and the file says so.
- Progress goes into `doc/briefs/157-progress.md`, updated after each
  part: commit hash, suite result, anything surprising.
- Evidence under `~/orionlayer-fixtures/evidence/work_order_157/`.
- **When in doubt whether something is still cleanup or already a
  decision: it is a decision. Park it.**

The parts run in order. Each part ends with a green suite and its own
commit(s) through the pre-commit hook.

## Global constraints

- **No behaviour change on any screen, anywhere in this order.** Where
  a part touches rendering, prove identity by the method 156 used
  (`colony_list_preview` or the matching preview tool, both input
  states, byte-identical per state).
- Do not touch `screens/fleets/`, research change mode (131), or
  orion2re.
- **D–G from 156 stay parked.** Data has not released them.
- Every place a changed name is used is found by full-project grep,
  `tools/` and the suite included.
- Markers (HD EXTENSION, DEVIATION, DERIVED, INVENTION) move with
  their code, in module, status document and suite. **None may
  vanish.**

## Part 1 — Close 156 with C

Data approved C. Remove the two fields `growth` and `beyond` from the
colony row structure; `row_boxes` has returned them empty since
`514ebb2` ("The colony list geometry becomes six boxes and a row
count").

**Why, so it survives in the tree:** both belonged to the HD
allocation bar, which was an INVENTION; the original's row draws
population sprites only (`Do_Colony_Info_Pop_Stuff_For_Pop_`,
coldraw.cpp). The bar no longer exists, so there is no place left for
either value. Unmarked empty fields from a removed invention are
residue.

**The note stays, rewritten.** In `colonytrack.py` and
`v3_projektstatus.md`, the line saying Stage 5 decides whether the
fields "come back in an honest place" becomes:

- A per-row capacity display is an open design question for Data.
- The original shows headroom only as a number in the scan box, for
  the scanned colony alone (`Draw_Colony_Scan_Info_`, colsum.cpp), so
  a per-row display would be a marked HD EXTENSION.
- If it comes, it is built new against the six column boxes and does
  not bring back `growth`, `beyond` or `growth_gap`.
- Where the old code is: `514ebb2`'s parent for the bar, the C commit
  for the fields.

The suite asserts one of the two fields explicitly; **that assertion
goes with the field**, and the progress file says what replaces it, if
anything. Mark C resolved in `156-parked-for-data.md` with the hash,
referencing the note by its first line.

## Part 2 — T3: a check that could go green while measuring nothing

From `156-parked-for-data.md`: the suite measures `ships._lift` by
substituting `playercolors.lift`. If the two drift apart, the check
stays green and no longer measures the function it names.

Fix it so the check measures **the real thing, by the path the real
thing travels** — not a stand-in. Acceptance, in the order the
fundament asks for it:

1. **First show the gap:** a deliberate temporary drift between the
   two functions that the current check does **not** catch. Record it
   in the evidence folder, then revert it.
2. **Then the repaired check**, and the same drift again — now it
   must fail. Record that, revert.
3. If the right fix turns out to be **merging** the two functions
   rather than repairing the check, that is a design decision: park it
   with both options described, and ship only the check repair.

## Part 3 — D17

Read D17 in `156-parked-for-data.md` and decide by one rule: if it is
a pure removal or correction, behaviour-neutral, and a test or a byte
comparison proves that, do it here. If it adds behaviour, adds a check
with a design choice in it, or closes an option, park it with a
two-sentence summary **in plain German** for Data. Either way the
progress file says which way it went and why.

## Part 4 — Profile the smoke test (measure only, change nothing)

Data finds the suite too slow for a commit gate. This part produces
the numbers for that decision; **it does not change the suite, the
hook, or the gate.**

- **Noise floor first.** Run the full suite several times unchanged
  and report the spread of total wall time. Per-check differences
  smaller than that spread are not findings.
- **Per-check timing.** Wall time per check (or per group, where the
  checks are closures inside `main()` and cannot be timed singly —
  say which). Sorted, with cumulative share of the total.
- **What the slow ones read.** For every check above the noise floor:
  which files and assets it loads, and which resolutions it renders.
- **Dependency question, answered from the tree.** Could each check be
  mapped to the files it depends on by computation — imports plus
  files actually opened during the run — rather than by a list kept by
  hand? Where would that mapping be unreliable? The fundament's cases
  where a failure surfaced far from its cause (the split delivery
  breaking the sidebar; a New Game box failing another resolution's
  panel check) are the test for any answer.
- Write the result as a brief, `doc/briefs/157-suite-profile.md`, no
  line numbers, ending with **two or three options for Data** — e.g. a
  fast tier for the hook with the full suite before push, a
  change-based selection with "shared file → run everything", or
  simply moving a few expensive checks. **Each option names what it
  would have missed among the known past failures.** No recommendation
  is implemented.

## Finish

- Suite green; fresh-clone verification of the final commit with
  `setup.py`, both input states as in 156.
- Line count with `tools/linecount.py`, same method as 156, as a new
  column beside the 156 numbers.
- **Push** — Data explicitly asks for it with this file. Push
  everything from 156 and this order together. If the gate is red,
  repair it, rerun the fresh-clone check, then push. If a part was
  parked, push what is done; parked parts are not a reason to hold the
  rest.
- Final report **in German**, short:
  - per part: done or parked, commit hash, one sentence
  - what the rewritten note in `colonytrack.py` says
  - T3: drift caught before/after, yes or no
  - D17: which way and why
  - the three slowest checks and their share of total time, against
    the noise floor
  - push confirmation
  - everything waiting for Data, with the path to the parked file

Then 156 is closed, and the next session is Fleets.
