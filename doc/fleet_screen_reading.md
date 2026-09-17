> **Provenance (work order 126 G, 17 September 2026).** A source reading, written in the unattended run by a read-only sub-session and filed unchanged. Spot-checked against the tree by the session that filed it: cur_map_scale forced to the maximum (flt.cpp:14), ship icon x/y rewritten (flt.cpp:54-55), the weapon list stops at the first empty slot (flt2.cpp:696-701). Everything else is the reading's own claim with its line reference — verify before building on it (CLAUDE.md, "You own every detail"). Nothing here was driven live.

# The Fleet screen in orion2re — a reading

Read 17 September 2026 against orion2re 1.60.0 (src/version.h)

`src/version.h:10` `ENGINE_VERSION[] = "1.60.0"`. Source reading only: no game
was run, no field list was measured, nothing was injected. Every "measured"
below is a citation of an earlier measurement, never one of this reading.

**`SCREEN_FLEET = 4`** (`orion2_consts.h:465`). Not the galaxy map's fleet box
(`FLEETPOP`, `MOVEBOX` box 2), which HD already draws (decisions 65, 67; open
fixes 20/21). Where the two share state it is named below.

---

## 1. Who owns the screen, how it is entered, who builds what

**Files.** `flt1.cpp` (namespace FLT1, loop, fields, drawing, scrap,
relocation), `flt2.cpp` (FLT2, big-icon list, scan text, ship panel, move),
`flt.cpp` (one function, inset icon positions). Neighbours read: `movebox.cpp`
(inset map), `evanhelp.cpp` (help), `fleetpop.cpp` (damage bars),
`initship.cpp`, `aipower.cpp`, `shipstak.cpp`, `ships.cpp`, `officer.cpp`,
`cmbtdrw1.cpp`, `ken.cpp`, `haccess.cpp`, `fields.cpp`.

**Entry — grep `SCREEN_FLEET` over `src/`, every hit:**

| site | what |
|---|---|
| `mainscr_main.cpp:632-643` | the ONLY assignment `_current_screen = SCREEN_FLEET`: galaxy map `_fleets_button`; sets `_return_screen = SCREEN_MAIN`, `_officer_screen_return_screen = SCREEN_FLEET` |
| `mainscr.cpp:1396` | that button: `Add_Irregular_Button_Field_(167,434,230,471,…,"F",0x28)`, type 13 |
| `mox2.cpp:57-60` | dispatch `FLT1::Fleet_Screen_()` |
| `flt1.cpp:725` | `_return_screen = SCREEN_FLEET` before switching to LEADERS; `officer.cpp:1158-1160` returns through it |
| flt1.cpp:89,96,132,273,401,409-410,454,1101,1469; flt2.cpp:118,288; movebox.cpp:111 | reads only |

No numeric `= 4` assignment exists (grep `screen[a-z_]* = (0x0*4|4)` hits only
`multplay.cpp` `subscreen_mode`). HD's galaxy map sends `ACTIVATE_FIELD 12`
for Fleets (`screens/galaxy_map/layout.json:35-38`); that id was not
re-checked here.

**The loop.** `FLT1::Fleet_Screen_` (flt1.cpp:486-837). Setup :507-578, then
`do { Clear_Fields_; Add_Fleet_Screen_Fields_; Get_Input_; Scan_Input_; …;
Draw_Fleet_Screen_ } while (exit_flag == 0)` (:580-824). **The field list is
rebuilt every iteration** (:582-585). Exits: RETURN → `SCREEN_MAIN` (:689-696),
LEADERS → `SCREEN_OFFICERS` (:718-729). On exit `_cur_map_scale` is restored
(:835) and, if box 2 is open, `_fleet_box_ship_stack = _small_ship_stack_ptr`
(:826-832).

**Builders, one per thing shown:**

