# Work order 157 — parked for Data

Unattended run, 21 September 2026. Nothing here blocked a later part.

---

## 1. T3 — should the two `lift` functions be MERGED? (part 2)

Part 2 shipped the check repair, as the order directs. **This is the
half that is a design decision, so it is parked rather than taken.**

`core/playercolors.lift(rgb, k)` and `screens/galaxy_map/ships._lift
(color, keep=TINT_KEEP_WHITE)` are the same arithmetic — names-only
copies, identical but for the parameter's default. Two copies, so the
third-copy rule has not fired. The repaired check no longer depends on
them agreeing, so **nothing is broken either way**; this is about
whether the tree should carry one function or two.

**Option A — leave them, two copies.** They belong to different
layers: `playercolors` is the palette machinery that derives a whole
skin, `ships` is one screen's tint with its own documented constant
(`TINT_KEEP_WHITE = 0.22`, with the reason for the value beside it).
Coupling them means the galaxy map's ship tint changes whenever the
palette module's helper changes, which is a dependency nobody asked
for. Cost: two copies that could drift — but after part 2 a drift is
*caught*, which is what made this worth raising at all.

**Option B — one function, imported.** `ships._lift` becomes a thin
call into `playercolors.lift` with `TINT_KEEP_WHITE` as the argument,
or disappears entirely and `TintCache.get` calls `playercolors.lift`
directly. Saves two lines. Cost: a screen module takes a dependency on
the palette module for one arithmetic expression, and the constant's
documentation has to move or be split from the code it explains.

**No recommendation.** Both are defensible and the check no longer
cares. Raised because 156 named T3 as the one parked group whose
failure mode was *a green check that means nothing*, and that half is
now fixed; what is left is taste.

---

## 2. D17 — three `HStrings` construction sites (part 3)

See part 3 in `157-progress.md` for which way it went and why.

**Auf Deutsch, für die Entscheidung:** `HStrings` wird an drei Stellen
gebaut statt an einer, und `screenhelp.py` verlangt im eigenen Text
„genau eine Konstruktionsstelle" — Galaxienkarte und Spielmenü lesen
die Datei HESTRNGS deshalb zweimal in zwei getrennte Objekte. Das
zusammenzulegen ist keine reine Entfernung: es legt fest, **wem** die
eine Instanz gehört und wann sie geleert wird, und eine der drei
Stellen (`colonybuild`) stürzt heute ab, wenn `settings` fehlt — das
zu ändern wäre eine Verhaltensänderung und keine Aufräumarbeit.

---

## 3. Still parked from 156, unchanged

**D–G** (the four extractions) stay parked — Data has not released
them, and this order explicitly leaves them alone. Their measured
sizes and the single condition each turns on are in
`doc/briefs/156-parked-for-data.md`.

**C is closed**, done in this order's part 1 (`1be0af0`).
