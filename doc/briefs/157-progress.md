# Work order 157 — progress

Unattended run, 21 September 2026. Updated after each part.

---

## Part 1 — close 156 with C — **DONE**

**Commit `1be0af0`.** Suite green, 243, count unchanged.

`RowBoxes` loses `growth` and `beyond`. Both were constants at both
construction sites since `514ebb2` (8 September) and carried no
marking; both belonged to the HD allocation bar, an INVENTION, and the
original's row draws population sprites only
(`Do_Colony_Info_Pop_Stuff_For_Pop_`, coldraw.cpp:282).

**What replaced the suite's assertion.** It asserted `not
_boxes.growth` per fixture. That is now `"growth"` and `"beyond"` not
in `RowBoxes._fields`, placed beside the `markers` assertion of 8
September that it is modelled on. **Strictly stronger**: the old one
said the field was empty for the rows that block happens to build, the
new one says the field cannot come back at all. No check was added or
removed — the count is 243 either way.

**The rewritten note**, first line in both `colonytrack._column_boxes`
and `v3_projektstatus.md`: *"A PER-ROW CAPACITY DISPLAY IS AN OPEN
DESIGN QUESTION FOR DATA."* It then records that the original shows
headroom only as a number in the scan box for the scanned colony
(`Draw_Colony_Scan_Info_`, colsum.cpp:1155), so a per-row display
would be a **marked HD EXTENSION**; that if it comes it is built new
against the six column boxes and does not bring back `growth`,
`beyond` or `growth_gap`; and where the old code is —`514ebb2`'s
parent for the bar, `1be0af0` for the fields.

**Render identity**: 16 PNGs at four resolutions, byte-identical, in
**both** input states (54 figures present; directory moved aside for
the coloured-cell fallback). The two states are different pictures, so
both branches were exercised. Evidence:
`~/orionlayer-fixtures/evidence/work_order_157/part1_rowboxes_render_identity.txt`.

**Nothing surprising.** Full-project grep found exactly one consumer
of either field (the suite's per-fixture assertion) and no positional
unpacking of `RowBoxes` anywhere.

C is marked resolved in `156-parked-for-data.md` with the hash.

---

## Part 2 — T3, the check that could go green measuring nothing — **DONE**

**Commit below.** Suite green, 243, count unchanged.

**The gap, shown before it was fixed.** `ships._lift` was halved —
`c * 0.5` instead of `c + (255 - c) * keep` — which on the real screen
draws **every player fleet on the galaxy map at half its tint**. The
suite ran green: `SMOKE TEST PASSED — 243 checks green`. The check
named "player colours: no preset ship is darker than the darkest
original ship" tinted by hand with
`_o.fill(playercolors.lift(tint, keep), BLEND_RGB_MULT)`, retyping
**both** halves of `TintCache.get`, so it measured `playercolors.lift`
while naming the ship tint. Nothing else in the suite called `_lift`
or `TintCache` at all — verified by grep, and that is why the drift
was invisible rather than merely unasserted.

**The repair.** The check calls `ships.TintCache().get(...)` itself,
with the preset colour placed in `ships.SHIP_COLORS` (which is where
`TintCache.get` reads a colour from, by index). A **fresh cache per
call**, because its key is `(cache_key, w, h, idx)` and the colour is
not in it — a shared cache would hand back the first preset's sprite
for every later one, which would be this same fault in a new place. It
also asserts that `get` did not hand back the untinted base, which is
what it does when `SHIP_COLORS` has no entry for the index and would
otherwise measure the grey sprite and pass.

**Caught: no before, yes after.**

| run | check | result |
|---|---|---|
| drift applied | original | **PASSED — 243 green** |
| drift applied | repaired | **AssertionError** — `okabe_ito 0.png: darkest preset ship 0.0182 below the darkest original 0.0188` |
| no drift | repaired | PASSED — 243 green |

The third row matters as much as the second: the repair did not change
the verdict on correct code, only on wrong code.

Evidence: `part2_step1_gap_not_caught.txt` and
`part2_step2_drift_caught.txt` in
`~/orionlayer-fixtures/evidence/work_order_157/`. Both drifts were
reverted with `git checkout` and the file's SHA-256 checked back to
its baseline each time, with every `__pycache__` cleared and every run
made with `python -B` — the stale-bytecode trap of work order 128 B.

**THE SURPRISE, and it is the same shape as 156's.**
`assets/shared/skins/default/colors.json`, under
`player_presets.rule._k_ship_protocol`, already said the criterion was
*"Measured … through ships.TintCache's own path (TINT_KEEP_WHITE lift,
then BLEND_RGB_MULT)"*. **It was not.** No check in the tree touched
`TintCache` or `_lift`. The note was true of the intent and false of
the code, and it had been since 14 September. The repair makes it
true, so the note needed no edit — which is the only reason this one
did not also become a documentation correction.

**Parked:** whether the two `lift` functions should be *merged* is a
design decision, not a repair, so it went to
`157-parked-for-data.md` with both options. The check no longer
depends on them agreeing either way.

---

## Part 3 — D17 — **PARKED**, no code

**Which way and why.** The order's rule: behaviour-neutral removal or
correction gets done here; anything that adds behaviour, adds a check
with a design choice in it, or closes an option gets parked. D17 hits
all three tests, and one of them is new since the audit.

**It is four construction sites now, not three** —
`galaxy_map/boxdraw`, `game_menu/screen`, `planets/planetwords`, and
**`screens/fleets/screen.py`**, which 157 may not touch because work
order 151's line is active there. Consolidating the other three would
leave the duplication standing while reporting it removed, which is
worse than leaving it alone.

**The three lifetimes are the substance.** Screen-cached, app-cached,
and fresh per Planets `enter`. Choosing one home decides when the
table is re-read and when it is dropped — memory and invalidation, not
tidiness.

**And unifying the language lookup would change behaviour.**
`colonybuild` uses `screen.app.settings.get(...)`, which raises where
the other sites' `(getattr(app, "settings", {}) or {})` defaults.
Today a missing `settings` crashes there; making them agree decides
whether it still does.

**One thing checked and found NOT wrong:** `core/screenhelp.py`'s
"exactly one construction site" is about `HelpText`, which genuinely
has one. The audit's phrasing invites reading it as a claim about
`HStrings`; it is not, so unlike 156's `FRAME_TITLE` and part 2's
`_k_ship_protocol`, there was no false claim to correct here.

Parked in `157-parked-for-data.md` with the two-sentence German
summary the order asks for, plus what Data has to decide first.

---

## Part 4 — profile the suite — **DONE**, measure only

**Commit below.** Nothing in the suite, the hook or the gate changed.
Full brief: `doc/briefs/157-suite-profile.md`. Raw data and the driver:
`~/orionlayer-fixtures/evidence/work_order_157/suite_profile/`.

**Noise floor.** Five full runs: 77.92, 77.63, 77.67, 78.13, 77.78 s.
Mean 77.83, spread 0.50 s, stdev 0.20 s — 0.64 % of the mean. Per
check the ninetieth-percentile spread is 0.004 s, and that is the floor
used throughout. 123 of 243 checks are measurable above it; they are
99.9 % of the runtime, and the other 120 together are 0.1 %.

**Granularity, stated as a limit.** The checks are inline blocks in one
`main()` of about twenty-one thousand lines; the only boundary the
suite draws is the `ok(...)` that closes each check. So every number is
a **segment** between two `ok()` calls — that check's work plus any
shared setup in front of it. Nothing finer is measurable without
changing the suite, which this part was not allowed to do.

**Three slowest, against the floor.**

| | time | share | cumulative |
|---|---:|---:|---:|
| figure pick-up (1–20 figures, 3 resolutions) | 28.20 s | 36.3 % | 36.3 % |
| RETURN cutout (12 resolutions) | 13.72 s | 17.7 % | 54.0 % |
| GAME menu frame opening | 3.00 s | 3.9 % | 57.8 % |

**Two checks are 54 % of the suite.**

**THE SURPRISE, and it is the third of this run.** The suite is
**62.42 s on a clone against 77.78 s here** — same 243 checks, both
green. Almost all of the 15.35 s is the figure pick-up check, whose
second pass over the player's own extracted figures reports absence and
stops where the files are missing. 579 distinct files are touched here,
525 without them, and the 54 in the difference are exactly the 54
population figures. **The gate costs Data twenty per cent more than it
costs a forker**, and the extra is a measurement that only exists where
an extractor has been run.

**The dependency question: yes, computable; unreliable in four ways,
one of them fatal.** Imports from `ast`, opened files from an `open()`
hook costing 0.3 % of wall time. But thirteen `os.walk` sweeps and
sixteen `glob`/`listdir` sweeps depend on *whatever is in a directory*,
and their job is to notice something NEW — **a map keyed on paths
cannot list a path that is not there**. The briefs-index check went red
on a just-added file twice in the last two work orders; under a
computed map neither run would have happened. The other three: the map
encodes the machine that built it (measured above), a run records only
the branches it took, and import-level dependency pulls in most of the
tree at once.

The two cases the order names both got tested. The split delivery that
broke the sidebar **would** have been caught, provided static imports
are in the map — which argues for including them. The New Game
resolution case survives at **file** granularity and breaks at anything
finer, so file level is the floor and not a starting point.

**Three options for Data**, each naming what it would have missed:
a fast tier for the hook (misses the marker-width and plating faults at
commit time, does not make the clone-only faults worse); change-based
selection (misses everything a directory sweep polices); cutting the
two heavy checks' breadth (breadth is where both earned their keep —
1366x768 and the one-to-twenty count sweep). A fourth is described but
not offered: caching a laid-out screen across checks would save more
than any of them, and would create a class of fault this project has
not had.

---

## Finish

### Line count — 157's column beside 156's

`tools/linecount.py`, same method as 156: `ast` docstring spans, then
blank, then whole-line `#`, then CODE; `linecount.walk()` over its own
`ROOTS`; `tools/smoke_test.py` on its own row because it is
`linecount.EXEMPT`.

