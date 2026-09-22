# Work order 162 — progress

Unattended run, 22 September 2026. Splitting `tools/smoke_test.py`
(22 221 lines, 1 172 833 bytes, almost all of it inside one `main()`)
into per-screen modules **by script**, so that screen work reads and
runs only that screen's checks plus the shared core.

**Written so a fresh session can resume from this file alone.** Each
part says what is done, what is committed, what the next step is and
where the evidence lives.

Evidence root: `~/orionlayer-fixtures/evidence/work_order_162/`.

---

## State at the start of the run

| | |
|---|---|
| HEAD | `a5c3f4e` (161) |
| tree | clean |
| suite | 247 checks, full tier; 7 push-only (`SLOW_TIER`), 240 in the fast tier |
| `tools/smoke_test.py` | 22 221 lines, 1 172 833 bytes; `main()` is lines 265–22147 |
| gates | pre-commit `--fast`, pre-push full (158, unchanged by this order) |

---

## Part 0 — the brief filed — **DONE**

`162-work-order-…md` byte for byte as it arrived, this file,
`162-parked-for-data.md`, and their row in `doc/briefs/README.md` in
the same step (the suite asserts the index in both directions).

## Part 1 — the baseline tool — **BUILT**

`tools/smoke_baseline.py`: `capture <dir>` runs both tiers N times,
records the ordered `ok(...)` list, the check count, the fast tier's
skipped set and the runtimes, refuses anything but a green run, and
fails if two runs of the same tier disagree. `compare <a> <b>` is what
the cut is held to.

**The normalisation table is EMPTY, and that was measured rather than
assumed.** Two full runs of the unchanged tree produced byte-identical
`ok(...)` lists, 247 sentences each — the suite prints verdicts and
transcribed constants, not measurements of the clock. The table stays
in the tool with that note and the rule that every rule names the
message that needed it: a rule written defensively is a blind spot the
size of its own pattern.

## Part 2 — the inventory tool — **BUILT**

`tools/smoke_names.py` (a library) and `tools/smoke_inventory.py` (the
tool). 221 sections, 247 checks, 1 040 KB of `main()` body.

**A section is a maximal run of top-level statements ending at an
`ok(...)`** — the only boundary the suite itself draws, which is what
157 measured against too.

**The name flow is ordered, not set-based.** `_fh = open(_fh)` reads a
name it then binds and `_fh = open(path)` does not; a "reads minus
binds" set cannot tell them apart and reported 881 free reads as
though every reused throwaway name were a dependency. Mutation is
tracked separately, because `_surf.blit(...)` binds nothing and
changes everything a later reader sees — and it is the edge that
matters most: 13 sections are pulled into the core's dependency
closure by a mutation of `app` alone.

**Attribution, and how each section's area was decided.** Tokens come
from the tree: each screen's folder name, its name parts longer than
three characters, and every file stem in its folder longer than five —
minus any stem `core/`, `tools/` or `assets/shared/` also carries, and
minus any stem two screens share. (`palette` is `core/palette.py` and
had filed the suite's very first block as a Fleets check.) A tree
sweep — `os.walk`, `glob.glob` — goes to the core whatever it names,
because it polices files that do not exist yet (157 section 5a). A tie
or no screen at all goes to the core. A margin on top of the tie rule
was measured and dropped: demanding three hits and twice the runner-up
moved 53 more sections into the core, and since every `--screen` run
carries the core it made every narrowed run *bigger*.

| area | sections | KB | s |
|---|---:|---:|---:|
| colony_summary | 53 | 372 | 45.1 |
| core | 82 | 237 | 9.0 |
| galaxy_map | 29 | 170 | 5.8 |
| fleets | 19 | 125 | 3.9 |
| planets | 11 | 40 | 1.5 |
| game_menu | 8 | 27 | 4.2 |
| empire_identity | 3 | 23 | 0.6 |
| research_select | 4 | 22 | 0.6 |
| main_menu | 6 | 13 | 0.1 |
| custom_race | 3 | 8 | 0.3 |
| select_race | 2 | 2 | 0.5 |
| new_game | 1 | 1 | 0.0 |

Evidence: `inventory_before.txt` (the table, 29 KB — the thing a
session reads) and `inventory_before.json` (the rows, for the cutting
script), plus `times_before.json`, a measured run with every check's
segment time anchored to its own file and line.

**The tool did not retire with the cut.** `--screen` asks it at run
time which sections a screen depends on; a baked dependency list would
be the second copy this project keeps paying for.

## Part 3 — the cut — *not started*

## Part 4 — the development selector — *not started*

## Part 5 — the size limit — *not started*
