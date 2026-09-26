# Work order 180 — parked for Data

Ordered by importance, as the order asks: engine patches to approve, with
what each one unlocks; then the proposed decision text from A2; then
everything else. Every item names the default this run continued with.

## 1. Engine patches to approve

*(filled by parts B3 and C3)*

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
> window may show the previous screen and ignore a click; a modal HD does
> not know appears that much later than the game shows it.

**Default this run continued with:** the rule is implemented exactly as
written above (`core/handover.py`, check 090o); the text sits in the
status document's "No native frame on a screen HD draws" entry until Data
files it with a number.

## 3. Everything else

- **The engine's window at startup (A1 part 3).** It is mapped when the
  engine starts and stays the top X window until OrionLayer's window maps,
  and once more for 72 ms while SDL recreates the pygame window. It never
  comes forward during play. Measured with the screen LOCKED, so focus on
  an unlocked desktop was not observable. **Default:** nothing changed —
  it is not the flash Data described, and hiding it is an engine change.
  Whether it is worth one is Data's call (a flag that sets `g_hide_window`
  before `SDL_ShowWindow`, platform.cpp:1406-1408).
