# The GAME menu tree — source reading (work order Stop 1)

14 September 2026. orion2re 1.60.0, `~/orion2re/src`. **No code was
written for this stop.** Every line number below was read in that tree
on this date; every field list marked *measured* was taken from the
running game (see "Live steps"). Anything marked *source reading* was
not driven.

---

## 1. The button

| what | where |
|---|---|
| field | `MAINSCR::Add_Map_Fields_`, mainscr.cpp:1389 — `_game_button = fields::Add_Button_Field_(249, 5, "", MOX::_main_game_button_seg, "G", 0x29)` |
| on the wire | galaxy map field **6**, `(249,5)-(307,21)`, type **0** (`FIELD_TYPE_BUTTON`, orion2_consts.h:205), hotkey `G` — *measured*, matches `doc/ext_api_dokumentation_v3.md` |
| handler | `MAINSCR::Main_Screen_` loop, mainscr_main.cpp:609-614: `_current_screen = SCREEN_GAME; exit_flag = 1; _screen_data = 0; _return_screen = SCREEN_MAIN` |
| dispatch | mox2.cpp:67-70 — `case SCREEN_GAME: LOADSAVE::_Game_Popup_()`; `SCREEN_GAME = 8` (orion2_consts.h:468) |
| ACTIVATE_FIELD | **reaches it.** Type 0, and the handler compares the field id (decision 20; fields.cpp:168-177 early exit). *Measured*: activating field 6 moves the game to screen 8 with the menu's 11 fields. |

**What HD does today.** The title cutout already sends `ACTIVATE_FIELD 6`
(`screens/galaxy_map/screen.py:576-584`, `layout.json` `actions.game_menu`),
and id 8 has no HD screen (`core/screen_names.py:41`), so the dispatcher
falls back to the original framebuffer. Clicking GAME in HD opens the
NATIVE popup now.

## 2. One screen id, four dialogs, each with its own input loop

`LOADSAVE::_Game_Popup_` (loadsave.cpp:1527-1620) is the whole tree.
It snapshots settings, loads the artwork (`Load_Game_Popup_Pictures_`,
:1174), then loops: clear fields, `Add_Game_Popup_Fields_` (:176-293)
builds the field list for `MOX::_screen_data`, and a `switch` runs one
of four dialog functions until `exit_condition` is set (:1554-1586).

| `_screen_data` | dialog | builds (`Add_Game_Popup_Fields_`) | input loop | draws |
|---|---|---|---|---|
| 0 | game menu | case 0, :181-203 | `Do_Main_Game_Popup_` :1222 | `_Draw_Main_Game_Popup_` :1334 |
| 1 | settings | case 1, :204-221 | `Do_Options_Game_Popup_` :412 | `_Draw_Options_Game_Popup_` :1424 |
| 2 | load | case 2, :223-266, :284 | `Do_Load_Game_Popup_` :298 | `_Draw_Load_Save_Game_Popup_` :794 |
| 3 | save | case 3, :223-256, :267-284 | `Do_Save_Game_Popup_` :470 | `_Draw_Load_Save_Game_Popup_` :794 |

Every dialog appends the same two fields last (:291-292): a hidden field
over the popup body and a hidden **whole-screen field with hotkey ESC**.

**Every loop calls `fields::Get_Input_()`, so the server talks
throughout** (section 3 of the fundament; `ext::Tick` at fields.cpp:167).
The confirmation box (its loop ends at gendraw.cpp:212) and the warning
box (gendraw.cpp:141-148) run their own `Get_Input_` loops too. The silent
stretches are the slide animations (`Animate_Game_Popup_`, :968-1039,
no `Get_Input_`) and `FILEDEF::Load_Game_`.

**The dialog is not on the wire.** The snapshot reports screen 8 for all
four; `_screen_data` is not serialized. Only the FIELD_LIST shape says
which dialog is up — and in a single-player game every node has a
distinct count (below).

## 3. The tree

One line per node, with the function that BUILDS it.

