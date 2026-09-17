> **Provenance (work order 126 G, 17 September 2026).** A source reading, written in the unattended run by a read-only sub-session and filed unchanged. Spot-checked against the tree by the session that filed it: SCREEN_RACE runs RACESCRN::Race_Screen_ (mox2.cpp:61-63), the galaxy map's RACES button sets it (mainscr_main.cpp:666), and screens/select_race claims GAME_SCREEN_ID 6 (screen.py:30). Everything else is the reading's own claim with its line reference — verify before building on it (CLAUDE.md, "You own every detail"). Nothing here was driven live.

# Read 17 September 2026 against orion2re 1.60.0 (src/version.h)

The Races screen (`RACESCRN::Race_Screen_`) and the diplomacy dialogs it opens: a source reading.
Version checked at `src/version.h:10` (`ENGINE_VERSION[] = "1.60.0"`).
Tree HEAD when read: `7067c366`. **No code was written, and nothing was run or driven live.** Every
claim here comes from reading the source. Nothing is *measured*, and every shape marked "derived"
still has to be checked against a live FIELD_LIST before anyone builds on it.

---

## 0. Verdict on the claim

> "chat found no assignment of a screen ID of its own in racescrn.cpp, which would make it the
> same problem ext_screen_id.patch solved for Select Race and Custom Race."

**The observation is true, but the conclusion is false. The real problem runs the other way.**

- True: `racescrn.cpp` never writes `SCREEN_RACE`. Its only write to `_current_screen` is on the
  way out, `= SCREEN_MAIN` (racescrn.cpp:873).
- False: the Races screen does not need to write it. It is a **dispatched** screen, not a called
  one. `SCREEN_RACE=6` (orion2_consts.h:466). `case SCREEN_RACE: RACESCRN::Race_Screen_();`
  (mox2.cpp:61-63). The galaxy map sets the value before it leaves (mainscr_main.cpp:665-669). So
  the game reports 6 for the whole time the Races screen is up. Select Race and Custom Race were
  **called** screens with no case in that switch (ext_screen_id.patch "WHY"). This is not the same
  problem.
- The actual problem: **our own patch reused the Races screen's id.** Hunk 1 sets
  `_current_screen = SCREEN_RACE` on entry to `Race_Selection_Screen_` (racesel.cpp:212-223). So
  6 now means two unrelated screens. OrionLayer maps 6 to `select_race`
  (screens/select_race/screen.py:30). So the HD client would draw Select Race over the Races
  screen. §4 has the details.

---

## 1. Files, entry, builders

| file | owns |
|---|---|
| `src/game/racescrn.cpp` (1093 lines) | Races screen: `Race_Screen_` :677-1093, drawing, fields, spy drag |
| `src/game/racerprt.cpp` (156) | Race report: `RACERPRT::Race_Report_Screen_` :9-155 |
| `src/game/dip_scrn_main.cpp` (2327) | `DIP_SCRN::Diplomacy_Screen_` :1257-1349, main choices :1156-1255, propose/break/offer/generic lists, `Npc_Diplomacy_Screen_` :1351 |
| `src/game/dip_scrn.cpp` (2571) | demand :1349, exchange tech :1013, declare war :234, surrender :277, system map :707-812, system list :2300-2362, net diplomacy |
| `src/game/billhelp.cpp` | help lists `_races_help_list` :74-83, `_report_help_list` :85-87 |
| `src/game/diplomac.cpp`, `npcdiplo.cpp`, `diplodef.cpp` | rules and AI (`Valid_Treaty_Proposal_` diplomac.cpp:2175). They build no UI. |

**How each one is entered**
- **Races.** Galaxy map field `_races_button` = `Add_Irregular_Button_Field_(386,435,453,471,…,"R")`
  (mainscr.cpp:1398). Its handler sets `_current_screen = SCREEN_RACE`, `exit_flag`, and
  `_return_screen = SCREEN_MAIN` (mainscr_main.cpp:665-669). Dispatch is at mox2.cpp:61.
  - **Leaving:** the EXIT button sets `SCREEN_MAIN` and returns (racescrn.cpp:857-874).
- **Race report.** Pick REPORT, then a race. `RACERPRT::Race_Report_Screen_(target)` is CALLED from
  racescrn.cpp:894.
- **Diplomacy (audience).** Pick AUDIENCE, then a race. `DIP_SCRN::Diplomacy_Screen_(target)` is
  CALLED from racescrn.cpp:913 (single player) and :948/:1005 (network).
  - Other callers are network only: netmox.cpp:540.
  - AI-initiated diplomacy is a different function, `Npc_Diplomacy_Screen_`. It is called from
    report.cpp:648/:653 (`Display_Report_Aux_`) and dip_scrn_main.cpp:1074 (sneak attack). The
    Races screen does not reach it.
- **Declare war.** Pick DECLARE WAR, then a race. `GENDRAW::Do_Confirmation_Box_`
  (racescrn.cpp:904 → gendraw.cpp:220 → :153).
  - YES writes only `delayed_diplomacy_orders[target] = 0` (racescrn.cpp:905).
  - Nothing happens when `treaty[target] >= 4` (:899-901).
