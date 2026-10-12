> **Not ready to use yet.** OrionLayer is under heavy development. It is
> not ready to play or to rely on yet, and none of its screens has been
> accepted.

# OrionLayer v3

An HD frontend for **Master of Orion 2**, built on
[orion2re](https://github.com/orion2re/orion2re) — the C++
reimplementation of the original engine by Joes and the orion2re team
(GPL-3.0-or-later). OrionLayer needs orion2re with its Extension API,
which is the fork [Data-crea/orion2re](https://github.com/Data-crea/orion2re)
(branch `orionlayer`).

orion2re runs the game; OrionLayer replaces its 640x480 interface with
high-resolution pygame screens. The two talk over a local TCP
Extension API on `localhost:17362`: OrionLayer receives game state
snapshots and sends the player's input. A screen that has no HD version
yet holds its last HD picture with the notice "F12 to answer"; F12
shows the original's picture, so the game is always playable.

**You need your own copy of Master of Orion 2.** OrionLayer is a
modification, not a game: it replaces the interface and nothing else.
The game's own texts and pictures that OrionLayer shows are not included
— they are read from your own installation. OrionLayer's own pictures
come as a separate download, the base pack (Creative Commons Attribution
4.0, its `LICENSE.txt`). See [LICENSE](LICENSE) for what the MIT licence
of this code covers and what it does not, and [Credits](#credits).

## Getting started

These are the steps, on Linux, from nothing to a game on the galaxy map.
They were run exactly like this in an empty folder (work order 243). On
Windows the steps are the same; the engine's build command is in the
fork's README, and OrionLayer itself has not been tried there yet.

You need Master of Orion 2 (GOG or Steam), Python 3.10 or newer, git,
CMake and Ninja, and a C++ compiler (Debian/Ubuntu: `sudo apt install
build-essential cmake ninja-build git python3-venv`). Below, the game is in
`~/Master of Orion 2`; use your own folder.

**1. Build the engine.** This puts the engine and its own data into your
game folder:

```sh
git clone --recurse-submodules --branch orionlayer https://github.com/Data-crea/orion2re.git
cd orion2re
cmake --preset linux-release -DORION2RE_EXT=ON -DORION2RE_GAME_DIR="$HOME/Master of Orion 2"
cmake --build --preset linux-release
cd ..
```

**2. Get OrionLayer and what it needs:**

```sh
git clone https://github.com/Data-crea/orionlayerv3.git
cd orionlayerv3
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

**3. Set it up.** This tells OrionLayer where the engine and the game are,
downloads OrionLayer's pictures (the base pack, checked file by file) and
reads the texts and pictures it needs from your own game:

```sh
.venv/bin/python tools/setup.py --engine "$HOME/Master of Orion 2/orion2re" --game "$HOME/Master of Orion 2" --extract
```

**4. Play:**

```sh
.venv/bin/python play.py
```

Choose LOAD GAME or NEW GAME as in the original. Your saves are the game's
own (`SAVE1.GAM` … in the game folder). This engine writes saves in its
own format (version 7), which orion2re builds before 2.0 cannot read; it
reads the older saves.

## Requirements

- **Master of Orion 2**, your own installation, anywhere (see *Where your
  game and engine are* below).
- **Python 3.10 or newer** (verified on 3.12 and 3.14) with pygame, numpy,
  Pillow and scipy — `requirements.txt`.
- **`xdotool`**, so the start can skip the original's intro (without it
  the intro plays).
- **orion2re, patched for OrionLayer** — see the next section.

## The orion2re build it needs

<!-- orion2re-patches -->
OrionLayer talks to orion2re built from the fork
[`Data-crea/orion2re`](https://github.com/Data-crea/orion2re), branch
**`orionlayer`**, with `-DORION2RE_EXT=ON`: orion2re v2.0.0 (public,
GPL-3.0-or-later) plus the Extension API and the fixes below, one commit
each (work order 243; how to build it is in the fork's README). `python
tools/version_check.py [path/to/orion2re]` checks a built tree against this
list. The list's one home is `LOCAL_PATCHES` in `tools/version_check.py`.

Each row names both commits: the fix as it was first made on
`orionlayer-local` (orion2re 1.60, a private base, frozen) with its patch
file under `doc/`, and its port on the v2 branch, whose own patch file is
`doc/v2/` (written by `dev:tools/v2_patches.py`). The
Extension API's protocol is the fork's `docs/extension-api.md`.

| # | 1.60 commit | v2 commit | fix | patch |
|---|---|---|---|---|
| 1 | `a111355d` | `8dce5c84` | the Extension API itself (`src/ext` and its hooks), with the `src/ext` parts of open fixes 1, 2, 3, 12, 14, 20, 21 | `doc/ext_save_slots.patch`, `doc/ext_fleet_selection.patch`, `doc/ext_fleet_select_ship.patch` |
| 2 | `191aaa78` | `74b06b98` | open fix 3: an injected click keeps its pointer | `doc/ext_inject_click.patch` |
| 3 | `6598052c` | `b2fa0c79` | open fix 5: Select Race records `_old_race` (patch file since work order 192) | `doc/ext_select_race_old_race.patch` |
| 4 | `e099d3fc`, `3305d78c` | `3fea2fb1`, `77b1fb07` | screen ids for Select Race and Custom Race; open fix 22 | `doc/ext_screen_id.patch` |
| 5 | `7067c366` | `1982b2a1` | open fix 12: the pop-move command, its engine half | `doc/ext_move_pop.patch` |
| 6 | `f838c754` | `62cc8968` | open fix 24: the research dialogs' own ids | `doc/ext_research_screens.patch` |
| 7 | `e9d07528` | `a7852545` | open fix 25: the activated research row is the one chosen | `doc/ext_tech_activate.patch` |
| 8 | `cc5ec133`, `e6199966` | `0aae309f`, `39bfe4fb` | open fixes 27, 28: the fleet screen's state, one ship | `doc/ext_fleet_screen_state.patch`, `doc/ext_fleet_screen_select.patch` |
| 9 | `f98b8547` | `007b4aa3` | open fix 31: present without VSync on request | `doc/ext_present_no_vsync.patch` |
| 10 | `cc542e02` | `fa61b768` | open fix 30: the Leaders screen's state | `doc/ext_officer_screen_state.patch` |
| 11 | `2269749c` | `aa59219a` | open fix 32: the Info screen's history and turn messages | `doc/ext_info_screen_state.patch` |
| 12 | `9ab84230` | `59425f3c` | open fix 34: the main menu's Load dialog sends its save slots | `doc/ext_main_menu_save_slots.patch` |
| 13 | `c5d4dacd`, `01bafd9c`, `a10e20ba`, `8a6acc08`, `2be953d4`, `2097b0c6` | `f8c859b4`, `45aba360`, `1a3a449a`, `9759f1e0`, `67d3c9fe`, `380daf98` | **open fixes 35-40, one commit each, in this order: which colony the colony screen and the build popup show (35), where its buildings stand (36), Plague and Pop Boom (37), the product's cost and turns (38), the build popup's queue under edit (39), its two lists and queue with their numbers (40)** (work order 181) | `doc/ext_colony_screen_colony.patch`, `doc/ext_colony_building_placement.patch`, `doc/ext_colony_status_word.patch`, `doc/ext_colony_product_cost.patch`, `doc/ext_build_popup_queue.patch`, `doc/ext_build_popup_lists.patch` |
| 14 | `4bf152e4` | `385d678a` | open fix 41: the engine's own window hidden from the start, and a hidden window presents without VSync (work order 183) | `doc/ext_engine_window_hidden.patch` |
| 15 | `70d31b10`, `4af9fefa`, `8aea1a25`, `ba9b6bc6`, `230a0638` | `1e608dfb`, `1b39a01f`, `6800ee70`, `2bbc0174`, `1780203a` | **open fixes 44, 45, 46, 47 and 43, one commit each, in this order: the Ship Designer's design as it is edited (44), its three pickers and what they offer (45), the diplomacy audience's own ids (46) and its state (47), and the engine's window hidden only when the starter asks and shown again on request (43, amends 41)** (work order 186) | `doc/ext_ship_designer_state.patch`, `doc/ext_ship_designer_boxes.patch`, `doc/ext_audience_screen.patch`, `doc/ext_audience_state.patch`, `doc/ext_engine_window_on_request.patch` |
| 16 | `010870bc` | `adc21aed` | open fix 48: the move verdict for the fleet box's selection at every star, for the travel line on hover (work order 188) | `doc/ext_fleet_move_verdict.patch` |
| 17 | `76f8c438` | `707bcd96` | open fix 29: the generic message box's kind, title, text and answers, for the HD message box (work order 188) | `doc/ext_message_box_text.patch` |
| 18 | `6859e163` | `7fbe221f` | open fix 49: the turn-time popups under their own ids (59-64; 40 kept for the Turn Summary) and what they show, for the HD turn popups (work order 188) | `doc/ext_turn_popups.patch` |
| 19 | `65b41b66` | `b1b25b88` | open fix 50: the Hall of Fame's entries, and 14 on both ways in (work order 188) | `doc/ext_hall_of_fame.patch` |
| 20 | `8f7bd9e3` | `e2a10520` | open fix 51: which multiplayer step is up and what it shows (work order 188) | `doc/ext_multiplayer_state.patch` |
| 21 | `96da4c4d` | `02fa6bff` | open fix 42: the extension ticks during a screen's input delay, so the research panel's list arrives ~550 ms sooner (work order 191) | `doc/ext_input_delay_tick.patch` |
| 22 | `ab3f6892` | `0b15e0b6` | open fix 61: a right click at a point (MSG_INJECT_RIGHT_CLICK), so the F12 view can turn a ship on the battle map (work order 194) | `doc/ext_inject_right_click.patch` |
| 23 | `2495e1cf` | `ca441bf9` | open fix 52: a tactical battle reports 65 (its scan view 66, its board popup 67), and the gate the combat blocks are written under (work order 194) | `doc/ext_combat_screen_id.patch` |
| 24 | `9b7dcba0` | `80484481` | open fix 53: the tactical battle's state — units field by field, the turn order, the view origin, the legal moves ("CMBT") (work order 194) | `doc/ext_combat_state.patch` |
| 25 | `f506bc6c` | `7190eb2d` | open fix 55: the ordnance in flight — missiles, torpedoes, fighters with their targets ("CMSL") (work order 194) | `doc/ext_combat_ordnance.patch` |
| 26 | `f1e6c581` | `9dc9601c` | open fix 57: how the last battle ended — winner, sides, each unit's fate — kept until the next battle ("CRES") (work order 194) | `doc/ext_combat_result.patch` |
| 27 | `750434ef` | `31f0aed4` | open fix 54: what each weapon slot of the acting unit can hit now, the engine's own verdict ("CTGT") (work order 194) | `doc/ext_combat_targets.patch` |
| 28 | `6f87c151` | `9b7f61a4` | open fix 59: the galaxy map fleet box's scroll row, so HD can show a stack past nine ships ("FBSC", work order 191's item 1) (work order 194) | `doc/ext_fleet_box_scroll.patch` |
| 29 | `5bd4c404` | `774f8267` | open fix 56: the battle's events, numbered, with their outcome — shots, moves, turns, launches, hits, deaths, retreats, boarding ("CMEV") (work order 194) | `doc/ext_combat_events.patch` |
| 30 | `e4b2256a` | `feeec356` | open fix 58: one command per battle action — move, fire, fire at a missile, face, select, release stasis, board — so HD plays a battle without clicks (MSG_COMBAT_COMMAND) (work order 194) | `doc/ext_combat_commands.patch` |
| 31 | `6f69de27` | `4417efd2` | open fix 62: an activation is checked against the field the client saw, so a list that ended in between cannot hand its index to the next — SELECT NEW RESEARCH no longer commits a row by itself (open fix 26) (work order 197) | `doc/ext_activate_checked.patch` |
| 32 | `ee844b0b` | `adfd7bb0` | open fix 63: the battle's event stream reports a missile merge and a missile gone only for a live missile — the original's merge loop goes on over empty slots (work order 197) | `doc/ext_combat_events_merge.patch` |
| 33 | `76c7b880` | `0d2edae6` | open fix 65: a battle command keeps the original's view round its action, as a click does — the view centred, a move longer than the view refused, a missile outside it given its field — so no command draws outside the frame buffer (work order 197) | `doc/ext_combat_command_view.patch` |
| 34 | `9e19c9f3` | `7a561725` | open fix 64: MSG_SET_SPIES — the Races screen's spies and missions set as one list through the game's own icon groups and setters, all or nothing (work order 197) | `doc/ext_set_spies.patch` |
| 35 | `121950ed` | `55362111` | open fix 66: CPOP — the battle's scan view and board popup on the wire: the scanned unit, the popup's message, range and chosen marines, read only (work order 199) | `doc/ext_combat_popup.patch` |
| 36 | `a8381e60` | `998d17e3` | open fix 67: MSGB version 2 — the values a message box's text prints through FMTPARA item codes (the boarding result), read only (work order 199) | `doc/ext_msgbox_items.patch` |
| 37 | `095ebac4` | `f0acb73d` | open fix 68: COPT — the battle's OPTIONS panel on the wire: whether it is up, and its five option flags as the battle holds them, read only (work order 200) | `doc/ext_combat_options.patch` |
| 38 | `f031cbad` | `ebdf5e69` | open fix 69: HLPL — the help list a right click is checked against on the wire: its ids and rectangles in its own order, read only (work order 200) | `doc/ext_help_list.patch` |
| 39 | `a8b5640b` | `624081b7` | open fix 70: the player's language — `ORION2RE_LANGUAGE` where the build forced 0, and `ORION2RE_LANGUAGE_DIR`, another install read for the language's files (its own files first, `ORION2RE_LANGUAGE_FILES`; read only; work order 200) | `doc/ext_language.patch` |
| 40 | `e75477c5` | `3a015989` | open fix 74: the Energy Absorber's discharge as a battle event — the beam shot it is drawn as (weapon 0x2E, no slot, its damage), before the target's death ("CMEV"; work order 210) | `doc/ext_combat_absorber.patch` |
| 41 | `2b773c31` | `6f76077b` | open fix 79: the battle's sounds as events — each sound, fade, loop and pitch bend recorded with the ticks since the event before ("CMEV"), and none played by the engine while a client draws the battle, so OrionLayer plays them with its own picture (work order 212) | `doc/ext_combat_sound.patch` |
| 42 | `89494e72` | `670bd95c` | open fix 71: the hidden engine's animation waits — skipped while a client draws the battle (not a timed message box's, not the input loop's), so an animated action reaches OrionLayer at once (work order 212) | `doc/ext_combat_waits.patch` |
| 43 | `003af991` | `91501ca3` | open fix 77: a fighter pass's beam and group as a battle event — the owner's fighter beam, the group's place, facing and quantity, the target point ("CMEV"; work order 212) | `doc/ext_combat_fighter_beam.patch` |
| 44 | `3a076921` | `36f080e7` | open fix 71, amended: a battle command taken leaves no input poll behind, so the first wait of its action is skipped too (work order 212) | `doc/ext_combat_waits_command.patch` |
| 45 | `65e48358` | `5a97facc` | open fix 82: a beam's aim as a battle event — each entry's last fire point and its target point with the miss offset, so a shot is drawn between the original's own points and runs its frames ("CMEV"; work order 213) | `doc/ext_combat_beam_aim.patch` |
| 46 | `910e1401` | `3d3c74b6` | open fix 83: the gyro destabilizer's spin as a battle event — the turns the engine drew for the target's spin ("CMEV"; work order 213) | `doc/ext_combat_gyro_spin.patch` |
| 47 | `8b1501f5` | `e9b3cf07` | open fix 84: the field list is sent when its content changes, not only its count — a view replaced by another of the same field count under one screen id (the race report's RETURN to Races) reaches OrionLayer (work order 223) | `doc/ext_field_list_content.patch` |
| 48 | `bdc3009b` | `b73185d2` | open fix 85: RFIT — the refit ship list's first row on the wire, with the list's length, while the build popup's id is up, read only; OrionLayer re-establishes the list's page from it instead of counting (work order 226) | `doc/ext_refit_first_ship.patch` |
| 49 | `4642eb1e` | `e7e823c8` | open fix 86: FBTN — the fleet box's order buttons on the wire: ALL, Outpost, Colonize, Engage, Transport and Attack, each with whether the box offers it and its field, and the stack's star with its ignore-enemies bit, read only; OrionLayer's fleet box offers the orders from it (work order 229) | `doc/ext_fleet_box_buttons.patch` |
| 50 | `34a1d873` | `b5692057` | open fix 87: INBX — the game's name box on the wire: its prompt, the name it opened with, the typed text, its fields, read only; OrionLayer draws "Enter Star Name" after a star's first colony from it instead of the F12 notice (work order 230) | `doc/ext_name_box.patch` |
| 51 | `6c431570` | `e3ae40c8` | open fix 88: TXTF — the text fields on the wire: per continuous input field its buffer and, while edited, the typed text, read only; OrionLayer shows and reads back a typed name (Custom Race's race name) from it (work order 230) | `doc/ext_text_fields.patch` |
| 52 | `0ff8f875` | `dd384efa` | open fix 89: MSG_INJECT_RAW_KEY — a key code as the engine translates F1-F10, Alt+F1-F10 and Alt+letter, nothing else; OrionLayer passes the original's F and Alt keys with it (work order 230) | `doc/ext_raw_key.patch` |
| 53 | `48718673` | `41c73182` | open fix 90: SYSW — the star system window on the wire: its star, whether it shows the system, and the fleet bar's slots (field and ship node per owner), read only; OrionLayer draws the map window's fleet bar from it and names a window the engine opened (work order 231) | `doc/ext_system_window.patch` |
| 54 | `bbbc546c` | `adbb683c` | open fix 91: the invasion on the wire — TPOP kinds 10 (the invasion choice and the bombing: its numbers, both sides' counts, its fields, the bombing's explosions) and 11 (the ground combat: both sides' troops and summary lines, and every unit, beam and explosion as its own drawing code drew them), read only; OrionLayer draws the choice, the bombing and the ground combat from it instead of the F12 notice (work order 232) | `doc/ext_invasion.patch` |
| 55 | `90a930f9` | `096c97fb` | open fix 92: MSG_SETTLE_POPS — colonists of the colony screen's colony to another colony at the same star, the engine's own `Pop_Tries_To_Settle_` and `Settle_Pop_` for each, all or nothing; OrionLayer drops the colonists carried on the pointer onto a planet of the system display with it (work order 233) | `doc/ext_settle_pops.patch` |
| 56 | — | `e3d81221` | open fix 93: the LAYOUT message — every member of the records the snapshot sends raw, by name, offset and size (decision 97) | `doc/ext_layout_table.patch` |

## Install

```bash
git clone https://github.com/Data-crea/orionlayerv3.git
cd orionlayerv3
pip install -r requirements.txt
python tools/setup.py --extract
```

**The pictures are not in this repository.** OrionLayer's own pictures
(backgrounds, banners, stars, nebulae, the new-game and race pictures, …)
come as one zip, the *base pack* (Creative Commons Attribution 4.0, its
`LICENSE.txt`), a release of this repository named after `basepack.json`
(`base-pack-<12 characters of its sha256>`). `setup.py` downloads the one
this checkout names and installs it into its own folder
(`~/.local/share/orionlayer/base` on Linux, `%LOCALAPPDATA%\OrionLayer\base`
on Windows, `ORIONLAYER_BASE_DIR` for another place), checking every file
against `basepack.json`; `python tools/basepack.py install <zip>` does the
same with a zip you have. Without it `setup.py`, `main.py` and `play.py`
say where they looked and start nothing. Pictures made from your own Master of Orion 2 are never in
the pack: `setup.py` and the extractors below make them on your machine.

On Arch and other PEP 668 distributions `pip install` into the system
environment is refused by design; use the system packages or a venv:

```bash
sudo pacman -S python-pygame python-numpy python-pillow python-scipy   # Arch
python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

`setup.py` rebuilds the artwork the repository does not carry (ship and
sidebar icons, the black hole, the HUD pieces, …) and reports what is
still missing from your own Master of Orion 2 installation. Those files
are read by the extractors below, and `python tools/setup.py --extract`
runs every one that has not run — none is required to start, but
without them the matching screen says so instead of showing the game's
text or picture (a right click, for one, names the command instead of
opening the game's help):

```bash
python tools/help_extract.py                        # right-click help texts
python tools/nebula_extract.py "$HOME/Master of Orion 2/STARBG.LBX"
python tools/techname_extract.py                    # building, ship-part and research names
python tools/billtext_extract.py                    # research panel wording
python tools/estrings_extract.py                    # option strings
python tools/hestrings_extract.py                   # message strings
python tools/maintext_extract.py                    # system special texts
python tools/kentext_extract.py                     # weapon firing-arc words
python tools/raceicon_extract.py                    # population figures
python tools/infotext_extract.py                    # Info screen texts
python tools/skildesc_extract.py                    # officer skill help texts
python tools/racestuf_extract.py                    # Select Race's race traits
python tools/techdesc_extract.py                    # ship design descriptions
python tools/fleet_art_extract.py                   # Fleets ship pictures
python tools/officer_art_extract.py                 # Leaders screen artwork
python tools/races_art_extract.py                   # Races screen artwork
python tools/colony_art_extract.py                  # colony screen pictures
python tools/invasion_art_extract.py                # invasion and ground combat pictures
python tools/design_art_extract.py                  # Ship Designer artwork
python tools/audience_art_extract.py                # audience artwork
```

`python tools/setup.py --check` lists what is present and what is not, and
changes nothing.

**Where your game and engine are — the two things you set.** OrionLayer
needs the folder of your Master of Orion 2 and the orion2re program built
for it. Tell it once; both are saved in your OrionLayer settings:

```bash
python play.py --engine /path/to/orion2re --game "/path/to/Master of Orion 2"
```

Or set `ORIONLAYER_ENGINE` and `ORIONLAYER_GAME_DIR` in the environment.
Without either, OrionLayer looks in `~/orion2re/out/build/Linux/linux-debug/orion2re`
and `~/Master of Orion 2`. When one is missing or wrong, `play.py` says
which and how to set it, and starts nothing. The extractors above read the
same game folder.

**German.** Game Settings → LANGUAGE → Deutsch, then restart. OrionLayer's
own words are German at once. The game's words need the German files of a
German MOO2 (`GER_HELP.LBX`, `HGSTRNGS.LBX`, `ESTRGERM.LBX`, `FONTSG.LBX`,
…): in the game's own folder, or — when that is an English install — in
another folder you name once:

```bash
python tools/language_files.py "/path/to/a German Master of Orion 2"
```

It checks the folder, records it, and extracts the German texts; the
folder is only read. The game itself then speaks German too (open fix 70).
Without the German files the game stays English and says so at its start.

## Quick start

```bash
python play.py
```

`play.py` starts orion2re in your game folder with its own window
hidden, skips the original's logos and intro, and opens OrionLayer
straight into the HD main menu. Closing OrionLayer stops the game. The
engine's log is `~/.cache/orionlayer/orion2re.log`.

By hand, in two terminals — the engine's own window is shown, and the
intro plays unless you press a key in it:

```bash
cd "/path/to/Master of Orion 2"
/path/to/orion2re
```

Wait for `ext: server started on port 17362`, then `python main.py`.
OrionLayer also starts without orion2re (`python main.py`): the HD
screens without live game data.

**Keys:** right click opens the game's context help where the original
has it; **F12** switches to the original's picture and window and back;
**F7** cycles the resolution presets; **F11** is fullscreen; **F8** saves
a screenshot of the window into `screenshots/` in OrionLayer's own folder
(`~/.config/orionlayer/screenshots/`, on Windows
`%APPDATA%\OrionLayer\screenshots`, on macOS
`~/Library/Application Support/OrionLayer/screenshots`); **F3** opens
the box editor. Every other F key is the original's: F1 / F2 the previous
and next fleet, F5 / F6 the previous and next own star, F9 the distance
between stars, F10 a quick save, Alt+F1 to Alt+F8 the game options. On the galaxy map the wheel zooms, a right-drag pans, `0`
hands the view back to the game and HOME flashes rings over your home
system (an OrionLayer addition, switchable under `home_ping` in
`screens/galaxy_map/layout.json`).

## Modding

See [MODDING.md](MODDING.md). Short version: mirror any file's path under
`mods/<your_mod>/`, list the mod in `settings.json`, restart;
`mods/example_mod/` is a working example. Colours, HUD style, texts and
pictures can also be changed per player in `~/.config/orionlayer/mod/` —
`python tools/mod_template.py` writes a starting point.

## Notes in the source

Comments and notes in the code cite the maintainer's developer notes as
`dev:<path>` — for example `dev:doc/v3_fundament.md`, the project's
decisions and working principles. Those notes (the design decisions,
readings of the orion2re source, work orders, measurements and the test
suite) are not part of this repository; a citation says where the
reasoning behind a line is recorded, not a file you are missing. Work
order, decision and open-fix numbers refer to the same notes.

## Credits

Master of Orion II's makers, the MOO2 1.50 patch team and Joes for
orion2re are credited in [doc/CREDITS.md](doc/CREDITS.md) (the main
menu's roll is its short form). The display font (Aldrich, SIL Open Font
License), the artwork's origins and what the MIT licence does not cover
are in [LICENSE](LICENSE).
