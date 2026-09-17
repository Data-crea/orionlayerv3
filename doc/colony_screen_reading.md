> **Provenance (work order 126 G, 17 September 2026).** A source reading, written in the unattended run by a read-only sub-session and filed unchanged. Spot-checked against the tree by the session that filed it: SCREEN_QUEUE_POPUP is its own case in Screen_Control_ (mox2.cpp:140-143); FIELD_LIST is resent only on a count, screen or dirty change (ext_api.cpp:670-671). Everything else is the reading's own claim with its line reference — verify before building on it (CLAUDE.md, "You own every detail"). Nothing here was driven live.

Read 17 September 2026 against orion2re 1.60.0 (src/version.h)

# The single colony view and its build queue in orion2re: a reading

`src/version.h:10` reads `ENGINE_VERSION[] = "1.60.0"`. This is a source reading only. Nothing
was driven, nothing measured, no file in either tree was changed. Every rectangle below
comes from an `Add_*_Field_` call or a draw call. Button sizes come from LBX art and are
**not in the source**. Hotkey letters come from ESTRINGS.LBX (the user's extracted
`assets/shared/names/estrings_en.json`), so they hold for English only.

- **`SCREEN_COLONY = 1`** (`orion2_consts.h:463`): `COLONY::Colony_Screen_`, colony_main.cpp:238-378
- **`SCREEN_QUEUE_POPUP = 25`** (`orion2_consts.h:482`): `COLBLDG::Build_Queue_Popup_`, colbldg.cpp:458-571

---

## 1. Owners, entry, and the functions that BUILD what is shown

### Files

| file | owns |
|---|---|
| `colony_main.cpp` (1295 lines) | screen loop, draw root, `Add_Screen_Fields_`, `Evaluate_Screen_Input_`, name/pop line, current-production box |
| `colony.cpp` (2374) | `Update_Fields_`, job/military/building/satellite field adders, the four `Check_*_Fields_` handlers, production/morale/officer/scan drawing |
| `coldraw.cpp` | production icons, morale icons, production bar, the pop icon walk |
| `colsysdi.cpp` | system display (left of the top band) |
| `colbldg.cpp` (2386) | the whole queue popup: arrays, fields, loop, input, drawing, queue mutation |
| `build_queue.h/.cpp` | orion2re's own autobuild presets (not MOO2): `Apply_Preset_To_Colony_`, `autobuild_settings` |
| `erichelp.cpp` | both help tables |

### Who sets `MOX::_current_screen` to 1 or 25 (grepped for the enum names and the literals `= 1` and `= 25`)

| site | sets | how the colony is named |
|---|---|---|
| mainscr.cpp:1583-1589 (`Do_Colony_Screen_`, galaxy map) | 1, return 0 | `_screen_data = star`, `COLONY::_orbit_temp = orbit` |
| colsum.cpp:916-919 (colony summary, name field) | 1, return 20 | same pair |
| info.cpp:2089, msg.cpp:663, turnsum.cpp:182 | 1, return 9 / 9 / 40 | via `MSG_::Goto_Msg_Colony_` |
| report.cpp:733-742 | 1, return 39, **then CALLS `COLONY::Colony_Screen_()` directly** (:742) | same pair |
| report.cpp:863 | 1, return 39 | same pair |
| colland.cpp:235 | literal `1` (its comment says `SCR_MAIN_VIEW`, but 1 is `SCREEN_COLONY`) | `COLONY::_colony_handle` already set |
| colony_main.cpp:1147-1148 (CHANGE button) | **25**, return 1 | unchanged globals |
| colsum.cpp:942-943 (colony summary, producing text) | **25**, return 20 | `_screen_data`/`_orbit_temp` set just above (:930-931) |
| colsum.cpp:808-809 | 25 when returning from a design started in the popup | |
| colbldg.cpp:556-559 | 3 (DESIGN) from the popup. design_main.cpp:373/:383 goes back to `_return_screen` | |

Dispatch: mox2.cpp:49-52 (`case SCREEN_COLONY`) and mox2.cpp:140-143 (`case SCREEN_QUEUE_POPUP`).
**The queue popup is a SWITCHED screen with its own id. It is not a call inside the colony
screen.**

### The colony is re-derived on every entry

`Colony_Screen_` reads `_star_handle = MOX::_screen_data`, then the planet from
`HAROLD::Planet_Index_(_screen_data, _orbit_temp)`, then
`_colony_handle = planet.colony_index` (colony_main.cpp:249-254). An invalid colony returns at once
(:276-282). **`MOX::_PLAYER_NUM` is set to the colony's owner for the whole screen** (:284) and
restored on exit (:362). The popup repeats the same derivation (colbldg.cpp:462-469).

### How each screen is left

**Colony screen.** The loop breaks on `input == _colony_fields[1]`, the RETURN button
(colony_main.cpp:350), or when `Evaluate_Input_` returns 0 (:341-347).
- On RETURN it runs `Cleanup_Colony_Queue_`, which puts Trade Goods into an empty
  `producing[0]` (colony.cpp:1074-1080), and switches to `_return_screen` (:365-374).
- On a 0 return it switches to nothing: officers (colony_main.cpp:1043-1048), the popup
  (:1146-1149), next/previous colony (:1152-1180) or a planet in the system display
  (colony.cpp:1809-1821). `Screen_Control_` then re-dispatches whatever id is current. **Changing
  colony therefore re-enters `Colony_Screen_` with the same id 1.**

**Popup.** It breaks on OK / Cancel / ESC (colbldg.cpp:529-534), on `<` / `>` (:538-542), or when
a design is requested (:535-537). Afterwards it returns to `_return_screen`, or to DESIGN, or
stays on 25 for `<` / `>` (:555-568).

