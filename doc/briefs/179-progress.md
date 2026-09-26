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
- The OrionLayer commit that records fix 34 is **`3787e0a`** (written into
  entry 34 by the part 3 commit — a commit cannot name its own hash).

## 3. The main menu's Load dialog in HD — **DONE (built by 177, live now)**

Nothing new had to be drawn: 177 wrote the main menu to hand its Load
dialog to the GAME menu overlay — the popup block of 169/174, glass and
tint, text in code, the same dialog the in-game Load uses — as soon as the
dialog's fields AND the slots are on the wire (`screens/main_menu/screen.py`
`_load_dialog`), and to keep the safety net for everything else. Fix 34
supplies the slots, so this part is the live proof and the guard for the
data's absence:

- **Live, 1920x1080** (engine 23512): the dialog drawn in HD, the ten rows
  equal to the ten save files (name, stardate, date = file mtime), CANCEL
  back to the menu, row 4 → SAVE4 loaded (3509.0).
  `evidence/work_order_179/fix34_main_menu_load_1920/`.
- **Live, 2576x1432** (engine 29787): the dialog drawn, CANCEL.
  `load_dialog_2576/`.
- **Without the data** — the fallback stays: without slots the net shows
  the game's picture (090j #1, unchanged); a stale slot message behind the
  menu's own list opens nothing (090j #2).
- One name reads "claude nicht lschen" (slot 8): the SAVE8 file itself holds
  those bytes — the game dropped the ö when the name was typed; HD shows
  what is stored.
- Checks: none new in this part (090j #1/#2 cover it).

## 4. New Game: the fourth tech level removed — **DONE, live-checked**

- **The original** offers three (newgame.cpp:281, `_civ_button_strings, 3`,
  `_tech_level_anims[3]`): 0 = E_Strings 0x1ad "Pre Warp", 1 = 0xbe
  "Average", 2 = 0xa9 "Advanced" (newgame.cpp:372-374, the player's English
  ESTRINGS), stored in `starting_civilization_level` (:382). The wire sends
  `_civ_button_variable` unchanged (ext_api.cpp:179).
- **HD had four since the first v3 commit** (`e0ae910`): `layout.json` also
  mapped a value 3, "Post Warp", with two pictures. The engine never sends
  3, so it was dead, but it was there to be shown and to be modded. Removed:
  the entry and `assets/tech_level/post_warp.png`, `post_warp1.png` (HD
  artwork, not MOO2 files). 0/1/2 were already mapped right.
- **Check** 090k (new group `new_game`): every category offers exactly the
  original's value count, from the source (5/5/3/7/3), each value with its
  picture, tech level Pre Warp/Average/Advanced = 0/1/2, no picture for a
  value that does not exist — the rule, not the instance. **349 → 350.**
- **Live** (engine 29787, intro skipped, guard `179_part4`): a new game per
  level, the level set by clicking HD's tech slot until the engine's value
  was the target, then ACCEPT → Select Race → ruler name and banner through
  the net → galaxy map. The level read back from **two sources**, the wire's
  `s_settings` byte 0xD9 (orion2.h:2493) and `MOX.SET` byte 0xD9 on disk
  (written by the new game):

  | set | HD label | wire 0xD9 | MOX.SET 0xD9 | size |
  |---|---|---|---|---|
  | 0 | Pre Warp | 0 | 0 | 1920x1080 |
  | 2 | Advanced | 2 | 2 | 1920x1080 |
  | 1 | Average | 1 | 1 | 2576x1432 |

  `evidence/work_order_179/tech_level_*/` (pictures and `*_result.json`),
  driver `techlevel179.py` beside them. After the run SAVE10 (the new games'
  autosave) and MOX.SET were restored; the guard verified clean.

## 5. 2160p scaling — **DONE (both screens), 1080p pixel-identical**

**The cause, one fault on both screens:** the text size was
`Layout.font_size(ref × box_font_scale(box))`. `box_font_scale` already
multiplies by `win_h / 1080`, and `Layout.font_size` multiplies by the window
scale again, so the resolution factor was SQUARED: ×1 at 1080p, ×1.78 at
1440p, **×4 at 2160p where ×2 is proportional**. `ScreenBase.
box_font_scale_stored` exists for exactly this (its docstring names the
failure, 7 September 2026) and was not used here. No hardcoded 2160p branch
existed and none was added: both screens now take the stored scale and let
`Layout.font_size` apply the resolution factor once.

- **Star names** (and the hover name, same line of code): 16 × zoom scale ×
  stored box scale → `Layout.font_size`. Measured by 090l on 88 names: every
  one at 3840x2160 is exactly twice its 1920x1080 size (before: 13 → 43 px).
- **Select Race**: grid names, race name and subtitle, description, traits
  (`race_grid`, `race_name`, `race_description`, `race_traits`), same change.
  Before, at 2160p, the race name ran into its subtitle and the Government
  row was cut off at the panel's lower edge. Measured by 090m on the
  screen's own 9 text sizes (the shared HUD frame excluded: it sizes itself
  by its own rule): each is twice its 1080p size (before: 13 → 52 px).
