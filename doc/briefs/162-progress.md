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

## Part 1 — the baseline — *not started*

## Part 2 — the inventory tool — *not started*

## Part 3 — the cut — *not started*

## Part 4 — the development selector — *not started*

## Part 5 — the size limit — *not started*