### Builders: colony screen (draw root `Draw_Colony_Screen_`, colony_main.cpp:100-185)

| thing | builder | native position |
|---|---|---|
| landscape | `C_Anims_(1)` = COLONY2.LBX 0x31, then `C_Anims_(0)` = planet backdrop by `climate_bg_type + climate*3` (colony_main.cpp:111-115, :476-481) | (0,0) |
| roads | `COLDRAW::Draw_Road_List_` (:117) | |
| top band | `Draw_Colony_Info_Background_`: `Darken_Fill_(0,0,640,150)` plus COLPUPS.LBX 5, or 6 while a pop is unassigned (colony.cpp:621-635) | (0,0) |
| system display | `COLSYSDI::Draw_Col_Sys_Disp_(7,24)` (colony_main.cpp:129; colsysdi.cpp:8-49), rows `y+i*24`, text via `Planet_Summary_String_` (:88) | x 7..115 |
| galaxy inset (`_drawing_display==1`) | `MOVEBOX::Draw_Galaxy_Map_Box_` (colony_main.cpp:142). **Unreachable in 1.60.0**, see §2 | |
| buildings | `Make_Bldg_Array_For_Colony_` (colony_main.cpp:536-631), then `Draw_Colony_Bldgs_` back-to-front (:77-98) | grid from `_building_cr` (colony.cpp:4-20) |
| satellites | `Draw_Colony_Satellites_`, x = `295 ± 50·i` alternating, y 162 (colony.cpp:637-661) | |
| military units | `Draw_Colony_Info_Military_` → `Do_Colony_Info_Military_Stuff_For_` (colony.cpp:690-704; colony_main.cpp:1193-1293). Drawn at y = `479 - h`, step `260/total` squished; `"x %d"` form when squished (:1228-1250) | bottom-left |
| officer | `Draw_Colony_Info_Officer_`: frame COLPUPS 0x16 at (544,351), portrait (550,357), name or `ETA:%d t` centred (586,433) (colony.cpp:706-734) | |
| production (BC, food, industry, research) | `Draw_Colony_Info_Production_For_` → `COLDRAW::Draw_Colony_Prod_(colony, sel, 128, y, 301, 20)`, y = 32/64/94/124 (colony.cpp:743-765). Icons: `Draw_Colony_Prod_Both_` (coldraw.cpp:36-181) from `production`, `maintenance`, `imports`, `pollution` | x 128..301 |
| population icons | `Draw_Colony_Info_Pop_For_(type)` → `Do_Colony_Info_Pop_Stuff_For_Pop_(…, mode 0, 310, 62+30·type, 510, shadows=1)` (colony.cpp:1332-1349; walk coldraw.cpp:281-444) | x 310..510, y 62/92/122 |
| morale | `COLDRAW::Draw_Info_Morale_(colony, 310, 33, 510)`: government icon, then `|morale/2|` icons, none under Unification or later (colony.cpp:963-965; coldraw.cpp:187-243) | |
| title | `Draw_Info_Name_And_Pop_`: `"%sColony of %s"` (E 97) or blinking `"Annihilating %s"` centred (320,0) (colony_main.cpp:806-826) | |
| status word | Blockaded / Plague / Pop Boom at `Print_(0,0)` (:831-853) | |
| population line | `"Pop %d,%03d k (%+dk)"` (E 424), right-aligned at (638,3). Value is `Sum_Colonists_` (assigned pops only) + Σ`pop_roundoff`/1000, then Σ`pop_growth` (:858-873) | |
| current production | `Draw_Info_Build_` (colony_main.cpp:899-977): picture clipped to (517,17)-(639,158) (:879-895, colony.cpp:779); name `Squeeze_Print_Paragraph_(522,38,112,141)` (:959); bar `Draw_Colony_PC_Bar_(606,43,cost,spent)` (colony.cpp:967-978; coldraw.cpp:249-279); `"%d turn(s)"` right-aligned (624,103) (colony.cpp:980-994); autobuild label centred (578,28) (colony_main.cpp:961-974) | |
| hover name strip | `Print_Scanned_String_`, centred (319,467) (colony.cpp:807-816) | |
| buttons | drawn by the field system (`fields::Draw_Visible_Fields_`, colony_main.cpp:176) | |

### Builders: popup (draw root `Draw_Build_Queue_Popup_`, colbldg.cpp:992-1042)

| thing | builder | native position |
|---|---|---|
| backdrop | planet, roads, buildings, then `Interlaced_Gray_Scale_Off_Page_` (:998-1004); `Darken_Fill_(202,304,463,470)` (:1010); frame COLBLDG.LBX 0 at (0,0) (:1011) | |
| title | `"Build List for %s"` in (235,309,194,17) (:1013-1018) | |
| buildings list | array `Calculate_Building_Array_`: Trade Goods, Housing, then every building with `Colony_Can_Build_Product_ == 1` except Colony Base, qsorted by name (:161-178). Drawn by `Draw_Buildings_List_` at x 13, y `20+i·(19-squish)`, width 171, dim when not queued (:665-692) | |
| ships / other list | array `Calculate_Military_Array_`: colony base, freighters, colony/outpost/transport, separator, 5 designs, doom star, separator, farmer/worker/scientist/spy (:180-264). Drawn by `Draw_Militarys_List_` at x 485, width 138 (:611-663) | |
| queue | `Draw_Build_Queue_`: 7 rows centred at x 332, y `335+20·i`, width 251, `"delete %s"` on hover (:708-755) | |
| selection panel | `Draw_Current_Selection_`: hovered product, else `_current_item[0]` (:822-986). Name x 306 y `21+13n`; `Draw_Cost_And_Time_Info_` (:1115-1174); description `Print_App_Description_(209,119,248,…)` from HELP.LBX (:1056-1076); ship info `(212,114,248,186)` (:1214); picture centred (244,56) or clipped (203,9)-(285,103) (:1108-1113) | |
| selection box | `Draw_Active_Prod_`: `Box_(207, 332+20·i, 252, 16)` or a building-row box at x 8 (:1792-1851) | |

