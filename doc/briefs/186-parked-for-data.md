# Work order 186 — parked for Data

Every item names the default this run continued with and why. First what
this order decided or left open, then the items carried over unchanged.

## 1. From this order

### 1a. Open fix 42 — not approved, not applied, stays open

Entry 42, "A screen is silent on the wire while its input delay counts
down": NOT APPLIED, its row and `version_check`'s `REPORTED_PATCHES` as
before; nothing in this run builds on it. Part 4 measures whether the
modal hold depends on it (see there). **Default: open.**

### 1b. The bundles' names

The order's pattern is `~/orion2re_bundle_<date>_<hash>_fixes34-<last>.bundle`.
Fix 42 is in none of the bundles, and the last fix applied is 43, which is
lower than 47 — so the five are named `…_fixes34-44`, `-45`, `-46`, `-47`
and `…_230a0638_fixes34-47_43.bundle`, the last saying that 43 came after
47. **Default: as named**; README names the newest.

### 1c. Name entry on the HD designer page — build it? (Part 3)

**Measured**: typing a name works through **F12** on the game's picture
(after this run's fix to the safety net): an injected click opens the
original's field, keys append, Enter commits, the HD page then shows it.
The HD page itself shows the name and does not edit it (OMISSION
`name_entry`): the text being typed is the engine's `_continuous_string`,
on no block — the wire carries the name only once committed. Options: (a)
as now — F12 for the name; (b) a click on the HD name hands over to the
game's picture until Enter (the modal-net shape, no new data); (c) HD
echoes the typed keys itself — an INVENTION the wire cannot confirm until
Enter; (d) an open fix sending `_continuous_string` while a field is open.
**Recommendation: (b)**, no engine change and nothing drawn that the
engine did not say. **Default: (a)**, unchanged.

### 1d. The AI's turn-start audience (58) — not reachable in SAVE4 / SAVE5

Ending one turn: SAVE4 stops at "Select planet for Colony Base in Malus
system" (place or scrap — a game decision; work order 122's dialog),
SAVE5 at "CyberToller select combat at peren" (a battle). Nothing was sent
to either. **The save it needs**: a scratch save whose next turn has no
pre-turn decision and no combat, and whose turn start carries an AI
diplomacy message — or permission to make one decision (place the colony
base in SAVE4 on a named planet, or auto-resolve SAVE5's battle) and end
the turn. **Default: parked**; the screen is the same as 57's.

### 1e. Multi-buttons (type 3) through the safety net — a question

The designer's hull buttons are multi-buttons, resolved in the mouse path
an activation skips (the HD page sends them by injected click). Through
F12 the safety net still sends an activation for them. By the source the
same fix as for string fields applies; **not measured** in this run.
**Default: unchanged** until measured.

### 1f. In memory during the designer test

Build wrote two designs into the loaded scratch game's slots 1 and 2 (the
first one a Cruiser "Interceptor" by the fault above) — in memory only,
never saved; the engine was then stopped. Noted for completeness.

### 1g. The hold before modal boxes — a decision (Part 4)

Measured (`evidence/work_order_186/P4/report.md`): every modal box over an
HD screen appears ~4 s after the input — the gate holds 36 snapshots, a
hold meant for late data that a modal never sends, at the box's own ~106-113
ms pace; an id no HD screen claims appears at once (0.14 s). Not related
to fix 42. Options: A as now (~4 s); B show at once (~0.1 s); **C show once
the list has stood `SETTLE` snapshots, counted in snapshots as documented
(~0.5 s)**; D a short `HOLD` for modals only (~0.5 s, two mechanisms for
one job); E hold in seconds (against decision 21). **Recommendation: C.
Default: A — nothing changed** (the order: measure only).

## 2. Questions from the side-by-side (Part 3)

### 2a. The audience

1. **The disabled "Peace Treaty"** is drawn light blue in HD, which reads
   like a highlight; the original prints it darker than the other items.
   Dim it instead? **Default: as built.**
2. (carried from 185, unchanged) the header line and the fade-in / talking
   loop — section 3.

### 2b. The designer

Nothing new: HD 186 is pixel for pixel HD 185 on every state 185 had.
185's two questions stand (section 3).


## 3. Carried over unchanged (not acted on in this order)

- **From 185** (`doc/briefs/185-parked-for-data.md` item 2c, "The Ship
  Designer live test (part 8) — three differences, as questions", and 2d,
  "The audience live test (part 11) — questions"): the chosen hull only
  faintly marked and its words small (default: as built); the audience's
  header line not drawn (default: not added), its fade-in and talking
  animation not played (default: still).
- **The extra slot message after ESC in the load dialog** — `doc/briefs/
  179-parked-for-data.md` item 1, "Open fix 34's ESC side effect — ask Joes
  for a reset? (default: no)". Default: leave it.
- **Narrow buttons with the word only** — decision 71, "The cockpit frames
  give way to ONE FRAMELESS STYLE, drawn in code, on every screen.".
  Default: unchanged until icons arrive.
- **Buildings as a list instead of the grid** — open fix 36, "Where the
  colony screen puts its buildings", applied and unused; DEVIATION
  `building_list`, UNVERIFIED `building_placement`. Default: unchanged.
- **Plague and population boom not yet seen live** — open fix 37, "The
  colony screen's Plague and Pop Boom word". Default: unchanged until a
  save has one.
- **The research query at turn start not measured** — `doc/briefs/
  184-parked-for-data.md` item 2, "The turn-start research prompt was not
  measured live" (it would write SAVE10). Default: not measured.

