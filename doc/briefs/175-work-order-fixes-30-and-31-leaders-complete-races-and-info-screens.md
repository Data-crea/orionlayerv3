Work order <n> — Fixes 30 and 31, Leaders complete, Races and Info screens

Number: next free work-order number from the tree; rename before filing under doc/briefs/.

Mode

Unattended single run, no reporting stops. Choices and questions go to doc/briefs/<n>-parked-for-data.md with the default taken, progress to doc/briefs/<n>-progress.md. One commit per part (and per fix inside a part), so each can be reviewed on its own. Builds on 167 and 169–174 (decisions 71, 72). First commit: note in 174's progress file that 174 was pushed (214cafb..cb70745).

Start

Clone per CLAUDE.md. Read the fundament index, the principles- parts, parts 04 and 09, the live-test protocol, doc/orion2re_open_fixes.md (entries 30 and 31), and the progress/parked files of 167 and 174.

Live-test protocol — extend it first

In 174, MOX.SET was rewritten by the game during a live test and had to be restored from an autosave; SAVE10 was rewritten by TURN. From now on, before every live test, back up and afterwards verify: SAVE1–11, MOX.SET and user_settings.json (and any other file the game or OrionLayer writes during a run — find them). Update the protocol in CLAUDE.md and the fundament, and make tools/engine_start.py (or the live tools) do the backup and the check.

Data's engine: never connect to it, never kill it. Use tools/engine_start.py.

A. Apply fixes 30 and 31 — Data authorises both

Per the patch rule: apply each on the local orion2re branch (orionlayer-local), one commit per fix, refresh the bundle, rebuild. orion2re stays local; nothing goes online. Update both entries in doc/orion2re_open_fixes.md to "applied" with commit and date.

Fix 31 (doc/ext_present_no_vsync.patch): present without VSync. After building: repeat 174's start test (many starts, with a fullscreen program in front if one runs) and report hangs. Check for visible tearing on the galaxy map and in a scrolling list; if it is visible, park it with a proposal (VSync off only during startup, or VSync with a timeout).
Fix 30 (doc/ext_officer_screen_state.patch): button mode, selected leader, the star or fleet on show, and the hire popup's leader on the wire.
B. Leaders screen complete

With fix 30 applied, finish what 167 left dead:

POOL, DISMISS, PREV/NEXT and assigning a leader work as in the original.
The top-right box shows the star or fleet the game shows — the placeholder text naming open fix 30 goes away. The box under PREV/NEXT and the empty box above HIRE get their content from the inventory in 167's Part A.
Data's screenshot shows the screen with near-black boxes and a black mini-map: make sure every box uses the glass fill and the blocks from 174, like every other screen.
Live test: every button in both tabs; hire on a scratch save that offers a leader. If none of the scratch slots does, say which state is needed and park only that step.
C. Races screen (RACES on the galaxy bar)

Build it as 167 built Leaders:

Inventory first from the orion2re source: views, fields, buttons, dialogs, what it reads and what it triggers. Into the progress file before building.
Complete = the inventory. Anything not built goes into the parked file with the reason. Data or actions not on the wire: patch rule (entry, patch file, reported, not applied), build everything else with a clear placeholder.
New style from the start: HUD blocks, glass, tint, background, text in code. Original MOO2 artwork (race portraits and the like) where the original shows it. Markers for every deviation and extension.
Smoke group, renders at 1080p/1440p/2160p and 2576x1432, live test.
D. Info screen (INFO on the galaxy bar), texts moddable

Build it the same way — inventory first, complete = the inventory, new style, markers, smoke group, renders, live test. In addition:

All texts of the Info screen are moddable.

Every text the Info screen shows (headings, labels, and the long texts — reference/help entries or whatever the inventory finds) is looked up by a stable key through one text resolver, like 173's asset resolver.
A mod replaces a text by putting a file into the mod folder (e.g. texts/info/… — structure and format your choice: plain UTF-8, easy for a non-programmer; park it). Missing key or file = default. Broken file = one log line, default.
Long texts wrap, and scroll if they do not fit — no text may be cut off or run out of its box at any window size.
The mod template (tools/mod_template.py) and MODDING.md gain a section for texts. It never copies original MOO2 texts — for those, it lists only the keys, as 173 does for images. OrionLayer's own texts may be copied as starting points.
Whether the resolver is Info-only or general for later screens: build it so it can be general; say which screens could use it.
Record the text resolver in the fundament with decision 72 (or as a new decision next to it).

The space-stripping bug in the shared string extraction (167's finding X: spaces lost in 32 HESTRNGS and 96 ESTRINGS entries, e.g. "%s Fleet: ") will show up on a text-heavy screen. Fix the extractor now, remove the Leaders-only workaround, and render before/after for every screen that uses the affected strings (Fleets at least).

Tests
Full suite green, fresh clone green.
Checks: fix entries marked applied; Leaders buttons wired; smoke groups for Races and Info; text resolver (override, missing, broken, no MOO2 text in the template); no text clipped in Info at any tested size; extractor keeps spaces.
Evidence under ~/orionlayer-fixtures/evidence/work_order_<n>/: Leaders, Races, Info at 1080p, 2160p, 2576x1432, native beside HD where it applies; Info with a demo text mod; extractor before/after. Live files named ..._LIVE_....
Backups and hashes per the extended protocol: identical before and after, except the scratch slot you named.
Done when

Fixes 30 and 31 applied and documented; Leaders fully working; Races and Info built to their inventories; Info texts moddable with template and guide; extractor fixed; protocol extended. Progress file ends with a table — step, result (works / broken / parked), evidence — plus what Data should look at first. Commits local. No push.
