Work order — Colony list: native comparison, figure origin, drop speed

Read doc/v3_fundament.md before touching anything. Parts A–F of the previous order are committed and pushed up to Part E; 7ca487e (Part F) is unpushed. This order goes on top. Report with diff summary and check count; Data pushes.

Reference save ab70cc9ad5442335, loaded in the game as slot 8; fixtures.verify_colonies before every run that touches the game, stop at the first non-returning round trip. Evidence names the save.

Part G — the comparison beside the original (owed)

--native at the four F9 sizes (1920×1080, 2560×1440, 3440×1440, 3840×2160 as requested — the granted surface is what it is; name both) did not appear in the Part F report. Run it now, one snapshot each, HD beside the original's rows from the same snapshot.

Report as questions, not findings, per size:

Do the six columns sit over the original's, plates included, empty rows included?
Do the figures fill the columns as the original's do at the same count (the 79 % residue is expected at 1080p/2160p, the 89 % at 1440p)?
Does the longest visible name sit inside its cell, and is the ink clear of the frame rail?
Does No Farming sit where the original's does? (Reference save cannot show it — one extra snapshot on natives_autosave for this line only, and say so.)
Does the description paragraph read like the original's?

Anything that differs and has no marker at the three homes is a finding, listed separately from the questions.

Part H — the figure origin in the cell

Data's observation on the 1080p reference-save screenshot: figures sit too high in their cells.

The source: draw and both hit tests use 31·i + 38 (colsum.cpp:683, :1006, :963); the field is at 31·i + 34 (colsum.cpp:311). The figure's top is four native px below the field's top. The geometry round set the figure at band top + 1 px because 46 of 54 masters carry ink on canvas row 0 — that was clearance for the plate line, not a transcription.

Answer first: where is the figure origin today — band top + 1, or 4·step below the band top? Then:

If band top + 1: transcribe. Origin = band top + 4·step. The band rule becomes 28·step + 4·step (top) plus whatever the bottom needs — the masters have ≥3 transparent rows below their ink, so probably nothing, but measure it as before, over the whole set.
Then check whether the band still holds the step at each size. If 1440p loses step 3 again, that is a number for list_area in layout_reference.json, the same way as last time, from the lower band, and reported before the plate is rebuilt. Not clipping.
The 1-px clearance rule and the 4-px transcription are two different facts; keep both written down where the band rule lives, so the next person does not "simplify" one away.

Beside native at 1080p, as a question: does the figure's top sit where the original's does relative to the cell's top edge?

Part I — the drop speed, two candidates, nothing else

Part F measured 731 ms median per drop, HD share 271 ms. Two HD-side candidates were named. Build both, measure again, same table.

RESORT only when needed. Today every move sends the sort key (83 ms). Question first: is _g_sort_index (or whatever the game holds as its sort state) readable on the wire — snapshot, field list, anything? If yes: skip RESORT when the game's state already equals the wanted one; a check asserts the comparison reads the wire, not HD's own memory of what it last sent. If no: RESORT stays, and the answer is written down with the place it was looked for — an unreadable state is not a state to assume.
finished on the first snapshot that shows the effect. The tail is 213 ms after the effect is visible. The step ends when the EFFECT_PAIRS predicate is met, not after a further wait. Say what the extra wait was for; if it guarded something real (a second snapshot confirming the first), keep that and say why.

Then ten drops, same table as Part F — per-step ms, states, visuals, ended on our floor or beyond — before and after, side by side. The number that matters is the HD share; the game's 460 ms is not ours to touch.

Not this round, and not proposed: option (b), drawing the moved figure before the snapshot. Decision 33; the game holds 63 % and nothing may look moved that the game has not moved.

Small
The hover popup ("Workers: 0") is still in the picture on an empty column. Marked at three homes since Part D — one line confirming, no change.
Acceptance
Part G: four sizes beside the original, questions answered per size, unmarked differences listed separately (zero is the goal).
Part H: figure origin transcribed with source lines; band rule carries both facts; steps 2/3/4 still earned at the three keys; beside native at 1080p.
Part I: before/after table, ten drops each; RESORT decision with its wire evidence; no optimistic drawing anywhere.
Every run against the game preceded by verify_colonies; the game state byte-equal to the .GAM at the end, or the report says which colony differs and why.
Smoke test green; count reported. Nothing pushed.