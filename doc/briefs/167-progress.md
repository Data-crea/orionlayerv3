# Work order 167 — progress

Unattended run, 24 September 2026. The Leaders screen (orion2re
`SCREEN_OFFICERS`, 29) as an HD screen: everything the original shows
and everything the player can do on it, original artwork only, no outer
frame.

**Written so a fresh session can resume from this file alone.**

Evidence root: `~/orionlayer-fixtures/evidence/work_order_167/`.

---

## Part 0 — the order filed — **DONE**

167 was free: `doc/briefs/` had nothing above 166 and the README's last
row was 166. The order is filed byte for byte as it arrived, under
`167-work-order-leaders-screen-in-hd-complete-original-assets-no-frame.md`
(its `<n>` placeholders are left as they came — the README says content
is never reworded).

**"Clone per CLAUDE.md (full tree)"** was read as: work in the full
working tree at `/home/data/orionlayerv3`, which is a complete clone of
`origin/main` with every generated and extracted file present, the tree
work orders 164-166 committed in. CLAUDE.md names no separate clone
step. Parked as a choice (parked file, item P0).

### What already existed for Leaders (checked before anything was added)

| where | what | consequence |
|---|---|---|
| `core/screen_names.py` | `29: ("OFFICERS", "leaders")` — the slug reserved, no folder | the screen folder is `screens/leaders/` |
| `core/structs/unverified.py` | `LEADER`, `s_leader_data` 59 B, **unverified**, with work order 154's attempt: six of fifteen fields corroborated live on 67 records, `xp` numerically, two blockers that were about the Fleets panel's officer path | the struct has to be verified before anything is drawn from it (decision 23) — Part B |
| `core/game_state.py` | `leaders_raw`: 67 × 59 B, always on the wire (ext_api.cpp:156-159) | the leader records need no patch |
| `tools/struct_probe.py` | a `leaders` mode against the unverified spec | reused for the live second source |
| `screens/fleets/` | the LEADERS button (`btn_leaders`, hotkey `L`), which opens this screen | nothing to change there |
| `screens/galaxy_map/` | the LEADERS nav button (field 13), which opens this screen | nothing to change there |
| briefs 134, 137, 146, 151, 153, 154, 155, 159 | Leaders only as the Fleets button, the officer path and the struct attempt | no earlier Leaders brief |
| `doc/orion2re_open_fixes.md` | nothing about screen 29; highest item 29 | the new request is **30** |
| smoke suite | no Leaders check | a new group, `leaders` |
| `~/orionlayer.log` | 24 Sep 2026 20:01-20:02: `original shown: -, game screen 29 — no reason given` | today the screen is the framebuffer fallback |

---

## Part A — the inventory of the original — **DONE (source reading)**

Everything below is read from orion2re 1.60.0 at `e6199966`
(`src/game/officer.cpp` unless another file is named). Coordinates are
native 640x480.

### A1. Screen id, entry and exit

| | |
|---|---|
| id | `SCREEN_OFFICERS = 29` (orion2_consts.h:484) |
| loop | `OFFICER::Officers_Screen_` (:856-1195) |
| entered from | the galaxy map's LEADERS button (mainscr_main.cpp:680-694, `_return_screen = SCREEN_MAIN`), the Fleets screen's LEADERS button (flt1.cpp:724), the colony screen (colony_main.cpp:1047, colony view forced) |
| view on entry | colony view if the previous screen was the colony screen, else the last view used, ship view the very first time (`_officer_scrn_type == -1` → ship, :893-901) |
| star / stack on entry | `_temp_star_handle`, set by the caller. From the map in colony view `Get_Star_Id_For_Officers_Screen_` (mainscr.cpp:2324-2356): the open system window's star if it holds an own colony, else the first star with an own colony walking the star array from the home star; in ship view the fleet box's stack, else `Get_Ship_Stack_For_Officers_Screen_` (mainscr.cpp:2363-2383), the first stack whose head ship is the player's (mainscr_main.cpp:677-694). Colony view falls back to the home star when the handle is -1 (:912-917) |
| exit | RETURN (hotkey ESC): `_current_screen = _return_screen` (:1158-1161); on the way out limbo leaders go to the pool (`Move_From_Limbo_To_Pool_`, :563-570) and colonies are recalculated (:1187-1189) |
| fade | `Fade_Into_Leaders_Screen_` (:664-693): palette FONTS.LBX `Load_Palette_(8)`, fade out, draw, fade in |

