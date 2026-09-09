OrionLayer v3 — "the industry row cannot tell its branches apart"

Small package, one commit. Do not modify anything outside this
repository. Do not run git push.

Everything below rests on ONE claim I did not verify in your tree, and
task 1 is to check it before any of the rest is written down. My last
three summaries of this material each failed a check — the BC row read
as 18, the A/D grouping, and "one building settles both" — so treat
this the same way and report if it does not hold.

=== TASK 1 — verify the derivation, or stop ===
`COLCALC::Pre_Import_Computing_` (colcalc.cpp, the function containing
the assignment at :507-511) appears to write

    imports[ECON_INDUSTRY] = min(maintenance[ECON_INDUSTRY],
                                 production[ECON_INDUSTRY])

with maintenance read as an unsigned byte. Confirm the line numbers,
confirm the enclosing function, and confirm it is UNCONDITIONAL for a
colony — if it sits inside a branch that some colonies skip, the whole
package is wrong and should be reported rather than adapted.

If it holds, then on the industry row, and ONLY under the assumption
that `production[ECON_INDUSTRY]` is never negative:

  maintenance[INDUSTRY] == 0 -> imports[INDUSTRY] == 0 -> branch C
                                -> production, which is also
                                   max(0, production - 0)
  otherwise                  -> A or D depending on the cast, and BOTH
                                are max(0, production - maintenance[t])

so all four branches collapse to one expression. Check that yourself
against the four as transcribed rather than taking my reduction.

The assumption is load-bearing and must be written down wherever the
conclusion goes: with a negative `production[INDUSTRY]` the collapse
fails — A returns 0 where C returns the negative value.

=== TASK 2 — A and D are not "unwitnessed", they are indistinguishable ===
If task 1 holds, correct the witness record in
`drawn_production.__doc__`. The present text says A and D have no live
witness and that a save with an industry-maintenance building would
settle them. The first half is true and the second is not: no savegame
can settle A against D, because on the only row that reaches either
they compute the same expression. That is a stronger and less
hopeful statement than the one it replaces, and it should not be
softened — an experiment that cannot come out two ways is not an
experiment waiting for data.

Say what a building WOULD settle: D against C, which is a real
distinction (production against production minus maintenance) and is
the one the reference save cannot make.

=== TASK 3 — item 7 does not apply to the industry row ===
doc/orion2re_open_fixes.md item 7 asks whether the original binary
sign-tests the byte or the word. Add which rows the answer can change:
not industry, where both sides of the test reach the same expression,
but FOOD, RESEARCH and BC, where the cast decides between B
(production - abs(imports)) and C (production) and those differ
sharply.

Give it the example the question deserves, and verify the citation:
`imports[ECON_BC]` is written as `(uint8)maintenance[ECON_BC] -
production[ECON_BC]` (colcalc.cpp:1265) and is not clamped, so a value
like 200 is positive as a word and negative as a byte — under the
cast, branch B then subtracts abs(200) from a small production. Say
whether that is reachable with plausible BC maintenance or only in
principle; if the field cannot get there, the example is worse than
none and a smaller one should replace it.

This makes the question sharper for Joe, which is the point — item 7
currently reads as a curiosity and it is not one.

=== TASK 4 — check whether the branch checks can fail ===
The previous package asked for all four branches "with values chosen
so the branches give DIFFERENT answers". If task 1 holds, that is
impossible for A against D, so the existing checks cannot be doing
what was asked.

Find out which:
  - if the checks assert only the RETURNED VALUE, then deleting
    branch A and letting D catch those cases passes the suite. Try it
    and report the outcome.
  - if the suite is green with branch A removed, the check is not
    holding A up and must say so rather than appear to. Either assert
    which branch was TAKEN — the cast is already a named function that
    a check can aim at — or record plainly that A is covered by the
    transcription and not by a test, in the same sentence that the
    witness note uses.

Do not manufacture a distinction that the code does not have. A test
that passes for a reason nobody can name is worse than a gap that is
written down.

=== VERIFICATION ===
  - smoke test green; report the count and whether it changed.
  - Report the branch-A deletion result either way — that is the
    finding of this package whichever way it comes out.
  - Not pushed.

=== WHAT YOU MAY SKIP ===
  - TASK 3's example: skippable if the value turns out to be
    unreachable. Then say so in item 7 — "the cast changes the answer
    only at import values this field cannot hold" is itself half an
    answer to the question.
  - Nothing else. Tasks 2 and 4 are the package.