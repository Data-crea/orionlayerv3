OrionLayer v3 — "which branch has been seen, and which has been computed"

Small package, one commit. Do not modify anything outside this
repository. Do not run git push.

=== TASK 1 — name the four branches where they are listed ===
screens/colony_summary/colonyrows.py, drawn_production.__doc__ lists
the four net branches as an unlabelled table. Label them A to D in
that table, in the order they are already written — A and B under
"imports[t] byte-negative", C and D under "otherwise" — so anything
that refers to a branch has one place to refer to. Do not invent a
different scheme; the order in the table is the order in the C++.

=== TASK 2 — record which of the four has a live witness ===
Under that table, in drawn_production.__doc__:

  WHICH BRANCH HAS A LIVE WITNESS, and which rests on the source and
  the suite alone — 4 September 2026, reference save, 11 colonies:
    B (production - abs(imports))    NINE colonies. Wolf II's BC, 18
                                     stored against 10 drawn.
    C (production[t])                every other row on that save.
    A and D (both subtract           NO WITNESS. maintenance[INDUSTRY]
    maintenance)                     is 0 on all eleven, so neither
                                     branch is ever reached. A save
                                     with an industry-maintenance
                                     building would settle both.

The precedent is core/structs/player.py, which records which evidence
stands PER FIELD rather than letting one spec-wide flag imply it
covers everything. This is the same question one level down: not which
field, but which branch.

=== TASK 3 — the same distinction in the status entry ===
v3_projektstatus.md's entry currently says the net is computed "in
four branches (coldraw.cpp:73-94) of which only one is
`production[t]`", which reads as if all four stand on the same
footing. Add the distinction in the same one-line-each style: two of
the four are confirmed against a running game, two are transcribed and
tested and have never been reached by a live save.

=== NO SMOKE CHECK, deliberately ===
Do not add one. The markings this tree holds under checks are
statements about behaviour that is still true, and a check keeps them
from silently disappearing. This is a record of EVIDENCE, and the
right thing for it to do is disappear — the day a save with a non-zero
maintenance[INDUSTRY] turns up, A and D get their witness and the note
should shrink. A check on the words "NO WITNESS" would make the good
outcome the one that fails the suite.

=== TASK 4 — two tidy-ups found while reading ===
4.1 colonyrows.py:144 — no blank line after `_low_byte_signed`, and
    the function sits inside the constants block, between the
    POP_LIMIT_CAP group and GOVERNMENT_UNIFICATION. It belongs beside
    `drawn_production`, which is the only thing that calls it and the
    only place its docstring points.
4.2 Confirm nothing else in the tree separates two top-level
    definitions without the blank line, so this was the one slip and
    not a habit.

=== VERIFICATION ===
  - smoke test green, count unchanged (this package adds none).
  - Not pushed.