### A2. Two views (tabs)

| view | `_officer_scrn_type` | tab field | what the right half shows |
|---|---|---|---|
| **Colony Leaders** | 1 (`LEADER_TYPE_COLONY`) | hidden field (9, 11)+button size, hotkey `C` (:2892-2899); drawn at (7, 10), OFFICER.LBX 3, frame 1 when active (:838-839) | the system display of `_officer_star_displayed` at (306, 17) (`Wrapper_For_Offscrn_System_Popup_`, :1928-1946), box art OFFICER.LBX 2 at (300, 12) |
| **Ship Officers** | 0 (`LEADER_TYPE_SHIP`) | hidden field (156, 11), hotkey `S` (:2883-2890); drawn at (160, 10), OFFICER.LBX 4 | the big ship icons of the stack `_small_ship_stack_ptr`, 5 × 3 at (302, 19) with a scroll bar (up (613, 22) `-`, down (613, 170) `+`, :2942-2960), box art OFFICER.LBX 1 at (300, 12) |

Switching is refused unless the button mode is -1 (:1140-1156).

### A3. What is on the screen (both views)

| element | source | native geometry |
|---|---|---|
| background | OFFICER.LBX 0, full screen (:648) — **the outer frame, not built in this order** | 640x480 |
| up to four leader rows | `Build_Captain_Id_List_` (:2705-2730): the player's leaders of this view's type with `status >= 0` (4 included), in index order, max 4 | row i: y = 34 + 109 i |
| portrait | OFFICER.LBX `0x15 + pict_num`; the DARKENED one `0x8F + pict_num` while `eta > 0` or `status == 4` (:626-642, :2639-2663, :3532-3540) | centred in a 75 × 90 cell at (12, 37 + 109 i) |
| name | `Leader_Name_(id, 0)` = level title + " " + name (:3099-3147), font 3, centred in 160 px from `text_x + 22` (:3624-3634) | text_x = 92, y = 38 + 109 i |
| level title | `_officer_level_names` (ship, ESTRINGS 0x308-0x30D) or `_star_officer_level_names` (colony, 0x30E-0x313), by `Owned_Officer_Level_` (xp steps 60/150/300/500/1000, level 5 only with WARLORD, :82-103) | — |
| cost column | status 4: "%d BC" right-aligned + HESTR 0x108 "to hire"; else the maintenance "%d BC" or HESTR 0x10A "no" + HESTR 0x109 "maint" (:3636-3675), font 0 | right edge 92 + 204 − 2 = 294 |
| status line under the portrait | status 0 HESTR 0x10B "Officer Pool"; 2 HESTR 0x10C "(Unassigned)"; 1 the SHIP name or the STAR name of `location`; 4 HESTR 0x10D "For Hire (%d)" with `30 − eta`, red (:3677-3738), fitted to 74 px, font 2 | centred on x 49, y = 34 + 109 i + 97 |
| ETA on the portrait | status 1 and `eta > 0`: HESTR 0x12F "ETA: %d", red, with two lines above and two below (:3073-3097) | centred on the portrait |
| skills | the special skills of the view's type first, then the general skills; per skill the icon (OFFICER.LBX `0x58 + skill/2`), the name (`_skill_data[s].name`, ESTRINGS 0x2D4-0x307, 0x26F, 0x2A0) and the bonus formatted with `_skill_data[s].format_str` right-aligned (:3747-3837); the bonus is `Officer_Skill_Bonus_` = ceil((level + 1) / level_up) × strength / 10 (:63-80) | from y = 38 + 109 i + 16, step 17; icon at x 94, name at 116, value right edge 293 |
| selected / scanned row | text in `_selected_text_colors` instead of `_normal_text_colors` (:3608-3622) | — |
| galaxy map box | `MOVEBOX::Draw_Galaxy_Map_Box_(…, 306, 235, 318, 169, …)` (:756), stars OFFICER.LBX 0x82-0x8C (:2206-2214), destination lines, small ship icons OFFICER.LBX 0x73.. (:2765-2793) | (306, 235) 318 × 169 |
| strip under the system / grid | colony view: the star's name, or "%s (%s)" / HESTR 0x92/0x93 with the leader and ETA (:810-826); ship view: the scanned big ship's name the same way (:695-727) | centred on x 466, y 210/211, 203/204 px |
| strip under the map | the scanned small ship: race name, or HESTR 0x131 "%s Fleet:" + ship counts (:2094-2204) | (364, 412) 203 px |
| PREV / NEXT | OFFICER.LBX 7 / 8, (327, 205) `,` and (568, 205) `.` (:2968-2984) — cycle own stars (colony view) or own stacks (ship view) (:1084-1106) | — |
| HIRE | OFFICER.LBX 9 at (313, 441) `H`, only while a leader of this view's type is for hire (status 4, own player) and not in hire mode; the dull picture OFFICER.LBX 18 otherwise (:2857-2868, :792-794) | — |
| POOL | hidden field at (388, 441) `P`, only with a leader and not in hire mode; OFFICER.LBX 10 frame 1 in pool mode, dull OFFICER.LBX 19 when absent (:2844-2855, :785-790) | — |
| DISMISS | hidden field at (463, 441) `D`, same condition; OFFICER.LBX 11 frame 1 in dismiss mode, dull OFFICER.LBX 20 when absent (:2831-2842, :778-783) | — |
| CANCEL (hire mode) | OFFICER.LBX 13 at (460, 439) `X`, only in hire mode (:2870-2881); the hire-mode panel OFFICER.LBX 17 at (300, 441) with the scanned leader's cost "%d bcs and %d bc/turn" (HESTR 0x121) or "%d bcs, no maintenance" (0x129) at (315, 450) (:796-808) | — |
| RETURN | OFFICER.LBX 12 at (538, 441), ESC (:2901-2908) | — |
| catch-all | hidden (0, 0)-(639, 479), no hotkey (:3013-3020) | — |

