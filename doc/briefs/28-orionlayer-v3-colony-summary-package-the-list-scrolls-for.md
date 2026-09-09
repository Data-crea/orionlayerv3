OrionLayer v3 — Colony Summary, package "the list scrolls, for viewing only"

READ FIRST: doc/v3_fundament.md, including decision 46, which this
package adds. Decisions 33, 35 and 36 are cited below. Do not modify
anything outside this repository. Do not run git push.

Line numbers are from the tree at 0c5ffcd and orion2re 1.60.0. Verify
before editing; if one has moved, fix the citation in the same commit.

WHAT THIS PACKAGE DOES AND DOES NOT DO
It makes the HD list scroll. It sends NOTHING to the game — no field
activation, no click, no key. `_first` stays where the game put it,
and per decision 46 that is fine as long as nothing is injected. The
synchronisation belongs to the control layer and is deliberately not
started here.

=== TASK 0 — the check count has two homes and one checker ===
v3_projektstatus.md's Snapshot table says 55; the suite runs 63.
CLAUDE.md's copy is under smoke_test.py:4616 and the table's is not.
Per decision 36 a hand-copied number is legitimate only with a
checker, so: correct the table to the current count and extend the
existing check to hold BOTH files against the run. Assert them
against the run, not against each other — two numbers agreeing with
each other and not with the suite is the state this prevents.
Verify it bites by changing one of the two.

=== TASK 1 — decision 46 into the fundament ===
Add the entry supplied with this package verbatim, in the group
"The orion2re boundary", after 45. No renumbering. The
"decision numbers unique" check at smoke_test.py:4509 must still pass
and its printed count goes up by one.
Note: 46 describes work not yet built, so it carries no check of its
own here. TASK 4's injection guard is what enforces the half of it
this package is responsible for.

=== TASK 2 — the scroll offset ===
2.1 State. Put it in screens/colony_summary/colonyselect.py, beside
    Selection, and keep screen.py's access as a property the way
    `_rows` and `_selected` already are. The reason for the shared
    module is that a SORT touches both and touches them DIFFERENTLY —
    it resets the window (`_first = 0`, colsum.cpp:832) and leaves the
    selected colony alone (colsum.cpp:830-837, which never assigns
    `_g_colony_n`). Two rules for one event belong where a reader sees
    both at once.

2.2 Clamping is TRANSCRIBED, not chosen. Upper bound:
    `first <= max(0, n_rows - visible)`, because `Increment_First_` is
    only reached when `_g_colony_list_ptr[_first + 10] != -1`
    (colsum.cpp:796) — the original stops before the window's last
    slot would be empty, so the last page is full. Lower bound 0
    (`Decrement_First_`, colsum.cpp:211-214). And with fewer rows than
    fit, the offset does not move at all (`colonies_count >=
    num_items`, colsum.cpp:209 and :226). Cite each of the three.

2.3 `visible` is DERIVED from `list_area` and `row_height` at the
    current resolution, never hardcoded to ten. It is ten today by
    arithmetic (see layout.json's _row_height_note) and that is a
    coincidence of the frame artwork, not a transcription. Decision 46
    says why this matters later.

=== TASK 3 — the renderer takes a first row ===
3.1 colonylist.render / _draw_rows take `first` (default 0) and slice.
    The module stays pure — it is handed dicts and knows nothing about
    where the offset lives.
3.2 _draw_overflow: its docstring currently says "The line is NOT a
    scrollbar and is not a step towards one." This package IS that
    step; rewrite the paragraph rather than leaving it to contradict
    the code below it. The line stays and now reports how many rows
    are hidden IN TOTAL, above plus below. Keep the layout.json
    template ("{count} more not shown") — the wording is still true
    and the count is now the honest one.
3.3 The line is the only indication that the list scrolls, and that is
    a deliberate choice to write down: the original draws a slider
    (`_slider_bar_position`, colsum.cpp:749-753) and HD does not. Note
    it as NOT DRAWN in colonylist.py, in the same form the blockade
    and the colony event already use — an omission that is recorded is
    a state, one that happens to work out is a bug waiting for its
    second cause. Do not build the slider in this package.

=== TASK 4 — input, and the guard that makes this package safe ===
4.1 Mouse wheel over `list_area` scrolls one row per notch. Mark it
    **HD EXTENSION** where it is handled: MOO2 has a slider and no
    wheel. Marked in the code, in layout.json's `list` block, and in
    a smoke check that fails if the marking disappears.
4.2 A scroll must not reach the game. Add a smoke check that installs
    the capturing client the sort-button checks already use
    (smoke_test.py, class _Cap), scrolls the list to its bottom and
    back, and asserts inject_click, activate_field and inject_key were
    all called ZERO times. Cite decision 46 in the comment. This is
    the check that lets the package ship without the synchronisation.
4.3 Scrolling must not move the selection: it is a COLONY, not a row
    index (colsum.cpp:830-837). Assert the selected colony index is
    unchanged across a scroll.
4.4 A sort resets the offset to 0 and leaves the selection alone —
    both in one check, citing colsum.cpp:832 for the first half and
    the absence of an assignment for the second.

=== VERIFICATION ===
  - python tools/smoke_test.py green; report the count before and
    after, and update CLAUDE.md and the status table together (TASK 0
    makes the second one checked, so a stale count now fails).
  - Run tools/colony_list_preview.py with and without --live and say
    which you ran. If --live is available, scroll to the bottom and
    confirm the eleventh colony appears — that is the whole point of
    the package and it cannot be proved from the synthetic empire,
    which is why the tool has that switch.
  - Each commit passes the suite alone. Suggested split: TASK 0+1 as
    one commit (numbers and the decision), TASK 2-4 as the second.
  - Not pushed.

=== WHAT YOU MAY SKIP ===
  - TASK 4.2: NOT skippable. Without it, the claim "this package sends
    nothing" is an intention, and the first future edit that adds an
    injection to a scroll path will not fail anything.
  - TASK 3.3: skippable, cost is a scrolling list with no visible
    indicator that it scrolls beyond one line of text, and no record
    that the original had one.
  - TASK 0: skippable in this package, but then say so — it is the
    item you found yourself, and a found-and-deferred entry belongs in
    the commit body so it is not found a third time.