- **Ignore.** Pick IGNORE, then a race. This XORs a bit in `_cur_plyr_ptr->ignoring` (:888). There
  is no dialog.
- **Every action ends in `break`.** That leaves the inner loop, and the outer `while(true)` reloads
  and redraws the whole screen (racescrn.cpp:716-825).

**Builders**

| thing shown | built by |
|---|---|
| background | `races.lbx` 0 at (0,0) (racescrn.cpp:742, :776) |
| per-race data | `Init_Race_Display_Data_` :283-336 |
| portraits, eliminated overlay, banner frame | `Draw_Race_Photos_` :258-281. Portrait `races.lbx race+32` (:328); overlay `races.lbx 0x1F` (:288); two `Box_` in `_banner_color_high/low[color]`, corner dots `_banner_color_edge` (:272-279) |
| name, treaties, "no contact", spy/agent bonus | `Draw_Race_Text_` :111-230 |
| relation bars and sliders | `Draw_Relations_Sliders_` :232-256 (`races.lbx` 3 = bar, 2 = slider) |
| relation word (only while the pointer is over a bar) | `Draw_Race_Screen_` :563-566 |
| spy icons per race, agent pool, dragged group | `Draw_Icon_Group_` :659-675, `Draw_Icon_Group_Cursor_` :623-657, via auto function `Draw_Race_Screen_` :532-606 |
| "Ignoring" tag | `Draw_Race_Screen_` :569-572 |
| network wait box (`races.lbx` 59) | `Draw_Race_Screen_` :593-605. Only when `_net_state` is 1 or 2 |
| report | `Race_Report_Screen_` :91-154. Tech panel is `INFO::_Tech_Review_Subscreen_` (info.cpp:779) |
| diplomacy backdrop | `Setup_Back_Page_` dip_scrn_main.cpp:1645 (`DIPLOMAT.LBX race*2+13`); ambassador `Setup_Ambassador_Pic_` :1665 (`race*2+14`) |
| ambassador statement and header | `Draw_Diplomacy_Synch_Mode_` :1554-1643 |
| option lists | `fields::Get_List_Field_` fields.cpp:1555-1682, one widget for every list |
| system picker map | `Draw_Diplomacy_System_Display_` dip_scrn.cpp:841, galaxy box (10,171) 180×110 (:742, :838) |

**The active race set.** Built at racescrn.cpp:766 by `BILL::Get_Players_Dead_Or_Alive_Or_Omniscient_`
(bill.cpp:312-338). That is: contacted living races, then eliminated races and, if you are
omniscient, every other race.

**It is then cut down again at racescrn.cpp:792**, by `BILL::Get_Active_Players_(0,0)`
(bill.cpp:565-593). That resets `_active_count` to contacted living races only. This happens
*after* portraits and text were drawn (:786, :789) but *before* the sliders (:793) and the fields
(:810-815).
- **Result:** an eliminated race, or an uncontacted race shown through omniscience, gets a portrait
  and a name but no bar, no fields and no spy icons.
- The pre-cut list is ordered: contacted living first, then the extras, each in ascending player
  index. So slots 0..n-1 are the same in both lists.

## 2. Field lists (build order)

Field 0 is the dummy (`Clear_Fields_` sets `_fields_count = 1`, fields.cpp:201). Add-function types:
- `Add_Button_Field_`: type 0 (fields.cpp:368)
- `Add_Radio_Button_Field_`: type 1 (:409)
- `Add_Multi_Button_Field_`: type 3 (:341)
- `Add_Hidden_Field_`: type 7 (:308)
- `Add_String_List_Field_`: type 10 (:788)

Sprite-sized rectangles (types 0, 1, 3) take their width and height from LBX art. The source does
not state them, so they are **NOT SETTLED** until a live list is read. Hotkey `""` is 0.

### 2a. Races, main mode (`Setup_Main_Fields_` :338-373, `Setup_Race_Display_Fields_` :426-457, :815)

The parameter names of `Setup_Main_Fields_` (agriculture/research/industry/diplomacy) are
**wrong**. The caller's names (:810), the help ids (billhelp.cpp:76-79) and the help titles all
agree on this mapping:

