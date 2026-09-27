# Work order 183 — progress

Unattended run, 27 September 2026, base `7d491d9` (= origin/main, 379
checks). orion2re `orionlayer-local` `2097b0c6`, its three untracked files
(`mox.set`, `racesel_custom_screen_id.patch`, `src.zip`) left alone.
Evidence root: `~/orionlayer-fixtures/evidence/work_order_183/`.

## Before part 1

- Read: `doc/v3_fundament.md` (the index), all three `principles-` parts
  (06, 07, 08) in full, and the parts this order touches: 09 (the start
  hang, the live-run file list, the engine line, the virtual display) and
  02 (decision 39's correction — the window shown before `g_hide_window`).
  Also 182's progress, parked file, virtual-display brief and entry 41.
- 17:40: no orion2re and no OrionLayer client running. **In Data's session**
  (left alone, noted): Borderlands 3 (PID 27418) playing sound on his HDMI
  sink, Steam, Firefox and Chromium — his, and the reason every audio step
  below touches only a stream this run started.

## Part 1 — apply fix 41 and document it — **DONE**

1. **Applied.** On `orionlayer-local` at `2097b0c6`:
   `patch -p1 --dry-run`, then `patch -p1` with
   `doc/ext_engine_window_hidden.patch` — both files, no offset, no fuzz;
   `ninja -C out/build/Linux/linux-debug` compiled the two files and linked
   (17:40). One commit, **`4bf152e4`** "OrionLayer Open Fix 41: keep the
   engine's own window hidden from the start" (`git add` of the two files;
   the three untracked files untouched).
   **Against 182's scratch proof, byte for byte:** the scratch clone lived
   in another session's scratchpad and is gone, but the patch file IS its
   `git diff` — and `git diff 4bf152e4~1 4bf152e4` equals the file's diff
   byte for byte, `diff --git` and `index` lines included (sha256
   `a2f8e948…` both); the post-image blobs are `88c157cd` and `3f943781`,
   the scratch commit's own.
2. **Live on Xvfb** (`:91`, every start through `tools/engine_start.py`
   with its own liveguard backup, each verified after):

   | | result |
   |---|---|
   | window (starts 29931, 30052, 30148, 30255) | **never mapped**: `xwatch` on the root from before the engine existed saw 0 maps of the engine's window and 2 of a control window per run; `xwininfo` `IsUnMapped` at READY and 20 s later |
   | start | no hang in 6 starts; READY 1.53-1.54 s, the intro skipped by the key |
   | pacing, main menu, 20 s (first 5 s left out) | 6.06/s, gap median 164.3, p95 166.4, max 166.8-167.1 ms — 182: 6.0-6.1/s, 164.8-165.2 / 166.4-166.5 / 166.7 |
   | the same WITHOUT `ORION2RE_NO_VSYNC` (30255) | 6.06/s, 164.5 / 166.5 / 167.5 ms — the hidden window alone turns VSync off |
   | flash walk, 1920, incl. the SAVE4 load (engine 30375) | 29 transitions, 0 native frames; identical to 182's unpatched and fix-41 runs on 182's comparison columns (only the gate's `held` counts differ, as between 182's own runs) |
   | colony screen + build popup, `--orders`, 1920 (engine 30611) | 23 transitions, 0 native frames, 407 colony frames agreeing, 0 disagreeing; every order's result and the table identical to 182's unpatched run |
   | guards `183_P1_start_{a,b,c,novsyncenv}`, `183_P1_flash`, `183_P1_colony` | starts: identical; the two load runs: MOX.SET's load byte (offset 21, 10 → 3), restored, verified identical |

   The first pacing figure of start a (7.2/s) counted the burst at connect;
   the script then measured the steady window, which is what the table
   gives. One run's name swallowed its flag (a shell quoting slip) and ran
   WITH the variable — kept as start c, its guard verified.
3. **Documented** as 34-40 were:
   - entry 41 **APPLIED**: date, `4bf152e4`, the OrionLayer commit (its
     hash added by Part 2's commit), file / function / lines (ext_api.cpp
     :16; platform.cpp `Present_VSync_Interval_` from :20, added 21-24;
     the show at :1410-1412, every line re-read on the committed tree), the
     full diff, the live table, the revert (`git revert` or `patch -R`,
     dry-run proved clean), and the side effects — a hidden window presents
     without VSync, and the measured pacing did not move;
   - `version_check`: 41 moved to `LOCAL_PATCHES`, `REPORTED_PATCHES`
     empty again. **A build without it is refused by name** — run on the
     whole `src/` of `2097b0c6` (`git archive`, nothing written to the
     repo): exit 1, one line, `doc/ext_engine_window_hidden.patch :
     MISSING` and "… (open fix 41) …";
   - the fresh-clone list: README's table row 14 and its bundle name,
     `setup.py`'s report (from `required_fixes`, now "… 34, 35, 36, 37, 38,
     39, 40, 41"), fundament part 09's engine line; one dated sentence each
     in part 09 (virtual display) and part 02 (decision 39's correction);
   - **the entry's diff against the commit**: the entry's diff is
     `git diff 4bf152e4~1 4bf152e4` with git's `diff --git`/`index` lines
     and the text after `@@` left out — produced from the commit, and held
     by the new check against the patch file, which is held against the
     commit;
   - **bundle** `~/orion2re_bundle_27sep_4bf152e4_fixes34-41.bundle`
     beside the others: `git bundle verify` exit 0, a clone of it has
     `4bf152e4` on top and 1164 commits, as the branch.
4. **Check 090r #4** (new): fix 41 applied and documented — required,
   status and hash in entry, summary row and patch file, two one-line
   markers, the entry's diff the file's; on a disk with the tree the
   commit's diff the file's and each marker once. 090r's old "41 is parked"
   assertions went with the state they described (in the same module).
   **Checks 379 → 380.**
