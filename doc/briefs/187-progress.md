# Work order 187 — progress

Unattended run, 28 September 2026. Evidence root:
`~/orionlayer-fixtures/evidence/work_order_187/`. The order:
`doc/briefs/187-work-order-modal-hold-hd-name-entry-ai-audience-original-only-on-f12.md`.

## Before part 1

- **Number 187**: the last brief in `doc/briefs/` is 186.
- **Baseline as expected**: main = origin/main = `557da0f` (186, "Work order
  186 Part 5: gates green and the end of the order"), 407 green by 186's
  push gate; orion2re `orionlayer-local` = `230a0638` (fixes 34-41, 43-47),
  its three untracked files left alone.
- Read: `doc/v3_fundament.md`, the three `principles-` parts, part 09, 186's
  progress, parked file and `186-modal-hold.md` (all read or written in
  this session).
- **Data was playing at the start**: `python play.py` (PID 199264, started
  18:40:33), its engine 199278 and OrionLayer 199301 — not touched, never
  connected to. `engine_start --check` refused (a foreign engine, the port
  taken). Live parts wait until his session has ended; the order's first
  guard is taken then, not mid-play (it would record his own saves as
  changes). Non-live work went first.

## Part 6 — where the original can still show (inventory, no change) — **DONE (committed before parts 1-5: it needs no live run, and Data was playing)**

Report: `doc/briefs/187-original-visibility.md`. **6 paths** by which the
original can show without F12, all through `main.App._showing_original`
and the gate: (1) a game screen with no HD screen (ids 7, 12, 14, 18, 30,
39, 40, 52 and every unlisted one, e.g. 33); (2) such an id with an empty
list past `EMPTY_HOLD`; (3) a known screen declining its id (an engine
without fixes 35-40 / 44-47); (4) a box over an HD page (`GAME_BOX`);
(5) a box over a screen with a modal net (map, main menu, select race);
(6) a known screen that cannot vouch (missing extractor files, a dialog
it cannot name) — the safety net's keys and clicks (7) are their input,
not an extra path. Seen in walks: 1, 4, 5 (the gate's log lines of
180-186: 10 designer-box and 2 colony-base releases; SAVE5's combat choice);
never seen: 2, 3, 6. **Recommendation**: one rule for all six — never the
picture, HD's last frame dimmed with a notice "Press F12 to answer it"
(needs Data's decision first); then one HD message box on open fix 29,
"A native message box's text is not in the snapshot" (needs Data's decision
first: an engine fix); then HD screens by frequency. Parked 1a.

