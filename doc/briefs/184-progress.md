# Work order 184 — progress

Unattended run, 27 September 2026, base `5b24070` (= origin/main, 381
checks). orion2re `orionlayer-local` `4bf152e4`, its three untracked files
(`mox.set`, `racesel_custom_screen_id.patch`, `src.zip`) left alone.
Evidence root: `~/orionlayer-fixtures/evidence/work_order_184/`.

## Before part 1

- Read: `doc/v3_fundament.md` (the index), all three `principles-` parts
  (06, 07, 08) in full, and the parts this order touches: 09 (live runs,
  the virtual display, the files a run writes) and 02 (the boundary; the
  hand-over). Also 182's and 183's progress, `core/handover.py`,
  `core/researchscreen.py`, `core/researchstate.py`, the dispatcher, and
  the engine's own side of the switch (`mainscr_main.cpp:697-713`,
  `mox2.cpp:41`, `tech.cpp:111-395`, `fields.cpp:158-185`, `timer.cpp`).
- 19:20: no orion2re and no OrionLayer client running.
- **Which screen "the research screen" is**: the galaxy map's research
  window opens CHANGE mode, wire id 36 (`screens/research_change/`), an
  overlay over the HD galaxy map. The turn-start prompt is SELECT mode,
  wire id 53 (`screens/research_select/`); both are
  `core.researchscreen.ResearchPanelScreen`.

## Part 1 — measure where the time goes — **DONE**

1. **Instrumentation**: `core/entrytiming.py` (new), switched on by
   `ORIONLAYER_ENTRY_TIMING` (`1` in memory, else a JSON-lines file;
   `ORIONLAYER_ENTRY_PROFILE=<dir>` adds `cProfile` around phase (d)).
   Off, `open` returns None and NOTHING is wrapped — the hooks are
   installed by wrapping the app's `_handle_events` / `_update` /
   `_render`, the client's `_send_message` / `_handle_message` and the
   research screens' `enter` / `update` / `render` / `on_resize` on the
   instance, so the product's loop carries no test for it; `main.App` gains
   one assignment and an import (369 → 371 code lines, the list in
   `v3_projektstatus.md` updated). Phases (a)-(e) as the order names them,
   consecutive by construction, with (d) the research screen's own calls
   (first entry and later ones apart) and `d_ready` its part between the
   list and the render; snapshots, field lists and a digest of every
   visual per entry. **Check 090w** (new): off by default and nothing
   replaced; `main.App` refers to it in one line; on, a stand-in entry
   through the three paths gives phases that add up to the total, a
   second entry is "later", a left screen ends an entry unreached —
   shown red by a mutation (`open` ignoring the switch: "on by default"),
   green after the restore, caches cleared. **Checks 381 → 382.**
2. **The driver**: `tools/research_timing.py W H` (new) — the product's
   loop paced by `app.clock.tick(60)` as `main.App.run`, SAVE4 loaded from
   the main menu through the flash walk's loader, per entry an HD click on
   the research window, 20 frames of panel, ESC, 60 frames of map; the
   frame trace on (native frames per entry); the raw payloads of the
   settled panel kept for the offline harness. No research row is ever
   activated (open fix 23).
3. **Xvfb** (`:91`, engine PID 72428, started 19:33:40 by
   `tools/engine_start.py`, guard `184_P1_1920`; `184_P1_2576` and
   `184_P1_3840` snapshotted before their runs on the same engine, SAVE4
   loaded once): 1920, 2576, 3840 — 20 entries by the research window's
   text and 5 by its icon each; 1920 again with `--profile` (4 entries).
   **89 entries, 0 native frames, 0 held frames, none lost.** The table,
   the shares and the ten most expensive calls are in
   [`184-research-timing.md`](184-research-timing.md). In short — later
   entries 685 / 728 / 872 ms (median), 80 / 75 / 66 % of it the ENGINE'S
   silence (c) of ~550 ms; first entries 1238 / 1658 / 3022 ms, the extra
   HD's first render of the panel (the HUD shapes, 19 builds of 4
   geometries) — and on every frame under the panel the galaxy map's OLED
   floor lift, a full-window additive fill (33 / 59 / 130 ms).
4. **Real desktop**, `--real-desktop "research-screen timing on the real
   display"` for the engine (PID 74936) and `ORIONLAYER_REAL_DESKTOP` with
   the same reason for the client, **19:59:43-20:01:07** (guard
   `184_P1_real`), 10 entries at 2576x1432 — Data's size as the tree records
   it (his screenshots at 2576x1432, work order 170; parked item 3); the
   window manager granted **2576x1371**. First 1610 ms, later 727 / 792 ms;
   the shares (b 18, c 73, e 9 %) are Xvfb's at 2576 within a few percent —
   **no material difference** (pygame draws in software on both).
   Only Data's Steam client was running in his session (no game), noted
   and left alone.
