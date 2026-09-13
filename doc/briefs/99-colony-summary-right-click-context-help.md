Colony Summary: right-click context help, transcribed from ERICHELP::_colony_summary_screen_help_list, on the existing popup.

Brief 98. Chat session 13 September 2026. Decision 38 governs this entirely; nothing here is new architecture. Two stops. Line numbers are yours. Highest decision is 58 as of commit ec325dc; take the next free number only if a real decision falls out — a transcription does not need one.

The screen is the Colony Summary (colsum.cpp, the list screen), not MOO2's colony build screen. The handover lists this as open item 4: 22 entries in the ERICHELP table.

Stop 1 — transcribe and report, no rendering code
Transcribe the table into screens/colony_summary/help.json in the same shape as the three existing files (main menu, new game, main screen): every entry with its help id and the original's 640x480 rectangle as provenance, in the ORIGINAL ORDER — the walk stops at the first hit, so the screen-wide fallback stays last, where the original keeps it.
Report how the three existing help.json files bind an original rectangle to HD geometry — by box name, by scaled rect, or both. Use that mechanism; do not invent a fourth.
Table of all 22 entries: help id, original rect, what it covers in the original (from the C++ context, not from the id's spelling — a field dump is not documentation), and the HD box it maps to. Three classes need naming:
entries whose original region has moved in HD (the whole bottom row after brief 97: planet_info left, colony_panel middle, empire_stats inside it) — these bind by box name, never by scaled rect, or the help lands on the wrong panel;
entries with no HD counterpart (something the HD screen does not draw) — list them, they stay in the file with a note, not deleted;
HD boxes with no original entry (planet_surface, the name heading, the row fills) — they get NO help text; inventing help copy is the same as inventing a value. If the screen-wide fallback covers them in the original's walk, say so. The list rows: is there one region for the list or one per row or column? Report what the table actually holds.
What does a right click do on this screen today in HD? Name the handler. The original swallows a right click over a help region so it does not act as Cancel (Check_Help_List_); report whether the HD screen's right-click path can do the same without a second copy of the walk — the popup module already exists for three screens, so the walk should be shared code, and the third screen was the signal to extract if it is not.
Confirm the text side needs nothing new: tools/help_extract.py already produces the file the loader reads, the absent-file state is already handled, and the ids in the new table exist in the extracted set — report any id that does not.

Stop and report. Data decides nothing here unless class two or three turns up something that needs a call.

Stop 2 — wire it
Right click walks the table in order, draws the entry in the existing popup (auto-sizing, HD EXTENSION, already marked), swallows the click. Outside every region: whatever the original does with a right click on this screen — report that too, from the source, and match it.
Smoke test: every entry in help.json names a box that exists (or carries the no-counterpart note); order matches the C++ table (assert against the transcribed provenance, not a hand-kept list); the fallback is last; a long entry stays scrollable at four resolutions, as the existing check does for the other screens.
Screenshots: one right-click popup at 1080p beside the original's own help box on the native screen, for one entry Data can find quickly (the list header is a good candidate). Name the one check that would break a fresh clone — first suspect: a clone without the user's HELP.LBX extraction must show the "not extracted yet" state and pass the suite, as the other three screens do. Push is Data's.