| thing | builder | notes |
|---|---|---|
| background | `Draw_Fleet_Screen_` flt1.cpp:385, FLEET.LBX 0 | art loaded `Reload_Fleet_Screen_` :1125-1164 (entries 0-18, small icons 19+, stars 34-44, portraits `pict_num+45` :1168) |
| inset galaxy map | `MOVEBOX::Draw_Galaxy_Map_Box_(nullptr,nullptr,15,52,305,182,0,0,0,0,1,-1)` flt1.cpp:411 → movebox.cpp:4-117, view_mode 1 = `_fleet_galaxy_star_seg[color]` at (sx-2,sy-2) (:83-85) |
| small ship icons | positions `FLT::Set_Fltscrn_Small_Ship_Icon_XYs_(15,52,305,182)` flt.cpp:5-57 (called flt1.cpp:531); drawn `Draw_Fltscrn_Small_Ship_Icons_` :216-235 |
| current stack marker | `Draw_Flashing_Small_Ship_Icon_` :237-258 |
| relocation lines | `Draw_Fltscrn_Relocation_Lines_` :1451-1491 from `_star[].relocate_ship_to[player]` (haccess.cpp:113-119) |
| destination lines | `Draw_Fltscrn_Ship_Destination_Lines_` :122-214 |
| scanned star / ship box | `Do_Fleet_Screen_Stuff_` movebox.cpp:215-227 → `Box_Fleet_Screen_Scanned_Star_` :190-200, `…_Ship_` :202-213 |
| status line under map | `FLT2::Print_Fltscrn_Scanned_Star_Name_` flt2.cpp:338-522 (hover star only, flt1.cpp:397-399) |
| scanned small stack text | `OFFICER::Print_Galmap_Scanned_Ship_` officer.cpp:2094ff, at (67,248) width 199 (:2109-2112) |
| **big icon list** (which ships, order) | `FLT2::Build_Fltscrn_Big_Icon_Fields_` flt2.cpp:207-268: walks the stack chain from `_ship_stack_start[stack]` along `next_node` (:219-253), keeps `Ok_To_Add_Ship_` && `status < 3`, restores prior selection by ship_idx (:223-261), officer move-to-front (:263-265) |
| big icon positions + fields | `FLT2::Add_Fltscrn_Big_Icon_Fields_` flt2.cpp:279-336; XY `Get_Fltscrn_Big_Icon_XY_` :116-128 |
| big icons drawn | `Draw_Fltscrn_Big_Ship_Icons_` flt1.cpp:47-120; picture `KEN::Get_Ship_Id_Picture_Seg_` ken.cpp:451-466 = SHIPS.LBX `picture_num + 50·color(previous_owner)`; damage bars `FLEETPOP::Draw_Damage_Bars_` fleetpop.cpp:41ff |
| selection frame | flt1.cpp:93-104 (`_selected_box_seg`, FLEET.LBX 17); scan frame :89-91 → :1096-1106 (FLEET.LBX 18) |
| **ship stats panel** | `FLT2::Print_Scanned_Ship_Data_` flt2.cpp:524-747, clipped (15,282)-(320,465) flt1.cpp:401-407; captain `Draw_Captains_Picture_` flt2.cpp:824-871; crew word `Crew_Description_String_` :749-773; bonuses `INITSHIP::Get_Ship_Combat_Bonuses_` initship.cpp:638-687 |
| scroll bar | `Initialize_Scroll_Bar_` flt1.cpp:31-45; fill `Fill_FltScrn_Scroll_Bar_` :260-309 |
| buttons (fields) | `Add_Fleet_Screen_Fields_` flt1.cpp:1177-1263 (§2) |
| dimmed button art | `Draw_Fleet_Screen_` :459-480 (relocate frame by `_relocate_button_mode`; dimmed SCRAP/ALL/LEADERS) |
| filter radio art | first frame :567-572; afterwards the type-1 fields |
| scrap | `Build_Scrap_List_` :936-949 → `Scrap_Ships_` :1504-1608 |
| move order | flt1.cpp:637-654 → `FLT2::Fltscrn_Move_Ships_` flt2.cpp:775-822 |
| relocation | `Star_Relocation_` flt1.cpp:898-921, checks :1626-1698 |

**The screen writes wire data it does not own.** `Set_Fltscrn_Small_Ship_Icon_XYs_`
sets `_cur_map_scale = _max_map_scale` (flt.cpp:14) and overwrites
`_ship_icon[i].x/y` with inset coordinates (flt.cpp:54-55);
`Add_Fltscrn_Small_Icon_Fields_` overwrites `_ship_icon[i].stack_id` with a
FIELD ID (flt2.cpp:34). Both are serialized (ext_api.cpp:110, :163-167). The
galaxy map rebuilds them only in `Main_Screen_` setup (mainscr_main.cpp:314-315).
So while screen 4 is up, every `s_ship_icon` on the wire is in fleet-inset
space — decision 59's "screen underneath keeps updating" hazard applies.

---

## 2. The field list, in build order

`Add_Fleet_Screen_Fields_` (flt1.cpp:1177-1263), per iteration. Field sizes of
type 0/1 come from artwork (`x_end = x + width - 1`, fields.cpp:364-365,
:400-401) — **NOT SETTLED** without a live dump; help rectangles (§6) bound them.

