# Work order 180, part B1 — the single-colony screen: inventory

27 September 2026, against orion2re `9ab84230` (`orionlayer-local`,
1.60.0). The reading this rests on is `doc/colony_screen_reading.md`
(work order 126 G); **the engine's colony sources have not changed since
it was written** — `git log --since=2026-09-16` over `colony_main.cpp`,
`colony.cpp`, `colbldg.cpp`, `coldraw.cpp`, `colsysdi.cpp`, `erichelp.cpp`
is empty; their last commit is `b44cbf76`, 9 August 2026 — so its line
references stand, and every one used below was re-read.

## The two things 126 said are not on the wire — still true

- **Which colony is shown.** `Colony_Screen_` derives it on entry from
  `MOX::_screen_data` (the star) and `COLONY::_orbit_temp`
  (colony_main.cpp:249-255) into `COLONY::_colony_handle`. None of the
  three is serialized: the trailing blocks of `SerializeState` on
  `9ab84230` are FSEL (fix 20), FLTS (27), OFFS (30) and INFS (32), plus
  the save-slot message of fixes 14/34, which reads `_screen_data` only to
  decide whether to send slots (ext_api.cpp:482-488) and does not send it.
  `grep -n "_colony_handle\|_orbit_temp" src/ext/ext_api.cpp` is empty.
- **The build and ship lists** (screen 25): `COLBLDG::_building_indexes`,
  `_military_indexes` and the queue under edit `_current_item` — the same
  grep over `ext_api.cpp` is empty. See `180-build-inventory.md`.

**Consequence for the whole screen.** Every value below belongs to ONE
colony, and without the colony's index nothing can be drawn that is not
a guess. So every "(b)" is buildable from the wire **once the colony is
known**, and the colony is the (c) that everything else waits on. That
is the order's own case: "HD must not guess the colony. Keep the screen
on the safety net." Open fix 35 carries it (part B3).

## What exists in HD today

**For screen 1: nothing.** `core/screen_names.py` names id 1 `colony`
and no folder exists; the dispatcher's decision-22 fallback shows the
game's picture and forwards clicks and keys (work orders 130 A, 177).
Since 180 A2 that is immediate — screen 1 always has a list — so it is
not a flash.

**Reusable, on the Colonies screen** (`screens/colony_summary/`), all
fed from the same colony record: the colony row model
(`colonyrows.build_rows`: name, jobs, pop cells, production, drawn
production, shortages, max pop, planet size/gravity/mineral, growth,
morale and its icon, producing), the icon walk (`colonyicons`,
coldraw.cpp:326-337 transcribed), the population figures
(`colonyfigures`, decision 50), the output rows (`colonyoutput`,
`colonyoutputicons`, decision 56), the planet surface pictures
(`colonysurfaces`, HD EXTENSION decision 58), the production names
(`core/prodname`, `core/buildnames`) and the pop move over
`MSG_SET_JOBS` (`colonymove`, `colonysend`, decision 52).

## Elements the original draws

Draw root `COLONY::Draw_Colony_Screen_` (colony_main.cpp:100-185).
Class: (a) already in HD on this screen, (b) buildable from data on the
wire (given the colony), (c) blocked, data not on the wire.

