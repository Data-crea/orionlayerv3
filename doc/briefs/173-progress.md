# Work order 173 — progress

Unattended run, 25 September 2026. One background everywhere, and
modding made easy. Builds on 169-172 (decision 71). Ends with a push
Data authorised for this order.

Evidence root: `~/orionlayer-fixtures/evidence/work_order_173/`.

## Start — how resources were resolved before anything was designed

- `core/resources.py`: one resolver, `Resources.resolve(relpath)`, mods
  under `mods/<name>/` in the TREE (settings.json `active_mods`) first,
  the base project last; `roots()` for the loaders that choose between
  file forms per root (the colony screen's figures, discs, surfaces,
  output icons); `resolve_dir` for skins and banners (decision 17).
- `user_settings.json` lives in the tree root, git-ignored, read and
  written only by `core/usersettings.py`.
- `tools/setup.py` builds the derived files, the HUD pieces among them.
- The background slot of 169: `ScreenBase._load_background` read
  `screens/<name>/assets/background.png`, else the placeholder; only the
  Main Menu had a picture. New Game's file there is NOT a background: a
  cutout template its slot geometry is mapped through (169 P6).
- The galaxy map drew its own floor, `map_background.png` — faint gas,
  no game content: nebulae, wormholes, stars, lines and fleets are all
  drawn over it.

## Part 1 — the universal background — **DONE**

- **In the tree** as `assets/shared/backgrounds/universal.png`, byte for
  byte (sha256 `65e4421c...`), LICENSE entry beside the HUD's. The Main
  Menu's title art moved beside it (`backgrounds/main_menu.png`), so
  every background is in one folder.
- **`core/backgrounds.py`**: the screen's own picture, else the
  universal one, else the placeholder; cover-scaled (the picture's own
  aspect, both axes filled, the overflow cut evenly — no stretch, no
  strip at any size, 16:9 or not); ONE copy per picture and window size,
  shared by every screen (before, each screen scaled its own: thirteen
  33 MB copies at 2160p). Never tinted.
- **Every screen and popup:** all screens via `ScreenBase`; New Game
  draws it (its cutout stays the geometry template); the research panel
  and the GAME menu are overlays over the map; every popup is the
  opaque popup block over its screen.
- **The galaxy map's floor IS the background** now, over the whole
  window, the floor lift and the point stars over it, every piece of
  game content over those. `map_background.png` stays in the tree,
  loaded by nothing. Renders before and after (parked P2).
