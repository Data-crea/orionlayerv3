Work order <n> — Recovery after the crash during 177, then finish 177

Number: next free work-order number from the tree; rename before filing under doc/briefs/.

Mode

Unattended single run, no reporting stops. Findings go to doc/briefs/<n>-progress.md, questions to doc/briefs/<n>-parked-for-data.md. The first three parts only look and restore — change no code before part 3 is written down.

What happened

Data's machine crashed while work order 177 (invisible galaxy-map modals, safety net, Select Race way back, load dialog, start deadline) was running. He was not at home and does not know how far it got. The previous Claude Code session is gone.

Known from git log: seven local commits of 177 on main, from f2b82a0 to 1bc79ba (E, D, C, B, a live fix "found live" on Select Race, and engine_start --blanked-ok). origin/main is still a30ef2f — nothing of 177 is pushed. The crash came during 177's live tests.

1. Protected files first

Run tools/liveguard.py against the backup taken before 177's live tests: SAVE1–11, MOX.SET, HOF.M2, lastrace.rac, TEMP.TMP, user_settings.json, and everything else liveguard protects. For every file that differs: say which, how, and restore it from the backup. If the backup itself is missing or incomplete, stop part 1 there, write what you found, and park it — do not guess a restore.

2. Processes

List running orion2re engines and OrionLayer clients (pgrep -a). Close leftovers per the rule from 176 (liveguard first, SIGTERM, SIGKILL only if needed); record PID and command line. If the classifier refuses, park it and name the PIDs.

3. State of the repository and of 177
git status, git stash list, untracked files, the state of ~/orion2re (branch, uncommitted changes, bundle) — nothing lost, nothing half-applied?
Read 177's work order and its progress/parked files (if they exist) and compare with the commits: which parts are done, which live steps ran and with what result, what is missing.
Uncommitted changes in the tree: look at each; finish it or discard it, with the reason in the progress file. Nothing is discarded unread.
Check that the crash left no corrupt files (the suite, git fsck, the evidence folder of 177).

Write parts 1–3 into the progress file before changing anything else.

4. Finish 177

From where it stopped, per 177's own work order:

The remaining live tests (home star name after CONTINUE, colony-base questions after TURN, safety net incl. keys, Select Race way back, load dialog, both window sizes). Steps that already ran and are recorded need not be repeated unless the crash may have spoiled their result.
Open fix 34 (load dialog save slots): do NOT apply. Park it as a decision for Data, with what the load dialog can and cannot do without it.
177's result table in its progress file.
5. Push — as authorised in 177

Only if right before pushing: full suite green, fresh clone green, working tree clean, liveguard clean, and no live step "broken" by a cause from 177. Complete push of the OrionLayer repository (all local commits, branches, tags missing on the remote), listed first; confirm local = remote afterwards. No force, no history rewrite. orion2re stays local. If any condition fails, do not push; park it with the reason.

Done when

Protected files verified or restored, leftovers closed, repository state described, 177 finished with its table, and pushed or parked with a reason. The progress file starts with a short answer for Data: what the crash touched, what was restored, and whether 177 is now complete and pushed.
