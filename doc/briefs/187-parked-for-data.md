# Work order 187 — parked for Data

Every item names the default this run continued with and why. First what
this order decided or left open, then the items carried over unchanged.

## 1. From this order

### 1a. The original outside F12 — six paths, one rule proposed (Part 6)

`doc/briefs/187-original-visibility.md`: six paths still show the game's
picture without F12 (three seen in walks: a screen with no HD version, a
box over an HD page, a box over the map). **Proposal**: never show the
picture — HD's last frame dimmed, with a one-line notice naming what the
game waits for and "Press F12 to answer it"; then one HD message box fed by
open fix 29 ("A native message box's text is not in the snapshot"); then HD
screens for the turn-time ids by frequency. **Default: unchanged** (the
order: inventory, no change) — so until Data decides, paths 1, 4 and 5
still show the picture, which is against his rule.

### 1b. Option C and the rule (Part 1)

Option C, approved in this order, is built: a modal box over an HD screen
now appears after ~0.4-0.7 s instead of ~2-4 s. But what appears is still
the GAME'S picture of the box — the order's own rule forbids that outside
F12. The two cannot both hold until HD draws those boxes (1a's step 2:
one HD message box on open fix 29). **Default: option C as approved**; the
rule's answer is 1a.

## 2. Questions

### 2a. The audience menu's title colour (Part 4)

The original prints "How may I serve you:" in the items' own green; HD
draws it in the HUD's label blue above white items. Same colour as the
items (white)? **Default: as built** (the order asked about disabled items
only).

## 3. Carried over unchanged (not acted on in this order)

- **From 185** (`doc/briefs/185-parked-for-data.md` item 2c, "The Ship
  Designer live test (part 8) — three differences, as questions", and 2d,
  "The audience live test (part 11) — questions"): the chosen hull only
  faintly marked (default: as built); the audience's header line not drawn
  (default: not added), its fade-in and talking animation not played
  (default: still).
- **The extra slot message after ESC in the load dialog** — `doc/briefs/
  179-parked-for-data.md` item 1, "Open fix 34's ESC side effect — ask Joes
  for a reset? (default: no)". Default: leave it.
- **Narrow buttons with the word only** — decision 71, "The cockpit frames
  give way to ONE FRAMELESS STYLE, drawn in code, on every screen.".
  Default: unchanged until icons arrive.
- **Buildings as a list instead of the grid** — open fix 36, "Where the
  colony screen puts its buildings", applied and unused; UNVERIFIED
  `building_placement`. Default: unchanged.
- **Plague and population boom not yet seen live** — open fix 37, "The
  colony screen's Plague and Pop Boom word". Default: unchanged until a
  save has one.
- **The research query at turn start not measured** — `doc/briefs/
  184-parked-for-data.md` item 2, "The turn-start research prompt was not
  measured live" (it would write SAVE10). Default: not measured.
