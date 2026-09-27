# Work order 180 — parked for Data

Ordered by importance, as the order asks: engine patches to approve, with
what each one unlocks; then the proposed decision text from A2; then
everything else. Every item names the default this run continued with.

## 1. Engine patches to approve

A series, open fixes 35-40, each one file (`src/ext/ext_api.cpp`), each
an optional block appended to the snapshot only while its screen is up,
each proved to apply (in order, on `9ab84230`, no offset, no fuzz) and to
compile with the engine's own flags with a misspelt-constant control
refused. Entries: `doc/orion2re_open_fixes.md` 35-40. **Default this run
continued with: none applied**; the HD screens that use them are built,
checked against recordings from a scratch build, and claim nothing on
Data's engine.

1. **Open fix 35 — which colony the colony screen and the build popup
   show ("COLS", `doc/ext_colony_screen_colony.patch`). THE SINGLE MOST
   IMPORTANT ITEM OF THIS ORDER.** The colony (`_screen_data`,
   `_orbit_temp`, `_colony_handle`) is not on the wire, the game enters
   screen 1 from eight places, several of its own, and HD must not guess
   it. **Unlocks:** the whole HD colony screen (`screens/colony/`) — and,
   with 39 and 40, the build popup. Without it both stay the game's own
   picture (the safety net, no flash).
2. **Open fix 39 — the build popup's queue under edit ("BLDQ",
   `doc/ext_build_popup_queue.patch`).** `_current_item` only reaches
   `producing[]` on OK. **Unlocks** (with 35 and 40): the HD build popup's
   queue, selection box and Auto Build state.
3. **Open fix 40 — the build popup's two lists and its queue, with their
   costs and times ("BLDL", `doc/ext_build_popup_lists.patch`).**
   **Unlocks** (with 35 and 39): the HD build popup's lists in the game's
   own order and the summary's numbers.
4. **Open fix 38 — the current product's cost and turns ("CPRD",
   `doc/ext_colony_product_cost.patch`).** **Unlocks:** the colony
   screen's production bar and turn count, the popup's "Turn(s) Left".
   Without it: the product is named, the bar and turns are HD STATE.
5. **Open fix 37 — Plague and Pop Boom ("CEVT",
   `doc/ext_colony_status_word.patch`).** **Unlocks:** the status word's
   two event states. Without it: Blockaded only, the rest HD STATE.
6. **Open fix 36 — where the buildings stand ("CBLD",
   `doc/ext_colony_building_placement.patch`).** **Unlocks:** nothing yet
   — its cells are verified against the live fields, but the grid holds
   housing and jittered satellites too and named Star Base twice where the
   scene shows it once, so HD keeps its list (UNVERIFIED
   `building_placement`). Worth applying only together with a reading of
   `Make_Bldg_Array_For_Colony_` that settles what a cell means.

## 2. Proposed decision text (A2) — number left free

> **N. A screen HD draws never presents a native frame.** Work order 180,
> Data's rule, after the Fleets screen flashed the game's own picture with
> OrionLayer's sentence on the left (`doc/briefs/180-flash-findings.md`).
>
> While a transition waits for the data an HD screen needs, the window
> keeps showing the last HD frame, or the universal background, and takes
> no input. The game's own picture is shown only for a screen or a modal HD
> has no view for at all — for an id no HD screen claims, as soon as its
> list holds something to answer; for a modal net's verdict, after the
> hold. If a known screen's data does not arrive within the hold (36
> snapshots, about two seconds), the picture is shown once, logged, and
> counted as a failure — never as normal behaviour.
>
> It is decided in ONE place, `core/handover.py`, asked by
> `main.App._showing_original` for every way into the game's picture, so a
> new screen is under the rule without doing anything. The hold counts
> snapshots, not seconds (decision 21): a load or a turn is silence, not a
> failure. Marked **DEVIATION `hold_last_frame`** — the original has no
> second picture to wait with. A smoke check replays recorded transitions
> for every screen in the registry and fails on a native frame, on a
> fallback, on a registry screen with no recorded transition, and — to
> prove it can fail — when the hold is taken away.
>
> What it costs, on record: for at most two seconds after a transition the
> window may show the previous screen and ignore a click or a key; a modal HD does
> not know appears that much later than the game shows it.

**Default this run continued with:** the rule is implemented exactly as
written above (`core/handover.py`, check 090o); the text sits in the
status document's "No native frame on a screen HD draws" entry until Data
files it with a number.

## 3. Everything else

- **A key or click during a hold is dropped** (found live, A2). The main
  menu's opening animation is held for up to 24 snapshots; an L pressed
  then did nothing, where the original would have opened Load. The
  decision text says a held frame "takes no input". **Default:** as
  written — a click on a stale picture is not a choice. The alternative
  is to forward keys (not clicks) to the game during a MODAL hold only.
- **The colony screen's CHANGE is sent as its field, not the key C**
  (DEVIATION `change_by_field`): C reaches `[5]`, recalculate, first
  (reading §2a, "NOT SETTLED live" there — not driven live here either,
  on purpose: `[5]` is `Do_Cheats_` with `_cheats`). **Default:** the
  field.
- **The build popup's ship rows are never dimmed** (DEVIATION
  `ship_row_dim`): the original's rule calls `Colony_Can_Build_Product_`
  and compares design sizes with the colony's bases. **Default:** all
  bright. Corsair and Paladin are dim in the native popup of Sol II.
- **Omitted on both screens, each marked:** the product picture, the
  officer portrait, the unit sprites, the roads, the popup's description
  (HELP.LBX by tech application) and a design's stat lines, the original's
  own-pointer hover strip and "delete %s" hint. **Default:** not drawn.
- **Loading a slot rewrites MOX.SET** (`loadsave.cpp:357-359`); every
  guard of this order restored the one byte. Written into part 09.
- **The engine's window at startup (A1 part 3).** It is mapped when the
  engine starts and stays the top X window until OrionLayer's window maps,
  and once more for 72 ms while SDL recreates the pygame window. It never
  comes forward during play. Measured with the screen LOCKED, so focus on
  an unlocked desktop was not observable. **Default:** nothing changed —
  it is not the flash Data described, and hiding it is an engine change.
  Whether it is worth one is Data's call (a flag that sets `g_hide_window`
  before `SDL_ShowWindow`, platform.cpp:1406-1408).