| # | field | pos | type | hotkey | present when | driven by | handler |
|---|---|---|---|---|---|---|---|
| 1 | SCRAP | (549,380) | 0 | S | `_n_big_icons_selected>0` && own stack && relocate mode≠1 (:1185-1191) | ACTIVATE | :698-716 |
| 2 | ALL | (348,380) | 0 | A | `_n_fltscrn_big_icons>0` && own && mode≠1 (:1193-1199) | ACTIVATE | :684-687: all on unless all already on |
| 3 | RETURN | (556,430) | 0 | ESC (0x1B) | always (:1201-1204) | ACTIVATE | :689-696 |
| 4 | scroll up | (606,59) | 0 | `-` | player ships>0 && icons>20 (:1211-1213) | ACTIVATE | :733-734 |
| 5 | scroll down | (605,325) | 0 | `+` | same (:1214) | ACTIVATE | :731-732 |
| 6 | PREV fleet | (19,249) | 0 | `,` | player ships>0 (:1216) | ACTIVATE | :761-771 |
| 7 | NEXT fleet | (283,249) | 0 | `.` | same (:1217) | ACTIVATE | :749-759 |
| 8 | RELOCATE | (441,380)-(441+w,380+h) | 7 | R | mode≠2 (:1223-1230); in mode 2 no field, id 0 | ACTIVATE | :737-747 (guarded `mode != 2`) |
| 9 | LEADERS | (342,430) | 0, else 7 | L, else none | always; type 0 if `At_Least_One_Officer_` (:1232-1241) | ACTIVATE | :718-729; hidden variant → message H 0x79 |
| 10.. | small ship icon, one per `_ship_icon[i]` | (icon.x,icon.y)-(+w,+h) | 7 | — | always (flt2.cpp:27-43) | ACTIVATE (id compare flt1.cpp:851) | selects that stack; see "overlap" below |
| .. | big icon, ≤20 | (x,y)-(x+58,y+57) | 7 | — | own stack only (flt2.cpp:319-330) | ACTIVATE sets the SCANNED ship only | flt1.cpp:614-627 |
| .. | scroll field | (605,86)-(619,320) | 6 | — | stack ptr>-1 && icons>4 (flt1.cpp:1245-1248, flt2.cpp:104-107) | cannot (pointer) | via `thumb_center_y` |
| .. | star, one per star | (sx-3,sy-3)-(sx+8,sy+9) | 7 | — | always, star order (movebox.cpp:506-511) | ACTIVATE (mainscr.cpp:3022-3028) | move / relocation (flt1.cpp:629-666) |
| .. | debug | (0,470)-(10,479) | 7 | — | always (:1252) | — | nothing compares it |
| .. | SUPPORT filter | (425,435) | 1 | U | player ships>0 (:1255) | INJECT_CLICK or INJECT_KEY U | :773-795 |
| .. | COMBAT filter | (487,435) | 1 | C | same (:1256) | INJECT_CLICK or INJECT_KEY C | :773-795 |
| last | whole screen | (0,0)-(639,479) | 7 | — | always (:1262) | — | nothing compares it |

Ids shift with every conditional field and with the icon and star counts, so a
client identifies fields by type, hotkey and geometry (decision 59), never by
index. FIELD_LIST is resent only when the count or screen changes
(ext_api.cpp:671-674); a stack switch that keeps the count leaves the old list
on the wire, whose big-icon slot rects are identical anyway.

**Keyboard-only commands** (Interpret_Keyboard_Input_ fields.cpp:2531-2570,
platform.cpp:416-420, :461-465): F1 → -1001 = PREV (flt1.cpp:761), F2 → -1002 =
NEXT (:749), F5 → -1005 = merge-relocations mode (:602-612), Alt-F5 → -1105 =
clear all relocations + message H 0x76 (:597-601). **INJECT_KEY cannot send
any of them**: its keysym is an int16 (ext_server.h:59) copied into
`event.key.key` (ext_api.cpp:520) with no modifier, and SDL3's `SDLK_F1` is
`0x4000003a`. F1/F2 have button twins; **F5 and Alt-F5 cannot be driven**.

**Radio buttons.** ACTIVATE returns the id without toggling (type 1 toggles
only in fields.cpp:1018-1024, :1116-1122, :1292-1297); the handler then finds
one status still 1 and only rebuilds the list. INJECT_CLICK toggles
(:1292-1297); an injected hotkey toggles too (:1010-1024). Semantics
(flt2.cpp:130-146): both 1 → all ships; combat only → combat ships; support
only → colony/outpost/transport; switching off the last lit one lights the
OTHER (flt1.cpp:775-781). Both reset to 1 by `Harold_Defaults_`
(harold.cpp:1475-1477) from `Init_Map_Defaults_` (mox2.cpp:215), i.e. on load
(filedef.cpp:158) and new game (initgame.cpp:233); persistent across visits.

