# Work order 160 — progress

21 September 2026. Verification run, **no code changed in either
tree**. `~/orion2re` read with `git log`, `git show`, `git grep` and
`grep` only — no checkout, no build, no patch. No live runs.

**160 was free**, confirmed in the tree before filing: the highest
number in `doc/briefs/` was 159.

**One delay worth recording.** The first attempt at this order failed
because `~/Downloads/orionlayer_notes_for_joes.md` did not exist — not
under that name anywhere, and no file on the disk contained the order's
own quoted phrase. The run stopped rather than verifying a substitute.
Data placed the file at 20:38 and the run went ahead unchanged.

## Results

| part | result |
|---|---|
| 1 — B1 to B8 | **B4 wrong**, everything else OK. Commit, files and status verified for all eight |
| 2 — move-pop | `doc/ext_move_pop.patch` is the stale one; **a second stale header found** (`ext_save_slots.patch`). Both parked |
| 3 — still open | all three still open (items 4, 13, 26); 156–159 touched none of them |
| 4 — references | 7 of 7 files in the **pushed** tree; repo confirmed **public** by an unauthenticated fetch |
| 5 — C and D claims | all four checked, all OK |
| 6 — anything else | nothing further in B, C or D; one out-of-scope observation parked |

**Two false statements, both in Part B**, both corrected in the copy:

1. The Part B intro's "a build without it is your code unchanged" —
   `6598052c` is one unguarded line in `racesel.cpp`, which B3 itself
   discloses. A qualifier, not a reversal.
2. **B4** reports one synthetic screen id where there are two (Custom
   Race 50, Select Race 51), and calls them "on the wire only" when
   both assign `MOX::_current_screen` itself. **B5's identical phrase
   is true** — it uses `ext::ScreenOverride`, whose own comment says
   the engine's variable is untouched. One phrase, two mechanisms.

Full evidence per claim: `doc/briefs/160-findings.md`.

## Deliverables

- `doc/briefs/160-findings.md` — per part, with the changed sentences
  as old → new at the top.
- `~/orionlayer-fixtures/evidence/work_order_160/orionlayer_notes_for_joes.md`
  — the corrected copy. **The original in `~/Downloads/` is
  untouched**, still 13 110 bytes, 21 September 20:38.
- `doc/briefs/160-parked-for-data.md` — the two stale patch headers,
  and the out-of-scope note about Part A's tree.

## Not done, and why

**Nothing was repaired.** The two stale headers are Data's to decide,
as the order directs. Part A was not read or changed.
