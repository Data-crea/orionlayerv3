Brief: Galaxy-map click reactions and space monsters in the Planets screen

Two related pieces of work. The first is pure transcription: the galaxy map reacts to clicks the way MOO2 reacts, nothing added. The second is a marked HD EXTENSION: the Planets screen shows the values of the monster guarding a system, which the original never shows outside combat.

Stop 1 is findings only, no code, no boxes, no change to the tree. Stop 2 starts after Data's decisions on the Stop 1 report.

Line numbers below come from the 14 Sep monster report and are pointers, not instructions; re-read the functions.

Part A — Galaxy-map click reactions (transcription)
A.1 Stop 1

Read the main screen's input handling in orion2re (MAINSCR, _main_screen_help_list, sys.cpp, fields::Get_Input_ / Check_Help_List_) and produce one table. Rows: every kind of object the pointer can be over — unexplored star, explored star without colony, own colony star, foreign colony star, black hole, nebula, wormhole, monster icon, own fleet stack, foreign fleet stack, empty space. Columns: left click, right click, double click.

For every cell:

What happens — popup, window, help entry, screen change. Function and file.
Where the text comes from — source literal, ESTRINGS, maintext.LBX, HELP.LBX.
HD status today — present, partial, missing. File in screens/galaxy_map/.
Anything the HD version would need from the wire that the snapshot does not carry.

Two cells to settle explicitly:

Right click on a black hole: does it go through Check_Help_List_ (decision 38) or through the system popup? Order in the help table matters — the walk stops at the first hit.
Left click on an unexplored star: what exactly does Draw_System_Display_Popup_ draw in that case, with which text and which picture.

Text from LBX files: does tools/help_extract.py already cover the file in question, or does maintext.LBX need its own extractor? Same rules as decision 38: bytes handed over untouched, decoding at load time, a format version in the file, generated files never committed or shipped, an absent file is a state to explain.

Report: the table, then a list of gaps sorted by how often a player hits them.

A.2 Stop 2 (after Data picks which gaps to close first)

Transcription only. Each reaction reproduces the original's: same trigger, same content, same dismissal. Popups that belong to the galaxy map alone use the two-boxes-and-a-render-call pattern (decision 11); anything reachable from more screens uses IS_OVERLAY. Text templates in the screen's JSON (decision 15), geometry in boxes.json. A right click that the original swallows as help must not reach the wire as Cancel (decision 38).

Smoke test per closed gap: the reaction exists (grep-checkable, not only visible), and a right click over a help region sends nothing.

Part B — Space monsters in the Planets screen (HD EXTENSION)
B.0 What the source established (14 Sep report)
Combat values are fixed per type, from compiled templates (SHIP_CONFIG, ship_config.cpp). Random are only whether a monster spawns, which type, where, and for events when and whom. Difficulty changes counts and event frequency, never values.
Two templates per type: [0] game start (no drive, stationary, smaller), [1] event (drive, flying, much stronger — Dragon hull 500 vs 2500). The Guardian has one template; its hull comes from hull and armour tables via Get_Design_Structure_ — computed, but deterministic. No value needs a range. The one distinction to display is start vs event, and the drive in the design tells which.
Monsters are fully repaired every turn (Repair_Ship_Full_ for owner > 8). Outside combat they are always at 100 %, so the displayed value is the maximum and correct.
Hull points are not on the wire — they come from a fixed table in Get_Ship_Structure_ (types 10–14) and from the design tables for the Guardian.
The design block s_ship_data.d and the damage fields are on the wire (129 bytes per ship, ext_api.cpp) but in no spec, not even unverified.py. core/structs/ship.py is verified only for owner, status, location, x, y.
Outside combat the original shows the type — "(Amoeba)" under the planet in the Planets list, "guarded by …" prompts — and a system popup that is unreachable in a running game and whose picture is chosen by star index % 5, not by type (russ.cpp).
B.1 Decisions (Data, 14 Sep 2026)
Show: type, stage (start / event), size, weapons, shield, armour, special abilities, hull points. Everything beyond the type is the extension. Fundament entry states the reason: the values are fixed and have been public for years; showing them removes a disadvantage newcomers have and veterans never had. This is levelling, not balance change.
Numbers, not judgements. No "dangerous", no traffic-light colour, no difficulty word. A rating would be a second invention.
Switch in the OrionLayer section of Game Settings, default on. Same mechanics as the two existing rows (usersettings, branch before the send path, no wire traffic).
"(Amoeba)" under the planet name stays exactly as the original draws it. The values go into the lower-middle info panel, which is empty today when a guarded system is selected.
Layout: sprite left, values right. Both are boxes in the Planets screen's boxes.json, F5-draggable and resizable like every other box. Sprite box per decision 4 (zoom and crop in the JSON); value labels as text boxes (decision 37), wording as templates in the JSON, values substituted at runtime, nothing serialized.
The sprite is the HD monster sprite the galaxy map already uses for that type, largest available step. One source, no second set of artwork.
HD shows the sprite by type, unlike the original popup's star-index choice. That is a deviation that is more correct than the original; mark it DEVIATION in the renderer and name it in the fundament entry with that reason.
B.2 Stop 1 (remaining findings, before any code)
flt2 click path. How is a monster stack selected in the fleet screen, and does Print_Scanned_Ship_Data_ show weapons and shield for it? If yes, that part of the display is transcription and only hull points remain extension — this decides how the fundament entry is cut.
What the original draws in the lower-middle info panel of the Planets screen when a guarded system is selected. Function and file. Nothing goes into that panel until this is known.
Spec for s_ship_data.d and the damage fields per decision 23: compile orion2re's header with #pragma pack(1) and match the assert in sizes.h; then probe against a live game with at least two monster types via tools/struct_probe.py. Until both agree, the spec stays in unverified.py. Report the offsets and the probe result.
Hull-point table. Transcribe the numbers from Get_Ship_Structure_ and the Guardian computation from Get_Design_Structure_ into a table with source next to each value, following core/zoomtables.py. Because a mod config can override the templates without OrionLayer noticing, this copy is only legitimate with a checker in the pattern of tools/version_check.py: it reads initship.cpp and fails on a mismatch. Report the table before writing it.
Sprite resolution. Check the six HD monster assets at their largest step against the info-panel size at 1080p and 4K. Judge the asset, not an assumption. If one lacks resolution, that is a finding for new artwork, not a case for upscaling.
Names. Type names come from ESTRINGS in the original; confirm whether HD already has them in JSON or reads them from the wire.
B.3 Stop 2 (after Data's go on B.2)
Spec verified and moved out of unverified.py; monsters identified as ships with owner 9..14.
Hull-point table plus checker; smoke test runs the checker.
Settings row (switch), reusing the existing OrionLayer rows' mechanics.
Planets screen: sprite box and value boxes in boxes.json, templates in the screen's JSON, renderer fills values at runtime. Stage decided from the drive field. HD EXTENSION marker in the module, DEVIATION marker at the sprite choice.
Smoke tests: a guarded system produces exactly the values the table and the design fields say (fixture from the reference save, slot 8); switch off draws nothing in the panel; the two markers are present (grep); no wire traffic from the panel.
Docs: fundament entry (next free number — confirm, two sessions once collided); status document inventions list; brief marked done.
Delivery

One package, verified against a pristine tree after tools/setup.py, SDL_VIDEODRIVER=dummy python tools/smoke_test.py green, list of touched files. Part A and Part B may ship as two packages if Part A's gaps turn out large; if so, the second carries the first (cumulative while unconfirmed).