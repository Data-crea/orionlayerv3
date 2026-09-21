# The smoke suite, measured

Work order 157 part 4, 21 September 2026. **Measure only — nothing in
the suite, the hook or the gate was changed by this part.** Data finds
the suite too slow for a commit gate; these are the numbers that
decision needs.

Method: `tools/smoke_test.py`'s own `main()` run from a driver that
replaces the module's `ok()` with a timing wrapper. The checks are
blocks inline in one `main()` of roughly twenty-one thousand lines,
and the only boundary the suite itself draws is the `ok(...)` that
closes each one — **so what is timed is the segment between
consecutive `ok()` calls**, which is that check's work plus any shared
setup sitting in front of it. That is the limit of the measurement and
it is stated here rather than discovered later. Nothing was timed
singly below that granularity.

---

## 1. The noise floor

Five full runs, unchanged tree, same machine, nothing else running.

| run | total |
|---|---:|
| 1 | 77.92 s |
| 2 | 77.63 s |
| 3 | 77.67 s |
| 4 | 78.13 s |
| 5 | 77.78 s |

**Mean 77.83 s, spread 0.50 s, standard deviation 0.20 s** — 0.64 % of
the mean. The suite is remarkably steady; a total-time difference below
about half a second is not a finding.

Per check, the spread across the five runs is much tighter: **median
0.0001 s, ninetieth percentile 0.0037 s**, single worst 0.35 s. The
per-check floor used in the rest of this document is **0.004 s**.

By that floor, 123 of the 243 checks are measurable at all. They are
**99.9 %** of the runtime. The other 120 checks together are **0.1 %** —
about eight hundredths of a second for half the suite.

---

## 2. Where the time goes

Median of five runs. Share is of the 77.8 s total.

| # | time | share | cumulative | check |
|---:|---:|---:|---:|---|
| 1 | 28.20 s | 36.3 % | 36.3 % | a click on the centre of a figure's visible area picks up that figure |
| 2 | 13.72 s | 17.7 % | 54.0 % | RETURN is the eighth cutout and behaves like one |
| 3 | 3.00 s | 3.9 % | 57.8 % | GAME menu frame: opening == the artwork's one hole |
| 4 | 2.19 s | 2.8 % | 60.6 % | a fallback says why: one log line per change of decision or reason |
| 5 | 2.19 s | 2.8 % | 63.5 % | sidebar research readout: the original's four cases |
| 6 | 2.01 s | 2.6 % | 66.0 % | figures sit on the plate's inner floor, row and held alike |
| 7 | 1.92 s | 2.5 % | 68.5 % | all 49 runnable tools import in a fresh process |
| 8 | 1.73 s | 2.2 % | 70.7 % | screen lifecycles (enter/update/render/click/resize) |
| 9 | 1.18 s | 1.5 % | 72.3 % | GAME menu frame drawn on the first opening |
| 10 | 1.08 s | 1.4 % | 73.7 % | help regions resolve (52 across 4 screens) |

**Two checks are 54 % of the suite.** Everything below rank ten is
under a second each, and the tail of 120 checks is rounding error.

---

## 3. What the slow ones read, and what they render

Measured by hooking `open()` and `pygame.image.load` and attributing
each first touch to the segment it happened in. The hook cost about
0.3 % of wall time — inside the noise floor, so the traced run is
comparable to the clean ones.

**The whole run touches 579 distinct files and opens them in 6 458
segment-file pairs** — an average file is first-opened in **eleven
different segments**. The most re-opened are the colony summary's own:
its `layout_reference.json` in 55 segments, `layout.json` in 48,
`boxes.json` in 42, its `frame.png` in 41, and the shared
`background_cockpit.png` in 50. **So the dominant cost is not unique
files, it is the suite standing an app and a screen up again and
again.** That matters for the options below: making the suite read
fewer files would not help much; making it build fewer screens would.

**Rank 1, the figure pick-up check (28.2 s).** It renders the whole
colony summary to a surface and then scans the rendered pixels with
numpy, for **one to twenty figures in every job column at three
resolutions** (1920x1080, 2560x1440, 3840x2160), and then does the
whole thing a second time with the player's extracted figures if they
are on the disk. It reads 116 files: the 54 population figures, the
colony frame, the shared background, and the screen's four JSON files.

**Rank 2, the RETURN cutout check (13.7 s).** Twelve resolutions, from
1280x720 to 3840x2160, each one a laid-out screen. 198 files, 185 of
them PNGs.

**Rank 3 and 9, the GAME menu frame (4.2 s together).** The frame
artwork loaded through the resource roots and then drawn, with the
metal's opaque pixels sampled off the result.

**Rank 7, the tool import check (1.9 s).** The only one in the top ten
that renders nothing: it starts 49 fresh Python processes.

---

## 4. The suite is 20 % slower on this machine than on a clone

Not a side finding — it decides how much of the rest of this document
can be trusted as "the" profile.

| | total | distinct files |
|---|---:|---:|
| with the population figures on disk | 77.78 s | 579 |
| with them absent, as in a fresh clone | **62.42 s** | 525 |

**Same 243 checks, both green.** The 15.35 s difference is almost
entirely rank 1: it falls from 28.20 s to 14.14 s, because its second
pass over the player's own extracted figures reports absence and stops
rather than running. The 54 files in the difference are exactly the 54
figures.

So **the gate costs Data more than it costs a forker**, and the extra
is a measurement that only exists where an extractor has been run.

---

## 5. Could a check be mapped to its files by computation?

**Yes, mostly, and the mapping is cheap.** Static imports come out of
`ast`; the files a check actually opens come out of an `open()` hook,
which cost 0.3 % of wall time to collect — inside the noise. The data
in section 3 *is* that mapping, built in one run.

