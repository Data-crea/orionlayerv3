# Work order 182 — progress

Unattended run, 27 September 2026, base `5c5d670` (= origin/main, 375
checks). orion2re `orionlayer-local` `2097b0c6`, its three untracked files
left alone. Evidence root: `~/orionlayer-fixtures/evidence/work_order_182/`.

## Before part 1

- Read: `doc/v3_fundament.md` (the index) and all three `principles-`
  parts (06, 07, 08) — read in full in this same session for work order
  181, two hours earlier, and unchanged since (`git log` on
  `doc/fundament/` shows only 181's line in part 09); the parts this order
  touches: 09 (orion2re facts: the start hang, the live-run file list, the
  pointer), 02 (decision 39 and its correction: the engine window is shown
  before `g_hide_window`), 03 (sizing and fonts, for part 4).
- 09:55: no orion2re and no OrionLayer client running; nothing in Data's
  session to leave alone.

## Part 1 — live tests on a virtual display — **DONE, switched over**

1. **Measured** (`doc/briefs/182-virtual-display.md`, the table): on this
   machine only **Xvfb** and **`mutter --headless`** exist (no weston, no
   kwin_wayland, no cage/sway; nothing installed). Both carry the engine,
   the HD client, screenshots, `xdotool` input and the intro skip, at the
   real desktop's pacing (main menu 6.0/s, 165 ms, no hang in any start).
   Chosen: **Xvfb** — no GPU, no D-Bus, no GNOME. `mutter --headless`
   writes a `.mutter-Xwaylandauth.*` into the session directory, which
   `engine_start`'s "newest auth file" rule would then have picked for the
   REAL desktop: the real path now takes the auth file that opens `:0`.
   (The manual measurements used engines 115221 and the mutter one, both
   started and closed by this session; guard `182_p1_xvfb`, clean.)
2. **Equivalence** — the same flash walk (29 transitions: pre-game, the
   SAVE4 load, every in-game nav transition, the system window) and 181's
   colony acceptance with orders (23 transitions), each on a fresh engine,
   at 1920 and 2576, on Xvfb and on the real desktop (`--real-desktop
   "equivalence proof, work order 182 Part 1.2"`, 10:07-10:11, the desktop
   in use — the reason the order exists): 0 native frames everywhere,
   transition tables, wire values per capture and every order's result
   identical; HD pixels identical except three animations; native
   differences each explained (animation phase, the game's random default
   ruler name, and one pop icon blinking under the REAL pointer on the real
   desktop — the interference this part removes). 16 guards, each: MOX.SET's
   load byte only, restored. A last real-desktop start measured the pacing
   reference (reason: "pacing reference for the virtual-display table").
3. **Switched over.** `tools/vdisplay.py` (new): the Xvfb (`:91`..`:99`,
   private cookie, no TCP; `status|start|stop`), `engine_env`,
   `headless_clients`, `--real-desktop REASON` / `ORIONLAYER_REAL_DESKTOP`.
   `tools/engine_start.py` starts on it by default (the screen checks and
   the idle inhibitor only for the real desktop; the intro skip gets the
   same environment; `--real-desktop` without a reason is refused).
   **Every tool that loads pygame now FORCES SDL's dummy video and audio
   drivers** (18 replaced a `setdefault`, which an exported
   `SDL_VIDEODRIVER=x11` beat; `colony_move_probe.py` opened a 32x32
   window and `mod_template.py` called `pygame.init()` with none; the smoke
   runner forces too). The engine's sound goes to SDL's dummy driver on the
   virtual display.
   **Check 090s** (two): the engine's environment by default and with a
   reason; every runnable tool that loads pygame (27) imported in a fresh
   process with `SDL_VIDEODRIVER=x11` exported must leave dummy/dummy —
   it found `gameload.py`, whose forcing came only through a lazy import —
   and the escape keeps the session's drivers. Fundament part 09 and
   CLAUDE.md carry the protocol.
   **Found on the way:** the count of checks in 091 counts only modules
   that run before it; the first name of this module (`091b_`) sorted
   after and passed uncounted. 091 now asserts it is the last module
   (shown red with a probe module).
4. Fallback not needed.

**Checks: 375 → 377.** Every file this part touched that was listed as
over 300 code lines moved by one (`colony_list_preview.py` 404,
`colony_move_hd.py` 371) and is listed at the new count.

## Part 2 — keep the engine's own window hidden — **WRITTEN, PROVED, PARKED** (open fix 41)

1. **The source.** Created hidden (`SDL_WINDOW_HIDDEN`, platform.cpp:1370,
   :1374), shown at :1406-1408 unless `ext::g_hide_window`; the flag is set
   by `ext::Init()` (ext_api.cpp:1086), called from mox2.cpp:382 — after
   the platform layer, hence shown. Dependents: VSync (a hidden window must
   not wait for a VSync present — fix 31's hang), input (focus starts at 1
   and changes only on focus events: unaffected), the intro skip (a key to
   the window by id), window screenshots and `xwatch` (see an unmapped
   window), the "window shown" log line (printed either way).
2. **The fix**: `g_hide_window = true` from the start, and
   `Present_VSync_Interval_` returns 0 while hidden — two places, each
   with `OrionLayer, open fix 41.` on one line. Entry 41 and
   `doc/ext_engine_window_hidden.patch`; `version_check` reports it (not
   required); FIX_NUMBERS names it; 090r #3 holds the written form.
3. **Scratch proof** (clone `o182` of `2097b0c6`; the vendored submodules
   copied from `~/orion2re`, nothing fetched; `cmake --preset linux-debug
   -DORION2RE_EXT=ON -DORION2RE_BUILD_CONFIG_TOOL=ON`, full build 14 s):
   applies clean on a second fresh clone, builds, control
   `ext::g_hide_windw` refused. Engines 143363, 145413, 145507 (real
   session: `--real-desktop "open fix 41: the hidden window on a real
   session, work order 182 Part 2.3"`), 145578, 147866, 147992 — started
   and closed by this session, each guard clean. Window never mapped on
   Xvfb and on `:0`; READY in 1.3-1.6 s with the skip, 115.1 s without;
   pacing 6.1/s, 164.8 ms; the flash walk (29, incl. the load) and the
   colony acceptance with orders identical to the unpatched engine.
   **The intro skip needs no second route** — the key reaches the hidden
   window. What a PLAYER sees during the hidden intro is parked (item 1).