### A4. The button modes (`_officer_button_mode`)

| mode | entered by | a click on a leader then… |
|---|---|---|
| -1 normal | entry; any mode button pressed again | selects it (`_officer_selected`), or — status 4 — opens the hire question; with a star chosen (colony view) or a ship icon selected (ship view) it ASSIGNS (below) (:1394-1475) |
| 0 hire | HIRE with nothing selected (:970-986) | `Do_Hire_Officer_` (:483-504): not for hire → "%s is already in your service!" (HESTR 0x122); too poor → "You have %d BC … costs %d to hire" (0x123); else the hire popup |
| 1 pool | POOL with nothing selected (:1118-1130) | `Move_Officer_To_Limbo_` (:1797-1839): status 4 → "You may not place %s in the Officer pool" (0x12B); ship view asks `SHIPMOVE::Confirm_Officer_Change_`; the leader goes to status 2, "(Unassigned)" |
| 2 dismiss | DISMISS (:1108-1116) | "Dismiss %s?" (0x126) confirmation, then `Confirm_Officer_Change_`, then `Dismiss_Officer_` (:1489-1512) |

POOL with a leader already selected acts at once (:1123-1124).

### A5. Assignments

* **Colony view:** click an own-colony star in the galaxy map box (sets `_officer_star_chosen` and `_officer_star_displayed`; a second click on the same star un-chooses it, :1049-1067), then click a leader → `Assign_Captain_` (colony branch, :1659-1693): "Assign %s to %s?" (0x119) or "It will take %d turns for %s to arrive on %s, okay?" (0x118), and if the star already has a leader "%s, currently on %s, will be reassigned to the pool, ok?" (0x11B) / "in route" (0x11A). Refusals: 0x127 "must be hired before…", 0x128 "You cannot assign %s to %s".
* **Ship view:** select a combat ship's big icon (a non-combat ship → "You may not place leaders on non-combat ships", 0x12C, warning) and a leader, in either order → `Assign_Captain_` (ship branch, :1615-1658) with the same confirmations; an enemy ship → 0x117; a leader who cannot serve → 0x12D.
* **PREV/NEXT** cycle the displayed star / stack (:1084-1106).
* **Right click on a leader's row** → `Find_Selected_Leader_` (:3159-3220): "is in the Officer Pool!" (0x111) / "does not have a location!" (0x112) / "…being refitted at %s" (0x113) / "cannot be located!" (0x114) as a warning, or it MOVES the display to the leader's star / fleet with a timed box "Transfering display to …" (0x115 / 0x116).
* **Right click on a skill** → the skill's help box (`Print_Officer_Skill_Help_`, :1761-1792): title = the skill NAME from SKILDESC.LBX entry 0, body = SKILDESC.LBX entry 1 formatted with "<level title> <name>, the <title>," and the bonus (10 / 15 BC for Megawealth).
* **Right click on a big ship icon** → `CMBTDRW1::Detailed_View_Ship_` (:1041-1047), the combat screen's ship detail view.
* **Clicks on the system display** (colony view) → only "Colonies are not accessible during REPORTS phase" (0x12E) when entered from REPORTS (:1069-1082).
* **Hover** on a small ship icon / a star / a big icon names it in the strips (:990-1067).

