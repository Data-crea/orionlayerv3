Two live findings after 8ac321c

Read doc/v3_fundament.md first. Both were seen in the running game against the pushed build, not in a check. Both need a live proof, not only a passing test.

1. The click lands one cell to the left

Horus IV: clicking the rightmost green cell selects the cell beside it. An offset of exactly one cell.

Find it and say which side is wrong — the drawing or the hit-test. Do not guess from the symptom; the row now has markers in it, and whether a marker counts as part of its group differs between the two paths is a plausible place to look, not a conclusion.

The more important half. The ink check was built for exactly this class of fault and did not catch it. It compares the drawn frame against the drop target's hit-test; it evidently does not cover the pick-up path (slot_at_x). A check that passes while the game mis-selects is a check that tests the wrong thing.

So: extend it so it would have caught this offset. The rule to assert is that the cell under a pixel is the cell drawn at that pixel, for every cell of every fixture row, pick-up and drop alike — not that two functions call a third. That was true yesterday too, and it was true while the drop bands were consistently wrong.

Report which existing check would have had to change, and why it did not cover this.

2. The minimap is still not black

The fill was measured, changed and accepted, and in the running game the panel still shows the panel blue.

Two possibilities, and the answer is a measurement: the change does not reach the box that is actually drawn, or it reaches it and something draws over it afterwards. Sample the running frame the same way as before and say which.

If it turns out the fill lands on a box that is not the one on screen, that is worth a line somewhere durable — it is the help-popup lesson in a new costume: the background you see is not always the background that is set.

Acceptance
The offset is gone, shown live: a click on a named cell of a named colony selects that cell, in the wire log and on screen.
The extended check fails against the current build and passes after the fix. Show it failing first — a check that has never been seen to fail is a check nobody has tested.
The minimap is black in the running game, shown by a sample, not by reading the code.
Smoke green under SDL_VIDEODRIVER=dummy. Full diff shown; Data pushes.
While you are in there

Two things from the last round that were reported as planned and did not appear in the acceptance:

The cell-per-icon change (one cell per drawn icon rather than per pop, so a held cluster leaves the row as it does in the original). Was it built? If yes, it is a behaviour change and belongs in the status document as one. If no, say so and leave it — it is its own task, not something to slip in here.
The marker fill looked lighter in one row than another in the acceptance strips. Probably contrast against neighbours; confirm it is one colour value and not two.