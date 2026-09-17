# Work order 126 — parked for Data

Every question this run met that is Data's to decide. Each item says what
it is, why it is Data's, the options with their cost, and what was done
meanwhile, so it can be answered in one line. Written as the run goes;
the closing state of this list is stated at the end.

## 1. Split the smoke test's `main()` into groups? (part C)

**What:** `tools/smoke_test.py` is ~16,400 lines, almost all ONE function.
Thirty runs today: 30 of 30 exit 0, peak resident memory 4540–4836 MB,
66.6–68.1 s each on this machine (not ~10 s as the order assumed). Locals of
one function live until it returns, which is the likely reason memory only
grows. **Why yours:** a 16,000-line refactor with no behaviour change, whose
time argument the order had dropped; the numbers above partly revive it.
**Options:** (a) leave it — costs ~4.8 GB per run and one exception still
aborts every later check; (b) split into group functions called from `main()`
with a per-group try/report — one careful order, frees memory per group, the
count must stay 195; (c) split AND allow running a group alone for iteration,
the full suite still before every commit (decision 31) — (b) plus a CLI.
**Meanwhile:** nothing split; quiet mode and the memory line are in.
**Answer in one line:** a / b / c.

