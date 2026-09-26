# Work order 180 — progress

Unattended run, 26 September 2026, base `5ecba52` (= origin/main, 354
checks). Evidence root: `~/orionlayer-fixtures/evidence/work_order_180/`.

## Before part A1

- Read: `doc/v3_fundament.md` (the index), all three `principles-` parts
  (06, 07, 08), and the parts this order touches: 02 (the orion2re
  boundary — decisions 22, 39, 59, 60, 65), 04 (markings, decisions 61, 71)
  and 09 (orion2re facts, the live-run file list).
- 22:51: no orion2re and no OrionLayer client running (`ps`). The desktop
  had been idle for 66 s (`org.gnome.Mutter.IdleMonitor.GetIdletime`),
  screen not locked — Data was at the desk minutes before. There was
  nothing running to leave or close; every engine in this order is started
  by this session and closed by it.

## A1. Measure before fixing — **DONE** (nothing fixed)

- **Instrumentation:** `core/frametrace.py` — every presented frame with
  screen id, field count, source (`hd` / `net` / `fill`), the way into the
  game's picture (`no_screen` / `hand_over` / `f12`), the HD screen on top,
  the note and a monotonic timestamp; off unless `ORIONLAYER_FRAME_TRACE`
  is set (a value other than `1` is also a JSON-lines file). `main.py`
  records the branch `_render` takes, before it takes it
  (`frametrace.record_app_frame`); `_showing_original` notes which way in.
- **Walk:** `tools/flash_walk.py` (front door, registry from the running
  App, trace AND pixel verdict per frame, a picture of the first native
  frame of each transition), `tools/flash_table.py` (the table),
  `tools/xwatch.py` (the X server as observer, part 3).
- **Live runs** (engines 58800, 59555, 60021, 60291 — all started and
  closed by this session, SIGTERM; `--blanked-ok`, the screen was blanked
  and locked from 22:57): 276 transition walks at 1920x1080 and 2576x1432,
  9,247 frames, trace and pixels never disagreeing. SAVE4 loaded (scratch)
  in each; nothing saved; SAVE1-11 identical in every run.
