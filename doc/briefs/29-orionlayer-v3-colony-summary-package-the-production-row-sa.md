OrionLayer v3 — Colony Summary, package "the production row says what the original says"

READ FIRST: doc/v3_fundament.md, including decisions 6, 23, 33, 43
(withdrawn) and 46. Do not modify anything outside this repository.
Do not run git push.

Line numbers are from the tree at b55c96b and orion2re 1.60.0. Verify
before editing; if one has moved, fix the citation in the same commit.
That instruction has now found two wrong citations in two packages, so
treat it as the first task and not a formality.

=== TASK 1 — split screen.py, before it grows again ===
screen.py is at 666 lines against a ~300 guideline and second on the
exceptions list. Move `_row_at` and `_visible_rows` into
`colonyselect.Window` as methods.

The seam is not "list geometry": it is the OFFSET. `_row_at` is a band
number plus the offset and `_visible_rows` is the number Window
already needs in order to clamp, so both are Window's business and
neither is a new concern. Do not create a fourth module — the
three-copies rule applies to modules too.

The wheel handler STAYS in screen.py: taking input is the screen's
job, interpreting it is not.

CHECK BEFORE YOU MOVE: if `_visible_rows` touches more screen geometry
than `list_area` and `row_height`, the seam does not hold. Say so and
leave the split undone rather than take it badly — a bad seam costs
more than 666 lines.

Report the line counts after, and update the exceptions list in
v3_projektstatus.md whichever way it goes.

=== TASK 2 — the NET rule, which is a correction and not an addition ===
Evidence: `COLDRAW::Draw_Colony_Prod_Both_` (coldraw.cpp:36) computes
what it draws first and draws `production[t]` only in one of four
branches (coldraw.cpp:71-94, transcribe all four):

  (int8_t)imports[t] < 0 :
      t == ECON_INDUSTRY -> max(0, production[t] - maintenance[t])
      otherwise          -> production[t] - abs(imports[t])
  otherwise :
      maintenance[ECON_INDUSTRY] == 0 or t != ECON_INDUSTRY
                         -> production[t]
      otherwise          -> max(0, production[t] - maintenance[t])

`maintenance` (offset 239, u8[4]) and `imports` (243, i16[4]) are
already in the verified core/structs/colony.py, so decision 23 is
satisfied and no new offset work is needed.

2.1 The computation belongs in colonyrows.build_rows, beside the
    existing `"production": list(col.production)`, because that is
    where the offsets live and colonyoutput is handed plain dicts.
    Keep `production` in the dict — the four SORT keys read it
    (colonyrows.py:494-496) and the original sorts on the stored
    value, not on the drawn net. Add the net as its own key so the two
    cannot be confused; a name that says which one it is.
2.2 colonyoutput draws the net.
2.3 THE CAST IS DELIBERATE AND STAYS. coldraw.cpp:71 tests
    `(int8_t)colony->imports[prod_type] < 0` — the LOW BYTE of an
    int16 — while the same function tests `colony->imports[t] < 0`
    without the cast at :151. Two sign tests on the same field,
    disagreeing for any value whose low byte and whole differ in sign.
    Transcribe it AS WRITTEN, with a comment naming both lines, and do
    not normalise it to a plain comparison. Then add it to
    doc/orion2re_open_fixes.md as a QUESTION in the shape item 6
    already has — does the original binary sign-test the byte or the
    word? — and NOT as a fix request. It changes nothing at realistic
    import values, which is exactly why it would never be noticed.

=== TASK 3 — the shortage, which is an addition ===
Same function: `shortage = maintenance[t] - imports[t] - production[t]`,
clamped to 0 below 1 (coldraw.cpp:60-64), drawn with
`COLONY::Short_Anims_` (coldraw.cpp:170-177, colony.cpp:2192).

3.1 THE REFUSAL IS PART OF THE TRANSCRIPTION. The shortage group sits
    in the ELSE branch at coldraw.cpp:151: it is drawn only when
    `imports[t] >= 0` AND `t != ECON_INDUSTRY`. A shortage computed
    and shown on the industry row would be an invention. Assert the
    two conditions, not just the arithmetic.
3.2 Display: the row's VALUE stays the net; the shortage is a second
    element beside it, in the red the original's sprites carry. The
    wording is layout.json's, per decision 15 — a template, not a
    format string in the renderer, and no shortage element at all when
    the value is zero.
3.3 Wolf II is the reference case and belongs in the comment: 13 pops,
    production 12, imports 0, so shortage = 13 - 0 - 12 = 1, and the
    original draws exactly one red marker. Screenshot evidence,
    4 September 2026.

=== TASK 4 — what is LEFT of deviation (1) ===
After tasks 2 and 3 the panel still omits two of the four groups the
original draws per row: `imports[t]` (coldraw.cpp:46, drawn with
`Import_Anims_` or `Prod_Anims_` depending on sign) and the secondary
group — `imports[ECON_INDUSTRY]` on the FOOD row, `pollution`
(offset 8) on the INDUSTRY row (coldraw.cpp:51-58).

Rewrite layout.json's `output._deviation_note` to say what is now
true rather than shrinking the old wording: the leading number is the
original's net, the shortage is drawn, imports and the secondary group
are not. Both remaining ones are REACHABLE — all three offsets are in
the verified spec — and are not drawn because four numbers on one row
of a 464x201 panel is a layout question this package does not open.
Same form as the blockade note in colonyrows.py.

=== TASK 5 — checks ===
5.1 All four net branches, one row each, with values chosen so the
    branches give DIFFERENT answers. A test where every branch returns
    production[t] proves nothing — pick maintenance and imports so a
    wrong branch is visible.
5.2 The shortage refusals: a colony with a shortage on the industry
    row draws none, and one with positive imports draws none.
5.3 Zero shortage draws no element at all — the same shape as the
    empty-selection check, which asserts the surface is untouched.
5.4 The `(int8_t)` cast: one row whose imports differ in sign between
    the byte and the word, asserting the byte wins. This is the check
    that stops a later reader from "fixing" the cast.
5.5 The deviation note still names imports and the secondary group,
    the way the existing marking checks work.

=== VERIFICATION ===
  - python tools/smoke_test.py green; count before and after; CLAUDE.md
    and the Snapshot table both updated, which task 0 of the last
    package made mandatory rather than polite.
  - tools/colony_list_preview.py --live if a game is up. If it is, the
    thing to look at is a colony with non-zero `maintenance[INDUSTRY]`,
    because that is the case task 2 exists for and Wolf II is not it.
    Report which colony you used and both numbers. If no such colony
    is in the save, say so — an absent case is a result, not a pass.
  - Suggested split: task 1 alone, then tasks 2-5. Each passes alone.
  - Not pushed.

=== WHAT YOU MAY SKIP ===
  - TASK 2: NOT skippable. It is the only item that changes a number
    the player reads.
  - TASK 2.3 and 5.4: skippable together, never separately. The cast
    without its check is a bug waiting to be tidied away.
  - TASK 3: skippable if the display of a second element per row turns
    out to need a layout decision. Then say what the decision is and
    leave the arithmetic in place unused — clearly marked as unused,
    because a computed value nobody draws is the next package's
    mystery otherwise.