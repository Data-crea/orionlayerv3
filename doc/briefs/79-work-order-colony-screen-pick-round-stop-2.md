Work order — Colony screen pick round, Stop 2

Follows brief_colony_pick.md; Stops 0 and 1 are reported and accepted. Read doc/v3_fundament.md before touching anything. Fundament and CLAUDE.md stay in sync. One commit, nothing pushed; report with the diff summary and the check count. Data pushes.

Saves: PICK/DROP evidence on the reference save ab70cc9ad5442335; No Farming and planet_info screenshots on the natives fixture b1f1aa466716d6c0 (the reference save has max_farms == 255 everywhere). Every evidence tool names the save it read.

Decisions set by Data (8 September, after Stop 1)
Both frames fall: the yellow cell frame (draw_pick) and the blue row frame (draw_drop_bands). The original marks nothing.
Drop target is the whole column cell, as _column_boxes already returns. The colony NAME field is the second target and means "put them back" (Send_Cluster_(colony, -1)), transcribed.
F/W/S removed. The first cell moves left by the marker width; click identity is re-established by construction, not by keeping invisible buttons.
No Farming centred in the column, as transcribed.
planet_info: description into the empty left panel, production stays in planet_output. Render both variants for Data — the original's five-line paragraph (E_Strings_(74)) and the current six label/value rows — beside native. Data picks from the picture; do not pick for her. Ship the variant switch only if it is one line; otherwise ship both as screenshots and one in code, marked as provisional.
- 1t is not this round. Fundament 25 answered: extraction from techdata.cpp with a checker, own brief after Stage 5.
Tasks
A — Pick transcription
Cluster pick per Get_Cluster_: clicked icon to the end of its identical group; identity is the four fields at colmove.cpp:102-124. Natives (nibble 9) refused, as the original does. One place holds the identity test; a check greps that no second copy exists.
Held pops leave the row exactly as the original does it — they stop being icons; no count − n arithmetic anywhere. The pitch comes from the existing single home (colonyicons.squish_step / column_pitch) over the shortened row. A check fails if a second pitch computation appears on the pick path.
Cursor figure: Draw_Cluster_ transcribed — +5 x, −10 y from the pointer, +20 per further held pop, drawn last. Whether these three native numbers scale with the sprite step is answered from core/zoomtables.py (decision 26), not chosen. If they scale, the scaled values are a DEVIATION with the three homes; if they do not, the docstring says why. Figure at the sprite step of the resolution: swap, never scale, checked against the files as the row check does.
The original blanks the hardware pointer and draws C_Anims_(15). Decide from source whether HD hides the OS cursor during a pick; either way the figure sits at the transcribed offset from the real pointer position.
Hover during pick (Get_Scanned_Pop_, mode 4) counts the shortened row. A pick does not route through the slot search at all — a check fails if slot_at (or its HD counterpart) is reached while a cluster is held.
B — Drop
Column cell rects as drop targets, all three jobs, empty columns included. The original's field is 30 px of the 31 px row pitch; ours is bar_h — name the difference in the module and in the status, DEVIATION if it changes which row a border click lands in.
NAME field as "put back". Live proof: pick from a column, drop on the name, struct unchanged.
Fundament correction in this commit: the icon row is 31·i + 38 (draw and both hit tests); 31·i + 34 is the field's y. Keep both numbers with their sources — the four pixels are the gap between drop rect and sprite row.
C — F/W/S removal and the frames
Remove the F/W/S markers and both frames. Every marker they carry (HD EXTENSION, DEVIATION) is deleted or retargeted in this same commit; the marker checks must stay green on the same commit, not the next.
_geometry_note in layout.json updated if a box moves.
D — No Farming
Centred in the whole column, box width from the transcription, Squeeze_Print_Paragraph_ semantics: centre at left + width/2, top at top_y + 5.
Font size: the 10 px cap height is a MEASUREMENT off colony_summary_native_split.png, single source, because the height lives in the user's FONTS.LBX. Mark it MEASURED with the picture as its source, the way SHIP_ICON_DIM says DERIVED. The font extractor goes on the horizon in the status; not here.
Drawn only when max_farms == 0, as the original.
E — planet_info
Left panel: description; right panel: production. Words via the estrings word list, word-list rule holds (label carries the prefix, value does not).
Two renderings beside native at 1920×1080, per decision 5 above.
_geometry_note updated.
Acceptance
Live PICK/DROP on the reference save: pick a group, drop into an empty column, drop back into the source row, drop on the NAME field. Struct diff per case, one line each; the tool names the save. Runs through colonymove.move_diff_verdict.
A native pop (nibble 9) cannot be picked — needs a save with natives; if none is available, say so and leave the check skipped by name, not silently.
Checks that fail when: the cursor figure comes from the wrong sprite step; a second pitch computation enters the pick path; the slot search runs while a cluster is held; a marker from the removed F/W/S or frames is left unread.
Screenshots beside native, as questions, three resolutions for the pick, 1080p for No Farming and both planet_info variants: does the figure sit relative to the pointer as the original's; does the shortened row squish as the original's; does No Farming sit where the original puts it; which planet_info variant reads like the original's.
Smoke test green; report the count. Nothing pushed.
Not this round

- 1t extraction (own brief); SORT label; per-row detail button (recorded as deliberate omission at the three homes if not already); font extractor (horizon); Stage 5 cleanup and its pre-commit.