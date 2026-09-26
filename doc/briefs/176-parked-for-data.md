# Work order 176 — parked for Data

Every choice and question this unattended run parked, with the default
taken.

---

## 1. The leftover engine could not be closed — every live step waits on it

**What happened:** at the start orion2re PID 368253 (parent 35660, a zsh;
started Sa Sep 26 10:03:06 2026; `/home/data/orion2re/out/build/Linux/
linux-debug/orion2re`) was running and holding port 17362, with no client.
Under this order's new rule it may be closed. `python tools/engine_start.py
--close-foreign --guard ~/orionlayer-fixtures/live_guard/176_close_foreign`
was **denied by Claude Code's auto-mode permission classifier** ("Interfere
With Workloads") before it ran: no backup, no signal. The denial forbids
reaching the same outcome another way, so it was not retried. The port is
fixed (`src/ext/ext_api.h:11`), so no engine of this run could start.

**What unblocks it** — either:
- close it yourself: `kill 368253` (it holds no client; the files it could
  have written are the ones liveguard protects — to be sure, first
  `python tools/liveguard.py snapshot ~/orionlayer-fixtures/live_guard/
  176_close_by_data`), or
- allow the action for the session (a Bash permission rule for
  `python tools/engine_start.py --close-foreign`), and I run part 3 of this
  order as written.

**Default taken:** part 3 parked in full (item 2); parts 1 and 2 done; the
push held (item 3).

## 2. Part 3, the live tests — the plan, ready to run

Every step with `tools/engine_start.py` (it takes the liveguard backup
before the engine exists), one client, SAVE4 as the scratch slot (SAVE5
spare, never SAVE8), `tools/liveguard.py verify <folder> --allow SAVE4.GAM`
after, 1920x1080 and 2576x1432, HD and native from one snapshot
(`tools/livedrive.Run` / `tools/leaders_hd.py`), files `..._LIVE_...` under
`evidence/work_order_176/<screen>/`:

- **Fix 31**: 40 starts with `engine_start.py` (with and without a
  full-screen window in front), count hangs; scroll the galaxy map and the
  Colonies list, look for tearing — if visible, park with the proposal
  "VSync off only during startup".
- **Leaders**: both tabs; POOL, DISMISS, PREV/NEXT, assign (colony view: a
  star with a colony, then a leader; ship view: a combat ship, then an
  officer), HIRE (SAVE2 offered three leaders for hire in 167's offline
  reading — copy it into slot 4 for that step), RETURN; the star/stack box,
  the galaxy box, the grid.
- **Races**: RETURN, AUDIENCE, REPORT, IGNORE, DECLARE WAR (answer NO);
  portraits, treaties, relations, spies and bonuses against the native
  picture.
- **Info**: every tab; History's curves against native (first live proof
  of open fix 32); Turn Summary's messages against native; long texts
  scrolling; the demo text mod (`evidence/work_order_175/demo_text_mod/`
  as the mod folder); the Turn Summary colony jump — see item 4.
- **Extractor**: Fleets' "%s Fleet: " strips and Leaders' ", the " titles
  show their spaces.

## 3. The push was NOT made

All of the order's conditions held at the end — full suite 336 green,
fresh clone with `setup.py` 336 green, working tree clean, no liveguard
check needed (no run touched a file), no live step broken (they are
parked, not broken). The push was still held: the order puts it at the end
of a run whose point is the live tests, and every one of them is parked
for the single reason in item 1, one decision away. Pushing 11 commits of
live-untested screen work in that state is a call for Data, not for an
unattended run that was told to stop on the denial. What would go out is
listed in the progress file; after item 1, the run pushes as the order says.

## 4. Info: the Turn Summary colony jump

In the original a left click on a colony message calls
`MSG_::Goto_Msg_Colony_` (msg.cpp:653-672), and info.cpp:641 then sets
SCREEN_MAIN unconditionally, overwriting it (175's note). Live it could not
be observed (item 1). In HD the messages are text in a scrolling box: the
engine's own list rows exist only while its local `current_tab` is the Turn
Summary and HD does not drive that tab (HD STATE `local_navigation`), so
HD offers no jump. Default: none; to be decided once the live run shows
what the engine does.

---

## After Data closed PID 368253 (26 September 2026, afternoon): items 1-3 resolved

Data ended the leftover engine himself; part 3 ran (progress file, "Part 3 —
run"). Items 1 and 2 are done; item 3 (the push) follows the order's
conditions at the end of the run; item 4's jump is measured (entry 33 of
the open-fix list). New items:

## 5. Fix 31: tearing is not observable from this session

The engine's presented image is the compositor's; this session sees the
framebuffer the API sends (whole frames, never torn) and no capture of
Xwayland's scanout. 82 starts showed no VSync hang (item 6's intros aside).
**Default taken:** fix 31 stays as applied. **Please look** at the engine's
own window while scrolling the galaxy map and the Colonies list; if it
tears, the proposal is **VSync off only during startup** (the hang is in
the logo frames, before the window has ever been drawn — switch VSync on
after `mox2: logos drawn`).

## 6. `tools/engine_start.py` times out on the original's intro

Of 82 starts, 11 played the full logo and intro sequence — 112.9 s every
time, the original's behaviour when no key or mouse button is down at start
(`JIM::Draw_Logos_`, jim.cpp:18-120); the rest skipped it at once. The tool's
default `--timeout` is 60 s (since 174), so those starts are reported as
TIMEOUT and stopped although nothing hangs (7 of 40 with 45 s; 0 of 42 with
150 s). Not caused by 175 or 176, so not changed here. **Proposal:** a
default of 150 s, or the tool sends the engine one key press after `mox2:
data space allocated` to skip the intro as a player would.

## 7. Leaders: the galaxy box has no destination lines

The original draws the flight line of a stack in transit in the galaxy box
(`FLT1::Draw_Fltscrn_Ship_Destination_Lines_(29)`, officer.cpp:758) — seen
in the live native half; HD's galaxy box does not. It was not in 175's
inventory (an inventory gap, not a regression). **Default taken:** recorded;
a later order draws it (the Fleets screen's own line drawing can be reused).
