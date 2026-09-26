# Work order 178 — progress

Unattended run, 26 September 2026, from 18:33 (the machine came back up at
18:26:33). Recovery after the crash during 177, then 177 finished.

## Short answer for Data

**What the crash touched:** nothing that mattered. It came at 18:24:55,
after all of 177's live steps had run and been written down, but before the
last write-up was committed. Every protected file (SAVE1-11, MOX.SET, HOF.M2,
lastrace.rac, TEMP.TMP, user_settings.json) was identical to 177's backup,
so **nothing was restored**. No engine or client was left running; git
fsck, orion2re and its bundle, and 177's 111 evidence files are all intact. The
three uncommitted doc edits were read and committed. One stray file
(`less`'s help screen, created after the reboot) was removed.

**177 is complete and pushed.** Four live steps had run at only one of the
two window sizes; this run did them at the other size, and all work. Open
fix 34 is **not applied** and is parked as your decision. `main` is
pushed: `a30ef2f..3fe2184`, plus this record, with the full suite and a fresh
clone at 344 green. Look first at 177's "What Data should look at first".

---

## 1. Protected files — **VERIFIED, NOTHING TO RESTORE**

Backup: `~/orionlayer-fixtures/live_guard/177_master`, taken 17:46:01 before
177's first engine start (177's own progress file names it as the master).
It is complete: its manifest holds SAVE1-11, MOX.SET, HOF.M2, lastrace.rac and
user_settings.json with a copy each; TEMP.TMP and user_settings.json.tmp /
.corrupt are recorded as absent at snapshot time, and they are still absent.

```
$ python tools/liveguard.py verify ~/orionlayer-fixtures/live_guard/177_master
CHANGED   tree/git status
exit=1
```

Every game file and every OrionLayer file is identical to the backup. The one
reported difference is the tree's `git status` — 177's own work (six code
commits since the snapshot, three uncommitted doc edits and one stray file,
all in part 3). No file restored because none differs. No game-folder file
has an mtime after 18:00.

## 2. Processes — **NONE RUNNING, NOTHING CLOSED**

`pgrep -a orion2re` → nothing (exit 1). `pgrep -af 'main.py|orionlayer'` →
only this session's own shell. The reboot ended every process; there was no
leftover to close.

## 3. The repository and 177

### What the crash was

`journalctl --list-boots`: the previous boot's last entry is **18:24:55**
(a snapper cleanup), with no shutdown sequence after it; the new boot starts
18:26:33. A hard stop, not a shutdown. Before it: two python processes
SEGV'd at 18:20:14 through `kill()` in libc — that is smoke check 091, which
kills a child with SIGSEGV on purpose (`os.kill(os.getpid(), signal.SIGSEGV)`
to test the 139 path), so **a suite run was in progress at 18:20**. Nothing in
the log names the crash's cause; it is not guessed here.

### Timeline, from the files

| time | what |
|---|---|
| 17:04 - 18:18 | 177's seven commits, f2b82a0 … 1bc79ba |
| 17:46 | liveguard `177_master`; 17:55 `177_run2`, 18:13 `177_run3` |
| up to 18:16 | the last live evidence (`main_menu_load/002_…_loaded_slot4_*`) |
| 18:20 | a suite run (the check-091 SEGVs) |
| 18:21 | the drivers `probe.py`, `turn177.py` copied into the evidence folder; `177-progress.md`, `177-parked-for-data.md` and `CLAUDE.md` written — **never committed** |
| 18:24:55 | the machine stops |
| 18:29:39 | the stray file (below) — **after** the reboot |

So the crash did not come in the middle of a live step: every live step 177
recorded had finished and been written down. It came between writing the
results and committing them; the push record and "what Data should look at
first" were not yet written.

### git

- `main` at 1bc79ba, `origin/main` at a30ef2f: seven local commits, nothing
  of 177 pushed. No other local branch, no tag missing on the remote (listed in
  part 5). `git stash list` empty.
- `git fsck --full`: no error; 17 unreferenced objects, the normal residue of
  amended commits and hook runs — not corruption.
- Uncommitted:
  - `doc/briefs/177-progress.md` (+122 lines): parts B, C, D, the checks, the
    live section and the 18-row results table. Read in full; consistent with
    the commits and the evidence. **Kept and finished** (part 4).
  - `doc/briefs/177-parked-for-data.md` (+61 lines): eight parked items.
    Read in full. **Kept**; item 1 (open fix 34) is extended in part 4.
  - `CLAUDE.md` (+3/-1): one sentence that `--blanked-ok` exists since 177 —
    matches commit 1bc79ba, which added the flag. **Kept** (committed with the
    docs).
  - untracked `go to the safety net (found live) (177-C)`, 17 182 bytes:
    **the help screen of `less`** (SUMMARY OF LESS COMMANDS … LINE EDITING,
    with overstriking), and nothing else. Its name is the tail of commit
    4cb5161's subject after "the ruler's" — a shell command that broke on that
    apostrophe and redirected a pager's help into a file named after the rest
    of the line. Created 18:29:39, three minutes after the reboot, so not by
    177's session; who ran it is not known here. **Discarded** — it carries
    no content of this project.

