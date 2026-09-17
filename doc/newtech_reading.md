> **Provenance (work order 129 B, 17 September 2026).** A source reading, written in the unattended run by a read-only sub-session and filed unchanged. Spot-checked against the tree by the session that filed it: the hand-over at tech.cpp:103-106 (science room, then `current_research_field` and `research_breakthrough` zeroed, then `_Tech_Select_(0)`), the three-field list at science.cpp:169-171, and the two readers of `MOX::_current_screen` in textbox.cpp (:40-50 for the box's x, :284 for its colour group). Everything else is the reading's own claim with its line reference — verify before building on it. Nothing here was driven live.

# The research PRESENTATION dialog (science room) in orion2re — a reading

Read 17 September 2026 against orion2re 1.60.0 (src/version.h)
(`ENGINE_VERSION[] = "1.60.0"`, version.h:10). **No code was written, nothing
was driven, nothing in either tree was modified.** Every statement is *source
reading* with its `file.cpp:line`. Companion to `doc/tech_change_reading.md`
(work order 126 G), which reads the SELECT NEW RESEARCH list that follows this
dialog; nothing from that reading is repeated except where this one corrects
or completes it.

**First correction: there is no `newtech.cpp` dialog.** `src/game/newtech.cpp`
(507 lines) is the AI tech chooser — `Choose_Tech_Application_`,
`Calc_Tech_Value_`, `Set_Competition_Tech_Values_` (newtech.h:7-51). It draws
nothing and is not on the human path. The dialog the work order describes is
the **science room**, `src/game/science.cpp`, namespace `SCIENCE`, 436 lines.

---

## 1. Ownership, entry, and the builders

**One function owns it:** `SCIENCE::Science_Room_(char* intro_animation_name,
uint16_t discovery_count, int16_t* discovery_data, char* footer_text)`
(science.cpp:112-392). It is a self-contained modal loop with its own field
list, its own auto function and its own teardown.

**How it is entered at turn start** (the work order's backtrace, completed):

```
mox2.cpp:184-185   Screen_Control_ case SCREEN_REPORTS -> MAINSCR2::Reports_Screen_
mainscr2.cpp:119   Reports_Screen_ sets MOX::_current_screen = SCREEN_MAIN
mainscr2.cpp:164   -> MAINSCR2::Do_Begin_Of_Turn_
mainscr2.cpp:490   Begin_Of_Turn_ -> MAINSCR2::Main_Screen_Report_Handler_
mainscr2.cpp:725   the do/while loop -> REPORT::Display_Report_
report.cpp:328     Display_Report_ -> Display_Report_Aux_(player, 1)
report.cpp:310     -> Has_Research_Breakthrough_(player, 1)
report.cpp:513     research_breakthrough != 0 -> TECH::Tech_Select_()
tech.cpp:103       Tech_Select_ -> SCIENCE::Show_Off_Researched_Tech_(_PLAYER_NUM)
science.cpp:428    -> SCIENCE::Science_Room_(...)
```

`TECH::Tech_Select_` (tech.cpp:97-109) is **two dialogs in a row**, in this
order: `Save_Palette_` :100, allocate the 0x7C830 animation buffer :101-102,
`Show_Off_Researched_Tech_` **:103** (the presentation), zero
`current_research_field` :104 and `research_breakthrough` :105, then
`_Tech_Select_(0)` **:106** (the select list), `Fast_Fade_Out_` :107,
`Reset_Screen_` :108.

**`Set_Initial_Tech_` never shows this dialog.** report.cpp:467-479 requires
`current_research_field == TECH_FIELD_STARTING_TECH` (= 0, orion2_consts.h:862);
`Show_Off_Researched_Tech_` returns at once when that field is 0
(science.cpp:405, :433-435: clear the text, `Clear_Fields_`, `Fast_Fade_Out_`).
So the start-of-game path goes **straight to the select list with no science
room**. Only `Has_Research_Breakthrough_` (report.cpp:507-519) reaches it.

**What decides the content** — `Show_Off_Researched_Tech_` (science.cpp:397-436):

| | line |
|---|---|
| field = `_cur_plyr_ptr->current_research_field`, must be != 0 | :405-406 |
| up to 4 tech ids from `TECHDATA::_technology_fields[field].tech[0..3]` whose `tech_applications[id] == TECH_RESEARCH_STATUS_RESEARCHED` (=3, orion2_consts.h:1324) and `id > TECH_APP_NO_TECH` | :410-416 |
| if none qualify: no dialog (:418 guard, fall through to :433-435) | :418 |
| headline text = `billtext.lbx` message **1**, then `JIM::Decode_Text_Field_(text, field, 0xFA)` — control byte 0x89 substitutes `TECH::Technology_Fields_Name_(field)` (jim.cpp:254-256, :308-310) | :419-420 |
| scientist animation = `"SR_R%x_SC.LBX"` with `_player[plr].race` | :422-426 |
| call | :428 |

**What draws each part** (all inside `Science_Room_`):

| part | builder | line | native position |
|---|---|---|---|
| **scientist picture / room** | `Open_Multi_File_Animation_(intro_animation_name, 0, slot 1)`; drawn each frame by `Update_Science_Anims_` -> `Draw_Multi_File_Animation_Stencil_(1)` | :168; :72-76 | full screen, drawn at (0,0) (file_ani.cpp:356-358, :394-397) |
| static fallback | `animations_on == 0` -> `Set_File_Animation_Frame_(18)` — frame 18, not an animation | :74-75 | — |
| **device sprite** | `Open_Multi_File_Animation_("TANM_%03hi.LBX" % (tech_id & 0x01FF), 0, slot 0)`; drawn by `Draw_Multi_File_Animation_(0)` | :140, :247; :83-85 | (0,0), full screen |
| room foreground / background | `SCIENCE.LBX` entry **1** (foreground) and **2** (background), `animate::Draw_(0, 0, …)` | :78-90 | (0,0) |
| **description box** | a 0xAF x 0xC3 (175 x 195) offscreen bitmap, filled at :263-300, blitted by `animate::Draw_(0xDD, 0x2C, …)` | :318, :326, :370 | **(221, 44)-(395, 238)** |
| — its title | `s_help_record.title[80]` at record offset 0, font style 3 `_science_high_color`, `Print_Formatted_Paragraph_To_Bitmap_(2, 1, 0xAB, …, justify 2)` | :265-266 | bitmap-local (2,1), width 171, centred |
| — its body | same record + **0x67** (`s_help_record.body`, orion2.h:1004-1011), font style 2, `Set_Font_LF_(1)`, printed at `y = title_height + 1` | :268-272, :297, :300 | bitmap-local (2, h+1) |
| — the record | `TEXTBOX::Get_Help_Lbx_Name_` (HELP.LBX / GER_/FRE_/SPA_/ITA_ by `_settings.language`, textbox.cpp:17-38) then `Far_Reload_Data_(name, 0, buf, tech_id & 0x1FF, 1, 0x57B)` | :253-261 | ONE record; `next_help_idx` is **not** followed |
| **the headline** ("Your scientists have completed their research in …") | `FMTPARA::Print_Formatted_Paragraph_(0x91, 0x1A4, 0x17C, footer_text, 2)`, outline colour 0xF2, font style 4 outline `_science_normal_color`; **redrawn every frame** | :333-335 | **x 145, y 420, width 380, centred** |
| mouse pointer | a 30x30 bitmap cut from `SCIENCE.LBX` 0 and pushed to the cursor | :146-147, :176-181 | — |
| the open/close transition | `bitmap::Jumble_Bitmap_(previous, current, amount, steps)`, amount 100 -> 0 in steps of 0x14 when `animations_on`, else 0; steps 6 -> 1 | :306-307, :316-327 | at (0xDD,0x2C) |
| the shrink-away on exit | `SCIENCE.LBX` 1 played backwards; the text bitmap scaled by `_bm_scale_x/_bm_scale_y` = {6,21,37,60,85} and drawn at `_bm_scaled_x1/_bm_scaled_y1` = {373,349,320,283,239}/{203,179,149,113,69} | :14-17, :341-383 | only when `animations_on != 0` |

**The auto function is EMPTY.** `fields::Assign_Auto_Function_(&SCIENCE::Draw_Science_Room_, 2)`
(:174) installs `Draw_Science_Room_`, which is `{ }` (science.cpp:394-395).
This is the decisive difference from the select list: nothing here reads the
pointer position, so no input path depends on where the mouse is. The select
list's `Draw_Tech_Select_` does (tech.cpp:448-466), which is the whole hazard
in work order 126 G section 2.1.

**Dead branch, noted:** `Show_Off_Artifact_Tech_` (science.cpp:41-67) has a
scientist-presented variant gated on `SCIENCE::_finds_presented_by_scientist`,
which is **declared at science.cpp:4 and never written anywhere in the tree**
(grep: only :4 and the test at :44) — always 0, so the artifact path always
takes `Show_Off_Captured_Tech_` (trooper animation).

## 2. The field list, in build order, and what dismisses it

`fields::Clear_Fields_()` (science.cpp:135) leaves count 1 — field 0 is the
dummy (fields.cpp:200-211). Then exactly two fields are added:

| # | call | line | type | native rect | hotkey | sound |
|---|---|---|---|---|---|---|
| 0 | — (dummy left by `Clear_Fields_`) | :135 | whatever was there | stale | stale | — |
| 1 | `fields::Add_Hidden_Field_(0, 0, 0x27F, 0x1DF, "", 0)` | :169 | 7 `FIELD_TYPE_HIDDEN` (orion2_consts.h:213; fields.cpp:296-310) | **(0,0)-(639,479)** | `'\0'` | 0 |
| 2 | `science_hot_key = fields::Add_Hot_Key_("\x1B")` | :171 | 7 `FIELD_TYPE_HIDDEN` (fields.cpp:234-249) | **(5000,5000)-(5000,5000)** — off screen by construction | **0x1B (ESC)** | — |

**`_fields_count == 3` for the whole dialog.** That three-field shape, with a
whole-screen type-7 field and an off-screen ESC field, is the wire signature.

**It is the game's main list, not a saved one.** science.cpp contains no
`FIELDSAV::Save_Field_Stats_` (grep: none), so `fields::_fields` still points
at `g_fields_storage` (fields.cpp:32) and `ext::SerializeFields`
(ext_api.cpp:245-259) serialises these three entries. The main screen's own
fields are *destroyed* by the `Clear_Fields_` at :135 and are rebuilt later by
`Begin_Of_Turn_` (mainscr2.cpp:494-507). Contrast the select list's category
popup and the description box, which do move the base (fieldsav.cpp:4-21).

### Which input reaches which field

The loop is science.cpp:231-339; the only reader is `fields::Get_Input_()` at
**:235**.

```
:236  input == 0 && !first_entry      -> Update_Science_Anims_(1,1,1,1); idle frame
:239  remaining_discoveries == 0
        || input == science_hot_key   -> should_close = true; break
        else                          -> present the NEXT discovery (:244-313)
```

- **Left click anywhere** -> field 1 (the whole-screen field covers every
  pixel, `Scan_Field_` fields.cpp:690-712). Non-zero, not the hotkey:
  **advances** to the next discovery, or **closes** once
  `remaining_discoveries` has reached 0.
- **ESC** -> `Interpret_Keyboard_Input_` matches hotkey 0x1B on field 2
  (fields.cpp:2607-2613), `Interpret_Mouse_Input_` returns 2
  (fields.cpp:1010-1039): **closes immediately**, at any point.
- **Right click** — *"A right click is not always Cancel"* applies, and here it
  is not Cancel either. `fields::Deactivate_Help_List_()` at :132 sets
  `_help_list_active = 0`, so the help branch (fields.cpp:1364-1368) is skipped;
  `_mouse_cancel_disabled` is 1 (set by `mainscr_main.cpp:281` and **never
  reset — there is no `Enable_Cancel_` in the tree**, grep), so the -1 branch
  at fields.cpp:1369-1376 is skipped too, and the pointer lands on field 1
  giving **-1** (fields.cpp:1508-1512). Non-zero -> identical to a left click.
  **There is no Cancel and no help in this dialog.**
- **`ACTIVATE_FIELD` works and is safe.** `ext::Tick` runs from
  `fields::Get_Input_` (fields.cpp:167) and `g_pending_field` returns before
  any mouse reading (fields.cpp:170-180); `ProcessInput` bounds-checks against
  `_fields_count` (ext_api.cpp:509), so 1 and 2 are accepted and 3+ rejected.
  Field 1 advances, field 2 closes. Because the auto function is empty and
  nothing reads the pointer, neither depends on where the mouse is — unlike
  the select list.
- **Clicks return on press, not release**, in this dialog only:
  `fields::Disable_Mouse_Wait_()` at :198 sets `_mouse_auto_exit = 1`, which
  breaks the hold loop at fields.cpp:1457. `Enable_Mouse_Wait_()` at :389
  restores it.
- Directly after presenting a discovery the code **spins until the physical
  button is released** (:309-311) and flushes the buffer (:313). An
  `ACTIVATE_FIELD` sets no button state and is unaffected.

**Frames the wire never sees:** the fade-in loop at :194-218 calls
`RUSS::Mox_Sync_Update_` (russ.cpp:221-224 -> `Mox_Update_` :215-219) and
*not* `Get_Input_`, so `ext::Tick` does not run for those ~5 iterations. The
same holds for the close animation at :341-383.

## 3. Every displayed value against the wire

Player offsets per `core/structs/player.py`: ✔ = in the verified SPEC;
"const" = a module constant outside the SPEC; "hand" = counted from
orion2.h, which is **not** verification (decision 23).

| value shown | source | on the wire? |
|---|---|---|
| the completed FIELD id | `s_player.current_research_field` | @901 **✔** — but see §5: `Tech_Select_` zeroes it at tech.cpp:104, *after* this dialog, so it is readable only while this dialog is up |
| the dialog fires at all | `s_player.research_breakthrough != 0` (report.cpp:510) | @48 **✔**, `i8`. Also cleared at tech.cpp:105 / report.cpp:514 |
| which applications are shown | `tech_applications[id] == 3` over `_technology_fields[field].tech[0..3]` | `tech_applications` @379 **const** (`TECH_APPLICATIONS_OFFSET`, "not decoded yet"); `tech[4]` is not a table — filled at init from `_technology_applications[].tech_field_id` (techinit.cpp:444-474) |
| the headline string | `billtext.lbx` msg 1 + field name (TECHNAME string 1..82) | **not on wire**; no billtext extractor exists, and `tools/techname_extract.py` writes buildings and ship parts only |
| description title and body | HELP.LBX record `tech_id & 0x1FF`, one record | **not on wire**. `assets/shared/help/help_en.json` holds 707 entries with 1..211 as tech titles (verified by reading the file: 1 = "Achilles Targeting Unit", 83 = "Heavy Fighter Bays", 211 = "Hyper Sociology") — usable as-is, but `help_extract.py` joins CHAINS while this reads a single record; whether any tech record has `next_help_idx != 0` is **NOT SETTLED** |
| scientist animation | `SR_R%x_SC.LBX`, `s_player.race` | race @37 **✔** |
| device animation | `TANM_%03hi.LBX`, tech id | derivable from the above |
| the "captured techs" footer variant (billtext 3) and the spy variant (billtext 2) | `Show_Off_Captured_Tech_` :29-30, `Show_Off_Stolen_Tech_` :102-103 | `REPORT::_reports[]` is **not on the wire** — see §5, this matters |
| HELP.LBX language suffix | `_settings.language` (textbox.cpp:17-38) | `s_settings` is on the wire (ext_api.cpp:117) but `language` is **not in the settings spec** |
| weapon-modification list (billtext 4 + `_weapon_modifications[].name`) | `discovery_data[i] & 0x4000` branch, :274-295 | **unreachable from this entry point**: `Show_Off_Researched_Tech_` stores raw tech ids (< 0x4000) at :414, so the flag is never set here. It belongs to the combat-capture path (combfind.cpp:2070, :2086) |
| `animations_on` (static frame 18 vs. the animation; jumble on/off; shrink-away on/off) | `_settings.animations_on` :72, :155, :306, :346 | in `s_settings`, **not in the settings spec** |

## 4. What `MOX::_current_screen` holds

Read, not inferred:

- `Screen_Control_` ticks the ext API once with **39** (`SCREEN_REPORTS`,
  orion2_consts.h:493) at mox2.cpp:38-41, then calls `Reports_Screen_`
  (mox2.cpp:185).
- `Reports_Screen_` sets **`MOX::_current_screen = SCREEN_MAIN`** at
  mainscr2.cpp:119 — before any report runs.
- Nothing on the path to either dialog writes it again. `science.cpp` does not
  contain the identifier at all (grep); `tech.cpp` writes it once, at :1167, in
  `Tech_Change_` — the *other* mode, which this path never enters.

**So: 0 for the presentation dialog, 0 for the select list that follows.**
Work order 126's claim in `doc/tech_change_reading.md` §4 — "the wire says 0
throughout" — is **right for both**, and its reasoning (mainscr2.cpp:119) is
the same reasoning that covers the presentation dialog it did not read.

Consequence for HD: `core/screen_names.py:35` maps 0 to `galaxy_map`, so
`screens/galaxy_map` is the active HD screen behind both. Two notes:

1. The parking hazard of decision 59 does **not** reach this dialog.
   `screens/galaxy_map/screen.py:256-260` now resolves the zoom-out field
   through `mapboxes.live_field` (mapboxes.py:63-77), which matches on
   `field_type` *and* the native rect; the science room's only type-7 field is
   `(0,0,639,479)`, which is not the zoom-out button's rect, so no
   `ACTIVATE_FIELD` goes out. The bounds check at ext_api.cpp:509 is a second
   line of defence (only 1 and 2 exist).
2. Screen id 39 is mapped to `"reports"` in `screen_names.py:56` with no
   `screens/reports/` folder — a name for a screen that is on the wire for one
   tick and then gone.

## 5. The hand-over, and what else sits in the same place

**Presentation ends -> select list begins**, with no screen switch and no
snapshot in between:

```
science.cpp:386-391  Pop_Block_; Clear_Fields_ (count -> 1); Clear_Mouse_Buffer_;
                     Enable_Mouse_Wait_; Put_Auto_Function_; Set_Fade_Percent_(0)
science.cpp:429      return from Show_Off_Researched_Tech_
tech.cpp:104-105     current_research_field = 0; research_breakthrough = 0
tech.cpp:106         _Tech_Select_(0)
tech.cpp:127-131     Clear_Fields_; Set_Refresh_Stencil_; Get_Auto_Function_;
                     Push_Block_; Disable_Cancel_
tech.cpp:198-240     the select list's fields are added
tech.cpp:276         Set_Input_Delay_(5)
tech.cpp:311         the select loop's first Get_Input_
```

No `Get_Input_` runs between science.cpp:235 (last) and tech.cpp:311 (first),
so **`ext::Tick` never sees the 1-field intermediate list** — the wire goes
from the 3-field science room straight to the select list. And
`Set_Input_Delay_(5)` (tech.cpp:276) returns before `ext::Tick`
(fields.cpp:159-163), so the first five frames of the select list are silent
too.

**The two zeroings at tech.cpp:104-105 are the load-bearing detail for HD.**
Once the select list is up, `current_research_field` and
`research_breakthrough` are both 0, so **which project just completed is no
longer on the wire.** It is readable only while the presentation dialog is up.

**What else runs in the report phase, in order.** `Display_Report_Aux_`
(report.cpp:296-325) is a fixed chain of early returns; each non-zero return
ends the call, `Main_Screen_Report_Handler_` loops (mainscr2.cpp:718-747) and
the chain restarts from the top:

| # | line | what | what it puts on screen |
|---|---|---|---|
| — | :299-305 | already-done bit / `_stardate == 35000` guards | — |
| 1 | :307 | `Antarans_` | Antaran room screen or the attack flic (report.cpp:671-718) |
| 2 | :308 | `Has_GNN_` | **GNN news** — `EVENTS::Check_For_Event_` (report.cpp:430-445) |
| 3 | :309 | `Set_Initial_Tech_` | the select list **without** a science room (§1) |
| 4 | :310 | `Has_Research_Breakthrough_` | **this dialog, then the select list** |
| 5 | :311 | `Has_Evolutionary_Upgrade_` | `raceopt::Setup_Evolutionary_Upgrade_` |
| 6 | :312 | `Has_Officer_For_Hire_` | `MAINPUPS::Random_New_Officer_Popup_` |
| 7 | :313 | `Colonization_` | colony/outpost selection popups, confirmation boxes, star-name popup, the colonize animation (`_current_screen = 0x21`, :269) |
| 8 | :314 | `Explored_New_Star_` | `MAINPUPS::New_System_Discovery_Popup_` |
| 9 | :315 | `Officer_Made_Level_Report_` | officer level popup |
| 10 | :316 | `Has_Report_` | **the same science room again** for a stolen tech (:814) or an artifact tech (:822), otherwise `GENDRAW::Message_Box_` (:831) |
| 11 | :317 | `Has_Diplomacy_Messages_` | `DIP_SCRN::Npc_Diplomacy_Screen_` |
| 12 | :318 | `Has_Msg_` | **the turn summary** — `_current_screen = SCREEN_TURN_SUMMARY` (:138) |
| 13 | :319 | `Empty_Colony_Queue_` | jumps to `SCREEN_COLONY` (:862-868) |
| 14 | :320 | `Need_To_Set_Occupation_Policy_` | jumps to `SCREEN_COLONY` (:733-742) |

Three consequences:

- **GNN news runs BEFORE the research presentation**, not after (:308 vs :310).
- **The council vote is not here.** `council::Check_For_Council_Meeting_` runs
  in `NEXTTURN::Next_Turn_Calc_` (nextturn.cpp:147), i.e. during turn
  resolution, before the report phase begins.
- **A 3-field science room at screen 0 is NOT uniquely the research
  presentation.** Step 10 reaches `Science_Room_` with the identical field
  list, differing only in the animation (`SR_R%x_SP.LBX` / `SR_R%x_TR.LBX`,
  science.cpp:6-9) and the footer (billtext 2 or 3). `REPORT::_reports[]` is
  not on the wire, so the only discriminator HD has is
  `research_breakthrough != 0`, which is true only for step 4.

**A second completed project in the same turn cannot happen.**
`research_breakthrough` is one `int8` and `current_research_field` one `int8`;
one field completes per turn. What *can* happen is several applications of the
same field in one science room — up to 4 (`tech[0..3]`, science.cpp:411), one
click each, which is the normal case for a Creative race.

## 6. What a patch would carry — described only

**Decision 25 first: almost all of it is reconstructible.** Given
`current_research_field`, `research_breakthrough`, `tech_applications[]` and
`race` from the snapshot, plus the static `_technology_fields[].tech` mapping
(techinit.cpp:444-474), HD can derive the field, the list of applications and
both LBX names without a patch. The data validates itself: `_fields_count == 3`
with `(0,0,639,479)` type 7 plus an off-screen ESC field, and
`research_breakthrough != 0`, must agree with the derived non-empty
application list.

What is missing is **not a patch but extraction and spec work**:
`s_settings.language` and `s_settings.animations_on` in the settings spec
(the first picks the HELP.LBX file, the second decides whether there is an
animation at all); `tech_applications` @379 promoted from a const anchor to a
decoded field; a `billtext.lbx` extractor for messages 0-4 (and 61-73 for the
select list) on the `hestrings_extract.py` pattern, since message **1** is the
headline this dialog is named after and exists nowhere in this tree;
`techname_extract.py` extended to TECHNAME strings 1..82 for the 0x89
substitution; and a decision on HELP.LBX chaining, because this dialog reads
ONE record (science.cpp:255-261) while `help_extract.py` joins chains.

**What no existing path reaches:** nothing. Unlike the select list, this dialog
needs **no input patch** — `ACTIVATE_FIELD 1` advances and `ACTIVATE_FIELD 2`
closes, both already bounds-safe and both independent of the pointer (§2). If
anything is wanted from Joes it is the *discriminator* for step 10 vs step 4
(which `Science_Room_` variant is running), and even that is answerable from
`research_breakthrough` without a patch.

**A synthetic screen id** would be the one real candidate, on the racesel.cpp
precedent (`core/screen_names.py:63-71`, ids 50 and 51): screen 0 with a
3-field list is the science room, but HD would rather be told than infer it.
That is a *direction* question for Data, not a detail.

## 7. Right-click help

**There is none.** `fields::Deactivate_Help_List_()` (science.cpp:132) sets
`_help_list_active = 0`, `_help_struct_pointer = nullptr`,
`_help_list_count = 0` (fields.cpp:116-120), and nothing in `Science_Room_`
re-installs a list — there is no `My_Set_Help_List_` call in science.cpp
(grep). `billhelp.cpp` has no science-room table (:36-75 lists the technology
select/change/list tables, ids 254, 255, 256, and none for this dialog).

So `Check_Help_List_` is never consulted, and a right click is just another
dismiss (§2). The select list that follows *does* install help — ids 254
(select panel) and 256 (category popup) per `doc/tech_change_reading.md` §6 —
so the two dialogs differ here, and an HD `help.json` for the presentation
would be an **HD EXTENSION**, not a transcription.

## 8. Does the drawing depend on `MOX::_current_screen`?

**For this dialog: no.** Every coordinate in `Science_Room_` is a literal —
the text bitmap at `(0xDD, 0x2C)` (:318, :326, :370), the headline at
`(0x91, 0x1A4)` width `0x17C` (:335), the animations at (0,0). `science.cpp`
does not contain the identifier `_current_screen` at all. A patch that changed
`_current_screen` to a synthetic id would move nothing here.

**For the select list that follows: yes, in two places, and both are in
`textbox.cpp`** — reached only by the right-click description popup
(`TECH::Draw_Application_Description_`, tech.cpp:718-779 -> `TEXTBOX::Text_Box_`
:775):

| what it decides | function | line | behaviour |
|---|---|---|---|
| the box's **x** and **y** | `TEXTBOX::Box_Centered_On_XY_` | textbox.cpp:44-53 | `_current_screen == SCREEN_MAIN` -> **x = 84**, y centred in the 400-px map viewport offset by 21, floored at 5; otherwise **x = 130**, y centred in 480. The box is 380 px wide (:74, :80), so at screen 0 it spans **x 84..464** and crosses the select panel's left edge at 161 |
| the box's **colours** | `TEXTBOX::Get_Mox_Text_Box_Base_Colors_` | textbox.cpp:284-300 | a `color_group` of 2 (colony screens), 3 (info), 1 (main menu) or **0 (default — and screen 0 falls here)**, added as `base + group*3` to the palette base (:302-304) |

I checked the other files a patch might disturb: `misc.cpp`, `fonts.cpp`,
`billhelp.cpp`, `list.cpp`, `bill.cpp`, `gendraw.cpp`, `harold.cpp`,
`animate.cpp`, `file_ani.cpp`, `fmtpara.cpp` — **none reads
`MOX::_current_screen`** (grep). In `fields.cpp` the only reader is
`ext::Tick(MOX::_current_screen)` at :167, i.e. the wire itself.

So: a patch that reported a synthetic id for the presentation dialog would be
purely cosmetic on the wire. A patch that reported one for the **select list**
would move its description popup by 46 px and change its palette group. That is
the concrete cost of "mode identity in select mode"
(`doc/tech_change_reading.md` §5.2) and it was not stated there.

## 9. NOT SETTLED

1. **The actual text of `billtext.lbx` message 1.** Nothing in either tree
   holds it; the work order's wording is from the game. The source only proves
   the shape (one 0x89 substitution of the field name, jim.cpp:308-310).
2. **Whether any HELP.LBX tech record chains** (`next_help_idx != 0`,
   orion2.h:1009). This dialog reads one record; `help_extract.py` joins. Same
   question as `doc/tech_change_reading.md` §3.
3. **The native size of the SCIENCE.LBX and SR_R*_SC.LBX frames**, and where
   the scientist and the device sit inside them. Drawn at (0,0) with no rect in
   the source; that is in the art, not the source, and *an asset is not a
   measurement*. (221,44)-(395,238) is the text bitmap's blit rect and is the
   one layout number the source does give.
5. **How many ticks HD sees before the first discovery is on screen.** The
   first loop iteration always takes the presentation branch (:236 is false
   while `first_entry`), but the preceding fade-in (:194-218) does not tick
   ext. A live measurement.
6. **`jumble_amount`/`jumble_steps` are seeded from string bytes**
   (`memcpy(&jumble_amount, animation_lbx_names[0], 2)`, :226-227 — the bytes
   `'T','A'`). Both are overwritten at :306-307 before the first read at :317,
   because `room_animation_ready` is false on the first pass (:328-331), so the
   garbage is dead. Transcribe it as dead, do not reproduce it — but if a live
   run ever shows a garbled first transition, this is where to look.
7. **Who takes the live measurements**: that `ACTIVATE_FIELD 1` and `2` behave
   as read; that the three-field list appears on the wire as described; that
   nothing intermediate shows between the two dialogs.