| # | element | the original's routine | data | class | HD component to reuse / plan |
|---|---|---|---|---|---|
| 1 | which colony | `Colony_Screen_` colony_main.cpp:249-255 | `_screen_data`, `_orbit_temp`, `_colony_handle` | **(c)** | open fix 35 |
| 2 | landscape backdrop | `C_Anims_(1)`, `C_Anims_(0)` by `climate_bg_type + climate*3` (:111-115, :476-481) | colony `climate` @226 | (b) | `colonysurfaces` — Data's picture per climate, HD EXTENSION 58; the original's art is not ours to ship |
| 3 | roads | `COLDRAW::Draw_Road_List_` (:117) | building placement | **(c)** | open fix 36; nothing drawn (HD STATE) |
| 4 | top band | `Draw_Colony_Info_Background_` (colony.cpp:621-635) | none | (b) | HUD panels (decision 71) |
| 5 | system display: the star's planets, one row each | `COLSYSDI::Draw_Col_Sys_Disp_(7,24)` (colsysdi.cpp:8-49, :88) | planets' `star_index`/`orbit`/type/size, colonies' owner | (b) | new |
| 6 | galaxy inset (`_drawing_display == 1`) | `MOVEBOX::Draw_Galaxy_Map_Box_` (:142) | — | — | **unreachable in 1.60.0** (reading §2: `[9]`/`[10]` are -1000 for ever) → OMISSION, nothing built |
| 7 | planet description (`_drawing_display == 2`) | colony.cpp:1825-1831, :1861-1866 | the mode | **(c)** | open fix 35 carries `_drawing_display` |
| 8 | buildings present | `Make_Bldg_Array_For_Colony_` then `Draw_Colony_Bldgs_` (:536-631, :77-98) | colony `buildings[49]` @310 | (b) which; **(c)** where | which: a HUD list (DEVIATION: a list, not the scene); where: open fix 36 |
| 9 | satellites | `Draw_Colony_Satellites_` x `295±50i`, y 162 (colony.cpp:637-661) | `buildings[]` of type 7 | (b) which; **(c)** order | in the list; order with fix 36 |
| 10 | military units | `Draw_Colony_Info_Military_` (colony.cpp:690-704; colony_main.cpp:1193-1293) | `military[2]` @304 | (b) counts | counts as text; the unit sprites are original art → OMISSION |
| 11 | officer: frame, portrait, name or `ETA:%d t` | `Draw_Colony_Info_Officer_` (colony.cpp:706-734) | star `officer_index[8]` (raw offset 187), leader record | (b) | name / ETA; portraits exist as extracted leader art (167) |
| 12 | production rows BC, food, industry, research | `Draw_Colony_Info_Production_For_` → `Draw_Colony_Prod_` y 32/64/94/124 (colony.cpp:743-765; coldraw.cpp:36-181) | `production`, `maintenance`, `imports`, `pollution` | (b) | `colonyrows.drawn_production`, `colonyoutputicons` |
| 13 | population icons per job | `Draw_Colony_Info_Pop_For_` mode 0, x 310..510, y 62/92/122 (colony.cpp:1332-1349; coldraw.cpp:281-444) | `pop[]`, `n_pops`, `max_farms`, race | (b) | `colonyicons`, `colonyfigures` |
| 14 | morale: government icon + `|morale/2|` icons | `COLDRAW::Draw_Info_Morale_(…, 310, 33, 510)` (colony.cpp:963-965; coldraw.cpp:187-243) | `morale` @7, government trait | (b) | `colonyrows.colony_morale`, `morale_icon` |
| 15 | title `"%sColony of %s"` / `"Annihilating %s"` | `Draw_Info_Name_And_Pop_` (colony_main.cpp:806-826) | `specialty` @11, `occupation_policy` @303, planet name | (b) | new, over `colonyrows.planet_name` |
| 16 | status word Blockaded | :831-837 | star `blockaded` @162 | (b) | new |
| 17 | status word Plague / Pop Boom | :838-848, `EVENTS::Event_Check_Plague_`, `Event_Check_Population_Boom_` | `EVENTS::_event_data` | **(c)** | open fix 37; nothing drawn (HD STATE) |
| 18 | population line `"Pop %d,%03d k (%+dk)"` | :858-873 | assigned pops, `pop_roundoff`, `pop_growth` | (b) | new |
| 19 | current production: name | `Draw_Info_Build_` (:899-977), `Squeeze_Print_Paragraph_(522,38,112,141)` (:959) | `producing[0]` @277 | (b) | `core/prodname` |
| 20 | current production: picture | :879-895, colony.cpp:779 | the product | (b) id | the original's building and ship pictures are not extracted → OMISSION |
| 21 | production bar, cost, `"%d turn(s)"` | `Draw_Colony_PC_Bar_(606,43,cost,spent)` (colony.cpp:967-978); turns (:980-994), `Colony_N_Turns_To_Produce_` (colcalc.cpp:1549) | `production_spent` @293 on the wire; the COST is `Colony_Product_Cost_` (colcalc.cpp:2576) over a source table and config | **(c)** cost, turns | open fix 38; the bar and the turns draw nothing (HD STATE) |
| 22 | autobuild label | colony_main.cpp:961-974 | `auto_building` @297 (wire), `autobuild_settings.enabled` (config) | (b) byte; **(c)** setting | open fix 35 carries the setting |
| 23 | hover name strip | `Print_Scanned_String_` (colony.cpp:807-816) | `_scanned_*`, the real pointer | HD-local | HD names what is under ITS pointer |
| 24 | buttons RETURN, CHANGE, BUY, LEADERS | field system (:176), COLPUPS art | FIELD_LIST (BUY type 0 when buyable, 7 when not) | (b) | HUD buttons |
| 25 | informational boxes on entry | `Do_Informational_And_Decision_Popups_` (:323; colony.cpp:996-1055) | modal | — | a modal HD has no view for → the safety net (allowed, A2) |

## Controls the original offers

`COLONY::Update_Fields_` (colony.cpp:1405-1436), field table in the
reading §2a. "Send" is what HD sends; "hotkey first" is decision 39 as
amended.

