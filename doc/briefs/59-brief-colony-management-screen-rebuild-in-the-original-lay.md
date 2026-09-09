Brief: colony management screen — rebuild in the original layout

Read doc/v3_fundament.md first. This brief supersedes the population row design of the current colony_summary screen; it does not supersede any decision in the fundament.

Decision

The colony management screen is rebuilt in the original's layout — column list of colonies with the original population figures, four panels below, sort bar and RETURN at the bottom — at 1080p as the lowest resolution, using the width that gives. The colour-cell population row is retired as the default and kept only as the fallback for a tree without raceicon_ref/ (decision 38).

Logic is kept, presentation is rebuilt. Everything in screens/colony_summary/ that talks to the game — snapshot parsing, colony list building, sort, selection, scroll tracking, pop-move (click-click, clusters, injected clicks, drop targets), field IDs, struct offsets — stays and is reused. Everything that decides where pixels go is new.

Three briefs already in flight are parts of this one and keep their own reporting stops: brief_pop_stacking.md (placement rules), brief_pop_sprites_assets.md (figures, loader, scale table), brief_colony_inset_geometry.md (inset, Part 3 pending).

Stage 0 — inventory, then stop

List every module in screens/colony_summary/ and classify it: LOGIC (kept as is), LOGIC-WITH-GEOMETRY (kept, geometry call replaced by the shared geometry function), PRESENTATION (replaced). For each replaced module name what it currently owns that must survive — e.g. the click offset corrections in the pop-move path, the shortage marker's rule, the sort bar's field mapping. Report; do not delete anything yet.

Stage 1 — layout as data, masks as output

screens/colony_summary/layout_reference.json: the rectangles below, in 1920x1080 reference space. tools/frame_mask.py reads it and writes one mask PNG per supported resolution (1920x1080, 2560x1440, 3840x2160): windows white, frame black, rectangles scaled and rounded to integer pixels per resolution, aspect held as close as integers allow. The per-resolution rectangles it produces are the source for boxes.json's per-resolution lists (decision 1) — they are generated, never typed.

The galaxy inset is 253x200 at reference (506:400 halved, isotropic — decisions from the inset brief). Before it goes into the mask, confirm against the inset document's Part 3 that this box reproduces the original's coverage for the four stock sizes and letterboxes Maximum; if Part 3 says otherwise, stop.

Reference rectangles (x, y, w, h), all in 1920x1080:

json
{
  "bezel": 36,
  "header":        [44,   44, 1832,  48],
  "list":          [44,  100, 1832, 660],
  "list_columns":  {"name": 300, "farmers": 394, "workers": 394,
                    "scientists": 394, "building": 314, "scroll": 36},
  "planet_info":   [44,  776,  320, 220],
  "planet_output": [376, 776,  883, 220],
  "galaxy_inset":  [1271, 786, 253, 200],
  "empire_stats":  [1556, 776, 320, 220],
  "sort_bar":      [44, 1008, 1532,  32],
  "return_button": [1588, 1008, 288, 32]
}

These are Data's design inputs. The list height assumes figures at integer scale 2x at 1080p, 3x at 1440p, 4x at 2160p (56/84/112 px from 28 native) — that table goes into core/zoomtables.py as a marked HD EXTENSION with the reasoning that 2.25 and 4.5 are not integers. If Data changes the 1080p step to 3x, the list grows and the lower band shrinks; the JSON is the only place to change.

Column widths are provisional until doc/pop_stacking.md says how many figures fit a column before the original's overlap starts; the HD column must fit at least as many unsquished figures as the original's 128 px at the chosen figure scale.

Stage 2 — frame

Data supplies the frame artwork (AI-generated from the 1080p mask, metal only, windows flat black). tools/frame_cut.py takes the artwork and, per resolution, scales it to the variant size and cuts the windows from the mask into the alpha channel — never from the artwork's own black. tools/frame_holes.py --write then derives the cutout boxes, and the smoke test asserts holes == mask == boxes.json for every resolution (decision 3).

Stage 3 — rows

Population columns draw the original figures through the loader chain pop_icons/ → raceicon_ref/ → RACEICON.LBX (assets brief, with the third stage added). Placement, draw order and overlap per doc/pop_stacking.md. One geometry function serves render and hit-test (decision 5); the pop-move path calls it, so the click offset corrections from the old rows must be re-derived against the new geometry — not carried over as constants. Name, building and the shortage marker are transcriptions of the original's row, placed relative to the row box. cells remains the fallback when the loader returns None, and the smoke test renders both.

Stage 4 — lower panels, inset, sort bar

Planet info, planet output icons, empire stats: content and order per the original (colsum.cpp), positions relative to their boxes in layout.json. Galaxy inset per the inset document: whole galaxy, isotropic, 3x3 dot table DERIVED from gstar.lbx, only the scanned star animated, star name label as the original draws it. Sort bar and RETURN keep their existing field mapping.

Reporting stops

After Stage 0. After Stage 1 (masks rendered to PNG, laid beside the original screenshot at 1080p — question: does the structure read as the original's?). After Stage 3 (rows beside a native screenshot with Wolf II and Blucher III — question: same figures, same order, same overlap onset?). Stages 2 and 4 report on completion.

Constraints
No push. Smoke test before every report.
Joes' tree untouched; anything needed there goes to doc/orion2re_open_fixes.md.
Every number in a renderer comes from layout.json, boxes.json or core/zoomtables.py; a literal in a draw call is a defect.
Files under ~300 lines; exceptions listed in the status document.
The old presentation modules are deleted in the same commit that makes the new ones default — no parallel copies.
Acceptance

Screen renders at all three resolutions from one JSON; holes, masks and boxes agree; figures are the originals at integer scale; the inset shows the whole galaxy with the scanned star marked; pop-move works in the new geometry (injected clicks land — verified live, not inferred); cells fallback renders without raceicon_ref/.