# Work order 179 — progress

Unattended run, 26 September 2026, base `d2b30a6` (= origin/main, 344
checks). Evidence root: `~/orionlayer-fixtures/evidence/work_order_179/`.

## Before part 1 — Data's own game, found running

At 19:33 an orion2re (PID 17960, started 19:21:23 from a terminal, pts/1)
and an OrionLayer client (`python main.py`, PID 18302, 19:21:36, pts/2)
were running, the desktop had been idle for 49 s, and `SAVE10.GAM` and
`MOX.SET` had been written at 19:25:33. That is somebody playing, not a
leftover, so neither was closed, and the two files were **not** restored:
they are that game's own writes, not a live run's. Data then wrote that the
game and the overlay were closed and that this run starts and closes its own.
Consequence for the guard: `177_master` no longer describes the game folder
(its SAVE10 and MOX.SET are older than Data's game); this order's live steps
take their own backups, and the final verify is against those.

## 1. user_settings.json in ~/.config/orionlayer/ — **DONE**

- `core/usersettings.py`: `default_path()` = `usermod.user_dir()` +
  `user_settings.json` — `$XDG_CONFIG_HOME/orionlayer/` (default
  `~/.config/orionlayer/`), `%APPDATA%\OrionLayer\` on Windows,
  `ORIONLAYER_USER_DIR` overriding, i.e. exactly the mod folder's base
  (decision 72), resolved at every call. `OLD_PATH` is the program folder's
  file. `migrate()`: new missing and old present → the old one COPIED
  (`shutil.copy2`), one INFO line; both present → the new one used, one INFO
  line naming the ignored old one; neither → nothing, not even the folder.
  The old file is never deleted or written. `load()` without a path migrates
  and reads the new home; `save()` creates the folder and writes only there.
- `tools/liveguard.py`: keys `config/user_settings.json` (+ `.tmp`,
  `.corrupt`) in `usermod.user_dir()` beside the old `layer/…` keys in the
  program folder; the manifest records `config_dir`; a restore recreates a
  missing folder. An old home that does not exist is recorded absent and not
  reported — held "as long as it exists". Manifests from before 179 verify as
  they were taken (no `config/` keys).
- Checks (new module `006g`, core): the migration's three states; the XDG
  override, the base shared with the mod folder, writes to the new home
  only; the guard backing up, naming and restoring both. 062's assertion that
  the loader's path is the tree's `user_settings.json` is REPLACED (not
  deleted): the tree's file is the old home and still ignored, the loader's
  home is outside the tree. **344 → 347.**
- Documented in decision 72 (part 01), decision 63's note (part 04), part 09
  and CLAUDE.md's live-run file list.
- On this machine: `~/.config/orionlayer/` did not exist; the program
  folder's `user_settings.json` (hue 161, …) is copied at the next start.

## 2. Open fix 34 — **APPLIED, live-checked**

- **Applied** from `doc/ext_main_menu_save_slots.patch` (dry-run clean) to
  `orionlayer-local`, after one change to the patch before applying it:
  its six-line comment shortened to two lines naming "Open Fix 34" and
  the reason, as this order asks. No code line differs from 177's patch.
  Rebuilt (`ninja -C out/build/Linux/linux-debug`, ext_api.cpp.o + link,
  binary 19:53:50). **One engine commit: `9ab84230`** "OrionLayer Open Fix
  34: send the save slots for the main menu's Load dialog too
  (ext_api.cpp)"; bundle `~/orion2re_bundle_26sep_9ab84230.bundle` (lists
  `orionlayer-local` = 9ab84230). Nothing pushed; orion2re untouched
  otherwise (the three untracked files as before).
- **Live** (engine 23512, started here, guard `179_fix34`; engine 27195,
  guard `179_run2`), 1920x1080:
  main menu → LOAD GAME: MSG_SAVE_SLOTS arrived (892 bytes, screen_data 2)
  and the GAME menu overlay drew the dialog; the ten rows' dates equal the
  ten `SAVEn.GAM` files' mtimes (SAVE1 Jul 31 13:52 … SAVE10 Sep 26 19:25,
  Data's own game). CANCEL → the menu; LOAD GAME → row 4 → **SAVE4 loaded,
  stardate 3509.0** (a row loads at once, as the original's). In game, the
  GAME menu's Load (screen_data 2) and Save (screen_data 3) sent the same
  ten slots — open fix 14 unchanged; both cancelled, nothing saved.
  **Wire excerpt**: `doc/briefs/179-fix34-wire.txt` (raw + parsed), and the
  three others under `evidence/work_order_179/`.
- **Side effect found, measured, harmless for HD:** leaving the dialog with
  ESC (not CANCEL) keeps `_screen_data` 2 (loadsave.cpp:388-391), so the
  main menu's own list is followed by a slot message; a game can also
  return to the main menu with a star index 2 in `_screen_data`. HD opens
  the dialog only on its own field shape plus slots — checked live and by
  090j's new check. Written into entry 34.
- **Entry 34** (`doc/orion2re_open_fixes.md`): APPLIED, date, 9ab84230, the
  recording OrionLayer commit (by subject; its hash is below), file,
  function, lines 481 → 481-485, the diff in full, the live result with the
  excerpt, revert, side effects. Table row updated. The patch file's header
  says APPLIED.
- **Byte for byte, verified by script:** the patch file's diff, and the diff
  in entry 34, both equal `git diff 9ab84230~1 9ab84230 --
  src/ext/ext_api.cpp` (the text git appends after `@@` — the enclosing
  function's name — is not part of the change and was stripped for the
  compare).
- **Where a fresh clone learns it needs fix 34:** `tools/version_check.py`
  moves it from REPORTED to LOCAL_PATCHES (a tree without it now fails and
  gets the `patch -p1` line printed); README gains "The orion2re build it
  needs" — the `orionlayer-local` commits in order, each fix and patch file,
  fix 34 included, and how a new machine gets the branch (the bundle); a
  check holds that table to LOCAL_PATCHES; CLAUDE.md's "Running it" names
  `version_check.py`. No other document listed the applied fixes as a set.
- Checks: 090j #2 (fix 34 required, README table, the stale slot message
  opens nothing). **347 → 348.**

### Also: the intro is skipped (Data, during this part)

"Always skip the intro — one key is enough." `tools/engine_start.py` now
sends one space key to the engine's OWN window (`xdotool key --window`)
while the log stands at "data space allocated", until "logos drawn" — the
original's own skip (jim.cpp:59-61, :93). The engine's `_skip_intro` flag
(mox2.cpp:301) is set by nothing and setting it would be an engine change,
so it is not used. Space is no main-menu hotkey (mainmenu.cpp:126-138).
Measured: READY after **3 s** (was ~115 s). `--intro` lets it play. The
closing of leftovers moved to `tools/engine_close.py` (engine_start had
passed the 300-line guideline: 307 → 257). Check 006e #3b. **348 → 349.**
