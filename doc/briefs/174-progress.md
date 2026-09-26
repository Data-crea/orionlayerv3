# Work order 174 — progress

Unattended run, 26 September 2026. Glass instead of black on every
screen, a glass slider, and the live test of 167-173. Builds on 169-173
(decisions 71, 72). Parts in the order's order: A, B, C.

Evidence root: `~/orionlayer-fixtures/evidence/work_order_174/`.

## Precondition — checked at the start

`ps -C orion2re`: no engine running. No OrionLayer client (`main.py`)
running. Port 17362: nobody listening. Data's engine from 173 (PID
287200) is gone. So A and C may start an engine of this run.

The mockup is at `~/Downloads/ChatGPT Image Sep 26, 2026, 06_07_07 AM.png`
(spaces and commas where the order has underscores; 1683 x 935, sha256
`80f7b6e2...`) — the only file of that time stamp.

## Part A — the start hang — **EXPLAINED; the fix is in orion2re (patch, not applied); our side detects and restarts**

Saves hashed before any engine started (`saves_before.sha256`).

**1. Started as the protocol says** (DISPLAY :0, the newest mutter auth
file, `SDL_VIDEODRIVER=x11`, `cd "$HOME/Master of Orion 2"`, `nohup`):
at 06:20 it ran cleanly to `ext: server started` (`engine_start1.log`).
The window "Orion2 Redone" was mapped and viewable. A second start with
the window minimised during the logos: clean too.

**2. It did hang, intermittently.** The new start tool's first run hung
at the old place (`engine_start3_tool.log`); alternating runs showed it
has nothing to do with the tool: 2 of 7 starts hung, with and without an
idle inhibitor, the screen on each time (idle 2-1403 ms).

**3. Where it waits — backtraces** (a start with ptrace allowed by the
child, `prctl(PR_SET_PTRACER)`, gdb attached only after a hang;
`hang_backtrace_6.txt`, `_9.txt`): the main thread in
`SDL_RenderPresent` → the NVIDIA GLX swap (driver 615.71.09) →
`drmSyncobjTimelineWait`; the game thread in `JIM::Draw_Logos_` →
`palstore::Slow_Fade_In_` → `video::Submit_Palette_`, in
`SDL_WaitCondition(..., timeoutNS=-1)`, waiting for that present. VSync
is on (platform.cpp:644, :1390). `SDL_LogInfo` writes unbuffered to
stderr, so "data space allocated" really is the last thing done
(mox2.cpp:299, then `Draw_Logos_` at :302). Under gdb from the start it
never hung (0 of 6): the fault is timing-sensitive. `_8.txt` is NOT a
hang — the intro cinematic playing (`Play_Cinematic_`, jim.cpp:151),
which holds the log at the same line; the tool tells the two apart only
by the threads' waits over several samples.

**4. When — what was running.** At 06:21:53 Data launched Borderlands 3
full-screen (3440x1440, focused, covering the monitor; journal and
`_NET_CLIENT_LIST_STACKING`). The one clean start before that was at
06:20; every later series ran behind the game. On 25 September (169)
the engine was started at 18:39:57, nine and a half minutes after
Data's last input in that session, with GNOME set to blank and lock
after 300 s idle (`idle-delay 300`, `lock-delay 0`) — the journal logs
no lock events, so that one is circumstantial. Data's engine at 19:00
started with him at the screen. An engine that DID come up behind the
game runs, throttled: 19-35 state snapshots in 6 s to a client of this
run.

**5. One change at a time** (`hangstat_r1..r4.json`; a "GPU-HANG" is the
signature, not a timeout):

| change | starts | hangs |
|---|---:|---:|
| none — Data's build, the protocol's command (three series) | 60 | 8 |
| an idle inhibitor / no inhibitor / a new session / nohup | 7 | 2 |
| `__NV_DISABLE_EXPLICIT_SYNC=1` | 40 (+12 with gdb armed) | hangs moved to `xcb_wait_for_special_event` (2 caught) |
| `SDL_RENDER_DRIVER=software` | 20 | 6 |
| `SDL_RENDER_DRIVER=vulkan` | 20 (+20 with gdb armed) | hangs moved to `VULKAN_AcquireNextSwapchainImage` (2 caught) |
| scratch build of e6199966, unpatched | 20 | 1 |
| scratch build with `ORION2RE_NO_VSYNC=1` (the patch) | 50 | **0** |

