Work order <next free number> — An unattended day: secure the patches, couple commit to test, quiet the smoke test, clear the small remainders, read ahead for the next screens, and audit the screens for redundant code (17 Sep 2026)

Assign the next free work-order number when you file this under doc/briefs/. Data is NOT at the screen today. This order is written to run through without him: there are no reporting stops. Where an earlier order would have stopped for a decision, this one PARKS the question and moves on to the next part. Nothing is pushed. Nothing new is applied to orion2re.

Chat drafted this against origin/main at d8006d7 and against memory of the 16 September evening handover. Both may be behind the tree. v3_projektstatus.md and doc/briefs/ are the authority on what is open; where this order and the tree disagree, the tree wins and you say so in the report.


RULES FOR THE WHOLE RUN — re-read this block at the start of every part

This is a long session, and rules read at the top of a long session are the ones that get broken at the bottom of it. Re-reading these twenty lines is cheap.

1. No push, in either repository. The decision to push stays with Data.
2. No new change to orion2re. If a part turns out to need a patch, describe it (what it carries, which file, why no existing path reaches the client — decision 25), file it under doc/orion2re_open_fixes.md as DESCRIBED, NOT APPLIED, park it, and go on. Part A only COMMITS what is already in Data's tree; it changes no byte of it.
3. Park, do not guess. Anything that is Data's to decide — a visual choice, a deviation from the original, a rule for the fundament, a hard-to-reverse cut — goes into the parked file (see "What Data finds when he is back") with the options and what you did meanwhile. Then continue with the next independent part. A parked item is a finished result, not a failure.
4. Green before every commit, and the commit is coupled to the result (part B makes that mechanical; until B is in, do it by hand and show the exit code). Exit 139 is not green. Re-run once, record both exits, never commit on it.
5. If a part goes red and you cannot get it green inside that part: revert to the last green commit, park what you learned, continue. Do not stack fixes on a red tree.
6. One commit per item, so each reverts alone. Decision numbers are identities: next free number, never renumber. Check the next free number in the TREE's fundament before filing.
7. Two independent sources before a value is trusted. Read the function that BUILDS the thing. A label in a field dump is interpretation until the source confirms it.
8. Live runs, if a part needs one:
   - exactly one client on the server. Check for a running OrionLayer before you connect; if Data left his open, do NOT kill it — skip the live step and park it.
   - scratch saves SAVE4 / SAVE5 only, RELOADED, never continued (the running game holds an in-memory colony on Malus II). Never SAVE8.
   - hash SAVE1–SAVE9 before and after, identical; SAVE10 is the autosave and is only logged; log SAVE11 the same way until part D has classified it.
   - every injected click is followed by a framebuffer read before the next one.
   - no action in any save dialog, no QUIT → YES.
   - in the colony screen a right click opens help (brief 98); cancel with a left click beside the rows.
   - evidence goes to ~/orionlayer-fixtures/evidence/work_order_<n>/.
9. After each part, append one line to the progress log (see below) BEFORE starting the next. If this session ends early, a fresh one must be able to resume from that line alone.


PART A — Put Data's orion2re changes under version control (~/orion2re)

Why first: the Extension API lives there as an untracked src/ext/ plus uncommitted modifications, guarded only by a tar archive made on 16 September BEFORE Open Fix 14 went in. Joes' tree is moving fast — a second upstream state appeared today with 155 files changed. One careless clean or checkout deletes what OrionLayer stands on.

- Make a fresh tar backup of ~/orion2re beside the old one first, and name it in the report.
- Create a local branch. Commit the existing changes as they are: the Extension API as its own commit, then one commit per Open Fix where the hunks separate cleanly, each message naming its number from doc/orion2re_open_fixes.md. Where two fixes interleave in one file and do not separate, one commit naming both — say so rather than forcing a split.
- Prove nothing changed: the working tree's content is byte-identical before and after (hash the source tree both times), the linux-debug preset still builds, and tools/version_check.py still reports every required fix as applied.
- Make an accidental push impossible: that remote is Joes'. Disable the push URL on the clone and show the resulting remote configuration.
- Do NOT fetch, pull, merge or rebase. Comparing against the newer upstream is a separate order.

Acceptance: a branch whose log reads as the list of what Data has changed in orion2re, an identical tree, a green build, a disabled push.


PART B — Couple commit and test result, and file the three lessons that are still only in the handover

A commit went through after a smoke run had exited 139, because nothing connected the two. For an unattended run this is the rule everything else leans on, so it comes before any other commit in OrionLayer.