- Both checks shown RED on the old code and GREEN on the new (run with
  `python -B`, fundament 08). **350 → 352** (new modules 090l, 090m).
- **Renders** (offline, the suite's fixtures, `tools/hud_evidence.py`), before
  and after, 1080p, 2160p and Data's 2576x1432:
  `evidence/work_order_179/scaling_2160/{before,after}/` and
  `compare_<screen>_<size>_before_left_after_right.png`. **1080p: pixel-
  identical** before and after on both screens (image difference: none).
  2160p: text at 1080p's proportions. **2576x1432 changes as well**: its
  factor was 1.78 instead of 1.33, so text there is now a quarter smaller —
  Data's own window size; parked item 2.

## 6. The missing icons (169's P11) — **DONE: every button has a glyph; shown where it fits**

- **Source: our own, drawn from coordinates.** 43 glyphs as line art on a
  unit square in `assets/shared/hud/glyphs.json` (back, close, check,
  load, save, new, power, gear, prev/next/up/down, person, players, hire,
  dismiss, pool, star, trash, relocate, all, wrench, swords, colony, ship,
  list, harvest, industry, science, hammer, coin, thermometer, crystal,
  size, shield, gravity, leaf, range, flag, outpost, exit, clear, play),
  drawn by the new `tools/hud_glyphs.py` (PIL, 4x supersampled, a soft
  glow) into `assets/shared/hud/cut/icon_<glyph>.png` beside the cut
  pieces — derived, ignored by git, built by `tools/setup.py` via
  `hud_cut.py`. **No MOO2 file** is touched; LICENSE says what they are.
  Colour, line and glow are `chosen.glyph` in `style.json` — the colour
  measured off five nav icons (median (29, 179, 255)).
- **Which button shows which:** one table, `glyphs.json` "buttons",
  67 buttons on the 12 screens of P11, by the button's own NAME (never its
  word). Wired through every path: box buttons (`Box.icon`, set by
  `ScreenBase`), frame buttons (`screenframe`), the colony sort keys and
  RETURN, the system window's CLOSE (`small_button` got `icon`), and the
  screens that draw their word themselves through one helper,
  `core/hud/icons.icon_beside` (Planets, GAME menu, Fleets via
  `icons.fitted_word`, Leaders, Research EXIT).
- **Moddable:** each glyph is a HUD piece — `art.PIECES`, so the mod
  folder's `hud/icon_<glyph>.png` replaces it (a typo still refused) and
  the mod template ships them; they turn with the frame colour like the
  nav glyphs (`tint.FOLLOWS`).
- **The rule: the word stays whole.** An icon is drawn only where it and
  the whole word fit; otherwise the word alone. Found by looking: the
  HUD block's own label path drew the icon and squeezed the word (the
  colony sort keys, POPULATION under a person) — fixed, same rule.
- **Placeholders: none needed** — every button has a clean source. What is
  missing is ROOM (parked item 4): at 1920x1080 and 2576x1432 the colony
  keys POPULATION, INDUSTRY, SCIENCE, PRODUCING and RETURN, Planets'
  CLIMATE and MINERALS, Fleets' SUPPORT, COMBAT, PREV and NEXT, and the GAME
  menu's five main buttons show their word only (HALL OF FAME too at
  2576). Leaders, Research EXIT and the system window's CLOSE have no
  offline state to render; their code path is the helper's.
- Split for the line guideline: `core/hud/icons.py` (the helper, and
  Fleets' `_centred` as `fitted_word`), `core/hud/glyphs.py` (names only,
  so `art` and `tint` do not import each other). Checks: new 006h (2), 006a
  now holds all pieces incl. glyphs, 013's label-colour measure leaves the
  glyph out (13 is listed at 46 KB now). **352 → 354.**
- Evidence: `evidence/work_order_179/icons/glyph_sheet.png` and every
  affected screen at 1920x1080 and 2576x1432 (`*_offline.png`).

### Found at the end: HUD words at the wrong size after a renderer was replaced

The fresh clone's FULL run failed 006h: the main menu drew its words at
38 px where 16 is right, so they overflowed and the icons were (rightly)
dropped. Cause: `core/hud/text.cap_ratio` cached per `id(style_renderer)`;
Python reuses a dead object's id, so a renderer built after another was
dropped inherited its ratio. The app keeps one renderer for its life and
never showed it; tools and checks that stand apps up did. The ratio lives
on the renderer now; 006h holds it. Pre-existing (not from this order),
fixed because it made a check machine-dependent.