- **Galaxy map — GAME button** — `MAINSCR::Add_Map_Fields_` mainscr.cpp:1389
  - **Game menu** (`_screen_data` 0) — `Add_Game_Popup_Fields_` case 0, loadsave.cpp:181-203
    - **SAVE GAME** → **Save dialog** (3) — `Add_Game_Popup_Fields_` :267-284
      - **slot name input** — type-11 field per slot (:274) plus the hidden strip under it (:279) that starts editing (:506-521)
      - *"Save Game function disabled"* (H 185) — `Game_Popup_User_Box_(…, 0)` → `GENDRAW::Message_Box_` → `TEXTBOX::Do_Text_Box_` (loadsave.cpp:1296-1301, gendraw.cpp:18, textbox.cpp:175). Only while `MOX::_disallow_saves_code != 0`; not reachable in this game
    - **LOAD GAME** → **Load dialog** (2) — `Add_Game_Popup_Fields_` :257-266
      - **bad slot warning** — `Bad_Game_File_Message_` (:929) → `Game_Popup_User_Box_(…, 3)` → `GENDRAW::Warning_Box_` → `Message_Box_Exploding_` (gendraw.cpp:90; its one field at :105). Text by slot status: 1 missing (H 178), 2 invalid (H 179), 3 multiplayer (H 180)
      - *load failed* — H 184 through the same warning box (:361-365); `FILEDEF::Load_Game_` has its own invalid-file warning with five language literals (filedef.cpp:128-143)
    - **NEW GAME** → **confirmation** H 186 — `GENDRAW::Confirmation_Box_` gendraw.cpp:153 (fields :172-173)
    - **QUIT GAME** → **confirmation** H 187 — same builder
    - **SETTINGS** → **Settings dialog** (1) — `Add_Game_Popup_Fields_` :204-221
    - **RETURN** — closes the popup
    - **Music / Sound Fx** sliders — type-6 scroll fields (:200-201)

In a multiplayer game (`_game_type` 2 or 3) LOAD GAME and NEW GAME are
not added (:190-193).

The Load dialog is ALSO the main menu's Load (`MAINMENU::Mainmenu_Load_Game_Popup_`,
mainmenu.cpp:187-209, calling `Do_Load_Game_Popup_` under
`SCREEN_MAIN_MENU`) — same builder, centred and on the menu art
(:225-229, :802-805). Out of scope here, but one builder.

## 4. Field lists, per node — measured

Field 0 is the list's dummy. **After a message box it carries stale
geometry** (warning: `(193,185)-(387,197)`; confirmation:
`(173,62)-(388,73)`), so a shape match must never read index 0.

**Game menu — 11 fields.** Order is BUILD order (:188-201), which is not
the visual order:

| # | rect | type | hotkey | art (GAME.LBX) | does (`Do_Main_Game_Popup_`) |
|---|---|---|---|---|---|
| 1 | (291,68)-(381,95) | 0 | L | LOAD GAME, entry 2 | `_screen_data = 2` (:1286-1290) |
| 2 | (184,113)-(274,140) | 0 | N | NEW GAME, entry 3 | confirm H 186; YES → `_game_type = 0`, `_return_screen = SCREEN_NEW_GAME` (:1240-1256) |
| 3 | (184,68)-(274,95) | 0 | S | SAVE GAME, entry 1 | `_screen_data = 3`, or the disabled message (:1291-1302) |
| 4 | (291,113)-(381,140) | 0 | Q | QUIT GAME, entry 4 | confirm H 187; YES → `FILEDEF::Save_Game_(9)`, `active_save_slot = 10`, settings, `SCREEN_EXIT` (:1257-1281) |
| 5 | (184,332)-(274,358) | 0 | O | SETTINGS, entry 5 | `_screen_data = 1` (:1282-1285) |
| 6 | (295,332)-(385,358) | 0 | ESC | RETURN, entry 6 | closes (:1234-1239) |
| 7 | (206,219)-(361,231) | 6 | — | music bar, entry 7 | `Set_Music_For_Game_Popup_` (:1685) |
| 8 | (206,241)-(361,253) | 6 | — | sound bar | `Set_Sound_For_Game_Popup_` (:1711) |
| 9 | (144,25)-(423,403) | 7 | — | popup body | nothing |
| 10 | (0,0)-(639,479) | 7 | ESC | whole screen | closes, with the slide-out when animations are on (:1309-1320) |