**But it is unreliable in four ways, and one of them is fatal on its
own.**

**(a) A path that does not exist yet — this is the fatal one.** The
suite contains thirteen whole-tree `os.walk` sweeps and sixteen further
`glob`/`listdir` sweeps. Those checks do not depend on a list of files;
they depend on *whatever is in that directory*, and their entire job is
to notice something NEW. The marker inventory walks every `.py` and
`.json` for HD EXTENSION and DEVIATION and compares the set against its
declared list. The briefs index asserts every file in `doc/briefs/` is
linked. The line-count list asserts every file over the guideline is
named and every named file is over. **A map keyed on paths cannot list
a path that is not there**, so adding a new screen's `boxes.json`, a
new module carrying a marking, or a new brief would select none of the
checks that police exactly that. Twice in the last two work orders the
briefs-index check went red on a file added minutes earlier — under a
computed map, neither would have run.

**(b) The map encodes the machine that built it.** Section 4 measures
this: 579 files here, 525 on a clone, 54 that exist only where an
extractor has been run. The fundament records four separate occasions
when a check passed here and failed in a clone, *each caught by the
fresh-clone run and never by the suite*. A dependency map computed on
Data's disk would inherit that fault and make it harder to see.

**(c) A run records only the branches it took.** This is the
fundament's own rule about byte-identity, in a new place: the map shows
the files a check opened *on the path it happened to take*. A check
with a present/absent fallback opens different files in each state.
`core/lbx.py`'s palette byte order is the precedent — weeks of
byte-identical regeneration because the branch was never taken once.

**(d) Import-level dependency is true but useless on its own.** One
segment already touches 212 `.py` files. Anything that imports `core/`
pulls in most of the tree, so a rule of "a shared file changed, run
everything" would fire on nearly every commit — which is safe, and is
also the full suite with extra steps.

**The two cases the order names, tested against this:**

- **The split delivery that broke the sidebar** — package B's
  `screen.py` calling a function that only existed in package A, with
  the failure surfacing in the sidebar, nowhere near the cause. A
  computed map **would** have caught this, *provided imports are in
  it*: the sidebar check statically imports the module whose function
  moved. This case argues for including static imports, not against
  the idea.
- **A New Game box failing another resolution's panel check.** The
  check walks every resolution in one `boxes.json` and asserts the rule
  — every `inner_panel` box inside a `thin_border` box — rather than a
  list. A **file-level** map survives this, because the changed box and
  the failing assertion are in the same file. Anything **finer** than
  file level does not: map a check to "the 1920x1080 block" and a box
  edited at 1080p stops selecting the check that fails at 1440p. So if
  a map is built, file granularity is the floor, not a starting point.

---

## 6. Options for Data

No recommendation, and none of these is implemented. Each names what
it would have missed among failures this project has actually had.

### Option A — a fast tier for the hook, the full suite before push

Drop the two heaviest checks and the frame-drawing ones from the
commit gate; run everything before a push. Ranks 1 and 2 alone are
**54 %**: the gate would fall from about 78 s to about 36 s, and
dropping the top ten would put it near 20 s.

**What it would have missed.** The marker-width fault — the drop
marker was two pixels wide in the hit test and a full square on
screen, every count on screen correct — was caught by rank 1, the
check that samples each drawn cell's own pixels and asks what picks up
there. Under this option that lands at push time instead of commit
time, with however many commits already stacked on top of it. The same
goes for the three days when the colony list plated only the occupied
bands while three documents said otherwise.

**What it would NOT make worse:** the four clone-only faults. Those
were never caught by the suite in any tier — only by the fresh-clone
run. This option does not touch that, and nothing in this profile
suggests the fresh-clone run should move.

### Option B — change-based selection, with "shared file → run everything"

Compute the map in section 5, select the checks whose files a commit
touches, and fall back to the full suite whenever a shared file moves.

**What it would have missed.** Section 5(a): everything a directory
sweep polices. A new module carrying a marking would not select the
marker inventory; a new brief would not select the index check — and
that check went red on exactly that, twice, in the last two work
orders. It is repairable only by a second rule — *any added or deleted
file runs everything* — and once that rule is in, the option mostly
degrades to Option A with more machinery. Section 5(b) applies too:
the map is built on Data's disk and would carry his file set into the
gate.

### Option C — move the two heavy checks' breadth, keep the checks

Leave every check in the gate but cut what the two big ones sweep:
rank 1 at one resolution instead of three and a sampled figure count
instead of one-to-twenty; rank 2 at three resolutions instead of
twelve. The full sweep runs before a push. Roughly 30 s saved without
removing a single check from the commit gate.

**What it would have missed.** Breadth is where both of these earned
their keep. Rank 2's twelve sizes exist because faults in this project
land at *particular* resolutions — 1366x768 is where the Planets
hover/draw mismatch was worst, at 24 disagreeing pixel rows, and it is
not one of the three resolutions anybody renders by hand. Rank 1's
one-to-twenty sweep is a count sweep, and the plating fault was exactly
a count fault: seven colonies drew seven bands where ten were owed. A
sampled version of either check would probably still have caught its
own famous failure — but "probably" is the whole of what this option
costs, and it is not measurable in advance.

### A note that belongs with any of them

The profile says the cost is **standing screens up repeatedly**, not
reading files: 579 distinct files opened 6 458 times, the colony
summary's own JSON re-read in over forty segments each. None of the
three options above addresses that, and a fourth — caching a laid-out
screen per resolution across checks — would cut more than any of them.
It is not offered as an option because it changes how checks are
isolated from one another, and a check that inherits another check's
app is a new class of fault this project has not had yet.