### ~/orion2re

Branch `orionlayer-local` at 2269749c (open fix 32, from 176), no uncommitted
change to tracked files. Untracked: `mox.set` (16 Sep), `racesel_custom_screen_id.patch`
(25 Aug), `src.zip` (5 Sep) — the three 176 found and left alone; untouched
since. Bundle `~/orion2re_bundle_26sep_2269749c.bundle` lists
`refs/heads/orionlayer-local` = 2269749c = HEAD. Nothing lost, nothing half
applied; 177 did not touch orion2re (open fix 34 is a patch file under `doc/`,
not applied).

### 177's evidence folder

`~/orionlayer-fixtures/evidence/work_order_177/`: 111 files; every PNG
decodes, every JSON parses, both drivers compile; no zero-size file. Nothing
newer than 18:21.

### 177: done, and what is missing

| part | state |
|---|---|
| E start deadline | committed f2b82a0 |
| A inventory | in the uncommitted progress file |
| B home star name, confirmations | committed 388b09c |
| C safety net | committed 57f1c8f, the Select Race live fix 4cb5161 |
| D Select Race way back, Load dialog | committed 8c3be1b, 57f1c8f; open fix 34 patch d3e60a2 |
| checks 338 → 344 | committed with the parts |
| live steps | 10 steps recorded as works (177 rows 8-17), liveguard clean (row 18) |
| docs | written, not committed |
| push record, "look at first" | **missing** |

Window sizes, from the evidence file names (177's order: every step at both):

| step | 1920x1080 | 2576x1432 |
|---|---|---|
| home star after CONTINUE, rename + ACCEPT | yes | via new game (Sol → Vega) |
| home star, accept unchanged (Enter) | **no** | yes |
| TURN, colony-base questions answered in HD | yes | yes |
| safety net with keys (ruler-name popup) | yes | **no** |
| safety net with the mouse (banner click) | yes | **no** |
| Select Race BACK / ESC | yes | yes |
| Load dialog: list, CANCEL | yes | yes |
| Load dialog: load a scratch slot | **no** | yes |

The crash cannot have spoiled a recorded result: each ran to completion
before 18:16, its pictures decode, and the final liveguard verify (repeated
above) is clean. They are not repeated. The four **no** cells are what part 4
runs.

---

## 4. 177 finished

**Live, own engines, liveguard before and after** (screen not blanked at
either start; `--blanked-ok` given, not needed):

| engine | PID | guard | used for | ended | verify |
|---|---|---|---|---|---|
| A | 8708 (launcher 8702), started 18:37:12 | `live_guard/178_engineA` | CONTINUE (SAVE10, read only) at 1920; GAME → NEW at 2576 | SIGTERM, gone within 10 s | SAVE10 and MOX.SET changed (the new game) → restored, verified identical |
| B | 9885 (launcher 9879) | `live_guard/178_engineB` | main menu Load → SAVE4 (scratch, read only) at 1920 | SIGTERM | MOX.SET changed → restored, verified identical |

After both: `liveguard verify 177_master` → only `tree/git status`;
SAVE4 `b36cc852…` and SAVE8 `ab70cc9a…` equal to the manifest. Slots loaded:
SAVE10 (by CONTINUE) and SAVE4; nothing saved to any slot.

The four gaps from part 3 — all **works**, rows 19-22 of 177's table:

| step | size | result | evidence (`work_order_178/`) |
|---|---|---|---|
| home star after CONTINUE, accept unchanged with Enter → "Mentar" | 1920 | works | `home_star_1920/` |
| safety net with keys: ruler-name popup, Backspace + "Tester", Enter | 2576 | works (one modalnet line per shape) | `net_keys_2576/` |
| safety net with the mouse: banner click → game starts, HD home star dialog "Altair" | 2576 | works | `net_mouse_2576/` |
| main menu Load: row 4 → SAVE4 loaded, 3509.0 | 1920 | works; a row click loads at once, the driver's extra LOAD click landed on the map with no effect | `main_menu_load_1920/` |

Nothing found that needs a code change. **Open fix 34 not applied**, parked
(178 parked 1, 177 parked 1 extended with what the dialog can and cannot do
without it). 177's results table is complete (rows 1-23), with the crash
noted, "look at first" written; its push record is filled at the push.

## 5. Push — **MADE**

The record is in `177-progress.md` "Push record": `a30ef2f..3fe2184`, fast-
forward, full suite and fresh clone 344 green right before, tree clean,
liveguard clean, no engine running, no broken step; local = remote after.
This file's commit is pushed the same way, right after.
