Brief — estrings, then Stage 3 on the game's own figures

Read doc/v3_fundament.md before touching anything. This brief sets direction and acceptance criteria; every number, line and offset is yours to establish and report. Tree state: d1e38f0 pushed, clean, 98 checks.

Decision from Data, 7 September, to be filed as the next free number under Data and resources: OrionLayer ships the game's own figure sprites, extracted from the user's installation at the sprite step (FIGURE_STEP, integer, swapped not scaled — decision 28). HD figure artwork is not a project deliverable; brief_pop_sprites_assets.md is retired. A user who wants other figures makes a mod, and that path has to be simple: one PNG, one documented name, one documented folder, restart, done. The original is the fallback per file (resources.resolve, already per-file; decision 17 stays about skins).

Three parts. Part 1 is its own commit. Part 2 is a report — Stage 3 Stop 1 finished. Part 3 runs only after Data's go on Part 2. Stop once after Part 2.

Part 1 — the estrings extractor (commit)

Two consumers: the BUILDING column, which is empty because every colony in the reference save produces Trade Goods — an option string resolved through ESTRINGS::E_Strings_, not a building — and the word lists currently read off the screen into layout.json, which the horizon already names as the wrong long-term source.

Same pattern as help_extract.py and techname_extract.py (decision 38): bytes untouched, format version, never committed, decode at load time, setup.py step, absence a state the loader explains. The walk is Load_E_Strings_ (estrings.cpp:11-37) — strlen+1 without skipping NUL runs, as you found; transcribe that, do not reuse the TECHNAME walk.

Acceptance:

BUILDING shows "Trade Goods" on the reference save, every visible row matching the native crop. The turn suffix stays open as reported; the column shows the name.
The producing sort key uses the extracted string for options and the building name for buildings, one function.
A smoke check pins three option strings and the count, reports "absent, run this" when the file is missing, and — since two extractors now exist — asserts that the TECHNAME and ESTRINGS loaders never read each other's file.
Word lists: report which layout.json lists could come from estrings (climate, minerals, size, gravity, the sort labels) with the entry indices; do not switch them in this commit. That is a separate change with its own before/after, because the word-list rule ("the table holds Rich, not Mineral Rich") has to be checked against what the LBX actually stores.
Part 2 — Stage 3 Stop 1, finished (report, no code)

Your Part B answers stand: per-file resolution proven, Colony_Pop_Anim_ for identity, conquered → static portrait, Native 0xAA / Android 0xA9, no tinting. Finish the stop on that basis.

The base set. raceicon_extract.py produces the originals. State what it produces per figure (race × profession × state, plus conquered, Native, Android), file names, and how the 2×/3×/4× steps are made — at extraction, at setup, or at load into a cache. The step is an integer nearest-neighbour enlargement of a 28×28 sprite; say where that lives and that no filtered scale is used (a filtered 28×28 is the "invention the original cannot do" test). Confirm the extractor is in setup.py and that the loader explains an absent set.

The mod path — the simple one. Draft, for Data to strike or add:

the folder: mods/<name>/screens/colony_summary/assets/figures/ or wherever resources.resolve already looks — name it, and say whether one folder serves all resolutions;
the file: one PNG per figure at the master size a modder draws (state the size and why — 4× of native is the obvious candidate; say if a different master size is better and what it costs), from which the steps are built at load into the derived cache, so the modder runs nothing;
the name: the same names the extractor writes, so a modder copies the extracted folder, replaces the files they want, and deletes the rest — one convention, no second naming scheme;
the check: a master with the wrong size is not drawn, the original is, and the log names file and reason once, not per frame;
the doc: doc/modding_figures.md, and its file list is generated from the same table the loader reads — a smoke check asserts the doc and the loader agree, or the doc is a copy that will drift.

The loader chain, one paragraph: mod master → derived steps (cache, gitignored, keyed by file hash so a replaced master regenerates) → or base step → draw. One function for the figure rect, read by drawing and slot_click_x (decision 5). The three homes for any marking.

The squish as overlap. Cells shrank; figures overlap as in the original. State how the draw order handles overlap (the original draws left to right, later over earlier — verify in coldraw.cpp or colony_main.cpp, file and line) and that the click still hits by index, not by pixel.

Acceptance criteria for Part 3, written out:

Figures replace cells on the reference save at three resolutions; Blucher II's farmers and Blucher III's scientists beside the native at the same scale.
A test mod in the smoke test with one synthetic master: that figure appears, every other figure is base — asserted by pixel sampling, not by looking.
The same master at a wrong size: not drawn, base drawn, one log line with file and reason — asserted.
Conquered, Native and Android each drawn from a fixture (Native also live on Urna I).
PICK and DROP per column re-proven with move_diff_verdict.
doc/modding_figures.md exists and agrees with the loader table.
Nothing deleted from the old modules; markers stay for Stage 5.