**Settings — 30 fields.** 1-26 are 13 pairs of hidden fields at
y = 66 + 17·i: the checkbox `(170,y)-(192,y+12)` and the label
`(193,y)-(387,y+12)`, both toggling `options[i]` (:433-438). 27 ACCEPT
`(241,363)-(315,382)` type 0 hotkey A; 28 body; 29 whole screen ESC.
The frame art has 17 checkbox slots; 13 are used.

**Load — 16 fields.** 1-10 slot rows `(173, 49+31·i)-(370, 73+31·i)`,
type 7; 11 `(629,469)-(639,479)` type 7 hotkey `D` (`debug_hotspot_id`,
:265 — no branch of `Do_Load_Game_Popup_` compares it); 12 LOAD
`(181,362)-(248,383)` hotkey L; 13 CANCEL `(315,363)-(382,383)` hotkey C;
14 body; 15 whole screen ESC.

**Save — 25 fields.** 1-10 name inputs `(170, 49+31·i)-(370, 61+31·i)`
type **11** (`FIELD_TYPE_CONTINUOUS_INPUT`); 11-20 hidden edit strips
`(173, 62+31·i)-(388, 73+31·i)` type 7; 21 SAVE `(181,363)-(248,383)`
hotkey S; 22 CANCEL hotkey C; 23 body; 24 whole screen ESC.

**Confirmation — 3 fields.** 0 stale; 1 YES `(235,302)-(286,323)` type
7 hotkey Y; 2 NO `(345,302)-(396,323)` type 7 hotkey N. The popup's
fields are gone for the duration.

**Warning — 2 fields.** 0 stale; 1 whole screen type 7 hotkey ESC.

What each Load/Save entry does:

- **Load**: a slot row loads THAT slot at once — there is no select-then-LOAD
  step (:332-375). LOAD with no row takes `active_save_slot` (:339-346).
  A slot whose status is not 0 shows the warning and the dialog is
  rebuilt (`exit_loop = 2`, :376-379). Success sets
  `_return_screen = SCREEN_REPORTS` (hotseat: `SCREEN_HOTSEAT_SELECT_PLAYER`),
  :366-369.
- **Save**: the first activation of a row selects it; a second on the
  same row, Enter in its input, or SAVE, saves (:496-536). An empty or
  `... empty slot ...` description becomes `"%s, %s, %d %s"` — player
  name, race name, colony count, H 188/189 — cut at 36 chars (:542-551).
  **After saving, the popup closes entirely** (`*out_should_close = 1`,
  :562) — it does not return to the menu.

## 5. How each node is left

ESC as a KEY resolves to the FIRST field whose hotkey is ESC
(`Interpret_Keyboard_Input_`, fields.cpp:2608-2613), not to the -1 of
fields.cpp:983 — the key value returned is `0x1B`, not `0x011B`.

| node | accept | cancel button | ESC key | right click (source reading) |
|---|---|---|---|---|
| game menu | — | RETURN → galaxy map | hits RETURN (field 6, before 10) → galaxy map. **measured** | help everywhere the table covers; elsewhere -1, which no branch compares |
| settings | ACCEPT → **menu** (:443-446) | — | whole-screen field → **galaxy map**, not the menu (:440-442). **measured** | help over rows and ACCEPT |
| load | row / LOAD → loads, leaves | CANCEL → menu (:382-387) | → **galaxy map** (:388-391). **measured** | help |
| save | SAVE / 2nd click / Enter → saves, leaves to galaxy map | CANCEL → menu (:565-567) | → **galaxy map** (:575-577). **measured** | -1 in `Do_Save_Game_Popup_` hits the `input_id < 0` branch: `abs(-1) = 1` is inside `saved_game_fields[0..9]` = 1..10, so **menu** (:568-574) |
| confirmation | YES → action | NO → menu. **measured** for NEW and QUIT | **ignored** — the loop wants Y or N (gendraw.cpp:212). **measured**: 25 frames, list unchanged | help is switched off (`_help_list_active = 0`, gendraw.cpp:58); -1 is ignored |
| warning | any input → back to Load. **measured** by field | — | its only field is ESC → back to Load | help off |

