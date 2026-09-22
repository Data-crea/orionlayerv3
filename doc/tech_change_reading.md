> **Provenance (work order 126 G, 17 September 2026).** A source reading, written in the unattended run by a read-only sub-session and filed unchanged. Spot-checked against the tree by the session that filed it: the commit reads Get_Selected_Entry_ and not the field id (tech.cpp:354-369); Reports_Screen_ sets SCREEN_MAIN before the prompt (mainscr2.cpp:119). Everything else is the reading's own claim with its line reference — verify before building on it (CLAUDE.md, "You own every detail"). Nothing here was driven live.

# The research selection screen in orion2re — a reading

Read 17 September 2026 against orion2re 1.60.0 (src/version.h)
(`ENGINE_VERSION[] = "1.60.0"`, version.h:10). **No code was written and
nothing was driven**; every statement below is *source reading* unless it
cites a document that measured it. Builds on work order 124 G
(`v3_projektstatus.md`, "Galaxy map: the research readout's source"), which
already covers `Player_N_Turns_Until_Research_Complete_`, the chance loop and
`Player_Research_Cost_` — none of that is repeated here.

**`SCREEN_TECH_CHANGE = 36`** (orion2_consts.h:491). HD maps it to the slug
`research` (`core/screen_names.py:53`); no `screens/research/` exists, so the
dispatcher falls back to the framebuffer today.

---

## 1. Ownership, entry, and the builders

**One function, two modes, two entries — and only one of them is screen 36.**
`src/game/tech.cpp` (namespace `TECH`, 1178 lines) owns everything;
`_Tech_Select_(uint8_t changing_tech)` (tech.cpp:111-395) is the whole screen.

| mode | entered by | chain | screen id on the wire |
|---|---|---|---|
| **change** (`changing_tech = 1`) | galaxy map research window | `_research_window_field = Add_Hidden_Field_(545, 344, 613, 415, "", 0x29)` (mainscr.cpp:1405); handler mainscr_main.cpp:697-713 (`_return_screen = SCREEN_MAIN` :709, `_current_screen = SCREEN_TECH_CHANGE` :711) -> `Screen_Control_` case mox2.cpp:177-180 -> `TECH::Tech_Change_` tech.cpp:1157-1168 -> `_Tech_Select_(1)` :1163 | **36** — SWITCHED to |
| **select** (`changing_tech = 0`) | "choose new research" at turn start | `Reports_Screen_` (screen 39) sets `_current_screen = SCREEN_MAIN` first (mainscr2.cpp:119), then `Do_Begin_Of_Turn_` :164 -> `Begin_Of_Turn_` :553 -> `Main_Screen_Report_Handler_` :490 -> `REPORT::Display_Report_` :725 -> `Display_Report_Aux_` report.cpp:309-310 -> `Set_Initial_Tech_` (:467-479, stardate > 35000 and field 0 at status 3) or `Has_Research_Breakthrough_` (:507-519, `research_breakthrough != 0`) -> `TECH::Tech_Select_` tech.cpp:97-109 -> `_Tech_Select_(0)` :106 | **0** — CALLED, never switched |

`grep -rn SCREEN_TECH_CHANGE src` finds exactly four sites: the enum, the one
setter (mainscr_main.cpp:711), the dispatch (mox2.cpp:177-179) and two palette
checks (mainscr_main.cpp:334, mainscr.cpp:133). `Tech_Select_` has exactly two
callers (report.cpp:474, :513); `_Tech_Select_` has exactly two (tech.cpp:106,
:1163). No second copy of the screen exists.

