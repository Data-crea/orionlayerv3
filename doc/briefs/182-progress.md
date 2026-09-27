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

## Part 3 — click log and stress test — **DONE: nothing lost**

1. **The click log**: `core/inputlog.py`, on only with
   `ORIONLAYER_INPUT_LOG` (`1` in memory, else a JSON-lines file); off, it
   is one `is None` test per event. `main.App` calls it around every event
   of `_handle_events` (two lines; `main.py` 363 → 369 code lines, listed).
   Per left click and key: time, screen id, the field count, the HD screen
   on top and its view's state, the outcome — "sent" when a message went to
   the engine while the input was handled (the ids listed) — or "dropped",
   with the reason in `main.App`'s own order: app key, F5 editor, not
   connected, the game's picture ("net"), a held frame ("hold"), else
   "screen sent nothing".
2. **The stress** (`tools/stress_inputs.py`, new; virtual display, SAVE4
   scratch, fresh engine per size, engines 150339, 152274, 153792 started
   and closed by this session; guards `182_P3_stress_*`, MOX.SET's load
   byte restored, clean): per size 100 Fleets open/back, 100 colony
   cycles (home star → system window → the colony's planet, `<`, `>`, ESC
   to the map), 200 popup cycles (CHANGE, Cancel):

   | size | cycles | steps | lost | inputs | dropped | inputs at an empty list | inputs during a hold | time |
   |---|---|---|---|---|---|---|---|---|
   | 1920x1080 | 400 | 1001 | **0** | 1003 | **0** | 0 | 0 | 291 s |
   | 2576x1432 | 400 | 1001 | **0** | 1003 | **0** | 0 | 0 | 368 s |
   | 3840x2160 | 400 | 1001 | **0** | 1003 | **0** | 0 | 0 | 547 s |

   Every input was sent. The frame traces hold 200 HD frames with an empty
   field list per size — every one the first frame back on the galaxy map
   (from Fleets and from the colony screen), none on the popup: **the
   popup's list never went empty in 600 cycles**, the frame 181 recorded.
3. **Evaluation: nothing lost, so the 181 case counts as outside
   interference** — Data was at the desk, and the engine's window follows
   the real pointer (a pop icon blinking under it is in part 1's
   comparison). The gate is not changed. What WOULD happen if the popup's
   list did go empty for a snapshot is parked (item 3): its view becomes a
   native box and the frame is held, so a click in that one snapshot would
   be dropped — by 180's rule, and never observed. The log stays as a
   debug tool. **Check 090u** holds it: off by default, every outcome and
   reason on a stand-in app, `main.App`'s two hooks around every event
   with no way out of the loop between them.

Also: `colony_accept.own_colony_disc` (the system window's disc of an own
colony) is shared with the stress tool now.

## Part 4 — the remaining double scaling — **DONE: two screens fixed, one general check**

1. **The search, not limited to the known screens.** By the code: every
   caller of the auto-factor `box_font_scale` (only Custom Race and Empire
   Identity called it; the Colony Summary's `colonyempire` docstring still
   named it while its caller already passed the stored scale) and every
   raw `win_h / 1080` (New Game's status line and `original_view` size in
   device pixels with one factor — correct; `fallbacknote` likewise). By
   the effect: every registered screen and both popups `hud_evidence` can
   open, rendered at 1920 and 3840, every font size by the line that chose
   it (`tools/hud_evidence.font_sites`). The list:

   | screen | element | cause | fixed |
   |---|---|---|---|
   | Custom Race | panel headers, pick rows and categories, specials, description, the Race Picks / Score bar, the message box — and the reference-space row heights and gaps they drive | `box_font_scale` (x win_h/1080) and `fs = win_h/1080` into `L.font_size` / `L.scale` / reference coordinates: 4x at 2160p (14 → 56 px, 24 → 96) | yes |
   | Empire Identity | the three input headers, the preview header and the preview's title, labels and values | `box_font_scale` into `L.font_size`: 4x (19 → 76, 34 → 136) | yes |
   | Colony Summary | `planet_paragraph` 17 → 54 at 3840 | NOT code: Data's F5 `font_scale` 1.6 in the 2560x1440 box section, which 3840 falls back to; with one box section at both sizes it scales once | not a fault — no change |
   | Colony Summary | `colonyempire.render` docstring | named `box_font_scale("sidebar")`; the caller passes `box_font_scale_stored("empire_stats")` | docstring corrected |
   | every other screen | — | scales once (star names and Select Race since 179) | — |

   Screens that draw no text without a game (colony, build popup, Leaders)
   were measured from their own fixtures: once.