Where "leaves" says galaxy map: `_Game_Popup_` ends in
`_current_screen = _return_screen` (:1593), which the GAME handler set
to `SCREEN_MAIN`. *Measured* after every close: screen 0 and a field
list identical to the one before GAME was pressed.

**Settings are committed on every exit, ESC included.**
`Update_Game_Settings_` + `Save_Session_Related_Settings_` run
unconditionally at the end of `_Game_Popup_` (:1588-1591), so ACCEPT and
ESC differ only in where the player lands. *Source reading* — nothing
was toggled in the live run.

## 6. Where the text comes from

| text | source | extractor |
|---|---|---|
| SAVE GAME, LOAD GAME, NEW GAME, QUIT GAME, SETTINGS, RETURN, Music, Sound Fx; GAME SETTINGS; ACCEPT; LOAD, SAVE, CANCEL | **baked into artwork**, GAME.LBX entries 0-7, 9-19, 27-29 (`Load_Game_Popup_Pictures_` :1177-1207) | **none** |
| YES, NO | artwork, CONFIRM.LBX 0-2 (gendraw.cpp:167-175) | none |
| warning frame | WARNING.LBX 0 (gendraw.cpp:96, :127) | none |
| 13 option labels | `HAROLD::H_Message_` 166-177 and 391 (:1503-1523) | `tools/hestrings_extract.py` — all present |
| `(ALT-F1)` … `(ALT-F8)` | string literals, loadsave.cpp:1504-1520 | — |
| confirmations, warnings | H 178-180, 184, 185, 186, 187 | hestrings — present |
| month names | H 190-201 (`Load_Month_Names_` :41-63) | hestrings — present |
| `Stardate:` | H 202 (:654) | present |
| `... empty slot ...` | H 388 | present |
| `(( save %d ))` | H 203 (:163) | present |
| default save name | literal format `"%s, %s, %d %s"` (:547) + H 188/189 | — |
| `* INVALID *`, `(Auto Save)`, `<< no description >>` | literals, loadsave.cpp:260, :271, :856; filedef.cpp:228, :230 | — |
| slot names | bytes 4..40 of each `SAVEn.GAM` (filedef.cpp:223) | — |
| slot dates | the file's mtime (`Get_File_Date_String_` :1747-1785) | — |

`H_Message_` is `HESTRNGS.LBX` (German `HGSTRNGS.LBX` …), harold.cpp:637
and :1531-1555. `Reload_Language_Strings_` (:1787) reloads the strings
and never GAME.LBX, so the button words stay whatever the artwork says
in every language — *source reading*.

## 7. What the Extension API carries, and what it does not

**Carried:**
- screen 8 for all four dialogs, the confirmation and the warning
- a FIELD_LIST on every node change (`ext_api.cpp:511-519`: count or
  screen changed). Every transition in this tree changes the count —
  11 / 30 / 16 / 25 / 3 / 2 — except entering a name edit (25 → 25)
- `MOX::_settings` whole, inside STATE (`ext_api.cpp:117`):
  `active_save_slot`, `music_level`, `sound_fx_level` and the 13 option
  bytes are in it. `core/game_state.py` reads only 0xD4-0xD7 of that
  block and no verified spec exists for the rest (decision 23).
- the framebuffer

**Not carried:**
- which dialog is up (`_screen_data`)
- the settings toggles WHILE the dialog is open: they live in
  `_game_popup_fields->options` (:433-438) and reach `MOX::_settings`
  only at popup exit (:1112-1124). The volume sliders are the exception —
  `Set_Music_For_Game_Popup_` writes `MOX::_settings` at once