Stop here. Report Part 1's commit and Part 2's answers. Data pushes Part 1 and gives the go for Part 3.

Part 3 — Stage 3 Stop 2 (after the go)

Implement against the seven criteria as confirmed. One commit. Evidence under ~/Bilder/rahmen/ with hash in the name, manifest updated. Fundament: the new decision as stated at the top, and the Sizing and artwork line for the integer step on extracted sprites. Status document: Stage 3 entry, HD-figure premise retired, the Stage 5 list of what now dies. Smoke count. Reference save preserved; hashes reported. No push.

Standing rules
Two independent sources before any production value.
No number in a doc that a check does not read.
A derived file needs a regeneration path and a check that says "absent, run this".
No orion2re changes expected; conditional permission applies, reported before, never silently.
Projektinhalt
OrionLayerv3
Von dir erstellt
v3_fundament.md

36,9 kB

MD

Inhalt
uebergabe_2026-09-07_colony_screen.md

90 Zeilen

MD

Stop 2 — implementation complete, nothing pushed Diff summary — 14 files, +715 / −181 file: core/zoomtables.py what changed: MAP_MAX_X_PER_SCALE = 50.6 deleted. maximum_galaxy_display_scale(x, y) transcribes mapgen.cpp:64-71; maximum_galaxy_map_max_y(x) inverts the grid for an x-only caller; max_m

PASTED

1. The x-only path had no caller — default and helper removed All seven callers pass both extents. The only single-argument calls in the tree were two assertions I had written in the smoke test to exercise the fallback. A fallback justified by a test written for it is a fallback with no caller, so

PASTED

Where the built plate lives today, and who reads it tools/frame_build.py writes screens/colony_summary/assets/frames/frame_<W>x<H>.png — three files, 1920×1080 / 2560×1440 / 3840×2160, 3.6 MB total, from _resolutions in layout_reference.json. The directory is already gitignored (.gitignore:81). No

PASTED

Stop 2 — Stage B and C complete, nothing pushed Diff summary — 22 files changed, 1 new, +1273 / −200 New: screens/colony_summary/colonyframe.py — the switch, its own module. ┌──────────────────────────────┬──────────────────────────────────────────────────┐ │ file │

PASTED

manifest.md

213 Zeilen

MD

Stop 1 — inventory and three verifications One correction to the brief's tree state before anything: Stage B/C is in the working tree, not in a commit. git log HEAD is still d5b28be; the 23 modified files plus colonyframe.py are uncommitted. Nothing depends on it, but "committed" is not true yet.

PASTED

Committed, and the two questions answered — one needs your pick before code Commits Two, not one. The galaxy-scale change was never committed either — git log HEAD was still d5b28be, so "Stage B/C committed" was not the tree state. Both Stop 2 reports described their own commit, so I split them.

PASTED

Stop 2 — the geometry swap Commits pushed by you, then this on top d2bcd24 and d0abd07 are in; this work sits uncommitted on top of them. Diff: 10 files, 2 new, +648 / −415. ┌──────────────────────────┬──────────────────────────────────────────────────────┐ │ file │

PASTED

Stop 3 — the rows are in the columns, and the live proof is not clean Plate height — the arithmetic, then the decision colonytrack.row_bands lays rows of row_height 58 from pad_y 14 inside the box (window + BLEED 2 each side): ┌────────┬─────────────┬─────┬───────────┬───────────────┬────────────

PASTED

manifest.md

251 Zeilen

MD

manifest.md

283 Zeilen

MD

Part A — Stage 4 closed, ac5b86f A1 — the pitch was the ratio; it is the sprite step now colonyicons.column_pitch was multiplied by room / native_column_width — about 2.7 at 1080p for farmers (342 ref px over 125 native). That is the excluded case: it spends the reservation on spacing, and Stage 3

PASTED

Part B — the column-2 diagnosis Nothing changed in either tool. Working tree clean at ac5b86f; the manifest wording is corrected and waiting for the next commit. 1. Which bytes changed, by field Colony records diffed through core/structs/colony.py, field by field, across one injected move. Scient

PASTED

Background command "Start the game for the live proof" failed with exit code 1 Three commits, tree clean, 98 green. A — the column-2 rule · ea1f1e3 (+425/−23, 8 files) The rule lives in colonymove.move_diff_verdict, read by both tools (a check greps each for the call, so a second copy fails the

PASTED