2. **Fixed as 179 did**: every `box_font_scale` → `box_font_scale_stored`
   (5 on Custom Race, 3 on Empire Identity) and Custom Race's reference
   factor `fs` → 1.0. **1080p pixel-identical, proved**: before/after
   renders of Custom Race, its message box and Empire Identity at
   1920x1080 — 0 pixels differ each (`~/orionlayer-fixtures/evidence/
   work_order_182/scaling/{before,after}/`, `compare_*`); at 2576 and 3840
   the text is now proportional (a 3840 render halved matches the 1080
   one). Custom Race at 3840 no longer runs its Governments off the panel.
3. **The general check — 090t, by rendering.** Every screen of the
   registry plus the help popup and Custom Race's message box, at 1920 and
   3840, both loading the SAME box section (so Data's per-resolution F5
   values neither pass for nor hide a code fault); per call site, the
   largest size at 3840 may not exceed twice the one at 1920 (+2). **Why
   rendering and not a static rule**: the fault travels — `win_h/1080`
   into an `fs` another module feeds to `L.font_size` — and a pattern
   either misses the hop or forbids the legitimate direct sizing. The
   attribution walks past the shared text helpers (`style`, `textfit`,
   `hud/text`, `ldrdraw`, `coldraw.text`/`lines`) so a fitting loop's
   trials count for their caller. Screens with no text offline are named,
   and measured in their groups (090p colony, 090q popup, 090c Leaders —
   each check extended, not replaced). **Shown red** on the old two screens
   (with `python -B`; Custom Race and Empire Identity named, 4x each),
   green on the new.
4. **Evidence**: live native | HD side by sides of Custom Race and Empire
   Identity at 1920, 2576 and 3840 (`scaling/live_side_by_side/`, the
   pre-game walk on the virtual display, engine 166148, guard clean, 0
   native frames in 27 transitions).

**For Data at 2576x1432**: Custom Race and Empire Identity get smaller —
their text was 1.78x its 1080p size there and is 1.33x now, the
proportional size, as the star names and Select Race became in 179.

**Checks: 378 → 379** (090t).

## Finish — what the fresh clone caught

The first fresh clone of `3c66682` failed where this machine passed —
fundament 08's "a check that reads the player's own files passes on the
machine that wrote them", once more, in this order's own additions:

1. 090p's new "scaled once" measurement counted texts drawn with the
   player's EXTRACTED string tables; a clone has none, draws fewer, and the
   count (>= 5 sites) failed. 090p and 090q now hand the screens the
   committed stand-ins (`derived(EStrings)`, `derived(BuildingNames)`).
2. That exposed a real fault: the build popup formatted its title and
   summary lines with `fmt % value`, and a template without the
   placeholder — the stand-in's, a mod's, a language's — raised in the
   render. Now `core.hestrings.printf`, the project's one safe
   substitution (decision 37), as `colwords._fmt` already did; the colony
   screen's officer ETA line had the same `%` and got the same fix.
3. One clone run aborted with `*** stack smashing detected ***` inside
   CPython 3.14.7's own `ast.parse` (`tools/linecount.py`, check 061) — a
   native fault in the interpreter, in code this order did not touch; the
   same clone passed 061 before and after. Recorded, not chased (parked).
