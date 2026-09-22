# The fundament, part 5 of 9 — Process

Decision 31 — the smoke suite, the two gates, and what a narrowed run is not.

**Decisions in this part:** 31.

The index is [`../v3_fundament.md`](../v3_fundament.md), and it is
what to read first. This file is one part of the fundament and
carries no rule that is not in it; the text below is what stood in
`doc/v3_fundament.md` before work order 164 moved it, unchanged.

<!-- fundament-body -->
### Process

**31. Verification via `tools/smoke_test.py` before every handoff.**

**Amended 17 September 2026, work order 126 part B: the commit is coupled
to the result by a mechanism, not by attention.** A commit went through
after a smoke run had exited 139, because nothing connected the two.
`tools/githooks/pre-commit` runs the full suite and refuses the commit on
any exit but 0 — a failure, a segfault (139), a kill (137) — and on a zero
exit that never printed the PASSED line; `tools/setup.py` points git's
`core.hooksPath` at it, since a clone does not inherit git config. A hook
rather than a wrapper, because a plain `git commit` is the habit every
session already has. **Exit 139 is not green:** re-run once by hand, record
both exits, never commit on the crashed run — the hook does not retry, since
a retry would turn a sporadic crash into a green commit. The smoke test runs
the hook against stub suites (a real SIGSEGV among them) and fails if it
lets any of them through. `--no-verify` bypasses it, and is a deliberate act.

**Refined 21 September 2026, work order 158: two tiers, and git enforces
both.** The suite reached about 78 s, and work order 157 measured where
that went — seven checks were about half of it, all seven expensive for
the same reason, standing screens up at many sizes or counts. So the
commit gate runs a FAST tier and the full suite moved to a second gate
before the push. **Amended here rather than given a new number**,
because a decision number is an identity and this is still one
decision: the gate. Two entries describing one mechanism is the second
copy this project keeps paying for.

- **`tools/githooks/pre-commit` runs `--fast`**, about 39 s.
  **`tools/githooks/pre-push` runs the full suite** and refuses the push
  on any exit but 0, on a missing PASSED line, and on a PASSED line that
  says FAST TIER. `core.hooksPath` switches on both at once, so a clone
  gets the pair or neither.
- **Full is the default, and that is the point.** `python
  tools/smoke_test.py` with no argument runs everything, exactly as
  before. Only the pre-commit hook passes `--fast`, so Data, a forker,
  or a session that has never read this entry gets the whole suite by
  doing the obvious thing. A fast run prints `SMOKE TEST PASSED (FAST
  TIER)` with the number of checks it did not run, so it cannot be read
  as a full one in a log or a report.
- **The slow list is declared in one place and policed.**
  `smoke_test.SLOW_TIER` names each push-only check with the reason it
  is expensive, and a check in the FAST tier holds the `slow(...)`
  guards and that list to each other in both directions — the marker
  inventory's shape, for the marker inventory's reason. Moving a check
  into the slow tier without declaring it turns the suite red.
- **No check was deleted, weakened or thinned.** The tiers change WHEN
  a check runs, never what it asserts. Both tiers also assert the
  documents' check count against the FULL number, so a fast run cannot
  go green against a count it never reached.
- **What it costs, accepted by Data rather than discovered later:** a
  fault only those seven can see now lands at push time instead of
  commit time. The drop-marker hit area and the colony list's plating
  were both found by checks that are now push-only. That is tolerable
  only because the push gate is mechanical too — and it is why work
  order 158 proved both gates by walking a real fault through them
  rather than by reading the hooks.
- **The fresh-clone run did not move and is not replaced.** Work order
  157: the four faults where a check read the player's own files passed
  on the author's machine and failed in a clone, every time, and none
  was caught by the suite in any tier.

**Extended 22 September 2026, work order 162: the suite is a
directory, and there is a third way to run it that is NOT a gate.**
The two gates are untouched — the numbers only moved because the
machine and the suite did. What changed is where the checks live and
what a development run prints.

- **`python tools/smoke_test.py` is still the full suite** and still
  the default, and `tools/smoke_test.py` is still the path. The checks
  are in `tools/smoke_suite/` now, 91 modules, one group per screen
  plus a shared core, executed in file-name order into ONE namespace —
  which is what `main()` did with its locals, and changing it would
  have been a rewrite rather than a move.
- **The working rule for a session.** *During screen work iterate with
  `--screen <name>`; before every handoff run the full suite; the push
  gate stays mechanical.* That sentence is in `CLAUDE.md` in the same
  words, deliberately, because it is the habit a session forms on its
  first day and `CLAUDE.md` is what a session reads first.
- **`--screen <name>` narrows what a run PRINTS, never what it runs**,
  and says `SCREEN <name> ONLY — NOT A GATE` on its first and last
  line. It was going to skip the other screens' checks, and the
  measurement said no: this suite's checks share their fixtures
  through objects — `d.active`, an app, a laid-out screen — filled by
  method calls no name analysis can see, so one screen's dependency
  closure is 87 % of the suite under a practical rule and 96 % under
  the only sound one, and a narrowed run died on the galaxy map's own
  screen object. 157 had refused this shape once already, for its
  caching idea: *a check that inherits another check's app is a new
  class of fault this project has not had yet.*
- **The selector widens itself.** Before it narrows the output it asks
  git what has changed against HEAD — index, working tree and
  untracked alike — and if anything outside `screens/<name>/` and that
  screen's own check modules has changed it runs the FAST TIER with
  its full output and names the files that caused it. A screen's
  territory is one computed function, so a new screen needs no edit.
- **What it is worth, measured rather than claimed:** a `--screen`
  run prints about a third of the sentences a full one does, and that
  is the whole of the saving — the wall-clock time is the tier's. The
  reading is where the split pays: a check for one screen is now in
  that screen's own file, not somewhere inside 1.2 MB.

---

