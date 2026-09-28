# Work order 188 — parked for Data

Every item names the default this run continued with and why. First what
this order decided or left open, then the items carried over unchanged.

## 1. From this order

### 1a. Answered from 187 (no decision needed any more)

- 187's 2a, "The audience menu's title colour": the order decided it — the
  items' colour. Built (Part 2).

### 1b. The fleet box's ETA text on hover (Part 3)

The original also prints "%d turns to %s" / "%d parsecs to %s" / the refusal
in the fleet box while a star is hovered (fleetpop.cpp:1063-1091). FMOV now
carries every number it needs (turns_left, parsecs, flags). **Default: not
built** (the order asked for the line); the box keeps its status line.

### 1c. The turn-time screens that still show the F12 notice (Parts 4, 5)

Tactical combat (and combat's own boxes), the invasion / bombard choice,
ground combat, the galactic council, the Antaran room, the evolutionary
mutation picker, the monster bribe, the star rename, the occupation-policy
popup and the end of game run under 12 / 0 / 33 without an HD view: the
F12 notice stands there (Stage 1), so the game is answered on F12. What each
needs is in `doc/brief_turn_messages.md` ("What would need engine fixes" of
the reading: the council's state and lists, the combat popups' data, the
star name field). **Default: notice**; proposal: the council and the star
rename next (they appear in normal play without combat).

### 1d. The popups' artwork (Part 4)

The HD turn popups and the message box are HUD panels (DEVIATION
`hud_turn_popup`, `hud_message_box`): the science room, the GNN studio and
its picture, the colony landing art, TURNSUM.LBX, the BUFFER0.LBX frames and
the system display's planet pictures are not drawn — the system display is
a list of the star's planets by name. **Default: as built**; the pictures
are an extractor away if Data wants them.

## 2. Carried over unchanged (not acted on in this order)

- **From 185** (`doc/briefs/185-parked-for-data.md` item 2c, "The Ship
  Designer live test (part 8) — three differences, as questions", and 2d,
  "The audience live test (part 11) — questions"): the chosen hull only
  faintly marked (default: as built); the audience's header line (text) not
  drawn (default: not added), its fade-in and talking animation not played
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
- **The research query at turn start not measured** — `doc/briefs/
  184-parked-for-data.md` item 2, "The turn-start research prompt was not
  measured live". Default: not measured.
