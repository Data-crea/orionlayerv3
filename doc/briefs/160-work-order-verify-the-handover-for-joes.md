# Work Order 160 — Verify the handover for Joes before it is sent

First line for references: "Work Order 160 — Verify the handover for Joes before it is sent"

Filed as 160: the highest number in `doc/briefs/` was 159, confirmed in
the tree before filing.

## How this run works

Unattended, no reporting stops. Questions for Data go into
`doc/briefs/160-parked-for-data.md`, progress into
`doc/briefs/160-progress.md`, evidence under
`~/orionlayer-fixtures/evidence/work_order_160/`. Commits through the
fast tier; the push through the full suite (decision 31 as refined by
158). Push only the brief files of this order. **No code changes in
either tree.**

## Why

Data is about to send Joes `~/Downloads/orionlayer_notes_for_joes.md`.
Part A (Joes' code) was checked against his 2.0.0 upload and is **out
of scope**. Parts B, C and D were written from our own documents and
were **not** checked against `~/orion2re`. This order checks them.

## Rules

- `~/orion2re` is **read-only**: `git log`, `git show`, `git diff`,
  `grep`. No checkout, no build, no patch.
- No live runs.
- orion2re never goes online.
- The handover is Data's text; wording and tone stay his.
- **Correct only statements that are false.**
- Every correction in a **copy**, not in the original.

## Parts

1. **Part B against `orionlayer-local`.** For B1–B8: is the change in
   the branch (name the commit); does it touch exactly the files named;
   is the stated status right.
2. **The move-pop contradiction.** `doc/ext_move_pop.patch` says "NOT
   YET APPLIED"; `doc/orion2re_open_fixes.md` item 12 says patched and
   verified live. Establish which is true from the branch, name the
   stale document, **park the repair**.
3. **"Still open on our side."** Radio buttons, Planets filters,
   SELECT NEW RESEARCH. Check whether 156–159 touched any of them.
4. **The `doc/...` references.** Every named file must exist in the
   pushed repo, and the repo URL must resolve.
5. **Factual claims in C and D**, e.g. "55 ms instead of 725 ms" and
   "`_ship_node[]` can be rebuilt from `_ship[]`".
6. **Anything else in B, C or D** that would not be signed as true.

## Deliverables

- `doc/briefs/160-findings.md` — per part: OK, or what is wrong with
  the evidence. At the top, every changed sentence as old → new.
- Corrected handover at
  `~/orionlayer-fixtures/evidence/work_order_160/orionlayer_notes_for_joes.md`;
  the original in `~/Downloads/` stays untouched.
- `doc/briefs/160-parked-for-data.md` — repo documents found stale,
  starting with the move-pop header.
