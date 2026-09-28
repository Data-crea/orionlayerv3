# Work order 187, Part 6 — where the original can still show without F12

Inventory, **no change** (Data decides). Data's rule (work order 187): the
player never sees any part of the original picture unless he presses F12.

## How the picture reaches the window — the one place

Every presented frame asks `main.App._showing_original()` (main.py), and
the answer goes through the hand-over gate (`core/handover.decide_for`,
work order 180 A2, "A screen HD draws never presents a native frame"). The
window shows the engine's framebuffer (`core/original_view.render`) in
exactly three cases, each then gated:

| way in (`frametrace` kind) | condition in the code | gate |
|---|---|---|
| `f12` | `render_mode == "original"` (F12) | never held — **allowed** |
| `no_screen` | `dispatcher.use_original` — no HD screen claims the id (dispatcher.py:225-244) | shown at once when the list has a field to answer; held while empty, up to `EMPTY_HOLD` = 36 snapshots, then shown anyway |
| `hand_over` / `modal` | the top screen's `wants_original()` (main.py) | `modal` (a net's or a `GAME_BOX` verdict): held `HOLD` = 36 snapshots, a BOX released after `MODAL_SETTLE` = 5 unchanged snapshots (work order 187, option C); `hand_over`: held 36, then shown once and counted as a failure |

Not a path: disconnected — `_showing_original` answers False, the window
shows HD or the fill. A HELD frame is HD's last frame or the universal
background (`handover.render_hold`), never the picture. The engine's OWN
window is a separate matter: hidden when OrionLayer starts it (open fix
43), shown on F12, visible only when the player starts the engine by hand.

"Seen" below is from the gate's own log lines and the frame traces in the
evidence of work orders 180-187 (`handover: released`, `FALLBACK:`,
`modalnet:`; transition tables' `native_total`).

## The paths

### 1. A game screen with no HD screen at all (`no_screen`, list answerable)

- **Where**: `core/dispatcher.py:225-244`; `core/screen_names.SCREENS`
  names the ids — without an HD folder: 7 EXIT, 12 NEXT_TURN (turn
  processing: the combat choice, 186), 14 HALL_OF_FAME, 18 PLANET_DATA,
  30 COLONIZATION_IN_MAIN, 39 REPORTS, 40 TURN_SUMMARY, 52 (the turn-start
  research query), and every id the table does not list (33, the colony
  landing screen, work order 123; the GNN; combat itself).
- **When**: whenever the game enters one — mostly at and after TURN.
- **Seen**: yes — SAVE5's combat choice (12) shown 0.14 s after TURN (186
  part 4); 39 during every load, but always with an EMPTY list (held 1-3
  snapshots, never shown). The flash walks do not end turns, so the
  turn-time screens are otherwise unwalked.
- **Instead**: an HD screen per id (the real answer); until then HD keeps
  its last frame dimmed with a notice — "The game is showing *<name>*,
  which OrionLayer cannot draw yet. Press F12 to answer it." — so the
  original appears only on F12, and nothing is answered blindly.

### 2. An id with no HD screen and an EMPTY list, past `EMPTY_HOLD`

- **Where**: `handover.Gate.decide`, `kind == NO_SCREEN`, 36 snapshots.
- **When**: a screen without fields standing longer than 36 snapshots
  (a long non-input screen that still ticks).
- **Seen**: never released in any recorded walk (39 ends in 1-3).
- **Instead**: keep holding (the universal background) — there is nothing
  to answer on an empty list; no notice needed.

### 3. A known screen that declines its id (`claims` False) — becomes path 1

- **Where**: `ScreenBase.claims` overrides: `screens/colony` and
  `build_queue` (open fixes 35-40's blocks), `ship_design` (44's DSGN),
  `design_box` (45's DSBX), `audience` (46/47's DIPL).
- **When**: an engine without those fixes; on the current engine only on a
  first tick whose blocks are not settled — then the list is usually the
  previous screen's or empty.
- **Seen**: not on the current engine (every colony / designer / audience
  transition of 181-187: 0 native frames).
- **Instead**: hold HD's last frame with the notice of path 1 (the cause is
  an engine that lacks a fix: the notice can say which, as `version_check`
  does).

### 4. A box over an HD screen's own page (`modal`, a BOX)

