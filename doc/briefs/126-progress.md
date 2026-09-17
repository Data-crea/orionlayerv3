# Work order 126 — progress log

One line per finished part, appended before the next part starts
(rule 9 of `126-work-order-unattended-run.md`). A fresh session resumes
from the last line. Smoke figures are the full suite's check count and
its exit code on the run the part's last commit was made on.

Baseline before any part: smoke **194** checks, exit 0 (orionlayerv3 at
d8006d7, 17 September 2026). No OrionLayer client and no orion2re were
running.

- **A** (orion2re) — done. Backup `~/orion2re_backup_17sep.tar.gz` (sha256
  `e9a50f44…`, with `.git`, without `out/`). Branch `orionlayer-local`, 5
  commits on cf4d9617: a111355d Extension API (src/ext was untracked, so it
  also carries the src/ext halves of open fixes 1, 2, 3, 12, 14, 20, 21 —
  not separable), 191aaa78 open fix 3 (platform.cpp), 6598052c open fix 5,
  e099d3fc screen IDs (ext_screen_id.patch), 7067c366 open fix 12 (colmove).
  Source tree hashed before/after over 4731 files: identical. linux-debug
  incremental build: no work to do, exit 0; a fresh clone of the branch built
  from scratch (662 steps, EXT on), exit 0; `tools/version_check.py` OK on
  both. Push URL set to `DISABLED-no-push-see-orionlayer-work-order-126`. No
  fetch. Untracked and left so: `mox.set`, `src.zip`,
  `racesel_custom_screen_id.patch` (in the backup). Smoke not touched: 194.
- **B** — done. Hook `tools/githooks/pre-commit` (full suite, refuses any
  exit but 0 and a zero exit without the PASSED line), `core.hooksPath` set
  by `tools/setup.py`; shown in a throwaway copy: SIGSEGV stub (139) and a
  failing stub refused with HEAD unchanged, the real suite committed
  (`~/orionlayer-fixtures/evidence/work_order_126/B_hook_demo.txt`); the new
  check fails with the hook neutered (`B_hook_check_mutation.txt`). Fundament:
  decision 5 "agree, not right", Diagnosis right-click line, decision 31
  amended. Smoke **195**, exit 0. Parked: none.
- **B commits:** f8be83e (hook, 194 -> 195), d4eedb5 (fundament), and 90a5af6
  filed the orders before them.
- **C** — done. `--quiet` and the peak-memory line; hook and setup use quiet.
  Thirty full runs: 30/30 exit 0, peak RSS 4540–4836 MB, 66.6–68.1 s
  (`evidence/work_order_126/C_thirty_runs.md`). Smoke **195**, exit 0.
  Parked: item 1 (split main()).
- **C commit:** 5719c70.
- **D** — done. 3f7d45a GAME menu on connect opens over the galaxy map
  (OVERLAY_PARENT; 195 -> 196); 79701c7 tools import again, `tools/toolenv.py`,
  four siblings fixed with colony_move_hd, a fresh-process import check
  (196 -> 197); 2a5e672 empty slot edit marked DEVIATION (and a source finding:
  the original APPENDS a character typed first); b6cfbd9 SAVE11 classified —
  nothing in the engine writes or reads it, hashed with SAVE1-9. Exit 139:
  no occurrence in 30 runs (C). 59 ms first menu open: left, as decided.
  Open fix 19: unchanged observation (see report). Smoke **197**, exit 0.
  Live: none. Parked: none from D.
- **E** — done, a report: Part 0 and Run A of the colony order are done; Run B
  (documentation audit) is not, and belongs with 127; the missing brief texts
  are 90's head and 125. No live run. Smoke **197**. Parked: item 2.
- **E commit:** 5e62885.
- **F** — done: input moved to `screens/galaxy_map/mapinput.py` (screen.py
  583 -> 461 code), exceptions list regenerated, two source-reading checks
  retargeted to where the text moved. Smoke **197**, exit 0. Parked: none.
- **G** — done: four readings e1a07e1 (colony + queue), e120dd6 (research),
  6e344ec (fleet), ad955b9 (races); open fix 22 DESCRIBED, NOT APPLIED; status
  section. Smoke **197**, exit 0. Parked: items 3-7.
- **H** — done (Stop 1 of 127 only): report in
  `evidence/work_order_126/H_reading_budget_stop1.md`, nothing in the tree
  changed by it. Parked: item 8.
- **H commit:** 453bee7.
- **I** — done: `doc/redundancy_audit.md` (39 groups: 4 clear, 7 two-copy, 24
  drifted, 4 deliberate); extracted 4c39b66 box_style, e5cb136 held_pops,
  e845dd6 frame trio (renders byte-identical at three sizes). Smoke **197**,
  exit 0. Parked: items 9-10.
- **Run closed.** Every part A-I reached. orionlayerv3: nothing pushed;
  orion2re: branch `orionlayer-local`, push URL disabled, nothing fetched.
  Smoke 194 at the start, **197** at the end, exit 0 on every commit (the hook
  from part B ran on each). CLAUDE.md changed three times (the hook sentence,
  the check count, the SAVE11 line); its division-of-labour section was not
  touched, so the chat-side copy of that agreement does not have to move.
