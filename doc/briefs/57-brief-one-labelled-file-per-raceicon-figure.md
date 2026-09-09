Brief: one labelled file per RACEICON figure

Extend tools/raceicon_extract.py; no new tool. Output stays inside screens/colony_summary/assets/raceicon_ref/ (gitignored, decision 38).

Output

raceicon_ref/figures/e<NNN>_<race>_<role>_game.png — every entry, game palette, index 0 as alpha 0, not cropped: the sprite's own canvas from the animation header, so all figures of one race share the same origin and the baseline is where the original puts it.

<race>: race<II>_<name> with the name from enum STOCK_RACE as the per-race directories already use it; entries 169/170 get shared.
<role> from the verified block layout: farmer_state0, farmer, worker_state0, worker, scientist_state0, scientist, military_1 … military_5, spy, portrait; 169 android, 170 native.

Plus raceicon_ref/_labelled_sheet.png: one row per race in block order, 13 columns, 4x nearest-neighbour, entry number and role under each figure, race name at the row start, android/native as a last row.

summary.txt lists every file with entry, role, canvas size, opaque bounding box.

Rules
Nearest-neighbour only for the sheet; the single files are 1x.
Regenerating produces byte-identical output; the existing _contact_sheet.png and the per-race directories are unchanged.
Smoke test green with and without raceicon_ref/.
No push.