**What the loop IGNORES from an injected click:**
- **Per-ship selection.** Painted in the DRAW pass: `Draw_Fleet_Screen_` tests
  `mouse::Mouse_Button_() == 1` and `fields::Auto_Input_()` against each big
  icon's `button_id` (flt1.cpp:413-436); `_auto_input_variable` is set before the
  auto call on a buffered click (fields.cpp:1286-1288) and while a button is
  held (:1456-1461), but the draw pass also needs the LIVE button state. ACTIVATE reaches
  `Scan_Fltscrn_Big_Icons_` result 0, which only scans (flt2.cpp:924-928,
  flt1.cpp:615-620). This is the fleet box's path again (open fix 20: an
  INJECT_CLICK on a box ship did not toggle, measured); for this screen it is
  **NOT SETTLED live, expected not to toggle**. Only ALL changes selection.
- **Hover state**: scanned ship (stats panel), scanned star (status line,
  destination preview), scanned small stack — all from `Scan_Input_`
  (fields.cpp:652ff, pointer) via flt1.cpp:590, :615-620, :629-633, :679-681.
  A click (result 0) also sets `_scanned_big_ship`; a star click never sets
  `_galaxy_map_scanned_star` (`star_idx_ptr_1` stays -1, mainscr.cpp:3030-3037).
