Brief: extract the per-race population sprites from RACEICON.LBX

Read doc/v3_fundament.md first. Decision 38 governs everything here: extracted game data is written locally, never committed, and a missing file is a state to explain, not an error.

Goal

A tool that reads the player's RACEICON.LBX and writes the population figures — farmer, worker, scientist, native, android — as PNG, organised per race, so the HD colony screen has a reference for its own icons and a second source for the colour/tool mapping that today rests on one framebuffer of one race.

Deliverable: tools/raceicon_extract.py, output under screens/colony_summary/assets/raceicon_ref/, that directory in .gitignore with the same comment block nebula_ref/ carries.

Stage 1 — dump, no interpretation

Extract every entry and every frame of RACEICON.LBX as raceicon_ref/raw/entry_<NNN>/frame_<F>.png, plus one contact sheet raceicon_ref/_contact_sheet.png with the entry number printed under each sprite. No race/job formula in this stage. The sheet is what the formula gets checked against in stage 2.

Decoder: the one already in tools/nebula_extract.py (LBX container per vfs_lbx.cpp, s_animation_header per orion2.h, bitmap and RLE frames per draw.cpp, embedded palette per animate.cpp). This is the third user after help_extract.py and nebula_extract.py, so pull container parser and frame decoder into core/lbx.py and point all three tools at it. Condition on the refactor: after it, nebula_extract.py must regenerate nebula_ref/ byte-for-byte. If it does not, the refactor is not done.

Reporting stop 1 (before writing PNGs)

Report, with file:line from the working tree:

Does RACEICON.LBX carry an embedded palette (FLAG_HAS_PALETTE) on its entries, all of them or some? If not: where does the colony screen load the palette these sprites are drawn with? Name the function; do not guess a file.
If no palette is available in this stage: write grayscale-by-index (as nebula_extract.py does) and say so in summary.txt. Colour comes in a later stage; do not substitute a palette from another LBX or from a screenshot.
Frame semantics: People_Anim_ loads animations. Which frame is the resting figure? Are the squished variants (Calculate_Squish_Step_) separate frames, separate entries, or drawn by clipping at runtime? Answer from the drawing code, not from the frame count.
Stage 2 — per race

Only after stage 1's sheet exists.

The entry mapping is claimed in layout.json (_invention note): COLONY::People_Anim_ (colony_main.cpp:444), entry race_idx * 13 + job_type * 2 (+1 for pop_state 2), natives 0xAA, androids 0xA9. That is a citation, not a verified value. Re-read the function in the working tree, state the formula as it actually is, then check it against the stage 1 sheet: the entries it predicts for the reference save's race (player 0, Elerian) must be the bronze farmer, teal worker and silver scientist seen on 4 September 2026. Both sources agree → the formula goes into the tool. They disagree → stop and report which one is wrong.

Output layout once verified:

raceicon_ref/
  race_<idx>_<name>/farmer.png  worker.png  scientist.png
                    farmer_<state>.png ...   (whatever pop_state 2 is)
  shared/native.png  android.png
  summary.txt        entry -> file, dimensions, palette source, flags

Race names: from wherever orion2re's own race table lives — cite it. If the names are in an LBX rather than the source, use the index only and say so.

Constraints
Joes' tree is not modified. Anything that would need a C++ change goes to doc/orion2re_open_fixes.md.
Every line number in this brief must be re-anchored against the patched working tree before it is cited in code or docs.
python tools/smoke_test.py green (SDL_VIDEODRIVER=dummy), including with raceicon_ref/ absent — the tree must not need it.
No push. Data reads the diff.
Acceptance
Stage 1 sheet exists; nebula_ref/ unchanged after the refactor (diff shows zero bytes changed).
Reporting stop 1 answered with citations.
Stage 2: per-race directory for the reference save's race, placed beside a native screenshot of the colony screen with visible pops. Question to answer, not a finding to state: do the three figures match?
.gitignore covers raceicon_ref/; git status clean of PNGs.