Work order — Colony screen: the remaining items, in order

Read doc/v3_fundament.md before touching anything. Fundament and CLAUDE.md stay in sync. Each part is its own commit or commits; report after each part with diff summary and check count; Data pushes. Reporting stops are marked; do not build past one.

Saves: reference save ab70cc9ad5442335 loaded as slot 8 for anything that touches the game; fixtures.verify_colonies before every run; stop at the first non-returning round trip. Data does not move population while a measuring run is open. SAVE10.GAM is the game's autosave slot and is overwritten at every turn end — Part 0 secures it.

Accepted and closed since the last order: sort-bar box measured on the drawn string, typography DEVIATION at three homes, Parts A–I.

Part 0 — secure the autosave fixture (first, ten minutes)

Confirm a copy of SAVE10.GAM lies under ~/orionlayer-fixtures/ with the sha256 the README carries (2610f39c…). If only the game's own file exists, copy it now and record it. fixtures.natives_autosave points at the fixture copy, never at the game folder — the game folder is what the game overwrites. Then the No Farming line of Part G: Data loads the autosave in the game, one snapshot beside the original on natives_autosave, the question answered, the gap in the status closed.

Part 1 — name hover (transcription)

In the original the colony name under the pointer is bright, the others dimmed. Source first: which function colours the name, and is the driver the scanned colony (_scanned, the same state that fills the description panel) or a separate hover? Colour as palette index into colors.json, with the line. Transcribe: a colour on the name, no rectangle, no frame. If the driver is the scanned colony, the HD hover and the description panel must follow the same state — one source, a check that they cannot disagree. Beside native at 1080p.

Part 2 — the scroll slider (transcription)

col_scroll is plated per band today; the original has one continuous track between the arrows with a blue slider (Fill_/Line_ at colsum.cpp:759-765 — the drawing decision 46 already reads _first from). Transcribe: one track instead of ten cells, slider position from _first, extent from the visible/total ratio the original uses (name the arithmetic and its line), colours from the palette. The plate check becomes row_count × 5 plus one track. The marker "NOT DRAWN — the original's SLIDER" (colonylist:40) falls in the same commit; the per-row detail button stays a recorded omission at three homes. Beside native at 1080p and 1440p — the track is where a band-height change would show first.

Part 3 — editor: resize on every box (stop before code)

Form as proposed: class derived from the screen's frame_holes rule via RULE_NAMES per screen plus a check that the rule never yields a name outside the list; never from a field in boxes.json.

FREE (both axes): eight handles, minimum size 20, save-reload-diff proves only ref_rect is written.
BOUND (the six columns): left/right only; top, bottom and corners refuse with the reason in the info bar; a dragged edge moves the neighbour's boundary, because width is the distance to the next column.
LOCKED (cutouts): all handles off, info bar names frame_holes.py. Decision 3.
DERIVED follows every frame (fonts, sort widths, plates, step, band). The galaxy inset keeps 1.2651 from movebox.cpp:20-21 on any edge — the rule goes into the editor now even though the inset is locked, so the first person to unlock it cannot break it.

Stop after the classification is in and one FREE box resizes, with the screen table (free/bound/locked counts) re-run against the code, not the earlier hand count. Then build the rest.

Open at Data: the colony screen has no FREE box — fourteen, all cutout or column. Whether the editor should edit holes (drag a cutout → write layout_reference.json → rebuild the plate through frame_build.py) is Data's decision, not in this part. If she says yes, it is Part 3b with its own stop: the plate is a derived file (decision 49) and the editor would be its first non-CLI writer.

Part 4 — Stage 5 cleanup, with its pre-commit

Pre-commit first, own commit: word lists onto estrings (the 23/26 identical ones; gravities via the %sravity split), the AST check for colonyrows without pygame, the clip check's behaviour on an absent figure set plus one red run with ink in the reserve rows.

Then Stage 5: delete the old modules; every marker they carry is retargeted in the same commit (the marker checks stay green on that commit); frame_preview with the old artwork removed (fundament 49 holds the dated sentence); decision 46/48 citations re-checked; the cell renderer stays as fallback for an absent figure set and the status says so; info_style removed — the paragraph is the only user. Grep that nothing deleted is imported anywhere.

Part 5 — - 1t (extraction, own brief, after Stage 5)

Pattern of decision 36: TECHDATA::_buildings[] (techdata.cpp:25, cost at techdata.h:44) transcribed into a Python table with the line numbers, plus tools/buildcost_check.py that reads Joes' source and fails on drift. Colony_N_Turns_To_Produce_ transcribed over the wire fields already verified (production_spent 293, production[IND] 231, maintenance[IND] 239, bought_outright 300); terraforming via s_planet_data.n_terraforms, ships via s_ship.d.cost / ship_designs[].cost; Trade Goods and Housing default to 1 as the original does. String E_Strings_(39) "%s - %dt". The producing sort then sorts by cost and the "unavailable" grey falls with its three markers. Stop after the table and checker, before the turn arithmetic: the table is the hard-to-reverse half.

Part 6 — drop speed, the HD share (measurement first)

The corrected table puts the HD share at the start: 57 ms local pick

84 ms to the first send state, plus ESTABLISH 162 ms over two messages. Name what each of the three waits for and whether it is guarding something real. Report, do not build. Option (b) stays rejected. If a wait guards nothing, that is a candidate for the next round with before/after on ten drops.
Recorded, not this round

Background cropping (Data, later). Font extractor for FONTS.LBX (owed twice: No Farming size, name cap). Production icons in the right panel (DEVIATION stands). SORT label. Frame master ≥ 3840. Android save for nibble 9. 68 double-scaling boxes on four screens (known-wrong in the status).

Order and stops

0 → 1 → 2 → 3 (stop after classification) → 4 (pre-commit, then Stage 5) → 5 (stop after table) → 6 (report only). Parts 1, 2 and the No Farming line need the game; do them while slot 8 or the autosave is loaded and say which. Push after each part is reported and Data has read the diff.