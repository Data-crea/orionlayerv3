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
