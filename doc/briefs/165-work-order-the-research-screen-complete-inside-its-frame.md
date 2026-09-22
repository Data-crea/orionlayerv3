# Work Order 165 — The research screen, complete inside its frame: change mode, the shared popups, and the rest of select mode

First line for references: "Work Order 165 — The research screen, complete inside its frame: change mode, the shared popups, and the rest of select mode"

Filed as 165 because 164 was the last one. Check that before filing and take the next free number if it is taken. The draft workorder_132_research_change_mode.md was never handed over and is superseded by this order; do not look for it and do not reuse 132.

Read doc/v3_fundament.md (the index) first, then every principles- part and the decision parts this task touches. Reading budget as in work order 127.

## Why (Data)

The release target (22 November 2026) is every screen in HD except the combat map; the framebuffer fallback does not count. The research screen is two screens on the wire and only one of them exists in HD, and that one is built but not accepted. This order makes the research screen complete in structure and behaviour. The outer frame and the artwork come later, as on every other screen — nothing in this order draws a frame, extracts panel art or designs a look.

## What already exists — build on it, do not start over

- `screens/research_select/` — select mode, wire id 53, built in work order 130 E and marked STRUCTURE ONLY, not accepted. It is the screen the player sees after a technology completes. It already reconstructs the offered rows (`core/researchlist.py`, decision 25), validates them against the game's own field list on every entry, and hands over to the fallback when it cannot vouch. This is the base for change mode. In the original both modes are the same function, `TECH::_Tech_Select_(changing_tech)` in tech.cpp; the HD side should end up with one implementation and two configurations, not two copies (the redundancy audit's lesson).
- `core/researchlist.py` already carries both position sets.
- `doc/tech_change_reading.md` — the source reading of both modes. Written BEFORE work orders 129 and 130; where the tree has moved on, the tree wins. Its section 8 lists twelve questions; the section "Status of the twelve questions" below says where each one stands.
- `doc/ext_tech_activate.patch` (open fix 25, work order 130 B) — the commit path by field id, inside `_Tech_Select_`, with the null guard. By source reading it covers change mode too; that is not measured.
- `doc/briefs/131-work-order-select-list-autocommit.md` — DEFERRED until change mode exists. Its parts are folded into part E below.
- `doc/briefs/130-parked-for-data.md` — the owed acceptance items.
- The GAME menu (`screens/game_menu/`, decisions 59 and 69) — the precedent for a panel over the frozen HD galaxy map.

## How this run works

Unattended, no reporting stops. Rules: the block headed "RULES FOR THE WHOLE RUN — re-read this block at the start of every part" in `doc/briefs/126-work-order-unattended-run.md`, plus the three additions at the top of work order 129 ("Work order <next free number> — The two dialogs at turn start, the research foundations, the sidebar's research readout, and Stop 1 for the research screen"). Not repeated here.

Progress in `doc/briefs/165-progress.md`, what is Data's in `doc/briefs/165-parked-for-data.md`, evidence under `~/orionlayer-fixtures/evidence/work_order_165/`. Separate commits per part. No push — Data decides that.

Claude Code decides the open choices in this order. Data has handed them over. For each choice below there is a default; take it unless the source or a live measurement gives a reason not to. Every choice made — default or not — goes into the parked file as one entry: what was chosen, why, and what it would take to reverse it. Data confirms or overturns afterwards. Do not file new fundament decisions; draft them in the parked file instead.

No change to orion2re is authorised. If something can only be solved on the engine side, describe it (file, function, what the change would carry — no diff applied) and park it.

## Status of the twelve questions (doc/tech_change_reading.md §8)

Settled by the tree — confirm, do not reopen:

- Q2 commit path, Q3 null dereference: `ext_tech_activate.patch`. Owed: one live proof in change mode (part D).
- Q4 map parking: select mode now reports 53, change mode 36. Owed: a check that parking fires on neither.
- Q6 tables, Q7 technames, Q8 billtext: transcribed with checker / extractors exist.

Rules for this order:

- Q5: two sources per offset (decision 23). Needed here: the current application @902 and `s_settings.language`; also promote `tech_applications` @379 and `hyper_advanced_tech` @640 out of `core/structs/unverified.py` when their second source is in. An offset without its second source stays unverified and the screen keeps validating against the field list.
- Q9: show what the original shows — the single help record tech.cpp reads. If `help_en.json` holds chained text for a technology, extract the single record instead.
- Q12: Claude Code takes every live measurement it can reach. Anything that needs Data's physical mouse goes into the parked file as exact steps.
- Geometry is transcribed, not designed, as in research_select (including change mode's panel 81 px left of select mode's).

