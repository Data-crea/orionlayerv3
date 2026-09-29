# Multiplayer in orion2re — what the engine offers (work order 188, Part 7)

The reading report of Part 7 ("First establish from the source what orion2re
really offers for multiplayer"), as a sub-agent wrote it from the source on
28 September 2026, kept as it came; the session's live exploration of the
same screens (their field lists and native frames,
`~/orionlayer-fixtures/evidence/work_order_188/P7_explore_1920x1080/`) adds
what the source reading could not see:

- **The artwork still says MODEM where the engine's type is ONLINE.** The
  setup's three radios read NETWORK / MODEM / HOTSEAT and its fourth button
  COMM INFO (MULTIGM.LBX art); selecting MODEM sets the engine's Online type
  (`multi_player_game_type` 2 → `_net.mode` 1, a direct endpoint), and COMM
  INFO opens the old MODEM CONNECT panel (COM PORT, BAUD RATE, PHONE NUMBER,
  modem strings…), of which ONE box is live: the endpoint, typed into the
  CLEAR STRING box's place (x+0x7C, y+0x81). The modem path itself is gone
  (netcode.cpp:266-275, `docs/networking.md`). HD names the engine's meaning
  (ONLINE, ENDPOINT) and marks it.
- **This player's endpoint reads "ATZ"** — a modem init string, apparently
  what the player's MOX.SET holds where orion2re now keeps the Online
  endpoint (the source's default is "127.0.0.1:47800"). Parked for Data.
- The field lists, live: the setup lists N, M, H, ESC, S, L and J (Network,
  the default), + C under Online, − J under Hotseat; LOAD GAME without a
  multiplayer save opens the engine's message box ("No multi-player saved
  games found") — the HD message box since open fix 29; JOIN GAME in
  Network mode on this machine found no game (the list's Cancel only).

---


Read-only reading on 28 Sep 2026. Paths are relative to `/home/data/orion2re` unless they start with `orionlayerv3/`. Nothing was run, except a 6-byte header read of `MULTIGM.LBX` (261 entries).

## 0. Verdict in one paragraph

Multiplayer in orion2re is **real, working code**, not a stub. There are three connection types. **Hotseat** runs on one engine. **Network (LAN)** and **Online** both go through orion2re's own TCP "router" (`src/network/`, default port 47800). The router replaced DirectPlay, IPX, modem and serial. Modem, serial and IPX are gone: the legacy mode 2 logs "Unsupported legacy networking mode" and fails, and mode 3 fails silently (`src/game/netcode.cpp:266-275`). None of the multiplayer screens is drawn by OrionLayer. Screen ids 15, 16, 17, 21, 22, 37 and 41 have no entry in `orionlayerv3/core/screen_names.py:33-86`, so pressing Multiplayer in HD ends in the held-frame "F12 to answer" notice.

## 1. Entry: main menu

- The field is `Add_Hidden_Field_(0x19F,0xF0,0x237,0x104,"M",0x29)` (`src/game/mainmenu.cpp:138`).
- A click (or scan 0x4d) sets `_current_screen = SCREEN_MULTI_PLAYER`, `_return_screen = SCREEN_MAIN_MENU` (`mainmenu.cpp:508-512`).
- The dispatcher then calls `case SCREEN_MULTI_PLAYER: MULTPLAY::Multi_Player_Screen_()` (`src/game/mox2.cpp:108-111`).

Screen ids come from `src/game/orion2_consts.h:475-495`: MULTI_PLAYER=15, HOTSEAT=16, HOTSEAT_SELECT_PLAYER=17, START_NET=21, JOIN_NET=22, NET_NEXT_TURN=37, LOAD_NET=41. `NEW_GAME`=13 is reused as well.

## 2. The screens, one by one

### 2.1 Multi-player setup: `MULTPLAY::Multi_Player_Screen_` (`src/game/multplay.cpp:244-389`), screen 15. WORKING.

**Artwork** is all from `MULTIGM.LBX`, loaded in `Load_MP_Setup_Pictures_` (`multplay.cpp:206-231`):
- 0: full-screen background
- 1: setup panel
- 2: "Network" radio
- 3: "Online" radio
- 5: "Hotseat" radio
- 6: Cancel
- 7: Start Game
- 8: Load Game
- 9: Join Game
- 10: Setup

`Draw_MP_Setup_Screen_` (`:163-204`) sets each radio's frame from its `flag_*_disabled` value. Despite the name, that value means "selected" (see `Set_Multi_Player_Game_Type_`). A button whose field is `-1000` is drawn greyed (frame 2). The screen draws no text of its own.

**Fields** (`Add_MP_Setup_Screen_Fields_`, `:520-637`):

| Field | Kind and hotkey | Rect (screen-relative) | Where it leads |
|---|---|---|---|
| Network | hidden field "N" | (x+0x3B, y+0x5B) | `multi_player_game_type=1` (`:288-290`) |
| Online | hidden field "M" | (x+0x3B, y+0x7A) | `multi_player_game_type=2` (`:291-293`) |
| Hotseat | hidden field "H" | (x+0x3B, y+0x9B) | `multi_player_game_type=4` (`:294-296`) |
| Cancel | button, ESC | (x+0xB0, y+0x11E) | `SCREEN_MAIN_MENU` (`:297-300`) |
| Start Game | button "S" | (x+0x10D, y+0x5B) | `SCREEN_NEW_GAME`. For network or online it first fills a default `net_game_name` of "Moo II " plus a letter (`:343-362`). |
| Load Game | button "L" | (x+0x10D, y+0x7A) | Checks for multiplayer saves, then runs `Load_Multi_Player_Game_Screen_` under screen 41 (§2.6). Afterwards goes to screen 17 for hotseat or 41 for network (`:315-342`). |
| Join Game | button "J" | (x+0x10D, y+0x9B) | Absent while Hotseat is selected (`:608-619`). Leads to `SCREEN_JOIN_NET` (`:363-366`). |
| Setup | button "C" | (x+0x10D, y+0xBB) | Present only while Online is selected (`:622-634`). Opens the Online setup dialog (§2.2) in place (`:301-313`). |

`Set_Multi_Player_Game_Type_` (`:2201-2227`) maps the choice:
- type 2 or 3 → `_game_type=3`, `_net.mode=1` (Online, direct endpoint)
- type 4 → `_game_type=1` (Hotseat)
- anything else → `_game_type=2`, `_net.mode=0` (Network/LAN)

Type 3 is folded into 2 (`:2204-2205`). That makes the `multi_player_game_type == 3` branches dead code: the "Has your opponent pressed…" warning (HESTR 0x1c, `:239-242`, `:319`, `:345`) can never fire. It is a modem leftover.

On exit it saves settings (`FILEDEF::Save_Game_Settings_()`, `:388`). That means MOX.SET is written again (see the memory note on live runs).

### 2.2 Online setup dialog: `Online_Setup_Screen_` (`multplay.cpp:677-725`). No screen id; runs under 15. WORKING.

- **Artwork**: MULTIGM 0 (background), 32 (panel), 38/39 (accept off/on), 33 (Cancel), 34 (OK) (`Load_Online_Setup_Screen_`, `:656-675`).
- **One text field**: `Add_Continuous_String_Input_Field_` for `_net.online_settings.endpoint`, 30 characters, at (x+0x7C, y+0x81) (`:813-826`).
- **Default endpoint**: `"127.0.0.1:47800"` (`:233-237`, `:513-518`).
- **Cancel** restores a backup of `_net`. **OK** copies the settings to `MOX::_settings` and saves (`:699-724`).

### 2.3 New Game options: `NEWGAME::Newgame_Screen_`, screen 13. WORKING.

For `_game_type != 0`, `mox2.cpp:97-100` sets `_return_screen = SCREEN_MULTI_PLAYER`. Accept leads to `SCREEN_HOTSEAT` when `_game_type==1` and to `SCREEN_START_NET` when it is 2 or 3 (`src/game/newgame.cpp:97-106`). Cancel returns to 15 (`:92-95`).

### 2.4 Hotseat setup: `HOTPOP::Hotseat_Screen_` (`src/game/hotpop.cpp:74-192`), screen 16. WORKING.

- **Artwork**: MULTIGM 0 (background), 0x0B (panel), 0x0C (Join), 0x0D (Accept), 0x0E (Cancel) (`:32-38`).
- **Drawing**: prints the numbers 1 to `number_of_players`, joined humans in active colours, at (bg+14, bg+70) with a 9 px step (`:196-231`).
- **Fields** (`:40-72`):
  - Join, at (+125, +99), absent once all slots are human
  - Accept, at (+125, +136)
  - Cancel, at (+140, +200), ESC
- **Join** runs `RACESEL::Race_Selection_Screen_(temp_player)` (reported as 51 on the wire), copies the result into the next `_player[]` slot and sets objectives 100 (`:159-169`).
- **The first player is joined automatically**, because input is forced to Join while there are 0 humans (`:105-107`).
- **Accept with 1 human** asks HESTR 162 and on yes falls back to a single-player game (`_game_type=0`, `:114-123`). With more humans it asks the formatted HESTR 163/164/165 (`:124-146`).
- **Exit**: builds the game with `INITGAME::Init_New_Game_` and goes to screen 17 (`:172-186`). Cancel, or backing out of the first race pick, goes to 15.

### 2.5 Hotseat player switch: `MULTPLAY::Hotseat_Select_Player_` (`multplay.cpp:391-480`), screen 17. WORKING.

- **Artwork**: MULTIGM 0x13/0x14/0x15 with player banners (`Hotseat_Load_Next_Player_`, `:2124-2167`).
- **Fields**: one hidden field plus a banner field per human who still has to play (`:2169-2199`).
- **Clicking a player** sets `_PLAYER_NUM`, restores that player's map view (`Restore_Hotseat_Map_Info_`) and goes to `SCREEN_REPORTS` with `_return_screen=17` (`:458-470`).
- **When all have played**, it goes to `SCREEN_MAIN_NEXT_TURN` (`:471-474`).
- **Turn flow**: the galaxy map's turn end routes back to 17 for hotseat (`src/game/mainscr.cpp:2690`), and loading a hotseat save lands here too (`mainmenu.cpp:474`, `loadsave.cpp:368`, `:1640`).
- **Per-player state**: map scale, fleet box and system box are kept per player in `MAINSCR::_hotseat_*` (`src/game/mainscr.h:48-55`, `src/game/haccess.cpp:745-787`).

### 2.6 Load multiplayer game: `Load_Multi_Player_Game_Screen_` (`multplay.cpp:727-811`). Runs under 41, which is set at `:326` before the call. WORKING.

- **Pre-check**: `Get_Valid_MP_Save_Games_` accepts only saves of type 1 to 3. If there are none it shows HESTR 0xF4 "no multiplayer saved games" (`:482-511`).
- **Artwork**: MULTIGM 0, then a header chosen by `_game_type`: 0xFF (hotseat), 0x12 (network) or 0xFE (online). Cancel is entry 0x101 (`:828-861`). All of these fit the file's 261 entries.
- **Fields**: 10 slot fields plus Cancel (`Add_Load_MP_Game_Screen_Fields_`, `:873-910`).
- **Invalid slot**: HESTR 0xFD warning (`:782-787`).
- **Loading**: `FILEDEF::Load_Game_` and reset of every `network_player_id` to -1 (`:769-781`).
- **Network or online loads** first run `Change_MP_Game_Name_` (`:912-967`, game-name editing).

### 2.7 Host a network or online game: `NETSTART::Start_Net_Screen_` (`src/game/netstart.cpp:258-510`), screen 21. WORKING.

Sequence:
1. "Initializing" animation, MULTIGM 25 (`multplay.cpp:153-156`, `:1345-1367`).
2. `netcode::Do_Net_Init_(mode)` (`netstart.cpp:269`). In LAN mode this **starts an embedded router thread** bound to `0.0.0.0:47800` TCP, with UDP discovery on 47800 (`src/game/netcode_bootstrap.cpp:7-15`, `src/game/netadapter.cpp:141-189`, `:229-234`). In Online mode it connects to the endpoint.
3. `Russ_Net_Create_Game_` (`:277-285`).
4. **Waiting for joiners**: MULTIGM 15 animation plus a "Begin" button (MULTIGM 16, "S", `multplay.cpp:1916-1933`). It prints "%d player(s)" (HESTR 0xF9/0xFA, `:2000-2036`). The loop ends on the button, or when users ≥ `number_of_players`. With a single user it asks `_really_start_with_only_1_msg` first (`netstart.cpp:298-320`).
5. Player assignment, then a `NET_PACKET_START_GAME` broadcast with the game settings and build date (`:325-374`).
6. The host picks its race (`Race_Selection_Screen_`, `:392`).
7. "Wait for race info", MULTIGM 0x18 (`multplay.cpp:2057-2061`), until every joiner has sent `PLAYER_SETUP` (`netstart.cpp:403-423`).
8. `Init_New_Game_`, random colours for unassigned players, "Sending data" MULTIGM 26, `Broadcast_Game_Data_Differential_(1)`, then return 1.

The dispatcher then sets `SCREEN_REPORTS` (`mox2.cpp:128-133`). Every failure path shows `_comm_failure_string` and returns to 15.

### 2.8 Join a network or online game: `NETSTART::Join_Net_Screen_` (`netstart.cpp:171-256`), screen 22. WORKING.

1. `Do_Net_Init_`. In LAN mode this is `BOOTSTRAP_LAN_DISCOVERY`: a UDP probe broadcast to `255.255.255.255:47800` (`src/network/router_session_browser.cpp:326-343`).
2. **Game list**, `MULTPLAY::Choose_Multi_Network_Game_Screen_` (`multplay.cpp:1216-1286`), still screen 22:
   - Artwork: MULTIGM 0 and 0x29 (list panel); Cancel is 0x101.
   - Up to 10 hidden row fields, 27 px apart, at (x+38, y+64)-(x+400, y+86), plus Cancel (`:1432-1473`).
   - The list refreshes every 5 s (`:1433-1437`).
   - Picking a row sets `cur_session_id`. Cancel sets `SCREEN_MULTI_PLAYER`.
3. `Net_Join_Game_`. A full game shows `_game_full_string` (`netstart.cpp:199-206`).
4. "Joined, waiting" animation, MULTIGM 0x17 (`multplay.cpp:158-161`), until the host moves the sync state on (`netstart.cpp:222-226`). No free slot shows `_no_more_player_slots_error`.
5. Next step depends on the sync state:
   - **New game**: `Net_Select_Race_` (`:29-70`). Race selection, then "Generating map" MULTIGM 30 while waiting for the host's game data.
   - **Loaded game**: `Net_Pick_Position_` (`:72-137`), which uses `Choose_Network_Plyrs_Screen_` (`multplay.cpp:1503-1593`: MULTIGM 0x1b/0x1c/0x1d banner list, Begin 16, Cancel 0x101), then "Getting data" MULTIGM 0x1F.

### 2.9 Host a loaded network game: `NETSTART::Load_Net_Screen_` (`netstart.cpp:543-749`), screen 41. WORKING.

Same shape as 2.7 in `LOAD_GAME_HOST_SETUP` state, which also uses an embedded router in LAN mode (`netcode_bootstrap.cpp:8-10`). The host assigns saved empires to joiners through `Choose_Network_Plyrs_Screen_` (`netstart.cpp:590`). Note that the dispatcher sets `_previous_screen = SCREEN_JOIN_NET` after it (`mox2.cpp:192-197`), which looks like a copy slip.

### 2.10 In-game: net next turn, screen 37, `NETTURN::Net_Next_Turn_` (`src/game/netturn.cpp:21`). WORKING.

- Waiting-for-other-players screen with **chat**. `Add_Net_Next_Turn_Fields_` (`multplay.cpp:1138-1183`) adds a continuous string input for chat plus a full-screen "C" field.
- `Chat_Box_Input_Loop_` (`:119-150`) sends through `CHAT::Send_Chat_Msg_` (`src/game/chat.cpp:23`, `NET_PACKET_CHAT`).
- Chat is also used while waiting on combat (`src/game/combfind.cpp:390`, `:1513`, `:2109`).
- **Network diplomacy and tactical combat** have full packet paths: `dip_scrn.cpp` `DIP_NET_PACKET_MESSAGE` (e.g. `:185`, `:2121`); `combinit.cpp:1029`, `cmbtmov1.cpp:177`, `combfind.cpp:434-476`.

### 2.11 What is a stub or missing

- **Pre-game lobby chat is missing.** `_allow_chat_mode` is set to 0 or 1 by every net info screen (`multplay.cpp:154`, `:159`, `:1289`, `:1294`, `:1918`, `:1992`, `:2059`), but nothing reads it (grep: only the declarations at `multplay.cpp:36` and `multplay.h:124`). The waiting screens have no chat field. Chat exists only in-game (§2.10).
- **Modem, serial and IPX are removed.** `netcode.cpp:266-275` (quoted in §0). This was a design decision: `docs/networking.md:7-17` says "remove dependency on DirectPlay…", "remove legacy modem, null-modem, and serial-cable assumptions", and "support both LAN and online play through one core networking stack".
- **Leftovers:**
  - The type-3 warning is dead (§2.1).
  - The strings `_dialing_failed_error` and `_answering_failed_error` are loaded but never used for anything live (`netstart.cpp:4-10`, `:139-169`).
  - `NETSTRAT` holds only `_comm_failure_string` (`src/game/netstrat.cpp`).
  - `netproto.cpp` is a 2-line include.
- **No reconnect.** A dropped player becomes AI (`docs/networking.md:66-80`).
- **Open router work** in `plan.md:34-38`: handshake, idle and request timeouts, all unchecked.
- **Sync-safety gaps** are documented in `docs/deterministic-net.md`: a single `network_data_ptr` mailbox (`:327`), non-transactional dropout handling (`:219`), and no terminal state on session loss (`:355`).
- `notes.md`, `todo.md`, `README.md` and `files.md` say nothing about multiplayer, apart from `README.md:60-67` (building a router-only `orion2re-router`, `CMakeLists.txt:448`) and generic test and compatibility items (`todo.md:46-47`).

## 3. Hotseat, two local engines, a second machine

**Hotseat** is fully possible on one engine with no network at all (§2.4, §2.5, `_game_type=1`).

**Two local engines** can connect to each other in principle. Protocol:
- TCP to a router at port 47800 (`src/game/netadapter.h:45-46`, `src/network/router_service.h:11`)
- Framed packets (`src/network/router_protocol.*`) with LZ4 compression (`CMakeLists.txt:183`)
- Session list, create and join. The router is packet-opaque (`docs/networking.md:76`).

The adapter's unit test does exactly this on 127.0.0.1: a host and a guest create and join one session and exchange packets (`tests/unit/test_netadapter.cpp:135-193`).

Practical routes on one machine:
- **(a)** Engine A hosts in **Network** mode, which starts the embedded router on `0.0.0.0:47800`. Engine B joins in **Online** mode with the endpoint `127.0.0.1:47800` (a direct TCP connect, which certainly reaches it).
  - B in **Network** mode would instead depend on the UDP broadcast to `255.255.255.255:47800` looping back to the same host. That is likely on Linux but **not verified**.
- **(b)** Run a standalone `orion2re-router` on 127.0.0.1:47800 and use **Online** mode on both. An Online host does *not* start a router (`netcode_bootstrap.cpp:15`, `DIRECT_ENDPOINT`).

Constraints:
- **Only one host per machine**, because the embedded router binds the fixed port 47800 (`netadapter.cpp:151`).
- **The ext server port is fixed at 17362** (`src/ext/ext_api.h:12`; `mox2.cpp:382` calls `ext::Init()` with no argument). A second engine on the same machine cannot bind it, so **only one of the two engines can be on OrionLayer's wire**. What happens after the bind fails was not traced.
- **Both engines share the working directory** unless each is started from its own copy. `MOX.SET` and `SAVE*.GAM` are rewritten, e.g. `multplay.cpp:388` and `:718-723`.
- Starting a second engine must obey "never connect to Data's engine": run both from a session-started scratch directory.

**A second machine is needed only for real two-person play**, or to test LAN discovery across a real subnet. Nothing in the code requires it, and the protocol runs over loopback.

## 4. OrionLayer's wire and HD today

**Screen ids on the wire.** `ext::Tick(MOX::_current_screen)` is called from `fields::Get_Input_` (`src/game/fields.cpp:167`) and the main loop (`mox2.cpp:41`). The reported id is overridden only by `ext::ScreenOverride`, which is used in `tech.cpp:143`, `science.cpp:124`, `desbox.cpp` and `dip_scrn_main.cpp`, and **never in any multiplayer file** (grep). Race selection writes 51 into `_current_screen` itself (`src/game/racesel.cpp:229-231`). So the wire shows:

| On the wire | What is open |
|---|---|
| 15 | MP setup (§2.1) **and** the Online setup dialog (§2.2). They can be told apart only by the field list (§2.2 has 3 fields: endpoint input, Cancel, OK). |
| 13 | New Game options |
| 16 | Hotseat setup; 51 while a hotseat player picks a race |
| 17 | Hotseat player switch |
| 21 | Every host step: initializing, waiting for joiners, wait for race info, sending. 51 during the host's race pick. |
| 22 | Every join step, including the game list and the pick-position list |
| 41 | Both the load-MP slot list (§2.6) and hosting a loaded game (§2.9) |
| 37 | Net next turn |

**`FIELD_LIST`** (`SerializeFields`, `src/ext/ext_api.cpp:875-890`) sends each field's index, rect, type and hotkey. The MP setup fields carry hotkeys N, M, H, S, L, J, C and ESC, so which buttons exist (Join missing under Hotseat, Setup only under Online) shows which type is selected.

**Nothing multiplayer-specific is serialized:** not the selected type flags, the endpoint string, the session names or player counts, the human count, the hotseat banners, or chat text. The save-slot message is sent only for screen 8 and the main-menu Load (`ext_api.cpp:909-916`), not for 41's slot list.

**OrionLayer's main menu today.**
- `orionlayerv3/screens/main_menu/boxes.json:106-137` and `:341-372` (two layouts) define a "Multiplayer" button box with a fixed `field_id: 4`.
- `ScreenBase.handle_click` sends `activate_field(box.field_id)` as-is (`orionlayerv3/core/screen_base.py:250-254`), and `main_menu/screen.py` has no handler of its own for it.
- The engine then switches to 15. No screen claims 15 (it is not in `screen_names.py`), so the dispatcher sets `use_original` (`orionlayerv3/core/dispatcher.py:237-244`). Under Data's F12 rule, `never_without_f12` holds the last HD frame with the "F12 to answer" notice (`orionlayerv3/core/handover.py:152-174`).
- **In HD the Multiplayer button therefore leads to a held frame and notice. Every multiplayer step is playable only through F12.**

**Side finding (not verified live).** Field numbers start at 1 (`Clear_Fields_` sets `_fields_count = 1`, `src/game/fields.cpp:206-207`). The main menu adds Continue only if `save10.gam` exists for game type 0 or 1, and Load only if any `save?.gam` exists (`mainmenu.cpp:117-135`).
- `field_id 4` is Multiplayer only when both exist, as in the list at `orionlayerv3/doc/ext_api_dokumentation_v3.md:696-701`.
- Without Continue, 4 is Hall of Fame. With neither, 4 is **Quit**.
- The static ids for continue (1) through quit (6) break the same way, against livefields' rule "nothing may remember an index" (`orionlayerv3/core/livefields.py:3-6`).
- It is worth checking whether something else hides those boxes. Nothing in `main_menu/screen.py` does.
