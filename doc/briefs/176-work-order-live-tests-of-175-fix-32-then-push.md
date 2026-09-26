Work order <n> — Live tests of 175, fix 32, then push

Number: next free work-order number from the tree; rename before filing under doc/briefs/.

Mode

Unattended single run, no reporting stops, ending with a push (last section). Findings and questions go to doc/briefs/<n>-parked-for-data.md, progress to doc/briefs/<n>-progress.md. One commit per part and per fix.

Start

Clone per CLAUDE.md. Read the fundament index, the principles- parts, parts 04 and 09, the live-test protocol, and the progress and parked files of 175 — every live step parked there is this order's work.

1. New rule: engines Claude Code did not start — record it first

Data does not play the game at the moment. Engines or clients found running that Claude Code did not start are leftovers from Data looking at screens, not games in progress. This replaces the rule from 171 ("never connect, never kill"):

If an engine or client is running that Claude Code did not start, it may be closed: first run tools/liveguard.py (backup of every file the game or OrionLayer can write), then SIGTERM, wait a few seconds, SIGKILL only if it is still there. Record PID, command line, start time and how it ended in the progress file.
Still never connect to such an engine — close it and start your own.
Update the rule in CLAUDE.md, the fundament (part 09, live-test protocol) and tools/engine_start.py, and note that it holds while Data does not play; if he plays again, he will say so.
2. Fix 32 — authorised by Data

Apply doc/ext_info_screen_state.patch (open fix 32: History curves and Turn Summary on the wire) on the local orion2re branch orionlayer-local, own commit, refresh the bundle, rebuild. orion2re stays local. Mark entry 32 in doc/orion2re_open_fixes.md as applied with commit and date. Wire the Info screen's History and Turn Summary pages to it and remove their "needs fix 32" notices.

While in that file: 175 could not read its end (the classifier refused) and appended entry 32 blind. Read the whole file now and check entry 32 sits correctly at the end, in the right format, with nothing duplicated or cut. Fix it if not.

Untracked files in ~/orion2re (mox.set, racesel_custom_screen_id.patch, src.zip) are not yours: do not touch, do not commit them; make sure the orion2re commits contain only the patch changes.

3. Live tests — everything parked in 175

Per the protocol, with tools/liveguard.py before and after, one client, own engine, scratch saves only (SAVE4/SAVE5, never SAVE8). Every step: expected vs. observed, screenshot HD and native side by side where it applies.

Fix 31: many starts (as in 174), report hangs; tearing on the galaxy map and in a scrolling list — if visible, park with a proposal.
Leaders: every button in both tabs — POOL, DISMISS, PREV/NEXT, assign, HIRE, RETURN; the top-right star/stack box; the galaxy box and ship grid. Hire and dismiss change the game: only on a scratch save. Hire needs a scratch save that offers a leader — if none does, park only that step and name the state needed.
Races: RETURN and the four actions; the portraits, treaties, relations, spies, bonuses against native. Actions only on a scratch save.
Info: every tab — Chart/History, Tech Review, Race Stats, Turn Summary, Reference; scrolling of long texts; the demo text mod; the jump from Turn Summary to a colony (175 noted a possible port deviation at info.cpp:641 — record what actually happens).
Extractor fix: Fleets and Leaders texts show their spaces live.
Window sizes: 1920x1080 and 2576x1432.

Fix only regressions clearly caused by 175 or this order, each with a check and its own commit. Everything else is recorded and parked with evidence.

Tests
Full suite green, fresh clone green after any change.
Evidence under ~/orionlayer-fixtures/evidence/work_order_<n>/, live files named ..._LIVE_..., one folder per screen.
liveguard check clean: every protected file identical before and after, except the scratch slot named in the progress file.
Push — authorised by Data for this order

At the end, push the OrionLayer repository to the remote — only if right before pushing: the full suite is green, a fresh clone with setup.py is green, the working tree is clean, the liveguard check is clean, and no live step is "broken" by a cause from 175 or this order. If any of that fails, do not push; park it with the reason.

Complete push: every local commit not yet on the remote, plus any local branch or tag of the OrionLayer repository missing there. List everything that goes out in the progress file first; after pushing, confirm local and remote are identical.
No force push, no history rewrite. orion2re stays local.
Done when

Rule recorded, fix 32 applied and wired, every live step from 175 has a result, and the progress file ends with a table — step, result (works / broken / parked), evidence — plus the push record and what Data should look at first.