| id | call | type | at | hotkey | meaning | input |
|---|---|---|---|---|---|---|
| 1 | `Add_Button_Field_(535,433, races.lbx 9)` :346 | 0 | (535,433) | ESC (0x1B) | EXIT → galaxy map | ACTIVATE (id compared :857) or ESC |
| 2 | `Add_Radio_Button_Field_(429,444, lbx 6)` :360 | 1 | (429,444) | I | IGNORE | see below |
| 3 | `…(429,423, lbx 7)` :363 | 1 | (429,423) | R | REPORT | see below |
| 4 | `…(334,423, lbx 8)` :366 | 1 | (334,423) | A | AUDIENCE | see below |
| 5 | `…(334,444, lbx 60)` :369 | 1 | (334,444) | D | DECLARE WAR | see below |
| 6 | `Add_Hidden_Field_(328,386,613,415)` :433 | 7 | agent pool | 0 | pick up / drop agents | pointer (below) |
| 7+5i | `Add_Multi_Button_Field_(sbx,sby, lbx 10+i, &mission, 1)` :441 | 3 | `_race_spy_btns[i]` | 0 | mission Spy | INJECT_CLICK only |
| 8+5i | `…(sbx+76, …, lbx 17+i, 2)` :442 | 3 | | 0 | Sabotage | INJECT_CLICK only |
| 9+5i | `…(sbx+149, …, lbx 24+i, 3)` :443 | 3 | | 0 | Assassinate (label from art order, **NOT SETTLED**) | INJECT_CLICK only |
| 10+5i | `Add_Hidden_Field_(sx, sy-6, sx+187, sy+25)` :448 | 7 | spy strip | 0 | pick up / drop spies | pointer (below) |
| 11+5i | `Add_Hidden_Field_(bx-6, by-6, bx+8, by+88)` :453 | 7 | bar | 0 | hover only; activating does nothing | — |
| 7+5n | `Add_Hidden_Field_(0,0,639,479)` :815 | 7 | whole screen | 0 | no-op in main mode | — |

`display_base` = 5 when n ≥ 1 (:372). **Count = 8 + 5n**, where n is the reduced `_active_count`
(n in 1..7, so 13..43). When n = 0 the four radios are skipped and every `btn_*` is 0 (:353-357):
**count = 3**.

Per-slot anchors, all from tables (racescrn.cpp:41-47):

| i | spy strip (field) | bar field | spy buttons y | portrait | text |
|---|---|---|---|---|---|
| 0 | (121,92)-(308,123) | (99,43)-(113,137) | 126 at x 120/196/269 | (21,49) | (125,50) |
| 1 | (121,199)-(308,230) | (99,149)-(113,243) | 233 | (21,156) | (125,157) |
| 2 | (121,305)-(308,336) | (99,256)-(113,350) | 338 | (21,262) | (125,262) |
| 3 | (121,411)-(308,442) | (99,364)-(113,458) | 445 | (21,369) | (125,366) |
| 4 | (333,92)-(520,123) | (522,43)-(536,137) | 126 at x 332/408/481 | (544,50) | (333,50) |
| 5 | (333,200)-(520,231) | (522,150)-(536,244) | 233 | (544,157) | (333,157) |
| 6 | (333,305)-(520,336) | (522,255)-(536,349) | 338 | (544,262) | (333,262) |

**How the inputs behave**
- **The four radios.** The handler compares the returned **id**: `active_action_field = input`
  (:1068-1078). It never reads `state_*`. So `ACTIVATE_FIELD` should reach the branch, **unlike the
  general type-1 rule** (ext doc "Field types"). The radio's own toggle (fields.cpp:1292-1297) is
  skipped, so the button would be drawn unpressed. The hotkeys A/R/I/D work through the keyboard
  path (fields.cpp:1010-1024). **NOT SETTLED live.**
- **Mission multi-buttons.** The value is written only inside `Draw_Field_(i, action≠0)`
  (fields.cpp:2793-2799). That happens when `_down_mouse_button == i` during `Draw_Visible_Fields_`
  (fields.cpp:2191, :2202-2204), which `Draw_Race_Screen_` runs with drawing enabled
  (racescrn.cpp:545-547). The early exit sets no down button, and no code compares these ids. So an
  activation does nothing, and only `INJECT_CLICK` can set a mission. `Adjust_Spy_Mission_Data_`
  turns 0 into 3 (:416-424).
- **Picking up spies depends on the pointer.** The id is compared (`Get_Spy_Group_For_Field_`
  :497-516), but the number of icons moved is `_g_spy_xfer_count`. That value is computed from
  `mouse_x` by `Draw_Icon_Group_Cursor_` (:561, :580), and only while `Scan_Input_` hovers that
  strip. An activation moves whatever the last hover computed. Use `INJECT_CLICK` at a computed x,
  with decision 39's pointer caveat.
- **Dropping is id-only.** `Move_Spy_Group_From_Mouse_` moves the whole dragged group, capped at 63
  (:391-409). Clicking any non-strip field while dragging drops the group back onto its source
  (:1025-1030, :1048-1056).

### 2b. Races, "who" mode

Entered by any radio (:1085-1088). `Setup_Race_Who_Fields_` :459-488 clears everything above
`display_base`:

| id | call | rect | input |
|---|---|---|---|
| 1-5 | unchanged from 2a | | a radio click here leaves who mode and rebuilds 2a (:1058-1066) |
| 6+i | `Add_Hidden_Field_(xo, py, xo+319, py+88)` :476 | xo = 0 for i<4, 320 for i≥4; py = `_race_picture[i].y` | ACTIVATE. Race index = `input - display_base - 1` (:883) |
| 7+n | whole-screen hidden (:1086) | | ACTIVATE → `break`, full rebuild (:879-881) |

