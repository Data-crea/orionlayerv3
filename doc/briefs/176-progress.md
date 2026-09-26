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
