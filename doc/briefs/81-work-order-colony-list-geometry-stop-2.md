Work order — Colony list geometry, Stop 2

Follows brief_colony_list_geometry.md; Stop 1 is reported and accepted. Read doc/v3_fundament.md before touching anything. Fundament and CLAUDE.md stay in sync. One commit for the frame change, one for the geometry; nothing pushed. Report with diff summary and check count. Data pushes after git status.

Saves: reference save ab70cc9ad5442335 for live gestures; natives_autosave for screenshots beside the original. Every evidence tool names the save.

Decisions set by Data (8 September, after Stop 1)
1440p gets its step: list_area grows by the reference px needed for a band that holds step 3, taken from the lower band's height, not from the list_band rail. Two questions are answered before the plate is rebuilt (Part A).
Decision 51 filed as drafted, next free number checked. Plates are marked as a deviation in kind — the original paints them into the COLSUM.LBX background bitmap, HD draws them — at the three homes.
Six column boxes including col_scroll. The cross-resolution check asserts the rule, not the state: column boxes are resolution-independent because they live in reference space.
ScreenBase.editor_note(box) now, and the hasattr race_grid special case in overlay.draw_info retires in the same change.
The 79 % residue at 1080p and 2160p is accepted: column factor 2.53 against steps 2 and 4, no spacing. It goes into the status as known and reasoned, with the numbers, not as an open item.
Part A — the lower band, before touching the plate

Two questions, report before frame_build runs:

At the reduced lower-band height, do the six sidebar readouts, the five production rows and the galaxy inset's letterbox still fit at all three resolutions without any font or box shrinking? Show it by rendering, not by arithmetic on box heights.
Band 84 against figure 84 is zero spare. Does the figure need clearance inside the plate's 1-px line, and if so, how many reference px does list_area need beyond 21? The number must hold the same rule at 1080p and 2160p (their spare shrinks too).

Then: layout_reference.json list height, frame_holes.py --write (report how many non-cutout boxes it kept), frame_build.py, the derived plates regenerated (decision 49), the A3 rail numbers in the status unchanged and re-asserted. Own commit.

Part B — geometry
Six column boxes in boxes.json; colonytrack.columns() reads them instead of the table colonyheader.install_columns bakes at init. Header plate, cell column, scroll slot: one rect source each.
Derived, never serialized: band (window ÷ list.row_count, last band takes the remainder), FIGURE_STEP (largest step whose 28·step fits the band), cell = column × band, drop = cell, plate = cell, figure origin, squish pitch, name-block rect. The hand-written FIGURE_STEP table goes; if a check depends on it, the check derives too.
list.row_count = 10 in the JSON. The nine dying values (row_height, pad_x, pad_y, name_width, name_gap, bar_height, tail_width, building_width, growth_gap) removed with a grep that none is read anywhere.
Transcription into core/zoomtables.py as the Get_Selected_Pop_ ratio 135 : 142 : 134 with line numbers; the deviation check reports every column into the status, red only where unmarked. col_name and col_building carry their existing reasons.
Cross-resolution check on the six boxes, worded as the rule.
Editor: a column dragged vertically is ignored and the info bar says so.
Part C — plates and decision 51
StyleRenderer.draw_plate(surface, rect, scale, color) extracted; draw_thin_border and colonyheader.render both call it — the duplicated max(6, int(10 * scale)) exists once afterwards, and a check greps for it.
Plates on every cell of every band including empty rows. Plate rect == drop rect asserted. The pick-round drop-height DEVIATION (52 % of band) is closed and its three homes say so.
Decision 51 in the fundament with the next free number; the uniqueness check stays green.
Part D — names and second line
Names left-aligned in the NAME cell. Second line marked HD EXTENSION at the three homes if not already.
The editor reports the NAME lower bound (widest typable WWWWWWW IV and the second line's Radiated 42/100), never clamps. The source of the seven-W cap (Max_Pixel_Width_Star_Name_Can_Be_, namestar.cpp) is written next to the number, with the note that the cap is measured in FONTS.LBX style 3, which this project cannot read — same gap as the No Farming size.
Part E — editor_note
ScreenBase.editor_note(box) -> str | None, default None; colony screen returns the line from the Stop-1 report for a selected column box, and the NAME bounds for col_name.
overlay.draw_info calls the hook; the race_grid hasattr case is gone and Select Race implements the hook if it needs the line.
Acceptance
Ten rows at all three resolutions, a check fails at any other count without a JSON change.
Derived steps 2 / 3 / 4 at 1080p / 1440p / 2160p — earned from the band, and a check that recomputes them from the boxes and the figure files.
Save-reload-diff: an editor save writes no derived value into boxes.json.
Deviation check and cross-resolution check green, both worded as rules.
One home for the plate arithmetic; one rect source per column.
Live PICK/DROP on the reference save after the change — the four gestures of the pick round — so click identity survives the move.
Screenshots beside native, three resolutions, as questions: do the cells sit like the original's; do the figures fill the columns as the original's at the same count; does Commoriom IV fit; does the lower band still read at its new height.
Status: the 79 % residue recorded with its arithmetic; the deviation table per column; the plates as deviation in kind; the font extractor on the horizon (now owed twice).
Smoke test green; report the count. Nothing pushed.
Not this round

Production icons in planet_output; SORT label; - 1t extraction; Stage 5 cleanup — next, and it now also removes info_style if the paragraph stays the only user.