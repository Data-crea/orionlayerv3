Task 4 — the row gets its three groups, a mark and a popup

Read doc/v3_fundament.md first. The three design questions that stood open in v3_projektstatus.md are decided. Build them in this order — each one narrows the next. Reporting stop before code, and one at the end.

A mockup of the intended structure is at /home/data/Bilder/Bildschirmfotos/Mockup.png. It shows the run F [cells] W [cells] S [cells], flush, grey markers with a light border, growth slots after a gap at the end.

It is a reference for structure only — not for sizes, cell counts or colour values. It came out of an image generator: the cell counts are wrong in most rows and the geometry is invented. Render against the real snapshot and judge there. The file stays where it is and is not carried into the tree; what has to survive is the reason for the markers, and that goes into the module as the HD EXTENSION marking below, not into a picture.

1. Job markers — three per row, always

Decision. Every row carries three marker cells, one per job, in ECON order. Not separate from the groups: each marker introduces its group, and marker plus that group's cells form one unbroken run.

F [food cells] W [worker cells] S [scientist cells]   · · · ·

Always present, whether or not the job holds pops. A colony with all pops farming shows F [14 cells] W S — and that is the whole point. Today such a row shows a run of squares and then nothing, so nothing tells the player the other two jobs exist. The runtime placeholder in drop_targets only appears once a pop is held, which is one click too late.

Appearance: grey fill, white/light border, the letter centred. Grey specifically because it must not collide with the three job colours — an amber marker read as a fourth job class in the first mockup. F/W/S are placeholders until icons exist, as agreed.

Flush, no gaps. No empty space anywhere inside the run. A marker whose group is empty is immediately followed by the next marker. Short colonies produce short rows; the length of a row has to keep meaning something.

What this collapses. No group is ever empty again, so the empty-group special case in drop_targets goes away — the marker is the permanent placeholder, now visible. One layout path. Take the special case out; do not leave it as a fallback nothing reaches.

The drop target for a job is marker plus cells — one contiguous rect. Two box types that look alike and behave differently is the trap decision 5 is about.

Growth slots move to the end. The dashed boxes belong to the colony, not to any job, so they follow all three groups after a clear, fixed gap. The gap is a layout value, not a side effect. This is a change from today's row and needs to be visible in the diff.

Open question the mockup cannot answer: whether one cell width is enough to hit a marker, or whether it needs two. Decide at the real render, at 1920x1080 and 4K, and say which you chose and why.

Cost, for the record: three cells of track width per row. Irrelevant at 42 slots, relevant when Task 6 shortens the track to the empire maximum. Note it in the status document beside the Task 6 entry so the trade is visible when it is made.

This is an HD EXTENSION and gets its marking: the original has column headings — FARMERS, WORKERS, SCIENTISTS — and no markers. A row without columns cannot carry a heading; that is the reason, and it belongs in the module, in the status document, and in a check that fails if the marking disappears.

2. The identity mark — a letter in the cell

Decision. A letter drawn in the cell; the fill colour is not touched. Native gets N.

What decided it: sprite 0xAA is one sprite for every native regardless of profession — in the original the profession lives in the column. The HD row has one track and no columns, so the cell carries both. Fill carries profession, the mark carries identity, and the mark may not disturb the fill.

The player's own pops carry no mark; the unmarked cell is the common case. Android and conquered need letters too — propose them, and keep the marking they carry: nibble 0 and 9 confirmed against fixture_natives_3502.5.GAM, nibble 8 and the conquered bit unverified with no witness in either fixture.

The case that can still overturn this: Zhadoom III, 14 pops, the narrowest cells in either fixture, at both resolutions, beside the native half from the same snapshot. If the letter is not legible there, say so plainly rather than shipping it.

3. Context — a popup below the row on hover

Decision. Hovering a group shows a popup below the row. It overlays; it never reflows the list — decision 46, the list is the click frame.

Two cases that need an answer, not a guess:

The last visible row — the popup flips above the row or runs off the panel. Pick one, render it.
While a pick is held — the drop targets are on screen. If the popup covers them, the rule is more likely "no popup while a cluster is held" than a different position.

Wording in layout.json, not in the renderer (decision 15). Text measured by rendering, not by one font's .size() (decision 30).

4. Minimap background

The galaxy minimap in the bottom panel: make the background black. Small, unrelated to the rest — do it in the same run, in its own commit if that keeps the diff readable.

Check first whether the panel currently has no fill of its own and is showing the cockpit texture through. If so, the fix is a fill on the box, not a change to the star renderer. The help popup taught this one: the background you see is not always the background that is set.

Stop before code

Report: the letters proposed for android and conquered; what the popup does in the last row and while a pick is held; whether the minimap needs a fill or a renderer change; the file list; which checks will be added.

Acceptance
Every row shows three markers at rest, in ECON order, whatever the population, flush with their groups, no gaps inside the run.
Growth slots after all three groups, separated by the fixed gap.
The empty-group placeholder path is gone, not bypassed — one layout path, with a check that would fail if a second appeared.
A marker is a drop target: a click on it sends the move. Frame and hit-test from one function, asserted by rendering and reading back the ink, as in the drop-target rebuild.
N appears on exactly the three native cells of Urna I and nowhere else in either fixture.
Zhadoom III and Urna I rendered at both resolutions beside the native half from one snapshot.
The popup does not cover a drop target, or does not appear while one is held — whichever was decided, asserted by a check.
Markings for all three extensions: module, layout.json, status document, check.
Smoke green under SDL_VIDEODRIVER=dummy. Full diff shown; Data pushes.
Not in this task

Warnings, filters, transit display — the rest of Phase 4. Track width and row count (Task 6). H1. Each of them draws into this row, so the row's shape settles first.