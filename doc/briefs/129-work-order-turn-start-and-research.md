Work order <next free number> — The two dialogs at turn start, the research foundations, the sidebar's research readout, and Stop 1 for the research screen (17 Sep 2026)

Assign the next free number. Parts A to D are decided and run through without a stop. Part E ends in a reporting stop: the research screen itself is built only after Data has read that report. Separate commits, no push.

Rules: the block headed "RULES FOR THE WHOLE RUN — re-read this block at the start of every part" in doc/briefs/126-work-order-unattended-run.md applies unchanged and is not repeated here. Three additions:
- This order includes live runs and authorises ONE change to orion2re (part B). After every commit in ~/orion2re, write a fresh `git bundle --all` beside the tar backup and name it in the report; Data copies it off the machine.
- Every counter-test ("show it red once") runs with the bytecode caches cleared or with `python -B`. 128 lost a round to a restore by cp that left stale bytecode behind.
- When this order refers to an open fix, a decision or a brief, it gives the number AND the entry's first line. Do the same in the report. Chat called the Screen-6 fix by the wrong name in 128 because it carried a bare number.


WHAT DATA SAW TODAY, live, in two windows side by side

At turn start, when a project completes, the game runs two dialogs in a row: first the presentation ("Your scientists have completed their research in …", scientist, device, description box), then SELECT NEW RESEARCH. Through both, OrionLayer keeps showing the galaxy map with "Breakthrough" in the sidebar and an ACTIVE TURN button. Data chooses in the orion2re window. Anyone playing in OrionLayer's window alone is stuck there, and 128 part C showed live what one wrong field into that list does: SIGSEGV in the tech selection.

doc/tech_change_reading.md covers the select list and says the wire reports the main screen's number throughout. It does NOT cover the presentation dialog — chat searched it for newtech, scientist and presentation and found nothing. That gap is closed in part B before anything is patched.


PART A — A live driver is a client

Twice now a live tool has sent a field into a dialog it had misidentified: the scrapped colony base in 122, the crash in 128. The repair from 128 part C applies to the tools as much as to the product.

- One shared helper for the live tools: before ANY ACTIVATE_FIELD or INJECT_CLICK, the dialog is identified from the field list read in the same step — not from an earlier snapshot, not from the screen number alone — and the tool refuses, loudly, when the shape is not the one it expects. Reuse mapboxes.live_field and the existing shape tests; do not write a parallel set. Move the live tools that send input onto it and list which ones you moved.
- A smoke check: handed a field list of the wrong shape, the helper sends nothing.
- File two lessons in the fundament, worded from what actually happened in 122 and 128: a live driver is a client and is bound by the same rule as the product (identify the dialog from the list you just read, or do not send); and the stale-bytecode trap in counter-tests, with the rule above. Check the tree first so nothing is filed twice.


PART B — Make both turn-start dialogs visible to the client (decided: synthetic ids, on the wire only)

1. Read first, and write it down as doc/newtech_reading.md in the pattern of the other reading reports: which source owns the presentation dialog, the function that BUILDS it, its field list, what it reports as its screen while it is up, how it hands over to the select list, and whether anything else at turn start (events, news, council, a second completed project in the same turn) can sit in the same place. Check 126's claim for the select list against the source yourself rather than taking the report's word.
2. Then the patch: each of the two dialogs reports a synthetic id of its own, next free above the ones in use, checked against the engine's own screen enum as 128's new check already demands. ON THE WIRE ONLY. The reading report notes that the description box's x position depends on the game's own current-screen value being the main screen's; nothing the game itself reads may change. Look at how ext_screen_id.patch reports the existing synthetic ids and whether that path touches the game's own variable — if it does, this needs a different path, and that is a finding to report before building.
   New commit on orionlayer-local, a new entry in doc/orion2re_open_fixes.md under the next free number, the REQUIRED_FIXES entry in tools/version_check.py, the patch file in doc/, the one screen-name table. Then the bundle.
3. No HD screen claims the new ids, so decision 22 ("Graceful fallback.") takes over: OrionLayer shows the original picture in its own window. Live, on a reloaded scratch save, ending turns until a project completes:
   - both dialogs appear as the original picture inside OrionLayer's window, and the HD map with its TURN button is not reachable while they are up;
   - a choice can be made with the mouse through the original view, and the game continues. The reading report lists pointer survival after an injected click as NOT SETTLED, and says an activation commits the row under the pointer. So settle it: click three different rows on three occasions and record whether the row clicked is the row chosen. If it is not reliable, do NOT work around it — report it with the evidence. Data's preferred direction for that case is the small ORION2RE_EXT insertion in the tech selection that marks the activated row as selected before it is evaluated (option c in the report's section "What a patch would carry — described only"); it is NOT authorised in this order.
   - the map's parking guard from 128 and the new ids do not fight: after the choice, HD returns to the galaxy map on its own.
