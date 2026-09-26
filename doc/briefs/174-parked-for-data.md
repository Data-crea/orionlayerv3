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