**The change that did it: not waiting for VSync** — which needs
orion2re. **Cause and fix belong to orion2re** (patch rule): open fix
31 in `doc/orion2re_open_fixes.md`, `doc/ext_present_no_vsync.patch`
(an `ORION2RE_EXT`-gated `ORION2RE_NO_VSYNC=1`; default unchanged),
`patch --dry-run` clean against Data's tree, built and run only in a
scratch copy (`git archive` plus `vendors/`; Data's tree untouched).
**NOT APPLIED — parked A1.**

**Our side** — `tools/engine_start.py`, the one way a live run starts
the engine now: sets `ORION2RE_NO_VSYNC=1` (ignored until the patch is
in), refuses on a locked screen / a taken port / an engine that is not
ours (found by binding, never connecting), runs under an idle
inhibitor, recognises the hang by its signature and starts again,
stopping only its own PID. Shown working: 10 runs, one of which met the
hang twice and came up on the third start (`engine_retry_*.log`). A
check holds its decisions offline (006e). Recorded in fundament part 09
beside the protocol; CLAUDE.md's "cause open" paragraph now says what
was found. Every engine started for A was stopped by its PID; none of
Data's processes was touched.

## Part B — glass instead of black — **DONE**

### B1 — the inventory, found rather than listed

`tools/glass_inventory.py` renders every stage twice, over a magenta and
over a green background; a pixel that does not change is opaque, and a
large, flat, near-black opaque region is a box. 20 stages: the 13
screens, the six GAME menu nodes, the help popup and Custom Race's
message box (`inventory_before_1080p.json`). Before B:

| stage | dark boxes | what they were |
|---|---:|---|
| colony_summary | 47 | 38 table rows and bands (`listgrid` A/B/selected fills, (5,18,31)/(1,12,25)); 6 header plates (own fill (2,12,23)); the empire-stats box (`colonyempire`, `panel.fill` filled by hand); 1 HUD panel; the galaxy inset (black, a map — excluded) |
| custom_race | 15 | 15 HUD panels (columns, picks, pick rows) |
| empire_identity | 3 | 2 text fields (`text_input`, (12,16,30)); 1 HUD panel |
| fleets | 25 | 20 ship-grid slots (`fltdraw` slot fill (0,0,36)); 4 HUD panels; the fleet map window (black, a map — excluded) |
| galaxy_map | 1 | the info panel |
| leaders | 7 | 6 HUD panels (leader rows, strips); the galaxy box (black, a map — excluded) |
| planets | 55 | 40 table rows (`listgrid`); 5 header cells (`table_header`); 9 HUD panels; the star-map inset (black, a map — excluded) |
| research_change / research_select | 9 / 8 | the category boxes (HUD panels) |
| select_race | 2 | grid and info panel (the `"fill": true` groups of 173) |
| GAME menu, six nodes | 35 | popup bodies, slot rows, the volume panel, the sidebar |
| help_popup, custom_race_message | 19 | popup bodies and the panels under them |
| main_menu, new_game | 0 | New Game's panels sit under its pictures |

Fills that only a state offline cannot reach draws, found in the code:
the colony pop-move popup (`colonypopup`, (14,20,34)), the research
change overlay's own panel-area fill (black, `researchscreen`). Both are
glass now. **Not glass, on purpose:** the four map areas above (the
engine's or the original's own black), the picture cells under
portraits and banners, the fallback view's note (it cuts itself out of
the cockpit texture, not a black fill), a button's own face.

### B2 — the glass, one fill in core/hud/

- **Measured from the mockup**, committed as
  `doc/briefs/174-mockup-select-race.png` (1683 x 935) and measured by
  `tools/hud_glass.py` into `style.json`'s `measured.glass`, held to the
  tool by the existing style check: the universal picture aligned to
  the mockup (correlation 0.82 outside the boxes — the generator
  re-painted it), the right box regressed per text-free band as
  `bg * (1 - a) + g * a`, a straight line fitted: **top (9,18,27) at
  opacity 0.686, bottom (2,10,17) at 0.819**. The bands scatter by about
  0.1 in opacity; the numbers say where they come from.
