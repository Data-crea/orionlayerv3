# Reading report: the diplomacy AUDIENCE screen (orion2re, as implemented)

> **Verified before filing (work order 185, part 9, 28 September 2026):** 30
> citations spot-checked against `4bf152e4` and the OrionLayer tree — the
> entry functions, the three callers and their reported ids, the report
> chain (report.cpp:640-656), the ScreenOverride sites, `fields.cpp:167`,
> `ext_api.cpp:100`/`:121`, the ambassador writes, the random variant
> (dip_scrn_main.cpp:603), the HUMAN test, player.py's offsets and 163's
> question — all agreed. The open fixes this reading led to are 46 (the
> audience's ids) and 47 (its state on the wire), `doc/orion2re_open_fixes.md`.

Work order 185, part 9. READ ONLY. Trees: orion2re `/home/data/orion2re`, branch
`orionlayer-local` at `4bf152e4` (checked with `git log -1`); OrionLayer
`/home/data/orionlayerv3`. Every citation is `file:line` on disk. "not found" means
not found, not "probably absent".

Three LBX files were opened read-only with `python3 -B` (no bytecode written) purely
to quote the English label and statement strings next to their ids: `JIMTEXT.LBX`,
`JIMTEXT2.LBX` and `DIPLOMSE.LBX` from `~/Master of Orion 2/`. These quotes are
**evidence from the data file, not from the source**. The source says which id is
read, and the file says what that id reads.

Files read: `src/game/dip_scrn.cpp` (2571 lines), `dip_scrn_main.cpp` (2327),
`dip_scrn.h`, `diplomac.cpp` (the parts cited), `npcdiplo.cpp` (the parts cited),
`report.cpp`, `racescrn.cpp`, `mainscr2.cpp`, `combfind.cpp`, `nextturn.cpp`,
`netmox.cpp`, `mox2.cpp`, `fields.cpp`, `jim.cpp`, `farload.cpp`, `colcalc*.cpp`,
`trade.cpp`, `orion2.h`, `orion2_consts.h`, `src/ext/ext_api.cpp`, `ext_api.h`,
`ext_server.cpp`.

---

## 0. The screen id: there is NO diplomacy screen id

- The SCREEN enum (`orion2_consts.h:461-496`) has **no** diplomacy or audience value.
  The values are MAIN 0, COLONY 1, DESIGN 3, FLEET 4, **RACE 6**, … REPORTS 39,
  TURN_SUMMARY 40, … SHOW_COMMAND_POINTS 43.
- `Screen_Control_` (`mox2.cpp:35-207`) has no diplomacy case. The audience is not a
  screen. It is a **nested function call**, `DIP_SCRN::Diplomacy_Screen_(int)`
  (`dip_scrn_main.cpp:1257`) or `DIP_SCRN::Npc_Diplomacy_Screen_(int16,int8)` (`:1351`).
  Its caller's `MOX::_current_screen` stays in force.
- Neither function writes `MOX::_current_screen`. Two helpers do write it, and neither
  restores it:
  - `Diplomacy_System_Display_` writes `MOX::_current_screen = 6` (`dip_scrn.cpp:717`).
  - `Diplomacy_Generic_System_List_` also writes 6 (`dip_scrn.cpp:2311`).
- No `ext::ScreenOverride` exists in any diplomacy file. The only two guards in the
  tree are `science.cpp:124` (52) and `tech.cpp:143` (53).
- **Wire consequence.** The id a client sees during an audience is its caller's id:
  6, 0 or 12 (§4). No `EVT_SCREEN_CHANGED` fires on entry, because `ext_api.cpp:1135`
  compares ids and the id does not change.
- Why the wire is live during the audience at all: `ext::Tick` runs from
  `fields::Get_Input_` (`fields.cpp:167`) as well as from `Screen_Control_`
  (`mox2.cpp:41`). Every audience loop calls `Get_Input_` (§1.4).

---

## 1. What the audience shows

### 1.1 Graphics: LBX files and entries

All indices are 0-based LBX entries. `race` is `MOX::_player[_current_ambassador].race`.

| what | file / entry | where |
|---|---|---|
| mouse image AND the screen palette | `DIPLOMAT.LBX` entry `race` | `Diplomacy_Mouse_Init_`, `dip_scrn_main.cpp:465-480`. `Far_Reload_Next_(..., race, ...)` at :466. Drawn into a 30×30 bitmap (:469-470) and set as the mouse picture (:480). Its palette is installed by `animate::Draw_Palette_` (:475), followed by `Update_Glass_Remap_Colors_` and `Set_Palette_Changes_(0,0xFF)` (:476-477). |
| background ("back page") | `DIPLOMAT.LBX` entry `race*2 + 13` | `Setup_Back_Page_`, `:1645-1657`: `Open_File_Animation_` (:1649), fill black 0,0-639,479 (:1653), `Draw_File_Animation_` (:1655), `Copy_Off_To_Back_` (:1656). The same entry is used by `Diplomacy_Load_New_Ambassador_`, `dip_scrn.cpp:120`. |
| ambassador (the talking loop) | `DIPLOMAT.LBX` entry `race*2 + 14` | `Setup_Ambassador_Pic_`, `dip_scrn_main.cpp:1665-1678`. `Open_File_Animation_` at :1668-1671. Frame 1 if called with 0, frame 0 otherwise (:1673). Drawn once statically if animations are off (:1675-1677). Also at `dip_scrn.cpp:127-129`. |
| system-picker star background | `dipstars.lbx` entry 0 | `dip_scrn_main.cpp:482` → `_diplomacy_system_star_background_seg`. Swapped into `MOX::_star_bg_seg` while the picker runs (`dip_scrn.cpp:718-719`, :808; :2310-2314, :2354). |
| system-picker star sprites | `dipstars.lbx` entries 1..11 → `MOX::_fleet_galaxy_star_seg[0..10]` | `dip_scrn_main.cpp:483-486` |
| animation buffer | 0x7C830 bytes from `_screen_seg` | `:545` |

**Per race:** yes, through the three formulas above. **Per mood:** there is no
mood-specific picture or entry in the source (not found). What varies with the
situation:

- **Animation on or off.** When `_ambassador_option == 0` (the audience is refused,
  §3.1):
  - `Draw_Diplomacy_Synch_Mode_` does not draw the animation stencil (`:1562`).
  - `Diplomacy_Fade_In_` skips the intro frames and never calls
    `Setup_Ambassador_Pic_` (`:1990-2015`).
  - `Setup_Ambassador_Pic_` is otherwise reached only when `_FULL_DRAW_SCREEN_FLAG == 1`
    (`:1557-1560`), and `Setup_Back_Page_` clears that flag (`:1646`).
  - So a refused audience draws entry `race*2+13` and **not** entry `race*2+14`.
    Whether +13 shows an ambassador by itself was not checked in the art.
- **Music.** Record byte 0 of each `DIPLOMSx` statement feeds
  `Start_Diplomacy_Music_(buf[0])` (`:751`, :553-566).
  - 0 selects `_diplomacy_bad_music` = `Random_(3)+13`.
  - Non-zero selects `_diplomacy_good_music` = `race+1`. Both are set at `:549-550`.
  - Playback is `JIM::Play_Streaming_Music_(_diplomacy_current_music + 100, -1, 1)`
    (`:1633`, :1662).
  - In the file, for example: 0x7E has music 0, 0x80 has 1, 0x8A has 0, 0xA9 has 1.
- **Fade-in.** `Diplomacy_Fade_In_` (`:1985-2016`) opens the back page (+13) and sets
  frame 1 (:1993). It then plays **up to 38 frames of the currently open animation,
  which is entry +13** (:1997-2013, drawn by `Draw_Diplomacy_Fade_In_Screen_`
  :1659-1663). Only after that does `Setup_Ambassador_Pic_(skip_anim)` open +14 (:2014).
  - Skip: a click on the full-screen hidden field or any key (`:2003-2007`).
  - The frames are skipped entirely when `settings.animations_on == 0` (`:1994-1996`).
- **Talking loop.** In `Draw_Diplomacy_Synch_Mode_`, when the animation reaches frame 0
  it is set back to frame 1 (`:1563-1566`).

### 1.2 Text

- **Statement paragraph.** `FMTPARA::Print_Formatted_Paragraph_(0x50, y, 0x1D6, _diplomacy_message, 2)`:
  - x = 80, width = 470 (`dip_scrn_main.cpp:1586`).
  - y is centred on 440: `0x1B8 - height/2` (`:1583-1584`).
  - Font style 4, outline colour 0xF8, `_diplomacy_normal_colors` (`:1569-1570`).
  - The text is regenerated from `_response_message` whenever
    `_old_response_message != _response_message` and the id is below 1000 (`:1572-1581`).
    See §3.3.
- **Header line.** Printed centred at (320, 10) (`:1618`), in a shadow colour taken from
  the ambassador's `color` (`:1588-1605`).
  - For a human ambassador: JIMTEXT2 0x43 "Player \x82: \x80", decoded with name and
    player number (`:1609-1611`; loaded at `dip_scrn.cpp:1000`).
  - Otherwise: JIMTEXT2 0x44 "\x86 Ambassador", decoded with the race (`:1613-1615`;
    loaded at `dip_scrn.cpp:1001`).
- **Network chat line.** "%s sez: %s" at (320, 29), network games only (`:1620-1630`).

### 1.3 Menus

Every menu is `fields::Get_List_Field_` (`fields.cpp:1561-1688`). One widget serves all
of them:

- **Position.** x 10, y 118, width 245 (`0x76`, `0xF5`), with `gradient_mode` 0x11. The
  one exception is the system-confirm list at (10, 102) (`dip_scrn.cpp:2352`).
- **Colours.** Normal, highlight and special colours are
  `_diplomacy_normal_colors` / `_highlight_colors` / `_special_colors`
  (`dip_scrn.cpp:62-64`), with line feed 4.
- **Title.** Each menu's title is its `help` string, drawn as the widget's last field
  (§2.0).

### 1.4 Drawing order (one frame)

The auto function is `Draw_Diplomacy_Synch_Mode_`. It is installed at every menu, e.g.
`dip_scrn_main.cpp:1186`, and runs from `Get_List_Field_` via `Invoke_Auto_Function_`
(`fields.cpp:1664`). Per frame:

1. `Set_Page_Off_` (`:1555`).
2. Only on a full redraw: `Setup_Back_Page_` (black fill, +13 drawn and copied to the
   back page), then `Setup_Ambassador_Pic_(1)` (`:1557-1560`).
3. The ambassador animation stencil (+14), if `_ambassador_option != 0` and animations
   are on (`:1562-1567`).
4. The statement paragraph (`:1569-1586`).
5. The header (`:1588-1618`).
6. The network chat line (`:1620-1630`).
7. The music tick (`:1632-1634`), then `Mox_Update_` (`:1636`).
8. The list fields themselves, drawn by the fields module after the auto function.

For the system picker, `Draw_Diplomacy_System_Display_` (`dip_scrn.cpp:841-858`) adds on
top: galaxy box (`:835-839`), "Choose A System:" at (10, 117), CANCEL at (18, 141), and
the system text (`:2370-2415`).

---

## 2. Everything the PLAYER can open (player-initiated audience)

### 2.0 Common field facts (all menus)

- `Get_List_Field_` first calls `Set_Input_Delay_(1)` and then `Clear_Fields_()`
  (`fields.cpp:1567-1568`). `Clear_Fields_` sets `_fields_count = 1`, so field 0 is the
  dummy (`:207`).
- **Item fields.** One `Add_String_List_Field_` per non-empty string (`fields.cpp:1582-1606`,
  function at :769-822):
  - Type 10 = `FIELD_TYPE_STRING_LIST` (`orion2_consts.h:217`).
  - Rectangle x 10..255 (`fields.cpp:789`).
  - Item k (0-based) has y = `118 + (k+1)·(font_height + spacing) − 1`: `cur_y += y_step`
    comes before the add (:1591), and the add stores `y-1` (:788).
  - y_end = `y + font_height + 1` (:799).
  - Hotkey = first character of `""` = **0** (`:801`, called with `s__00551100` at
    :1598-1603).
- **Disabled items** still get a field. `is_selectable` is stored inside the field data
  (`:803`), and activation of a disabled item is ignored (`:1647-1649`).
- **Title field.** One more type-10 field at (10, 117)-(255, 118+fh+1) (`:1624-1626`).
  Activating it does nothing (`:1650-1652`).
- **Count and return value.** `count = 1 + items + 1`. The return is `input − 1`, or −1
  for a negative input, which is how ESC arrives (`:1683-1687`).
- **Font 4 height** is not in the source, so absolute item y values are NOT SETTLED.
  This is the same gap as races_screen_reading §2e.

### 2.1 Entry sequence

`Diplomacy_Screen_(player_idx)` (`dip_scrn_main.cpp:1257-1349`) runs:

1. Reset state (`:1258-1277`).
2. `_current_ambassador = player_idx` (`:1271`).
3. Choose the greeting (§3.1, `:1282-1297`).
4. `Diplomacy_Fade_In_` (`:1321` network / :1325).
5. Then one of:
   - if `_ambassador_option == 1`:
     - if either party has `traits[0x13]` (TRAIT_REPULSIVE = 19, `orion2_consts.h:968`),
       `Get_Main_Repulsive_Diplomacy_Choices_` (`:1327-1329`);
     - else `Get_Main_Diplomacy_Choices_` (`:1332`);
   - otherwise only `Diplomacy_Display_Response_` (`:1336`).

### 2.2 Main menu: `Get_Main_Diplomacy_Choices_` (`dip_scrn_main.cpp:1156-1255`)

- Title: JIMTEXT 0x1E "How may I serve you:" (`dip_scrn.cpp:862`).
- Items: JIMTEXT 0x1F..0x26 (`:863-876`); item [8] is empty (`:878`).
- Count **10**.
- Help ids {567..574} (`dip_scrn.cpp:7`, `Setup_Diplomacy_Help_` `dip_scrn_main.cpp:1955-1983`).

On entry against an AI, the tradeable-tech lists are built once with
`npcdiplo::Get_Exchange_Tech_List_(me, amb, &_exchange_tech_count, _target_tech_list, _exchange_tech_list)`
(`:1159-1167`; function at `npcdiplo.cpp:1224`). That function draws `Random_(150)`
inside `Get_Tech_Exchange_Reaction_` (`npcdiplo.cpp:1069`).

On every loop iteration:

- `Diplomacy_Set_Main_Options_` (`:1680-1727`) computes the enable flags.
- If `Find_Worst_Modifier_(me, amb) <= -100` (`diplomac.cpp:2432-2453`, the minimum of
  the four modifiers; 0 when `_COUNCIL_FLAG == 3`), the menu is **not** shown. The game
  shows response 0x82 "We tire of diplomatic negotiations…" and leaves (`:1178-1184`).

| idx | label (JIMTEXT) | enabled when (`Diplomacy_Set_Main_Options_`) | action (`:1211-1249`) |
|---|---|---|---|
| 0 | 0x1F "Propose Treaty" | at least one of `Valid_Treaty_Proposal_` 7, 8, 3, 1, 2 (`:1715-1721`; the function is `diplomac.cpp:2175-2225`) | `Diplomacy_Propose_Treaty_` (§2.3) |
| 1 | 0x20 "Break Treaty" | trade, research or tribute treaty, or treaty == 1 or 2 (`:1706-1713`) | `Diplomacy_Break_Treaty_` (§2.4) |
| 2 | 0x21 "Demand" | not at war: cleared when `treaty >= 4` (`:1702`) | `Diplomacy_Demand_` (§2.5) |
| 3 | 0x22 "Offer Gift" | always | `Diplomacy_Offer_Gift_` (§2.6) |
| 4 | 0x23 "Exchange Tech" | not at war AND `_exchange_tech_count > 0` (`:1694-1697`, :1703) | `Diplomacy_Exchange_Technology_` (§2.7) |
| 5 | 0x24 "Declare War" | not at war (`:1701`) | `Diplomacy_Declare_War_Resolution_` (§2.8). On 1 it shows the reply and leaves. |
| 6 | 0x25 "Surrender" | `COLCALC::May_Surrender_Empire_` (`:1723-1726`; `colcalc.cpp:421-426`) | `Diplomacy_Surrender_` (§2.9). On 1 it leaves. |
| 7 | 0x26 "Good Bye" | always | leave. ESC (−1) also leaves. |

Every sub-action except 5 and 6 first clears `_diplomacy_message` (e.g. `:1213`) and
returns to this loop.

**How a reply is seen.** The AI's reply is not a separate dialog. It is the new
statement text drawn above the main menu, which reappears straight away (§3.3).

### 2.3 Propose Treaty: `Diplomacy_Propose_Treaty_` (`dip_scrn_main.cpp:2035-2146`)

- Title: JIMTEXT 0x28 "You propose a treaty:" (`dip_scrn.cpp:913`).
- Items: 0x29..0x2D, plus 0x2E "Cancel" (`:914-923`).
- Count 8. Help {576..580, 613, 0} (`dip_scrn.cpp:11`).

| idx | label | treaty type | enabled (`Valid_Treaty_Proposal_`, `diplomac.cpp:2175-2225`) | on the AI's "yes" |
|---|---|---|---|---|
| 0 | "Trade Treaty" | 7 | treaty < 4 and no trade treaty yet | `diplomac::Start_Trade_Treaty_` (`diplomac.cpp:2404`) → `TRADE::Start_Trade_Agreement_` (`trade.cpp:199-211`) |
| 1 | "Research Treaty" | 8 | treaty < 4 and no research treaty yet | `Start_Research_Treaty_` (`diplomac.cpp:2419`) → `trade.cpp:216ff` |
| 2 | "Peace Treaty" | 3 | treaty >= 4 (at war) | `Declare_Peace_` (`diplomac.cpp:1599-1630`) |
| 3 | "Non-Aggression Pact" | 1 | treaty not >= 4 and not 2 | `Start_Treaty_(…,1)` (`diplomac.cpp:835`) |
| 4 | "Alliance" | 2 | treaty == 1 | `Start_Treaty_(…,2)` |
| 5 | "Cancel" | — | always | nothing |

Treaty value meanings come from the turn-summary switch (`dip_scrn_main.cpp:1133-1148`):
1 non-aggression, 2 alliance, 3 peace, 4-6 war. The comment "TREATY_PEACE" on type 1 at
`diplomac.cpp:845` contradicts this.

Each branch runs, in order (`:2081-2129`):

1. `_old_response_message = -1`.
2. `Diplomacy_Determine_Treaty_Proposal_` (§3.2).
3. `Adjust_Diplomat_Modifiers_` (−10 on all four modifiers, `diplomac.cpp:1988-1995`).
4. The matching modifier −20:
   - trade/research → `trade_modifier`;
   - peace → `peace_modifier`;
   - NAP/alliance → `treaty_modifier`.
5. On success, the start function.
6. After a success against an AI, the exchange-tech lists are rebuilt (`:2135-2145`).

**Counter-demand sub-dialog.** `Diplomacy_Need_Better_Offer_` (`:783-838`) opens when
the AI answers with a demand (§3.2):

- Title: JIMTEXT 0x4A "What do you think?" or 0x4B "How about it?", chosen by `Random_(2)` (`:791-792`).
- Items: JIMTEXT 0x45 "Agree", 0x46 "Forget It" (`dip_scrn.cpp:986-987`). Count 4.
- "Agree" pays what the AI asked for (`:819-837`):
  - 1 = BC: the player's `bc` −, the AI's `bc` +.
  - 2 = system: `COLCALC::Surrender_Star_`, which is a surrender order (see §5).
  - 3 = tribute: writes `_player[me].tribute_treaty[amb] = tribute` directly.
  - 4 = tech: `Player_Gets_Tech_App_` on the AI.

### 2.4 Break Treaty: `Diplomacy_Break_Treaty_` (`dip_scrn_main.cpp:94-174`)

- Title: JIMTEXT 0x2F "Break Which treaty:".
- Items: 0x30..0x34, plus 0x2E Cancel (`dip_scrn.cpp:928-942`). Count 8. Help {582..586, 613, −1}.

| idx | label | enabled when (`:97-112`) | resolution (`Diplomacy_Break_Treaty_Resolution_` `dip_scrn.cpp:170-232`) |
|---|---|---|---|
| 0 | Break Trade Treaty | trade_treaty == 1 | type 7: `Break_Trade_` (`diplomac.cpp:1278`), reply `Get_Break_Trade_Message_` |
| 1 | Break Research Treaty | research_treaty == 1 | type 8: `Break_Research_` (`:2047`), `Get_Break_Research_Message_` |
| 2 | Break Tribute Treaty | tribute_treaty > 0 | type 9 (tribute 1) or 10: `Break_Tribute_` (`:2111`), `Get_Break_Tribute_Treaty_Message_` |
| 3 | Break Non-Aggression Pact | treaty == 1 | type 1: `Break_Treaties_` (`:1175`), `Get_Break_Treaty_Message_` |
| 4 | Break Alliance | treaty == 2 | type 2: same as type 1 |
| 5 | Cancel | always | — (`choice > 4` returns, `:143-145`) |

### 2.5 Demand: `Diplomacy_Demand_` (`dip_scrn.cpp:1349-1606`)

- Title: JIMTEXT 0x35 "Your actions:".
- Items: 0x36..0x3E, plus 0x2E Cancel (`:945-968`). Count 12. Help {588..596, 613, 0}.
- In each case, `demand_type` = the index. The AI answer is `diplomac::Get_Demand_Response_`
  (§3.2). A human target (hotseat) answers through `Get_Human_Demand_Response_`.
- After each answer, `Adjust_Diplomat_Modifiers_` runs. On acceptance,
  `Diplomacy_Give_In_To_Demand_` (`:2162-2206`) applies the result.

| idx | label | enabled when | sub-choice | on accept (`Give_In_To_Demand_`) |
|---|---|---|---|---|
| 0 | "Declare War On..." | `Get_Diplomacy_Demand_Treaty_List_(…,5)` non-empty: third races both know, whose treaty with the AI is < 4 (`dip_scrn_main.cpp:224-259`; `dip_scrn.cpp:1357-1360`) | list of their names, title JIMTEXT 0x47 (`:1437-1443`) | AI's `delayed_diplomacy_orders[x] = 0`, a war applied next turn by `Resolve_Delayed_Diplomacy_Orders_` (`dip_scrn_main.cpp:997-1023`, called at `nextturn.cpp:103`) |
| 1 | "Make Peace With..." | **only when `MOX::_game_type == 0`** and treaty 4/5 list non-empty (`:1364-1369`) | list, title 0x48 | `delayed_diplomacy_orders[x] = 1` (peace next turn) |
| 2 | "Break Alliance With..." | list of races allied (treaty 2) with the AI (`:1373-1376`) | list, title 0x49 | `delayed_diplomacy_orders[x] = 2` (Break_Treaties_ next turn) |
| 3 | "5% Annual Tribute" | no tribute either way (`:1378-1393`) | — | `Start_Tribute_Treaty_(AI, me, 1)` (`diplomac.cpp:819`) |
| 4 | "10% Annual Tribute" | same | — | `Start_Tribute_Treaty_(AI, me, 2)` |
| 5 | "Stop Spying" | always (`:1395`) | — | nothing in `Give_In` (case 5 falls to default, `:2202-2204`). The effect is inside `Get_Demand_Response_`: `stop_spying_duration[demand_value] = Random_(50)+Random_(50)+10` (`diplomac.cpp:2735-2739`). The call passes `demand_value` 0 (`dip_scrn.cpp:1547`), so index 0 is written, whoever player 0 is. Transcribed, not judged. |
| 6 | "Technology" | AI has techs the player lacks (`:1397-1403`) | `Diplomacy_Generic_Exchange_Tech_List_` over those techs, title `_demand_title` (`:1553`) | `Player_Gets_Tech_App_(me, tech)` |
| 7 | "Surrender System" | `Check_Surrender_System_(AI, me)` (`:1405-1407`; function `dip_scrn_main.cpp:758-781`) | the system picker, mode 1 (§2.10) | `Surrender_Star_(star, AI, me)` if `May_Surrender_Star_` |
| 8 | "Remove Fleet From My System" | `SHIPMOVE::Player_Has_Ships_Pestering_Other_Player_(AI, me)` (`:1409-1411`) | — | AI's `stop_blockading_duration[me] = Random_(50)+Random_(50)+10` (`:2194-2199`) |
| 9 | Cancel | always | — | — |

### 2.6 Offer Gift: `Diplomacy_Offer_Gift_` (`dip_scrn_main.cpp:311-461`)

- Title: JIMTEXT 0x3F "What Do You Offer:".
- Items: 0x40..0x44, plus 0x2E Cancel (`dip_scrn.cpp:971-984`). Count 8. Help {598..602, 613, −1}.

| idx | label | enabled when (`:317-354`) | sub-choice | effect |
|---|---|---|---|---|
| 0 | "5% Annual Tribute" | no tribute either way (`:320-337`) | — | `Start_Tribute_Treaty_(me, AI, 1)` (`:386`); AI reply `Get_Gift_Response_(…,2,1)` → 0xA2; `NPC_Proposal_Rejection_Accept_(AI, me, 1)` |
| 1 | "10% Annual Tribute" | same | — | the same with amount 2 (`:398-401`) |
| 2 | "Technology" | player has techs the AI lacks, via `Get_Differential_Tech_List_(AI, me, …)` (`:340-344`) | paged tech list (`:410`, §2.7 widget, mode 0, 11 per page) | `Player_Gets_Tech_App_(AI, tech)` (`:417`); reply `Get_Gift_Response_(…,3,tech)` → 0xA1; exchange lists rebuilt (`:422`) |
| 3 | "System" | `Check_Surrender_System_(me, AI)` (`:346-348`) | system picker, mode 0 (§2.10) | reply `Get_Gift_Response_(…,4,star)` → 0xA4, then `Surrender_Star_(star, me, AI)` (`:439-449`) |
| 4 | "Money" | player bc > 100 (`:350-352`) | `Diplomacy_Offer_Money_` (`:919-995`), see below | bc moved (`:979-980`), reply `Get_Gift_Response_(…,1,bc)` → 0xA3. `NPC_Proposal_Rejection_Accept_` runs only if `bc >= stardate*5 − 175000` (`:987-989`). |
| 5 | Cancel | always | | |

**Money sub-list** (`Diplomacy_Offer_Money_`, `:919-995`):

- Title: JIMTEXT2 8 "How much do you offer?" (`:968`).
- Balance used: `min(bc, 32000)` rounded down to 20 (`:935-940`).
- Amounts:
  - If the rounded balance is below 100: `balance/20` rows out of 20, 40, 60, 80, 100
    (`:942-949`).
  - Otherwise: five rows at 1/5, 2/5, 3/5, 4/5 and 5/5 of the rounded balance, each
    rounded to 20 (`:950-957`).
- Each row reads "  %d BC" (`s__d_BC`, `dip_scrn.cpp:44`) and is disabled when
  bc < amount (`:959-964`).
- Cancel is JIMTEXT 0x2E (`:966`).
- Full-screen help 0x267 (`:927`).

### 2.7 Exchange Technology: `Diplomacy_Exchange_Technology_` (`dip_scrn.cpp:1013-1149`)

**Tech list widget.** `Diplomacy_Generic_Exchange_Tech_List_` (`dip_scrn_main.cpp:1729-1837`):

- Page size 11 (mode 0) or 8 (mode 1) (`:1730`).
- "Previous Page..." (JIMTEXT 76) is the first row when not on the first page;
  "Next Page..." (77) follows the last tech when there are more (`:1744-1745`,
  :1759-1798).
- Cancel is JIMTEXT 46 "Cancel" (mode 0) or 70 (mode 1) (`:1746`).
- Tech names come from `TECH::Technology_Applications_Name_`, formatted "  %s" (`:1782-1783`).
- The help ids passed are the tech ids, and 0x265 for Cancel (`:1801`, :1805).
- The return is the index into `tech_ids`, or −1.

**Against an AI:**

1. List title: JIMTEXT2 3 "What tech interests you?". Rows: `_target_tech_list`
   (`:1024-1028`).
2. If `_exchange_tech_list[idx] == 0`, the AI refuses: 0xAE, possibly replaced by 0xAF
   (`:1118-1121`).
3. Otherwise `tech_2 = _exchange_tech_list[idx]`. The message is JIMTEXT2 0x2F
   "\x80 would like to give you \x85 for your \x83." (`:2064-2067`). Then comes a yes/no
   list with the Agree/Forget It rows, title JIMTEXT2 5 "Is it a trade?" (`:1123-1127`).
4. On accept (`:1136-1146`):
   - `Change_Relations_(12, me, AI, …)`;
   - both sides `Player_Gets_Tech_App_`;
   - the lists are rebuilt;
   - `Adjust_Diplomat_Modifiers_`;
   - `tech_exchange_modifier[AI] −= 20`.
5. The accept text is JIMTEXT2 0x31 "The exchange is agreed upon." (`:2074-2076`).

**Hotseat human–human** (`:1034-1068`): a second list for the other human, JIMTEXT2 4
"What tech do you want?", then the same yes/no. Network variants are at `:1069-1116`.

### 2.8 Declare War: `Diplomacy_Declare_War_Resolution_` (`dip_scrn.cpp:234-275`)

- A confirmation list: `Diplomacy_Generic_List_(1, "  Yes, I want to declare war" [JIMTEXT2 0x3B], add_cancel=1, title "REALLY DECLARE WAR?!" [0x3C])`
  (`:241-244`). Count 4. Help 0x266 (`:239`).
- On yes:
  1. AI reply `Get_Declare_War_Message_` (0x42 or 0xA0, `diplomac.cpp:2455-2468`);
  2. `Declare_War_` (`diplomac.cpp:863-930`);
  3. `Adjust_Diplomat_Modifiers_` (`:267-271`);
  4. return 1, so the main loop shows the reply and exits (`dip_scrn_main.cpp:1232-1236`).

### 2.9 Surrender: `Diplomacy_Surrender_` (`dip_scrn.cpp:277-315`)

- Confirmation: JIMTEXT2 6 "  Yes, I want to surrender", title 7 "REALLY SURRENDER?!" (`:284-287`). Help 612.
- On yes: `COLCALC::Surrender_Empire_(me, AI)` if `May_Surrender_Empire_` (`:288-290`;
  `colcalc.cpp:387-406` sets `surrender_to`). Return 1, which exits the audience.
- There is no AI reply message in the AI branch (not found).

### 2.10 The system picker and the system confirm

**`Diplomacy_System_Display_(giver, receiver, mode)`** (`dip_scrn.cpp:707-812`):

- Help 0x261 (mode 1) or 0x268 (`:725-729`).
- Message: JIMTEXT2 0x3F "Choose a system to demand \x84 surrender to you." (mode 1) or
  0x37 "Choose a system to offer \x80." (`:734-736`).
- **Fields:**
  - one `Add_Hidden_Field_(x, y, x+5, y+5, "", 0)` per star, from
    `MOVEBOX::Get_Galaxy_Map_Star_XY_(i, 10, 0xAB, 0xB4, 0x6E, 0, 0, 1, …)`, which is the
    box at (10, 171), 180×110 (`:741-745`);
  - then CANCEL `Add_Hidden_Field_(15, 139, 157, 162, "", 0)` (`:747`);
  - all type 7 (`fields.cpp:314`), hotkey 0. Count = NUM_STARS + 2.
- **Hover** (`Scan_Input_`, `:753-776`) shows the system name (JIMTEXT2 0x3A), its
  population (0x38) and planets, drawn by `Draw_Diplomacy_System_Text_` (`:2370-2415`):
  - "(Unsurrenderable)" (0x46) is appended when `!May_Surrender_Star_`;
  - "(HOMEWORLD)" (0x39) marks the capitol planet.
- **Click** (`:782-797`) is accepted only on a star the giver owns
  (`Diplomacy_System_Scan_`, `dip_scrn_main.cpp:887-917`) that `May_Surrender_Star_`
  (`colcalc.cpp:2420ff`) allows and that holds no capitol.
- It **writes `MOX::_current_screen = 6`** (`:717`) and does not restore it.

**`Diplomacy_Generic_System_List_`** (`dip_scrn.cpp:2300-2362`): an Accept/Reject list
(JIMTEXT 0x4F/0x50), title 0x4B, at (10, 102). It is used for hotseat confirms. It also
writes `_current_screen = 6` (`:2311`).

### 2.11 Repulsive main menu: `Get_Main_Repulsive_Diplomacy_Choices_` (`dip_scrn_main.cpp:2148-2284`)

Items (`dip_scrn.cpp:895-901`): 0 JIMTEXT 0x2B "Peace Treaty", 1 = main[5] "Declare War",
2 = main[6] "Surrender", 3 = main[7] "Good Bye". Count 6.

| idx | enabled when | action |
|---|---|---|
| 0 Peace Treaty | only at war (`:2159-2164`) | proposes treaty type 3 (`:2228-2237`) |
| 1 Declare War | only when not at war (`:2159-2164`) | as §2.8 |
| 2 Surrender | `May_Surrender_Empire_` (`:2166-2169`) | as §2.9 |
| 3 Good Bye | always | leave. ESC also leaves. |

The same `Find_Worst_Modifier_ < -99` → 0x82 exit applies (`:2171-2178`).

### 2.12 Hotseat and network only

Listed for completeness; none of these is reachable against an AI in a single-player
game.

- `Check_Human_Treaty_Proposal_` (`dip_scrn.cpp:415-467`), `Get_Human_Treaty_Choice_`
  (`:503-554`: Accept / Reject / "Need Better Offer" JIMTEXT 0x52).
- `Diplomacy_Human_Need_Better_Offer_` (`:1151-1347`: Offer System / Technology / Money,
  JIMTEXT2 0x34/0x35/0x40).
- `Get_Human_Demand_Response_` (`:2091-2141`).
- Chat and listen modes (`:317-405`, :556-621), including the only
  `Add_Hidden_Field_(15,139,157,162,"C")`, `(15,165,157,188,"G")` and
  `Add_Hot_Key_("\x1B")` fields (`:578-580`) and the continuous string input
  (`:329-340`, type 11).
- `Get_Net_Diplomacy_Choices_` (`:1654ff`).

The source comments `/* SINGLE_PLAYER */` at `dip_scrn.cpp:436` and :2095 label
`_game_type == 1`, but the game sets 1 for the hotseat set-up (`multplay.cpp:2214-2215`)
and 0 from the main menu (`mainmenu.cpp:403`).

---

## 3. The AI's replies

### 3.1 The greeting (player-initiated)

`Diplomacy_Screen_`, `dip_scrn_main.cpp:1282-1297`:

- **Refusal** when `Find_Worst_Modifier_ <= -100`, or `diplodef::_COUNCIL_FLAG` is 2 or 3:
  - 0x7E "The \x82 ambassador was recalled when war was declared.", or 0x7F when
    `treaty < 4`;
  - `_ambassador_option = 0`: the menu is not shown, only the response (`:1336`), and the
    animation is not drawn (§1.1).
- **Otherwise:** 0x80 "It is a pleasure to meet with you once again.", or 0x81 when
  `relations < -12`; `_ambassador_option = 1`.

### 3.2 How each reply id is chosen

| player action | deciding function | factors | reply ids |
|---|---|---|---|
| propose treaty 1, 2, 3, 7, 8 | `diplomac::Check_Treaty_Proposal_(AI, me, type, …)` (`diplomac.cpp:2923-3205`), called from `Diplomacy_Determine_Treaty_Proposal_` (`dip_scrn_main.cpp:12-86`) | `Diplomacy_Test_` (`diplomac.cpp:3259-3343`): `broken_treaties_modifier + relations + trust_worthiness` (twice for honourable), minus `(difficulty_mod − personality modifier)` where `difficulty_mod` is 0x4B NAP, `0x7D + broken` alliance, 0x3C trade, 0x28 research, or a war formula for peace (`:3065-3072`); plus `Random_(100)`, the type's modifier, Charismatic +50 / Repulsive −50, Telepathic +25, Xeno Psychology +30, and the best diplomat leader. <−75 → 0, <−50 → 2, <0 → 1, else 3 (`:3334-3342`). Alliance also needs relations ≥ 50 (`:2995-2997`). Peace also needs `time_since_last_attack >= 10` (`:3074-3076`). | 3 → 0x83 NAP, 0x84 alliance, 0x85 trade, 0x86 research, 0x87 peace, or 0x88 (random, already allied) or 0x89 (random, if you gave a gift). 0 → 0x8B (they broke a treaty), 0x8C (dishonoured), 0x8D (trust), `0x8D + last_bad_diplomatic_incident`, or 0x8A. 1/2 → a demand (0xAA) filled by `Get_Demands_` (`:2742`) into the diplomac globals `_diplomacy_proposal_*_bribe` (`diplomac.cpp:9-15`) and copied into both records by `Set_Demands_` (`:1814-1828`). The counter-demand dialog (§2.3) then returns 1 → 0x83..0x87 (`dip_scrn_main.cpp:41-62`) or 0 → 0x8A (`:63-66`). After it: `npcdiplo::NPC_Message_Rejection_Check_` (`npcdiplo.cpp:1107-1151`) turns a rejection (0x8A..0x98, 0xAE) into **0xAF** when `diplomacy_proposal_rejection <= −4`, and re-rolls that counter by personality. An unchanged id becomes 0x8A (`dip_scrn_main.cpp:81-83`). |
| break treaty | `Get_Break_Treaty_Message_` (`diplomac.cpp:2281-2304`), `Get_Break_Trade_Message_` (:2306-2337), `Get_Break_Tribute_Treaty_Message_` (:2339-2370), `Get_Break_Research_Message_` (:2378-2402) | war count, `Fleet_Comparison_`, `Random_(200)`, `_personality_break_treaty_war` | treaty 0x9A (honourable) / 0x99; trade 0x9C; research 0x9E; tribute 0xAC (honourable) / 0xAB. The AI may **declare war** inside the first and third, and it may break treaties inside the second and fourth. In all four the "war" id (0x9B, 0x9D, 0xAD, 0x9F) is overwritten before returning (`:2295-2300`, :2331-2336, :2363-2369, :2398-2401). |
| demand | `Get_Demand_Response_` (`diplomac.cpp:2593-2740`) | `(Tech_Comparison_ + Fleet_Comparison_ + Population_Comparison_)/3 + worst modifier + Random_(200) + 2·personality modifier`, then per-type penalties (`:2609-2666`), and five calls to `Adjust_Diplomat_Modifiers_` (`:2668-2672`) | under NAP/alliance: <−100 or dishonoured → 0xA5 plus `Declare_War_`; <−50 → 0xA6 plus all treaties broken; <−25 → 0xA7 plus threats and base relations −10; <0 → 0xA8; else **0xA9 accept**. Otherwise the thresholds are −150 / −75 / 0. With a modifier of exactly 0 in the second branch, `*accepted` is never written (`:2709-2733`), and the caller's `response` is uninitialised (`dip_scrn.cpp:1448` etc.). Transcribed. |
| gift | `Get_Gift_Response_` (`diplomac.cpp:2494-2591`) | writes `last_gift`; value from BC/maintenance, tech group or system population; relations += `(Random_(4)+4)·value` capped at 100; base_relations += value | 0xA3 BC, 0xA2 tribute, 0xA1 tech, 0xA4 system |
| declare war | `Get_Declare_War_Message_` (`diplomac.cpp:2455-2468`) | honourable AI, not dishonoured, treaty 1/2 | 0x42, else 0xA0 |
| exchange tech | `_exchange_tech_list[idx]` (`npcdiplo.cpp:1224ff`, random via `:1069`) | | 0xAE refusal (maybe 0xAF). The accept and trade texts are JIMTEXT2 (§2.7). |

### 3.3 Where the text comes from

**`Get_Diplomacy_Statement_(statement_id, speaker, listener, out, size)`** (`dip_scrn_main.cpp:568-752`):

- **File by language** (`:575-584`): DIPLOMSE (0 / default), DIPLOMSG (1), DIPLOMSF (2),
  DIPLOMSS (3), DIPLOMSI (4), DIPLOMSP (5). File names are at `dip_scrn.cpp:50-55`. On
  this disk only E/F/G/S exist; DIPLOMSI and DIPLOMSP are absent.
- **Entry = statement id**, except for the "framed" ids. The 14 ids 0x14, 0x16, 0x1D,
  0x1F, 0x28, 0x2A, 0x31, 0x33, 0x3A, 0x3C, 0x48, 0x4A, 0x8F, 0x91 read entry `id−1`
  and append JIMTEXT2 0x45 " (You Were Framed)" (`:586-597`, :747-749). 0x6A also reads
  `id−1`, without the suffix (`:595`).
- **Record** (`:599-604`): `Farload_Data_Static_(file, id, buf, 0, 1, 5202)`.
  - byte 0 = music flag (§1.1);
  - byte 1 = variant count n;
  - then n records of 200 bytes.
  - One variant is chosen with `Random_(n) − 1`. The chosen variant is not stored
    anywhere else.
  - In the file: 180 entries, element size 5202 = 2 + 26×200.
- **Placeholders** (bytes 0x80..0x95, `:606-745`). As called by the screen,
  speaker = `MOX::_PLAYER_NUM` and listener = `_current_ambassador` (`:1575`, :1987):

  | byte | replaced by |
  |---|---|
  | 0x80 | the player's `name` |
  | 0x81 | the player's `race_name` |
  | 0x82 | the AI's `race_name` |
  | 0x83 | the AI's `name` |
  | 0x84 / 0x85 | "a"/"an" + race name (English only, `An_` `dip_scrn.cpp:2143-2160`) |
  | 0x86, 0x93 | star name of the AI's `diplomacy_system[me]` |
  | 0x87, 0x88, 0x91 | race name of the AI's `diplomacy_proposal_war_player[me]` |
  | 0x8B | leader name of that same player |
  | 0x89 | tech name of the AI's `diplomacy_proposal_exchange_tech[me]` |
  | 0x8A | the current treaty label (`MOX::_treaty_labels`) or "Trade Treaty"/"Research Treaty" (JIMTEXT2 0x49/0x4A) |
  | 0x8C | last gift word, JIMTEXT2 0x4B..0x4E, else "FWEE!" |
  | 0x8D | building name of `diplomacy_value[me]` |
  | 0x8E | the stardate "%d.%d" |
  | 0x8F | nothing |
  | 0x90, 0x95 | the bribe: "\x82% Tribute Treaty" with 5 or 10, a tech name, "%d BC", or a system name |
  | 0x92 | the last broken treaty's label |
  | 0x94 | race name of the AI's `trust_breaker_player[me]` |

  Verified against the file: 0x83 reads "The \x82s agree to a Non-Aggression Pact…",
  where \x82 is the AI race.

**`JIM::Get_Text_Message_(file, id, dest, max)`** (`jim.cpp:336-359`) serves every
label, title and human-side message:

- entry = `id*6 + language` (`:346`);
- files `jimtext.lbx` and `jimtext2.lbx` (`dip_scrn.cpp:38-41`);
- the `Decode_Text_*` family substitutes a different code set: `jim.cpp:206-258`, with
  the general decoder `Decode_Text_Message_` at :258.

The menu labels are loaded once per audience by `Load_Diplomacy_Text_Messages_`
(`dip_scrn.cpp:860-1011`), called from `Diplomacy_Mouse_Init_` (`dip_scrn_main.cpp:546`).

**Display.**

- The paragraph is redrawn every frame from `_diplomacy_message`. When the id changed,
  that buffer is regenerated first (`:1572-1581`).
- Human-side messages are written straight into `_diplomacy_message`, with
  `_response_message = _old_response_message = 0` so the regeneration does not overwrite
  them (e.g. `dip_scrn.cpp:175-176`, :520-521).

**Dismissal.**

- A reply shown by `Diplomacy_Display_Response_` (`dip_scrn_main.cpp:1077-1104`) is a
  loop around one `Add_Hidden_Field_(0, 0, 639, 479, "", 0)` (`:1087`): count 2, type 7,
  hotkey 0. A click closes it. Whether a key press closes it was not traced in `fields`.
- All other replies need no dismissal: the next menu appears under them.

### 3.4 AI-initiated audience: what the AI says, and what the player can answer

`Npc_Diplomacy_Screen_(player_idx, is_sneak_attack)` (`dip_scrn_main.cpp:1351-1552`):

- **Statement:**
  - `sneak_attack_message` of the AI if this is a sneak attack (`:1375-1377`);
  - otherwise `_player[AI].diplomacy_message[me]` (`:1379`), set during the turn (§4.2).
- **Interactive ids** (`:1386-1397`, the same set as `Diplomacy_Message_Is_Interactive_`
  `dip_scrn.cpp:2488-2518`):
  - 0x53..0x55, 0x61..0x68, 0x7D, 0x56, 0x69, 0x6A, 0x1C..0x24;
  - they first show greeting 0x80/0x81 and a click (`:1422-1424`), then
    `Get_Non_Player_Proposals_` (`:1839-1945`).
- **The player's answer:**
  - **Most:** Accept / Reject (JIMTEXT 0x4F / 0x50), title JIMTEXT 0x4A "What do you
    think?" (`:1853`, :1856-1865, :1930-1933). Count 4. ESC counts as Reject
    (`default_retval = 1`, `:1840`, :1936-1938).
  - **0x65 (AI offers a tech exchange):** a tech list (mode 1, 8 per page) of the
    player's techs up to `diplomacy_proposal_exchange_max_value[me]`, title JIMTEXT 0x51
    "In exchange you will receive:" (`:1879-1914`). Picking one swaps the techs at once
    (`:1905-1914`). The return value is the tech **index**, so any pick other than row 0
    is then treated as a rejection by the caller (`:1427` tests `== 0`). Transcribed.
  - **0x7D:** a click only, result 1 (`:1916-1928`).
- **Accept results** (`:1427-1491`):
  - 0x1C-0x24 → reply 0x26, then `Accepted_Npc_Demand_Resolution_` (relations
    +11..23, threats cleared, `:1947-1953`) and `Npc_Give_Gift_(me→AI)` (`:2286-2327`:
    tribute, tech, BC or system from the `diplomacy_proposal_*_bribe` fields);
  - 0x53 → peace; 0x54 → the player pays and peace; 0x55 → the AI pays and peace;
  - 0x56 → war on `diplomacy_proposal_war_player`, then reply 0x58;
  - 0x61/0x62 → `Start_Treaty_` 1/2; 0x63 → trade; 0x64 → research;
  - 0x66/0x67 → war on the third party (0x67 with an AI gift); 0x68 → break treaties with it;
  - 0x69/0x6A → 0x26 plus gift, as for 0x1C-0x24.
- **Reject results** (`:1492-1538`):
  - 0x1C-0x24 → all treaties broken, reply 0x25;
  - 0x56 → treaties broken, reply 0x57;
  - 0x68 → break;
  - 0x69 → relations −50, reply 0x25;
  - 0x6A → a **sneak attack is armed** (`sneak_attack_planet/player/message`, `:1525-1530`),
    or war with reply 0xB3.
  - Also `NPC_Proposal_Rejection_Accept_(AI, me, 0|1)` (`npcdiplo.cpp:909-958`) moves
    `diplomacy_proposal_rejection`.
- **Non-interactive ids:** one response click, then side effects (`:1399-1420`):
  - 0x30-0x33 break everything;
  - 0x39/0x3A → the AI declares war;
  - 0x60/0x6B → the AI gives a gift.

---

## 4. Every way IN and OUT

### 4.1 Player-opened, from the Races screen: reported id **6**

`SCREEN_RACE = 6` is confirmed (`orion2_consts.h:466`; `mox2.cpp:61-64` →
`RACESCRN::Race_Screen_`).

- The AUDIENCE button (`btn_diplomacy`) arms WHO mode (`racescrn.cpp:1072-1078`).
- Clicking a race then runs `racescrn.cpp:908-915`:
  1. clear the `ignoring` bit;
  2. if not a network game, `DIP_SCRN::Diplomacy_Screen_(target)` (`:913`), then `break`.
- Network variants: AI target `:917-957` (`:948`); human target `:958-1013` (`:1005`).

OrionLayer's name for the button: `racesgeom.py:83` "audience" at (334, 423), type radio,
hotkey 'A'.

### 4.2 Computer-requested at turn start: reported id **0**

**Where the message is set** (during `NEXTTURN::Next_Turn_Calc_`):

- `diplomac::Clear_Diplomacy_Messages_` zeroes every `diplomacy_message`
  (`nextturn.cpp:105`, `diplomac.cpp:464-481`).
- `npcdiplo::NPC_Diplomacy_` (`nextturn.cpp:106`, `npcdiplo.cpp:72`).
- `diplomac::Determine_First_Contacts_` (`nextturn.cpp:141`, `diplomac.cpp:673-718`).
- **`diplomac::Determine_Diplomacy_Messages_`** (`nextturn.cpp:143`, `diplomac.cpp:720-816`).
  For every AI i and living human j in contact with no message yet:
  - incidents 1-9 → `Determine_Bad_Message_` (`:1433`);
  - incidents 10-11 → 'B' (0x42) / 'P' / 'Q' plus war;
  - incidents 12-16 → `Determine_Good_Message_` (`:1365`);
  - 17 → personality+1;
  - 18 → personality+7 or +13;
  - 19-23 → 'F', 'l', 'R', 'P', 'o';
  - then `Peace_Proposal_`, `Required_Alliances_`, `NPC_Required_Alliances_`,
    `Unprovoked_Good_Messages_`;
  - Repulsive cancels a range of ids (`:807-813`);
  - Council final vote: only '{' (`:738-744`).
- Other writers:
  - `Sneak_Attack_Or_Declare_War_` (`diplomac.cpp:669`, message+56; or
    `sneak_attack_message = message+70` at :659);
  - `NPC_Tech_Exchange_Check_` (`npcdiplo.cpp:1216`, 101 = 0x65);
  - `diplomac.cpp:336-350` (0x6A / 0x69 / 0x7C).

**Where it is shown** (the chain, each hop cited):

1. `Screen_Control_` case SCREEN_REPORTS (`mox2.cpp:184-187`)
2. → `MAINSCR2::Reports_Screen_` (`mainscr2.cpp:115`), which **sets
   `MOX::_current_screen = SCREEN_MAIN`** (`:119`)
3. → `Do_Begin_Of_Turn_` (`:164`, :543)
4. → `Begin_Of_Turn_` (`:553`, :486)
5. → `Main_Screen_Report_Handler_` (`:490`, :683)
6. → `REPORT::Display_Report_` (`:725`; `report.cpp:327-329`)
7. → `Display_Report_Aux_` (`report.cpp:296`)
8. → `Has_Diplomacy_Messages_` (`:317`, :621-664)
9. For each player i ≠ me, in index order, not in `ignoring`, with
   `diplomacy_message[me] != 0`: `Npc_Diplomacy_Screen_(i, 0)` (`:648` network with a
   request handshake, `:653` otherwise), then `diplomacy_message[me] = 0` (`:649`, :654).

The reported id is **0** (galaxy map) all the way through, via `fields.cpp:167`.
`Has_Diplomacy_Messages_` returns 5, which `mainscr2.cpp:727-733` treats as a pop-up
report (redraw after pop-ups). OrionLayer's modal inventory lists this as row 14
(`doc/briefs/177-progress.md:43`).

### 4.3 Sneak attack during turn processing: reported id **12**

1. `nextturn.cpp:123` `COMBFIND::Search_For_Battles_`
2. → `Do_1_Combat_` (`combfind.cpp:169`)
3. → `Russ_Combat_` (`:1504`)
4. → when the defender is human, the game is not multiplayer and `is_sneak_attack`:
   `DIP_SCRN::Show_Sneak_Attack_Message_` (`combfind.cpp:1634-1636`)
5. → `Npc_Diplomacy_Screen_(attacker, 1)` (`dip_scrn_main.cpp:1073-1075`).

This runs inside `Next_Turn_` under SCREEN_MAIN_NEXT_TURN (`mox2.cpp:79-82`;
`nextturn.cpp:43`, where `_current_screen` is reassigned only at :45), so the id is
**12**. It is followed by `Player_Attacked_Popup_` (`combfind.cpp:1637`).

### 4.4 Network only

`NETMOX::Accept_Diplomacy_Request_` (`netmox.cpp:511-547`, `Diplomacy_Screen_` at :540)
is called from `mainscr.cpp:2443`, so the id is 0.

### 4.5 Others

- **Council:** `diplodef` does not call the audience (not found). It only blocks it
  through `_COUNCIL_FLAG` 2/3 (`dip_scrn_main.cpp:1283`).
- **Events:** `EVENT_DIPLOMATIC_BLUNDER` and `EVENT_DIPLOMATIC_MARRIAGE`
  (`orion2_consts.h:131-132`) do not call it (not found).
- The complete caller list of both functions is the one above: `grep` over `src`, with
  `racescrn.cpp` ×3, `netmox.cpp` ×1, `report.cpp` ×2 and `combfind.cpp` via
  `Show_Sneak_Attack_Message_`.

### 4.6 Ways OUT

**`Diplomacy_Screen_`** leaves on:

- Good Bye, or ESC;
- a confirmed war (§2.8) or surrender (§2.9);
- `Find_Worst_Modifier_` ≤ −100 (response 0x82);
- the refusal click (option 0).

It then:

1. restores the background music (`:1340-1341`);
2. clears the fields and the animation buffer and releases `_screen_seg` (`:1342-1345`);
3. fades out (`:1346-1348`);
4. returns to `Race_Screen_`'s `break` (`racescrn.cpp:914`). The outer loop
   (`racescrn.cpp:716ff`) rebuilds the Races screen.

**`Npc_Diplomacy_Screen_`** returns after its switch. It fades the stream and restores
the saved auto function (`:1541-1551`, saved at :1361). It returns to
`Has_Diplomacy_Messages_` (next ambassador), or to `Russ_Combat_`.

---

## 5. What each outcome writes

All writes land in `s_player` (and, for systems, `s_star_data`).

| function | writes | cite |
|---|---|---|
| `Start_Treaty_(p1,p2,t)` | `treaty[]` both, `threats[]` 0, `peace_duration[]` += | `diplomac.cpp:835-861` |
| `Declare_Peace_` | `treaty` = 3, relations +50 capped at 0, `peace_duration` = 30, threats, war losses, bio flag | `:1599-1630` |
| `Declare_War_` | Break_Trade/Research/Tribute/Treaties, `base_relations` −10, `relations` = 181−Random_(25) as int8, `treaty` = 5/6 (human involved; 6 at difficulty ≥ HARD) else 4, the four modifiers −200 / −130, `reward_attack_player`, `time_since_last_attack`, `peace_duration`, `first_contact` | `:863-930` |
| `Break_Treaties_` | `last_broken_treaty`, `threats++`, `dishonored_flag`, `peace_duration`, … | `:1175ff` |
| `Break_Trade_` / `Break_Research_` / `Break_Tribute_` | the respective treaty arrays | `:1278`, `:2047`, `:2111` |
| `Start_Trade_Treaty_` → `TRADE::Start_Trade_Agreement_` | `peace_duration`, `trade_treaty`=1, `current_trade_agreement_level`, `trade_agreement_goal` | `diplomac.cpp:2404-2417`, `trade.cpp:199-211` |
| `Start_Research_Treaty_` → `Start_Research_Agreement_` | `research_treaty`=1, `current_research_agreement_level`, … | `diplomac.cpp:2419-2430`, `trade.cpp:216ff` |
| `Start_Tribute_Treaty_` | `tribute_treaty[target]` = 1/2, threats, `peace_duration` | `diplomac.cpp:819-833` |
| `Change_Relations_` | relations (tech exchange +12; NPC demand accept +11..23; reject 0x69 −50) | `:1019` |
| `Adjust_Diplomat_Modifiers_` | the four modifiers −10 | `:1988-1995` |
| `Get_Gift_Response_` | `last_gift`, `last_diplomacy_proposal_turn` /=, relations, base_relations (mirrored) | `:2494-2591` |
| `Get_Demand_Response_` | threats, base_relations, `stop_spying_duration`, war/break | `:2593-2740` |
| `Diplomacy_Test_` | the tested modifier −(20..49 / 50..99) | `:3300-3312` |
| `NPC_Proposal_Rejection_Accept_`, `NPC_Message_Rejection_Check_` | `diplomacy_proposal_rejection[]` both | `npcdiplo.cpp:909-958`, `:1107-1151` |
| `COLCALC::Player_Gets_Tech_App_` | `tech_applications[id]` = 3, `got_new_app`, government trait for four techs | `colcalc_main.cpp:578ff` |
| `COLCALC::Surrender_Star_` | `_star[i].surrender_to[]`, an ORDER. The transfer happens in `COLCALC::Do_Surrenders_` next turn (`nextturn.cpp:121`). | `colcalc.cpp:366-385` |
| `COLCALC::Surrender_Empire_` | `_player[].surrender_to` | `colcalc.cpp:387-406` |
| BC moves | `bc` of both sides | `dip_scrn_main.cpp:821-822`, :979-980, :2306-2311 |
| `Diplomacy_Give_In_To_Demand_` | `delayed_diplomacy_orders[]`, `stop_blockading_duration[]`, tribute, tech, star | `dip_scrn.cpp:2162-2206` |
| NPC reject 0x6A | `sneak_attack_planet`, `_player`, `_message` | `dip_scrn_main.cpp:1525-1530` |
| treaty 0 → n in summary | `Add_Diplomacy_Turn_Summary_Messages_` compares `last_turn_treaty` vs `treaty` (turn end) | `:1107-1154`, `diplomac.cpp:520` |

---

## 6. The globals holding the audience state (none of them in `s_player`)

**`DIP_SCRN::` (`dip_scrn.cpp`)**

| global | line | what it holds |
|---|---|---|
| `_current_ambassador` (u8) | :31 | which race |
| `_ambassador_option` (u8) | :6 | 0 refused, 1 normal, 2 AI proposal |
| `_response_message`, `_old_response_message` (i16) | :8, :10 | the statement id, and change detection |
| `_diplomacy_message[250]` | :32 | the rendered reply text |
| `_diplomacy_list_choice[15][50]` | :68 | the menu currently shown |
| `_jim_help_list[15]` | :69 | help regions |
| `_main_diplomacy_list[9]` and the other `_*_list`/`_*_title` pointers | :20ff, :71-90; allocated `dip_scrn_main.cpp:488-543` | label buffers |
| `_target_tech_list[212]`, `_exchange_tech_list[212]`, `_exchange_tech_count` | :17, :22, :19 | the tech offer |
| `_diplomacy_current_music` | :15 | music |
| `_diplomacy_good_music` | :97 | music |
| `_diplomacy_bad_music` | :99 | music |
| `_diplomacy_system_giver/_receiver/_planet_list/_planet_count/_population/_homeworld_flag/_fields[]`, `_diplomacy_scan_input_flag` | :79-94 | the picker |
| `_diplomacy_mouse_bitmap` | :95 | the cursor |
| `_talker_ambassador`, `_listen_ambassador`, `_net_diplomacy_message`, `_chat_*`, `_synch_up_established_flag`, `_net_diplomacy_esc_pressed` | :14, :18, :75, :56-61, :9, :16 | network |

**`diplomac::`** `_diplomacy_proposal_system_bribe`, `_tribute_bribe`, `_gold_bribe`,
`_tech_bribe1` (`diplomac.cpp:9-15`): the AI's counter-demand before `Set_Demands_`.
Local variables of `Diplomacy_Determine_Treaty_Proposal_` carry the offer type and
amounts (`dip_scrn_main.cpp:13-19`).

**Elsewhere:** `diplodef::_COUNCIL_FLAG`; the `file_ani` module's current animation and
frame; `EVENTS::_jim_saved_autofunction` (`dip_scrn_main.cpp:1361`).

---

## 7. Input delays: every `Set_Input_Delay_` in `dip_scrn*.cpp`

All 16 calls pass **1**.

The mechanism:

- `Set_Input_Delay_` sets `_input_delay` and flushes both mouse buffers
  (`fields.cpp:143-147`).
- `Clear_Fields_` sets `_input_delay = 0` (`fields.cpp:208`).
- While the delay is above 0, `Get_Input_` returns 0 **before** `ext::Tick`
  (`fields.cpp:161-164`).
- `Get_List_Field_` does its own `Set_Input_Delay_(1)` followed by `Clear_Fields_()`
  (`fields.cpp:1567-1568`).

**Every one of the 16 is therefore zeroed before the next `Get_Input_`.** What remains
of them is the mouse-buffer flush.

| file:line | function | what zeroes it before input |
|---|---|---|
| dip_scrn.cpp:1416 | `Diplomacy_Demand_` | `Get_List_Field_` :1429 |
| dip_scrn.cpp:1698 | `Get_Net_Diplomacy_Choices_` (net) | `Clear_Fields_` :1709 / listen mode :575 |
| dip_scrn.cpp:2344 | `Diplomacy_Generic_System_List_` | `Get_List_Field_` :2352 |
| dip_scrn_main.cpp:115 | `Diplomacy_Break_Treaty_` | `Get_List_Field_` :128 |
| dip_scrn_main.cpp:274 | `Diplomacy_Generic_List_` | `Get_List_Field_` :299 |
| dip_scrn_main.cpp:357 | `Diplomacy_Offer_Gift_` | `Get_List_Field_` :372 |
| dip_scrn_main.cpp:797 | `Diplomacy_Need_Better_Offer_` | `Get_List_Field_` :810 |
| dip_scrn_main.cpp:1187 | `Get_Main_Diplomacy_Choices_` | `Get_List_Field_` :1203 |
| dip_scrn_main.cpp:1254 | end of `Get_Main_Diplomacy_Choices_` | `Clear_Fields_` in `Diplomacy_Screen_` :1343 |
| dip_scrn_main.cpp:1277 | `Diplomacy_Screen_` | `Clear_Fields_` :1278 |
| dip_scrn_main.cpp:1369 | `Npc_Diplomacy_Screen_` | `Clear_Fields_` :1370 |
| dip_scrn_main.cpp:1734 | `Diplomacy_Generic_Exchange_Tech_List_` | `Get_List_Field_` :1809 |
| dip_scrn_main.cpp:1871 | `Get_Non_Player_Proposals_` | `Get_List_Field_` :1930, `Clear_Fields_` :1917 or :1732 |
| dip_scrn_main.cpp:2054 | `Diplomacy_Propose_Treaty_` | `Get_List_Field_` :2069 |
| dip_scrn_main.cpp:2185 | `Get_Main_Repulsive_Diplomacy_Choices_` | `Get_List_Field_` :2213 |
| dip_scrn_main.cpp:2280 | exit of the same | `Clear_Fields_` :1343 |

---

## 8. The WIRE question

**What `SerializeState` sends** (`ext_api.cpp:94-632`):

- the identity header, with `current_screen` first (`:100`);
- `s_settings` whole (`:119`);
- **all 8 `s_player` records whole** (`:121-124`);
- stars, ships, colonies, planets, nebulas and leaders whole (`:126-160`);
- antarans, ship icons, ng_* values, icon owners, and FSEL (`:162-242`).

The screen-specific optional blocks are written only on FLEET (FLTS `:266`), OFFICERS
(OFFS `:345`), INFO (INFS `:419`), COLONY / QUEUE_POPUP (COLS, CBLD, CEVT, CPRD, BLDQ,
BLDL, `:459-631`). **No block exists for the audience.** None could key on its id, since
it has none.

Also sent:

- **The field list:** index, rectangle, type and hotkey per field (`:636-651`). It is
  re-sent only when the count changes, the screen changes, or a client reconnects
  (`:1151-1153`; `ext_server.cpp:192-194`).
- **The framebuffer and palette:** 640×480×8 plus 768 bytes (`:704-719`).

OrionLayer keeps each player record as the raw 3854 bytes (`core/game_state.py:203-205`,
`PLAYER_SIZE` :16) and decodes a subset through `core/structs/player.py`.

**Offsets** of the diplomacy fields that are not in the spec were computed by hand from
`orion2.h:1755-1919`, between two compiler-verified anchors: `tribute_treaty` @1700
(`player.py:224`) and `traits` @2308 (`player.py:235`). The running sum lands exactly on
2308, and continued to the end it gives exactly 3854. They are still **header route,
hand-summed, not compiled**: `tools/struct_header_check.py` should confirm them before
use.

| data the audience needs | on the wire today? | carrier |
|---|---|---|
| which race (`_current_ambassador`) | **no** | DIP_SCRN global (`dip_scrn.cpp:31`). Reconstructable in part: Races path = the race HD sent in WHO mode; turn-start path = the lowest i ≠ me with `player[i].diplomacy_message[me] != 0` and not in `ignoring`, because the message is cleared only after that audience (`report.cpp:627-654`); sneak attack = no reliable carrier. |
| reported screen id | yes, but ambiguous | header int16 (`ext_api.cpp:100`): 6 / 0 / 12 as the caller, and 6 during a picker |
| race → art | yes | `s_player.race` @37 (`player.py:104`, VERIFIED) |
| leader mood / animation frame | **no** | `file_ani` module state. Only the framebuffer shows it. Good/bad music is byte 0 of the DIPLOMSx record, so it follows from the statement id. |
| the statement id (`_response_message`) | **no** | DIP_SCRN global. The opening id of an AI audience is on the wire as `diplomacy_message[8]` @1724 (hand-summed) of the AI's record, or `sneak_attack_message` @2094. The greeting substitution 0x80/0x81 follows from `relations` (on the wire). Every later reply id is not. |
| the reply text | **no** | `_diplomacy_message[250]`, a global. The variant is `Random_(n)−1` of the record (`dip_scrn_main.cpp:603`), so even a known id does not name the text. Visible only in the framebuffer. |
| the menu shown | **no** (its geometry yes) | the field list gives count and rectangles, type 10, hotkey 0. Propose, Break and Offer are all count 8 at the same place. Need-better, NPC Accept/Reject and the war/surrender confirmations are all count 4. |
| the menu's item strings | **no** | `_diplomacy_list_choice`. The labels themselves are JIMTEXT/JIMTEXT2 ids, so they are reconstructable from the file. |
| which items are enabled | **no** | `item_flags`, stored in the field data but not serialized (`ext_api.cpp:642-649`). Reconstructable in part from s_player (`Valid_Treaty_Proposal_` and the treaty arrays are pure); tech-dependent flags are not (next rows). |
| techs offered (exchange) | **no** | `_target_tech_list`, `_exchange_tech_list`. They depend on `Random_(150)` (`npcdiplo.cpp:1069`), so they are not reconstructable. |
| techs for gift / demand lists | **no** | locals. `Get_Differential_Tech_List_` over `tech_applications` (on the wire @379), but values come from `newtech::Calc_Tech_Value_`, which would have to be re-implemented. |
| BC amounts | **no** | locals. Pure arithmetic of `bc` @50 (on the wire). |
| AI counter-demand (type, amount) | partly | locals / diplomac globals. After `Set_Demands_` in both records: `diplomacy_proposal_tribute_bribe` @1988, `tech_bribe1` @1996, `gold_bribe` @2012, `system_bribe` @2076 (hand-summed). |
| AI proposal payload | yes (raw) | `diplomacy_proposal_war_player` @2028, `_exchange_max_value` @2036, `_exchange_tech` @2068, `diplomacy_system` @1764, `diplomacy_value` @1748 |
| treaty / relations | yes | `relations` @1660, `treaty` @1676, `trade_treaty` @1684, `research_treaty` @1692, `tribute_treaty` @1700 (`player.py:220-224`, spec) |
| modifiers (worst-modifier gate) | yes (raw) | `treaty_modifier` @1780, `trade_` @1796, `tech_exchange_` @1812, `peace_` @1828 |
| `_COUNCIL_FLAG` (refusal gate) | **no** | `diplodef` global |
| `ignoring`, `objectives`, `personality`, `traits` | yes | `player.py:231`, :107, :106; TRAITS_OFFSET 2308 |
| settings language / animations_on | yes | `settings.py:70`, :42 |
| star `surrender_to` | yes (raw) | `s_star_data` whole (`ext_api.cpp:127-130`); not checked against `core/structs/star.py` |

### 8.1 The line parked by work order 163

The exact words "until the diplomacy screen" do **not** occur in
`doc/ai_behaviour_reading.md`. They are the work order's paraphrase
(`doc/briefs/185-work-order-open-items-ship-designer-audience.md:90`). The parked line
is open question 3, `doc/ai_behaviour_reading.md:402-407`:

> 3. **Do you want `objectives` on the HD side?** It is one line in
>    `core/structs/player.py`, at an offset both of whose neighbours are
>    already verified, and it would let an HD screen say what an AI
>    player is playing for. `relations[]` and `treaty[]` are the same
>    kind of one-line additions and are what a diplomacy screen would
>    need.

Its premise is §5 of the same document, `:273-274`: "So every AI-state field in
`s_player` is **already on the wire today**, with no patch and no change to orion2re".
The code it cites is placed at `ext_api.cpp:120-122` (`:270`); the actual lines are
121-124.

**Answer, from the source and the wire code.**

1. **Yes, the player record is on the wire, all 3854 bytes of all 8 players, every
   snapshot** (`ext_api.cpp:121-124`). **That includes while an audience is up.** Every
   audience loop calls `fields::Get_Input_`, and `Get_Input_` calls `ext::Tick`
   (`fields.cpp:167`). The loops that do so:
   - `Diplomacy_Display_Response_` `dip_scrn_main.cpp:1088`;
   - `Get_List_Field_` `fields.cpp:1642`;
   - the fade-in `:2004`;
   - the picker `dip_scrn.cpp:752`;
   - the 0x7D wait `:1919`, :1925.
   
   Outcomes are written to `s_player` the moment they happen (§5), so the next snapshot
   already shows, for example, a new `treaty[]`.
2. **`objectives` is declared on the HD side.** `("objectives", 40, "u8")` is at
   `core/structs/player.py:107`, and `relations`/`treaty`/`trade_treaty`/
   `research_treaty`/`tribute_treaty` are at `player.py:220-224` (work order 175 C).
   Question 3's three "one-line additions" are therefore done.
3. **The audience needs `objectives`.** It tests `objectives == PLAYER_OBJECTIVE_HUMAN`
   (100, `orion2_consts.h:429`) for the ambassador throughout, e.g.
   `dip_scrn_main.cpp:1159`, :1609, :23. It never reads the other objective values.
4. **What is NOT on the wire** is the audience's **own** state (§6): who is being talked
   to, the statement id, the reply text, the menu and its enable flags, and the offered
   techs and amounts. The player record does not carry them, and no optional block does.
5. **Stale claims found on the way.**
   - `doc/pop_order_reading.md:126` says "Nothing on the wire reports `objectives`". That
     is wrong: it is byte 40 of each record, and is decoded at `player.py:107`.
   - `doc/races_screen_reading.md:256-263` lists relations, treaty and the treaties as
     "on wire, not in spec". They are in the spec now (`player.py:220-224`).
   - `races_screen_reading.md:242` cites `ext_api.cpp:119-121` for the players; the
     actual lines are 121-124.

---

## 9. What the OrionLayer tree already has

- **`screens/races/`**: the Races screen (work order 175 C, "BUILT, NOT ACCEPTED",
  `screen.py:1-5`).
  - `raceswire.View` classifies a snapshot as MAIN / WHO / IN_BOX / WAITING / DIALOG
    (`raceswire.py:102-131`).
  - A diplomacy audience under id 6 has neither field shape. After `WAIT_BOUND` = 66
    snapshots (`:47`) it becomes DIALOG with the reason "the race report or diplomacy"
    (`:126-131`), and the screen hands over to the original picture
    (`screen.py:92-100`; module doc `raceswire.py:25-30`, `screen.py:23-26`).
  - The AUDIENCE button's geometry is at `racesgeom.py:83`, its label at `racesdraw.py:43`.
  - Nothing in the tree draws the audience in HD (not found).
- **`core/screen_names.py`**: no diplomacy id, and the engine has none either (§0).
  - Id 6 is `("RACE", "races")` (`:39`); 0 is `galaxy_map` (`:35`); 12 is
    `("NEXT_TURN", None)` (`:44`).
  - The only mention is the comment at `:66-70`: race selection used to borrow 6 and
    "HD drew Select Race over diplomacy".
  - A synthetic id for the audience would need to lie above `ENGINE_SCREEN_MAX = 43`
    (`:93`), as 50-53 do.
- **String extractors.** None reads JIMTEXT, JIMTEXT2 or DIPLOMSx: `grep -i` for
  `jimtext|diploms|diplomat.lbx|dipstars` over the tree finds only prose in
  `doc/races_screen_reading.md:83`, :214 and `doc/briefs/177-progress.md:43`.
  - **Reusable walk:** `tools/billtext_extract.py` (`:12-24`) and `core/billtext.py`
    (`:10-20`) implement exactly `Get_Text_Message_`'s `id*6 + language` addressing
    (`jim.cpp:336-359`) for BILLTEXT.LBX. JIMTEXT.LBX (498 entries) and JIMTEXT2.LBX
    (480) have the same shape: 100-byte records read this way, as done for this report.
  - `tools/kentext_extract.py:10-24` and `tools/infotext_extract.py:23` (BILLTEX2)
    document the same addressing.
  - **DIPLOMSx is a different shape.** One entry per statement id, element size 5202:
    music byte, count, then 200-byte variants (`dip_scrn_main.cpp:599-604`). No extractor
    exists (not found).
  - The help texts for the audience's help ids (567-613, 0x2B6, 0x261-0x268, 612) are in
    whatever `tools/help_extract.py` writes. It walks every HELP.LBX record
    (`help_extract.py:222`), but no screen's `help.json` references them (not checked
    beyond this grep).
  - ESTRINGS (`tools/estrings_extract.py`) holds the treaty labels the statement's 0x8A
    and 0x92 codes use (`MOX::_treaty_labels`; races_screen_reading §3 cites
    `estrings.cpp:91-97`).
