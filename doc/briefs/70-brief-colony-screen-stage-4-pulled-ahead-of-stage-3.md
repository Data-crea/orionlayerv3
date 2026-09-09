Brief — Colony screen, Stage 4 (pulled ahead of Stage 3)

Read doc/v3_fundament.md before touching anything. This brief sets direction and acceptance criteria; every number, line and offset is yours to establish and report. Tree state: Stage B/C committed, frame_preview off by default, 94 checks.

What Stage 4 is

The screen switches over to the new geometry with everything except figures: boxes.json swap, frame_holes.py --write, three lower panels, sort row and RETURN, the 253×200 inset with its dot table, and the list in the new columns — using the cell rendering as the interim, since cells stay the fallback anyway. Stage 3 (sprites, squish, loader chain, figure runs) replaces cells in a list that is by then live; Stage 5 deletes the old modules and re-targets the markers in one commit.

Three stops. Code starts after Stop 1, not before.

Stop 1 — inventory and three verifications against the original

Two frame questions are open and both must be answered before the geometry swap, because their answers can change the plate — and the plate's holes are what boxes.json is generated from (decision 3). Content that moves twice is the cost of getting the order wrong.

1. The whole screen beside the original. The header was compared against the native colony summary; the full screen was not. Put the flag-on render (stageB_colony_flagon_1920x1080_*.png) beside a native screenshot of screen 20 at the same scale. Questions, not findings: which window edges does the original have, how strong are its bevels, where do they sit relative to the content, and what separates its lower panels — a strut, a bevel, or nothing? The original is the reference, not the old HD frame (fundament: "judge new artwork against the original, not against design rules"). It is a legitimate result that the old HD frame's deep bevels were the invention.

2. The struts. A3 left them plain, and the flag-on render shows what that means at median luminance 2. Report what the original does between its panels (from 1), and what a strut bevel from the master would cost: which master element supplies it, and whether the gap widths (now 26 / 28 / 29 / 38 as master struts) change. If they change, say by how much per role. Data decides plain or bevelled at this stop; the gap table is locked after that.

3. The header. Two questions carried from Stage B: does the column reservation 302 + 347·3 + 314 + 36 map onto five raised plates plus the scroll arrow, as in the original? Does the master carry a raised-plate element with a rounded bevel, or would one have to be built — from what, and marked how? Data decides five plates, master cartouche, or the interim band at this stop.

Also at Stop 1, the inventory for the swap itself:

which boxes in boxes.json are cutout-derived and which are hand-placed content boxes (decision 3), and what --write will keep versus regenerate;
the inset: state of doc/colony_inset_geometry.md §3.3/§3.5, INSET_DOT_DIM as DERIVED beside INSET_DOT_TARGET, and how you will show that the computed star pixel is the centre of the dot, measured on the image;
the click plan for Stop 3: identity re-established by construction from the icon_pops order (decision 48), one PICK and one DROP per column on the live game; name which functions produce the cell rect and the click target and confirm they are one function (decision 5);
the marker net: which HD EXTENSION / DEVIATION markings are touched by this stage, each with its three homes, and which checks read them.

Wait.

Stop 2 — the geometry swap, no list content

After Data's decisions from Stop 1. If header or struts changed, the plate is rebuilt first (derived, decision 49) and the mask follows. Then, in one commit: boxes.json swap, frame_holes.py --write (report how many non-cutout boxes it kept), the three lower panels, sort row and RETURN, the inset at 253×200 with the dot table.

Acceptance:

frame_holes.py and boxes.json agree; the smoke test asserts it.
_geometry_note in layout.json matches the built geometry; the check that keeps the 286 out still passes.
Inset: HD EXTENSION and DEVIATION markings each in their three homes; the marker inventory check is green; dot centre criterion shown on an image.
The list window is empty or carries a placeholder — no rows yet. The screen renders at 1080p, 1440p and 2160p beside the native screenshot; evidence under ~/Bilder/rahmen/ with hash in the name.
Flag-off path: state what it now means. If the old frame cannot host the new boxes.json, the flag's fallback semantics changed and that is a status-document entry, not a surprise.
Smoke green, count reported.

Wait.

Stop 3 — the list in cells, click proof, switch-on

The list rows in the new columns, cell rendering, name column with ellipsis threshold in reference px and slack only on the name, "No Farming" after the run (per the colonylist findings). Then the live proof: one PICK and one DROP per column on the reference save, with the game's response on the wire as the evidence, not the screen.

Acceptance:

Click identity by construction: the function that draws a cell is the function that targets it (decision 5). No transferred offsets.
PICK/DROP proven live per column; log excerpts in the report.
Marker checks name the files they read; the inventory check is green; nothing in the old modules is deleted yet (that is Stage 5, and marker re-targeting must be in the same commit as deletion).
Cells are the documented interim; the status document says Stage 3 replaces them and what stays (Cancel, "own group sends nothing").
Smoke green; tools/colony_list_preview.py --live and --native both run.
Reference save preserved; hashes reported.

No push at any stop — Data reviews and pushes.

Standing rules that apply throughout
Two independent sources before any production value.
No number in a doc that a check does not read.
orion2re permission as in the Stage B/C brief: conditional, one home, patch file, Stop-1 item never a Stop-2 surprise. I expect none of it here.
Long reports only for evidence, markings and hard-to-reverse decisions. Drawing questions get a crop beside a native screenshot.