- **Measured as in 168** (`tools/background_measure.py`, `measure.txt`,
  `measure.json`):

  | | size / upscale | lapnorm | edge 10-90 | block8 |
  |---|---|---:|---:|---:|
  | source | 1675 x 939, aspect 1.784 (16:9 is 1.778) | 0.595 | 1.66 px | 1.01 |
  | 1920x1080 | x1.15 | 0.196 | 2.11 px | 1.00 |
  | 2560x1440 | x1.53 | 0.086 | 2.44 px | 1.00 |
  | **3840x2160** | **x2.30** | **0.027** | **3.31 px** | 1.00 |
  | 2576x1432 (Data's) | x1.54 | 0.085 | 2.45 px | 1.00 |

  **Effective detail:** shrunk and blown back up, the picture loses its
  grain at ANY shrink (1.5 % RMS already at 90 %) and its structure
  only below 20 % of its width — the clouds carry about 335 px of
  structure; the rest is grain and point stars. **At 2160p it is a 2.3x
  upscale**: the clouds hold up (they were soft to begin with), the
  grain and the point stars go soft (edges 3.3 px against 1.7 in the
  source), and the code-drawn panels in front of it are crisp. A
  3840x2160 source would sharpen only the stars and the grain.
- **Readability, measured** where text stands directly on the picture
  (not on a panel): every word three renders, WCAG contrast against the
  brightest background under it. Galaxy map names >= 5.06:1 (5.39 at
  2160p), research >= 11.6, the GAME menu over the map >= 5.06. **Select
  Race and Custom Race lost the most**: their text groups were outlines
  over the bright left edge of the picture — race names 9.4 -> 3.4:1 at
  2160p, Custom Race's left column 13.6 -> 4.1. **The HUD panel fill
  does the work**, as the order says: a `thin_border` box may carry
  `"fill": true` (data, F5-safe), and those five groups at both box
  lists do; both screens draw their groups before their words, so
  nothing is covered (172's lesson checked). Afterwards neither screen
  has a word on the bare picture at 1080p, Custom Race six at 2160p at
  >= 5.14. **Left as they are:** New Game's "|" separators in the status
  hint, 3.48:1 (3.35 on the old placeholder — their own dim colour), and
  the Main Menu's version line, 3.72:1 on its own title art (unchanged
  by this order).

## Part 2 — the mod folder — **DONE**, HD EXTENSION, decision 72

- **Where:** `~/.config/orionlayer/mod` (Linux, `$XDG_CONFIG_HOME`
  honoured), `%APPDATA%\OrionLayer\mod` (Windows), `~/Library/Application
  Support/OrionLayer/mod` (macOS); `ORIONLAYER_USER_DIR` replaces the
  part before `mod`. Outside the tree; nothing is copied in. **Parked
  P1**: the order says "next to the settings file", and
  `user_settings.json` is in the tree root.
- **One resolver:** `Resources.resolve` asks `core.usermod` first and
  nothing else does; the partial style and the frame colour are read by
  `core.hud.style` through it. No screen loads around it.
- **What can be replaced** (the template lists every name with its
  size): `background.png`; `backgrounds/<screen>.png` (beats the
  universal one); `hud/<piece>.png` (twelve icons, the title plate);
  `style.json` PARTIAL, key by key, kinds checked; `colour.json`, the
  default frame colour (the player's own choice beats it, RESET returns
  to it, the settings row stores the player's value and never the
  mod's); **added through the same mechanism:** `files/<tree path>` for
  every other picture the screens resolve — 136 names on this disk (a clone that has not extracted the ship and sidebar icons lists fewer): New Game's
  setting pictures, the race portraits, Custom Race's pictures, Empire
  Identity's home world, the stars, nebulae, black hole, ship and
  monster icons and sidebar icons of the galaxy map, the Main Menu logo
  (`usermod.GAME_ART`, from a trace of every screen's render).
- **Robust:** every file checked before use; garbage, a wrong format, an
  unknown name, non-JSON, a wrong-kind key: one log line each, the
  default used. A picture of another size is scaled ONCE to the
  default's size (a copy in `cache/` beside the folder); backgrounds are
  cover-scaled and keep theirs.
- **Off without deleting:** GAME -> SETTINGS -> **Mod folder: On / Off**
  (`user_mod` in `user_settings.json`), shown with how many of the
  folder's files are in use; takes effect at the next start, like the
  colour preset (decision 18), and the row's restart note says so. The
  thirteen engine rows gave up 29 px (38 -> 36 each) so the dialog kept
  its size and ACCEPT did not move.
- **`tools/mod_template.py`:** writes `MODDING.md` (plain language),
  `NAMES.txt` (every name, size, format) and OrionLayer's own files under
  `originals/` — the universal background, the HUD pieces cut fresh
  from Data's HUD, the style values, the measured colour — which change
  nothing until one is copied up a level, so a template never pins
  today's defaults. **Never a MOO2 file**: pictures extracted from the
  game or derived from its artwork (LICENSE) are listed by name only.
  It refuses a target inside the tree and never overwrites a file.
  An example run is in the evidence folder.
- **Decision 72** in fundament part 01, with what the folder does not
  reach (the colony screen's per-root loaders; whole-directory banners
  and skins — all still replaceable through `mods/`). `MODDING.md`
  opens with the easy way.
- **Several mods side by side:** not built — parked P3.

## Found on the way

- `tools/hud_evidence.py`'s app had `user_settings = {}`, so every
  settings row rendered with a blank value in every earlier render
  ("Map floor" with nothing after it). Now the defaults.
- The smoke suite's App boot (061) opened the player's own mod folder —
  the same leak it already guarded `user_settings.json` against; the
  first full run also wrote one cache file into `~/.config/orionlayer`
  (removed; the directory had been created by that run and held nothing
  else). The cache now lives beside the folder in use, the boot points
  `ORIONLAYER_USER_DIR` at its scratch directory, and the check asserts
  both.
- `tint._hls` warned about 0/0 on black pixels (the result was already
  discarded); it now divides only where defined.
- The offline galaxy render shows the synthetic nebula cut off straight
  on its right side — before this order too (`galaxy_floor_before_*`);
  not the background's doing, not touched.

## Checks

307 -> **314**, none deleted:
- background covers the window at eight sizes (aspect, both axes,
  centred, one shared copy, never tinted);
- override order per-screen > universal > default, file by file, the
  galaxy floor included;
- a partial style.json overrides only its keys;
- broken, unknown and odd-sized files fall back, five screens render on
  a broken folder;
- switched off it is not read; colour.json is the default colour;
- the template holds no MOO2 file (every file it writes hashed against
  every other file in the tree) and refuses the tree;
- text on the universal background >= 3.4:1, and Select Race's and
  Custom Race's words on the panel fill (push-only, ~30 s).
006a's "screens without a picture draw the placeholder" now asserts the
filled slot. The runtime lines in CLAUDE.md and the status document
were stale since 172 (they said ~72 s / ~32 s): measured now ~155 s
full, ~63 s fast.

## Live — PARKED

`ps -C orion2re`: PID 287200, started 19:00 by Data, holds port 17362.
Not connected to; no engine of this run could take the port. Everything
above is offline, and every render says so in its name.

## Evidence — for Data to look at

`~/orionlayer-fixtures/evidence/work_order_173/`:
- `contact_sheet_1920x1080.png`, `contact_sheet_3840x2160.png` and
  `screens/` — every screen at 1080p and 2160p, the GAME menu's settings
  with the new row, the galaxy map at 2576x1432.
- `demo_mod_galaxy_map_*.png`, `demo_mod_colony_summary_*.png` — a demo
  mod (its own procedural violet background, colour.json hue 32) through
  the real resolver; `demo_mod_switched_off_*` the same folder switched
  off; the folder itself in `demo_mod_folder/`.
- `galaxy_floor_before_map_background.png` / `galaxy_floor_after_universal.png` (P2).
- `main_menu_alternative_on_universal_1920x1080_offline.png` (P4).
- `template_example/` — what `tools/mod_template.py` writes.
- `measure.txt`, `measure.json` — the picture and every word's contrast.

## Push — what goes out (listed BEFORE pushing)

Remote `origin` = `git@github.com:Data-crea/orionlayerv3.git`, which held
`main` at `9896b34` and nothing else (`git ls-remote`: HEAD and
refs/heads/main only; no tags anywhere, local or remote).

**`main`**: every local commit not on the remote — 32 listed here, oldest
first, plus the commit that carries this document:

- `dfd9d42` 2026-09-24 Work order 167 filed: the Leaders screen in HD, and its inventory (167)
- `a5bb2d3` 2026-09-24 Parts B-E: the Leaders screen, its verified data and its checks (167)
- `67cdb2e` 2026-09-24 The live driver for the Leaders screen, and one home for its field list (167)
- `eabd549` 2026-09-24 Work order 167: the live part parked, the closing state (167)
- `ac5ed00` 2026-09-25 Work order 168: which outer frame becomes the shared ring, the evaluation (168)
- `bf2bd29` 2026-09-25 Work order 169 filed, and decision 71 recorded first (169)
- `c251ab6` 2026-09-25 The HUD style: material, measured style, blocks; galaxy map and GAME menu (169)
- `42872f4` 2026-09-25 Colony summary in the HUD style (169)
- `24e67fc` 2026-09-25 Planets in the HUD style (169)
- `ea41cd9` 2026-09-25 Fleets in the HUD style (169)
- `2a09509` 2026-09-25 Research select and change in the HUD style (169)
- `33c7615` 2026-09-25 Leaders in the HUD style (169)
- `4a75bf0` 2026-09-25 Custom Race in the HUD style (169)
- `0c7b832` 2026-09-25 New Game in the HUD style (169)
- `baa5d0f` 2026-09-25 Empire Identity in the HUD style (169)
- `b2f0cf8` 2026-09-25 Custom Race: the message box is the HUD popup block (169)
- `ab04137` 2026-09-25 Popups and dialogs on Leaders and research wear the popup block (169)
- `d63b48f` 2026-09-25 Work order 169 closed: progress, parked items, status, evidence tool fix (169)
- `14e0433` 2026-09-25 169 progress: the fresh-clone results (169)
- `c7f9f7f` 2026-09-25 Work order 170 filed, with the cause of the gap measured (170)
- `b79ed30` 2026-09-25 Galaxy map: the bar on the bottom edge, the map in the free space (170)
- `2168e80` 2026-09-25 Colony summary: the sort row and RETURN on the bottom edge (170)
- `01187d4` 2026-09-25 Pre-game screens: the frame buttons on the bottom edge (170)
- `ba6c755` 2026-09-25 The HUD frame colour: a hue slider in the GAME menu's Settings (170)
- `cc0fe90` 2026-09-25 Work order 170 closed: progress, parked items, status, evidence tool (170)
- `7b6c5b6` 2026-09-25 Work order 171 filed (171)
- `53576fa` 2026-09-25 Galaxy map: the title plate centred on the map, not the window (171)
- `783090e` 2026-09-25 The HUD frame colour reaches grey, silver and black (171)
- `227a132` 2026-09-25 Work order 171 closed: progress, parked items, status, evidence tool (171)
- `d8238ba` 2026-09-25 New Game's pictures back; the frame colour by component, never by colour (172)
- `70d66d1` 2026-09-25 One background behind every screen, and the player's mod folder (173)
- `b3faed2` 2026-09-25 Text groups take the panel fill over the new background; decision 72 (173)

**Two local branches the remote does not have**, pushed as they are:
- `colony-free-bands` at `a24f761` (2026-09-11, Fundament 53, and two rules nobody can source yet) — already contained in `main`'s history, so it adds a name, not a commit.
- `rescue/ties-abend` at `0907b63` (2026-09-03, colony summary: the word rule, growth's unit, the tenth row, and the sort set instead of read) — already contained in `main`'s history, so it adds a name, not a commit.

Nothing force-pushed, no history rewritten. orion2re stays local: only
this repository is pushed (the suite holds that no orion2re source file is
tracked here).