- **Every guard** (`live_guard/20260926_225659`, `_231033`, `_231423`,
  `_231747`) reported exactly ONE change: `game/MOX.SET`, one byte at
  offset 21 (10 → 3, the active save slot pointing at SAVE4), written at
  the moment of the LOAD (mtime 23:11:24 = the walk's load). Restored with
  `--restore` each time, then verified identical. So loading a slot writes
  MOX.SET too — one writer more than part 09's list ("after every save and
  when a loaded game is left for New Game"); recorded here, the list is
  amended with A2's documentation.
- **One walk misfired and sent one key** (try 2 at 22:59): it decided on
  the screen id before the first snapshot had arrived (-1), skipped the
  load and pressed ESC into the MAIN MENU (no field, no game state touched;
  the menu stayed). The walk now waits for the first snapshot and refuses
  the in-game leg unless the galaxy map's own list is on the wire. A zsh
  loop meant to repeat at 2576 ran at 1920 (no word splitting); its folder
  overwrote the first 1920 repeat — named in the evidence's
  `README_repeat_logs.txt`, and the 2576 repeat was then run properly.
- **Findings:** `doc/briefs/180-flash-findings.md`. Data's flash is the
  Fleets entry (1 native frame + the fallback sentence in the left
  pillarbox, 11 of 14 entries, ≤0.155 s): `fltwire.View._read` judges the
  first snapshot a refusal (NO_STACK before WAITING). Two more: the main
  menu's opening animation (1.29 s, the modal net takes its list for a
  modal) and the load (screen 39 with an empty list, 0.5 s through the
  load's silence). The engine's window is not a source (never raised or
  focused after its first map; screen locked, so focus unobservable).
- Checks: 090n (three). **354 → 357.** `main.py` 330 → 341 code lines,
  its exception entry updated with the reason.

## A2. Fix it — **DONE, live-verified**

- **One place:** `core/handover.py`'s `Gate`, asked by
  `main.App._showing_original` (`_gated`) for every way into the game's
  picture. An id with no HD screen is shown at once when its list holds a
  field to answer, and HELD while the list is empty (the load's 39). A known
  screen's hand-over is HELD — the window keeps the last HD frame, or the
  universal background (`handover.render_hold`), and takes no click, key or
  right button — until the data arrives; after `HOLD` = 36 snapshots it
  falls back ONCE, logged `FALLBACK`, counted in `Gate.failures`. A modal
  net's hand-over (`ScreenBase.handover_is_modal`: main menu, select race,
  galaxy map) is held the same way and then shown, not failed. Counted in
  snapshots (`client.stats["state"]`), so a load's silence never runs it
  out. No screen was changed to fix its own case: Fleets' ordering, the
  main menu's net and the dispatcher's 39 are untouched, all three are
  under the gate. DEVIATION `hold_last_frame`, in the module, the status
  document and 090o.
- **The engine window:** not a cause (A1) — nothing to fix client-side.
  Its visibility at startup is parked (item 3.1) with the default "no
  change".
- **Live, after** (engines 62004 and 62162, guards `20260926_234659` and
  `_235026`; the full walk — pre-game, load of SAVE4, the in-game leg five
  times, the system window — at 1920x1080 and 2576x1432): **202
  transitions, 0 with native frames**, 0 fallbacks; 6,901 frames, trace and
  pixels agreeing on every one. Holds: 1 snapshot entering Fleets, 2 through
  the load, 24 through the main menu's opening animation (bound 36). Each
  guard: MOX.SET's load byte only, restored, then identical. Evidence:
  `A2_after_*`, `A2_flash_table.md`.
- **Before / after** (`A1_flash_table.md`, `A2_flash_table.md`):

  | transition | size | before: walks with native frames | after |
  |---|---|---|---|
  | galaxy_map -> fleets | 1920x1080 | 7 of 7 (≤0.141 s) | 0 of 5 |
  | galaxy_map -> fleets | 2576x1432 | 4 of 7 (≤0.155 s) | 0 of 5 |
  | startup -> main_menu | 1920x1080 | 0 of 1 (connected after the animation) | 0 of 1 (held 24 snapshots) |
  | startup -> main_menu | 2576x1432 | 1 of 1 (62 frames, 1.29 s) | 0 of 1 |
  | main_menu -> load dialog | 1920x1080 | 0 of 2 | 0 of 1 |
  | main_menu -> load dialog | 2576x1432 | 1 of 2 (0.160 s) | 0 of 1 |
  | load dialog -> galaxy_map | 1920x1080 | 2 of 2 (≤0.488 s) | 0 of 1 |
  | load dialog -> galaxy_map | 2576x1432 | 2 of 2 (≤0.523 s) | 0 of 1 |
  | every other transition | both | 0 of 252 | 0 of 186 |
  | **all** | | **17 of 276** | **0 of 202** |

- **The replay check (090o):** `tools/flash_fixture.py` wrote
  `tools/fixtures/transitions_180.json` from the after-walks — 122 distinct
  transitions, one row per snapshot, the inputs the gate reads (what the
  engine and the screens said, not what the gate did). 090o replays them:
  no native frame anywhere in any transition, no fallback, every registry
  screen (`screens_loader.discover_screens`) a target — research_select as
  the one SYNTHETIC transition, because only TURN reaches 53 — and, run
  through a gate that holds nothing, the three A1 flashes come back.
- **Existing checks adjusted, not weakened:** 048 (a fallback says why)
  holds the gate open (`hold=0`) and counts the report's log lines, not the
  gate's; 061's science-room fixture (52) carries the ESC hot key its real
  list always has, because an EMPTY list is now a held transition.
- **Also found and written down:** loading a slot rewrites MOX.SET
  (`LOADSAVE` → `Save_Session_Related_Settings_`, loadsave.cpp:357-359,
  :1044) — part 09's list of writers amended.
- **The rule as a proposed decision:** `180-parked-for-data.md` item 2,
  number left free.
- Checks: 090o (four). **357 → 361.**
