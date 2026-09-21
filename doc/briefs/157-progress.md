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
