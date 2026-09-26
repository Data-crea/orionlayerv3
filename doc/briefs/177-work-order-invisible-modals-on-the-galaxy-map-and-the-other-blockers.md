Work order <n> — Invisible modals on the galaxy map, and the other blockers

Number: next free work-order number from the tree; rename before filing under doc/briefs/.

Mode

Unattended single run, no reporting stops, ending with a push (last section). Findings and questions go to doc/briefs/<n>-parked-for-data.md, progress to doc/briefs/<n>-progress.md. One commit per part and per fix.

Start

Clone per CLAUDE.md. Read the fundament index, the principles- parts, parts 04 and 09, the live-test protocol, and the progress/parked files of 174 and 176 (174 found the invisible modal after TURN).

What Data saw

He pressed CONTINUE in the HD main menu on a freshly started game. The game loads, but the HD galaxy map shows no "Enter Home Star Name" dialog, which the original shows at that moment: a text field prefilled with the home star's name (in his screenshot "Mentar") and an ACCEPT button. The player cannot name the star and, very likely, cannot go on.

This is the same class of bug as 174's finding: after TURN, three colony-base questions were shown by the engine but the HD galaxy map showed only the map. Check it yourself — reproduce both live.

A. Find every modal the galaxy map can show
Inventory from the orion2re source: every dialog/modal that can appear over the galaxy map (home star name, colony base questions, and whatever else: events, confirmations, messages, text entries). For each: what it shows, what input it takes (buttons, text entry, choices), what it sends back. Into the progress file.
For each: is it on the wire today, and does HD draw it? Table in the progress file.
B. Draw them in HD
Every modal from A drawn with the popup block from 169/174 (glass, tint, text in code), with working input: buttons, choices, and text entry (cursor, typing, backspace, Enter = ACCEPT, the prefilled name) for the home star name.
Data not on the wire: patch rule (entry in doc/orion2re_open_fixes.md, patch file, reported, not applied) — and until then part C catches it.
C. Safety net for modals HD does not know

A modal the engine shows but HD does not draw must never leave the player stuck in front of a map that ignores him. Whenever the engine is in a modal state HD has no view for, HD shows the native picture of that moment (the existing fallback view) with input passed through — including keys, which 174 found the fallback does not forward. Marked DEVIATION where it applies. Log one line naming the unknown modal so it can be built later.

D. The other blockers from 174
Select Race: no way back in HD. Add the original's way back (whatever the original offers — check).
Load dialog in the main menu is not drawn in HD. Draw it (popup block), with the save list and its actions as in the original.
E. Small
tools/engine_start.py: the 60 s start deadline reports the original intro (112.9 s, 176) as a timeout. Detect the intro or raise the deadline; say which.
Live tests

Per the protocol, tools/liveguard.py before and after, own engine, scratch saves only (never SAVE8). Engines found running that you did not start may be closed per the rule from 176; if the classifier refuses, park and say so.

A new game → CONTINUE → the home star name dialog in HD: rename the star, ACCEPT, the new name shows on the map; also accept unchanged.
TURN on a scratch save until colony-base questions (or any other modal from A) appear; answer each in HD.
Force an unknown modal if possible (or simulate one offline) and show the safety net working, keys included.
Select Race: way back works. Main menu: load dialog lists saves, loads a scratch save, cancels.
Every step at 1920x1080 and 2576x1432, HD beside native.
Tests
Full suite green, fresh clone green.
Checks: every modal from A has an HD view or is routed to the safety net; text entry; safety net forwards mouse and keys; Select Race way back; load dialog.
Evidence under ~/orionlayer-fixtures/evidence/work_order_<n>/, live files ..._LIVE_....
liveguard clean: protected files identical before and after, except the named scratch slot.
Push — authorised by Data for this order

At the end, push the OrionLayer repository — only if right before pushing: full suite green, fresh clone green, working tree clean, liveguard clean, and no live step "broken" by a cause from this order. Otherwise do not push; park it with the reason. Complete push (all local commits, branches, tags missing on the remote), listed first; confirm local = remote afterwards. No force, no history rewrite. orion2re stays local.

Done when

Every galaxy-map modal is drawn or caught by the safety net, the home star name can be entered in HD, Select Race has its way back, the load dialog is drawn, the start deadline fixed. Progress file ends with a table — step, result (works / broken / parked), evidence — plus the push record and what Data should look at first.
