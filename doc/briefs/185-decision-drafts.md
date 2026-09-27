# Work order 185 — two decision drafts (numbers: Data)

Drafted in the style of the existing decisions, from what the tree does
today. **Not filed in `doc/fundament/`** — each names the part it would go
into; Data assigns the number, and the number is checked at the commit
that files it (the rule decisions 71-73 followed: "the highest entry was
N, and nothing in the tree used N+1").

Both rest on work already done and held by checks, so filing them changes
no code: they write down a rule the tree already obeys.

---

## Draft 1 — the flash rule (work order 180)

**Would go into:** part 02, *The orion2re boundary*
(`doc/fundament/02-decisions-the-orion2re-boundary.md`), directly after
decision 22 ("**22. Graceful fallback.** An unknown screen ID falls back to
the…"), which it narrows: 22 says what HD shows for a screen it has no view
for; this says it never shows that picture for a screen it does have one
for.

> **<number: Data>. The player never sees an original frame before or
> between HD screens.** 27 September 2026, Data's rule, from work order 180
> ("Work Order — flash before HD, colony screen, build screen"), after the
> Fleets screen flashed the game's own picture, with OrionLayer's sentence
> on the left, before its HD screen appeared
> (`doc/briefs/180-flash-findings.md`).
>
> **The rule.** A screen HD draws never presents a native frame — not
> before its first HD frame, not after it, not between two HD screens.
> While a transition waits for the data a screen needs, the window keeps
> showing the last HD frame, or the universal background, and takes no
> input: a click or a key on a frame that no longer shows the game's state
> is not a choice (decision 65's reasoning), and it is dropped, never
> queued. The game's own picture is shown only for a screen or a modal HD
> has no view for at all (decision 22) — for an id no HD screen claims, as
> soon as its list holds something to answer; for a modal net's verdict,
> after the hold.
>
> **One gate, not one rule per screen.** It is decided in ONE place,
> `core/handover.py`, which `main.App._showing_original` asks for every way
> into the game's picture — the three the frame trace names: an id no HD
> screen claims, a known screen that cannot vouch for its data
> (`wants_original`), and the player's own F12. A new screen is under the
> rule without doing anything; there is nothing for it to forget.
>
> **The hold is counted in snapshots, not seconds** (decision 21, "Dialog
> chains are event-driven, never timed."): a load, a galaxy generation or a
> turn is silence, not a failure. Its bound is 36 snapshots (`HOLD`) — about
> two seconds on the galaxy map, which sends 18 a second, and about six at
> the main menu, which sends 6; longer than any transition measured (the
> main menu's opening animation, 24). If a KNOWN screen's data does not
> arrive within it, the picture is shown ONCE, logged, and counted as a
> failure — never as normal behaviour.
>
> **A screen that is not ready says so; it does not hand over.** Change
> mode's research panel (work order 166 A, "the glimpse of the original on
> entry") draws nothing while the game has not built its list, so the
> galaxy map it is an overlay over stays on screen; a screen whose whole
> content hangs on a block an engine may not send (the colony screen and
> open fix 35) declines its id (`ScreenBase.claims`), which is decision
> 22's path with no hold and no failure.
>
> **Marked DEVIATION `hold_last_frame`** in `core/handover.py`, the status
> document and smoke check 090o: the original draws each screen the moment
> it draws it and has no second picture to wait with.
>
> **The flash check.** Smoke check 090o replays recorded transitions
> (`tools/fixtures/transitions_180.json`) for EVERY screen in the registry
> — both directions, the galaxy map's overlays and modals — through the
> real gate, and fails on a native frame before or after the target's
> first HD frame, on a fallback, and on a registry screen with no recorded
> transition; and it is shown to fail, with the hold taken away, on the
> three flashes 180 A1 measured. Its live counterpart is
> `tools/flash_walk.py`, which walks every transition on the running game
> and judges every presented frame twice: by the branch `App._render` took
> (`core/frametrace`) and by the pixels inside the picture area. **A new HD
> screen is not finished until its transitions are in the replay set** —
> the check fails on it otherwise.
>
> **What it costs, on record:** for at most `HOLD` snapshots after a
> transition the window may show the previous screen and ignore a click or
> a key; a modal HD has no view for appears that much later than the game
> shows it.

*What stood before it:* the text proposed in `doc/briefs/180-parked-for-data.md`
item 2 ("Proposed decision text (A2) — number left free"), unchanged in
substance; updated with the snapshot rates measured since (work order 184:
the galaxy map 18.2/s, the main menu 6.05/s), 166 A's waiting overlay, 180
B's `claims`, and the live walk.

---

## Draft 2 — the player's start: no intro, no engine window (work order 183)

**Would go into:** part 02, *The orion2re boundary*, after decision 39
("**39. A button whose native rectangle is in the source is clicked by…**"),
whose correction is about the engine's own window and the real pointer.

> **<number: Data>. A player starts in the HD main menu: the original's
> intro is skipped, nothing of it is heard, and the engine's window is not
> shown.** 27 September 2026, Data's decision, from work order 183 ("Work
> Order — apply Fix 41, players skip the intro silently").
>
> **The start.** A player starts the game with `python play.py`. It starts
> orion2re through `tools/engine_start.start` — the SAME function every
> live tool starts it with, so the skip is the tools' by construction, not
> a copy: one key to the engine's own window while its log stands at "data
> space allocated", the original's own skip (jim.cpp:59-61), and the intro
> is never played (jim.cpp:150-152). OrionLayer then opens in the HD main
> menu without a key. Closing OrionLayer stops the engine `play.py`
> started; an engine it did not start is never touched. OrionLayer itself
> (`main.py`) still starts and stops no engine (work order 176, check
> 006e).
>
> **No intro sound.** Measured with the real audio driver into a private
> null sink (work order 183, part 2): with the key the engine produces
> nothing before the main menu's music, which begins after READY; without
> it, 108 s of intro sound from 5.0 s on. Nothing was built for audio,
> because nothing needed silencing.
>
> **The engine's window stays hidden.** Open fix 41 (APPLIED by work order
> 183, orion2re `4bf152e4`; entry 41, "The engine's own window is shown
> before it is hidden") creates the window hidden and never shows it; a
> hidden window presents without VSync. The player sees only OrionLayer's
> window, and the original no longer follows the real pointer over a
> window of its own (decision 39's correction).
>
> **The consequences, accepted by Data for now** (work order 184, "Fix 41
> as it stands"): orion2re started ON ITS OWN, without OrionLayer, starts
> invisible and stays so — nothing can show its window; and the engine's
> own window cannot be shown from OrionLayer either. F12 itself still
> works as it always did — it switches OrionLayer's window to the engine's
> picture, forwards clicks and keys, and returns to HD (measured on the
> applied build by work order 185, part 2) — but what it shows is the
> picture inside OrionLayer, never the original's window.
>
> **The proper version is prepared, not applied:** open fix 43 (work order
> 185 part 2, "The engine's window: hidden only when OrionLayer starts it,
> and shown again on request") hides the window only when the starter asks
> (`ORION2RE_HIDE_WINDOW`, which `tools/engine_start` and so `play.py` would
> set), leaves an engine started on its own as it was before fix 41, and
> lets a client show and hide the window again (`MSG_SHOW_WINDOW`) — the
> way back for F12. When Data approves and a later order applies it, this
> paragraph and the one above are replaced by it.
>
> **Held by** smoke checks 090r (fix 41 required and documented) and 090v
> (the player's start is `engine_start.start` with its skip).

*What stood before it:* the text proposed in `doc/briefs/183-parked-for-data.md`
item 1 ("Proposed decision (number left free for you)"), with the
consequences Data accepted in 184 and the pointer to fix 43 added.
