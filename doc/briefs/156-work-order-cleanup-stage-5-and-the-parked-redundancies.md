# Work Order 156 — Cleanup: Stage 5 and the parked redundancies

First line for references: "Work Order 156 — Cleanup: Stage 5 and the parked redundancies"

Filed as 156: the highest number in `doc/briefs/` was 155 when this
was filed (work order 155, Fleets: the bar under the map).

Read `doc/v3_fundament.md` first.

## Why

OrionLayer has grown to a size where every line is something a forker
(or Data, in six months) has to understand. The orion2re release on
22 November is the deadline for a playable HD frontend, and the repo
has to be tidy by then. The goal of this order is **less code with
identical behaviour** — not new structure, not new features.

Two known sources of dead weight:

- **Stage 5**, described in the fundament: old modules that were
  superseded but never deleted. The cell renderer stays as the
  fallback for missing figure sets.
- **`doc/redundancy_audit.md`** (work order 126 part I): only the
  clear cases were extracted, the rest was parked. That audit also
  excluded `tools/` entirely, and `tools/` is now the largest part of
  the tree.

## Hard constraints

- **No behaviour change on any screen.** If a cleanup would change
  what is drawn or sent, it is not a cleanup — park it.
- **Redundancy that is the point stays** (fundament, "Refactoring":
  `ext_diag.py` re-derives the FIELD_LIST offsets on purpose).
  Anything else that exists as a deliberate second source stays too;
  say why.
- **Markers (HD EXTENSION, DEVIATION, DERIVED) move with their code
  in the same commit** — module, status document and smoke test. A
  marker must never disappear because its module did.
- Do not touch `screens/fleets/` (work order 151 line is active) or
  the research change-mode work (131, deferred). Do not touch
  orion2re.
- One commit per theme, each through the pre-commit hook. **No push**
  — that is Data's decision.
- No new tools, no new abstractions unless the third-copy rule forces
  one.

## Stop 1 — inventory, no code

Report, with evidence from the tree:

1. **Line count baseline.** Total Python lines and code-only lines
   (without blank, comment, docstring), per top-level folder. State
   the method so the same count can be repeated after Stop 2.
2. **Stage 5 candidates.** Every module that is superseded: what
   replaced it, who still imports it (full-project grep, including
   `tools/` and the smoke test), which markers it carries.
3. **The parked audit groups.** For each group in
   `doc/redundancy_audit.md` that was not extracted: still diverged?
   Extract, merge, or leave — with one sentence of reason.
4. **`tools/` audit**, same method as 126 part I: duplicated helpers,
   one-off scripts whose work order is closed, probes nothing calls
   anymore. Distinguish "unused" from "used only by hand" — a manual
   diagnostic is not dead code.
5. **Risk per item**: what could break, and which smoke-test
   assertion (if any) would catch it. Items no test would catch are
   flagged.

Group everything into proposed commits and stop. Data decides which
ones run.

## Stop 2 — implement the approved commits

- One commit per approved group, smoke test green after each.
- Verify against a **fresh clone**, not the working tree.
- Final report: line count again with the Stop 1 method, before/after
  per folder, list of deleted files, list of moved markers, and
  anything parked in `doc/briefs/156-parked-for-data.md`.

## Acceptance

- Smoke test green, fresh-clone verified.
- Every screen behaves exactly as before; no marker lost.
- Before/after numbers measured the same way, not estimated.
- The status document lists what Stage 5 removed; the fundament
  changes only if a decision was actually reversed.
