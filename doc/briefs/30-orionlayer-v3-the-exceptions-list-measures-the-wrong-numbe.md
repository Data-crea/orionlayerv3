OrionLayer v3 — "the exceptions list measures the wrong number"

READ FIRST: doc/v3_fundament.md, decision 6 and the "Diagnosis" group
of the working principles. Do not modify anything outside this
repository. Do not run git push.

=== TASK 0 — a53a730 was done for a number that turns out to be wrong ===
screen.py was split because it read 666 lines. Measured properly it is
218 lines of CODE, 295 docstring, 75 comment, 78 blank — under the
~300 guideline before the split and after it. The split bought 39
lines of a file that was never over, and it cost colonyselect its
independence from pygame, which the commit report names.

Do not revert on that reasoning alone. Find out whether the property
was load-bearing:
  - does any smoke check, tool or test import colonyselect without a
    display, or assert that it imports no pygame?
  - does anything else in the tree depend on that module being
    importable headless?

If YES: move `row_at` and `visible` back to screen.py and keep
`Window.top` and the clamp where they are. The offset is state, the
hit-test is geometry, and the screen computes `visible` and hands it
in the way it did before — that was the shape colonyselect was carved
out to have.

If NO: keep the split, and correct the REASON recorded for it. A
commit justified by a line count that task 1 disproves must not go on
standing on it in the status file. Give it the reason it actually has
or write down that it was done for a measure since retired — either is
honest, "it is there now" is not.

Report which of the two the evidence gave, with the grep.

=== TASK 1 — measure code, not prose ===
Measured across screens/, core/ and tools/: 24 files exceed 300 total
lines and 17 of those are under 300 lines of code. The ranking also
INVERTS — custom_race/screen.py is 558 total against
colony_summary/screen.py's 666, and 392 code against 218 — so a reader
working the list from the top splits the wrong file first. Confirm
both numbers with your own recount before using them; the twenty
entries in the status file may not be the same set my scan found.

1.1 The exceptions list in v3_projektstatus.md reports BOTH numbers
    per entry and ranks by CODE lines. Total length still matters for
    navigation, so it stays; it stops being the thing that decides.
1.2 The counts are COMPUTED, not typed — one helper that both the list
    and the smoke check read, the same trade the check count already
    made. Code = total minus blank, minus whole-line comments, minus
    docstring lines, via `ast` and not a regex: a triple-quoted string
    that is not a docstring is code.
1.3 Decision 6 gets one added sentence, not a new number: the
    guideline counts CODE, and a file over the line on documentation
    alone does not belong on the list. One line on why — a measure
    that penalises explanation works against the method that depends
    on it.
1.4 Working principles, "Diagnosis" group, beside the skip-condition
    entry, because it is the same failure: a proxy holds until
    something else moves the proxy. Here the proxy was that a long
    file does a lot, and this project's own documentation habit broke
    it. The two numbers above are the evidence.
1.5 Re-derive every entry and report which files LEAVE the list. If
    colony_summary/screen.py, colonylist.py and colonyrows.py all
    leave, say so plainly — three entries added over three packages
    that were never exceptions is the finding, not a side effect.

A file still over on CODE lines stays on the list and is not split
inside this package.

=== TASK 2 — the sprite groups are separated by a slot, and a reader
    who does not know that reads two groups as one number ===
Not a code change: a note. `Draw_Colony_Prod_Both_` increments
`drawn_count` BETWEEN groups (coldraw.cpp, the bare `drawn_count++`
before the imports loop), so a row reads as net, gap, secondary, gap,
imports, shortage. And for NEGATIVE imports the import group is drawn
with `Prod_Anims_` — the same artwork as the net — so on screen the
two groups are distinguishable only by that gap.

This is how the reference screenshot of 4 September was misread: Wolf
II's BC row, one gold bar and eight coins with an empty slot between
them, was read as a single 18 and used to confirm a value that was
10 plus 8. Put it where the next person compares against a native
screenshot — beside the deviation note in layout.json, which is
already about exactly these groups. Two sentences: the gap separates
groups, and negative imports share the net's sprites.

=== VERIFICATION ===
  - smoke test green; count before and after; CLAUDE.md and the
    Snapshot table both updated.
  - If TASK 0 lands on "move back", that is its own commit and it goes
    FIRST, so task 1's recount describes the tree that will exist.
  - Not pushed.

=== WHAT YOU MAY SKIP ===
  - TASK 1.2: skippable, cost is a hand-typed count that drifts — and
    the last package already showed that the copy without a checker is
    the one that goes stale.
  - TASK 2: skippable, cost is that the next side-by-side repeats a
    mistake that has now been made once and is written down nowhere.

Zu Aufgabe 0 habe ich bewusst keine Antwort vorgegeben. Ich habe a53a730 nicht gesehen — es liegt lokal — und mein letzter Versuch, eine Naht aus einem Bericht zu beurteilen, ging in beide Richtungen daneben: erst hielt sie angeblich nicht, dann stellte sich heraus, dass gar nicht geteilt werden musste. Der Grep entscheidet das besser als ich.