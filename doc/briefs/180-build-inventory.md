# Work order 180, part C1 — the build screen (wire id 25): inventory

27 September 2026, against orion2re `9ab84230` (`orionlayer-local`). The
reading this rests on is `doc/colony_screen_reading.md` §1, §2b and §3
(work order 126 G); `colbldg.cpp` is unchanged since it was written
(`git log --since=2026-09-16` empty, B1). `SCREEN_QUEUE_POPUP = 25`
(orion2_consts.h:482), `COLBLDG::Build_Queue_Popup_` (colbldg.cpp:
458-571), a SWITCHED screen with its own id (mox2.cpp:140-143), reached
from the colony screen's CHANGE (colony_main.cpp:1146-1149) and from the
Colonies screen's producing column (colsum.cpp:925-948).

**Recorded live** on a scratch engine carrying open fixes 35-40 (27
September 2026, SAVE4, `evidence/work_order_180/B_record`, stops
`popup_row0..2`): the field list is exactly the reading's §2b — Cancel,
OK, ESC, `<`, `>`, B, the autobuild radio (type 1), Refit (R), Design (D),
Repeat (E), the eleven preset keys Q 1-9 0, seven queue rows at
(207, 329+20i)-(458, 350+20i), the buildings at (13, 20+19i)-(184, 38+19i)
and the others at x 485..623 — 29 + 2 + 12 fields for Sol II. The costs
and times BLDL sent equal the native popup's own print (Colony Ship:
cost 500, build time 7, turns left 4).

## What exists in HD today

**Nothing.** `core/screen_names.py` has no HD name for 25; the popup is
the game's picture through decision 22's fallback (immediate since 180 A2
— its list always has fields).

## The two gaps 126 named — still true on `9ab84230`

Which colony (`_screen_data`/`_orbit_temp`/`_colony_handle`) and the
popup's own arrays (`_building_indexes`, `_military_indexes`,
`_current_item`, `_active_prod`, `_field_mode`, `_colony_auto_building`)
— none is serialized (B1's grep). The queue the wire shows is the one
from BEFORE the popup until OK (`Do_Exit_Screen_Cleanup_`,
colbldg.cpp:2003-2016). So, as on screen 1, every (b) below is buildable
**given** open fixes 35 (colony), 39 (queue under edit) and 40 (lists),
and the screen claims its id only when all three arrive.

## Elements the original draws

Draw root `Draw_Build_Queue_Popup_` (colbldg.cpp:992-1042).

| # | element | routine | data | class | HD |
|---|---|---|---|---|---|
| 1 | which colony | colbldg.cpp:462-469 | the pair, the handle | **(c)** | open fix 35 |
| 2 | backdrop: the colony scene, greyed | :998-1004 | — | (b) | the universal background under glass panels |
| 3 | frame COLBLDG.LBX 0 | :1011 | — | (b) | HUD panels (decision 71) |
| 4 | title "Build List for %s" | :1013-1018, E 210 | planet name | (b) | text |
| 5 | the buildings list | `Calculate_Building_Array_` :161-178, `Draw_Buildings_List_` :665-692 | the array | **(c)** | open fix 40 |
| 6 | the ships and others list | `Calculate_Military_Array_` :180-264, `Draw_Militarys_List_` :611-663 | the array | **(c)** | open fix 40; names from the wire (designs `s_player.ship_designs`, verified by 180 C) |
| 7 | a list row dim when not queued | :665-692 | the queue under edit | **(c)** | open fix 39 |
| 8 | the queue, seven rows, `"delete %s"` on hover | `Draw_Build_Queue_` :708-755, E 257 | `_current_item[7]` | **(c)** | open fix 39 |
| 9 | the selection box | `Draw_Active_Prod_` :1792-1851 | `_active_prod` | **(c)** | open fix 39 |
| 10 | the selection panel: name, cost, maintenance, build time, turns left | `Draw_Current_Selection_` :822-986, `Draw_Cost_And_Time_Info_` :1115-1174; E 242, 367, 211, 544 | the hovered or first item's numbers | **(c)** numbers | open fix 40 carries each entry's cost, maintenance and build time; turns left is fix 38's |
| 11 | the selection panel: description | `Print_App_Description_` from HELP.LBX by tech application :1056-1076 | the player's HELP.LBX | — | OMISSION `description` (the tech-application → help-entry map is not read) |
| 12 | the selection panel: picture | :1108-1113 | art | — | OMISSION `product_picture` |
| 13 | ship design stats (for designs) | `Draw_Ship_Design_Info_` :1205-1303 | `ship_designs` | (b) data | OMISSION `design_stats` — nine lines of weapon and system names from tables not transcribed; the design's NAME, cost and time are drawn |
| 14 | buttons Cancel, OK, Refit, Design, Repeat Build, Auto Build | fields :346-364, COLBLDG art | FIELD_LIST | (b) | HUD buttons; DEVIATION `button_words` |
| 15 | the autobuild radio's state | `_colony_auto_building` | — | **(c)** | open fix 39 |

## Controls the original offers

| control | field | hotkey | handler | class | HD |
|---|---|---|---|---|---|
| Cancel | `[0]` type 0 (493,447) | — | exit, scraps ships it made (:1540-1576) | (b) | field |
| ESC | `[1]` type 7 | ESC | same as Cancel | (b) | key → field |
| OK | `[3]` type 0 (560,447) | — | commit (:1487-1539) | (b) | field |
| next / previous colony | `[8]` / `[9]` | `<` / `>` | commit and switch (:1622-1641) | (b) | key → field |
| buy | `[10]` | B | commit, then buy (:1615-1621) | (b) | key → field; the box is a modal → the net |
| a building row | `_building_fields[i]` | — | toggle in the queue (:1649-1679) | (b) | field, row i of BLDL's order — **an order, sent only on the player's click** |
| a ship / other row | `_military_fields[i]` | — | add, or pick a design in mode 1 (:1681-1718); separators ignored | (b) | field; a separator row sends nothing |
| a queue row | `_queue_fields[i]` | — | select / move / delete (:1720-1780) | (b) | field |
| Refit | `[4]` type 0 (tactical only) | R | `Colony_Refit_Popup_` | (b) | field; modal → the net |
| Design | `[5]` type 0 (tactical only) | D | `_field_mode = 1` | (b) | field |
| Repeat Build | `[6]` type 0 | E | `_field_mode = 2` | (b) | field |
| Auto Build | `[2]` type **1** (490,342) | — | radio (:1465-1485) | (b) | INJECT_CLICK inside its rect (decision 20: a radio takes no activation) |
| autobuild presets | `_build_queue_hotkeys` | Q 1-9 0 | orion2re preset: commit + apply (:379-396) | (b) | keys → fields |
| right-click help | `_colony_building_queue_screen_help_list`, 13 entries (erichelp.cpp:49-63) | — | — | (b) | `help.json` |

The safety rule holds here too: `core.colony_guard` refuses a type-8
field and any full-screen field while screen 25 is reported.

## Counts

Of the 15 elements: **(a) 0**; **(b) 5** (2, 3, 4, 13 — its name, cost and
time — and 14); **(c) 8** (1, 5, 6, 7, 8, 9, 10's numbers, 15); 2 omitted
(11, 12), and 13's stat lines omitted with them. Of the 14 controls: all 14 (b) — every one reaches
its own field, and the screen that offers them waits on fixes 35, 39, 40.
