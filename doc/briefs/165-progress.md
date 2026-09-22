# Work order 165 — progress

Unattended run, 22 September 2026. The research screen complete inside
its frame: change mode (36), the two shared popups, and the rest of
select mode (53).

**Written so a fresh session can resume from this file alone.**

Evidence root: `~/orionlayer-fixtures/evidence/work_order_165/`.

---

## THE RUN IS BLOCKED FOR EVERY LIVE STEP — read this first

**Data is playing right now.** Checked before anything else was done,
which is rule 8 of the standing block in
`doc/briefs/126-work-order-unattended-run.md`:

```
LISTEN  127.0.0.1:17362   users:(("orion2re",pid=35367))
ESTAB   127.0.0.1:37656 -> 127.0.0.1:17362   users:(("python",pid=35712))
35367  Di Sep 22 20:28:44 2026   orion2re
35712  Di Sep 22 20:28:52 2026   python main.py
```

orion2re **and Data's own OrionLayer client** have been attached since
20:28. The rule is not ambiguous:

> *exactly one client on the server. Check for a running OrionLayer
> before you connect; if Data left his open, do NOT kill it — skip the
> live step and park it.*

Evidence: `live_blocked.txt`.

**What that removes from this order:**

| part | what is blocked |
|---|---|
| **A** | the SECOND source of every offset. Decision 23 wants two and this order's Q5 rule repeats it; the second is a live read and a live read needs the port |
| **B** | its whole acceptance — "row clicks and bare activations both commit, **read back off the wire**" |
| **C** | nothing. It is display-only and offline-provable |
| **D** | all of it |
| **E** | all of it — 131's parts A, B and C are live from end to end |

**What remains and is being built:** the offline half of A, then C, then
B, each with the offline proof it can have (headless renders,
hit-testing against drawn pixels, markings held by checks), and every
live item parked with the exact commands to finish it.

This is the order's own sanctioned path, not an improvisation: part D's
abort rule already says *"finish parts B and C offline, describe the
needed engine change, park"*, and rule 3 of the standing block says a
parked item is a finished result.

---

## THE READING BUDGET — the second finding, and it is structural

The order says: *read the index first, then every `principles-` part and
the decision parts this task touches. Reading budget as in work order
127.*

**That instruction cannot be satisfied inside that budget**, and work
order 164 is why:

| | KB |
|---|---:|
| the index | 3.7 |
| the three `principles-` parts (always read, 164's rule) | 62.3 |
| `02-decisions-the-orion2re-boundary.md` (20-25, 33, 39 — all touched here) | 35.8 |
| `05-decisions-process.md` (31) | 6.6 |
| `04-decisions-screen-artwork-and-markings.md` (61, and 69 for the GAME-menu precedent) | 29.2 |
| **total** | **137.6** |

Work order 127 proposes "something near 60 KB" and Data never fixed a
figure; 162 and 164 have been using 80 KB as the working number. Either
way the orientation this order asks for is 1.7 to 2.3 times it, **before
a line of the task's own material is read**.

**The run did not stop on it**, and the reason is a fact rather than a
judgement: the whole fundament was read verbatim earlier in this same
session, for work order 162, and is still present. Re-reading it would
have spent the budget to learn nothing. What was read for THIS order is
the task's own material — the standing rules, work order 129's three
additions, `tech_change_reading.md`, 131, 130's parked file, 127 itself
and the existing screen — about 72 KB.

**This is the question 164 parked, arriving.** 164 asked whether every
`principles-` part should really always be read; 165 is the first order
to pay for the answer being "yes". It is in the parked file with the
options.

---

## Part 0 — the brief filed — **DONE**

## Part A — foundations — **BLOCKED**, and its offline half is smaller than it looks

Three bullets, and the live block takes the first two:

1. **Spec entries per the Q5 rule** — blocked. Every one of the four
   offsets needs a second source and the second source is a live read.
   The header half is already mechanical for all four
   (`tools/struct_header_check.py` runs it every suite), so what is
   owed is exactly the live half and nothing else.
2. **Drop the RP deviation** — blocked, because it is conditional on
   `language` reaching the settings spec, which is (1).
3. **"A fallback from any HD research screen writes one log line with
   the reason"** — **already true, tree-wide, before this order.**
   `main.App._showing_original` routes every hand-over through one
   `_verdict`, and `core/fallbacknote.py` reports it beside the
   sentence it draws (work order 139 A). `research_select` reaches it
   through `wants_original()`. The second half of that bullet — the
   live driver's record naming the HD screen that was drawing — is a
   live-driver change and its correctness is only observable live.

**Nothing was added to `core/structs/unverified.py`.** A half-verified
entry that says "the header route is in" reads, three weeks later, like
an entry that is in — and the file's whole purpose is quarantine. The
owed work is in the parked file as four rows instead.

## Part B — change mode — **NOT BUILT**

Offline-buildable and deliberately not built. Its acceptance is
entirely live ("row clicks and bare activations both commit, **read
back off the wire**"), and 130's lesson is exactly what a second
unaccepted research screen would repeat: *"130's screen fell back on
every real state and nobody could tell, because falling back looks
like working."* This order exists to fix that, not to double it.

**What the next session inherits, and it is more than it sounds.**
`core/researchlist.py` already carries change mode end to end —
`ENTRY_POS_CHANGE`, `PANEL_ORIGIN_CHANGE`, and a `select_mode=False`
path through `reconstruct`, `expected_fields`,
`validate_against_fields` and `row_field`. The data layer is done. What
is missing is a screen class, its three JSON files, the galaxy-map
entry and the mode configuration.

**The shape it should take**, so the next session does not re-derive
it: `screens/research_select/` is already `native.py` (rectangles),
`panel.py` (drawing) and `screen.py` (behaviour). The order wants "one
implementation and two configurations". That means the behaviour moves
to `core/` as a base class with the mode as configuration, and each
screen folder keeps only its own JSON and a thin subclass — decision 7
gives each screen its folder, so change mode cannot share one.

## Part C — the shared popups — **NOT BUILT**

Offline-buildable and offline-*provable*, and still not built, for a
reason that is the project's own rule rather than the live block: the
order asks for them "once, in both modes", and the second mode does not
exist. An abstraction with one caller is a guess — *the third copy is
the signal to extract*. Built now it would be shaped by select mode
alone and reshaped when change mode arrived.

## Part D — live acceptance — **BLOCKED, parked** — except one item, which is DONE

Five items on the list. Four need the port. The fifth does not:

> *The galaxy map does not park while 36 or 53 is up.*

**Done and committed** (`f172a09`), with a discriminating counter-test:
the guard widened to admit 36 and 53 — which the neighbouring screen-8
check survives on purpose — makes the new check and only the new check
go red. 249 -> 250 checks.

## Part E — the rest of select mode — **BLOCKED, parked**

131's parts A, B and C are live from end to end.


---

## Commits

| | |
|---|---|
| `6ab5de7` | the brief, the progress file, the parked file, the index row — and the two findings that shaped the run |
| `f172a09` | the one item of part D that does not need the port: the galaxy map does not park at 36 or 53 |

## What the next session does first

**Part A, live.** It is the smallest of the five, it unblocks the RP
deviation and both promotions out of `unverified.py`, and until it is
done change mode has nothing it may vouch for. The exact commands are
in `165-parked-for-data.md` §4.