- **the save slot list, entirely.** `Set_Up_Load_Save_Popup_` (:136-171)
  and `Check_For_Saved_Games_` (:599-640) enumerate `SAVE1.GAM` …
  `SAVE10.GAM` in the game's working directory into engine globals —
  `MOX::_save_game_description[10]` (37 bytes each, orion2.h:907),
  `MOX::_save_game_dates`, `MOX::_save_game_stardates`,
  `_game_popup_fields->slot_status` and `saved_game_types` — and none
  of those is serialized. What they are made from, all per file:

  | value | from | read by |
  |---|---|---|
  | valid | uint32 at 0 is `0xE0` or `0xE1` (savegame.h:6-7) | `Is_Valid_Game_Type_` :953 |
  | description | bytes 4..40 | filedef.cpp:223; slot 10 is forced to `(Auto Save)` (:227) |
  | stardate | int32 at 0x29 | filedef.cpp:224, savegame.cpp:1538; `Check_Magic_Number_` (:720) reads the SAME four bytes and calls them a magic number |
  | game type | int8 at 0x2D | filedef.cpp:245-258 → icon GAME.LBX 16/17/18 (:833-838) |
  | date | file mtime | :1747 |

  `SAVE11.GAM` exists in the folder and is never shown: the loops stop
  at ten.
- the game's working directory, so a client cannot find those files
  without being told where they are

**Reachability by input.** Types 0 and 7 are everywhere and take
`ACTIVATE_FIELD`. Two exceptions:
- **the sliders** (type 6): activation reaches the branch, but the new
  value is written from the POINTER by `fields::Find_Bar_Position_`
  (fields.cpp:1702, via :2839) — the same clobbered-pointer path as
  decision 39's correction. An activation sets nothing new.
- **the name input** (type 11): activating the hidden strip under a name
  starts editing without a mouse (`_input_field_active = 1` and the
  string copied, :512-520); characters would then go in as
  `INJECT_KEY`, one per `Get_Input_` (decision 21). *Source reading* —
  not driven, because it ends in a save.

**Questions, not requests** (nothing filed in `doc/orion2re_open_fixes.md`):
1. Should the slot list (description, stardate, date, status, type per
   slot) go on the wire — or should HD read the ten file headers itself,
   which needs the game's directory as a setting and is a second copy of
   `Get_Saved_Game_Descriptions_`?
2. Should a volume value be settable by command? Without one the sliders
   need an injected drag, which decision 39's correction says the pointer
   sync will overwrite unless the game window is unfocused.
3. Is `_screen_data` worth a byte in STATE? In single player the field
   count already identifies every node; a multiplayer menu (9 fields)
   and a future change to any builder would not.

## 8. Help

| dialog | table | entries | installed by | called from |
|---|---|---|---|---|
| galaxy map GAME button | `_main_screen_help_list` evanhelp.cpp:4 | 285 `(237,0)-(320,20)` | — | **already in** `screens/galaxy_map/help.json` |
| game menu | `_main_game_screen_help_list` evanhelp.cpp:40-53 | 12 | `Set_Main_Game_Screen_Help_List_` :278 | loadsave.cpp:1228 |
| load | `_load_game_screen_help_list` :77-85 | 7 | `Set_Load_Game_Screen_Help_List_` :286 | :317 |
| settings | `_options_game_screen_help_list` :87-106 | 18 | `Set_Options_Game_Screen_Help_List_` :290 | :418 |
| save | `_save_game_screen_help_list` :108-116 | 7 | `Set_Save_Game_Screen_Help_List_` :294 | :480 |
| confirmation, warning | none — help switched off | | gendraw.cpp:58 | |

All four dialog tables begin with the same four **415 "Game Popup Exit"**
rectangles covering everything outside the popup — `(145,0,639,26)`,
`(0,0,143,479)`, `(145,403,420,479)`, `(422,28,639,479)` — then:

- menu: 416 save `(181,69,276,97)`, 417 load `(290,69,382,97)`, 418 new
  `(182,112,275,143)`, 419 quit `(289,113,382,144)`, 420 music
  `(196,188,370,236)`, 421 sound `(196,238,369,290)`, 422 settings
  `(181,332,276,363)`, 423 return `(293,332,385,362)`
- load: 424 slot list `(163,43,401,357)`, 426 load `(178,360,254,389)`,
  425 cancel `(310,359,385,388)`
- settings: 429-441 the thirteen rows, x 169/170 … 395-398, 17 px pitch
  from y 67; 442 accept `(236,358,319,387)`