**Count = 7 + n** (8..14). This never equals 8+5n, so every main↔who switch changes the count and
resends FIELD_LIST (ext_api.cpp:670-677).

**ESC in who mode hits field 1**, the first ESC hotkey (per game_menu_reading §5). That leaves the
Races screen entirely; it does not just cancel the pick. *Source reading.*

### 2c. Race report (racerprt.cpp)
- Field 1: `Add_Button_Field_(0x216,0x1B1 = 534,433, racerprt.lbx 1, ESC)` :87. The handler
  compares the id (:149), so ACTIVATE works.
- Then `_Tech_Review_Subscreen_`:
  - four type-3 tabs at `_tech_rev_field` (info.cpp:810-821)
  - up `(410,65)` and down `(410,395)` buttons, both hotkey ESC (info.cpp:824-825), which is
    shadowed by field 1
  - list page fields (info.cpp:851). Count **NOT SETTLED**.

### 2d. Declare-war confirmation
`Confirmation_Box_` (gendraw.cpp:153): 3 fields. YES `(235,302)-(286,323)` hotkey Y, NO
`(345,302)-(396,323)` hotkey N. Help is off, and ESC is ignored. That was measured for the GAME
popup (game_menu_reading §4-5); here it is the same builder.

### 2e. Diplomacy (all under the caller's id; see §4)
- **Fade-in** (only if animations are on): up to 38 frames of `Clear_Fields_` plus
  `Add_Hidden_Field_(0,0,639,479)`. Count 2. ACTIVATE field 1 or any key skips it
  (dip_scrn_main.cpp:1997-2011).
- **Response box** `Diplomacy_Display_Response_`: count 2, the same whole-screen type-7 field.
  ACTIVATE 1 closes it (:1085-1093). It is the only dialog when `Find_Worst_Modifier_ <= -100` or
  the Council is in session (:1283-1289, :1335-1337).
- **Main options.** `Get_List_Field_(10, 0x76, 0xF5, title, list, 50, …, main_options, 0x11)`
  (:1203-1209).
  - Items 1..8 are type 10 at x 10..255, y = 118 + k·(font height + spacing), height = font + 1
    (fields.cpp:1576-1597, :763-800).
  - After them comes one type-10 title field at (10,118) (fields.cpp:1618-1620).
  - **Count 10.** Item strings are jimtext 0x1F..0x26, and item 8 is empty (dip_scrn.cpp:862-877).
  - Returned index: 0 Propose, 1 Break, 2 Demand, 3 Offer Gift, 4 Exchange Tech, 5 Declare War,
    6 Surrender, 7 Goodbye; −1 exits (:1211-1249).
  - **Disabled items** (flag 0 from `Diplomacy_Set_Main_Options_` :1680-1727) **ignore
    activation** (fields.cpp:1641-1643). The title field ignores it too (:1644-1646).
  - ACTIVATE works on enabled items; the list returns `input-1` (:1681).
  - Font-4 height is not in the source, so item y is **NOT SETTLED**.
- **Sub-lists.** Every other list uses the same widget at (10,118) width 245, with count =
  items + 2:
  - propose dip_scrn_main.cpp:2069
  - break :128
  - generic yes/no (declare war and surrender confirmations use `Diplomacy_Generic_List_` :261,
    called from dip_scrn.cpp:244/:287)
  - offer :372
  - money :970
  - need-better-offer :810
  - exchange tech :1809
  - demand dip_scrn.cpp:1429
  - repulsive main :2213
- **System picker** `Diplomacy_System_Display_` (dip_scrn.cpp:707-812):
  - fields: one 6×6 hidden field per star from `Get_Galaxy_Map_Star_XY_(i,10,0xAB,0xB4,0x6E,0,0,1)`
    (:741-745), then CANCEL `(15,139)-(157,162)` (:747)
  - count = NUM_STARS + 2
  - ACTIVATE on a star is filtered by owner, `May_Surrender_Star_` and not-homeworld (:786-793)
- **System confirm** `Diplomacy_Generic_System_List_`: list at (10,102) width 245 (:2352).

## 3. Displayed values and the wire

The STATE snapshot carries `MOX::_player[8]` whole (ext_api.cpp:119-121). Spec status is from
`core/structs/player.py` (decision 23):
- "header" = member line in `orion2.h`. No offset was computed in this reading, since a compile was
  not allowed.
- `unverified.py` has none of these fields.

