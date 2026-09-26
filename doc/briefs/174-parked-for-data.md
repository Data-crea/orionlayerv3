# Work order 174 — parked for Data

Every choice, finding and question this unattended run parked, with the
default taken.

---

## A1 — open fix 31: present without VSync on request

**Default taken: written, not applied** (`doc/ext_present_no_vsync.patch`).
It is the only change that removed the start hang (0 in 50 against 8 in
60). Applying it is Data's (and Joes') call; until then
`tools/engine_start.py` recognises the hang and starts again. A deeper
fix — a timeout on the game thread's wait for the present — was not
attempted.

## A2 — the inhibitor

`tools/engine_start.py` holds `gnome-session-inhibit --inhibit idle` for
the engine's lifetime so the screen does not blank during a live run —
no setting changed, gone with the engine. **Alternative:** `--no-inhibit`.

## A3 — what was running on the desktop

This run started at 06:18; Data launched Borderlands 3 full-screen at
06:21:53, and every engine of this run after that sat behind it. An
engine that came up runs throttled there. Noted because the live part
(C) ran in the same state.

## B1 — the look

**Default taken:** Data's mockup, measured — top (9,18,27) at 0.686,
bottom (2,10,17) at 0.819. Renders: `screens/select_race_beside_mockup_offline.png`,
every screen in `screens/`, the five tones in `tints/`.

## B2 — which boxes are dense

**Default taken:** the colony and planet lists, Select Race's portrait
grid, the fleet slots, the research lists, table rows and headers, text
fields. Custom Race's columns stay normal glass (lists, but text-led).

## B3 — table stripes over glass

**Default taken:** the row's own colour laid over dense glass at 0.45,
the selected row at 0.75, a header at 0.6 — chosen, the mockup has no
table.

## B4 — softening

**Default taken: none** — the mockup shows the nebula dimmed, not
blurred. `chosen.glass.soften` exists as a value and does nothing yet.

## B5 — inner corner lines

**Default taken: off.** Built as the mockup draws them (a thin dim line
inset from each corner, following its chamfer, at half strength), and
only in panels large enough for them (four arms wide, three tall) — on
the colony screen none qualifies, on Select Race both boxes show them,
faintly. Off because at that strength they add little; stronger they
would be a second edge. Data's call from the renders in `corners/`.

## B6 — popups show the background, not the map

A popup's glass shows the background picture under it, never the map a
screen drew there, so a dialog still hides the game behind it. **Alternative:**
glass over whatever is drawn — then the map's stars would show through
every dialog.

## B7 — the second mockup of the morning

`~/Downloads/ChatGPT Image Sep 26, 2026, 06_14_19 AM.png` (a galaxy
screen with a glass info panel and a silver frame) is not named by the
order and was not used.

## C1 — the live test ran on the fix-31 build

**Default taken:** after four steps on your build — throttled to about a
frame a second behind your full-screen game, a click lost — the live
test ran on a scratch build of e6199966 with open fix 31 and
`ORION2RE_NO_VSYNC=1`. Game code and Extension API are yours; only the
present no longer waits. **Alternative:** repeat the live steps on your
build with the engine's window in front (`live/driver/` holds the
scripts).

## C2 — an unknown modal on the galaxy map is invisible in HD

Found live after TURN (colony base on Malus). The galaxy map draws only
the boxes it knows and never hands an unknown one to the fallback view.
**Default taken:** not fixed here (from before 169). **Suggestion:** the
galaxy map's `wants_original()` answers True while `mapboxes.classify`
says unknown — the game's own picture and its clicks, as for every
screen HD has no version of.

## C3 — Select Race's ESC

HD's ESC injects a click at native (162, 445), where no field lies; the
list's own ESC field (hotkey 27) would take the game back to New Game.
**Default taken:** not fixed (first commit).

## C4 — the main menu's Load dialog

HD keeps drawing the main menu while the game's Load dialog is up, and
`tools/gameload.py` knows only the GAME menu's variant (base (0x90,
0x19)); the main menu centres it (`loadsave.cpp:224-229`). **Default
taken:** not fixed; the driver checked the ten rows against the source
itself.

## C5 — MOX.SET

Written by the game at 09:26:31 (leaving the loaded scratch game for New
Game), not copied before — the order named SAVE1-11. **Default taken:**
restored from the settings block of your own 06:18 autosave (7 bytes
differed, `active_save_slot` among them); the run's file kept as
`MOX.SET_after_run`. Not provably identical to the file before the run.
**If anything in the game's options looks different**, copy
`MOX.SET_after_run` or your own copy back.

## C6 — three older findings

New Game's layout lists a fourth tech level the original lacks; Select
Race's text overlaps at 2160p (as before 169); the fallback view
forwards clicks but not keys.

## C7 — hiring a leader

SAVE4 offers the player no leader for hire (as 167 found). Needs a
scratch save that does.
