# OrionLayer v3

An HD frontend for **Master of Orion 2**, built on
[orion2re](https://github.com/) — the open-source C++
reimplementation of the original engine.

orion2re runs the game; OrionLayer replaces its 640x480 interface
with high-resolution pygame screens. The two talk over a TCP
Extension API on `localhost:17362`: OrionLayer receives game state
snapshots and injects input. Screens that have no HD version yet
fall back to the original framebuffer, scaled up, so the game is
always fully playable.

No RAM reading, no screen scraping, no root privileges — v2 needed
all three, v3 needs none of them.

**You need your own copy of Master of Orion 2.** OrionLayer is a
modification, not a game: it replaces the interface and nothing else.
Artwork in this repository is derived from the original's; copyright
in the underlying work stays with its rightsholder, and no ownership
of it is claimed. The context-help texts and the nebula reference
sprites are not included at all — they are read from your own
installation by `tools/help_extract.py` and `tools/nebula_extract.py`.
See [LICENSE](LICENSE) for what the MIT licence covers and what it
does not.

## Install

```bash
git clone <your-repo-url> orionlayerv3
cd orionlayerv3
python tools/setup.py
```

`setup.py` needs pygame, numpy and Pillow (see `requirements.txt`).
Install them the way your system expects — on Arch and other
PEP 668 distributions `pip install` into the system environment is
refused by design:

```bash
sudo pacman -S python-pygame python-numpy python-pillow   # Arch
pip install -r requirements.txt                           # elsewhere
python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

`setup.py` rebuilds the generated artwork the repository does not
carry — ship icons, sidebar icons, the black hole master — and then
runs the smoke test, so a clone reports for itself whether it came
out complete. Expect `SMOKE TEST PASSED`. `.gitignore` explains what
is generated and, more usefully, why each exception is one.

Two things come from your own copy of Master of Orion 2 and are
therefore not in the repository. Neither is required to start, but
skipping the first looks like a broken feature rather than a missing
step: right-click help then opens a panel that names this command
instead of showing the game's text.

```bash
python tools/help_extract.py                       # right-click help texts
python tools/help_extract.py --lang de             # for GER_HELP.LBX
python tools/nebula_extract.py /path/to/starbg.lbx # nebula sprites
```

The language must match `"language"` in `settings.json` — the app
reads `help_<language>.json` and nothing else. `python tools/setup.py`
reports which of the two is missing, in the language you have set.

Requires Python 3.10+ (verified on 3.12 and 3.14).

## The orion2re build it needs

<!-- orion2re-patches -->
OrionLayer talks to an orion2re built from the branch **`orionlayer-local`**
(`-DORION2RE_EXT=ON`), which is upstream plus the Extension API and the
fixes below, in this order. The branch is never uploaded anywhere; on a new
machine it comes from the bundle beside the backup
(`~/orion2re_bundle_<date>_<hash>[_<fixes>].bundle`, the newest one —
today `~/orion2re_bundle_28sep_230a0638_fixes34-47_43.bundle`:
`git clone -b orionlayer-local <bundle> ~/orion2re`), and each fix also has
its patch file here. `python tools/version_check.py` checks a built tree
against this list and prints the `patch -p1` command for any fix that is
missing. The list's one home is `LOCAL_PATCHES` in `tools/version_check.py`;
a smoke check holds this table to it.

| # | orion2re commit | fix | patch |
|---|---|---|---|
| 1 | `a111355d` | the Extension API itself (`src/ext` and its hooks), with the `src/ext` parts of open fixes 1, 2, 3, 12, 14, 20, 21 | `doc/ext_save_slots.patch`, `doc/ext_fleet_selection.patch`, `doc/ext_fleet_select_ship.patch` |
| 2 | `191aaa78` | open fix 3: an injected click keeps its pointer | `doc/ext_inject_click.patch` |
| 3 | `6598052c` | open fix 5: Select Race records `_old_race` | — (one line, in the entry) |
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

Every entry, with its status, reason and revert, is in
`doc/orion2re_open_fixes.md`.

## Quick start

**Play** (orion2re from `orionlayer-local`, built with `-DORION2RE_EXT=ON`,
and `xdotool` installed):

```bash
cd ~/orionlayerv3
python play.py
```

This is the player's start (work order 183). It starts orion2re in
`~/Master of Orion 2` — its own window stays hidden, because this start
asks for it (open fixes 41 and 43) — skips
the original's logos and intro with the same key the live tools send, so
nothing of the intro is played or heard, and then opens OrionLayer straight
into the HD main menu, no key needed. Closing OrionLayer stops the game.
**F12** switches OrionLayer's window to the original's picture AND shows
the original's own window (open fix 43); F12 again hides it and returns
to HD.
The engine's log is `~/.cache/orionlayer/orion2re.log`.

**By hand, in two terminals** — the engine's own window is shown, as
before open fix 41 (fix 43 hides it only when OrionLayer's start asks), and
the original's intro plays with its sound for about two minutes unless you
press a key in that window.

```bash
cd "$HOME/Master of Orion 2"
~/orion2re/out/build/Linux/linux-debug/orion2re
```

Wait for `ext: server started on port 17362`, then:

```bash
cd ~/orionlayerv3
python main.py 2>&1 | tee ~/orionlayer.log
```

OrionLayer also runs standalone without orion2re (HD screens without
live game data).

**After any change**, before committing:

```bash
python tools/smoke_test.py
```

## Hotkeys

### Global

| Key | Action |
|---|---|
| Right click | Context help, where MOO2 has it (see below) |
| F5 | Box editor (H inside for help; Ctrl+Wheel scales fonts) |
| F9 | Cycle resolution presets (1080p / 1440p / UW / 4K) |
| F11 | Fullscreen with pillarboxing |
| F12 | Toggle HD / original framebuffer view |

### Context help (right click)

MOO2 answers a right click over a control with a help box, and does
**not** treat it as Cancel — `fields::Check_Help_List_` walks a
per-screen table of rectangles and swallows the click on a hit. HD
does the same, on Main Menu, New Game and the Galaxy Map: right click
a menu entry, a New Game setting, a sidebar readout or a bottom-bar
button. Any key or click closes the box; the wheel scrolls a long
entry.

**The texts come from your own MOO2 installation.** They live in
`HELP.LBX`, not in the orion2re source and not on the Extension API,
so they are not part of this project. Extract them once:

```bash
python tools/help_extract.py            # or --lang de for GER_HELP.LBX
```

Until you do, the popup says so instead of appearing empty. The
regions themselves are transcribed from the C++ tables and live in
`screens/<name>/help.json`, with the original's 640x480 rectangle
recorded next to each one.

The panel's position and font size are a normal F5 box
(`help_popup`); it shrinks to fit its text inside that rect.
On the Galaxy Map the right button still pans over the map area —
the original has no help box there either, so the two never collide.

### Galaxy Map

Most of these are the game's own keys, forwarded as field
activations:

| Key | Action |
|---|---|
| G | Game menu |
| T | End turn |
| C / P / F | Colonies / Planets / Fleets |
| L / R / I | Leaders / Races / Info |

Three are **not** the game's — they are handled entirely in
OrionLayer and never reach orion2re:

| Input | Action |
|---|---|
| Mouse wheel | Zoom the HD map, anchored on the pointer |
| Right-drag | Pan the HD map (over the map area only) |
| + / − | Zoom on the map centre |
| 0 | Reset — hand the view back to the game |
| HOME | Flash rings over your own home system |

**The wheel zoom is client-side.** The state snapshot carries every
star's galaxy coordinate, so the HD map scales and pans on its own
origin; the game is never told. It is parked at maximum zoom-out
meanwhile, so clicks keep landing where the game expects them —
see decision 35 in `doc/v3_fundament.md` for why the click frame may
never follow the HD one.

**HOME is an invention.** MOO2 has no such effect and no binding on
that key, so nothing is taken away from it. It is a navigation aid
for large galaxies, marked as an invention in
`screens/galaxy_map/ping.py`, and configurable (or switchable off)
under `home_ping` in `screens/galaxy_map/layout.json`.

## Project structure

```
main.py                 entry point, window, main loop, event routing
settings.json           window, connection, skin, active mods
core/
  resources.py          mod-aware file resolution (see MODDING.md)
  palette.py            skin color access
  screens_loader.py     screen auto-discovery (base + mods)
  dispatcher.py         screen switching by orion2re screen ID
  game_client.py        TCP client for the Extension API
  game_state.py         binary state parser
  original_view.py      framebuffer fallback + original-mode input
  screen_base.py        base class for all screens
  style.py              skins, fonts, buttons, panels;
                        render_text() falls back per character on
                        glyphs the font substitutes;
                        draw_inner_panel / draw_thin_border
  nineslice.py          9-slice texture rendering
  frame.py              cockpit frame renderer (variants)
  banner.py             runtime-tinted MOO2 banners
  injection.py          injection chain: drives orion2re through
                        original dialogs, detected by field shape
  mapcoords.py          galaxy <-> 640x480 <-> HD transforms;
                        MapView (integer, the game's frame) and
                        SmoothMapView (float, the HD viewport)
  zoomtables.py         zoom levels, icon sizes, font scales —
                        transcribed from orion2re, single source
  mouse.py              pointer position, single source
  layout.py, box.py     1080p-reference coordinate system
  structs/              declarative binary struct specs
  widgets/              ListView, TextInput
  editor/               in-app box editor (F5)
  screenhelp.py         right-click context help, mixed into
                        every screen
  helppopup.py          the help popup itself (auto-sized, scrolls)
  helptext.py           loads the extracted HELP.LBX strings
screens/<name>/         one folder per screen:
                        screen.py + boxes.json + assets/
                        (+ optional data JSON like races.json)
  galaxy_map/viewctl.py the decoupled HD viewport (zoom, pan,
                        parking the game at maximum zoom-out)
assets/shared/          fonts, cursor, banner, skins/<skin>/
mods/                   drop-in mods (see MODDING.md)
tools/
  smoke_test.py         headless verification — run after changes
  help_extract.py       pull the context-help texts out of HELP.LBX
  frame_holes.py        derive galaxy map boxes from frame cutouts
  make_star_icons.py    generate the 36 star sprites
  make_ship_icons.py    generate the ship and monster size steps
  make_black_hole_master.py  build the rotatable black hole master
  make_sidebar_icons.py cut the five sidebar icons from a sheet
  make_nebula_icons.py  render the HD nebula shapes
  nebula_extract.py     pull the original nebula sprites from LBX
  star_icon_check.py    which star sprite each step resolves to
  ship_icon_check.py    owner, kind and sprite per ship icon (live)
  nebula_check.py       nebula spec check
  nebula_asset_check.py nebula asset resolution
  zoom_check.py         zoom ladder against a live map
  zoom_probe.py         what a zoom step does to the game's origin
  starfield_measure.py  background star density
  starfield_preview.py  render the star field to a PNG
  struct_probe.py       verify struct offsets against a live game
  ext_diag.py           Extension API protocol diagnostics
  ext_diag_race.py      race screen field diagnostics
```

## Conventions

- **Reference space 1920x1080** — all box coordinates; layouts are
  stored per resolution in each screen's `boxes.json`.
- **Data over code** — positions, colors, labels, and game data live
  in JSON, editable in-game (F5) or in a mod. That includes message
  text: Custom Race's rejection wording sits in `traits.json`.
- **One folder per screen, files under 300 lines** (the exceptions
  are listed with their line counts in `v3_projektstatus.md`).
- **Screens are auto-discovered** — copy `screens/_template/`, set
  `SCREEN_NAME` and optionally `GAME_SCREEN_ID`, done.
- **Two panel skins.** `inner_panel` is the 9-slice art and frames
  pictures; `thin_border` is the rounded blue outline and groups
  things. Both are box skins — set one in `boxes.json`, never draw a
  border in a screen. A screen that renders panel skins selectively
  must match on both names.
- **Input**: `ACTIVATE_FIELD` for buttons and click-through fields,
  `INJECT_CLICK` for radio buttons (type 1) — see the Extension API
  docs for why. Inside an injection-chain step use INJECT_KEY /
  INJECT_CLICK only: `g_pending_field` is consumed before queued SDL
  events, so ACTIVATE_FIELD would fire out of order.
- **The HD viewport may decouple from the game's; the click frame may
  not.** Anything that reaches the wire converts galaxy → native with
  the *game's* view state, never the HD one. Mixing them selects the
  wrong system while looking right.
- **Sizes come from `core/zoomtables.py`**, which transcribes
  orion2re's own tables. Star icon dimensions, zoom levels and font
  scales are not tuned by eye; changing a value there is a
  deliberate deviation from the original. Tables that are *derived*
  rather than transcribed say so — see
  `doc/ship_icon_measurement.md` — and so do HD-only helpers such as
  `hd_zoom_level`.
- **Text goes through `style.render_text`**, not
  `get_font(...).render`. The shipped Aldrich (OFL) substitutes
  nothing, but a mod's font may map several characters onto one
  glyph; render_text detects them and falls back per character. If
  you need to *measure* such text, measure by rendering it.
- **Read the source before theorising** — and check which side of the
  boundary the problem is on first. When the API behaves
  unexpectedly, the answer is usually one function in the orion2re
  tree (`doc/v3_orion2re_index.md` says where to look), and the
  function that BUILDS a structure beats the ones that read it. But
  sometimes the answer is that you already hold the data.

## Verifying changes

```bash
python tools/smoke_test.py
```

51 checks, headless, no orion2re needed. Covers resource resolution,
mod overrides, screen discovery, all screen lifecycles, the
dispatcher's sub-screen lock, the injection chain — including that it
survives a silent gap with no field list and that a reconnect drops
its stale one — the Empire Identity progress panel in both of its
layouts, the Custom Race Accept guard, the New Game panel-skin rule,
the editor, the struct specs, the galaxy map transform and sprite
indexing, the anchored HD zoom (the galaxy point under the pointer
must not move), ship icon kinds and tinting and owner resolution, the
black hole master's geometry, wormhole opacity and antialiasing, the
font glyph substitution, the right-click context help on all three
screens that have it, the colony summary's cutouts and native click
points, and that both cockpit frames' cutout boxes still match their
`frame.png`. It also refuses archives or backup folders under
`screens/` and duplicate decision numbers in the fundament. Run it
before every commit.

## Modding

See [MODDING.md](MODDING.md). Short version: mirror any file's path
under `mods/<your_mod>/`, list the mod in `settings.json`, restart.
`mods/example_mod/` is a working example.

## Documentation

| Document | Contents |
|---|---|
| `doc/v3_fundament.md` | Architecture decisions and working rules — read first |
| `v3_projektstatus.md` | What is built today, what is next |
| `MODDING.md` | Complete modding guide |
| `doc/v3_orion2re_index.md` | orion2re source-code reference |
| `doc/ext_api_dokumentation_v3.md` | Extension API protocol + patch |
| `doc/orion2re_open_fixes.md` | What is asked of Joes (the only list) |
| `doc/ship_icon_measurement.md` | Where the ship icon sizes come from |
| `doc/starfield_measurement.md` | Background star density |
| `doc/empire_identity_slowload.md` | The 23-second gap — open investigation |
| `doc/UMZUG.md` | Git/GitHub setup and the day-to-day workflow (German) |
| `CLAUDE.md` | Working agreement, read by a Claude Code session on start |

`doc/v3_fundament.md` holds the settled part — decisions, principles
and the mistakes that produced them. It changes rarely.
`v3_projektstatus.md` is rewritten every session.