| value | source line | wire / spec |
|---|---|---|
| race (portrait, spy icon) | `s_player.race` racescrn.cpp:311, :286 | @37 **VERIFIED** |
| eliminated (overlay) | :315, :266 | @36 **VERIFIED** (header plus assert) |
| banner colour | `color` :270 | @38 **VERIFIED** (header plus assert) |
| player name | `name` :310, :144 | @1 **VERIFIED** (header plus assert) |
| contact (active set, "No Contact") | `contact[]` bill.cpp:572, racescrn.cpp:122 | `CONTACT_OFFSET` 1512, a constant rather than a spec field; header-derived, NOT VERIFIED |
| omniscience | `HAROLD::Player_Is_Omniscient_` harold.cpp:765-775: leader lore OR `traits[27]` | traits @2308 constant; leaders not verified; partial |
| relations (slider y, relation word) | `relations[]` sbyte, orion2.h:1834; racescrn.cpp:296 | on wire, **not in spec** |
| treaty (label, war gate) | `treaty[]` orion2.h:1836; :151, :899 | on wire, not in spec |
| research treaty and level | orion2.h:1838, :1824; :160-187 | on wire, not in spec |
| trade treaty and level | orion2.h:1837, :1821; :190-195 | on wire, not in spec |
| tribute giving / receiving | `tribute_treaty[]` int16 orion2.h:1839, both directions; :197-209 | on wire, not in spec |
| spy counts, missions, agent pool | `spies[]` orion2.h:1903: low 6 bits count, high 2 bits mission, `spies[self]` = agents (bill.cpp:57-59, :340-352) | on wire, not in spec. **Stale during a drag**: the drag edits local `race_display_data`; `s_player` is written only by `Update_Spy_Stuff_` (:518-530) at :841/:864/:893/:898/:909 |
| ignoring bitmask | `ignoring` orion2.h:1905; :569, :888 | on wire, not in spec |
| objectives (report) | orion2.h:1763; racerprt.cpp:22 | on wire, not in spec |
| personality (report) | @39 | **VERIFIED** (header plus assert) |
| spy/agent bonus % | `spy::Compute_Spy_Bonuses_` spy.cpp:34ff: traits, `Tech_Spy_Bonus_`, leader skills | derived; leaders and tech table not verified; **not reproducible today** |
| `_active_count`, `_active_player[]` | mox.cpp:309-310 | **not serialized**; derivable from contact, eliminated and omniscience (bill.cpp:312, :565) |
| who mode, spy mode, dragged count, `_net_state` | racescrn.cpp:10-18 globals | **not on wire**; only the field-list shape shows who mode |
| relation words (17), "Ignoring", "No Contact", bonus prefixes, treaty prefixes | billtext.lbx 0x21-0x31, 0x32-0x35, 0x39-0x3C (:687-705) | text, not state |
| treaty labels | `E_Strings_(0x275..0x27B)` estrings.cpp:91-97 | text |
| research/trade unit suffix per language | literals racescrn.cpp:164-192 | text |
| ambassador statement | `_response_message` → `Get_Diplomacy_Statement_` dip_scrn_main.cpp:568 | **not on wire** |
| which diplomacy option is enabled | `Diplomacy_Set_Main_Options_` :1680-1727 (treaty, trade, research, tribute, `Valid_Treaty_Proposal_`, `May_Surrender_Empire_`, tech lists) | disabled flags **not on wire**; the list field is present either way |
| report alliances and wars | `treaty[]` of the target, ==2 or >=4 (racerprt.cpp:54-68) | on wire, not in spec |
| report "their spies on me" | `spies[target][me]` (racerprt.cpp:46) | on wire, not in spec |

## 4. The screen id question, settled

1. `SCREEN_RACE=6` (orion2_consts.h:466). There is no synthetic id range in the enum; its highest
   value is 43 (:496).
2. The dispatcher runs it: `case SCREEN_RACE: RACESCRN::Race_Screen_(); MOX::_previous_screen =
   SCREEN_RACE;` (mox2.cpp:61-63). `ext::Tick(current_screen)` is also called there (mox2.cpp:40-42)
   and in every `Get_Input_` (fields.cpp:168).
3. **Every site that writes 6** (grep of `SCREEN_RACE` and literal `= 6`, the whole of `src/`):
   - mainscr_main.cpp:666. The galaxy map RACES button. The original's own line.
   - racesel.cpp:222. **Our hunk 1** (`#ifdef ORION2RE_EXT`, :212-223), in `Race_Selection_Screen_`.
   - dip_scrn.cpp:717, in `Diplomacy_System_Display_`. The original's line, never restored.
   - dip_scrn.cpp:2311, in `Diplomacy_Generic_System_List_`. Same.
   - Readers of the value: movebox.cpp:37, where `Draw_Galaxy_Map_Box_` skips its fill when
     id == 6. That is probably why the two diplomacy functions set it (**inference**).
   - Callers of those two are all inside player-initiated diplomacy: dip_scrn.cpp:1207 (via
     :1151 ← `Diplomacy_Determine_Treaty_Proposal_` ← propose/repulsive), :1572 (demand), :1837
     and :2281 (network demand), and dip_scrn_main.cpp:433 (offer). In single player they run only
     under `Race_Screen_`, where the id already is 6. Through netmox.cpp:540 (network) they could
     leave a stale 6 under another screen: **NOT SETTLED**, multiplayer only.
