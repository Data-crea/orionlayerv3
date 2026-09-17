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