---

## 2. Field lists in build order, and what reaches each field

Engine facts behind the "reach" column:
- The early exit returns an activated id before any mouse code runs (fields.cpp:167-177).
- A type-1 toggle happens only inside `Interpret_Mouse_Input_` (fields.cpp:1292-1298, :1479-1485).
- A type-6 value is written from the pointer by `Find_Bar_Position_` (fields.cpp:1702, via :2839).
- A key resolves to the FIRST field whose hotkey matches, scanning from index 0 (fields.cpp:2608-2613).
- `Add_Hot_Key_` fields are type 7 at (5000,5000) (fields.cpp:241-245).
- `Add_Multi_Hot_Key_Field_` fields are type 8 at (-1,-1) with hotkey 0 (fields.cpp:634-639).

### 2a. SCREEN_COLONY: `COLONY::Update_Fields_` (colony.cpp:1405-1436)

It is rebuilt after every non-zero input (colony_main.cpp:329-330).

Let **M** = the number of `military[i] > 0` (colony_main.cpp:1253-1269). Let **P** = the number of
occupied planet slots in the displayed star (colsysdi.cpp:194-224). Then `b = 4 + M + 2P`.

| # | array slot | builder line | type | rect | hotkey | handler | reach |
|---|---|---|---|---|---|---|---|
| 0 | — | Clear_Fields_ | — | stale | — | — | never read |
| 1-3 | `_job_fields[0..2]`, mode 0 | coldraw.cpp:409 | **6** | (310, 62+30i)-(518, 92+30i) | — | pick-up: `Get_Selected_Pop_` mode 3 reads the scroll value (colony.cpp:1510-1518, coldraw.cpp:361) | **cannot be driven**: the value comes from the pointer (fundament §3). Use `MSG_SET_JOBS` (ext_api.cpp:566). |
| 1-3 | same, mode 1 (cluster held) | colony.cpp:1681-1690 | 7 | (310, 60+30i)-(510, 88+30i) | — | drop: `Send_Cluster_(colony, i)` (:1524-1531) | ACTIVATE_FIELD |
| 4.. | `_military_fields[i]`, only if `military[i]>0` | colony_main.cpp:1265 | 7 | (x·step, 479-h)-(…-1, 479); h from art | — | `NEWPUP::Troop_Popup_` (colony.cpp:2040-2044) | ACTIVATE_FIELD |
| .. | `_sys_disp_planet_fields[i]` | colsysdi.cpp:215 | 7 | around (22, 38+24k) ± art/2 | — | switch colony, or `Send_Cluster_(target,-1)` while a cluster is held (colony.cpp:1794-1824) | ACTIVATE_FIELD |
| .. | `_sys_disp_summ_fields[i]` | colsysdi.cpp:220 | 7 | (x+w/2+17, …)-(113, …) | — | `_drawing_display=2`, then a planet description box on the next frame (colony.cpp:1825-1831, :1861-1866) | ACTIVATE_FIELD |
| b | `[2]` | colony_main.cpp:984 | 7 | 5000 | ESC | maps to `[1]` (:1181-1183) | ACTIVATE_FIELD or key |
| b+1 | `[6]` | :985 | 7 | 5000 | `<` | `Get_Next_Colony_(…,0)`, i.e. index **+1** (:1152-1157; colony.cpp:1633-1635) | ACTIVATE_FIELD |
| b+2 | `[7]` | :986 | 7 | 5000 | `>` | index **-1** (:1174-1179) | ACTIVATE_FIELD |
| b+3 | `[19]` | :988 | **8** | -1 | "CRUNCH" | **cheat**: `production_spent = cost`, marks the player as cheated (:1167-1173) | **never send** |
| b+4 | `[20]` | :989 | **8** | -1 | "TOGGLE" | cheat toggle (:1159-1166) | **never send** |
| b+5 | `[1]` RETURN | :991 | 0 | (556,459)+art | 0 | loop break (:350) | ACTIVATE_FIELD |
| b+6 | `[5]` | :992 | 7 | 5000 | **C** | `Col_Calc_Wrapper_`, or `Do_Cheats_` when `_cheats` (:1106-1114) | ACTIVATE_FIELD |
| b+7 | `[17]` officer, no officer | :995 | 0 | (556,427)+art | L | SCREEN_OFFICERS (:1043-1048) | ACTIVATE_FIELD |
| b+7 | `[17]` officer present | :998 | 7 | (550,357)-(623,445) | L | same | ACTIVATE_FIELD |
| b+8 | `[12]` morale | :1001 | 7 | (310,32)-(510,61) | — | `Show_Morale_` text box (:1116-1120) | ACTIVATE_FIELD |
| b+9 | `[13]` BC | :1002 | 7 | (128,32)-(301,61) | — | `Show_BC_Production_` (:1122) | ACTIVATE_FIELD |
| b+10 | `[14]` food | :1003 | 7 | (128,62)-(301,91) | — | `Show_Food_Production_` | ACTIVATE_FIELD |
| b+11 | `[15]` industry | :1004 | 7 | (128,92)-(301,121) | — | `Show_Industry_Production_` | ACTIVATE_FIELD |
| b+12 | `[16]` research | :1005 | 7 | (128,122)-(301,151) | — | `Show_Research_Production_` | ACTIVATE_FIELD |
| b+13 | `[4]` CHANGE | :1008 | 0 | (519,123)+art | C (**shadowed**, below) | SCREEN_QUEUE_POPUP (:1146-1149) | ACTIVATE_FIELD |
| b+14 | `[18]` autobuild | :1009 | 7 | (525,26)-(630,37) | A | toggle, or preset prompt (:1079-1094) | ACTIVATE_FIELD |
| b+15 | `[3]` BUY | :1012 / :1018 | **0 when buyable, 7 otherwise**, same rect | (590,123)+art | B | `Tested_Colony_Buys_Outright_`: confirmation or refusal box (:1096-1104; :740-803) | ACTIVATE_FIELD |
| +1 opt | `[8]`, only if `occupation_policy==0` | colony.cpp:1766 | 7 | (0,0)-(639,19) | 0 | `Occupation_Policy_Popup_` (colony_main.cpp:1036-1041) | ACTIVATE_FIELD |
| +1 opt | `[11]`, only while a pop is unassigned | colony.cpp:1778 | 0 | (307,159)+art | 0 | `COLXPORT::Xport_Popup_` (colony_main.cpp:1068-1077) | ACTIVATE_FIELD |
| +n | `_colony_satellite_fields[i]` | colony.cpp:1754 | 7 | (295±50i, 162)+art | 0 | scrap confirmation; `-id` opens an info box (:1582-1613) | ACTIVATE_FIELD |
| +n | `_colony_bldg_fields[r*6+c]`, occupied cells, diamond order (colony.cpp:1699-1705) | :1717 | 7 | centre ±20 x, -30/+10 y, centre from `_building_cr` (:2273-2282) | 0 | demolish confirmation; `-id` opens an info box (:1932-2028) | ACTIVATE_FIELD, **but see below** |
| last | `[0]` | colony_main.cpp:1030 | 7 | (0,0)-(639,479) | 0 | building lookup by POINTER polygon (colony.cpp:1950-1953) | **never send** |