### A6. Dialogs reachable from the screen

| dialog | engine | fields on the wire | reached by |
|---|---|---|---|
| confirmation | `GENDRAW::Confirmation_Box_` via `Officer_Screen_User_Box_(…, 1)` | Y (235, 302)-(286, 323), N (345, 302)-(396, 323) — `core/gamebox.CONFIRMATION` | dismiss, assign, reassign |
| message | `GENDRAW::Message_Box_` via type 0 | one ESC catcher — `core/gamebox.WARNING` | already hired, too poor, must be hired, cannot assign, cannot serve, REPORTS phase |
| warning | `GENDRAW::Warning_Box_` via type 3 | the same catcher | not in pool, non-combat ship, enemy ship, the four "where is" answers |
| timed text box | `TEXTBOX::Timed_Text_Box_` via type 5 (textbox.cpp:175-266) | the same catcher, auto-closes | "Transfering display to …" |
| skill help | `TEXTBOX::Text_Box_` (textbox.cpp:261) | the same catcher | right click on a skill |
| **hire popup** | `MAINPUPS::Random_New_Officer_Popup_` through `Hire_Officer_Popup_` (mainpups.cpp:784-930, :1644-1655, :1721-1778, :1822-1916) | REJECT `r` at (g_x + 0x2C, g_y + 0xE2) and HIRE `h` at (g_x + 0xAF, g_y + 0xE2), up to five skill help fields; g_x/g_y centre MAINPUPS.LBX 0x39 on (320, 240) | clicking a leader for hire, or any leader in hire mode |
| ship detail view | `CMBTDRW1::Detailed_View_Ship_` | the combat detail view's own | right click on a big icon |
| right-click help | `EVANHELP::Set_ColOff_Screen_Help_List_` / `Set_ShipOff_Screen_Help_List_` (evanhelp.cpp:170-212, :476-510), HELP.LBX 313-336 | — | right click outside a field that answers it |

### A7. What the screen reads

`MOX::_leaders[67]` (all of it), `_player[PLAYER_NUM]` (bc, traits WARLORD, home planet, colour), `_star[]` (names, x/y, officer_index per player, owner/colonies), `_ship[]` (names, owner, officer_index, location, status, type), `_planet[]`, `_colony[]`, ship icons and stacks (galaxy box), `_skill_data[54]` (a literal in mox.cpp:667-722), ESTRINGS (skill and level names), HESTRNGS (every message above), SKILDESC.LBX (skill help), OFFICER.LBX (all artwork), MAINPUPS.LBX 0x39-0x3B (hire popup art), FONTS.LBX 9 (palette).

**And the screen's own state, none of it on the wire:** `_officer_scrn_type`, `_officer_button_mode`, `_officer_selected`, `_officer_scanned`, `_officer_star_displayed`, `_officer_star_chosen`, `_officer_id_list[4]`, `_small_ship_stack_ptr`, the big-icon list and its selection, the scroll bar row.

### A8. What the screen writes (the actions)

`Hire_Officer_` (bc −= cost, status 0, galactic lore), `Dismiss_Officer_` → `Deassign_Officer_` (status −1, player −1, star/ship link cleared, xp to the next level threshold), `Move_Officer_To_Limbo_` (status 2), `Assign_Leader_To_Star_` / `Assign_Leader_To_Ship_` (status 1, location, eta; the previous holder to the pool), `SHIPMOVE::Recalculate_Moving_Fleet_`, colony recalculation on exit.

---

## Part B onward

(filled in as the run goes)
