# Work Order 158 — Two-tier gate: fast suite on commit, full suite on push

First line for references: "Work Order 158 — Two-tier gate: fast suite on commit, full suite on push"

Filed as 158: the highest number in `doc/briefs/` was 157 when this was
filed. Read `doc/v3_fundament.md` and `doc/briefs/157-suite-profile.md`
first — **this order implements its Option A and nothing else.**

## How this run works

Unattended, no reporting stops. Questions for Data go into
`doc/briefs/158-parked-for-data.md`, progress into
`doc/briefs/158-progress.md`, evidence under
`~/orionlayer-fixtures/evidence/work_order_158/`. When in doubt whether
something is still this order or already a new design choice: park it.

## Decision (Data)

The full suite on every commit costs about 78 s on Data's machine, and
157 measured where that goes: two checks are 54 %, the top ten about
74 %, the tail of 120 checks 0.1 %. **Option B** (change-based
selection) is rejected for the reasons in 157 §5(a) — directory sweeps
police files that do not exist yet. **Option C** (thinning the heavy
checks) is rejected because breadth is exactly where those checks
earned their keep. The caching idea from 157's closing note stays off
the table.

So: **the commit hook runs a fast tier; the full suite runs before
every push, enforced by git, not by habit.**

Option A's known cost, from 157 §6: a fault that only the heavy checks
catch (the marker-width fault, the plating fault) lands at push time
instead of commit time. **That is accepted.** It is only acceptable if
the push gate is as mechanical as the commit gate is today — which is
Part 2.

## Hard constraints

- **No check is deleted, weakened or thinned.** Every one of the 243
  still runs, unchanged, in the full suite. The tiers change *when* a
  check runs, never *what* it asserts.
- **Full is the default.** `python tools/smoke_test.py` with no
  argument runs everything, exactly as today. Only an explicit flag
  selects the fast tier. Anyone who runs the suite by hand — Data, a
  forker, a future session that has not read this order — gets the
  whole thing.
- **The fresh-clone verification is not touched and not moved.**
  157 §6: the four clone-only faults were never caught by the suite in
  any tier, only by the fresh-clone run.
- Do not touch `screens/fleets/`, research change mode (131), or
  orion2re. D17, T3 variant B and 156's D–G stay parked.
- No behaviour change on any screen.

## Part 1 — The fast tier

- **Which checks leave the commit gate.** Start from 157's ranking.
  Move to the push-only tier the checks that are expensive because they
  stand screens up at many sizes or counts — ranks 1 and 2 at least,
  the GAME-menu frame drawing (ranks 3 and 9) if the numbers justify
  it. Where you draw the line beyond that is yours to decide by
  measurement; **state the threshold and the reason** in the progress
  file. Cheap checks stay in the fast tier even if they are
  thematically related to a slow one.
- **The player's-own-figures pass goes push-only regardless.** 157 §4:
  the second pass of rank 1 over extracted figures exists only on a
  machine where the extractor has run, and it is most of the 15 s by
  which Data's gate is slower than a forker's.
- **The slow tier is a declared list, and the suite polices it.** Each
  push-only check carries its reason next to it in the suite (one line:
  what makes it expensive). A check in the fast tier asserts the set of
  push-only checks equals the declared list — the same shape as the
  marker inventory, so moving a check to the slow tier silently turns
  the suite red. **The list lives in exactly one place.**
- **The fast run says what it skipped.** Its PASSED line names the tier
  and the number of checks run and skipped, so a fast pass can never be
  mistaken for a full one in a log or a report.
- **Measure the result with 157's method:** several fast runs for the
  noise floor, then the fast-tier total on Data's tree and on a clone.
  No target number is set in advance; report what it is.

## Part 2 — The push gate

A **pre-push hook** in `tools/githooks/`, installed by
`tools/setup.py` exactly like the pre-commit hook, that runs the **full
suite** and refuses the push on any exit other than 0 or on a missing
PASSED line. Same rules as the pre-commit hook's header: 139 is a
segfault, not green; no automatic retry.

The **pre-commit hook switches to the fast tier**. Update its header
comment: what it runs now, why, and that the full suite moved to
pre-push — with the pointer to 157 and this order.

**Prove both gates by the path a fault would travel**, not by reading
the hooks:

1. A deliberate fault that only a push-only check catches (e.g. the
   drop-marker hit area narrowed, as in the original marker-width
   fault): **the commit goes through, the push is refused.** Do this in
   a scratch clone or on a throwaway branch against a throwaway remote
   — **the fault must never reach GitHub.** Record both hook outputs in
   the evidence folder, then remove the scratch setup.
2. A deliberate fault in a fast-tier check: **the commit is refused.**
3. A fresh clone plus `setup.py`: **both hooks are active.** Check by
   running them, not by reading `core.hooksPath`.

## Part 3 — Documentation

- **Fundament.** Decision 31 ("Verification via `tools/smoke_test.py`
  before every handoff") is **refined, not reversed**. Amend it in
  place or add a new decision under the Process group with the next
  free number — whichever keeps references honest; **the numbers are
  identities.** It must say: fast tier on commit, full suite on push,
  full is the default, the slow list is declared and policed, and the
  known cost of Option A in one sentence.
- **Status document:** the two tiers, the hook commands, the measured
  times.
- **`CLAUDE.md`**, if it describes the commit gate: bring it in line.
  The division-of-labour agreement lives there too — **do not touch
  that part.**
- **`157-parked-for-data.md`:** mark item 4 (suite gate) resolved with
  the hash.

## Finish

- Full suite green, fast tier green.
- Fresh-clone verification with `setup.py`, both input states as in
  156 — this run also proves the pre-push hook works from a clone.
- **Push** — Data explicitly asks for it with this file. The push
  itself must go through the new pre-push hook; that is its first real
  use. If it refuses, repair, re-verify, push.
- Final report **in German**, short:
  - which checks are push-only, and the threshold used
  - fast-tier time and full time, on Data's tree and on a clone,
    against the noise floor
  - the three gate proofs from Part 2: passed or not
  - what decision 31 says now, and whether it got a new number
  - push confirmation, and that it went through the pre-push hook
  - anything parked