- save: 427 slot list `(155,37,402,357)`, 428 save `(178,360,252,387)`,
  425 cancel `(310,359,386,388)`

Every one of 285 and 415-442 is present in the extracted
`assets/shared/help/help_en.json` (checked by id).

## 9. Side effects on disk

| node | reads | writes |
|---|---|---|
| menu, settings | `MOX.SET` at exit | **`MOX.SET` bytes 0-210 on EVERY popup exit, any path** (:1588-1591 → :1044-1075). *Measured*: mtime 18:26:06 → 18:33:58, content byte-identical |
| load / save dialog open | headers and mtimes of `SAVE1..10.GAM` | — |
| load a slot | that `SAVEn.GAM` | `MOX.SET` (:359) |
| save to a slot | — | `SAVEn.GAM`, then `MOX.SET` whole (filedef.cpp:82) and again 0-210 (:557) |
| **QUIT → YES** | — | **`SAVE10.GAM`** (`Save_Game_(9)`, :1262), `MOX.SET` |
| settings language branch | — | the language file (:455) — no field in this dialog changes `language`, so *source reading* says unreachable |

**The nodes that touch SAVE10.GAM:** QUIT → YES writes it; the Save
dialog writes it if slot 10 is chosen; the Load dialog reads it on open
and loads it if slot 10 is chosen. The turn-end autosave is outside this
tree. Every later live step on Save, Load or Quit names the slot and
checks SAVE10.GAM against the secured fixture before and after.

## 10. Live steps and native screenshots

**Game**: orion2re pid 7992 (`~/orion2re/out/build/Linux/linux-debug`),
on the galaxy map, stardate 3500.0, 99 stars, 50 colony records —
**not a known fixture** (`fixtures.fixture_name` → None). Nothing was
loaded and nothing saved. OrionLayer (`main.py`) was connected alongside.

**SAVE10.GAM**: `9f9f35e4…` before and after the run. The secured
fixture `fixture_natives_autosave_3502.4.GAM` is `2610f39c…` — **the
slot had ALREADY diverged before this session** (file dated
13 Sep 09:03, an autosave). This run did not cause it.
Every `SAVE*.GAM` hash was identical before and after, and no new file
appeared (the warning was provoked on the missing `SAVE4.GAM`).

**Screenshots**: `~/orionlayer-fixtures/evidence/game_menu/`, sixteen
PNGs plus `fields_capture.json` and `fields_esc.json` (every node's
field list and the ESC results). Taken by a scratch script, driven by
`ACTIVATE_FIELD` and waiting on FIELD_LIST shape; the one
`INJECT_CLICK` was on slot 4's name input for the edit state.

| file | node |
|---|---|
| `00_galaxy_map` | before |
| `01_game_menu` | game menu |
| `02_options`, `02b_menu_after_options_accept` | settings; ACCEPT → menu |
| `03_load`, `03a_load_empty_slot_warning`, `03b_load_after_warning`, `03c_menu_after_load_close` | load; warning on slot 4; back to load; CANCEL → menu |
| `04_save`, `04a_save_slot_name_input`, `04b_menu_after_save_close` | save; editing slot 4; CANCEL → menu |
| `05_new_game_confirm`, `05a_menu_after_new_no` | NEW confirmation; NO → menu |
| `06_quit_confirm`, `06a_menu_after_quit_no` | QUIT confirmation; NO → menu |
| `07_galaxy_after_close` | RETURN → galaxy map |

**Deviation from the work order: they are not under `doc/`.** They show
unmodified GAME.LBX artwork and the player's own save names, which is
what decision 42 keeps out of the repository and what the fixtures
README says of every screenshot of the player's game. Moving them into
`doc/` is one `cp` if Data decides otherwise.

**Not captured**: the save-disabled message box, the invalid and
multiplayer warnings (same box as `03a`), the load-failed warning, help
popups, and the multiplayer menu.

## 11. Seen on the way — orion2re behaviour worth a decision

Not faults of this tree; recorded because Stop 2 has to decide whether
to transcribe them.