- Build the coupling so that it is mechanical and lives in the tree (a tracked hook path or a commit wrapper — your choice, say which and why). Acceptance: with the smoke test forced to exit non-zero, including a simulated 139, no commit is created; with it green, one is. Show both.
- File, under the next free numbers / in the right section of the fundament, what the 16 September handover says is not there yet. Check the tree first — if any of it has landed meanwhile, do not file it twice:
  · a shared geometry function guarantees that drawing and hit-testing AGREE, not that they are RIGHT (the stacked colony figures: 165 of 210 clicks off while both sides shared one function that described the sprite rect instead of the visible area);
  · the live-protocol line about the colony screen's right click;
  · the delivery rule this part implements.
  These are lessons already paid for and already worded by Data's handover, so filing them is transcription. If you find yourself deciding what the rule should BE, park it instead.


PART C — The smoke test: quiet mode, a memory figure, and thirty runs. The split into groups is NOT today.

Corrected after drafting: on Data's machine a full run takes about ten seconds. Chat had measured in a slow 4 GB container and drew the wrong conclusion from it. At ten seconds there is no case for running only part of the suite — the rule stays as decision 31 has it: the FULL suite, after every step and before every commit. No two-tier rule is filed.

What is left of chat's measurement, as claims to verify: the file is about 16,300 lines and almost all of it is ONE function, main(); resident memory climbed steadily during the run and passed 3.5 GB around check 105, where the 4 GB container killed it (exit 137). The likely mechanism is that every local of a 16,000-line function lives until the function returns, so no rendered surface is released. Whether that has anything to do with the sporadic exit 139 is a SUSPICION, not a finding.

- Add a quiet mode that prints failures and the summary line only. The full sentences stay available behind a switch — they matter when something is red, not 194 times when it is green. This is about context, not time: every full run today puts a few hundred lines into the session. Use quiet mode for the rest of this run.
- Add a final line with peak resident memory.
- Then run the full suite thirty times (in a loop, a few minutes) and record exit code and peak memory per run. That is the first real evidence on the 139 question. Report the table; do not chase the segfault further today.
- Do NOT split main() into groups in this run. It is a careful refactor of 16,000 lines whose main argument — time — has just fallen away. What remains in its favour is that one exception aborts every later check, and the memory growth if the thirty runs show it matters. Put it in the parked file as a question for Data, with the peak-memory figure beside it.

Acceptance: quiet mode and the memory line in, check count unchanged, the thirty-run table in the report.


PART D — The small remainders from the 16 September handover

Take the list from the status document, not from here; chat's copy is a pointer. As chat remembers it:

- connecting OrionLayer while the GAME menu is already open draws the main-menu backdrop instead of the galaxy map (reproducible: open the menu, then start the client) — fix;
- tools/colony_move_hd.py fails on import — fix;
- the save dialog's empty slot starts in HD with an empty field instead of the original's "… empty slot …" text: deliberately left, NOT YET MARKED. Mark it as the deliberate deviation it is — module, status document, a check that fails if the marking disappears;
- SAVE11 has no place in the live protocol: read what writes it, then classify it beside SAVE10 in CLAUDE.md and the status document. If the source does not settle it, park it;
- the exit-139 segfault: part C's thirty runs are the evidence. report what the thirty runs show. Do not chase it further today;
- first menu open at 59 ms against 25: leave it, as decided;
- Open Fix 19: report its state in one paragraph, nothing else.


PART E — What is still open in the colony work order

workorder_colony_runs_and_doc_audit.md names three runs. Establish from the tree and the status document what of it is actually done. Do whatever remains that needs no decision of Data's and no unavailable input (the handover noted brief files missing from the clone — if they are still missing, name them and park). Live measurements follow rule 8; they use the scratch saves, and the reference save in slot 8 is read, never played. Run 3, the documentation audit, is NOT part of today: it belongs with the reading-budget order (part H).


PART F — screens/galaxy_map/screen.py, before Brief 110 part C lands in it

