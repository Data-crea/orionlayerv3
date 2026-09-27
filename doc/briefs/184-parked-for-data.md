# Work order 184 — parked for Data

Ordered as the order asks: the open fix first, then everything else. Every
item names the default this run continued with.

## 1. Open fix 42 — the research screen ~550 ms sooner on every entry (NOT APPLIED)

**What.** `fields::Get_Input_()` returns 0 while a screen's input delay
counts down and calls `ext::Tick` only after it (fields.cpp:161-167), so
while a delay runs the engine tells OrionLayer nothing. The research
panel's delay is five passes of 110 ms (tech.cpp:306, :349-351): the
engine has built and drawn the panel, and then says nothing for ~550 ms.
The fix calls `ext::Tick` during the delay too — six lines, one marker,
nothing else changes (the delay still returns 0 and still counts down).
Entry 42 in `doc/orion2re_open_fixes.md`, patch
`doc/ext_input_delay_tick.patch`, reported (not required) by
`tools/version_check.py`, held by smoke check 090r #5.

**Proved** in a scratch clone of `orionlayer-local` `4bf152e4`, never on
the branch: applies with no offset or fuzz, builds in full, compiles alone
with the build's own command, the misspelt-constant control refused.

**Measured gain** (virtual display, SAVE4, OrionLayer with this order's
HD changes in both columns, 19 later entries each):

| size | without | with fix 42 |
|---|---|---|
| 1920 | 636 / 685 ms (median / max) | **77 / 138 ms** |
| 2576 | 638 / 688 ms | **94 / 128 ms** |
| 3840 | 686 / 690 ms | **103 / 137 ms** |

The first entry after a start: 637 / 679 / 1444 ms without, 380 / 672 /
1423 ms with (see item 4).

**Cost.** Six lines in one engine function. Engine CPU over ten research
entries 5.1 % both ways; snapshot pacing unchanged at the main menu
(6.05/s, 164.6 → 164.7 ms), on the galaxy map (18.20 → 18.15/s) and on
the colony screen (18.20 → 18.15/s).

**Risk, named.**
- *It touches every screen that sets an input delay* — 42 call sites (1,
  2, 3, 5 or 20 passes) — not only research: each is heard sooner. The
  flash walk over every HD transition (29, 0 native frames) and 182's
  stress (1002 inputs, 0 lost, 0 dropped) were run on the scratch engine;
  the 42 sites were not read one by one.
- *It raises no snapshot rate*: it adds one snapshot per delay pass, at
  that screen's own loop pace, where there was silence. A loop that does
  not pace its delay passes would send them back to back (~300 KB each);
  none was seen.
- *A list heard during the delay*: a screen whose field list is only half
  built at its first delayed `Get_Input_` would now show it. None found;
  OrionLayer's hand-over gate (180) holds such a screen rather than show
  the game's picture.
- *Commands during a delay*: `MSG_SET_JOBS` and `MSG_SELECT_SHIP` act in
  `ProcessInput`, which now runs during the delay; both check their own
  preconditions, and none was sent in these runs.
- *HD draws the panel before the engine's own window would*: the engine
  presents its panel at the end of its first idle pass, the wire carries
  what was presented, so the list arrives ~110-220 ms before the native
  picture. HD draws the validated list of the loop the engine is in; a row
  clicked in that interval is held until the delay ends and then commits
  that row (open fix 25).

**Default: not applied.** OrionLayer works without it (everything else in
this order is on the HD side and measured without it). To apply:
`patch -p1 < ~/orionlayerv3/doc/ext_input_delay_tick.patch` on
`orionlayer-local`, rebuild, and move the patch from `REPORTED_PATCHES` to
`LOCAL_PATCHES`.

## 2. The turn-start research prompt was not measured live

The order asks for the other ways into research "where they exist in the
scratch save". SAVE4 has no completed research pending: the turn-start
prompt (53) appears only when a turn ends with one, and ending a turn
writes SAVE10, the autosave — this order allows SAVE4 and SAVE5 only.
The research window's text and its icon (the same field) were both
measured. By the source the prompt has no (c) at all — its id is set
inside `_Tech_Select_`, so the first snapshot carrying 53 already carries
the list — but the same five silent passes stand in front of that
snapshot (open fix 42 removes them), and its first frame gets the
geometry memo; the preparation during the wait cannot help a screen that
never waits. **Default: not measured.** If you want it measured, allow a
TURN on the scratch slot (SAVE10 would then be restored by liveguard).

## 3. Your window size for the real-desktop runs

The order says "at his window size". `settings.json` starts at 1920x1080;
the tree records your screenshots at 2576x1432 (work order 170's floor,
`screens/galaxy_map/screen.py`) on your 3440x1440 monitor. **Default:
2576x1432** — the window manager granted 2576x1371. If you play at another
size, the numbers at 1920 or 3840 on Xvfb are the nearest (the real
desktop and Xvfb agreed within a few percent at 2576).

## 4. The first entry after a start at 3840 (and with fix 42 everywhere)

The preparation during the engine's silence (`core/researchprepare.py`)
hides HD's first render completely at 1920 and 2576 (first entry 637 and
679 ms, as fast as the later ones), but at 3840 the preparation takes
~1.3 s and the silence ~0.55 s, so the first entry is 1444 ms (from 3022).
With open fix 42 there is no silence to hide it in at any size: 380 / 672
/ 1423 ms. The next step would be preparing the panel before the click —
at start or while the map is idle — which costs startup time or a hitch
on the map (at 3840 the panel's four outlines take ~0.6 s together in the
profile, the frame's the largest, and one outline cannot be split). **Default: not done** — the order says startup must not get
noticeably worse, and a hitch on the map is a thing the player sees.

## 5. The galaxy map is faster too

The floor lift (`floor_lift: light`, your setting) was an additive fill of
the whole window on every map frame — 33 / 59 / 130 ms at 1920 / 2576 /
3840 on the virtual display. It is now done once per picture and step,
byte for byte the same picture (smoke check 067 #14). This speeds up
EVERY galaxy map frame, not only the research panel's. Nothing to decide;
noted because it reaches beyond the research screen the order is about.
