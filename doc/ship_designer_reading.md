# The Ship Designer — reading report (work order 185, part 6)

What the original's Ship Designer shows and does, every sub-dialog, every
way in and out, what happens to a finished design, and — piece by piece —
whether it is on the wire today. Read in orion2re `orionlayer-local`
`4bf152e4`; every citation is `file:line` against that tree. Paths are
relative to `src/game/` unless another root is given (`ext/…` =
`src/ext/`, `OL:` = this repository).

**How it was made, and what was checked.** The reading was drafted by a
read-only agent over `design_main.cpp`, `design.cpp`, `desbox.cpp`,
`design_config.cpp` and their headers, and then checked at the tree before
anything was built on it (the delivery agreement, fundament part 07): the
way in (colbldg.cpp:556-559), Cancel and Build (design_main.cpp:370-386),
the only input delay (design.cpp:869-870), the save
(`Update_Player_Design_`, design.cpp:755), the in-progress struct
(`s_current_design`, orion2.h:702-743 — the draft said 702-747, which is
the next struct's header; corrected), the absence of any design data in
ext/ext_api.cpp, that no other screen writes SCREEN_DESIGN, what the main
page prints (design_main.cpp:20-96) and computes, and the rows each picker
prints (desbox.cpp:2203-2221, :2279, :2395-2402, :2502-2504, :2821). **And
live** (section 10): the blocks open fixes 44 and 45 add were recorded off
a scratch engine and agree with the native screens value for value.

Screen id: `SCREEN_DESIGN = 3` (orion2_consts.h:464); `Screen_Control_`
case SCREEN_DESIGN calls `DESIGN::Design_Screen_()` (mox2.cpp:53-56).
Source files: `design_main.cpp` (the loop, drawing, loading, fields),
`design.cpp` (calculations and click handlers), `desbox.cpp` (the three
sub-dialogs), `design_config.cpp` (the configurable tables).

---

## 1. What the screen shows

### 1.1 Loading (`Load_Design_Screen_Pictures_`, design_main.cpp:505-591)

This runs only on the first entry, the `_first_design_screen_call != 0` branch (design_main.cpp:310-312). All art comes from **DESIGN.LBX**, loaded into `MOX::_screen_seg`:

| DESIGN.LBX entry | global | line |
|---|---|---|
| 0 | `_design_screen_seg` (full-screen background, `Far_Reload_`) | 507 |
| 1, 2 | `_design_icon_lf_arrow_seg`, `_design_icon_rt_arrow_seg` | 508-509 |
| 3, 4, 5 | `_clear_design_button_seg`, `_cancel_design_button_seg`, `_build_design_button_seg` | 510-512 |
| 6..11 | `_design_size_button_seg[0..5]` | 515-517 |
| 6..11 again | `_darkened_size_button_seg[0..5]` (the **same** entries as the row above) | 518-520 |
| 12 | `DESIGN::_dark_build_design_button_seg` | 522-523 |
| 13, 14 | `_plus_button_seg`, `_minus_button_seg` | 526-527 |
| 15, 16 | `_d_scroll_up_button_seg`, `_d_scroll_dn_button_seg` | 528-529 |
| 17, 18 | `_dull_plus_button_seg`, `_dull_minus_button_seg` | 530-531 |
| 19, 20 | `_dull_d_scroll_up_button_seg`, `_dull_d_scroll_dn_button_seg` | 532-533 |
| 21 | `_d_scroll_bar_seg` | 535 |
| 22..25 | beam / missile / bomb / special filter buttons | 537-540 |
| 26, 27 | `_weapons_cancel_button_seg`, `_weapons_accept_button_seg` | 541-542 |
| 28..31 | weapons top, mid and bottom box, `_weapons_selected_seg` | 545-548 |
| 32 | `_weapons_rack_seg` | 551 |
| 33..37 | `_weapons_arc_pict_seg[5]` | 553-555 |
| 38..42 | `_weapons_arc_text_seg[5]` | 556-558 |
| 43..47 | `_weapons_rack_text_seg[5]` | 560-562 |
| 48 | `_weapons_blank_mods_seg` | 564 |
| 49..66 | `_weapons_special_seg[18]` (the modification buttons) | 565-567 |
| 67 | `_system_repl_scroll_bar_seg` | 570 |
| 68..70 | `_system_repl_box_top/mid/btm_seg` | 571-573 |
| 71 | `_system_repl_box_cancel_btn` | 574 |

That makes entries 0..71, 72 in all. `OL:doc/v3_original_gui_construction.md:54` lists DESIGN.LBX with 72 entries.

The same function then:
- allocates `MOX::_design` (an `s_current_design`) and `MOX::_weapon_filter` (40 × `s_weapon_filter_item`) in `MOX::_global_data_seg` (design_main.cpp:576-578);
- loads the tech-description LBX that matches the language: GERTECD, FRETECD, SPATECD, ITATECD, or TECHDESC.LBX for English and anything else (design.cpp:1016-1042). From it, entry 1, records 0..38, go into `MOX::_special_desc_string[i]`, and entry 3, records 0..39, go into `MOX::_weapon_notes_string[i]`. Each record is 100 bytes (design_main.cpp:580-590).

Other resources the screen uses:
- The ship picture: `KEN::Get_Ship_Picture_Seg_` → `Do_Get_Ship_Picture_Seg`, from `ships.lbx` entry `ship_type + color*50` (ken.cpp:389-391, :458-466).
- The ship palette: `KEN::Load_Player_Ship_Palette_`, from `ships.lbx` entry `color*50+49` (ken.cpp:71-80), called at design_main.cpp:296 and :329.
- Default design names: `shipname.lbx` entry 0. The record index is `variant + (race*6 + size)*8` and each record is 16 bytes (design.cpp:1134-1157).
- Every fixed label is a `HAROLD::H_Message_` string, i.e. the HESTRNGS table. The file depends on the language: HESTRNGS / HGSTRNGS / HFSTRNGS / HSSTRNGS / HISTRNGS.LBX (harold.cpp:1525-1558). The lookup is `H_Message_` (harold.cpp:637-648). `MISC::Get_LBX_Message_` is only a copy of `H_Message_` (misc.cpp:156-163), so every "LBX message" id in this screen is a HESTRNGS id. The names are listed in `orion2_str.h:808-908, 1189-1196`.
- The firing-arc words: `KEN::Ken_Get_Text_Message_` 3/4/5/6, from KENTEXT.LBX (design.cpp:1407-1443; ken.cpp:116-118).
- Help texts: HELP.LBX, or GER_/FRE_/SPA_/ITA_HELP.LBX, entry 0, one record per tech_app_id (`EVANHELP::Get_Application_Description_`, evanhelp.cpp:336-354; textbox.cpp help-name switch).
- Music: `JIM::Play_Streaming_Music_(8, -1, 1)`, called on every draw (design.cpp:695).

### 1.2 Drawing order (`Draw_Design_Screen_`, design.cpp:690-696)

1. The background, DESIGN.LBX 0, at (0,0) (design.cpp:691).
2. `Draw_Down_Buttons_` (design.cpp:1238-1277):
   - For every row that holds a weapon but has no active button, the dull minus at (55,y) and the dull plus at (19,y). y starts at 169 and steps by 13 (design.cpp:1239-1254).
   - The dark build button at (544,439) when the build button is absent (design.cpp:1256-1258).
   - Size buttons, drawn in frame 0 through `Reset_Animation_Frame_`. Outside refit, this is every size whose flag is not 1 (design.cpp:1262-1267). In refit, it is only the current size, and the function then returns (design.cpp:1268-1274).
3. `Print_Current_Design_` (design_main.cpp:7-273). Font colours: style 3 is `Get_Mox_Font_Colors_(3,'U','[')`, style 2 is `(2,'U','[')` (design_main.cpp:22-23), and style 4 is `(4,'U','Y')` (design_main.cpp:263-265). Hex coordinates are shown as they appear in the source.
   - **Drive:** the name `_drives[ftl_type].name` in style 3 at (0xEC,0x38) (design_main.cpp:25-27). Then HESTR_17E "^ %d parsecs/turn" at (0xFB,0x47) and HESTR_054 "^ %d combat speed" at (0xFB,0x56), both style 2 (design_main.cpp:29-35).
   - **Armour:** the name at (0xEC,0x6B) (design_main.cpp:37-39). Then HESTR_055 structure points at (0xFB,0x7A) and HESTR_056 armor points at (0xFB,0x89) (design_main.cpp:41-47).
   - **Shield block:** it flashes while the shield field is hovered (design_main.cpp:51-53).
     - Without a shield: HESTR_036 "No Shield" at (0x1B5,0x38), HESTR_057 at (0x1C5,0x47) and HESTR_058 at (0x1C5,0x55) (design_main.cpp:55-61).
     - With a shield: the shield name, HESTR_059 strength (`Shield_Strength_`) and HESTR_05A damage points blocked (design_main.cpp:62-73).
   - **Computer:** the name at (0x1B5,0x61), flashing while hovered (design_main.cpp:75-80). HESTR_05B "^ %d beam attack" at (0x1C5,0x70) (design_main.cpp:82-85).
   - **Beam defence and missile evasion:** HESTR_05C "Beam Defense" at (0x1B5,0x7D), with the value right-aligned at 0x26A. HESTR_05D "Missile Evasion" at (0x1B5,0x89), with the value printed as "%d%%" (design_main.cpp:87-95). Both values come from `INITSHIP::Get_Design_Combat_Bonuses_` over a template built by `Build_Design_Template_` (design_main.cpp:15-16; initship.cpp:1339-1379).
   - **Weapon table:** clipped to the window (0x10,0x9B)-(0x272,0x11C) (design_main.cpp:98-99).
     - Headers at y 0x9C: HESTR_05E Weapon Type at 0x53, 05F Damage at 0xF9, 060 Arc at 0x13C, 030 Space at 0x19E, 185 Cost at 0x167 and 061 Modifications at 0x1DF (design_main.cpp:101-106).
     - Eight rows start at y 0xAA and step by 13. Each row prints the count right-aligned at 0x31 (140). The name, singular or plural, goes at 0x55, with " (ammo)" added for rack weapons (128-138). Then the damage string centred at 0x10B (141-150), the arc centred at 0x149 (152), the space per weapon centred at 0x1B4 (153-161), the cost per weapon centred at 0x179 (162-170) and the modifications string centred at 0x211 (171).
     - The mods and arc strings are indexed with `i` and not `slot` (design_main.cpp:125-126). `_first_weapon_ctr` is only ever set to 0 (design_main.cpp:282, the only write found), so the two indices are the same.
     - When an empty row is hovered, the table adds a message. It is HESTR_17F "Add New Weapon" if `Space_For_Weapon_Replacement_()` finds room. Otherwise it is HESTR_01A (no space at all) or HESTR_018 (no weapon fits) (design_main.cpp:176-194).
   - **Specials table:** clipped to the window (0x11,0x131)-(0x272,0x1B0). Headers HESTR_062 at (0x1E,0x132) and HESTR_038 at (0x118,0x132) (design_main.cpp:197-201). Rows start at y 0x140 and step by 13, with the name at 0x23 and `_special_desc_string[id]` at 0x10E (design_main.cpp:204-228). The hover message is HESTR_180, 01B or 019 (design_main.cpp:230-248).
   - **Ship picture:** centred in the box that starts at (0x27,0x3A) and measures 0x36 × 0x3A (design_main.cpp:253-256).
   - **Hull space:** HESTR_030 "Space" at (0x19,0x81), with `hull_space` right-aligned at 0x6A (design_main.cpp:258-261).
   - **Bottom line, style 4:** HESTR_185 Cost at 0x18, with `Printed_Design_Cost_()` right-aligned at 0x87. HESTR_063 "Space Available" at 0xA3, with `_printed_space_avail` right-aligned at 0x160 (design_main.cpp:266-272). In refit, `Printed_Design_Cost_` returns `AIBUILD::Refit_Cost_(old, new)` (design.cpp:1044-1056).
   - What the fields draw themselves: the name input and the button sprites.
4. `Check_For_Auto_Repeat_` (design.cpp:698-753): while mouse button 1 is held, plus repeats after 4 frames and minus after 5 (design.cpp:713, :735).
5. Music (design.cpp:695).

Flashing colours come from `Set_Flashing_Colors_` (design.cpp:1159-1189).

---

## 2. Controls (`Add_Design_Buttons_`, design_main.cpp:596-708)

The signatures are `Add_Button_Field_(x, y, help, pic, hotkey, sound)` (fields.cpp:361, hotkey = first char, :378) and `Add_Hidden_Field_(x, y, x_end, y_end, hotkey, sound)` (fields.h:403). The trailing `0x28`/`0x29` in these calls is the **sound** argument, not a hotkey. The `/* ( */` comments in design_main.cpp are misleading.

| control | call and rectangle | hotkey | line |
|---|---|---|---|
| 6 hull-size buttons | `Add_Multi_Button_Field_(x1,y1,"",size_seg[i],&MOX::_design_size,i,"",0x29)` when `_add_size_button_flag[i]==1`, otherwise `Add_Hidden_Field_(x1,y1,x2,y2)`. Rects are x 118..227, with y 54-69 / 70-84 / 85-102 / 103-117 / 118-132 / 133-149 for Small .. Doom Star (design.cpp:1093-1132) | none | 597-610 |
| weapon row minus ×8 | `Add_Button_Field_(0x37, y, …minus…)`, only if the slot holds a weapon and count ≥ 2. Otherwise a hidden field (0x37,y)-(0x44,y+12) when a weapon is present | none | 624-632 |
| weapon row plus ×8 | `Add_Button_Field_(0x13, y, …plus…)`, only if the slot holds a weapon and one more still fits. Otherwise a hidden field (0x13,y)-(0x20,y+12) | none | 634-649 |
| weapon row ×8 | a hidden field: (0x10,y)-(0x26F,y+13) for an empty slot, (0x4D,y)-(0x22C,y+13) for a filled one. y starts at 0xA9 and steps by 13. No fields at all when `((i<1) \|\| empty) && !Replacement_Exists_(WEAPON)` | none | 612-663 |
| special row ×8 | a hidden field (0x11,y)-(0x26F,y+13), y from 0x13F in steps of 13, only if `Replacement_Exists_(SPECIAL)` | none | 665-676 |
| picture left / right | `Add_Button_Field_(0x11,0x52)` and `(0x5E,0x52)` | none | 678-679 |
| design name | `Add_Continuous_String_Input_Field_(0x12, name_y, 0x86, h, MOX::_design->name, 15, …)`, max 15 characters | – | 681-691 |
| shield | hidden (0x1B5,0x38)-(0x273,0x5F) | none | 693 |
| computer | hidden (0x1B5,0x61)-(0x273,0x7B) | none | 694 |
| Cancel | button (0x1CD,0x1BB) | ESC (`"\x1B"`) | 696 |
| Clear | button (0x176,0x1BB) | `L` | 697 |
| Build | button (0x223,0x1BB), or `-1000` (absent) when `hull_space < space_used` | `B` | 699-704 |
| debug | hidden (0,0x1D6)-(10,0x1DF) | none | 706 |
| catch-all | hidden (0,0)-(0x27F,0x1DF), sound 0 | none | 707 |

Drive, armour and fuel have **no field**. They are always set to the best researched: `Best_Warp_Drive_`, `Best_Armor_` and `Best_Ship_Fuel_` (design.cpp:31, :39-40, :990-995).

### The input loop (`Design_Screen_`, design_main.cpp:278-500)

Each pass:
1. `Get_Input_` and `Scan_Input_` (350-351).
2. `_changed_design_name` is set once the name differs from the saved slot name (353-361).
3. A click on the name field suppresses the field rebuild (363-368).
4. **Cancel** (370-374): sets `screen_exit_flag=1`, `_temp_star_handle=0` and `_current_screen=_return_screen`. The in-progress design is discarded.
5. **Clear** (376-379): `Clear_Design_()` (design.cpp:986-1014). It resets drive, computer, armour and fuel to the best, and zeroes all weapons and specials. It does **not** touch shield, size, name or picture. There is no confirmation.
6. **Build** (381-386): `Update_Player_Design_(PLAYER_NUM, design_idx)`, then `_current_screen=_return_screen`, `exit=1` and `_temp_star_handle=1`. There is no confirmation.
7. **Debug** (388-390): formats `"cstdes%d.log"` into a local and does nothing else.
8. The four sub-handlers (393-396). They can set `screen_exit_flag=99` (see 3).
9. **Hull size changed** (398-408), i.e. the multi-button wrote `_design_size`:
   - `ship_size` is set to it, `hull_space = _hull_data[size].size`, and a refresh follows;
   - `picture_type` becomes 43 for a Doom Star, otherwise `size*8`.
10. **Plus / minus** (410-439):
    - plus adds 1 if the new `Weapon_Space_` still fits, capped at 99;
    - minus subtracts 1, down to a floor of 1.
11. When a refresh is needed, `Update_Calculated_Design_Data_` runs (441-444), design.cpp:292-315.
12. The fields are rebuilt unless the name field was the input (446-450).
13. **A size field was the input** (452-466):
    - if the flag is below 241, `_changed_design_name=0` and the default name is loaded from shipname.lbx;
    - otherwise `Print_Ship_Size_Error_Message_`.
14. Redraw (468-479). The name is trimmed, and an empty name falls back to the saved slot name (481-486). Then `Release_Time_(2)` (488).
15. When the exit flag is non-zero, the function returns (490-497). Background music is restarted only if `_current_screen != SCREEN_DESIGN` (494-496).

The icon arrows are handled in `Check_Plus_Minus_Buttons_` (design.cpp:953-984):
- `picture_type` cycles within `size*8 .. size*8+7`. A Doom Star does not cycle.
- If the name was not changed by hand, it is reloaded from shipname.lbx.

A right-click arrives as a negative field id:
- On a weapon row it opens `TEXTBOX::Text_Box_` with the weapon's help description (design.cpp:893-899).
- On a special row it does the same with the special's help description (design.cpp:941-949).

---

## 3. Sub-dialogs

**Common pattern:**
- Each sub-dialog is started from inside the design loop.
- Each sets `_current_screen = SCREEN_DESIGN` and `*out_status = 99` (design.cpp:821-823, :841-843, :890-891, :938-940).
- The design loop then redraws (design_main.cpp:475-479) and **returns** (design_main.cpp:490-497) with `_current_screen` still `SCREEN_DESIGN`.
- `Screen_Control_` then calls `Design_Screen_` again. This time `_first_design_screen_call == 0`, so the short branch runs (design_main.cpp:294-309): no reload, no template rebuild, and `_design` is kept.

So after **every** sub-dialog the screen passes through `Screen_Control_` again, and `ext::Tick` runs at mox2.cpp:41.

Each sub-dialog runs its own `Get_Input_` loop. Every one of those calls `ext::Tick(MOX::_current_screen)` (fields.cpp:158-167), which here is 3.

### 3.1 Shield / computer picker (`DESBOX::Generic_Replacement_Box_`, desbox.cpp:1225-1313)

**Trigger** (design.cpp:810-849):
- **Computer.** If `N_Replacements_For_Generic_Item_(COMPUTER)` returns 0, a `GENDRAW::Warning_Box_` shows HESTR_050 "You may not upgrade the ship's computer." That function returns `Best_Computer_` (design.cpp:1462-1472). Otherwise the picker opens.
- **Shield, with a Damper Field on the design.** Warning HESTR_051 (design.cpp:828-832).
- **Shield, with nothing researched.** Warning HESTR_052 (design.cpp:844-847).

**Contents:**
- Choices (desbox.cpp:751-781): all `SHIELD_COUNT` or `COMPUTER_COUNT` rows. Row 0, and any row whose tech_app is researched, is selectable. Every other row is `-1`.
- The box is centred on 640×440. Its height is rows×16 plus the cancel button (desbox.cpp:783-808).

**Fields** (desbox.cpp:810-864):
- One hidden field per selectable row: (bx+10, y)-(bx+600, y+13), y stepping by 14. `-1` rows get `-1000`.
- A cancel button at the bottom right, hotkey ESC (`s__00551120 = "\x1b"`, desbox.cpp:32).
- A catch-all over the box, sound 0.
- A full-screen field with hotkey ESC.

The loop code (desbox.cpp:1244-1247) names these locals `clear_btn_field`, `ok_btn_field` and `box_field`. They are the cancel button, the full-screen field and the box field, in that order.

**Loop** (desbox.cpp:1259-1302):
- **Right-click** (negative input): help via `Draw_Generic_Replacement_Box_Help_` (desbox.cpp:866-942). Help ids 0x2A9-0x2AE and 0x2B4/0x2B5, or `Text_Box_` with the item's description.
- **Cancel:** `chosen=-1`, no change.
- **Full-screen field:** done, and the current item is kept.
- **Row:** done, with that row chosen.

**Return:** the choice is written to `_design->shield` or `_design->computer_type` (desbox.cpp:1304-1310).

**Drawing** (desbox.cpp:1971-1998):
- the top, mid and bottom sprites (DESIGN.LBX 68-70);
- for shields, `Print_Shield_Data_` (desbox.cpp:2333-2426), with headers HESTR_033/034/035, then name, cost and space per row, and "No Shield" 036 for row 0;
- for computers, `Print_Computer_Data_` (desbox.cpp:2428-2534), with headers HESTR_029/02A/02B, then name, "+%d" bonus and cost per row, and "No Computer" 02D for row 0.

The source flags that the shield column centring is swapped (desbox.cpp:2387, :2398).

### 3.2 Weapon picker with arcs, racks and modifications (`DESBOX::Weapons_Replacement_Box_`, desbox.cpp:1315-1600)

**Trigger** (design.cpp:857-901):
- It first calls `Clear_Mouse_Buffer_` and **`Set_Input_Delay_(20)`** (design.cpp:869-870).
- A click on an empty row redirects to the first empty slot (design.cpp:872-879).
- Before the box opens, `_printed_space_avail` and `_printed_cost` are adjusted by the slot's current space and cost (design.cpp:882-884).

**Labels:** arc words from HESTR 0x46 Full, 0x47 Forward Extended, 0x48 Back Extended and 0x49 Rear, plus "360" (desbox.cpp:1327-1333).

**List** (`Weapon_Choices_`, desbox.cpp:1643-1762):
- Row 0 is "No Weapon", with cost 99999. Every weapon 1..39 with a researched tech_app follows, if its filter is on:
  - type 0 (beam) under the beam filter;
  - types 1 and 2 (missile, torpedo) under the missile filter;
  - type 3 (bomb) under the bomb filter;
  - types 4 and 5 (fighter, special) under the special filter.
- The type enum is `orion2_consts.h:1328-1334`.
- A tractor beam is offered only if the design does not already carry one (desbox.cpp:1681-1684, :1796-1813). The list stops at 40 rows.
- The list is sorted by research cost, **descending** (`qsort_by_research_cost_` returns `b - a`, desbox.cpp:2028-2032; sort call desbox.cpp:1362-1364).
- Rows that fit are marked `replacement_item_unlocked` (`Space_With_Weapons_`, desbox.cpp:1815-1831).
- If nothing fits, `_temp_string` receives HESTR_045. The caller at desbox.cpp:1360 ignores that return value.

**Box geometry:** width 0x27C, x = 2, y centred and at least 0x26 (desbox.cpp:956-977).

**Fields** (`Add_Replacement_Weapon_Fields_`, desbox.cpp:284-540):
- **Rows:** up to 10 hidden row fields, (bx+0x1C, y)-(bx+0x256, y+0xC), y stepping by 0xE (desbox.cpp:310-330).
- **Scrolling:** with more than 10 rows, a scroll-up button (`-`), a scroll field and a scroll-down button (`+`) (desbox.cpp:334-374).
- **Filters:** hidden fields with hotkeys `B`, `M`, `O` and `S` (desbox.cpp:376-413).
- **Arcs or racks:** once a weapon is chosen, 5 arc fields (beam type 0) or 5 rack fields (rack weapons) (desbox.cpp:415-457).
- **Arc/rack box:** a hidden field over the whole box (desbox.cpp:459-468).
- **Modifications:** one hidden field per shown modification (desbox.cpp:470-492). The positions come from `Get_Weapon_Mod_Field_XYs_`: two columns at x 233 and 386, y = (n/2)*17 + offset + 70 (desbox.cpp:2123-2182).
- **Cancel:** hotkey ESC (`s_space="\x1b"`, desbox.cpp:31) (desbox.cpp:494-501).
- **Accept:** hotkey `A`, only when `Weapon_Choice_Valid_`. Otherwise it is a hidden field (desbox.cpp:503-525).
- **Catch-all** over the box (desbox.cpp:527-534).
- **Full-screen field** with hotkey ESC (desbox.cpp:536).

**Loop** (desbox.cpp:1397-1593):
- **Full-screen field or cancel:** closes with no change (1403-1404). Right-click on cancel: help 0x2B0 (1405-1407).
- **Arc click:** sets `_weapon_replacement_arcs = FORWARD << i`. If the arc is marked invalid, the message is HESTR_04B instead (1413-1422).
- **Rack click:** sets arc 360 and `_weapon_replacement_rack = i`. If the rack is marked invalid, the message is HESTR_04C instead (1423-1432).
  - `_valid_arcs_racks[]` is only ever written with 1, and only for the fields that are added (desbox.cpp:436, :450). So the two "invalid" messages have no path in this code that reaches them.
- **Filter toggles** (1437-1445). The list is rebuilt and re-sorted, and the selection is kept (1525-1557).
- **Modifications:** right-click shows `Print_Weapon_Mod_Help_Description_`, help records 400 and 400+mod (desbox.cpp:1923-1949). A left-click on a valid mod toggles it. Heavy Mount (1) and Point Defense (2) exclude each other (1447-1458).
  - Which mods a weapon type offers is a mask (`Mod_Allowed_On_Weapon_Type_`, desbox.cpp:2073-2096): beam 0x01FE, missile 0x3E00, torpedo 0x6520. Other types get none.
  - Validity (`Valid_Modifications_`, desbox.cpp:1187-1223) is 1 when valid, 0xFE when the weapon does not allow the mod, 0xFD for Emissions Guidance without the tech, and 0xFA when the miniaturisation level is too low. The `New_Mod_Space_` results are thrown away (1200, 1214), so space is never checked there.
  - `Should_Add_Mod_` shows only status 1 (or 0xF9/0xFB/0xFC, which nothing produces) (desbox.cpp:2063-2071).
  - `Print_Weapon_Modification_Message_` has messages for 0xF9 (HESTR_03A), 0xFA (03B/03C), 0xFB (03D), 0xFC (03E), 0xFD (03F) and 0xFE (040) (desbox.cpp:667-728). It is only reached for fields that exist and have status > 0xF8 (1505-1509). Since fields exist only for status 1, those messages are effectively unreachable.
- **Row click** (`Scan_Replacement_Fields_`, desbox.cpp:542-589):
  - Row 0 ("No Weapon") clears the slot and closes (desbox.cpp:1466-1474 → `Update_Weapon_Replacement_` with choice 0 → `DESIGN::Clear_Weapon_Slot_`, desbox.cpp:594-602; design.cpp:1724-1746, which shifts the later slots up).
  - Clicking the row that is already chosen commits it (desbox.cpp:1473-1474).
  - Clicking another row selects it and resets mods to 0, arc to FORWARD for a beam or 360 otherwise, and rack index to 1 (desbox.cpp:1475-1494).
  - Right-click on a row: help 0x2B2 for "No Weapon", otherwise `Text_Box_` with the description (desbox.cpp:1495-1503).
- **Click on the arc/rack box:** with no weapon chosen, HESTR_04E. For types 3/4/5, HESTR_04F "%ss have built-in 360 arc capability" (1511-1523).
- **Scroll** buttons (1559-1567).
- **Accept** (1569-1571) → `Update_Weapon_Replacement_` (desbox.cpp:591-665):
  - first `Weapon_Choice_Valid_` (desbox.cpp:2098-2121); on failure a `Message_Box_`;
  - then it sets type, count 1, specials from the mod toggles (desbox.cpp:2034-2046), arc, ammo (`Missile_Rack_Quantity_(rack)`), space and cost;
  - if it replaces a weapon, the count becomes old_space / new_space, clamped to 1..99 (647-659);
  - then `Update_Calculated_Design_Data_` and exit.
  - `Weapon_Choice_Valid_` tests `_weapon_replacement_arcs == -1` (desbox.cpp:2106). The code only ever resets arcs to `WEAPON_FIRING_ARC_NONE` (0) (desbox.cpp:1348, 1467, 1881). So HESTR_044 "Beam weapons must have at least one arc" is not produced by that test.
- **Exit** (desbox.cpp:1595-1599).

**Drawing:** `Draw_Weapons_Replacement_Box_` (desbox.cpp:1006-1072) draws:
- the table through `Print_Main_Weapon_Box_` (desbox.cpp:2184-2331), with headers HESTR 0x2E/0x2F/0x30/0x2B/0x31 and rows of name "(n)", damage, cost, space and the note from `_weapon_notes_string`. The "(n)" is computed as `0 / weapon_space`, which the source calls a kept original bug (desbox.cpp:2256-2266);
- the rack box (desbox.cpp:1119-1138) or the arc box (desbox.cpp:1140-1167);
- the modification box (desbox.cpp:1764-1794);
- the four filter buttons, whose status is the animation frame (desbox.cpp:1057-1069).

### 3.3 Special-system picker (`DESBOX::Special_Systems_Box_`, desbox.cpp:99-283)

**Trigger** (design.cpp:909-951). A click on an empty row redirects to the first empty slot (921-928). The printed cost and space are adjusted first (930-933).

**Choices** (desbox.cpp:34-97): row 0 is "No Special", then every special 0..38 whose tech_app is researched. Items already on the ship are marked selected (59-70).

**Box geometry** (desbox.cpp:2588-2612): rows×16 + cancel + 20, centred on 640×440.

**Fields** (desbox.cpp:2662-2763):
- 10 row fields, (bx+25, by+89+16i)-(bx+584, +16);
- with more than 10 rows, a scroll field and up/down buttons (`-`/`+`);
- a cancel button with hotkey ESC;
- a catch-all over the box;
- a full-screen field with hotkey "".

**Loop** (desbox.cpp:147-272):
- **Row 0:** removes the special from the slot (`Clear_Special_System_Slot_`, which shifts the later ones up, design.cpp:1685-1697) (desbox.cpp:171-175).
- **Any other row:**
  - it checks exclusions (`Special_System_Exclusion_`, `_specials[].exclude[6]`, desbox.cpp:2614-2645) and `Items_Selected_ < 8`;
  - if the item is not already selected, or is the one in the current slot, it is added (192-195);
  - an exclusion instead gives `Warning_Box_` HESTR_042 (same name) or HESTR_043 (conflict, with "a"/"an") (196-210);
  - an item already on the ship gives HESTR_041 (211-216).
  - Space is **not** checked on click. The computation at 181-184 is thrown away. Space only changes the row colour (desbox.cpp:2831-2846).
- **Right-click on a row:** help 691 for "No Special", otherwise `Text_Box_` (218-226).
- **Scroll** (235-242).
- **Cancel or full-screen field:** closes with no change (244-245). Right-click on them: help 689 or 687 (246-250).
- **Exit** (274-282): the scroll position is stored in `_design->special_system_scroll_*`, then `Update_Calculated_Design_Data_`.

**Drawing:** `Draw_Special_Systems_Replacement_Box` (desbox.cpp:2563-2586) calls `Print_Special_System_Data_` (desbox.cpp:2765-2925). Headers are HESTR 0x37/0x30/0x2B/0x38. Rows show name, space, cost and description. Row 0 is 0x39 "No Special" with "0" and "0". Space and cost come from `System_Added_Cost_And_Space_` (desbox.cpp:2963-2984).

### 3.4 Hull size, name, clear/cancel/build and message boxes

- **Hull choice:** not a dialog, just the six multi-buttons (§2).
  - `Add_Size_Button_` returns 0xF4 in refit and 1 otherwise (design.cpp:1474-1479).
  - `Print_Ship_Size_Error_Message_` (design.cpp:1279-1324) maps 0xF1/F2/F3/F4/F5 to HESTR 000-006 / 001-006 / 007-00C / 00D / 00E, shown through `GENDRAW::Message_Box_`. Only 0xF4 → HESTR_00D "You may not change hull sizes while refitting a ship" can happen, because nothing produces the other codes.
  - The 0xF5 branch would format a planet name when `_return_screen == 0x19` (`SCREEN_QUEUE_POPUP`=25, `orion2_consts.h:482`).
- **Name entry:** the continuous string field in the main screen (§2). There is no separate dialog.
- **Clear, Cancel, Build:** no confirmation box (§2).
- **Message and warning boxes:** listed above, all with HESTRNGS ids. `Text_Box_` help comes from HELP.LBX.

---

## 4. Ways in and out

**In.** The only write of `SCREEN_DESIGN` outside the design and desbox code is **colbldg.cpp:556-559**, when the build popup (`COLBLDG::Build_Queue_Popup_`, colbldg.cpp:458; dispatched as `SCREEN_QUEUE_POPUP`, mox2.cpp:140-143) closes with `_return_to_build_popup_from_custom_design != 0`. The loop breaks on that flag at colbldg.cpp:535-537. Then:

```
MOX::_first_design_screen_call = 1;
MOX::_return_screen = MOX::_current_screen;   // = SCREEN_QUEUE_POPUP
MOX::_current_screen = SCREEN_DESIGN;
```

Three routes set the flag, and each sets `_temp_star_handle`, which becomes `design_idx` (design_main.cpp:280):

1. **The "Design" button** of the build popup: `_fields[5]`, button (561,379), hotkey `ESTRINGS::E_Strings_(251)` (colbldg.cpp:361). It is absent when `strategic_combat_flag != 0` (colbldg.cpp:356-358).
   - Clicking it switches the cursor to "which ship", `_field_mode=1` (colbldg.cpp:1577-1579).
   - Clicking a ship-design row in the military list then sets the flag and `_temp_star_handle = Colony_Production_Ship_Design_Index_(id)`, which is design slot 0..4 (colbldg.cpp:1703-1709; colbldg.h:37-39; list i<5 at colbldg.cpp:221-240).
2. **The "Refit" button** `_fields[4]`, (492,379) (colbldg.cpp:360), and then `COLREFIT::Colony_Refit2_Popup_`. When it returns **-2** (its row `_fields[11]`, colrefit.cpp:572-577, :623-629):
   - the ship's own design is copied into `ship_designs[5]`;
   - `_refit_ship=1` and `_temp_star_handle=5` (colbldg.cpp:1599-1604).
   - A return of -3 (an existing design picked) does **not** open the designer (colbldg.cpp:1594-1598; colrefit.cpp:545-556).
3. **Adding a COLONY_PRODUCTION_CUSTOM_DESIGN** combat product that is not a Doom Star sets `_temp_star_handle=4` (colbldg.cpp:2080-2089).
   - No code was found that adds `COLONY_PRODUCTION_CUSTOM_DESIGN` to `_military_indexes`. Its only uses are colbldg.cpp:645, 856, 2061 and 2346, and colsum.cpp:1249.

The galaxy map, colony screen, fleet screen and others were **not found** to set `SCREEN_DESIGN`. A grep for `SCREEN_DESIGN` returns only the lines already cited.

**Out.**
- **Cancel** (ESC) or **Build** (`B`): `_current_screen = _return_screen`, which is `SCREEN_QUEUE_POPUP` (design_main.cpp:370-386). Cancel sets `_temp_star_handle=0` and Build sets it to 1.
- Back in the popup, `Evaluate_Input_` (colbldg.cpp:1444-1456) clears the flags. It then sets `_refit_ship=0` when `_temp_star_handle==0`, or calls `Add_Refited_Ship_To_Queue_()` when `_refit_ship` is set.
- No `_global_esc` handling was found in the design code. ESC works only through the Cancel hotkey.
- Leaving through `Screen_Control_` after a sub-dialog re-enters the same screen (§3).

---

## 5. What happens to a finished design

`Update_Player_Design_(player_idx, design_idx)` (design.cpp:755-801) writes into `MOX::_player[player_idx].ship_designs[design_idx]`. That is `struct s_ship_design ship_designs[6]` (orion2.h:1809), with `s_ship_design` at orion2.h:1732-1748 and `s_ship_weapons` at orion2.h:1723-1730, packed(1).

The fields written:
- name, trimmed, or the old name if empty (757-767);
- size, shield_type, ftl_type, computer_type, armor_type (769-773);
- special_device_flags: 5 bytes, one bit per special (775-783);
- ship_weapon[8]: type, count, current_count = count, firing_arc, specials, ammo (785-792);
- picture_num, cost = `total_cost` (int16), date_of_design = `_stardate` (794-796);
- combat_speed, with `_use_augmented_engines=0` so without the augmented-engines bonus (798-799);
- speed = `Get_FTL_Speed_` (800).

`ship_type` and `previous_owner` are **not written**.

What is computed while editing (`Update_Calculated_Design_Data_`, design.cpp:292-315):
- **Component costs** (`Design_Template_Costs_`, design.cpp:317-369), each through `Cost_Given_M_Level_` (1491-1501) with `Tech_Level_` (1370-1383) and `Miniaturization_Level_` (1657-1677).
- **Space** (`Design_Template_Space_Requirements_`, design.cpp:402-449), through `Space_Given_M_Level_` (1534-1544) and `Weapon_Space_` (614-654).
- **total_cost** (`Total_Design_Cost_`, design.cpp:371-400): hull + computer + drive + armour + shield + weapons + specials, reduced by government (`Cost_Reduction_For_Govt_Type_`, design.cpp:474-495, from `traits[TRAIT_CURRENT_GOVERNMENT]`).
- **space_used** (design.cpp:580-600).
- **hull_space** (design.cpp:281-290), +25 % with Megafluxers (design_config.h:31-34).
- The counts `_n_weapons_loaded` and `_n_special_systems`.

**Limits:**
- 8 weapon slots and 8 special slots;
- counts from 1 to 99;
- a name of 15 characters (16 bytes);
- **6 design slots**, of which the popup offers 0..4 (colbldg.cpp:221).

There is no "list full" case in the design code. The screen always overwrites the slot it was given (`_temp_star_handle`). Slot 5 is scratch for refit (and for colony, outpost and transport ships, colbldg.cpp:2068-2076), and slot 4 is the Custom Design route.

Cancel discards the edit. `_design` is never written back, and the slot keeps its previous bytes.

---

## 6. Globals and structures that hold the in-progress design

- **`MOX::_design`**: `s_current_design*` (mox.h:101). The struct is at orion2.h:702-743. It holds name[16], shield / cost / space, ftl_type, drive_speed / cost, base_space, base_combat_speed, computer_type / cost, fuel_type, armor_type / cost, weapon_type / count / firing_arc / specials / cost / space / ammo [8], special_devices / cost / space [8], ship_size, picture_type, hull_space, space_used, total_cost, show_help, num_weapon_slots, num_special_slots, replacement_item_unlocked[40] and the special scroll state. It is allocated in `_global_data_seg` (design_main.cpp:577).
- **MOX, main screen** (mox.h):
  - `_design_size` (211), the multi-button target;
  - `_design_name_field` / `_design_cancel_button` / `_design_clear_button` / `_design_build_button` (246-249);
  - `_design_ship_size_field[6]` (419);
  - `_weapons_count_plus_button[8]` / `_minus_button[8]` (417-418), `_weapons_field[8]` (185), `_weapons_clear_button[8]` (451);
  - `_special_system_field[8]` (208), `_special_system_clear_button[8]` (452);
  - `_ship_icon_lf_button` / `_rt_button` (489-490);
  - `_first_weapon_ctr` (265), `_first_special_system_ctr` (207);
  - `_n_weapons_loaded` (153), `_n_special_systems` (154);
  - `_scanned_field` (174), `_temp_star_handle` (756), `_return_screen` (170);
  - `_first_design_screen_call` (210), `_refit_ship` (244), `_draw_design_screen_to_back` (243), `_original_cost` (245, written at design_main.cpp:314, no reader found).
- **MOX, sub-dialogs:**
  - `_design_screen_replacement_type` / `_slot` (183-184), `_design_screen_replacement_item` (352);
  - `_design_choice_items[40]` (88), `_design_choice_item_selected[40]` (206);
  - `_weapon_filter` (459), `_special_desc_string[39]` / `_weapon_notes_string[40]` (460-461);
  - `_scroll_bar` (48), `_repl_fields[10]` (85);
  - `_weapon_mod_field_status[15]` (82), `_weapon_mod_fields[15]` (89), `_weapon_arc_field[5]` / `_weapon_rack_field[5]` (90-91);
  - `_beam_filter_button` (93), `_replacement_box_accept_button` (96);
  - `_special_scroll_up_button[2]` / `_dn_button` (201, 152).
- **DESIGN** (design.cpp:4-20): `_repeat_count`, `_replacement_wait_ctr`, `_design_size_field` (only ever set to -1000), `_use_augmented_engines`, `_printed_space_avail`, `_design_shield_replacement_field`, `_design_computer_replacement_field`, `_printed_cost`, `_changed_design_name`, `_add_size_button_flag[6]`, plus three sprite pointers.
- **DESIGN configuration** (design_config.cpp:6-47):
  - `_missile_x3_shot`, `_alternative_refit`, `_design_button_computer` / `_shield` (whether the template keeps the saved computer and shield or takes the best, design.cpp:35-43);
  - the miniaturisation tables and `miniaturization_categories[212]`;
  - the missile rack tables.
  - Several of these are settable from orion2re's config (`src/config/generated/config.cpp:9251, 9267, 9353, 9363, 9378`). So are shield cost, space and class (`TECHDATA::_shields[...]`, same file) and the government cost reduction (config.cpp:5960-5961).
- **DESBOX** (desbox.cpp:5-28): `_weapon_replacement_mods`, `_weapon_replacement_arcs`, `_weapon_replacement_rack`, `_field_item_chosen` / `_scanned`, the box geometry, the four filter statuses, `_valid_mods[16]`, `_valid_arcs_racks[5]`, and others.

---

## 7. Input delay

`fields::Set_Input_Delay_(20)` at **design.cpp:870**, in `Check_Weapon_Fields_`, right before `Weapons_Replacement_Box_` opens. It is the only call in design.cpp, design_main.cpp and desbox.cpp.
- It sets `_input_delay` and flushes the mouse buffers (fields.cpp:143-147).
- `Get_Input_` then returns 0 for 20 calls **before** `ext::Tick` is reached (fields.cpp:158-167).

---

## 8. The wire question

What the engine sends (ext/ext_api.cpp):
- **`SerializeState`** (ext/ext_api.cpp:94-632), sent on every `Tick`. It carries the screen id and `_previous_screen` (100-101), `_stardate`, `_PLAYER_NUM`, the counts, `s_settings` (120), **all 8 `s_player` records in full** (121-124), stars, ships, colonies, planets, nebulas, leaders, antarans and ship icons, the new-game variables, and then the optional blocks FSEL, FLTS (SCREEN_FLEET), OFFS (SCREEN_OFFICERS), INFS (SCREEN_INFO), COLS / CBLD / CEVT / CPRD (SCREEN_COLONY / QUEUE_POPUP), BLDQ and BLDL (SCREEN_QUEUE_POPUP).
- **No block for `SCREEN_DESIGN`.** A grep of ext_api.cpp for `SCREEN_DESIGN`, `DESIGN::`, `DESBOX::` and `_design` finds nothing.
- **`SerializeFields`** (ext/ext_api.cpp:636-650) sends index, rect, type and hotkey for every field.
- **`SerializeVisual`** (ext/ext_api.cpp:704-719) sends the 640×480 framebuffer and palette.
- `Tick` runs from `Screen_Control_` (mox2.cpp:41) and from every `Get_Input_` (fields.cpp:167), sub-dialogs included, always reporting screen 3.

What the HD client reads:
- `OL:core/game_state.py` keeps `settings_raw` (196) and `player_raw[8]` (203-205), with the sizes at :16-17.
- `OL:core/structs/player.py` names:
  - `tech_fields` @296 u8[83]
  - `tech_applications` @379 u8[212]
  - `ship_designs` @906 u8[594], a raw array
  - `race` @37
  - `traits` @2308 (a constant with a reader, not a spec field, player.py:235, :312-316)
  - `design_name()` / `design_cost()` for name@0 and cost@94 within each 99-byte design (player.py:329-348)
- `OL:core/structs/ship.py` names every `s_ship_design` member offset (name 0 … date_of_design 97) inside `s_ship_data`, plus `WEAPON_SPEC` for `s_ship_weapons` (ship.py:110-124, :169-176). Both are verified. They are not wired to `player.ship_designs`.
- `OL:core/structs/unverified.py:54-65` holds `hyper_advanced_tech` @640, single-source.
- `OL:core/structs/settings.py:70` names `language` @210.

**Conclusion:**
- Nothing the screen holds **while editing** is on the wire. `MOX::_design` and all DESIGN and DESBOX globals live only in engine memory.
- The saved **design slots** are on the wire, as bytes inside `s_player`. After Build, the result shows up in `player.ship_designs[design_idx]`.
- Which slot is being edited (`_temp_star_handle`) and whether it is a refit (`_refit_ship`) are **not** on the wire.
- Which of the three sub-dialogs is open is not on the wire as data. It can only be inferred from the field list or the framebuffer.

---

## 9. What the OrionLayer tree already has

- `OL:core/screen_names.py:37`: `3: ("DESIGN", "ship_design")`. There is **no** `screens/ship_design/` directory (`ls` fails), and no screen declares `GAME_SCREEN_ID = 3` (grep). Screen 3 therefore falls back to the original framebuffer.
- `OL:screens/build_queue/`:
  - bqwire.py:52 has `DESIGN = (TYPE_BUTTON, 561, 379)` and :51 `REFIT = (TYPE_BUTTON, 492, 379)`;
  - screen.py:15 and :169 list and forward the Design and Refit buttons;
  - bqdraw.py:116 draws them;
  - layout.json:8 has `"design": "DESIGN"` and :17 `omission_design_stats` (the nine stat lines are not drawn because the weapon and system name tables are missing).
- The BLDQ block (ext/ext_api.cpp:552-564) sends `_field_mode` (1 means "pick a design"), and `OL:core/game_state.py:105` stores it.
- `OL:core/shipparts.py:1-120`: names for specials, armour, shields, weapons, hulls and hull plurals from TECHNAME.LBX (TABLES at :68-75). It has **no** computers, drives, fuel, weapon mods or weapon plurals.
  - `OL:tools/techname_extract.py` writes `shipparts_<lang>.json` and `techfields_<lang>.json` (field and application names). `OL:assets/shared/names/shipparts_en.json` exists.
- `OL:core/structs/player.py:202-213, :329-348`: `ship_designs` plus the name and cost readers.
- `OL:core/structs/ship.py`: the verified s_ship_design and s_ship_weapons offsets, a `weapons()` reader (:183-203) and `special_bits()` (:205-209).
- `OL:core/kentext.py`: the arc words, transcribing `Weapon_Arc_String_`'s order (:1-30).
- `OL:core/hestrings.py` plus `hestrings_en.json`: the HESTRNGS table, i.e. every label and message id this screen uses.
- `OL:core/prodname.py:32-35, :89-118`: design-name production ids. Its docstring at :34 still says the design name "is not on the wire", which player.py:202-213 has since superseded.
- Engine tables transcribed on the HD side:
  - `OL:core/monsterhull.py:49-54`: `_hull_data` armor_hp and structure_hp, and `_armor.ships_bonus`;
  - `OL:core/research.py:27`: `_technology_fields[].cost`;
  - `OL:core/researchlist.py:52-68+`: `NEXT_FIELD` (next_field_id) and `APP_FIELD` (tech_field_id).
  - **Not found** on the HD side: `_weapons`, `_shields`, `_computers`, `_drives`, `_specials`, `_weapon_modifications`, hull size and cost, `_technology_applications[].type`, the miniaturisation tables, and the TECHDESC.LBX, shipname.lbx and DESIGN.LBX loaders. A grep of core/, tools/ and screens/ for techdesc, shipname and DESIGN.LBX finds only a hit in `assets/shared/help/help_en.json`.
- `OL:tools/help_extract.py` exists (HELP.LBX), which is the source of the tech descriptions `Text_Box_` shows.
- `OL:doc/briefs/185-work-order-open-items-ship-designer-audience.md:68-86`: this work order (parts 6-8).

---

## Final table

| piece | what it is | source (file:line) | on the wire today | reconstructable on HD side |
|---|---|---|---|---|
| in-progress design | `MOX::_design`, s_current_design | orion2.h:702-743; mox.h:101; design_main.cpp:577 | **no**: no SCREEN_DESIGN block; heap in `_global_data_seg` | partly: only its start state (= saved slot, with best drive/armour/fuel and optionally best computer/shield, design.cpp:22-103). Every edit after that: no |
| edited slot index | `_temp_star_handle` → `design_idx` | design_main.cpp:280; colbldg.cpp:1604, :1707, :2086 | **no** | partly: the HD client knows which popup row it clicked (BLDQ `_field_mode`, ext_api.cpp:563) |
| refit flag | `MOX::_refit_ship` | mox.h:244; colbldg.cpp:1597-1601 | **no** | partly: the HD client knows it clicked Refit and then the custom row |
| hull size (edited) | `_design->ship_size`, `_design_size` | design_main.cpp:398-408 | **no** | no |
| hull size (saved) | `ship_designs[i].size` @+16 | orion2.h:1734 | **yes**: player @906+99i+16; offset named by ship.py SPEC "size" 16 (for s_ship_data.d); player.py names only the raw u8[594] | yes (bytes present) |
| each weapon slot (edited) | `_design->weapon_*[8]` | orion2.h:724-730 | **no** | no |
| each weapon slot (saved) | `ship_weapon[8]` @+28, 8 bytes each | orion2.h:1723-1730, :1742 | **yes** in player bytes; offsets in ship.py WEAPON_SPEC (:169-176), not wired to player designs | yes |
| shield / computer / drive / armour (edited) | `_design->shield`, `computer_type`, `ftl_type`, `armor_type` | orion2.h:704, 712, 719, 722 | **no** | drive / armour / fuel: yes (always the best, from `tech_applications` plus the component tables). Shield / computer: no |
| shield / computer / drive / armour (saved) | s_ship_design @+18/+21/+19/+22 | orion2.h:1736-1740 | **yes** (player bytes; offsets named in ship.py SPEC) | yes |
| specials (edited) | `_design->special_devices[8]` | orion2.h:732 | **no** | no |
| specials (saved) | `special_device_flags[5]` @+23 | orion2.h:1741; design.cpp:775-783 | **yes** (player bytes; ship.py `special_device_flags` 23, `special_bits()`) | yes |
| name (edited) | `_design->name[16]` | orion2.h:703; design_main.cpp:688-691 | **no** | no |
| name (saved) | `ship_designs[i].name` | orion2.h:1733 | **yes**: `player.design_name()` (player.py:335-340), verified | yes |
| default names | shipname.lbx entry 0, record `variant+(race*6+size)*8` | design.cpp:1134-1157 | no (LBX); race is on the wire (player @37) | partly: needs a shipname.lbx extractor (none found) |
| picture | `picture_type` (edited), `picture_num` @+92 (saved) | orion2.h:737, :1743 | edited: **no**; saved: **yes** (ship.py 92) | saved: yes. Art: ships.lbx `type+color*50` (ken.cpp:458-466); color is on the wire only as raw player byte 38 (player.py `color`) |
| available computers / shields | `Generic_Replacement_Box_Choices_` | desbox.cpp:751-781 | **no**, but `tech_applications` is **yes** (player.py @379, verified) | partly: needs `_shields/_computers[].tech_app_id` (engine table, not transcribed) |
| available weapons | `Weapon_Choices_` (+ filters, tractor rule, research-cost sort) | desbox.cpp:1643-1762 | **no** (derived) | partly: needs `_weapons[]` (type, tech_app_id) and `_technology_fields[].cost` (the latter is in research.py) |
| available specials | `Special_System_Choices_` | desbox.cpp:34-97 | **no** | partly: needs `_specials[].tech_app_id` and `exclude[6]` |
| allowed weapon mods | `Valid_Modifications_`, `Mod_Allowed_On_Weapon_Type_` | desbox.cpp:1187-1223, :2073-2096 | **no** | partly: needs `_weapons[].available_mods`, `_weapon_modifications[].level`, and the miniaturisation level (tech_fields @296 yes, NEXT_FIELD / APP_FIELD in researchlist.py, hyper_advanced @640 unverified) |
| per-component cost | `Design_Template_Costs_`, `Cost_Given_M_Level_` | design.cpp:317-369, :1491-1501; design_config.cpp:20-27, :75-80 | **no** | partly: formula transcribable, but needs cost tables and config-overridable multipliers and shield costs (config.cpp:9251 ff.) |
| per-component space | `Design_Template_Space_Requirements_`, `Weapon_Space_` | design.cpp:402-449, :614-654, :1534-1544 | **no** | partly: same as above, plus `miniaturization_categories[212]` |
| total cost printed | `Printed_Design_Cost_` (refit: `AIBUILD::Refit_Cost_`) | design.cpp:1044-1056, :371-400, :474-495 | **no** for the edited design; saved `cost` @+94 **yes** (`design_cost()`) | partly: needs the tables, government reduction (traits @2308 on the wire; `government_bonuses` is config) and `Refit_Cost_` |
| space available / hull space | `_printed_space_avail`, `hull_space` | design_main.cpp:305, :470; design.cpp:281-290 | **no** | partly: hull size table (not transcribed) plus Megafluxers from `tech_applications` |
| combat speed / structure / armour pts / shield strength / beam def / missile evasion | the stat lines | design.cpp:189-226, :497-528, :558-568; initship.cpp:1339-1379, :402-417 | **no** for the edited design; saved `combat_speed` @+96 **yes** | partly: hull hp and armour bonus are in monsterhull.py; drives and shields tables are not |
| drive name / armour name / shield name / weapon names | TECHNAME.LBX | shipparts.py:68-75 | names not on the wire (LBX) | armour / shield / weapon / special: yes (shipparts). Computer / drive / mod names and weapon plurals: no (not extracted) |
| special descriptions / weapon notes | TECHDESC.LBX entries 1 and 3 | design_main.cpp:580-590; design.cpp:1016-1042 | no | no (no extractor found) |
| labels and messages | HESTRNGS ids | orion2_str.h:808-908, :1189-1196 | no (LBX) | yes (`core/hestrings.py`, `hestrings_en.json`) |
| arc words | KENTEXT 3-6 | design.cpp:1407-1443 | no | yes (`core/kentext.py`) |
| help texts | HELP.LBX records | evanhelp.cpp:336-354 | no | yes (`tools/help_extract.py`) |
| screen art | DESIGN.LBX 0..71 | design_main.cpp:505-575 | no; the framebuffer is (ext_api.cpp:704-719) | yes (user's LBX; no DESIGN.LBX extractor found yet) |
| design list (5 + 1 slots) | `player.ship_designs[6]` | orion2.h:1809; colbldg.cpp:221 | **yes** (player @906, 6×99) | yes |
| sub-dialog open / which | out_status 99 path, DESBOX loops | design.cpp:819-823, :887-891, :936-940 | **no**: screen stays 3; only the field list and framebuffer differ | partly: from the field list (ext_api.cpp:636-650) |
| sub-dialog selection state | `_field_item_chosen`, `_weapon_replacement_*`, `_weapon_mod_field_status`, filter statuses, `_scroll_bar` | desbox.cpp:5-28; mox.h:48, :82 | **no** | no |
| field rects / hotkeys | every Add_*_Field_ above | design_main.cpp:596-708; desbox.cpp:284-540, :810-864, :2662-2763 | **yes** (`SerializeFields`, index / rect / type / hotkey) | yes (as is) |
| game config affecting the numbers | miniaturisation, `_design_button_*`, shield table, megafluxers, x3 racks, government reduction | design_config.cpp:6-47; config.cpp:5960, 9251-9378 | **no** | partly: only if the HD client reads the same orion2re config file (no reader found) |

---

## 10. With open fixes 44 and 45 — recorded live (work order 185)

Both fixes were written in a scratch worktree of `4bf152e4` (never on
`orionlayer-local`), built, and run on the virtual display with SAVE4
(`~/orionlayer-fixtures/evidence/work_order_185/P6_design_record*`, each
start guarded and verified identical). The way in was the one the source
names: the colony screen's CHANGE, the build popup's Design button
(`field_mode` 1 on BLDQ), then a ship-design row (product `-50 - slot`).

| step | reported id | block | agrees with the native screen |
|---|---|---|---|
| the designer, slot 0 "Scout" | 3 | DSGN | space 25, space available 13, cost 25, 2 parsecs, 16 combat speed, 8 structure, 8 armor points, +25 beam attack, beam defense +80, missile evasion 0 %, special 11 (Extended Fuel Tanks) — every value the native page prints |
| the shield field, nothing researched | 3 | DSGN | the warning box "You may not upgrade the ship's shield." (HESTR_052) — no picker, as the source says; its full-screen field ended it |
| the designer, slot 1 "Rafale" | 3 | DSGN | four Nuclear Missiles and three Nuclear Bombs with their engine-formatted damage ("8", "3-12") and "no modifications" |
| the computer field | **54** | DSGN + DSBX (generic, 6 rows) | row 1 the Electronic Computer, cost 8, bonus 25; rows 2-5 not researched (-1) |
| the first weapon row | **55** | DSGN + DSBX (weapon, 4 rows) | No Weapon 0/0/0, Nuclear Missile 8/0/1, Nuclear Bomb 3-12/1/3, Laser Cannon 1-4/5/10 — the native picker's rows, number for number |
| the first special row | **56** | DSGN + DSBX (special, 4 rows) | three specials with their cost and space |
| Cancel | 25 | none | the build popup; DSGN gone |

Two things the recording taught, written down so the HD screen does not
re-learn them: **the weapon picker's list is not `_design_choice_items`** —
its rows go through `DESBOX::Weapon_Index_(row)`, so DSBX carries the
weapon id per row (`extra`) beside the item; and **every "may not upgrade"
answer is a warning box under screen 3**, not a picker — a client that
activates the shield field on a ship with nothing to offer gets a modal it
must answer.

## 11. Open fixes prepared by this reading

- **Open fix 44 — "DSGN"** (`doc/ext_ship_designer_state.patch`): the design
  being edited, the slot and the refit flag, the printed cost and space, the
  values the main page computes at draw time, the weapon rows' damage and
  modification strings. Covers every "no" in the table's in-progress rows,
  the edited slot index and the refit flag, and the printed numbers.
- **Open fix 45 — ids 54 / 55 / 56 and "DSBX"**
  (`doc/ext_ship_designer_boxes.patch`, on top of 44): which sub-dialog is
  open, its list with the numbers it prints per row, its selection, arcs,
  rack, modifications, filters and scroll. Covers the "sub-dialog open /
  which" and "sub-dialog selection state" rows and the available-component
  rows.
- **No engine fix for the texts and pictures**: every name is in the
  player's TECHNAME.LBX (the tree's `techname_extract.py` walks it; the
  computer, drive, fuel and modification names and the weapon plurals are
  one extension of the same walk), the descriptions and weapon notes in
  TECHDESC.LBX, the default names in SHIPNAME.LBX, the ship pictures in
  SHIPS.LBX (already extracted for the Fleets screen), the arc pictures in
  DESIGN.LBX 33-37 — all extractions from the player's own files on the HD
  side (decision 38), none of them wire data.
- **Not covered, on record**: the numbers orion2re's own configuration can
  change (miniaturisation, shield table, Megafluxers, government reduction)
  are applied by the engine in every value the two blocks carry, so the HD
  side never recomputes them — the reason the blocks carry printed values
  rather than tables.