- **`core/hud/glass.py`**: every filled panel (`blocks.panel`) and every
  former own fill (`glass.draw`: table rows and headers, grid slots, text
  fields, the colony popup, the research overlay's area) is the
  background picture under it, dimmed, under the gradient. The gradient
  colours go through the tint rule (measured: navy under blue, violet
  under violet, no hue under grey and silver, darkest under black —
  check 006f); the picture is never tinted. What shows through is the
  BACKGROUND, never what a screen drew over it — a popup still hides the
  map under it.
- **Dense variant** (`dense_transparency` 0.5 — half the transparency):
  the colony list, the planet list, Select Race's portrait grid, the
  fleet slots, the research lists, table rows and headers, text fields.
  Parked B2.
- **Tables keep their stripes**: a row is dense glass with its A/B or
  selected colour laid over (0.45 / 0.75), a header band at 0.6 — chosen,
  the mockup has no table. Parked B3.
- **Soften: none** — the mockup shows no blur. Parked B4.
- **Inner corner lines**: built (`glass.corner_lines`), off; drawn only
  in panels big enough, faint. Renders in `corners/`. Parked B5.
- **Built once** per panel, position, window size, tint, background and
  slider (the blocks' cache and the glass's own); nothing is blended per
  frame.

### B3 — the Panel glass slider

GAME -> SETTINGS -> **Panel glass** (HD EXTENSION), between Frame tone
and Mod folder, with its own RESET: 0 = twice the mockup's transparency,
0.5 = the mockup (default), 1 = solid. Stored as `hud_glass` in
`user_settings.json` (the player's value; None = default), applied at
once, back after a restart; a mod's partial style.json may move the
default (`chosen.glass.slider_default`). The dialog kept its size: the
thirteen engine rows went 36 -> 34 and the OrionLayer rows are 28 px.

**The floor.** At every position every HUD word stays at 170/171's
4.5:1: per panel, the brightest background row under it (3x3 average,
99th percentile — a point star smaller than a stroke does not decide)
must stay dark enough under the glass for the dimmest HUD word
(`text.label`); where the slider would go below, THAT panel is made
denser. Where and to what (`glass_clamps.txt` / `.json`, 1080p):

| background | slider | panels made denser | transparency kept (of wanted) |
|---|---|---|---|
| universal | 0.5 (default) | none | — |
| universal | 0.25 | the galaxy info panel (on every GAME menu node too), Planets' side panel | 1.14 and 1.07 of 1.50 |
| universal | 0.0 | the same two; Planets' planet panel, Custom Race's picks and description, the colony planet info, Select Race's info panel, one New Game panel | 1.07 - 1.97 of 2.00 |
| 173's demo mod | 0, 0.25, 0.5 | none — the picture is darker than the limit under every panel | — |

The check (006f, push-only) sweeps 58 panels x 3 backgrounds (universal,
a bright procedural nebula, plain white) x 5 frame colours x 5 positions:
worst 4.50:1. Words outside the HUD's own list (a screen's palette
words) keep 173's rule; measured again below in C.

### Checks — 315 -> 320

006f: glass on every box (no opaque dark box left on 20 stages but the
named map and picture areas); glass follows the tint and never tints the
background; the slider's persistence, reset, mod default, dense denser;
the floor over tints x backgrounds x slider (push-only); New Game's
pictures their source at both slider ends. Five existing checks read a
flat fill back and now read the glass their fill draws instead
(successors, none deleted): 016 (colony header and window), 032b (the
list stripes, split out of 032 for the 40 KB rule), 058 (Planets' fills
and hover lines, through the new `listgrid.fill_colour_at`), 077 (the
dialog's geometry keys), 080j (the research boxes).

## Part C — the live test of 167-173 and B — **RUN**, 06:47-09:31

**Precondition held**: no engine and no client of Data's; every engine was
this run's, started by `tools/engine_start.py`, stopped by its PID. **One
client** at a time: each step is its own process around
`tools/livedrive.Run` (the real `main.App`, headless, real pygame events
— clicks and keys go in at OrionLayer's front door, never through the
desktop pointer, because Data was playing a full-screen game on the same
machine). Every step's HD window and native framebuffer are captured
from one frame, in one folder per screen under `live/`, named
`..._LIVE_<size>_...`; the driver scripts are copied to `live/driver/`;
`live/results.jsonl` is every step's expected, observed, result, slot and
evidence.

**Saves.** SAVE1-11 hashed at 06:18 (`saves_before.sha256`). Only
**SAVE4** was loaded (three times), never saved; SAVE8 never touched.
TURN rewrote the autosave SAVE10 (08:59), which had been copied first
and was put back: **after the run SAVE1-11 are identical to 06:18**,
checked. `user_settings.json` was copied first and put back byte for
byte (the settings steps wrote it).

**`MOX.SET` — found afterwards, stated plainly.** The order names
SAVE1-11; `MOX.SET` was not copied before the run, and it WAS written:
at 09:26:31, when GAME -> NEW GAME -> YES left the loaded game,
`FILEDEF::Save_Game_Settings_` wrote the settings in memory — SAVE4's
(a save carries its settings, `savegame.cpp:1368`). Against Data's own
autosave of 06:18 (whose `Save_Game_` writes `MOX.SET` right after the
save, `filedef.cpp:82`) the file differed in 7 bytes, among them
`active_save_slot` 3 instead of 10 (CONTINUE would then pick the scratch
slot). The settings block of that 06:18 save (offset 48, 553 bytes,
equal to the written file in everything but those 7 bytes, the volumes
included) was written back as `MOX.SET`; the file as the run left it is
kept as `MOX.SET_after_run`, the reconstruction as
`MOX.SET_reconstructed_from_SAVE10_0618`. Byte identity with the file
before the run cannot be proven — there is no copy of it. Parked C5.

**Which engine.** The first four steps ran on Data's build. Behind the
full-screen game it was presenting about one frame a second (9 state
snapshots in 10 s against 61 with the fix; a click injected into the
colony screen was lost for 15 s) — the start hang's cause, still acting
after the start (A). Every later step ran on the scratch build of
e6199966 with open fix 31 and `ORION2RE_NO_VSYNC=1`: the same game and
the same Extension API, presenting without waiting. Parked C1.

**Sizes.** 1920x1080 and Data's 2576x1432 (the size 172's New Game bug
was found at) — the galaxy steps, the screens, the settings slider, New
Game and Select Race at both.

### What was found (none caused by 169-173 or by B, so none fixed — each parked with evidence)

1. **An unknown modal on the galaxy map is invisible in HD** (broken).
   After TURN the game asked "Select planet for Colony Base in Malus
   system", then "Really trash your colony base for 100BC?", then "Build
   colony on Malus II". HD drew the bare map throughout
   (`showing_original` False): the galaxy map draws the boxes it knows
   (system, fleet — brief 110, 15 September) and never hands an unknown
   one to the fallback view; ESC did not close it, a click would land on
   the map. The driver answered the three from the live list (NO, a
   planet, YES — work order 122's dialog, on the scratch save, in memory).
2. **Select Race has no way back in HD** (broken): HD's ESC injects a
   click at native (162, 445) (`select_race/screen.py:310`, first
   commit, 31 August), where no field of this list lies; the list's own
   ESC field (field 1, hidden) was never used. Custom Race's ESC works.
3. **The main menu's Load dialog is not drawn in HD**: the main menu
   stays on screen while the game's dialog (15 fields) is up; the row
   positions are the centred variant (`loadsave.cpp:224-229`, base
   (180, 51)), which `tools/gameload.py` does not know — the driver
   checked all ten rows against that source instead.
4. **New Game's layout offers a fourth tech level** (`post_warp`) the
   original does not have (three, `newgame.cpp:18`); the game cycles
   three, HD follows, every picture right. First commit.
5. **Select Race's text at 2160p overlaps** (name over subtitle, the
   government line cut) — the same before 169 (rendered at `ac5ed00`).
6. **Keys are not forwarded by the fallback view** (Races, Info): its
   RETURN works by click; ESC typed there does nothing.

**98 of the 103 steps work, 3 are broken (two causes, findings 1 and 2), 2 are parked.** Works: the GAME plate and every nav button there
and back at both sizes (Races and Info through the fallback view); star
and fleet boxes open and close (HD draws them, glass popup); TURN
advances the stardate; the turn's report pages and the new colony's
screen answer through the fallback view; the frame colour's three bars
and the glass slider change the look at once, both RESETs return to the
measured values, ACCEPT writes them, they survive a client restart; the
mod folder is used, switched off and on again across three restarts;
New Game's five settings cycle through every value with every picture
equal to its source, each checkbox flips in the game and redraws, CANCEL
returns — at 1920x1080 AND 2576x1432; Select Race's right box follows
the race under the pointer, Custom Race opens after its portrait and
takes an option; Colonies (hover scans, a sort key), Planets (a sort),
Fleets (next fleet), Leaders (both tabs, READY; a leader click sends
nothing, as decision 65 wants), research (the sidebar opens research
change), the GAME menu's Load and Save dialogs, the help popup.
**Parked:** hiring a leader — SAVE4 offers the player none (167's
finding, again live).

## Checks

315 (after A) -> 320 (B); C added no check — it fixed nothing (nothing
it found was caused by 169-173 or B).

## Results — every live step

| # | step | result | engine | evidence |
|---:|---|---|---|---|
| 1 | load SAVE4 from the main menu's Load dialog | **works** | Data's build | load/001_main_menu_load_dialog_LIVE_1920x1080_hd.png, galaxy_map/002_after_load_slot4_LIVE_1920x1080_hd.png |
| 2 | galaxy: GAME plate click opens the menu (1920x1080) | **works** | Data's build | game_menu/001_opened_by_plate_LIVE_1920x1080_hd.png |
| 3 | galaxy: GAME menu RETURN (1920x1080) | **works** | Data's build | — |
| 4 | galaxy: nav COLONIES opens its screen and comes back (1920x1080) | **works** | Data's build | colony_summary/002_opened_from_colonies_LIVE_1920x1080_hd.png |
| 5 | load SAVE4 from the main menu's Load dialog | **works** | probe (fix 31) | load/001_main_menu_load_dialog_LIVE_1920x1080_hd.png, galaxy_map/002_after_load_slot4_LIVE_1920x1080_hd.png |
| 6 | galaxy: GAME plate click opens the menu (1920x1080) | **works** | probe (fix 31) | game_menu/001_opened_by_plate_LIVE_1920x1080_hd.png |
| 7 | galaxy: GAME menu RETURN (1920x1080) | **works** | probe (fix 31) | — |
| 8 | galaxy: nav COLONIES opens its screen and comes back (1920x1080) | **works** | probe (fix 31) | colony_summary/002_opened_from_colonies_LIVE_1920x1080_hd.png |
| 9 | galaxy: nav PLANETS opens its screen and comes back (1920x1080) | **works** | probe (fix 31) | planets/003_opened_from_planets_LIVE_1920x1080_hd.png |
| 10 | galaxy: nav FLEETS opens its screen and comes back (1920x1080) | **works** | probe (fix 31) | fleets/004_opened_from_fleets_LIVE_1920x1080_hd.png |
| 11 | galaxy: nav LEADERS opens its screen and comes back (1920x1080) | **works** | probe (fix 31) | leaders/005_opened_from_leaders_LIVE_1920x1080_hd.png |
| 12 | galaxy: nav RACES opens its screen and comes back (1920x1080) | **works** | probe (fix 31) | races/006_opened_from_races_LIVE_1920x1080_hd.png |
| 13 | galaxy: nav RACES comes back (1920x1080) | **works** | probe (fix 31) | races/001_races_screen_LIVE_1920x1080_hd.png |
| 14 | galaxy: nav INFO opens its screen and comes back (1920x1080) | **works** | probe (fix 31) | info/001_opened_from_info_LIVE_1920x1080_hd.png |
| 15 | galaxy: star click (1920x1080) | **works** | probe (fix 31) | galaxy_map/001_star_click_Hastur_LIVE_1920x1080_hd.png + native |
| 16 | galaxy: star box closes (1920x1080) | **works** | probe (fix 31) | — |
| 17 | galaxy: fleet click (1920x1080) | **works** | probe (fix 31) | galaxy_map/002_fleet_click_LIVE_1920x1080_hd.png + native |
| 18 | galaxy: fleet box closes (1920x1080) | **works** | probe (fix 31) | — |
| 19 | galaxy: TURN advances the stardate (1920x1080) | **works** | probe (fix 31) | galaxy_map/003_after_turn_LIVE_1920x1080_hd.png |
| 20 | galaxy: a native modal after TURN (Colony Base in Malus) (1920x1080) | **broken** | probe (fix 31) | galaxy_map/001_090153_after_turn_colony_base_modal_LIVE_1920x1080_hd.png vs 001_090153_after_turn_colony_base_modal_LIVE_1920x1080_native.png |
| 21 | galaxy: the three turn-start dialogs answered (1920x1080) | **works** | probe (fix 31) | state/*_modal_*, state/*_screen33_* |
| 22 | galaxy: after TURN, back to the map through the fallback screens (1920x1080) | **works** | probe (fix 31) | state/*turn_page*, galaxy_map/002_091122_back_after_turn_LIVE_1920x1080_hd.png |
| 23 | GAME -> SETTINGS opens (1920x1080) | **works** | probe (fix 31) | game_menu_settings/001_091138_settings_open_LIVE_1920x1080_hd.png |
| 24 | SETTINGS: hue changes the look live (1920x1080) | **works** | probe (fix 31) | game_menu_settings/002_091139_after_hue_LIVE_1920x1080_hd.png |
| 25 | SETTINGS: saturation changes the look live (1920x1080) | **works** | probe (fix 31) | game_menu_settings/003_091141_after_saturation_LIVE_1920x1080_hd.png |
| 26 | SETTINGS: brightness changes the look live (1920x1080) | **works** | probe (fix 31) | game_menu_settings/004_091143_after_brightness_LIVE_1920x1080_hd.png |
| 27 | SETTINGS: Panel glass changes the look live (1920x1080) | **works** | probe (fix 31) | game_menu_settings/005_091145_after_Panel_glass_LIVE_1920x1080_hd.png |
| 28 | SETTINGS: frame colour Reset (1920x1080) | **works** | probe (fix 31) | game_menu_settings/006_091146_after_frame_colour_Reset_LIVE_1920x1080_hd.png |
| 29 | SETTINGS: Panel glass Reset (1920x1080) | **works** | probe (fix 31) | game_menu_settings/007_091148_after_Panel_glass_Reset_LIVE_1920x1080_hd.png |
| 30 | SETTINGS: ACCEPT writes the choice (1920x1080) | **works** | probe (fix 31) | user_settings.json (restored from the backup at the end) |
| 31 | SETTINGS survive a restart (1920x1080) | **works** | probe (fix 31) | galaxy_map/001_091208_after_restart_settings_LIVE_1920x1080_hd.png |
| 32 | mod folder on after a restart (1920x1080) | **works** | probe (fix 31) | galaxy_map/001_091224_mod_on_background_LIVE_1920x1080_hd.png |
| 33 | SETTINGS: Mod folder row switches (1920x1080) | **works** | probe (fix 31) | game_menu_settings/002_091229_mod_on_switched_LIVE_1920x1080_hd.png |
| 34 | mod folder off after a restart (1920x1080) | **works** | probe (fix 31) | galaxy_map/001_091232_mod_off_background_LIVE_1920x1080_hd.png |
| 35 | SETTINGS: Mod folder row switches (1920x1080) | **works** | probe (fix 31) | game_menu_settings/002_091237_mod_off_switched_LIVE_1920x1080_hd.png |
| 36 | mod folder on after a restart (1920x1080) | **works** | probe (fix 31) | galaxy_map/001_091241_mod_back_on_background_LIVE_1920x1080_hd.png |
| 37 | PLANETS: sort by Minerals, RETURN (1920x1080) | **works** | probe (fix 31) | planets/004_091444_sort_minerals_clicked_LIVE_1920x1080_hd.png |
| 38 | FLEETS: next fleet, RETURN (1920x1080) | **works** | probe (fix 31) | fleets/006_091446_next_fleet_clicked_LIVE_1920x1080_hd.png |
| 39 | LEADERS: opens, both tabs (1920x1080) | **works** | probe (fix 31) | leaders/007_091449_tab_ship_LIVE_1920x1080_hd.png, leaders/008_091449_tab_colony_LIVE_1920x1080_hd.png |
| 40 | LEADERS: a leader click (1920x1080) | **works** | probe (fix 31) | leaders/009_091450_leader_row_clicked_LIVE_1920x1080_hd.png |
| 41 | LEADERS: hire popup (1920x1080) | **parked** | probe (fix 31) | — |
| 42 | LEADERS: RETURN (1920x1080) | **works** | probe (fix 31) | — |
| 43 | RESEARCH: the sidebar's research row opens the research panel, and back (1920x1080) | **works** | probe (fix 31) | research_change/010_091454_opened_from_sidebar_LIVE_1920x1080_hd.png |
| 44 | GAME menu: LOAD dialog opens and CANCEL returns (1920x1080) | **works** | probe (fix 31) | game_menu_load/011_091457_opened_LIVE_1920x1080_hd.png |
| 45 | GAME menu: SAVE dialog opens and CANCEL returns (1920x1080) | **works** | probe (fix 31) | game_menu_save/012_091500_opened_LIVE_1920x1080_hd.png |
| 46 | help: a right click opens the help popup, a click closes it (1920x1080) | **works** | probe (fix 31) | help_popup/013_091503_right_click_sidebar_LIVE_1920x1080_hd.png |
| 47 | COLONIES: hover scans a colony, a sort key sends, RETURN (1920x1080) | **works** | probe (fix 31) | colony_summary/001_091606_hover_second_row_LIVE_1920x1080_hd.png, colony_summary/002_091607_sort_population_LIVE_1920x1080_hd.png |
| 48 | NEW GAME opens from GAME -> NEW GAME -> YES (1920x1080) | **works** | probe (fix 31) | new_game/001_091722_opened_LIVE_1920x1080_hd.png |
| 49 | NEW GAME: difficulty cycles through every value, its picture visible at each (1920x1080) | **works** | probe (fix 31) | new_game/002_091726_after_cycling_difficulty_LIVE_1920x1080_hd.png |
| 50 | NEW GAME: galaxy_size cycles through every value, its picture visible at each (1920x1080) | **works** | probe (fix 31) | new_game/003_091729_after_cycling_galaxy_size_LIVE_1920x1080_hd.png |
| 51 | NEW GAME: galaxy_age cycles through every value, its picture visible at each (1920x1080) | **works** | probe (fix 31) | new_game/004_091731_after_cycling_galaxy_age_LIVE_1920x1080_hd.png |
| 52 | NEW GAME: players cycles through every value, its picture visible at each (1920x1080) | **works** | probe (fix 31) | new_game/005_091736_after_cycling_players_LIVE_1920x1080_hd.png |
| 53 | NEW GAME: tech_level cycles through every value, its picture visible at each (1920x1080) | **works** | probe (fix 31) | new_game/006_091738_after_cycling_tech_level_LIVE_1920x1080_hd.png |
| 54 | NEW GAME: checkbox tactical_combat toggles and shows its state (1920x1080) | **works** | probe (fix 31) | new_game/007_091740_toggled_tactical_combat_LIVE_1920x1080_hd.png |
| 55 | NEW GAME: checkbox random_events toggles and shows its state (1920x1080) | **works** | probe (fix 31) | new_game/008_091741_toggled_random_events_LIVE_1920x1080_hd.png |
| 56 | NEW GAME: checkbox antarans_attack toggles and shows its state (1920x1080) | **works** | probe (fix 31) | new_game/009_091743_toggled_antarans_attack_LIVE_1920x1080_hd.png |
| 57 | NEW GAME: CANCEL returns (1920x1080) | **works** | probe (fix 31) | main_menu/010_091743_after_new_game_cancel_LIVE_1920x1080_hd.png |
| 58 | SELECT RACE opens from New Game's ACCEPT (1920x1080) | **works** | probe (fix 31) | select_race/001_091905_opened_LIVE_1920x1080_hd.png |
| 59 | SELECT RACE: the right box follows the race under the pointer (1920x1080) | **works** | probe (fix 31) | select_race/002_091906_hover_race_0_LIVE_1920x1080_hd.png, select_race/003_091906_hover_race_12_LIVE_1920x1080_hd.png |
| 60 | SELECT RACE: Custom Race opens (1920x1080) | **works** | probe (fix 31) | select_race/004_091908_after_custom_click_LIVE_1920x1080_hd.png |
| 61 | CUSTOM RACE opens after a portrait (1920x1080) | **works** | probe (fix 31) | custom_race/005_091909_opened_LIVE_1920x1080_hd.png |
| 62 | CUSTOM RACE: an option click (1920x1080) | **works** | probe (fix 31) | custom_race/001_091952_option_clicked_LIVE_1920x1080_hd.png |
| 63 | CUSTOM RACE -> ESC, then CANCEL back to the main menu (1920x1080) | **broken** | probe (fix 31) | select_race/003_092156_back_to_main_menu_LIVE_1920x1080_hd.png |
| 64 | SELECT RACE: ESC goes back (1920x1080) | **broken** | probe (fix 31) | select_race/001_092308_after_select_race_esc_LIVE_1920x1080_hd.png |
| 65 | load SAVE4 from the main menu's Load dialog | **works** | probe (fix 31) | load/001_092355_main_menu_load_dialog_LIVE_1920x1080_hd.png, galaxy_map/002_092358_after_load_slot4_LIVE_1920x1080_hd.png |
| 66 | galaxy: GAME plate click opens the menu (2576x1432) | **works** | probe (fix 31) | game_menu/001_092417_opened_by_plate_LIVE_2576x1432_hd.png |
| 67 | galaxy: GAME menu RETURN (2576x1432) | **works** | probe (fix 31) | — |
| 68 | galaxy: nav COLONIES opens its screen and comes back (2576x1432) | **works** | probe (fix 31) | colony_summary/002_092420_opened_from_colonies_LIVE_2576x1432_hd.png |
| 69 | galaxy: nav PLANETS opens its screen and comes back (2576x1432) | **works** | probe (fix 31) | planets/003_092422_opened_from_planets_LIVE_2576x1432_hd.png |
| 70 | galaxy: nav FLEETS opens its screen and comes back (2576x1432) | **works** | probe (fix 31) | fleets/004_092425_opened_from_fleets_LIVE_2576x1432_hd.png |
| 71 | galaxy: nav LEADERS opens its screen and comes back (2576x1432) | **works** | probe (fix 31) | leaders/005_092426_opened_from_leaders_LIVE_2576x1432_hd.png |
| 72 | galaxy: nav RACES opens its screen and comes back (2576x1432) | **works** | probe (fix 31) | races/006_092428_opened_from_races_LIVE_2576x1432_hd.png |
| 73 | galaxy: nav INFO opens its screen and comes back (2576x1432) | **works** | probe (fix 31) | info/007_092429_opened_from_info_LIVE_2576x1432_hd.png |
| 74 | galaxy: star click (2576x1432) | **works** | probe (fix 31) | galaxy_map/001_092435_star_click_Hastur_LIVE_2576x1432_hd.png + native |
| 75 | galaxy: star box closes (2576x1432) | **works** | probe (fix 31) | — |
| 76 | galaxy: fleet click (2576x1432) | **works** | probe (fix 31) | galaxy_map/002_092440_fleet_click_LIVE_2576x1432_hd.png + native |
| 77 | galaxy: fleet box closes (2576x1432) | **works** | probe (fix 31) | — |
| 78 | PLANETS: sort by Minerals, RETURN (2576x1432) | **works** | probe (fix 31) | planets/002_092458_sort_minerals_clicked_LIVE_2576x1432_hd.png |
| 79 | FLEETS: next fleet, RETURN (2576x1432) | **works** | probe (fix 31) | fleets/004_092501_next_fleet_clicked_LIVE_2576x1432_hd.png |
| 80 | LEADERS: opens, both tabs (2576x1432) | **works** | probe (fix 31) | leaders/005_092504_tab_ship_LIVE_2576x1432_hd.png, leaders/006_092505_tab_colony_LIVE_2576x1432_hd.png |
| 81 | LEADERS: a leader click (2576x1432) | **works** | probe (fix 31) | leaders/007_092506_leader_row_clicked_LIVE_2576x1432_hd.png |
| 82 | LEADERS: hire popup (2576x1432) | **parked** | probe (fix 31) | — |
| 83 | LEADERS: RETURN (2576x1432) | **works** | probe (fix 31) | — |
| 84 | RESEARCH: the sidebar's research row opens the research panel, and back (2576x1432) | **works** | probe (fix 31) | research_change/008_092511_opened_from_sidebar_LIVE_2576x1432_hd.png |
| 85 | GAME menu: LOAD dialog opens and CANCEL returns (2576x1432) | **works** | probe (fix 31) | game_menu_load/009_092516_opened_LIVE_2576x1432_hd.png |
| 86 | GAME menu: SAVE dialog opens and CANCEL returns (2576x1432) | **works** | probe (fix 31) | game_menu_save/010_092521_opened_LIVE_2576x1432_hd.png |
| 87 | help: a right click opens the help popup, a click closes it (2576x1432) | **works** | probe (fix 31) | help_popup/011_092524_right_click_sidebar_LIVE_2576x1432_hd.png |
| 88 | COLONIES: hover scans a colony, a sort key sends, RETURN (2576x1432) | **works** | probe (fix 31) | colony_summary/001_092552_hover_second_row_LIVE_2576x1432_hd.png |
| 89 | SETTINGS: Panel glass live, both ends and Reset (2576x1432) | **works** | probe (fix 31) | game_menu_settings/002_092601_glass_see_through_LIVE_2576x1432_hd.png, game_menu_settings/003_092604_glass_solid_LIVE_2576x1432_hd.png |
| 90 | NEW GAME opens from GAME -> NEW GAME -> YES (2576x1432) | **works** | probe (fix 31) | new_game/001_092633_opened_LIVE_2576x1432_hd.png |
| 91 | NEW GAME: difficulty cycles through every value, its picture visible at each (2576x1432) | **works** | probe (fix 31) | new_game/002_092637_after_cycling_difficulty_LIVE_2576x1432_hd.png |
| 92 | NEW GAME: galaxy_size cycles through every value, its picture visible at each (2576x1432) | **works** | probe (fix 31) | new_game/003_092641_after_cycling_galaxy_size_LIVE_2576x1432_hd.png |
| 93 | NEW GAME: galaxy_age cycles through every value, its picture visible at each (2576x1432) | **works** | probe (fix 31) | new_game/004_092643_after_cycling_galaxy_age_LIVE_2576x1432_hd.png |
| 94 | NEW GAME: players cycles through every value, its picture visible at each (2576x1432) | **works** | probe (fix 31) | new_game/005_092648_after_cycling_players_LIVE_2576x1432_hd.png |
| 95 | NEW GAME: tech_level cycles through every value, its picture visible at each (2576x1432) | **works** | probe (fix 31) | new_game/006_092651_after_cycling_tech_level_LIVE_2576x1432_hd.png |
| 96 | NEW GAME: checkbox tactical_combat toggles and shows its state (2576x1432) | **works** | probe (fix 31) | new_game/007_092653_toggled_tactical_combat_LIVE_2576x1432_hd.png |
| 97 | NEW GAME: checkbox random_events toggles and shows its state (2576x1432) | **works** | probe (fix 31) | new_game/008_092655_toggled_random_events_LIVE_2576x1432_hd.png |
| 98 | NEW GAME: checkbox antarans_attack toggles and shows its state (2576x1432) | **works** | probe (fix 31) | new_game/009_092656_toggled_antarans_attack_LIVE_2576x1432_hd.png |
| 99 | NEW GAME: CANCEL returns (2576x1432) | **works** | probe (fix 31) | main_menu/010_092657_after_new_game_cancel_LIVE_2576x1432_hd.png |
| 100 | SELECT RACE opens from New Game's ACCEPT (2576x1432) | **works** | probe (fix 31) | select_race/001_092702_opened_LIVE_2576x1432_hd.png |
| 101 | SELECT RACE: the right box follows the race under the pointer (2576x1432) | **works** | probe (fix 31) | select_race/002_092703_hover_race_0_LIVE_2576x1432_hd.png, select_race/003_092704_hover_race_12_LIVE_2576x1432_hd.png |
| 102 | SELECT RACE: Custom Race opens (2576x1432) | **works** | probe (fix 31) | select_race/004_092705_after_custom_click_LIVE_2576x1432_hd.png |
| 103 | CUSTOM RACE opens after a portrait (2576x1432) | **works** | probe (fix 31) | custom_race/005_092707_opened_LIVE_2576x1432_hd.png |

(`live/results.jsonl` has each step's expected and observed text in
full. Evidence paths are relative to `live/`.)

## What was parked

A1 open fix 31 not applied; A2 the idle inhibitor; A3 the desktop's
full-screen game during the run. B1 the measured look; B2 which boxes
are dense; B3 table stripes over glass; B4 no softening; B5 corner lines
off; B6 popups show the background, not the map; B7 the second mockup
unused. C1 the live test on the fix-31 build; C2 the invisible modal on
the galaxy map; C3 Select Race's ESC; C4 the main menu's Load dialog in
HD, and `gameload` without the centred variant; C5 `MOX.SET`; C6 the
fourth tech level, the 2160p Select Race text, keys in the fallback
view; C7 hiring a leader.

## What Data should look at first

1. **`MOX.SET`** (C5): whether the reconstruction is what you had —
   START a game with CONTINUE once and see that it offers your own game.
2. **The invisible modal** (C2): `live/state/*modal*_native.png` beside
   `_hd.png` — a player in HD cannot answer the turn's colony-base
   question. The first thing to fix after this order.
3. **Glass**: `screens/select_race_beside_mockup_offline.png`, then
   `tints/` and `slider/`.
4. **Open fix 31** (A1): the patch, and whether to apply it — it is what
   made the live test possible behind your game.

## Push — DONE, 26 September 2026 (recorded by work order 175)

Data asked for it after 174 closed. Gates: working tree clean, a fresh
clone with `python tools/setup.py` 320 green, the pre-push hook's full
suite 320 green. `git push origin main`: **`214cafb..cb70745`** (174's
three commits: A `2e3203e`, B `8742339`, C `cb70745`). Remote after it
identical to the local refs: `main` at `cb70745`, `colony-free-bands`
and `rescue/ties-abend` unchanged.
