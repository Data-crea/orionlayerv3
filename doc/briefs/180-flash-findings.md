# Work order 180, part A1 — what flashes, where, and why

Measured 26 September 2026, 22:57–23:20, before anything was changed.
Evidence: `~/orionlayer-fixtures/evidence/work_order_180/` (the `A1_*`
folders, one per walk; `A1_flash_table.md`; `A1_engine_window/`).

## The answer in three lines

- **Data's flash is the Fleets screen.** On entering it from the galaxy
  map, the window presents ONE frame of the game's own picture (still the
  galaxy map, because the game has not drawn its fleet screen yet) with
  OrionLayer's own fallback sentence in the left pillarbox, for 0.09–0.16 s.
  It happened on 11 of 14 entries. The "description on the left" is not a
  panel of any original screen: it is `core/fallbacknote.py` (work order
  139 D), which `band()` puts in the LEFT bar because at 4:3 in a wide
  window both bars are equal and the left one wins the tie.
- Two more transitions present native frames, without a sentence: the
  engine's **main-menu opening animation** (up to 1.29 s, at startup) and
  the **load of a saved game** (one frame standing 0.49–0.52 s through the
  load's silence).
- **The engine's own window is not a source.** Over the start, the
  intro-skip key and 29 transitions, the X server saw it mapped once and
  never raised, re-mapped or focused afterwards.

## How it was measured

**The instrumentation** (`core/frametrace.py`, committed with this file).
Every frame `App._render` presents is recorded with the game's screen id,
its field count, the SOURCE — `hd` (an HD screen drew it), `net` (the
game's picture) or `fill` (neither) — which WAY into the game's picture it
was (`no_screen`: decision 22's id with no HD screen; `hand_over`: a screen
that knows the id said `wants_original()`; `f12`: the player's own mode),
the HD screen on top, the note's sentence, and `time.monotonic()`. Off
unless `ORIONLAYER_FRAME_TRACE` is set (the debug input's rule); one
`is None` test per frame otherwise. Three smoke checks hold it (090n).

**The second verdict.** The trace records a branch, and work order 129
once reported a flag as an observation. So `tools/flash_walk.py` also
compares, on every frame, nine points inside the 4:3 picture area with the
product's own rendering of the game's picture (work order 166 A's method,
`entry_glimpse.shows_picture`). **Over 9,247 frames the two verdicts never
disagreed.**

**The walk** (`tools/flash_walk.py`). The real `main.App`, driven through
its front door — clicks on the HD buttons, keys into the HD window, ESC
out (the screens forward it as the original's own way back) — and the
registry read from the running App (`dispatcher.screen_map`), not from a
list. The one step that is not an HD input is the load of SAVE4, which
goes through `livesend` against the list read at that moment, as
`gameload.py` does. A transition's watch ends when the target screen has
drawn 30 frames of its own in a row.

| walk | size | what |
|---|---|---|
| `A1_walk_1920x1080` | 1920x1080 | pre-game leg, then the in-game leg once |
| `A1_repeat_1920x1080` | 1920x1080 | the in-game leg five times (a second run overwrote the first, see `README_repeat_logs.txt`) |
| `A1_x11window_1920x1080` | 1920x1080 | the whole walk with a REAL x11 window, for part 3 |
| `A1_walk_2576x1432` | 2576x1432 | the in-game leg once |
| `A1_full_2576x1432` | 2576x1432 | the whole walk |
| `A1_repeat_2576x1432` | 2576x1432 | the in-game leg five times |

276 transition walks in all; every run's guard verified afterwards (see
the progress file).

## The registry, and what was walked

`dispatcher.screen_map` at run time: galaxy_map 0, fleets 4, races 6,
game_menu 8 (overlay), info 9, main_menu 10, new_game 13, colony_summary
20, leaders 29, planets 32, research_change 36 (overlay), custom_race 50,
select_race 51, research_select 53 — and empire_identity, a sub-screen
with no id. Walked into and back out of: **all of them except
research_select (53)**, which the engine reaches only when a research
project completes during TURN, and TURN writes SAVE10 (not a scratch
slot). A2's replay check covers it from a recorded transition shape.
The galaxy map's own boxes were walked through the system window on the
home star; the GAME menu overlay and change mode through their HD entries.

## The table

Only rows with native frames; every other one of the 276 walks presented
none. Full table: `A1_flash_table.md`.

| transition | size | walks | with native frames | native frames | longest | way in |
|---|---|---:|---:|---:|---:|---|
| galaxy_map -> fleets | 1920x1080 | 7 | 7 | 7 | 0.141 s | hand_over |
| galaxy_map -> fleets | 2576x1432 | 7 | 4 | 4 | 0.155 s | hand_over |
| startup -> main_menu | 2576x1432 | 1 | 1 | 62 | 1.289 s (after HD's first frame) | hand_over |
| main_menu -> load dialog | 2576x1432 | 2 | 1 | 1 | 0.160 s | hand_over |
| load dialog -> galaxy_map (SAVE4) | 1920x1080 | 2 | 2 | 3 | 0.488 s | no_screen |
| load dialog -> galaxy_map (SAVE4) | 2576x1432 | 2 | 2 | 2 | 0.523 s | no_screen |

"Longest" is how long the native picture stood on screen: from the first
native frame to the frame that replaced it. A single native frame stands
as long as the NEXT frame takes, which is why one frame is 0.09–0.16 s on
Fleets (the fleet screen's first HD frame is slow to build) and half a
second on the load (the engine is silent while it loads).

## Each flashing transition

### 1. galaxy_map -> fleets — Data's flash

- **Source:** the safety net inside the HD window (`hand_over`), with the
  fallback sentence "The game is showing no fleet. `_small_ship_stack_ptr`
  is -1, …" in the left pillarbox. Picture:
  `A1_repeat_1920x1080/005_FLASH_galaxy_map-fleets_hd.png`.
- **Frames:** 1 per entry, 11 of 14 entries, 0.089–0.155 s.
- **Cause in the code.** The first snapshot at screen 4 still carries the
  galaxy map's 23 fields (`Screen_Control_` ticks before it dispatches,
  mox2.cpp:40-41) AND a fleet block whose stack is still -1.
  `screens/fleets/fltwire.View._read` tests the stack FIRST
  (`fltwire.py:359`, state `NO_STACK`) and the "list is not ours yet"
  transient only after it (`fltwire.py:390`, state `WAITING`). So the
  transient is judged a refusal, `FleetsScreen.wants_original()`
  (`screens/fleets/screen.py:213`) is true for that one snapshot, and
  `main.App._showing_original` takes the hand-over branch
  (`top.wants_original()`). Work order 142 A made WAITING the exception
  for exactly this moment; the stack test in front of it lets the moment
  through whenever the block is also still empty — timing, which is why
  it is 11 of 14 and not 14 of 14.

### 2. startup -> main_menu (and main_menu -> load dialog pressed during it)

- **Source:** the safety net inside the HD window (`hand_over`), no
  sentence (the main menu gives no reason), the game's picture of its
  menu animation. Pictures: `A1_full_2576x1432/001_FLASH_startup-main_menu_*`.
- **Frames:** 62 frames, 1.289 s, AFTER HD's first frame; once more for
  1 frame (0.160 s) when a walk pressed L while the animation still ran.
  Not at 1920x1080 only because those walks connected after it had ended.
- **Cause in the code.** `MAINMENU` plays its opening animation in an input
  loop with its own list (mainmenu.cpp:48-59): six 15x15 hidden fields
  with the hotkeys C S L M H Q, an ESC hot key and a full-screen ESC field.
  The main menu's modal net (`screens/main_menu/screen.py:164-176`,
  `core/modalnet.Net`) knows only the finished menu (`_own_list`, the NEW
  GAME field of mainmenu.cpp:137) and the Load dialog with slots, so the
  animation's list is "a modal HD has no view for"; after `SETTLE` = 5
  snapshots (`modalnet.py:32`) `wants_original()` is true until the menu's
  own list arrives. The log names the shape: `8 fields: t7/C/15x15@10,20 …
  t7/0x1b/639x479@0,0`.

### 3. load dialog -> galaxy_map

- **Source:** the safety net inside the HD window (`no_screen`), no
  sentence.
- **Frames:** 1–2 per load, standing 0.49–0.52 s.
- **Cause in the code.** After a slot row is activated the engine reports
  SCREEN_REPORTS (39) with an EMPTY field list for one or two snapshots,
  then goes silent inside `FILEDEF::Load_Game_`, and the next snapshot is
  the galaxy map (`Reports_Screen_` writes SCREEN_MAIN before any report
  runs, mainscr2.cpp:119). 39 has no HD screen, so
  `Dispatcher.update_from_game` takes decision 22's fallback
  (`core/dispatcher.py:227-234`: `use_original = True`), and the picture
  then stands through the whole silence. There is nothing on that picture
  a player could answer — the list is empty.

## Part 3 — the engine's own window

**Method.** `tools/xwatch.py`: both programs are X11 clients of Xwayland
here (SDL's x11 driver), so the X server itself was the observer — root
PropertyNotify for `_NET_ACTIVE_WINDOW`, `_NET_CLIENT_LIST` and
`_NET_CLIENT_LIST_STACKING`, and Map/Unmap/Configure of every top-level —
recorded through an engine start with the intro-skip key and the whole
walk with a real x11 HD window (`A1_engine_window/`).

**What it saw.**
- The engine's window is mapped once, 0.15 s after the start
  (`platform.cpp:1408`, `SDL_ShowWindow` — `ext::Init` sets
  `g_hide_window` later, from mox2.cpp:382, decision 39's correction).
- **The intro-skip key** (`xdotool key --window`, i.e. `XSendEvent` to the
  engine's window by id) caused no restack, no configure, no map and no
  focus change.
- **Screen changes:** over 29 transitions and 60 s, no event at all on
  the engine's window — no restack, no map or unmap, no focus. OrionLayer's
  window stayed the top X client throughout. The engine's source agrees:
  the only other window call is the fullscreen toggle on real input
  (`platform.cpp:398`); nothing raises, focuses or re-shows it.
- **Startup:** the engine's window is the top X client from its start
  until OrionLayer's window maps — and once more for **72 ms** while SDL
  recreates the pygame window (mapped, unmapped, mapped again: +6.198,
  +6.241, +6.313 s). That recreation is SDL's x11 window setup, not
  OrionLayer code: a bare `pygame.display.set_mode` does the same
  (reproduced three times, scratch).

**What it cannot see**, written into every record's header: Wayland-native
surfaces (the lock screen, a Wayland terminal) have no X window, so "on
top" is among X clients only; whether the compositor PRESENTS a window is
not an X property; and **the screen was locked during this run**, so
mutter reported focus as none throughout — focus behaviour on an unlocked
desktop was not observable and is one of the steps for Data.

**What it excluded.** The engine window coming forward during the intro
skip or during any screen change. It remains visible BEFORE OrionLayer's
window exists (by the engine's design), which is exposure at startup, not
a flash during play; it shows the game's main menu with no sentence, so it
is not what Data described.

## Part 4 — the description on the left

No original screen involved here shows a description panel on the left:
the flash frame's native half is the GALAXY MAP (`005_FLASH_…_native.png`).
The text is `core/fallbacknote.render`, drawn outside the picture in the
band `fallbacknote.band()` chooses — the left pillarbox, because at 16:9
the two bars are equal and `px >= right` picks the left. The screens that
can draw such a note are the ones with a `fallback_reason()`: fleets,
races, leaders, info and the two research screens. **Only Fleets
flashed.** The two other flashing transitions draw no note at all (the
main menu and decision 22's fallback give no reason).

## What A2 has to change, from this

1. A known screen's hand-over is let through on its FIRST snapshot. The
   Fleets case is one ordering inside one screen, but the shape — a
   transient judged a refusal — is the general one, and 142 A and 166 A
   each fixed an instance of it screen by screen.
2. An id with no HD screen and an EMPTY list is shown at once, though
   there is nothing on it to answer.
3. A modal net treats a screen's own transitional list as a modal (the
   main menu's opening animation).