It is the one product module that is genuinely large by CODE (the status document's own list has it first), and part C's click reactions will go into it. If the file has a seam — click handling against render orchestration is the obvious candidate, but read it, do not take chat's word — split along it. Moves only, no behaviour change, smoke green, the exceptions list re-generated from tools/linecount.py. If it has no honest seam, say so and leave it: inventing a seam to satisfy a number is what decision 6's amendment warns about.


PART G — Read ahead: the next screens. Reports only, nothing is built.

Data decided today that the remaining screens are built as before — one screen, one order, his decisions between reading and building. What speeds that up is having the reading done. For each screen below write doc/<screen>_reading.md in the pattern of doc/plntsum_reading.md and doc/game_menu_reading.md:

- which orion2re source files own the screen, and the function that BUILDS each thing it shows;
- its field list with types, and which inputs go by ACTIVATE_FIELD, which need INJECT_CLICK, and whether the screen is one that ignores injected clicks;
- every value it displays: already on the wire (which struct, which offset, VERIFIED or not) or not on the wire;
- whether the game reports a screen ID of its own while the screen is up;
- what would need a patch, described per rule 2;
- the questions Data has to answer before a build can start, phrased so he can answer each in a line.

In this order, by how often each one blocks a play-through:
  1. the single colony view with its build queue (SCREEN_COLONY, SCREEN_QUEUE_POPUP);
  2. research selection (SCREEN_TECH_CHANGE);
  3. fleet (SCREEN_FLEET);
  4. races / diplomacy — READ EARLY even though it is built late: chat found no assignment of a screen ID of its own in racescrn.cpp, which would make it the same problem ext_screen_id.patch solved for Select Race and Custom Race. Confirm or refute from the source.

One draft rule to read WITH, not to file: a screen built before its frame exists should hang everything from ONE provisional content-area box, so that the frame, when it comes, moves one box and not a hundred (the colony list's stale-column bug was this lesson once already, and decision 3 is why it matters). For each screen, say whether its layout would fit under that rule. The rule itself goes into the parked file as a DRAFT for Data — it is his to make.


PART H — Only if time remains: Stop 1 of the reading-budget order

workorder_reading_budget.md (handed over TOGETHER with this order as a second file; file it under doc/briefs/ with its own number) has a Stop 1 that reads, measures and proposes and changes no file. That is a good use of unattended time. Do Stop 1 exactly as written there — it is not repeated here, one home — and stop where it says stop. Nothing of its Stop 2 today.


PART I — Last: check every screen for redundant code

The fundament's rule is that the THIRD copy is the signal to extract. Chat ran a crude pre-scan on d8006d7 (function bodies compared after normalising names; identical bodies only) and found eight groups — claims to verify, and a floor, not a list: a scan like that sees only copies that are still identical, and the interesting ones are the copies that have started to drift.

  _scale_frame          identical in colony_summary/screen.py, galaxy_map/screen.py and planets/screen.py — the literal third copy
  _load_frame           colony_summary/screen.py and planets/screen.py (a function of that name exists in four files)
  _render_frame_image   colony_summary/screen.py and galaxy_map/screen.py
  cover / _make_thumbnail        core/imagebox.py and select_race/renderer.py — a screen carrying its own copy of a core function
  fallback_text_rect / busy_text_rect   custom_race/popup.py and empire_identity/renderer.py
  fill                  colony_summary/colonypopup.py and colonypick.py — two copies inside ONE screen
  message / string      core/hestrings.py and core/estrings.py
  lift / _lift          core/playercolors.py and galaxy_map/ships.py

The frame trio matters most: every screen still to be built will want a fixed frame image, and as things stand each one will paste these three functions again.

- First the audit, as a report (doc/redundancy_audit.md): every group of duplicated or near-duplicated code across screens/ and between screens/ and core/. Go beyond chat's scan — look for the drifted copies: same purpose, same shape, different details (grid and row arithmetic, hit-testing, text fitting, background loading, the per-screen `_load` helpers). For each group: where, how many copies, identical or drifted, and if drifted WHAT differs and whether the difference is intended.
- Then extract only the clear cases: bodies that are identical, or differ only in names, where a third copy exists or is certain to come (the frame trio). One commit per extraction, moves only, no behaviour change, smoke green, the exceptions list regenerated from tools/linecount.py. The new home follows decision 10 and the existing structure — say where you put it and why there.
- Everything else goes into the parked file, not into a commit: drifted copies (which of the versions is right is a finding, and possibly a bug — report it, do not silently pick one), two-copy cases with no third in sight, and anything where the duplication may be deliberate. The fundament names one such case itself: tools/ext_diag.py re-derives the FIELD_LIST offsets by hand on purpose. tools/ is out of scope for this part.

Acceptance: the audit document, one commit per clear extraction with the smoke count unchanged, and the judgement calls parked.


NOT IN THIS ORDER

No new screen is built. No frame, no artwork. No fundament split. No work on the game's computer-player AI — that is an idea for after the release and not part of this project's core. No comparison against Joes' newer tree. No push.


WHAT DATA FINDS WHEN HE IS BACK

Two files under doc/briefs/, both committed:

<n>-progress.md — one line per finished part, appended as you go: part, commits, smoke count and exit, anything parked. This is what a fresh session resumes from.

<n>-parked-for-data.md — every parked item: what it is, why it is his, the options with what each costs, and what was done meanwhile. Write each so it can be answered in one line. If this file is empty at the end, say so explicitly — an empty list that was checked is different from a list nobody wrote.

And a closing report in the session: what is committed (hashes), the smoke count before and after, the thirty-run table from part C, the redundancy audit's headline numbers, which parts were not reached, and — separately and first — anything where you deviated from this order and why.
