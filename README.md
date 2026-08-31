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

## Quick start

**Terminal 1 — the game** (built with `-DORION2RE_EXT=ON`):

```bash
cd "$HOME/Master of Orion 2"
~/orion2re/out/build/Linux/linux-debug/orion2re
```

Wait for `ext: server started on port 17362`.

**Terminal 2 — the frontend:**

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

50 checks, headless, no orion2re needed. Covers resource resolution,
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
| `doc/orion2re_open_fixes.md` | What is asked of Joe (the only list) |
| `doc/ship_icon_measurement.md` | Where the ship icon sizes come from |
| `doc/starfield_measurement.md` | Background star density |
| `doc/empire_identity_slowload.md` | The 23-second gap — open investigation |
| `doc/UMZUG.md` | Git/GitHub setup and the day-to-day workflow (German) |
| `CLAUDE.md` | Working agreement, read by a Claude Code session on start |

`doc/v3_fundament.md` holds the settled part — decisions, principles
and the mistakes that produced them. It changes rarely.
`v3_projektstatus.md` is rewritten every session.
