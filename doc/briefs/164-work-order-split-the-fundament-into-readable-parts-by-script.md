# Work Order 164 — Split the fundament into readable parts, by script

First line for references: "Work Order 164 — Split the fundament into
readable parts, by script"

Filed as 164 because 163 was the last one. Check that before filing and
take the next free number if it is taken.

Read `doc/v3_fundament.md` first — by section, not whole. Work order 162
is the model: same shape, same discipline, same kind of proof.

## Why (Data)

`doc/v3_fundament.md` is about 200 KB, two and a half times the 80 KB
reading budget of work order 127, and every session is supposed to read
it at startup. Its four sections are already there, but the first alone
is 106 KB:

  1. Architecture decisions      106.2 KB   lines   14-1913
  2. Working principles           60.6 KB   lines 1914-3026
  3. orion2re facts               26.0 KB   lines 3027-3492
  4. pygame facts                  1.2 KB   lines 3493-3516

The goal: **a session reads an index and the parts its task needs, and
each part fits the budget.** Nothing in the fundament changes in
meaning; this is a move, exactly like 162.

## How this run works

**Unattended, no reporting stops.** Data has decided the direction and
the constraints below; everything inside them is Claude Code's. Questions
go into `doc/briefs/164-parked-for-data.md` and do not stop the run.
Progress into `doc/briefs/164-progress.md`. Evidence under
`~/orionlayer-fixtures/evidence/work_order_164/`. Write the progress file
so a fresh session can resume from it alone.

## Hard constraints

- **The text does not change.** Not a sentence rewritten, not a rule
  improved, not a contradiction resolved, nothing merged, nothing
  dropped, nothing added. If two rules contradict each other, park it.
- **Decision numbers keep their numbers.** They are identities, cited
  all over the tree. A decision moves to another file; it never gets
  renumbered or reordered.
- **The move is done by script**, not by reading blocks into context and
  writing them out again — the same rule that made 162 safe.
- **Proof of identity, before the commit:** a script concatenates the
  parts in order, strips only the lines the split itself added (each
  part's own title line and any navigation line, and these must be
  recognisable by a fixed pattern), and compares the result byte for
  byte with the original file. Identical, or the run rolls back.

## Part 1 — The cut

Split into `doc/fundament/` — file names, grouping and the exact
boundaries are Claude Code's choice, guided by:

- **Section 1 must be split further.** Group decisions by subject, in
  their existing order, never by line count alone.
- **Sections 3 and 4 may stay whole or be merged**, whichever reads
  better; both are small.
- **Size limit: no part over 40 KB**, half the reading budget, the same
  number 162 uses for test modules. Exceptions only if listed with a
  reason, the way decision 6 handles files over ~300 lines.

`doc/v3_fundament.md` itself becomes the **index**: the title, the
preamble that is already at the top, and a list of the parts — each with
its file name, one line on what it covers, and which decision numbers
live in it. The index carries no rule text of its own. A rule is in
exactly one file, and the index points at it. Keeping the old path as
the index means every existing reference to the fundament still lands
somewhere useful.

## Part 2 — The startup rule

Today the rule is "read the fundament first". Rewrite it, in `CLAUDE.md`
and in the index itself, to: read the index first, then the parts the
task needs; the working-principles part is always read. Claude Code
writes the wording. If the rule appears in both files, both copies must
read the same, word for word — that was a real fault in 162.

## Part 3 — References

- Documents, briefs and comments that cite the fundament by line number
  will break. Find them with a grep, point each at its part, list what
  changed in the progress file.
- **The smoke suite reads the fundament** (decision-number uniqueness
  and the single-literal rules among them). Those checks must work
  against the new layout. They may be adapted where the path or the file
  boundary forces it, but not weakened: after the change the full suite
  is green, and the check count may only go up, never down.
- Add one check: every part is listed in the index, and every decision
  number appears in exactly one part.

## Abort rule — this replaces a decision by Data

If the byte-for-byte comparison fails and the cause cannot be fixed in
the splitting script, roll the whole cut back and build the **fallback**
instead: split at the four existing section boundaries only, index as
above, and section 1 stays one file over the limit, listed as an
exception with its size. The same proof applies. Say in the report which
of the two was built and why.

## Acceptance

- Concatenation identical to the original; the diff (or its absence) in
  the evidence folder.
- Every decision number present exactly once, and the same set as before.
- Full suite green, fast tier green, on a fresh clone.
- No part over 40 KB except those listed as exceptions with a reason.
- The startup rule reads the same in `CLAUDE.md` and the index.
- Push is Data's decision.

## Final report for Data — in German, short, no code

Data will read this and nothing else. Answer only these:

1. **Built or rolled back?** Full split or fallback, and in one or two
   sentences why.
2. **Is the text unchanged?** Yes or no, and what proves it.
3. **How is it laid out now?** The parts with their sizes, one line
   each, and which decisions are where.
4. **How much does a session read at startup now** compared to 200 KB
   before?
5. **What changed in `CLAUDE.md` and the index?** Quote the new startup
   rule.
6. **Is anything parked for Data?** In plain words.