4. `racescrn.cpp` writes `_current_screen` once, `SCREEN_MAIN` on exit (:873).
5. **The dialogs are CALLED functions and report the caller's id, 6:**
   - `Race_Report_Screen_` (racerprt.cpp: no write)
   - `Diplomacy_Screen_` (dip_scrn_main.cpp:1257-1349: no write)
   - the confirmation box
   - every `Get_List_Field_`
   - the system picker, which writes 6 again

   None has its own id. `Npc_Diplomacy_Screen_` (AI-initiated) reports whatever called it
   (report.cpp:648). That is outside this screen.
6. **The collision.** `Race_Selection_Screen_` reports 6 from racesel.cpp:222 until either:
   - cancel restores the caller's id (racesel.cpp:351-353), or
   - it is overwritten by `Racial_Option_Screen_` (50 at :471, then `_return_screen` at :704 on
     Custom accept).

   OrionLayer registers one screen per id: `screen_map[game_id] = name` (core/dispatcher.py:47),
   and `update_from_game` switches by that map alone (:195). main.py:246-247 calls it with no
   other gate.

   `select_race` declares `GAME_SCREEN_ID = 6` (screens/select_race/screen.py:30), and
   core/screen_names.py:39 labels 6 as `select_race`. No other screen claims 6.
7. **What this means for routing.** The HD galaxy map's RACES action is field 14
   (screens/galaxy_map/layout.json:46-50, sent as ACTIVATE_FIELD at screen.py:688-691). When the
   game enters `Race_Screen_`, the next snapshot reports 6, and the dispatcher switches to HD
   **Select Race** on top of the Races screen. *Source reading. Not observed live.* Its inputs then
   go to the wrong screen:
   - A portrait click sends `INJECT_CLICK` at (412 or 538, 114+48·row) (select_race/screen.py:282-291).
     For example, (412,114) lands in slot 4's spy strip (333,92)-(520,123), and (412,210) in slot
     5's. The same call then switches to `empire_identity` with `lock_ids=(6,)` (:280), whose chain
     types a ruler name into the Races screen.
   - HD ESC clicks (162,445) (:306). With n ≥ 4 that is slot 3's Spy mission button at (120,445)
     if the art is at least 43 px wide (**NOT SETTLED**). Otherwise it lands on the whole-screen
     no-op.
8. **Can the two be told apart on the wire?** Yes, without a patch, by two independent signals:
   - **`previous_screen`**, STATE byte 2 (ext_api.cpp:99, read at core/game_state.py:150).
     - Under `Race_Screen_` it is always 0: the only single-player entry is mainscr_main.cpp:666,
       and mox2.cpp:47 sets 0 when `Main_Screen_` returns.
     - Under race selection it is the New Game caller's predecessor: 10 (mox2.cpp:77 or
       mainmenu.cpp:227), 8 (game popup NEW GAME, loadsave.cpp:1246 → mox2.cpp:69), or 15
       (multiplayer, mox2.cpp:110). Hotseat and network are also 15, by the same line
       (**inference**; not traced end to end).
   - **Field shape.** Select Race single player has 16 fields (ext doc, *measured*): field 1 is
     type 7 at (5000,5000) with hotkey ESC (`Add_Hot_Key_`, racesel.cpp:196; fields.cpp:234-246),
     and fields 2-15 are type 1 at x 351/477 (racesel.cpp:202-206). Races has field 1 as type 0
     at (535,433) with hotkey ESC, fields 2-5 as type 1 at x 334/429, and counts 3, 13..43 or
     8..14. The diplomacy dialogs have type-10 lists at x 10, or one whole-screen type-7 field with
     no hotkey.
   - **Count alone is not enough.** A 14-item diplomacy list would also have 16 fields
     (`_diplomacy_list_choice[15]`, dip_scrn.h:90). Types and geometry are what separate them.
   - **Select Race's own sub-dialogs** also run under 6: `Naming_Popup_` and `Flag_Screen_`
     (racesel.cpp:262, :271). Their shapes against the diplomacy whole-screen field are **NOT
     SETTLED**.

### Seen on the way (not about the Races screen, but it is the same hunk)
- **ext_screen_id.patch says** "every accept from race selection goes through
  `Racial_Option_Screen_` (racesel.cpp:308)". **The source contradicts that.**
  - The stock-race path (`_custom_flag == 0`, racesel.cpp:251-285) runs `Naming_Popup_` and
    `Flag_Screen_`, sets `done_flag`, and returns 1 at :451 without writing `_current_screen`. So 6
    stays in place after a stock accept.
  - New Game: nothing writes it before `Init_Map_Defaults_` sets `SCREEN_REPORTS` (mox2.cpp:211),
    called from initgame.cpp:233. Whether a `Get_Input_` tick falls in between is **NOT SETTLED**.
  - Hotseat: `Hotseat_Screen_` carries on for the next player, with 6 reported over screen 16,
    until hotpop.cpp:153 or :184.
- **The hunk changes native drawing, not only the wire.** `namestar::Input_Box_Popup_` (:339) and
  `Setup_Input_Box_Popup_` (:57) choose their font colours by `_current_screen == SCREEN_NEW_GAME`.
  `Naming_Popup_` reaches both (racesel.cpp:262/:674 → namestar.cpp:408 → :300 → :352). With the
  hunk the id is 6 or 50, not 13, so the ruler-name box takes the non-New-Game colours.
  *Source reading. Not compared against a non-EXT build.*