- **Where**: the `GAME_BOX` states — `ship_design/sdwire.py`,
  `design_box/dbwire.py`, `colony/colwire.py`, `build_queue/bqwire.py`,
  `audience/auwire.py` — through `handover_is_modal()`/`modal_is_box()`;
  released by option C (work order 187).
- **When**: every warning, message or confirmation box the game opens over
  those screens (the designer's "You may not upgrade the ship's shield",
  the colony screen's refusals, the popup's messages, the audience's
  system picker).
- **Seen**: yes — the designer's shield warning, 10 releases in 185-187.
- **Instead**: an HD message box. Most of these are `TEXTBOX` / `GENDRAW`
  boxes whose only field is a full-screen hidden field (or Yes/No);
  **open fix 29, "A native message box's text is not in the snapshot"**,
  would put their text on the wire, and one HD box would then draw them
  all. Until then: HD's page dimmed with the notice of path 1.

### 5. A box over a screen with a modal net (`modal`, galaxy map / main menu / select race)

- **Where**: `core/modalnet.Net` in `screens/galaxy_map/mapmodal.py`,
  `main_menu/screen.py`, `select_race/screen.py`; a box once the screen's
  own list was seen (`Net.box`, work order 187), otherwise the full hold.
- **When**: the map's turn-time prompts (the colony-base choice, the
  "Really trash your colony base" confirmation, work order 122), messages
  over the menu; the main menu's opening animation (held and never shown —
  its own list comes after it).
- **Seen**: yes — the colony-base choice, 2 releases (186); the main
  menu's net fired in every start of 180-186 and was always held.
- **Instead**: as path 4 (open fix 29 + one HD box); the colony-base choice
  itself is a small HD dialog (a star's planets — already on the wire).

### 6. A known screen that cannot vouch for its data (`hand_over`, then FALLBACK)

- **Where**: `wants_original()` of `research_select` / `research_change`
  (`core/researchscreen.py:715`: the list contradicts its reconstruction,
  or an extractor file is absent), `ship_design` / `design_box` (extracted
  names or art absent), `fleets` (no fleet block), `leaders`, `races` and
  `info` (`raceswire.WAIT_BOUND`, `info.WAIT_BOUND`: a dialog they cannot
  name after the wait) — held 36 snapshots, then shown once as a counted
  failure.
- **When**: a player who has not run the extractors (a fresh install) — on
  every entry of those screens; the Races screen's own dialogs other than
  the audience (the race report); a research list HD cannot rebuild.
- **Seen**: no FALLBACK in any recorded walk of 180-187 (the tree has the
  extracted files); historically the research panel's entry (166 A, fixed).
- **Instead**: the missing-extractor case needs no picture at all — HD can
  say "run `tools/setup.py`" on its own screen (`setup.py` already names
  every extractor); the dialog cases need their HD view, and meanwhile the
  notice of path 1.

### 7. The safety net's input: keys and clicks while the picture shows

- **Where**: `main.py` (keys: `original_view.forward_key`; clicks:
  `forward_click`, work orders 130 A and 177).
- **When**: only while one of paths 1-6 shows the picture — it adds no
  picture of its own, but it is what "hand over to the original for input"
  consists of.
- **Instead**: disappears with the paths above; under F12 it stays.

## Count

**6 paths** by which the original can show without F12 (1-6); path 7 is
their input and adds none. **Seen in walks**: 1 (combat choice), 4
(designer's warning box), 5 (colony-base choice). **Never seen**: 2, 3, 6
on the current engine with the extracted files.

## Recommendation

1. **Now, one rule for all six**: never show the picture; keep HD's last
   frame (or the universal background), dimmed, with a one-line notice
   naming what the game is waiting for and "Press F12 to answer it". This
   is Data's rule literally — the original only on F12 — and it keeps the
   game answerable. It changes one place (`main.App._showing_original` /
   the gate), and the three kinds already say which path it is.
   **Needs Data's decision first** (it changes what a player sees at every
   box and turn-time screen).
2. **Next, one HD message box** for paths 4 and 5, fed by open fix 29 (the
   box's text on the wire) — it covers most of what the player meets.
   **Needs Data's decision first** (an engine fix).
3. **Then HD screens by frequency** for path 1: the turn summary (40), the
   combat choice (12), the colony landing (33), the research query (52).
4. Path 6's missing-extractor case: an HD "run setup" notice — no decision
   of Data's needed beyond 1.
