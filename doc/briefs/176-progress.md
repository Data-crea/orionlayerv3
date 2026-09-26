# Work order 176 — progress

Unattended run, 26 September 2026. The new rule for leftover engines,
open fix 32 applied and wired, the live tests parked in 175, then the push.
Evidence root: `~/orionlayer-fixtures/evidence/work_order_176/`.

## 1. The new rule — engines Claude Code did not start — **RECORDED; the close was REFUSED by the harness**

Rule (Data, this order; holds while Data does not play): an engine or
client found running that Claude Code did not start is a leftover and may be
closed — `tools/liveguard.py` first, SIGTERM, a few seconds, SIGKILL only if
it is still there, all recorded; never connected to. Recorded in CLAUDE.md
("AN ENGINE OR CLIENT THIS SESSION DID NOT START"), fundament part 09 (after
"A LIVE RUN WRITES MORE THAN THE SAVES") and `tools/engine_start.py`
(`--close-foreign`, `close_foreign`, `foreign_clients`; the refusal message
names the option). Check: 006e's third check closes two processes the check
itself starts (one ends on SIGTERM, one needs SIGKILL) after a backup, and
holds the rule in both documents. 334 -> 335.

**Found running at the start:** orion2re PID 368253, parent 35660
(`/usr/bin/zsh`), command `/home/data/orion2re/out/build/Linux/linux-debug/
orion2re`, started Sa Sep 26 10:03:06 2026 (3 h 8 min before). No OrionLayer
client (175's `python main.py` PID 369007 had gone).

**How it ended: it did not.** `python tools/engine_start.py --close-foreign
--guard ~/orionlayer-fixtures/live_guard/176_close_foreign` was DENIED by
Claude Code's auto-mode permission classifier ("Interfere With Workloads")
before it ran — no backup was taken, no signal sent. The denial says not to
reach the same outcome another way, and this run did not. The engine is
still running and still holds port 17362, so no engine of this run can
start and every live step below is parked for that one reason (parked item
1 says what unblocks it).

## 2. Open fix 32 — **APPLIED and WIRED**

- **orion2re**: `patch -p1 < doc/ext_info_screen_state.patch` on
  `orionlayer-local` (dry-run first), commit **`2269749c`** — it contains
  `src/ext/ext_api.cpp` only (+41); the untracked `mox.set`,
  `racesel_custom_screen_id.patch` and `src.zip` were not touched and are
  not in it. Rebuilt (`ninja`, binary 13:20:59; the running leftover engine
  was unaffected). Bundle `~/orion2re_bundle_26sep_2269749c.bundle`,
  `--all`, verified (21 refs, `orionlayer-local` = 2269749c). Nothing went
  online.
- **Records**: the patch header says APPLIED with commit and date; row 32
  and section 32 of `doc/orion2re_open_fixes.md` say Applied; version_check
  requires `MOX::_bill_savegame[i]` (its report: "OK — all three agree").
- **175's blind append, read now in full (end and table)**: entry 32 sat
  correctly as the last section and the last table row, each exactly once,
  the file ending whole; `git show 7a2526f` shows the append was 25
  insertions and no deletion. Two format points fixed: two blank lines stood
  before "## 32." (one now, as before "## 31."), and — older than 175 — the
  status table had **no row 29** although section 29 ("A native message
  box's text is not in the snapshot", OPEN, work order 152) exists; the row
  is added from that section's own text.
- **Wired** (`screens/info/`): `core/game_state` parses the INFS block
  (whole or None); the History Graph draws `Draw_Histories_` — the rings
  times the divisors, ten smoothing passes, the 25..2000 ladder, the maximum
  at (246,138), the step 10/5/2/1 and the eight stardate labels — in the
  players' colours; the metric toggles are HD-local, from `history_btns`
  bits 0-3; the Turn Summary lists the engine's rendered messages under
  BILLTEXT 26 with the stardate (0x88), or NO MESSAGES. The "needs fix 32"
  notices are gone; an engine WITHOUT the block gets `info.history.no_block`
  / `info.turns.no_block` (moddable), like Leaders' NO_BLOCK.
- **Second source for the divisors' place in the save**: `tools/
  leaders_offline.arrays` now reads `_bill_savegame` from the save
  (savegame.cpp:1389-1392); the reference fixture gives `[2, 24, 1, 57, 5,
  34]` — `[1]` = 24 is exactly the turn count of stardate 3502.4, which the
  ring index must be.
- **Checks**: 090f's fifth check (records, the engine's tree with `patch -R`
  dry-run, the block parsed from real bytes and cut, the history math, both
  pages wired, the notice only without the block); 090c's fix-30 check now
  takes fix 32 off its scratch copy first (they are stacked in one file).
  335 -> 336.
- **Evidence (offline)**: `evidence/work_order_176/info/info_*_offline_*`
  (1920x1080, 2576x1432) — History with curves from the fixture's own
  divisors; Turn Summary offline has no messages (the engine renders them).
  **A slip:** refreshing them this run deleted 175's four
  `info_history_offline_*` files (the pre-fix-32 History page) from
  `evidence/work_order_175/info/`; they are gone, the 175 code that drew
  them is in git (7a2526f).

## 3. Live tests — **PARKED** (parked items 1 and 2)

No live step ran: the leftover engine PID 368253 held the fixed port all run
and closing it was denied by the harness (part 1). Every step of 175's
parked list is written out, ready to run, in parked item 2. No regression
from 175 or this order was observed — none could be, live. No liveguard
backup was taken (no engine of this run existed); no game or OrionLayer
file was written by a run.

## Tests

- Full suite: **336 green** (26 September 2026, after part 2).
- Fresh clone (`git clone` of the local commits, `tools/setup.py` exit 0,
  full suite): **336 green**.
- 334 -> 336 over this order: 006e's leftover-engine check, 090f's open
  fix 32 check; nothing removed.

## Push — **NOT MADE** (parked item 3)

What WOULD go out — `main`, 11 commits ahead of `origin/main`
(`git@github.com:Data-crea/orionlayerv3.git`):

    fe9b348 Open fix 32 applied and wired: History curves, Turn Summary (176-2)
    38d155d Work order 176 filed; the rule for engines this session did not start (176-1)
    54a5c3f Work order 175: tests, results and what to look at first; CLAUDE.md fix
    7a2526f Work order 175 D: the Info screen, its texts moddable (decision 73)
    6b55071 Work order 175 C: the Races screen
    51b2517 Work order 175 B: the Leaders screen complete, with open fix 30
    8b03592 The string extractor keeps its spaces; the Leaders workaround goes (175)
    9cfa50e Open fix 30 applied: the Leaders screen's view state on the wire (175 A)
    64bb4ec Open fix 31 applied: present without VSync on request (175 A)
    8842bca The live-test protocol backs up every file a run can write (175)
    266f6f5 174 recorded as pushed; work order 175 filed (175)

plus this closing commit. The other local branches (`colony-free-bands`,
`rescue/ties-abend`) are identical to their remote counterparts; there are
no tags. orion2re stays local (bundle in `~/`).

## Results

| step | result | evidence |
|---|---|---|
| rule for leftover engines recorded (CLAUDE.md, fundament 09, engine_start.py) | works | 38d155d; 006e check 3 |
| leftover engine PID 368253 closed | parked — denied by the harness | part 1; parked item 1 |
| fix 32 applied (orion2re 2269749c), bundle, rebuild | works | part 2; version_check OK |
| entry 32 checked whole; row 29 and a blank line fixed | works | part 2; 090f check 5 |
| Info History curves and Turn Summary wired | works (offline) | `evidence/work_order_176/info/*_offline_*`; 090f check 5 |
| fix 31 starts and tearing | parked (port) | parked item 2 |
| Leaders live, every button both tabs, hire | parked (port) | parked item 2 |
| Races live | parked (port) | parked item 2 |
| Info live, every tab, text mod, colony jump | parked (port) | parked items 2, 4 |
| extractor spaces live | parked (port) | parked item 2 |
| full suite / fresh clone | works (336 / 336) | above |
| push | not made | parked item 3 |

## What Data should look at first

1. Parked item 1: close PID 368253 (`kill 368253`) or allow
   `engine_start.py --close-foreign` — everything live, and the push,
   follows from that one decision.
2. `evidence/work_order_176/info/info_history_offline_*_1920x1080.png` —
   the History Graph from open fix 32's divisors (the save's own), the
   first page fix 32 opens.
3. `doc/orion2re_open_fixes.md` row 29 — a row the table had been missing
   since work order 152, added from its section.

## Data's added question — does `python main.py` start an engine and leave it running? — **NO; nothing to change**

Asked after the push was held (26 September 2026, own commit). Answer, in
three parts:

- **The source**: nothing `main.py`, `core/` or a screen runs launches a
  process (`App._connect` only opens the TCP client, main.py:153-163; the
  one `subprocess` call in `core/config.py` asks git for the build
  revision) and nothing signals one; `App.run` ends with
  `client.disconnect()` and `pygame.quit()` (main.py:170-181). There is no
  launcher script in the tree.
- **Live, with an engine running** (this run's PID 398250): `python main.py`
  with a real window (`DISPLAY=:0`, x11) connected to it, had no child
  process, and no new orion2re appeared; `xdotool windowquit` (the window
  manager's normal close, WM_DELETE_WINDOW) ended it with exit 0 and the
  engine — not its own — kept running.
  `evidence/work_order_176/main_py/close_with_engine_LIVE.json` (+ `.log`).
- **Live, without an engine**: it ran standalone ("Could not connect …
  Running in standalone mode"), started nothing, closed with exit 0, and
  no orion2re existed before, during or after.
  `.../main_py/close_without_engine_LIVE.json`.

So OrionLayer never starts an engine and therefore has none of its own to
stop, and it never stops a foreign one — the requested behaviour already
holds. The rule is now a check (006e check 4: an AST scan of main.py, core
and screens for process launches and signals, and the exit path's
disconnect). 337 -> 338.

## Part 3 — run, after Data closed PID 368253

Data ended the leftover engine; the port was free, no client ran. Every
engine below was started by this session with `tools/engine_start.py` and
stopped by its PID (SIGTERM, each ended on it).

**liveguard.** Master snapshot `~/orionlayer-fixtures/live_guard/176_master`
(15:00:53, before any engine), plus the per-start guards `176_run1`,
`176_run2`. After the run: `SAVE4.GAM` changed (the one deliberate change:
SAVE2's game copied into scratch slot 4 for the hire step) and `MOX.SET`
changed (the game rewrites it when a loaded game is left — 175's reason for
liveguard), both **restored** from the master copy; then **every protected
file identical to the master snapshot** (SAVE1-11, MOX.SET, HOF.M2,
lastrace.rac, user_settings.json; TEMP.TMP absent before and after), and
`176_run2` reports "every file identical". The only other difference, the
tree's git status, was this run's own uncommitted code, gone once committed.
Scratch slot named: **SAVE4** (SAVE5 loaded, never written; SAVE8 never
touched).

**Fix 31 — starts.** 82 starts in three series: 40 with a 45 s wait (33
ready at once, 7 "timeout"), 12 with 150 s (12 ready), 30 with 150 s and a
backtrace armed (30 ready: 26 at once, 4 after exactly 112.9 s). **No VSync
hang** (the signature never appeared). The 11 slow starts are the original's
logo/intro sequence, which plays when no key or button is down at start
(jim.cpp:18-120) — `gdb` could not attach (ptrace refused), the timing and
the source settle it. The tool's 60 s default reads them as timeouts:
parked item 6. `evidence/work_order_176/fix31/starts_LIVE_*.json`,
`stalls_LIVE.json`. **Tearing**: not observable from this session — parked
item 5.

**Leaders** (SAVE4; both sizes, 21 of 21 steps each): open with the OFFS
block; the ship tab; NEXT / PREV cycle the stack; a stack icon in the galaxy
box becomes the stack on show; the grid; assign (officer, then a combat
ship, a confirmation answered YES → status 1 on that ship); POOL mode, an
assigned officer to the pool (status 1 → 2); DISMISS mode, the "Dismiss %s?"
box, YES → gone from the list; the colony tab; NEXT / PREV cycle the star;
a star with a colony clicked in the galaxy box → chosen and shown; RETURN.
**HIRE** (SAVE4 holding SAVE2's game; both sizes, 6 of 6): three leaders for
hire, hire mode with CANCEL and the price panel, the hire popup naming its
leader (open fix 30's `popup_leader`), HIRE → Ruola joins, BC 790 → 760.
`evidence/work_order_176/leaders/` (`record_slot4_*`, `record_hire_slot4_*`;
the hire run's `001_…_open` picture was overwritten by the later Leaders
run's — its record is intact).

**Races** (SAVE4; both sizes, 11 of 11): open in the main mode, beside the
native picture: portraits and banner frames, WAR / No Treaty, the sliders,
three agents, SPY 0 % / AGENT 10 % all as the original; IGNORE → a race →
its bit flips and (IGNORED) shows, and back; REPORT → the report (the
fallback) and back; AUDIENCE → the ambassador (the fallback: "…will listen
when you are ready to surrender") clicked away; DECLARE WAR on the race at
peace → the confirmation, NO → no war; RETURN. `evidence/work_order_176/races/`.
**Three 175 regressions found and fixed here**, each with a check and its own
commit: the screen did not recognise its own list (slot 1's SABOTAGE is
13 px high, 175 used slot 0's 14 for all — 9fad509), the declare-war box
crashed it (`raceswire.View` had no `in_box` — fddc428), and "No Treaty"
was upper-cased (739a908). The run above is after the fixes.

**Info** (SAVE5 at 1920x1080, SAVE4 at 2576x1432 with the demo text mod;
10 of 10 and 12 of 12): opens on the game's saved tab (3); open fix 32's
block live — divisors `[2, 91, 1, 9, 1, 6]` / `[2, 90, 1, 9, 1, 6]`, exactly
the ones in the save files (the second source), and the turn's message;
every tab HD-local; a Reference category and a How-to page; with the demo
mod the tab, the title and BACK replaced, the 213 article 1338 px too long
and scrolled by the wheel (offset 384), and one log line each for the
non-UTF-8 and the empty file. **The colony jump**: the engine's Turn
Summary row for "Malus Prime finished construction: Colony Base. …" (a
colony message) was activated: screen 9 → **0**, not 1 — the jump is
overwritten, as 175 read at info.cpp:641; recorded as open-fix entry 33
(an observation for Joes). `evidence/work_order_176/info/`; the offline
renders of part 2 re-made in `evidence/work_order_176/info_offline/` (the
first set was deleted by this run's clean-up of the live folders).

**Extractor fix live**: Leaders' skill help "Commander Hawk, the
Astrogator, increases …" and the fleet strip "CYBERTOLLER FLEET: 1 Frigate"
keep their spaces (both sizes); the Fleets screen's ten texts show no two
words run together (`evidence/work_order_176/fleets/`).

**Window sizes**: every screen above at 1920x1080 and 2576x1432.

The drivers are `tools/screens175_live.py` with `screens175_steps.py`,
`screens175_leaders.py`, `screens175_others.py` (one client, scratch slots
only, each step EXPECTED / OBSERVED with native and HD from one snapshot).
Note on the three fix commits: the pre-commit hook runs the fast suite on the
working tree, which held all three fixes; each intermediate commit's own
tree was not run separately.