## 5. What would need a patch

**None is needed to tell the two apart** (§4.8, decision 25). A patch is needed only if Data wants
routing by id alone.

Draft entry (**DESCRIBED, NOT APPLIED**; not written to `doc/orion2re_open_fixes.md`):

> ### N. Select Race borrows SCREEN_RACE, which the Races screen owns — DESCRIBED, NOT APPLIED
> **What we found (orion2re 1.60, 17 September 2026).** `SCREEN_RACE` (6) is the Races/diplomacy
> screen, dispatched at mox2.cpp:61 and entered from mainscr_main.cpp:666. Our
> `ext_screen_id.patch` hunk 1 (racesel.cpp:222) makes `Race_Selection_Screen_` report the same
> 6. A client that routes by id cannot tell the two apart. OrionLayer maps 6 to Select Race, so
> the galaxy map's RACES button would open HD Select Race over the Races screen. Separately, the
> stock-race Accept returns at racesel.cpp:451 with 6 still set. The patch's note says every accept
> goes through `Racial_Option_Screen_`; that is true only for Custom.
> **The change.** Two edits inside `#ifdef ORION2RE_EXT` in racesel.cpp:
> (1) hunk 1 sets a synthetic 51 instead of `SCREEN_RACE` (outside 0-43, as 50 is);
> (2) before `return 1` (racesel.cpp:451), `if (MOX::_current_screen == 51) MOX::_current_screen
> = ext_saved_screen;`. The guard leaves Custom's `= _return_screen` (racesel.cpp:704) alone.
> Hunks 2-4 stay as they are.
> **What it carries.** One int16 that is already on the wire (STATE offset 0). No new message and
> no header change.
> **Why no existing path gives it by id.** `SerializeState` writes the `current_screen` handed to
> `Tick` (ext_api.cpp:98), which is `MOX::_current_screen` (fields.cpp:168). Nothing else names
> the running function. `previous_screen` and the field shape separate the two only by inference.
> **What it costs us.** `select_race` `GAME_SCREEN_ID` 6→51; `empire_identity` `lock_ids` (6,)→(51,)
> (select_race/screen.py:280); `custom_race` `lock_ids` (50,6)→(50,51) (custom_race/screen.py:438;
> **the observed 50→6 hop there must be re-measured**); `screen_names.py` gets 51; select_race's
> `update()` compares against 6 (select_race/screen.py:115). Then 6 is free for a future HD Races
> screen, and its dialogs still need shape classification as in decision 59.
> **Alternative, not recommended.** Leave 6 and route it by `previous_screen` inside OrionLayer.
> That needs a dispatcher rule the dispatcher does not have today.

No patch is proposed for the diplomacy dialogs: they are called functions, like the GAME popup's
dialogs (decision 59). Nothing proposed puts spy drag or who mode on the wire either; the field
shape shows who mode, and HD would own the drag.

## 6. Right-click help

The first matching rectangle wins (fields.cpp:2916-2935). A hit shows help and makes `Get_Input_`
return 0 (fields.cpp:1363-1368).

**Races**: `_races_help_list[8]` (billhelp.cpp:74-83), installed by `Races_Help_` (:118-120) at
racescrn.cpp:731:

| id | rect | title (help_en.json) |
|---|---|---|
| 259 | (320,360)-(639,422) | Races: Agents |
| 260 | (429,444)-(515,460) | Races: Ignore Button |
| 261 | (429,423)-(515,439) | Races: Report Button |
| 262 | (334,423)-(421,439) | Races: Audience Button |
| 572 | (334,444)-(421,460) | Declare War (the diplomacy entry, reused) |
| 258 | (0,0)-(319,479) and (320,0)-(639,479) | Races: Individual Displays |
| 0 | (0,0)-(0,0) | terminator, shadowed |

- **Two consequences:**
  - The two 258 halves cover the whole screen, so every right-click shows help.
  - `input < 0 → -input` (racescrn.cpp:845-847) would make a right-click on field k act as a
    left-click on k. That is unreachable while this list is active. *Source reading.*
- **Report**: `_report_help_list` = 263 over the whole screen (billhelp.cpp:85-87), installed at
  racerprt.cpp:33.
- **Diplomacy** (AI ambassador or `_game_type` 0/1 only; dip_scrn_main.cpp:1958-1960,
  :2021-2023), `Setup_Diplomacy_Help_`:
  - It adds `count-1` rows at x 10..255, y from 118+step, then a whole-screen 694
    "Diplomacy Options" (:1955-1982).
  - Main list 567-574 (dip_scrn.cpp:7). Propose 576-580, 613 (:11). Break 582-586, 613 (:65).
    Demand 588-596, 613 (:70). Offer 598-602, 613 (:76). Repulsive 578, 572-574 (:71).
  - Whole-screen: `Setup_Full_Screen_Diplomacy_Help_` with 609/616 for the system picker
    (dip_scrn.cpp:726-728), 614 declare war (:239), 612 surrender (:282), 615 money
    (dip_scrn_main.cpp:927), 694 generic.
  - The fade-in and response boxes remove help (dip_scrn_main.cpp:1261, :1081).
  - Present in `help_en.json`, checked by id: 258-263, 567-580, 582, 588, 598, 609-616, 694.
    The rest of 583-602 was not looked up.

