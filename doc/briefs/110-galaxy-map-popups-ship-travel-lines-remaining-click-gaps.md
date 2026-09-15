 
The click table for every map object exists (brief 107, part A.1). Gaps 3 (right-click cancel) and 4 (maintext.LBX extractor) are closed as of 16c0ae7. Gaps 1 and 2 are this brief.
The original opens moveable boxes on screen 0: box 0 is the system window (Add_System_Display_Popup_Fields_, sys.cpp), box 2 is the fleet box (Add_Fleet_Movement_Box_Fields_). HD switches only on current_screen and shows no framebuffer in HD mode, so the click goes out and the answer is invisible.
The box state is on the wire (live-confirmed on a black hole): opening the system window adds its fields to the FIELD_LIST (close button with ESC hotkey, title strip, grid, whole-box field); ESC restores the previous list exactly. Field-list shape change is the signal, per decision 21. No orion2re change needed; nothing for orion2re_open_fixes.md.
Not on the wire: which star the open box belongs to (_moveable_box[0].id). HD knows it only when HD itself sent the click. A box the user has dragged changes the rectangles.
The fleet box is read in source only, never live-checked.
HD has no hit test for ship or monster icons. _star_at wins, the click lands on the star centre, the game opens the star instead of the fleet. Consequence: fleets cannot be moved on the HD map today — every fleet order goes through the framebuffer. That is the reason this brief comes before anything else on the map.
Ship icon positions are the game's (decision 24): s_ship_icon.x/y are finished 640x480 coordinates, re-anchored under the HD viewport (decision 35). An icon hit test is a rectangle around those coordinates with the measured icon size, not new geometry.
Right-click on the map: Check_Help_List_ first (decision 38), then the cancel effects; HD now sends CANCEL_FIELD before panning.
Part A — Popups: system window and fleet box
A.1 Stop 1
Fleet box, live. Open it on an own fleet and on a monster. Which fields appear, which types, which hotkeys; what the ship selection toggles look like on the wire; what the next star click does while the box is open (order path, mainscr_main.cpp:425-438). Same protocol as the black-hole run: fixture named, saves hashed before and after, SAVE10 only logged.
System window on a normal star, live. Planet and ship fields (sys.cpp:1836, :1863) — how many, which types, and what a click on a planet field does.
Which star. Since the star id is not on the wire: is it recoverable from what is? Candidates to check, not assume — the box title text (does the FIELD_LIST or snapshot carry it), the planet fields' count and picture indices matching one star's planet list, or the last star HD clicked. State which of these is a fact and which is a guess.
Dragged box. Confirm from source how the box rectangle reaches the field list after a drag, so HD can follow it rather than assume the default position.
Two designs, costed. (a) HD renders both boxes itself, data-driven, with the fields mapped to ACTIVATE_FIELD like the game menu. (b) While a box is open, HD shows the framebuffer for the box region only, until (a) exists. For each: what it needs from the wire, what it reuses, what the smoke test can pin. Data expects both in this order; the question is whether (b) is cheap enough to be worth building first.
 
Do not send fleet orders during Stop 1 on the reference save.
 
A.2 Stop 2 (after Data's decision on A.1.5)
Icon hit test in screens/galaxy_map/ before _star_at, click order matching the original (ships before stars while the box is closed, reversed while open).
Whichever design was chosen; boxes in boxes.json, wording in the screen's JSON, no wire-facing coordinate that does not go through the game's own view (decision 35).
Smoke tests: an icon click sends the icon's click, not the star's; a box-open field list is recognised and a box-closed one is not; a dragged box is followed; no fleet order is ever sent from a test.
Part B — Ship travel lines
 
The original draws a line from a ship in flight to its destination (and other map lines — relocation lines are a game setting, wormholes are drawn today in HD). HD draws no travel line.
 
B.1 Stop 1
Every kind of line the original draws on the map, from the function that draws them, with file: travel/destination line, selected-fleet order preview, relocation line, wormhole, anything else. For each: when it appears, colour source, style (solid, dashed, dash length in native pixels), endpoints (star centre? icon position? offset?).
How HD draws the wormhole line today. Which function, which pygame call, whether it is antialiased (aaline), width, colour source, and whether the endpoints and style match the original — side by side, both rendered, per the fundament rule.
Antialiasing is an invention. MOO2 is palette-indexed and cannot antialias. If HD's wormholes are antialiased, that is a marked HD EXTENSION or an unmarked one — report which. Whatever Data decides, it has to be one rule for every line on the map, not per line kind.
What the wire carries for a ship in flight: destination star, current position, ETA — which fields of s_ship_data (the design part is verified as of 16c0ae7; status, location, x, y were already), and whether the destination is a verified offset.
Dash geometry under zoom. The original's dash length is native pixels at a fixed zoom step; under the decoupled HD viewport the scale is continuous. Propose how the dash follows zoom (fixed screen pixels, scaled with the rung, or hd_zoom_level) and mark it as the HD EXTENSION it is.
B.2 Stop 2 (after Data's decisions on B.1.3 and B.1.5)
Travel lines drawn from snapshot data, geometry through the shared galaxy→HD conversion, colour from the palette, style from a table with source (dash length transcribed, HD scaling marked).
Wormhole line brought to the same rule.
Smoke test: a ship with a destination produces a line between the right two points; a ship without one produces none; every map line uses the same drawing routine (grep — one function, not three copies).
Part C — Remaining click reactions
 
From the brief-107 table, list what is still missing on the map once A is done, in the order a player hits it. Expected candidates: the system special popup (Draw_System_Special_Popup_, text now extractable from maintext.LBX), the "unexplored" and black-hole system popups (HESTRINGS), fleet-order error messages (HESTR 0x21–0x24). For each: original behaviour with source, HD status, what it needs. No implementation in this brief — Stop 2 for C is a separate decision after A lands.
 
Delivery
 
Stop 1 as one report, three parts, with the live protocol. Stop 2 per part as its own package, cumulative while unconfirmed, verified against a pristine tree after tools/setup.py, SDL_VIDEODRIVER=dummy python tools/smoke_test.py green, list of touched files, side-by-side screenshots original vs HD for every line kind and every popup.