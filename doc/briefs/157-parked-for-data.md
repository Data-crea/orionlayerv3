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

## 2. D17 — `HStrings` construction sites — **PARKED** (part 3)

**Auf Deutsch, für die Entscheidung:** `HStrings` wird an vier Stellen
gebaut statt an einer, mit drei verschiedenen Lebensdauern, sodass
Galaxienkarte, Spielmenü, Planeten und Flotten die Datei HESTRNGS
mehrfach in getrennte Objekte einlesen. Zusammenlegen ist keine reine
Entfernung, sondern eine Entscheidung darüber, **wem** die eine
Instanz gehört und wann sie geleert wird — und eine der vier Stellen
liegt in `screens/fleets/`, das dieser Auftrag nicht anfassen darf.

**Why it was parked, in detail — and one reason the audit could not
have known.**

1. **It is not three sites any more, it is four**, and the fourth is
   out of bounds. `screens/fleets/screen.py` builds its own
   `HStrings` per screen; work order 151's line is active there and
   157 may not touch it. Consolidating the other three would leave the
   duplication standing while reporting it removed — which is worse
   than leaving it, because the next reader would believe the claim.
2. **The three lifetimes are the substance, not an accident.**
   `galaxy_map/boxdraw` caches on the SCREEN, `game_menu/screen`
   caches on the APP, and `planets/planetwords` builds a fresh one on
   every Planets `enter`. Picking one home decides when the table is
   re-read and when it is dropped — a memory and invalidation
   question, not a tidy-up.
3. **One site would change behaviour if unified.**
   `colonybuild` reads `screen.app.settings.get("language", "en")`,
   which raises `AttributeError` where `boxdraw` and `game_menu` use
   the tolerant `(getattr(app, "settings", {}) or {})`. Making them
   agree means choosing whether a missing `settings` crashes or
   defaults — and today it crashes, so "fixing" it is a behaviour
   change.

**What is NOT wrong.** `core/screenhelp.py`'s "exactly one
construction site" is about `HelpText`, and `HelpText` genuinely has
one. The audit's phrasing invited reading it as a claim about
`HStrings`; it is not, so nothing needed correcting.

**If Data wants it done**, the decision to make first is where the one
instance lives — almost certainly the App, on `screenhelp.helptext`'s
model — and then whether the fleets site joins in the same commit,
which needs 151's line to be clear.

---

## 3. Still parked from 156, unchanged

**D–G** (the four extractions) stay parked — Data has not released
them, and this order explicitly leaves them alone. Their measured
sizes and the single condition each turns on are in
`doc/briefs/156-parked-for-data.md`.

**C is closed**, done in this order's part 1 (`1be0af0`).