**Unreachable in 1.60.0: the galaxy-map inset.** `_colony_fields[9]`/`[10]` are set to -1000
(colony_main.cpp:981-982) and never assigned again. `_sys_disp_fields[0]` is only ever set to
-1000 (colony.cpp:559). The inset branch (`_drawing_display = 1`) sits behind exactly those
comparisons (colony_main.cpp:1051-1056, colony.cpp:1790-1792), so no input reaches it.

**Where the loop IGNORES or MISROUTES injected input** (source reading, none driven):
- **Pop pick-up**: type 6, and the value comes from the pointer. Same shape as the colony summary
  (fundament §3). The drop is by id.
- **Buildings**: `Check_Bldg_Fields_` walks the 6×6 grid in (row, col) order and, for each cell,
  RETURNS as soon as the scan test matches: `field_val == scan_field` OR the **real pointer** lies
  inside that cell's polygon (colony.cpp:2014-2024; pointer read at :1936-1937).
  - An `ACTIVATE_FIELD` on building k is **swallowed** whenever the real pointer rests over a
    building that comes earlier in the walk.
  - An `ACTIVATE_FIELD` on `[0]` opens the **demolish confirmation for whatever building the real
    pointer is over** (:1950-1976).
- **Hover-only state** (`_scanned_pop`, `_scanned_bldg_C/R`, `_scanned_military`,
  `_scanned_satellite`, the popup's `_scanned_prod`) comes from `Scan_Input_` and the real pointer
  (colony_main.cpp:338, colbldg.cpp:526). It cannot be injected.
- **Key C**: `[5]` (b+6) is built before `[4]` (b+13), and both carry hotkey `C` (E 213 is `c`,
  uppercased by `Add_Hot_Key_`/`Add_Button_Field_`, fields.cpp:247-251, :372-375). A C keypress
  therefore resolves to `[5]` (recalculate), **not** CHANGE. NOT SETTLED live.
- **Modal refusals**: every `GENDRAW::Help_`, `Confirmation_Box_` and `TEXTBOX::Text_Box_` on this
  screen is a modal loop (fundament §3). The count differs by entry path:
  - The screen shows up to four informational boxes BEFORE its main loop:
    `Do_Informational_And_Decision_Popups_` (colony_main.cpp:323; colony.cpp:996-1055).
  - A colony that just finished something opens straight into a box.

### 2b. SCREEN_QUEUE_POPUP: `COLBLDG::Update_Fields_` (colbldg.cpp:343-377)

It is rebuilt on every `Do_Draw_Build_Queue_` (:1966-1971).

| # tactical (strategic) | slot | line | type | rect | hotkey | handler | reach |
|---|---|---|---|---|---|---|---|
| 1 | `[0]` Cancel | :346 | 0 | (493,447)+art COLBLDG 1 | 0 | exit without commit, scraps new ships (`Remove_Ships_(0)`, :1540-1576) | ACTIVATE_FIELD |
| 2 | `[3]` OK | :347 | 0 | (560,447)+art 3 | 0 | commit `Do_Exit_Screen_Cleanup_` (:1487-1539; :2003-2016) | ACTIVATE_FIELD |
| 3 | `[1]` | :349 | 7 | 5000 | ESC | same as Cancel | ACTIVATE_FIELD |
| 4 | `[8]` | :350 | 7 | 5000 | `<` | commit, then next colony; stays on 25 (:1622-1631) | ACTIVATE_FIELD |
| 5 | `[9]` | :351 | 7 | 5000 | `>` | previous colony, then commit (:1632-1641) | ACTIVATE_FIELD |
| 6 | `[10]` | :352 | 7 | 5000 | B | commit, then buy (:1615-1621) | ACTIVATE_FIELD |
| 7 | `[2]` autobuild | :354 | **1** | (490,342)+art 2 | 0 | radio on `_colony_auto_building`. With `autobuild_settings.enabled` there is also an id branch (:1465-1485) | **INJECT_CLICK** (id branch only when enabled) |
| 8 (—) | `[4]` Refit | :360 | 0 | (492,379)+art 4 | R | `Colony_Refit_Popup_` (:1583-1613) | ACTIVATE_FIELD |
| 9 (—) | `[5]` Design | :361 | 0 | (561,379)+art 5 | D | `_field_mode=1` (pick a design) (:1577-1579) | ACTIVATE_FIELD |
| 10 (8) | `[6]` Repeat | :364 | 0 | (503,411)+art 6 | E | `_field_mode=2` (:1580-1582) | ACTIVATE_FIELD |
| 11-21 (9-19) | `_build_queue_hotkeys` | :367-372 | 7 | 5000 | Q,1..9,0 | orion2re preset: commit + apply (:379-396) | ACTIVATE_FIELD |
| 22-28 (20-26) | `_queue_fields[0..6]` | :323-341 | 7 | (207, 329+20i)-(458, 350+20i) | 0 | select/move/delete (:1720-1780) | ACTIVATE_FIELD |
| 29.. (27..) | `_building_fields[i]` | :299-321 | 7 | (13, 20+i·s)-(184, 19+(i+1)·s), s=19 while n≤23 | 0 | toggle in queue (:1649-1679) | ACTIVATE_FIELD |
| then | `_military_fields[i]` | :266-284 | 7 | (485, 20+i·s)-(623, …), s=19 while n≤15 | 0 | add, or pick a design in mode 1 (:1681-1718). Separators are ignored | ACTIVATE_FIELD |

- `[4]`/`[5]` exist only when `strategic_combat_flag == 0` (:356-362). `[7]` is -1000 (:365).
- Total fields = **29 + n_b + n_m**, or 27 under strategic combat. `n_b ≥ 2` (:162-164).
- Squish comes from `Calculate_Squish_Step_` (coldraw.cpp:12-34) with (13, 469, n, 19) for buildings
  and (13, 308, n, 19) for ships.
- Nothing in this input loop reads the pointer to route a click. Only the hover display
  (`_scanned_prod`) and the mouse picture do.
- **The loop recalculates the colony every frame**: `selected_field_id != nullptr` is always
  true (:1787-1789).

---

## 3. Every displayed value: on the wire or not

STATE layout is `SerializeState`, ext_api.cpp:92-241. Colonies are whole `s_colony` (:139),
players whole `s_player` (:121), stars whole (:127), ships whole (:133), planets 5 per star (:146),
leaders 67 raw (:157), settings whole (:117). `MOX::_screen_data`, all `COLONY::` and `COLBLDG::`
globals, `EVENTS::_event_data` and `BUILD_QUEUE::autobuild_settings` are **not** serialized
(absent from :92-241).

"V" = field in a `verified=True` spec (colony.py:228, planet.py:126, star.py:51, player.py:121,
ship.py:130, settings.py:55). Colony offsets are header-verified. Value second sources are as
colony.py records them.

| value shown | source member | wire | spec state |
|---|---|---|---|
| which colony (star + orbit) | `_screen_data`, `_orbit_temp`, `_colony_handle` | **NOT** | — |
| title specialty / annihilate | `specialty` @11, `occupation_policy` @303 | STATE colonies | V (colony.py:186, :222) |
| planet name | `HACCESS::Get_Planet_Name_` (haccess.cpp:236) over star name | star `name` @0 | V (star.py:35); the roman-numeral rule is NOT SETTLED (not read) |
| "Blockaded" | star `blockaded` @162 bit `_PLAYER_NUM` | STATE stars | V (star.py:44) |
| "Plague" / "Pop Boom" | `EVENTS::_event_data[…]` (events.cpp:131-150) | **NOT** | — |
| Pop k, growth | `pop[]` @12 assigned bit, `pop_roundoff` @180, `pop_growth` @200 | STATE | V; `pop_growth` value-verified; `MASK_ASSIGNED` not live-verified (colony.py:248-254) |
| production icons | `production` @231, `maintenance` @239, `imports` @243, `pollution` @8 | STATE | V layout; the icon arithmetic is coldraw.cpp:36-181, to transcribe |
| morale icons | `morale` @7; government `traits[0]` at player+2308 | STATE | morale NOT value-verified (colony.py:88); traits a constant (player.py:124) |
| pop icons | `pop[]` prof / nibble / conquered, `n_pops` @10, `max_farms` @224, player `race` @37 | STATE | prof and nibble 9 verified; 8 and conquered not (colony.py:253, :270, :289) |
| system display planets | star `planet_index[5]` (orion2.h:3006, **offset 195** by header arithmetic) | STATE stars | **not in star.py**; derivable from planet `star_index`/`orbit` (planet.py:111-112, V) |
| planet climate/size/gravity/mineral, colony climate, max pop | planet.py:113-119; colony `climate` @226; `Planet_Max_Population_For_Player_` | STATE | V; max pop derived (fundament §3) |
| owner race name | player `race_name` @21 | STATE | V (player.py:96) |
| current product id | `producing[0]` @277 | STATE | V |
| product name | `TECHDATA::_buildings[].name`, ship `d.name` @0, `Option_String_` (colbldg.cpp:2338) | ship name on wire; tables in source | V for the ship (ship.py:96) |
| production bar, cost, turns | `production_spent` @293, `bought_outright` @300, `Colony_Product_Cost_` (colcalc.cpp:2576), `Colony_N_Turns_To_Produce_` (:1549) | inputs partly | building cost is a source table (techdata.cpp:25), ship `d.cost` @94 V (ship.py:107); **`ship_designs` not in player.py**; `lander_ship_cost` is config (config.cpp:3340), **NOT** |
| autobuild label | `auto_building` @297 plus `autobuild_settings.enabled` (config.cpp:9621-9625) | byte yes, setting **NOT** | V byte |
| BUY available | `[3]` type 0/7 in FIELD_LIST; or `bc` @50, `Production_Cost_To_Buy_` (colcalc_base.cpp:13-31), blockade, `bought_outright` | FIELD_LIST and STATE | bc V (player.py:104) |
| officer present / name / ETA | star `officer_index[8]` (offset 187), leader `name`/`eta` | STATE raw | star member **not in spec**; `s_leader_data` **unverified** (unverified.py:28-36); presence also visible as `[17]` type 0/7 |
| military counts | `military[2]` @304; names `TECHDATA::_units` | STATE | V |
| buildings present | `buildings[49]` @310 | STATE | V |
| **building placement** | `Make_Bldg_Array_For_Colony_` with `game_random` seeded by the colony index (colony_main.cpp:537-538, :651-652, :591-597) | **NOT**; the occupied cells' rects ARE in FIELD_LIST | — |
| satellites | `buildings[]` with `type==7`; rects in FIELD_LIST | STATE and FIELD_LIST | V |
| entry messages | `just_produced` @291 | STATE (cleared on show, colony.cpp:1024) | V |
| demolish-once rule | `last_turn_building_destroyed` @359 vs stardate (header @3) | STATE | V |
| hover strings | `_scanned_*` | **NOT** | HD-local |
| popup: queue being edited | `COLBLDG::_current_item[7]` | **NOT until commit** (colbldg.cpp:2009-2011) | `producing` shows the pre-popup queue |
| popup: queued new ships | `MOX::_ship[]` created with status 6 at once (colbldg.cpp:1348-1360; may raise `_NUM_SHIPS`, :422-424) | STATE ships | status V (ship.py:111) |
| popup: building list and order | `_building_indexes` (`Colony_Can_Build_Product_==1`, sorted by name) | **NOT**; count = FIELD_LIST rows at x 13..184 | — |
| popup: ships/other list | `_military_indexes` | **NOT**; count = rows at x 485..623 | — |
| popup: selection box, mode, radio | `_active_prod`, `COLBLDG::_field_mode`, `_colony_auto_building` | **NOT** | — |
| popup: cost / maint / build time / turns left | colbldg.cpp:1115-1174 | derived as above | label `HESTR_16F_PENALTY` is really `"Maint. Cost: %d"` (E 367) |
| popup: descriptions | HELP.LBX record by `tech_app` (:1056-1076), `Print_Setting_Description_` (:1044) | not on wire; HELP extractor exists | — |
| popup: ship design stats | `ship_designs[i]` / `ship.d` (:1205-1303) | ships V; designs **not in spec** | — |
| `strategic_combat_flag`, `language`, `auto_delete_tg_housing` | `s_settings` | STATE settings | only `auto_delete_tg_housing` is in settings.py (:46); the other two are **not** |

---

## 4. Screen ID reported while up

- `ext::Tick` runs from `Screen_Control_` with the id about to be dispatched (mox2.cpp:41) and from
  every `Get_Input_` with `MOX::_current_screen` (fields.cpp:167). STATE offset 0 is that value
  (ext_api.cpp:98).
- **Colony screen: 1** for its whole loop. So are all its modals (text boxes, confirmations,
  occupation/transport/troop popups, autobuild input box), because none of them changes
  `_current_screen`. The report.cpp:742 path CALLS `Colony_Screen_`, but sets 1 first (:733).
- **Queue popup: 25.** It is a switched screen (mox2.cpp:140-143), not a call. Its modals (refit
  popups, confirmations, the preset prompt) also report 25. When it was opened from the colony
  summary it returns to 20.
- **Colony change (`<`/`>`, system display) keeps id 1.** In the popup it keeps id 25. **No
  `EVT_SCREEN_CHANGED` fires**, and FIELD_LIST is re-sent only if the count changed or a client
  reconnected (ext_api.cpp:671-672; ext_server.cpp:194). Two colonies with the same field count
  switch with **nothing on the wire but the framebuffer**.
- `MOX::_PLAYER_NUM` at STATE offset 7 is the colony owner while screen 1 is up
  (colony_main.cpp:284). It equals the local player on every entry path read here (e.g.
  mainscr.cpp:1571).

---

## 5. What would need an Extension API patch (DESCRIBE ONLY)

**P1: which colony, and the screen-local modes.**
- Carries: `COLONY::_colony_handle` (int16), `_drawing_display` (u8), `COLONY::_field_mode` (u8).
  On 25 it also carries `COLBLDG::_current_item[7]`, `_active_prod[0]`, `COLBLDG::_field_mode`,
  `_colony_auto_building`.
- Where: a trailing optional STATE block in `src/ext/ext_api.cpp` `SerializeState`, after "FSEL"
  (:197-240), same pattern as open fix 20.
- Why nothing reaches it:
  - `_screen_data`/`_orbit_temp` are not serialized.
  - `last_planet_selected` is written only on colony switches (colony.cpp:1567, :1820), not on
    entry from the galaxy map or colony summary (mainscr.cpp:1583-1589, colsum.cpp:916-919), and
    it names an orbit without a star.
  - Game-initiated entries (reports, info, turn summary, landing) cannot be predicted by a client.
  - Decision 25 applies in part: `Get_Next_Colony_` is a pure function of `owner`/`outpost_flag`
    (colony.cpp:1628-1656), so `<`/`>` could be tracked **from a known start**. The start is the
    part that is missing.
  - The queue under edit exists only in `_current_item` until commit (colbldg.cpp:2003-2016).

**P2: the popup's two product lists (optional; reconstruction is possible).**
- Carries: `_n_building_indexes` plus `_building_indexes[]`, `_n_military_indexes` plus
  `_military_indexes[]`.
- Where: the same block.
- Why: the building filter is `Colony_Can_Build_Product_ == 1` (colcalc.cpp:2916 onward, long, over
  `tech_applications`, `traits`, other colonies' queues). It is then sorted by the language's
  building names (colbldg.cpp:152-177).
  - A client copy is possible and has a validation (the FIELD_LIST row counts), but the counts
    check membership size, not order. That is a second copy of a large rule. Data decides.

**P3: the status word (optional).**
- Carries: plague and population-boom `status`/`target_id` from `EVENTS::_event_data`.
- Where: `ext_api.cpp`.
- Why: not in any serialized block. The only other route is the framebuffer.

**P4: building placement (optional).**
- Carries: `COLONY::_colony_bldgs[6].buildings[6]` and `_colony_satellites[10]`.
- Why: placement uses `game_random` seeded with the colony index plus `Random_` draws
  (colony_main.cpp:537-631). A client would have to transcribe the RNG exactly.
- FIELD_LIST gives the occupied cells' rectangles, but not which building sits in each.

**Not needed as patches, only as spec work (decision 23):**
- star `officer_index` (offset 187) and `planet_index` (195) in star.py;
- `s_player.ship_designs`, `tech_applications` decoding, `ship_range`/`ship_speed`;
- `s_settings.strategic_combat_flag`/`language`;
- `s_leader_data`.

**Config values not on the wire:**
- `autobuild_settings.enabled` (config.cpp:9621) changes the label (colony_main.cpp:961-974), the
  `[18]` and radio semantics (:1080-1091, colbldg.cpp:1465), and whether OK commits the radio
  (colbldg.cpp:8-13).
- `lander_ship_cost` (config.cpp:3340) feeds colony/outpost/transport ship costs
  (colcalc.cpp:1489-1503).
- Whether HD must know either is a question (§8).

**A command instead of popup driving (question, not request):**
- A `MSG_SET_QUEUE`-style command would bypass `_current_item`.
- But queue entries for ships CREATE ship records (colbldg.cpp:2093-2100) and refit ships carry
  confirmations (:2170-2175), so it would be a larger handler than `Set_Jobs_`.
- **Pop moves need no patch here**: `Set_Jobs_` accepts any colony the player owns
  (ext_api.cpp:360-386).

**Injection gap noticed on the way:** `MSG_CANCEL_FIELD` pushes right-button events without setting
`g_injected_mouse_pending` (ext_api.cpp:586-615; compare :536). Its position is therefore exposed
to the pointer re-sync that the click path guards against. NOT SETTLED live.

---

## 6. Right-click help

| screen | table | entries | installed by | called from |
|---|---|---|---|---|
| colony | `_colony_screen_help_list` erichelp.cpp:90-108 | 17 | `Set_Colony_Screen_Help_List_` :149 | colony_main.cpp:192, :272 |
| queue popup | `_colony_building_queue_screen_help_list` erichelp.cpp:49-63 | 13 | `Set_Building_Queue_Screen_Help_List_` :141 | colbldg.cpp:488, :514 |

Rectangles are `{id, x1, y1, x2, y2}` (orion2.h:993-999).

**Colony table, first match wins:**
- 484 status (1,1)-(120,14); 485 name (122,1)-(506,15); 486 pop (508,1)-(638,15)
- 487 system display (7,24)-(115,151); 488 current production (526,27)-(632,112)
- 489 BC (124,29)-(304,57); 490 morale (307,29)-(512,56)
- 492/493/494 farmers/workers/scientists (125,59/88/118)-(305,88/118/148); 495 jobs (307,59)-(512,148)
- 496 units (1,443)-(176,478); 497 change (520,124)-(578,143); 498 buy (591,124)-(625,143)
- 499 leaders (552,425)-(638,448); 500 return (551,455)-(638,478)
- 483 general (0,0)-(639,50), last

491 "Jobs Output" is not referenced.

**Popup table:**
- 501 buildings list (13,9)-(184,469); 502 picture (203,9)-(285,103); 503 summary (302,10)-(462,103)
- 504 ships list (482,10)-(626,308); 505 description (204,114)-(461,302); 506 queue (207,332)-(458,465)
- 507 auto build (490,342)-(623,363); 508 refit (492,379)-(552,397); 509 design (561,379)-(621,397)
- 510 repeat (503,411)-(615,431); 537 cancel (493,447)-(554,465); 511 ok (560,447)-(623,465)
- 512 general (1,1)-(638,478)

All ids 483-512 and 537 are present in `assets/shared/help/help_en.json`. The help anims for
497-500 name COLPUPS.LBX 1/2/21/4, which agrees with `_c_anims[19,20,32,21]` = COLPUPS 1/2/21/4
(colony_main.cpp:397-403).

**Right click outside a help rectangle is NOT -1 here.**
- `Disable_Cancel_` runs on galaxy map entry (mainscr_main.cpp:281). The only writer of
  `_mouse_cancel_disabled` is fields.cpp:113, and nothing clears it. So in a running game a right
  click returns `-field_idx` (fields.cpp:1360, :1513).
- Colony screen: a right click on a building or satellite outside the help table opens that
  building's **info text box** (colony.cpp:1990-2010, :1608-1613).
  - Over empty landscape it hits `-[0]`, and the pointer polygon test decides (:1992-1996).
  - Most of the landscape (y 151-442) is outside every help rectangle.
- Popup: entry 512 covers everything but the 1-px border, so a right click shows help.
  `Evaluate_Input_` has no negative-id branch.

---

## 7. Layout under one provisional content box

**Verdict: neither screen fits the draft rule as "one coherent content region". Both are
several regions fixed to their frame artwork at native 640×480.**

**Colony screen.** It is a full-bleed scene plus an overlay band, not a framed content area:
- The **landscape** and the building grid cover the whole screen. Backdrop at (0,0)
  (colony_main.cpp:111-115). Building anchor points run x -21..666, y 288..492, past the canvas
  on three sides (colony.cpp:4-20). Satellites sit at y 162 (colony.cpp:652).
- The **top band** (0,0)-(640,150) is itself artwork, COLPUPS.LBX 5/6 (colony.cpp:623-632), with
  holes that fix its sub-regions:
  - system display (7,24)-(115,151)
  - production x 128..301, rows at y 32/64/94/124
  - pop and morale x 310..510
  - current-production window (517,17)-(639,158), which overhangs the band by 8 px (colony.cpp:779)
- **Bottom-right cluster**: officer frame (544,351), officer/leaders button (556,427), RETURN
  (556,459) (colony.cpp:714; colony_main.cpp:991-995).
- **Bottom-left**: the unit strip, y `479-h`, x 0..~260 (colony_main.cpp:1222, :1279).
- **Hover strip** centred (319,467..478) (colony.cpp:813-815).

The only single box that contains all of this is (0,0)-(639,479) itself. Under the rule that
degenerates to "scale the screen". The band's sub-regions still move with COLPUPS art, not with a
box.

**Queue popup.** One frame (COLBLDG.LBX 0 at (0,0), colbldg.cpp:1011) with six fixed holes:
- buildings list (13,9)-(184,469)
- picture (203,9)-(285,103)
- summary x 306.., y 21+13n (up to 462)
- description / ship info (204..461, 114..302)
- queue (202,304)-(463,470), darkened (:1010), with rows (207,329)-(458,470)
- ships list plus buttons (482..626, 10..465)

They are side by side, so there is no inner content region distinct from the frame. Hanging them
from one box is possible only as the full popup rectangle, and every hole would still be a
per-region offset inside it.

The native rectangles that decide it are the ones listed above.
`doc/colony_inset_geometry.md` was not read for this report.

---

## Seen on the way (source reading, not driven)

- **Key naming is inverted relative to the arrows.** `<` takes the next index (+1) and `>` the
  previous one (colony.cpp:1633-1645). The previous-colony wrap sets `search_idx = _NUM_COLONIES`,
  one past the last record (:1642-1643, marked BUG in the source).
- **`<` and `>` differ in the popup.** `<` commits and then switches (Cleanup runs on the committed
  queue, colbldg.cpp:1626-1630). `>` switches first, so `Cleanup_Colony_Queue_` runs on the
  pre-commit `producing`, and then commits (:1634-1640). A queue emptied in the popup and left by
  `>` may keep `producing[0] = NONE`.
- **Two turn formulas.**
  - The colony screen's `"%d turn(s)"` is `ceil((cost-spent)/(industry-maintenance))`
    (colcalc.cpp:1549-1573).
  - The popup's "Build Time" is `cost/industry + 1`, with neither spent nor maintenance
    (colony.cpp:422-440).
- **The population figure excludes held pops.** `Sum_Colonists_` counts only the assigned bit
  (colony.cpp:2138-2140), so the title number drops while a cluster is held.
- **Mislabelled comments.** `HESTR_16F_PENALTY` prints "Maint. Cost: %d". The comment `"x %d"` at
  colony_main.cpp:1241 is ":%d" in the English ESTRINGS.
- **Squish mismatch in the popup.** `Draw_Active_Prod_`'s building-row box uses the squish left by
  `Draw_Militarys_List_` (colbldg.cpp:1037-1041, :1840-1846). It is visible only when the two
  lists squish differently.

---

## 8. Questions for Data before a build can start

1. Screen 25 is a switched screen reached from 1 and from 20: is it its own HD screen or an overlay?
2. Which colony is shown: patch P1, or HD tracks the entries it starts and falls back to the framebuffer otherwise?
3. Queue edits: drive the popup by ACTIVATE_FIELD (the edit is invisible until OK), or ask for a queue command?
4. Building and ship lists: transcribe `Colony_Can_Build_Product_` plus the name sort, or carry the arrays (P2)?
5. Building placement is RNG-seeded per colony: transcribe `game_random`, carry the grid (P4), or use an HD layout marked as an extension?
6. Pop moves on this screen go through `MSG_SET_JOBS` as on the colony summary. Agreed?
7. Key C reaches recalculate, not CHANGE (source reading): verify live first, then transcribe or mark a deviation?
8. CRUNCH/TOGGLE (type 8) and `[0]`: add a hard guard so HD never activates them on screen 1?
9. Building demolish and right-click info boxes: offered in HD (modal confirmation), or view-only for now?
10. orion2re's autobuild presets (Q/0-9, "Auto Build Queue n"): in scope, and is `autobuild_settings.enabled` needed on the wire?
11. `strategic_combat_flag` removes Refit/Design and shifts every popup index by 2. May settings.py gain that byte as a verified field?
12. The galaxy-map inset branch is unreachable in 1.60.0: omit it from HD?
13. The Plague/Pop Boom status word is not on the wire: patch P3, or omit and mark?
14. Under the draft single-box rule, does a full-bleed screen count as "one box = 640×480", or is it exempt?
