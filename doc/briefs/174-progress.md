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
