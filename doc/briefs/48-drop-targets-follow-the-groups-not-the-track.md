Drop targets follow the groups, not the track

Observed at 1920x1080, Draconis V (9/14, four farmers, four workers, one scientist), one pop held: all nine cells lie inside the first of the three equal bands from drop_band() (colonylist.py); the other two bands are empty track to the right. A click on a worker cell therefore names "farm". Looks right, clicks wrong — decision 5.

The docstring's reason (an empty job still needs a target) stands. The geometry that answers it does not.

Target model

The drop target for job j is the horizontal extent of group j's cells in this row. A group with no pops gets a placeholder of one cell width at the position it would hold in ECON order — between its neighbours, not at the end, so it does not move when the first pop lands. Free slots after the last group are not a target.

A click on a cell of the held pop's OWN group is a no-op, as in the original. It does not change the selection; right-click stays the only abort.

Questions to answer from the code before writing it
Do the transient zone frames (the blue outlines while a pick is held) and drop_band() share one geometry function today? If not, they must after this change — the frame and the hit-test come from the same rect (decision 5). Name the function.
Where does the placeholder for an empty group get its slot — is row_regions() the place, so the placeholder is a region like any other and the resting row can later carry a permanent blocker cell in the same slot without a second layout path?
Does anything else read the three-equal-bands assumption — layout.json under move, the smoke check that marks the extension, tooltip placement?

Report the answers, then the file list. Stop before writing code.

Acceptance
The Draconis V case: a click on a worker cell while a farmer is held names industry; a click on the scientist cell names research; a click on the free slots names nothing.
A colony with zero workers shows a one-cell industry target between farmers and scientists; a click there sends the move.
Own-group click sends nothing (wire log).
Frame and hit-test are asserted equal by a smoke check, not by looking.
PNG of the held state beside the current screenshot, same colony.
Marks updated: docstring, layout.json, status document, smoke check — the extension is still an extension, only its shape changed.
Smoke green under SDL_VIDEODRIVER=dummy. Diff shown; Data pushes.