On the galaxy map the research window is the fifth `(545, y)` hidden field,
index **20** in the measured 24-field dump (`doc/ext_api_dokumentation_v3.md`
"Galaxy Map (24 fields)", and `screens/galaxy_map/mapboxes.py` "indices 0-20
identical"). Type 7, no hotkey, and the handler compares the id
(mainscr_main.cpp:697, guarded by `_skip_fields == 0`) — **ACTIVATE_FIELD 20
reaches it.** *Aside:* that dump labels 16-20 "fleet icons 1..5"; the source
says treasury, command points, food, freighters, research (mainscr.cpp:1401-1405).

Mode differences, all set at the top of `_Tech_Select_`:

| | change | select |
|---|---|---|
| panel origin `_g_scrn_x, _g_scrn_y` | 80, 0 (tech.cpp:146-147) | 161, 0 (:170-171) |
| panel art / 8 button images | TECHSEL.LBX 14 / 15-22 (:153-164) | TECHSEL.LBX 0 / 1-8 (:177-188) |
| extra picture | TECHSEL 27 = the exit button art (:166) | TECHSEL 13 = mouse cursor picture (:190, :300) |
| cursor/cycle colour | 0xEF (:151) | 0xFF (:175) |
| research cost offset | `research_accumulated` (:203) | 0 (:212) |
| exit button | yes (:198-200) | none (`accept_btn_id = -1`, :207) |
| behind the panel | galaxy map, drawn by `Draw_Mini_Main_Screen_` before the switch (mainscr_main.cpp:700-703; `Tech_Change_` :1159-1161) | black fill + race science-room animation `SR_R%x_SC.LBX` (:245, :250, :257-273; frame 0x11 for race 7, :261-266) |

**The builders:**

| shown | built by |
|---|---|
| 8 entry positions, one per technology CATEGORY | `Init_Entry_Positions_` tech.cpp:397-428 — `_tech_change_pos` / `_tech_select_pos` (:17-25), HIWORD y / LOWORD x (:412-413); category `id = _entry_to_group[i]` = {4,2,6,8,7,1,3,5} (:42, :401) |
| the field offered per category | `Init_Entry_Data_` tech.cpp:513-614: start at `MOX::_first_field_in_group[id]` (mox.cpp:103 = {0,18,55,57,29,7,22,28,10,74}) and follow `next_field_id` until `tech_fields[f] == 2 && f != current_research_field` (:520-533). In change mode `current_research_field` is zeroed around the call (:201, :204), so the current field IS offered |
| the application choices per field | same, :537-586: for a field < 75, each of `_technology_fields[f].tech[0..3]` whose `tech_applications[app] == 1` (`TECH_RESEARCH_STATUS_AVAILABLE`, orion2_consts.h:1323); none -> billtext.lbx msg 62 as a placeholder with `app_id 0` (:515, :557-569). Field >= 75 (hyper): one choice, `Get_Hyper_Tech_App_ID_` (:996-1017) |
| `tech[4]` itself | NOT a table in the source: filled at init from `_technology_applications[].tech_field_id`, ascending app id, first free slot (techinit.cpp:444-474) |
| cost string per entry | :590-607: `Player_Research_Cost_(plr, f)` (colcalc.cpp:526-539) minus the offset, clamped at 0, `"%i RP"` / `"%i FP"` (language 1) / `"%i PR"` (language 4) |
| field name | `Technology_Fields_Name_` :1019-1026: `_technology_fields[f].name`, or `MOX::_hyper_field_title` = `E_Strings_(0x284)` (estrings.cpp:294) for f >= 75 |
| application name | `Technology_Applications_Name_` :1117-1136: `.name`, and for app >= 204 name + " " + `_roman_literals[hyper+1]` (mox.cpp:426), or `%u` above 20 |
| drawing | `Display_Entry_Text_` :616-671, `Display_Selected_Entry_Text_` :1138-1155, `Draw_Little_Arrow_` :673-716, auto function `Draw_Tech_Select_` :448-466 |
| description popup (right click) | `Draw_Application_Description_` :718-779 -> `TEXTBOX::Text_Box_` |
| category list popup (category button) | `_Tech_List_` :781-963, rows from `Get_Group_List_` :1038-1102 |

**Research points and turns to complete are NOT on this screen.** The only
number is the per-entry cost string (and the full cost in the description).
Turns live in the galaxy sidebar (124 G). `research_accumulated` is never
written in tech.cpp; changing the field only clears `research_breakthrough`
(:1164-1166).

`extra_fields_cnt == 0` (no category has an offerable field) returns at once
with nothing shown (:227-233).

## 2. Field lists, in build order

`Clear_Fields_` (tech.cpp:127) leaves count 1 (fields.cpp:201); field 0 is the
dummy. `x, y` below are the entry origin: change x = 95 / 322, select
x = 176 / 403; y = 30, 31, 135, 135, 240, 240, 347, 347 for entries 0-7 (tech.cpp:17-25).

**Main panel** (`s` = `_g_scrn_x`):

| # | call | line | type | rect | hotkey | driven by |
|---|---|---|---|---|---|---|
| 1 (change only) | `Add_Button_Field_(s+189, 452, …, TECHSEL 27, "\x1B", 40)` | tech.cpp:198-200 | 0 (fields.cpp:368) | **(269, 452)-(360, 470)** — SETTLED 22 September 2026, work order 165 part D: read off the live list with change mode open, 91 x 18 px. It was NOT SETTLED here because the rect comes from the art (fields.cpp:366-367) | ESC | ACTIVATE (compared, :347) or ESC key |
| per entry 0..7, per choice k | `Add_Hidden_Field_(x, y+21+y1[k], x+218, y+21+y2[k], "", 0)`, y1 = {0,34,49,64}, y2 = {33,48,63,78} (:27-29) | :545-552, :560-567, :577-584 | 7 | row 0 is 34 px tall (y+21..y+54), rows 1-3 15 px | — | see below |
| 8 x | `Add_Hidden_Field_(x-2, y+18, x+215, y+99, "", 0)` — entry block, ALL eight entries | :217-223 | 7 | e.g. (93,48)-(310,129) | — | see below |
| per NON-EMPTY entry | `Add_Radio_Button_Field_(s+{21\|248}, {30,31,135,135,240,240,347,347}, …, "", 40)` | :236 -> :430-446, pos :35-40 | **1** (fields.cpp:409) | change (101,30), (328,31), (101,135) … | — | ACTIVATE works (id compared, :377-388) |
| last | `Add_Hidden_Field_(0, 0, 639, 479, "", 0)` | :240 | 7 | whole screen | — | nothing (no branch, :346-391) |

Count: `1 + [1] + A + 8 + R + 1`, A = choices shown, R = non-empty categories.

**Category list popup** (`_Tech_List_`; `FIELDSAV::Save_Field_Stats_` moves the
`_fields` base and clears, fieldsav.cpp:4-21, so the wire shows the popup's
own list — ext_api.cpp:245-259 serializes through the moved pointer):
1 up `Add_Button_Field_(w+247, 77)` :869; 2 down `(w+248, 398)` :870 — both
type 0, no hotkey, and **type becomes -1001 while disabled**
(`Set_List_Up_Down_Field_Drawing_` list.cpp:123-134 -> fields.cpp:1522-1523);
3.. one hidden field per application row (`LIST::Add_Fields_To_List_Page_`
list.cpp:94-121); then `(0,0,639,479)` hotkey ESC (:901) and `(0,0,639,479)`
no hotkey (:902). `w = _list_window_x_offsets[i] + s` = s+205 for the left
column's entries, s+6 for the right (:33, :421, :841).

**Description box**: the modal text-box shape — dummy plus one whole-screen
hidden field, hotkey ESC (textbox.cpp:249); any input closes (:145-149).

### What each input does, and what ignores an injected one

Main loop tech.cpp:311-393:
- `input == accept_btn_id` -> leave, nothing changed (:347-353).
- **any positive `input < first_btn_field`** — every choice row, every entry
  block, (change) never the exit button — **commits**: `_g_selected_entry_p =
  Get_Selected_Entry_(entries)` (:356), then `current_research_field` and
  `current_research_application` (:367-369), leave. **The activated field id
  is never used.** The committed entry is whichever has `current_app_index != 0`,
  and only `Set_Selected_Entry_` sets that — from `Draw_Tech_Select_`, which
  reads `fields::Scan_Input_()`, i.e. the **game pointer** (:449-459;
  fields.cpp:652-663, first match in id order fields.cpp:704-710). Because the
  whole-screen field makes every pointer position a positive id,
  `Set_Selected_Entry_` runs on every idle frame and CLEARS every entry when
  the pointer is not over a row or entry block (:482-484).
- radio `first_btn_field..last_btn_field` -> opens `_Tech_List_` for
  `entries[input - first_btn_field]` (:377-391).
- negative (right click with cancel disabled, :131; fields.cpp:1356-1361,
  :1511-1514) -> negated; outside the radio range `Set_Selected_Entry_(entries,
  id)` BY ID and the description box for that choice (:323-337); inside the
  radio range it falls through as positive and **opens the list** (:324, :377).

Consequences, all *source reading*:
1. **ACTIVATE_FIELD on a choice commits the pointer's hover, not the field.**
   With the pointer off every entry at the last idle frame
   `Get_Selected_Entry_` returns `nullptr` (:499-510) and :367 dereferences it
   — **a null dereference in the game process.** Not tried.
2. **INJECT_CLICK on a choice** works only if the pointer is still the click
   point when `Quick_Call_Auto_Function_` (fields.cpp:1288) runs
   `Draw_Tech_Select_`: the injected event sets it (platform.cpp:1184), and
   `Sync_Mouse_State_From_SDL_` may pull it back to the physical mouse once
   `g_injected_mouse_pending` is cleared (platform.cpp:838-859, :1513) — unless
   the window is unfocused (:826). Decision 39's caveat, here load-bearing.
   **NOT SETTLED live.**
3. **Radio buttons take ACTIVATE_FIELD** despite type 1: the handler compares
   ids and zeroes the variable (:377-388). The table in the ext doc ("type 1
   does not work") is about handlers that read the variable.
4. **Radio index skew.** Radios exist only for non-empty entries (:432), but
   the handler indexes `entries[input - first_btn_field]` (:378-379). With an
   empty category before it, a button opens the WRONG category, and may read
   `button_image` of an entry that never got one (:380, :443). Reachable only
   when a whole category has no offerable field. Consequence NOT SETTLED.
5. **ESC**: change mode — the exit button is the first ESC field
   (`Interpret_Keyboard_Input_` fields.cpp:2608-2613) -> leaves unchanged.
   Select mode — no ESC field, cancel disabled (:131, fields.cpp:983-988):
   **ignored; select mode has no way out but a commit.**
6. `Set_Input_Delay_(5)` (:276) makes the next five `Get_Input_` calls return
   before `ext::Tick` (fields.cpp:161-167): five silent frames after every redraw.

List popup loop :906-961: up/down by id (:913-924, ACTIVATE works); a row
left-click returns its id and **nothing branches on it** (highlight is pointer
hover via `Draw_Tech_List_` :1104-1115); right click on a row -> description of
the POINTER's row (`LIST::Get_Selected_List_Entry_`, :935-944), not the id's;
the first whole-screen field (ESC, ACTIVATE or left click anywhere else) closes
(:949-960); right click outside the help rects and rows only redraws (:926).
The popup is display-only: **nothing in it changes the research.**

## 3. Every displayed value against the wire

Player offsets: ✔ = in `core/structs/player.py` SPEC (verified=True);
"const" = an offset constant in player.py outside the SPEC; "hand" = my count
from orion2.h:1755-1920 between two spec anchors (379 and 591, 591 and 901) —
**not** verification.

| value | source | on the wire? |
|---|---|---|
| category of each entry | `_entry_to_group`, `_first_field_in_group` (tech.cpp:42, mox.cpp:103) | static — not on wire, transcribable |
| field offered | `tech_fields[83]` + `next_field_id` chain | `s_player.tech_fields` @296 (hand; 379 − 83) — **not in spec**; chain static (techdata.cpp:319ff) |
| choices offered | `tech_applications[212] == 1` + `tech[4]` | @379 const (`TECH_APPLICATIONS_OFFSET`, "not decoded yet"); `tech[4]` derivable (techinit.cpp:444-474) |
| field name | TECHNAME string f (1..82) | **not on wire**; not extracted (`techname_extract.py` writes buildings and ship parts only) |
| hyper field name | ESTRINGS 0x284 | not on wire; `estrings_en.json` index 644 present ("Hyper-advanced...") |
| application name | TECHNAME string 83 + app | not on wire; **not extracted** |
| hyper level numeral | `hyper_advanced_tech[f-75]` + `_roman_literals` | @640 (hand) not in spec; numerals static (mox.cpp:426) |
| cost "N RP" | `cost` table − `research_accumulated` (change) | `research_accumulated` @591 ✔; `hyper_advanced_tech` @640 (hand); cost table static, not on wire (124 G) |
| RP/FP/PR unit | `_settings.language` (tech.cpp:598-605) | s_settings on wire; `language` (orion2.h:2486) **not in settings spec** |
| current field highlight | `current_research_field` | @901 ✔ |
| current choice highlight | `current_research_application` + strcasecmp of names (:659-661) | @902 (hand) not in spec |
| all choices highlighted | `traits[TRAIT_CREATIVE=22]` or field ∈ {55,57,29,22,28,23} (:637-648) | traits @2308 const (live-corroborated per player.py); the six ids equal `_starting_tech_field_ids` (techdata.cpp) |
| "no applications" text | billtext.lbx msg 62 | not on wire; **no billtext extractor** |
| selection box, arrow | pointer hover state, `s_list_item_research` in `_screen_seg` | **not on wire, not reconstructible** |
| description title/body | HELP.LBX record `app_id`, ONE record (:732-733) | not on wire; `help_en.json` holds records 1, 83, 211 as tech titles — but the extractor joins CHAINS (help_extract.py), this reads one; whether any tech record chains is **NOT SETTLED** |
| description cost | billtext 61 + FULL `Player_Research_Cost_` (:735, :1028-1036) — not the remaining cost the entry shows | as cost above |
| list popup title | billtext 64+group + msg 63 (:802-816, :885-889) | not on wire, not extracted |
| list popup rows, colours 1/2/4 | `Get_Group_List_` :1038-1102 (status 3 and hyper > 20 skipped) | same inputs as above; page not on wire |
| category labels on the panel, exit-button label | none printed by tech.cpp — presumably baked into TECHSEL art | **NOT SETTLED** |
| science-room animation (select) | `SR_R%x_SC.LBX`, race | race @37 ✔ |

Strings a build needs from TECHNAME.LBX: 1..82 (fields) and 83..294
(applications) — the same block and walk `buildnames` already uses
(techinit.cpp:43-66). Plus billtext.lbx 61, 62, 63, 64-73, ESTRINGS 0x284, HELP.LBX 0..211.

## 4. The screen id while the screen is up

- Change mode: `Screen_Control_` ticks 36 (mox2.cpp:41) then CALLS
  `Tech_Change_`; every `Get_Input_` ticks `MOX::_current_screen`
  (fields.cpp:167), still 36 — main panel, list popup and description box
  alike. Leaves with `_current_screen = _return_screen` (tech.cpp:1167) = 0.
  The first snapshot at 36 carries the 1-field list left by
  `Clear_Fields_` (mainscr_main.cpp:699).
- Select mode: **the wire says 0 throughout** (mainscr2.cpp:119), with a
  foreign field list. `SCREEN_REPORTS` 39 is seen at most for the one
  `Screen_Control_` tick. Even the description box position depends on it:
  `Box_Centered_On_XY_` puts x = 84 when screen is 0, 130 otherwise
  (textbox.cpp:44-53).

**Hazard (decision 59's rule, second instance, source reading):**
`GalaxyMapScreen` parks with `ACTIVATE_FIELD 9` whenever the state reports
screen 0 and `map_scale < fit` (`screens/galaxy_map/screen.py:265-273`,
`viewctl.py:209-219`). In the select list field 9 is a choice row or entry
block — the commit branch: the hovered choice is committed, or the game
dereferences null. Not observed; normally the map is already parked at turn start.

## 5. What a patch would carry — described only

**Decision 25 first: the offered list is reconstructible.** It is a pure
function of `tech_fields`, `tech_applications`, `hyper_advanced_tech`,
`current_research_field` (the snapshot carries all four inside `s_player`,
ext_api.cpp:120-122) and static tables (`_first_field_in_group`,
`next_field_id`, `cost`, `_technology_applications[].tech_field_id`, the
hyper mapping). What is missing is not a patch but: spec entries for
@296, @640, @902 (and `language` in s_settings) with decision 23's two
sources, and transcribed tables with a checker against techdata.cpp /
mox.cpp (the `monster_hull_check.py` pattern 124 G names). **The data
carries its own validation:** the FIELD_LIST has one hidden row per offered
choice at `y+21+y1[k]` under each entry's x, and one radio per non-empty
category — counts and row y must match the reconstruction per entry.

**What no existing path reaches:**
1. **A commit by id.** Section 2: activation commits the pointer's hover or
   crashes; a click depends on pointer survival. Options, for Data: (a) a
   command in `ext_api.cpp` `ProcessInput` like `MSG_SET_JOBS`, writing
   `current_research_field/application` with the checks tech.cpp:520-586
   make — but the loop would still be open and select mode has no exit but
   a commit; (b) in the early exit (fields.cpp:168-178) also placing the
   game pointer at the activated field's centre, which fixes every
   pointer-reading handler at once and changes behaviour for every screen;
   (c) an `ORION2RE_EXT` insertion in tech.cpp:354-356 calling
   `Set_Selected_Entry_(entries, input_val)` before `Get_Selected_Entry_`.
   Files: `src/ext/ext_api.cpp`, `src/game/fields.cpp` or `src/game/tech.cpp`.
2. **Mode identity in select mode.** Screen 0 plus a list shape; the
   precedent is the synthetic id 50 in `racesel.cpp` (`core/screen_names.py:54-57`).
3. Nothing else: hover and list page are UI state HD would own itself.

## 6. Right-click help

`_help_list_active` is re-installed every redraw (tech.cpp:278-283) through
`BILLHELP::My_Set_Help_List_` (billhelp.cpp:89-92); `s_help_box` is
{id, x1, y1, x2, y2} (orion2.h:993-999).

| where | table | entries | installed |
|---|---|---|---|
| change panel | `_technology_change_help_list` billhelp.cpp:48-52 | 255 (0,0,80,479), (557,0,639,479), (80,0,557,25) | `Technology_Change_Help_` :122 |
| select panel | `_technology_select_help_list` :42-46 | 254 (0,0,163,479), (163,0,639,25), (163,449,639,479) | `Technology_Select_Help_` :126 |
| list popup, change, right column (`w − s > 6`) | list3 :64-67 | 256 (0,0,285,479), (553,0,639,479) | `Tech_Change_List_Right_Help_` :149, from tech.cpp:858-859 |
| list popup, change, left | list4 :69-72 | 256 (0,0,86,479), (354,0,639,479) | :157, tech.cpp:850-851 |
| list popup, select, right / left | list1 :54-57 / list2 :59-62 | 256 (0,0,366,479)+(634,…) / (0,0,167,479)+(435,…) | :153 / :161 |
| description box | none — `Text_Box_Startup_` sets `_help_list_active = 0` (textbox.cpp:91-95) | | |

Every help rectangle lies OUTSIDE the panel or popup window. Inside, a right
click is not help and not Cancel: it is the description (choices) or the list
(category buttons), section 2. Ids 254, 255, 256 are present in
`assets/shared/help/help_en.json` ("Select New Research", "Change Current
Research", "Technology List"); the galaxy map's 292 "Research Window" is
already in `screens/galaxy_map/help.json:20`.

## 7. Layout under one provisional content box

**Change mode fits, and the source already works that way.** Every panel
position is `_g_scrn_x/_g_scrn_y + constant`: the art at (s, 0) (:291), the
black fill (s+4, 4)-(s+471, 472) (:290), the exit button (s+189, 452)
(:198), radios `_tech_button_pos + s` (:435-436), popup windows
`_list_window_x_offsets + s` (:421). The entry table is absolute, but it is
s + 15 / s + 242 in both tables (95 = 80+15, 176 = 161+15; 322 = 80+242,
403 = 161+242). So for change mode ONE box is (84,4)-(551,472), or the
art's rect from (80,0) — the help rects put its edge at x 81..556, y 26..479.
All children lie inside it: entries x 93..540, y 48..446; list windows
(86 or 285) to +267, y 31..449 (:882); description box x 130..510
(textbox.cpp:51, :80). The galaxy map outside is the HD galaxy map, not this
screen's content.

**Select mode needs a second region, and has two absolute rectangles.** The
panel box is the same box at s = 161 ((165,4)-(632,472)), but (a) the
science-room animation fills x 0..160, outside it (:257-273; help 254 covers
0..163), and (b) the description box is at x = 84 because the wire says screen
0 (textbox.cpp:45) — 84..464, crossing the panel's left edge. Also absolute and
not following s: the list popup's background capture (84,40)-(519,439)
(:847, :880-881), which does not cover a right-column window at 366..633 in
select mode — a restore quirk to transcribe or not, not a layout input. The
popup's y (31, 47, 77, 398) are absolute but `_g_scrn_y` is 0 in both modes.

Verdict: **one content box per mode, same inner layout shifted by 81 px**;
select mode adds the animation area and a description box anchored to the map
viewport. The native size of the panel art (TECHSEL 0 and 14) is NOT SETTLED
from the source; the fill rect is the best source-side bound.

## 8. Questions for Data before a build can start

1. Build change mode only (screen 36) first, leaving select mode (screen 0) on the framebuffer?
2. Commit path: patch (5.1 a, b or c) or INJECT_CLICK with the focus caveat?
3. Until then, may HD refuse to send ANY field id into this list (decision 33), given the null dereference in 2.1?
4. Guard the galaxy map's parking against a non-map list at screen 0 (section 4) now, as its own fix?
5. Add @296, @640, @902 and `s_settings.language` to the specs by header compile plus a live read?
6. Transcribe `cost`, `next_field_id`, `tech_field_id` and `_first_field_in_group` with a checker, or ask for them on the wire?
7. Extend `techname_extract.py` to fields and applications (strings 1-294) — same file, second output?
8. A billtext.lbx extractor for msgs 61-73, following the hestrings pattern?
9. Tech descriptions from `help_en.json` (chained) or a single-record extraction, matching tech.cpp:733?
10. Is the category list popup (display-only) in scope for the first build?
11. Transcribe the radio index skew (2.4) and the full-vs-remaining cost difference (3), or mark them?
12. Who takes the live measurements still NOT SETTLED: art rects, the exit button's label, pointer survival after INJECT_CLICK?