## 7. Layout under one provisional content box

**It fits the rule, with one qualification: the box is the whole native screen.**
- The frame is `races.lbx` 0 at (0,0), full screen (racescrn.cpp:776). There is no inner frame.
  Every rectangle is absolute in 640×480 and comes from the tables at racescrn.cpp:32-47 or from
  literals.
- The deciding extents:
  - left column x 21..308: portrait 21, bar 99..113, text 125..307, spy strip 121..308
  - right column x 322..620, **mirrored**: text 333, spies 333..520, bar 522..536, portrait 544..620
  - rows y 43..458
  - control block: agent pool (328,386)-(613,415), bonus strings centred at (417,372) and
    (519,372), buttons (334..515, 423..460), exit (535,433)
  - help 259 (320,360)-(639,422)

  The union is roughly (21,43)-(620,471), and nothing inside is independent of that one canvas. So
  one provisional box standing for native (0,0)-(639,479) carries the whole screen.
- **Transcribe the per-slot tables; do not generate a grid.**
  - Portrait y: 49/156/262/369 on the left (gaps 107, 106, 107) and 50/157/262 on the right.
  - Text y: 50/157/262/**366**.
  - Bar y: 49/155/262/370 on the left and 49/156/261 on the right.
  - Spy strips 98/205/311/417 against 98/206/311.
  - Spy buttons x+0, +76, +149 (not a uniform step).
  - Left and right columns differ in layout: the portrait moves to the outside, and the slider x is
    96 against 520 (:44). A hundred children under one box is fine; a hundred children derived from
    a pitch is not.
- **The report and the diplomacy dialogs are full-screen art too, each with its own single box:**
  - Report: portrait (70,28), panel fill (212,23)-(620,457), exit (534,433); racerprt.cpp:87-135.
  - Diplomacy: list (10,118) width 245; statement at x 80 width 470 centred on y 440; header
    (320,10); dip_scrn_main.cpp:1586, :1618, :1203.
  - System picker: box (9,170) 182×112, galaxy (10,171) 180×110; dip_scrn.cpp:836-838.
- **NOT SETTLED:** whether HD treats the diplomacy dialogs as one frame or one per dialog. The
  backdrop is the same animation for all of them (dip_scrn_main.cpp:1645-1657).

## 8. Questions for Data before a build can start

1. Route 6 by `previous_screen` and field shape in OrionLayer, or apply the §5 patch (51 for
   Select Race)?
2. Until then, should `select_race` refuse id 6 when `previous_screen == 0`, so the RACES button
   falls back to the native framebuffer instead of drawing Select Race?
3. Is the stock-accept leak (6 stays set after racesel.cpp:451, visible over the Hotseat screen)
   for `doc/orion2re_open_fixes.md`, as a correction to the patch's own note?
4. Are the ruler-name box colours changed by our hunk (namestar.cpp:57/:339) to be compared
   against a non-EXT build, or accepted?
5. Races: one HD screen with who mode read off the field shape (count 8+5n against 7+n), in the
   style of decision 59?
6. The spy drag moves a pointer-computed count: build it in HD as INJECT_CLICKs at computed x, or
   leave spies out of the first build and mark them?
7. Mission buttons accept only INJECT_CLICK (type 3, set in `Draw_Field_`). Acceptable, or a
   question to Joes?
8. May the four action radios be driven by ACTIVATE_FIELD or by their hotkeys A/R/I/D? The
   source says the id is compared; this needs one live check.
9. Should `relations`, `treaty`, `trade_treaty`, `research_treaty`, `tribute_treaty`, the two
   agreement levels, `spies`, `ignoring` and `objectives` be added to `core/structs/player.py`
   through the header-compile route before any number is drawn (decision 23)?
10. Spy and agent bonus percentages depend on leaders and the tech table, neither verified. Draw
    them from the framebuffer, omit them, or wait?
11. Omniscient, eliminated and uncontacted races get a portrait but no bar (racescrn.cpp:792).
    Transcribe that?
12. Diplomacy dialogs: transcribe them in HD (statement text is not on the wire), or leave them on
    the native framebuffer for the first build?
13. Disabled diplomacy options are not on the wire: recompute `Diplomacy_Set_Main_Options_` in HD
    (decision 33 limits this to one-comparison rules; this is not one), or send activations and
    accept silent refusals?
14. Race report (tech review subscreen): in scope for the first build, or native fallback?
15. Should ESC in who mode leave the whole screen as the source says (§2b), and is that to be
    verified live before it is transcribed?