- **The year prints as 126.** `MISC::Get_Time_Stamp_` hands over
  `tm_year` raw (misc.cpp:699) — years since 1900.
- **The Load dialog shows no month on its first visit.** The date strings
  are built in `Set_Up_Load_Save_Popup_` (:153), called from
  `_Game_Popup_` (:1573), before `Do_Load_Game_Popup_` runs
  `Load_Month_Names_` (:304). `03_load` reads "31, 126 13:52";
  `04_save`, taken after that first load visit, reads "Jul 31, 126 13:52".
- **Two different Alt-key label sets for the settings.** The screen path
  prints F4 … F8 on rows 4-8 (:1511-1520, what `02_options` shows); the
  bitmap path, used for the slide animation, prints F5 … F8 on rows 5-8
  and no F4 (:1481-1487).
- **The two auto keys are named backwards.** `-0x455` runs
  `Auto_Save_Last_Saved_Game_`, which asks "Load game %d?" (H 205) and
  loads; `-0x456` runs `Auto_Load_Last_Saved_Game_`, which asks
  "Save game %d?" and saves (mainscr_main.cpp:617-630, loadsave.cpp:1625,
  :1799). Behaviour and message agree; only the names are swapped.
  Outside this tree.

## 12. Open questions for Data before Stop 2

1. **Overlay or screen (decision 11)?** The original draws every dialog
   over `MAINSCR::Draw_Mini_Main_Screen_` (:1354, :808), and it blocks
   only that screen's input — which reads as a screen-local popup of the
   galaxy map. But the game REPORTS a different screen id (8), and the
   dispatcher switches screens by id and opens overlays by name, so
   "local to the galaxy map" needs id 8 to keep the galaxy map active.
   Which?
2. **The slot list** — patch (7, question 1), or HD reads `SAVEn.GAM`
   headers from a configured game directory?
3. **The volume sliders** — patch, an injected drag with the focus
   caveat, or not offered in HD (and marked)?
4. **Settings toggles are invisible on the wire while the dialog is
   open.** HD would have to hold them locally, initialised from
   `s_settings` — which first needs a verified spec for those 13 bytes,
   `active_save_slot` and the two volumes (decision 23). Agreed?
5. **Name entry**: HD's `TextInput` drives the game's continuous input one
   key at a time (decision 21), or something else? The default name when
   left empty is the original's (§4) and should stay.
6. **The quirks in §11**: transcribe what orion2re shows (year 126, no
   month on first load), or what MOO2 showed? And is any of them for
   `doc/orion2re_open_fixes.md`?
7. **QUIT → YES ends the game process.** What does HD do when the server
   goes away because the player asked it to?
8. **Load success lands on `SCREEN_REPORTS`**, through a period of
   silence (`FILEDEF::Load_Game_`). That screen has no HD version and
   falls back — fine for Stop 2, or in scope?
9. **Right-click inside the Save dialog outside a help rectangle returns
   to the menu** (§5, source reading). Transcribe, or verify live first?
10. **Screenshot location** (§10).

No HD EXTENSION is required by anything above. The one that would be
tempting — ESC cancelling a confirmation — is exactly what the original
does NOT do (§5, measured) and is not proposed.

---

## Stop 2 — what the implementation measured

The implementation is `screens/game_menu/`, its status and live
acceptance are in `v3_projektstatus.md` ("GAME menu — work order
Stop 2"), its decisions are fundament 59-62. The HD pictures beside the
native frames are in `~/orionlayer-fixtures/evidence/game_menu/hd_live/`
— outside the repository, which carries no save names. Three readings
above changed status:

- **§5, "Settings are committed on every exit, ESC included"** — now
  MEASURED: a toggle followed by ESC changed `s_settings` byte 4.
- **§5, ESC while editing a save name -> menu** — now MEASURED on the
  native path.
- **§5, the Save dialog's right click outside a help rectangle** — still
  a source reading; it could not be produced (status document).

And §7's "characters would then go in as INJECT_KEY, one per
`Get_Input_`" was right about the need and wrong about the tool: the
existing injector bursts, and the game's ten-key ring loses the rest
(measured, 15 keys kept 9).
