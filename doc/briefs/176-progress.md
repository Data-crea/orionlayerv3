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