- **Scroll field value**: pointer-read (decision 39's correction).
- **Relocate mode `input < 0`** (flt1.cpp:592-596) needs a right click.

**Overlap cycling.** A click on a small icon passes through
`SHIPS::Overlapped_Ship_Icon_Button_(&i,7,4)` (flt1.cpp:853, ships.cpp:568-623):
a repeat click within 7x4 px of the last one (`_icon_overlay_x/y`, reset to -1
on entry flt1.cpp:518-519) ROTATES `_ship_icon[]` entries and swaps
`_ship_stack_start[]` using ICON indices as STACK indices (ships.cpp:611-615).
The rotation is visible on the wire; the stack swap is not.

**Dead branch.** `ret_map == 1 && mode == 1` → `Cancel_Star_Relocation_`
(flt1.cpp:635-636) can never fire: `Scan_Galaxy_Map_Fields_` returns only -1,
0, 4, 2 (mainscr.cpp:3017-3045). A same-star second click cancels instead
(flt1.cpp:910-911).

---

## 3. Every value displayed, and the wire

STATE layout per `SerializeState` (ext_api.cpp:92-241). s_ship_data offsets not
in `core/structs/ship.py` are hand-counted from orion2.h:2847-2868 against the
verified anchors 99-109; s_star_data ones from orion2.h:2975-3013 against
`PLANET_INDEX_OFFSET = 195` (star.py:60).

| value | source line | on wire | struct @offset | verified |
|---|---|---|---|---|
| inset star x/y | movebox.cpp:69-70 | yes | s_star_data x 15, y 17 | VERIFIED star.py |
| inset star colour | movebox.cpp:72-82 (black hole, visited, owner colour) | yes | spectral_class 22, owner 20, visited 171; s_player color 38 | VERIFIED |
| inset scale | movebox.cpp:20-21, :69-70 (`_max_map_scale`) | derivable | MAP_MAX_X/Y header 25/27 | fundament §3 |
| star hit rect | movebox.cpp:365-380 (`/ (506000/w + 1)`, centre offset 3) — a DIFFERENT transform from the draw (`/ (506000/w)`, :20, :69) | derivable | — | — |
| small icon x/y (inset space on screen 4) | flt.cpp:24-55 | yes | s_ship_icon x 8, y 10 | VERIFIED ship_icon.py (map-space meaning only) |
| small icon owner colour / monster | flt1.cpp:219-233 | yes | FSEL owner bytes (ext_api.cpp:189-195); s_ship.owner 99 | VERIFIED |
| current stack (flashing) | flt1.cpp:243-257, `_small_ship_stack_ptr` | **NO** | mox.cpp:188 | — |
| relocation lines | flt1.cpp:1481-1490; no `show_relocation_lines` test | yes | s_star_data relocate_ship_to[8] @205 (hand count) | **UNVERIFIED** |
| own moving ship lines | flt1.cpp:176-212 | yes | s_ship location 101 | VERIFIED |
| enemy lines toward our colony | flt1.cpp:189 `SHIPS::Enemy_Ship_Heading_Toward_Our_Colony_` | derivable, function NOT READ | — | NOT SETTLED |
| selected-target line (green/red) | flt1.cpp:132-174 from `_g_ship_move_info.moving` | **NO** (hover) | — | — |
| status line: star name | flt2.cpp:481 | yes | name 0 | VERIFIED |
| status line: governor + ETA | flt2.cpp:479-490 | partly | s_star_data officer_index[8] @187 (hand count); s_leader_data name 0, eta | **UNVERIFIED** (unverified.py) |
| status line: "N turns to X", out of range, black hole, flux | flt2.cpp:356-469 from `SHIPMOVE::Ships_Try_To_Move_To_` | **NO** (computed on hover) | — | — |
| status colour by star owner | flt2.cpp:508-516 | yes | owner 20, color 38 | VERIFIED |
| scanned small stack text (race FLEET, counts) | officer.cpp:2094ff | derivable (hover) | ships | — |
| big icon SET and ORDER | flt2.cpp:219-265 | **only for the fleet box's stack** (FSEL chain ext_api.cpp:225-240) | — | see below |
| big icon picture | ken.cpp:451-466 | yes | picture_num 92, previous_owner 93 (BUILDER colour, not owner) | VERIFIED |
| selection per icon | `_fltscrn_big_icon[].selected` flt1.cpp:429 | **NO** (not `_ship_node[].selected`; FSEL does not carry it) | orion2.h:405-413 | — |
| "≥1 selected" | SCRAP field present (flt1.cpp:1185) | yes, FIELD_LIST | — | source reading |
| damage bar | fleetpop.cpp:41-81, `AIPOWER::Max/Current_Ship_Hits_` aipower.cpp:200-250 | partly | structural_damage 125, armor_damage 123; s_settings strategic_combat_flag (orion2.h:2492) | **UNVERIFIED** (ship.py says so; flag not in settings.py) |
| ship name | flt2.cpp:581 | yes | d.name 0 | VERIFIED |
| crew word + EP | flt2.cpp:589-594 | yes | crew_quality @113, crew_experience @114 (i16) | **UNVERIFIED** |
| shield name | flt2.cpp:598-599 | yes | shield_type 18; TECHNAME via core/shipparts.py | VERIFIED |
| attack / defense bonus | flt2.cpp:546, :605-641; initship.cpp:638-687 | **NO**, derived from design, officer skills (leader record), `_crew_data` (mox.cpp:780), traits (player.py TRAITS_OFFSET 2308), strategic flag, `Best_Warp_Drive_` (tech applications, not decoded) | — | inputs partly UNVERIFIED |
| location line | flt2.cpp:645-677 | yes | location 101, visited 171, traits[27] | VERIFIED; galactic-lore leader UNVERIFIED |
| weapons "n Name (arc)" | flt2.cpp:696-724 | yes | weapon type/count/firing_arc | VERIFIED (WEAPON_SPEC); arc text `DESIGN::Weapon_Arc_String_` NOT READ |
| specials, red when damaged | flt2.cpp:728-746 | yes / no | special_device_flags 23 VERIFIED; special_device_damage_flags @118 UNVERIFIED |
| captain portrait, name, ETA box | flt2.cpp:824-871 | yes | s_leader_data player_index, status, type, location, pict_num, eta | **UNVERIFIED** |
| support-ship text (colony/transport/outpost) | flt2.cpp:548-576, HELP.LBX records 0x29/0xBD/0x6D | not wire (HELP.LBX) | — | — |
| scroll thumb | flt1.cpp:260-309 | **NO** (`first_visible_row`) | — | — |
| filter button states | type-1 fields | **NO** (mox.cpp:152-153) | — | — |
| relocate button frame / merge mode | flt1.cpp:459-470 | partly: mode 1 removes SCRAP/ALL, mode 2 removes RELOCATE (flt1.cpp:1185, :1193, :1223-1225) | FIELD_LIST | source reading |
| dimmed LEADERS | flt1.cpp:478-480 | yes: LEADERS field type 0 vs 7 | FIELD_LIST | source reading |

**Big-icon membership off the wire — why decision 25 stops short.** Nodes
are appended in rising index (shipstak.cpp:76-100) and
`Sort_Ships_In_Stack_` rewrites ship_idx along the chain without moving nodes
(:261-278), so an OWN stack's chain is its nodes in rising index. But
`Remove_Non_Detected_Ships_` unlinks nodes of foreign stacks
(shipstak.cpp:200-250) and `Delete_Ship_Node_` leaves their `ship_idx` in place
(:5-11), so the FSEL node table (all `_next_free_node` entries,
ext_api.cpp:217-224) still names undetected ships; and the overlap swap
permutes `_ship_stack_start` (ships.cpp:613-615), which decides NEXT/PREV
order. Own stacks: reconstructable with a validation, against decision 67's
"nothing rebuilds it" — a question for Data. Foreign stacks: **not**.

---

## 4. Screen IDs while it is up

`ext::Tick(MOX::_current_screen)` runs inside every `Get_Input_`
(fields.cpp:167). The screen reports **4** throughout its loop.

| sub-popup | how | reports | field list | leaves to |
|---|---|---|---|---|
| help text | CALLED `TEXTBOX::Draw_Help_Entry_` fields.cpp:2930 | 4 | — | fleet |
| message box (H 0x76, 0x77, 0x79, 0x75, "Too many ships") | CALLED `HAROLD::User_Box_` type 0 harold.cpp:1274ff; flt1.cpp:601, :662, :722, :930; flt2.cpp:887 | 4 | box's own | fleet |
| warning box (H 0x78, 137, 127, 130, 0x83-0x88, move refusals H 0x21/0x90/0x91/0x24) | CALLED type 3; flt1.cpp:644, :895, :1526, :1640, :1695; flt2.cpp:802, :813, :819 | 4 | 2 fields (game_menu_reading §4) | fleet |
| confirmation (scrap H 122-125, 126, 128/129; monster-guarded relocation H 0x87) | CALLED type 1; flt1.cpp:1523, :1543, :1571, :1674 | 4 | 3 fields | fleet |
| fleet-change confirmation inside a move order | CALLED `GENDRAW::Confirmation_Box_` shipmove.cpp:79, :96 via `Apply_Player_Movement_Order_` :693-694 | 4 | 3 fields | fleet |
| officer change | CALLED `SHIPMOVE::Confirm_Officer_Change_` shipmove.cpp:1021 (flt1.cpp:1558) — body NOT READ | 4 | NOT SETTLED | fleet |
| recovered tech text box (H 116) | CALLED type 2 flt1.cpp:1433 | 4 | NOT SETTLED | fleet |
| **Detailed ship view** | CALLED `CMBTDRW1::Detailed_View_Ship_` cmbtdrw1.cpp:153-240, from a RIGHT click on an own big icon (flt2.cpp:929-933 → flt1.cpp:621-626) | 4 | new list (`Mark_Fields_` shifts `_fields`, fields.cpp:865-876): 1 name input type 11 (262,50) max 15, 2 hidden (268,50)-(383,64), 3 whole screen type 7; field 0 stale | fleet; renames `d.name` on exit (:229-234) |
| LEADERS | SWITCHED, `SCREEN_OFFICERS` = **29** (flt1.cpp:724, mox2.cpp:149-152) | 29 | its own | back to 4 via `_return_screen` (officer.cpp:1158-1160) |

The right click reaches the detail view because `_mouse_cancel_disabled` is
set once by `Main_Screen_` (mainscr_main.cpp:281) and nothing clears it
(grep: fields.cpp:113 only), so a right click outside a help rectangle returns
`-field_idx` (fields.cpp:1360, :1513), not -1. Occupied big icons carry no
help rectangle (§6). `CANCEL_FIELD` pushes the right button at the field's
centre (ext_api.cpp:586-615), but `Check_Help_List_` tests the POINTER
(fields.cpp:2917-2918) — whether CANCEL_FIELD opens the view is **NOT SETTLED**.

LEADERS does not force the ship officer list: `Officers_Screen_` keeps
`_officer_scrn_type` unless coming from the colony screen or at -1
(officer.cpp:893-901), and load/new game set it to 1 = COLONY
(harold.cpp:1480, orion2_consts.h:313-314). Which list opens is **NOT SETTLED**
at runtime.

---

## 5. What would need a patch (description only)

1. **Fleet screen view state — optional trailing block "FLTS" in
   `ext::SerializeState` (ext_api.cpp), only while `current_screen == 4`.**
   Carries: `_small_ship_stack_ptr`, its head node, `_fltscrn_stack_owner`,
   `_n_fltscrn_big_icons`, then per icon `ship_idx` and `selected` in
   display order, `first_visible_row`, the two filter statuses,
   `_relocate_button_mode`, `_merging_relocations`, `_scanned_big_ship`. Why no
   path: all are MOX/FLT1 globals (mox.cpp:109-188, flt1.cpp:5-12) that
   `SerializeState` never touches; FSEL carries only box 2's stack
   (ext_api.cpp:211-216) and `_ship_node[].selected`, which this screen does
   not use. Reconstruction first (decision 25): selection is mirrorable while
   only ALL changes it (empty on entry flt1.cpp:523, flt2.cpp:223-261; cleared
   after a move flt2.cpp:795); filters are mirrorable from a known reset
   (harold.cpp:1475-1477) but a human at the shown game window can change
   them (decision 46's argument); stack identity and big-icon order are not
   reconstructable for foreign stacks (§3). One file, `src/ext/ext_api.cpp`.
2. **Per-ship selection on this screen** — a command, the write half of 1. Either
   `MSG_SELECT_SHIP` branching on screen 4 or a new id; writes
   `_fltscrn_big_icon[i].selected` after checks: screen 4, own stack, ship in
   the list, relocate mode ≠ 1 (painting is off there, flt1.cpp:413). Why:
   painting cannot be driven (§2); open fix 21's handler requires box 2 and
   writes `_ship_node` (ext_api.cpp:463-497). Files: ext_api.cpp,
   ext_server.cpp/.h (message id). Without it a subset of a stack cannot be
   moved or scrapped from HD.
3. **Attack/defense bonus** — only if Data does not want a transcription:
   two int16 per displayed ship. Reconstruction needs `s_leader_data`
   (unverified.py), crew fields @113-116, `strategic_combat_flag`, tech
   applications and `_td_combat_speed_bonus` (initship.cpp:649-683).
4. **Move preview** (`_g_ship_move_info` for a target) — hover-computed
   (flt2.cpp:356-429); transcription would copy `SHIPMOVE::Ships_Try_To_Move_To_`
   (not read). A patch would need a target from the client, i.e. a query
   command. Alternative: OMISSION.
5. **F5 / Alt-F5** — `MSG_INJECT_KEY` widened to a uint32 keycode plus
   modifier (ext_server.cpp:206-213, ext_api.cpp:514-523), or two commands.

Nothing else needs a patch: move orders (star field ACTIVATE), relocation,
scrap, ALL, NEXT/PREV, scroll buttons, RETURN and LEADERS are all id-compared.

---

## 6. Right-click help

Installed by `EVANHELP::Set_Fleet_Screen_Help_List_(_n_fltscrn_big_icons_added)`
(evanhelp.cpp:378-407) at entry (flt1.cpp:549), every iteration (:802) and after
the detail view (:624). Static table `_static_fleet_screen_help_list`
(evanhelp.cpp:153-166), first match wins (fields.cpp:2924-2932):

| id | rect | | id | rect |
|---|---|---|---|---|
| 361 | (605,59)-(619,349) scroll column | | 369 | (441,380)-(529,407) RELOCATE |
| 363 | (66,248)-(267,268) status line | | 370 | (549,380)-(621,407) SCRAP |
| 364 | (19,249)-(50,267) PREV | | 371 | (342,430)-(414,456) LEADERS |
| 365 | (283,249)-(313,267) NEXT | | 372 | (425,435)-(485,453) SUPPORT |
| 366 | (13,280)-(319,465) ship panel | | 373 | (487,435)-(546,453) COMBAT |
| 368 | (348,380)-(421,407) ALL | | 374 | (456,430)-(628,456) RETURN |

Dynamic (help id 360): with 0 icons added, one rect (344,53)-(591,353)
(:383-388); otherwise one per EMPTY slot i = added..19 at
(342+64·(i%4), 52+64·(i/4))-(406+…, 114+…) (:390-403) — **pitch 64, while the
icons step 62 x 60** (flt2.cpp:124-127); transcribe, do not unify. No help
over the inset map (15..320, 52..234). HELP.LBX 359 (galaxy map), 362 (scroll
bar) and 367 (scroll down) exist but no table uses them. All 360-374 are in
`assets/shared/help/help_en.json` (checked by id).

---

## 7. Layout under one provisional content box

Every coordinate is an absolute native constant; nothing is a movable box.
Native rectangles that decide it:

| region | rect | source |
|---|---|---|
| inset map | (15,52) 305x182 | flt1.cpp:411, :531; mouse list (15,52)-(319,233) :15 |
| status line, PREV, NEXT | (19..313, 248..268); text centre x 169, y 248+(23-h)/2 | evanhelp.cpp:155-157; flt2.cpp:521 |
| ship panel | clip (15,282)-(320,465); x 18/23/173/188; y 287 + font heights | flt1.cpp:402; flt2.cpp:572-745 |
| captain | portrait (242,284), frame (240,282) | flt2.cpp:855-866 |
| big-icon grid | origin (347,53), 4x5, step 62x60, cell 58x57 | flt1.cpp:508-514; flt2.cpp:124-127, :289-290 |
| scroll column | (605..619, 59..349); track x 606 y 86 w 12 len 234 | evanhelp.cpp:154; flt1.cpp:274-278, :35 |
| button band | (342..628, 380..456) | flt1.cpp:1187-1256; evanhelp.cpp:159-165 |

Union: **(13,52)-(628,465)** inside the full-screen FLEET.LBX 0 background
(flt1.cpp:385). **It fits one box** as a uniform scale of that union. Four
limits for the draft rule:
1. **Four natural sub-panels** (map + status line, ship panel, grid + scroll,
   button band), divided by the ARTWORK. A frame that re-proportions them
   moves four boxes, not one; the rule should say the provisional box holds
   sub-boxes in native proportion.
2. **The inset is aspect-bound**: 305:182, and `Box_Fleet_Screen_Scanned_Star_`
   hardcodes 1659 and 2197 (= 506000/305, 400000/182) plus +10/+47
   (movebox.cpp:193-199).
3. **The ship panel's y is data- and font-dependent** (flt2.cpp:584-686:
   `Get_Font_Height_` steps; captain present moves defense to a new line
   :614-641); FONTS.LBX, not in the source.
4. Hit rects and help rects stay native whatever the layout (decision 35).

Third site of the small galaxy inset (colony summary and Planets were two,
plntsum_reading "the third is the signal"): here `Draw_Galaxy_Map_Box_`
view_mode 1 and `Get_Galaxy_Map_Star_XY_` marker mode 1 → centre offset 3
(movebox.cpp:374).

---

## 8. Seen on the way

- **Damage bar width 1 on this screen** (flt1.cpp:56-59, :110) → effective
  width -3 (fleetpop.cpp:42); green clamps to 2 (:50-52). Geometry **NOT
  SETTLED**; needs a native screenshot.
- **Weapon list stops at the first empty slot** (flt2.cpp:700-701, `break`
  via `no_weapons`); `core/structs/ship.py weapons()` skips empty slots and
  its docstring cites flt2.cpp as a `count > 0` filter — a drifted reading.
- Specials loop stops at 38 (flt2.cpp:728; decision 64 knows).
- `N_Fltscrn_Ships_Selected_` counts from the first visible row (flt1.cpp:979),
  and the post-scrap rebuild compares it with the whole list (:707).
- `At_Least_One_Officer_` counts any leader with status ≥ 0 (flt1.cpp:1313-1322);
  portraits load only ship leaders with status 1 (:1153-1159).
- Help text 361 says sixteen ships; the grid holds 20 (label, HELP.LBX).
- Scrap BC is credited only when interactive and value > 0 at an own colony
  (flt1.cpp:1563-1582); the value (`maintain::Ship_Scrap_Value_`,
  maintain.cpp:206) was NOT READ.
- Whether `Kill_Ship_` compacts `_ship[]`, which would shift the ship_idx
  a kept selection is matched by (flt2.cpp:257), NOT READ.

---

## 9. Questions for Data before a build can start

1. Screen (own id 4, own background) and not an overlay — agreed?
2. Request the FLTS view-state block (§5.1) as open fix 22, or build on the ALL-only mirror first?
3. Per-ship selection: extend MSG_SELECT_SHIP to screen 4, new command, or ALL-only in HD?
4. Own-stack big-icon order rebuilt from rising node index (decision 25) despite decision 67, or wire only?
5. Attack/defense bonus: transcription with a checker, patch, or OMISSION?
6. Verification stop first for s_ship_data 113/114/116/118/123/125, s_star_data 187/205, s_leader_data?
7. Damage bars: screenshot first, then transcribe the width-1 result as drawn?
8. Weapon list: transcribe "stop at first empty slot" on this screen, and fix ship.py's docstring?
9. Specials: 39 like this screen or 40 like the Planets panel?
10. Detailed ship view (right click, rename): in scope, and may it use CANCEL_FIELD despite decision 66?
11. Move preview status line: transcribe SHIPMOVE, patch a query, or OMISSION?
12. F5 merge and Alt-F5 clear relocations: widen INJECT_KEY, or OMISSION?
13. Relocation (two-step star picking, merge) in the first build or later?
14. Native confirmation/warning boxes: HD draws them (decision 33 mirrors) or leaves the framebuffer?
15. Galaxy map HD must ignore s_ship_icon while screen ≠ 0 (inset coordinates, field ids in stack_id) — confirmed as a rule?
16. LEADERS opens whatever officer list was last used — transcribe that?
17. Layout: one provisional box holding four native-proportion sub-panels — acceptable reading of the draft rule?