4. A smoke check for the rule: while the state reports either new id, no HD screen sends anything.


PART C — The research foundations (decision 25: reconstruct before asking for a patch)

The status document already holds the reading — the section headed "Galaxy map: the research readout's source — work order 124 G, 16 September 2026 (a report, no change)". Build what it says HD lacks:

- The player-struct fields the turn count needs (the per-field status array and the hyper-advanced counters), each with decision 23's two sources: header compile against the size assert, and a live read that agrees. Until both agree they stay in unverified.py.
- The field cost table as a transcription with a checker against techdata.cpp, in the pattern of tools/monster_hull_check.py, and the hyper-advanced surcharge. A hand-copied table without a checker is the nebula sizes again (decision 36's reasoning).
- The original's loop for turns-until-complete and its per-turn breakthrough chance, transcribed and marked TRANSCRIBED with their source.
- Validation the data provides: the two measured points in that status section (412 RP at 44 per turn reading 18 turns; 500 RP at 44 reading 16), plus a third taken live today beside the native frame. Data's screenshot from this afternoon showed 653 RP at 27 per turn in HD next to "~17 turns / 27 RP" in the original — treat that as a pointer and read it again yourself. Also one point where the chance line is above zero, if the scratch save can be brought there.


PART D — The sidebar's research readout, as the original prints it

Today HD prints accumulated RP over "+produced RP"; the original prints, for a running project, the chance for this turn as "N%" when above zero, then "~N turns", then produced RP per turn — and "0 RP" when research stands still. The difference was seen twice on 16 September and deliberately left; it is described in the status document but NOT marked in the code, and sidebar.py's docstring claims to mirror the original. That is an unmarked deviation, and with part C in place it can simply be removed.

- The readout follows the original's four cases. Wording comes from the game's own strings where the extractor has them, with the JSON label as fallback (decision 15); numeric text stays in the proportional font, as the module already explains.
- The row now carries up to three lines. It must fit its boxes at all four resolutions without touching the label — measure by rendering (decision 30's consequence), do not estimate.
- Correct the docstring and the player-struct note that repeats it.
- Evidence: HD beside the native frame at three resolutions, for a running project and for "Breakthrough".
- A smoke check on the four cases with constructed player records.


PART E — Stop 1 for the research select screen. Report, then STOP.

- Reconstruct the offered list from the player record and the static tables, and validate it against the FIELD_LIST the way the reading report proposes: one hidden row per offered choice and one radio per non-empty category, counts and row positions agreeing per entry. Do this live for at least two different offered lists. If it agrees, the list needs no patch; if it does not, say exactly where.
- An extractor plan for the names, the messages and the descriptions, following the existing extractor pattern: which of the player's own files, which records, where the output goes, that the target is ignored by git, and what the screen shows when the file is absent. Nothing extracted from a game installation is committed.
- Go through the twelve questions under "Questions for Data before a build can start" in doc/tech_change_reading.md and mark each: settled by this order (and how), decided by Data in chat, or still open. Decided in chat so far: select mode before change mode; the offered list is reconstructed, not patched; names and texts come from extractors; the category popup is not in the first build.
- The same for the presentation dialog from part B's reading: what an HD version would need, in the same six headings as the other reports.

Report and stop.


IF THERE IS TIME — one observation, report only

In Data's screenshot of the galaxy map there is white text under the star sprite at the destination of a selected fleet's course line; it reads like an ETA label that the star covers. Compare with where the original draws it, side by side. Report what you find; change nothing.


NOT IN THIS ORDER

The research screen itself. Option c or any other second change to orion2re. The colony view and its patches. The smoke-test split. Stop 2 of 127. The draft rule about one provisional content box — Data has decided NOT to file it (the readings showed it fits two of five screens badly and two more only by force); record that answer under point 5 of doc/briefs/126-parked-for-data.md.


REPORT

Deviations from this order first. Then per part: what was seen live with the evidence path, what is committed in which repository (hash), the bundle's name, the smoke count before and after. Then Stop 1's findings. A parked file only if something beyond Stop 1 is Data's to decide; if it stays empty, say so.
