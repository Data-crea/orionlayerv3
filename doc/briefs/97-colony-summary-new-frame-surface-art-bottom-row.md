Colony Summary: the new frame with three bottom windows, the planet surface art cut from Data's sheet, and the bottom row rearranged as in 97-mockup.png.

Brief 97. Chat session 13 September 2026. Three stops; Stop 1 and Stop 2 report and wait. Line numbers are yours; nothing below asserts what a file contains, only where to look. Highest decision is 57 as of commit 3fe55b6; take the next free number yourself.

Files first

Copy from ~/Downloads/:

frame.png → screens/colony_summary/assets/frame.png (Data closed the title hole and joined the two middle bottom windows into one)
planet_surfaces.png → screens/colony_summary/assets/_src/surfaces/ (committed source, like brief 92's icon sheets)
mockup1.png → doc/briefs/97-mockup.png

Report sha256 and pixel size of all three, and confirm the old frame.png is gone from the working tree (not merely shadowed).

Stop 1 — geometry and source, no code beyond the regenerator
Run tools/frame_holes.py on the new frame WITHOUT --write. Report the holes it finds. Expected: bottom row has three, the title cartouche is gone (so SPARE_HOLES should be empty — the docstring in name_holes_colony_summary still explains the spare by that cartouche; it is now stale, note it for Stop 3).
The match against layout_reference.json will fail, because the reference still names four bottom rectangles. Propose the new reference: planet_info (left), one middle window — name it, e.g. colony_panel — and galaxy_inset. BAND_KEYS and row_shape change with it. Say what else reads planet_output and empire_stats as CUTOUT names; those two become hand-placed content boxes INSIDE the middle window (like the sb_* readouts, decision 3), and their renderers must be pointed at the new boxes, not at holes.
The surface sheet: report the ten tiles' bounds the way brief 94 cut the icons (flood fill from the sheet border, tell the frame around each picture from the picture). Sheet order, read from the labels: Toxic, Radiated, Barren, Desert, Tundra / Ocean, Swamp, Arid, Terran, Gaia. Map each to orion2re's climate enum FROM THE SOURCE (the same enum that picks the disc in colonyplanets) — do not assume the sheet order is the game's order. Report the mapping as a table with the enum names and values.
Two things in the mockup that need a source before they are drawn:
FOOD shows 0  -5 in red. Does the original draw a second figure beside a colony's food on this screen? Check colsum.cpp's output rows. Report what it is, or that there is none.
The left panel's text: name as a heading, then climate, size and climate, gravity, minerals, population, growth. The current paragraph is transcribed; report its line order and source, so Data can decide between the transcription and the mockup with both in front of him.
Where does the surface picture go and how does it blend? The mockup fades the picture's left and right edges into the panel base. The empire_identity image box already has a fade property (decision 4, pannable image boxes). Report whether that fade does what the mockup shows, so the picture is a plain image box and the softness is a box property in boxes.json, not a renderer constant. If it does not, say what is missing — do not build it yet.

Stop. Data decides on the reference names, the mapping if anything is ambiguous, the -5, the paragraph order, and the fade.

Stop 2 — cut and build
tools/setup.py cuts the ten tiles from the committed sheet into screens/colony_summary/assets/surfaces/ (generated, gitignored), byte-identical rebuild asserted as for brief 92; note the same Pillow-resampling caveat if any scaling is involved. Prefer no scaling at build time: store the tile at sheet resolution and let the image box scale, so a 1440p screen is not fed a 1080p crop.
Filenames by climate enum name, resolved at load time through core/resources.py by the scanned colony's climate — the same path the disc takes, so a mod skin replaces the surfaces by replacing the directory (decisions 16, 17). Never a path in boxes.json.
Marked: the pictures are AI-generated artwork (ChatGPT) with no copyright claim, DEVIATION in the module that draws them, and a line in the LICENSE scope section's artwork list. The surface picture itself is an HD EXTENSION — the original shows no landscape on this screen — mark it as such where the row fills were marked (57), in the status document, and in a smoke check.
Report tile bounds actually used, sha256 of the ten outputs, and stop for Data's look at the tiles beside the sheet.
Stop 3 — rearrange
Regenerate cutouts with --write; the regenerator keeps every non-cutout box and reports how many (decision 3).
Inside the middle window, three content boxes at every resolution list: planet_output (rows, left), planet_surface (image box with fade, centre), empire_stats (right). Inside planet_info: the existing disc and paragraph boxes plus a text box for the name heading if Data chose the mockup's layout in Stop 1. All F5-draggable, all saved where the brief 95 boxes are saved.
Retire the stale cartouche explanation in frame_holes.py. Retire any code that still knows four bottom holes.
The palette from brief 95 applies unchanged; the surface picture sits ON the panel base, and the fade blends into panel_background, not into a typed colour.
Smoke test: three bottom holes match three reference rectangles; ten surface tiles exist after setup; every climate value in the enum has a tile (assert the rule); the fade is a box property; no image path in boxes.json after an editor round-trip.
Screenshots at 1080p and 1440p beside 97-mockup.png and beside the last native screenshot. Name the one check that would break a fresh clone — first suspect: a clone without running setup.py has no tiles, so the loader must treat a missing tile as a state to explain (decision 38's rule), not a crash. Push is Data's.
