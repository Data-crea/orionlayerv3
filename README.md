# OrionLayer v3

An HD frontend for **Master of Orion 2**, built on
[orion2re](https://github.com/mrjoes/orion2re) — the C++
reimplementation of the original engine by Joes (its repository is
private at the moment).

orion2re runs the game; OrionLayer replaces its 640x480 interface with
high-resolution pygame screens. The two talk over a local TCP
Extension API on `localhost:17362`: OrionLayer receives game state
snapshots and sends the player's input. A screen that has no HD version
yet holds its last HD picture with the notice "F12 to answer"; F12
shows the original's picture, so the game is always playable.

**You need your own copy of Master of Orion 2.** OrionLayer is a
modification, not a game: it replaces the interface and nothing else.
Artwork in this repository is derived from the original's; copyright
in the underlying work stays with its rightsholder, and no ownership
of it is claimed. The game's own texts and pictures that OrionLayer
shows are not included at all — they are read from your own
installation (see Install). See [LICENSE](LICENSE) for what the MIT
licence covers and what it does not, and [Credits](#credits).

## Requirements

- **Master of Orion 2**, your own installation, in `~/Master of Orion 2`.
- **Python 3.10 or newer** (verified on 3.12 and 3.14) with pygame, numpy
  and Pillow — `requirements.txt`.
- **`xdotool`**, so the start can skip the original's intro (without it
  the intro plays).
- **orion2re, patched for OrionLayer** — see the next section.

## The orion2re build it needs

<!-- orion2re-patches -->
OrionLayer talks to an orion2re built from the branch **`orionlayer-local`**
(`-DORION2RE_EXT=ON`): upstream orion2re plus the Extension API and the
fixes below, in this order. Each fix that has a patch file carries it under
`doc/`, and `python tools/version_check.py [path/to/orion2re]` checks a
built tree against this list and prints the `patch -p1` command for any
fix that is missing. The list's one home is `LOCAL_PATCHES` in
`tools/version_check.py`.

**The engine cannot yet be built from this repository alone.** Two
things are missing: the Extension API itself (row 1, `src/ext` and its
hooks) has no patch file here, and orion2re's own repository,
github.com/mrjoes/orion2re, is private, so the upstream commit the
patches apply to (`cf4d9617`, "1.50 Backport: mixed race penalty") is
not publicly reachable. Until both change, the patched branch comes
from the maintainer.

| # | orion2re commit | fix | patch |
|---|---|---|---|
| 1 | `a111355d` | the Extension API itself (`src/ext` and its hooks), with the `src/ext` parts of open fixes 1, 2, 3, 12, 14, 20, 21 | `doc/ext_save_slots.patch`, `doc/ext_fleet_selection.patch`, `doc/ext_fleet_select_ship.patch` |
| 2 | `191aaa78` | open fix 3: an injected click keeps its pointer | `doc/ext_inject_click.patch` |
| 3 | `6598052c` | open fix 5: Select Race records `_old_race` (patch file since work order 192) | `doc/ext_select_race_old_race.patch` |
| 4 | `e099d3fc`, `3305d78c` | screen ids for Select Race and Custom Race; open fix 22 | `doc/ext_screen_id.patch` |
| 5 | `7067c366` | open fix 12: the pop-move command, its engine half | `doc/ext_move_pop.patch` |
| 6 | `f838c754` | open fix 24: the research dialogs' own ids | `doc/ext_research_screens.patch` |
| 7 | `e9d07528` | open fix 25: the activated research row is the one chosen | `doc/ext_tech_activate.patch` |
| 8 | `cc5ec133`, `e6199966` | open fixes 27, 28: the fleet screen's state, one ship | `doc/ext_fleet_screen_state.patch`, `doc/ext_fleet_screen_select.patch` |
| 9 | `f98b8547` | open fix 31: present without VSync on request | `doc/ext_present_no_vsync.patch` |
| 10 | `cc542e02` | open fix 30: the Leaders screen's state | `doc/ext_officer_screen_state.patch` |
| 11 | `2269749c` | open fix 32: the Info screen's history and turn messages | `doc/ext_info_screen_state.patch` |
| 12 | `9ab84230` | open fix 34: the main menu's Load dialog sends its save slots | `doc/ext_main_menu_save_slots.patch` |
| 13 | `c5d4dacd`, `01bafd9c`, `a10e20ba`, `8a6acc08`, `2be953d4`, `2097b0c6` | **open fixes 35-40, one commit each, in this order: which colony the colony screen and the build popup show (35), where its buildings stand (36), Plague and Pop Boom (37), the product's cost and turns (38), the build popup's queue under edit (39), its two lists and queue with their numbers (40)** (work order 181) | `doc/ext_colony_screen_colony.patch`, `doc/ext_colony_building_placement.patch`, `doc/ext_colony_status_word.patch`, `doc/ext_colony_product_cost.patch`, `doc/ext_build_popup_queue.patch`, `doc/ext_build_popup_lists.patch` |
| 14 | `4bf152e4` | open fix 41: the engine's own window hidden from the start, and a hidden window presents without VSync (work order 183) | `doc/ext_engine_window_hidden.patch` |
| 15 | `70d31b10`, `4af9fefa`, `8aea1a25`, `ba9b6bc6`, `230a0638` | **open fixes 44, 45, 46, 47 and 43, one commit each, in this order: the Ship Designer's design as it is edited (44), its three pickers and what they offer (45), the diplomacy audience's own ids (46) and its state (47), and the engine's window hidden only when the starter asks and shown again on request (43, amends 41)** (work order 186) | `doc/ext_ship_designer_state.patch`, `doc/ext_ship_designer_boxes.patch`, `doc/ext_audience_screen.patch`, `doc/ext_audience_state.patch`, `doc/ext_engine_window_on_request.patch` |
| 16 | `010870bc` | open fix 48: the move verdict for the fleet box's selection at every star, for the travel line on hover (work order 188) | `doc/ext_fleet_move_verdict.patch` |
| 17 | `76f8c438` | open fix 29: the generic message box's kind, title, text and answers, for the HD message box (work order 188) | `doc/ext_message_box_text.patch` |
| 18 | `6859e163` | open fix 49: the turn-time popups under their own ids (59-64; 40 kept for the Turn Summary) and what they show, for the HD turn popups (work order 188) | `doc/ext_turn_popups.patch` |
| 19 | `65b41b66` | open fix 50: the Hall of Fame's entries, and 14 on both ways in (work order 188) | `doc/ext_hall_of_fame.patch` |
| 20 | `8f7bd9e3` | open fix 51: which multiplayer step is up and what it shows (work order 188) | `doc/ext_multiplayer_state.patch` |
| 21 | `96da4c4d` | open fix 42: the extension ticks during a screen's input delay, so the research panel's list arrives ~550 ms sooner (work order 191) | `doc/ext_input_delay_tick.patch` |
| 22 | `ab3f6892` | open fix 61: a right click at a point (MSG_INJECT_RIGHT_CLICK), so the F12 view can turn a ship on the battle map (work order 194) | `doc/ext_inject_right_click.patch` |
| 23 | `2495e1cf` | open fix 52: a tactical battle reports 65 (its scan view 66, its board popup 67), and the gate the combat blocks are written under (work order 194) | `doc/ext_combat_screen_id.patch` |
| 24 | `9b7dcba0` | open fix 53: the tactical battle's state — units field by field, the turn order, the view origin, the legal moves ("CMBT") (work order 194) | `doc/ext_combat_state.patch` |
| 25 | `f506bc6c` | open fix 55: the ordnance in flight — missiles, torpedoes, fighters with their targets ("CMSL") (work order 194) | `doc/ext_combat_ordnance.patch` |
| 26 | `f1e6c581` | open fix 57: how the last battle ended — winner, sides, each unit's fate — kept until the next battle ("CRES") (work order 194) | `doc/ext_combat_result.patch` |
| 27 | `750434ef` | open fix 54: what each weapon slot of the acting unit can hit now, the engine's own verdict ("CTGT") (work order 194) | `doc/ext_combat_targets.patch` |

## Install

```bash
git clone https://github.com/Data-crea/orionlayerv3.git
cd orionlayerv3
pip install -r requirements.txt
python tools/setup.py
```

On Arch and other PEP 668 distributions `pip install` into the system
environment is refused by design; use the system packages or a venv:

```bash
sudo pacman -S python-pygame python-numpy python-pillow   # Arch
python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

`setup.py` rebuilds the artwork the repository does not carry (ship and
sidebar icons, the black hole, the HUD pieces, …) and reports what is
still missing from your own Master of Orion 2 installation. Those files
are read by the extractors below — none is required to start, but
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
python tools/techdesc_extract.py                    # ship design descriptions
python tools/fleet_art_extract.py                   # Fleets ship pictures
python tools/officer_art_extract.py                 # Leaders screen artwork
python tools/races_art_extract.py                   # Races screen artwork
python tools/design_art_extract.py                  # Ship Designer artwork
python tools/audience_art_extract.py                # audience artwork
```

`python tools/help_extract.py --lang de` reads `GER_HELP.LBX`; the language
must match `"language"` in `settings.json`. `python tools/setup.py --check`
lists what is present and what is not, and changes nothing.

## Quick start

```bash
python play.py
```

`play.py` starts orion2re in `~/Master of Orion 2` with its own window
hidden, skips the original's logos and intro, and opens OrionLayer
straight into the HD main menu. Closing OrionLayer stops the game. The
engine's log is `~/.cache/orionlayer/orion2re.log`.

By hand, in two terminals — the engine's own window is shown, and the
intro plays unless you press a key in it:

```bash
cd "$HOME/Master of Orion 2"
~/orion2re/out/build/Linux/linux-debug/orion2re
```

Wait for `ext: server started on port 17362`, then `python main.py`.
OrionLayer also starts without orion2re (`python main.py`): the HD
screens without live game data.

**Keys:** right click opens the game's context help where the original
has it; **F12** switches to the original's picture and window and back;
**F9** cycles the resolution presets; **F11** is fullscreen; **F5** opens
the box editor. On the galaxy map the wheel zooms, a right-drag pans, `0`
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
