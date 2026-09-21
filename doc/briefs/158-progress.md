# Work order 158 — progress

Unattended run, 21 September 2026. Implements 157's Option A and
nothing else.

---

## Part 1 — the fast tier — **DONE**, `2d73c66`

**Seven checks go push-only.** Declared in `smoke_test.SLOW_TIER`, each
with the reason it is expensive beside its name:

| check | why | cost |
|---|---|---:|
| figure pick-up, 1–20 figures × 3 resolutions | renders the colony summary and reads the drawn pixels back; its second pass uses the player's OWN extracted figures | 28.2 s |
| RETURN's cutout | twelve resolutions, and the twelve are the point | 13.7 s |
| GAME menu frame: opening | loaded through the resource roots, measured against the artwork | 3.0 s |
| GAME menu frame: drawn | the metal's opaque pixels sampled off a first opening | 1.2 s |
| `main._verdict`'s fallback log | stands the app up repeatedly | 2.3 s |
| sidebar research readout | renders the readout for the original's four cases | 2.3 s |
| 49 tools import in fresh processes | 49 subprocesses; the only expensive check that renders nothing | 2.0 s |

**The threshold, and it is not the ranking.** A check goes push-only
when **(a)** it costs at least a second **and (b)** its own block can be
skipped without a later check noticing. **(b) did the real work.** 157
warned that a segment's measured time includes shared setup sitting in
front of it, and that is exactly what three of the top ten turned out to
be: ranks 6, 8 and 10 have safely-skippable blocks of five to nine lines
because their cost *is* setup other checks need. They stay in the fast
tier — which is the order's own rule, that a cheap check stays even when
it is thematically related to a slow one, arriving from the other
direction.

**How each block was chosen**, rather than by eye: for every candidate,
compute scope-correctly which names it binds that a later statement
reads *before* rebinding, and which containers defined outside it it
mutates. All seven come out clean on both. Two findings from doing it
properly:

- **RETURN's block is deliberately narrower than its segment.** The
  wider one fills `_class_c` for the frame checks that follow, so
  skipping it would have broken them silently — a mutation, which no
  read-before-rebind analysis sees. The mutation test is what caught it.
- A first pass got this wrong twice: once by ignoring nested function
  scopes (names inside a `def` are not main's), once by stopping the
  search at the first mutation instead of extending past the
  accumulator's own creation. Both were caught before anything was
  edited.

**The list is policed**, marker-inventory shape: a new check asserts the
`if slow("...")` guards and the `SLOW_TIER` keys agree in **both**
directions, that every entry carries a reason, and that the run reached
every guard. It runs in the **fast** tier, because that is the tier a
commit goes through. That is the 244th check, so `CLAUDE.md` and the
Snapshot table moved with it.

**Both tiers assert the FULL count.** The documents' number is compared
against `PASS + skipped`, so a fast run still holds them to the whole
suite and cannot go green against a count it never reached.

**Full is the default.** Only the pre-commit hook passes `--fast`. A
fast run prints `SMOKE TEST PASSED (FAST TIER)` with the number of
checks it did not run.

### Measured, 157's method

| | runs | min–max | spread |
|---|---:|---|---:|
| **this tree, fast** | 6 | 38.87–39.24 s | 0.37 s |
| **this tree, full** | 6 | 79.49–80.37 s | 0.88 s |
| **clone, fast** | 3 | 37.29–37.32 s | 0.03 s |
| **clone, full** | 3 | 63.56–64.08 s | 0.51 s |

**The gate falls 51 % here and 42 % in a clone**, and peak memory falls
with it, 6.7 GB → 4.8 GB. The saving is *smaller* for a forker, and 157
§4 says why: the biggest push-only item is the figure check's second
pass over extracted figures, which never ran in a clone anyway. So the
fast tier narrows the gap between Data's gate and a forker's rather than
widening it.

### One thing worth recording, because the rule says never to bury it

**A fast run segfaulted once**, `rc = -11`, in the first of a batch of
five. Twelve further runs (six fast, six full) were clean, so it is
sporadic and not the tier — the full suite crashed neither before nor
after. Cause not established. It is recorded because the project's rule
is that 139 is never retried into green, and because a gate that
sporadically segfaults is worse than a slow one: both hooks refuse on
it, which is the designed behaviour and was not changed.

---

## Part 2 — the push gate — **DONE**, `8a691be`

`tools/githooks/pre-push` runs the **full** suite and refuses the push
on any exit but 0, on a missing PASSED line, **and on a PASSED line that
says FAST TIER**. The last case exists because the two hooks differ by
one flag: a hook that quietly passed `--fast` would leave the project
with two fast gates and no full one.

The pre-commit hook's header now says what it runs, why, what it costs
and where the full suite went. `setup.py` names both hooks, checks both
are executable, and reports them together — `core.hooksPath` switches on
a *directory*, so it is the pair or neither.

### The three proofs, by the path a fault would travel

Evidence: `~/orionlayer-fixtures/evidence/work_order_158/gate_proofs.txt`.
A scratch clone whose origin was replaced by a local bare repository,
checked for the absence of a github remote before any push, removed
afterwards. **Nothing reached GitHub.**

| | | |
|---|---|---|
| **1** | a fault only a push-only check sees — `_seen_centres` measuring the canvas instead of the visible ink, which is Data's own 16 September report | **PASSED.** Fast tier green, **commit went through**, full suite red, **push refused**, remote empty |
| **2** | a fault in a fast-tier check — `pick_zones` narrowed to a quarter | **PASSED.** **Commit refused**, HEAD unchanged |
| **3** | a fresh clone + `setup.py`, both hooks proved by *running* them | **PASSED.** Commit printed the FAST TIER line; push printed "running the FULL smoke test" and 244 green |

**The first attempt at proof 1 failed, and that is the most useful thing
in this part.** The fault first tried was narrowing `pick_zones` — the
marker-width fault's own shape — and the **fast tier caught it at
once**. So the fast tier keeps real coverage of the pick path; what it
gives up is the figures-present ink measurement, which is precisely what
the push-only pass is for. The failed attempt became proof 2.

---

## Part 3 — documentation — **DONE**

**Decision 31 was refined in place, not given a new number.** It already
carried the gate; a second entry describing one mechanism is the second
copy this project keeps paying for, and a decision number is an
identity. The refinement states: fast tier on commit, full on push, full
is the default, the slow list is declared and policed, no check
weakened, and the cost in one sentence.

`CLAUDE.md`'s gate section, the status document's Snapshot row and a new
"The gate has two tiers" section carry the same facts with the measured
times. The division-of-labour agreement in `CLAUDE.md` was not touched.

`157-parked-for-data.md` marks the suite gate resolved with the hashes.