5. **The native floor**: on the wire the engine's picture arrives in the
   SAME snapshot as the list (no visual in between in any of the 89
   entries), so send → native panel on the wire = (b)+(c) ≈ 630-720 ms,
   no faster than HD; the engine's own window is unmapped (fix 41) and
   by the source has the panel drawn ~550 ms earlier — Part 2 measures
   that with a scratch build.
6. **Guards**: `184_P1_1920` — MOX.SET's load byte (offset 21), restored,
   verified identical; `184_P1_2576`, `184_P1_3840` — only "tree/git
   status" (this order's own uncommitted files); `184_P1_real` — MOX.SET's
   load byte restored, then "every file identical". SAVE1-9 identical and
   SAVE10/11 unchanged in every run.
7. **An incident, recorded**: the first run of the offline render harness
   (`tools/research_render.py`, Part 2's instrument) constructed `main.App`
   while this session's engine 72428 was still up, and `App.__init__`
   connected to it — the only client at that moment (the timing runs had
   ended), for the few seconds of one render; it sent no input of its own
   (the galaxy map's parking may have sent its usual zoom-out activation,
   field 9, which is safe). The harness now replaces `App._connect` so it
   CANNOT connect, and asserts it; the engine was stopped by PID and the
   guards verified before anything else ran.

## Part 2 — faster where the measurement says it pays — **DONE: three HD changes, pixel-identical; open fix 42 written, proved and parked**

The instrument first: `tools/research_render.py` (new) renders change mode
offline from the raw wire payloads Part 1 recorded (`fixture_36`, in the
evidence folder — the player's data), the real `main.App` with the clock
frozen (the map animates) and its `_connect` replaced so it CANNOT reach an
engine; one process per size (the caches are module-global), the path a
cache has to survive (first entry, leave, second entry, resize to each other
size and back). Baseline `render_before`: 18 renders, every render of one
size equal to every other. Each change below was measured with it and with
`tools/research_timing.py` as in Part 1.

1. **The geometry memo** (`core/hud/raster.py`, `_geometry`): a shape's
   coverage masks and blurred bands depend on the outline and widths only,
   and the research panel's 19 shapes were 4 outlines — so they are built
   once per outline and every panel composes its own colours and glass over
   them, as before. Read-only arrays; bounded by bytes (96 MB: the 3840
   frame's outline is ~70 MB and is used twice in one frame). First READY
   frame offline: 577 → 349 ms (1920), 979 → 586 (2576), 2322 → 1521 (3840).
   Renders identical. **Check 006i** (new). `core/hud/blocks.py` is not
   touched (it stands at 300 code lines).
2. **Prepared while the game is silent** (`core/researchprepare.py`, new;
   two lines in `core/researchscreen.py`, which stays at 300 code lines): in
   the WAITING state the screen draws its panel once onto a scratch surface
   — the entries are the unvalidated reconstruction, and nothing of it is
   shown (080h's with/without-overlay pixel comparison still passes) — so
   the READY frame finds the HUD panels and glass cached. Offline, with a
   wait fed first: the READY frame 46 / 74 / 154 ms, building 1 shape (the
   exit button, whose size only the list gives). Renders identical.
   **Check 080l** (new): after a wait the READY frame builds no HUD panel
   and equals the frame drawn cold, byte for byte, as it is and after each
   of a resize (2576), the frame colour, the glass slider, a box somewhere
   else, other names (language / text resolver) — each done while the cache
   is warm; once per visit; a mod folder can change only at a start
   (`usermod.init` has one caller) and the preparation writes nothing.
3. **The floor lift once per picture** (`screens/galaxy_map/floorlift.py`,
   `_lifted`): Data's `floor_lift: light` made every map frame add a colour
   to the whole window (33 / 59 / 130 ms); the picture is opaque, so the
   lifted copy blitted is the old blit + add, byte for byte. READY frame
   offline 14 / 17 / 28 ms first, 9 / 12 / 20 ms later (was 41 / 69 / 148).
   Every map frame gains. **Check 067 #14** (new) holds the equality, one
   copy per picture and step, the rebuild for a new step or a new picture of
   the same size, nothing for off; check 067 #13's assertions changed to the
   new shape (one adding place, `apply`, per floor path, before the stars).

**Pixel identity, final tree** (`render_after`): all 18 renders identical to
`render_before` — 1920 `0583eaab…`, 2576 `4065bed7…`, 3840 `2ac5711d…`
(sha256 of the RGB bytes) — and the 1920 PNG looked at: the whole panel over
the map. **No difference to explain.**

**Live, after** (Xvfb, engine 81717, guards `184_P2_1920/2576/3840`; the real
desktop 20:19:58-20:20:34, engine 82183, guard `184_P2_real`, same reason as
Part 1, granted 2576x1371). Median / maximum, ms:

| | first entry | later entries | (e) later | native frames |
|---|---|---|---|---|
| 1920 | 1238 → **637** | 685 / 720 → **636 / 685** | 40 → 7 | 0 |
| 2576 | 1658 → **679** | 728 / 794 → **638 / 688** | 66 → 10 | 0 |
| 3840 | 3022 → **1444** | 872 / 880 → **686 / 690** | 149 → 19 | 0 |
| real desktop 2576x1371 | 1610 → **679** | 727 / 792 → **683 / 684** | 69 → 17 | 0 |

At 3840 the preparation (~1.3 s) outlasts the engine's ~550 ms silence, so
(c) stretches to 1.3 s on the first entry — still half of what it was
(parked item 4). The later entries' remaining time is the engine's: (b)
64-113 ms and (c) ~550 ms.

**Startup**: `main.App()` plus its first three frames, standalone, ten runs
each from scratch copies with fresh bytecode: median 405 ms before, 401 ms
after — unchanged. (A first comparison said 537 → 406 ms: the "before"
copy's `.pyc` files were stale after `git checkout` and `-B` recompiled on
every run. Measured again with both caches rebuilt.)

**The hand-over wait (c)**: it is not the 180 gate — change mode's WAITING
state (166 A) keeps the map, the gate held no frame in any of the 255 timed
entries of this order, 0 native frames — and it
waits for nothing it does not need: the list is serialised on the SIXTH
`Get_Input_` of the research loop (the input delay), and HD needs exactly
that list to validate the panel (decision 33). No condition on the HD side
to tighten; the silence is the engine's. **The flash check and 182's stress
stay green** (below).

**The engine side — open fix 42, written, proved, parked** (entry 42 in
`doc/orion2re_open_fixes.md`, `doc/ext_input_delay_tick.patch`, reported by
`version_check`, **check 090r #5** new; parked item 1). `Get_Input_` ticks
during an input delay too; six lines, one marker. Scratch clone of
`orionlayer-local` `4bf152e4` (`$SCRATCH/orion2re_184`, commit `21a37ffb`,
never on the branch), vendors copied, `cmake --preset linux-debug
-DORION2RE_EXT=ON`, `ninja orion2re`: built, exit 0. The patch FILE applied
to a worktree at `4bf152e4` with `patch -p1 --dry-run` and `patch -p1`, no
offset, no fuzz, `fields.cpp` byte for byte the scratch commit's; compiled
alone with the build's own command (`ninja -t commands`, `-fsyntax-only`);
the control `MOX::_current_scren` refused ("»_current_scren« ist kein
Element von »MOX«"). (A first attempt read the command from
`compile_commands.json`, which lists only vendor files, and ran an empty
script — its "OK" was discarded, not reported.) Measured with it (engines
82309, 82722, 84560, all this session's, guards `184_F42_*` verified): later
entries **77 / 94 / 103 ms** (from 636 / 638 / 686), (c) 0.8 ms; the
engine's own panel on the wire ~290 ms after the click (one idle pass after
the list); flash walk 29 transitions, 0 native frames; stress 1002 inputs,
0 lost, 0 dropped; pacing main menu 6.05/s (164.7 ms), map 18.15/s, colony
18.15/s against 6.05 / 18.20 / 18.20 without; engine CPU over ten entries
5.1 % both ways.

**The same runs on the normal engine with the HD changes** (engine 83146,
guard `184_P2_flash`): flash walk at 1920, 29 transitions, **0 native
frames**; stress at 1920, 400 cycles, **1002 inputs, 0 lost, 0 dropped**
(238 s).

**Corrected in this part**: `184-research-timing.md` said the galaxy map
runs at 6.06 snapshots a second and 165 ms — the main menu's figures, copied
from 183 and not measured. The map is 18.2 a second, 55.9 ms (the pacing
probe); the brief says so where it said the other, marked as corrected, and
fundament part 09 carries the fact now.

**Guards, one lesson**: after the 3840 run MOX.SET's load byte came back
from the 2576 guard — which had been snapshotted AFTER the load, so its
"restore" put the loaded state back; the 1920 guard (taken before the engine
existed) then showed the change and restored the original, verified
identical, and against this order's first guard (`184_P1_1920`) only the
tree's own changes differ. From then on only a guard taken before its engine
was restored from.

**Checks 382 → 386** (006i, 080l, 067 #14, 090r #5), each shown red by a
mutation in a copy of the tree (the read-only flag removed; the preparation
not called: "('waiting', False)"; the lifted copy never reused: "the lift was
redone for a frame"; fix 42's status line changed) and green in this tree.