Decided by Claude Code in this order (defaults in the parts below): Q1/Q10 scope, Q11 the two original quirks, and the change-mode background.

## PART A — Foundations

- Spec entries per the Q5 rule above.
- With `language` in the settings spec, the cost suffix follows the game (RP / FP / PR). Drop the DEVIATION in research_select and its check in the same commit.
- A fallback from any HD research screen writes one log line with the reason, and the live driver's record names the HD screen that was actually drawing (work order 131 part D, taken over as written).

Acceptance: suite green; each promoted offset names both sources in its spec comment; a counter-test shows the language check red once.

## PART B — Change mode (screen 36)

Build change mode on the select-mode implementation: shared code for the panel, the rows, hover and hit-testing; the mode differences from `doc/tech_change_reading.md` §1 as configuration. Among them: the exit button and ESC leave with nothing changed; the current field and its current application are shown in the original's second colour; the entry cost is the remaining cost (`research_accumulated` subtracted); the current field IS offered.

Entry: the galaxy map's research window (the sidebar field the reading names) opens change mode. Leaving returns to the HD galaxy map.

Choice — background. Default: a panel over the frozen HD galaxy map, on the GAME-menu pattern; the map takes no input while the panel is up. Alternative if that pattern does not carry: its own screen with a neutral background, marked.

Acceptance: row clicks and bare activations both commit, read back off the wire; ESC and the exit button leave unchanged, read back off the wire; hit-testing asserted against drawn pixels (as the select screen does); every marking held by a check (decision 61).

## PART C — The shared popups, both modes

The category list popup (`_Tech_List_`) and the description box on right click are display-only in the original — nothing in them changes the research. HD draws them itself and sends nothing to the game for them. They are the same code in both modes; build them once and remove their two OMISSION markings from research_select.

Choice — scope (Q1/Q10). Default: both popups in this order, in both modes.

Choice — Q11, the radio index skew (a category button opens the wrong list when an earlier category is empty). Default: HD opens the right category and marks it as a DEVIATION, because the original reads data that was never set. Full versus remaining cost (remaining on the entry, full in the description) is the original's design, not a bug: default transcribe it.

Acceptance: both popups open and close in both modes as the original's input table describes; a right click inside the panel now opens the description; right-click help outside the panel unchanged; checks for every marking.

## PART D — Live acceptance, change mode

Live-test protocol as in the fundament (one client, SAVE4/SAVE5 for scratch, SAVE8 never, hashes before and after).

- Three changes in three different categories, each read back off the wire, via HD row click and at least one via bare `ACTIVATE_FIELD` — this is the proof that the patch covers change mode.
- ESC and exit leave `current_research_field` and the application unchanged.
- One field with research already accumulated: entry shows remaining, description shows full.
- HD beside the native frame, every capture with its colour count, at every resolution the machine can drive.
- The galaxy map does not park while 36 or 53 is up.

## PART E — The rest of select mode

This is work order 131, deferred until now.

Choice — scope. Default: do 131 parts B and C (third live choice, missing resolutions, the six "everyone gets everything" fields, Creative and Uncreative) and the 128 crash case if a run reaches an empty category. Open fix 26 (the list commits by itself about 1.5 s after the hand-over) gets one bounded attempt: 131 part A's separation of variables and its reading of the injected-click path. If the mechanism is not established by then, file what was learnt under open fix 26's entry (quoting its first line) and park — do not let it hold up the rest.

Acceptance as in 131 where done; where not, the parked file says which item and why.

## Abort rules

- A save hash differs after a live run: stop all live work in this order, park with the evidence.
- The live proof in part D shows the patch does NOT cover change mode: finish parts B and C offline, describe the needed engine change, park, and do not work around it with injected clicks (decision 20).
- The display server stops accepting clients (130's failure): finish everything offline, park the live items with exact commands.
- The suite goes red and the cause is not found within two attempts: revert that part's commits, park it, continue with the next part.
- Reading budget exceeded before part B starts: stop and report.

## Closing

Suite green, working tree clean, commits listed with one line each. Then a short final report in German for Data, at most one page: what is done, what each of the choices above ended up as, what is parked and why, and the next step. The German report is for the chat; files in the repo stay English.
