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