| control | field | hotkey | handler | class | HD |
|---|---|---|---|---|---|
| pick up pops | `_job_fields[0..2]`, type 6 | — | `Get_Selected_Pop_` reads the pointer | (b) via command | the Colonies screen's click-click gesture over `MSG_SET_JOBS` (decision 52); the field cannot be driven |
| drop pops | same, type 7 while held | — | `Send_Cluster_` | (b) | part of the same command |
| RETURN | `[1]` type 0; `[2]` ESC | ESC | loop break (:350) | (b) | ESC first, the button's field as fallback |
| next colony (index +1) | `[6]` | `<` | `Get_Next_Colony_(…,0)` (:1152-1157) | (b) | key first |
| previous colony (index -1) | `[7]` | `>` | (:1174-1179) | (b) | key first |
| **CRUNCH** | `[19]` type 8 at (-1,-1) | "CRUNCH" | cheat: `production_spent = cost` (:1167-1173) | — | **NEVER** — held by a check |
| **TOGGLE** | `[20]` type 8 | "TOGGLE" | cheat toggle (:1159-1166) | — | **NEVER** — held by a check |
| recalculate | `[5]` type 7 | C | `Col_Calc_Wrapper_` or `Do_Cheats_` when `_cheats` (:1106-1114) | — | **not offered**: it has no button, and with `_cheats` set it is a cheat |
| LEADERS | `[17]` type 0 or 7 | L | SCREEN_OFFICERS (:1043-1048) | (b) | key first |
| morale info | `[12]` | — | `Show_Morale_` text box | (b) | field; the box is a modal → the net |
| BC / food / industry / research info | `[13]`..`[16]` | — | `Show_*_Production_` text boxes | (b) | field; modal → the net |
| CHANGE | `[4]` type 0 | C, **shadowed by `[5]`** | SCREEN_QUEUE_POPUP (:1146-1149) | (b) | the FIELD, never the key — a C reaches `[5]` first (fields.cpp:2608-2613); marked DEVIATION from decision 39's key-first order, with the reason |
| autobuild | `[18]` | A | toggle, or preset prompt (:1079-1094) | (b) | key first |
| BUY | `[3]` type 0 when buyable | B | `Tested_Colony_Buys_Outright_`: confirmation or refusal (:1096-1104) | (b) | key first; the box is a modal → the net |
| occupation policy | `[8]` (only if `occupation_policy == 0`) | — | `Occupation_Policy_Popup_` | (b) | field; modal → the net |
| transport | `[11]` (only while a pop is unassigned) | — | `COLXPORT::Xport_Popup_` | (b) | field; modal → the net |
| system display: planet | `_sys_disp_planet_fields[i]` | — | switch colony (colony.cpp:1794-1824) | (b) | field |
| system display: summary | `_sys_disp_summ_fields[i]` | — | `_drawing_display = 2` (:1825-1831) | (b) send, (c) draw | field; the description needs fix 35's mode |
| satellites | `_colony_satellite_fields[i]` | — | scrap confirmation; right-click info (:1582-1613) | (b) | field; modal → the net |
| buildings | `_colony_bldg_fields[r*6+c]` | — | demolish confirmation — routed by the REAL POINTER's polygon (colony.cpp:1932-2028) | — | **not offered**: an activation is swallowed or lands on the building under the pointer (reading §2a) — OMISSION |
| military units | `_military_fields[i]` | — | `NEWPUP::Troop_Popup_` | (b) | field; modal → the net |
| **`[0]`** | type 7, (0,0)-(639,479) | — | building lookup by the pointer polygon (colony.cpp:1950-1953) | — | **NEVER** — held by a check |
| right-click help | `_colony_screen_help_list`, 17 entries (erichelp.cpp:90-108) | — | — | (b) | `help.json` regions, texts from the player's HELP extract |

## The safety rule (126, and this order)

CRUNCH (`[19]`), TOGGLE (`[20]`) and the full-screen field `[0]` must
never be activated — not live, not in a test, not by any HD control. HD
finds its fields in the live list by hotkey, type and rectangle; a smoke
check (B2) fails if any send path of the colony screen can resolve to a
type-8 field, to a field whose hotkey spells CRUNCH or TOGGLE, or to the
full-screen type-7 field at (0,0)-(639,479), and the colony screen's
sender refuses them at the one place it sends.

## Counts

Of the 25 elements: **(a) 0** — nothing is on this screen in HD, though
the machinery for eight of them exists on the Colonies screen; **(b) 17**
given the colony (2, 4, 5, 8 which, 9 which, 10 counts, 11, 12, 13, 14,
15, 16, 18, 19, 20 the id, 22 the byte, 24); **(c) 5** (1, 3, 7, 17, 21 —
and with them the "where" of 8 and 9 and 22's setting); and 3 outside the
scheme: 6 unreachable in the engine, 23 HD-local, 25 a modal. Of the 20
controls: 15 (b), 2 not offered with a reason (recalculate, buildings), 3
never (CRUNCH, TOGGLE, `[0]`).