**CODE lines:**

| folder | before 156 | after 156 | **after 157** | 157's delta |
|---|---:|---:|---:|---:|
| `(root)` — `main.py` | 323 | 323 | **323** | 0 |
| `core/` | 6 372 | 6 360 | **6 360** | 0 |
| `screens/` | 11 743 | 11 726 | **11 726** | 0 |
| `tools/` without the suite | 8 678 | 8 678 | **8 678** | 0 |
| `tools/smoke_test.py` | 14 702 | 14 702 | **14 719** | **+17** |
| **TOTAL** | 41 818 | 41 789 | **41 806** | **+17** |
| **TOTAL without the suite** | 27 116 | 27 087 | **27 087** | **0** |

**157 added 17 code lines and removed none, and every one of them is
in the suite** — the repaired tint check of part 2. Outside the suite
the tree is byte-for-byte the same size it was after 156: part 1
removed two namedtuple fields without removing a line (the fields were
names in one declaration and constants at two call sites), part 3 was
a park, and part 4 changed nothing.

Total lines rose by 78 (76 311 → 76 389), which is the rewritten note
in `colonytrack.py` and `v3_projektstatus.md` plus the repaired
check's reasoning. **That is the shape this order had: it is not a
line-reduction order.** 156 was, and it took 29.

The over-guideline list is unchanged: 10 files over 300 CODE lines.

### Fresh-clone verification, both input states

`git clone` of `9b2b721`, then `python tools/setup.py`.

| state | figures | result |
|---|---:|---|
| as a forker gets it, no player extractions | 0 | **243 checks green** |
| with the player's figures copied in | 54 | **243 checks green** |

Both states pass in a tree that was never the working tree. The second
state matters here specifically: part 4 measured that the figure
pick-up check takes a **different path** depending on those 54 files,
so a clone check in one state only would have exercised one of them.

### Push

Everything from 156 and 157 together, as the order authorises.
