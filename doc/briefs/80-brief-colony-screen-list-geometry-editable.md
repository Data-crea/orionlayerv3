Brief — Colony screen: list geometry, editable

Read doc/v3_fundament.md before touching anything. Fundament and CLAUDE.md stay in sync. Two reporting stops before code; nothing pushed, Data pushes after git status.

Reference save ab70cc9ad5442335 for live gestures; natives_autosave (tools/fixtures.py) for the screenshots beside the original. Every evidence tool names the save.

The pick round is committed and stays as it is. This round only moves geometry and adds plates; if a pick-round check goes red, that is a finding, not something to adjust.

Decisions set by Data (8 September)
Ten colony rows visible at every resolution, as the original. Row count is a value in the screen's JSON, not a constant in code.
Column widths stay transcribed (Get_Selected_Pop_ literals in core/zoomtables.py) as the source. The columns become editable (below); the transcription is what the editor's value is measured against, never replaced by it.
No spacing. The figure pitch is the sprite step and the squish rule; a pitch scaled by column width is the excluded case from Stage 4 and stays excluded.
Sprites are swapped by step, never scaled (decision 28). The step is derived from the row band, never set by hand.
The list geometry is F5-editable like other screens (14, 37). What is a box and what is derived is fixed in Stop 1, not improvised.
Cell plates as in the original: every cell, including the empty rows, draws a plate. The plate rect is the drop rect is the cell rect — one function (5).
Names left-aligned in the NAME cell, as the original. The second line (climate word and population fraction) is ours: it stays, marked HD EXTENSION at the three homes if it is not already.
Stop 1 — report, no code
A. The arithmetic at ten rows

Per resolution 1920×1080, 2560×1440, 3840×2160, from the current list window (the frame cutout, tools/frame_holes.py output):

row band at ten rows, in px;
the largest FIGURE_STEP whose figure fits the band without clipping, and the step above it with its overflow in px;
figures per column before the squish engages at that step, beside the original's count at native (Calculate_Squish_Step_, coldraw.cpp:12, 30 px pitch);
how far that step fills the transcribed column, as a ratio, beside the original's fill at native.

File and function for every number. Where the fill ratio falls well below the original at some resolution, say so plainly — Data decides between accepting the residue and a taller list window in the frame. Do not propose spacing.

B. The longest colony name

Two sources, both required:

the longest entry in the star-name table (name the file it lives in — source, LBX or estrings);
the maximum a player can type for a star name (the input field's limit; namestar.cpp or wherever it is set).

Each plus a space and the longest orbit numeral the game uses. Width by rendering through Style.render_text at each resolution's name font, not by .size() — Bank Gothic mixes two fonts on blocked glyphs. Report the widest beside the current NAME column width.

Same for the second line: the longest climate word from the estrings list plus the widest population fraction the game can show. This is the lower bound the NAME box may not go below; the editor reports it, it does not silently clamp.

C. Box or derived — the split

Name every geometry value on this screen and put it on one side:

Boxes (in boxes.json, F5-draggable): the five columns NAME, FARMERS, WORKERS, SCIENTISTS, BUILDING. One box per column; the header plate and the cell column read the same rect. Anything else you want to make a box, argue it here.
Derived, never serialized: row band = window ÷ row count; FIGURE_STEP = largest step fitting the band; cell rect = column × band; drop rect = cell rect; plate rect = cell rect; figure origin in the cell. Like text in decision 37 — computed at runtime, absent from the JSON.
The row count: a value in the JSON, editable, not a box.

Then the check that makes editable columns legitimate (36): compare each column box against its transcription in zoomtables and report the deviation in the status; red only when a deviation is unmarked. Say where the marking lives.

D. Fifty plates and decision 34

Cells are a rule, not fifty boxes. Say how a plate skin is drawn from a rect the screen computes without the screen "drawing a border itself" (34) — a skin callable with a rect, a box-less skin call, or something else. If it needs a new decision number, draft it with the next free number and the reason.

E. Editor preview

When Data drags a column, the step, the plates and the figures must follow live in the editor; otherwise she drags blind. Say what the editor shows today and what it needs.

Stop and report.

Stop 2 — implementation and acceptance (after Data's calls)
Ten rows at all three resolutions; a check fails at any other count without an explicit JSON change.
Columns as boxes; header plate and cell column from one rect; a check greps that no second rect source exists for either.
Row band, step, cell, drop and plate rects all derived from the boxes through one function; a check fails if any of them appears in boxes.json after an editor save (save, reload, diff).
Deviation check per column against the transcription: reports in the status, red only when unmarked.
Plates on every cell including empty rows; plate rect == drop rect asserted. The Stop-2 pick-round DEVIATION on drop height (52 % of the band) is closed by this — record that at its three homes.
Names left, second line marked; NAME box lower bound from Stop 1-B reported by the editor, not clamped.
Live PICK/DROP on the reference save after the geometry change — the four gestures from the pick round — so click identity is shown to survive the move, not assumed.
Screenshots beside native, three resolutions, as questions: do the cells sit like the original's; do the figures fill the columns as the original's do at the same count; does the longest name fit.
Smoke test green; report the count. Nothing pushed.
Not this round

Production icons in planet_output (label/value stays, marked DEVIATION); SORT label; - 1t extraction (own brief); Stage 5 cleanup — after this round, since Stage 5 only deletes dead code and this round moves what lives.