- **Art extractors.** `tools/races_art_extract.py` takes only `RACES.LBX` (portraits
  32+race, overlay 31, spy icons 46+race) and the `RACES.LBX` 0 palette over `FONTS.LBX`
  9 (`races_art_extract.py:15-24`).
  - **It takes nothing from `DIPLOMAT.LBX` or `DIPSTARS.LBX`.**
  - No extractor for the audience art exists (not found).
  - Both files are present on this disk (`~/Master of Orion 2/`), as are DIPLOMSE, F, G
    and S, JIMTEXT and JIMTEXT2.
- **Prior reading.** `doc/races_screen_reading.md` §1 builders table (`:83-86`) and §2e
  (`:202-239`) already cover the diplomacy field shapes (count 10 main, sub-lists
  count = items + 2, system picker). The statement's wire status is at `:271-272`.

---

## Final table

"hs" = hand-summed from `orion2.h` between compiler-verified anchors (§8).

| piece | what it is | source (file:line) | on the wire today | reconstructable on HD side |
|---|---|---|---|---|
| audience entry id | caller's screen: 6 Races, 0 turn start, 12 sneak attack | racescrn.cpp:913; mainscr2.cpp:119 → report.cpp:653; combfind.cpp:1636, nextturn.cpp:43 | yes: header int16, ext_api.cpp:100 (no own id, no event) | partly: the id plus a field shape tells "some dialog", not "audience" |
| current ambassador | `_current_ambassador` | dip_scrn.cpp:31; set dip_scrn_main.cpp:1271, :1364 | no | partly: Races = HD's own click; turn start = lowest i with `diplomacy_message[me]≠0` @1724 hs, not ignored (report.cpp:627-654); sneak = no |
| background art | DIPLOMAT.LBX race*2+13 | dip_scrn_main.cpp:1649 | race yes: @37 player.py:104 | yes, with a new extractor (none exists) |
| ambassador animation | DIPLOMAT.LBX race*2+14, frame loop | dip_scrn_main.cpp:1668-1673, :1562-1566 | no (only the framebuffer) | partly: the art yes, the frame phase no |
| fade-in | 38 frames of +13 | dip_scrn_main.cpp:1985-2016 | no | partly (same) |
| palette / cursor | DIPLOMAT.LBX entry race | dip_scrn_main.cpp:465-480 | race yes | yes, with an extractor |
| mood / music | good = race+1, bad = Random(3)+13, from record byte 0 | dip_scrn_main.cpp:549-550, :751 | no | partly: the flag yes once the id is known; bad music is random |
| refused audience | option 0, 0x7E/0x7F, no ambassador drawn | dip_scrn_main.cpp:1282-1290, :1562, :1990 | modifiers yes (hs @1780-1843); `_COUNCIL_FLAG` no | partly |
| greeting | 0x80/0x81 by relations < −12 | dip_scrn_main.cpp:1291-1296 | relations yes, player.py:220 | yes (id); the text variant no |
| statement id | `_response_message` | dip_scrn.cpp:8 | no; AI opening id only: `diplomacy_message` @1724 hs, `sneak_attack_message` @2094 hs | partly: opening id yes, replies no (random factors) |
| reply text | `_diplomacy_message[250]` from DIPLOMSx id, random variant, 0x80-0x95 substitution | dip_scrn_main.cpp:568-752 | no (framebuffer only) | partly: candidates and placeholders yes; the chosen variant no |
| header line | JIMTEXT2 0x43/0x44 | dip_scrn_main.cpp:1609-1618 | inputs yes (name, race_name) | yes |
| menu widget | `Get_List_Field_` at (10,118) w245, type 10, hk 0 | fields.cpp:1561-1688, :769-822 | yes: FIELD_LIST, ext_api.cpp:636-651 | yes (geometry) |
| which menu | main 10 / propose, break, offer 8 / demand 12 / yes-no 4 / repulsive 6 | dip_scrn_main.cpp:1202, :2069, :128, :372; dip_scrn.cpp:1429 | only through the count | partly: ambiguous (8 and 4 each cover several menus) |
| item labels | JIMTEXT 0x1E-0x52, JIMTEXT2 | dip_scrn.cpp:860-1011 | no | yes, with a JIMTEXT extractor (billtext walk) |
| enabled items | `Diplomacy_Set_Main_Options_`, per-menu flags | dip_scrn_main.cpp:1680-1727, :97-112, :317-354; dip_scrn.cpp:1350-1413 | no | partly: treaty-based flags yes; tech and surrender-based need `Calc_Tech_Value_` and `May_Surrender_Star_` |
| exchange techs | `_target_tech_list`, `_exchange_tech_list` | npcdiplo.cpp:1224ff, random :1069 | no | no |
| gift / demand tech lists | `Get_Differential_Tech_List_` | npcdiplo.cpp:1013ff | inputs: `tech_applications` @379 | partly (tech-value rules) |
| BC amounts | `Diplomacy_Offer_Money_` | dip_scrn_main.cpp:919-995 | `bc` @50 yes | yes |
| AI counter-demand | `_diplomacy_proposal_*` → `Set_Demands_` | diplomac.cpp:9-15, :1814-1828 | after Set_Demands_: @1988, 1996, 2012, 2076 hs | partly |
| AI proposal payload | war player, exchange tech/max, system, value | orion2.h:1843-1844, :1868-1871 | yes (raw): @2028, 2068, 2036, 1764, 1748 hs | yes (decode needed) |
| NPC answer list | Accept/Reject, or tech list (0x65), or click (0x7D) | dip_scrn_main.cpp:1839-1945 | no | partly (the id decides; the tech list needs tech values) |
| treaties | treaty, trade, research, tribute | diplomac.cpp:835ff etc. | yes: player.py:220-224 | yes |
| relations / modifiers | relations, base_relations, 4 modifiers | orion2.h:1834-1848 | yes: relations spec; the rest raw hs | yes |
| tech outcome | `Player_Gets_Tech_App_` | colcalc_main.cpp:578 | yes: tech_applications @379 | yes (after the fact) |
| BC outcome | bc moves | dip_scrn_main.cpp:821, :979, :2306 | yes: @50 | yes (after the fact) |
| system outcome | surrender order | colcalc.cpp:366-385 | yes (raw star record) | yes (after the fact; transfer next turn) |
| delayed demands | `delayed_diplomacy_orders` | dip_scrn.cpp:2165-2173 | yes: @2300 hs | yes |
| objectives (163's line) | HUMAN test only | orion2_consts.h:429; dip_scrn_main.cpp:1159 | yes: @40, player.py:107 | yes |
| input delays | 16 × `Set_Input_Delay_(1)`, each zeroed | §7 | n/a | n/a |
